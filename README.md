# FastAPI 模板项目

## 项目简介

此项目是一个基于 [FastAPI](https://fastapi.tiangolo.com/) 的模板项目，旨在为使用相同技术栈的后续开发提供基础框架和最佳实践。通过使用此模板，开发者可以快速启动新项目，专注于业务逻辑的实现，而无需从头开始构建基础结构。

## 技术栈

- **后端框架**: FastAPI
- **数据库**: 使用 SQLAlchemy 或其他数据库 ORM（视具体需求而定）
- **Web服务器**: Uvicorn
- **身份验证**: OAuth2/JWT（视具体需求而定）
- **前端**: 可选，支持使用 React, Vue.js 或其他前端框架
- **测试框架**: pytest
- **监控工具**: Prometheus, Grafana

## 特性

- **模块化项目结构**: 采用模块化设计，易于扩展和维护。
- **自动生成文档**: 利用 FastAPI 的特性自动生成交互式 API 文档。
- **基本身份验证**: 提供简单的用户身份验证机制示例。
- **数据库连接**: 提供基本的数据库连接配置与示例。
- **环境变量配置**: 使用 `.env` 文件管理环境变量，支持不同环境的配置。
- **监控与可视化**: 通过集成 Prometheus 和 Grafana，监控应用的性能和请求指标。

## 使用方法

1. **克隆项目**:

    ```bash
    git clone <repository-url>
    cd <project-directory>
    ```

2. **创建虚拟环境** (可选) 建议使用poetry管理虚拟环境，项目中已经提供了 `pyproject.toml` 文件。

    ```bash
    pip install poetry
    ```

3. **安装依赖**
在项目目录中，运行以下命令以安装 `pyproject.toml` 中列出的所有依赖：

    ```bash
    poetry install
    ```

4. **运行应用**:

    ```bash
    poetry run python app.py 
    ```

5. **访问 API 文档**:
   打开浏览器并访问 [http://localhost:8000/docs](http://localhost:8000/docs)。

6. **设置监控**:
   - **Prometheus**: 请确保已经配置好 Prometheus，并在 `prometheus.yml` 中添加 FastAPI 应用的监控目标（例如，`http://localhost:8000/metrics`）。
   - **Grafana**: 安装 Grafana，并创建新的仪表盘来可视化 Prometheus 监控的数据。

## 后续扩展

- 根据具体业务需求，可以在此基础上添加新的 API 路由、数据库模型和其他功能。
- 可集成更多中间件，如请求日志、CORS、速率限制等。
- 通过增加更多的监控指标和告警机制，增强应用的可观察性。

## 贡献

欢迎任何形式的贡献！如有疑问或建议，请通过 Issue 与我们联系。

## 日志规范

为保证整个项目的日志一致、清晰、可检索，请统一遵循如下规范：

- 组件日志器：使用 `get_logger("<COMP>")` 获取带组件标识的日志器（如 `HTTP`、`APP`、`DB`）。
- 键值对格式：使用 `kv(...)` 将关键字段以 `key=value` 形式输出，避免自由文本。
- 消息前缀：统一使用 `▶ START`（开始）、`✔ DONE`（完成）、`✖ ERROR`（错误）。
- 日志级别：
  - `INFO`：正常请求开始与完成（状态码 < 400）。
  - `WARNING`：客户端错误（4xx）。
  - `ERROR`：服务端错误（5xx）或异常。
- 禁止敏感信息：不得记录 `Authorization`、`Cookie`、密钥或个人敏感数据。
- 结构化扩展：必要时通过 `extra={...}` 增加结构化字段，便于采集与分析。

### 使用方式

```python
from app.utils import get_logger, kv

http_logger = get_logger("HTTP")

# 请求开始
http_logger.info(
    "▶ START " + kv(rid=rid, method=request.method, path=request.url.path, ip=client_ip, ua=request.headers.get("user-agent")),
    extra={
        "type": "request_start",
        "request_id": rid,
        "method": request.method,
        "path": request.url.path,
    },
)

# 请求完成
http_logger.log(
    log_level,  # INFO / WARNING / ERROR 依据状态码
    "✔ DONE " + kv(rid=rid, method=request.method, path=request.url.path, status=response.status_code, latency_ms=latency_ms, size=response_size, ip=client_ip),
    extra={
        "type": "request_complete",
        "request_id": rid,
        "status_code": response.status_code,
        "latency_ms": latency_ms,
    },
)

# 请求异常
http_logger.error(
    "✖ ERROR " + kv(rid=rid, method=request.method, path=request.url.path, err=str(exc), latency_ms=latency_ms, ip=client_ip),
    extra={
        "type": "request_error",
        "request_id": rid,
        "error": str(exc),
    },
    exc_info=True,
)
```

### 命名建议

- 组件标识：`APP`（应用生命周期）、`HTTP`（HTTP中间件/路由）、`DB`（数据库）、`TASK`（异步任务）、`AUTH`（认证）。
- 关键字段：`rid`、`method`、`path`、`status`、`latency_ms`、`size`、`ip`、`ua` 等。

### 采集与监控

- 输出：日志默认打印到控制台并写入 `logs/` 目录（见 `app/utils/logger_config.py`）。
- 检索：推荐使用 `ripgrep`/`grep` 按 `COMP` 或键值过滤，如 `COMP=HTTP status=500`。
- 聚合：后续可集成 ELK/Vector/Loki，将 kv 字段作为索引，便于告警与看板展示。

### 贡献者须知

- 新增模块请按上述规范选择组件标识并使用 `get_logger("<COMP>") + kv(...)`。
- 保持英文消息与统一键名，避免混用大小写或自由文本。
- 不记录敏感信息；如需调试，可在本地临时开启更高日志级别，但勿提交到仓库。
