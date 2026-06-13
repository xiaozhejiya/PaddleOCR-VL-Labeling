import { api } from './client'

export interface ProjectLabel {
  id: number | null
  project_id: number | null
  namespace: string
  name: string
  display_name: string
  display_name_i18n?: Record<string, string> | null
  geometry_types: string[]
  attributes_schema: Record<string, unknown>
  default_color?: string | null
  is_builtin: boolean
  is_active: boolean
}

export interface ProjectLabelListResponse {
  items: ProjectLabel[]
  total: number
}

export const labelsApi = {
  listByProject: (projectId: string) =>
    api.get<ProjectLabelListResponse>(`/projects/${projectId}/labels`),
}
