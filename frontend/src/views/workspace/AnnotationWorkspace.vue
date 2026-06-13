<script setup lang="ts">
/**
 * 标注工作台页面
 * 通过 AnnotationWorkspaceLayout 提供布局
 * 负责加载 page 元数据、图片、latest revision、label registry
 *
 * 参考：doc/开发文档/前端/frontend_routing_spec.md 第 14 章
 */
import { ref, computed, onMounted, onUnmounted, inject, watch, nextTick, type Ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { pagesApi, type Page, type Capabilities } from '@/api/pages'
import { annotationsApi, type AnnotationRevision, type AnnotationDraft } from '@/api/annotations'
import { labelsApi, type ProjectLabel } from '@/api/labels'
import { qcApi, type QcIssue } from '@/api/qc'
import { annotationsApi as saveApi } from '@/api/annotations'
import { ApiClientError } from '@/api/client'
import AnnotationCanvas from '@/components/annotation/AnnotationCanvas.vue'
import { getDefaultColor, type AnnotationObject } from '@/composables/useAnnotationStore'
import { SAVE_STATUS_KEY, UPDATE_SAVE_STATUS_KEY, computeCanWriteAnnotation, type SaveStatus } from './workspaceGuards'
import { revokeObjectUrl, syncThumbnailObjectUrls } from './workspaceImageUrls'
import { getQcIssueSuggestion, getQcIssueTarget, getQcOverlayRegions, groupQcIssues } from './workspaceQc'
import {
  MousePointer2,
  SquareDashedMousePointer,
  BookOpen,
  Hand,
  ZoomIn,
  ZoomOut,
  Maximize,
  Expand,
  Undo2,
  Redo2,
  Trash2,
  Fullscreen,
  Save,
  Loader2,
  ChevronLeft,
  ChevronRight,
} from 'lucide-vue-next'

const { t, locale } = useI18n()
const route = useRoute()
const router = useRouter()

const pageId = computed(() => route.params.page_id as string)
const revisionId = computed(() => route.query.revision_id as string | undefined)

type ActiveTool = 'select' | 'bbox' | 'read_order' | 'pan'

function getReadonlyCapabilities(): Capabilities {
  return {
    can_view_project: true,
    can_create_annotation_revision: false,
    can_submit_revision: false,
    can_review_revision: false,
    can_create_export_job: false,
    can_download_export: false,
    can_manage_project_members: false,
    can_manage_labels: false,
    can_manage_relations: false,
    can_lock_revision: false,
    can_unlock_revision: false,
    can_rollback_revision: false,
    can_upload_assets: false,
    can_import_pages: false,
    can_view_audit_log: false,
    can_manage_system_users: false,
  }
}

// ── 状态 ──
const loading = ref(true)
const error = ref('')
const errorCode = ref<number | undefined>()
const saving = ref(false)

// ── 数据 ──
const page = ref<Page | null>(null)
const capabilities = ref<Capabilities | null>(null)
const revision = ref<AnnotationRevision | null>(null)
const labels = ref<ProjectLabel[]>([])
const qcIssues = ref<QcIssue[]>([])
const activeQcIssueId = ref<string | null>(null)
const imageUrl = ref<string | null>(null)

// ── 页面列表（同项目） ──
const pageList = ref<Page[]>([])
const thumbnailUrls = ref<Record<string, string>>({})
const currentIndex = computed(() => pageList.value.findIndex(p => p.page_id === pageId.value))
const hasPrev = computed(() => currentIndex.value > 0)
const hasNext = computed(() => currentIndex.value < pageList.value.length - 1)

const isReadonly = computed(() => {
  if (revisionId.value) return true
  if (!capabilities.value?.can_create_annotation_revision) return true
  return false
})

const saveStatus = inject<Ref<SaveStatus> | null>(SAVE_STATUS_KEY, null)
const updateSaveStatus = inject<((status: SaveStatus) => void) | undefined>(UPDATE_SAVE_STATUS_KEY)
const isConflict = computed(() => saveStatus?.value === 'conflict')
const conflictDraft = ref<AnnotationDraft | null>(null)
const pendingHydration = ref<{ page: Page; revision: AnnotationRevision | null } | null>(null)

function syncWorkspaceMeta(status?: SaveStatus) {
  if (status) {
    updateSaveStatus?.(status)
  } else {
    updateSaveStatus?.(isReadonly.value ? 'readonly' : 'saved')
  }
}

const canWriteAnnotation = computed(() => computeCanWriteAnnotation({
  can_create_annotation_revision: Boolean(capabilities.value?.can_create_annotation_revision),
  revision_id: revisionId.value ?? null,
  saving: saving.value,
  save_status: saveStatus?.value ?? null,
}))

const canWrite = computed(() => canWriteAnnotation.value)

// ── 工具栏状态 ──
const activeTool = ref<ActiveTool>('select')
const zoomLevel = ref(100)
const canvasRef = ref<InstanceType<typeof AnnotationCanvas> | null>(null)

const tools = [
  { key: 'select', icon: MousePointer2, label: 'annotation.tools.select', shortcut: 'V' },
  { key: 'bbox', icon: SquareDashedMousePointer, label: 'annotation.tools.bbox', shortcut: 'W' },
  { key: 'read_order', icon: BookOpen, label: 'annotation.tools.read_order', shortcut: 'R' },
  { key: 'pan', icon: Hand, label: 'annotation.tools.pan', shortcut: 'Space' },
]

// ── 右侧面板 ──
const objectCount = ref(0)
const qcCount = ref(0)

// ── 标签数据 ──
const activeLabelKey = ref<string | null>(null)
const groupedQcIssues = computed(() => groupQcIssues(qcIssues.value))
const qcOverlayRegions = computed(() => getQcOverlayRegions(qcIssues.value))

function getLabelKey(label: Pick<ProjectLabel, 'namespace' | 'name'>): string {
  return `${label.namespace}:${label.name}`
}

function findLabel(name: string, namespace: string): ProjectLabel | undefined {
  return labels.value.find(label => label.name === name && label.namespace === namespace)
}

function getLabelDisplayName(label: ProjectLabel): string {
  return label.display_name_i18n?.[locale.value] || label.display_name || label.name
}

function getLabelColor(name: string, namespace = 'k12'): string {
  return findLabel(name, namespace)?.default_color || getDefaultColor(name)
}

const activeLabel = computed(() => {
  const label = labels.value.find(item => getLabelKey(item) === activeLabelKey.value)
  if (!label) return null
  return {
    name: label.name,
    namespace: label.namespace,
    color: getLabelColor(label.name, label.namespace),
  }
})

function syncActiveLabel() {
  if (labels.value.length === 0) {
    activeLabelKey.value = null
    return
  }

  const exists = labels.value.some(label => getLabelKey(label) === activeLabelKey.value)
  if (!exists) {
    activeLabelKey.value = getLabelKey(labels.value[0])
  }
}

function setActiveTool(nextTool: ActiveTool) {
  if (nextTool === 'read_order' && !canWriteAnnotation.value) {
    return
  }
  activeTool.value = nextTool
}

function getLabelText(type: string, namespace = 'k12') {
  const label = findLabel(type, namespace)
  return label ? getLabelDisplayName(label) : type
}

// ── 选中对象属性 ──
const selectedObject = ref<AnnotationObject | null>(null)

function onObjectSelected(id: string | null) {
  if (!id) {
    selectedObject.value = null
    return
  }
  selectedObject.value = canvasRef.value?.store.objects.value.find(o => o.id === id) || null
}

function onObjectsChanged() {
  if (!canvasRef.value) return
  const store = canvasRef.value.store
  objectCount.value = store.objects.value.length
  selectedObject.value = store.selectedObject.value
  if (canWriteAnnotation.value) {
    syncWorkspaceMeta('dirty')
  }
}

// ── 属性编辑 ──
function onLabelChange(e: Event) {
  if (!canWriteAnnotation.value) return
  const labelKey = (e.target as HTMLSelectElement).value
  const label = labels.value.find(item => getLabelKey(item) === labelKey)
  if (selectedObject.value && canvasRef.value) {
    if (!label) return
    const color = getLabelColor(label.name, label.namespace)
    canvasRef.value.store.updateObject(selectedObject.value.id, {
      type: label.name,
      label_namespace: label.namespace,
      color,
    })
    onObjectsChanged()
  }
}

function onReadOrderChange(e: Event) {
  if (!canWriteAnnotation.value) return
  const order = parseInt((e.target as HTMLInputElement).value, 10)
  if (selectedObject.value && canvasRef.value && !isNaN(order)) {
    canvasRef.value.store.setReadOrder(selectedObject.value.id, order)
    onObjectsChanged()
  }
}

function clearReadOrder() {
  if (!canWriteAnnotation.value) return
  canvasRef.value?.store.clearReadOrder()
  onObjectsChanged()
}

function focusImageRegion(bbox: [number, number, number, number]) {
  const canvas = canvasRef.value
  if (!canvas) return

  const [xmin, ymin, xmax, ymax] = bbox
  const width = Math.max(xmax - xmin, 1)
  const height = Math.max(ymax - ymin, 1)
  const renderer = canvas.renderer
  const viewport = renderer.viewport.value
  const nextScale = Math.min(Math.max(Math.min((viewport.w * 0.8) / width, (viewport.h * 0.8) / height), 0.05), 20)
  const centerX = (xmin + xmax) / 2
  const centerY = (ymin + ymax) / 2

  renderer.scale.value = nextScale
  renderer.offset.value = {
    x: viewport.w / 2 - centerX * nextScale,
    y: viewport.h / 2 - centerY * nextScale,
  }
  canvas.redraw()
  zoomLevel.value = renderer.zoomPercent.value
}

function getQcIssueTargetLabel(issue: QcIssue): string {
  const target = getQcIssueTarget(issue)
  if (target.annotationId) {
    return t('annotation.qc.targetObject', { id: target.annotationId })
  }
  return t('annotation.qc.pageLevel')
}

function getQcIssueSeverityClass(severity: QcIssue['severity']): string {
  if (severity === 'failed') return 'bg-danger-bg text-danger'
  if (severity === 'warning') return 'bg-warning-bg text-warning'
  return 'bg-success-bg text-success'
}

function getQcIssueSuggestionText(issue: QcIssue): string | null {
  return getQcIssueSuggestion(issue)
}

function locateQcIssue(issue: QcIssue) {
  const canvas = canvasRef.value
  if (!canvas) return

  activeQcIssueId.value = issue.id
  const target = getQcIssueTarget(issue)
  const matchedObject = target.annotationId
    ? canvas.store.objects.value.find(obj => obj.id === target.annotationId)
    : null

  setActiveTool('select')

  if (matchedObject) {
    canvas.store.select(matchedObject.id)
    onObjectSelected(matchedObject.id)
    if (matchedObject.geometry.bbox_xyxy) {
      focusImageRegion(matchedObject.geometry.bbox_xyxy)
    }
    return
  }

  canvas.store.select(null)
  onObjectSelected(null)
  if (target.bbox) {
    focusImageRegion(target.bbox)
  }
}

// ── 保存 ──
async function saveAnnotation() {
  if (!canvasRef.value || !page.value || !canWriteAnnotation.value) return
  saving.value = true
  syncWorkspaceMeta('manual_saving')
  try {
    const draft = canvasRef.value.store.toDraft(page.value.page_id)
    console.log('[DEBUG] 保存标注:', { pageId: page.value.page_id, base_revision_id: draft.base_revision_id, draft })
    conflictDraft.value = null
    const result = await saveApi.save(page.value.page_id, draft)
    canvasRef.value.store.baseRevisionId.value = result.id
    canvasRef.value.store.revisionNo.value = result.revision_no
    revision.value = result
    syncWorkspaceMeta('saved')
  } catch (e) {
    if (e instanceof ApiClientError && e.status === 409) {
      if (page.value) {
        conflictDraft.value = canvasRef.value.store.toDraft(page.value.page_id)
      }
      syncWorkspaceMeta('conflict')
    } else if (e instanceof ApiClientError && e.status === 403) {
      if (page.value) {
        try {
          capabilities.value = await pagesApi.getCapabilities(String(page.value.project_id))
        } catch {
          capabilities.value = getReadonlyCapabilities()
        }
      }
      error.value = t('errors.forbidden')
      errorCode.value = 403
      syncWorkspaceMeta('readonly')
    } else {
      syncWorkspaceMeta('autosave_failed')
    }
  } finally {
    saving.value = false
  }
}

async function saveAsNewRevisionFromConflict() {
  if (!isConflict.value) return
  if (!page.value || !canvasRef.value) return
  if (saving.value) return

  const confirmed = window.confirm(t('workspace.conflictRebaseConfirm'))
  if (!confirmed) return

  saving.value = true
  syncWorkspaceMeta('manual_saving')
  try {
    const latest = await annotationsApi.getLatest(page.value.page_id)
    const draft = conflictDraft.value ?? canvasRef.value.store.toDraft(page.value.page_id)
    const rebased: AnnotationDraft = {
      page_id: page.value.page_id,
      base_revision_id: latest?.id ?? null,
      data: draft.data,
    }
    const result = await saveApi.save(page.value.page_id, rebased)
    canvasRef.value.store.baseRevisionId.value = result.id
    canvasRef.value.store.revisionNo.value = result.revision_no
    revision.value = result
    conflictDraft.value = null
    syncWorkspaceMeta('saved')
  } catch (e) {
    if (e instanceof ApiClientError && e.status === 409) {
      conflictDraft.value = canvasRef.value.store.toDraft(page.value.page_id)
      syncWorkspaceMeta('conflict')
    } else if (e instanceof ApiClientError && e.status === 403) {
      syncWorkspaceMeta('readonly')
    } else {
      syncWorkspaceMeta('autosave_failed')
    }
  } finally {
    saving.value = false
  }
}

async function rebaseConflictAndContinueEditing() {
  if (!isConflict.value) return
  if (!page.value || !canvasRef.value) return
  if (saving.value) return

  const confirmed = window.confirm(t('workspace.conflictRebaseConfirm'))
  if (!confirmed) return

  try {
    const latest = await annotationsApi.getLatest(page.value.page_id)
    canvasRef.value.store.baseRevisionId.value = latest?.id ?? undefined
    canvasRef.value.store.revisionNo.value = latest?.revision_no ?? 0
    revision.value = latest
    syncWorkspaceMeta('dirty')
  } catch {
    syncWorkspaceMeta('conflict')
  }
}

function discardLocalChangesAndReloadLatest() {
  if (!isConflict.value) return
  const confirmed = window.confirm(t('workspace.conflictDiscardConfirm'))
  if (!confirmed) return
  conflictDraft.value = null
  loadWorkspace()
}

function exportConflictDraftJson() {
  if (!page.value || !canvasRef.value) return
  const draft = conflictDraft.value ?? canvasRef.value.store.toDraft(page.value.page_id)
  const json = JSON.stringify(draft.data, null, 2)
  const blob = new Blob([json], { type: 'application/json;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `annotation_draft_${page.value.page_id}_${Date.now()}.json`
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

// ── 缩放控制 ──
function onZoomIn() {
  canvasRef.value?.renderer.zoomIn()
  canvasRef.value?.redraw()
  zoomLevel.value = canvasRef.value?.renderer.zoomPercent.value || 100
}

function onZoomOut() {
  canvasRef.value?.renderer.zoomOut()
  canvasRef.value?.redraw()
  zoomLevel.value = canvasRef.value?.renderer.zoomPercent.value || 100
}

function onFitWidth() {
  canvasRef.value?.renderer.fitToWidth()
  canvasRef.value?.redraw()
  zoomLevel.value = canvasRef.value?.renderer.zoomPercent.value || 100
}

function onFitPage() {
  canvasRef.value?.renderer.fitToContainer()
  canvasRef.value?.redraw()
  zoomLevel.value = canvasRef.value?.renderer.zoomPercent.value || 100
}

function onZoomLevelUpdate(val: number) {
  zoomLevel.value = val
}

// ── 撤销/重做/删除 ──
function onUndo() {
  if (!canWriteAnnotation.value) return
  canvasRef.value?.store.undo()
  onObjectsChanged()
}

function onRedo() {
  if (!canWriteAnnotation.value) return
  canvasRef.value?.store.redo()
  onObjectsChanged()
}

function onDelete() {
  if (!canWriteAnnotation.value) return
  canvasRef.value?.store.deleteSelected()
  onObjectsChanged()
}

function onDeleteObject(id: string) {
  if (!canWriteAnnotation.value) return
  canvasRef.value?.store.deleteObject(id)
  onObjectsChanged()
}

// ── 页面导航 ──
function goToPage(targetPageId: string) {
  if (targetPageId === pageId.value) return
  router.push({ name: 'pages.workspace', params: { page_id: targetPageId } })
}

function goToPrevPage() {
  if (hasPrev.value) goToPage(pageList.value[currentIndex.value - 1].page_id)
}

function goToNextPage() {
  if (hasNext.value) goToPage(pageList.value[currentIndex.value + 1].page_id)
}

async function loadPageList(projectId: string) {
  try {
    const res = await pagesApi.list(projectId)
    thumbnailUrls.value = syncThumbnailObjectUrls({
      current: thumbnailUrls.value,
      nextPageIds: res.items.map(item => item.page_id),
    })
    pageList.value = res.items

    for (const p of res.items) {
      if (!thumbnailUrls.value[p.page_id]) {
        try {
          const url = await pagesApi.fetchImageBlob(p.page_id)
          thumbnailUrls.value[p.page_id] = url
        } catch { /* 缩略图加载失败不影响功能 */ }
      }
    }
  } catch { /* 页面列表加载失败不阻止工作台 */ }
}

async function loadLabels(projectId: string) {
  try {
    const response = await labelsApi.listByProject(projectId)
    labels.value = response.items
  } catch {
    labels.value = []
  }
  syncActiveLabel()
}

function syncLoadedObjectColors() {
  const store = canvasRef.value?.store
  if (!store) return
  for (const obj of store.objects.value) {
    obj.color = getLabelColor(obj.type, obj.label_namespace)
  }
}

function hydrateStoreFromLoadedData(targetPage: Page, targetRevision: AnnotationRevision | null) {
  if (!canvasRef.value) {
    pendingHydration.value = { page: targetPage, revision: targetRevision }
    return
  }
  canvasRef.value.store.setImageBounds(targetPage.width, targetPage.height)
  canvasRef.value.store.loadFromRevision(targetRevision)
  syncLoadedObjectColors()
  objectCount.value = canvasRef.value.store.objects.value.length
}

async function loadImageUrl(targetPageId: string): Promise<string | null> {
  try {
    const url = await pagesApi.fetchImageBlob(targetPageId)
    return url
  } catch {
    return null
  }
}

// ── 键盘快捷键 ──
function onKeyDown(e: KeyboardEvent) {
  const target = e.target as HTMLElement | null
  const tagName = target?.tagName
  if (target?.isContentEditable || tagName === 'INPUT' || tagName === 'TEXTAREA' || tagName === 'SELECT') {
    return
  }

  if (e.defaultPrevented) return

  // Delete / Backspace: 删除选中对象
  if (e.key === 'Delete' || e.key === 'Backspace' || e.key === 'Del' || e.code === 'Delete') {
    e.preventDefault()
    if (canWriteAnnotation.value) {
      onDelete()
    }
    return
  }

  // 快捷键切换工具
  if (!e.ctrlKey && !e.metaKey) {
    if (e.key === 'v' || e.key === 'V') { setActiveTool('select'); e.preventDefault() }
    if ((e.key === 'w' || e.key === 'W') && canWrite.value) { setActiveTool('bbox'); e.preventDefault() }
    if ((e.key === 'r' || e.key === 'R') && canWrite.value) { setActiveTool('read_order'); e.preventDefault() }
    // 页面切换
    if (e.key === 'a' || e.key === 'A') { goToPrevPage(); e.preventDefault() }
    if (e.key === 'd' || e.key === 'D') { goToNextPage(); e.preventDefault() }
  }
  // Ctrl+S 保存
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault()
    if (canWriteAnnotation.value) {
      saveAnnotation()
    }
  }
}

onMounted(() => { window.addEventListener('keydown', onKeyDown) })
onUnmounted(() => { window.removeEventListener('keydown', onKeyDown) })

watch([activeTool, canWriteAnnotation, canvasRef], ([tool, canWrite]) => {
  const store = canvasRef.value?.store
  if (!store) return

  if (tool === 'read_order' && canWrite) {
    store.startReadOrderSession()
    return
  }

  store.endReadOrderSession()
  if (tool === 'read_order' && !canWrite) {
    activeTool.value = 'select'
  }
})

// ── 加载数据 ──
const isInitialLoad = ref(true)

async function loadWorkspace() {
  error.value = ''
  errorCode.value = undefined

  // 仅首次加载显示全屏 spinner，页面切换时保留旧内容避免闪烁
  if (isInitialLoad.value) {
    loading.value = true
  }

  try {
    if (!pageId.value) {
      error.value = t('errors.notFound')
      errorCode.value = 404
      syncWorkspaceMeta()
      return
    }

    try {
      page.value = await pagesApi.get(pageId.value)
    } catch (e) {
      if (e instanceof ApiClientError) {
        errorCode.value = e.status
        if (e.status === 404) error.value = t('errors.notFound')
        else if (e.status === 403) error.value = t('errors.forbidden')
        else error.value = t('errors.server')
      }
      syncWorkspaceMeta()
      return
    }

    try {
      capabilities.value = await pagesApi.getCapabilities(String(page.value.project_id))
    } catch (e) {
      if (e instanceof ApiClientError && e.status === 403) {
        error.value = t('errors.forbidden')
        errorCode.value = 403
        syncWorkspaceMeta('readonly')
        return
      }
      capabilities.value = getReadonlyCapabilities()
    }

    await loadLabels(String(page.value.project_id))

    // 加载同项目页面列表（不阻塞主流程）
    loadPageList(String(page.value.project_id))

    const nextImageUrl = await loadImageUrl(page.value.page_id)
    if (nextImageUrl !== imageUrl.value) {
      revokeObjectUrl(imageUrl.value)
      imageUrl.value = nextImageUrl
    }

    // latest 接口在页面尚无标注时返回 null，避免制造无意义的 404 噪音。
    revision.value = revisionId.value
      ? await annotationsApi.getRevision(pageId.value, revisionId.value)
      : await annotationsApi.getLatest(pageId.value)

    // 加载 QC
    try {
      const qcResponse = await qcApi.listByPage(pageId.value)
      qcIssues.value = qcResponse.items
      qcCount.value = qcResponse.items.length
      activeQcIssueId.value = null
    } catch { /* QC 加载失败不阻止页面显示 */ }

    // 将 revision 数据加载到 store
    await nextTick()
    if (page.value) {
      hydrateStoreFromLoadedData(page.value, revision.value)
    }

    syncWorkspaceMeta()
  } finally {
    loading.value = false
    isInitialLoad.value = false
  }
}

watch([pageId, revisionId], () => { loadWorkspace() })
watch(isReadonly, () => { syncWorkspaceMeta() })
watch(canvasRef, () => {
  if (!canvasRef.value) return
  if (!pendingHydration.value) return
  hydrateStoreFromLoadedData(pendingHydration.value.page, pendingHydration.value.revision)
  pendingHydration.value = null
})
onMounted(() => { loadWorkspace() })
onUnmounted(() => {
  revokeObjectUrl(imageUrl.value)
  for (const url of Object.values(thumbnailUrls.value)) {
    revokeObjectUrl(url)
  }
})
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- Loading -->
    <div v-if="loading" class="flex-1 flex items-center justify-center text-text-muted">
      <div class="flex items-center gap-2">
        <div class="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
        {{ t('common.loading') }}
      </div>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="flex-1 flex items-center justify-center">
      <div class="text-center">
        <p class="text-heading text-text mb-2">{{ error }}</p>
        <p v-if="errorCode" class="text-caption text-text-muted mb-4">{{ errorCode }}</p>
        <button type="button"
          class="inline-flex items-center justify-center rounded-md bg-primary px-3 py-2 text-caption font-medium text-white transition-colors hover:bg-primary-hover"
          @click="loadWorkspace">
          {{ t('common.retry') }}
        </button>
      </div>
    </div>

    <!-- Workspace -->
    <template v-else-if="page">
      <div v-if="isConflict" class="border-b border-border bg-danger-bg px-3 py-2 text-caption text-danger">
        <div class="flex items-center justify-between gap-3">
          <div class="truncate">{{ t('errors.conflict') }}</div>
          <div class="flex items-center gap-2 shrink-0">
            <button type="button"
              class="inline-flex items-center justify-center rounded-md bg-primary px-2.5 py-1.5 text-micro font-medium text-white transition-colors hover:bg-primary-hover disabled:opacity-40 disabled:cursor-not-allowed"
              :disabled="saving" @click="saveAsNewRevisionFromConflict">
              {{ t('workspace.conflictSaveAsNew') }}
            </button>
            <button type="button"
              class="inline-flex items-center justify-center rounded-md bg-surface px-2.5 py-1.5 text-micro font-medium text-text-secondary border border-border transition-colors hover:bg-surface-muted disabled:opacity-40 disabled:cursor-not-allowed"
              :disabled="saving" @click="rebaseConflictAndContinueEditing">
              {{ t('workspace.conflictRebase') }}
            </button>
            <button type="button"
              class="inline-flex items-center justify-center rounded-md bg-surface px-2.5 py-1.5 text-micro font-medium text-text-secondary border border-border transition-colors hover:bg-surface-muted"
              @click="exportConflictDraftJson">
              {{ t('workspace.conflictExport') }}
            </button>
            <button type="button"
              class="inline-flex items-center justify-center rounded-md bg-danger px-2.5 py-1.5 text-micro font-medium text-white transition-colors hover:opacity-90"
              @click="discardLocalChangesAndReloadLatest">
              {{ t('workspace.conflictDiscard') }}
            </button>
          </div>
        </div>
      </div>
      <!-- ═══ 工具栏 ═══ -->
      <div class="h-12 bg-surface border-b border-border flex items-center px-3 shrink-0 gap-1 z-toolbar">
        <!-- 左侧工具组 -->
        <div class="flex items-center gap-1">
          <button v-for="tool in tools" :key="tool.key" :class="[
            'w-8 h-8 flex items-center justify-center rounded-md transition-all duration-fast',
            activeTool === tool.key
              ? 'bg-primary/10 text-primary border border-primary/30'
              : 'text-text-secondary hover:bg-surface-muted hover:text-text border border-transparent',
            (!canWrite && tool.key !== 'select' && tool.key !== 'pan') ? 'opacity-40 cursor-not-allowed' : '',
          ]" :aria-label="t(tool.label)" :title="`${t(tool.label)} (${tool.shortcut})`"
            :disabled="!canWrite && tool.key !== 'select' && tool.key !== 'pan'"
            @click="setActiveTool(tool.key as ActiveTool)">
            <component :is="tool.icon" class="w-4 h-4" />
          </button>
        </div>

        <!-- 分隔线 -->
        <div class="w-px h-5 bg-border mx-1"></div>

        <!-- 上一张/下一张 -->
        <div class="flex items-center gap-1">
          <button
            class="w-8 h-8 flex items-center justify-center rounded-md text-text-secondary hover:bg-surface-muted hover:text-text transition-colors"
            :class="{ 'opacity-40 cursor-not-allowed': !hasPrev }" :disabled="!hasPrev"
            :aria-label="t('workspace.prevPage')" :title="`${t('workspace.prevPage')} (A)`" @click="goToPrevPage">
            <ChevronLeft class="w-4 h-4" />
          </button>
          <span class="text-caption font-mono text-text-secondary min-w-[4rem] text-center">
            {{ t('workspace.pageN', { current: currentIndex + 1, total: pageList.length }) }}
          </span>
          <button
            class="w-8 h-8 flex items-center justify-center rounded-md text-text-secondary hover:bg-surface-muted hover:text-text transition-colors"
            :class="{ 'opacity-40 cursor-not-allowed': !hasNext }" :disabled="!hasNext"
            :aria-label="t('workspace.nextPage')" :title="`${t('workspace.nextPage')} (D)`" @click="goToNextPage">
            <ChevronRight class="w-4 h-4" />
          </button>
        </div>

        <!-- 分隔线 -->
        <div class="w-px h-5 bg-border mx-1"></div>

        <!-- 缩放控件 -->
        <div class="flex items-center gap-1">
          <button
            class="w-8 h-8 flex items-center justify-center rounded-md text-text-secondary hover:bg-surface-muted hover:text-text transition-colors"
            :aria-label="t('annotation.tools.zoomOut')" @click="onZoomOut">
            <ZoomOut class="w-4 h-4" />
          </button>
          <button
            class="w-8 h-8 flex items-center justify-center rounded-md text-text-secondary hover:bg-surface-muted hover:text-text transition-colors"
            :aria-label="t('annotation.tools.zoomIn')" @click="onZoomIn">
            <ZoomIn class="w-4 h-4" />
          </button>
          <button
            class="w-8 h-8 flex items-center justify-center rounded-md text-text-secondary hover:bg-surface-muted hover:text-text transition-colors"
            :aria-label="t('annotation.tools.fitWidth')" @click="onFitWidth">
            <Expand class="w-4 h-4" />
          </button>
          <button
            class="w-8 h-8 flex items-center justify-center rounded-md text-text-secondary hover:bg-surface-muted hover:text-text transition-colors"
            :aria-label="t('annotation.tools.fitPage')" @click="onFitPage">
            <Maximize class="w-4 h-4" />
          </button>
        </div>

        <!-- 分隔线 -->
        <div class="w-px h-5 bg-border mx-1"></div>

        <!-- 缩放百分比 -->
        <button
          class="h-7 px-2 text-caption font-mono text-text-secondary hover:bg-surface-muted rounded-md transition-colors"
          @click="onFitPage">
          {{ zoomLevel }}%
        </button>

        <!-- 右侧操作 -->
        <div class="ml-auto flex items-center gap-1">
          <!-- 保存 -->
          <button
            class="w-8 h-8 flex items-center justify-center rounded-md text-text-secondary hover:bg-surface-muted hover:text-text transition-colors"
            :class="{ 'opacity-40 cursor-not-allowed': !canWriteAnnotation }" :aria-label="t('common.save')"
            :title="`${t('common.save')} (Ctrl+S)`" :disabled="!canWriteAnnotation" @click="saveAnnotation">
            <Loader2 v-if="saving" class="w-4 h-4 animate-spin" />
            <Save v-else class="w-4 h-4" />
          </button>

          <!-- 撤销/重做 -->
          <button
            class="w-8 h-8 flex items-center justify-center rounded-md text-text-secondary hover:bg-surface-muted hover:text-text transition-colors"
            :class="{ 'opacity-40 cursor-not-allowed': !canvasRef?.store.canUndo.value || !canWriteAnnotation }"
            :disabled="!canvasRef?.store.canUndo.value || !canWriteAnnotation" :aria-label="t('annotation.tools.undo')"
            :title="`${t('annotation.tools.undo')} (Ctrl+Z)`" @click="onUndo">
            <Undo2 class="w-4 h-4" />
          </button>
          <button
            class="w-8 h-8 flex items-center justify-center rounded-md text-text-secondary hover:bg-surface-muted hover:text-text transition-colors"
            :class="{ 'opacity-40 cursor-not-allowed': !canvasRef?.store.canRedo.value || !canWriteAnnotation }"
            :disabled="!canvasRef?.store.canRedo.value || !canWriteAnnotation" :aria-label="t('annotation.tools.redo')"
            :title="`${t('annotation.tools.redo')} (Ctrl+Y)`" @click="onRedo">
            <Redo2 class="w-4 h-4" />
          </button>

          <!-- 分隔线 -->
          <div class="w-px h-5 bg-border mx-1"></div>

          <!-- 删除 -->
          <button
            class="w-8 h-8 flex items-center justify-center rounded-md text-text-secondary hover:bg-danger-bg hover:text-danger transition-colors"
            :class="{ 'opacity-40 cursor-not-allowed': !selectedObject || !canWriteAnnotation }"
            :aria-label="t('annotation.tools.delete')" :disabled="!selectedObject || !canWriteAnnotation"
            :title="`${t('annotation.tools.delete')} (Delete)`" @click="onDelete">
            <Trash2 class="w-4 h-4" />
          </button>

          <!-- 全屏 -->
          <button
            class="w-8 h-8 flex items-center justify-center rounded-md text-text-secondary hover:bg-surface-muted hover:text-text transition-colors"
            :aria-label="t('common.fullscreen')">
            <Fullscreen class="w-4 h-4" />
          </button>
        </div>
      </div>

      <!-- ═══ 主工作区 ═══ -->
      <div class="flex flex-1 overflow-hidden">
        <!-- 最左侧：页面缩略图列表 -->
        <div class="w-28 bg-surface border-r border-border flex flex-col shrink-0">
          <div class="p-2 border-b border-border-soft">
            <span class="text-micro text-text-tertiary uppercase tracking-wider">{{ t('workspace.pageList') }}</span>
          </div>
          <div class="flex-1 overflow-y-auto p-1.5 space-y-1">
            <button v-for="(p, idx) in pageList" :key="p.page_id" :class="[
              'w-full rounded-md border transition-all duration-fast overflow-hidden',
              p.page_id === pageId
                ? 'border-primary ring-1 ring-primary/30'
                : 'border-border-soft hover:border-primary/40',
            ]" :title="`${p.filename || p.page_id} (${p.width}×${p.height})`" @click="goToPage(p.page_id)">
              <!-- 缩略图 -->
              <div class="w-full h-16 bg-surface-alt flex items-center justify-center overflow-hidden">
                <img v-if="thumbnailUrls[p.page_id]" :src="thumbnailUrls[p.page_id]"
                  class="w-full h-full object-contain" loading="lazy" />
                <span v-else class="text-micro text-text-muted">{{ idx + 1 }}</span>
              </div>
              <!-- 文件名 -->
              <div class="px-1 py-0.5">
                <p class="text-micro text-text-secondary truncate">{{ p.filename || p.page_id }}</p>
              </div>
            </button>
          </div>
        </div>

        <!-- 左侧面板：标签选择 -->
        <div class="w-32 bg-surface-muted border-r border-border-soft flex flex-col shrink-0">
          <div class="p-2 border-b border-border-soft">
            <span class="text-micro text-text-tertiary uppercase tracking-wider">{{ t('annotation.labels.title')
            }}</span>
          </div>
          <div class="flex-1 overflow-y-auto p-1.5 space-y-0.5">
            <button v-for="label in labels" :key="getLabelKey(label)" :class="[
              'w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-caption transition-colors',
              activeLabelKey === getLabelKey(label)
                ? 'bg-primary/10 text-primary font-medium'
                : 'text-text-secondary hover:bg-surface-muted',
            ]" @click="activeLabelKey = getLabelKey(label)">
              <span class="w-3 h-3 rounded-sm shrink-0"
                :style="{ backgroundColor: getLabelColor(label.name, label.namespace) }"></span>
              <span class="truncate">{{ getLabelDisplayName(label) }}</span>
            </button>
          </div>
        </div>

        <!-- ═══ 中间画布区 ═══ -->
        <AnnotationCanvas ref="canvasRef" :image-url="imageUrl" :active-tool="activeTool" :active-label="activeLabel"
          :qc-overlays="qcOverlayRegions" :active-qc-issue-id="activeQcIssueId" :readonly="!canWriteAnnotation"
          class="flex-1" @update:zoom-level="onZoomLevelUpdate" @object-selected="onObjectSelected"
          @objects-changed="onObjectsChanged" />

        <!-- ═══ 右侧：属性编辑 ═══ -->
        <div class="w-64 bg-surface border-l border-border flex flex-col shrink-0">
          <!-- 属性编辑 -->
          <div class="p-3 border-b border-border">
            <div class="text-body-medium text-text mb-3">{{ t('annotation.properties.title') }}</div>
            <button v-if="activeTool === 'read_order' && canWriteAnnotation" type="button"
              class="mb-3 inline-flex h-7 items-center rounded-md border border-border px-2 text-caption text-text-secondary transition-colors hover:bg-surface-muted hover:text-text"
              @click="clearReadOrder">
              {{ t('annotation.properties.clearReadOrder') }}
            </button>

            <template v-if="selectedObject">
              <!-- 标签选择 -->
              <div class="mb-2">
                <label class="text-micro text-text-tertiary block mb-1">{{ t('annotation.properties.label') }}</label>
                <select :value="getLabelKey({ namespace: selectedObject.label_namespace, name: selectedObject.type })"
                  class="w-full h-7 px-2 text-caption bg-surface border border-border rounded-md text-text focus:outline-none focus:ring-2 focus:ring-focus"
                  @change="onLabelChange">
                  <option v-for="label in labels" :key="getLabelKey(label)" :value="getLabelKey(label)">
                    {{ getLabelDisplayName(label) }}
                  </option>
                </select>
              </div>

              <!-- 阅读顺序 -->
              <div class="mb-2">
                <label class="text-micro text-text-tertiary block mb-1">{{ t('annotation.properties.readOrder')
                }}</label>
                <input type="number" :value="selectedObject.read_order" min="0"
                  class="w-full h-7 px-2 text-caption bg-surface border border-border rounded-md text-text focus:outline-none focus:ring-2 focus:ring-focus"
                  @change="onReadOrderChange" />
              </div>

              <!-- 坐标 -->
              <div class="mb-2">
                <label class="text-micro text-text-tertiary block mb-1">{{ t('annotation.properties.coordinates')
                }}</label>
                <div class="grid grid-cols-4 gap-1">
                  <input v-for="(val, idx) in (selectedObject.geometry.bbox_xyxy || [])" :key="idx" type="text"
                    :value="Math.round(val)"
                    class="h-7 px-1.5 text-caption font-mono bg-surface border border-border rounded-md text-text text-center"
                    readonly />
                </div>
              </div>

              <!-- ID -->
              <div class="flex justify-between text-micro text-text-tertiary">
                <span>{{ t('annotation.properties.id') }}: <span class="font-mono">{{ selectedObject.id.slice(0, 12)
                    }}</span></span>
              </div>
            </template>

            <template v-else>
              <p class="text-caption text-text-muted">{{ t('common.noData') }}</p>
            </template>
          </div>

          <!-- 对象列表 -->
          <div class="flex-1 overflow-y-auto p-3">
            <div class="text-body-medium text-text mb-2">
              {{ t('annotation.objects.count', { count: objectCount }) }}
            </div>
            <div class="space-y-1">
              <div v-for="obj in (canvasRef?.store.objects.value || [])" :key="obj.id" :class="[
                'flex items-center gap-2 px-2 py-1.5 rounded-md text-caption cursor-pointer transition-colors',
                selectedObject?.id === obj.id
                  ? 'bg-primary/10 text-primary'
                  : 'text-text-secondary hover:bg-surface-muted',
              ]" @click="canvasRef?.store.select(obj.id); onObjectSelected(obj.id)">
                <span class="w-2.5 h-2.5 rounded-sm shrink-0" :style="{ backgroundColor: obj.color }"></span>
                <span class="flex-1 truncate">{{ getLabelText(obj.type, obj.label_namespace) }}</span>
                <span class="text-micro text-text-muted">#{{ obj.read_order }}</span>
                <button type="button"
                  class="ml-1 inline-flex h-6 w-6 items-center justify-center rounded hover:bg-surface-alt disabled:opacity-40 disabled:cursor-not-allowed"
                  :aria-label="t('annotation.tools.delete')" :title="t('annotation.tools.delete')"
                  :disabled="!canWriteAnnotation" @click.stop="onDeleteObject(obj.id)">
                  <Trash2 class="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          </div>

          <!-- QC 问题 -->
          <div class="border-t border-border p-3">
            <div class="text-body-medium text-text mb-2">
              {{ t('annotation.qc.count', { count: qcCount }) }}
            </div>
            <div v-if="!qcIssues.length" class="text-caption text-text-muted">
              {{ t('annotation.qc.empty') }}
            </div>
            <div v-else class="space-y-3">
              <div v-for="group in groupedQcIssues" :key="group.severity" class="space-y-1.5">
                <div class="flex items-center justify-between">
                  <span class="text-micro font-medium uppercase tracking-wider text-text-tertiary">
                    {{ t(`annotation.qc.severity.${group.severity}`) }}
                  </span>
                  <span class="text-micro text-text-muted">{{ group.items.length }}</span>
                </div>
                <button v-for="issue in group.items" :key="issue.id" type="button"
                  class="w-full rounded-md border border-border-soft bg-surface-alt px-2 py-2 text-left transition-colors hover:border-primary/40 hover:bg-surface-muted"
                  :class="{ 'border-primary/50 ring-1 ring-primary/20': activeQcIssueId === issue.id }"
                  @click="locateQcIssue(issue)">
                  <div class="mb-1 flex items-center justify-between gap-2">
                    <span class="font-mono text-micro text-text-tertiary">{{ issue.code }}</span>
                    <span class="rounded px-1.5 py-0.5 text-micro font-medium"
                      :class="getQcIssueSeverityClass(issue.severity)">
                      {{ t(`annotation.qc.severity.${issue.severity}`) }}
                    </span>
                  </div>
                  <div class="text-caption text-text">{{ issue.message }}</div>
                  <div class="mt-1 text-micro text-text-muted">{{ getQcIssueTargetLabel(issue) }}</div>
                  <div v-if="getQcIssueSuggestionText(issue)" class="mt-1 text-micro text-text-secondary">
                    {{ t('annotation.qc.suggestion') }}: {{ getQcIssueSuggestionText(issue) }}
                  </div>
                </button>
              </div>
            </div>
          </div>

          <!-- 快捷键帮助 -->
          <div class="border-t border-border p-3 shrink-0">
            <div class="text-body-medium text-text mb-2">{{ t('annotation.shortcuts.title') }}</div>
            <div class="grid grid-cols-2 gap-x-3 gap-y-1 text-micro">
              <div class="flex items-center gap-1.5">
                <kbd
                  class="font-mono text-text-tertiary bg-surface-alt border border-border rounded px-1 py-0.5">W</kbd>
                <span class="text-text-secondary">{{ t('annotation.shortcuts.bboxTool') }}</span>
              </div>
              <div class="flex items-center gap-1.5">
                <kbd
                  class="font-mono text-text-tertiary bg-surface-alt border border-border rounded px-1 py-0.5">Ctrl+Z</kbd>
                <span class="text-text-secondary">{{ t('annotation.shortcuts.undo') }}</span>
              </div>
              <div class="flex items-center gap-1.5">
                <kbd
                  class="font-mono text-text-tertiary bg-surface-alt border border-border rounded px-1 py-0.5">V</kbd>
                <span class="text-text-secondary">{{ t('annotation.shortcuts.selectTool') }}</span>
              </div>
              <div class="flex items-center gap-1.5">
                <kbd
                  class="font-mono text-text-tertiary bg-surface-alt border border-border rounded px-1 py-0.5">Ctrl+Y</kbd>
                <span class="text-text-secondary">{{ t('annotation.shortcuts.redo') }}</span>
              </div>
              <div class="flex items-center gap-1.5">
                <kbd
                  class="font-mono text-text-tertiary bg-surface-alt border border-border rounded px-1 py-0.5">R</kbd>
                <span class="text-text-secondary">{{ t('annotation.shortcuts.readOrderTool') }}</span>
              </div>
              <div class="flex items-center gap-1.5">
                <kbd
                  class="font-mono text-text-tertiary bg-surface-alt border border-border rounded px-1 py-0.5">Delete</kbd>
                <span class="text-text-secondary">{{ t('annotation.shortcuts.deleteSelected') }}</span>
              </div>
              <div class="flex items-center gap-1.5">
                <kbd
                  class="font-mono text-text-tertiary bg-surface-alt border border-border rounded px-1 py-0.5">Space</kbd>
                <span class="text-text-secondary">{{ t('annotation.shortcuts.panCanvas') }}</span>
              </div>
              <div class="flex items-center gap-1.5">
                <kbd
                  class="font-mono text-text-tertiary bg-surface-alt border border-border rounded px-1 py-0.5">Ctrl+S</kbd>
                <span class="text-text-secondary">{{ t('annotation.shortcuts.save') }}</span>
              </div>
              <div class="flex items-center gap-1.5">
                <kbd class="font-mono text-text-tertiary bg-surface-alt border border-border rounded px-1 py-0.5">A /
                  D</kbd>
                <span class="text-text-secondary">{{ t('workspace.prevPage') }}/{{ t('workspace.nextPage') }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
