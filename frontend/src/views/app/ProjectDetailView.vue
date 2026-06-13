<script setup lang="ts">
/**
 * 项目详情页 — 优化版文件上传
 * 支持拖拽上传、实时进度、取消、重试、上传后自动刷新页面列表
 */
import { computed, ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { pagesApi, type Page, type Capabilities } from '@/api/pages'
import { assetsApi } from '@/api/assets'
import { formatProjectDetailError } from './projectDetailErrors'
import { FileCheck, AlertCircle, Loader2, FileImage, PenTool, X, RotateCcw, Upload } from 'lucide-vue-next'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const projectId = computed(() => route.params.project_id as string)
const projectCapabilities = ref<Capabilities | null>(null)
const canDeletePages = computed(() => Boolean(projectCapabilities.value?.can_import_pages))

// ── 页面列表 ──
const pages = ref<Page[]>([])
const pagesLoading = ref(true)

async function loadPages() {
  pagesLoading.value = true
  try {
    const res = await pagesApi.list(projectId.value)
    pages.value = res.items
  } catch {
    pages.value = []
  } finally {
    pagesLoading.value = false
  }
}

async function loadProjectCapabilities() {
  try {
    projectCapabilities.value = await pagesApi.getCapabilities(projectId.value)
  } catch {
    projectCapabilities.value = null
  }
}

function openWorkspace(pageId: string) {
  router.push({ name: 'pages.workspace', params: { page_id: pageId } })
}

onMounted(() => {
  loadProjectCapabilities()
  loadPages()
})

const activeTab = ref((route.query.tab as string) || 'pages')
const tabs = ['pages', 'members', 'jobs', 'exports', 'qc', 'settings'] as const

function getPageStatusText(status: string) {
  const key = `annotation.pages.status.${status}`
  const text = t(key)
  return text === key ? status : text
}

function switchTab(tab: string) {
  activeTab.value = tab
  router.replace({ query: { ...route.query, tab } })
}

watch(() => route.query.tab, (tab) => {
  if (typeof tab === 'string' && tab !== activeTab.value) {
    activeTab.value = tab
  }
})

// ── 拖拽状态 ──
const isDragOver = ref(false)
let dragCounter = 0

function onDragEnter(e: DragEvent) {
  e.preventDefault()
  dragCounter++
  isDragOver.value = true
}

function onDragOver(e: DragEvent) {
  e.preventDefault()
}

function onDragLeave(e: DragEvent) {
  e.preventDefault()
  dragCounter--
  if (dragCounter === 0) {
    isDragOver.value = false
  }
}

function onDrop(e: DragEvent) {
  e.preventDefault()
  dragCounter = 0
  isDragOver.value = false
  const files = Array.from(e.dataTransfer?.files || [])
  addFiles(files)
}

// ── 上传队列 ──
interface UploadItem {
  id: string
  file: File
  status: 'pending' | 'uploading' | 'done' | 'error' | 'cancelled'
  progress: number
  error?: string
  result?: { asset_id: string; document_id: string; page_id: string; width: number; height: number }
  abort?: () => void
  fadeOut: boolean
}

const uploadItems = ref<UploadItem[]>([])
let idCounter = 0
const deleteError = ref('')

function addFiles(files: File[]) {
  const imageFiles = files.filter(f => f.type.startsWith('image/'))
  for (const file of imageFiles) {
    uploadItems.value.push({
      id: `upload-${++idCounter}`,
      file,
      status: 'pending',
      progress: 0,
      fadeOut: false,
    })
  }
}

function onFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files) {
    addFiles(Array.from(input.files))
    input.value = ''
  }
}

function startUpload() {
  const pending = uploadItems.value.filter(i => i.status === 'pending')
  for (const item of pending) {
    uploadSingle(item)
  }
}

function uploadSingle(item: UploadItem) {
  item.status = 'uploading'
  item.progress = 0
  item.error = undefined

  const { promise, abort } = assetsApi.uploadWithProgress(
    projectId.value,
    item.file,
    (percent) => { item.progress = percent },
  )
  item.abort = abort

  promise.then((res) => {
    item.status = 'done'
    item.progress = 100
    item.result = res.data
    setTimeout(() => {
      item.fadeOut = true
      setTimeout(() => {
        uploadItems.value = uploadItems.value.filter(i => i.id !== item.id)
      }, 300)
    }, 800)
    loadPages()
  }).catch((e) => {
    if (item.status === 'cancelled') return
    item.status = 'error'
    item.error = formatProjectDetailError(t, e, 'upload.failed')
  }).finally(() => {
    item.abort = undefined
  })
}

function cancelUpload(item: UploadItem) {
  item.error = undefined
  item.abort?.()
  item.abort = undefined
  item.status = 'cancelled'
  item.fadeOut = true
  setTimeout(() => {
    uploadItems.value = uploadItems.value.filter(i => i.id !== item.id)
  }, 300)
}

function retryUpload(item: UploadItem) {
  item.status = 'pending'
  item.error = undefined
  item.progress = 0
  uploadSingle(item)
}

function removeItem(item: UploadItem) {
  if (item.status === 'uploading') {
    item.abort?.()
    item.abort = undefined
  }
  item.fadeOut = true
  setTimeout(() => {
    uploadItems.value = uploadItems.value.filter(i => i.id !== item.id)
  }, 300)
}

function clearCompleted() {
  const toRemove = uploadItems.value.filter(i => i.status === 'done' || i.status === 'cancelled')
  for (const item of toRemove) {
    item.fadeOut = true
  }
  setTimeout(() => {
    uploadItems.value = uploadItems.value.filter(i => i.status !== 'done' && i.status !== 'cancelled')
  }, 300)
}

const pendingCount = computed(() => uploadItems.value.filter(i => i.status === 'pending').length)
const activeCount = computed(() => uploadItems.value.filter(i => i.status === 'uploading').length)

// ── 删除页面 ──
const deletingId = ref<string | null>(null)

async function deletePage(pageId: string, e: Event) {
  e.stopPropagation()
  if (!confirm(t('upload.deleteConfirm'))) return
  deletingId.value = pageId
  deleteError.value = ''
  try {
    await pagesApi.delete(pageId)
    pages.value = pages.value.filter(p => p.page_id !== pageId)
  } catch (e) {
    deleteError.value = formatProjectDetailError(t, e, 'errors.server')
  } finally {
    deletingId.value = null
  }
}

</script>

<template>
  <div class="flex-1 overflow-auto">
    <div class="max-w-5xl mx-auto p-6">
      <!-- 页面头部 -->
      <div class="mb-6">
        <nav class="flex items-center gap-1.5 text-caption text-text-secondary mb-3">
          <router-link :to="{ name: 'projects.index' }" class="hover:text-text transition-colors">
            {{ t('routes.projects.index') }}
          </router-link>
          <span class="text-text-muted">/</span>
          <span class="text-text">{{ t('routes.projects.detail') }}</span>
        </nav>
        <h1 class="text-title text-text">{{ t('routes.projects.detail') }}</h1>
      </div>

      <!-- Tab 导航 -->
      <div class="mb-6 flex flex-wrap gap-2 border-b border-border pb-3">
        <button v-for="tab in tabs" :key="tab" type="button"
          class="rounded-md px-3 py-2 text-caption font-medium transition-colors" :class="activeTab === tab
            ? 'bg-primary/10 text-primary'
            : 'text-text-secondary hover:bg-surface-muted hover:text-text'" @click="switchTab(tab)">
          {{ t(`routes.projects.tabs.${tab}`) }}
        </button>
      </div>

      <section v-if="activeTab === 'pages'">
        <!-- 拖拽上传区域 -->
        <div
          class="relative border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200 cursor-pointer"
          :class="isDragOver
            ? 'border-primary bg-primary/5'
            : 'border-border hover:border-primary/40 hover:bg-surface-muted'" @dragenter="onDragEnter"
          @dragover="onDragOver" @dragleave="onDragLeave" @drop="onDrop"
          @click="($refs.fileInput as HTMLInputElement).click()">
          <input ref="fileInput" type="file" multiple accept="image/*" class="hidden" @change="onFileSelect" />
          <Upload class="w-8 h-8 mx-auto mb-3" :class="isDragOver ? 'text-primary' : 'text-text-muted'" />
          <p class="text-body text-text mb-1">
            {{ isDragOver ? t('upload.dropHere') : t('upload.selectFiles') }}
          </p>
          <p class="text-caption text-text-muted">
            {{ isDragOver ? '' : t('upload.dragHint') }}
          </p>
        </div>

        <!-- 上传队列 -->
        <div v-if="uploadItems.length > 0" class="mt-4">
          <div class="flex items-center justify-between mb-3">
            <span class="text-caption text-text-secondary">
              {{ activeCount > 0 ? `${activeCount} ${t('upload.uploading')}` : `${uploadItems.length}
              ${t('upload.selectFiles')}` }}
            </span>
            <div class="flex gap-2">
              <button type="button"
                class="inline-flex items-center justify-center rounded-md border border-border bg-surface px-3 py-1.5 text-caption font-medium text-text transition-colors hover:bg-surface-muted disabled:cursor-not-allowed disabled:opacity-50"
                :disabled="!uploadItems.some(i => i.status === 'done' || i.status === 'cancelled')"
                @click="clearCompleted">
                {{ t('common.close') }}
              </button>
              <button v-if="pendingCount > 0" type="button"
                class="inline-flex items-center justify-center rounded-md bg-primary px-3 py-1.5 text-caption font-medium text-white transition-colors hover:bg-primary-hover"
                @click="startUpload">
                {{ t('upload.startUpload') }}
              </button>
            </div>
          </div>

          <!-- 文件状态列表 -->
          <div class="space-y-2">
            <TransitionGroup name="upload-item">
              <div v-for="item in uploadItems" :key="item.id"
                class="flex items-center gap-3 p-3 bg-surface rounded-lg border border-border transition-all duration-300"
                :class="{
                  'opacity-0 -translate-y-2': item.fadeOut,
                  'border-danger/40 bg-danger/5': item.status === 'error',
                }">
                <!-- 状态图标 -->
                <Loader2 v-if="item.status === 'uploading'" class="w-4 h-4 text-primary animate-spin shrink-0" />
                <FileCheck v-else-if="item.status === 'done'" class="w-4 h-4 text-success shrink-0" />
                <AlertCircle v-else-if="item.status === 'error'" class="w-4 h-4 text-danger shrink-0" />
                <X v-else-if="item.status === 'cancelled'" class="w-4 h-4 text-text-muted shrink-0" />
                <FileImage v-else class="w-4 h-4 text-text-muted shrink-0" />

                <!-- 文件信息 -->
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <p class="text-body text-text truncate">{{ item.file.name }}</p>
                    <span class="text-micro text-text-muted shrink-0">
                      {{ (item.file.size / 1024 / 1024).toFixed(1) }}MB
                    </span>
                  </div>

                  <!-- 进度条 -->
                  <div v-if="item.status === 'uploading'"
                    class="mt-1.5 h-1 bg-surface-muted rounded-full overflow-hidden">
                    <div class="h-full bg-primary rounded-full transition-all duration-300"
                      :style="{ width: item.progress + '%' }"></div>
                  </div>

                  <!-- 结果信息 -->
                  <p v-if="item.result" class="text-caption text-text-muted mt-1">
                    {{ item.result.width }}×{{ item.result.height }}
                  </p>

                  <!-- 错误信息 -->
                  <p v-if="item.error" class="text-caption text-danger mt-1">{{ item.error }}</p>
                </div>

                <!-- 操作按钮 -->
                <div class="flex items-center gap-1 shrink-0">
                  <button v-if="item.status === 'uploading'"
                    class="p-1 rounded hover:bg-surface-muted text-text-muted hover:text-text transition-colors"
                    :title="t('common.cancel')" @click="cancelUpload(item)">
                    <X class="w-3.5 h-3.5" />
                  </button>
                  <button v-if="item.status === 'error'"
                    class="p-1 rounded hover:bg-surface-muted text-text-muted hover:text-primary transition-colors"
                    :title="t('common.retry')" @click="retryUpload(item)">
                    <RotateCcw class="w-3.5 h-3.5" />
                  </button>
                  <button v-if="item.status === 'pending' || item.status === 'done' || item.status === 'cancelled'"
                    class="p-1 rounded hover:bg-surface-muted text-text-muted hover:text-text transition-colors"
                    :title="t('common.remove')" @click="removeItem(item)">
                    <X class="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </TransitionGroup>
          </div>
        </div>

        <!-- 已有页面列表 -->
        <div class="mt-6">
          <h3 class="text-body-medium text-text mb-3">{{ t('routes.projects.tabs.pages') }}</h3>

          <div v-if="deleteError"
            class="mb-3 rounded-lg border border-danger/30 bg-danger-bg px-4 py-3 text-caption text-danger">
            {{ deleteError }}
          </div>

          <div v-if="pagesLoading" class="space-y-2">
            <div v-for="i in 3" :key="i" class="h-16 bg-surface-alt rounded-lg animate-pulse"></div>
          </div>

          <div v-else-if="pages.length === 0"
            class="rounded-lg border border-dashed border-border bg-surface px-6 py-12 text-center text-text-muted">
            {{ t('upload.selectFiles') }}
          </div>

          <div v-else class="space-y-2">
            <div v-for="page in pages" :key="page.page_id"
              class="flex items-center gap-3 p-3 bg-surface rounded-lg border border-border hover:border-primary/40 cursor-pointer transition-all duration-fast"
              @click="openWorkspace(page.page_id)">
              <FileImage class="w-5 h-5 text-primary shrink-0" />
              <div class="flex-1 min-w-0">
                <p class="text-body text-text truncate">{{ page.filename }}</p>
                <p class="text-caption text-text-muted">
                  {{ page.width }}×{{ page.height }} · {{ getPageStatusText(page.status) }}
                </p>
              </div>
              <button type="button"
                class="inline-flex items-center gap-1.5 rounded-md border border-border bg-surface px-3 py-1.5 text-caption font-medium text-text transition-colors hover:bg-surface-muted">
                <PenTool class="w-3.5 h-3.5" />
                {{ t('common.edit') }}
              </button>
              <button v-if="canDeletePages" type="button"
                class="inline-flex items-center justify-center rounded-md p-2 text-danger transition-colors hover:bg-danger-bg"
                :loading="deletingId === page.page_id" @click="deletePage(page.page_id, $event)">
                <Loader2 v-if="deletingId === page.page_id" class="w-3.5 h-3.5 animate-spin" />
                <X v-else class="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </section>

      <template v-else-if="activeTab === 'jobs' || activeTab === 'exports' || activeTab === 'qc'">
        <div class="text-center py-8 text-gray-400">
          {{ t('common.featureNotAvailable') }}
        </div>
      </template>

      <section v-else
        class="rounded-lg border border-dashed border-border bg-surface px-6 py-12 text-center text-text-muted">
        {{ t('common.noData') }}
      </section>
    </div>
  </div>
</template>

<style scoped>
.upload-item-enter-active,
.upload-item-leave-active {
  transition: all 0.3s ease;
}

.upload-item-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.upload-item-leave-to {
  opacity: 0;
  transform: translateX(20px);
}
</style>
