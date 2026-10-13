<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { createCheckoutSession } from '../api'
import { supabase } from '../supabase'
import { isExistingAccount } from '../utils/accountExists'
import { TERMS_VERSION } from '../legal/terms'
import { PRIVACY_DATE } from '../legal/privacy'

const router = useRouter()
const route = useRoute()

const email = ref('')
const password = ref('')
const companyName = ref('')
const error = ref('')
const loading = ref(false)
const needsEmailConfirmation = ref(false)
const existingAccount = ref(false)
const agreed = ref(false)

async function handleSubmit() {
  if (!agreed.value) {
    error.value = 'Please agree to the Terms of Service and Privacy Policy to create an account.'
    return
  }
  loading.value = true
  error.value = ''

  const { data, error: authError } = await supabase.auth.signUp({
    email: email.value,
    password: password.value,
    // The agreement is also kept on the account itself (which version, and when), alongside the check made at first login.
    options: { data: { company_name: companyName.value, agreed_terms_version: TERMS_VERSION, agreed_privacy_date: PRIVACY_DATE, agreed_at: new Date().toISOString() } },
  })

  existingAccount.value = false
  if (isExistingAccount(data, authError)) {
    existingAccount.value = true
    loading.value = false
    return
  }

  if (authError) {
    error.value = authError.message
    loading.value = false
    return
  }

  // If email confirmation is required, Supabase returns a user but no session yet.
  if (!data.session) {
    needsEmailConfirmation.value = true
    loading.value = false
    return
  }

  if (route.query.plan === 'pro') {
    try {
      const { checkout_url } = await createCheckoutSession()
      window.location.href = checkout_url
      return
    } catch (err) {
      error.value = 'Account created, but starting checkout failed. You can upgrade later from the dashboard.'
    }
  }

  loading.value = false
  router.push('/dashboard')
}
</script>

<template>
  <div class="auth-screen">
    <div class="auth-card">
      <h2>Create an account</h2>

      <template v-if="!needsEmailConfirmation">
        <form @submit.prevent="handleSubmit">
          <label class="field">
            <span>Company name (optional)</span>
            <input v-model="companyName" type="text" autocomplete="organization" />
          </label>
          <label class="field">
            <span>Email</span>
            <input v-model="email" type="email" autocomplete="email" required />
          </label>
          <label class="field">
            <span>Password (min 8 characters)</span>
            <input v-model="password" type="password" autocomplete="new-password" minlength="8" required />
          </label>

          <label class="source-check" style="display: block; margin: 12px 0">
            <input v-model="agreed" type="checkbox" required />
            I have read and agree to the
            <a href="/#terms" target="_blank" rel="noopener">Terms of Service</a> and the
            <a href="/#privacy" target="_blank" rel="noopener">Privacy Policy</a>.
          </label>

          <p v-if="existingAccount" class="status error">
            An account with this email already exists.
            <router-link :to="{ path: '/login', query: { email } }">Log in instead</router-link>
          </p>
          <p v-if="error" class="status error">{{ error }}</p>

          <button class="run-btn" type="submit" :disabled="loading || !agreed">
            {{ loading ? 'Creating account…' : (route.query.plan === 'pro' ? 'Sign up & continue to checkout' : 'Sign up') }}
          </button>
        </form>
        <p class="switch-link">
          Already have an account? <router-link to="/login">Log in</router-link>
        </p>
      </template>

      <p v-else class="status">
        Check your email to confirm your account, then log in.
      </p>
    </div>
  </div>
</template>
