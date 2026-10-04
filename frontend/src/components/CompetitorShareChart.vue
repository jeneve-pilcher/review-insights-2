<script setup>
import { computed, ref } from 'vue'
import { Bar } from 'vue-chartjs'
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  LinearScale,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'
import { analyzeCompetitorShare } from '../api'

ChartJS.register(Title, Tooltip, Legend, CategoryScale, LinearScale, BarElement)

const THEME_LABELS = ['Product Quality', 'Pricing', 'Weekend Communication', 'Staff Behavior']
const THEME_COLORS = ['#3498db', '#9b59b6', '#e67e22', '#1abc9c']

const props = defineProps({ businessLocation: { type: String, required: true } })

// "Your Business" is always the account's fixed location - only
// competitors are free-text and editable.
const competitors = ref([{ name: 'Competitor A', search_query: '' }])
const loading = ref(false)
const error = ref('')
const result = ref(null)

function addCompetitor() {
  if (competitors.value.length >= 5) return
  competitors.value.push({ name: `Competitor ${competitors.value.length + 1}`, search_query: '' })
}

function removeCompetitor(index) {
  if (competitors.value.length <= 1) return
  competitors.value.splice(index, 1)
}

async function runAnalysis() {
  if (competitors.value.some((c) => !c.search_query.trim())) return
  loading.value = true
  error.value = ''
  try {
    result.value = await analyzeCompetitorShare({
      competitors: competitors.value,
      reviewLimit: 0,
    })
  } catch (err) {
    error.value = err?.response?.data?.detail || 'Something went wrong.'
  } finally {
    loading.value = false
  }
}

// Flatten each business's tiers into ordered columns: "Biz (5★)", "Biz (4★)", ...
const flattenedColumns = computed(() => {
  if (!result.value) return []
  const cols = []
  for (const biz of result.value.businesses) {
    for (const tierRow of biz.tiers) {
      cols.push({ label: `${biz.name}\n(${tierRow.tier}★)`, tierRow })
    }
  }
  return cols
})

const chartData = computed(() => {
  if (!result.value) return null
  const columns = flattenedColumns.value

  const datasets = THEME_LABELS.map((theme, i) => ({
    label: theme,
    data: columns.map((c) => c.tierRow.theme_pct[theme] ?? 0),
    backgroundColor: THEME_COLORS[i],
    stack: 'themes',
  }))

  return { labels: columns.map((c) => c.label), datasets }
})

const chartOptions = {
  responsive: true,
  plugins: { legend: { position: 'bottom' } },
  scales: {
    x: { stacked: true },
    y: { stacked: true, max: 100, title: { display: true, text: '% of review volume' } },
  },
}
</script>

<template>
  <section class="chart-section">
    <h3>🏁 Competitor Semantic Share Matrix</h3>
    <p class="chart-desc">
      Compares <strong>{{ businessLocation }}</strong> (your account's business) against up to 5
      competitors you name here, breaking down what drives each of their top 3 dominant star
      tiers by theme - exposing exactly where a competitor is vulnerable. Top keywords per tier
      are shown below the chart as a lightweight topic signal (word frequency, not full topic
      modeling).
    </p>

    <p class="chart-desc" style="margin-top: -8px">
      Tip: if a competitor's name is ambiguous (multiple locations in the same city), paste that
      location's specific Google Maps URL instead of typing its name.
    </p>

    <div class="competitor-inputs">
      <div class="competitor-row">
        <input :value="`Your Business (${businessLocation})`" type="text" class="competitor-query" disabled />
      </div>
      <div v-for="(c, i) in competitors" :key="i" class="competitor-row">
        <input v-model="c.name" type="text" placeholder="Competitor name" class="competitor-name" />
        <input v-model="c.search_query" type="text" placeholder="Location, or a Google Maps URL" class="competitor-query" />
        <button v-if="competitors.length > 1" class="remove-btn" @click="removeCompetitor(i)">✕</button>
      </div>
      <button v-if="competitors.length < 5" class="add-btn" @click="addCompetitor">+ Add competitor</button>
    </div>

    <div class="analysis-form">
      <button class="run-btn" @click="runAnalysis" :disabled="loading">
        {{ loading ? 'Analyzing…' : 'Run Analysis' }}
      </button>
    </div>

    <p v-if="error" class="status error">{{ error }}</p>

    <Bar v-if="chartData" :data="chartData" :options="chartOptions" />

    <div v-if="result" class="keyword-topics">
      <div v-for="biz in result.businesses" :key="biz.name" class="keyword-business-block">
        <h4>{{ biz.name }}</h4>
        <div v-for="tierRow in biz.tiers" :key="tierRow.tier" class="keyword-tier-row">
          <span class="keyword-tier-label">{{ tierRow.tier }}★:</span>
          <span v-if="tierRow.top_keywords?.length" class="keyword-chips">
            <span v-for="kw in tierRow.top_keywords" :key="kw.word" class="keyword-chip">
              {{ kw.word }} ({{ kw.count }})
            </span>
          </span>
          <span v-else class="keyword-chips-empty">No standout keywords</span>
        </div>
      </div>
    </div>
  </section>
</template>
