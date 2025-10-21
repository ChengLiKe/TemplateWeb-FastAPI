"""
Logger configuration:
- Colored console output; color auto-disabled on non-TTY
- Plain text file output without ANSI sequences
- Avoid duplicate handlers on repeated setup calls
- Configurable level and directory via environment variables
"""

import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Level configuration via env: LOG_LEVEL=DEBUG|INFO|WARNING|ERROR|CRITICAL
LOG_LEVEL_NAME = os.getenv("LOG_LEVEL", "DEBUG").upper()
LOGGER_LEVEL = getattr(logging, LOG_LEVEL_NAME, logging.DEBUG)

# Log directory via env: LOG_DIR=./logs
LOG_DIR = Path(os.getenv("LOG_DIR", "logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"

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


def setup_logger(logger_name: str = "app") -> logging.Logger:
    """
    Create or retrieve a logger with:
    - Colored console handler (level from env, default DEBUG)
    - Rotating file handler (INFO+), UTF-8, 1MB x 3 backups
    - No handler duplication across repeated calls
    """
    logger = logging.getLogger(logger_name)

    # If already configured, return as-is to avoid duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(LOGGER_LEVEL)

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
