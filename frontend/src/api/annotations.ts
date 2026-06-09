/**
 * 标注相关 API
 */
import { api } from './client'

export interface AnnotationRevision {
  id: string
  page_id: string
  revision_no: number
  base_revision_id?: string
  created_at: string
  created_by: string
  data: Record<string, unknown>
}

export interface AnnotationDraft {
  page_id: string
  base_revision_id: string
  data: Record<string, unknown>
}

export const annotationsApi = {
  /** 获取页面最新标注 */
  getLatest: (pageId: string) =>
    api.get<AnnotationRevision>(`/pages/${pageId}/annotations/latest`),

  /** 保存标注修订 */
  save: (pageId: string, draft: AnnotationDraft) =>
    api.post<AnnotationRevision>(`/pages/${pageId}/annotations`, draft),

  /** 获取标注历史 */
  listRevisions: (pageId: string) =>
    api.get<AnnotationRevision[]>(`/pages/${pageId}/annotations`),
}
