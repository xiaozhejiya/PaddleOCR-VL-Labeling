<script setup lang="ts">
/**
 * 项目列表页
 */
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { projectsApi, type Project } from '@/api/projects'
import { FolderKanban, Plus, Trash2 } from 'lucide-vue-next'

const { t } = useI18n()
const router = useRouter()

const projects = ref<Project[]>([])
const loading = ref(true)
const feedback = ref<{ type: 'success' | 'error'; text: string } | null>(null)

// ── 创建项目弹窗 ──
const showModal = ref(false)
const creating = ref(false)
const formName = ref('')
const formDesc = ref('')

async function loadProjects() {
  loading.value = true
  try {
    const response = await projectsApi.list()
    projects.value = response.items
  } catch {
    // 后端不可用或无数据时视为空列表，引导用户创建
    projects.value = []
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  if (!formName.value.trim()) return
  creating.value = true
  try {
    await projectsApi.create({
      name: formName.value.trim(),
      description: formDesc.value.trim() || undefined,
    })
    showModal.value = false
    formName.value = ''
    formDesc.value = ''
    feedback.value = { type: 'success', text: t('common.success') }
    await loadProjects()
  } catch {
    feedback.value = { type: 'error', text: t('common.error') }
  } finally {
    creating.value = false
  }
}

function handleDelete(project: Project) {
  if (!window.confirm(t('project.deleteConfirm', { name: project.name }))) return
  projectsApi.delete(project.id)
    .then(async () => {
      feedback.value = { type: 'success', text: t('common.success') }
      await loadProjects()
    })
    .catch(() => {
      feedback.value = { type: 'error', text: t('common.error') }
    })
}

onMounted(() => { loadProjects() })

function goToProject(projectId: string) {
  router.push({ name: 'projects.detail', params: { project_id: projectId } })
}

function closeModal() {
  showModal.value = false
}
</script>

<template>
  <div class="flex-1 overflow-auto">
    <div class="max-w-5xl mx-auto p-6">
      <!-- 页面头部 -->
      <div class="flex items-center justify-between mb-6">
        <h1 class="text-title text-text">{{ t('routes.projects.index') }}</h1>
        <button
          type="button"
          class="inline-flex items-center gap-2 rounded-md bg-primary px-3 py-2 text-caption font-medium text-white transition-colors hover:bg-primary-hover"
          @click="showModal = true"
        >
          <Plus class="w-4 h-4" />
          {{ t('project.create') }}
        </button>
      </div>

      <div
        v-if="feedback"
        class="mb-4 rounded-md border px-3 py-2 text-caption"
        :class="feedback.type === 'success'
          ? 'border-success/30 bg-success-bg text-success'
          : 'border-danger/30 bg-danger/5 text-danger'"
      >
        {{ feedback.text }}
      </div>

      <!-- Loading -->
      <div v-if="loading" class="flex justify-center py-16">
        <div class="h-8 w-8 rounded-full border-2 border-primary border-t-transparent animate-spin"></div>
      </div>

      <!-- Empty -->
      <div
        v-else-if="projects.length === 0"
        class="rounded-lg border border-dashed border-border bg-surface px-6 py-16 text-center"
      >
        <p class="mb-4 text-body text-text-muted">{{ t('common.noData') }}</p>
        <button
          type="button"
          class="inline-flex items-center gap-2 rounded-md bg-primary px-3 py-2 text-caption font-medium text-white transition-colors hover:bg-primary-hover"
          @click="showModal = true"
        >
          <Plus class="w-4 h-4" />
            {{ t('project.create') }}
        </button>
      </div>

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
          <div class="flex items-center gap-2 shrink-0">
            <span class="text-micro text-text-muted">{{ project.schema_version }}</span>
            <button
              type="button"
              class="inline-flex items-center justify-center rounded-md p-2 text-danger transition-colors hover:bg-danger-bg"
              @click.stop="handleDelete(project)"
            >
              <Trash2 class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建项目弹窗 -->
    <div
      v-if="showModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
      @click="closeModal"
    >
      <div class="w-full max-w-md rounded-lg border border-border bg-surface p-5 shadow-modal" @click.stop>
        <h2 class="mb-4 text-subheading text-text">{{ t('project.create') }}</h2>
        <label class="mb-4 block">
          <span class="mb-1 block text-caption text-text-secondary">{{ t('project.name') }}</span>
          <input
            v-model="formName"
            :placeholder="t('project.name')"
            class="h-9 w-full rounded-md border border-border bg-surface px-3 text-body text-text outline-none transition-colors placeholder:text-text-muted focus:border-primary"
          />
        </label>
        <label class="mb-5 block">
          <span class="mb-1 block text-caption text-text-secondary">{{ t('project.description') }}</span>
          <textarea
            v-model="formDesc"
            :placeholder="t('project.description')"
            rows="3"
            class="w-full rounded-md border border-border bg-surface px-3 py-2 text-body text-text outline-none transition-colors placeholder:text-text-muted focus:border-primary"
          ></textarea>
        </label>
        <div class="flex justify-end gap-2">
          <button
            type="button"
            class="inline-flex items-center justify-center rounded-md border border-border bg-surface px-3 py-2 text-caption font-medium text-text transition-colors hover:bg-surface-muted"
            @click="closeModal"
          >
            {{ t('common.cancel') }}
          </button>
          <button
            type="button"
            :disabled="creating || !formName.trim()"
            class="inline-flex items-center justify-center rounded-md bg-primary px-3 py-2 text-caption font-medium text-white transition-colors hover:bg-primary-hover disabled:cursor-not-allowed disabled:opacity-50"
            @click="handleCreate"
          >
            {{ t('common.confirm') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
