<script setup lang="ts">
/**
 * Kbd 组件
 * 用于快捷键提示，使用 mono 字体
 * 规范：frontend_component_library_spec.md §5.4
 */
</script>

<template>
  <kbd
    class="inline-flex items-center justify-center min-w-5 h-5 px-1 text-micro font-mono font-medium bg-surface-alt text-text-tertiary border border-border rounded-sm"
  >
    <slot />
  </kbd>
</template>
