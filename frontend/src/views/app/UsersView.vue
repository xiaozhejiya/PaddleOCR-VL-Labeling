<script setup lang="ts">
/**
 * 用户管理页（仅系统管理员可访问）
 */
import { useI18n } from 'vue-i18n'
import { NEmpty } from 'naive-ui'

const { t } = useI18n()
</script>

<template>
  <div class="flex-1 overflow-auto">
    <div class="max-w-5xl mx-auto p-6">
      <div class="mb-6">
        <h1 class="text-title text-text">{{ t('nav.users') }}</h1>
      </div>

      <NEmpty :description="t('common.noData')" class="py-16" />
    </div>
  </div>
</template>
