<script setup>
import { computed } from 'vue'
import DataBasis from './DataBasis.vue'

const props = defineProps({
  result: { type: Object, default: null },
  meta: { type: Object, default: null },
})

const ok = computed(() => props.result?.status === 'ok')
const isPreview = computed(() => props.result?.preview === true)
const hiddenTotal = computed(() => {
  const h = props.result?.hidden
  return h ? (h.rising ?? 0) + (h.fading ?? 0) : 0
})

function arrow(trend) {
  if (!trend || trend.direction === 'flat') return '→'
  return trend.direction === 'up' ? '▲' : '▼'
}

function trendClass(trend) {
  if (!trend || trend.direction === 'flat') return 'trend-flat'
  return trend.direction === 'up' ? 'trend-up' : 'trend-down'
}

function fmt(n, digits = 2) {
  return typeof n === 'number' ? n.toFixed(digits) : '–'
}

function signed(n, digits = 2) {
  if (typeof n !== 'number') return '–'
  return (n > 0 ? '+' : '') + n.toFixed(digits)
}
</script>

<template>
  <section class="chart-section">
    <div class="title-row">
      <h3>🧠 Emerging Topic Trends</h3>
      <span class="nlp-badge">🧠 NLP</span>
      <span v-if="isPreview" class="trend-preview-tag">Free preview</span>
      <DataBasis :meta="meta" uses="both" />
    </div>
    <p class="chart-desc">
      Language analysis of review text: it compares the most recent third of your time window
      against the earlier period and surfaces phrases that are rising or fading in a
      statistically meaningful way (not just a one-off mention). Treat these as signals worth a
      look, not proof.
    </p>

    <p v-if="!result" class="status">Run analysis above to see trends.</p>

    <p v-else-if="result.status === 'insufficient_data'" class="status">
      {{ result.message }}
    </p>

    <template v-else-if="ok">
      <div v-if="isPreview" class="trend-preview-note">
        You're seeing a free preview: the top 3 rising and top 3 fading topics, without example
        quotes<span v-if="hiddenTotal"> ({{ hiddenTotal }} more topics are hidden)</span>.
        <router-link :to="{ path: '/', hash: '#pricing' }" class="trend-upgrade-link">See Pro plans</router-link>
      </div>

      <div v-if="result.insights.length" class="trend-insights">
        <div
          v-for="(insight, i) in result.insights"
          :key="i"
          class="trend-insight"
          :class="`trend-insight-${insight.type}`"
        >
          {{ insight.type === 'warning' ? '⚠️' : '✅' }} {{ insight.message }}
        </div>
      </div>
      <p v-else class="status">No significant shifts detected between the two periods.</p>

      <p class="nlp-technique" style="margin: -6px 0 16px">
        How it works: word and phrase frequency is compared between the two periods using a
        log-likelihood significance test; star and tone changes use a t-test.
      </p>

      <div class="trend-stats">
        <div class="trend-stat">
          <span class="label">Star rating (all reviews)</span>
          <span class="value" :class="trendClass(result.rating_trend)">
            {{ arrow(result.rating_trend) }} {{ fmt(result.rating_trend.baseline_mean) }} →
            {{ fmt(result.rating_trend.recent_mean) }}
          </span>
          <span class="sub">{{ signed(result.rating_trend.delta) }} ·
            {{ result.rating_trend.significant ? 'significant' : 'not significant' }}</span>
        </div>
        <div class="trend-stat">
          <span class="label">Review language (−1 to +1)</span>
          <span class="value" :class="trendClass(result.sentiment_trend)">
            {{ arrow(result.sentiment_trend) }} {{ fmt(result.sentiment_trend.baseline_mean) }} →
            {{ fmt(result.sentiment_trend.recent_mean) }}
          </span>
          <span class="sub">{{ signed(result.sentiment_trend.delta) }} ·
            {{ result.sentiment_trend.significant ? 'significant' : 'not significant' }}</span>
        </div>
        <div class="trend-stat">
          <span class="label">Periods compared</span>
          <span class="value trend-flat" style="font-size: 13px">
            Earlier: {{ result.windows.baseline.reviews }} written reviews<br />
            Recent: {{ result.windows.recent.reviews }} written reviews
          </span>
          <span class="sub">
            Recent period starts {{ result.windows.recent.start }}. Stars use all
            {{ (result.windows.baseline.all_reviews ?? 0) + (result.windows.recent.all_reviews ?? 0) }} reviews
          </span>
        </div>
      </div>

      <div class="trend-columns">
        <div class="trend-col">
          <h4>📈 Rising topics</h4>
          <p v-if="!result.rising.length" class="status">Nothing rising significantly.</p>
          <div v-for="t in result.rising" :key="t.term" class="trend-item" :class="`tone-${t.tone}`">
            <div class="trend-item-head">
              <strong>{{ t.term }}</strong>
              <span class="trend-item-nums">{{ t.baseline_pct }}% → {{ t.recent_pct }}% of reviews</span>
            </div>
            <div class="trend-item-sub">
              avg {{ fmt(t.avg_rating, 1) }}★ when mentioned · {{ t.tone }}
            </div>
            <div v-if="t.example" class="trend-item-example">“{{ t.example }}”</div>
          </div>
        </div>

        <div class="trend-col">
          <h4>📉 Fading topics</h4>
          <p v-if="!result.fading.length" class="status">Nothing fading significantly.</p>
          <div v-for="t in result.fading" :key="t.term" class="trend-item" :class="`tone-${t.tone}`">
            <div class="trend-item-head">
              <strong>{{ t.term }}</strong>
              <span class="trend-item-nums">{{ t.baseline_pct }}% → {{ t.recent_pct }}% of reviews</span>
            </div>
            <div class="trend-item-sub">
              avg {{ fmt(t.avg_rating, 1) }}★ when mentioned · {{ t.tone }}
            </div>
          </div>
        </div>
      </div>
    </template>
  </section>
</template>

<style>
.trend-insights {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 18px;
}

.trend-insight {
  font-size: 13px;
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid;
}

.trend-insight-warning {
  background: #fff8e6;
  border-color: #f2d98a;
}

.trend-insight-positive {
  background: #eafaf0;
  border-color: #b7e4c7;
}

.trend-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.trend-stat {
  background: #f7f8fa;
  border: 1px solid #e4e6ea;
  border-radius: 8px;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.trend-stat .label {
  font-size: 12px;
  color: #666;
}

.trend-stat .value {
  font-size: 17px;
  font-weight: 700;
}

.trend-stat .sub {
  font-size: 11px;
  color: #888;
}

.trend-up { color: #1e8e4e; }
.trend-down { color: #c0392b; }
.trend-flat { color: #444; }

.trend-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.trend-col h4 {
  margin: 0 0 10px;
  font-size: 14px;
}

.trend-item {
  border: 1px solid #e4e6ea;
  border-left-width: 4px;
  border-radius: 8px;
  padding: 10px 12px;
  margin-bottom: 8px;
  background: white;
  font-size: 13px;
}

.trend-item.tone-negative { border-left-color: #e74c3c; }
.trend-item.tone-positive { border-left-color: #2ecc71; }
.trend-item.tone-mixed { border-left-color: #f1c40f; }

.trend-item-head {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.trend-item-nums {
  color: #666;
  font-size: 12px;
  white-space: nowrap;
}

.trend-item-sub {
  font-size: 12px;
  color: #888;
  margin-top: 2px;
}

.trend-item-example {
  margin-top: 6px;
  font-size: 12px;
  color: #555;
  font-style: italic;
}

.trend-preview-tag {
  background: #e8f4fd;
  color: #1a6fa8;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 999px;
}

.trend-preview-note {
  background: #f0f7ff;
  border: 1px solid #cfe3f7;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 13px;
  margin-bottom: 16px;
}

.trend-upgrade-link {
  color: #ff4b4b;
  font-weight: 700;
  text-decoration: none;
  margin-left: 6px;
}

@media (max-width: 720px) {
  .trend-stats,
  .trend-columns {
    grid-template-columns: 1fr;
  }
}
</style>
