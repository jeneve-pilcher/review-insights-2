<script setup>
import { computed } from 'vue'
import { Scatter } from 'vue-chartjs'
import { Chart as ChartJS, Legend, LineElement, LinearScale, PointElement, Tooltip } from 'chart.js'
import ByWeekBadge from './ByWeekBadge.vue'
import DataBasis from './DataBasis.vue'
import { readFit, toneStarFit } from '../utils/toneVsStars'
import { signed } from '../utils/nlpInsights'

ChartJS.register(Tooltip, Legend, LinearScale, PointElement, LineElement)

const props = defineProps({
  weekly: { type: Array, default: () => [] },
  meta: { type: Object, default: null },
})

const fit = computed(() => toneStarFit(props.weekly))
const reading = computed(() => (props.weekly.length ? readFit(fit.value) : ''))
const drawn = computed(() => fit.value.status === 'ok' || fit.value.status === 'flat')

const chartData = computed(() => {
  const f = fit.value
  const sets = [{
    type: 'scatter',
    label: 'One dot = one week',
    data: f.points.map((p) => ({ x: p.stars, y: p.tone })),
    backgroundColor: 'rgba(234, 88, 12, 0.65)',
    borderColor: '#fff',
    borderWidth: 1,
    // Busier weeks (more written reviews) get bigger dots, matching how the line is weighted.
    pointRadius: f.points.map((p) => Math.min(4 + Math.sqrt(p.n) * 1.6, 14)),
    pointHoverRadius: 10,
  }]
  if (f.status === 'ok') {
    sets.push({
      type: 'scatter',
      showLine: true,
      label: 'Trend line across weeks',
      data: f.line,
      borderColor: '#7c2d12',
      borderWidth: 2.5,
      borderDash: [7, 5],
      pointRadius: 0,
      fill: false,
    })
  }
  return { datasets: sets }
})

const chartOptions = computed(() => ({
  responsive: true,
  plugins: {
    legend: { labels: { usePointStyle: true, padding: 16 } },
    tooltip: {
      filter: (ctx) => ctx.datasetIndex === 0,
      callbacks: {
        title: (items) => `Week starting ${fit.value.points[items[0].dataIndex].week}`,
        label: (ctx) => {
          const p = fit.value.points[ctx.dataIndex]
          return [`Average stars: ${p.stars}★`, `Average tone: ${signed(p.tone)}`, `${p.n} written of ${p.reviews} reviews that week`]
        },
      },
    },
  },
  scales: {
    x: { type: 'linear', min: 1, max: 5, title: { display: true, text: 'Average star rating in that week (each dot is a week)' }, grid: { color: 'rgba(0,0,0,0.05)' } },
    y: { type: 'linear', min: -1, max: 1, title: { display: true, text: 'Average tone of that week’s written reviews (-1 to 1)' }, grid: { color: 'rgba(0,0,0,0.05)' } },
  },
}))
</script>

<template>
  <section class="chart-section tone-stars-section">
    <div class="title-row">
      <h3>🔗 Tone vs star rating<ByWeekBadge /></h3>
      <DataBasis :meta="meta" uses="both" />
    </div>
    <p class="chart-desc">
      Each dot is one calendar week: that week's average star rating against the average tone of the words people wrote that
      week. The dashed line is the best straight-line fit across weeks (weeks with more written reviews count for more). When
      the dots sit well below the line, people wrote harsher words than their stars suggest. Stars use every review; tone uses
      written reviews only. A link between the two is not proof that one causes the other.
    </p>

    <template v-if="weekly.length">
      <p class="tvs-reading" :class="{ 'tvs-muted': !drawn }">{{ reading }}</p>

      <Scatter v-if="drawn" :data="chartData" :options="chartOptions" />

      <div v-if="fit.harsher?.length" class="tvs-harsher">
        <h4>Weeks where the words were harsher than the stars</h4>
        <ul>
          <li v-for="h in fit.harsher" :key="h.week">
            <strong>Week of {{ h.week }}:</strong> {{ h.stars }}★ on average, but tone {{ signed(h.tone) }}
            ({{ Math.abs(h.gap).toFixed(2) }} below the line), from {{ h.n }} written reviews.
          </li>
        </ul>
      </div>
    </template>
    <p v-else class="status">Run analysis above to see this chart.</p>
  </section>
</template>

<style>
.tvs-reading { margin: 0 0 12px; font-weight: 600; color: #7c2d12; }
.tvs-reading.tvs-muted { font-weight: 400; color: #78716c; }
.tvs-harsher { margin-top: 14px; font-size: 13px; }
.tvs-harsher h4 { margin: 0 0 6px; font-size: 14px; }
.tvs-harsher ul { margin: 0; padding-left: 18px; }
.tvs-harsher li { margin: 3px 0; }
</style>
