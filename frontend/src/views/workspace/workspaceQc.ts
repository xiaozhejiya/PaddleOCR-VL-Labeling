import type { QcIssue, QcSeverity } from '@/api/qc'

export interface QcIssueGroup {
  severity: QcSeverity
  items: QcIssue[]
}

export interface QcIssueTarget {
  annotationId: string | null
  bbox: [number, number, number, number] | null
  isPageLevel: boolean
}

export interface QcOverlayRegion {
  issueId: string
  severity: QcSeverity
  bbox: [number, number, number, number]
}

const SEVERITY_ORDER: QcSeverity[] = ['failed', 'warning', 'passed']

function isNumberArray(value: unknown, length: number): value is number[] {
  return Array.isArray(value) && value.length === length && value.every(item => typeof item === 'number')
}

function parsePolygon(value: unknown): Array<[number, number]> | null {
  if (!Array.isArray(value) || value.length < 3) {
    return null
  }

  const points = value.filter(
    (item): item is [number, number] => Array.isArray(item) && item.length === 2 && item.every(v => typeof v === 'number'),
  )

  return points.length >= 3 ? points : null
}

function polygonToBbox(polygon: Array<[number, number]>): [number, number, number, number] {
  const xs = polygon.map(point => point[0])
  const ys = polygon.map(point => point[1])
  return [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)]
}

export function groupQcIssues(issues: QcIssue[]): QcIssueGroup[] {
  return SEVERITY_ORDER
    .map((severity) => ({
      severity,
      items: issues.filter(issue => issue.severity === severity),
    }))
    .filter(group => group.items.length > 0)
}

export function getQcIssueTarget(issue: QcIssue): QcIssueTarget {
  const details = issue.details ?? {}
  const annotationId = issue.annotation_id
    ?? (typeof details.annotation_id === 'string' ? details.annotation_id : null)
    ?? (typeof details.ann_id === 'string' ? details.ann_id : null)

  const bboxRaw = details.bbox_xyxy ?? details.bbox
  const bbox = isNumberArray(bboxRaw, 4)
    ? [bboxRaw[0], bboxRaw[1], bboxRaw[2], bboxRaw[3]] as [number, number, number, number]
    : null

  if (bbox) {
    return {
      annotationId,
      bbox,
      isPageLevel: false,
    }
  }

  const polygon = parsePolygon(details.polygon)
  if (polygon) {
    return {
      annotationId,
      bbox: polygonToBbox(polygon),
      isPageLevel: false,
    }
  }

  return {
    annotationId,
    bbox: null,
    isPageLevel: annotationId === null,
  }
}

export function getQcIssueSuggestion(issue: QcIssue): string | null {
  const details = issue.details ?? {}
  const suggestion = details.suggestion ?? details.recommendation ?? details.hint
  return typeof suggestion === 'string' && suggestion.trim() ? suggestion.trim() : null
}

export function getQcOverlayRegions(issues: QcIssue[]): QcOverlayRegion[] {
  return issues
    .map((issue) => {
      const target = getQcIssueTarget(issue)
      if (!target.bbox) return null
      return {
        issueId: issue.id,
        severity: issue.severity,
        bbox: target.bbox,
      } satisfies QcOverlayRegion
    })
    .filter((item): item is QcOverlayRegion => item !== null)
}
