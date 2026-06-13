/**
 * API 模块统一导出
 */
export { api, ApiClientError, setToken, getToken, clearToken } from './client'
export type { ApiError } from './client'

export { authApi } from './auth'
export type { User, LoginRequest, LoginResponse } from './auth'

export { projectsApi } from './projects'
export type { Project, ProjectListResponse } from './projects'

export { pagesApi } from './pages'
export type { Page, PageListResponse } from './pages'

export { annotationsApi } from './annotations'
export type { AnnotationRevision, AnnotationDraft } from './annotations'

export { assetsApi } from './assets'
export type { Asset, AssetUploadResponse } from './assets'

export { qcApi } from './qc'
export type { QcIssue, QcListResponse, QcSeverity } from './qc'
