<script setup lang="ts">
/**
 * 标注工作台布局组件
 * 负责标注工作台外壳：面包屑、状态统计栏、工具栏、左右面板、画布、底部缩略图条、底部状态栏
 *
 * 职责：
 * 1. 接入工作台保存状态
 * 2. 向路由离页拦截暴露 saved、dirty、autosave_pending、autosaving、autosave_failed、manual_saving、conflict、readonly
 * 3. 在页面切换、revision 切换、离开工作台和关闭浏览器前触发离页确认
 *
 * 不负责：
 * 1. 不在路由层实现 bbox 绘制、坐标换算、自动保存 debounce 或冲突合并算法
 */
import { ref, provide, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter, type RouteLocationNormalized } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuth } from '@/composables/useAuth'
import { pagesApi } from '@/api/pages'
import { projectsApi } from '@/api/projects'
import { SAVE_STATUS_KEY, UPDATE_SAVE_STATUS_KEY, type SaveStatus } from './workspaceGuards'
import {
  Search,
  Keyboard,
  Bell,
  HelpCircle,
  ChevronDown,
  Settings,
} from 'lucide-vue-next'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const { user } = useAuth()

const userDisplayName = computed(() => user.value?.username || t('workspace.unknownUser'))
const userInitial = computed(() => (user.value?.username?.charAt(0) || t('workspace.unknownUser').charAt(0)).toUpperCase())
const roleText = computed(() => t('workspace.roleUnknown'))
const timeZone = computed(() => {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || '--'
  } catch {
    return '--'
  }
})

// ── 面包屑数据 ──
const projectName = ref('')
const projectId = ref('')
const pageFilename = ref('')

async function loadBreadcrumb() {
  const pageId = route.params.page_id as string
  if (!pageId) return
  try {
    const page = await pagesApi.get(pageId)
    pageFilename.value = page.filename || page.page_id
    if (page.project_id) {
      projectId.value = String(page.project_id)
      try {
        const project = await projectsApi.get(projectId.value)
        projectName.value = project.name
      } catch { /* ignore */ }
    }
  } catch { /* ignore */ }
}

// ── 保存状态 ──
const saveStatus = ref<SaveStatus>('saved')

function updateSaveStatus(status: SaveStatus) { saveStatus.value = status }

const footerSaveDotClass = computed(() => {
  if (saveStatus.value === 'saved') return 'bg-success'
  if (saveStatus.value === 'dirty' || saveStatus.value === 'autosave_pending') return 'bg-warning'
  if (saveStatus.value === 'autosaving' || saveStatus.value === 'manual_saving') return 'bg-primary animate-pulse'
  if (saveStatus.value === 'autosave_failed' || saveStatus.value === 'conflict') return 'bg-danger'
  return 'bg-text-muted'
})
const footerSaveText = computed(() => t(`annotation.saveStatus.${saveStatus.value}`))

provide(SAVE_STATUS_KEY, saveStatus)
provide(UPDATE_SAVE_STATUS_KEY, updateSaveStatus)

// ── 离页守卫 ──
function needsLeaveConfirmation(): boolean {
  return ['dirty', 'autosave_pending', 'autosaving', 'autosave_failed', 'manual_saving', 'conflict'].includes(saveStatus.value)
}

function isLightweightWorkspaceNavigation(to: RouteLocationNormalized, from: RouteLocationNormalized): boolean {
  if (!to.meta.workspaceRoute || !from.meta.workspaceRoute) return false
  return to.params.page_id === from.params.page_id && (to.query.revision_id ?? '') === (from.query.revision_id ?? '')
}

const unregisterGuard = router.beforeEach((to, _from, next) => {
  if (!needsLeaveConfirmation()) { next(); return }
  if (isLightweightWorkspaceNavigation(to, _from)) { next(); return }
  const confirmed = window.confirm(t('workspace.leaveConfirm'))
  confirmed ? next() : next(false)
})

function handleBeforeUnload(event: BeforeUnloadEvent) {
  if (needsLeaveConfirmation()) { event.preventDefault(); event.returnValue = '' }
}

onMounted(() => {
  window.addEventListener('beforeunload', handleBeforeUnload)
  loadBreadcrumb()
})
onUnmounted(() => {
  window.removeEventListener('beforeunload', handleBeforeUnload)
  unregisterGuard()
})
</script>

<template>
  <div class="h-screen flex flex-col bg-bg-app">
    <!-- ═══ 顶部面包屑栏 ═══ -->
    <header class="h-12 bg-surface border-b border-border flex items-center px-4 shrink-0 z-sticky">
      <!-- 面包屑 -->
      <nav class="flex items-center gap-1.5 text-caption text-text-secondary" :aria-label="t('common.breadcrumb')">
        <router-link :to="{ name: 'projects.index' }" class="hover:text-text transition-colors">
          {{ t('nav.projects') }}
        </router-link>
        <span class="text-text-muted">/</span>
        <router-link v-if="projectId" :to="{ name: 'projects.detail', params: { project_id: projectId } }"
          class="text-text hover:text-primary truncate max-w-48 transition-colors">
          {{ projectName || t('common.loading') }}
        </router-link>
        <span v-else class="text-text truncate max-w-48">{{ projectName || t('common.loading') }}</span>
        <span class="text-text-muted">/</span>
        <span class="text-text truncate max-w-48">{{ pageFilename || t('common.loading') }}</span>
        <span class="text-text-muted">/</span>
        <span class="text-text font-medium">{{ t('routes.pages.workspace') }}</span>
      </nav>

      <!-- 右侧操作区 -->
      <div class="ml-auto flex items-center gap-2">
        <!-- 搜索 -->
        <div class="relative">
          <Search class="absolute left-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-muted" />
          <input type="text" :placeholder="t('common.searchPlaceholder')"
            class="h-7 w-56 pl-7 pr-3 text-caption bg-surface-muted border border-border rounded-md text-text placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-focus focus:border-primary transition-colors" />
        </div>

        <!-- 快捷键 -->
        <button
          class="h-7 px-2 text-caption text-text-secondary hover:bg-surface-muted rounded-md flex items-center gap-1 transition-colors">
          <Keyboard class="w-3.5 h-3.5" />
          {{ t('project.keyboardShortcuts') }}
        </button>

        <!-- 提交任务 -->
        <button
          class="h-7 px-3 bg-primary text-white text-caption font-medium rounded-md hover:bg-primary-hover active:bg-primary-active transition-colors flex items-center gap-1">
          {{ t('project.submitTask') }}
          <ChevronDown class="w-3 h-3" />
        </button>

        <!-- 图标操作 -->
        <div class="flex items-center gap-0.5 ml-1">
          <button
            class="w-7 h-7 flex items-center justify-center rounded-md text-text-secondary hover:bg-surface-muted transition-colors relative">
            <Bell class="w-4 h-4" />
            <span
              class="absolute -top-0.5 -right-0.5 w-3.5 h-3.5 bg-danger text-white text-micro rounded-full flex items-center justify-center">!</span>
          </button>
          <button
            class="w-7 h-7 flex items-center justify-center rounded-md text-text-secondary hover:bg-surface-muted transition-colors">
            <HelpCircle class="w-4 h-4" />
          </button>
          <button
            class="w-7 h-7 flex items-center justify-center rounded-md text-text-secondary hover:bg-surface-muted transition-colors">
            <Settings class="w-4 h-4" />
          </button>
        </div>

        <!-- 用户头像 -->
        <div class="flex items-center gap-1.5 ml-1 pl-2 border-l border-border">
          <div
            class="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center text-caption font-medium text-primary">
            {{ userInitial }}</div>
          <span class="text-caption text-text">{{ userDisplayName }}</span>
          <ChevronDown class="w-3 h-3 text-text-muted" />
        </div>
      </div>
    </header>

    <!-- ═══ 状态统计栏 ═══ -->
    <div class="h-16 bg-surface border-b border-border flex items-center px-6 shrink-0 gap-8">
      <!-- 任务进度 -->
      <div class="flex-1 max-w-48">
        <div class="text-micro text-text-tertiary mb-1">{{ t('project.taskProgress') }}</div>
        <div class="flex items-center gap-2">
          <div class="flex-1 h-1.5 bg-surface-alt rounded-full overflow-hidden">
            <div class="h-full bg-primary rounded-full" style="width: 0%"></div>
          </div>
          <span class="text-body-medium text-text">--</span>
        </div>
        <div class="text-micro text-text-muted mt-0.5">-- / --</div>
      </div>

      <!-- 图片进度 -->
      <div class="max-w-32">
        <div class="text-micro text-text-tertiary mb-1">{{ t('project.imageProgress') }}</div>
        <div class="text-heading text-text">-- <span class="text-text-muted text-body">/</span> --</div>
      </div>

      <!-- 当前图片 -->
      <div class="max-w-32">
        <div class="text-micro text-text-tertiary mb-1">{{ t('project.currentImage') }}</div>
        <div class="text-heading text-text">-- <span class="text-text-muted text-body">/</span> --</div>
      </div>

      <!-- 标注时长 -->
      <div class="max-w-32">
        <div class="text-micro text-text-tertiary mb-1">{{ t('project.annotationTime') }}</div>
        <div class="text-heading font-mono text-text">--:--:--</div>
      </div>

      <!-- 保存状态 -->
      <div class="max-w-40">
        <div class="text-micro text-text-tertiary mb-1">{{ t('common.save') }}</div>
        <div class="flex items-center gap-1.5">
          <span :class="[
            'w-2 h-2 rounded-full shrink-0',
            saveStatus === 'saved' ? 'bg-success' : '',
            saveStatus === 'dirty' || saveStatus === 'autosave_pending' ? 'bg-warning' : '',
            saveStatus === 'autosaving' || saveStatus === 'manual_saving' ? 'bg-primary animate-pulse' : '',
            saveStatus === 'autosave_failed' || saveStatus === 'conflict' ? 'bg-danger' : '',
            saveStatus === 'readonly' ? 'bg-text-muted' : '',
          ]" />
          <span class="text-body text-text">
            {{ t(`annotation.saveStatus.${saveStatus}`) }}
          </span>
        </div>
        <div class="text-micro text-text-muted mt-0.5">{{ t('workspace.lastSaved', { time: '--:--:--' }) }}</div>
      </div>

      <!-- Revision -->
      <div class="max-w-24">
        <div class="text-micro text-text-tertiary mb-1">{{ t('project.revision') }}</div>
        <div class="text-heading text-text">--</div>
        <div class="text-micro text-primary">{{ t('project.base') }}: --</div>
      </div>
    </div>

    <!-- ═══ 主要工作区 ═══ -->
    <div class="flex-1 flex overflow-hidden">
      <!-- 中间画布区（左右面板由子路由自行渲染） -->
      <main class="flex-1 bg-bg-canvas relative overflow-hidden flex flex-col">
        <router-view />
      </main>
    </div>

    <!-- ═══ 底部状态栏 ═══ -->
    <footer
      class="h-8 bg-surface border-t border-border flex items-center px-4 shrink-0 text-micro text-text-tertiary gap-6 z-sticky">
      <slot name="footer">
        <div class="flex items-center gap-1.5">
          <span :class="['w-1.5 h-1.5 rounded-full', footerSaveDotClass]"></span>
          {{ footerSaveText }}
        </div>
        <span>{{ t('workspace.autoSaveInterval') }}</span>
        <span class="ml-auto">{{ t('workspace.currentUser') }}：{{ userDisplayName }}（{{ roleText }}）</span>
        <div class="flex items-center gap-1.5">
          {{ t('workspace.networkStatus') }}：
          <span class="w-1.5 h-1.5 rounded-full bg-success"></span>
          {{ t('workspace.networkGood') }}
        </div>
        <span>{{ t('workspace.timezone') }}：{{ timeZone }}</span>
      </slot>
    </footer>
  </div>
</template>
