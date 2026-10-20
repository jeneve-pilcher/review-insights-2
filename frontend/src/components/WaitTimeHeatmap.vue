<script setup>
import { computed, ref } from 'vue'
import DataBasis from './DataBasis.vue'
import NlpCallout from './NlpCallout.vue'
import { heatmapReadItems } from '../utils/nlpInsights'

// Every star rating, best to worst, as its real share of the reviews posted in a slot.
const STARS = [5, 4, 3, 2, 1]
const STAR_COLORS = { 5: '#2ecc71', 4: '#a3d977', 3: '#f1c40f', 2: '#e67e22', 1: '#e74c3c' }

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

// Reviews behind the picked topic, newest first; click a box to narrow to that day and time.
const slot = ref(null)
function pickSlot(day, hour) {
  const same = slot.value && slot.value.day === day && slot.value.hour === hour
  slot.value = same || !countFor(cellFor(day, hour)) ? null : { day, hour }
}
const topicReviews = computed(() => {
  const out = []
  for (const c of props.result?.matrix || []) {
    if (slot.value && (c.day !== slot.value.day || c.hour !== slot.value.hour)) continue
    for (const r of c.reviews || []) {
      if ((r.topics || []).includes(topic.value)) out.push({ ...r, day: c.day, hour: c.hour })
    }
  }
  return out.sort((a, b) => String(b.review_date).localeCompare(String(a.review_date)))
})
const shownReviews = computed(() => topicReviews.value.slice(0, 30))
function when(d) { try { return new Date(d).toLocaleDateString() } catch { return '' } }

function cellTitle(day, hour) {
  const cell = cellFor(day, hour)
  const mentions = countFor(cell)
  const base = `${day} ${hour}`
  const stars = cell?.review_count
    ? `\n${cell.review_count} review${cell.review_count === 1 ? '' : 's'}: ${STARS.map((s) => `${s}★ ${cell.star_pct?.[s] ?? 0}% (${cell.star_counts?.[s] ?? 0})`).join(' · ')}`
    : '\nNo reviews posted in this slot'
  const talk = mentions ? `\n${mentions} review(s) mention ${topicLabel.value.toLowerCase()}` : ''
  return base + stars + talk
}

</script>

<template>
  <section class="chart-section">
    <div class="title-row">
      <h3>🔥 Wait-Time and Topic Heatmap</h3>
      <DataBasis :meta="meta" uses="both" />
    </div>
    <p class="chart-desc">
      Maps the day and hour reviews were posted. Each box is filled by the real share of every star rating (5★ to 1★) among the reviews posted in that slot, and hovering shows the exact percentages and counts. It also lets you see when reviews mention waiting or any of your industry's topics. Time of day uses Google
      reviews only, because other platforms may give just a date.
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
          @click="topic = t.id; slot = null"
        >{{ t.label }}</button>
      </div>
      <p v-if="busiestSlot" class="topic-busiest">
        Most reviews mentioning <strong>{{ topicLabel.toLowerCase() }}</strong> were posted {{ busiestSlot.day }} {{ busiestSlot.hour }} ({{ busiestSlot.n }}).
      </p>
      <p v-else class="topic-busiest">No reviews in these time slots mention {{ topicLabel.toLowerCase() }}.</p>

      <div class="heatmap-legend">
        <span v-for="s in STARS" :key="s">
          <span class="swatch" :style="{ background: STAR_COLORS[s] }"></span>
          {{ s }}★
        </span>
      </div>
      <p class="mention-key">
        <span class="mention-key-badge">💬 2</span>
        A speech bubble means reviews posted in that day and time <strong>mention the topic picked above</strong>
        (waiting, by default: “long wait”, “took forever”). The number is how many. Hover a box for its star percentages; click it to list those reviews below.
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
            :class="{ 'heatmap-picked': slot && slot.day === day && slot.hour === hour }"
            @click="pickSlot(day, hour)"
          >
            <template v-if="cellFor(day, hour)?.review_count">
              <div
                v-for="s in STARS"
                :key="s"
                class="heatmap-segment"
                :style="{
                  width: (cellFor(day, hour).star_pct?.[s] || 0) + '%',
                  background: STAR_COLORS[s],
                }"
              ></div>
            </template>
            <div v-else class="heatmap-empty">–</div>
            <span v-if="countFor(cellFor(day, hour))" class="heatmap-mention">💬 {{ countFor(cellFor(day, hour)) }}</span>
          </div>
        </div>
      </div>

      <div class="topic-reviews">
        <h4>
          Reviews that mention {{ topicLabel.toLowerCase() }}
          <span v-if="slot">— {{ slot.day }} {{ slot.hour }}</span>
          ({{ topicReviews.length }})
        </h4>
        <button v-if="slot" type="button" class="topic-chip" @click="slot = null">Show all times</button>
        <p v-if="!topicReviews.length" class="status">None in {{ slot ? 'this slot' : 'these time slots' }}. Click a box with a 💬 to see just that time.</p>
        <ul v-else class="topic-review-list">
          <li v-for="(r, i) in shownReviews" :key="i">
            <div class="topic-review-meta">
              {{ r.rating }}★ · {{ r.day }} {{ r.hour }} · {{ when(r.review_date) }}
            </div>
            <div>{{ r.text }}</div>
          </li>
        </ul>
        <p v-if="topicReviews.length > shownReviews.length" class="status">Showing the newest {{ shownReviews.length }} of {{ topicReviews.length }}.</p>
      </div>

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
.heatmap-cell { cursor: pointer; }
.heatmap-picked { outline: 2px solid #2563eb; outline-offset: -2px; }
.topic-reviews { margin: 14px 0; }
.topic-review-list { list-style: none; padding: 0; margin: 8px 0; display: grid; gap: 8px; }
.topic-review-list li { border: 1px solid rgba(128, 128, 128, 0.35); border-radius: 8px; padding: 8px 10px; font-size: 0.9rem; line-height: 1.45; }
.topic-review-meta { font-size: 0.8rem; opacity: 0.75; margin-bottom: 2px; }
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
