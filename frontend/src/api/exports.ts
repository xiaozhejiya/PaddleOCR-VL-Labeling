/**
 * 导出相关 API
 */
import { api } from './client'

export type ExportStatus = 'pending' | 'running' | 'completed' | 'failed'

export interface ExportJob {
  id: string
  project_id: string
  status: ExportStatus
  format: string
  created_at: string
  completed_at?: string
  download_url?: string
  error?: string
}

export interface ExportListResponse {
  items: ExportJob[]
  total: number
}

export const exportsApi = {
  /** 获取项目导出列表 */
  list: (projectId: string, _params?: { page?: number; page_size?: number }) =>
    api.get<ExportListResponse>(`/projects/${projectId}/exports`),

  /** 创建导出任务 */
  create: (projectId: string, data: { format: string; options?: Record<string, unknown> }) =>
    api.post<ExportJob>(`/projects/${projectId}/exports`, data),

  /** 获取导出任务详情 */
  get: (exportId: string) =>
    api.get<ExportJob>(`/exports/${exportId}`),

  /** 获取导出下载 URL */
  getDownloadUrl: (exportId: string) =>
    api.get<{ url: string; expires_at: string }>(`/exports/${exportId}/download`),
}
