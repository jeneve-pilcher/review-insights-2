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
import { shortBusinessName } from '../utils/placeName'

ChartJS.register(Title, Tooltip, Legend, CategoryScale, LinearScale, BarElement)

const THEME_LABELS = ['Product Quality', 'Pricing', 'Weekend Communication', 'Staff Behavior']
const THEME_COLORS = ['#3498db', '#9b59b6', '#e67e22', '#1abc9c']

const props = defineProps({
  businessLocation: { type: String, required: true },
  // Comes from the same Run Analysis click as every other panel.
  result: { type: Object, default: null },
  months: { type: Number, default: 6 },
  competitors: { type: Array, default: () => [] },
  comparing: { type: Boolean, default: false },
  error: { type: String, default: '' },
})
const emit = defineEmits(['update:competitors', 'run'])

function addCompetitor() {
  if (props.competitors.length >= 5) return
  emit('update:competitors', [...props.competitors, { name: `Competitor ${props.competitors.length + 1}`, search_query: '' }])
}
function removeCompetitor(i) {
  emit('update:competitors', props.competitors.filter((_, idx) => idx !== i))
}
function editCompetitor(i, key, value) {
  emit('update:competitors', props.competitors.map((c, idx) => (idx === i ? { ...c, [key]: value } : c)))
}

const readItems = computed(() => competitorReadItems(props.result))

// Say why a business has nothing in the chart, instead of leaving it out without a word.
const businessNotes = computed(() => {
  const out = []
  for (const biz of props.result?.businesses ?? []) {
    if (biz.no_reviews) {
      out.push(`${biz.name}: no Google reviews were found in the last ${props.months} ${props.months === 1 ? 'month' : 'months'}. Check that its Google Maps link or "name, street, city" points to one place, or try a longer time window.`)
    } else if (!biz.written_count) {
      out.push(`${biz.name}: ${biz.review_count} star ratings but no written reviews, so there are no themes to compare.`)
    }
  }
  return out
})

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
      <span class="data-basis">Each business: star tiers from all its reviews · themes from written reviews</span>
    </div>
    <p class="chart-desc">
      Compares <strong>{{ shortBusinessName(businessLocation) }}</strong> against the
      competitors you add below, using reviews from the last {{ months }}
      {{ months === 1 ? 'month' : 'months' }}. It breaks down what drives each business's top 3
      dominant star tiers by theme - exposing exactly where a competitor is vulnerable. Top
      keywords per tier are shown below the chart as a lightweight topic signal (word frequency,
      not full topic modeling).
    </p>

    <div class="competitor-inputs">
      <p class="chart-desc" style="margin-bottom: 8px">
        <strong>Add competitors.</strong> Your own business is always in the comparison. Each competitor you add is one
        extra review pull. Paste a Google Maps link if a name is ambiguous.
      </p>
      <div class="competitor-row">
        <input type="text" class="competitor-name" :value="shortBusinessName(businessLocation)" disabled />
        <input type="text" class="competitor-query" value="Your business (always included)" disabled />
      </div>
      <div v-for="(c, i) in competitors" :key="i" class="competitor-row">
        <input :value="c.name" type="text" placeholder="Competitor name (optional)" class="competitor-name" @input="editCompetitor(i, 'name', $event.target.value)" />
        <input :value="c.search_query" type="text" placeholder="Location, or a Google Maps URL" class="competitor-query" @input="editCompetitor(i, 'search_query', $event.target.value)" />
        <button type="button" class="remove-btn" @click="removeCompetitor(i)">✕</button>
      </div>
      <button v-if="competitors.length < 5" type="button" class="add-btn" @click="addCompetitor">+ Add competitor</button>
      <button type="button" class="run-btn" style="width: auto; padding: 8px 20px; margin-left: 8px" :disabled="comparing" @click="emit('run')">{{ comparing ? 'Comparing…' : 'Compare' }}</button>
      <p v-if="error" class="status error" style="margin-top: 6px">{{ error }}</p>
    </div>

    <p v-if="!result" class="status">Run the analysis (or press Compare) to see this chart.</p>

    <template v-else>
      <NlpCallout
        title="Your opening"
        :items="readItems"
        technique="A zero-shot language model reads each written review and assigns themes (quality, pricing, weekend communication, staff) with no keyword lists, then keywords are extracted per star tier."
      />

      <ul v-if="businessNotes.length" class="status error" style="margin: 0 0 12px; padding-left: 18px">
        <li v-for="n in businessNotes" :key="n">{{ n }}</li>
      </ul>

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
