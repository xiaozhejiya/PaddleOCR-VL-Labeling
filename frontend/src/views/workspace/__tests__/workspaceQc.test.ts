import { describe, expect, it } from 'vitest'

import type { QcIssue } from '@/api/qc'
import { getQcIssueSuggestion, getQcIssueTarget, getQcOverlayRegions, groupQcIssues } from '../workspaceQc'

describe('groupQcIssues', () => {
  it('按 failed > warning > passed 分组并保持固定顺序', () => {
    const issues: QcIssue[] = [
      {
        id: '2',
        page_id: 'page_1',
        severity: 'warning',
        code: 'geometry',
        message: 'warning issue',
        created_at: '2026-06-11T10:00:00Z',
      },
      {
        id: '1',
        page_id: 'page_1',
        severity: 'failed',
        code: 'schema',
        message: 'error issue',
        created_at: '2026-06-11T09:00:00Z',
      },
      {
        id: '3',
        page_id: 'page_1',
        severity: 'passed',
        code: 'dataset',
        message: 'info issue',
        created_at: '2026-06-11T11:00:00Z',
      },
    ]

    expect(groupQcIssues(issues)).toEqual([
      { severity: 'failed', items: [issues[1]] },
      { severity: 'warning', items: [issues[0]] },
      { severity: 'passed', items: [issues[2]] },
    ])
  })
})

describe('getQcIssueTarget', () => {
  it('优先使用 issue.annotation_id 和 bbox_xyxy', () => {
    const issue: QcIssue = {
      id: 'qc_1',
      page_id: 'page_1',
      annotation_id: 'ann_1',
      severity: 'failed',
      code: 'geometry',
      message: 'bbox 越界',
      details: {
        bbox_xyxy: [10, 20, 30, 40],
      },
      created_at: '2026-06-11T10:00:00Z',
    }

    expect(getQcIssueTarget(issue)).toEqual({
      annotationId: 'ann_1',
      bbox: [10, 20, 30, 40],
      isPageLevel: false,
    })
  })

  it('支持从 details.ann_id 和 polygon 推导定位框', () => {
    const issue: QcIssue = {
      id: 'qc_2',
      page_id: 'page_1',
      severity: 'warning',
      code: 'geometry',
      message: 'polygon 越界',
      details: {
        ann_id: 'ann_2',
        polygon: [[20, 40], [60, 20], [80, 90], [10, 100]],
      },
      created_at: '2026-06-11T10:00:00Z',
    }

    expect(getQcIssueTarget(issue)).toEqual({
      annotationId: 'ann_2',
      bbox: [10, 20, 80, 100],
      isPageLevel: false,
    })
  })

  it('页面级 issue 没有对象和区域时标记为 page-level', () => {
    const issue: QcIssue = {
      id: 'qc_3',
      page_id: 'page_1',
      severity: 'passed',
      code: 'dataset',
      message: '页面级提示',
      details: {},
      created_at: '2026-06-11T10:00:00Z',
    }

    expect(getQcIssueTarget(issue)).toEqual({
      annotationId: null,
      bbox: null,
      isPageLevel: true,
    })
  })
})

describe('getQcIssueSuggestion', () => {
  it('从 details.suggestion 读取修复建议', () => {
    const issue: QcIssue = {
      id: 'qc_4',
      page_id: 'page_1',
      severity: 'warning',
      code: 'read_order',
      message: 'read_order 不连续',
      details: {
        suggestion: '重新按阅读顺序点击对象',
      },
      created_at: '2026-06-11T10:00:00Z',
    }

    expect(getQcIssueSuggestion(issue)).toBe('重新按阅读顺序点击对象')
  })

  it('没有建议时返回 null', () => {
    const issue: QcIssue = {
      id: 'qc_5',
      page_id: 'page_1',
      severity: 'passed',
      code: 'dataset',
      message: '页面级提示',
      details: {},
      created_at: '2026-06-11T10:00:00Z',
    }

    expect(getQcIssueSuggestion(issue)).toBeNull()
  })
})

describe('getQcOverlayRegions', () => {
  it('仅为带 bbox/polygon 的 issue 生成 overlay 区域', () => {
    const issues: QcIssue[] = [
      {
        id: 'qc_1',
        page_id: 'page_1',
        severity: 'failed',
        code: 'geometry',
        message: 'bbox 越界',
        details: { bbox_xyxy: [10, 20, 30, 40] },
        created_at: '2026-06-11T10:00:00Z',
      },
      {
        id: 'qc_2',
        page_id: 'page_1',
        severity: 'warning',
        code: 'polygon',
        message: 'polygon 越界',
        details: { polygon: [[20, 40], [60, 20], [80, 90], [10, 100]] },
        created_at: '2026-06-11T10:00:00Z',
      },
      {
        id: 'qc_3',
        page_id: 'page_1',
        severity: 'passed',
        code: 'dataset',
        message: '页面级提示',
        details: {},
        created_at: '2026-06-11T10:00:00Z',
      },
    ]

    expect(getQcOverlayRegions(issues)).toEqual([
      {
        issueId: 'qc_1',
        severity: 'failed',
        bbox: [10, 20, 30, 40],
      },
      {
        issueId: 'qc_2',
        severity: 'warning',
        bbox: [10, 20, 80, 100],
      },
    ])
  })
})
