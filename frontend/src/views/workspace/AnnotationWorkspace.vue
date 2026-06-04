<script setup lang="ts">
/**
 * 标注工作台页面
 * 通过 AnnotationWorkspaceLayout 提供布局
 * 负责加载 page 元数据、图片访问入口、latest revision、label registry、QC 列表和 capabilities
 */
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const route = useRoute()
const pageId = route.params.page_id as string

// TODO: 加载 page 元数据、revision、capabilities
const loading = ref(true)

onMounted(async () => {
  try {
    // 1. 校验 page_id 参数格式
    if (!pageId) return

    // 2. 加载 page 元数据，获取 project_id、图片尺寸和基础状态
    // 3. 加载当前 project capabilities
    // 4. 加载 label registry 和 relation registry
    // 5. 加载 latest revision
    // 6. 加载 QC 问题、任务上下文和相邻页面导航数据
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="h-full flex flex-col">
    <div v-if="loading" class="flex-1 flex items-center justify-center text-muted">
      {{ t('common.loading') }}
    </div>
    <div v-else class="flex-1">
      <!-- TODO: 实现标注画布 -->
    </div>
  </div>
</template>
