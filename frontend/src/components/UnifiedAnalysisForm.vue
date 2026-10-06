<script setup>
import { ref } from 'vue'
import { analyzeAll } from '../api'

const props = defineProps({
  businessLocation: { type: String, required: true },
  months: { type: Number, default: 6 },
  // Only Pro/Enterprise ever see the Wait-Time Heatmap that uses these two
  // values - no point showing them to a Free-tier user.
  showRevenueInputs: { type: Boolean, default: false },
  // Pro/Enterprise: optional competitors, analyzed in the same click.
  showCompetitors: { type: Boolean, default: false },
})

const emit = defineEmits(['result', 'update:months'])

const MONTH_OPTIONS = [1, 3, 6, 12, 24]

const avgOrderValue = ref(35)
const multiplier = ref(20)
const loading = ref(false)
const error = ref('')

const competitors = ref([])

function addCompetitor() {
  if (competitors.value.length >= 5) return
  competitors.value.push({ name: `Competitor ${competitors.value.length + 1}`, search_query: '' })
}

function removeCompetitor(index) {
  competitors.value.splice(index, 1)
}

async function runAnalysis() {
  loading.value = true
  error.value = ''
  try {
    const data = await analyzeAll({
      months: props.months,
      avgOrderValue: avgOrderValue.value,
      reviewsToCustomersMultiplier: multiplier.value,
      competitors: props.showCompetitors
        ? competitors.value
            .filter((c) => c.search_query.trim())
            .map((c) => ({ name: c.name.trim() || 'Competitor', search_query: c.search_query.trim() }))
        : [],
    })
    emit('result', { data })
  } catch (err) {
    error.value = err?.response?.data?.detail || 'Something went wrong.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="chart-section unified-form">
    <h3>🔎 Run Analysis</h3>
    <p class="chart-desc">
      One review pull for <strong>{{ businessLocation }}</strong> powers every panel below,
      all from this one button. A shorter time window runs faster and uses fewer scraping credits.
    </p>

    <div class="analysis-form">
      <label class="field">
        <span>Pull reviews from the last</span>
        <select
          class="months-select"
          :value="months"
          @change="emit('update:months', Number($event.target.value))"
        >
          <option v-for="m in MONTH_OPTIONS" :key="m" :value="m">
            {{ m }} {{ m === 1 ? 'month' : 'months' }}
          </option>
        </select>
      </label>
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
    </div>

    <div v-if="showCompetitors" class="competitor-inputs" style="margin-top: 14px">
      <p class="chart-desc" style="margin-bottom: 8px">
        <strong>Optional: compare against competitors in the same click.</strong> Your own reviews
        are pulled once and shared; each competitor you add is one extra pull. Paste a Google Maps
        link if a name is ambiguous.
      </p>
      <div v-for="(c, i) in competitors" :key="i" class="competitor-row">
        <input v-model="c.name" type="text" placeholder="Competitor name" class="competitor-name" />
        <input v-model="c.search_query" type="text" placeholder="Location, or a Google Maps URL" class="competitor-query" />
        <button class="remove-btn" @click="removeCompetitor(i)">✕</button>
      </div>
      <button v-if="competitors.length < 5" class="add-btn" @click="addCompetitor">+ Add competitor</button>
    </div>

    <button class="run-btn" style="width: auto; padding: 10px 28px; margin-top: 16px" @click="runAnalysis" :disabled="loading">
      {{ loading ? 'Analyzing…' : 'Run Analysis' }}
    </button>

    <p v-if="error" class="status error">{{ error }}</p>
  </section>
</template>

<style>
.months-select {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #d3d6db;
  border-radius: 6px;
  font-size: 13px;
  font-family: inherit;
  background: white;
}
</style>
