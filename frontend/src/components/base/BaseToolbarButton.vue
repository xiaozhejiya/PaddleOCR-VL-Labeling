<script setup lang="ts">
/**
 * 工具栏按钮组件
 * 用于画布工具栏、表格工具栏、面板 header 工具
 * 规范：frontend_component_library_spec.md §5.2
 */
import { Loader2 } from 'lucide-vue-next'
import type { Component } from 'vue'

interface Props {
  icon: Component
  label?: string
  selected?: boolean
  disabled?: boolean
  loading?: boolean
  ariaLabel: string
  shortcut?: string
}

const props = withDefaults(defineProps<Props>(), {
  selected: false,
  disabled: false,
  loading: false,
})
</script>

<template>
  <button
    :disabled="disabled || loading"
    :aria-label="ariaLabel"
    :title="shortcut ? `${ariaLabel} (${shortcut})` : ariaLabel"
    :class="[
      'inline-flex items-center gap-1.5 rounded-md px-2 py-1.5 text-caption font-medium shrink-0',
      'transition-all duration-fast ease-standard',
      'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus',
      'disabled:opacity-50 disabled:cursor-not-allowed',
      selected
        ? 'bg-primary/10 text-primary border border-primary/30'
        : 'text-text-secondary hover:bg-surface-muted hover:text-text active:bg-surface-alt border border-transparent',
    ]"
  >
    <Loader2 v-if="loading" class="w-4 h-4 animate-spin shrink-0" />
    <component :is="icon" v-else class="w-4 h-4 shrink-0" />
    <span v-if="label" class="hidden sm:inline">{{ label }}</span>
  </button>
</template>
