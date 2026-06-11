# 后端接口文档

版本：v0.1
日期：2026-06-09
用途：记录当前后端已经实现、可用于前后端联调的 API 契约。规划中但尚未实现的接口继续以 `k12_annotation_platform_backend_design.md` 为准。

## 目录

- 版本记录
- 1. 文档边界
- 2. 全局约定
- 3. 接口总览
- 4. 认证与会话
  - 4.1 用户登录
  - 4.2 获取当前用户
- 5. 系统健康检查
- 6. 图片资产导入
  - 6.1 项目级上传入口
  - 6.2 M3 兼容上传入口
- 7. 页面与标注 revision
  - 7.1 获取页面详情
  - 7.2 获取页面图片签名 URL
  - 7.3 读取页面图片文件
  - 7.4 读取页面最新标注版本
  - 7.5 创建页面标注版本
- 8. 当前错误响应约定
- 9. 当前限制与后续收敛点
- 10. 维护规则

---

## 版本记录

| 版本 | 日期 | 说明 |
|---|---|---|
| v0.1 | 2026-06-09 | 初版接口文档，补充 auth、health、assets、pages 和 annotation revision 已实现接口。 |

---

## 1. 文档边界

本文只记录当前代码中已经挂载到 FastAPI 的接口，主要用于前后端联调、测试用例编写和 agent 快速查阅。

```text
1. 已实现接口以本文和后端代码为准。
2. 规划接口、模块边界和业务流程以 k12_annotation_platform_backend_design.md 为准。
3. API 编码规范、安全规范和响应格式约束以 backend_development_spec.md 为准。
4. 本文不展开数据库表设计、权限模型设计、导出器设计或前端交互细节。
```

---

## 2. 全局约定

### 2.1 Base URL

当前 FastAPI 默认 API 前缀：

```text
/api/v1
```

OpenAPI 与调试页面：

```text
GET /api/v1/openapi.json
GET /docs
GET /redoc
```

### 2.2 请求与响应格式

```text
1. JSON 请求和响应默认使用 UTF-8。
2. 文件上传接口使用 multipart/form-data。
3. 成功响应通常使用 { "data": ..., "request_id": "req_xxx" } 包装。
4. 登录和当前用户接口直接返回认证 schema，不使用 data 包装。
5. M4 页面与标注 revision 业务错误已使用 `{ "error": ..., "request_id": "req_xxx" }` 包装；认证、权限和 FastAPI/Pydantic 自动校验错误仍可能返回默认 `detail`，后续通过全局 exception handler 收敛。
```

### 2.3 鉴权

除 `POST /auth/login` 和 `GET /health` 外，当前业务接口均要求 Bearer token：

```http
Authorization: Bearer <access_token>
```

前端不得把 token 放入 URL query、local log、异常提示或可分享链接。

### 2.4 ID 语义

```text
1. API path 中的 {page_id} 表示 pages.public_id，不是 pages.id 内部主键。
2. 响应体中的 page_id、document_id、asset_id、revision_id 默认表示公开稳定编号。
3. 上传接口中的 project_id 当前仍为项目数据库内部主键。
4. 如果后续新增公开 project_id，需要同步修改接口文档、前端路由和权限校验逻辑。
```

### 2.5 权限能力

当前接口使用项目成员 capability 做权限判定：

| 能力 | 使用接口 |
|---|---|
| `can_upload_assets` | 上传图片资产 |
| `can_view_project` | 读取页面详情、读取最新标注版本 |
| `can_create_annotation_revision` | 创建页面标注版本 |

---

## 3. 接口总览

| 方法 | 路径 | 鉴权 | 状态 | 说明 |
|---|---|---|---|---|
| `POST` | `/api/v1/auth/login` | 否 | 已实现 | 用户登录，返回 Bearer JWT。 |
| `GET` | `/api/v1/auth/me` | 是 | 已实现 | 获取当前登录用户。 |
| `GET` | `/api/v1/health` | 否 | 已实现 | 数据库和 Redis 健康检查。 |
| `POST` | `/api/v1/projects/{project_id}/assets/upload` | 是 | 已实现 | 标准项目级图片上传入口。 |
| `POST` | `/api/v1/assets/upload` | 是 | 兼容入口 | M3 简化上传入口，project_id 放在 form 中。 |
| `GET` | `/api/v1/pages/{page_id}` | 是 | 已实现 | 获取页面详情和图片元数据。 |
| `GET` | `/api/v1/pages/{page_id}/image` | 是 | 已实现 | 获取页面图片短期签名访问 URL。 |
| `GET` | `/api/v1/pages/{page_id}/image/raw?exp=&sig=` | 否 | 已实现 | 读取页面图片文件；依赖短期签名 URL。 |
| `GET` | `/api/v1/pages/{page_id}/annotation/latest` | 是 | 已实现 | 读取页面最新标注 revision。 |
| `POST` | `/api/v1/pages/{page_id}/annotation/revisions` | 是 | 已实现 | 创建新的整页标注 revision。 |

---

## 4. 认证与会话

### 4.1 用户登录

```http
POST /api/v1/auth/login
Content-Type: application/json
```

鉴权：不需要。

请求体：

```json
{
  "username": "annotator",
  "password": "password"
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `username` | string | 是 | 登录用户名。 |
| `password` | string | 是 | 登录密码。 |

成功响应：

```json
{
  "expires_in": 86400,
  "user": {
    "id": 1,
    "username": "annotator",
    "display_name": "标注员"
  }
}
```

如果页面存在但尚未产生任何标注 revision，也返回成功响应：

```json
{
  "data": null,
  "request_id": "req_xxx"
}
```

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `expires_in` | integer | Cookie 会话有效期，单位秒，由 `JWT_EXPIRE_MINUTES` 决定。 |
| `user.id` | integer | 用户数据库内部主键。 |
| `user.username` | string | 登录用户名。 |
| `user.display_name` | string | 用户显示名称。 |

Cookie：

```text
1. 登录成功后，后端会通过 Set-Cookie 写入 HttpOnly 会话 Cookie。
2. 前端不得读取该 Cookie，后续请求需显式设置 credentials: 'include'。
3. 当前后端仍兼容 Bearer JWT，但浏览器前端默认走 Cookie 会话。
```

错误：

| HTTP 状态码 | 场景 |
|---|---|
| `401` | 用户名或密码错误、账号不可用或已软删除。 |
| `422` | 请求体字段缺失或类型不合法。 |

### 4.2 用户登出

```http
POST /api/v1/auth/logout
```

鉴权：不强制要求已登录；接口会主动清除会话 Cookie。

成功响应：

```text
HTTP 204 No Content
```

### 4.3 获取当前用户

```http
GET /api/v1/auth/me
Cookie: k12_access_token=...
```

鉴权：需要登录。浏览器前端默认通过 HttpOnly Cookie 会话鉴权，也兼容 Bearer JWT。

成功响应：

```json
{
  "id": 1,
  "username": "annotator",
  "display_name": "标注员"
}
```

错误：

| HTTP 状态码 | 场景 |
|---|---|
| `401` | token 缺失、无效或已过期。 |

---

## 5. 系统健康检查

```http
GET /api/v1/health
```

鉴权：不需要。

成功响应：

```json
{
  "status": "ok",
  "database": {
    "status": "ok"
  },
  "redis": {
    "status": "ok"
  }
}
```

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `status` | string | `ok` 或 `degraded`。任一依赖不可用或未配置时返回 `degraded`。 |
| `database.status` | string | `ok`、`not_configured` 或 `error`。 |
| `database.error_type` | string/null | 数据库检查异常类型，仅异常时返回。 |
| `redis.status` | string | `ok`、`not_configured` 或 `error`。 |
| `redis.error_type` | string/null | Redis 检查异常类型，仅异常时返回。 |

---

## 6. 图片资产导入

### 6.1 项目级上传入口

```http
POST /api/v1/projects/{project_id}/assets/upload
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

鉴权：需要登录，并具备 `can_upload_assets`。

路径参数：

| 参数 | 类型 | 说明 |
|---|---|---|
| `project_id` | integer | 项目数据库内部主键。 |

Form 字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `file` | file | 是 | 待导入的单页图片文件。当前同步上传入口不处理 PDF 渲染。 |

成功响应：

```json
{
  "data": {
    "asset_id": "asset_xxx",
    "document_id": "doc_xxx",
    "page_id": "page_xxx",
    "sha256": "64_hex_sha256",
    "size_bytes": 123456,
    "mime_type": "image/png",
    "width": 1200,
    "height": 1800,
    "asset_reused": false
  },
  "request_id": "req_xxx"
}
```

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `asset_id` | string | 原始图片资产公开编号。 |
| `document_id` | string | 导入后创建或关联的文档公开编号。 |
| `page_id` | string | 导入后创建或关联的页面公开编号，后续页面接口使用该值。 |
| `sha256` | string | 上传文件内容 SHA-256。 |
| `size_bytes` | integer | 文件大小，单位 byte。 |
| `mime_type` | string | 后端校验后的图片 MIME 类型。 |
| `width` | integer | 图片宽度，单位像素。 |
| `height` | integer | 图片高度，单位像素。 |
| `asset_reused` | boolean | 相同 SHA-256 资产已存在时为 `true`，不会覆盖原始文件。 |

错误：

| HTTP 状态码 | 场景 |
|---|---|
| `400` | 文件格式不支持、文件存储失败或上传内容不合法。 |
| `401` | token 缺失、无效或已过期。 |
| `403` | 当前用户不存在、已失效或缺少 `can_upload_assets`。 |
| `404` | 项目不存在。 |
| `413` | 文件超过 `MAX_UPLOAD_MB`。 |
| `422` | form 字段缺失或类型不合法。 |
| `500` | 资产导入内部错误。 |

### 6.2 M3 兼容上传入口

```http
POST /api/v1/assets/upload
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

鉴权：需要登录，并具备 `can_upload_assets`。

Form 字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `project_id` | integer | 是 | 项目数据库内部主键。 |
| `file` | file | 是 | 待导入的单页图片文件。 |

响应体和错误码与 `POST /projects/{project_id}/assets/upload` 一致。

新前端优先使用项目级上传入口；该接口仅作为 M3 兼容入口保留。

---

## 7. 页面与标注 revision

### 7.1 获取页面详情

```http
GET /api/v1/pages/{page_id}
Authorization: Bearer <access_token>
```

鉴权：需要登录，并具备 `can_view_project`。

路径参数：

| 参数 | 类型 | 说明 |
|---|---|---|
| `page_id` | string | 页面公开稳定编号，即 `pages.public_id`。 |

成功响应：

```json
{
  "data": {
    "page_id": "page_xxx",
    "document_id": "doc_xxx",
    "project_id": 1,
    "page_index": 0,
    "status": "imported",
    "capture_method": "scan",
    "visual_difficulty": "normal",
    "image": {
      "asset_id": "asset_xxx",
      "width": 1200,
      "height": 1800,
      "sha256": "64_hex_sha256"
    }
  },
  "request_id": "req_xxx"
}
```

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `page_id` | string | 页面公开稳定编号。 |
| `document_id` | string | 文档公开稳定编号。 |
| `project_id` | integer | 项目数据库内部主键。 |
| `page_index` | integer | 文档内页序号，从 0 开始。 |
| `status` | string | 页面导入和标注状态。 |
| `capture_method` | string/null | 页面采集方式。 |
| `visual_difficulty` | string/null | 页面视觉难度标签。 |
| `image.asset_id` | string/null | 页面图片资产公开编号。 |
| `image.width` | integer | 页面图片宽度，单位像素。 |
| `image.height` | integer | 页面图片高度，单位像素。 |
| `image.sha256` | string/null | 页面图片资产 SHA-256。 |

错误：

| HTTP 状态码 | 场景 |
|---|---|
| `401` | token 缺失、无效或已过期。 |
| `403` | 缺少 `can_view_project`。 |
| `404` | 页面不存在。 |

### 7.2 获取页面图片签名 URL

```http
GET /api/v1/pages/{page_id}/image
Authorization: Bearer <access_token>
```

鉴权：需要登录，并具备 `can_view_project`。

路径参数：

| 参数 | 类型 | 说明 |
|---|---|---|
| `page_id` | string | 页面公开稳定编号，即 `pages.public_id`。 |

成功响应：

```json
{
  "url": "/api/v1/pages/page_xxx/image/raw?exp=1760000000&sig=base64url_hmac",
  "expires_at": "2026-06-09T12:00:00Z"
}
```

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `url` | string | 页面图片短期签名访问 URL。当前使用 `page_id + exp` 的 HMAC-SHA256 签名。 |
| `expires_at` | string | 签名 URL 的 UTC 过期时间。当前默认签发后 5 分钟过期。 |

行为约束：

```text
1. 只有通过 /image 接口且具备 can_view_project 的用户才能获得签名 URL。
2. raw URL 自带 exp 和 sig；服务端会校验签名是否匹配、是否过期。
3. 当前签名 URL 不绑定用户会话，拿到 URL 的客户端可在过期前重复访问。
```

错误：

| HTTP 状态码 | 场景 |
|---|---|
| `401` | token 缺失、无效或已过期。 |
| `403` | 缺少 `can_view_project`。 |
| `404` | 页面不存在。 |

### 7.3 读取页面图片文件

```http
GET /api/v1/pages/{page_id}/image/raw?exp=1760000000&sig=base64url_hmac
```

鉴权：不要求 Bearer token；依赖 `/image` 下发的短期签名 URL。

路径参数：

| 参数 | 类型 | 说明 |
|---|---|---|
| `page_id` | string | 页面公开稳定编号，即 `pages.public_id`。 |

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `exp` | integer | 是 | UTC 秒级过期时间戳。 |
| `sig` | string | 是 | 基于 `page_id + exp` 计算的 HMAC-SHA256 签名。 |

成功响应：

```text
返回页面图片文件流，Content-Type 使用资产的 mime_type。
```

错误：

| HTTP 状态码 | 场景 |
|---|---|
| `401` | `exp` 已过期、超出允许窗口或 `sig` 校验失败。 |
| `404` | 页面不存在、页面未绑定图片、资产不存在或磁盘文件缺失。 |

### 7.4 读取页面最新标注版本

```http
GET /api/v1/pages/{page_id}/annotation/latest
Authorization: Bearer <access_token>
```

鉴权：需要登录，并具备 `can_view_project`。

路径参数：

| 参数 | 类型 | 说明 |
|---|---|---|
| `page_id` | string | 页面公开稳定编号，即 `pages.public_id`。 |

成功响应：

```json
{
  "data": {
    "revision_id": "rev_xxx",
    "page_id": "page_xxx",
    "revision_no": 1,
    "status": "draft",
    "qc_status": "pending",
    "sha256": "64_hex_sha256",
    "size_bytes": 2048,
    "annotation_json": {
      "schema_version": "k12_annotation_v0.1",
      "page_id": "page_xxx",
      "k12_annotations": [],
      "relations": [],
      "history": []
    }
  },
  "request_id": "req_xxx"
}
```

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `revision_id` | string | 标注 revision 公开编号。 |
| `page_id` | string | 页面公开稳定编号。 |
| `revision_no` | integer | 同一页面内递增的 revision 序号。 |
| `status` | string | 当前版本状态，如 `draft`、`submitted`、`reviewed`、`locked`。 |
| `qc_status` | string | 质检状态，如 `pending`、`passed`、`failed`、`warning`。 |
| `sha256` | string/null | revision JSON 文件 SHA-256。 |
| `size_bytes` | integer/null | revision JSON 文件大小。 |
| `annotation_json` | object | 整页标注 JSON。 |
| `data` | object/null | 页面已有 latest revision 时返回 revision 数据；尚无 revision 时返回 `null`。 |

错误：

| HTTP 状态码 | 场景 |
|---|---|
| `401` | token 缺失、无效或已过期。 |
| `403` | 缺少 `can_view_project`。 |
| `404` | 页面不存在。 |
| `500` | 标注 JSON 资产缺失或读取失败。 |

### 7.5 创建页面标注版本

```http
POST /api/v1/pages/{page_id}/annotation/revisions
Authorization: Bearer <access_token>
Content-Type: application/json
```

鉴权：需要登录，并具备 `can_create_annotation_revision`。

路径参数：

| 参数 | 类型 | 说明 |
|---|---|---|
| `page_id` | string | 页面公开稳定编号，即 `pages.public_id`。 |

请求体支持两种形式。

形式一：直接提交整页标注 JSON。

```json
{
  "schema_version": "k12_annotation_v0.1",
  "page_id": "page_xxx",
  "k12_annotations": [
    {
      "id": "ann_001",
      "type": "question_block",
      "label_namespace": "k12",
      "geometry": {
        "bbox_xyxy": [10, 20, 110, 120]
      },
      "read_order": 1,
      "attributes": {},
      "source_refs": [],
      "status": "draft"
    }
  ],
  "relations": []
}
```

形式二：包装提交整页标注 JSON，并附带修改说明。页面已经存在 latest revision 时，必须提交 `base_revision_id`，否则返回 `409`。

```json
{
  "annotation_json": {
    "schema_version": "k12_annotation_v0.1",
    "page_id": "page_xxx",
    "k12_annotations": [],
    "relations": []
  },
  "base_revision_id": "rev_xxx",
  "change_summary": "首次人工校正",
  "change_reason": "完成预标注结果修正"
}
```

请求字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `annotation_json` | object | 否 | 包装形式下的整页标注 JSON。缺失时整个请求体会被视为整页标注 JSON。 |
| `base_revision_id` | string/null | 条件必填 | 当前编辑基于的 latest revision 编号。页面已有 latest revision 时必填；如果不是当前 latest，返回 `409`。首次保存页面时应省略或传 `null`。 |
| `change_summary` | string/null | 否 | 本次 revision 的简短修改说明，仅包装形式支持。 |
| `change_reason` | string/null | 否 | 本次 revision 的修改原因，仅包装形式支持。 |
| `schema_version` | string | 建议 | 标注 JSON schema 版本。当前服务端不强制校验该字段。 |
| `page_id` | string | 否 | 如果存在，必须与 path 中的 `{page_id}` 一致。 |
| `k12_annotations` | array | 是 | 整页标注对象数组；允许空数组，但字段必须存在。 |
| `relations` | array | 否 | 标注对象关系数组，缺失时按空数组处理。 |

标注对象当前基础校验：

| 字段 | 要求 |
|---|---|
| `id` | 非空字符串，同一 revision 内不可重复。 |
| `type` / `label_name` | 二选一，作为标签名称，必须是非空字符串。 |
| `label_namespace` | 非空字符串。 |
| `geometry` | 必须是对象，且至少包含 `bbox_xyxy`、`quad` 或 `polygon` 之一。 |
| `geometry.bbox_xyxy` | 可选，格式为 `[xmin, ymin, xmax, ymax]`，必须在页面范围内，且满足 `xmin < xmax`、`ymin < ymax`。 |
| `geometry.quad` | 可选，必须是 4 个点，每个点为 `[x, y]`。 |
| `geometry.polygon` | 可选，至少 3 个点，每个点为 `[x, y]`。 |
| `read_order` | 可选；如果存在，必须是正整数，且同一 revision 内不可重复。 |
| `attributes` | 可选；如果存在，必须是对象。 |
| `source_refs` | 可选；如果存在，必须是数组或对象。 |
| `status` | 可选；允许 `draft`、`active`、`deleted`，缺失时按 `active` 处理。 |

关系对象当前基础校验：

| 字段 | 要求 |
|---|---|
| `id` / `rel_id` | 二选一，关系 id 必须是非空字符串，同一 revision 内不可重复。 |
| `type` / `relation_type` | 二选一，关系类型必须是非空字符串。 |
| `from_id` / `from_ann_id` | 二选一，必须引用当前 revision 中已存在的标注对象。 |
| `to_id` / `to_ann_id` | 二选一，必须引用当前 revision 中已存在的标注对象。 |
| `attributes` | 可选；如果存在，必须是对象。 |
| `status` | 可选；允许 `active`、`deleted`，缺失时按 `active` 处理。 |

保存行为：

```text
1. 服务端先解析 page_id，并检查项目权限。
2. 校验 annotation JSON、几何坐标、read_order 和 relation 引用。
3. 生成新的 revision_id 和 revision_no。
4. 写入 revision JSON 文件。
5. 登记 annotation_revisions。
6. 重建 annotation_objects 和 relation_objects 索引。
7. 向 annotation_json.history 追加本次 revision 记录。
```

成功响应与 `GET /pages/{page_id}/annotation/latest` 一致，HTTP 状态码为 `201`。

错误：

| HTTP 状态码 | 场景 |
|---|---|
| `401` | token 缺失、无效或已过期。 |
| `403` | 缺少 `can_create_annotation_revision`。 |
| `404` | 页面不存在。 |
| `409` | 页面已有 latest revision 但未提交 `base_revision_id`，或提交的 `base_revision_id` 不是当前 latest。 |
| `422` | annotation JSON、几何、read_order 或 relation 校验失败。 |
| `500` | revision JSON 写入、读取或数据库登记失败。 |

---

## 8. 当前错误响应约定

M4 页面与标注 revision 接口捕获的业务错误使用统一结构：

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "bbox 超出页面范围。",
    "details": {
      "page_id": "page_xxx"
    }
  },
  "request_id": "req_xxx"
}
```

当前认证、权限和 Pydantic 请求校验失败仍可能返回 FastAPI 默认 `detail`，后续应通过全局 exception handler 按后端开发规范统一收敛。

常见状态码：

| HTTP 状态码 | 说明 |
|---|---|
| `400` | 请求内容可解析，但上传文件、存储或业务输入不符合要求。 |
| `401` | 未登录、token 无效、token 过期或登录失败。 |
| `403` | 已登录但缺少项目 capability，或用户状态不允许执行操作。 |
| `404` | 项目、页面或 revision 不存在。 |
| `409` | annotation revision 保存存在版本冲突。 |
| `413` | 上传文件超过大小限制。 |
| `422` | Pydantic 请求校验失败，或标注 JSON 业务校验失败。 |
| `500` | 服务端内部错误、资产导入异常或标注 JSON 读写异常。 |

M4 页面与标注 revision 接口当前使用的业务错误 code：

| code | HTTP 状态码 | 场景 |
|---|---|---|
| `PAGE_NOT_FOUND` | `404` | 页面不存在。 |
| `ANNOTATION_REVISION_NOT_FOUND` | `404` | 指定 revision 不存在。 |
| `VALIDATION_ERROR` | `422` | 标注 JSON、几何、read_order 或 relation 业务校验失败。 |
| `REVISION_CONFLICT` | `409` | `base_revision_id` 缺失或不是当前 latest。 |
| `STORAGE_ERROR` | `500` | 标注 JSON 文件写入或读取失败。 |

---

## 9. 当前限制与后续收敛点

```text
1. 当前 project_id 仍使用内部数据库主键，后续如果需要公开项目编号，应整体收敛 API 和权限校验。
2. POST 创建 annotation revision 已提供 base_revision_id 和 409 冲突控制；前端保存已有 revision 时必须带当前 latest revision_id。
3. 当前没有对象级 patch API；标注保存以整页 annotation JSON revision 为单位。
4. 当前标注 JSON 已要求 k12_annotations 字段存在；relations 仍允许缺失并按空数组处理。
5. 当前没有 revision submit、lock、rollback、review、qc run 等流转接口。
6. 当前页面图片访问已提供短期签名 URL；签名默认 5 分钟有效，raw 端点要求 exp 和 sig 校验通过。
7. 当前认证、权限和 Pydantic 请求校验错误尚未统一包装 request_id；M4 页面与标注 revision 的业务错误已统一。
8. 当前接口文档不替代自动生成的 OpenAPI；字段变化时两者都需要核对。
```

---

## 10. 维护规则

```text
1. 新增、删除或修改后端 endpoint 时，必须同步更新本文。
2. 如果接口只处于规划阶段，不写入“接口总览”的已实现列表，应写入后端设计文档。
3. 如果 schema 字段变化，必须同步更新请求示例、响应示例和字段说明。
4. 如果权限 capability 变化，必须同步更新“全局约定”和具体接口章节。
5. 如果错误响应结构统一改造，需要同步更新第 8 章。
6. 如果后端 API 文档路径变化，需要同步更新 doc/开发文档/后端/INDEX.md。
```
