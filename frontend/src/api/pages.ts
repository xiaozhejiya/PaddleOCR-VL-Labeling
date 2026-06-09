/**
 * 页面相关 API
 */
import { api, mockFallback } from './client'
import { mockPages, mockCapabilities, mockDelay } from './mock'

export interface Page {
  page_id: string
  project_id: string
  filename: string
  status: string
  width: number
  height: number
  created_at: string
  updated_at: string
}

export interface PageListResponse {
  items: Page[]
  total: number
}

export interface Capabilities {
  can_edit: boolean
  can_review: boolean
  can_export: boolean
  can_manage: boolean
}

export const pagesApi = {
  /** 获取项目页面列表 */
  list: (projectId: string, _params?: { page?: number; page_size?: number }) =>
    mockFallback(
      () => api.get<PageListResponse>(`/projects/${projectId}/pages`),
      () => mockDelay({
        items: mockPages.filter(p => p.project_id === projectId),
        total: mockPages.filter(p => p.project_id === projectId).length,
      }),
    ),

  /** 获取页面详情 */
  get: (pageId: string) =>
    mockFallback(
      () => api.get<Page>(`/pages/${pageId}`),
      () => mockDelay(mockPages.find(p => p.page_id === pageId) || mockPages[0]),
    ),

  /** 获取页面图片访问 URL */
  getImageUrl: (pageId: string) =>
    api.get<{ url: string; expires_at: string }>(`/pages/${pageId}/image`),

  /** 获取用户在项目中的 capabilities */
  getCapabilities: (projectId: string) =>
    mockFallback(
      () => api.get<Capabilities>(`/projects/${projectId}/me/capabilities`),
      () => mockDelay(mockCapabilities),
    ),
}
