# 后端文档索引

版本：v0.1
日期：2026-05-27
用途：本文件是后端相关任务的文档入口，只维护后端文档导航和读取路径，不存放详细设计。

## 目录

- 1. 使用原则
- 2. 文档索引
- 3. 常见任务读取路径
- 4. 维护规则

---

## 1. 使用原则

```text
1. 后端任务先读本文件，再打开具体详细文档。
2. 本文件只保留后端读取路径，不复制表结构、API 详情、安全细则或完整流程。
3. 技术栈、依赖、代码规范、安全和加密细节以 backend_development_spec.md 为准。
4. 架构、表、API、流程、模块和导出器设计以 k12_annotation_platform_backend_design.md 为准。
```

---

## 2. 文档索引

| 文档 | 什么时候读 | 内容边界 |
|---|---|---|
| `doc/开发文档/后端/backend_development_spec.md` | 写后端代码、选依赖、建目录、写安全/加密/测试规范 | 技术栈、依赖、代码规范、安全规范、加密规范 |
| `doc/开发文档/后端/k12_annotation_platform_backend_design.md` | 设计或实现后端表、API、流程、模块、导出器 | 架构、表、API、流程、模块设计 |
| `doc/开发文档/mvp_implementation_plan.md` | 判断后端 MVP 开发顺序和验收口径 | MVP 阶段、开发顺序、验收标准 |
| `doc/开发文档/k12_annotation_platform_design.md` | 理解平台主格式、标签关系、版本和导出目标 | 功能设计、主数据格式、标注工作流 |
| `doc/PaddleOCR技术文档/INDEX.md` | 涉及 PaddleOCR-VL / PP-DocLayoutV3 输入输出或导出格式 | OCR/VL 技术参考入口 |

---

## 3. 常见任务读取路径

后端编码任务：

```text
1. doc/开发文档/mvp_implementation_plan.md
2. doc/开发文档/后端/backend_development_spec.md
3. doc/开发文档/后端/k12_annotation_platform_backend_design.md 中对应章节
```

数据库表或 migration 任务：

```text
1. doc/开发文档/后端/k12_annotation_platform_backend_design.md 的核心数据库表章节
2. doc/开发文档/后端/backend_development_spec.md 的数据库开发规范
3. doc/开发文档/mvp_implementation_plan.md 的 M2 / M4 阶段
```

API 任务：

```text
1. doc/开发文档/后端/k12_annotation_platform_backend_design.md 的 API 设计
2. doc/开发文档/后端/backend_development_spec.md 的 API 开发规范
```

权限、角色和审计任务：

```text
1. doc/开发文档/后端/k12_annotation_platform_backend_design.md 的 users / role_registry / project_members / member_role_bindings 表
2. doc/开发文档/后端/k12_annotation_platform_backend_design.md 的权限、锁定、审计章节
3. doc/开发文档/后端/backend_development_spec.md 的鉴权、权限和安全规范
4. doc/开发文档/mvp_implementation_plan.md 的 M4a 角色管理与 capabilities
```

安全和加密任务：

```text
1. doc/开发文档/后端/backend_development_spec.md 的安全规范和加密规范
2. doc/开发文档/后端/k12_annotation_platform_backend_design.md 的权限、备份、恢复和审计章节
```

PaddleOCR-VL 预标注任务：

```text
1. doc/PaddleOCR技术文档/INDEX.md
2. doc/开发文档/后端/k12_annotation_platform_backend_design.md 的 PaddleOCR-VL 预标注章节
3. doc/开发文档/后端/backend_development_spec.md 的异步任务和文件归档规范
```

导出器任务：

```text
1. doc/PaddleOCR技术文档/INDEX.md 的 PP-DocLayoutV3 训练数据读取路径
2. doc/开发文档/后端/k12_annotation_platform_backend_design.md 的导出器设计
3. doc/开发文档/后端/backend_development_spec.md 的导出器开发规范
```

后端与前端联调任务：

```text
1. doc/开发文档/后端/k12_annotation_platform_backend_design.md 的 API、权限和错误码章节
2. doc/开发文档/前端/INDEX.md
3. 只打开前端 INDEX 指向的相关交互或组件文档
```

---

## 4. 维护规则

```text
1. 后端新增详细文档时，在“文档索引”加入一行。
2. 后端任务读取路径变化时，只更新本文件，不扩写根 AGENTS.md。
3. 后端技术栈、依赖、代码规范、安全和加密规则写入 backend_development_spec.md。
4. 后端架构、表、API、流程、权限、备份、审计和导出器设计写入 k12_annotation_platform_backend_design.md。
```
