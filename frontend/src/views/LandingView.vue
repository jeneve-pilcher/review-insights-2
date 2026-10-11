<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import GetStartedPanel from '../components/GetStartedPanel.vue'
import IndustryShowcase from '../components/IndustryShowcase.vue'
import PricingCard from '../components/PricingCard.vue'
import StatsStrip from '../components/StatsStrip.vue'
import { readQuery } from '../utils/startFlow'

const route = useRoute()
const router = useRouter()

const selected = ref('') // the industry chosen in the section below the hero
const plan = ref('free')

function scrollToSection(id) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

// Every "get started" and purchase button scrolls to the panel on this page (no popup). If no industry has been
// chosen yet, it takes you to the industries first.
function startFlow(chosenPlan) {
  if (chosenPlan) plan.value = chosenPlan
  scrollToSection(selected.value ? 'start' : 'industries')
}

function chooseFree() {
  startFlow('free')
}

function choosePro() {
  startFlow('pro')
}

function chooseEnterprise() {
  router.push('/enterprise')
}

// A link like /?industry=dental&plan=pro lands you straight on the get-started panel for that industry.
onMounted(() => {
  const q = readQuery(route.query)
  if (q.plan) plan.value = q.plan
  if (q.industry) {
    selected.value = q.industry
    setTimeout(() => scrollToSection('start'), 50)
  }
})
</script>

<template>
  <div class="landing">
    <nav class="landing-nav">
      <span class="landing-brand">📊 Review Insights</span>
      <div class="landing-nav-links">
        <a href="#industries">Industries</a>
        <a href="#pricing">Plans</a>
        <router-link to="/login">Log in</router-link>
        <button class="run-btn" @click="startFlow('free')">Get started</button>
      </div>
    </nav>

    <header class="landing-hero">
      <h1>📊 Review Insights</h1>
      <p>
        Review intelligence for restaurants, healthcare practices and more. Turn your reviews into early-warning
        signals: catch sentiment drift, wait-time revenue leaks and competitor weak spots, with the themes and graphs
        that matter in your industry.
      </p>
      <button class="run-btn" @click="scrollToSection('industries')">Choose your industry</button>
    </header>

    <StatsStrip />

    <IndustryShowcase :selected="selected" @select="selected = $event" @start="startFlow()" />

    <GetStartedPanel :industry="selected" :plan="plan" @update:plan="plan = $event" />

    <section id="pricing" class="pricing-section">
      <h2>Plans</h2>
      <div class="pricing-grid">
        <PricingCard
          title="Free"
          price="$0"
          :features="['Sentiment Drift chart', '1 business', 'Weekly refresh']"
          cta-label="Start free"
          @cta="chooseFree"
        />
        <PricingCard
          title="Pro"
          price="$49"
          period="/ month"
          :highlighted="true"
          :features="[
            'All 3 charts',
            'Wait-Time Revenue Heatmap',
            'Competitor Semantic Share Matrix',
            'Up to 6 competitors tracked',
          ]"
          cta-label="Start Pro"
          @cta="choosePro"
        />
        <PricingCard
          title="Enterprise"
          price="Custom"
          :features="['Everything in Pro', 'Custom competitor limits', 'Dedicated support', 'Custom integrations']"
          cta-label="Contact sales"
          @cta="chooseEnterprise"
        />
      </div>
    </section>
  </div>
</template>

<style>
.landing-nav {
  position: sticky;
  top: 0;
  z-index: 5;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 28px;
  background: white;
  border-bottom: 1px solid #e4e6ea;
}

.landing-brand {
  font-weight: 700;
}

.landing-nav-links {
  display: flex;
  align-items: center;
  gap: 18px;
  font-size: 14px;
}

.landing-nav-links a {
  color: inherit;
  text-decoration: none;
}

.landing-nav-links .run-btn {
  width: auto;
  padding: 8px 16px;
}

.landing {
  scroll-behavior: smooth;
}

#industries,
#start,
#pricing {
  scroll-margin-top: 64px;
}
</style>
