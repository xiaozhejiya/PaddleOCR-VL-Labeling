<script setup lang="ts">
/**
 * 应用主布局
 * 负责工作台通用框架，包括侧边栏、顶部状态区、主内容区、全局 toast、全局 modal 容器
 */
import { useI18n } from 'vue-i18n'
import { useAuth } from '@/composables/useAuth'

const { t } = useI18n()
const { logout } = useAuth()

async function handleLogout() {
  await logout()
  // TODO: 跳转到登录页
}
</script>

<template>
  <div class="min-h-screen flex">
    <!-- 侧边栏 -->
    <aside class="w-64 bg-surface border-r border-border flex flex-col">
      <div class="p-4 border-b border-border">
        <h1 class="text-lg font-bold text-text">{{ t('routes.app.home') }}</h1>
      </div>

      <nav class="flex-1 p-4 space-y-2">
        <router-link
          :to="{ name: 'projects.index' }"
          class="block px-3 py-2 rounded-md text-text hover:bg-background"
          active-class="bg-background"
        >
          {{ t('routes.projects.index') }}
        </router-link>

        <router-link
          :to="{ name: 'settings.index' }"
          class="block px-3 py-2 rounded-md text-text hover:bg-background"
          active-class="bg-background"
        >
          {{ t('routes.settings.index') }}
        </router-link>
      </nav>

      <div class="p-4 border-t border-border">
        <button
          class="w-full px-3 py-2 text-sm text-muted hover:text-text"
          @click="handleLogout"
        >
          {{ t('auth.logout') }}
        </button>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="flex-1 overflow-auto">
      <router-view />
    </main>
  </div>
</template>
