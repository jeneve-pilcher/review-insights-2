<script setup>
const props = defineProps({
  result: { type: Object, default: null },
})

const STAR_COLORS = { 5: '#2ecc71', 4: '#8bd96b', 3: '#f1c40f', 2: '#f39c12', 1: '#e74c3c' }

function starMix(platform) {
  if (!platform.reviews) return []
  return [5, 4, 3, 2, 1].map((star) => {
    const count = platform.star_counts?.[star] ?? 0
    return {
      star,
      count,
      pct: Math.round((1000 * count) / platform.reviews) / 10,
      color: STAR_COLORS[star],
    }
  })
}

function pace(platform) {
  if (platform.recent_per_week == null) return '–'
  const before = platform.earlier_per_week == null ? '–' : platform.earlier_per_week
  return `${platform.recent_per_week} / wk (was ${before})`
}
</script>

<template>
  <section class="chart-section">
    <div class="title-row">
      <h3>🏷️ Platform Comparison</h3>
      <span class="data-basis">Each platform on its own: counts, ratings and pace</span>
    </div>
    <p class="chart-desc">
      Your platforms side by side. Ratings aren't directly comparable across platforms because
      they attract different customers, so judge each one against its own past rather than
      against the other.
    </p>

    <p v-if="!result" class="status">Run analysis above to compare your platforms.</p>

    <template v-else>
      <div v-if="result.mix?.shifted" class="platform-mix-warning">
        ⚠️ {{ result.mix.message }}
      </div>

      <div class="platform-grid">
        <div v-for="p in result.platforms" :key="p.source" class="platform-card">
          <h4>{{ p.label }}</h4>

          <template v-if="p.reviews">
            <div class="platform-row"><span>Reviews</span><strong>{{ p.reviews }}</strong><em>{{ p.text_reviews }} written</em></div>
            <div class="platform-row"><span>Average rating</span><strong>{{ p.avg_rating }}★</strong></div>
            <div class="platform-row"><span>1–2★ share</span><strong>{{ p.low_star_pct }}%</strong></div>
            <div class="platform-row"><span>Review pace</span><strong>{{ pace(p) }}</strong></div>
            <div class="platform-row">
              <span>Last review</span>
              <strong>{{ p.days_since_last }} {{ p.days_since_last === 1 ? 'day' : 'days' }} ago</strong>
            </div>

            <div class="platform-mixbar">
              <div
                v-for="s in starMix(p)"
                :key="s.star"
                class="platform-mixseg"
                :style="{ width: s.pct + '%', background: s.color }"
                :title="`${s.star}★: ${s.count} reviews (${s.pct}%)`"
              ></div>
            </div>
          </template>
          <p v-else class="status">No {{ p.label }} reviews in this window.</p>
        </div>
      </div>
    </template>
  </section>
</template>

<style>
.platform-mix-warning {
  background: #fff8e6;
  border: 1px solid #f2d98a;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 13px;
  margin-bottom: 14px;
}

.platform-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 14px;
}

.platform-card {
  background: #f7f8fa;
  border: 1px solid #e4e6ea;
  border-radius: 10px;
  padding: 14px 16px;
}

.platform-card h4 {
  margin: 0 0 10px;
  font-size: 15px;
}

.platform-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
  font-size: 13px;
  padding: 4px 0;
  border-bottom: 1px solid #eceef1;
}

.platform-row span {
  flex: 1;
  color: #666;
}

.platform-row em {
  color: #888;
  font-size: 11px;
}

.platform-mixbar {
  display: flex;
  height: 12px;
  border-radius: 6px;
  overflow: hidden;
  background: #e4e6ea;
  margin-top: 12px;
}

.platform-mixseg {
  height: 100%;
}
</style>
