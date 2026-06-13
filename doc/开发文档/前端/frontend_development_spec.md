# 文档标注平台前端开发规范

版本：v0.8
日期：2026-06-03
参考：

```text
doc/开发文档/后端/k12_annotation_platform_backend_design.md
doc/开发文档/k12_annotation_platform_design.md
doc/开发文档/后端/backend_development_spec.md
doc/开发文档/前端/frontend_routing_spec.md
doc/开发文档/前端/frontend_component_library_spec.md
```

## 目录

- 版本记录
- 1. 目标与边界
- 2. 技术栈
  - 2.1 运行环境
  - 2.2 推荐核心依赖
  - 2.3 暂不引入的依赖
- 3. 依赖文件规范
- 4. 项目目录结构
- 5. 配置规范
- 6. 路由与页面入口规范
- 7. API Client 规范
  - 7.1 OpenAPI 边界
  - 7.2 请求规范
  - 7.3 响应和错误处理
  - 7.4 文件访问和下载
- 8. 状态管理规范
- 9. 组件开发规范
- 10. 样式与设计系统落地规范
- 11. 国际化与本地化规范
- 12. 标注数据前端处理规范
- 13. 文件上传、预览与画布基础规范
- 14. 权限与前端安全规范
- 15. 日志与错误展示
- 16. 测试规范
  - 16.1 单元测试
  - 16.2 组件测试
  - 16.3 端到端测试
  - 16.4 MCP 浏览器联调测试
- 17. 代码风格
- 18. 本地开发流程
- 19. Git 提交规范
- 20. 工程落地检查项
- 21. 关键结论

---

## 版本记录

| 版本 | 日期 | 说明 |
|---|---|---|
| v0.1 | 2026-05-26 | 初版前端开发规范，定义前端技术栈、目录结构、依赖、配置、API client、状态管理、组件、样式、标注数据处理、安全、测试和本地开发流程。 |
| v0.2 | 2026-05-26 | 拆分前端组件库规范，明确颜色 token、组件规格和视觉复用规则由 `frontend_component_library_spec.md` 维护。 |
| v0.3 | 2026-05-26 | 补充角色管理前端边界：前端消费后端 capabilities，提供项目成员与角色管理界面，但不承担最终权限判断。 |
| v0.4 | 2026-05-26 | 补充国际化与本地化规范，明确前端多语言能力、文案 key、locale、格式化、错误文案和测试要求。 |
| v0.5 | 2026-05-27 | 同步前端路由专题文档，明确路由契约由 `frontend_routing_spec.md` 维护，总规范只保留工程入口约束。 |
| v0.6 | 2026-05-27 | 修正路由总规范口径：未知路径统一进入 404；项目任务和导出改为项目详情 tab URL 示例，避免误写为 route path。 |
| v0.7 | 2026-05-29 | 恢复 MCP 浏览器联调测试规范章节；移除对 demo 文档的依赖引用。 |
| v0.8 | 2026-06-03 | 收紧中文提交信息、中文注释、中文日志和中文错误文案要求，统一引用提交规范文档。 |
| v0.9 | 2026-06-09 | 同步后端 API 响应格式（{ data, request_id } 包装与解包），更新画布渲染架构为固定视口 Canvas 矩阵渲染，补充页面导航规范。 |

---

## 1. 目标与边界

本文定义文档数据采集与标注平台的前端开发规范，包括技术栈、目录结构、依赖管理、配置、路由、API client、状态管理、组件组织、样式约束、国际化与本地化、标注数据前端处理方式、文件预览、测试、代码风格和本地开发流程。

本文不维护完整产品需求、完整页面地图、完整交互流程、完整后端 API 清单、完整标注画布交互细节、完整视觉设计系统、完整权限模型或完整业务验收拆分；这些内容分别以对应文档为准：

```text
业务功能、标注格式、标签关系、导出目标：
doc/开发文档/k12_annotation_platform_design.md

后端表、API、流程、权限、并发、任务和导出器：
doc/开发文档/后端/k12_annotation_platform_backend_design.md

后端工程、安全、加密和 API 基础规范：
doc/开发文档/后端/backend_development_spec.md

已拆分的前端专题文档：
doc/开发文档/前端/annotation_workspace_interaction_spec.md
doc/开发文档/前端/frontend_routing_spec.md
doc/开发文档/前端/frontend_component_library_spec.md

后续如需要再单独补充：
产品流程、质量和可访问性专项规范。
```

本文中的接口路径、页面名、状态名、组件名和标注对象名，只作为前端工程实现约束的示例或引用，不作为新的业务设计来源。

---

## 2. 技术栈

### 2.1 运行环境

前端技术栈根据当前平台目标、后端 API 形态和本地开发约束确定。MVP 阶段采用轻量、可维护、便于本地启动的 Vue 方案。

```text
Runtime: Node.js 20+，优先使用当前 LTS 或已验证稳定版本
Package Manager: npm
Framework: Vue 3
Build Tool: Vite
Router: Vue Router 4
CSS: Tailwind CSS 3
PostCSS: postcss + autoprefixer
I18n: vue-i18n
UI Primitives: Headless UI Vue
Icons: lucide-vue-next
HTML Sanitizer: DOMPurify
Testing: Vitest + @vue/test-utils + jsdom
Language: TypeScript + Vue SFC
```

说明：

```text
1. 第一版使用 TypeScript，降低 annotation JSON、geometry、revision、QC error 和 OpenAPI 对齐时的字段错用风险。
2. API 类型以后端 OpenAPI 或前后端共享 schema 为准，禁止在前端手写一套长期漂移的业务类型。
3. 前端框架不与后端耦合，所有服务端能力通过 HTTP API、下载 token 或后续明确的实时通道访问。
4. 前端不直接读写服务端文件系统、数据库或后台任务队列。
```

### 2.2 推荐核心依赖

`package.json` 推荐依赖：

```json
{
  "dependencies": {
    "@headlessui/vue": "^1.7.23",
    "@tailwindcss/typography": "^0.5.19",
    "dompurify": "^3.3.2",
    "lucide-vue-next": "^0.577.0",
    "vue": "^3.5.24",
    "vue-i18n": "^11.1.12",
    "vue-router": "^4.6.4"
  },
  "devDependencies": {
    "@types/node": "^24.10.1",
    "@vitejs/plugin-vue": "^6.0.1",
    "@vue/test-utils": "^2.4.6",
    "autoprefixer": "^10.4.24",
    "jsdom": "^28.1.0",
    "postcss": "^8.5.6",
    "tailwindcss": "^3.4.19",
    "typescript": "^5.9.3",
    "vite": "^7.2.4",
    "vue-tsc": "^3.1.5",
    "vitest": "^4.0.18"
  }
}
```

可选依赖：

```text
canvas / annotation
  仅在原生 SVG / Canvas 方案无法满足性能或交互复杂度时再引入第三方画布库。

state
  MVP 优先使用 Vue composables 和模块级 ref。只有跨模块状态复杂到难以维护时，再引入 Pinia。

e2e
  需要浏览器级验收时引入 Playwright。
```

### 2.3 暂不引入的依赖

默认不引入：

```text
1. 大型 UI 组件库的全量包，除非确认能长期承载标注工作台。
2. 多个互相重叠的状态管理库。
3. 与后端职责重复的 schema 校验和导出转换库。
4. 浏览器端 OCR、模型推理或大文件解析依赖。
5. 未明确用途的动画库、图表库、拖拽库和富文本编辑器。
```

---

## 3. 依赖文件规范

前端依赖文件固定放在：

```text
frontend/package.json
frontend/package-lock.json
```

要求：

```text
1. 使用 npm 安装依赖，提交 package.json 和 package-lock.json。
2. 不提交 node_modules。
3. 新增依赖必须说明用途、使用位置和不可替代原因。
4. 不从其他项目复制 package.json 后直接使用。
5. 删除未使用依赖时同步删除代码引用和测试 mock。
```

推荐脚本：

```json
{
  "scripts": {
    "dev": "vite",
    "typecheck": "vue-tsc --noEmit",
    "build": "vue-tsc --noEmit && vite build",
    "preview": "vite preview",
    "test": "vitest run",
    "test:watch": "vitest"
  }
}
```

---

## 4. 项目目录结构

推荐目录：

```text
frontend/
  index.html
  package.json
  package-lock.json
  vite.config.ts
  tailwind.config.js
  postcss.config.js
  tsconfig.json
  public/
    favicon.svg
    logo.svg
  src/
    main.ts
    App.vue
    style.css
    i18n/
      index.ts
      locales/
        zh-CN.ts
        en-US.ts
    api/
      client.ts
      auth.ts
      projects.ts
      assets.ts
      pages.ts
      annotations.ts
      qc.ts
      exports.ts
      jobs.ts
      index.ts
    router/
      index.ts
    composables/
      useAuth.ts
      useToast.ts
      useTheme.ts
      usePaginatedList.ts
      useAnnotationDraft.ts
      useCanvasRenderer.ts        # 固定视口 Canvas 矩阵渲染器（DPR、setTransform、坐标反算）
      useAnnotationStore.ts       # 标注对象草稿状态管理（增删改、撤销重做）
    components/
      base/
      layout/
      annotation/
      qc/
      export/
      project/
    views/
      auth/
      app/
      workspace/
    utils/
      geometry.ts
      format.ts
      file.ts
      id.ts
      sanitize.ts
    assets/
    __tests__/
```

目录职责：

```text
api
  只封装 HTTP 请求、响应转换和错误对象，不写页面状态。

router
  只维护路由表、路由元信息和全局导航守卫。

i18n
  维护 locale 初始化、语言包加载、文案 key 和日期/数字格式化策略。

composables
  维护可复用前端状态和交互逻辑，禁止直接混入大量 DOM 查询。

components/base
  可复用基础组件，例如 Button、Input、Modal、Tooltip、Select、EmptyState。

components/annotation
  标注相关组件，例如画布容器、对象列表、标签选择、几何编辑器。

views
  页面级组合，负责组织组件和调用 composables，不直接堆复杂业务算法。

utils
  纯函数工具，必须可单元测试。
```

禁止：

```text
1. 在单个 Vue 文件中同时实现页面布局、API 请求、复杂几何算法和全局状态。
2. 在 components/base 中写业务 API 调用。
3. 在 view 中直接拼接不可信 HTML。
4. 在多个目录重复实现同一套分页、toast、错误处理或文件下载逻辑。
```

---

## 5. 配置规范

Vite 配置要求：

```text
1. `@` 指向 `src`。
2. 开发环境使用 Vite proxy 转发 `/api`、文件预览和下载路径。
3. 构建输出到 `frontend/dist`。
4. 生产部署路径默认 `/`，如果部署到子目录必须同步调整 `base`。
5. Vitest 使用 jsdom 环境。
```

示例：

```js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  plugins: [vue()],
  test: {
    environment: 'jsdom',
  },
  server: {
    host: '127.0.0.1',
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  base: '/',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        app: resolve(__dirname, 'index.html'),
      },
    },
  },
})
```

环境变量：

```text
1. 浏览器可见变量必须以 `VITE_` 开头。
2. 不得在前端环境变量中保存数据库密码、Redis 密码、服务端密钥、下载签名私钥或管理员 token。
3. API 基础路径优先使用同源相对路径 `/api/v1`。
4. 本地端口和代理目标可以写入 `.env.local`，不得提交个人机器绝对路径。
5. 默认语言可通过 `VITE_DEFAULT_LOCALE` 配置，默认值为 `zh-CN`。
6. 支持语言列表可通过 `VITE_SUPPORTED_LOCALES` 配置，默认值为 `zh-CN,en-US`。
```

---

## 6. 路由与页面入口规范

推荐使用 Vue Router 4 的 history 模式。

完整 route name、params、Query、meta、history fallback、离页拦截和错误路由契约以以下文档为准：

```text
doc/开发文档/前端/frontend_routing_spec.md
```

路由分组：

```text
/
  可选项目入口或登录跳转，不承担复杂业务。

/auth/login
/auth/register
  认证页。注册页默认禁用，仅部署配置开放注册时启用。

/app
/app/projects
/app/projects/:project_id
/app/pages/:page_id
/app/settings
  工作台页面。
```

项目详情 tab URL 示例：

```text
/app/projects/:project_id?tab=jobs
/app/projects/:project_id?tab=exports
```

`tab=jobs|exports` 是 Query，不是 route path 配置。MVP 项目内任务和导出视图挂在项目详情页下，不定义全局 `/app/jobs` 和 `/app/exports`。

要求：

```text
1. 受保护页面使用 `meta.requiresAuth`。
2. 路由守卫只做认证检查、权限前置判断和轻量跳转，不发起业务写操作。
3. 页面刷新后必须能恢复认证状态和当前路由，生产部署必须配置 history fallback。
4. 未知路径统一进入可解释的 404。
5. 页面级组件应懒加载。
6. 项目上下文来源使用 `projectContextSource` 表达，不能只用布尔值误判工作台 page_id 路由。
```

布局：

```text
AuthLayout
  登录、注册、忘记密码。

AppLayout
  侧边栏、顶部状态区、主内容区、全局 toast、全局 modal 容器。

AnnotationWorkspaceLayout
  左任务队列、中间标注画布、右属性/QC 面板、底部 revision/任务日志。
```

`AnnotationWorkspaceLayout` 的详细交互规则不在本文维护，以以下文档为准：

```text
doc/开发文档/前端/annotation_workspace_interaction_spec.md
```

---

## 7. API Client 规范

### 7.1 OpenAPI 边界

后端 API 的唯一事实来源是 FastAPI OpenAPI 和后端设计文档。

前端不得手工维护一份与后端冲突的完整 API 清单。本文只规定前端如何调用、如何处理错误、如何组织 client。

要求：

```text
1. OpenAPI 本地可访问后，优先用 OpenAPI 对照或生成前端 API 类型/示例。
2. 每个 `src/api/*.ts` 文件按资源域划分。
3. API 函数命名使用动词短语，例如 `fetchProjects`、`createAnnotationRevision`。
4. 页面组件不得直接散落 `fetch('/api/...')`，必须通过 `src/api` 封装。
```

### 7.2 请求规范

请求路径：

```text
API 前缀：/api/v1
```

要求：

```text
1. 默认使用相对路径，便于本地代理和生产同源部署。
2. JSON 请求必须显式设置 `Content-Type: application/json`。
3. 需要 cookie 会话时显式设置 `credentials: 'include'`。
4. 写接口必须由后端校验权限，前端只做交互层提示和入口隐藏。
5. 上传文件使用 FormData，不手动设置 multipart boundary。
```

禁止：

```text
1. 前端拼接服务端真实文件路径。
2. 前端构造数据库 id 以外的存储路径。
3. 前端绕过 API 直接访问 raw asset 目录。
4. 在 URL query 中传递敏感 token、完整私有文本或完整答案内容。
```

### 7.3 响应和错误处理

后端 M4 已实现接口使用 `{ "data": ..., "request_id": "req_xxx" }` 包装成功响应。前端 API 层必须在返回给调用方前解包 `data` 字段，页面组件不得直接操作带包装的原始响应。

响应解包要求：

```text
1. src/api/*.ts 中每个资源模块定义后端原始响应类型（如 PageReadResponse）和前端使用类型（如 Page）。
2. 提供 unwrap 函数将 { data, request_id } 解包为前端类型，同时扁平化嵌套字段（如 data.image.width → width）。
3. request_id 不传给页面组件，仅在错误对象中保留用于排查。
4. 如果后端接口尚未使用 data 包装（如登录、健康检查），前端直接使用原始响应类型。
```

前端 API 模块结构示例：

```text
src/api/pages.ts
  - PageReadData          后端 data 字段类型
  - PageReadResponse      后端 { data, request_id } 类型
  - Page                  前端解包后类型
  - unwrapPage()          解包函数
  - pagesApi.get()        调用 unwrapPage 后返回 Page
```

错误对象字段：

```text
message      中文可展示错误文案，来自本地 i18n 映射或后端中文兜底 message
status       HTTP 状态码
code         后端业务错误码
request_id   后端 request_id
details      可选结构化错误详情
```

错误转换要求：

```text
1. API client 优先使用稳定 code 映射本地化中文文案。
2. 不得把英文异常、浏览器原生错误或第三方库错误直接展示给用户。
3. Error 对象保留 status / code / request_id / details，供 UI 定位和日志排查使用。
```

状态码处理：

```text
400 参数错误
  显示可修正提示，不重试。

401 未登录
  清空当前登录态，跳转登录页。

403 无权限
  显示权限不足，不暴露敏感资源是否存在。

404 资源不存在
  显示空态或返回列表。

409 revision 冲突或锁定冲突
  打开冲突处理入口，不自动覆盖。

422 schema 校验失败
  展示字段级或对象级校验错误，允许用户定位到标注对象。

500 服务端错误
  显示 request_id，提示稍后重试，不展示 traceback。
```

禁止：

```text
1. 直接把后端 traceback 展示给用户。
2. 每个页面各写一套错误解析。
3. 静默吞掉保存失败、导出失败或 QC 失败。
4. 409 冲突时自动覆盖 latest revision。
5. 直接展示 Network Error、Failed to fetch、Unexpected token 这类英文原始异常。
```

### 7.4 文件访问和下载

文件预览和下载必须通过后端授权入口。

要求：

```text
1. 页面图片、overlay、导出包下载都使用后端返回的受控 URL 或 download_token。
2. token 过期时重新请求，不在前端长期缓存。
3. 下载导出包、原始文件、授权材料必须触发权限校验。
4. 下载失败时展示失败原因和 request_id。
5. 不把真实 STORAGE_ROOT 路径展示到前端。
```

---

## 8. 状态管理规范

MVP 阶段优先使用 Vue composables 管理状态。

推荐模式：

```text
模块级 ref
  登录用户、主题、全局 toast、全局任务状态等跨页面单例状态。

局部 ref / reactive
  页面内部筛选、表单草稿、临时 modal 状态。

纯函数 utils
  坐标转换、格式化、校验、文件名处理。
```

可引入 Pinia 的条件：

```text
1. 多个页面需要共同读写同一批复杂实体。
2. 状态存在明确生命周期、缓存、失效和恢复规则。
3. composables 已经出现循环依赖或难以测试。
```

禁止：

```text
1. 把后端数据库当作前端 store 的结构模板完整复制。
2. 把大型 annotation JSON 深度绑定到多个组件，导致保存时来源不清。
3. 在组件卸载后保留未清理的监听器、定时器或全局事件。
4. 用 localStorage 保存敏感数据、原始试卷内容、答案、导出 token。
```

标注草稿状态：

```text
1. 以 page_id 和 base_revision_id 为边界。
2. 本地草稿必须能区分 dirty、saving、saved、conflict、readonly。
3. 保存成功后更新 latest revision 元数据。
4. 保存失败不得清空本地草稿。
```

---

## 9. 组件开发规范

组件分层：

```text
base
  无业务语义基础组件。

layout
  页面框架和工作台布局。

domain
  带业务语义的组件，例如 AnnotationObjectList、QcIssuePanel。

view
  页面级组合，只组织数据获取、状态和组件。
```

基础组件要求：

```text
1. 必须支持 disabled、loading、error、empty 等常见状态。
2. 可交互组件必须有清晰 focus 样式。
3. 图标按钮必须有 aria-label 或 tooltip。
4. 表单组件必须支持 label、description、error message。
5. Modal、Dropdown、Popover 优先使用 Headless UI，避免自写不可访问交互。
```

业务组件要求：

```text
1. props 命名表达业务含义，避免 `data`、`item`、`info` 这类模糊命名。
2. emit 事件使用动词过去式或意图短语，例如 `save-requested`、`object-selected`。
3. 复杂组件必须拆分纯渲染部分和状态管理部分。
4. 大型列表需要考虑分页、虚拟滚动或按需渲染。
```

禁止：

```text
1. 在组件中直接修改 props。
2. 在基础组件里写具体 API 请求。
3. 用颜色作为唯一状态表达。
4. 在模板中写大量复杂表达式。
```

---

## 10. 样式与设计系统落地规范

视觉方向不在本文完整维护。本文只规定前端工程如何落地样式；组件规格、颜色 token、圆角、间距、状态和业务组件复用规则以 `frontend_component_library_spec.md` 为准。

推荐方向：

```text
主风格：Linear.app 类型的高密度工作台
表格、表单、状态和审计区域：参考 IBM Carbon 的企业级清晰度
文档预览区域：保留类似 Notion 的温和纸面阅读感
```

样式实现：

```text
1. 使用 Tailwind CSS 作为主要样式工具。
2. 全局 token 放在 `src/style.css` 的 `:root` 中。
3. 深色模式由根节点 `.dark` class 控制。
4. 可复用样式优先沉淀为 base component，不滥用全局 class。
5. 页面级特殊样式限制在对应 view 或 component 内。
```

基础 token 应覆盖：

```text
color
  background、surface、border、text、muted、accent、success、warning、danger。

spacing
  4px / 8px 基础节奏，工作台区域避免过大留白。

radius
  4px / 6px / 8px 为主，内部工具型 UI 不使用过大圆角。

shadow
  内部工作台少用装饰性阴影，优先用边框和层级背景。
```

禁止：

```text
1. 把营销页 hero 风格套到标注工作台。
2. 使用大面积装饰渐变影响阅读和框选精度。
3. 在同一页面混用多套按钮、输入框和状态标签样式。
4. 在没有设计系统文档前硬编码大量一次性颜色。
```

完整视觉规范、组件规格、颜色 token 和页面布局以 `frontend_component_library_spec.md` 为准。本文只保留工程落地约束，避免在前端开发规范中混入视觉方案细节。

---

## 11. 国际化与本地化规范

国际化属于前端开发规范职责范围。前端必须提供多语言工程能力、locale 初始化、文案 key 管理、日期/数字格式化和错误文案映射；但前端不得擅自翻译用户内容、OCR 内容、原始试卷内容或后端业务标签。

MVP 范围：

```text
1. 默认语言为 zh-CN。
2. 前端结构必须支持 en-US 语言包，避免后续重构。
3. MVP 不要求完整 RTL 语言支持；如果后续支持阿拉伯语、希伯来语等 RTL 语言，需要单独补充布局和图标方向规范。
4. 语言切换是 UI 展示能力，不改变后端存储事实、annotation JSON、revision 或导出数据。
```

目录和初始化：

```text
1. `src/i18n/index.ts` 负责创建 vue-i18n 实例、读取默认 locale、加载语言包。
2. `src/i18n/locales/zh-CN.ts` 保存简体中文文案。
3. `src/i18n/locales/en-US.ts` 保存英文文案。
4. locale 解析顺序：用户显式选择 > 浏览器语言 > `VITE_DEFAULT_LOCALE` > `zh-CN`。
5. 用户 locale 偏好可保存到 localStorage 的低敏 key，例如 `k12.locale`；禁止把业务数据、token、annotation JSON 与 locale 偏好混存。
```

文案 key：

```text
1. 用户可见文案必须通过 i18n key 获取，不在组件模板中硬编码中文或英文。
2. key 使用领域命名空间，例如 `common.save`、`annotation.saveStatus.saved`、`errors.revisionConflict.title`。
3. key 名表达语义，不使用 `text1`、`button2`、`messageA`。
4. 业务状态展示使用 code 到 i18n key 的映射，未知 code 显示安全 fallback。
5. 快捷键符号本身不翻译，例如 `Ctrl + S`；快捷键说明文案需要翻译。
```

必须国际化的内容：

```text
1. 导航、菜单、按钮、工具栏、tooltip、popover、modal、drawer。
2. 表单 label、description、placeholder、error message。
3. toast、inline alert、empty state、loading 文案。
4. 表格列名、筛选项、排序说明、分页说明。
5. 保存状态、任务状态、QC severity、权限提示、锁定原因。
6. aria-label、可访问名称和快捷键帮助。
```

不得由前端擅自翻译的内容：

```text
1. 用户上传文件名、项目名、文档名、用户输入备注。
2. OCR 原文、试卷题目、答案、解析和原始标注文本。
3. 后端 label_registry 中没有提供本地化 display_name 的业务标签。
4. request_id、revision_id、page_id、job_id、ann_id。
5. 导出文件中的训练标签名和官方格式字段名。
```

后端数据展示：

```text
1. label_registry 如需多语言展示，应由后端返回 `display_name_i18n` 或等价结构；前端只按当前 locale 选择展示。
2. 后端错误响应应优先使用稳定 `code`，前端用 code 映射本地化文案。
3. 后端 `message` 可作为开发和兜底信息，但不应成为最终用户文案的唯一来源。
4. 未知状态、未知错误码必须有通用兜底文案，并保留 request_id。
```

日期、时间、数字和单位：

```text
1. 日期、时间、数字、百分比和文件大小使用集中 formatter，不在组件中手写拼接。
2. 日期时间展示使用 `Intl.DateTimeFormat`，数字使用 `Intl.NumberFormat`。
3. 后端时间字段按 API 约定解析；前端展示时必须明确使用用户 locale 和时区策略。
4. 坐标、bbox、revision_no、页码等工程数据保持数字格式清晰，不进行会改变含义的本地化转换。
5. 文件大小、处理耗时、置信度百分比必须使用统一格式化函数。
```

布局和文案长度：

```text
1. 组件必须允许英文文案比中文更长，不能依赖固定中文长度。
2. 按钮、状态 badge、表头和工具栏文案过长时优先截断并提供 tooltip。
3. 不用图标替代翻译文案，除非组件同时有 aria-label 或 tooltip。
4. 组件库中的固定尺寸控件必须验证 zh-CN 和 en-US 下不会遮挡画布和表格内容。
```

测试要求：

```text
1. 单元测试覆盖 locale 解析、fallback、日期/数字/文件大小 formatter。
2. 组件测试至少覆盖 zh-CN 和 en-US 的基础按钮、表单错误、空态和状态 badge。
3. 测试必须能发现缺失的核心 i18n key。
4. E2E 如覆盖关键工作流，应至少验证默认 zh-CN 文案能正常显示。
```

---

## 12. 标注数据前端处理规范

前端必须尊重后端设计中的 revision 模式和不可变数据原则。

要求：

```text
1. 前端编辑的是 annotation draft，不直接修改 raw res.json。
2. 保存时提交完整 page annotation 或后端明确支持的 patch。
3. MVP 采用整页 revision 保存时，必须携带 base_revision_id。
4. 409 冲突时进入人工选择或手动合并流程，不自动覆盖。
5. locked page / locked revision 只能只读展示，不能打开编辑控件。
```

几何字段：

```text
bbox_xyxy
  页面原始坐标系中的 [xmin, ymin, xmax, ymax]。

quad
  页面原始坐标系中的四点坐标。

polygon
  页面原始坐标系中的多点轮廓。
```

前端坐标处理要求：

```text
1. 屏幕坐标和页面原始坐标必须显式转换。
2. 缩放、平移、旋转后的显示坐标不得直接保存为原始坐标。
3. 新建 bbox 后必须保证 xmin < xmax、ymin < ymax。
4. 派生 quad / polygon 时要标记来源，例如 auto_generated。
5. 所有几何转换函数必须放入 `src/utils/geometry.ts` 并写单元测试。
```

标签和关系：

```text
1. 标签列表来自 label_registry API 或后端配置，不在前端写死。
2. 标签颜色可以使用后端 default_color，但前端需要有兜底颜色。
3. 关系类型来自 relation_registry，不在前端写死。
4. 不合法关系可以在前端提前提示，但最终以后端校验为准。
```

---

## 13. 文件上传、预览与画布基础规范

上传：

```text
1. 使用 FormData 上传。
2. 前端可以做文件类型、大小和数量的预检查。
3. 最终文件安全、hash、归档路径和重复检测以后端为准。
4. 上传过程中显示进度、取消入口和失败重试入口。
```

预览：

```text
1. 图片预览使用后端授权 URL。
2. PDF 是否在浏览器预览由产品和安全策略决定，本文不定义完整 PDF 交互。
3. 大图加载必须有 skeleton 或 loading 状态。
4. 图片加载失败应显示可操作错误，不应让画布空白。
```

标注画布基础要求（固定视口 Canvas 矩阵渲染架构）：

```text
1. Canvas 物理尺寸和 CSS 尺寸在初始化时锁定（如 800×600），绝不因图片尺寸动态改变。
2. 物理尺寸 = 逻辑尺寸 × devicePixelRatio，保证高清屏清晰。
3. 使用 ctx.setTransform(dpr*s, 0, 0, dpr*s, dpr*ox, dpr*oy) 一次性设置矩阵绘制图片，禁止 ctx.scale()/translate() 累积。
4. 绘制图片后重置矩阵 ctx.setTransform(dpr, 0, 0, dpr, 0, 0)，再叠加绘制标注 UI。
5. 坐标反算公式：imgX = (screenX - offsetX) / scale，screenX 为鼠标相对 Canvas 左上角的 CSS 像素偏移。
6. SVG overlay 的 viewBox 与 Canvas 逻辑尺寸一致，标注坐标通过 imageToViewport() 转换后直接对应 SVG 坐标系。
7. 大图和多对象页面必须避免全量无意义重渲染。
```

渲染器 composable：

```text
src/composables/useCanvasRenderer.ts
  - initCanvas(canvas)       锁定 Canvas 尺寸（含 DPR），返回 DPR 值
  - loadImage(url)           加载图片，设置 imageSize 和 imageSource，不触碰 Canvas 尺寸
  - render(canvas, drawUI?)  矩阵渲染图片 + 重置后绘制 UI
  - screenToImage(sx, sy)    鼠标坐标 → 原图像素坐标（逆矩阵）
  - imageToViewport(ix, iy)  原图坐标 → 视口坐标（用于 SVG overlay）
  - zoomAt(delta, cx, cy)    以指定视口坐标为中心锚点缩放
  - fitToContainer()         等比适配固定视口（留 5% 边距）
```

完整画布交互、快捷键、对象选择、拖拽、调整、撤销重做、read_order、关系连线和 QC 定位规则应进入：

```text
doc/开发文档/前端/annotation_workspace_interaction_spec.md
```

---

## 14. 权限与前端安全规范

前端权限只用于用户体验优化，不作为最终安全边界。

要求：

```text
1. 所有写操作、下载、导出、锁定、回滚、用户管理都以后端权限校验为准。
2. 前端根据用户角色隐藏不可用入口，但不能假设隐藏即安全。
3. 收到 403 时显示权限不足，不暴露敏感资源细节。
4. 收到 401 时清理前端登录态并跳转登录页。
```

角色与 capabilities：

```text
1. 前端应从 `/api/v1/projects/{project_id}/me/capabilities` 或后端实际 OpenAPI 定义加载当前用户项目能力。
2. 页面按钮、菜单、批量操作和快捷键是否可用，优先根据 capabilities 判断。
3. role_key 只用于展示和成员管理表单，不作为前端安全判断的唯一来源。
4. 同一用户在不同项目的 capabilities 可能不同，切换项目时必须重新加载。
5. 收到 403 后必须刷新当前项目 capabilities 或提示用户重新进入项目。
6. system_admin / project_admin / annotator 等展示文本必须有中文说明，不能只显示英文 role_key。
```

项目成员管理 MVP：

```text
1. project_admin 可看到项目成员列表入口。
2. 成员列表显示用户、状态、项目角色、最后操作时间。
3. project_admin 可添加成员、修改项目角色、禁用或移除成员。
4. 角色修改提交后以前端重新加载 capabilities 和成员列表为准。
5. 前端不允许直接编辑 system_admin，系统级用户管理以后端权限和后续管理页为准。
6. 角色变更成功后展示审计提示，例如“已记录操作日志”。
```

认证：

```text
1. 优先使用 HttpOnly Cookie 会话。
2. 如果后端采用 token，前端不得把长期 token 存入 localStorage。
3. 当前用户信息通过 `/api/v1/auth/me` 或后端实际 OpenAPI 定义加载。
4. 跨站请求、CSRF、防重放策略以后端安全规范为准，前端按接口要求携带必要字段。
```

XSS 和内容安全：

```text
1. 所有服务端返回的 markdown / HTML 预览必须经过 DOMPurify 或等效白名单净化。
2. 默认不用 `v-html`，确实需要时必须集中封装。
3. 用户文件名、标签名、来源信息只作为文本渲染。
4. 不在前端日志中输出 token、下载 URL、完整私有文本、答案、授权材料内容。
```

浏览器端数据保护：

```text
1. 不在 localStorage 保存原始试卷、标注 JSON、导出包地址或敏感 token。
2. sessionStorage 仅可保存低敏 UI 状态，例如当前 tab、临时筛选条件。
3. IndexedDB 缓存大文件需要单独安全评估，MVP 默认不使用。
4. 用户退出登录后清理前端内存态和可清理的本地 UI 状态。
5. locale 偏好属于低敏 UI 设置，可以保存到 localStorage，但必须与业务数据隔离。
```

---

## 15. 日志与错误展示

前端日志和用户可见错误以中文为主；i18n key、route name、error code、接口字段名保持英文稳定标识。

前端日志原则：

```text
1. 开发环境可以输出调试日志。
2. 生产环境只输出必要错误摘要。
3. 不输出敏感字段、完整 annotation JSON、完整 OCR 文本、完整下载 URL。
4. 所有可上报错误必须带前端上下文和后端 request_id。
5. console 日志 message 使用中文，写清页面、用户动作、失败阶段和 request_id。
```

用户可见错误：

```text
toast
  短暂操作反馈，例如保存成功、上传失败。

inline error
  表单字段、标注对象、QC 问题的定位错误。

modal
  revision 冲突、锁定冲突、危险操作确认。

empty state
  无项目、无页面、无任务、无导出记录。
```

错误文案要求：

```text
1. 说明发生了什么。
2. 说明用户能做什么。
3. 必要时显示 request_id。
4. 不显示服务端 traceback。
5. 权限、锁定、冲突、自动保存失败、文件加载失败必须写清影响范围和下一步动作。
```

---

## 16. 测试规范

### 16.1 单元测试

工具：

```text
Vitest
jsdom
```

必须覆盖：

```text
1. API client 成功和失败响应解析。
2. geometry 坐标转换。
3. bbox / quad / polygon 基础校验。
4. 文件大小、扩展名、mime type 前端预检查。
5. 格式化函数、枚举显示函数和 i18n fallback。
6. locale 解析、日期时间、数字、百分比和文件大小本地化格式。
```

### 16.2 组件测试

工具：

```text
@vue/test-utils
Vitest
```

必须覆盖：

```text
1. 基础组件 disabled、loading、error、empty 状态。
2. Modal、Dropdown、Select 的打开关闭和键盘行为。
3. AnnotationObjectList 的选择、过滤、错误定位。
4. QcIssuePanel 的错误列表、跳转事件和空态。
5. 权限不同导致的按钮禁用或隐藏。
6. zh-CN 和 en-US 下的关键按钮、表单错误、空态、状态 badge 不缺失文案。
```

### 16.3 端到端测试

浏览器级测试可在前端框架稳定后引入 Playwright。

优先覆盖：

```text
1. 登录后进入工作台。
2. 上传样例图片。
3. 打开页面预览。
4. 创建 bbox 标注。
5. 保存 annotation revision。
6. 触发 QC 并展示错误。
7. revision 冲突时不自动覆盖。
8. 创建导出任务并查看状态。
9. 默认 zh-CN 文案正常显示，语言包缺失不会导致页面崩溃。
```

测试数据：

```text
1. 使用 fixtures，不依赖生产数据。
2. fixtures 必须覆盖空数据、普通样本、QC 错误、锁定数据、冲突、无权限、任务失败。
3. 示例图片应脱敏或使用可公开样例。
```

### 16.4 MCP 浏览器联调测试

适用工具：

```text
chrome-devtools MCP（agent 控制浏览器）
```

定位：

```text
1. 用于开发期联调、冒烟验证、接口排查和人工验收复现。
2. 不替代单元测试（Vitest）和 CI 级端到端测试（Playwright）。
```

推荐覆盖：

```text
1. 页面关键交互：click、fill、press_key、drag、upload_file。
2. 页面断言：wait_for。
3. 接口联调：list_network_requests + get_network_request。
4. 前端报错巡检：list_console_messages。
```

执行要求：

```text
1. 每次交互前使用 take_snapshot 获取最新 uid，不复用旧 uid。
2. 每个测试步骤必须有“操作 + 断言文本”。
3. 至少记录一次关键接口请求与响应。
4. 至少检查一次 console error/warn。
```

产出要求：

```text
1. 记录执行日期、页面 URL、步骤、预期、实际结果。
2. 关键证据保存到仓库可追溯路径（snapshot、screenshot、network-response）。
3. 联调结论写明“通过项、失败项、已知噪声”。
```

通过标准（开发期）：

```text
1. 关键路径交互可执行且断言可通过。
2. 关键接口请求状态码符合预期。
3. 无新增高优先级前端错误（或错误已登记并可复现）。
```

---

## 17. 代码风格

TypeScript / Vue：

```text
1. 使用 ES Module。
2. Vue SFC 使用 Composition API。
3. `<script setup lang="ts">` 作为默认组件写法。
4. 文件名按组件类型使用 PascalCase，例如 `BaseButton.vue`。
5. composables 使用 `useXxx.ts`。
6. API 文件使用资源名复数或领域名，例如 `annotations.ts`。
7. 工具函数保持纯函数优先。
```

类型规范：

```text
1. API DTO 类型以后端 OpenAPI 生成或人工同步的 `src/api/types.ts` 为准。
2. Annotation、Geometry、QC、Revision 等核心类型必须集中定义，不在组件中临时声明。
3. 对后端返回的不可信 JSON，必须经过最小 runtime guard 或字段存在性检查后再进入核心状态。
4. 禁止用 `as any` 绕过核心数据结构校验。
5. 暂未接入 OpenAPI 生成前，复杂对象必须写明确 interface，并在注释中标明来源 API 或文档章节。
```

命名：

```text
组件：PascalCase
composable：useCamelCase
变量和函数：camelCase
常量：UPPER_SNAKE_CASE
CSS 自定义属性：--k12-name
路由 path：kebab-case
```

注释：

```text
1. 复杂几何、权限、冲突处理、自动保存、离页拦截、安全处理和下载逻辑必须写中文注释。
2. 注释应说明业务背景、输入假设、状态边界、失败路径和用户影响，不只重复函数名或变量名。
3. 组件顶部应使用中文说明职责边界；复杂组件还应说明不负责的逻辑，例如不直接提交复核、不直接判断最终权限。
4. composable、store、API client 中的复杂函数应写中文 doc comment，说明参数、返回值、错误语义和副作用。
5. 所有对外 API schema 字段显示，应有中文含义来源，不仅展示英文 key。
6. i18n key、route name、capability code 可以保持英文稳定标识，但注释必须配中文解释。
7. 复杂代码块注释至少覆盖：用户动作、状态前置条件、关键分支、失败后 UI 行为、是否会触发远端写操作。
8. 修改复杂逻辑时必须同步更新注释，避免注释描述旧状态机或旧接口。
```

禁止：

```text
1. 在模板中写复杂三元表达式链。
2. 在组件中混写大段业务转换逻辑。
3. 使用 magic number 表示坐标、状态和权限。
4. 使用 `any` 风格的模糊对象约定而不写字段说明。
```

---

## 18. 本地开发流程

准备环境：

```powershell
cd frontend
npm install
```

启动前端：

```powershell
cd frontend
npm run dev
```

默认访问：

```text
http://127.0.0.1:5173
```

后端代理：

```text
开发环境前端请求 `/api/v1`，由 Vite proxy 转发到本地 FastAPI。
后端默认地址以后端开发规范和实际启动端口为准。
```

构建：

```powershell
cd frontend
npm run build
```

预览构建产物：

```powershell
cd frontend
npm run preview
```

测试：

```powershell
cd frontend
npm run test
```

---

## 19. Git 提交规范

项目统一提交信息规范见：

```text
doc/开发文档/COMMIT_RULES.md
```

本节不重复维护提交标题、正文格式和示例；如需修改提交规范，只更新 `doc/开发文档/COMMIT_RULES.md`。

要求：

```text
1. 前端工程提交不混入无关后端重构。
2. 视觉调整和业务逻辑调整尽量分开提交。
3. 新增复杂组件时同步提交测试或说明测试缺口。
4. 更新前端规范时同步确认 AGENTS.md 索引是否需要调整。
5. 提交正文按统一规范写明验证结果；如果未执行 `npm run build`、测试或浏览器联调，必须说明原因。
```

---

## 20. 工程落地检查项

第一步先完成前端工程骨架：

```text
1. frontend/package.json 存在。
2. Vite + Vue 可以启动。
3. Tailwind CSS 生效。
4. Vue Router 可以进入 /auth 和 /app。
5. API client 能访问 /api/v1/health 或后端实际健康检查。
6. vue-i18n 初始化完成，zh-CN 和 en-US 语言包存在。
7. Vitest 能运行。
8. build 能生成 dist。
```

第二步再接入平台能力：

```text
1. 登录态加载。
2. 项目和页面列表。
3. 页面图片预览。
4. label_registry 加载。
5. annotation latest 加载。
6. annotation draft 保存 revision。
7. QC 结果展示。
8. background job 状态展示。
9. export job 创建和下载入口。
```

第三步再实现复杂标注工作台：

```text
1. bbox 创建和编辑。
2. quad / polygon 人工调整。
3. 关系连线。
4. read_order 编辑。
5. revision diff。
6. 冲突合并。
7. 多人复核和仲裁。
```

---

## 21. 关键结论

前端 MVP 以 Vue 3、Vite、Vue Router、vue-i18n、Tailwind CSS、Headless UI、lucide-vue-next、DOMPurify、Vitest 为核心技术栈。

本文只约束前端工程实现方式，不维护完整业务流程、完整接口清单、完整视觉设计系统或完整标注画布交互细节。

前端必须尊重后端的 revision 模式、不可变原始数据、权限校验、下载 token、request_id 和错误响应规范。

前端必须具备多语言工程能力，但不能擅自翻译用户内容、OCR 内容、原始试卷内容、训练标签名或后端未本地化的业务标签。

标注画布的核心风险是坐标换算、冲突处理和误覆盖。第一版必须把 geometry 工具函数、API client、草稿状态和错误处理打牢，再扩展复杂交互。

前端可以隐藏无权限入口，但不能承担最终安全边界。所有写入、下载、导出、锁定和回滚必须以后端权限校验为准。
