/**
 * 标注相关 API
 *
 * 后端接口契约参见：doc/开发文档/后端/backend_api_reference.md §7.2, §7.3
 */
import { api } from './client'

// ── 后端响应原始类型 ──

/** 后端 annotation revision 响应中的 data 字段 */
interface AnnotationRevisionData {
  revision_id: string
  page_id: string
  revision_no: number
  status: string
  qc_status: string
  sha256: string | null
  size_bytes: number | null
  annotation_json: Record<string, unknown>
}

/** 后端包装响应 */
interface AnnotationRevisionResponse {
  data: AnnotationRevisionData
  request_id: string
}

// ── 前端使用类型 ──

/** 前端统一 AnnotationRevision 类型（从后端解包） */
export interface AnnotationRevision {
  id: string
  page_id: string
  revision_no: number
  status: string
  qc_status: string
  data: Record<string, unknown>
}

/** 保存标注时的提交体（后端包装形式） */
interface AnnotationSavePayload {
  annotation_json: Record<string, unknown>
  base_revision_id?: string | null
  change_summary?: string
  change_reason?: string
}

/** 前端保存标注用的 draft */
export interface AnnotationDraft {
  page_id: string
  base_revision_id?: string | null
  data: Record<string, unknown>
}

/** 将后端 AnnotationRevisionData 解包为前端 AnnotationRevision */
function unwrapRevision(res: AnnotationRevisionResponse): AnnotationRevision {
  const d = res.data
  return {
    id: d.revision_id,
    page_id: d.page_id,
    revision_no: d.revision_no,
    status: d.status,
    qc_status: d.qc_status,
    data: d.annotation_json,
  }
}

export const annotationsApi = {
  /** 获取页面最新标注（解包 { data, request_id } → AnnotationRevision） */
  getLatest: async (pageId: string): Promise<AnnotationRevision> => {
    const res = await api.get<AnnotationRevisionResponse>(`/pages/${pageId}/annotation/latest`)
    return unwrapRevision(res)
  },

  /** 保存标注修订（包装为后端要求的 { annotation_json, base_revision_id } 格式） */
  save: async (pageId: string, draft: AnnotationDraft): Promise<AnnotationRevision> => {
    const payload: AnnotationSavePayload = {
      annotation_json: draft.data,
      base_revision_id: draft.base_revision_id ?? null,
    }
    const res = await api.post<AnnotationRevisionResponse>(
      `/pages/${pageId}/annotation/revisions`,
      payload,
    )
    return unwrapRevision(res)
  },

  /** 获取标注历史（当前后端未实现，保留接口） */
  listRevisions: async (pageId: string): Promise<AnnotationRevision[]> => {
    // 后端暂无此接口，返回空数组
    console.warn(`listRevisions not implemented for page ${pageId}`)
    return []
  },
}
