<script setup>
import { defaultStats } from '../content/defaultStats'
import { pickStats, safeUrl } from '../utils/statsSource'

// The statistics strip on the front page. It shows your own content/stats.js if you have one (a file updates never
// overwrite); otherwise it shows the default statistics, so the strip is never missing.
const files = import.meta.glob('../content/stats.js', { eager: true })
const items = pickStats(Object.values(files)[0], defaultStats)
</script>

<template>
  <section v-if="items.length" class="stats-strip" aria-label="Why reviews matter">
    <div v-for="s in items" :key="s.value + s.label" class="stat-card">
      <span class="stat-value">{{ s.value }}</span>
      <span class="stat-label">{{ s.label }}</span>
      <span v-if="s.source" class="stat-source">
        <a v-if="safeUrl(s.url)" :href="safeUrl(s.url)" target="_blank" rel="noopener noreferrer">{{ s.source }}</a>
        <template v-else>{{ s.source }}</template>
      </span>
    </div>
  </section>
</template>

<style>
.stats-strip {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 16px;
  padding: 8px 20px 28px;
  max-width: 1000px;
  margin: 0 auto;
}

.stat-card {
  flex: 1 1 170px;
  background: white;
  border: 1px solid #e4e6ea;
  border-radius: 12px;
  padding: 18px 20px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-value {
  font-size: 34px;
  font-weight: 700;
  color: var(--brand, #ff4b4b);
  line-height: 1.1;
}

.stat-label {
  font-size: 14px;
  color: #333;
}

.stat-source,
.stat-source a {
  font-size: 11px;
  color: #888;
}

.stat-source a:hover {
  text-decoration: underline;
}
</style>
