<script setup>
import { ref } from 'vue'
import { submitEnterpriseContact } from '../api'

const name = ref('')
const email = ref('')
const companyName = ref('')
const message = ref('')
const submitted = ref(false)
const error = ref('')
const loading = ref(false)

async function handleSubmit() {
  loading.value = true
  error.value = ''
  try {
    await submitEnterpriseContact({
      name: name.value,
      email: email.value,
      company_name: companyName.value,
      message: message.value,
    })
    submitted.value = true
  } catch (err) {
    error.value = 'Something went wrong sending your message. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-screen">
    <div class="auth-card" style="width: 420px">
      <h2>Enterprise</h2>

      <template v-if="!submitted">
        <p>Tell us about your use case and we'll follow up with custom pricing and scope.</p>
        <form @submit.prevent="handleSubmit">
          <label class="field">
            <span>Name</span>
            <input v-model="name" type="text" required />
          </label>
          <label class="field">
            <span>Work email</span>
            <input v-model="email" type="email" required />
          </label>
          <label class="field">
            <span>Company</span>
            <input v-model="companyName" type="text" />
          </label>
          <label class="field">
            <span>What are you looking to do?</span>
            <textarea v-model="message" rows="4" required></textarea>
          </label>

          <p v-if="error" class="status error">{{ error }}</p>

          <button class="run-btn" type="submit" :disabled="loading">
            {{ loading ? 'Sending…' : 'Send' }}
          </button>
        </form>
      </template>

      <p v-else class="status">Thanks — we'll be in touch shortly.</p>
    </div>
  </div>
</template>
