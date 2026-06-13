<script setup lang="ts">
/**
 * 注册页
 * MVP 默认不开放注册
 */
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const username = ref('')
const email = ref('')
const password = ref('')
const loading = ref(false)
const registrationEnabled = import.meta.env.VITE_ENABLE_REGISTRATION === 'true'

async function handleRegister() {
  if (!registrationEnabled) return
}
</script>

<template>
  <div class="bg-surface rounded-lg shadow-modal p-8">
    <h1 class="text-title text-center mb-6">{{ t('auth.register') }}</h1>

    <form @submit.prevent="handleRegister" class="space-y-4">
      <div v-if="!registrationEnabled" class="rounded-md border border-warning/30 bg-warning-bg px-3 py-2 text-caption text-warning">
        <p class="font-medium">{{ t('auth.registerUnavailableTitle') }}</p>
        <p class="mt-1">{{ t('auth.registerUnavailableDescription') }}</p>
      </div>

      <label class="block">
        <span class="mb-1 block text-caption text-text-secondary">{{ t('auth.username') }}</span>
        <input
          v-model="username"
          :placeholder="t('auth.username')"
          :disabled="loading || !registrationEnabled"
          class="h-9 w-full rounded-md border border-border bg-surface px-3 text-body text-text outline-none transition-colors placeholder:text-text-muted focus:border-primary disabled:cursor-not-allowed disabled:bg-surface-muted"
        />
      </label>

      <label class="block">
        <span class="mb-1 block text-caption text-text-secondary">{{ t('auth.email') }}</span>
        <input
          v-model="email"
          :placeholder="t('auth.email')"
          :disabled="loading || !registrationEnabled"
          class="h-9 w-full rounded-md border border-border bg-surface px-3 text-body text-text outline-none transition-colors placeholder:text-text-muted focus:border-primary disabled:cursor-not-allowed disabled:bg-surface-muted"
        />
      </label>

      <label class="block">
        <span class="mb-1 block text-caption text-text-secondary">{{ t('auth.password') }}</span>
        <input
          v-model="password"
          type="password"
          :placeholder="t('auth.password')"
          :disabled="loading || !registrationEnabled"
          class="h-9 w-full rounded-md border border-border bg-surface px-3 text-body text-text outline-none transition-colors placeholder:text-text-muted focus:border-primary disabled:cursor-not-allowed disabled:bg-surface-muted"
        />
      </label>

      <button
        type="submit"
        :disabled="loading || !registrationEnabled || !username || !email || !password"
        class="inline-flex w-full items-center justify-center rounded-md bg-primary px-4 py-2 text-caption font-medium text-white transition-colors hover:bg-primary-hover disabled:cursor-not-allowed disabled:opacity-50"
      >
        {{ t('auth.register') }}
      </button>
    </form>

    <p class="mt-4 text-center text-sm text-text-muted">
      {{ t('auth.hasAccount') }}
      <router-link :to="{ name: 'auth.login' }" class="text-link hover:underline">
        {{ t('auth.login') }}
      </router-link>
    </p>
  </div>
</template>
