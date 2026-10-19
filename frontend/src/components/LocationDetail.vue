<script setup>
import { computed, onMounted, ref } from 'vue'
import { orgApi } from '../api'
import { MAX_MONTHS, parseMonths } from '../utils/months'
import { ratingClass, signed, sparkline, timeAgo } from '../utils/orgFormat'
import MentionsPanel from './MentionsPanel.vue'
import NegativeReviewAlerts from './NegativeReviewAlerts.vue'
import PlatformComparison from './PlatformComparison.vue'
import ReviewReplies from './ReviewReplies.vue'
import RevenueSignals from './RevenueSignals.vue'
import SentimentDriftChart from './SentimentDriftChart.vue'
import IndustryPanel from './IndustryPanel.vue'
import AiSummary from './AiSummary.vue'
import { FEATURES } from '../content/features'
import LocationProviders from './LocationProviders.vue'
import TrendsPanel from './TrendsPanel.vue'
import WaitTimeHeatmap from './WaitTimeHeatmap.vue'
import WeeklyThemesChart from './WeeklyThemesChart.vue'
import ToneVsStarsChart from './ToneVsStarsChart.vue'

const props = defineProps({
  locationId: { type: String, required: true },
  info: { type: Object, default: null },
  embedded: { type: Boolean, default: false },   // shown on the main dashboard: no "back to all locations" button
})
const repliesOff = computed(() => props.info?.org?.pack?.replies_allowed === false)
const providersOn = computed(() => Boolean(props.info?.org?.provider_data_enabled && props.info?.org?.pack?.provider_level))
const emit = defineEmits(['back', 'changed'])

const loc = ref(null)
const history = ref([])
const analysis = ref(null)
const loading = ref(true)
const error = ref('')

const monthsText = ref('6')
const monthsCheck = computed(() => parseMonths(monthsText.value))
const includeMentions = ref(false)
const analyzing = ref(false)
const analysisError = ref('')

const running = ref(false)
const runMessage = ref('')

async function loadBasics() {
  try {
    const [locs, hist] = await Promise.all([orgApi.locations(), orgApi.history(props.locationId)])
    loc.value = locs.find((l) => l.id === props.locationId) || null
    history.value = hist
    if (!loc.value) error.value = 'Location not found.'
  } catch (err) {
    error.value = err?.response?.data?.detail || 'Could not load this location.'
  } finally {
    loading.value = false
  }
}

onMounted(loadBasics)

const ratings = computed(() => history.value.map((h) => h.avg_rating))
const spark = computed(() => sparkline(ratings.value))
const recentHistory = computed(() => [...history.value].reverse().slice(0, 8))
const snap = computed(() => loc.value?.snapshot ?? null)
const change = computed(() =>
  snap.value && snap.value.avg_rating != null && snap.value.prev_avg_rating != null
    ? Math.round((snap.value.avg_rating - snap.value.prev_avg_rating) * 100) / 100
    : null
)

async function analyze(view = 'combined') {
  if (!monthsCheck.value.valid) {
    analysisError.value = monthsCheck.value.message
    return
  }
  analyzing.value = true
  analysisError.value = ''
  try {
    analysis.value = await orgApi.analysis(props.locationId, monthsCheck.value.value, view, FEATURES.internetMentions && includeMentions.value)
    emit('changed')
  } catch (err) {
    analysisError.value = err?.response?.data?.detail || 'The analysis failed.'
  } finally {
    analyzing.value = false
  }
}

async function runNow() {
  running.value = true
  runMessage.value = ''
  try {
    const res = await orgApi.runLocation(props.locationId)
    runMessage.value =
      `Checked. ${res.new_alerts} new negative review${res.new_alerts === 1 ? '' : 's'}` +
      `${res.emailed ? ' (manager emailed)' : ''}; ${res.fresh_reviews} reviews bought.`
    await loadBasics()
    emit('changed')
  } catch (err) {
    runMessage.value = err?.response?.data?.detail || 'The check failed.'
  } finally {
    running.value = false
  }
}

const VIEW_LABELS = { combined: 'Combined', google: 'Google', yelp: 'Yelp', opentable: 'OpenTable', doordash: 'DoorDash', grubhub: 'Grubhub' }
const viewChoices = computed(() => (analysis.value && analysis.value.meta.sources.length > 1 ? ['combined', ...analysis.value.meta.sources] : []))
</script>

<template>
  <div>
    <button v-if="!embedded" class="oc-btn" style="margin-bottom: 12px" @click="emit('back')">← Back to all locations</button>

    <p v-if="loading" class="status">Loading…</p>
    <p v-else-if="error" class="status error">{{ error }}</p>

    <template v-else-if="loc">
      <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px; align-items: center">
        <div>
          <h3 style="margin: 0">{{ loc.name }}</h3>
          <div class="oc-note" style="margin: 2px 0">
            {{ [loc.brand, loc.region].filter(Boolean).join(' · ') }}
            <span v-if="loc.manager_email"> · manager {{ loc.manager_email }}</span>
          </div>
        </div>
        <button class="oc-btn" :disabled="running" @click="runNow">{{ running ? 'Checking…' : 'Run check now' }}</button>
      </div>
      <p v-if="runMessage" class="status analysis-note">{{ runMessage }}</p>

      <div v-if="snap" class="oc-grid" style="margin-top: 12px">
        <div class="oc-card oc-stat">
          <span class="label">Rating</span>
          <span class="value" :class="ratingClass(snap.avg_rating)">{{ snap.avg_rating }}★</span>
          <span class="sub"><span v-if="change != null">{{ signed(change) }} since last check · </span>checked {{ timeAgo(snap.run_at) }}</span>
        </div>
        <div class="oc-card oc-stat">
          <span class="label">Reviews</span>
          <span class="value">{{ snap.reviews_total }}</span>
          <span class="sub">Google {{ snap.reviews_google }}<span v-if="snap.reviews_yelp"> · Yelp {{ snap.reviews_yelp }}</span></span>
        </div>
        <div class="oc-card oc-stat">
          <span class="label">1–2★ share</span>
          <span class="value">{{ snap.low_star_pct ?? '–' }}%</span>
        </div>
        <div class="oc-card oc-stat">
          <span class="label">Open tasks</span>
          <span class="value">{{ loc.open_alerts }}</span>
        </div>
      </div>
      <p v-else class="status">No check has run for this location yet. Press "Run check now".</p>

      <div v-if="history.length > 1" class="oc-card" style="margin: 14px 0">
        <strong>Rating over time</strong>
        <svg v-if="spark" viewBox="0 0 240 48" width="240" height="48" style="display: block; margin-top: 6px">
          <polyline :points="spark" fill="none" style="stroke: var(--accent, #7c5ce0)" stroke-width="2" />
        </svg>
        <div class="oc-scroll">
          <table class="oc-table" style="margin-top: 8px">
            <thead><tr><th>Checked</th><th>Rating</th><th>Reviews</th><th>1–2★</th><th>Reviews/wk</th></tr></thead>
            <tbody>
              <tr v-for="h in recentHistory" :key="h.run_at">
                <td>{{ timeAgo(h.run_at) }}</td>
                <td :class="ratingClass(h.avg_rating)">{{ h.avg_rating }}</td>
                <td>{{ h.reviews_total }}</td>
                <td>{{ h.low_star_pct ?? '–' }}%</td>
                <td>{{ h.recent_per_week ?? '–' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <section class="chart-section">
        <h3>🔎 Full analysis</h3>
        <p class="chart-desc">
          Every panel for this location: signals, reviews with draft replies, language analysis,
          the wait-time heatmap, and optionally internet mentions. It pulls this location's reviews
          now, which is paid from your company credit and counts toward your monthly spending limit, if you set one (repeat pulls inside 30 minutes are free).
        </p>
        <div class="analysis-form">
          <label class="field">
            <span>Analyze the last (months)</span>
            <input
              v-model="monthsText"
              class="months-input"
              :class="{ invalid: !monthsCheck.valid }"
              type="number"
              min="1"
              :max="MAX_MONTHS"
              step="1"
              required
            />
          </label>
          <label v-if="FEATURES.internetMentions" class="source-check" style="align-self: flex-end; margin-bottom: 8px">
            <input v-model="includeMentions" type="checkbox" /> Include internet mentions
          </label>
          <button class="run-btn" :disabled="analyzing" @click="analyze('combined')">
            {{ analyzing ? 'Analyzing…' : 'Load full analysis' }}
          </button>
        </div>
        <p v-if="!monthsCheck.valid" class="status error">{{ monthsCheck.message }}</p>
        <p v-if="analysisError && monthsCheck.valid" class="status error">{{ analysisError }}</p>

        <div v-if="viewChoices.length" class="view-switch" style="margin-top: 10px">
          <span class="view-switch-label">View:</span>
          <button
            v-for="v in viewChoices"
            :key="v"
            class="view-btn"
            :class="{ active: analysis.meta.view === v }"
            @click="analyze(v)"
          >
            {{ VIEW_LABELS[v] ?? v }}
          </button>
        </div>
      </section>

      <template v-if="analysis">
        <p v-for="note in analysis.meta.notes" :key="note" class="status analysis-note">ℹ️ {{ note }}</p>
        <ReviewReplies
          :review-list="analysis.review_list"
          :location-id="loc.id"
          :business-location="loc.google_query"
          :yelp-url="loc.yelp_url"
          :opentable-url="loc.opentable_url"
          :doordash-url="loc.doordash_url"
          :grubhub-url="loc.grubhub_url"
          :replies-off="repliesOff"
        />
        <AiSummary v-if="FEATURES.aiSummaries" :result="analysis.ai_summary" />
        <RevenueSignals :result="analysis.signals" :meta="analysis.meta" />
        <PlatformComparison v-if="(analysis.platforms?.platforms?.length ?? 0) > 1" :result="analysis.platforms" />
        <SentimentDriftChart :result="analysis.sentiment_drift" :meta="analysis.meta" />
        <WeeklyThemesChart :weekly="analysis.sentiment_drift?.weekly ?? []" :meta="analysis.meta" />
        <ToneVsStarsChart :weekly="analysis.sentiment_drift?.weekly ?? []" :meta="analysis.meta" />
        <TrendsPanel :result="analysis.trends" :meta="analysis.meta" />
        <IndustryPanel :result="analysis.industry" :meta="analysis.meta" />
        <LocationProviders v-if="providersOn" :location-id="loc.id" />
        <MentionsPanel v-if="FEATURES.internetMentions && analysis.mentions" :result="analysis.mentions" />
        <WaitTimeHeatmap :result="analysis.wait_time_heatmap" :meta="analysis.meta" />
        <NegativeReviewAlerts :business-location="loc.name" :result="analysis.negative_reviews" :meta="analysis.meta" />
      </template>
    </template>
  </div>
</template>
