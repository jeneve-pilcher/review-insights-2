<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import CompetitorShareChart from '../components/CompetitorShareChart.vue'
import LockedPanel from '../components/LockedPanel.vue'
import MentionsPanel from '../components/MentionsPanel.vue'
import NegativeReviewAlerts from '../components/NegativeReviewAlerts.vue'
import OrgConsole from '../components/OrgConsole.vue'
import PlatformComparison from '../components/PlatformComparison.vue'
import ReviewReplies from '../components/ReviewReplies.vue'
import RevenueSignals from '../components/RevenueSignals.vue'
import SentimentDriftChart from '../components/SentimentDriftChart.vue'
import SetBusinessLocation from '../components/SetBusinessLocation.vue'
import TermsGate from '../components/TermsGate.vue'
import TrendsPanel from '../components/TrendsPanel.vue'
import UnifiedAnalysisForm from '../components/UnifiedAnalysisForm.vue'
import WaitTimeHeatmap from '../components/WaitTimeHeatmap.vue'
import WeeklyThemesChart from '../components/WeeklyThemesChart.vue'
import YelpSetup from '../components/YelpSetup.vue'
import { createCheckoutSession, createPortalSession, deleteAccount, fetchMe } from '../api'
import { REQUIRE_ACCEPTANCE, TERMS_VERSION, needsAcceptance } from '../legal/terms'
import { supabase } from '../supabase'
import { heatmapReadItems, negativeReadItems } from '../utils/nlpInsights'

const router = useRouter()
const route = useRoute()

const me = ref(null)
const loadingMe = ref(true)

// Terms of Service: everyone must agree to the current version once (and again if it changes).
const showTerms = ref(false)
const mustAccept = computed(() => REQUIRE_ACCEPTANCE && !loadingMe.value && needsAcceptance(me.value))

function onTermsAccepted(saved) {
  me.value = { ...me.value, terms_version: saved.terms_version, terms_accepted_at: saved.terms_accepted_at }
}

// The "last X months" window - shared by Run Analysis and the competitor chart.
const months = ref(6)

// Which pulled platform(s) the panels analyze. Switching re-analyzes cached reviews: free.
const view = ref('combined')
const formRef = ref(null)

// 'single' = your own business; 'company' = the multi-location console.
const mode = ref('single')

const sentimentResult = ref(null)
const waitTimeResult = ref(null)
const negativeResult = ref(null)
const trendsResult = ref(null)
const signalsResult = ref(null)
const competitorsResult = ref(null)
const platformsResult = ref(null)
const reviewList = ref(null)
const mentionsResult = ref(null)
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

onMounted(async () => {
  await loadMe()
  // Someone invited to a company who isn't on a paid plan lands in the company view.
  if (me.value?.org_role && !isPaid()) mode.value = 'company'
})

function handleLocationSet(location) {
  me.value = { ...me.value, business_location: location }
}

function handleYelpSaved(url) {
  me.value = { ...me.value, yelp_url: url }
}

const VIEW_LABELS = { combined: 'Combined', google: 'Google', yelp: 'Yelp' }
const viewChoices = computed(() => (meta.value && meta.value.sources.length > 1 ? ['combined', ...meta.value.sources] : []))

const sourceSummary = computed(() => {
  const by = meta.value?.by_source
  if (!by || Object.keys(by).length < 2) return ''
  return Object.entries(by)
    .map(([src, v]) => `${VIEW_LABELS[src] ?? src} ${v.reviews}`)
    .join(' · ')
})

function switchView(next) {
  view.value = next
  formRef.value?.runAnalysis(next)
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
const showCompany = () => isPaid() || Boolean(me.value?.org_role)

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
  platformsResult.value = data.platforms
  reviewList.value = data.review_list
  mentionsResult.value = data.mentions
  view.value = data.meta.view
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

    <TermsGate v-if="mustAccept" mode="accept" @accepted="onTermsAccepted" @decline="handleLogout" />
    <TermsGate v-if="showTerms" mode="read" @close="showTerms = false" />

    <p v-if="route.query.checkout === 'success'" class="status" style="color: #2ecc71">
      🎉 Subscription active — thanks for upgrading!
    </p>

    <p v-if="loadingMe" class="status">Loading account…</p>

    <template v-else-if="me">
      <div v-if="showCompany()" class="mode-tabs">
        <button class="mode-tab" :class="{ active: mode === 'single' }" @click="mode = 'single'">My business</button>
        <button class="mode-tab" :class="{ active: mode === 'company' }" @click="mode = 'company'">🏢 Company (many locations)</button>
      </div>

      <OrgConsole v-if="mode === 'company'" :me="me" />
      <SetBusinessLocation v-else-if="!me.business_location" @set="handleLocationSet" />

      <template v-else>
      <div class="nlp-intro">
        <span class="nlp-badge">🧠 NLP</span>
        <span>
          <strong>Every panel reads the words in your reviews, not just the stars.</strong>
          Look for the purple <em>Language read</em> boxes: plain-English findings from natural
          language processing (sentiment scoring, phrase detection, topic extraction).
        </span>
      </div>

      <YelpSetup v-if="isPaid() && !me.yelp_url" @saved="handleYelpSaved" />

      <UnifiedAnalysisForm
        ref="formRef"
        v-model:months="months"
        :view="view"
        :yelp-url="isPaid() ? me.yelp_url : null"
        :business-location="me.business_location"
        :show-revenue-inputs="isPaid()"
        :show-competitors="isPaid()"
        :show-mentions="isPaid()"
        @result="handleUnifiedResult"
      />

      <p v-if="meta" class="status analysis-meta">
        Analyzed <strong>{{ meta.reviews_analyzed }}</strong> reviews
        ({{ meta.reviews_with_text }} with written text<span v-if="sourceSummary">; {{ sourceSummary }}</span>) from the last
        {{ meta.months }} {{ meta.months === 1 ? 'month' : 'months' }} · most recent review:
        <strong>{{ meta.latest_review_date ?? 'n/a' }}</strong>
        <span v-if="meta.from_cache"> · reused a recent pull (no new scraping charge)</span>
      </p>
      <p v-for="note in meta?.notes ?? []" :key="note" class="status analysis-note">ℹ️ {{ note }}</p>

      <div v-if="viewChoices.length" class="view-switch">
        <span class="view-switch-label">View:</span>
        <button
          v-for="choice in viewChoices"
          :key="choice"
          class="view-btn"
          :class="{ active: meta.view === choice }"
          @click="switchView(choice)"
        >
          {{ VIEW_LABELS[choice] ?? choice }}
        </button>
        <span class="view-hint">Switching re-analyzes the reviews already pulled, at no extra cost.</span>
      </div>

      <p v-if="meta && meta.reviews_analyzed === 0" class="status error">
        No reviews were found in this window. Try a longer time window, or double-check your
        business location.
      </p>
      <p v-else-if="meta && meta.reviews_with_text === 0" class="status error">
        These reviews are star ratings only, so counts and ratings are shown but the language
        panels have no words to read. Try a longer time window.
      </p>

      <ReviewReplies
        v-if="isPaid() && reviewList"
        :review-list="reviewList"
        :business-location="me.business_location"
        :yelp-url="me.yelp_url"
      />
      <LockedPanel
        v-else-if="!isPaid()"
        title="💬 Reviews & draft replies"
        chart-name="Reply drafts"
        technique="Lists every review in your window and drafts a reply to any of them (AI-written when set up, otherwise a safe template) that you edit, copy and post, with a record of what's been answered."
      />

      <RevenueSignals :result="signalsResult" :meta="meta" />
      <PlatformComparison v-if="isPaid() && (platformsResult?.platforms?.length ?? 0) > 1" :result="platformsResult" />
      <SentimentDriftChart :result="sentimentResult" :meta="meta" />
      <WeeklyThemesChart :weekly="sentimentResult?.weekly ?? []" :meta="meta" />
      <TrendsPanel :result="trendsResult" :meta="meta" />
      <MentionsPanel v-if="isPaid()" :result="mentionsResult" />

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
          title="🏷️ Platform Comparison (Google + Yelp)"
          chart-name="Platform Comparison"
          technique="Pulls your Yelp page alongside Google and compares review volume, ratings and pace per platform, with a warning when a changing platform mix could distort your averages."
        />
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
    </template>

    <footer class="legal-footer">
      <button class="oc-link" @click="showTerms = true">Terms of Service</button>
      <span> · version {{ TERMS_VERSION }}</span>
    </footer>
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

.analysis-note {
  background: #fffbea;
  border: 1px solid #f0e0a0;
  border-radius: 8px;
  padding: 8px 14px;
  font-size: 13px;
}

.view-switch {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 18px;
}

.view-switch-label {
  font-size: 13px;
  font-weight: 600;
}

.view-btn {
  border: 1px solid #d3d6db;
  background: white;
  border-radius: 999px;
  padding: 5px 16px;
  font-size: 13px;
  cursor: pointer;
}

.view-btn.active {
  background: #ff4b4b;
  border-color: #ff4b4b;
  color: white;
  font-weight: 600;
}

.view-hint {
  font-size: 12px;
  color: #888;
}

.mode-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 18px;
}

.mode-tab {
  border: 1px solid #d3d6db;
  background: white;
  border-radius: 8px;
  padding: 8px 18px;
  font-size: 14px;
  cursor: pointer;
}

.mode-tab.active {
  background: #1a1a1a;
  border-color: #1a1a1a;
  color: white;
  font-weight: 600;
}

.legal-footer {
  margin-top: 40px;
  padding-top: 14px;
  border-top: 1px solid #e4e6ea;
  font-size: 12px;
  color: #888;
}
</style>
