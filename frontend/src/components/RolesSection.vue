<script setup>
import { ROLES, ROLES_NOTE } from '../content/roles'
import '../theme/tones.css'
import CardArt from './CardArt.vue'
</script>

<template>
  <section id="who" class="roles-section">
   <div class="roles-inner">
    <h2>Who uses it</h2>
    <p class="roles-sub">From one location to many, everyone sees what fits their job.</p>

    <div class="roles-grid">
      <article v-for="r in ROLES" :key="r.id" class="role-card" :class="`tone-${r.tone}`">
        <CardArt :name="r.id" />
        <h3>{{ r.title }}</h3>
        <p class="role-purpose"><strong>Uses it to</strong> {{ r.purpose }}.</p>
        <h4 class="role-looks">What they look at</h4>
        <ul>
          <li v-for="u in r.uses" :key="u">{{ u }}</li>
        </ul>
      </article>
    </div>

    <p class="roles-note">{{ ROLES_NOTE }}</p>
   </div>
  </section>
</template>

<style>
.roles-section {
  padding: 36px 20px 32px;
  background: linear-gradient(180deg, #fff8e6 0%, #ffffff 100%);
}

.roles-inner {
  max-width: 1000px;
  margin: 0 auto;
}

.roles-section h2 {
  text-align: center;
  margin-bottom: 6px;
}

.roles-section h2::after {
  content: '';
  display: block;
  width: 64px;
  height: 4px;
  border-radius: 2px;
  margin: 8px auto 0;
  background: var(--brand, #ff4b4b);
}

.roles-sub {
  text-align: center;
  color: #555;
  margin: 0 auto 20px;
  max-width: 620px;
}

.roles-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.role-card {
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

.role-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.07);
}

@media (prefers-reduced-motion: reduce) {
  .role-card { transition: none; }
  .role-card:hover { transform: none; }
}

.role-icon {
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

.role-card h3 {
  margin: 0;
  font-size: 16px;
  text-align: center;
}

.role-purpose {
  margin: 0;
  font-size: 14px;
  color: #333;
  text-align: center;
}

.role-card strong {
  color: var(--tone-text);
}

.role-looks {
  margin: 8px 0 0;
  font-size: 11px;
  color: var(--tone-text);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  text-align: center;
}

.role-card ul {
  margin: 4px 0 0;
  padding-left: 18px;
  font-size: 13px;
  color: #333;
  flex: 1;
}

.role-card li {
  margin-bottom: 4px;
}

.role-card li::marker {
  color: var(--tone);
}

.roles-note {
  text-align: center;
  font-size: 13px;
  color: #666;
  max-width: 720px;
  margin: 16px auto 0;
}
</style>
