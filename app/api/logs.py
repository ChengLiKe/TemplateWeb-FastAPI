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
                /* 全局样式 */
                * {
                    box-sizing: border-box;
                    margin: 0;
                    padding: 0;
                }
                
                html, body {
                    height: 100%;
                    margin: 0;
                    padding: 0;
                    overflow: hidden;
                }
                
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    background-color: #f5f7fa;
                    color: #333;
                    line-height: 1.6;
                }
                
                .container {
                    max-width: 1400px;
                    margin: 0 auto;
                    padding: 20px;
                    height: 100%;
                    display: flex;
                    flex-direction: column;
                    box-sizing: border-box;
                }
            
            /* 标题样式 */
            h1 {
                color: #2c3e50;
                margin-bottom: 20px;
                font-size: 24px;
                font-weight: 600;
            }
            
            /* 统计卡片样式 */
            .stats {
                display: flex;
                gap: 20px;
                margin-bottom: 20px;
            }
            
            .stat-card {
                flex: 1;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                transition: transform 0.2s ease;
            }
            
            .stat-card:hover {
                transform: translateY(-2px);
            }
            
            .stat-card h3 {
                font-size: 14px;
                font-weight: 400;
                opacity: 0.9;
                margin-bottom: 8px;
            }
            
            .stat-card .value {
                font-size: 28px;
                font-weight: bold;
            }
            
            /* 筛选器样式 */
            .filters {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                gap: 15px;
                flex-wrap: wrap;
            }
            
            .filters select, 
            .filters input {
                padding: 10px 15px;
                border: 1px solid #e1e8ed;
                border-radius: 6px;
                background: white;
                font-size: 14px;
                transition: border-color 0.2s ease;
            }
            
            .filters select:focus, 
            .filters input:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
            }
            
            .filters button {
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            
            #refresh-btn {
                background-color: #28a745;
                color: white;
            }
            
            #refresh-btn:hover {
                background-color: #218838;
            }
            
            #clear-filter-btn {
                background-color: #6c757d;
                color: white;
            }
            
            #clear-filter-btn:hover {
                background-color: #5a6268;
            }
            
            #auto-refresh-toggle {
                background-color: #17a2b8;
                color: white;
            }
            
            #auto-refresh-toggle.active {
                background-color: #dc3545;
            }
            
            /* 表格容器样式 */
            .table-container {
                background: white;
                border-radius: 10px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                overflow: hidden;
                flex: 1;
                display: flex;
                flex-direction: column;
                min-height: 0;
            }
            
            /* 表格样式 */
            table {
                width: 100%;
                border-collapse: collapse;
                font-size: 14px;
                display: block;
                overflow: hidden;
            }
            
            thead {
                position: sticky;
                top: 0;
                background-color: #f8f9fa;
                z-index: 10;
                display: table;
                width: 100%;
                table-layout: fixed;
            }
            
            th {
                padding: 15px;
                text-align: left;
                font-weight: 600;
                color: #495057;
                border-bottom: 2px solid #dee2e6;
            }
            
            tbody {
                display: block;
                max-height: calc(100vh - 400px); /* 为分页控件预留空间 */
                overflow-y: auto;
                width: 100%;
            }
            
            tbody tr {
                display: table;
                width: 100%;
                table-layout: fixed;
            }
            
            td {
                padding: 12px 15px;
                border-bottom: 1px solid #e9ecef;
                vertical-align: top;
                word-break: break-word;
            }
            
            tbody tr:hover {
                background-color: #f8f9fa;
            }
            
            /* 日志级别颜色 */
            .level-DEBUG { color: #28a745; }
            .level-INFO { color: #17a2b8; }
            .level-WARNING { color: #ffc107; }
            .level-ERROR { color: #dc3545; }
            .level-CRITICAL { color: #6f42c1; }
            
            /* 分页样式 */
            .pagination {
                padding: 15px;
                background: white;
                border-top: 1px solid #e9ecef;
                display: flex;
                justify-content: center;
                align-items: center;
                flex-wrap: wrap;
                gap: 5px;
                height: auto;
            }
            
            .pagination button {
                padding: 8px 12px;
                background-color: #f1f3f4;
                border: 1px solid #dadce0;
                border-radius: 4px;
                font-size: 14px;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            
            .pagination button:hover:not(:disabled) {
                background-color: #e8eaed;
            }
            
            .pagination button.active {
                background-color: #667eea;
                color: white;
                border-color: #667eea;
            }
            
            .pagination button:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
            
            /* 加载状态 */
            .loading {
                text-align: center;
                padding: 40px;
                color: #6c757d;
            }
            
            /* 无数据状态 */
            .no-data {
                text-align: center;
                padding: 40px;
                color: #6c757d;
            }
            
            /* 错误状态 */
            .error {
                text-align: center;
                padding: 40px;
                color: #dc3545;
            }
            
            /* 滚动条样式 */
            tbody::-webkit-scrollbar {
                width: 8px;
            }
            
            tbody::-webkit-scrollbar-track {
                background: #f1f1f1;
            }
            
            tbody::-webkit-scrollbar-thumb {
                background: #c1c1c1;
                border-radius: 4px;
            }
            
            tbody::-webkit-scrollbar-thumb:hover {
                background: #a8a8a8;
            }
            
            /* 响应式设计 */
            @media (max-width: 768px) {
                .stats {
                    flex-direction: column;
                }
                
                .filters {
                    flex-direction: column;
                    align-items: stretch;
                }
                
                .filters select, 
                .filters input, 
                .filters button {
                    width: 100%;
                }
                
                table {
                    font-size: 12px;
                }
                
                th, td {
                    padding: 8px;
                }
            }
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
                <button id="auto-refresh-toggle">自动刷新: 开启</button>
            </div>
            
            <div class="table-container">
                <table id="logs-table">
                    <thead>
                        <tr>
                            <th style="width: 60px;">ID</th>
                            <th style="width: 160px;">时间</th>
                            <th style="width: 80px;">级别</th>
                            <th style="width: 100px;">组件</th>
                            <th style="width: 120px;">模块</th>
                            <th style="width: calc(100% - 520px);">消息</th>
                        </tr>
                    </thead>
                    <tbody id="logs-body">
                        <tr><td colspan="6" class="loading">加载中...</td></tr>
                    </tbody>
                </table>
                
                <div class="pagination" id="pagination"></div>
            </div>
        </div>
        
        <script>
            // 全局变量
            let currentPage = 1;
            let pageSize = 50;
            let autoRefreshInterval = null;
            let autoRefreshEnabled = true;
            let lastLogId = 0; // 用于跟踪最后一条日志ID
            
            // 初始化页面
            document.addEventListener('DOMContentLoaded', function() {
                loadStats();
                loadComponents();
                loadLogs();
                
                // 确保表格高度正确
                setTimeout(updateTableHeight, 100); // 延迟执行以确保DOM完全加载
                
                // 监听窗口大小变化
                window.addEventListener('resize', updateTableHeight);
                
                // 设置自动刷新
                startAutoRefresh();
                
                // 添加事件监听
                document.getElementById('refresh-btn').addEventListener('click', loadLogs);
                document.getElementById('clear-filter-btn').addEventListener('click', clearFilters);
                document.getElementById('page-size').addEventListener('change', function() {
                    pageSize = parseInt(this.value);
                    currentPage = 1;
                    loadLogs();
                });
                
                // 自动刷新切换按钮
                const toggleBtn = document.getElementById('auto-refresh-toggle');
                toggleBtn.addEventListener('click', function() {
                    autoRefreshEnabled = !autoRefreshEnabled;
                    this.textContent = autoRefreshEnabled ? '自动刷新: 开启' : '自动刷新: 关闭';
                    this.classList.toggle('active', !autoRefreshEnabled);
                    
                    if (autoRefreshEnabled) {
                        startAutoRefresh();
                    } else {
                        stopAutoRefresh();
                    }
                });
            });
            
            // 启动自动刷新
            function startAutoRefresh() {
                if (autoRefreshInterval) {
                    clearInterval(autoRefreshInterval);
                }
                
                // 每3秒刷新一次统计信息和新日志
                autoRefreshInterval = setInterval(() => {
                    if (autoRefreshEnabled) {
                        loadStats();
                        loadNewLogs(); // 只加载新日志
                    }
                }, 3000);
            }
            
            // 停止自动刷新
            function stopAutoRefresh() {
                if (autoRefreshInterval) {
                    clearInterval(autoRefreshInterval);
                    autoRefreshInterval = null;
                }
            }
            
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
                
                // 添加exclude参数来排除logs相关的API调用日志
                let url = `/logs?page=${currentPage}&page_size=${pageSize}&exclude=logs.web`;
                if (level) url += `&level=${level}`;
                if (component) url += `&component=${component}`;
                if (search) url += `&search=${encodeURIComponent(search)}`;
                
                try {
                    const logsBody = document.getElementById('logs-body');
                    logsBody.innerHTML = '<tr><td colspan="6" class="loading">加载中...</td></tr>';
                    
                    const response = await fetch(url);
                    const data = await response.json();
                    
                    if (data.status === 'success') {
                        logsBody.innerHTML = '';
                        
                        if (data.data.logs.length === 0) {
                            logsBody.innerHTML = '<tr><td colspan="6" class="no-data">暂无日志记录</td></tr>';
                            document.getElementById('pagination').innerHTML = '';
                            return;
                        }
                        
                        // 更新最后日志ID
                        if (data.data.logs.length > 0) {
                            lastLogId = Math.max(...data.data.logs.map(log => log.id));
                        }
                        
                        // 渲染日志行
                        data.data.logs.forEach(log => {
                            const row = createLogRow(log);
                            logsBody.appendChild(row);
                        });
                        
                        // 渲染分页
                        renderPagination(data.data.pagination);
                    } else {
                        logsBody.innerHTML = `<tr><td colspan="6" class="error">加载失败: ${data.message}</td></tr>`;
                    }
                } catch (error) {
                    console.error('加载日志失败:', error);
                    document.getElementById('logs-body').innerHTML = `<tr><td colspan="6" class="error">加载失败: ${error.message}</td></tr>`;
                }
            }
            
            // 加载新日志（只加载比lastLogId大的日志）
            async function loadNewLogs() {
                // 只有在第一页时才自动加载新日志
                if (currentPage !== 1) return;
                
                const level = document.getElementById('level-filter').value;
                const component = document.getElementById('component-filter').value;
                const search = document.getElementById('search-input').value;
                
                // 只获取新日志，添加exclude参数
                let url = `/logs?page=1&page_size=50&min_id=${lastLogId + 1}&exclude=logs.web`;
                if (level) url += `&level=${level}`;
                if (component) url += `&component=${component}`;
                if (search) url += `&search=${encodeURIComponent(search)}`;
                
                try {
                    const response = await fetch(url);
                    const data = await response.json();
                    
                    if (data.status === 'success' && data.data.logs.length > 0) {
                        const logsBody = document.getElementById('logs-body');
                        
                        // 保存现有日志行数
                        const hasExistingLogs = logsBody.children.length > 0 && 
                                              !logsBody.querySelector('.loading') && 
                                              !logsBody.querySelector('.no-data') && 
                                              !logsBody.querySelector('.error');
                        
                        // 将新日志添加到顶部
                        data.data.logs.reverse().forEach(log => {
                            const row = createLogRow(log);
                            if (hasExistingLogs) {
                                logsBody.insertBefore(row, logsBody.firstChild);
                            } else {
                                logsBody.appendChild(row);
                            }
                        });
                        
                        // 更新最后日志ID
                        lastLogId = Math.max(lastLogId, ...data.data.logs.map(log => log.id));
                        
                        // 如果日志太多，删除旧日志
                        const maxVisibleLogs = pageSize * 2; // 最多显示2页的日志
                        while (logsBody.children.length > maxVisibleLogs) {
                            logsBody.removeChild(logsBody.lastChild);
                        }
                    }
                } catch (error) {
                    console.error('加载新日志失败:', error);
                }
            }
            
            // 创建日志行元素
            function createLogRow(log) {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td style="width: 60px;">${log.id}</td>
                    <td style="width: 160px;">${log.timestamp}</td>
                    <td style="width: 80px;" class="level-${log.level}">${log.level}</td>
                    <td style="width: 100px;">${log.component || '-'}</td>
                    <td style="width: 120px;">${log.module}</td>
                    <td style="width: calc(100% - 520px);">${log.message}</td>
                `;
                return row;
            }
            
            // 渲染分页
            function renderPagination(pagination) {
                const paginationDiv = document.getElementById('pagination');
                paginationDiv.innerHTML = '';
                
                // 延迟更新表格高度，确保分页元素已渲染
                setTimeout(updateTableHeight, 50);
                
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
            
            // 计算表格内容区域高度的函数
            function updateTableHeight() {
                // 计算tbody的高度，确保它不会超出浏览器并为分页控件留出足够空间
                const windowHeight = window.innerHeight;
                const containerPadding = 40; // container的padding
                const statsHeight = document.querySelector('.stats').offsetHeight;
                const filtersHeight = document.querySelector('.filters').offsetHeight;
                const tableHeaderHeight = document.querySelector('thead').offsetHeight;
                const paginationReservedHeight = 80; // 为分页控件预留的高度，确保充足
                const verticalSpacing = 30; // 组件间的垂直间距
                
                // 计算可用高度
                const availableHeight = windowHeight - (containerPadding + statsHeight + filtersHeight + tableHeaderHeight + paginationReservedHeight + verticalSpacing);
                
                // 设置表格内容区域高度
                const tbody = document.querySelector('tbody');
                if (tbody) {
                    tbody.style.maxHeight = Math.max(availableHeight, 200) + 'px';
                }
            }
            
            // 页面卸载时清除定时器和事件监听
            window.addEventListener('beforeunload', function() {
                stopAutoRefresh();
                window.removeEventListener('resize', updateTableHeight);
            });
        </script>
    </body>
    </html>
    '''
    return HTMLResponse(content=html_content)