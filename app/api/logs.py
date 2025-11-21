# app/api/logs.py
from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse
from sqlalchemy import text
from typing import Optional
from app.services.db import get_db_engine
from app.utils import get_logger
from app.config.settings import Settings
import time

settings = Settings.load()

router = APIRouter()
log = get_logger("LOG_MONITOR")

@router.get("/logs", tags=["Monitoring"], summary="获取日志列表")
async def get_logs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页条数"),
    level: Optional[str] = Query(None, description="日志级别过滤"),
    component: Optional[str] = Query(None, description="组件过滤"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    min_id: Optional[int] = Query(None, description="最小日志ID，用于获取新日志"),
    exclude: Optional[str] = Query(None, description="排除的模块，格式为module.submodule")
):
    """
    获取数据库中的日志记录，支持分页、级别过滤和关键词搜索
    """
    ts = time.time()
    engine = get_db_engine()
    
    if not engine:
        log.error("数据库不可用")
        return {
            "status": "error",
            "message": "数据库不可用",
            "ts": ts
        }
    
    try:
        with engine.connect() as conn:
            # 构建查询条件
            conditions = []
            params = {}
            
            if level:
                conditions.append("level = :level")
                params["level"] = level
                
            if component:
                conditions.append("component = :component")
                params["component"] = component
                
            # 最小ID过滤（用于获取新日志）
            if min_id:
                conditions.append("id >= :min_id")
                params["min_id"] = min_id
                
            # 排除特定模块
            if exclude:
                conditions.append("module != :exclude")
                params["exclude"] = exclude
                
            if search:
                conditions.append("(message LIKE :search OR logger LIKE :search OR module LIKE :search)")
                params["search"] = f"%{search}%"
            
            # 构建WHERE子句
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            # 计算偏移量
            offset = (page - 1) * page_size
            
            # 查询日志记录
            logs_query = f"""
                SELECT id, timestamp, level, logger, module, line, message, component, trace_id 
                FROM {settings.logs_table_name} 
                {where_clause}
                ORDER BY id DESC 
                LIMIT :limit OFFSET :offset
            """
            
            logs_result = conn.execute(text(logs_query), {
                **params,
                "limit": page_size,
                "offset": offset
            }).fetchall()
            
            # 查询总记录数
            count_query = f"""
                SELECT COUNT(*) FROM {settings.logs_table_name} {where_clause}
            """
            total = conn.execute(text(count_query), params).scalar()
            
            # 转换为日志条目列表
            logs = [
                {
                    "id": row[0],
                    "timestamp": row[1],
                    "level": row[2],
                    "logger": row[3],
                    "module": row[4],
                    "line": row[5],
                    "message": row[6],
                    "component": row[7],
                    "trace_id": row[8]
                }
                for row in logs_result
            ]
            
            log.info(f"获取日志成功 page={page} page_size={page_size} total={total}")
            
            return {
                "status": "success",
                "data": {
                    "logs": logs,
                    "pagination": {
                        "page": page,
                        "page_size": page_size,
                        "total": total,
                        "pages": (total + page_size - 1) // page_size
                    }
                },
                "ts": ts
            }
            
    except Exception as e:
        error_msg = f"获取日志失败: {str(e)}"
        log.error(error_msg)
        return {
            "status": "error",
            "message": error_msg,
            "ts": ts
        }

@router.get("/logs/stats", tags=["Monitoring"], summary="获取日志统计信息")
async def get_logs_stats():
    """
    获取日志统计信息，包括各级别日志数量
    """
    ts = time.time()
    engine = get_db_engine()
    
    if not engine:
        log.error("数据库不可用")
        return {
            "status": "error",
            "message": "数据库不可用",
            "ts": ts
        }
    
    try:
        with engine.connect() as conn:
            # 查询各级别日志数量
            stats_query = f"""
                SELECT level, COUNT(*) as count 
                FROM {settings.logs_table_name} 
                GROUP BY level 
                ORDER BY count DESC
            """
            stats_result = conn.execute(text(stats_query)).fetchall()
            
            # 查询总日志数
            total_query = f"SELECT COUNT(*) FROM {settings.logs_table_name}"
            total = conn.execute(text(total_query)).scalar()
            
            # 查询最近的日志时间
            latest_query = f"SELECT MAX(timestamp) FROM {settings.logs_table_name}"
            latest_timestamp = conn.execute(text(latest_query)).scalar()
            
            stats = {
                "by_level": {row[0]: row[1] for row in stats_result},
                "total": total,
                "latest_timestamp": latest_timestamp
            }
            
            log.info("获取日志统计信息成功")
            
            return {
                "status": "success",
                "data": stats,
                "ts": ts
            }
            
    except Exception as e:
        error_msg = f"获取日志统计失败: {str(e)}"
        log.error(error_msg)
        return {
            "status": "error",
            "message": error_msg,
            "ts": ts
        }

@router.get("/logs/components", tags=["Monitoring"], summary="获取所有组件列表")
async def get_log_components():
    """
    获取所有出现在日志中的组件列表
    """
    ts = time.time()
    engine = get_db_engine()
    
    if not engine:
        log.error("数据库不可用")
        return {
            "status": "error",
            "message": "数据库不可用",
            "ts": ts
        }
    
    try:
        with engine.connect() as conn:
            # 查询所有唯一的组件名称
            components_query = f"""
                SELECT DISTINCT component 
                FROM {settings.logs_table_name} 
                WHERE component IS NOT NULL AND component != '' 
                ORDER BY component
            """
            components_result = conn.execute(text(components_query)).fetchall()
            
            components = [row[0] for row in components_result]
            
            log.info(f"获取组件列表成功 count={len(components)}")
            
            return {
                "status": "success",
                "data": {
                    "components": components
                },
                "ts": ts
            }
            
    except Exception as e:
        error_msg = f"获取组件列表失败: {str(e)}"
        log.error(error_msg)
        return {
            "status": "error",
            "message": error_msg,
            "ts": ts
        }

import os
import pathlib

@router.get("/logs/web", tags=["Monitoring"], summary="日志监控Web界面")
async def logs_web():
    """
    简单的日志监控Web界面
    """
    try:
        # 获取当前文件所在目录
        current_dir = pathlib.Path(__file__).parent.parent
        # 构建HTML文件的绝对路径
        html_file_path = os.path.join(current_dir, 'static', 'log_monitor.html')
        
        # 读取HTML文件内容
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        return HTMLResponse(content=html_content)
    except Exception as e:
        error_msg = f"读取日志监控页面失败: {str(e)}"
        log.error(error_msg)
        return HTMLResponse(content=f"<h1>错误</h1><p>{error_msg}</p>", status_code=500)