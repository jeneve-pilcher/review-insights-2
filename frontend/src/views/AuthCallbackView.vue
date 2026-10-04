<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../supabase'

const router = useRouter()
const error = ref('')

onMounted(async () => {
  // supabase-js automatically parses the session out of the URL fragment
  // that the IdP redirect includes. We just need to wait for it, then move on.
  const { data, error: sessionError } = await supabase.auth.getSession()

  if (sessionError || !data?.session) {
    error.value = 'Could not complete SSO sign-in. Please try again.'
    return
  }

  router.push('/dashboard')
})
</script>

<template>
  <div class="auth-screen">
    <div class="auth-card">
      <p v-if="!error" class="status">Signing you in…</p>
      <template v-else>
        <p class="status error">{{ error }}</p>
        <router-link to="/login" class="switch-link">Back to login</router-link>
      </template>
    </div>
  </div>
</template>
