<script setup>
import { ref } from 'vue'
import { setBusinessLocation } from '../api'

const emit = defineEmits(['set'])

const location = ref('')
const loading = ref(false)
const error = ref('')

async function handleSubmit() {
  if (!location.value.trim()) return
  loading.value = true
  error.value = ''
  try {
    await setBusinessLocation(location.value.trim())
    emit('set', location.value.trim())
  } catch (err) {
    error.value = err?.response?.data?.detail || 'Could not save your business location.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="chart-section">
    <h3>📍 Set Your Business</h3>
    <p class="chart-desc">
      One-time setup: enter your business name/location, or paste its Google Maps URL for
      precision if the name is ambiguous. This is permanent for your account - all analysis
      will run against this business only. Contact support if you need it changed later.
    </p>

    <div class="analysis-form">
      <label class="field" style="flex: 1; min-width: 260px">
        <span>Business Location or Google Maps URL</span>
        <input
          v-model="location"
          type="text"
          placeholder="e.g. Joe's Pizza, Brooklyn NY - or paste a Google Maps link"
          @keyup.enter="handleSubmit"
        />
      </label>
      <button class="run-btn" @click="handleSubmit" :disabled="loading">
        {{ loading ? 'Saving…' : 'Save (permanent)' }}
      </button>
    </div>

    <p v-if="error" class="status error">{{ error }}</p>
  </section>
</template>
