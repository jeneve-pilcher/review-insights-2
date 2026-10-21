<script setup>
import { nextTick, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import GetStartedPanel from '../components/GetStartedPanel.vue'
import PrivacyPolicy from '../components/PrivacyPolicy.vue'
import TermsOfService from '../components/TermsOfService.vue'
import IndustryShowcase from '../components/IndustryShowcase.vue'
import PricingCard from '../components/PricingCard.vue'
import RevenueSection from '../components/RevenueSection.vue'
import RolesSection from '../components/RolesSection.vue'
import LocationPricing from '../components/LocationPricing.vue'
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
async function startFlow(chosenPlan) {
  if (chosenPlan) plan.value = chosenPlan
  await nextTick() // let the panel show the chosen industry before scrolling to it
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

// The Terms and the privacy policy sit at the bottom of the page and open in place (no popup). Links to #terms / #privacy open them.
const privacyOpen = ref(false)
const termsOpen = ref(false)
async function openLegal(which) {
  if (which === 'terms') termsOpen.value = true
  else privacyOpen.value = true
  await nextTick()
  document.getElementById(which)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

// A link like /?industry=dental&plan=pro lands you straight on the get-started panel for that industry.
onMounted(() => {
  if (window.location.hash === '#privacy') setTimeout(() => openLegal('privacy'), 50)
  if (window.location.hash === '#terms') setTimeout(() => openLegal('terms'), 50)
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
        <a href="#revenue">Revenue</a>
        <a href="#who">Who it's for</a>
        <a href="#industries">Industries</a>
        <a href="#pricing">Plans</a>
        <router-link to="/login">Log in</router-link>
        <button class="run-btn" @click="startFlow('free')">Get started</button>
      </div>
    </nav>

    <header class="landing-hero">
      <p class="landing-kicker">Review intelligence for restaurants, healthcare practices and more</p>
      <h1>Uncover where revenue may be slipping away</h1>
      <p>
        We read your reviews for the patterns that cost you customers: waits at certain hours, a repeating complaint, a
        drifting rating. See what to look at first, with graphs built for your industry.
      </p>
      <button class="run-btn" @click="scrollToSection('industries')">Choose your industry</button>
      <p class="landing-fineprint">Revenue figures are estimates from review patterns, not your sales.</p>
    </header>

    <StatsStrip />

    <RevenueSection />

    <RolesSection />

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
            'Industry and revenue trends',
            'Wait-Time Revenue Heatmap',
            'Competitor Semantic Share Matrix',
            'Up to 5 competitors tracked',
          ]"
          cta-label="Start Pro"
          @cta="choosePro"
        />
        <PricingCard
          title="Enterprise"
          price="Custom"
          :features="['Everything in Pro', 'Volume pricing by location', 'Custom competitor limits', 'Dedicated support']"
          cta-label="Contact sales"
          @cta="chooseEnterprise"
        />
      </div>
      <div class="landing-location-pricing">
        <LocationPricing quiet />
      </div>
    </section>

    <footer class="landing-footer">
      <details id="terms" class="privacy-details" :open="termsOpen" @toggle="termsOpen = $event.target.open">
        <summary>Terms of Service</summary>
        <TermsOfService />
      </details>
      <details id="privacy" class="privacy-details" :open="privacyOpen" @toggle="privacyOpen = $event.target.open">
        <summary>Privacy Policy</summary>
        <PrivacyPolicy />
      </details>
      <p class="landing-fineprint">
        Review Insights ·
        <a href="#terms" @click.prevent="openLegal('terms')">Terms of Service</a> ·
        <a href="#privacy" @click.prevent="openLegal('privacy')">Privacy Policy</a>
      </p>
    </footer>
  </div>
</template>

<style>
.landing-hero {
  background: linear-gradient(135deg, #fff1ee 0%, #fff8f5 100%);
}

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

.landing-kicker {
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #777;
  margin: 0 0 6px;
}

.landing-footer {
  max-width: 820px;
  margin: 0 auto;
  padding: 28px 16px 40px;
  text-align: center;
}

.privacy-details {
  text-align: left;
  border: 1px solid #fdba74;
  border-radius: 10px;
  background: #fffaf5;
  padding: 10px 16px;
}

.privacy-details summary {
  cursor: pointer;
  font-weight: 600;
  color: #7c2d12;
}

.privacy-details + .privacy-details {
  margin-top: 10px;
}

.privacy-details[open] summary {
  margin-bottom: 12px;
}

.landing-fineprint {
  font-size: 12px;
  color: #777;
  margin: 10px 0 0;
}

#terms,
#privacy,
#revenue,
#who,
#industries,
#start,
#pricing {
  scroll-margin-top: 64px;
}
.landing-location-pricing {
  max-width: 480px;
  margin: 24px auto 0;
}

/* Phones and small tablets: the three plans stack one under another, full width, with room around them. */
@media (max-width: 760px) {
  .pricing-section {
    padding-left: 16px;
    padding-right: 16px;
  }
  .pricing-section .pricing-grid {
    display: grid !important;
    grid-template-columns: minmax(0, 1fr) !important;
    gap: 16px;
    width: 100%;
    max-width: 480px;
    margin-left: auto;
    margin-right: auto;
  }
  .pricing-section .pricing-grid > * {
    width: 100%;
    max-width: none !important;
    min-width: 0 !important;
    margin: 0 !important;
    box-sizing: border-box;
  }
  .landing-location-pricing {
    max-width: 100%;
    padding: 0 2px;
  }
}
</style>
