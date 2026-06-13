/**
 * 页面相关 API
 *
 * 后端接口契约参见：doc/开发文档/后端/backend_api_reference.md §7
 */
import { api, ApiClientError, fetchWithAuth, parseApiErrorResponse } from './client'

// ── 后端响应原始类型 ──

/** 后端 GET /pages/{page_id} 响应中的 data 字段 */
interface PageReadData {
  page_id: string
  document_id: string
  project_id: number
  page_index: number
  status: string
  capture_method: string | null
  visual_difficulty: string | null
  image: {
    asset_id: string | null
    width: number
    height: number
    sha256: string | null
  }
}

/** 后端包装响应 */
interface PageReadResponse {
  data: PageReadData
  request_id: string
}

// ── 前端使用类型 ──

/** 前端统一 Page 类型（从后端响应解包 + 扁平化） */
export interface Page {
  page_id: string
  document_id?: string
  project_id: number
  page_index?: number
  status: string
  capture_method?: string | null
  visual_difficulty?: string | null
  filename?: string
  width: number
  height: number
  image_asset_id?: string | null
  created_at?: string
  updated_at?: string
}

export interface PageListResponse {
  items: Page[]
  total: number
}

export interface Capabilities {
  can_view_project: boolean
  can_create_annotation_revision: boolean
  can_submit_revision: boolean
  can_review_revision: boolean
  can_create_export_job: boolean
  can_download_export: boolean
  can_manage_project_members: boolean
  can_manage_labels: boolean
  can_manage_relations: boolean
  can_lock_revision: boolean
  can_unlock_revision: boolean
  can_rollback_revision: boolean
  can_upload_assets: boolean
  can_import_pages: boolean
  can_view_audit_log: boolean
  can_manage_system_users: boolean
}

/** 将后端 PageReadData 解包为前端 Page */
function unwrapPage(res: PageReadResponse): Page {
  const d = res.data
  return {
    page_id: d.page_id,
    document_id: d.document_id,
    project_id: d.project_id,
    page_index: d.page_index,
    status: d.status,
    capture_method: d.capture_method,
    visual_difficulty: d.visual_difficulty,
    width: d.image.width,
    height: d.image.height,
    image_asset_id: d.image.asset_id,
  }
}

export const pagesApi = {
  /** 获取项目页面列表 */
  list: (projectId: string, params?: { page?: number; page_size?: number }) => {
    const query = new URLSearchParams()
    if (params?.page) query.set('page', String(params.page))
    if (params?.page_size) query.set('page_size', String(params.page_size))
    const qs = query.toString()
    return api.get<PageListResponse>(`/projects/${projectId}/pages${qs ? `?${qs}` : ''}`)
  },

  /** 获取页面详情（解包 { data, request_id } → Page） */
  get: async (pageId: string): Promise<Page> => {
    const res = await api.get<PageReadResponse>(`/pages/${pageId}`)
    return unwrapPage(res)
  },

  /** 获取页面图片访问 URL */
  getImageUrl: (pageId: string) =>
    api.get<{ url: string; expires_at: string }>(`/pages/${pageId}/image`),

  /** 获取页面图片二进制并转换为 object URL（调用方负责 revoke） */
  fetchImageBlob: async (pageId: string): Promise<string> => {
    const { url } = await pagesApi.getImageUrl(pageId)
    const response = await fetchWithAuth(url)
    if (!response.ok) {
      throw new ApiClientError(await parseApiErrorResponse(response))
    }

    const blob = await response.blob()
    return URL.createObjectURL(blob)
  },

  /** 获取用户在项目中的 capabilities */
  getCapabilities: (projectId: string) =>
    api.get<Capabilities>(`/projects/${projectId}/me/capabilities`),

  /** 删除页面 */
  delete: (pageId: string) =>
    api.delete<void>(`/pages/${pageId}`),
}
