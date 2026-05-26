# 前端路由契约规范

版本：v0.2
日期：2026-05-27
适用范围：K12 文档数据采集与标注平台前端

参考文档：

```text
doc/开发文档/前端/frontend_development_spec.md
doc/开发文档/前端/frontend_component_library_spec.md
doc/开发文档/前端/annotation_workspace_interaction_spec.md
doc/开发文档/后端/k12_annotation_platform_backend_design.md
doc/开发文档/mvp_implementation_plan.md
```

## 目录

- 1. 版本记录
- 2. 文档目标
- 3. 职责边界
- 4. 路由设计原则
- 5. 路由命名规范
- 6. MVP 路由表
- 7. Layout 归属
- 8. 路由参数规范
- 9. Query 参数规范
- 10. 路由 Meta 规范
- 11. 导航守卫流程
- 12. 登录、会话与重定向
- 13. 项目上下文与 capabilities
- 14. 标注工作台路由规则
- 15. 自动保存、未保存状态与离页拦截
- 16. 错误路由与异常状态
- 17. 菜单、面包屑与页面标题
- 18. 国际化与本地化
- 19. 部署与 history fallback 规则
- 20. 路由测试要求
- 21. MVP 验收标准
- 22. 后续扩展规则
- 23. 关键结论

---

## 1. 版本记录

| 版本 | 日期 | 说明 |
|---|---|---|
| v0.1 | 2026-05-26 | 初版前端路由契约规范，定义 MVP 路由表、参数、Query、Meta、导航守卫、capabilities、离页拦截、错误页和验收标准。 |
| v0.2 | 2026-05-27 | 根据 review 修正 history fallback、page_id 全局唯一契约、项目内 jobs/exports 范围、projectContextSource meta、Query push/replace、latest revision 语义和注册页默认禁用规则。 |

---

## 2. 文档目标

本文定义前端路由层的稳定契约，用于约束 Vue Router 4 的 route path、route name、参数、Query、Meta、布局归属、导航守卫、异常页面和标注工作台离页行为。

目标：

```text
1. 让 MVP 前端路由结构稳定，避免页面开发时各自发明路径。
2. 让可分享 URL 能恢复用户所在的项目、页面、revision、对象和 QC 问题定位。
3. 让登录、权限、403、404、未保存草稿、自动保存和冲突处理有统一规则。
4. 让菜单、面包屑、页面标题、i18n key 和路由名称有统一来源。
5. 明确路由文档只维护路由契约，不扩写组件、接口 DTO 或画布算法。
```

---

## 3. 职责边界

本文负责：

```text
1. 前端 path、route name、route params、Query 参数和 route meta。
2. AuthLayout、AppLayout、AnnotationWorkspaceLayout 的路由归属。
3. 登录态恢复、受保护页面跳转、redirect 参数安全规则。
4. 项目上下文、page 上下文和 capabilities 的路由加载边界。
5. 标注工作台在切换页面、切换 revision、离开工作台和关闭浏览器时的路由约束。
6. 401、403、404、409、5xx 在路由层的处理口径。
7. 路由级测试和 MVP 验收标准。
```

本文不负责：

```text
1. 不定义完整业务流程，业务流程以产品设计、后端设计和 MVP 计划为准。
2. 不定义完整 API 清单、请求字段或响应 DTO，接口以后端 OpenAPI 或后端设计文档为准。
3. 不定义组件视觉规格、颜色 token、表格表单细节或具体组件 props，组件规范以 frontend_component_library_spec.md 为准。
4. 不定义标注画布绘制算法、bbox 编辑细节、快捷键完整表或自动保存定时器实现，工作台交互以 annotation_workspace_interaction_spec.md 为准。
5. 不定义最终权限模型，权限事实来源以后端 capabilities 和写接口校验为准。
6. 不定义前端目录、依赖、状态管理、API client 或测试工具选型，这些以 frontend_development_spec.md 为准。
```

---

## 4. 路由设计原则

路由是应用状态的一部分，但不是业务数据存储。

基本原则：

```text
1. URL 只承载可恢复、可分享、低敏感的定位状态。
2. URL 不承载完整 annotation JSON、OCR 文本、答案内容、下载 token、私有文件路径或后端内部路径。
3. Path 用于资源身份，Query 用于视图状态、筛选、定位和只读历史查看。
4. route name 必须稳定，组件内跳转优先使用 name，不手写 path 字符串。
5. 受保护页面必须声明 meta.requiresAuth。
6. 路由守卫不得发起业务写操作，不得触发保存、提交、锁定、导出或回滚。
7. 路由守卫可以做登录态检查、轻量上下文检查、capabilities 读取和安全重定向。
8. 页面级数据加载可以渲染 loading skeleton，不要求所有业务数据都在全局守卫中完成。
9. 项目权限、按钮启用和快捷键写操作都以后端 capabilities 为准。
10. 未保存草稿、自动保存中、自动保存失败和 revision conflict 必须拦截会丢失上下文的导航。
```

---

## 5. 路由命名规范

route name 使用点分层级，保持稳定。

命名规则：

```text
auth.login
app.home
projects.index
projects.detail
pages.workspace
settings.index
error.forbidden
error.notFound
```

约束：

```text
1. route name 一经用于导航、菜单、测试或埋点，不得随意重命名。
2. 新增页面时必须先定义 route name，再定义 path。
3. path 参数使用 snake_case，与后端路径参数风格保持一致。
4. 组件名使用 PascalCase，route name 不使用组件名作为唯一来源。
5. 测试用例优先断言 route name 和参数，不依赖页面中文标题。
```

---

## 6. MVP 路由表

MVP 路由表：

| route name | path | Layout | 认证 | 说明 |
|---|---|---|---|---|
| `root` | `/` | 无或轻量入口 | 否 | 根入口。未登录进入登录页，已登录进入 `/app/projects`。 |
| `auth.login` | `/auth/login` | `AuthLayout` | 否 | 登录页。支持安全的 `redirect` Query。 |
| `auth.register` | `/auth/register` | `AuthLayout` | 否 | 可选注册页。默认不作为 MVP 必需入口；仅在部署配置明确开放注册时启用。 |
| `app.home` | `/app` | `AppLayout` | 是 | 工作台根入口，默认跳转 `/app/projects`。 |
| `projects.index` | `/app/projects` | `AppLayout` | 是 | 项目列表、项目筛选和项目入口。 |
| `projects.detail` | `/app/projects/:project_id` | `AppLayout` | 是 | 项目详情。MVP 用 Query tab 承载页面列表、成员、项目内任务、项目内导出和项目设置。 |
| `pages.workspace` | `/app/pages/:page_id` | `AnnotationWorkspaceLayout` | 是 | 标注工作台主入口。通过 page_id 加载 page、project、latest revision 和 capabilities。 |
| `settings.index` | `/app/settings` | `AppLayout` | 是 | 用户级或系统级设置入口，MVP 可只实现最小页。 |
| `error.forbidden` | `/403` | `AppLayout` 或轻量错误页 | 视场景 | 权限不足页，不暴露敏感资源细节。 |
| `error.notFound` | `/404` | `AppLayout` 或轻量错误页 | 否 | 兜底 404 页。 |

兜底规则：

```text
1. 未匹配路径统一进入 `error.notFound`。
2. `/app` 不承载业务内容，只做工作台默认跳转。
3. `/` 不承载复杂业务逻辑，只做入口判断。
4. 项目成员、项目设置、项目页面列表、项目内任务和项目内导出在 MVP 可先作为 `/app/projects/:project_id?tab=...` 的 tab 实现。
5. 如果后续项目详情复杂度升高，可扩展为 `/app/projects/:project_id/members` 等子路由，但必须先更新本文。
6. MVP 不定义 `/app/jobs` 和 `/app/exports` 全局列表页；当前后端导出和任务查询以项目或 job_id 为边界，前端入口必须落在项目详情 tab 或后续明确的项目子路由中。
7. 如果后续需要跨项目任务或导出聚合页，必须先补充后端全局列表 API、权限范围和数据可见性规则，再新增 `/app/jobs` 或 `/app/exports`。
```

---

## 7. Layout 归属

`AuthLayout`：

```text
1. 负责登录、注册、忘记密码等认证页外壳。
2. 不加载项目上下文。
3. 不展示工作台侧边栏。
4. 已登录用户访问登录页时，可跳转 redirect 或 `/app/projects`。
5. 注册页默认禁用；未配置开放注册时，访问 `/auth/register` 应显示不可用说明或跳转登录页。
```

`AppLayout`：

```text
1. 负责工作台通用框架，包括侧边栏、顶部状态区、主内容区、全局 toast、全局 modal 容器。
2. 负责展示全局登录状态、当前用户、基础导航和轻量状态。
3. 可以承载项目列表、项目详情、项目内任务 tab、项目内导出 tab、设置、403、404。
4. 不负责标注画布对象编辑、快捷键和保存状态细节。
```

`AnnotationWorkspaceLayout`：

```text
1. 负责标注工作台外壳，包括左任务队列、中间画布、右属性/QC 面板、底部 revision 或任务日志区域。
2. 负责接入工作台保存状态，向路由离页拦截暴露 saved、dirty、autosave_pending、autosaving、autosave_failed、manual_saving、conflict、readonly。
3. 负责在页面切换、revision 切换、离开工作台和关闭浏览器前触发离页确认。
4. 不在路由层实现 bbox 绘制、坐标换算、自动保存 debounce 或冲突合并算法。
```

---

## 8. 路由参数规范

Path 参数：

| 参数 | 所属 path | 类型 | 说明 |
|---|---|---|---|
| `project_id` | `/app/projects/:project_id` | string id | 项目 id。用于加载项目详情、项目成员、项目级能力。 |
| `page_id` | `/app/pages/:page_id` | global page route id | 页面公开路由 id。标注工作台主资源 id，必须全局唯一且不可变。 |

参数约束：

```text
1. 前端不自行生成真实 project_id 或 page_id。
2. 路由参数只做格式校验和存在性校验，不在前端推断资源是否有权限。
3. 参数为空、格式明显非法或包含路径穿越字符时，直接进入 404 或显示无效链接。
4. page_id 是全局唯一、不可变的公开路由 id，后端 `pages.page_id` 必须有唯一约束。
5. page_id 不等同于后端内部自增 id；内部主键是否暴露以后端设计为准。
6. page_id 是工作台主入口，project_id 不放入 workspace path，避免 project/page 层级变化导致 URL 不稳定。
7. 进入 workspace 后，通过 page API 或后端实际接口加载 page 所属 project，再加载 capabilities。
8. 如果后端无法保证 page_id 全局唯一，则必须在前端实现前把工作台路由改为 `/app/projects/:project_id/pages/:page_id` 并同步更新本文、后端 API 和测试。
9. 不把后端文件路径、storage key、下载签名或图片真实路径放入 route params。
```

---

## 9. Query 参数规范

Query 只保存视图状态和定位状态。

通用 Query：

| 参数 | 适用路由 | 示例 | 说明 |
|---|---|---|---|
| `redirect` | `/auth/login` | `/app/pages/page_123` | 登录后返回路径。只能是站内相对路径。 |
| `q` | 列表页 | `math` | 搜索关键字。不得写入敏感原文。 |
| `page` | 列表页 | `2` | 分页页码。 |
| `page_size` | 列表页 | `50` | 每页数量，应有上限。 |
| `sort` | 列表页 | `updated_desc` | 排序 key，必须白名单。 |
| `status` | 列表页 | `running` | 状态筛选，必须白名单。 |

项目详情 Query：

| 参数 | 示例 | 说明 |
|---|---|---|
| `tab` | `pages` | 项目详情子视图。MVP 建议白名单：`overview`、`pages`、`members`、`jobs`、`exports`、`settings`。 |
| `label_set` | `default` | 可选标签集视图筛选。 |

标注工作台 Query：

| 参数 | 示例 | 说明 |
|---|---|---|
| `revision_id` | `rev_123` | 查看指定历史 revision。存在时默认只读，除非后续文档明确支持从历史派生编辑。 |
| `object_id` | `obj_456` | 定位并选中标注对象。 |
| `issue_id` | `qc_789` | 定位 QC 问题。 |
| `mode` | `bbox` | 初始工具模式。MVP 白名单：`select`、`bbox`、`read_order`、`pan`。 |
| `panel` | `qc` | 右侧面板初始 tab。MVP 白名单：`properties`、`qc`、`revisions`。 |
| `from` | `queue` | 返回来源提示，仅用于 UI 返回按钮，不作为安全判断。 |

禁止写入 Query：

```text
1. 完整 annotation JSON。
2. OCR 原文、试卷正文、答案、解析或学生隐私信息。
3. access token、refresh token、下载 token、临时签名 URL。
4. 后端内部文件路径、storage root、私有 bucket key。
5. 未脱敏错误详情、traceback、SQL、调试开关。
6. base_revision_id。并发控制字段必须随保存请求发送，不放入 URL。
```

Query 变更规则：

```text
1. 只改变 `object_id`、`issue_id`、`panel`、`mode` 通常不视为离开当前 page。
2. 改变 `revision_id` 可能改变只读状态，若当前有 dirty 或 conflict，必须先确认。
3. 改变 `page_id` 一律视为切换标注页面，必须执行工作台离页检查。
4. 列表筛选 Query 变更不得清空用户登录态或项目上下文。
5. 无效 Query 值应被忽略、修正为默认值或显示轻量提示，不应导致应用崩溃。
```

Query 写入浏览器历史策略：

```text
1. 普通对象选择、对象列表点击、画布点击导致的 `object_id` 变化必须使用 `router.replace`，避免浏览器历史被对象选择填满。
2. 工具栏切换 `mode`、右侧面板切换 `panel`、轻量定位状态变化默认使用 `router.replace`。
3. 显式从 QC 列表打开某个 issue、从外部链接进入 issue、用户点击“复制当前定位链接”前整理 URL 时，可以使用 `router.push` 或生成可分享 URL。
4. 切换 `page_id`、切换 `revision_id`、提交后的列表筛选、分页和排序可以使用 `router.push`，让浏览器后退符合用户预期。
5. 输入框联想、搜索输入过程中的中间态不得连续 push；需要写入 URL 时应 debounce 后 replace，用户确认搜索时再 push。
6. 任何 push / replace 前都必须先通过 Query 白名单和敏感字段检查。
```

---

## 10. 路由 Meta 规范

每条路由应声明稳定 Meta。

推荐字段：

```ts
type AppRouteMeta = {
  requiresAuth: boolean
  layout: 'auth' | 'app' | 'annotationWorkspace' | 'plain'
  titleKey: string
  projectContextSource: 'none' | 'routeParam' | 'pageLoader'
  projectParamName?: 'project_id'
  workspaceRoute?: boolean
  capability?: string
  navKey?: string
  allowWhenAuthenticated?: boolean
}
```

字段说明：

| 字段 | 说明 |
|---|---|
| `requiresAuth` | 是否需要登录。受保护页面必须为 true。 |
| `layout` | 页面使用的 Layout。 |
| `titleKey` | 页面标题 i18n key，不写死中文或英文标题。 |
| `projectContextSource` | 项目上下文来源。`none` 表示无需项目，`routeParam` 表示从 `project_id` 读取，`pageLoader` 表示先加载 page 元数据再得到 project_id。 |
| `projectParamName` | 当 `projectContextSource=routeParam` 时使用的参数名，MVP 固定为 `project_id`。 |
| `workspaceRoute` | 是否属于标注工作台。用于离页拦截和快捷键作用域。 |
| `capability` | 进入页面建议具备的能力。只能用于 UX 判断，最终以后端为准。 |
| `navKey` | 菜单高亮 key。 |
| `allowWhenAuthenticated` | 已登录用户是否仍可访问。登录页通常为 false。 |

Meta 约束：

```text
1. route meta 只放稳定的页面级配置，不放运行时业务数据。
2. 不在 meta 中硬编码后端返回的角色、用户 id、项目 id 或 page id。
3. capability 字段只能表示前端建议能力，不能替代后端鉴权。
4. titleKey 必须存在于前端语言包。
5. 不再使用单纯的 `requiresProject` 布尔值表达项目上下文；必须用 `projectContextSource` 避免把 workspace 误判为 route params 中有 project_id。
6. `projectContextSource=pageLoader` 的路由不得在全局守卫中强行读取 `project_id`，应交给页面级 loader 通过 `page_id` 加载。
```

MVP projectContextSource 映射：

| route name | projectContextSource | 说明 |
|---|---|---|
| `auth.login` | `none` | 无项目上下文。 |
| `projects.index` | `none` | 项目列表由用户可见项目集合加载，不是单一项目上下文。 |
| `projects.detail` | `routeParam` | 从 `project_id` 读取项目上下文。 |
| `pages.workspace` | `pageLoader` | 先通过 `page_id` 加载 page 元数据，再得到 project_id。 |
| `settings.index` | `none` | 用户级或系统级设置默认无项目上下文。 |

---

## 11. 导航守卫流程

全局守卫建议流程：

```text
1. 规范化目标路由，解析 path params 和 Query。
2. 如果目标是未匹配路由，进入 `error.notFound`。
3. 如果目标需要登录，先恢复会话或确认当前登录态。
4. 未登录访问受保护页面时，跳转 `auth.login`，携带安全 redirect。
5. 已登录访问登录页时，跳转 redirect 或 `/app/projects`。
6. 如果从 workspace 离开，先执行未保存状态检查。
7. 如果 `projectContextSource=routeParam`，从 `projectParamName` 读取 project_id，加载轻量 project 上下文和 capabilities。
8. 如果 `projectContextSource=pageLoader`，全局守卫只校验基础路由和登录态，不假设 route params 中存在 project_id。
9. 如果目标是 workspace，允许页面先进入 loading，再由页面级 loader 根据 page_id 加载 page、project、revision 和 capabilities。
10. 收到 403 时刷新当前 project capabilities，仍无权限则进入 403 或显示权限不足状态。
11. 设置页面标题和菜单高亮。
```

守卫禁止行为：

```text
1. 不在路由守卫中保存 annotation。
2. 不在路由守卫中提交复核、锁定 revision、创建导出任务或删除数据。
3. 不在路由守卫中静默吞掉 401、403、404、409。
4. 不在路由守卫中把用户从 conflict 状态直接导航走。
5. 不在路由守卫中读取或写入完整敏感业务数据到 localStorage。
```

页面级 loader 与全局守卫分工：

```text
1. 全局守卫负责登录态、路由合法性、redirect 安全和离页拦截。
2. 项目详情页负责加载项目详情、项目页面列表、成员、项目内任务、项目内导出或设置 tab 数据。
3. 工作台页面负责加载 page 元数据、图片访问入口、latest revision、指定 revision、label registry、relation registry、QC 列表和 capabilities。
4. 工作台页面在 capabilities 未加载完成前，所有写操作入口默认 disabled 或 readonly。
```

---

## 12. 登录、会话与重定向

登录态规则：

```text
1. 刷新页面后必须能恢复当前路由。
2. 会话恢复失败时，清理前端登录态并跳转登录页。
3. 登录成功后优先跳回安全 redirect。
4. 没有 redirect 时进入 `/app/projects`。
5. 登出后清理内存态、可清理的 UI 状态和敏感缓存，再进入登录页。
```

redirect 安全规则：

```text
1. redirect 只能是站内相对路径，必须以 `/` 开头。
2. redirect 不能以 `//` 开头。
3. redirect 不能包含协议，如 `http:`、`https:`、`javascript:`。
4. redirect 不能指向 `/auth/login` 自身形成循环。
5. redirect 中的 Query 需要保留时，必须经过 URL 解析和白名单校验。
6. 不合法 redirect 一律丢弃，登录后进入 `/app/projects`。
```

401 处理：

```text
1. API 返回 401 时，清理登录态。
2. 如果当前路由需要登录，跳转登录页并设置安全 redirect。
3. 如果当前是登录页，不重复跳转。
4. 不展示后端内部错误详情。
```

---

## 13. 项目上下文与 capabilities

项目上下文来源：

```text
1. `projectContextSource=routeParam` 时，直接从 route params 获取 project_id。
2. `projectContextSource=pageLoader` 时，先通过 page 元数据获取所属 project_id。
3. `/app/projects/:project_id` 使用 routeParam 来源。
4. `/app/pages/:page_id` 使用 pageLoader 来源。
5. 当前项目上下文不得只依赖本地缓存，页面刷新后必须可重新加载。
```

项目上下文加载约束：

```text
1. projects.detail 的 project_id 缺失或格式非法时，进入 404 或显示无效项目链接。
2. pages.workspace 不从 route params 读取 project_id，必须通过 page_id 加载 page 元数据。
3. page 元数据返回的 project_id 是工作台 capabilities、面包屑和返回项目详情链接的唯一来源。
4. 如果 page 存在但当前用户无权访问其 project，按 403 处理，不暴露不必要资源细节。
5. 如果 page_id 不存在，按 page 资源 404 处理。
```

capabilities 来源：

```text
1. 前端应从 `/api/v1/projects/{project_id}/me/capabilities` 或后端实际 OpenAPI 定义加载当前用户项目能力。
2. 前端不得根据 role_key 自行推断安全权限。
3. 同一用户在不同 project 中 capabilities 可能不同，切换 project 或 page 所属 project 时必须重新加载。
4. capabilities 缺失、加载失败或收到 403 后尚未确认时，工作台写操作默认 disabled 或 readonly。
5. capabilities 只能优化前端体验，最终权限以后端写接口校验为准。
```

路由层使用 capabilities 的范围：

```text
1. 控制菜单入口是否可见或 disabled。
2. 控制项目成员、导出、复核、锁定等页面入口的前置提示。
3. 控制工作台写操作入口、快捷键写操作和保存入口的启用状态。
4. 收到 403 后刷新 capabilities 并更新当前页面状态。
```

路由层不得使用 capabilities 做的事：

```text
1. 不把前端 capability 判断当作最终安全边界。
2. 不因为本地 capability 为 true 就跳过后端写接口校验。
3. 不把 capabilities 写入 URL。
4. 不把 capabilities 长期持久化到 localStorage 作为下次登录依据。
```

---

## 14. 标注工作台路由规则

工作台主路由：

```text
/app/pages/:page_id
```

语义：

```text
1. 无 `revision_id` 时，表示进入当前 page 的 latest working view。
2. 有 `revision_id` 时，表示查看指定历史 revision，默认 readonly。
3. `object_id` 用于定位对象，不改变当前 revision。
4. `issue_id` 用于定位 QC 问题，不改变当前 revision。
5. `mode` 和 `panel` 只控制初始 UI 状态，不替代用户权限。
6. latest working view 不等于一定可编辑；是否可编辑必须由 capabilities、locked、页面状态、校验状态和 conflict 状态共同决定。
```

进入工作台加载顺序：

```text
1. 校验 page_id 参数格式。
2. 加载 page 元数据，获取 project_id、图片尺寸和基础状态。
3. 加载当前 project capabilities。
4. 加载 label registry 和 relation registry。
5. 根据 revision_id 加载指定 revision，或加载 latest revision。
6. 加载 QC 问题、任务上下文和相邻页面导航数据。
7. 根据 capabilities、locked、revision_id、conflict 等状态决定 readonly 或可编辑。
```

历史 revision 规则：

```text
1. 带 `revision_id` 的页面默认 readonly。
2. 历史 revision 不触发自动保存。
3. 历史 revision 不允许直接覆盖 latest revision。
4. 从历史 revision 回到无 `revision_id` 的 URL 时，必须重新加载 latest revision，不得把历史 revision 内容直接当作可编辑 draft。
5. 重新加载 latest 后，如用户具备写 capability、页面未锁定、无 conflict 且不处于只读状态，可以进入可编辑 latest working view；否则保持 readonly 并显示原因。
6. 如果后续支持从历史 revision 派生新 draft，必须先更新本文和工作台交互规范。
```

对象和 QC 定位规则：

```text
1. `object_id` 存在且对象可见时，进入页面后选中并滚动或缩放到可见区域。
2. `object_id` 不存在时，保留页面并给出轻量提示，不进入 404。
3. `issue_id` 存在且 QC 问题可见时，打开 QC panel 并定位对应对象或区域。
4. `issue_id` 不存在时，保留页面并给出轻量提示，不进入 404。
5. 定位失败不得清空当前 draft。
```

上一页和下一页：

```text
1. 工作台内上一页、下一页本质是从一个 page_id 跳转到另一个 page_id。
2. 跳转前必须执行未保存状态检查。
3. 如果当前有 dirty、autosave_failed、manual_saving、autosaving 或 conflict，不得静默切换。
4. 快捷键触发的上一页、下一页也必须经过同一套路由离页逻辑。
```

---

## 15. 自动保存、未保存状态与离页拦截

路由层必须识别工作台保存状态：

```text
saved
dirty
autosave_pending
autosaving
autosave_failed
manual_saving
conflict
readonly
```

离页拦截适用范围：

```text
1. 从 `/app/pages/:page_id` 跳到另一个 page_id。
2. 从工作台跳到项目、任务、导出、设置或登录页。
3. 从无 `revision_id` 的可编辑视图切到有 `revision_id` 的历史视图。
4. 浏览器刷新、关闭标签页或输入新地址。
5. 浏览器后退和前进。
```

离页规则：

| 当前状态 | 路由行为 |
|---|---|
| `saved` | 可直接离开。 |
| `readonly` | 可直接离开。 |
| `dirty` | 必须二次确认。 |
| `autosave_pending` | 必须提示有待保存修改，可由用户确认离开。 |
| `autosaving` | 必须提示保存仍在进行中。不得假设异步保存一定完成。 |
| `autosave_failed` | 必须提示自动保存失败，并保留用户取消离开的机会。 |
| `manual_saving` | 必须提示手动保存未完成。 |
| `conflict` | 必须提示 revision 冲突未处理，本地修改可能丢失。 |

自动保存与路由的关系：

```text
1. 自动保存是防丢失机制，不是路由切换许可。
2. 触发离页时可以尝试等待已在进行中的保存完成，但不能依赖 beforeunload 异步请求成功。
3. 路由确认框不得静默触发新的保存 revision 并直接离开。
4. 如果用户取消离开，应保持当前 route 和当前 draft。
5. 如果用户确认离开，前端可以丢弃未保存 UI 草稿，但不得伪造 saved 状态。
6. 自动保存成功后不需要把最新 revision_id 强制写入 URL；无 `revision_id` 表示 latest working view。
7. base_revision_id 是保存请求并发控制字段，不放入路由。
```

Query 变更与离页：

```text
1. 只切换 `panel`、`mode`、`object_id` 或 `issue_id` 不需要离页确认。
2. 从一个 `revision_id` 切换到另一个 `revision_id`，若当前是 readonly 且无本地修改，可直接切换。
3. 从可编辑视图切到历史 revision，若当前 dirty、autosave_pending、autosaving、autosave_failed、manual_saving 或 conflict，必须确认。
4. 从历史 revision 返回 latest working view 时，必须重新加载 latest revision，并重新计算 capabilities、locked、conflict 和 readonly；只有满足可写条件后才进入编辑态。
```

浏览器 beforeunload：

```text
1. dirty、autosave_pending、autosaving、autosave_failed、manual_saving、conflict 状态必须注册 beforeunload 保护。
2. saved 和 readonly 状态不注册 beforeunload 保护。
3. 浏览器通常会忽略自定义文案，前端只需触发原生确认机制。
4. beforeunload 中不得依赖异步保存请求完成。
```

---

## 16. 错误路由与异常状态

401：

```text
1. 表示未登录或会话失效。
2. 受保护页面收到 401 后跳转登录页。
3. 登录成功后可回到安全 redirect。
4. 不单独维护 `/401` 页面。
```

403：

```text
1. 表示已登录但无权访问或操作。
2. 如果发生在项目上下文内，先刷新当前 project capabilities。
3. 刷新后仍无权访问页面时，进入 `error.forbidden` 或在当前页面显示权限不足状态。
4. 403 页面不得暴露资源是否存在、内部权限表达式或后端堆栈。
```

404：

```text
1. 未匹配前端 path 进入 `error.notFound`。
2. 后端返回 project/page/revision 不存在时，页面显示资源不存在。
3. object_id 或 issue_id 定位失败不进入全局 404，只在工作台内提示。
4. 404 页面应提供返回项目列表或返回上一页的入口。
```

409：

```text
1. revision conflict 属于工作台状态，不是独立路由页。
2. 收到 409 后工作台进入 conflict 状态。
3. conflict 状态禁止继续编辑几何对象，直到用户完成冲突处理。
4. conflict 状态离开页面必须提示本地修改可能丢失。
```

5xx：

```text
1. 5xx 不改变 route name。
2. 当前页面显示可重试错误状态。
3. 需要携带 request_id 或等价追踪信息，但不展示 traceback。
4. 路由层不得无限重试。
```

---

## 17. 菜单、面包屑与页面标题

菜单高亮：

```text
1. 菜单高亮以 route meta.navKey 为准。
2. `/app/projects` 和 `/app/projects/:project_id` 默认高亮 `projects`。
3. `/app/pages/:page_id` 默认高亮 `projects` 或 `workspace`，具体取决于导航设计，但必须保持一致。
4. `/app/projects/:project_id?tab=jobs` 和 `/app/projects/:project_id?tab=exports` 默认仍高亮 `projects`。
5. `/app/settings` 高亮 `settings`。
6. 后续如新增全局 `/app/jobs` 或 `/app/exports`，必须先补充全局 API 和权限范围，再新增独立 navKey。
```

面包屑：

```text
1. 面包屑文本优先来自 API 返回的项目名、文档名或页面名。
2. API 加载前使用 i18n fallback，不直接显示 undefined。
3. 页面不存在或无权限时，不在面包屑中暴露敏感名称。
4. 工作台面包屑至少能返回项目详情或项目列表。
```

页面标题：

```text
1. 页面标题由 route meta.titleKey 和页面数据组合生成。
2. 静态标题必须使用 i18n key。
3. 动态标题可以使用项目名或 page 显示名，但不得包含敏感 OCR 原文或答案。
4. 标题加载失败时使用通用标题。
```

---

## 18. 国际化与本地化

路由层 i18n 规则：

```text
1. route meta.titleKey 必须写入语言包。
2. 菜单、错误页、离页确认、权限不足提示、定位失败提示都使用 i18n key。
3. 不通过 URL path 表示 locale，MVP 使用前端 locale 配置、浏览器偏好或用户设置。
4. 如果后续需要 `/zh-CN/...` 或 `/en-US/...` 前缀，必须先更新本文并评估 redirect、分享链接和 404 规则。
5. 路由不得翻译用户内容、OCR 内容、原始试卷内容或后端未本地化的业务标签。
```

建议 titleKey：

```text
routes.auth.login
routes.auth.register
routes.projects.index
routes.projects.detail
routes.projects.tabs.jobs
routes.projects.tabs.exports
routes.pages.workspace
routes.settings.index
routes.error.forbidden
routes.error.notFound
```

---

## 19. 部署与 history fallback 规则

MVP 前端采用 Vue Router history 模式，生产部署必须配置服务端 fallback，否则直接访问或刷新 `/app/pages/:page_id` 会被服务端错误返回 404。

history fallback 基本规则：

```text
1. 非 `/api`、非真实静态资源、非文件下载入口的 GET / HEAD 请求，应 fallback 到前端 `index.html`。
2. `/api` 前缀必须先于前端 fallback 匹配，API 404 必须返回 API 的 JSON 错误，不得返回 `index.html`。
3. `/assets`、`/static`、`/favicon.ico`、`/robots.txt`、`/manifest.webmanifest` 等真实静态资源应按文件存在性返回，缺失时返回静态资源 404，不应 fallback 到 `index.html`。
4. 文件下载、图片授权访问、导出包下载等后端授权入口不得被前端 fallback 截获。
5. 如果前端部署在子路径，Vite `base`、路由 base、反向代理前缀和 redirect 白名单必须同时调整。
6. 生产环境必须验证直接打开 `/app/projects`、`/app/projects/:project_id`、`/app/pages/:page_id`、`/403` 和 `/404` 都能返回前端应用并由前端接管路由。
7. 服务端 fallback 只解决前端路由入口，不代表对应业务资源存在；资源存在性仍由前端页面 loader 调后端 API 判断。
```

Nginx 类部署示例约束：

```text
1. `/api` location 应在前端 fallback location 之前声明。
2. 前端 location 可使用 `try_files $uri $uri/ /index.html` 类策略。
3. 下载和图片访问 location 应与 `/api` 一样在 fallback 之前声明。
4. 静态资源应配置长期缓存，`index.html` 不应长期强缓存。
```

本地开发规则：

```text
1. Vite dev server 自带 history fallback，但不能因此省略生产部署配置。
2. `vite preview` 只能验证前端构建产物，不等价于最终反向代理配置。
3. 本地联调必须验证刷新工作台深链接时 API proxy 和前端 fallback 不冲突。
```

---

## 20. 路由测试要求

单元测试：

```text
1. route name 到 path 的映射正确。
2. 未登录访问受保护页面跳转登录页。
3. 登录页 redirect 只接受安全站内相对路径。
4. 已登录访问登录页跳转工作台默认页或安全 redirect。
5. 未匹配 path 进入 404。
6. 无效 Query 被忽略或修正，不导致崩溃。
7. route meta 的 requiresAuth、layout、titleKey、navKey 完整。
8. route meta 的 projectContextSource 对项目详情为 routeParam，对工作台为 pageLoader。
9. `/app/jobs` 和 `/app/exports` 在 MVP 不作为有效全局路由。
```

守卫测试：

```text
1. 401 清理登录态并跳转登录页。
2. 403 刷新 capabilities 后仍无权限时进入 403 或显示权限不足。
3. 从 dirty 工作台离开时弹出确认。
4. 从 autosaving、manual_saving、autosave_failed、conflict 状态离开时弹出对应确认。
5. 只改变 object_id、issue_id、panel 或 mode 不触发离页确认。
6. 切换 page_id 触发离页确认。
7. 切换 revision_id 时按当前保存状态判断是否确认。
8. 普通对象选择使用 replace，不连续 push 浏览器历史。
9. 显式打开 QC issue 或切换 revision 使用 push，并遵守离页检查。
```

集成测试：

```text
1. 刷新 `/app/pages/:page_id` 后能恢复工作台页面并重新加载必要上下文。
2. 带 `revision_id` 进入工作台时默认 readonly。
3. 带 `object_id` 或 `issue_id` 进入工作台时能定位或给出轻量失败提示。
4. 切换项目后重新加载 capabilities。
5. 权限变化后收到 403 能刷新 capabilities 并更新入口状态。
6. 浏览器后退和前进遵守未保存状态拦截。
7. 直接刷新 `/app/pages/:page_id` 能通过服务端 history fallback 回到前端应用，再由页面 loader 判断资源状态。
8. 无 `revision_id` 的 latest working view 会重新加载 latest revision，并按 capabilities 和 locked 状态决定是否可编辑。
```

---

## 21. MVP 验收标准

MVP 路由验收必须满足：

```text
1. `/`、`/auth/login`、`/app`、`/app/projects`、`/app/projects/:project_id`、`/app/pages/:page_id`、`/app/settings`、`/403`、`/404` 可进入或按规则跳转。
2. 所有 `/app` 下页面需要登录。
3. 未登录访问受保护页面时，登录后能回到安全 redirect。
4. `/auth/register` 默认不是 MVP 必需入口；只有部署配置开放注册时才启用。
5. `/app/jobs` 和 `/app/exports` 默认不是 MVP 全局路由；任务和导出入口位于 `/app/projects/:project_id?tab=jobs|exports`。
6. route name、meta.layout、meta.titleKey、meta.requiresAuth 和 meta.projectContextSource 完整。
7. 项目详情和工作台能加载或重新加载项目上下文。
8. 工作台能基于全局唯一 page_id 恢复 page、project、revision 和 capabilities。
9. 工作台 dirty、autosave_pending、autosaving、autosave_failed、manual_saving、conflict 状态离页有确认。
10. 历史 revision 默认 readonly，不触发自动保存；返回 latest working view 时必须重新加载 latest 并重新计算可写状态。
11. 403、404、409 和 5xx 的路由口径清晰，不暴露内部错误。
12. URL 中不出现 token、私有路径、完整 annotation JSON、OCR 原文或答案内容。
13. 菜单高亮、面包屑和页面标题不依赖硬编码中文。
14. Query push / replace 策略明确，普通对象选择不会污染浏览器历史。
15. 生产部署配置了 history fallback，直接打开和刷新深链接不会被服务端静态 404 截断。
16. 路由测试覆盖认证、redirect、404、403、工作台离页、Query 白名单、Query push/replace 和 history fallback。
```

---

## 22. 后续扩展规则

新增路由前必须确认：

```text
1. 是否已有 route name 可以复用。
2. 是否需要新的 Layout。
3. 是否需要登录。
4. 是否需要 project 上下文。
5. 是否需要 capabilities。
6. 是否会影响工作台离页拦截。
7. 是否会引入敏感 Query。
8. 是否需要新增 i18n titleKey。
9. 是否需要新增或调整服务端 history fallback。
10. 是否需要更新菜单、面包屑和测试。
```

允许的后续扩展示例：

```text
/app/projects/:project_id/members
/app/projects/:project_id/settings
/app/projects/:project_id/labels
/app/projects/:project_id/jobs
/app/projects/:project_id/exports
/app/pages/:page_id/revisions/:revision_id
/app/review
/app/review/:task_id
/app/admin/users
```

扩展约束：

```text
1. 子路由从 Query tab 演进为 path 前，必须保证旧链接可兼容或有明确 redirect。
2. review、admin、labels 等页面必须声明 capability 或更明确的权限前置规则。
3. 如果引入多语言 path 前缀，必须统一处理 redirect、404、分享链接和服务端 history fallback。
4. 如果引入多窗口协作或实时路由状态，需要先补充协作状态规范。
5. `/app/jobs` 或 `/app/exports` 这类跨项目聚合页只能在后端提供全局列表 API、权限过滤和数据范围说明后新增。
```

---

## 23. 关键结论

```text
1. MVP 前端路由采用 Vue Router history 模式，生产部署必须配置服务端 fallback 到 `index.html`。
2. route name、route meta 和 projectContextSource 必须稳定。
3. `/app/pages/:page_id` 是标注工作台主入口，page_id 必须是后端全局唯一、不可变的公开路由 id。
4. `revision_id`、`object_id`、`issue_id` 只作为定位 Query；普通对象选择使用 replace，显式深链接和 revision 切换才使用 push。
5. MVP 不提供 `/app/jobs` 和 `/app/exports` 全局列表，任务和导出先作为项目详情 tab 或后续项目子路由。
6. 无 `revision_id` 表示 latest working view，但是否可编辑必须重新计算 capabilities、locked、conflict 和 readonly。
7. 路由层只做认证、轻量上下文、capabilities、redirect 安全、错误页和离页拦截，不做业务写操作。
8. capabilities 来自后端，前端只用于入口展示、disabled、readonly 和提示，最终权限以后端校验为准。
9. 自动保存和未保存状态必须纳入路由离页逻辑，但保存算法和快捷键细节由 annotation_workspace_interaction_spec.md 维护。
10. URL 不保存敏感数据、完整标注数据、token、私有路径或并发控制字段。
11. 路由文案、页面标题、错误页和确认提示必须支持 i18n。
```
