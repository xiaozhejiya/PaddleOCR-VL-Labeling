<script setup lang="ts">
/**
 * 项目详情页
 */
import { computed, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { assetsApi, type AssetUploadResponse } from '@/api/assets'
import { pagesApi, type Page } from '@/api/pages'
import { ApiClientError } from '@/api/client'
import { NTabs, NTabPane, NUpload, NButton, NEmpty } from 'naive-ui'
import type { UploadFileInfo } from 'naive-ui'
import { FileCheck, AlertCircle, Loader2, FileImage, PenTool } from 'lucide-vue-next'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const projectId = computed(() => route.params.project_id as string)

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

function openWorkspace(pageId: string) {
  router.push({ name: 'pages.workspace', params: { page_id: pageId } })
}

onMounted(() => { loadPages() })

const activeTab = ref((route.query.tab as string) || 'pages')

function switchTab(tab: string) {
  activeTab.value = tab
  router.replace({ query: { ...route.query, tab } })
}

// ── 上传状态 ──
interface UploadItem {
  file: File
  status: 'pending' | 'uploading' | 'done' | 'error'
  result?: AssetUploadResponse['data']
  error?: string
}

const uploadItems = ref<UploadItem[]>([])

function handleUploadChange(options: { fileList: UploadFileInfo[] }) {
  const newFiles = options.fileList
    .filter(f => f.status === 'pending' || !f.status)
    .map(f => ({
      file: f.file!,
      status: 'pending' as const,
    }))
  uploadItems.value = newFiles
}

async function startUpload() {
  const pending = uploadItems.value.filter(i => i.status === 'pending')
  for (const item of pending) {
    item.status = 'uploading'
    try {
      const res = await assetsApi.upload(projectId.value, item.file)
      item.status = 'done'
      item.result = res.data
    } catch (e) {
      item.status = 'error'
      item.error = e instanceof ApiClientError ? e.message : t('upload.failed')
    }
  }
}

function clearCompleted() {
  uploadItems.value = uploadItems.value.filter(i => i.status !== 'done')
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
      <NTabs v-model:value="activeTab" type="line" @update:value="switchTab">
        <NTabPane name="pages" :tab="t('routes.projects.tabs.pages')">
          <NUpload
            multiple
            directory-dnd
            accept="image/*"
            :max="50"
            @change="handleUploadChange"
          >
            <NButton>{{ t('upload.selectFiles') }}</NButton>
          </NUpload>

          <!-- 上传按钮和文件列表 -->
          <div v-if="uploadItems.length > 0" class="mt-4">
            <div class="flex items-center justify-between mb-3">
              <span class="text-caption text-text-secondary">
                {{ uploadItems.length }} {{ t('upload.selectFiles') }}
              </span>
              <div class="flex gap-2">
                <NButton size="small" @click="clearCompleted">
                  {{ t('common.close') }}
                </NButton>
                <NButton
                  type="primary"
                  size="small"
                  :disabled="!uploadItems.some(i => i.status === 'pending')"
                  @click="startUpload"
                >
                  {{ t('upload.startUpload') }}
                </NButton>
              </div>
            </div>

            <!-- 文件状态列表 -->
            <div class="space-y-2">
              <div
                v-for="(item, index) in uploadItems"
                :key="index"
                class="flex items-center gap-3 p-3 bg-surface rounded-lg border border-border"
              >
                <Loader2 v-if="item.status === 'uploading'" class="w-4 h-4 text-primary animate-spin shrink-0" />
                <FileCheck v-else-if="item.status === 'done'" class="w-4 h-4 text-success shrink-0" />
                <AlertCircle v-else-if="item.status === 'error'" class="w-4 h-4 text-danger shrink-0" />
                <div class="flex-1 min-w-0">
                  <p class="text-body text-text truncate">{{ item.file.name }}</p>
                  <p v-if="item.result" class="text-caption text-text-muted">
                    {{ item.result.asset_id }} · {{ item.result.width }}×{{ item.result.height }}
                  </p>
                  <p v-if="item.error" class="text-caption text-danger">{{ item.error }}</p>
                </div>
                <span class="text-caption text-text-muted shrink-0">
                  {{ (item.file.size / 1024 / 1024).toFixed(1) }}MB
                </span>
              </div>
            </div>
          </div>

          <!-- 已有页面列表 -->
          <div class="mt-6">
            <h3 class="text-body-medium text-text mb-3">{{ t('routes.projects.tabs.pages') }}</h3>

            <div v-if="pagesLoading" class="space-y-2">
              <div v-for="i in 3" :key="i" class="h-16 bg-surface-alt rounded-lg animate-pulse"></div>
            </div>

            <NEmpty
              v-else-if="pages.length === 0"
              :description="t('upload.selectFiles')"
              class="py-12"
            />

            <div v-else class="space-y-2">
              <div
                v-for="page in pages"
                :key="page.page_id"
                class="flex items-center gap-3 p-3 bg-surface rounded-lg border border-border hover:border-primary/40 cursor-pointer transition-all duration-fast"
                @click="openWorkspace(page.page_id)"
              >
                <FileImage class="w-5 h-5 text-primary shrink-0" />
                <div class="flex-1 min-w-0">
                  <p class="text-body text-text truncate">{{ page.filename }}</p>
                  <p class="text-caption text-text-muted">{{ page.width }}×{{ page.height }} · {{ page.status }}</p>
                </div>
                <NButton size="small" quaternary>
                  <template #icon><PenTool /></template>
                  {{ t('annotation.tools.select') }}
                </NButton>
              </div>
            </div>
          </div>
        </NTabPane>

        <NTabPane name="members" :tab="t('routes.projects.tabs.members')">
          <NEmpty :description="t('common.noData')" class="py-12" />
        </NTabPane>

        <NTabPane name="jobs" :tab="t('routes.projects.tabs.jobs')">
          <NEmpty :description="t('common.noData')" class="py-12" />
        </NTabPane>

        <NTabPane name="exports" :tab="t('routes.projects.tabs.exports')">
          <NEmpty :description="t('common.noData')" class="py-12" />
        </NTabPane>

        <NTabPane name="settings" :tab="t('routes.projects.tabs.settings')">
          <NEmpty :description="t('common.noData')" class="py-12" />
        </NTabPane>
      </NTabs>
    </div>
  </div>
</template>
