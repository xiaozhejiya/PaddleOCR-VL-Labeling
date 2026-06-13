# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 目录

- 1. 定位与优先级
- 2. 项目背景
- 3. 技术架构
- 4. 常用命令
- 5. Git 提交规范
- 6. 前端开发约定
- 7. 后端开发约定
- 8. 文档导航

## 1. 定位与优先级

```text
1. 本文件是 Claude Code 的快捷入口，帮助快速定位项目背景、常用命令和文档入口。
2. 仓库级 agent 总入口仍是 AGENTS.md。
3. 具体任务应继续按 AGENTS.md 指向的二级 INDEX.md 和详细规范文档展开。
4. 如果本文件与详细规范冲突，以对应 INDEX.md 和详细规范文档为准。
5. 本文件不复制详细规则，详细约定只保留文档入口链接。
```

## 项目背景

通用文档数据采集与标注平台。第一个场景是 K12 试卷识别与结构化解析，兼容 PaddleOCR-VL / PP-DocLayoutV3 官方输入输出，同时维护可扩展标注、质检、版本和导出能力。

## 技术架构

```
backend/   Python 3.11 + FastAPI + SQLAlchemy 2.0 + PostgreSQL + Redis + Celery
frontend/  Vue 3 + TypeScript + Vite 7 + Tailwind CSS + vue-i18n
doc/       中文开发文档（前后端规范、MVP 计划、PaddleOCR 技术参考）
```

- 前后端通过 `/api/v1` REST API 通信，开发环境由 Vite proxy 转发到后端 `:8000`
- 数据库 16 张核心表，BIGINT identity 主键，`public_id` 作为外部稳定标识，JSONB 扩展字段
- 标注采用 revision 不可变模式，原始数据只追加不覆盖
- 所有长任务统一走 Celery，Redis 只作缓存和队列

## 常用命令

### 前端（工作目录：`frontend/`）
```bash
npm run dev         # Vite 开发服务器，地址 127.0.0.1:5173
npm run build       # vue-tsc --noEmit && vite build
npm run test        # vitest run
npm run test:watch  # vitest 监听模式
npm run typecheck   # vue-tsc --noEmit
```

### 后端（工作目录：`backend/`，需激活 .venv）
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
python -m celery -A app.workers.celery_app worker --pool=solo --loglevel=INFO
python -m alembic upgrade head
python -m alembic downgrade base
pytest backend/tests
ruff check backend
```

## Git 提交规范

标题格式：`<type>(<scope>): <中文摘要>`

- type：`feat` / `fix` / `docs` / `test` / `refactor` / `chore` / `style` / `perf` / `build` / `ci` / `revert`
- scope：`backend` / `frontend` / `sql` / `docs` / `auth` / `workspace` / `export` 等
- 中文摘要必须具体，禁止"更新代码""修复问题"等空泛描述
- 正文用无序列表，至少包含变更内容和验证结果（执行的命令及结果）
- 前后端、文档、数据库变更应按功能边界拆分提交
- 详细规范见 `doc/开发文档/COMMIT_RULES.md`

示例：
```
fix(backend): 补齐项目角色绑定审计日志

- 在项目角色绑定写入后同步创建 audit_logs 记录
- 补充 repository 单元测试，覆盖系统角色拒绝绑定和项目角色授予审计
- 验证 ruff check backend 和 pytest backend/tests 通过
```

## 前端开发约定

- Vue SFC 使用 `<script setup lang="ts">` + Composition API
- route name 使用点分层级：`auth.login`、`projects.index`、`pages.workspace`
- 受保护路由必须声明 `meta.requiresAuth`，工作台路由声明 `meta.workspaceRoute`
- 所有用户可见文案必须通过 vue-i18n key，不在模板中硬编码中文
- i18n key 使用领域命名空间：`common.save`、`annotation.saveStatus.saved`
- API 请求统一通过 `src/api/` 封装，页面不直接 `fetch`
- 坐标换算必须显式转换，屏幕坐标和页面原始坐标不能混用
- 保存标注必须携带 `base_revision_id`，409 冲突时不能自动覆盖
- 详细规范见 `doc/开发文档/前端/frontend_development_spec.md`

## 后端开发约定

- API 前缀 `/api/v1`，路由定义在 `app/api/v1/`
- ORM 模型在 `app/db/models/`，使用 `DeclarativeBase` + shared mixins
- 配置通过 `app/core/config.py` 的 Pydantic Settings 从 `.env` 加载
- Migration 必须用 `annotation_migrator` 账号执行，不用应用运行账号
- 默认不在应用启动时自动执行 Alembic；如开发环境需启用，设置 `AUTO_MIGRATE_ON_STARTUP=true`，迁移失败会中止启动
- K12 场景特有逻辑放 `app/scenarios/k12/`，核心保持通用
- 详细规范见 `doc/开发文档/后端/backend_development_spec.md`

## 文档导航

不要一次性读取所有文档。按任务类型定位：

| 任务 | 入口 |
|---|---|
| 后端 / 数据库 / API / 权限 | `doc/开发文档/后端/INDEX.md` |
| 前端 / 路由 / 组件 / 工作台 | `doc/开发文档/前端/INDEX.md` |
| PaddleOCR-VL / 训练数据 | `doc/PaddleOCR技术文档/INDEX.md` |
| MVP 阶段和开发顺序 | `doc/开发文档/mvp_implementation_plan.md` |
| 平台功能和标注格式 | `doc/开发文档/k12_annotation_platform_design.md` |

详细文档与 INDEX.md 冲突时，以详细文档为准。
