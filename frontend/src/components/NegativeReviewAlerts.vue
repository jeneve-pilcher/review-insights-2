<script setup>
import { ref } from 'vue'
import { fetchNegativeReviews } from '../api'

defineProps({ businessLocation: { type: String, required: true } })

const lookbackDays = ref(30)
const loading = ref(false)
const error = ref('')
const result = ref(null)

async function runAnalysis() {
  loading.value = true
  error.value = ''
  try {
    result.value = await fetchNegativeReviews({
      reviewLimit: 0,
      lookbackDays: lookbackDays.value,
      maxReviews: 20,
    })
  } catch (err) {
    error.value = err?.response?.data?.detail || 'Something went wrong.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="chart-section">
    <h3>🚨 Negative Review Alerts</h3>
    <p class="chart-desc">
      Recent 1-2★ reviews for <strong>{{ businessLocation }}</strong> so managers can respond
      fast. Author names are removed, and review text is scrubbed of anything that looks like an
      email, phone number, or order number before it's shown here — a best-effort filter, not a
      guarantee. New negative reviews from the last 24 hours also trigger an email alert to your
      account email.
    </p>

    <div class="analysis-form">
      <label class="field">
        <span>Lookback (days)</span>
        <input v-model.number="lookbackDays" type="number" min="1" max="180" />
      </label>
      <button class="run-btn" @click="runAnalysis" :disabled="loading">
        {{ loading ? 'Checking…' : 'Check for negative reviews' }}
      </button>
    </div>

    <p v-if="error" class="status error">{{ error }}</p>

    <template v-if="result">
      <p v-if="result.alert_sent" class="status" style="color: #e67e22">
        📧 Email alert sent — {{ result.recent_count }} new negative review(s) in the last 24h.
      </p>

      <div v-if="result.negative_reviews.length" class="negative-review-list">
        <div v-for="(r, i) in result.negative_reviews" :key="i" class="negative-review-card">
          <div class="negative-review-header">
            <span class="negative-review-rating">{{ r.rating }}★</span>
            <span class="negative-review-date">{{ r.review_date }}</span>
          </div>
          <p>{{ r.redacted_text }}</p>
        </div>
      </div>
      <p v-else class="status">No negative reviews found in this window.</p>
    </template>
  </section>
</template>
