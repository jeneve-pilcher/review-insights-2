<script setup>
defineProps({
  title: { type: String, required: true },
  price: { type: String, required: true },
  period: { type: String, default: '' },
  features: { type: Array, required: true },
  ctaLabel: { type: String, required: true },
  highlighted: { type: Boolean, default: false },
})
const emit = defineEmits(['cta'])
</script>

<template>
  <div class="pricing-card" :class="{ highlighted }">
    <h3>{{ title }}</h3>
    <div class="price">
      <span class="amount">{{ price }}</span>
      <span v-if="period" class="period">{{ period }}</span>
    </div>
    <ul>
      <li v-for="f in features" :key="f">✓ {{ f }}</li>
    </ul>
    <button class="cta-btn" @click="emit('cta')">{{ ctaLabel }}</button>
  </div>
</template>
