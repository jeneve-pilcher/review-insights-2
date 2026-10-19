<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchBranding } from '../api'
import { supabase } from '../supabase'
import { applyBranding, brandTitle, emailDomain, forgetBrand, recallBrand, rememberBrand, safeLogo } from '../utils/theme'

const router = useRouter()
const route = useRoute()

// Arriving from sign-up with "you already have an account" fills the email in (/login?email=...).
const email = ref(typeof route.query.email === 'string' ? route.query.email.slice(0, 254) : '')
const password = ref('')
const error = ref('')
const loading = ref(false)

// Someone invited by their company arrives from the emailed link already signed in and chooses a password here.
const settingPassword = ref(false)
const newPassword = ref('')
const newPassword2 = ref('')
const pwError = ref('')
const pwLoading = ref(false)

async function checkInvite() {
  if (route.query.invited === undefined) return
  const { data } = await supabase.auth.getSession()
  if (data?.session) settingPassword.value = true
}

async function savePassword() {
  pwError.value = ''
  if (newPassword.value.length < 8) { pwError.value = 'Use at least 8 characters.'; return }
  if (newPassword.value !== newPassword2.value) { pwError.value = 'The two passwords do not match.'; return }
  pwLoading.value = true
  const { error: upErr } = await supabase.auth.updateUser({ password: newPassword.value })
  pwLoading.value = false
  if (upErr) { pwError.value = upErr.message; return }
  router.push('/dashboard')
}

const ssoEmail = ref('')
const ssoError = ref('')
const ssoLoading = ref(false)
const showSso = ref(false)

// A company with white-label branding gets its own look here, found from the work email's domain BEFORE sign-in.
const branding = ref(null)
const brandLogo = computed(() => safeLogo(branding.value))
const brandName = computed(() => (branding.value ? brandTitle(branding.value) : ''))

onMounted(() => {
  checkInvite()
  supabase.auth.onAuthStateChange((event) => {
    if (route.query.invited !== undefined && (event === 'SIGNED_IN' || event === 'PASSWORD_RECOVERY')) settingPassword.value = true
  })
  const saved = recallBrand() // a return visit starts branded, without a flash of the default look
  if (saved) {
    branding.value = saved
    applyBranding(saved)
    document.title = brandTitle(saved)
  }
})

let timer = null
let lastDomain = ''

function lookup(value) {
  const domain = emailDomain(value)
  if (!domain || domain === lastDomain) return
  lastDomain = domain
  clearTimeout(timer)
  timer = setTimeout(async () => {
    try {
      const { branding: found } = await fetchBranding(value)
      branding.value = found
      applyBranding(found)
      document.title = brandTitle(found)
      if (found) rememberBrand(found)
      else forgetBrand()
    } catch {
      /* the login page works the same without branding */
    }
  }, 350)
}

watch(email, lookup)
watch(ssoEmail, lookup)

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

async function startSso(domain) {
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

async function handleSso() {
  const domain = ssoEmail.value.split('@')[1]
  if (!domain) {
    ssoError.value = 'Enter your full work email address.'
    return
  }
  await startSso(domain)
}

// The company's own SSO button, shown once its branding has been recognised.
function handleBrandSso() {
  return startSso(branding.value.sso_domain)
}
</script>

<template>
  <div v-if="settingPassword" class="auth-screen">
    <div class="auth-card">
      <h2>Choose a password</h2>
      <p>Welcome. Choose a password for your account. You'll use it with your email to log in.</p>
      <form @submit.prevent="savePassword">
        <label class="field">
          <span>Password</span>
          <input v-model="newPassword" type="password" autocomplete="new-password" minlength="8" required />
        </label>
        <label class="field">
          <span>Repeat password</span>
          <input v-model="newPassword2" type="password" autocomplete="new-password" minlength="8" required />
        </label>
        <p v-if="pwError" class="status error">{{ pwError }}</p>
        <button class="run-btn" type="submit" :disabled="pwLoading">{{ pwLoading ? 'Saving…' : 'Save and continue' }}</button>
      </form>
    </div>
  </div>
  <div v-else class="auth-screen">
    <div class="auth-card">
      <div v-if="branding" class="brand-header" style="text-align: center; margin-bottom: 14px">
        <img v-if="brandLogo" :src="brandLogo" :alt="brandName" class="brand-logo" />
        <h3 v-else style="margin: 0">{{ brandName }}</h3>
      </div>

      <h2>Log in</h2>

      <template v-if="branding && branding.sso">
        <button class="run-btn" type="button" :disabled="ssoLoading" @click="handleBrandSso">
          {{ ssoLoading ? 'Redirecting…' : `Continue with ${brandName} SSO` }}
        </button>
        <p v-if="ssoError" class="status error">{{ ssoError }}</p>
        <div class="sso-divider">or use email and password</div>
      </template>

      <form @submit.prevent="handleSubmit">
        <label class="field">
          <span>Email</span>
          <input v-model="email" type="email" autocomplete="email" required />
        </label>
        <label class="field">
          <span>Password</span>
          <input v-model="password" type="password" autocomplete="current-password" required />
        </label>

        <p v-if="error" class="status error">{{ error }}</p>

        <button class="run-btn" type="submit" :disabled="loading">
          {{ loading ? 'Logging in…' : 'Log in' }}
        </button>
      </form>

      <template v-if="!(branding && branding.sso)">
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
      </template>

      <p class="switch-link">
        Don't have an account? <router-link to="/signup">Sign up</router-link>
      </p>
    </div>
  </div>
</template>
