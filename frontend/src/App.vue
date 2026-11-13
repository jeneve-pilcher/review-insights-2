<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import CookieBanner from './components/CookieBanner.vue'

// Password-reset emails can land on the site root (e.g. /#access_token=...&type=recovery) when the
// /login?reset=1 address is not on Supabase's allowed redirect list. Send those visitors to the
// "choose a new password" screen, keeping the hash so the sign-in tokens are still read.
const router = useRouter()
onMounted(async () => {
  await router.isReady()
  const hash = window.location.hash || ''
  if (!hash.includes('type=recovery') && !hash.includes('error=')) return
  const params = new URLSearchParams(hash.replace(/^#/, ''))
  if (params.get('type') === 'recovery') {
    router.replace({ path: '/login', query: { reset: '1' }, hash })
  } else if (params.get('error') || params.get('error_code')) {
    router.replace({ path: '/login', query: { expired: '1' } })
  }
})
</script>

<template>
  <router-view />
  <CookieBanner />
</template>
