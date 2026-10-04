<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { supabase } from '../supabase'

const router = useRouter()
const route = useRoute()

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

const ssoEmail = ref('')
const ssoError = ref('')
const ssoLoading = ref(false)
const showSso = ref(false)

async function handleSubmit() {
  loading.value = true
  error.value = ''
  const { error: authError } = await supabase.auth.signInWithPassword({
    email: email.value,
    password: password.value,
  })
  loading.value = false

  if (authError) {
    error.value = authError.message
    return
  }

  router.push(route.query.redirect || '/dashboard')
}

async function handleSso() {
  const domain = ssoEmail.value.split('@')[1]
  if (!domain) {
    ssoError.value = 'Enter your full work email address.'
    return
  }

  ssoLoading.value = true
  ssoError.value = ''

  const { data, error: ssoErr } = await supabase.auth.signInWithSSO({ domain })

  if (ssoErr) {
    ssoLoading.value = false
    ssoError.value = ssoErr.message
    return
  }

  if (data?.url) {
    window.location.href = data.url
  } else {
    ssoLoading.value = false
    ssoError.value = `No SSO connection is set up for ${domain}. Contact your admin or use email/password instead.`
  }
}
</script>

<template>
  <div class="auth-screen">
    <div class="auth-card">
      <h2>Log in</h2>
      <form @submit.prevent="handleSubmit">
        <label class="field">
          <span>Email</span>
          <input v-model="email" type="email" autocomplete="email" required />
        </label>
        <label class="field">
          <span>Password</span>
          <input v-model="password" type="password" autocomplete="current-password" required />
        </label>
        <p class="switch-link" style="text-align: left; margin: -6px 0 14px">
          <router-link to="/forgot-password">Forgot password?</router-link>
        </p>

        <p v-if="error" class="status error">{{ error }}</p>

        <button class="run-btn" type="submit" :disabled="loading">
          {{ loading ? 'Logging in…' : 'Log in' }}
        </button>
      </form>

      <div class="sso-divider">or</div>

      <template v-if="!showSso">
        <button class="run-btn sso-toggle-btn" @click="showSso = true">
          🏢 Continue with company SSO
        </button>
      </template>
      <template v-else>
        <label class="field">
          <span>Work email</span>
          <input v-model="ssoEmail" type="email" placeholder="you@yourcompany.com" />
        </label>
        <p v-if="ssoError" class="status error">{{ ssoError }}</p>
        <button class="run-btn sso-toggle-btn" @click="handleSso" :disabled="ssoLoading">
          {{ ssoLoading ? 'Redirecting…' : 'Continue' }}
        </button>
      </template>

      <p class="switch-link">
        Don't have an account? <router-link to="/signup">Sign up</router-link>
      </p>
    </div>
  </div>
</template>
