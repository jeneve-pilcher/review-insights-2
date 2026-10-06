<script setup>
import { computed } from 'vue'
import DataBasis from './DataBasis.vue'
import NlpCallout from './NlpCallout.vue'
import { negativeReadItems, signed } from '../utils/nlpInsights'

const props = defineProps({
  businessLocation: { type: String, required: true },
  // Comes from the same review pull as the charts above - no separate fetch.
  result: { type: Object, default: null },
  meta: { type: Object, default: null },
})

const readItems = computed(() => negativeReadItems(props.result?.summary))

// Only worth showing which platform a review came from when there's more than one.
const showSource = computed(() => (props.meta?.sources?.length ?? 0) > 1)
const SOURCE_LABELS = { google: 'Google', yelp: 'Yelp' }
</script>

<template>
  <section class="chart-section">
    <div class="title-row">
      <h3>🚨 Negative Review Alerts</h3>
      <span class="nlp-badge">🧠 NLP</span>
      <DataBasis :meta="meta" uses="both" />
    </div>
    <p class="chart-desc">
      Recent 1-2★ reviews for <strong>{{ businessLocation }}</strong> from the analysis window,
      so managers can respond fast. Star-only ratings with no comment are included, because they
      still pull your score down. Author names are removed, and review text is scrubbed of
      anything that looks like an email, phone number, or order number before it's shown here — a
      best-effort filter, not a guarantee. New negative reviews from the last 24 hours also
      trigger an email alert to your account email (once per review).
    </p>

    <template v-if="result">
      <NlpCallout
        :items="readItems"
        technique="Sentiment scoring on each review, topic extraction across all negative reviews, and automatic removal of emails, phone numbers and order numbers."
      />

      <p v-if="result.alert_sent" class="status" style="color: #e67e22">
        📧 Email alert sent — new negative review(s) in the last 24h.
      </p>

      <div v-if="result.negative_reviews.length" class="negative-review-list">
        <div v-for="(r, i) in result.negative_reviews" :key="i" class="negative-review-card">
          <div class="negative-review-header">
            <span class="negative-review-rating">{{ r.rating }}★</span>
            <span class="negative-review-meta">
              <span v-if="showSource" class="neg-source-chip">{{ SOURCE_LABELS[r.source] ?? r.source }}</span>
              <span
                v-if="r.has_text"
                class="neg-tone-pill"
                :title="'Language tone, -1 (very negative) to +1 (very positive)'"
              >
                tone {{ signed(r.sentiment) }}
              </span>
              <span class="negative-review-date">{{ r.review_date }}</span>
            </span>
          </div>
          <p v-if="r.has_text">{{ r.redacted_text }}</p>
          <p v-else class="neg-no-text">Star rating only, no written comment.</p>
          <div v-if="r.topics.length" class="neg-topics">
            <span class="neg-topics-label">Topics:</span>
            <span v-for="t in r.topics" :key="t" class="neg-topic-chip">{{ t }}</span>
          </div>
        </div>
      </div>
      <p v-else class="status">No negative reviews found in this window.</p>
      <p
        v-if="result.summary && result.summary.count > result.negative_reviews.length"
        class="status"
      >
        Showing the {{ result.negative_reviews.length }} most recent of
        {{ result.summary.count }} negative reviews.
      </p>
    </template>
    <p v-else class="status">Run analysis above to check for negative reviews.</p>
  </section>
</template>

<style>
.negative-review-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.neg-tone-pill {
  background: #fde8e6;
  color: #a93226;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 999px;
}

.neg-source-chip {
  background: #eef6ff;
  color: #1a5f9e;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 999px;
}

.neg-no-text {
  color: #888;
  font-style: italic;
}

.neg-topics {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.neg-topics-label {
  font-size: 11px;
  color: #888;
}

.neg-topic-chip {
  background: #efeaff;
  color: #5b3fc4;
  font-size: 11px;
  padding: 2px 9px;
  border-radius: 999px;
}
</style>
