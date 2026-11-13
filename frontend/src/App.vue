<script>
// Read at load time, before the router or the sign-in library tidy the address up.
const arrivedByRecovery = typeof window !== 'undefined' && /[#&?]type=recovery/.test(window.location.hash || '')
const arrivedExpired = typeof window !== 'undefined' && /[#&?]error(_code)?=/.test(window.location.hash || '')
</script>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from './supabase'
import CookieBanner from './components/CookieBanner.vue'

// A password-reset email can land on the site root (/#access_token=...&type=recovery) when /login?reset=1
// is not on Supabase's allowed redirect list. Whatever page that is (even one that bounces to /login or
// shows "not found"), send the person to the "Choose a new password" screen.
const router = useRouter()
let sub = null

function goReset() {
  if (router.currentRoute.value.query.reset === undefined) router.replace({ path: '/login', query: { reset: '1' } })
}

onMounted(async () => {
  const { data } = supabase.auth.onAuthStateChange((event) => {
    if (event === 'PASSWORD_RECOVERY') goReset()
  })
  sub = data?.subscription
  await router.isReady()
  if (arrivedByRecovery) goReset()
  else if (arrivedExpired) router.replace({ path: '/login', query: { expired: '1' } })
})

onUnmounted(() => sub?.unsubscribe())
</script>

<template>
  <router-view />
  <CookieBanner />
</template>
