<script setup>
import { computed } from 'vue'
import DataBasis from './DataBasis.vue'

const props = defineProps({
  result: { type: Object, default: null },
  meta: { type: Object, default: null },
})

const isPreview = computed(() => props.result?.preview === true)

const ICONS = { warning: '⚠️', opportunity: '💡', positive: '✅' }
const BASIS = { all: 'All reviews', written: 'Written reviews', both: 'All + written reviews', web: 'Web mentions' }
</script>

<template>
  <section class="chart-section">
    <div class="title-row">
      <h3>💡 Revenue Signals</h3>
      <span class="nlp-badge">🧠 NLP + star ratings</span>
      <span v-if="isPreview" class="trend-preview-tag">Free preview</span>
      <DataBasis :meta="meta" uses="both" />
    </div>
    <p class="chart-desc">
      Plain-English signals from <strong>all</strong> your reviews, written and star-only, ranked
      by how much they appear to be costing or earning you. Star ratings, review pace and
      time-of-day use every review; topics come from the written ones. These point to likely
      causes. They don't measure revenue, which this app can't see.
    </p>

    <p v-if="!result" class="status">Run analysis above to see your signals.</p>

    <p v-else-if="result.status === 'insufficient_data'" class="status">{{ result.message }}</p>

    <template v-else>
      <div v-if="isPreview" class="trend-preview-note">
        You're seeing the top {{ result.signals.length }} signals<span v-if="result.hidden">
          ({{ result.hidden }} more are hidden)</span>.
        <router-link :to="{ path: '/', hash: '#pricing' }" class="trend-upgrade-link">See Pro plans</router-link>
      </div>

      <p v-if="!result.signals.length" class="status">
        Nothing stands out in this window: no significant shifts or patterns found.
      </p>

      <div
        v-for="(s, i) in result.signals"
        :key="i"
        class="signal-card"
        :class="`signal-${s.type}`"
      >
        <div class="signal-head">
          <span class="signal-icon">{{ ICONS[s.type] }}</span>
          <strong>{{ s.title }}</strong>
        </div>
        <p class="signal-detail">{{ s.detail }}</p>
        <p class="signal-action"><strong>What to check:</strong> {{ s.action }}</p>
        <span class="signal-basis">{{ BASIS[s.basis] }}</span>
      </div>
    </template>
  </section>
</template>

<style>
.signal-card {
  border: 1px solid #e4e6ea;
  border-left-width: 5px;
  border-radius: 10px;
  padding: 12px 16px;
  margin-bottom: 10px;
  background: white;
  font-size: 13px;
}

.signal-warning { border-left-color: #e67e22; background: #fffaf3; }
.signal-opportunity { border-left-color: #7c5ce0; background: #faf8ff; }
.signal-positive { border-left-color: #2ecc71; background: #f5fcf8; }

.signal-head {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 14px;
}

.signal-detail {
  margin: 6px 0;
  color: #444;
  line-height: 1.5;
}

.signal-action {
  margin: 6px 0 8px;
  color: #444;
}

.signal-basis {
  display: inline-block;
  font-size: 11px;
  color: #666;
  background: #eef0f3;
  border-radius: 999px;
  padding: 2px 9px;
}
</style>
