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
} from 'chart.js'

ChartJS.register(Title, Tooltip, CategoryScale, LinearScale, BarElement)

const props = defineProps({
  weekly: { type: Array, default: () => [] },
})

// Red (negative) -> amber (neutral) -> green (positive), interpolated by
// VADER compound score (-1 to 1).
function colorForSentiment(score) {
  const clamped = Math.max(-1, Math.min(1, score))
  if (clamped >= 0) {
    // amber (241,196,15) -> green (46,204,113)
    const t = clamped
    const r = Math.round(241 + (46 - 241) * t)
    const g = Math.round(196 + (204 - 196) * t)
    const b = Math.round(15 + (113 - 15) * t)
    return `rgb(${r}, ${g}, ${b})`
  }
  // amber (241,196,15) -> red (231,76,60)
  const t = -clamped
  const r = Math.round(241 + (231 - 241) * t)
  const g = Math.round(196 + (76 - 196) * t)
  const b = Math.round(15 + (60 - 15) * t)
  return `rgb(${r}, ${g}, ${b})`
}

const chartData = computed(() => ({
  labels: props.weekly.map((w) => w.week_start),
  datasets: [
    {
      label: 'Avg. sentiment (text tone, -1 to 1)',
      data: props.weekly.map((w) => w.avg_sentiment),
      backgroundColor: props.weekly.map((w) => colorForSentiment(w.avg_sentiment)),
      borderRadius: 6,
    },
  ],
}))

const chartOptions = computed(() => ({
  responsive: true,
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label: (ctx) => `Avg. sentiment: ${ctx.parsed.y}`,
        afterLabel: (ctx) => {
          const week = props.weekly[ctx.dataIndex]
          if (!week?.top_words?.length) return 'No standout words this week'
          const words = week.top_words.map((w) => w.word).join(', ')
          return `Top words: ${words}`
        },
      },
    },
  },
  scales: {
    y: { min: -1, max: 1, title: { display: true, text: 'Sentiment (text tone)' } },
  },
}))
</script>

<template>
  <section class="chart-section">
    <h3>🗣️ Weekly Themes &amp; Sentiment</h3>
    <p class="chart-desc">
      Average tone of the actual review text each week (separate from star ratings - this can
      shift before ratings do), plus the words that came up most. Hover a bar to see that week's
      top words.
    </p>

    <Bar v-if="weekly.length" :data="chartData" :options="chartOptions" />
    <p v-else class="status">Run analysis above to see this chart.</p>
  </section>
</template>