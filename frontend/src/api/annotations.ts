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
  data: AnnotationRevisionData | null
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

export interface AnnotationRevisionListItem {
  id: string
  page_id: string
  revision_no: number
  status: string
  qc_status: string
  created_at?: string | null
  change_summary?: string | null
}

export interface AnnotationRevisionListResponse {
  items: AnnotationRevisionListItem[]
  total: number
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
function unwrapRevision(res: AnnotationRevisionResponse): AnnotationRevision | null {
  const d = res.data
  if (!d) {
    return null
  }
  return {
    id: d.revision_id,
    page_id: d.page_id,
    revision_no: d.revision_no,
    status: d.status,
    qc_status: d.qc_status,
    data: d.annotation_json,
  }
}

function unwrapRequiredRevision(res: AnnotationRevisionResponse): AnnotationRevision {
  const revision = unwrapRevision(res)
  if (!revision) {
    throw new Error('Annotation revision response data is unexpectedly null.')
  }
  return revision
}

export const annotationsApi = {
  /** 获取页面最新标注；页面尚无标注时返回 null */
  getLatest: async (pageId: string): Promise<AnnotationRevision | null> => {
    const res = await api.get<AnnotationRevisionResponse>(`/pages/${pageId}/annotation/latest`)
    return unwrapRevision(res)
  },

  /** 获取页面指定 revision */
  getRevision: async (pageId: string, revisionId: string): Promise<AnnotationRevision> => {
    const res = await api.get<AnnotationRevisionResponse>(
      `/pages/${pageId}/annotation/revisions/${revisionId}`,
    )
    return unwrapRequiredRevision(res)
  },

  /** 列出页面所有 revisions（只返回元数据，不包含 annotation_json） */
  listRevisions: async (
    pageId: string,
    params?: { limit?: number; offset?: number },
  ): Promise<AnnotationRevisionListResponse> => {
    const query = new URLSearchParams()
    if (params?.limit) query.set('limit', String(params.limit))
    if (params?.offset) query.set('offset', String(params.offset))
    const qs = query.toString()
    const raw = await api.get<{
      items: Array<{
        revision_id: string
        page_id: string
        revision_no: number
        status: string
        qc_status: string
        created_at?: string | null
        change_summary?: string | null
      }>
      total: number
    }>(`/pages/${pageId}/annotation/revisions${qs ? `?${qs}` : ''}`)

    return {
      total: raw.total,
      items: raw.items.map((it) => ({
        id: it.revision_id,
        page_id: it.page_id,
        revision_no: it.revision_no,
        status: it.status,
        qc_status: it.qc_status,
        created_at: it.created_at ?? null,
        change_summary: it.change_summary ?? null,
      })),
    }
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
    return unwrapRequiredRevision(res)
  },
}
