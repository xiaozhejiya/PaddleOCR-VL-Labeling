<script setup lang="ts">
/**
 * 标注工作台布局组件
 * 负责标注工作台外壳，包括左任务队列、中间画布、右属性/QC 面板、底部 revision 或任务日志区域
 *
 * 职责：
 * 1. 接入工作台保存状态
 * 2. 向路由离页拦截暴露 saved、dirty、autosave_pending、autosaving、autosave_failed、manual_saving、conflict、readonly
 * 3. 在页面切换、revision 切换、离开工作台和关闭浏览器前触发离页确认
 *
 * 不负责：
 * 1. 不在路由层实现 bbox 绘制、坐标换算、自动保存 debounce 或冲突合并算法
 */
import { ref, provide, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const router = useRouter()

// 保存状态：saved | dirty | autosave_pending | autosaving | autosave_failed | manual_saving | conflict | readonly
type SaveStatus = 'saved' | 'dirty' | 'autosave_pending' | 'autosaving' | 'autosave_failed' | 'manual_saving' | 'conflict' | 'readonly'

const saveStatus = ref<SaveStatus>('saved')
const pageTitle = ref('')

// 向子组件提供保存状态
provide('saveStatus', saveStatus)
provide('updateSaveStatus', (status: SaveStatus) => {
  saveStatus.value = status
})

/**
 * 判断当前状态是否需要离页确认
 */
function needsLeaveConfirmation(): boolean {
  return ['dirty', 'autosave_pending', 'autosaving', 'autosave_failed', 'manual_saving', 'conflict'].includes(saveStatus.value)
}

/**
 * 路由离开守卫
 */
const unregisterGuard = router.beforeEach((to, _from, next) => {
  // 只处理从工作台离开的情况
  if (to.meta.workspaceRoute) {
    next()
    return
  }

  if (needsLeaveConfirmation()) {
    // TODO: 显示确认对话框
    const confirmed = window.confirm(t('workspace.leaveConfirm'))
    if (confirmed) {
      next()
    } else {
      next(false)
    }
  } else {
    next()
  }
})

/**
 * 浏览器关闭/刷新守卫
 */
function handleBeforeUnload(event: BeforeUnloadEvent) {
  if (needsLeaveConfirmation()) {
    event.preventDefault()
    event.returnValue = ''
  }
}

onMounted(() => {
  window.addEventListener('beforeunload', handleBeforeUnload)
})

onUnmounted(() => {
  window.removeEventListener('beforeunload', handleBeforeUnload)
  unregisterGuard()
})
</script>

<template>
  <div class="h-screen flex flex-col">
    <!-- 顶部工具栏 -->
    <header class="h-12 bg-surface border-b border-border flex items-center px-4 shrink-0">
      <router-link :to="{ name: 'projects.index' }" class="text-muted hover:text-text mr-4">
        {{ t('common.back') }}
      </router-link>
      <h1 class="text-sm font-medium text-text">{{ pageTitle || t('routes.pages.workspace') }}</h1>

      <!-- 保存状态指示器 -->
      <div class="ml-auto">
        <span
          class="text-xs px-2 py-1 rounded"
          :class="{
            'bg-success/10 text-success': saveStatus === 'saved',
            'bg-warning/10 text-warning': saveStatus === 'dirty' || saveStatus === 'autosave_pending',
            'bg-accent/10 text-accent': saveStatus === 'autosaving' || saveStatus === 'manual_saving',
            'bg-danger/10 text-danger': saveStatus === 'autosave_failed' || saveStatus === 'conflict',
            'bg-muted/10 text-muted': saveStatus === 'readonly',
          }"
        >
          {{ t(`annotation.saveStatus.${saveStatus}`) }}
        </span>
      </div>
    </header>

    <!-- 主要工作区 -->
    <div class="flex-1 flex overflow-hidden">
      <!-- 左侧任务队列 -->
      <aside class="w-64 bg-surface border-r border-border shrink-0 overflow-y-auto">
        <slot name="queue">
          <div class="p-4">
            <h3 class="text-sm font-medium text-text mb-2">{{ t('workspace.taskQueue') }}</h3>
            <p class="text-xs text-muted">{{ t('common.loading') }}</p>
          </div>
        </slot>
      </aside>

      <!-- 中间画布区 -->
      <main class="flex-1 bg-background relative overflow-hidden">
        <slot>
          <div class="absolute inset-0 flex items-center justify-center text-muted">
            {{ t('workspace.canvasPlaceholder') }}
          </div>
        </slot>
      </main>

      <!-- 右侧属性/QC 面板 -->
      <aside class="w-72 bg-surface border-l border-border shrink-0 overflow-y-auto">
        <slot name="panel">
          <div class="p-4">
            <h3 class="text-sm font-medium text-text mb-2">{{ t('workspace.propertiesPanel') }}</h3>
            <p class="text-xs text-muted">{{ t('common.loading') }}</p>
          </div>
        </slot>
      </aside>
    </div>

    <!-- 底部 revision/任务日志 -->
    <footer class="h-8 bg-surface border-t border-border flex items-center px-4 shrink-0">
      <slot name="footer">
        <span class="text-xs text-muted">{{ t('workspace.revisionLog') }}</span>
      </slot>
    </footer>
  </div>
</template>
