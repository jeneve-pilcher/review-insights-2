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
import DataBasis from './DataBasis.vue'
import NlpCallout from './NlpCallout.vue'
import { signed, weeklyReadItems } from '../utils/nlpInsights'

ChartJS.register(Title, Tooltip, CategoryScale, LinearScale, BarElement)

const props = defineProps({
  weekly: { type: Array, default: () => [] },
  meta: { type: Object, default: null },
})

const readItems = computed(() => weeklyReadItems(props.weekly))

// Most recent weeks first, so the freshest language is at the top.
const recentWeeks = computed(() => props.weekly.slice(-8).reverse())

// Red (negative) -> amber (neutral) -> green (positive), interpolated by
// VADER compound score (-1 to 1).
function colorForSentiment(score) {
  if (score == null) return '#d5d9df' // nobody wrote a review that week
  const clamped = Math.max(-1, Math.min(1, score))
  if (clamped >= 0) {
    const t = clamped
    const r = Math.round(241 + (46 - 241) * t)
    const g = Math.round(196 + (204 - 196) * t)
    const b = Math.round(15 + (113 - 15) * t)
    return `rgb(${r}, ${g}, ${b})`
  }
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
    <div class="title-row">
      <h3>🗣️ Weekly Themes &amp; Sentiment</h3>
      <DataBasis :meta="meta" uses="both" />
    </div>
    <p class="chart-desc">
      Average tone of the written review text each week (separate from star ratings - this can
      shift before ratings do), plus the words that came up most. Star-only reviews have no
      words to read, so weeks with none show as gaps.
    </p>

    <template v-if="weekly.length">
      <NlpCallout
        :items="readItems"
        technique="VADER sentiment scoring per week, plus keyword extraction (common filler words removed, then word frequency)."
      />

      <Bar :data="chartData" :options="chartOptions" />

      <div class="week-words">
        <h4>Words by week</h4>
        <div v-for="w in recentWeeks" :key="w.week_start" class="week-words-row">
          <span class="week-words-date">{{ w.week_start }}</span>
          <span class="week-pill" :style="{ background: colorForSentiment(w.avg_sentiment) }">
            {{ w.avg_sentiment == null ? 'n/a' : signed(w.avg_sentiment) }}
          </span>
          <span class="week-words-count">
            {{ w.total_reviews }} {{ w.total_reviews === 1 ? 'review' : 'reviews' }} · {{ w.text_reviews }} written
          </span>
          <span class="week-chips">
            <span v-for="word in w.top_words.slice(0, 5)" :key="word.word" class="week-chip">
              {{ word.word }}
            </span>
            <span v-if="!w.top_words.length" class="week-chip-empty">no standout words</span>
          </span>
        </div>
      </div>
    </template>
    <p v-else class="status">Run analysis above to see this chart.</p>
  </section>
</template>

<style>
.week-words {
  margin-top: 22px;
}

.week-words h4 {
  margin: 0 0 8px;
  font-size: 14px;
}

.week-words-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 7px 0;
  border-top: 1px solid #eef0f3;
  font-size: 12px;
  flex-wrap: wrap;
}

.week-words-date {
  width: 82px;
  color: #666;
  flex-shrink: 0;
}

.week-pill {
  min-width: 46px;
  text-align: center;
  color: #1a1a1a;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 999px;
  flex-shrink: 0;
}

.week-words-count {
  width: 150px;
  color: #888;
  flex-shrink: 0;
}

.week-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.week-chip {
  background: #eef0f3;
  border-radius: 999px;
  padding: 2px 10px;
  color: #444;
}

.week-chip-empty {
  color: #aaa;
  font-style: italic;
}
</style>
