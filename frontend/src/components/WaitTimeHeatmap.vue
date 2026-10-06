<script setup>
import { computed } from 'vue'
import DataBasis from './DataBasis.vue'
import NlpCallout from './NlpCallout.vue'
import { heatmapReadItems } from '../utils/nlpInsights'

const TIER_COLORS = ['#2ecc71', '#f1c40f', '#e74c3c']

const props = defineProps({
  result: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  meta: { type: Object, default: null },
})

const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

const readItems = computed(() => heatmapReadItems(props.result?.summary))

const hourLabels = computed(() => {
  if (!props.result) return []
  return [...new Set(props.result.matrix.map((c) => c.hour))]
})

function cellFor(day, hour) {
  if (!props.result) return null
  return props.result.matrix.find((c) => c.day === day && c.hour === hour) || null
}

function cellTitle(day, hour) {
  const cell = cellFor(day, hour)
  const mentions = cell?.wait_mentions ?? 0
  const base = `${day} ${hour}`
  return mentions ? `${base}: ${mentions} review(s) mention waiting or slow service` : base
}

const maxDrag = computed(() => {
  if (!props.result?.revenue_drag?.length) return 1
  return Math.max(...props.result.revenue_drag.map((r) => r.estimated_dollars))
})

const sortedDrag = computed(() => {
  if (!props.result) return []
  return [...props.result.revenue_drag].sort((a, b) => b.estimated_dollars - a.estimated_dollars)
})
</script>

<template>
  <section class="chart-section">
    <div class="title-row">
      <h3>🔥 Wait-Time Revenue Leak Heatmap</h3>
      <span class="nlp-badge">🧠 NLP</span>
      <DataBasis :meta="meta" uses="both" />
    </div>
    <p class="chart-desc">
      Maps operational hours against your top 3 dominant star tiers, and estimates the dollar
      value of service-delay drag using your average order value.
      <em>Dollar figures are a heuristic estimate, not a certified financial calculation.</em>
    </p>

    <p v-if="loading" class="status">Analyzing…</p>

    <template v-if="result">
      <NlpCallout
        :items="readItems"
        technique="Phrase detection (“long wait”, “slow service”, “took forever” and similar) on each review's text, matched to the day and hour the review was posted."
      />

      <div class="heatmap-legend">
        <span v-for="(tier, i) in result.dominant_tiers" :key="tier">
          <span class="swatch" :style="{ background: TIER_COLORS[i] }"></span>
          {{ tier }}★ (Dominant #{{ i + 1 }})
        </span>
        <span>💬 = reviews posted in this slot mention waiting</span>
      </div>

      <div class="heatmap-grid">
        <div class="heatmap-row heatmap-header">
          <div class="heatmap-corner"></div>
          <div v-for="hour in hourLabels" :key="hour" class="heatmap-hour-label">{{ hour }}</div>
        </div>
        <div v-for="day in days" :key="day" class="heatmap-row">
          <div class="heatmap-day-label">{{ day }}</div>
          <div
            v-for="hour in hourLabels"
            :key="hour"
            class="heatmap-cell heatmap-cell-rel"
            :title="cellTitle(day, hour)"
          >
            <template v-if="cellFor(day, hour)?.review_count">
              <div
                v-for="(tier, i) in result.dominant_tiers"
                :key="tier"
                class="heatmap-segment"
                :style="{
                  width: (cellFor(day, hour).tier_pct[tier] || 0) + '%',
                  background: TIER_COLORS[i],
                }"
              ></div>
            </template>
            <div v-else class="heatmap-empty">–</div>
            <span v-if="cellFor(day, hour)?.wait_mentions" class="heatmap-mention">💬</span>
          </div>
        </div>
      </div>

      <div v-if="sortedDrag.length" class="revenue-drag">
        <h4>💸 Estimated Revenue Drag</h4>
        <div v-for="(row, i) in sortedDrag" :key="i" class="drag-row">
          <span class="drag-label">{{ row.day }} {{ row.hour }}</span>
          <div class="drag-bar-track">
            <div
              class="drag-bar-fill"
              :style="{ width: (row.estimated_dollars / maxDrag) * 100 + '%' }"
            ></div>
          </div>
          <span class="drag-value">${{ row.estimated_dollars.toLocaleString() }}</span>
        </div>
      </div>
      <p v-else class="status">No significant wait-time revenue drag detected.</p>
    </template>
    <p v-else-if="!loading" class="status">Run analysis above to see this chart.</p>
  </section>
</template>

<style>
.heatmap-cell-rel {
  position: relative;
}

.heatmap-mention {
  position: absolute;
  right: 4px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 11px;
  line-height: 1;
  filter: drop-shadow(0 0 1px rgba(255, 255, 255, 0.9));
}
</style>
