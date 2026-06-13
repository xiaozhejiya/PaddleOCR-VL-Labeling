<script setup lang="ts">
/**
 * 系统设置页
 */
import { useI18n } from 'vue-i18n'
import { Globe, User, Bell, Shield } from 'lucide-vue-next'

const { t, locale } = useI18n()

const languageOptions = [
  { label: '简体中文', value: 'zh-CN' },
  { label: 'English', value: 'en-US' },
]

function changeLocale(lang: string) {
  locale.value = lang
  localStorage.setItem('k12.locale', lang)
}
</script>

<template>
  <div class="flex-1 overflow-auto">
    <div class="max-w-3xl mx-auto p-6">
      <!-- 页面头部 -->
      <div class="mb-6">
        <h1 class="text-title text-text mb-1">{{ t('routes.settings.index') }}</h1>
        <p class="text-body text-text-secondary">{{ t('routes.settings.index') }}</p>
      </div>

      <!-- 设置分组 -->
      <div class="space-y-6">
        <!-- 语言设置 -->
        <section class="bg-surface rounded-lg border border-border p-5">
          <div class="flex items-center gap-2.5 mb-4">
            <Globe class="w-4 h-4 text-primary" />
            <h2 class="text-subheading text-text">{{ t('settings.language') }}</h2>
          </div>
          <div class="max-w-xs">
            <label class="block">
              <span class="mb-1 block text-caption text-text-secondary">{{ t('settings.language') }}</span>
              <select
                :value="locale"
                class="h-9 w-full rounded-md border border-border bg-surface px-3 text-body text-text outline-none transition-colors focus:border-primary"
                @change="changeLocale(($event.target as HTMLSelectElement).value)"
              >
                <option v-for="option in languageOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
            </label>
          </div>
        </section>

        <!-- 个人信息 -->
        <section class="bg-surface rounded-lg border border-border p-5">
          <div class="flex items-center gap-2.5 mb-4">
            <User class="w-4 h-4 text-primary" />
            <h2 class="text-subheading text-text">{{ t('settings.personalInfo') }}</h2>
          </div>
          <div class="max-w-md space-y-4">
            <label class="block">
              <span class="mb-1 block text-caption text-text-secondary">{{ t('auth.username') }}</span>
              <input
                :value="''"
                :placeholder="t('auth.username')"
                readonly
                class="h-9 w-full rounded-md border border-border bg-surface-muted px-3 text-body text-text-muted outline-none"
              />
            </label>
            <label class="block">
              <span class="mb-1 block text-caption text-text-secondary">{{ t('auth.email') }}</span>
              <input
                :value="''"
                :placeholder="t('auth.email')"
                readonly
                class="h-9 w-full rounded-md border border-border bg-surface-muted px-3 text-body text-text-muted outline-none"
              />
            </label>
          </div>
        </section>

        <!-- 通知设置 -->
        <section class="bg-surface rounded-lg border border-border p-5">
          <div class="flex items-center gap-2.5 mb-4">
            <Bell class="w-4 h-4 text-primary" />
            <h2 class="text-subheading text-text">{{ t('settings.notifications') }}</h2>
          </div>
          <p class="text-caption text-text-muted">{{ t('settings.noConfigItems') }}</p>
        </section>

        <!-- 安全设置 -->
        <section class="bg-surface rounded-lg border border-border p-5">
          <div class="flex items-center gap-2.5 mb-4">
            <Shield class="w-4 h-4 text-primary" />
            <h2 class="text-subheading text-text">{{ t('settings.security') }}</h2>
          </div>
          <p class="text-caption text-text-muted">{{ t('settings.noConfigItems') }}</p>
        </section>
      </div>
    </div>
  </div>
</template>
