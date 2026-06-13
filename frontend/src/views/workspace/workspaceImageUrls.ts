export function revokeObjectUrl(url: string | null) {
  if (!url) return
  if (url.startsWith('blob:')) {
    URL.revokeObjectURL(url)
  }
}

export function syncThumbnailObjectUrls(params: {
  current: Record<string, string>
  nextPageIds: string[]
}): Record<string, string> {
  const nextPageIdSet = new Set(params.nextPageIds)

  for (const [pageId, url] of Object.entries(params.current)) {
    if (!nextPageIdSet.has(pageId)) {
      revokeObjectUrl(url)
    }
  }

  return Object.fromEntries(
    Object.entries(params.current).filter(([pageId]) => nextPageIdSet.has(pageId))
  )
}
