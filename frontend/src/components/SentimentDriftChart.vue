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

ChartJS.register(Title, Tooltip, CategoryScale, LinearScale, PointElement, LineElement, BarElement, Filler)

const TIER_COLORS = ['#2ecc71', '#f1c40f', '#e74c3c']

const props = defineProps({
  result: { type: Object, default: null },
  loading: { type: Boolean, default: false },
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
    <h3>📈 Sentiment Drift Matrix</h3>
    <p class="chart-desc">
      Tracks weekly volume across your top 3 dominant star tiers against the rolling average
      rating - built to catch a shift from your top tier into #2/#3 before the overall score
      visibly moves. Large red points mark weeks with a detected drift alert.
    </p>

    <p v-if="loading" class="status">Analyzing…</p>

    <template v-if="chartData">
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