<script setup>
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Filler,
  LinearScale,
  LineElement,
  PointElement,
  Title,
  Tooltip,
} from 'chart.js'
import DataBasis from './DataBasis.vue'
import NlpCallout from './NlpCallout.vue'
import { driftReadItems } from '../utils/nlpInsights'

ChartJS.register(Title, Tooltip, CategoryScale, LinearScale, PointElement, LineElement, BarElement, Filler)

const TIER_COLORS = ['#2ecc71', '#f1c40f', '#e74c3c']

const props = defineProps({
  result: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  meta: { type: Object, default: null },
})

const readItems = computed(() => driftReadItems(props.result))

// Review pace, freshness and star mix: built from EVERY review, star-only included.
const velocity = computed(() => props.result?.velocity ?? null)

const STAR_COLORS = { 5: '#2ecc71', 4: '#8bd96b', 3: '#f1c40f', 2: '#f39c12', 1: '#e74c3c' }

const starMix = computed(() => {
  const v = velocity.value
  if (!v || !v.reviews) return []
  return [5, 4, 3, 2, 1].map((star) => {
    const count = v.star_counts[star] ?? 0
    return { star, count, pct: Math.round((1000 * count) / v.reviews) / 10, color: STAR_COLORS[star] }
  })
})

const paceClass = computed(() => {
  const v = velocity.value
  if (!v || v.earlier_per_week == null || !v.earlier_per_week) return ''
  const ratio = v.recent_per_week / v.earlier_per_week
  if (ratio <= 0.6) return 'pace-down'
  return ratio >= 1.4 ? 'pace-up' : ''
})

const alertWeeks = computed(() => new Set((props.result?.drift_alerts ?? []).map((a) => a.week_start)))

// Canvas gradient fill under the #1 dominant tier line - purely visual polish.
function tier1Gradient(context) {
  const { chart } = context
  const { ctx, chartArea } = chart
  if (!chartArea) return 'rgba(46, 204, 113, 0.12)'
  const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom)
  gradient.addColorStop(0, 'rgba(46, 204, 113, 0.35)')
  gradient.addColorStop(1, 'rgba(46, 204, 113, 0.02)')
  return gradient
}

const chartData = computed(() => {
  if (!props.result) return null
  const { dominant_tiers: tiers, weekly } = props.result

  const labels = weekly.map((w) => w.week_start)

  const tierDatasets = tiers.map((tier, i) => ({
    label: `${tier}★ volume (Dominant #${i + 1})`,
    data: weekly.map((w) => w.counts[tier] ?? 0),
    borderColor: TIER_COLORS[i] || '#888',
    borderWidth: i === 0 ? 3 : 2,
    backgroundColor: i === 0 ? tier1Gradient : 'transparent',
    fill: i === 0,
    tension: 0.35,
    yAxisID: 'y',
    pointRadius: weekly.map((w) => (alertWeeks.value.has(w.week_start) ? 6 : 2)),
    pointBackgroundColor: weekly.map((w) =>
      alertWeeks.value.has(w.week_start) ? '#e74c3c' : (TIER_COLORS[i] || '#888')
    ),
    pointBorderColor: '#fff',
    pointBorderWidth: weekly.map((w) => (alertWeeks.value.has(w.week_start) ? 2 : 1)),
    pointHoverRadius: 7,
  }))

  const avgDataset = {
    label: 'Rolling average rating',
    data: weekly.map((w) => w.rolling_avg_rating),
    borderColor: '#3498db',
    borderDash: [6, 4],
    tension: 0.3,
    yAxisID: 'y1',
    pointRadius: 2,
  }

  return { labels, datasets: [...tierDatasets, avgDataset] }
})

const chartOptions = {
  responsive: true,
  interaction: { mode: 'index', intersect: false },
  plugins: {
    legend: { labels: { usePointStyle: true, padding: 16 } },
  },
  scales: {
    y: {
      type: 'linear',
      position: 'left',
      title: { display: true, text: 'Review volume' },
      beginAtZero: true,
      grid: { color: 'rgba(0,0,0,0.05)' },
    },
    y1: {
      type: 'linear',
      position: 'right',
      title: { display: true, text: 'Rolling avg rating' },
      min: 1,
      max: 5,
      grid: { drawOnChartArea: false },
    },
    x: { grid: { display: false } },
  },
}
</script>

<template>
  <section class="chart-section sentiment-drift-section">
    <div class="title-row">
      <h3>📈 Sentiment Drift Matrix</h3>
      <DataBasis :meta="meta" uses="both" />
    </div>
    <p class="chart-desc">
      Tracks weekly volume across your top 3 dominant star tiers against the rolling average
      rating - built to catch a shift from your top tier into #2/#3 before the overall score
      visibly moves. Volume and ratings count every review, including star-only ones with no
      comment. Large red points mark weeks with a detected drift alert.
    </p>

    <p v-if="loading" class="status">Analyzing…</p>

    <template v-if="chartData">
      <div v-if="velocity" class="velocity-stats">
        <div class="velocity-card">
          <span class="label">Reviews per week</span>
          <span class="value" :class="paceClass">{{ velocity.recent_per_week }}</span>
          <span class="sub">last 4 weeks · {{ velocity.earlier_per_week ?? '–' }} before</span>
        </div>
        <div class="velocity-card">
          <span class="label">Last review</span>
          <span class="value">{{ velocity.days_since_last }} {{ velocity.days_since_last === 1 ? 'day' : 'days' }} ago</span>
          <span class="sub">{{ velocity.last_review_date }}</span>
        </div>
        <div class="velocity-card">
          <span class="label">Average rating (all reviews)</span>
          <span class="value">{{ velocity.avg_rating }}★</span>
          <span class="sub">{{ velocity.reviews }} reviews · {{ velocity.text_reviews }} written</span>
        </div>
      </div>

      <div v-if="starMix.length" class="star-mix">
        <div class="star-mix-bar">
          <div
            v-for="s in starMix"
            :key="s.star"
            class="star-mix-seg"
            :style="{ width: s.pct + '%', background: s.color }"
            :title="`${s.star}★: ${s.count} reviews (${s.pct}%)`"
          ></div>
        </div>
        <div class="star-mix-legend">
          <span v-for="s in starMix" :key="s.star">
            <span class="star-swatch" :style="{ background: s.color }"></span>{{ s.star }}★ {{ s.pct }}%
          </span>
        </div>
      </div>

      <NlpCallout
        :items="readItems"
        technique="VADER sentiment scoring on every review, plus detection of phrases like “used to be” and “formula change”."
      />

      <Line :data="chartData" :options="chartOptions" />

      <div v-if="result.drift_alerts.length" class="drift-alerts">
        <h4>⚠️ Sentiment Drift Alerts</h4>
        <ul>
          <li v-for="(alert, i) in result.drift_alerts" :key="i">
            <strong>{{ alert.week_start }}:</strong> {{ alert.message }}
          </li>
        </ul>
      </div>
      <p v-else class="status">No drift pattern detected in this window.</p>
    </template>
    <p v-else-if="!loading" class="status">Run analysis above to see this chart.</p>
  </section>
</template>

<style>
.velocity-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 14px;
}

.velocity-card {
  background: #f7f8fa;
  border: 1px solid #e4e6ea;
  border-radius: 8px;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.velocity-card .label {
  font-size: 12px;
  color: #666;
}

.velocity-card .value {
  font-size: 20px;
  font-weight: 700;
}

.velocity-card .value.pace-down { color: #c0392b; }
.velocity-card .value.pace-up { color: #1e8e4e; }

.velocity-card .sub {
  font-size: 11px;
  color: #888;
}

.star-mix {
  margin-bottom: 18px;
}

.star-mix-bar {
  display: flex;
  height: 14px;
  border-radius: 7px;
  overflow: hidden;
  background: #eef0f3;
}

.star-mix-seg {
  height: 100%;
}

.star-mix-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  margin-top: 6px;
  font-size: 11px;
  color: #666;
}

.star-swatch {
  display: inline-block;
  width: 9px;
  height: 9px;
  border-radius: 2px;
  margin-right: 4px;
}

@media (max-width: 720px) {
  .velocity-stats {
    grid-template-columns: 1fr;
  }
}
</style>
