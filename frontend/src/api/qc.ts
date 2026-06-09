/**
 * 质检(QC)相关 API
 */
import { api, mockFallback } from './client'
import { mockQcIssues, mockDelay } from './mock'

export type QcSeverity = 'error' | 'warning' | 'info'

export interface QcIssue {
  id: string
  page_id: string
  annotation_id?: string
  severity: QcSeverity
  code: string
  message: string
  details?: Record<string, unknown>
  created_at: string
}

export interface QcListResponse {
  items: QcIssue[]
  total: number
}

export const qcApi = {
  /** 获取页面 QC 问题列表 */
  listByPage: (pageId: string) =>
    mockFallback(
      () => api.get<QcListResponse>(`/pages/${pageId}/qc`),
      () => mockDelay({
        items: mockQcIssues.filter(q => q.page_id === pageId),
        total: mockQcIssues.filter(q => q.page_id === pageId).length,
      }),
    ),

  /** 获取项目 QC 问题列表 */
  listByProject: (projectId: string, _params?: { page?: number; page_size?: number; severity?: QcSeverity }) =>
    api.get<QcListResponse>(`/projects/${projectId}/qc`),
}
