/**
 * 质检(QC)相关 API
 */
import { api } from './client'

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
    api.get<QcListResponse>(`/pages/${pageId}/qc`),

  /** 获取项目 QC 问题列表 */
  listByProject: (projectId: string, _params?: { page?: number; page_size?: number; severity?: QcSeverity }) =>
    api.get<QcListResponse>(`/projects/${projectId}/qc`),
}
