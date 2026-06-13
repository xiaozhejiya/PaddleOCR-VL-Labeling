/**
 * 项目相关 API
 * 后端：/api/v1/projects
 */
import { api } from './client'

/** 后端返回的原始项目数据 */
interface RawProject {
  id: number
  name: string
  description: string | null
  schema_version: string
  created_at: string
  updated_at: string
}

export interface Project {
  id: string
  name: string
  description: string | null
  schema_version: string
  created_at: string
  updated_at: string
}

export interface ProjectListResponse {
  items: Project[]
  total: number
}

function adaptProject(raw: RawProject): Project {
  return { ...raw, id: String(raw.id) }
}

export const projectsApi = {
  /** 获取项目列表 */
  list: async (params?: { page?: number; size?: number }): Promise<ProjectListResponse> => {
    const query = new URLSearchParams()
    if (params?.page) query.set('page', String(params.page))
    if (params?.size) query.set('size', String(params.size))
    const qs = query.toString()
    const res = await api.get<{ items: RawProject[]; total: number }>(`/projects${qs ? `?${qs}` : ''}`)
    return { items: res.items.map(adaptProject), total: res.total }
  },

  /** 获取项目详情 */
  get: async (projectId: string): Promise<Project> => {
    const raw = await api.get<RawProject>(`/projects/${projectId}`)
    return adaptProject(raw)
  },

  /** 创建项目 */
  create: async (data: { name: string; description?: string }): Promise<Project> => {
    const raw = await api.post<RawProject>('/projects', data)
    return adaptProject(raw)
  },

  /** 更新项目 */
  update: async (projectId: string, data: Partial<Project>): Promise<Project> => {
    const raw = await api.patch<RawProject>(`/projects/${projectId}`, data)
    return adaptProject(raw)
  },

  /** 删除项目 */
  delete: (projectId: string) =>
    api.delete<void>(`/projects/${projectId}`),
}
