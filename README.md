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

2. **创建虚拟环境** (可选):
    ```bash
    pip install poetry
    source venv/bin/activate  # 在 Linux/MacOS
    venv\Scripts\activate     # 在 Windows
    ```

3. **安装依赖**:
    ```bash
    pip install -r requirements.txt
    ```

4. **运行应用**:
    ```bash
    uvicorn fastapi-app.main:fastapi-app --reload
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
