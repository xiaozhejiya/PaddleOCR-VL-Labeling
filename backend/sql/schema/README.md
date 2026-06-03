# Schema SQL

目录：`backend/sql/schema`

本目录保存数据库结构 SQL 草案，用于 M2 表结构审阅和 Alembic migration 对齐。

正式落库优先使用：

```text
backend/alembic/versions/20260603_0001_create_core_tables.py
```

## 文件

`001_create_core_tables.sql`

包含 M2 首批核心表：

```text
projects
users
role_registry
project_members
member_role_bindings
assets
documents
pages
label_registry
annotation_revisions
annotation_objects
relation_objects
qc_results
background_jobs
export_jobs
audit_logs
```

## 设计约定

```text
1. 内部数据库主键使用 BIGINT identity。
2. 内部外键使用 <entity>_id，例如 document_id / page_id / revision_id。
3. API、文件系统、manifest、审计展示需要的稳定编号统一使用 public_id。
4. JSON 扩展字段使用 JSONB。
5. JSONB 字段应通过 jsonb_typeof 约束 object / array。
6. 每张表都有 created_at / updated_at，普通业务表通过 trigger 自动刷新 updated_at。
7. audit_logs 只允许追加，禁止 UPDATE / DELETE。
8. 核心表和关键字段使用 COMMENT ON 写中文说明。
9. role_registry 内置系统角色和项目角色；member_role_bindings 只能绑定 project scope 角色。
```

## 后续落地

M2 已提供 Alembic migration。后续结构变更应新增 migration，不应直接修改已发布 migration。
