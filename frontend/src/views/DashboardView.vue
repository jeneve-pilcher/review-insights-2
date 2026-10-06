<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import CompetitorShareChart from '../components/CompetitorShareChart.vue'
import LockedPanel from '../components/LockedPanel.vue'
import NegativeReviewAlerts from '../components/NegativeReviewAlerts.vue'
import RevenueSignals from '../components/RevenueSignals.vue'
import SentimentDriftChart from '../components/SentimentDriftChart.vue'
import SetBusinessLocation from '../components/SetBusinessLocation.vue'
import TrendsPanel from '../components/TrendsPanel.vue'
import UnifiedAnalysisForm from '../components/UnifiedAnalysisForm.vue'
import WaitTimeHeatmap from '../components/WaitTimeHeatmap.vue'
import WeeklyThemesChart from '../components/WeeklyThemesChart.vue'
import { createCheckoutSession, createPortalSession, deleteAccount, fetchMe } from '../api'
import { supabase } from '../supabase'
import { heatmapReadItems, negativeReadItems } from '../utils/nlpInsights'

const router = useRouter()
const route = useRoute()

const me = ref(null)
const loadingMe = ref(true)

// The "last X months" window - shared by Run Analysis and the competitor chart.
const months = ref(6)

const sentimentResult = ref(null)
const waitTimeResult = ref(null)
const negativeResult = ref(null)
const trendsResult = ref(null)
const signalsResult = ref(null)
const competitorsResult = ref(null)
const waitTimePreview = ref(null)
const negativePreview = ref(null)
const meta = ref(null)

// Free-tier teasers: a real finding from the user's own reviews.
const waitPreviewItems = computed(() => heatmapReadItems(waitTimePreview.value))
const negativePreviewItems = computed(() => negativeReadItems(negativePreview.value))

async function loadMe() {
  loadingMe.value = true
  try {
    me.value = await fetchMe()
  } catch {
    me.value = null
  } finally {
    loadingMe.value = false
  }
}

onMounted(loadMe)

function handleLocationSet(location) {
  me.value = { ...me.value, business_location: location }
}

async function handleLogout() {
  await supabase.auth.signOut()
  router.push('/login')
}

async function handleUpgrade() {
  try {
    const { checkout_url } = await createCheckoutSession()
    window.location.href = checkout_url
  } catch (err) {
    alert(err?.response?.data?.detail || 'Could not start checkout.')
  }
}

async function handleManageSubscription() {
  try {
    const { portal_url } = await createPortalSession()
    window.location.href = portal_url
  } catch (err) {
    alert(err?.response?.data?.detail || 'Could not open the billing portal.')
  }
}

const isPaid = () => me.value && ['pro', 'enterprise'].includes(me.value.tier)

async function handleDeleteAccount() {
  const confirmed = window.confirm(
    'Delete your account permanently? This cancels any active subscription and cannot be undone.'
  )
  if (!confirmed) return

  try {
    await deleteAccount()
    await supabase.auth.signOut()
    router.push('/')
  } catch (err) {
    alert(err?.response?.data?.detail || 'Could not delete your account. Please try again.')
  }
}

function handleUnifiedResult({ data }) {
  sentimentResult.value = data.sentiment_drift
  waitTimeResult.value = data.wait_time_heatmap
  negativeResult.value = data.negative_reviews
  trendsResult.value = data.trends
  signalsResult.value = data.signals
  competitorsResult.value = data.competitors
  waitTimePreview.value = data.wait_time_preview
  negativePreview.value = data.negative_preview
  meta.value = data.meta
}
</script>

<template>
  <div class="dashboard">
    <div class="topbar">
      <h1>📊 Review Insights</h1>
      <div class="user-info" v-if="me">
        <span>{{ me.email }}</span>
        <span class="tier-badge" :class="me.tier">{{ me.tier }}</span>
        <button v-if="isPaid()" class="logout-btn" @click="handleManageSubscription">Manage subscription</button>
        <button v-else class="logout-btn" @click="handleUpgrade">Upgrade</button>
        <button class="logout-btn" @click="handleLogout">Log out</button>
        <button class="logout-btn danger-btn" @click="handleDeleteAccount">Delete account</button>
      </div>
    </div>

    <p v-if="route.query.checkout === 'success'" class="status" style="color: #2ecc71">
      🎉 Subscription active — thanks for upgrading!
    </p>

    <p v-if="loadingMe" class="status">Loading account…</p>

    <template v-else-if="me && !me.business_location">
      <SetBusinessLocation @set="handleLocationSet" />
    </template>

    <template v-else-if="me">
      <div class="nlp-intro">
        <span class="nlp-badge">🧠 NLP</span>
        <span>
          <strong>Every panel reads the words in your reviews, not just the stars.</strong>
          Look for the purple <em>Language read</em> boxes: plain-English findings from natural
          language processing (sentiment scoring, phrase detection, topic extraction).
        </span>
      </div>

      <UnifiedAnalysisForm
        v-model:months="months"
        :business-location="me.business_location"
        :show-revenue-inputs="isPaid()"
        :show-competitors="isPaid()"
        @result="handleUnifiedResult"
      />

      <p v-if="meta" class="status analysis-meta">
        Analyzed <strong>{{ meta.reviews_analyzed }}</strong> reviews
        ({{ meta.reviews_with_text }} with written text) from the last
        {{ meta.months }} {{ meta.months === 1 ? 'month' : 'months' }} · most recent review:
        <strong>{{ meta.latest_review_date ?? 'n/a' }}</strong>
        <span v-if="meta.from_cache"> · reused a recent pull (no new scraping charge)</span>
      </p>
      <p v-if="meta && meta.reviews_analyzed === 0" class="status error">
        No reviews were found in this window. Try a longer time window, or double-check your
        business location.
      </p>
      <p v-else-if="meta && meta.reviews_with_text === 0" class="status error">
        These reviews are star ratings only, so counts and ratings are shown but the language
        panels have no words to read. Try a longer time window.
      </p>

      <RevenueSignals :result="signalsResult" :meta="meta" />
      <SentimentDriftChart :result="sentimentResult" :meta="meta" />
      <WeeklyThemesChart :weekly="sentimentResult?.weekly ?? []" :meta="meta" />
      <TrendsPanel :result="trendsResult" :meta="meta" />

      <template v-if="isPaid()">
        <WaitTimeHeatmap :result="waitTimeResult" :meta="meta" />
        <NegativeReviewAlerts :business-location="me.business_location" :result="negativeResult" :meta="meta" />
        <CompetitorShareChart
          :business-location="me.business_location"
          :result="competitorsResult"
          :months="months"
        />
      </template>
      <template v-else>
        <LockedPanel
          title="🔥 Wait-Time Revenue Leak Heatmap"
          chart-name="Wait-Time Revenue Heatmap"
          :preview-items="waitPreviewItems"
          technique="Phrase detection (“long wait”, “slow service”, “took forever” and similar) on each review's text, matched to the day and hour it was posted."
        />
        <LockedPanel
          title="🚨 Negative Review Alerts"
          chart-name="Negative Review Alerts"
          :preview-items="negativePreviewItems"
          technique="Sentiment scoring, topic extraction across negative reviews, and automatic removal of emails, phone numbers and order numbers."
        />
        <LockedPanel
          title="🏁 Competitor Semantic Share Matrix"
          chart-name="Competitor Semantic Share Matrix"
          technique="A zero-shot language model classifies each written review into themes (quality, pricing, weekend communication, staff) with no keyword lists."
        />
      </template>
    </template>
  </div>
</template>

<style>
.analysis-meta {
  background: #f0f9ff;
  border: 1px solid #cfe8fb;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 13px;
  margin-bottom: 20px;
}

.nlp-intro {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  background: #faf8ff;
  border: 1px solid #e4defa;
  border-radius: 10px;
  padding: 12px 16px;
  font-size: 13px;
  line-height: 1.5;
  margin-bottom: 20px;
}

.nlp-intro .nlp-badge {
  margin-top: 2px;
  flex-shrink: 0;
}
</style>
