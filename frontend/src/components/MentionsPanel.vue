<script setup>
import { computed, ref } from 'vue'
import { CATEGORY_LABELS, toneClass, toneLabel } from '../utils/mentions'

const props = defineProps({
  result: { type: Object, default: null },
})

const PAGE = 8
const shownCount = ref(PAGE)
const items = computed(() => props.result?.items ?? [])
const shown = computed(() => items.value.slice(0, shownCount.value))
</script>

<template>
  <section class="chart-section">
    <div class="title-row">
      <h3>🌐 Internet mentions</h3>
      <span class="nlp-badge">🧠 NLP</span>
      <span class="data-basis">Web search results (news, blogs, forums, social), not review sites</span>
    </div>
    <p class="chart-desc">
      What the open web says about your business beyond Google and Yelp reviews. Each mention's tone is
      scored from its search-result headline and snippet, and complaints rising in your reviews are
      checked against what shows up here. <em>Snippets are short and Google's results aren't
      exhaustive (posts on Facebook or Instagram rarely appear), so read the pages before acting.</em>
    </p>

    <p v-if="!result" class="status">
      Optional: tick "Include internet mentions" in Run Analysis above. It runs two extra web searches.
    </p>

    <template v-else>
      <p v-for="n in result.notes ?? []" :key="n" class="status analysis-note">ℹ️ {{ n }}</p>
      <p v-if="result.status === 'unavailable'" class="status error">
        Internet mentions couldn't be loaded this time. Your review analysis is unaffected.
      </p>
      <p v-else-if="result.status === 'no_results'" class="status">
        No relevant mentions found for “{{ result.terms }}”. Try different search words in Run Analysis
        (a business name plus city works best).<span v-if="result.dropped"> {{ result.dropped }} unrelated result(s) were ignored.</span>
      </p>

      <template v-else>
        <div class="oc-grid">
          <div class="oc-card oc-stat">
            <span class="label">Mentions found</span>
            <span class="value">{{ result.summary.count }}</span>
            <span class="sub">searching “{{ result.terms }}”</span>
          </div>
          <div class="oc-card oc-stat">
            <span class="label">Overall tone</span>
            <span class="value" :class="toneClass(result.summary.avg_sentiment)">{{ toneLabel(result.summary.avg_sentiment) }}</span>
            <span class="sub">{{ result.summary.positive_count }} positive · {{ result.summary.negative_count }} negative</span>
          </div>
          <div class="oc-card oc-stat">
            <span class="label">Where</span>
            <span class="sub" style="font-size: 12px; margin-top: 4px">
              <span v-for="(n, cat) in result.summary.by_category" :key="cat" class="oc-chip">{{ CATEGORY_LABELS[cat] ?? cat }} {{ n }}</span>
            </span>
          </div>
        </div>

        <div v-if="result.topic_overlap.length" class="platform-mix-warning">
          ⚠️ Complaints rising in your reviews also show up on the web:
          <span v-for="o in result.topic_overlap" :key="o.term" class="oc-chip warn">“{{ o.term }}” in {{ o.mentions }} mention{{ o.mentions === 1 ? '' : 's' }}</span>
        </div>

        <div v-for="m in shown" :key="m.url" class="mn-item">
          <div class="mn-head">
            <span class="oc-chip">{{ m.domain }}</span>
            <span class="oc-chip">{{ CATEGORY_LABELS[m.category] ?? m.category }}</span>
            <span class="oc-note" style="margin: 0">{{ m.date ? String(m.date).slice(0, 10) : 'no date' }}</span>
            <span class="mn-tone" :class="toneClass(m.sentiment)">{{ toneLabel(m.sentiment) }}</span>
          </div>
          <a :href="m.url" target="_blank" rel="noopener noreferrer" class="mn-title">{{ m.title || m.url }}</a>
          <p v-if="m.snippet" class="mn-snippet">{{ m.snippet }}</p>
        </div>

        <button v-if="items.length > shownCount" class="oc-btn" @click="shownCount += PAGE">
          Show {{ Math.min(PAGE, items.length - shownCount) }} more
        </button>
        <p v-if="result.dropped" class="oc-note">{{ result.dropped }} unrelated result(s) were ignored.</p>
      </template>
    </template>
  </section>
</template>

<style>
.mn-item {
  border: 1px solid #e4e6ea;
  border-radius: 10px;
  padding: 10px 14px;
  margin-bottom: 8px;
  background: white;
}

.mn-head {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 4px;
}

.mn-title {
  font-weight: 600;
  font-size: 14px;
  color: #1a5f9e;
  text-decoration: none;
}

.mn-title:hover {
  text-decoration: underline;
}

.mn-snippet {
  margin: 4px 0 0;
  font-size: 13px;
  color: #444;
  line-height: 1.45;
}

.mn-tone {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 9px;
  border-radius: 999px;
  background: #eef0f3;
}

.mn-tone.mn-good, .value.mn-good { color: #1e8e4e; }
.mn-tone.mn-bad, .value.mn-bad { color: #c0392b; }
.mn-tone.mn-ok, .value.mn-ok { color: #8a6200; }
</style>
