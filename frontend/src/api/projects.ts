/**
 * 项目相关 API
 */
import { api, mockFallback } from './client'
import { mockProjects, mockDelay } from './mock'

export interface Project {
  id: string
  name: string
  description: string
  status: string
  created_at: string
  updated_at: string
}

export interface ProjectListResponse {
  items: Project[]
  total: number
}

export const projectsApi = {
  /** 获取项目列表 */
  list: (params?: { page?: number; size?: number }) => {
    const query = new URLSearchParams()
    if (params?.page) query.set('page', String(params.page))
    if (params?.size) query.set('size', String(params.size))
    const qs = query.toString()
    return mockFallback(
      () => api.get<ProjectListResponse>(`/projects${qs ? `?${qs}` : ''}`),
      () => mockDelay({ items: mockProjects, total: mockProjects.length }),
    )
  },

  /** 获取项目详情 */
  get: (projectId: string) =>
    mockFallback(
      () => api.get<Project>(`/projects/${projectId}`),
      () => mockDelay(mockProjects.find(p => p.id === projectId) || mockProjects[0]),
    ),

  /** 创建项目 */
  create: (data: { name: string; description?: string }) =>
    mockFallback(
      () => api.post<Project>('/projects', data),
      () => mockDelay({
        id: `proj-${Date.now()}`,
        name: data.name,
        description: data.description || '',
        status: 'active',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }),
    ),

  /** 更新项目 */
  update: (projectId: string, data: Partial<Project>) =>
    api.patch<Project>(`/projects/${projectId}`, data),

  /** 删除项目 */
  delete: (projectId: string) =>
    api.delete<void>(`/projects/${projectId}`),
}
