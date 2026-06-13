<script setup lang="ts">
/**
 * 用户管理页（仅系统管理员可访问）
 */
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<template>
  <div class="flex-1 overflow-auto">
    <div class="max-w-5xl mx-auto p-6">
      <div class="mb-6">
        <h1 class="text-title text-text">{{ t('nav.users') }}</h1>
      </div>

      <div class="rounded-lg border border-dashed border-border bg-surface px-6 py-16 text-center text-text-muted">
        {{ t('common.noData') }}
      </div>
    </div>
  </div>
</template>
