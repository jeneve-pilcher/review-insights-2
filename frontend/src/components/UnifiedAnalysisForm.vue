<script setup>
import { ref } from 'vue'
import { analyzeAll } from '../api'

const props = defineProps({
  businessLocation: { type: String, required: true },
  // Only Pro/Enterprise ever see the Wait-Time Heatmap that uses these two
  // values - no point showing them to a Free-tier user who can't see the
  // chart they feed.
  showRevenueInputs: { type: Boolean, default: false },
})

const emit = defineEmits(['result'])

const avgOrderValue = ref(35)
const multiplier = ref(20)
const loading = ref(false)
const error = ref('')

async function runAnalysis() {
  loading.value = true
  error.value = ''
  try {
    const data = await analyzeAll({
      reviewLimit: 0, // 0 = unlimited (Outscraper's native "fetch all" value)
      avgOrderValue: avgOrderValue.value,
      reviewsToCustomersMultiplier: multiplier.value,
    })
    emit('result', { data })
  } catch (err) {
    error.value = err?.response?.data?.detail || 'Something went wrong.'
  } finally {
    loading.value = false
  }
}

defineExpose({ loading })
</script>

<template>
  <section class="chart-section unified-form">
    <h3>🔎 Run Analysis</h3>
    <p class="chart-desc">
      Loads the Sentiment Drift chart (and the Wait-Time heatmap, if your plan includes it) for
      <strong>{{ businessLocation }}</strong>.
    </p>

    <div class="analysis-form">
      <template v-if="showRevenueInputs">
        <label class="field">
          <span>Avg. order value ($)</span>
          <input v-model.number="avgOrderValue" type="number" min="0" step="0.5" />
        </label>
        <label class="field">
          <span>Est. customers per review</span>
          <input v-model.number="multiplier" type="number" min="1" />
        </label>
      </template>
      <button class="run-btn" @click="runAnalysis" :disabled="loading">
        {{ loading ? 'Analyzing…' : 'Run Analysis' }}
      </button>
    </div>

    <p v-if="error" class="status error">{{ error }}</p>
  </section>
</template>
