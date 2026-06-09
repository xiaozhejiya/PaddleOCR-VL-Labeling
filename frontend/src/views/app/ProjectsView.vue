<script setup lang="ts">
/**
 * 项目列表页
 */
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { projectsApi, type Project } from '@/api/projects'
import { ApiClientError } from '@/api/client'
import { NButton, NEmpty, NSpin } from 'naive-ui'
import { FolderKanban, Plus } from 'lucide-vue-next'

const { t } = useI18n()
const router = useRouter()

const projects = ref<Project[]>([])
const loading = ref(true)
const error = ref('')

async function loadProjects() {
  loading.value = true
  error.value = ''
  try {
    const response = await projectsApi.list()
    projects.value = response.items
  } catch (e) {
    if (e instanceof ApiClientError) {
      if (e.status === 404 || e.status === 501) {
        projects.value = []
      } else if (e.status === 0) {
        error.value = t('errors.network')
      } else {
        error.value = t('errors.server')
      }
    } else {
      error.value = t('errors.unknown')
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => { loadProjects() })

function goToProject(projectId: string) {
  router.push({ name: 'projects.detail', params: { project_id: projectId } })
}
</script>

<template>
  <div class="flex-1 overflow-auto">
    <div class="max-w-5xl mx-auto p-6">
      <!-- 页面头部 -->
      <div class="flex items-center justify-between mb-6">
        <h1 class="text-title text-text">{{ t('routes.projects.index') }}</h1>
        <NButton type="primary">
          <template #icon><Plus /></template>
          {{ t('project.create') }}
        </NButton>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="flex justify-center py-16">
        <NSpin size="large" />
      </div>

      <!-- Error -->
      <div v-else-if="error" class="text-center py-16">
        <p class="text-body text-danger mb-4">{{ error }}</p>
        <NButton @click="loadProjects">{{ t('common.retry') }}</NButton>
      </div>

      <!-- Empty -->
      <NEmpty v-else-if="projects.length === 0" :description="t('common.noData')" class="py-16">
        <template #extra>
          <NButton type="primary">
            <template #icon><Plus /></template>
            {{ t('project.create') }}
          </NButton>
        </template>
      </NEmpty>

      <!-- 项目列表 -->
      <div v-else class="space-y-2">
        <div
          v-for="project in projects"
          :key="project.id"
          class="group flex items-center gap-4 p-4 bg-surface rounded-lg border border-border hover:border-primary/40 cursor-pointer transition-all duration-fast"
          @click="goToProject(project.id)"
        >
          <div class="w-10 h-10 rounded-lg bg-primary/8 flex items-center justify-center shrink-0">
            <FolderKanban class="w-5 h-5 text-primary" />
          </div>
          <div class="flex-1 min-w-0">
            <h3 class="text-body-medium text-text group-hover:text-primary transition-colors truncate">
              {{ project.name }}
            </h3>
            <p v-if="project.description" class="text-caption text-text-secondary mt-0.5 truncate">
              {{ project.description }}
            </p>
          </div>
          <div class="text-caption text-text-muted shrink-0">
            <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-sm bg-success-bg text-success text-micro font-medium">
              <span class="w-1.5 h-1.5 rounded-full bg-success"></span>
              {{ t('project.statusInProject') }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
