<script setup>
import { computed } from 'vue'
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
import NlpCallout from './NlpCallout.vue'
import { competitorReadItems } from '../utils/nlpInsights'

ChartJS.register(Title, Tooltip, Legend, CategoryScale, LinearScale, BarElement)

const THEME_LABELS = ['Product Quality', 'Pricing', 'Weekend Communication', 'Staff Behavior']
const THEME_COLORS = ['#3498db', '#9b59b6', '#e67e22', '#1abc9c']

const props = defineProps({
  businessLocation: { type: String, required: true },
  // Comes from the same Run Analysis click as every other panel.
  result: { type: Object, default: null },
  months: { type: Number, default: 6 },
})

const readItems = computed(() => competitorReadItems(props.result))

// Flatten each business's tiers into ordered columns: "Biz (5★)", "Biz (4★)", ...
const flattenedColumns = computed(() => {
  if (!props.result) return []
  const cols = []
  for (const biz of props.result.businesses) {
    for (const tierRow of biz.tiers) {
      cols.push({ label: `${biz.name}\n(${tierRow.tier}★)`, tierRow })
    }
  }
  return cols
})

const chartData = computed(() => {
  if (!props.result) return null
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
    y: { stacked: true, max: 100, title: { display: true, text: '% of written reviews in the tier' } },
  },
}
</script>

<template>
  <section class="chart-section">
    <div class="title-row">
      <h3>🏁 Competitor Semantic Share Matrix</h3>
      <span class="nlp-badge">🧠 NLP</span>
      <span class="data-basis">Each business: star tiers from all its reviews · themes from written reviews</span>
    </div>
    <p class="chart-desc">
      Compares <strong>{{ businessLocation }}</strong> (your account's business) against the
      competitors you add in <em>Run Analysis</em> above, using reviews from the last {{ months }}
      {{ months === 1 ? 'month' : 'months' }}. It breaks down what drives each business's top 3
      dominant star tiers by theme - exposing exactly where a competitor is vulnerable. Top
      keywords per tier are shown below the chart as a lightweight topic signal (word frequency,
      not full topic modeling).
    </p>

    <p v-if="!result" class="status">
      Optional: add competitors in Run Analysis above, then click Run Analysis. Each competitor
      is one extra review pull.
    </p>

    <template v-else>
      <NlpCallout
        title="Your opening"
        :items="readItems"
        technique="A zero-shot language model reads each written review and assigns themes (quality, pricing, weekend communication, staff) with no keyword lists, then keywords are extracted per star tier."
      />

      <Bar :data="chartData" :options="chartOptions" />

      <div class="keyword-topics">
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
    </template>
  </section>
</template>
