<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import CompetitorShareChart from '../components/CompetitorShareChart.vue'
import LockedPanel from '../components/LockedPanel.vue'
import MentionsPanel from '../components/MentionsPanel.vue'
import NegativeReviewAlerts from '../components/NegativeReviewAlerts.vue'
import OrgConsole from '../components/OrgConsole.vue'
import LocationDetail from '../components/LocationDetail.vue'
import LocationSwitcher from '../components/LocationSwitcher.vue'
import PlatformComparison from '../components/PlatformComparison.vue'
import CreditsPanel from '../components/CreditsPanel.vue'
import IndustryPanel from '../components/IndustryPanel.vue'
import AiSummary from '../components/AiSummary.vue'
import { FEATURES } from '../content/features'
import IndustryPrompt from '../components/IndustryPrompt.vue'
import ReviewReplies from '../components/ReviewReplies.vue'
import RevenueSignals from '../components/RevenueSignals.vue'
import SentimentDriftChart from '../components/SentimentDriftChart.vue'
import BusinessSetup from '../components/BusinessSetup.vue'
import TermsGate from '../components/TermsGate.vue'
import TrendsPanel from '../components/TrendsPanel.vue'
import UnifiedAnalysisForm from '../components/UnifiedAnalysisForm.vue'
import WaitTimeHeatmap from '../components/WaitTimeHeatmap.vue'
import WeeklyThemesChart from '../components/WeeklyThemesChart.vue'
import ToneVsStarsChart from '../components/ToneVsStarsChart.vue'
import YourPagesModal from '../components/YourPagesModal.vue'
import { createCheckoutSession, createPortalSession, deleteAccount, fetchIndustries, fetchMe } from '../api'
import { applyBranding, brandTitle, forgetBrand, rememberBrand, safeLogo } from '../utils/theme'
import { billingLine } from '../utils/credits'
import { REQUIRE_ACCEPTANCE, TERMS_VERSION, needsAcceptance } from '../legal/terms'
import { supabase } from '../supabase'
import AdminBilling from '../components/AdminBilling.vue'
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

// Company managers switch between the locations they manage right here on the dashboard.
const isManager = computed(() => me.value?.org_role === 'manager')
const activeLocation = ref('')
const orgInfo = ref(null)
const showingLocation = computed(() => isManager.value && activeLocation.value && activeLocation.value !== 'own')

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
  fetchIndustries().then((d) => { industries.value = d.industries }).catch(() => {})
  await loadMe()
  // Someone invited to a company who isn't on a paid plan lands in the company view.
  if (me.value?.org_role && me.value.org_role !== 'manager' && !isPaid()) mode.value = 'company'
})

// First-time setup finished: the Google business, plus any review pages saved with it.
function handleSetupDone({ location, links }) {
  me.value = { ...me.value, business_location: location, ...links }
}

// "Your pages": merge newly saved links into the account.
const showPages = ref(false)
function handleLinksSaved(links) {
  me.value = { ...me.value, ...links }
}

// Credit summary (balance, rates, caps) shared with the run form so it can show an estimate.
// Industry packs and white-label branding.
const industries = ref([])
const industryResult = ref(null)
const aiSummaryResult = ref(null)
const industryDefaultAov = computed(() => industries.value.find((i) => i.id === (me.value?.industry || 'casual_dining'))?.default_aov ?? 35)
const repliesOff = computed(() => industries.value.find((i) => i.id === (me.value?.industry || 'casual_dining'))?.replies_allowed === false)
const brandLogo = computed(() => safeLogo(me.value?.branding))
const brandName = computed(() => brandTitle(me.value?.branding))
watch(me, (m) => {
  if (!m) return
  applyBranding(m.branding)
  document.title = brandTitle(m.branding)
  if (m.branding) rememberBrand(m.branding)
  else forgetBrand()
})

const creditInfo = ref(null)
const creditsPanel = ref(null)
const billingText = ref('')

const VIEW_LABELS = { combined: 'Combined', google: 'Google', yelp: 'Yelp', opentable: 'OpenTable', doordash: 'DoorDash', grubhub: 'Grubhub', ubereats: 'Uber Eats', web: 'Web mentions' }
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
const showCompany = () => isPaid() || Boolean(me.value?.org_role) || Boolean(me.value?.has_contract)

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
  industryResult.value = data.industry
  aiSummaryResult.value = data.ai_summary
  view.value = data.meta.view
  waitTimePreview.value = data.wait_time_preview
  negativePreview.value = data.negative_preview
  meta.value = data.meta
  billingText.value = billingLine(data.billing)
  creditsPanel.value?.reload()        // the balance just changed
}
</script>

<template>
  <div class="dashboard">
    <div class="topbar">
      <h1>
        <img v-if="brandLogo" :src="brandLogo" :alt="brandName" class="brand-logo" />
        <template v-else-if="me && me.branding">{{ brandName }}</template>
        <template v-else>📊 Review Insights</template>
      </h1>
      <div class="user-info" v-if="me">
        <span>{{ me.email }}</span>
        <span class="tier-badge" :class="me.tier">{{ me.tier }}</span>
        <button v-if="isPaid()" class="logout-btn" @click="handleManageSubscription">Manage subscription</button>
        <button v-else class="logout-btn" @click="handleUpgrade">Upgrade</button>
        <button v-if="isPaid() && me.business_location" class="logout-btn" @click="showPages = true">Your pages</button>
        <button class="logout-btn" @click="handleLogout">Log out</button>
        <button class="logout-btn danger-btn" @click="handleDeleteAccount">Delete account</button>
      </div>
    </div>

    <TermsGate v-if="mustAccept" mode="accept" @accepted="onTermsAccepted" @decline="handleLogout" />
    <TermsGate v-if="showTerms" mode="read" @close="showTerms = false" />
    <YourPagesModal v-if="showPages" :current="me" @saved="handleLinksSaved" @close="showPages = false" />

    <p v-if="route.query.checkout === 'success'" class="status" style="color: #2ecc71">
      🎉 Subscription active — thanks for upgrading!
    </p>

    <p v-if="loadingMe" class="status">Loading account…</p>

    <template v-else-if="me">
      <div v-if="showCompany()" class="mode-tabs">
        <button class="mode-tab" :class="{ active: mode === 'single' }" @click="mode = 'single'">{{ isManager ? 'My locations' : 'My business' }}</button>
        <button class="mode-tab" :class="{ active: mode === 'company' }" @click="mode = 'company'">🏢 Company (many locations)</button>
      </div>

      <AdminBilling v-if="me.is_admin" />

      <template v-if="isManager && mode === 'single'">
        <LocationSwitcher v-model="activeLocation" :has-own="Boolean(me.business_location)" @loaded="orgInfo = $event" />
        <LocationDetail v-if="showingLocation" :key="activeLocation" :location-id="activeLocation" :info="orgInfo" embedded />
      </template>

      <OrgConsole v-if="mode === 'company'" :me="me" />
      <BusinessSetup v-else-if="!isManager && !me.business_location" :can-add-links="isPaid()" :current="me" @set="handleSetupDone" />

      <template v-else-if="!showingLocation && (!isManager || me.business_location)">
      <IndustryPrompt v-if="!me.industry_set" :current="me" @saved="handleLinksSaved" />
      <div class="nlp-intro">
        <span>
          <strong>Every panel reads the words in your reviews, not just the stars.</strong>
          Look for the purple <em>Language read</em> boxes: plain-English findings from natural
          language processing (sentiment scoring, phrase detection, topic extraction).
        </span>
      </div>

      <CreditsPanel ref="creditsPanel" scope="user" @loaded="creditInfo = $event" />

      <UnifiedAnalysisForm
        ref="formRef"
        v-model:months="months"
        :view="view"
        :yelp-url="isPaid() ? me.yelp_url : null"
        :opentable-url="isPaid() ? me.opentable_url : null"
        :doordash-url="isPaid() ? me.doordash_url : null"
        :ubereats-url="isPaid() ? me.ubereats_url : null"
        :grubhub-url="isPaid() ? me.grubhub_url : null"
        :credit-info="creditInfo"
        :default-aov="industryDefaultAov"
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
        <span v-if="meta.web_mentions"> · plus {{ meta.web_mentions }} web mentions (separate from star reviews)</span>
        <span v-if="meta.from_cache"> · reused a recent pull (no new scraping charge)</span>
        <span v-if="billingText"> · {{ billingText }}</span>
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
        :opentable-url="me.opentable_url"
        :doordash-url="me.doordash_url"
        :grubhub-url="me.grubhub_url"
        :replies-off="repliesOff"
      />
      <LockedPanel
        v-else-if="!isPaid()"
        title="💬 Reviews & draft replies"
        chart-name="Reply drafts"
        technique="Lists every review in your window and drafts a reply to any of them (AI-written when set up, otherwise a safe template) that you edit, copy and post, with a record of what's been answered."
      />

      <AiSummary v-if="FEATURES.aiSummaries" :result="aiSummaryResult" />
      <RevenueSignals :result="signalsResult" :meta="meta" />
      <PlatformComparison v-if="isPaid() && (platformsResult?.platforms?.length ?? 0) > 1" :result="platformsResult" />
      <SentimentDriftChart :result="sentimentResult" :meta="meta" />
      <WeeklyThemesChart :weekly="sentimentResult?.weekly ?? []" :meta="meta" />
      <ToneVsStarsChart :weekly="sentimentResult?.weekly ?? []" :meta="meta" />
      <TrendsPanel :result="trendsResult" :meta="meta" />
      <IndustryPanel :result="industryResult" :meta="meta" :locked="!isPaid()" />
      <MentionsPanel v-if="FEATURES.internetMentions && isPaid()" :result="mentionsResult" />

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
          title="🏷️ Platform Comparison (every platform you connect)"
          chart-name="Platform Comparison"
          technique="Pulls your Yelp, reservation and delivery-app pages alongside Google and compares review volume, ratings and pace per platform, with a warning when a changing platform mix could distort your averages."
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
      <span> · </span>
      <a href="/#privacy" class="oc-link">Privacy Policy</a>
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
  background: var(--brand-soft, #faf8ff);
  border: 1px solid var(--brand-border, #e4defa);
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
  background: var(--brand, #ff4b4b);
  border-color: var(--brand, #ff4b4b);
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
