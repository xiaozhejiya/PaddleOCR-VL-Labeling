<script setup lang="ts">
/**
 * 登录页
 */
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuth } from '@/composables/useAuth'
import { ApiClientError } from '@/api/client'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const { login } = useAuth()

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')
const registrationEnabled = import.meta.env.VITE_ENABLE_REGISTRATION === 'true'

function isValidRedirect(redirect: string): boolean {
  if (!redirect.startsWith('/')) return false
  if (redirect.startsWith('//')) return false
  if (redirect.includes(':')) return false
  if (redirect === '/auth/login') return false
  return true
}

async function handleLogin() {
  if (!username.value || !password.value) return

  loading.value = true
  error.value = ''

  try {
    await login(username.value, password.value)

    const redirect = route.query.redirect as string
    if (redirect && isValidRedirect(redirect)) {
      router.replace(redirect)
    } else {
      router.replace({ name: 'projects.index' })
    }
  } catch (e) {
    if (e instanceof ApiClientError) {
      if (e.status === 401) {
        error.value = t('errors.loginFailed')
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
</script>

<template>
  <div class="bg-surface rounded-lg shadow-modal p-8">
    <h1 class="text-title text-center mb-6">{{ t('auth.login') }}</h1>

    <form @submit.prevent="handleLogin" class="space-y-4">
      <div v-if="error" class="rounded-md border border-danger/30 bg-danger/5 px-3 py-2 text-caption text-danger">
        {{ error }}
      </div>

      <label class="block">
        <span class="mb-1 block text-caption text-text-secondary">{{ t('auth.username') }}</span>
        <input
          v-model="username"
          :placeholder="t('auth.username')"
          :disabled="loading"
          class="h-9 w-full rounded-md border border-border bg-surface px-3 text-body text-text outline-none transition-colors placeholder:text-text-muted focus:border-primary disabled:cursor-not-allowed disabled:bg-surface-muted"
        />
      </label>

      <label class="block">
        <span class="mb-1 block text-caption text-text-secondary">{{ t('auth.password') }}</span>
        <input
          v-model="password"
          type="password"
          :placeholder="t('auth.password')"
          :disabled="loading"
          class="h-9 w-full rounded-md border border-border bg-surface px-3 text-body text-text outline-none transition-colors placeholder:text-text-muted focus:border-primary disabled:cursor-not-allowed disabled:bg-surface-muted"
        />
      </label>

      <button
        type="submit"
        :disabled="loading || !username || !password"
        class="inline-flex w-full items-center justify-center rounded-md bg-primary px-4 py-2 text-caption font-medium text-white transition-colors hover:bg-primary-hover disabled:cursor-not-allowed disabled:opacity-50"
      >
        {{ t('auth.login') }}
      </button>
    </form>

    <p v-if="registrationEnabled" class="mt-4 text-center text-sm text-text-muted">
      {{ t('auth.noAccount') }}
      <router-link :to="{ name: 'auth.register' }" class="text-link hover:underline">
        {{ t('auth.register') }}
      </router-link>
    </p>
  </div>
</template>
