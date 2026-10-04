<script setup>
import { useRouter } from 'vue-router'
import PricingCard from '../components/PricingCard.vue'

const router = useRouter()

function chooseFree() {
  router.push({ path: '/signup', query: { plan: 'free' } })
}

function choosePro() {
  router.push({ path: '/signup', query: { plan: 'pro' } })
}

function chooseEnterprise() {
  router.push('/enterprise')
}

const stats = [
  {
    value: '97%',
    label: 'of consumers read reviews before choosing a local business',
    source: 'BrightLocal, 2026',
  },
  {
    value: '81%',
    label: 'specifically check Google reviews before visiting a business',
    source: 'DemandSage / Wiser Review, 2026',
  },
  {
    value: '70%',
    label: 'of potential customers a business can lose after just 4 negative reviews',
    source: 'LocalIQ, 2026',
  },
  {
    value: '10',
    label: 'reviews the average consumer reads before trusting a business',
    source: 'BrightLocal, 2026',
  },
]
</script>

<template>
  <div class="landing">
    <header class="landing-hero">
      <div class="hero-badge">📍 Built on real Google review data</div>
      <h1>Your reviews are already telling you what's wrong.<br />Most businesses just aren't listening fast enough.</h1>
      <p>
        Turn Google reviews into early-warning signals: catch sentiment drift, wait-time revenue
        leaks, and competitor weak spots before they show up in your star rating.
      </p>
      <button class="run-btn hero-cta" @click="chooseFree">Get started free</button>
    </header>

    <section class="stats-section">
      <h2>Why review analysis matters</h2>
      <p class="stats-intro">
        Reviews aren't just reputation management anymore - they're a live data feed on how your
        business is actually performing, read by nearly every customer before they walk in.
      </p>
      <div class="stats-grid">
        <div v-for="stat in stats" :key="stat.label" class="stat-card">
          <div class="stat-value">{{ stat.value }}</div>
          <p class="stat-label">{{ stat.label }}</p>
          <span class="stat-source">{{ stat.source }}</span>
        </div>
      </div>
      <p class="stats-footnote">
        The problem: by the time a trend is obvious in your overall star rating, it's already
        cost you customers. Review Insights is built to catch the shift while it's still small -
        a subtle move from your best tier into your second or third tier, a bad Thursday evening
        pattern, a competitor's weak spot - not after it's already visible to everyone searching
        your name on Google.
      </p>
    </section>

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
            'All charts',
            'Wait-Time Revenue Heatmap',
            'Negative Review Alerts',
            'Competitor Semantic Share Matrix',
            'Up to 5 competitors tracked',
          ]"
          cta-label="Start Pro"
          @cta="choosePro"
        />
        <PricingCard
          title="Enterprise"
          price="Custom"
          :features="['Everything in Pro', 'SAML/OIDC company login', 'Custom competitor limits', 'Dedicated support']"
          cta-label="Contact sales"
          @cta="chooseEnterprise"
        />
      </div>
    </section>
  </div>
</template>