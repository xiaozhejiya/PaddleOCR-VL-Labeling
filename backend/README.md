# K12 后端（M0-M3 基线）

本后端工程当前包含 `M0`、`M1`、`M2` 和 `M3` 阶段的可运行基线，定义见：

```text
doc/开发文档/mvp_implementation_plan.md
```

## 已包含内容

- FastAPI 入口：`app/main.py`
- V1 路由：`app/api/v1/router.py`
- 健康检查接口：`GET /api/v1/health`
- 配置加载：`app/core/config.py`
- SQLAlchemy session：`app/db/session.py`
- 数据库和 Redis 健康检查：`app/core/health.py`
- Celery app：`app/workers/celery_app.py`
- 测试任务：`debug_ping`
- SQLAlchemy 核心模型：`app/db/models/core.py`
- Alembic migration：`alembic/versions/20260603_0001_create_core_tables.py`
- 最小 repository：`app/repositories/roles.py`
- 文件上传与只读归档：`POST /api/v1/projects/{project_id}/assets/upload`
- M3 兼容上传入口：`POST /api/v1/assets/upload`
- 依赖文件：
  - `requirements.txt`
  - `requirements-dev.txt`
- 环境变量模板：`.env.example`

## 快速开始

```powershell
cd E:\code\python\K12
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r backend\requirements.txt
pip install -r backend\requirements-dev.txt
```

## 配置 .env

```powershell
cd E:\code\python\K12\backend
copy .env.example .env
```

编辑 `.env`，替换所有 `<REPLACE_WITH_...>` 占位符。

## 启动 API

```powershell
cd E:\code\python\K12\backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## 启动 Celery Worker

```powershell
cd E:\code\python\K12\backend
python -m celery -A app.workers.celery_app worker --pool=solo --loglevel=INFO
```

## 执行 debug_ping 任务

```powershell
cd E:\code\python\K12\backend
python -c "from app.workers.tasks.debug import debug_ping; print(debug_ping.apply().get())"
```

## 数据库初始化 SQL（管理员）

数据库账号和授权脚本位于：

```text
backend/sql/admin
```

执行顺序见：

```text
backend/sql/admin/README.md
```

安全说明：

```text
1. .env.example 仅为模板，不提供可直接使用的默认密码。
2. SQL 脚本不内置默认密码，必须在执行时显式传入。
3. 禁止把真实密码提交到 Git 仓库。
```

## M2 数据库 migration

M2 的 DDL 必须使用 `annotation_migrator` 这类迁移账号执行，不要使用 `.env` 中的 `annotation_app` 运行账号执行建表。

```powershell
cd E:\code\python\K12\backend
$env:MIGRATOR_DATABASE_URL = "postgresql+psycopg://annotation_migrator:<你的迁移账号密码>@127.0.0.1:5432/annotation_platform"
python -m alembic upgrade head
```

回滚检查：

```powershell
cd E:\code\python\K12\backend
python -m alembic downgrade base
python -m alembic upgrade head
```

如果只是人工审阅或一次性初始化，也可以参考：

```text
backend/sql/schema/001_create_core_tables.sql
```

## M1 验收检查

1. 健康检查：

```powershell
curl http://127.0.0.1:8000/api/v1/health
```

期望返回：

```json
{"status":"ok","database":{"status":"ok"},"redis":{"status":"ok"}}
```

如果 `.env` 未配置或占位符未替换，健康检查会返回 `not_configured`。

2. OpenAPI 页面：

```text
http://127.0.0.1:8000/docs
```

## M3 图片上传验收

M3 当前支持单页图片直接导入；PDF 渲染属于后续 worker 任务能力，暂不在同步上传接口中处理。

规范入口：

```powershell
$LOGIN = curl -X POST "http://127.0.0.1:8000/api/v1/auth/login" `
  -H "Content-Type: application/json" `
  -d "{\"username\":\"<你的用户名>\",\"password\":\"<你的密码>\"}"

$TOKEN = ($LOGIN | ConvertFrom-Json).access_token

curl -X POST "http://127.0.0.1:8000/api/v1/projects/1/assets/upload" `
  -H "Authorization: Bearer $TOKEN" `
  -F "file=@E:\path\to\paper.png"
```

兼容 MVP 任务清单的入口：

```powershell
curl -X POST "http://127.0.0.1:8000/api/v1/assets/upload" `
  -H "Authorization: Bearer $TOKEN" `
  -F "project_id=1" `
  -F "file=@E:\path\to\paper.png"
```

成功后返回 `asset_id`、`document_id` 和 `page_id`。文件会写入 `STORAGE_ROOT/raw/assets/<sha256前两位>/`，数据库 `assets` 表记录 `sha256`、`size_bytes`、`mime_type` 和相对 `storage_path`。重复上传相同 sha256 文件会复用已有 asset，不覆盖 raw 原始文件。

上传接口使用 `Authorization: Bearer <token>` 鉴权，并要求当前用户在项目内具备 `can_upload_assets` capability。
