<script setup lang="ts">
/**
 * 标注工作台页面
 * 通过 AnnotationWorkspaceLayout 提供布局
 * 负责加载 page 元数据、图片、latest revision、label registry
 *
 * 参考：doc/开发文档/前端/frontend_routing_spec.md 第 14 章
 */
import { ref, computed, onMounted, inject, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { pagesApi, type Page, type Capabilities } from '@/api/pages'
import { annotationsApi, type AnnotationRevision } from '@/api/annotations'
import { qcApi, type QcIssue } from '@/api/qc'
import { annotationsApi as saveApi } from '@/api/annotations'
import { ApiClientError } from '@/api/client'
import { NButton } from 'naive-ui'
import AnnotationCanvas from '@/components/annotation/AnnotationCanvas.vue'
import type { AnnotationObject } from '@/composables/useAnnotationStore'
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
} from 'lucide-vue-next'

const { t } = useI18n()
const route = useRoute()

const pageId = computed(() => route.params.page_id as string)
const revisionId = computed(() => route.query.revision_id as string | undefined)

// ── 状态 ──
const loading = ref(true)
const error = ref('')
const errorCode = ref<number | undefined>()
const saving = ref(false)

// ── 数据 ──
const page = ref<Page | null>(null)
const capabilities = ref<Capabilities | null>(null)
const revision = ref<AnnotationRevision | null>(null)
const qcIssues = ref<QcIssue[]>([])
const imageUrl = ref<string | null>(null)

const isReadonly = computed(() => {
  if (revisionId.value) return true
  if (capabilities.value && !capabilities.value.can_edit) return true
  return false
})

const updateSaveStatus = inject<((status: string) => void) | undefined>('updateSaveStatus')

function syncWorkspaceMeta(status?: string) {
  if (status) {
    updateSaveStatus?.(status)
  } else {
    updateSaveStatus?.(isReadonly.value ? 'readonly' : 'saved')
  }
}

// ── 工具栏状态 ──
const activeTool = ref<'select' | 'rectangle' | 'readingOrder' | 'pan'>('select')
const zoomLevel = ref(100)
const canvasRef = ref<InstanceType<typeof AnnotationCanvas> | null>(null)

const tools = [
  { key: 'select', icon: MousePointer2, label: 'annotation.tools.select', shortcut: 'R' },
  { key: 'rectangle', icon: SquareDashedMousePointer, label: 'annotation.tools.rectangle', shortcut: 'W' },
  { key: 'readingOrder', icon: BookOpen, label: 'annotation.tools.readingOrder', shortcut: 'O' },
  { key: 'pan', icon: Hand, label: 'annotation.tools.pan', shortcut: 'Space' },
]

// ── 右侧面板 ──
const objectCount = ref(0)
const qcCount = ref(0)

// ── 标签数据 ──
const labels = [
  { key: 'question_block', i18nKey: 'question', color: '#5e6ad2' },
  { key: 'answer_area', i18nKey: 'answerArea', color: '#24a148' },
  { key: 'option_block', i18nKey: 'optionArea', color: '#0f62fe' },
  { key: 'option_image', i18nKey: 'imageArea', color: '#da1e28' },
  { key: 'formula', i18nKey: 'formula', color: '#dd5b00' },
  { key: 'table', i18nKey: 'table', color: '#0f62fe' },
  { key: 'noise_or_erasure', i18nKey: 'other', color: '#8c8c8c' },
]
const activeLabel = ref('question_block')

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
  syncWorkspaceMeta('dirty')
}

// ── 属性编辑 ──
function onLabelChange(e: Event) {
  const label = (e.target as HTMLSelectElement).value
  if (selectedObject.value && canvasRef.value) {
    const color = labels.find(l => l.key === label)?.color || '#5e6ad2'
    canvasRef.value.store.updateObject(selectedObject.value.id, { label, color })
    onObjectsChanged()
  }
}

function onReadOrderChange(e: Event) {
  const order = parseInt((e.target as HTMLInputElement).value, 10)
  if (selectedObject.value && canvasRef.value && !isNaN(order)) {
    canvasRef.value.store.setReadOrder(selectedObject.value.id, order)
    onObjectsChanged()
  }
}

// ── 保存 ──
async function saveAnnotation() {
  if (!canvasRef.value || !page.value || saving.value) return
  saving.value = true
  syncWorkspaceMeta('saving')
  try {
    const draft = canvasRef.value.store.toDraft(page.value.page_id)
    const result = await saveApi.save(page.value.page_id, draft)
    canvasRef.value.store.baseRevisionId.value = result.id
    canvasRef.value.store.revisionNo.value = result.revision_no
    syncWorkspaceMeta('saved')
  } catch (e) {
    if (e instanceof ApiClientError && e.status === 409) {
      syncWorkspaceMeta('conflict')
    } else {
      syncWorkspaceMeta('autosave_failed')
    }
  } finally {
    saving.value = false
  }
}

// ── 缩放控制 ──
function onZoomIn() {
  canvasRef.value?.transform.zoom(0.25)
  zoomLevel.value = canvasRef.value?.transform.zoomPercent.value || 100
}

function onZoomOut() {
  canvasRef.value?.transform.zoom(-0.25)
  zoomLevel.value = canvasRef.value?.transform.zoomPercent.value || 100
}

function onFitWidth() {
  canvasRef.value?.transform.fitToWidth()
  zoomLevel.value = canvasRef.value?.transform.zoomPercent.value || 100
}

function onFitPage() {
  canvasRef.value?.transform.fitToContainer()
  zoomLevel.value = canvasRef.value?.transform.zoomPercent.value || 100
}

function onZoomLevelUpdate(val: number) {
  zoomLevel.value = val
}

// ── 撤销/重做/删除 ──
function onUndo() {
  canvasRef.value?.store.undo()
  onObjectsChanged()
}

function onRedo() {
  canvasRef.value?.store.redo()
  onObjectsChanged()
}

function onDelete() {
  canvasRef.value?.store.deleteSelected()
  onObjectsChanged()
}

// ── 键盘快捷键 ──
function onKeyDown(e: KeyboardEvent) {
  // 快捷键切换工具
  if (!e.ctrlKey && !e.metaKey) {
    if (e.key === 'r' || e.key === 'R') { activeTool.value = 'select'; e.preventDefault() }
    if (e.key === 'w' || e.key === 'W') { activeTool.value = 'rectangle'; e.preventDefault() }
    if (e.key === 'o' || e.key === 'O') { activeTool.value = 'readingOrder'; e.preventDefault() }
  }
  // Ctrl+S 保存
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault()
    saveAnnotation()
  }
}

onMounted(() => { window.addEventListener('keydown', onKeyDown) })

// ── 加载数据 ──
async function loadWorkspace() {
  loading.value = true
  error.value = ''
  errorCode.value = undefined

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
      capabilities.value = await pagesApi.getCapabilities(page.value.project_id)
    } catch {
      capabilities.value = { can_edit: false, can_review: false, can_export: false, can_manage: false }
    }

    // 加载图片
    try {
      const authHeaders = { Authorization: `Bearer ${sessionStorage.getItem('k12.access_token') || ''}` }
      // 先获取图片访问 URL（返回 JSON { url, expires_at }）
      const urlRes = await fetch(`/api/v1/pages/${page.value.page_id}/image`, { headers: authHeaders })
      if (urlRes.ok) {
        const { url } = await urlRes.json()
        // 再用拿到的 URL 请求真实图片二进制
        const imgRes = await fetch(url, { headers: authHeaders })
        if (imgRes.ok) {
          const blob = await imgRes.blob()
          imageUrl.value = URL.createObjectURL(blob)
        } else {
          imageUrl.value = `https://placehold.co/${page.value.width}x${page.value.height}/f8f8f8/333?text=${encodeURIComponent(page.value.filename)}`
        }
      } else {
        imageUrl.value = `https://placehold.co/${page.value.width}x${page.value.height}/f8f8f8/333?text=${encodeURIComponent(page.value.filename)}`
      }
    } catch {
      imageUrl.value = `https://placehold.co/${page.value.width}x${page.value.height}/f8f8f8/333?text=${encodeURIComponent(page.value.filename)}`
    }

    // 加载标注
    try {
      if (revisionId.value) {
        const revisions = await annotationsApi.listRevisions(pageId.value)
        revision.value = revisions.find(r => r.id === revisionId.value) || null
      } else {
        revision.value = await annotationsApi.getLatest(pageId.value)
      }
    } catch (e) {
      if (e instanceof ApiClientError && e.status === 404) revision.value = null
    }

    // 加载 QC
    try {
      const qcResponse = await qcApi.listByPage(pageId.value)
      qcIssues.value = qcResponse.items
      qcCount.value = qcResponse.items.length
    } catch { /* QC 加载失败不阻止页面显示 */ }

    // 将 revision 数据加载到 store
    if (canvasRef.value) {
      canvasRef.value.store.loadFromRevision(revision.value)
      objectCount.value = canvasRef.value.store.objects.value.length
    }

    syncWorkspaceMeta()
  } finally {
    loading.value = false
  }
}

watch([pageId, revisionId], () => { loadWorkspace() })
watch(isReadonly, () => { syncWorkspaceMeta() })
onMounted(() => { loadWorkspace() })
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
        <p v-if="errorCode" class="text-caption text-text-muted mb-4">Error {{ errorCode }}</p>
        <NButton type="primary" @click="loadWorkspace">
          {{ t('common.retry') }}
        </NButton>
      </div>
    </div>

    <!-- Workspace -->
    <template v-else-if="page">
      <!-- ═══ 工具栏 ═══ -->
      <div class="h-12 bg-surface border-b border-border flex items-center px-3 shrink-0 gap-1 z-toolbar">
        <!-- 左侧工具组 -->
        <div class="flex items-center gap-1">
          <button
            v-for="tool in tools"
            :key="tool.key"
            :class="[
              'w-8 h-8 flex items-center justify-center rounded-md transition-all duration-fast',
              activeTool === tool.key
                ? 'bg-primary/10 text-primary border border-primary/30'
                : 'text-text-secondary hover:bg-surface-muted hover:text-text border border-transparent',
            ]"
            :aria-label="t(tool.label)"
            :title="`${t(tool.label)} (${tool.shortcut})`"
            @click="activeTool = tool.key as any"
          >
            <component :is="tool.icon" class="w-4 h-4" />
          </button>
        </div>

        <!-- 分隔线 -->
        <div class="w-px h-5 bg-border mx-1"></div>

        <!-- 缩放控件 -->
        <div class="flex items-center gap-1">
          <button
            class="w-8 h-8 flex items-center justify-center rounded-md text-text-secondary hover:bg-surface-muted hover:text-text transition-colors"
            :aria-label="t('annotation.tools.zoomOut')"
            @click="onZoomOut"
          >
            <ZoomOut class="w-4 h-4" />
          </button>
          <button
            class="w-8 h-8 flex items-center justify-center rounded-md text-text-secondary hover:bg-surface-muted hover:text-text transition-colors"
            :aria-label="t('annotation.tools.zoomIn')"
            @click="onZoomIn"
          >
            <ZoomIn class="w-4 h-4" />
          </button>
          <button
            class="w-8 h-8 flex items-center justify-center rounded-md text-text-secondary hover:bg-surface-muted hover:text-text transition-colors"
            :aria-label="t('annotation.tools.fitWidth')"
            @click="onFitWidth"
          >
            <Expand class="w-4 h-4" />
          </button>
          <button
            class="w-8 h-8 flex items-center justify-center rounded-md text-text-secondary hover:bg-surface-muted hover:text-text transition-colors"
            :aria-label="t('annotation.tools.fitPage')"
            @click="onFitPage"
          >
            <Maximize class="w-4 h-4" />
          </button>
        </div>

        <!-- 分隔线 -->
        <div class="w-px h-5 bg-border mx-1"></div>

        <!-- 缩放百分比 -->
        <button
          class="h-7 px-2 text-caption font-mono text-text-secondary hover:bg-surface-muted rounded-md transition-colors"
          @click="onFitPage"
        >
          {{ zoomLevel }}%
        </button>

        <!-- 右侧操作 -->
        <div class="ml-auto flex items-center gap-1">
          <!-- 保存 -->
          <button
            class="w-8 h-8 flex items-center justify-center rounded-md text-text-secondary hover:bg-surface-muted hover:text-text transition-colors"
            :aria-label="t('common.save')"
            :title="`${t('common.save')} (Ctrl+S)`"
            :disabled="saving"
            @click="saveAnnotation"
          >
            <Loader2 v-if="saving" class="w-4 h-4 animate-spin" />
            <Save v-else class="w-4 h-4" />
          </button>

          <!-- 撤销/重做 -->
          <button
            class="w-8 h-8 flex items-center justify-center rounded-md text-text-secondary hover:bg-surface-muted hover:text-text transition-colors"
            :class="{ 'opacity-40 cursor-not-allowed': !canvasRef?.store.canUndo.value }"
            :aria-label="t('annotation.tools.undo')"
            :title="`${t('annotation.tools.undo')} (Ctrl+Z)`"
            @click="onUndo"
          >
            <Undo2 class="w-4 h-4" />
          </button>
          <button
            class="w-8 h-8 flex items-center justify-center rounded-md text-text-secondary hover:bg-surface-muted hover:text-text transition-colors"
            :class="{ 'opacity-40 cursor-not-allowed': !canvasRef?.store.canRedo.value }"
            :aria-label="t('annotation.tools.redo')"
            :title="`${t('annotation.tools.redo')} (Ctrl+Y)`"
            @click="onRedo"
          >
            <Redo2 class="w-4 h-4" />
          </button>

          <!-- 分隔线 -->
          <div class="w-px h-5 bg-border mx-1"></div>

          <!-- 删除 -->
          <button
            class="w-8 h-8 flex items-center justify-center rounded-md text-text-secondary hover:bg-danger-bg hover:text-danger transition-colors"
            :class="{ 'opacity-40 cursor-not-allowed': !selectedObject }"
            :aria-label="t('annotation.tools.delete')"
            :title="`${t('annotation.tools.delete')} (Delete)`"
            @click="onDelete"
          >
            <Trash2 class="w-4 h-4" />
          </button>

          <!-- 全屏 -->
          <button
            class="w-8 h-8 flex items-center justify-center rounded-md text-text-secondary hover:bg-surface-muted hover:text-text transition-colors"
            aria-label="Fullscreen"
          >
            <Fullscreen class="w-4 h-4" />
          </button>
        </div>
      </div>

      <!-- ═══ 主工作区 ═══ -->
      <div class="flex flex-1 overflow-hidden">
        <!-- 左侧面板：标签选择 -->
        <div class="w-32 bg-surface-muted border-r border-border-soft flex flex-col shrink-0">
          <div class="p-2 border-b border-border-soft">
            <span class="text-micro text-text-tertiary uppercase tracking-wider">{{ t('annotation.labels.title') }}</span>
          </div>
          <div class="flex-1 overflow-y-auto p-1.5 space-y-0.5">
            <button
              v-for="label in labels"
              :key="label.key"
              :class="[
                'w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-caption transition-colors',
                activeLabel === label.key
                  ? 'bg-primary/10 text-primary font-medium'
                  : 'text-text-secondary hover:bg-surface-muted',
              ]"
              @click="activeLabel = label.key"
            >
              <span class="w-3 h-3 rounded-sm shrink-0" :style="{ backgroundColor: label.color }"></span>
              <span class="truncate">{{ t(`annotation.labels.${label.i18nKey}`) }}</span>
            </button>
          </div>
        </div>

        <!-- ═══ 中间画布区 ═══ -->
        <AnnotationCanvas
          ref="canvasRef"
          :image-url="imageUrl"
          :active-tool="activeTool"
          :active-label="activeLabel"
          class="flex-1"
          @update:zoom-level="onZoomLevelUpdate"
          @object-selected="onObjectSelected"
          @objects-changed="onObjectsChanged"
        />

        <!-- ═══ 右侧：属性编辑 ═══ -->
        <div class="w-64 bg-surface border-l border-border flex flex-col shrink-0">
          <!-- 属性编辑 -->
          <div class="p-3 border-b border-border">
            <div class="text-body-medium text-text mb-3">{{ t('annotation.properties.title') }}</div>

            <template v-if="selectedObject">
              <!-- 标签选择 -->
              <div class="mb-2">
                <label class="text-micro text-text-tertiary block mb-1">{{ t('annotation.properties.label') }}</label>
                <select
                  :value="selectedObject.label"
                  class="w-full h-7 px-2 text-caption bg-surface border border-border rounded-md text-text focus:outline-none focus:ring-2 focus:ring-focus"
                  @change="onLabelChange"
                >
                  <option v-for="label in labels" :key="label.key" :value="label.key">
                    {{ t(`annotation.labels.${label.i18nKey}`) }}
                  </option>
                </select>
              </div>

              <!-- 阅读顺序 -->
              <div class="mb-2">
                <label class="text-micro text-text-tertiary block mb-1">Read Order</label>
                <input
                  type="number"
                  :value="selectedObject.read_order"
                  min="0"
                  class="w-full h-7 px-2 text-caption bg-surface border border-border rounded-md text-text focus:outline-none focus:ring-2 focus:ring-focus"
                  @change="onReadOrderChange"
                />
              </div>

              <!-- 坐标 -->
              <div class="mb-2">
                <label class="text-micro text-text-tertiary block mb-1">{{ t('annotation.properties.coordinates') }}</label>
                <div class="grid grid-cols-4 gap-1">
                  <input
                    v-for="(val, idx) in selectedObject.bbox_xyxy"
                    :key="idx"
                    type="text"
                    :value="Math.round(val)"
                    class="h-7 px-1.5 text-caption font-mono bg-surface border border-border rounded-md text-text text-center"
                    readonly
                  />
                </div>
              </div>

              <!-- ID -->
              <div class="flex justify-between text-micro text-text-tertiary">
                <span>{{ t('annotation.properties.id') }}: <span class="font-mono">{{ selectedObject.id.slice(0, 12) }}</span></span>
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
              <div
                v-for="obj in (canvasRef?.store.objects.value || [])"
                :key="obj.id"
                :class="[
                  'flex items-center gap-2 px-2 py-1.5 rounded-md text-caption cursor-pointer transition-colors',
                  selectedObject?.id === obj.id
                    ? 'bg-primary/10 text-primary'
                    : 'text-text-secondary hover:bg-surface-muted',
                ]"
                @click="canvasRef?.store.select(obj.id); onObjectSelected(obj.id)"
              >
                <span class="w-2.5 h-2.5 rounded-sm shrink-0" :style="{ backgroundColor: obj.color }"></span>
                <span class="flex-1 truncate">{{ obj.label }}</span>
                <span class="text-micro text-text-muted">#{{ obj.read_order }}</span>
              </div>
            </div>
          </div>

          <!-- 快捷键帮助 -->
          <div class="border-t border-border p-3 shrink-0">
            <div class="text-body-medium text-text mb-2">{{ t('annotation.shortcuts.title') }}</div>
            <div class="grid grid-cols-2 gap-x-3 gap-y-1 text-micro">
              <div class="flex items-center gap-1.5">
                <kbd class="font-mono text-text-tertiary bg-surface-alt border border-border rounded px-1 py-0.5">W</kbd>
                <span class="text-text-secondary">{{ t('annotation.shortcuts.rectangleTool') }}</span>
              </div>
              <div class="flex items-center gap-1.5">
                <kbd class="font-mono text-text-tertiary bg-surface-alt border border-border rounded px-1 py-0.5">Ctrl+Z</kbd>
                <span class="text-text-secondary">{{ t('annotation.shortcuts.undo') }}</span>
              </div>
              <div class="flex items-center gap-1.5">
                <kbd class="font-mono text-text-tertiary bg-surface-alt border border-border rounded px-1 py-0.5">R</kbd>
                <span class="text-text-secondary">{{ t('annotation.shortcuts.selectTool') }}</span>
              </div>
              <div class="flex items-center gap-1.5">
                <kbd class="font-mono text-text-tertiary bg-surface-alt border border-border rounded px-1 py-0.5">Ctrl+Y</kbd>
                <span class="text-text-secondary">{{ t('annotation.shortcuts.redo') }}</span>
              </div>
              <div class="flex items-center gap-1.5">
                <kbd class="font-mono text-text-tertiary bg-surface-alt border border-border rounded px-1 py-0.5">O</kbd>
                <span class="text-text-secondary">{{ t('annotation.shortcuts.readingOrderTool') }}</span>
              </div>
              <div class="flex items-center gap-1.5">
                <kbd class="font-mono text-text-tertiary bg-surface-alt border border-border rounded px-1 py-0.5">Delete</kbd>
                <span class="text-text-secondary">{{ t('annotation.shortcuts.deleteSelected') }}</span>
              </div>
              <div class="flex items-center gap-1.5">
                <kbd class="font-mono text-text-tertiary bg-surface-alt border border-border rounded px-1 py-0.5">Space</kbd>
                <span class="text-text-secondary">{{ t('annotation.shortcuts.panCanvas') }}</span>
              </div>
              <div class="flex items-center gap-1.5">
                <kbd class="font-mono text-text-tertiary bg-surface-alt border border-border rounded px-1 py-0.5">Ctrl+S</kbd>
                <span class="text-text-secondary">{{ t('annotation.shortcuts.save') }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
