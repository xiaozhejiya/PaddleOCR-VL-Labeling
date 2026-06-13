# 前端文档索引

版本：v0.2
日期：2026-06-09
用途：本文件是前端相关任务的文档入口，只维护前端文档导航和读取路径，不存放详细设计。

## 目录

- 1. 使用原则
- 2. 文档索引
- 3. 常见任务读取路径
- 4. 维护规则

---

## 1. 使用原则

```text
1. 前端任务先读本文件，再打开具体详细文档。
2. 本文件只保留前端读取路径，不复制组件规格、路由表、画布交互或 API 细节。
3. 前端通用技术栈、目录结构、状态管理、安全和 i18n 以 frontend_development_spec.md 为准。
4. 路由契约以 frontend_routing_spec.md 为准。
5. 组件规格和视觉复用规则以 frontend_component_library_spec.md 为准。
6. 标注工作台交互以 annotation_workspace_interaction_spec.md 为准。
7. 已实现后端 API 契约以 backend_api_reference.md 为准。
```

---

## 2. 文档索引

| 文档 | 什么时候读 | 内容边界 |
|---|---|---|
| `doc/开发文档/前端/frontend_development_spec.md` | 写前端代码、选前端依赖、建前端目录、写前端测试、安全和国际化规范 | 前端技术栈、目录结构、API client、状态管理、i18n、组件、样式、测试规范 |
| `doc/开发文档/前端/frontend_routing_spec.md` | 设计或实现前端路由、路由参数、页面入口、导航守卫、403/404 和离页拦截 | 前端路由契约、route name、params、query、meta、layout、导航守卫、异常路由 |
| `doc/开发文档/前端/frontend_component_library_spec.md` | 设计或实现前端组件、颜色 token、工作台布局、状态标签、表格表单、业务组件和多语言组件 | 前端组件库、设计 token、组件规格、多语言组件约束、视觉复用规则 |
| `doc/开发文档/前端/annotation_workspace_interaction_spec.md` | 实现前端标注工作台、画布、bbox、缩放、read_order、保存冲突和 QC 定位 | 标注画布 MVP 交互、坐标系统、bbox 编辑、revision 冲突、QC 定位 |
| `doc/开发文档/后端/backend_api_reference.md` | 前后端联调、确认接口路径/请求体/响应格式/错误码 | 已实现后端 API 契约、请求响应示例、权限和错误码 |
| `doc/开发文档/后端/INDEX.md` | 前端任务涉及后端架构、权限模型、表设计或规划 API 时 | 后端文档导航 |
| `doc/开发文档/k12_annotation_platform_design.md` | 理解平台功能、标注格式、标签关系、版本和导出目标 | 功能设计、主数据格式、标注工作流 |
| `doc/开发文档/mvp_implementation_plan.md` | 判断前端任务是否属于 MVP 范围 | MVP 阶段、开发顺序、验收标准 |

---

## 3. 常见任务读取路径

前端编码任务：

```text
1. doc/开发文档/mvp_implementation_plan.md
2. doc/开发文档/前端/frontend_development_spec.md
3. doc/开发文档/前端/frontend_routing_spec.md
4. doc/开发文档/前端/frontend_component_library_spec.md
5. doc/开发文档/后端/backend_api_reference.md 中接口路径、请求体和响应格式
```

前端路由任务：

```text
1. doc/开发文档/前端/frontend_development_spec.md 的路由与页面入口规范
2. doc/开发文档/前端/frontend_routing_spec.md
3. doc/开发文档/前端/annotation_workspace_interaction_spec.md 的保存状态、自动保存、冲突和离页规则
4. doc/开发文档/后端/backend_api_reference.md 中 capabilities、401/403/404/409 相关章节
```

前端组件或视觉任务：

```text
1. doc/开发文档/前端/frontend_development_spec.md
2. doc/开发文档/前端/frontend_component_library_spec.md
3. doc/开发文档/前端/annotation_workspace_interaction_spec.md 中对应标注工作台交互章节
```

前端国际化或多语言任务：

```text
1. doc/开发文档/前端/frontend_development_spec.md 的国际化与本地化规范
2. doc/开发文档/前端/frontend_component_library_spec.md 的多语言组件规范
3. 涉及业务标签展示时读取 doc/开发文档/后端/backend_api_reference.md 或后端设计文档
```

前端标注工作台任务：

```text
1. doc/开发文档/前端/frontend_development_spec.md
2. doc/开发文档/前端/frontend_routing_spec.md
3. doc/开发文档/前端/frontend_component_library_spec.md
4. doc/开发文档/前端/annotation_workspace_interaction_spec.md
5. doc/开发文档/后端/backend_api_reference.md 中页面详情、标注 revision 接口
6. doc/开发文档/k12_annotation_platform_design.md 的 bbox / quad / polygon / read_order 和 QC 章节
```

前后端联调任务：

```text
1. doc/开发文档/后端/backend_api_reference.md
2. doc/开发文档/前端/frontend_development_spec.md 的 API Client 规范
3. doc/开发文档/前端/annotation_workspace_interaction_spec.md 的保存和冲突章节
```

---

## 4. 维护规则

```text
1. 前端新增详细文档时，在"文档索引"加入一行。
2. 前端任务读取路径变化时，只更新本文件，不扩写根 AGENTS.md。
3. 前端通用技术栈、依赖、目录结构、API client、状态管理、安全和 i18n 规则写入 frontend_development_spec.md。
4. 路由契约、route name、params、query、meta、layout、导航守卫、异常路由和离页拦截写入 frontend_routing_spec.md。
5. 组件库、颜色 token、组件规格、多语言组件约束和视觉复用规则写入 frontend_component_library_spec.md。
6. 标注画布、bbox、read_order、坐标换算、保存冲突和 QC 定位写入 annotation_workspace_interaction_spec.md。
7. 已实现后端 API 契约、请求响应示例、权限和错误码写入 backend_api_reference.md。
```
