<script setup lang="ts">
/**
 * 应用主布局
 * 提供全局框架：左侧导航栏、顶部栏、主内容区
 * 规范：frontend_component_library_spec.md §6 AppShell
 */
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import {
  LayoutDashboard,
  FolderKanban,
  ClipboardList,
  Database,
  PenTool,
  ShieldCheck,
  Download,
  Settings,
  LogOut,
  ChevronDown,
} from 'lucide-vue-next'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const { user, logout } = useAuth()

const userDisplayName = computed(() => user.value?.username || t('workspace.unknownUser'))
const userInitial = computed(() => (user.value?.username?.charAt(0) || t('workspace.unknownUser').charAt(0)).toUpperCase())

const currentProjectText = computed(() => {
  const raw = route.params.project_id
  const projectId = Array.isArray(raw) ? raw[0] : raw
  if (typeof projectId === 'string' && projectId.trim()) return projectId
  return t('common.noData')
})

async function handleLogout() {
  await logout()
  router.replace({ name: 'auth.login' })
}

interface NavItem {
  key: string
  icon: typeof LayoutDashboard
  routeName?: string
  routeParams?: Record<string, string>
  routeQuery?: Record<string, string>
  disabled?: boolean
}

const currentProjectId = computed(() => {
  const raw = route.params.project_id
  const id = Array.isArray(raw) ? raw[0] : raw
  return typeof id === 'string' && id.trim() ? id : null
})

const navItems = computed<NavItem[]>(() => [
  { key: 'dashboard', icon: LayoutDashboard, disabled: true },
  { key: 'projects', icon: FolderKanban, routeName: 'projects.index' },
  { key: 'tasks', icon: ClipboardList, disabled: true },
  { key: 'datasets', icon: Database, disabled: true },
  { key: 'workspace', icon: PenTool, routeName: 'projects.index' },
  ...(currentProjectId.value
    ? [{ key: 'qc', icon: ShieldCheck, routeName: 'projects.detail' as const, routeParams: { project_id: currentProjectId.value }, routeQuery: { tab: 'qc' } }]
    : [{ key: 'qc', icon: ShieldCheck, disabled: true }]),
  { key: 'exports', icon: Download, disabled: true },
  { key: 'settings', icon: Settings, routeName: 'settings.index' },
])
</script>

<template>
  <div class="h-screen flex overflow-hidden bg-bg-app">
    <!-- 左侧导航栏 -->
    <aside class="w-56 bg-surface border-r border-border flex flex-col shrink-0 z-sticky">
      <!-- Logo -->
      <div class="h-12 flex items-center px-4 border-b border-border shrink-0">
        <div class="flex items-center gap-2">
          <div class="w-6 h-6 bg-primary rounded-md flex items-center justify-center">
            <PenTool class="w-3.5 h-3.5 text-white" />
          </div>
          <span class="text-body-medium text-text">{{ t('app.logoName') }}</span>
        </div>
      </div>

      <!-- 导航项 -->
      <nav class="flex-1 py-2 px-2 space-y-0.5 overflow-y-auto" role="navigation">
        <template v-for="item in navItems" :key="item.key">
          <router-link
            v-if="item.routeName"
            :to="{
              name: item.routeName,
              ...(item.routeParams ? { params: item.routeParams } : {}),
              ...(item.routeQuery ? { query: item.routeQuery } : {}),
            }"
            :class="[
              'flex items-center gap-2.5 px-3 py-2 rounded-md text-body transition-colors',
              'text-text-secondary hover:bg-surface-muted hover:text-text',
              $route.name === item.routeName && (!item.routeQuery || Object.entries(item.routeQuery).every(([k, v]) => $route.query[k] === v)) ? 'bg-primary/8 text-primary font-medium' : '',
            ]"
          >
            <component :is="item.icon" class="w-4 h-4 shrink-0" />
            <span>{{ t(`nav.${item.key}`) }}</span>
          </router-link>
          <span
            v-else
            :class="[
              'flex items-center gap-2.5 px-3 py-2 rounded-md text-body',
              'text-text-muted cursor-not-allowed',
            ]"
            aria-disabled="true"
          >
            <component :is="item.icon" class="w-4 h-4 shrink-0" />
            <span>{{ t(`nav.${item.key}`) }}</span>
          </span>
        </template>
      </nav>

      <!-- 当前项目 -->
      <div class="px-3 py-2 border-t border-border">
        <div class="text-micro text-text-muted mb-1">{{ t('project.currentProject') }}</div>
        <button class="flex items-center justify-between w-full px-2 py-1.5 rounded-md text-caption text-text hover:bg-surface-muted transition-colors">
          <span class="truncate">{{ currentProjectText }}</span>
          <ChevronDown class="w-3.5 h-3.5 shrink-0 text-text-muted" />
        </button>
      </div>

      <!-- 用户信息 -->
      <div class="px-3 py-3 border-t border-border">
        <div class="flex items-center gap-2.5">
          <div class="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-caption font-medium text-primary">
            {{ userInitial }}
          </div>
          <div class="flex-1 min-w-0">
            <div class="text-body-medium text-text truncate">{{ userDisplayName }}</div>
            <div class="flex items-center gap-1 text-micro text-success">
              <span class="w-1.5 h-1.5 rounded-full bg-success"></span>
              {{ t('workspace.online') }}
            </div>
          </div>
          <button
            class="p-1.5 rounded-md text-text-muted hover:text-danger hover:bg-danger-bg transition-colors"
            :aria-label="t('auth.logout')"
            @click="handleLogout"
          >
            <LogOut class="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>

    <!-- 右侧主内容区 -->
    <main class="flex-1 flex flex-col overflow-hidden">
      <router-view />
    </main>
  </div>
</template>
