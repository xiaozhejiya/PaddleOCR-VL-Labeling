/**
 * 后台任务相关 API
 */
import { api } from './client'

export type JobStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
export type JobType = 'import' | 'export' | 'ocr' | 'qc' | 'other'

export interface Job {
  id: string
  project_id: string
  type: JobType
  status: JobStatus
  progress: number
  created_at: string
  started_at?: string
  completed_at?: string
  error?: string
}

export interface JobListResponse {
  items: Job[]
  total: number
}

export const jobsApi = {
  /** 获取项目任务列表 */
  list: (projectId: string, _params?: { page?: number; page_size?: number; status?: JobStatus }) =>
    api.get<JobListResponse>(`/projects/${projectId}/jobs`),

  /** 获取任务详情 */
  get: (jobId: string) =>
    api.get<Job>(`/jobs/${jobId}`),

  /** 取消任务 */
  cancel: (jobId: string) =>
    api.post<void>(`/jobs/${jobId}/cancel`),
}
