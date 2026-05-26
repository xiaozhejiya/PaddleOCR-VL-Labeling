# 文档标注平台后端开发规范

版本：v0.5
日期：2026-05-26  
参考：

```text
doc/开发文档/后端/k12_annotation_platform_backend_design.md
doc/开发文档/k12_annotation_platform_design.md
doc/PaddleOCR技术文档/paddleocr_vl_official_reference.md
```

## 目录

- 版本记录
- 1. 目标与边界
- 2. 技术栈
  - 2.1 运行环境
  - 2.2 推荐核心依赖
- 3. 依赖文件规范
- 4. 项目目录结构
- 5. 配置规范
- 6. 数据库开发规范
  - 6.1 ORM
  - 6.2 Alembic
  - 6.3 命名规范
  - 6.4 字段说明规范
  - 6.5 数据库注释
  - 6.6 业务表边界
- 7. API 开发规范
  - 7.1 路径规范
  - 7.2 响应规范
  - 7.3 HTTP 状态码
  - 7.4 OpenAPI
- 8. 标注数据开发规范
  - 8.1 Revision 模式
  - 8.2 几何字段
  - 8.3 标签命名空间
  - 8.4 关系对象
- 9. 文件存储规范
  - 9.1 不可变资产
  - 9.2 写入流程
  - 9.3 路径规范
- 10. 后台任务规范
- 11. 质检开发规范
- 12. 导出器开发规范
- 13. 日志与错误处理
- 14. 安全规范
  - 14.1 鉴权
  - 14.2 传输加密与防抓包
  - 14.3 存储加密与私有数据保护
  - 14.4 SQL 注入防护
  - 14.5 文件安全
  - 14.6 日志与脱敏
  - 14.7 接口防护
  - 14.8 Redis 与任务队列安全
  - 14.9 加密体系分层
  - 14.10 当前必须实现的加密与完整性措施
  - 14.11 MVP 后应实现的加密措施
  - 14.12 生产化可选增强
  - 14.13 信封加密规范
  - 14.14 Signed URL / 请求签名规范
  - 14.15 审计日志哈希链
  - 14.16 密钥管理与轮换
- 15. 测试规范
  - 15.1 单元测试
  - 15.2 集成测试
  - 15.3 测试工具
- 16. 代码风格
  - 16.1 Python
  - 16.2 格式化
  - 16.3 命名
- 17. 本地开发流程
  - 17.1 准备环境
  - 17.2 启动依赖
  - 17.3 数据库迁移
  - 17.4 启动 API
  - 17.5 启动 Worker
- 18. Git 提交规范
- 19. 工程落地检查项
- 20. 关键结论

---

## 版本记录

| 版本 | 日期 | 说明 |
|---|---|---|
| v0.1 | 2026-05-25 | 初版后端开发规范，定义技术栈、目录结构、配置、数据库、API、任务、质检、导出、测试和代码风格。 |
| v0.2 | 2026-05-26 | 删除无关项目依赖说明；补充字段中文说明规范；强化私有数据保护、传输加密、存储加密、SQL 注入防护、日志脱敏和接口安全要求。 |
| v0.3 | 2026-05-26 | 补充加密工程方案：TLS、签名 URL、HMAC 请求签名、文件哈希、导出 manifest 签名、信封加密、KMS/Vault、审计日志哈希链和密钥轮换。 |
| v0.4 | 2026-05-26 | 明确开发规范边界：保留技术栈、依赖、代码规范、安全规范和加密规范；业务架构、表、API、流程和模块设计以后端设计文档为准。 |
| v0.5 | 2026-05-26 | 补充角色与权限实现规范：后端基于 user_id + project_id 计算 capabilities，角色变更必须审计，前端角色仅作展示。 |

---

## 1. 目标与边界

本文定义文档数据采集与标注平台后端开发规范，包括技术栈、目录结构、依赖管理、配置、数据库开发方式、API 开发方式、异步任务、文件存储、测试、代码风格、安全规范和加密规范。

本文不维护完整业务架构、完整业务表结构、完整 API 清单、场景流程和验收拆分；这些内容以后端设计文档为准：

```text
doc/开发文档/后端/k12_annotation_platform_backend_design.md
```

本规范中的表名、字段名、接口路径、导出类型或场景名称，只作为命名、编码、安全和测试约束的示例或引用，不作为新的业务设计来源。

---

## 2. 技术栈

### 2.1 运行环境

```text
Python: 3.11.x
OS: Windows 本地开发，后续可容器化部署
Database: PostgreSQL 18+
Cache / Queue Broker: Redis
API Framework: FastAPI
ORM: SQLAlchemy 2.x
Migration: Alembic
Validation: Pydantic 2.x
Background Jobs: Celery + Redis
File Storage: 本地文件系统，预留 MinIO / S3 适配
Testing: pytest
```

### 2.2 推荐核心依赖

建议后端 MVP 使用：

```text
fastapi
uvicorn[standard]
pydantic
pydantic-settings
sqlalchemy
alembic
psycopg[binary]
redis
celery
python-dotenv
python-multipart
orjson
rich
requests
aiohttp
tqdm
opencv-python
Pillow
pdf2image
numpy
pytest
pytest-asyncio
httpx
```

建议开发工具：

```text
ruff
black
mypy
pre-commit
```

说明：

```text
1. FastAPI 负责 HTTP API 和 OpenAPI 文档。
2. SQLAlchemy 2.x 使用 typed declarative style。
3. Alembic 管理所有数据库 schema 变更。
4. Celery 负责 PaddleOCR-VL 预标注、导出、质检、报告生成等长任务。
5. Redis 仅作缓存和任务队列，不保存关键业务事实。
6. PostgreSQL 是业务状态、索引、权限、任务记录的唯一数据库。
```

---

## 3. 依赖文件规范

推荐使用 `pyproject.toml` 作为主依赖声明，必要时导出 `requirements.txt`。

MVP 可先使用：

```text
backend/requirements.txt
backend/requirements-dev.txt
```

后续稳定后迁移到：

```text
backend/pyproject.toml
backend/uv.lock 或 poetry.lock
```

依赖分组：

```text
core
  FastAPI、Pydantic、SQLAlchemy、Alembic、Redis、Celery

media
  Pillow、opencv-python、pdf2image、numpy

dev
  pytest、httpx、ruff、black、mypy

optional-ai
  openai、langchain、langgraph 等，默认不安装
```

禁止：

```text
1. 直接把另一个项目 requirements.txt 全量复制过来。
2. 把 Agent / LLM 依赖放进核心后端依赖。
3. 在代码里硬编码数据库密码、Redis 密码、文件路径。
4. 不经过 Alembic 手工改数据库结构。
```

依赖引入原则：

```text
1. 只引入当前平台确实需要的依赖。
2. 每个新增依赖必须说明用途、使用范围和是否进入生产环境。
3. 能由标准库或已有依赖清晰完成的功能，不新增重复依赖。
4. AI / Agent / LLM 相关依赖默认不进入核心后端，只能作为独立可选模块。
```

---

## 4. 项目目录结构

推荐后端目录：

```text
backend/
  app/
    main.py
    api/
      v1/
        router.py
        endpoints/
          auth.py
          projects.py
          documents.py
          pages.py
          annotations.py
          paddleocr_runs.py
          qc.py
          exports.py
          jobs.py
    core/
      config.py
      logging.py
      security.py
      errors.py
      constants.py
    db/
      base.py
      session.py
      models/
        asset.py
        project.py
        document.py
        page.py
        annotation.py
        label_registry.py
        relation_registry.py
        qc.py
        export.py
        job.py
    schemas/
      asset.py
      project.py
      document.py
      page.py
      annotation.py
      geometry.py
      qc.py
      export.py
      job.py
    repositories/
      assets.py
      documents.py
      annotations.py
      jobs.py
    services/
      asset_service.py
      annotation_service.py
      paddleocr_service.py
      qc_service.py
      export_service.py
    workers/
      celery_app.py
      tasks/
        paddleocr_tasks.py
        qc_tasks.py
        export_tasks.py
        backup_tasks.py
    storage/
      local.py
      base.py
      checksums.py
    qc/
      base.py
      schema_rules.py
      geometry_rules.py
      dataset_rules.py
      scenario_rules.py
    exporters/
      base.py
      pp_doclayout_v3.py
      annotation_json.py
      element_table.py
      statistics_report.py
    scenarios/
      k12/
        labels.json
        relations.json
        qc_rules.py
        exporters.py
    utils/
      ids.py
      time.py
      geometry.py
      json_io.py
  alembic/
  tests/
    unit/
    integration/
  requirements.txt
  requirements-dev.txt
.env.example
README.md
```

约束：

```text
api 层只处理 HTTP 请求/响应。
service 层处理业务流程。
repository 层处理数据库读写。
exporter / qc / storage 作为独立模块，不直接依赖 API。
worker task 调用 service，不直接写散落逻辑。
```

每个目录应在 README 或开发文档中说明用途，避免仅靠英文目录名理解职责。例如：

```text
services/
  中文说明：业务服务层。负责组织完整业务流程，例如创建标注版本、触发质检、创建导出任务。

repositories/
  中文说明：数据库访问层。只封装查询和持久化，不写跨模块业务流程。

exporters/
  中文说明：导出器。负责把平台主数据转换为目标训练或交付格式。
```

---

## 5. 配置规范

使用 `pydantic-settings` 加载配置。

配置来源优先级：

```text
环境变量
.env
默认值
```

`.env.example` 必须包含：

```env
APP_ENV=dev
APP_NAME=document-annotation-platform
API_PREFIX=/api/v1

DATABASE_URL=postgresql+psycopg://annotation:annotation@127.0.0.1:5432/annotation_platform
REDIS_URL=redis://:123456@127.0.0.1:6379/0
CELERY_BROKER_URL=redis://:123456@127.0.0.1:6379/1
CELERY_RESULT_BACKEND=redis://:123456@127.0.0.1:6379/2

STORAGE_ROOT=E:/code/python/K12/data
MAX_UPLOAD_MB=200

JWT_SECRET_KEY=change-me
JWT_EXPIRE_MINUTES=1440

PADDLEOCR_VL_ENABLED=false
PADDLEOCR_VL_MODEL_DIR=
```

禁止：

```text
1. 真实密码提交到 Git。
2. 在代码里写死 Redis 密码。
3. 在代码里写死 PostgreSQL 密码。
4. 生产配置复用本地开发密钥。
```

---

## 6. 数据库开发规范

### 6.1 ORM

使用 SQLAlchemy 2.x。

要求：

```text
1. 所有表必须有 id、created_at、updated_at。
2. 软删除使用 deleted_at，不直接物理删除关键业务数据。
3. JSON 字段统一使用 JSONB。
4. 枚举字段使用字符串枚举，不使用魔法数字。
5. 外键关系必须明确。
6. 写操作必须在事务中完成。
7. 每个表和关键字段必须有中文业务说明。
```

### 6.2 Alembic

规则：

```text
1. 所有 schema 变更必须生成 Alembic migration。
2. migration 文件名要说明变更目的。
3. migration 必须可升级、可回滚。
4. 禁止直接手工改数据库结构后不提交 migration。
```

### 6.3 命名规范

```text
表名：复数 snake_case，例如 annotation_revisions
字段名：snake_case
索引名：ix_<table>_<columns>
唯一约束：uq_<table>_<columns>
外键：fk_<table>_<column>_<ref_table>
```

命名要求：

```text
1. 代码和数据库字段可以使用英文 snake_case，但不能只有英文名字。
2. 所有对外 API schema、数据库表、枚举值、配置项都必须补充中文说明。
3. 字段说明必须描述业务含义、数据来源、是否必填、单位/格式、示例值和安全级别。
4. 容易产生歧义的字段必须在文档中给出反例或边界说明。
```

### 6.4 字段说明规范

每个字段至少需要维护以下说明：

```text
field_name        英文字段名，例如 document_id
display_name      中文展示名，例如 文档编号
description       业务含义，说明这个字段解决什么问题
source            数据来源，例如 系统生成 / 用户填写 / 模型输出 / 导出器生成
required          是否必填
type              数据类型
format            格式要求，例如 UUID、ISO8601、bbox_xyxy
example           示例值
sensitivity       数据敏感级别：public / internal / sensitive / secret
validation        校验规则
```

示例：

```json
{
  "field_name": "document_id",
  "display_name": "文档编号",
  "description": "平台内部生成的文档唯一标识，用于关联页面、标注版本、导出记录和质检结果。不是原始文件名，也不应暴露为业务来源证明。",
  "source": "system_generated",
  "required": true,
  "type": "string",
  "format": "doc_<short_id>",
  "example": "doc_001",
  "sensitivity": "internal",
  "validation": "同一项目内唯一"
}
```

几何字段必须给出坐标系说明：

```text
bbox_xyxy
  中文名：轴对齐矩形框
  含义：页面图像坐标系中的矩形区域。
  格式：[xmin, ymin, xmax, ymax]
  单位：像素
  边界：xmin < xmax, ymin < ymax，坐标不得超出图像宽高。

quad
  中文名：四点区域
  含义：用于表达倾斜或透视区域的四边形。
  格式：[[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
  边界：点序必须可解释，面积必须大于 0。

polygon
  中文名：多边形轮廓
  含义：用于表达实例分割轮廓，可由 bbox 或 quad 自动生成。
  格式：[[x1,y1], [x2,y2], ...]
  边界：至少 3 个点，不能越界。
```

### 6.5 数据库注释

数据库 migration 中应为核心表和字段写入注释。PostgreSQL 可使用：

```sql
COMMENT ON TABLE annotation_revisions IS '标注版本表：保存每次页面标注提交形成的不可变版本记录';
COMMENT ON COLUMN annotation_revisions.revision_no IS '标注版本号：同一页面内递增，回滚也创建新版本';
```

### 6.6 业务表边界

本规范不重复维护核心业务表清单。表结构、字段含义、索引、约束和表间关系以后端设计文档的“核心数据库表”为准。

本节只要求数据库实现满足：有 migration、有字段中文说明、有主键和外键约束、有必要索引、有审计字段、有敏感级别标注。

---

## 7. API 开发规范

### 7.1 路径规范

API 统一前缀：

```text
/api/v1
```

示例：

```text
GET  /api/v1/projects
POST /api/v1/projects
GET  /api/v1/documents/{document_id}
GET  /api/v1/pages/{page_id}/annotation/latest
POST /api/v1/pages/{page_id}/annotation/revisions
POST /api/v1/projects/{project_id}/exports
```

### 7.2 响应规范

成功响应：

```json
{
  "data": {},
  "request_id": "req_..."
}
```

分页响应：

```json
{
  "data": [],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total": 100
  },
  "request_id": "req_..."
}
```

错误响应：

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid annotation geometry",
    "details": {}
  },
  "request_id": "req_..."
}
```

### 7.3 HTTP 状态码

```text
200 成功
201 创建成功
400 请求参数错误
401 未登录
403 无权限
404 资源不存在
409 revision 冲突或锁定冲突
422 schema 校验失败
500 服务端错误
```

### 7.4 OpenAPI

要求：

```text
1. 每个 endpoint 必须声明 response_model。
2. 每个 schema 必须有清晰字段说明，且必须包含中文 display_name / description。
3. 不向前端暴露内部 traceback。
4. OpenAPI 文档必须能本地访问。
```

Pydantic 字段示例：

```python
from pydantic import BaseModel, Field


class DocumentRead(BaseModel):
    document_id: str = Field(
        ...,
        title="文档编号",
        description="平台内部生成的文档唯一标识，用于关联页面、标注版本、质检结果和导出记录。",
        examples=["doc_001"],
    )
```

API 文档要求：

```text
1. 列表筛选字段必须说明筛选语义。
2. 排序字段必须说明允许的字段白名单。
3. 枚举值必须给出中文含义。
4. 坐标字段必须说明坐标系、单位和边界。
5. 安全敏感字段必须说明是否会被脱敏返回。
```

---

## 8. 标注数据开发规范

### 8.1 Revision 模式

标注保存采用 revision 模式：

```text
每次保存创建新 annotation_revision。
历史 revision 不覆盖、不删除。
latest 只是当前指针。
回滚创建新 revision，不直接恢复覆盖。
```

### 8.2 几何字段

标注对象必须支持：

```text
bbox_xyxy
quad
polygon
mask_ref
```

MVP 可以只让前端画 bbox，后端或前端自动生成矩形 `quad` 和 `polygon`。

### 8.3 标签命名空间

内置官方 layout 标签：

```text
paddle.layout.*
```

场景标签：

```text
k12.*
medical.*
invoice.*
contract.*
```

禁止把场景标签写死在平台核心逻辑中。

### 8.4 关系对象

关系统一使用：

```text
rel_id
relation_type
from_ann_id
to_ann_id
attributes
status
```

具体关系类型由 `relation_registry` 和 `scenario_profile` 定义。

---

## 9. 文件存储规范

### 9.1 不可变资产

以下文件只追加，不覆盖：

```text
原始 PDF / 图片
PaddleOCR-VL res.json
PaddleOCR-VL markdown
PaddleOCR-VL visualization
PP-DocLayoutV3 candidate json
annotation revision json
export package
backup snapshot
```

### 9.2 写入流程

```text
1. 写临时文件。
2. 计算 sha256。
3. 原子移动到目标路径。
4. 写入 assets 表。
5. 写入 checksum 记录。
```

### 9.3 路径规范

所有存储路径必须相对 `STORAGE_ROOT` 生成，不允许任意路径写入。

禁止：

```text
1. 接收前端传入路径后直接写文件。
2. 在 API 层拼接不受控路径。
3. 覆盖 raw asset。
4. 删除历史 revision 文件。
```

---

## 10. 后台任务规范

所有长任务必须进入队列：

```text
PaddleOCR-VL 预标注
PDF 渲染
QC 批处理
PP-DocLayoutV3 导出
统计报告生成
overlay 生成
备份
```

任务记录必须包含：

```text
job_id
job_type
status
payload_json
result_json
progress
error_message
created_by
created_at
started_at
finished_at
```

任务状态：

```text
queued
running
succeeded
failed
canceled
```

Celery 任务要求：

```text
1. 可重试任务必须幂等。
2. 输出目录使用唯一 job_id / export_id。
3. 失败任务保留中间日志和错误摘要。
4. 任务不直接返回大对象，只返回 artifact 路径和统计结果。
```

---

## 11. 质检开发规范

QC 引擎分为：

```text
schema QC
geometry QC
dataset QC
export QC
scenario QC
```

平台核心提供通用执行框架：

```python
class QCRule:
    rule_id: str
    severity: str

    def check(self, context):
        ...
```

场景规则通过 `scenario_profile` 注册。

禁止：

```text
1. 在通用 QC 模块里硬编码特定业务场景规则。
2. 在导出器里临时绕过 QC。
3. QC 失败仍默认生成训练集。
```

---

## 12. 导出器开发规范

导出器统一接口：

```python
class Exporter:
    export_type: str

    def validate_scope(self, scope): ...
    def collect_inputs(self, scope): ...
    def validate_inputs(self, inputs): ...
    def export(self, inputs, output_dir): ...
    def write_report(self, output_dir): ...
```

核心导出器：

```text
pp_doclayout_v3
annotation_json
element_table
statistics_report
```

场景导出器通过 `scenario_profile` 注册，具体类型由后端设计文档或对应场景扩展文档定义。

PP-DocLayoutV3 导出必须生成：

```text
images/
images_mask/
annotations/instance_train.json
annotations/instance_val.json
export_config.json
export_report.md
```

并检查：

```text
category_id 稳定
bbox 为 COCO [x, y, width, height]
segmentation 非空
read_order 连续
split 不泄漏
```

---

## 13. 日志与错误处理

日志格式：

```json
{
  "timestamp": "...",
  "level": "INFO",
  "request_id": "req_...",
  "user_id": "user_...",
  "event": "annotation_revision_created",
  "message": "...",
  "extra": {}
}
```

要求：

```text
1. 每个请求生成 request_id。
2. 后台任务生成 job_id。
3. 错误日志不泄露密码。
4. API 返回错误码和用户可读 message。
5. traceback 只进服务端日志。
```

---

## 14. 安全规范

平台处理的原始文档、页面图像、授权材料、标注结果、模型输出和导出数据均属于用户或机构的私有数据资产。安全策略必须按“默认不可信、最小权限、全链路加密、可审计、可回滚”执行。

### 14.1 鉴权

MVP 使用 JWT。

要求：

```text
1. 密码不可明文存储。
2. JWT secret 来自环境变量。
3. 角色权限在后端校验。
4. locked 数据修改必须校验 project_admin 或等价 capability。
5. JWT 必须设置过期时间，禁止长期不过期 token。
6. 刷新 token、退出登录、密码修改后应支持 token 失效。
7. 后续生产环境优先接入组织级 SSO / OAuth2 / OIDC。
```

角色与权限实现要求：

```text
1. 后端不得信任前端传入的 role、capability 或 is_admin 字段。
2. 每个项目内操作都必须基于 authenticated user_id + project_id 计算 capabilities。
3. 项目级权限来自 project_members、member_role_bindings 和 role_registry。
4. system_admin 只用于系统级用户管理和紧急维护，不默认拥有所有项目业务操作。
5. 前端可展示 role_key，但写接口必须以后端 capability 校验为准。
6. 角色授予、撤销、成员禁用、成员移除、锁定、回滚、导出下载必须写 audit_log。
7. 禁用用户或移除成员后，不应破坏历史 created_by、reviewer_id、export created_by 的可追溯性。
8. 权限不足返回 403，不在错误详情中暴露敏感资源是否存在。
```

### 14.2 传输加密与防抓包

要求：

```text
1. 生产环境必须启用 HTTPS/TLS，禁止明文 HTTP 传输私有数据。
2. 内网部署也应启用 TLS，不能默认认为局域网可信。
3. 前端访问 API、文件下载、WebSocket、后台管理接口都必须走 HTTPS。
4. Cookie 必须设置 Secure、HttpOnly、SameSite。
5. JWT 不应存入 localStorage；如使用 Cookie，必须配合 CSRF 防护。
6. 对外下载链接必须使用短期有效的签名 URL 或一次性 token。
7. 严禁在 URL query 中传递密码、访问 token、数据库连接串或敏感文件路径。
8. 本地开发可以使用 HTTP，但必须在 `.env` 中显式标记 APP_ENV=dev。
```

反抓包边界：

```text
TLS 能防止网络链路上的明文抓包。
TLS 不能防止终端机器被控、浏览器插件窃取或用户主动导出数据。
因此还必须配合权限控制、审计日志、水印、下载限制和最小化返回数据。
```

### 14.3 存储加密与私有数据保护

要求：

```text
1. 生产环境数据库磁盘应启用磁盘级加密或云厂商 KMS 加密。
2. 文件存储目录应启用磁盘级加密；对象存储应启用 server-side encryption。
3. 授权文件、原始试卷、页面图像、导出包属于 sensitive 数据。
4. 密码、JWT secret、数据库密码、Redis 密码属于 secret 数据。
5. secret 数据只能存储在环境变量、密钥管理系统或受控配置中。
6. 不允许把真实原始数据、导出包、数据库 dump 提交到 Git。
7. 备份文件必须加密保存，并限制访问权限。
8. 删除数据默认软删除；涉及用户要求销毁时，需要有明确审批和审计记录。
```

敏感级别：

```text
public
  可公开信息，例如接口版本号、公开文档。

internal
  内部业务信息，例如 document_id、page_id、标签配置。

sensitive
  私有业务数据，例如原始图片、标注 JSON、导出数据、授权材料。

secret
  密钥和凭证，例如 JWT_SECRET_KEY、数据库密码、Redis 密码。
```

### 14.4 SQL 注入防护

要求：

```text
1. 所有数据库访问默认使用 SQLAlchemy ORM 或 SQLAlchemy Core 参数化查询。
2. 禁止使用 f-string、字符串拼接、format 构造 SQL。
3. 如必须使用 raw SQL，必须使用 bind parameters，并经过代码审查。
4. 排序字段、筛选字段、表名、列名不能直接来自用户输入，必须走白名单映射。
5. limit / offset / page_size 必须限制最大值。
6. JSONB 查询条件必须经过 schema 校验。
7. 数据库账号使用最小权限，应用账号不得拥有创建超级用户、删除数据库等权限。
8. migration 账号和运行时账号分离。
9. 错误响应不得暴露 SQL 语句、表结构、连接串或数据库错误详情。
```

禁止示例：

```python
query = f"select * from documents where document_id = '{document_id}'"
```

允许示例：

```python
stmt = select(Document).where(Document.document_id == document_id)
result = await session.execute(stmt)
```

排序白名单示例：

```python
SORT_FIELDS = {
    "created_at": Document.created_at,
    "document_id": Document.document_id,
}
sort_column = SORT_FIELDS.get(request.sort_by)
if sort_column is None:
    raise ValidationError("Unsupported sort field")
```

### 14.5 文件安全

```text
1. 上传文件限制大小和类型。
2. 文件名不直接作为存储路径。
3. 禁止路径穿越。
4. 下载接口校验权限。
5. 上传文件必须重新生成 asset_id，不能信任原始文件名。
6. 文件 MIME 类型和扩展名都要校验，不能只看扩展名。
7. 文件下载默认不暴露真实磁盘路径。
8. 导出包必须按权限检查后才能下载。
9. 临时文件必须写入受控临时目录，任务结束后清理。
```

### 14.6 日志与脱敏

```text
1. .env 不提交 Git。
2. .env.example 不包含真实生产密码。
3. 日志不打印 DATABASE_URL / REDIS_URL 完整值。
4. 日志不打印 Authorization header、Cookie、JWT、密码。
5. 日志不打印完整原始文本、完整 OCR 内容或大段标注 JSON。
6. 对 document_id、page_id、user_id 可以记录；对原始文件路径和来源授权信息应谨慎记录。
7. 错误日志中 traceback 只保存在服务端，不返回给前端。
```

### 14.7 接口防护

```text
1. 所有写接口必须鉴权。
2. 重要操作必须校验角色权限，包括锁定、回滚、导出、删除、下载原始数据。
3. 登录、导出、下载、批量任务接口必须有速率限制。
4. 后台管理接口不能暴露到公网。
5. CORS 必须使用明确 origin 白名单，禁止生产环境使用 `*`。
6. 对外返回对象时必须做字段级过滤，不能直接返回 ORM 对象。
7. 需要审计的操作必须写 audit log。
```

### 14.8 Redis 与任务队列安全

```text
1. Redis 必须启用密码，生产环境不得使用弱密码。
2. Redis 只允许内网或本机访问，不暴露公网。
3. Redis 不保存关键业务事实，只保存缓存、队列和短期任务状态。
4. Celery payload 不放置明文 secret 或大体量私有数据。
5. Redis URL 不进入日志。
```

### 14.9 加密体系分层

本平台的数据集、原始文档、页面图像、标注结果、导出包和授权材料都是核心资产。加密方案应采用多层组合，而不是只依赖单一算法。

推荐分层：

```text
传输层
  TLS / HTTPS，防止链路明文抓包。

访问层
  短期 signed URL、HMAC 请求签名、时间戳、nonce，防止未授权访问和重放。

存储层
  文件级加密、数据库加密、备份加密。

密钥层
  KMS / Vault / Key Vault 管理主密钥，应用只拿到受控的数据密钥。

完整性层
  sha256、manifest、数字签名、审计日志哈希链，发现篡改。

权限层
  RBAC、最小权限、导出审批、下载审计。
```

### 14.10 当前必须实现的加密与完整性措施

MVP 阶段必须实现：

```text
1. 生产环境启用 HTTPS/TLS。
2. 所有原始文件、页面图像、标注 revision、导出包计算 sha256。
3. assets 表记录 sha256、size_bytes、mime_type、storage_path。
4. annotation revision 保存后计算 sha256，写入 revision metadata。
5. 导出任务生成 export_manifest.json，记录文件列表、sha256、大小、来源 revision、导出人、导出时间。
6. 文件下载使用短期 download_token，不直接暴露真实文件路径。
7. download_token 必须包含 expires_at，并在服务端校验有效期。
8. 重要写操作记录 audit_log，包括用户、时间、IP、资源、操作类型。
9. 数据库访问使用参数化查询，防止 SQL 注入。
10. 日志脱敏，不记录密钥、token、完整连接串、完整私有文本。
```

`export_manifest.json` 示例：

```json
{
  "export_id": "export_20260526_000001",
  "export_type": "pp_doclayout_v3",
  "created_at": "2026-05-26T10:00:00+08:00",
  "created_by": "user_001",
  "source_revisions": [
    "rev_001",
    "rev_002"
  ],
  "files": [
    {
      "path": "annotations/instance_train.json",
      "sha256": "hex_sha256",
      "size_bytes": 12345
    }
  ],
  "manifest_version": "v1"
}
```

### 14.11 MVP 后应实现的加密措施

MVP 稳定后应增加：

```text
1. 导出 manifest 数字签名。
2. annotation revision 哈希链。
3. audit_log 哈希链。
4. signed URL 支持 HMAC 签名、expires_at、nonce、method、path 参与签名。
5. 备份文件加密。
6. 文件级信封加密。
7. 密钥轮换流程。
8. 导出审批和二次确认。
```

导出包签名文件建议：

```text
export_manifest.json
export_manifest.sha256
export_manifest.sig
public_key.pem，或 signing_key_id
```

签名范围：

```text
1. manifest 内容。
2. 文件 sha256 列表。
3. source_revisions。
4. created_at / created_by。
5. export_type。
```

### 14.12 生产化可选增强

生产环境或高价值数据集建议进一步增加：

```text
1. KMS / Vault / Azure Key Vault / 云 KMS 管理主密钥。
2. 信封加密：DEK 加密数据，KMS key 加密 DEK。
3. mTLS 保护内部服务调用。
4. HSM 或云 KMS 托管签名私钥，私钥不落盘。
5. WORM / 不可变备份，防止管理员误删或勒索软件篡改。
6. 数据水印和导出包唯一标识，用于泄漏追踪。
7. 数据库透明加密或磁盘级加密。
8. 对象存储 server-side encryption。
9. 定期密钥轮换和密钥吊销。
10. 安全扫描：依赖漏洞扫描、SAST、DAST、容器镜像扫描。
```

### 14.13 信封加密规范

信封加密用于大文件和导出包。

推荐流程：

```text
1. 为每个文件或每个导出包生成随机 DEK。
2. 使用 DEK 加密文件内容。
3. 使用 KMS / Vault 中的 KEK 加密 DEK。
4. 保存 encrypted_file。
5. 保存 encrypted_dek、key_id、algorithm、nonce、tag、aad。
6. 解密时先向 KMS 请求解密 DEK，再用 DEK 解密文件。
```

推荐算法：

```text
文件内容加密：AES-256-GCM 或 ChaCha20-Poly1305。
哈希：SHA-256。
数字签名：Ed25519 或 RSA-PSS/SHA-256。
请求签名：HMAC-SHA256。
密码哈希：Argon2id 或 bcrypt，不使用普通 hash 存密码。
随机数：使用操作系统 CSPRNG。
```

禁止：

```text
1. 自己设计加密算法。
2. 使用 ECB 模式。
3. 重复使用同一个 nonce。
4. 把 DEK 和密文放在同一处且不加保护。
5. 把 KMS 主密钥写入 .env。
6. 在日志中打印明文密钥、DEK、签名私钥。
```

加密元数据示例：

```json
{
  "encryption": {
    "algorithm": "AES-256-GCM",
    "key_strategy": "envelope",
    "key_id": "kms_key_dataset_v1",
    "encrypted_dek": "base64...",
    "nonce": "base64...",
    "tag": "base64...",
    "aad": {
      "asset_id": "asset_001",
      "revision_id": "rev_001"
    }
  }
}
```

### 14.14 Signed URL / 请求签名规范

下载、上传、导出包访问应使用短期签名。

签名载荷建议：

```text
method
path
resource_id
user_id
expires_at
nonce
content_sha256，可选
```

签名流程：

```text
1. 服务端生成待签名字符串 canonical_request。
2. 使用 HMAC-SHA256 或私钥签名生成 signature。
3. 返回 token / signed URL。
4. 客户端请求时携带 signature、expires_at、nonce。
5. 服务端校验过期时间、nonce 是否重复、用户权限、签名是否匹配。
```

要求：

```text
1. signed URL 默认有效期不超过 10 分钟。
2. 高敏感导出包可设置一次性 token，下载成功后立即失效。
3. nonce 需要短期缓存，防止重放。
4. 删除、导出、批量下载等危险操作不得只依赖 signed URL，还要校验用户会话和权限。
```

### 14.15 审计日志哈希链

审计日志用于追踪私有数据访问和导出行为，应具备篡改发现能力。

每条审计日志保存：

```text
audit_id
created_at
actor_id
action
resource_type
resource_id
request_id
ip
user_agent
details_json
prev_hash
entry_hash
```

哈希计算：

```text
entry_hash = sha256(canonical_json(entry_without_entry_hash) + prev_hash)
```

要求：

```text
1. audit_log 只追加，不更新。
2. 删除或修改审计日志必须被禁止。
3. 定期生成 audit digest。
4. audit digest 可以进一步做数字签名。
5. 导出和原始数据下载必须写 audit_log。
```

### 14.16 密钥管理与轮换

密钥分类：

```text
JWT signing key
download token signing key
export manifest signing key
file encryption KEK
database password
Redis password
backup encryption key
```

要求：

```text
1. 每类密钥使用不同 key，不复用。
2. 密钥必须有 key_id、created_at、status、purpose。
3. 密钥状态至少包括 active、retired、revoked。
4. 新数据使用 active key。
5. retired key 只允许解密/验签历史数据，不允许加密/签名新数据。
6. revoked key 需要触发风险排查和数据重新加密计划。
7. 密钥轮换必须有操作记录和回滚方案。
```

---

## 15. 测试规范

### 15.1 单元测试

覆盖：

```text
geometry utils
schema validation
QC rules
exporters
storage path generation
revision creation
```

### 15.2 集成测试

覆盖：

```text
API 创建项目
上传文件
创建 document/page
保存 annotation revision
运行 QC
创建导出任务
生成 PP-DocLayoutV3 数据
```

### 15.3 测试工具

```text
pytest
pytest-asyncio
httpx
temporary PostgreSQL database
temporary Redis database
temporary storage root
```

要求：

```text
1. 新增 service/exporter/qc 逻辑必须有测试。
2. 导出器必须测试输出文件结构和 JSON schema。
3. 禁止测试依赖真实生产数据路径。
```

---

## 16. 代码风格

### 16.1 Python

```text
1. 使用类型标注。
2. 函数不超过合理长度，复杂逻辑拆 service。
3. API schema 与 DB model 分离。
4. 禁止在 endpoint 中写复杂业务逻辑。
5. 禁止裸 except 后吞异常。
```

### 16.2 格式化

建议：

```text
ruff check backend/app backend/tests
black backend/app backend/tests
mypy backend/app
pytest backend/tests
```

### 16.3 命名

```text
文件：snake_case.py
类：PascalCase
函数：snake_case
常量：UPPER_SNAKE_CASE
数据库表：snake_case plural
API 路径：kebab-case 或 snake_case 统一，推荐 kebab-case
```

---

## 17. 本地开发流程

### 17.1 准备环境

```powershell
cd E:\code\python\K12
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r backend\requirements.txt
pip install -r backend\requirements-dev.txt
```

### 17.2 启动依赖

Redis 当前本机服务：

```powershell
Get-Service Redis
redis-cli -a 123456 ping
```

PostgreSQL 启动后应验证：

```powershell
psql --version
pg_isready -h 127.0.0.1 -p 5432
```

### 17.3 数据库迁移

```powershell
cd backend
alembic upgrade head
```

### 17.4 启动 API

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 17.5 启动 Worker

```powershell
celery -A app.workers.celery_app worker --loglevel=INFO
```

---

## 18. Git 提交规范

提交前至少运行：

```powershell
ruff check backend/app backend/tests
pytest backend/tests
```

提交信息建议：

```text
feat: add annotation revision API
fix: validate polygon bounds before export
docs: add backend development spec
test: cover PP-DocLayoutV3 exporter
refactor: split annotation service
```

禁止：

```text
1. 提交 .env。
2. 提交真实上传数据。
3. 提交临时导出包。
4. 提交 __pycache__、.pytest_cache、日志文件。
```

---

## 19. 工程落地检查项

第一步先创建后端骨架：

```text
backend/
  app/
  alembic/
  tests/
  requirements.txt
  requirements-dev.txt
  .env.example
```

第二步验证工程基础能力：

```text
1. Settings 配置加载。
2. PostgreSQL 连接。
3. Redis 连接。
4. Alembic migration 可执行。
5. API 健康检查可访问。
6. Celery worker 可启动并执行测试任务。
7. 日志、配置、测试、格式化工具可运行。
```

第三步再按后端设计文档实现业务模块：

```text
架构
核心表
API
业务流程
质检流程
导出流程
```

---

## 20. 关键结论

本平台后端以 FastAPI、PostgreSQL、Redis、SQLAlchemy、Alembic、Pydantic、Celery 为核心技术栈。

依赖选择必须以当前平台需求为准，不从其他项目继承无关技术栈。AI / Agent / LLM 类依赖默认不进入核心后端。

后端必须保持通用平台能力，特定行业或业务只作为场景扩展实现。核心逻辑不得硬编码某个场景的标签、关系、字段或导出格式。

业务架构、场景扩展、核心表、API、流程、模块拆分和 MVP 优先级以后端设计文档为准；本规范只约束工程实现方式。

数据属于用户和机构的私有财产。后端必须把传输加密、存储加密、权限校验、SQL 注入防护、日志脱敏、审计追踪作为基础设计要求，而不是上线前补丁。

所有英文表名、字段名、枚举值和配置项都必须配套中文说明、业务含义、示例、校验规则和敏感级别，避免仅凭英文名称理解产生歧义。
