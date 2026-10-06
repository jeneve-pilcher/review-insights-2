<script setup>
import { ref } from 'vue'
import { setYelpUrl } from '../api'

const emit = defineEmits(['saved'])

const link = ref('')
const loading = ref(false)
const error = ref('')

async function save() {
  if (!link.value.trim()) return
  loading.value = true
  error.value = ''
  try {
    const { yelp_url } = await setYelpUrl(link.value.trim())
    emit('saved', yelp_url)
  } catch (err) {
    error.value = err?.response?.data?.detail || 'Could not save your Yelp link.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="chart-section">
    <h3>⭐ Add your Yelp page</h3>
    <p class="chart-desc">
      Optional: add your Yelp business page to analyze Yelp reviews alongside Google, with a
      side-by-side comparison. Paste the link from your browser, for example
      <code>https://www.yelp.com/biz/your-business-name</code>. It's saved once for this
      account, like your business location.
    </p>
    <div class="analysis-form">
      <label class="field" style="flex: 1; min-width: 260px">
        <span>Yelp business page link</span>
        <input
          v-model="link"
          type="text"
          placeholder="https://www.yelp.com/biz/your-business-name"
          @keyup.enter="save"
        />
      </label>
      <button class="run-btn" :disabled="loading" @click="save">
        {{ loading ? 'Saving…' : 'Save Yelp page' }}
      </button>
    </div>
    <p v-if="error" class="status error">{{ error }}</p>
  </section>
</template>
