<script setup>
import { REVENUE_ITEMS, REVENUE_NOTE } from '../content/revenue'
import '../theme/tones.css'
import CardArt from './CardArt.vue'
</script>

<template>
  <section id="revenue" class="rev-section">
   <div class="rev-inner">
    <h2>Where revenue may be slipping away</h2>
    <p class="rev-sub">Six patterns we look for in your reviews.</p>

    <div class="rev-grid">
      <article v-for="r in REVENUE_ITEMS" :key="r.id" class="rev-card" :class="`tone-${r.tone}`">
        <CardArt :name="r.id" />
        <h3>{{ r.title }}</h3>
        <p><strong>We look at</strong> {{ r.look }}</p>
        <p><strong>You see</strong> {{ r.see }}</p>
        <span class="rev-plan">{{ r.plan }}</span>
      </article>
    </div>

    <p class="rev-note">{{ REVENUE_NOTE }}</p>
   </div>
  </section>
</template>

<style>
.rev-section {
  padding: 36px 20px 32px;
  background: linear-gradient(180deg, #fff3ea 0%, #ffffff 100%);
}

.rev-inner {
  max-width: 1000px;
  margin: 0 auto;
}

.rev-section h2 {
  text-align: center;
  margin-bottom: 6px;
}

.rev-section h2::after {
  content: '';
  display: block;
  width: 64px;
  height: 4px;
  border-radius: 2px;
  margin: 8px auto 0;
  background: var(--brand, #ff4b4b);
}

.rev-sub {
  text-align: center;
  color: #555;
  margin: 0 auto 20px;
  max-width: 620px;
}

.rev-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.rev-card {
  flex: 1 1 290px;
  background: white;
  border: 1px solid #e4e6ea;
  border-top: 4px solid var(--tone);
  border-radius: 12px;
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.rev-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.07);
}

@media (prefers-reduced-motion: reduce) {
  .rev-card { transition: none; }
  .rev-card:hover { transform: none; }
}

.rev-icon {
  align-self: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--tone-soft);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.rev-card h3 {
  margin: 0;
  font-size: 16px;
  text-align: center;
}

.rev-card p {
  margin: 0;
  font-size: 14px;
  color: #333;
}

.rev-card strong {
  color: var(--tone-text);
}

.rev-plan {
  align-self: center;
  margin-top: auto;
  padding: 2px 10px;
  font-size: 11px;
  font-weight: 600;
  color: var(--tone-text);
  background: var(--tone-soft);
  border-radius: 999px;
}

.rev-note {
  text-align: center;
  font-size: 13px;
  color: #666;
  max-width: 720px;
  margin: 16px auto 0;
}
</style>
