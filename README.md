# enterprise-ai

企业AI能力后端（知识 / 数据 / 内容 / 流程）

基于 **FastAPI + SQLAlchemy + SQLite** 构建的企业级 AI 能力后端，涵盖四大核心模块：

| 模块 | 前缀 | 说明 |
|------|------|------|
| 知识管理 | `/api/v1/knowledge` | 知识库 & 文档 CRUD、全文关键字搜索 |
| 数据管理 | `/api/v1/data` | 数据源、数据集、数据作业管理 |
| 内容管理 | `/api/v1/content` | 内容模板、内容创作与发布 |
| 流程管理 | `/api/v1/process` | 工作流定义、实例运行、任务追踪 |

---

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动服务

```bash
uvicorn main:app --reload
```

服务默认运行在 `http://127.0.0.1:8000`。

### 交互式 API 文档

- Swagger UI：`http://127.0.0.1:8000/docs`
- ReDoc：`http://127.0.0.1:8000/redoc`

---

## 运行测试

```bash
pytest tests/ -v
```

---

## 项目结构

```
enterprise-ai/
├── main.py                   # FastAPI 应用入口
├── requirements.txt
├── app/
│   ├── config.py             # 配置（pydantic-settings）
│   ├── database/
│   │   └── db.py             # SQLAlchemy 引擎 & 会话
│   ├── models/
│   │   ├── knowledge.py      # ORM：知识库 & 文档
│   │   ├── data.py           # ORM：数据源 & 数据集 & 作业
│   │   ├── content.py        # ORM：内容模板 & 内容
│   │   └── process.py        # ORM：工作流 & 实例 & 任务
│   ├── services/
│   │   ├── knowledge_service.py
│   │   ├── data_service.py
│   │   ├── content_service.py
│   │   └── process_service.py
│   └── routers/
│       ├── knowledge.py      # API 路由：知识管理
│       ├── data.py           # API 路由：数据管理
│       ├── content.py        # API 路由：内容管理
│       └── process.py        # API 路由：流程管理
└── tests/
    ├── conftest.py           # pytest fixtures
    ├── test_knowledge.py
    ├── test_data.py
    ├── test_content.py
    └── test_process.py
```

---

## 主要 API 端点

### 知识管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/knowledge/bases` | 列出知识库 |
| POST | `/api/v1/knowledge/bases` | 创建知识库 |
| GET | `/api/v1/knowledge/bases/{id}` | 获取知识库 |
| PUT | `/api/v1/knowledge/bases/{id}` | 更新知识库 |
| DELETE | `/api/v1/knowledge/bases/{id}` | 删除知识库 |
| GET | `/api/v1/knowledge/bases/{id}/documents` | 列出文档 |
| POST | `/api/v1/knowledge/bases/{id}/documents` | 添加文档 |
| GET | `/api/v1/knowledge/search?q=关键词` | 全文搜索 |

### 数据管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | `/api/v1/data/sources` | 数据源列表 / 创建 |
| GET/PUT/DELETE | `/api/v1/data/sources/{id}` | 数据源详情 / 更新 / 删除 |
| GET/POST | `/api/v1/data/sources/{id}/datasets` | 数据集列表 / 创建 |
| GET/POST | `/api/v1/data/datasets/{id}/jobs` | 作业列表 / 创建 |
| PUT | `/api/v1/data/jobs/{id}/status` | 更新作业状态 |

### 内容管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | `/api/v1/content/templates` | 模板列表 / 创建 |
| GET/PUT/DELETE | `/api/v1/content/templates/{id}` | 模板详情 / 更新 / 删除 |
| GET/POST | `/api/v1/content/items` | 内容列表 / 创建 |
| GET/PUT/DELETE | `/api/v1/content/items/{id}` | 内容详情 / 更新 / 删除 |
| POST | `/api/v1/content/items/{id}/publish` | 发布内容 |

### 流程管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | `/api/v1/process/workflows` | 工作流列表 / 创建 |
| GET/PUT/DELETE | `/api/v1/process/workflows/{id}` | 工作流详情 / 更新 / 删除 |
| GET/POST | `/api/v1/process/workflows/{id}/instances` | 实例列表 / 启动 |
| GET | `/api/v1/process/instances/{id}` | 实例详情 |
| PUT | `/api/v1/process/instances/{id}/finish` | 结束实例 |
| GET/POST | `/api/v1/process/instances/{id}/tasks` | 任务列表 / 创建 |
| PUT | `/api/v1/process/tasks/{id}/status` | 更新任务状态 |
