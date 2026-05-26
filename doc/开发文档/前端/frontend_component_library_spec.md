# 前端组件库规范

版本：v0.3  
日期：2026-05-26  
参考：

```text
doc/开发文档/前端/frontend_development_spec.md
doc/开发文档/前端/annotation_workspace_interaction_spec.md
doc/开发文档/k12_annotation_platform_design.md
doc/开发文档/后端/k12_annotation_platform_backend_design.md
brand-design-md 获取的 Linear-design-analysis
brand-design-md 获取的 IBM-design-analysis
brand-design-md 获取的 Notion-design-analysis
```

## 目录

- 版本记录
- 1. 目标与边界
- 2. 风格来源与适配原则
- 3. 设计 Token
  - 3.1 颜色
  - 3.2 字体
  - 3.3 间距
  - 3.4 圆角
  - 3.5 边框、阴影和层级
  - 3.6 动效
- 4. 组件分层与命名
- 5. 基础组件
  - 5.1 Button
  - 5.2 IconButton 和 ToolbarButton
  - 5.3 表单组件
  - 5.4 Badge、Tag 和状态标识
  - 5.5 Tabs、SegmentedControl 和 Navigation
  - 5.6 Tooltip、Popover、Menu 和 ContextMenu
  - 5.7 Modal、Drawer 和 ConfirmDialog
  - 5.8 Toast、InlineAlert 和 EmptyState
  - 5.9 Table、DataGrid 和分页
  - 5.10 Loading、Skeleton 和 Progress
- 6. 布局组件
- 7. 标注工作台组件
- 8. 文档预览组件
- 9. 任务、复核、导出、角色和审计组件
- 10. 组件状态规范
- 11. 可访问性规范
- 12. 多语言组件规范
- 13. 响应式与密度规范
- 14. 图标规范
- 15. 组件 API 约定
- 16. 测试与示例
- 17. 禁止事项
- 18. 验收标准
- 19. 关键结论

---

## 版本记录

| 版本 | 日期 | 说明 |
|---|---|---|
| v0.1 | 2026-05-26 | 初版组件库规范，定义 K12 标注平台的视觉 token、基础组件、布局组件、标注业务组件、状态、可访问性和复用规则。 |
| v0.2 | 2026-05-26 | 补充角色管理相关组件：成员列表、角色标签、角色选择器、capability 提示和权限不足提示。 |
| v0.3 | 2026-05-26 | 补充多语言组件规范，明确组件文案、aria、tooltip、长文案、格式化和测试要求。 |

---

## 1. 目标与边界

本文定义前端组件库的复用规范，重点约束组件命名、组件分层、设计 token、基础组件规格、业务组件边界、标注工作台组件形态、状态表达、多语言适配、可访问性和测试要求。

本文服务于以下目标：

```text
1. 让前端 MVP 的按钮、表单、表格、面板、状态、画布工具栏和业务组件保持一致。
2. 避免每个页面临时写一套颜色、圆角、间距、状态标签和空态。
3. 支持后续任务队列、标注工作台、复核、QC、revision、导出管理等页面长期复用。
4. 明确哪些组件是无业务语义基础组件，哪些组件可以包含标注、QC、导出等业务语义。
```

本文不定义：

```text
1. 完整产品需求和页面流程。
2. 完整路由表和菜单权限。
3. 后端 API 字段、状态流转和权限模型。
4. bbox / quad / polygon 的具体绘制算法。
5. Vue 组件的完整 props 代码、样式源码和测试源码。
6. 营销官网、品牌落地页或公开展示页视觉方案。
```

路由、API、状态管理、保存冲突、快捷键和画布交互分别以对应专题文档为准。本文只维护“组件应该长什么样、如何复用、如何表达状态”。

---

## 2. 风格来源与适配原则

主风格采用：

```text
基础工作台：Linear.app 的高密度产品工作台纪律
表格 / 表单 / 审计 / 状态：IBM Carbon 的企业级清晰度
试卷预览 / 文档阅读区域：Notion 的温和纸面感
```

适配原则：

```text
1. Linear 只作为工作台密度、层级、焦点色、窄圆角和产品 UI 克制感来源，不照搬深黑营销页。
2. IBM 作为表格、表单、状态、审计、错误和权限提示的主要参考，不照搬 0px 直角到所有组件。
3. Notion 只用于试卷页面、文档预览、轻量说明区域和标签色，不把整个平台做成文档编辑器。
4. 本项目是内部生产工具，首屏必须是可操作界面，不做营销页 hero。
5. 颜色以中性灰白为主，紫蓝用于操作焦点，红橙用于 QC 错误和风险，绿色只用于完成或成功。
6. 不使用品牌 logo、品牌专有图片或不可授权字体文件。
7. 不使用大面积装饰渐变、彩色背景块或插画抢占标注画布注意力。
```

品牌 token 取舍：

```text
Linear:
  primary #5e6ad2
  primary-hover #828fff
  focus #5e69d1
  radius 4px / 6px / 8px
  4px spacing grid

IBM / Carbon:
  text #161616
  muted #525252
  border #e0e0e0
  surface #f4f4f4
  link / info #0f62fe
  success #24a148
  error #da1e28

Notion:
  paper surface #fafaf9 / #f8f5e8
  warm text #37352f
  soft border #ede9e4
  pastel tag backgrounds for low-priority labels
```

---

## 3. 设计 Token

### 3.1 颜色

基础颜色：

| Token | 值 | 用途 |
|---|---:|---|
| `--color-bg-app` | `#f7f8f8` | 应用背景，接近 Linear light surface |
| `--color-bg-canvas` | `#ffffff` | 页面主画布、表格、表单背景 |
| `--color-surface` | `#ffffff` | 默认面板、弹层、控件背景 |
| `--color-surface-muted` | `#f6f5f4` | Notion 风格试卷预览外层、轻量说明区域 |
| `--color-surface-alt` | `#f4f4f4` | IBM 风格表格 header、输入框底色、审计条 |
| `--color-surface-strong` | `#e0e0e0` | 禁用控件、分隔条、低层级填充 |
| `--color-border` | `#e0e0e0` | 默认边框 |
| `--color-border-soft` | `#ede9e4` | 文档预览和轻量卡片分隔 |
| `--color-border-strong` | `#c8c4be` | 输入框、选中行和分组边界 |
| `--color-text` | `#161616` | 主文本 |
| `--color-text-secondary` | `#525252` | 次级文本 |
| `--color-text-tertiary` | `#787671` | 辅助信息、表格 meta |
| `--color-text-muted` | `#8c8c8c` | 占位符、禁用说明 |
| `--color-text-warm` | `#37352f` | 试卷预览、文档说明中的温和正文 |

操作颜色：

| Token | 值 | 用途 |
|---|---:|---|
| `--color-primary` | `#5e6ad2` | 主操作、选中工具、选中对象描边 |
| `--color-primary-hover` | `#828fff` | 主操作 hover |
| `--color-primary-active` | `#5e69d1` | 主操作 active / focus |
| `--color-link` | `#0f62fe` | 文本链接、信息入口 |
| `--color-link-hover` | `#0050e6` | 文本链接 hover |
| `--color-focus-ring` | `#5e69d1` | 统一键盘焦点环 |

语义颜色：

| Token | 值 | 用途 |
|---|---:|---|
| `--color-success` | `#24a148` | 保存成功、任务完成、校验通过 |
| `--color-warning` | `#dd5b00` | 可修复风险、弱冲突、需要确认 |
| `--color-warning-bg` | `#fef7d6` | warning 轻背景 |
| `--color-danger` | `#da1e28` | 删除、校验失败、QC error |
| `--color-danger-bg` | `#fde0ec` | error 轻背景 |
| `--color-info` | `#0f62fe` | 信息提示、后台任务运行中 |
| `--color-info-bg` | `#dcecfa` | info 轻背景 |

标注 overlay 颜色：

| Token | 值 | 用途 |
|---|---:|---|
| `--overlay-manual` | `#5e6ad2` | 人工标注 bbox / quad |
| `--overlay-candidate` | `#0f62fe` | OCR / layout candidate |
| `--overlay-selected` | `#5645d4` | 当前选中对象 |
| `--overlay-qc-error` | `#da1e28` | QC error |
| `--overlay-qc-warning` | `#dd5b00` | QC warning |
| `--overlay-relation` | `#2a9d99` | 关系线、跨块引用 |

颜色使用规则：

```text
1. primary 不作为大面积背景，只用于主按钮、focus、选中工具、当前对象。
2. link 与 primary 分工明确：link 用于文本链接，primary 用于操作。
3. danger 只用于删除、错误、QC error 和不可逆风险。
4. warning 需要搭配文字说明，不单独用橙色表达含义。
5. overlay 必须支持透明度，不得遮挡试卷文字。
6. 颜色不能作为唯一状态表达，必须同时有文字、图标、边框、aria 状态或位置变化。
```

### 3.2 字体

字体栈：

```text
Sans:
  Inter, Geist, IBM Plex Sans, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif

Mono:
  JetBrains Mono, Geist Mono, ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace
```

字体 token：

| Token | 字号 | 字重 | 行高 | 用途 |
|---|---:|---:|---:|---|
| `text-display` | 32px | 600 | 1.25 | 少量页面标题，不用于工作台面板内 |
| `text-title` | 24px | 600 | 1.30 | 页面标题、一级分区标题 |
| `text-heading` | 20px | 600 | 1.35 | 面板标题、弹窗标题 |
| `text-subheading` | 16px | 600 | 1.45 | 表格组标题、属性分组 |
| `text-body` | 14px | 400 | 1.50 | 默认 UI 文本 |
| `text-body-medium` | 14px | 500 | 1.50 | 按钮、选中项、表头 |
| `text-caption` | 12px | 400 | 1.40 | meta、说明、时间、request_id |
| `text-micro` | 11px | 500 | 1.30 | 紧凑 badge、快捷键辅助 |
| `text-mono` | 12px | 400 | 1.45 | id、revision、坐标、日志 |

字体规则：

```text
1. 本项目不沿用 Linear / Notion 的大字号负字距，letter-spacing 统一为 0。
2. 工作台内部不使用 hero 级大标题。
3. 表格、坐标、revision_id、request_id 和日志使用 mono 字体。
4. 中文界面下按钮文案保持短句，避免强制大写。
5. 长文本说明使用 14px 或 13px，不在紧凑面板中使用 18px 以上正文。
```

### 3.3 间距

间距 token：

| Token | 值 | 用途 |
|---|---:|---|
| `space-0` | 0px | 无间距 |
| `space-1` | 2px | 图标微调、紧凑分隔 |
| `space-2` | 4px | badge 内部、工具按钮间隔 |
| `space-3` | 6px | 紧凑表单 gap |
| `space-4` | 8px | 默认小间距 |
| `space-5` | 12px | 表单行、列表行内间距 |
| `space-6` | 16px | 面板 padding、默认布局 gap |
| `space-7` | 20px | 较宽面板 padding |
| `space-8` | 24px | 页面区块间距 |
| `space-10` | 32px | 页面级间距 |
| `space-12` | 48px | 大型空态或页面组间距 |

间距规则：

```text
1. 4px grid 是基础节奏，工作台优先使用 4 / 8 / 12 / 16 / 24。
2. 工具栏按钮间距使用 4px 或 6px。
3. 表格行内 padding 默认 8px 12px，紧凑模式可降到 6px 8px。
4. 面板 padding 默认 12px 或 16px，不使用 32px 以上营销式留白。
5. 标注工作台左右栏宽度稳定，不因内容短暂变化抖动。
```

### 3.4 圆角

圆角 token：

| Token | 值 | 用途 |
|---|---:|---|
| `radius-none` | 0px | 表格网格线、分隔条 |
| `radius-xs` | 2px | bbox handle、极小状态点 |
| `radius-sm` | 4px | badge、tag、菜单项、紧凑控件 |
| `radius-md` | 6px | 输入框、select、工具按钮 |
| `radius-lg` | 8px | 按钮、面板、弹层、重复项卡片 |
| `radius-pill` | 9999px | 状态 pill、头像、极少数 tag |

圆角规则：

```text
1. 常规卡片和面板最大使用 8px。
2. 按钮默认 6px 或 8px，不使用大圆角胶囊按钮。
3. 数据表格、审计列表和日志区域可使用 0px 或 4px。
4. 标注画布上的 bbox handle 使用 2px，避免视觉面积过大。
5. 不把卡片套进卡片。需要分区时使用边框、标题栏或 full-width band。
```

### 3.5 边框、阴影和层级

边框：

```text
hairline: 1px solid var(--color-border)
hairline-soft: 1px solid var(--color-border-soft)
hairline-strong: 1px solid var(--color-border-strong)
focus: 2px solid var(--color-focus-ring)
```

阴影：

| Token | 值 | 用途 |
|---|---|---|
| `shadow-none` | none | 默认工作台 |
| `shadow-popover` | `0 8px 24px rgba(15, 15, 15, 0.12)` | 菜单、popover |
| `shadow-modal` | `0 16px 48px rgba(15, 15, 15, 0.16)` | modal、drawer |

层级：

| 层级 | 用途 |
|---:|---|
| 0 | 页面背景 |
| 10 | sticky header、左侧任务栏、右侧属性栏 |
| 20 | 画布工具栏、悬浮缩放控件 |
| 30 | dropdown、tooltip、popover |
| 40 | drawer、modal |
| 50 | toast、全局阻断错误 |

规则：

```text
1. 默认使用边框和背景层级表达深度，少用阴影。
2. 阴影只用于真正浮起的组件，例如 menu、popover、modal。
3. z-index 必须来自层级 token，禁止在组件内随意写 9999。
4. 标注 overlay 的 z-index 必须在画布内部封装，不污染全局层级。
```

### 3.6 动效

动效 token：

| Token | 值 | 用途 |
|---|---:|---|
| `duration-fast` | 120ms | hover、pressed |
| `duration-base` | 160ms | popover、tooltip |
| `duration-slow` | 220ms | drawer、modal |
| `ease-standard` | `cubic-bezier(0.2, 0, 0, 1)` | 默认 easing |

规则：

```text
1. 动效只用于状态反馈和空间关系，不做装饰性动效。
2. bbox 拖拽、控制点调整、画布缩放不加过渡动画，保证精确操作。
3. 尊重 prefers-reduced-motion，关闭非必要动画。
4. loading 状态必须有静态可见文本，不能只靠 spinner。
```

---

## 4. 组件分层与命名

目录分层：

```text
frontend/src/components/base
  无业务语义基础组件，例如 BaseButton、BaseInput、BaseModal。

frontend/src/components/layout
  页面框架和工作台布局，例如 AppShell、SplitPane、Panel。

frontend/src/components/domain
  带业务语义组件，例如 annotation、qc、revision、export、task。

frontend/src/views
  页面级组合，只组织数据获取、状态和组件。
```

命名规则：

```text
1. 基础组件使用 Base 前缀，例如 BaseButton、BaseTable、BaseTooltip。
2. 布局组件使用语义名，例如 AppShell、WorkspaceLayout、ResizablePanel。
3. 业务组件使用领域前缀，例如 AnnotationObjectList、QcIssuePanel、RevisionStatusBar。
4. 组件文件名使用 PascalCase。
5. emit 事件使用意图短语，例如 save-requested、object-selected、panel-resized。
6. 基础组件不得直接调用 API。
7. domain 组件可以接收业务对象，但不把完整后端表结构复制成 props。
```

组件复用优先级：

```text
1. base component
2. layout component
3. domain component
4. view 内部局部组件
5. 一次性模板片段
```

如果同一模式在 2 个以上页面重复出现，应沉淀为 base、layout 或 domain 组件。

---

## 5. 基础组件

### 5.1 Button

组件名：

```text
BaseButton
```

尺寸：

| size | 高度 | padding | 用途 |
|---|---:|---|---|
| `xs` | 24px | 4px 8px | 表格内轻操作、紧凑工具 |
| `sm` | 28px | 6px 10px | 工具栏、面板 header |
| `md` | 32px | 8px 12px | 默认按钮 |
| `lg` | 40px | 10px 16px | 表单主提交、弹窗底部 |

变体：

| variant | 样式 | 用途 |
|---|---|---|
| `primary` | primary 背景，白字 | 保存、确认、创建 |
| `secondary` | 白底，边框，主文本 | 次要操作 |
| `ghost` | 透明背景 | 面板内轻操作 |
| `link` | 透明背景，link 颜色 | 文本链接型操作 |
| `danger` | danger 背景或 danger 文本 | 删除、撤销不可逆动作 |

状态：

```text
default
hover
active
focus-visible
disabled
loading
```

规则：

```text
1. loading 时保留按钮宽度，避免布局跳动。
2. danger 按钮必须有明确文案，不只用图标。
3. 同一区域只允许一个 primary 主按钮。
4. BaseButton 可以带 leftIcon / rightIcon，但图标必须来自 lucide-vue-next。
5. 不使用 9999px 圆角的常规按钮。
```

### 5.2 IconButton 和 ToolbarButton

组件名：

```text
BaseIconButton
BaseToolbarButton
```

用途：

```text
1. BaseIconButton 用于单个图标操作，例如关闭、刷新、更多、折叠。
2. BaseToolbarButton 用于画布工具、表格工具栏、面板 header 工具。
```

尺寸：

| size | 尺寸 | 图标 |
|---|---:|---:|
| `xs` | 24px | 14px |
| `sm` | 28px | 16px |
| `md` | 32px | 16px |
| `lg` | 40px | 18px |

规则：

```text
1. 只有图标时必须提供 aria-label。
2. 低频或不熟悉图标必须有 tooltip。
3. 工具栏当前选中态使用 primary 轻背景 + primary 边框。
4. disabled 状态不能只降低 opacity，必须阻止交互并提供原因提示。
5. 画布工具按钮尺寸固定，hover、active、selected 不能改变布局。
```

### 5.3 表单组件

基础组件：

```text
BaseFormField
BaseInput
BaseTextarea
BaseNumberInput
BaseSearchInput
BaseSelect
BaseCombobox
BaseCheckbox
BaseRadioGroup
BaseSwitch
BaseSlider
BaseStepper
BaseFileInput
BaseDropzone
```

FormField 结构：

```text
label
required mark
description
control
error message
helper / meta
```

输入框尺寸：

| size | 高度 | 用途 |
|---|---:|---|
| `sm` | 28px | 表格 filter、紧凑属性 |
| `md` | 36px | 默认表单 |
| `lg` | 44px | 上传、登录、宽表单 |

状态：

```text
default
hover
focus-visible
invalid
disabled
readonly
loading
```

规则：

```text
1. 表单错误必须显示在字段下方，并能被屏幕阅读器读取。
2. readonly 与 disabled 区分：readonly 可复制和聚焦，disabled 不参与交互。
3. 数字输入用于坐标、阈值、页码时必须限制 min / max / step。
4. Select 和 Combobox 优先使用 Headless UI primitives。
5. 中文输入法 composition 阶段不得触发自动保存或快捷键写操作。
6. 上传控件不得显示真实服务端路径。
```

### 5.4 Badge、Tag 和状态标识

组件名：

```text
BaseBadge
BaseTag
BaseStatusBadge
BaseKbd
```

Badge 变体：

| variant | 颜色 | 用途 |
|---|---|---|
| `neutral` | 灰白 | 默认标签、meta |
| `primary` | primary 轻背景 | 当前选择、推荐 |
| `success` | success 轻背景 | 完成、保存成功 |
| `warning` | warning 轻背景 | 需确认、可修复风险 |
| `danger` | danger 轻背景 | 错误、阻断 |
| `info` | info 轻背景 | 运行中、后台任务 |

业务状态建议：

| 状态 | badge |
|---|---|
| `saved` | success |
| `dirty` | warning |
| `saving` | info |
| `autosave_failed` | warning |
| `conflict` | danger |
| `readonly` | neutral |
| `locked` | neutral |
| `submitted` | info |
| `reviewed` | success |
| `failed` | danger |

规则：

```text
1. 状态 badge 必须显示文字，不能只有颜色点。
2. BaseTag 可关闭时必须有可点击关闭按钮和 aria-label。
3. Kbd 用于快捷键提示，使用 mono 字体，不能当作按钮。
4. 标签色用于识别 label，不用于表达权限或错误。
```

### 5.5 Tabs、SegmentedControl 和 Navigation

组件名：

```text
BaseTabs
BaseSegmentedControl
BaseBreadcrumb
BasePagination
BaseStepperNav
```

使用场景：

```text
Tabs:
  同一页面内的平级视图，例如 属性 / QC / 历史。

SegmentedControl:
  小范围模式切换，例如 全部 / 错误 / 警告。

Breadcrumb:
  项目 / 文档 / 页面定位，不替代主导航。

Pagination:
  表格和任务列表分页。
```

规则：

```text
1. Tabs 不负责路由，是否同步 URL 由页面和路由文档决定。
2. 选中态使用 primary 下划线或轻背景，不使用大面积彩色块。
3. tab label 过长时截断并提供 tooltip。
4. SegmentedControl 高度固定，切换时不改变容器尺寸。
```

### 5.6 Tooltip、Popover、Menu 和 ContextMenu

组件名：

```text
BaseTooltip
BasePopover
BaseDropdownMenu
BaseContextMenu
BaseCommandMenu
```

规则：

```text
1. Tooltip 只放短文本，不放可交互内容。
2. Popover 可放轻量表单或说明，复杂编辑使用 Drawer 或 Modal。
3. DropdownMenu 菜单项必须支持键盘上下选择和 Esc 关闭。
4. ContextMenu 只在画布或列表区域使用，并提供等价工具栏入口。
5. CommandMenu 后续可用于全局命令，但 MVP 不要求实现。
```

### 5.7 Modal、Drawer 和 ConfirmDialog

组件名：

```text
BaseModal
BaseDrawer
BaseConfirmDialog
```

使用场景：

```text
Modal:
  阻断式短流程，例如删除确认、冲突处理。

Drawer:
  保持上下文的长表单，例如对象详情、导出配置、历史 revision。

ConfirmDialog:
  二次确认，特别是删除、覆盖、离开 dirty 页面。
```

规则：

```text
1. Modal 打开时必须 focus trap，Esc 可关闭时必须明确。
2. ConfirmDialog 的 primary action 文案必须具体，例如“删除对象”，不能只写“确定”。
3. danger 确认按钮放在明确危险语义下，不默认作为主按钮。
4. Drawer 不遮挡关键对象时优先右侧滑出。
5. 长流程不要堆在 Modal 中，改用页面或 Drawer。
```

### 5.8 Toast、InlineAlert 和 EmptyState

组件名：

```text
BaseToast
BaseInlineAlert
BaseEmptyState
BaseErrorState
```

规则：

```text
1. Toast 用于短暂反馈，例如保存成功、复制完成。
2. 阻断错误使用 InlineAlert 或 Modal，不只用 Toast。
3. EmptyState 必须说明当前为空的原因和可执行动作。
4. ErrorState 显示 request_id，但不展示后端 traceback。
5. 自动保存失败不应每次重试都弹 Toast，应在状态区持续显示。
```

### 5.9 Table、DataGrid 和分页

组件名：

```text
BaseTable
BaseDataGrid
BaseTableToolbar
BaseColumnHeader
BasePagination
```

默认规格：

| 项 | 默认值 |
|---|---|
| header height | 36px |
| row height compact | 32px |
| row height default | 40px |
| cell padding | 8px 12px |
| border | 1px hairline |
| font | text-body |

能力：

```text
1. 排序状态。
2. 筛选入口。
3. 行选择。
4. loading skeleton。
5. empty state。
6. error state。
7. 分页或虚拟滚动。
8. sticky header。
```

规则：

```text
1. 表格用于高密度数据，不使用大卡片替代表格。
2. 行选中态使用 primary 轻背景和左侧细边，不只改变文字颜色。
3. 状态列使用 BaseStatusBadge。
4. 操作列默认右对齐，低频操作折叠菜单。
5. 超长文本默认单行截断，详情通过 tooltip、drawer 或详情页查看。
6. 表格列宽必须可预测，避免数据加载后抖动。
```

### 5.10 Loading、Skeleton 和 Progress

组件名：

```text
BaseSpinner
BaseSkeleton
BaseProgressBar
BaseProgressSteps
```

规则：

```text
1. 首次加载页面用 skeleton，局部保存用 spinner + 状态文案。
2. 后台任务必须显示 queued、running、succeeded、failed、cancelled 等状态。
3. 进度不可知时使用 indeterminate，但必须显示“正在处理”类文本。
4. 长任务需要显示 request_id / job_id 入口，便于排查。
```

---

## 6. 布局组件

组件清单：

```text
AppShell
WorkspaceLayout
SplitPane
ResizablePanel
Panel
PanelHeader
PanelBody
PanelFooter
Toolbar
StatusBar
PageHeader
SideNav
TaskRail
```

AppShell：

```text
职责：
  提供全局应用框架、顶部栏、侧边导航、用户区和主内容槽位。

不负责：
  不直接加载业务数据，不实现具体页面状态流转。
```

WorkspaceLayout：

```text
职责：
  提供左任务队列、中间主工作区、右属性 / QC 面板、底部状态栏的稳定布局。

要求：
  1. 左右栏可折叠。
  2. 中间工作区优先保证画布空间。
  3. 面板宽度有 min / max，不能被内容撑破。
  4. 底部状态栏常驻显示保存、revision、任务和错误摘要。
```

Panel：

```text
职责：
  承载属性、筛选、QC、任务详情等工具型区域。

要求：
  1. header、body、footer 结构稳定。
  2. header 可放标题、计数、工具按钮。
  3. body 可滚动时 header 和 footer 不跟随滚动。
  4. 不在 Panel 内再包视觉卡片，分组用边框和标题。
```

Toolbar：

```text
职责：
  组织图标按钮、分隔线、模式选择、缩放值、保存入口。

要求：
  1. 工具按钮尺寸固定。
  2. 使用图标优先，低频功能配 tooltip。
  3. 分组之间用 1px divider 或 8px gap。
  4. selected、disabled、readonly 状态必须可见。
```

---

## 7. 标注工作台组件

标注组件放在：

```text
frontend/src/components/domain/annotation
```

组件清单：

| 组件 | 职责 | 不负责 |
|---|---|---|
| `AnnotationWorkspaceShell` | 组合工作台布局、面板槽位、状态栏 | 具体绘制算法 |
| `AnnotationCanvasViewport` | 承载图片、overlay、缩放和平移容器 | 后端保存 |
| `AnnotationCanvasToolbar` | 工具模式、缩放、适配、显示控制 | 快捷键全局监听实现 |
| `AnnotationToolButton` | bbox、select、pan 等工具按钮 | 业务权限判断来源 |
| `AnnotationOverlayLayer` | 渲染 raw、manual、selected、QC overlay | 坐标换算算法定义 |
| `AnnotationObjectList` | 对象列表、选择、定位、过滤 | 直接修改 draft |
| `AnnotationObjectRow` | 单个标注对象摘要 | 弹窗编辑复杂属性 |
| `AnnotationLabelPicker` | 标签选择和颜色展示 | 维护 label_registry |
| `AnnotationAttributeEditor` | 根据 schema 展示属性表单 | 后端最终 schema 校验 |
| `AnnotationGeometryReadout` | bbox / quad / polygon 坐标只读或轻编辑 | 坐标系统定义 |
| `AnnotationZoomControls` | 放大、缩小、适配整页、适配宽度 | 页面级快捷键策略 |
| `AnnotationLayerToggle` | 控制 raw、manual、QC、relation 显示 | 改变 annotation 数据 |
| `AnnotationShortcutHelp` | 展示快捷键说明 | 定义快捷键语义 |

画布组件规则：

```text
1. 画布组件必须区分 image coordinate 和 viewport coordinate。
2. overlay 颜色来自 overlay token。
3. selected 对象必须有明确描边、控制点和对象列表同步选中。
4. raw candidate 与 manual annotation 视觉上必须可区分。
5. QC error 不能覆盖原标签颜色，需要叠加独立边框或 issue marker。
6. 工具栏操作必须有等价快捷键提示，但不能只依赖快捷键。
7. 画布内组件不得直接调用保存 API，保存由页面或 composable 统一处理。
```

对象列表规则：

```text
1. 行高默认 32px 或 36px，支持高密度扫描。
2. 显示 ann_id 短码、label、read_order、状态、QC 数量。
3. 点击行选中对象并可触发 Ctrl + G 定位。
4. 错误对象显示 danger 标识，但保留 label 原色。
5. 长 label 或属性摘要截断，并提供 tooltip。
```

保存状态组件：

```text
RevisionStatusBar
SaveStatusIndicator
AutosaveStatus
ConflictBanner
RevisionMeta
```

要求：

```text
1. 常驻显示 saved、dirty、saving、autosave_failed、conflict、readonly。
2. 显示 revision_no、base_revision_id 或可展开调试信息。
3. 409 conflict 使用 ConflictBanner 或 Modal，不用 Toast 静默处理。
4. autosave_failed 保留手动保存入口。
```

---

## 8. 文档预览组件

文档预览组件放在：

```text
frontend/src/components/domain/document
```

组件清单：

```text
DocumentPageSurface
DocumentThumbnail
DocumentPreviewToolbar
OcrTextBlock
OcrConfidenceBadge
PageImage
PageMetaStrip
```

视觉规则：

```text
1. 使用 Notion 来源的 warm surface：#fafaf9 / #f8f5e8。
2. 试卷图片本身保持白底，不额外套重阴影。
3. 预览区域可以比工作台更温和，但不使用插画、贴纸或彩色装饰。
4. 页面缩略图选中态使用 primary 边框。
5. OCR 文本块使用轻边框和 caption meta，不抢占原试卷视觉。
```

---

## 9. 任务、复核、导出、角色和审计组件

任务组件：

```text
TaskQueueList
TaskQueueItem
TaskFilterBar
TaskAssigneeBadge
TaskPriorityBadge
```

复核组件：

```text
ReviewDecisionPanel
ReviewCommentBox
ReviewHistoryList
ReviewStatusBadge
```

QC 组件：

```text
QcIssuePanel
QcIssueItem
QcSeverityBadge
QcIssueLocationButton
QcSummaryStrip
```

导出组件：

```text
ExportConfigPanel
ExportJobList
ExportJobItem
ExportFormatBadge
ExportManifestSummary
```

角色管理组件：

```text
ProjectMemberTable
ProjectMemberRow
MemberStatusBadge
RoleBadge
RoleMultiSelect
CapabilityHint
PermissionDeniedInline
MemberInviteDialog
MemberDisableConfirmDialog
```

角色组件规则：

```text
1. RoleBadge 展示 role_key 的中文名，不只显示英文 key。
2. RoleMultiSelect 只表达用户选择意图，不在组件内判断最终授权结果。
3. PermissionDeniedInline 必须给出可理解原因，例如“当前项目中缺少 can_create_export_job 权限”。
4. 成员禁用、移除和角色撤销必须使用 ConfirmDialog。
5. 成员列表中 system_admin 只可展示，不在项目成员组件内直接编辑。
6. capability 状态用于禁用按钮和展示提示，不能作为前端安全边界。
```

审计组件：

```text
AuditTimeline
AuditEventItem
RequestIdBadge
RevisionTimeline
RevisionDiffEntry
```

规则：

```text
1. 表格、复核、导出和审计区域优先采用 IBM / Carbon 的清晰表格和状态表达。
2. 审计信息使用 mono 展示 request_id、revision_id、job_id。
3. 失败状态必须显示可排查信息和下一步动作。
4. 复核操作必须有明确二次确认或可撤回策略，具体流程以后端和产品文档为准。
5. 导出任务列表必须区分 queued、running、succeeded、failed、cancelled。
```

---

## 10. 组件状态规范

所有可交互组件至少考虑：

```text
default
hover
active
focus-visible
disabled
readonly
loading
error
empty
selected
dirty
conflict
```

状态表达规则：

```text
1. focus-visible 使用 2px focus ring，不能被 outline: none 吞掉。
2. disabled 禁止交互，readonly 允许选择和复制。
3. loading 需要保留原始布局尺寸。
4. error 需要说明原因，不能只显示红边框。
5. selected 使用背景、边框、图标或左侧 indicator 组合表达。
6. dirty、saving、saved、conflict 等保存状态必须出现在底部状态栏或面板 header。
```

---

## 11. 可访问性规范

基础要求：

```text
1. 所有按钮必须有可访问名称。
2. 图标按钮必须提供 aria-label 或可读 tooltip。
3. 表单字段必须关联 label 和 error message。
4. Modal、Drawer、Menu、Popover 必须支持键盘操作和 Esc 退出。
5. 不用颜色作为唯一状态表达。
6. 文字和背景对比度应满足 WCAG AA。
7. 快捷键不能在输入框聚焦时误触发画布操作。
```

键盘要求：

```text
1. Tab 顺序符合视觉顺序。
2. Shift + Tab 可返回。
3. Enter / Space 激活按钮。
4. Arrow key 在菜单、列表、表格和画布中的语义必须明确。
5. Esc 优先关闭当前浮层，再取消绘制或选择。
```

---

## 12. 多语言组件规范

组件库必须支持多语言文案扩展。组件规范只定义组件如何接收、展示和保护本地化文案，不维护具体翻译内容；翻译 key、locale 初始化和格式化策略以 `frontend_development_spec.md` 为准。

组件文案：

```text
1. 基础组件不得硬编码用户可见中文或英文。
2. Button、Modal、Drawer、Toast、EmptyState、Table、FormField 的文案由调用方传入，或由组件内部通过稳定 i18n key 获取。
3. Tooltip、aria-label、placeholder、error message、empty description 都必须可本地化。
4. 危险操作文案必须完整可翻译，例如“删除对象”不能拆成不可控的字符串拼接。
5. 快捷键符号不翻译，例如 `Ctrl + S`；快捷键说明、tooltip 和帮助文本必须翻译。
```

长文案和布局：

```text
1. 组件必须允许 en-US 文案比 zh-CN 更长，不能依赖固定中文长度。
2. Button、Badge、Tab、TableHeader、ToolbarButton 必须定义溢出策略。
3. 表格列名和状态 badge 过长时优先截断并提供 tooltip。
4. 空态、错误态和说明文本允许换行，但不能遮挡主要操作按钮。
5. 固定宽度工具栏不得因为语言切换挤压标注画布。
```

格式化数据：

```text
1. 组件不手写日期、时间、数字、百分比和文件大小格式。
2. 基础组件接收已经格式化的展示文本，或调用统一 formatter。
3. 坐标、revision_id、request_id、job_id、ann_id 保持原始可排查格式。
4. 用户输入、OCR 原文、试卷题目和导出字段名不由组件自动翻译。
```

可访问性：

```text
1. aria-label、aria-description、sr-only 文本必须跟随 locale。
2. 图标按钮的 tooltip 和 aria-label 必须表达同一动作。
3. 语言切换后焦点不能丢失到不可见元素。
4. 组件不支持 RTL 时不得声称支持；RTL 需要单独验收布局和方向图标。
```

测试：

```text
1. 基础组件示例至少覆盖 zh-CN 和 en-US。
2. 组件测试应能发现核心文案 key 缺失。
3. 长英文文案测试不能出现按钮文字溢出、表头遮挡或工具栏挤压画布。
4. 图标按钮在两种语言下都必须有可访问名称。
```

---

## 13. 响应式与密度规范

断点：

| 名称 | 宽度 | 规则 |
|---|---:|---|
| `mobile` | < 640px | 只保证基础查看、列表和表单，不承诺完整标注效率 |
| `tablet` | 640px - 1023px | 面板折叠，画布优先 |
| `desktop` | 1024px - 1439px | 默认工作台 |
| `wide` | >= 1440px | 三栏工作台完整展示 |

密度：

```text
compact:
  表格、任务队列、对象列表，行高 32px。

default:
  表单、属性面板、普通列表，行高 36px / 40px。

comfortable:
  文档预览、空态、复核说明，行高和间距适度放大。
```

规则：

```text
1. 标注工作台以 desktop 和 wide 为主要目标。
2. 小屏幕可以进入只读或低效编辑模式，但不能破坏数据。
3. 固定格式控件必须有稳定宽高，不能因文本变化挤压画布。
4. 长文本必须截断、换行或使用 tooltip，不允许溢出覆盖其他控件。
```

---

## 14. 图标规范

图标库：

```text
lucide-vue-next
```

常用图标建议：

| 场景 | 图标 |
|---|---|
| 保存 | `Save` |
| 刷新 | `RefreshCw` |
| 删除 | `Trash2` |
| 更多 | `MoreHorizontal` |
| 搜索 | `Search` |
| 筛选 | `Filter` |
| 设置 | `Settings` |
| 放大 / 缩小 | `ZoomIn` / `ZoomOut` |
| 适配页面 | `Maximize` |
| 选择工具 | `MousePointer2` |
| 框选 | `SquareDashedMousePointer` 或 `BoxSelect` |
| 锁定 | `Lock` |
| 冲突 | `GitCompare` 或 `AlertTriangle` |
| QC 错误 | `CircleAlert` |
| 成功 | `CircleCheck` |
| 运行中 | `LoaderCircle` |

规则：

```text
1. 有 lucide 图标时不手写 SVG。
2. 同一动作在全站使用同一个图标。
3. 图标大小默认 16px，紧凑区域 14px，大按钮 18px。
4. 图标不能替代文字表达危险动作。
5. 图标按钮的 aria-label 和 tooltip 必须来自可本地化文案。
```

---

## 15. 组件 API 约定

基础组件 props 约定：

```text
modelValue / update:modelValue
  表单类组件默认双向绑定。

disabled
  禁止交互。

readonly
  只读但可聚焦和复制。

loading
  操作进行中。

invalid
  字段无效。

size
  xs / sm / md / lg。

variant
  primary / secondary / ghost / danger / neutral / info 等。
```

事件命名：

```text
save-requested
cancel-requested
delete-requested
object-selected
object-focused
filter-changed
sort-changed
page-changed
panel-resized
```

规则：

```text
1. 基础组件暴露通用 props，不暴露 page_id、revision_id 等业务字段。
2. 业务组件的 props 使用明确业务名，不使用 data、item、info。
3. 复杂业务组件应拆分 presentational component 和 composable。
4. emit 只表达用户意图，不在基础组件里拼 API payload。
5. 对外暴露 slot 时必须说明 slot 职责和默认布局限制。
6. 文案类 props 使用 label、description、placeholder、ariaLabel、emptyText、errorMessage 等明确名称。
7. 组件如果接收 translation key，必须同时定义缺失 key 的 fallback 行为。
```

---

## 16. 测试与示例

测试要求：

```text
1. 基础组件必须覆盖 disabled、loading、error、focus-visible、keyboard 操作。
2. 表单组件必须覆盖 label、description、error message 和 aria 关联。
3. Modal、Menu、Popover 必须覆盖打开、关闭、Esc、Tab 顺序。
4. Table 必须覆盖 empty、loading、error、排序、分页。
5. Annotation domain 组件必须覆盖 readonly、conflict、selected、dirty 状态。
6. 基础组件必须覆盖 zh-CN 和 en-US 的关键文案、aria-label 和长文案溢出。
```

示例要求：

```text
1. 每个新增基础组件应提供最小示例。
2. 复杂业务组件应提供 mock 数据示例。
3. 示例数据不得包含真实试卷内容、答案、授权材料或敏感 token。
4. MVP 阶段可先用测试 fixture 或开发预览页承载示例，是否引入 Storybook 后续再定。
```

---

## 17. 禁止事项

```text
1. 把 Apple / Stripe 营销页 hero 风格套进生产工作台。
2. 使用大面积装饰渐变、发光背景、彩色 blob 或高饱和插画。
3. 在同一页面混用多套按钮、输入框、状态 badge 和表格样式。
4. 在业务组件中直接写一次性颜色值。
5. 用颜色作为唯一状态表达。
6. 在基础组件里发起 API 请求。
7. 在组件内保存完整 annotation JSON 到 localStorage。
8. 卡片套卡片，或者把每个页面区块都做成浮动卡片。
9. 为了视觉效果改变标注坐标、试卷图片比例或 overlay 准确性。
10. 不提供键盘焦点样式。
11. 在组件模板中硬编码用户可见中文或英文。
12. 通过字符串拼接生成不可翻译的危险操作或错误文案。
```

---

## 18. 验收标准

组件库 MVP 可按以下标准验收：

```text
1. 有统一 color、typography、spacing、radius、shadow、z-index token。
2. Button、IconButton、Input、Select、Checkbox、Modal、Tooltip、Tabs、Badge、Table、Toast、EmptyState 可复用。
3. 任务队列、标注工作台、QC、revision、导出、审计都有对应 domain 组件规划。
4. 保存状态 saved、dirty、saving、autosave_failed、conflict、readonly 有统一显示组件。
5. 标注 overlay 使用统一颜色 token，raw / manual / selected / QC 可区分。
6. 表格和表单遵循 IBM / Carbon 的清晰度和高密度规则。
7. 文档预览区域使用 Notion 式温和纸面感，但不影响标注精度。
8. 组件支持键盘焦点、aria、disabled、readonly、loading、error 状态。
9. 新增复杂组件有测试或明确测试缺口说明。
10. 没有在页面内散落大量一次性颜色、圆角和间距。
11. 基础组件和核心业务组件支持 zh-CN / en-US 文案，不因英文长文案导致布局遮挡。
12. Tooltip、aria-label、empty state、error message 都有本地化入口。
```

---

## 19. 关键结论

本项目组件库的主目标是支撑高密度、长时间使用的内部生产工具。Linear 提供工作台气质和克制层级，IBM / Carbon 提供表格、表单、审计和状态的可靠性，Notion 只补充试卷预览和文档阅读区域的温和纸面感。

组件库必须优先保证可复用、可访问、多语言可扩展、状态清晰和标注精度。视觉风格服务于 bbox、QC、revision、导出和任务流转，不服务于营销展示。
