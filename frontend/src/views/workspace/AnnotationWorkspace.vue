<script setup lang="ts">
/**
 * 标注工作台页面
 * 通过 AnnotationWorkspaceLayout 提供布局
 * 负责加载 page 元数据、图片访问入口、latest revision、label registry、QC 列表和 capabilities
 *
 * 参考：doc/开发文档/前端/frontend_routing_spec.md 第 14 章
 */
import { ref, computed, onMounted, provide, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { pagesApi, type Page, type Capabilities } from '@/api/pages'
import { annotationsApi, type AnnotationRevision } from '@/api/annotations'
import { qcApi, type QcIssue } from '@/api/qc'
import { ApiClientError } from '@/api/client'

const { t } = useI18n()
const route = useRoute()

const pageId = computed(() => route.params.page_id as string)
const revisionId = computed(() => route.query.revision_id as string | undefined)

// 状态
const loading = ref(true)
const error = ref('')
const errorCode = ref<number | undefined>()

// 数据
const page = ref<Page | null>(null)
const capabilities = ref<Capabilities | null>(null)
const revision = ref<AnnotationRevision | null>(null)
const qcIssues = ref<QcIssue[]>([])

/** 是否只读：历史 revision 或无编辑权限 */
const isReadonly = computed(() => {
  if (revisionId.value) return true
  if (capabilities.value && !capabilities.value.can_edit) return true
  return false
})

// 向布局层提供保存状态
const saveStatus = ref<'saved' | 'dirty' | 'readonly'>('saved')
provide('saveStatus', saveStatus)

/** 更新保存状态 */
function updateSaveStatus(status: 'saved' | 'dirty' | 'readonly') {
  saveStatus.value = status
}
provide('updateSaveStatus', updateSaveStatus)

/** 加载工作台数据 */
async function loadWorkspace() {
  loading.value = true
  error.value = ''
  errorCode.value = undefined

  try {
    // 1. 校验 page_id
    if (!pageId.value) {
      error.value = t('errors.notFound')
      errorCode.value = 404
      return
    }

    // 2. 加载 page 元数据
    try {
      page.value = await pagesApi.get(pageId.value)
    } catch (e) {
      if (e instanceof ApiClientError) {
        errorCode.value = e.status
        if (e.status === 404) {
          error.value = t('errors.notFound')
        } else if (e.status === 403) {
          error.value = t('errors.forbidden')
        } else {
          error.value = t('errors.server')
        }
      }
      return
    }

    // 3. 加载 capabilities
    try {
      capabilities.value = await pagesApi.getCapabilities(page.value.project_id)
    } catch {
      // capabilities 加载失败不阻止页面显示，按无权限处理
      capabilities.value = { can_edit: false, can_review: false, can_export: false, can_manage: false }
    }

    // 4. 加载 revision
    try {
      if (revisionId.value) {
        // 加载指定 revision
        const revisions = await annotationsApi.listRevisions(pageId.value)
        revision.value = revisions.find(r => r.id === revisionId.value) || null
      } else {
        // 加载 latest revision
        revision.value = await annotationsApi.getLatest(pageId.value)
      }
    } catch (e) {
      if (e instanceof ApiClientError && e.status === 404) {
        // 无标注数据，正常情况
        revision.value = null
      }
    }

    // 5. 加载 QC 问题
    try {
      const qcResponse = await qcApi.listByPage(pageId.value)
      qcIssues.value = qcResponse.items
    } catch {
      // QC 加载失败不阻止页面显示
    }

    // 6. 更新保存状态
    if (isReadonly.value) {
      saveStatus.value = 'readonly'
    } else {
      saveStatus.value = 'saved'
    }
  } finally {
    loading.value = false
  }
}

// 监听 page_id 或 revision_id 变化
watch([pageId, revisionId], () => {
  loadWorkspace()
})

onMounted(() => {
  loadWorkspace()
})
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- Loading -->
    <div v-if="loading" class="flex-1 flex items-center justify-center text-muted">
      {{ t('common.loading') }}
    </div>

    <!-- Error -->
    <div v-else-if="error" class="flex-1 flex items-center justify-center">
      <div class="text-center">
        <p class="text-lg text-text mb-2">{{ error }}</p>
        <p v-if="errorCode" class="text-sm text-muted mb-4">Error {{ errorCode }}</p>
        <button
          class="px-4 py-2 bg-accent text-white rounded-md hover:bg-accent/90"
          @click="loadWorkspace"
        >
          {{ t('common.retry') }}
        </button>
      </div>
    </div>

    <!-- Workspace -->
    <div v-else-if="page" class="flex-1 flex flex-col">
      <!-- 画布区域占位 -->
      <div class="flex-1 flex items-center justify-center bg-background">
        <div class="text-center text-muted">
          <p class="text-lg mb-2">{{ page.filename }}</p>
          <p class="text-sm">{{ page.width }} × {{ page.height }}</p>
          <p v-if="isReadonly" class="text-xs mt-2 text-warning">
            {{ t('annotation.saveStatus.readonly') }}
          </p>
          <p v-if="revision" class="text-xs mt-1">
            Revision #{{ revision.revision_no }}
          </p>
          <p v-if="qcIssues.length > 0" class="text-xs mt-1 text-danger">
            {{ qcIssues.length }} QC {{ t('errors.notFound') }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
