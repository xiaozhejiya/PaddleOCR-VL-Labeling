<script setup lang="ts">
/**
 * 基础按钮组件
 * 支持 disabled、loading 状态
 */
import { Loader2 } from 'lucide-vue-next'

interface Props {
  variant?: 'primary' | 'secondary' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  disabled: false,
  loading: false,
})

const variantClasses = {
  primary: 'bg-accent text-white hover:bg-accent/90',
  secondary: 'bg-surface text-text border border-border hover:bg-background',
  danger: 'bg-danger text-white hover:bg-danger/90',
}

const sizeClasses = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base',
}
</script>

<template>
  <button
    :disabled="disabled || loading"
    :class="[
      'rounded-md font-medium transition-colors inline-flex items-center justify-center',
      'focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2',
      'disabled:opacity-50 disabled:cursor-not-allowed',
      variantClasses[variant],
      sizeClasses[size],
    ]"
  >
    <Loader2 v-if="loading" class="w-4 h-4 mr-2 animate-spin" />
    <slot />
  </button>
</template>
