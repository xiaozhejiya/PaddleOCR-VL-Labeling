<script setup lang="ts">
/**
 * 状态 Badge 组件
 * 用于业务状态展示：saved、dirty、saving、conflict 等
 * 规范：frontend_component_library_spec.md §5.4
 */
import { CircleCheck, CircleAlert, Loader2, Lock } from 'lucide-vue-next'
import type { Component } from 'vue'

type StatusVariant = 'saved' | 'dirty' | 'saving' | 'conflict' | 'readonly' | 'locked' | 'submitted' | 'reviewed' | 'failed' | 'info'

interface Props {
  status: StatusVariant
  label?: string
}

const props = defineProps<Props>()

const config: Record<StatusVariant, { variant: string; icon: Component | null }> = {
  saved: { variant: 'success', icon: CircleCheck },
  dirty: { variant: 'warning', icon: null },
  saving: { variant: 'info', icon: Loader2 },
  conflict: { variant: 'danger', icon: CircleAlert },
  readonly: { variant: 'neutral', icon: Lock },
  locked: { variant: 'neutral', icon: Lock },
  submitted: { variant: 'info', icon: null },
  reviewed: { variant: 'success', icon: CircleCheck },
  failed: { variant: 'danger', icon: CircleAlert },
  info: { variant: 'info', icon: null },
}

const variantClasses: Record<string, string> = {
  neutral: 'bg-surface-alt text-text-secondary',
  success: 'bg-success-bg text-success',
  warning: 'bg-warning-bg text-warning',
  danger: 'bg-danger-bg text-danger',
  info: 'bg-info-bg text-info',
}
</script>

<template>
  <span
    :class="[
      'inline-flex items-center gap-1 px-2 py-0.5 text-caption font-medium rounded-sm whitespace-nowrap',
      variantClasses[config[status].variant],
    ]"
  >
    <component
      :is="config[status].icon"
      v-if="config[status].icon"
      :class="['w-3 h-3 shrink-0', status === 'saving' ? 'animate-spin' : '']"
    />
    <span v-if="label">{{ label }}</span>
  </span>
</template>
