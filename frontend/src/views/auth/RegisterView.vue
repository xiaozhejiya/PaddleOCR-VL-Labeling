<script setup lang="ts">
/**
 * 注册页
 * MVP 默认不开放注册
 */
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { NInput, NFormItem, NButton, NAlert } from 'naive-ui'

const { t } = useI18n()

const username = ref('')
const email = ref('')
const password = ref('')
const loading = ref(false)
const registrationEnabled = false

async function handleRegister() {
  if (!registrationEnabled) return
}
</script>

<template>
  <div class="bg-surface rounded-lg shadow-modal p-8">
    <h1 class="text-title text-center mb-6">{{ t('auth.register') }}</h1>

    <form @submit.prevent="handleRegister" class="space-y-4">
      <NAlert v-if="!registrationEnabled" type="warning" :bordered="false" class="mb-4">
        <p class="font-medium">{{ t('auth.registerUnavailableTitle') }}</p>
        <p class="mt-1">{{ t('auth.registerUnavailableDescription') }}</p>
      </NAlert>

      <NFormItem :label="t('auth.username')">
        <NInput
          v-model:value="username"
          :placeholder="t('auth.username')"
          :disabled="loading || !registrationEnabled"
        />
      </NFormItem>

      <NFormItem :label="t('auth.email')">
        <NInput
          v-model:value="email"
          :placeholder="t('auth.email')"
          :disabled="loading || !registrationEnabled"
        />
      </NFormItem>

      <NFormItem :label="t('auth.password')">
        <NInput
          v-model:value="password"
          type="password"
          show-password-on="click"
          :placeholder="t('auth.password')"
          :disabled="loading || !registrationEnabled"
        />
      </NFormItem>

      <NButton
        type="primary"
        block
        :loading="loading"
        :disabled="!registrationEnabled || !username || !email || !password"
        attr-type="submit"
      >
        {{ t('auth.register') }}
      </NButton>
    </form>

    <p class="mt-4 text-center text-sm text-text-muted">
      {{ t('auth.hasAccount') }}
      <router-link :to="{ name: 'auth.login' }" class="text-link hover:underline">
        {{ t('auth.login') }}
      </router-link>
    </p>
  </div>
</template>
