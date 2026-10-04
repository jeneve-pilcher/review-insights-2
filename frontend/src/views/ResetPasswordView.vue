<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../supabase'

const router = useRouter()

const newPassword = ref('')
const error = ref('')
const loading = ref(false)
const success = ref(false)
const sessionReady = ref(false)

onMounted(async () => {
  // Supabase puts the user into a temporary "recovery" session when they
  // land here from the emailed link - confirm that session exists before
  // letting them submit a new password.
  const { data } = await supabase.auth.getSession()
  sessionReady.value = !!data?.session

  if (!sessionReady.value) {
    error.value = 'This reset link is invalid or has expired. Request a new one.'
  }
})

async function handleSubmit() {
  loading.value = true
  error.value = ''

  const { error: updateError } = await supabase.auth.updateUser({ password: newPassword.value })

  loading.value = false

  if (updateError) {
    error.value = updateError.message
    return
  }

  success.value = true
  setTimeout(() => router.push('/dashboard'), 1500)
}
</script>

<template>
  <div class="auth-screen">
    <div class="auth-card">
      <h2>Set a new password</h2>

      <template v-if="sessionReady && !success">
        <form @submit.prevent="handleSubmit">
          <label class="field">
            <span>New password (min 8 characters)</span>
            <input v-model="newPassword" type="password" autocomplete="new-password" minlength="8" required />
          </label>

          <p v-if="error" class="status error">{{ error }}</p>

          <button class="run-btn" type="submit" :disabled="loading">
            {{ loading ? 'Updating…' : 'Update password' }}
          </button>
        </form>
      </template>

      <p v-else-if="success" class="status">Password updated — redirecting…</p>
      <template v-else>
        <p class="status error">{{ error }}</p>
        <p class="switch-link">
          <router-link to="/forgot-password">Request a new link</router-link>
        </p>
      </template>
    </div>
  </div>
</template>
