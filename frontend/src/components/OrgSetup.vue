<script setup>
import { computed, ref } from 'vue'
import { orgApi } from '../api'

const props = defineProps({
  tier: { type: String, default: 'free' },
})
const emit = defineEmits(['created'])

const name = ref('')
const loading = ref(false)
const error = ref('')

const canCreate = computed(() => ['pro', 'enterprise'].includes(props.tier))

async function create() {
  if (!name.value.trim()) return
  loading.value = true
  error.value = ''
  try {
    await orgApi.create(name.value.trim())
    emit('created')
  } catch (err) {
    error.value = err?.response?.data?.detail || 'Could not create the organization.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="chart-section">
    <h3>🏢 Company view</h3>
    <p class="chart-desc">
      Monitor many locations in one place: company roll-ups by brand and region, rankings against
      your sibling locations, daily automatic checks, and negative reviews sent to each location's
      manager as a task list.
    </p>

    <template v-if="canCreate">
      <div class="analysis-form">
        <label class="field" style="flex: 1; min-width: 240px">
          <span>Company name</span>
          <input v-model="name" type="text" placeholder="e.g. Acme Restaurant Group" @keyup.enter="create" />
        </label>
        <button class="run-btn" :disabled="loading" @click="create">
          {{ loading ? 'Creating…' : 'Create company' }}
        </button>
      </div>
      <p v-if="error" class="status error">{{ error }}</p>
    </template>
    <p v-else class="status">
      Creating a company needs a Pro or Enterprise plan. If someone at your company has already
      set one up, ask them to add your email address on the Team tab, then sign in with that email
      and you'll be added automatically.
    </p>
  </section>
</template>
