<script setup>
import NlpCallout from './NlpCallout.vue'
import UpgradeLock from './UpgradeLock.vue'

defineProps({
  title: { type: String, required: true },
  chartName: { type: String, required: true },
  // Free-tier teaser: a real finding from the user's own reviews.
  previewItems: { type: Array, default: () => [] },
  technique: { type: String, default: '' },
})
</script>

<template>
  <section class="chart-section">
    <div class="title-row">
      <h3>{{ title }}</h3>
      <span class="nlp-badge">🧠 NLP</span>
    </div>
    <NlpCallout
      title="Free preview, from your own reviews"
      :items="previewItems"
      :technique="technique"
    />
    <UpgradeLock :chart-name="chartName" />
  </section>
</template>
