<script setup>
import { computed, ref } from 'vue'
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

// Time-and-topic map: the 💬 count is for whichever topic is picked (waiting by default).
const topic = ref('wait')
const topics = computed(() => props.result?.topics?.length ? props.result.topics : [{ id: 'wait', label: 'Waiting / slow service' }])
const topicLabel = computed(() => (topics.value.find((t) => t.id === topic.value) || topics.value[0]).label)

function countFor(cell) {
  if (!cell) return 0
  if (cell.topic_mentions) return cell.topic_mentions[topic.value] || 0
  return topic.value === 'wait' ? (cell.wait_mentions || 0) : 0
}

const busiestSlot = computed(() => {
  let best = null
  for (const c of props.result?.matrix || []) {
    const n = countFor(c)
    if (n && (!best || n > best.n)) best = { n, day: c.day, hour: c.hour }
  }
  return best
})

function cellTitle(day, hour) {
  const cell = cellFor(day, hour)
  const mentions = countFor(cell)
  const base = `${day} ${hour}`
  return mentions ? `${base}: ${mentions} review(s) mention ${topicLabel.value.toLowerCase()}` : base
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
      <DataBasis :meta="meta" uses="both" />
    </div>
    <p class="chart-desc">
      Maps the day and hour reviews were posted against your top 3 dominant star tiers, lets you see when reviews mention waiting or any of your industry's topics, and estimates the dollar
      value of service-delay drag using your average order value. Time of day uses Google
      reviews only, because other platforms may give just a date.
      <em>Dollar figures are a heuristic estimate, not a certified financial calculation.</em>
    </p>

    <p v-if="loading" class="status">Analyzing…</p>

    <template v-if="result && result.matrix.length">
      <NlpCallout
        :items="readItems"
        technique="Phrase detection (“long wait”, “slow service”, “took forever” and similar) on each review's text, matched to the day and hour the review was posted."
      />

      <div class="topic-picker">
        <span class="topic-picker-label">Show when reviews mention:</span>
        <button
          v-for="t in topics"
          :key="t.id"
          type="button"
          class="topic-chip"
          :class="{ active: topic === t.id }"
          @click="topic = t.id"
        >{{ t.label }}</button>
      </div>
      <p v-if="busiestSlot" class="topic-busiest">
        Most reviews mentioning <strong>{{ topicLabel.toLowerCase() }}</strong> were posted {{ busiestSlot.day }} {{ busiestSlot.hour }} ({{ busiestSlot.n }}).
      </p>
      <p v-else class="topic-busiest">No reviews in these time slots mention {{ topicLabel.toLowerCase() }}.</p>

      <div class="heatmap-legend">
        <span v-for="(tier, i) in result.dominant_tiers" :key="tier">
          <span class="swatch" :style="{ background: TIER_COLORS[i] }"></span>
          {{ tier }}★ (Dominant #{{ i + 1 }})
        </span>
      </div>
      <p class="mention-key">
        <span class="mention-key-badge">💬 2</span>
        A speech bubble means reviews posted in that day and time <strong>mention the topic picked above</strong>
        (waiting, by default: “long wait”, “took forever”). The number is how many. Hover a box to see which reviews.
      </p>

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
            <span v-if="countFor(cellFor(day, hour))" class="heatmap-mention">💬 {{ countFor(cellFor(day, hour)) }}</span>
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
    <p v-else-if="result" class="status">
      No Google reviews are in this view, and time of day uses Google reviews. Switch the view
      to Combined or Google above to see it.
    </p>
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
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
  padding: 2px 4px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.92);
  color: #333;
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.25);
}
.topic-picker { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; margin: 10px 0 4px; }
.topic-picker-label { font-size: 0.9rem; font-weight: 600; margin-right: 4px; }
.topic-chip {
  border: 1px solid rgba(128, 128, 128, 0.5);
  background: transparent;
  color: inherit;
  border-radius: 999px;
  padding: 3px 10px;
  font-size: 0.85rem;
  cursor: pointer;
}
.topic-chip.active { background: #2563eb; border-color: #2563eb; color: #fff; }
.topic-busiest { margin: 4px 0 8px; font-size: 0.9rem; }
.mention-key {
  margin: 8px 0 12px;
  font-size: 0.9rem;
  line-height: 1.5;
}
.mention-key-badge {
  display: inline-block;
  padding: 1px 6px;
  margin-right: 6px;
  border-radius: 8px;
  font-weight: 700;
  background: rgba(255, 255, 255, 0.92);
  color: #333;
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.25);
}
</style>
