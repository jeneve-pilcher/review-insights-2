
<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import CompetitorShareChart from '../components/CompetitorShareChart.vue'
import NegativeReviewAlerts from '../components/NegativeReviewAlerts.vue'
import SentimentDriftChart from '../components/SentimentDriftChart.vue'
import SetBusinessLocation from '../components/SetBusinessLocation.vue'
import UnifiedAnalysisForm from '../components/UnifiedAnalysisForm.vue'
import UpgradeLock from '../components/UpgradeLock.vue'
import WaitTimeHeatmap from '../components/WaitTimeHeatmap.vue'
import WeeklyThemesChart from '../components/WeeklyThemesChart.vue'
import { createCheckoutSession, createPortalSession, deleteAccount, fetchMe } from '../api'
import { supabase } from '../supabase'

const router = useRouter()
const route = useRoute()

const me = ref(null)
const loadingMe = ref(true)

const sentimentResult = ref(null)
const waitTimeResult = ref(null)

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
      <UnifiedAnalysisForm
        :business-location="me.business_location"
        :show-revenue-inputs="isPaid()"
        @result="handleUnifiedResult"
      />

      <SentimentDriftChart :result="sentimentResult" />
      <WeeklyThemesChart :weekly="sentimentResult?.weekly ?? []" />

      <template v-if="isPaid()">
        <WaitTimeHeatmap :result="waitTimeResult" />
        <NegativeReviewAlerts :business-location="me.business_location" />
        <CompetitorShareChart :business-location="me.business_location" />
      </template>
      <template v-else>
        <section class="chart-section">
          <UpgradeLock chart-name="Wait-Time Revenue Heatmap" />
        </section>
        <section class="chart-section">
          <UpgradeLock chart-name="Negative Review Alerts" />
        </section>
        <section class="chart-section">
          <UpgradeLock chart-name="Competitor Semantic Share Matrix" />
        </section>
      </template>
    </template>
  </div>
</template>