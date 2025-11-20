"""
Logger configuration:
- Colored console output; color auto-disabled on non-TTY
- Plain text file output without ANSI sequences
- Database log storage support
- Avoid duplicate handlers on repeated setup calls
- Configurable level and directory via environment variables
"""

import logging
import os
import sys
import time
from pathlib import Path
from logging.handlers import RotatingFileHandler
from sqlalchemy import text
from app.config.settings import Settings

settings = Settings.load()

# Level configuration via settings
LOG_LEVEL_NAME = settings.log_level.upper()
LOGGER_LEVEL = getattr(logging, LOG_LEVEL_NAME, logging.DEBUG)

# Log directory via settings
LOG_DIR = Path(settings.log_dir)
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"

# Database logging configuration - 使用settings对象中的配置
DB_LOGGING_ENABLED = settings.db_logging_enabled  # 从settings中获取是否启用数据库日志
DB_LOGGING_LEVEL = getattr(logging, settings.db_logging_level.upper(), logging.INFO)  # 从settings中获取数据库日志级别

# ANSI escape sequences
RESET = "\x1b[0m"
COLOR_DEBUG = "\x1b[92m"     # Bright green
COLOR_INFO = "\x1b[34m"      # Blue (fix from 32/green)
COLOR_WARNING = "\x1b[93m"   # Bright yellow
COLOR_ERROR = "\x1b[91m"     # Bright red
COLOR_CRITICAL = "\x1b[95m"  # Bright magenta

LEVEL_COLORS = {
    "DEBUG": COLOR_DEBUG,
    "INFO": COLOR_INFO,
    "WARNING": COLOR_WARNING,
    "ERROR": COLOR_ERROR,
    "CRITICAL": COLOR_CRITICAL,
}

CONSOLE_FMT = "%(asctime)s.%(msecs)03d [%(levelname)8s] %(name)s:%(lineno)d - %(message)s"
FILE_FMT = "%(asctime)s.%(msecs)03d [%(levelname)8s] %(name)s:%(lineno)d - %(message)s"
DATE_FMT = "%Y-%m-%d %H:%M:%S"


class ColoredFormatter(logging.Formatter):
    """Formatter that wraps the entire formatted string with level color."""

    def __init__(self, fmt=None, datefmt=None, use_color=True):
        super().__init__(fmt=fmt, datefmt=datefmt)
        # Disable color when stdout is not a TTY (e.g., piped)
        self.use_color = bool(use_color) and sys.stdout.isatty()

    def format(self, record):
        base = super().format(record)
        if not self.use_color:
            return base
        color = LEVEL_COLORS.get(record.levelname, RESET)
        return f"{color}{base}{RESET}"


class DatabaseHandler(logging.Handler):
    """
    Custom logging handler that writes log records to the database.
    Uses lazy initialization and dynamic activation to ensure the database is available when needed.
    Implements table creation once on first use and safe parameter handling.
    """
    
    def __init__(self, level=logging.NOTSET):
        super().__init__(level)
        self.db_engine = None
        self.table_created = False  # 表创建标志，避免重复创建
        self.last_error_time = 0  # 上次错误时间，用于限制错误输出频率
        self.error_cooldown = 5  # 错误输出冷却时间（秒）
        self.is_active = False  # 初始状态为非活动，数据库就绪后激活
    
    def emit(self, record):
        """Write log record to database, with fallback if database is not available."""
        # 检查日志来源，防止递归
        if record.name == 'app.db_logger' or 'DatabaseHandler' in record.name or \
           any("DatabaseHandler" in str(value) for value in record.__dict__.values()):
            return
            
        try:
            # 如果处理器未激活，尝试激活它
            if not self.is_active:
                # 延迟导入以避免循环导入
                from app.services.db import get_db_engine
                engine = get_db_engine()
                # 只有当数据库引擎可用时才激活处理器
                if engine:
                    self.is_active = True
                    # 首次激活时尝试创建表
                    with engine.connect() as conn:
                        try:
                            conn.execute(text("""
                                CREATE TABLE IF NOT EXISTS "+settings.logs_table_name+" (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    timestamp TEXT,
                                    level TEXT,
                                    logger TEXT,
                                    module TEXT,
                                    line INTEGER,
                                    message TEXT,
                                    component TEXT,
                                    trace_id TEXT
                                )
                            """))
                            conn.commit()
                            self.table_created = True
                        except Exception as table_err:
                            self._log_error(f"Failed to create log table: {str(table_err)}")
                # 数据库未就绪，暂时跳过日志记录
                return
                
            # 处理器已激活，继续记录日志
            from app.services.db import get_db_engine
            engine = get_db_engine()
            
            if not engine:
                # 数据库变得不可用，重置激活状态
                self.is_active = False
                # 避免使用可能导致递归的日志记录
                self._log_error("Database not available, cannot store log")
                return
            
            # Store log in database
            with engine.connect() as conn:
                # 表已在激活时创建，直接进行日志插入
                
                # 使用更安全的参数处理方式，避免SQL注入风险
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(record.created))
                level = record.levelname
                logger_name = record.name.replace("'", "''")
                module = record.module.replace("'", "''")
                line = record.lineno
                message = record.getMessage().replace("'", "''")
                component = getattr(record, 'component', None)
                if component: component = component.replace("'", "''")
                trace_id = getattr(record, 'trace_id', None)
                if trace_id: trace_id = trace_id.replace("'", "''")
                
                # 简化SQL语句格式，避免复杂的字符串拼接
                component_str = f"'{component}'" if component else 'NULL'
                trace_id_str = f"'{trace_id}'" if trace_id else 'NULL'
                
                # 构建更简洁的插入语句
                insert_sql = """
                    INSERT INTO "+settings.logs_table_name+" (timestamp, level, logger, module, line, message, component, trace_id)
                    VALUES ('{}', '{}', '{}', '{}', {}, '{}', {}, {})
                """.format(timestamp, level, logger_name, module, line, message, component_str, trace_id_str)
                
                # 执行插入并提交
                conn.execute(text(insert_sql))
                conn.commit()
                
        except Exception as e:
            # 记录错误但避免过于频繁的输出
            self._log_error(f"Failed to write log to database: {str(e)}")
            # 重置表创建标志，以便在数据库恢复后可以重新尝试
            self.table_created = False
    
    def _log_error(self, message):
        """安全地记录错误消息，避免过于频繁的输出"""
        import sys
        current_time = time.time()
        # 限制错误输出频率，避免日志风暴
        if current_time - self.last_error_time >= self.error_cooldown:
            sys.stderr.write(f"[ERROR] {message}\n")
            self.last_error_time = current_time


def setup_logger(logger_name: str = "app") -> logging.Logger:
    """
    Create or retrieve a logger with:
    - Colored console handler (level from env, default DEBUG)
    - Rotating file handler (INFO+), UTF-8, 1MB x 3 backups
    - Database handler (optional, configurable level)
    - No handler duplication across repeated calls
    """
    logger = logging.getLogger(logger_name)

    # If already configured, return as-is to avoid duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(LOGGER_LEVEL)
    
    # 配置SQLAlchemy日志级别，减少SQL执行日志输出
    # 设置为WARNING以避免显示每个SQL查询的详细信息
    sa_logger = logging.getLogger('sqlalchemy.engine')
    sa_logger.setLevel(logging.WARNING)

    # Console handler with color
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(LOGGER_LEVEL)
    console_handler.setFormatter(
        ColoredFormatter(CONSOLE_FMT, datefmt=DATE_FMT, use_color=True)
    )

    # File handler, plain text formatter
    file_handler = RotatingFileHandler(
        str(LOG_FILE), maxBytes=1 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(FILE_FMT, datefmt=DATE_FMT))

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Database handler (optional)
    if DB_LOGGING_ENABLED:
        db_handler = DatabaseHandler()
        db_handler.setLevel(DB_LOGGING_LEVEL)
        db_handler.setFormatter(logging.Formatter(FILE_FMT, datefmt=DATE_FMT))
        logger.addHandler(db_handler)

    # Do not propagate to parent to avoid duplicate outputs
    logger.propagate = False
    return logger


class ComponentLoggerAdapter(logging.LoggerAdapter):
    """LoggerAdapter that prefixes messages with a component tag and injects extra.component."""

    def __init__(self, logger: logging.Logger, component: str):
        super().__init__(logger, {})
        self.component = component

    def process(self, msg, kwargs):
        extra = kwargs.get("extra") or {}
        # ensure component in record for potential formatters
        extra.setdefault("component", self.component)
        kwargs["extra"] = extra
        return f"[{self.component}] {msg}", kwargs


def get_logger(component: str = "APP") -> ComponentLoggerAdapter:
    """Get a component-specific logger adapter to enforce unified style."""
    base = setup_logger("app")
    return ComponentLoggerAdapter(base, component)


def kv(**kwargs) -> str:
    """Format key-value pairs as 'k=v' joined by spaces, skipping None values."""
    parts = []
    for k, v in kwargs.items():
        if v is None:
            continue
        parts.append(f"{k}={v}")
    return " ".join(parts)

__all__ = ["setup_logger", "get_logger", "kv"]
