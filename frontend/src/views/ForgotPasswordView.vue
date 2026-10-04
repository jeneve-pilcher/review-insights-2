<script setup>
import { ref } from 'vue'
import { supabase } from '../supabase'

const email = ref('')
const error = ref('')
const loading = ref(false)
const sent = ref(false)

async function handleSubmit() {
  loading.value = true
  error.value = ''

  const { error: resetError } = await supabase.auth.resetPasswordForEmail(email.value, {
    redirectTo: `${window.location.origin}/reset-password`,
  })

  loading.value = false

  if (resetError) {
    error.value = resetError.message
    return
  }

  sent.value = true
}
</script>

<template>
  <div class="auth-screen">
    <div class="auth-card">
      <h2>Reset your password</h2>

      <template v-if="!sent">
        <p class="status">Enter your account email and we'll send you a reset link.</p>
        <form @submit.prevent="handleSubmit">
          <label class="field">
            <span>Email</span>
            <input v-model="email" type="email" autocomplete="email" required />
          </label>

          <p v-if="error" class="status error">{{ error }}</p>

          <button class="run-btn" type="submit" :disabled="loading">
            {{ loading ? 'Sending…' : 'Send reset link' }}
          </button>
        </form>
      </template>

      <p v-else class="status">
        Check your email for a link to reset your password. It may take a minute to arrive.
      </p>

      <p class="switch-link">
        <router-link to="/login">Back to login</router-link>
      </p>
    </div>
  </div>
</template>
