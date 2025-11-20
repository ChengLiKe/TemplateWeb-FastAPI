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
    search: Optional[str] = Query(None, description="搜索关键词")
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
                FROM "+settings.logs_table_name+" 
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
                SELECT COUNT(*) FROM "+settings.logs_table_name+" {where_clause}
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
            stats_query = """
                SELECT level, COUNT(*) as count 
                FROM "+settings.logs_table_name+" 
                GROUP BY level 
                ORDER BY count DESC
            """
            stats_result = conn.execute(text(stats_query)).fetchall()
            
            # 查询总日志数
            total_query = "SELECT COUNT(*) FROM "+settings.logs_table_name
            total = conn.execute(text(total_query)).scalar()
            
            # 查询最近的日志时间
            latest_query = "SELECT MAX(timestamp) FROM "+settings.logs_table_name
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
            components_query = """
                SELECT DISTINCT component 
                FROM "+settings.logs_table_name+" 
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

@router.get("/logs/web", tags=["Monitoring"], summary="日志监控Web界面")
async def logs_web():
    """
    简单的日志监控Web界面
    """
    html_content = '''
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>日志监控系统</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            h1 { color: #333; margin-bottom: 20px; }
            .filters { margin-bottom: 20px; padding: 15px; background-color: #f9f9f9; border-radius: 6px; }
            .filters select, .filters input, .filters button { padding: 8px 12px; margin-right: 10px; border: 1px solid #ddd; border-radius: 4px; }
            .filters button { background-color: #4CAF50; color: white; border: none; cursor: pointer; }
            .filters button:hover { background-color: #45a049; }
            .stats { display: flex; gap: 20px; margin-bottom: 20px; }
            .stat-card { flex: 1; padding: 15px; background-color: #e3f2fd; border-radius: 6px; text-align: center; }
            .stat-card h3 { margin: 0; color: #1976d2; }
            .stat-card .value { font-size: 24px; font-weight: bold; color: #333; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background-color: #f2f2f2; font-weight: 600; }
            tr:hover { background-color: #f5f5f5; }
            .level-DEBUG { color: #4caf50; }
            .level-INFO { color: #2196f3; }
            .level-WARNING { color: #ff9800; }
            .level-ERROR { color: #f44336; }
            .level-CRITICAL { color: #9c27b0; }
            .pagination { margin-top: 20px; text-align: center; }
            .pagination button { margin: 0 5px; padding: 8px 12px; background-color: #f1f1f1; border: 1px solid #ddd; border-radius: 4px; cursor: pointer; }
            .pagination button:hover { background-color: #ddd; }
            .pagination button.active { background-color: #2196f3; color: white; border-color: #2196f3; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>日志监控系统</h1>
            
            <div class="stats" id="stats-container">
                <div class="stat-card">
                    <h3>总日志数</h3>
                    <div class="value" id="total-count">加载中...</div>
                </div>
                <div class="stat-card">
                    <h3>错误日志</h3>
                    <div class="value" id="error-count">加载中...</div>
                </div>
                <div class="stat-card">
                    <h3>最近更新</h3>
                    <div class="value" id="latest-time">加载中...</div>
                </div>
            </div>
            
            <div class="filters">
                <select id="level-filter">
                    <option value="">所有级别</option>
                    <option value="DEBUG">DEBUG</option>
                    <option value="INFO">INFO</option>
                    <option value="WARNING">WARNING</option>
                    <option value="ERROR">ERROR</option>
                    <option value="CRITICAL">CRITICAL</option>
                </select>
                <select id="component-filter">
                    <option value="">所有组件</option>
                </select>
                <input type="text" id="search-input" placeholder="搜索关键词...">
                <select id="page-size">
                    <option value="20">20条/页</option>
                    <option value="50" selected>50条/页</option>
                    <option value="100">100条/页</option>
                </select>
                <button id="refresh-btn">刷新</button>
                <button id="clear-filter-btn">清除筛选</button>
            </div>
            
            <table id="logs-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>时间</th>
                        <th>级别</th>
                        <th>组件</th>
                        <th>模块</th>
                        <th>消息</th>
                    </tr>
                </thead>
                <tbody id="logs-body">
                    <tr><td colspan="6" style="text-align: center; padding: 20px;">加载中...</td></tr>
                </tbody>
            </table>
            
            <div class="pagination" id="pagination"></div>
        </div>
        
        <script>
            // 全局变量
            let currentPage = 1;
            let pageSize = 50;
            
            // 初始化页面
            document.addEventListener('DOMContentLoaded', function() {
                loadStats();
                loadComponents();
                loadLogs();
                
                // 添加事件监听
                document.getElementById('refresh-btn').addEventListener('click', loadLogs);
                document.getElementById('clear-filter-btn').addEventListener('click', clearFilters);
                document.getElementById('page-size').addEventListener('change', function() {
                    pageSize = parseInt(this.value);
                    currentPage = 1;
                    loadLogs();
                });
            });
            
            // 加载统计信息
            async function loadStats() {
                try {
                    const response = await fetch('/logs/stats');
                    const data = await response.json();
                    
                    if (data.status === 'success') {
                        document.getElementById('total-count').textContent = data.data.total || 0;
                        document.getElementById('error-count').textContent = data.data.by_level.ERROR || 0;
                        document.getElementById('latest-time').textContent = data.data.latest_timestamp || '无';
                    }
                } catch (error) {
                    console.error('加载统计信息失败:', error);
                }
            }
            
            // 加载组件列表
            async function loadComponents() {
                try {
                    const response = await fetch('/logs/components');
                    const data = await response.json();
                    
                    if (data.status === 'success') {
                        const componentSelect = document.getElementById('component-filter');
                        data.data.components.forEach(component => {
                            const option = document.createElement('option');
                            option.value = component;
                            option.textContent = component;
                            componentSelect.appendChild(option);
                        });
                    }
                } catch (error) {
                    console.error('加载组件列表失败:', error);
                }
            }
            
            // 加载日志
            async function loadLogs() {
                const level = document.getElementById('level-filter').value;
                const component = document.getElementById('component-filter').value;
                const search = document.getElementById('search-input').value;
                
                let url = `/logs?page=${currentPage}&page_size=${pageSize}`;
                if (level) url += `&level=${level}`;
                if (component) url += `&component=${component}`;
                if (search) url += `&search=${encodeURIComponent(search)}`;
                
                try {
                    const logsBody = document.getElementById('logs-body');
                    logsBody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px;">加载中...</td></tr>';
                    
                    const response = await fetch(url);
                    const data = await response.json();
                    
                    if (data.status === 'success') {
                        logsBody.innerHTML = '';
                        
                        if (data.data.logs.length === 0) {
                            logsBody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px;">暂无日志记录</td></tr>';
                            document.getElementById('pagination').innerHTML = '';
                            return;
                        }
                        
                        // 渲染日志行
                        data.data.logs.forEach(log => {
                            const row = document.createElement('tr');
                            row.innerHTML = `
                                <td>${log.id}</td>
                                <td>${log.timestamp}</td>
                                <td class="level-${log.level}">${log.level}</td>
                                <td>${log.component || '-'}</td>
                                <td>${log.module}</td>
                                <td>${log.message}</td>
                            `;
                            logsBody.appendChild(row);
                        });
                        
                        // 渲染分页
                        renderPagination(data.data.pagination);
                    } else {
                        logsBody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 20px; color: red;">加载失败: ${data.message}</td></tr>`;
                    }
                } catch (error) {
                    console.error('加载日志失败:', error);
                    document.getElementById('logs-body').innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 20px; color: red;">加载失败: ${error.message}</td></tr>`;
                }
            }
            
            // 渲染分页
            function renderPagination(pagination) {
                const paginationDiv = document.getElementById('pagination');
                paginationDiv.innerHTML = '';
                
                const { page, pages } = pagination;
                
                // 上一页按钮
                const prevBtn = document.createElement('button');
                prevBtn.textContent = '上一页';
                prevBtn.disabled = page <= 1;
                prevBtn.addEventListener('click', () => {
                    if (page > 1) {
                        currentPage = page - 1;
                        loadLogs();
                    }
                });
                paginationDiv.appendChild(prevBtn);
                
                // 页码按钮
                const showPages = 5; // 显示的页码数量
                let startPage = Math.max(1, page - Math.floor(showPages / 2));
                let endPage = Math.min(pages, startPage + showPages - 1);
                
                // 调整起始页，确保显示足够的页码
                if (endPage - startPage + 1 < showPages) {
                    startPage = Math.max(1, endPage - showPages + 1);
                }
                
                for (let i = startPage; i <= endPage; i++) {
                    const pageBtn = document.createElement('button');
                    pageBtn.textContent = i;
                    pageBtn.classList.toggle('active', i === page);
                    pageBtn.addEventListener('click', () => {
                        currentPage = i;
                        loadLogs();
                    });
                    paginationDiv.appendChild(pageBtn);
                }
                
                // 下一页按钮
                const nextBtn = document.createElement('button');
                nextBtn.textContent = '下一页';
                nextBtn.disabled = page >= pages;
                nextBtn.addEventListener('click', () => {
                    if (page < pages) {
                        currentPage = page + 1;
                        loadLogs();
                    }
                });
                paginationDiv.appendChild(nextBtn);
            }
            
            // 清除筛选条件
            function clearFilters() {
                document.getElementById('level-filter').value = '';
                document.getElementById('component-filter').value = '';
                document.getElementById('search-input').value = '';
                currentPage = 1;
                loadLogs();
            }
        </script>
    </body>
    </html>
    '''
    return HTMLResponse(content=html_content)