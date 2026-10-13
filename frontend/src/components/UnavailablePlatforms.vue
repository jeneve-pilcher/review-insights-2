<script setup>
import { computed } from 'vue'
import { unavailableFor } from '../content/platformNotes'

// Says which review sites aren't offered for this industry and why, so there is no link box to wonder about.
const props = defineProps({ industry: { type: String, default: '' } })
const items = computed(() => unavailableFor(props.industry))
const terms = computed(() => items.value.filter((i) => i.reason === 'terms'))
const nosource = computed(() => items.value.filter((i) => i.reason === 'nosource'))
</script>

<template>
  <div v-if="items.length" class="up-note">
    <p class="up-title">Not available for this industry</p>
    <ul>
      <li v-for="i in terms" :key="i.id"><strong>{{ i.label }}</strong>: {{ i.why }}.</li>
      <li v-for="i in nosource" :key="i.id"><strong>{{ i.label }}</strong>: {{ i.why }}.</li>
    </ul>
    <p class="up-foot">So there is nothing to paste for these. Google reviews and the pages listed above are what we read.</p>
  </div>
</template>

<style scoped>
.up-note { margin: 14px 0 6px; padding: 10px 12px; border-radius: 8px; background: #fff8f2; border: 1px solid #fde1cc; font-size: 0.88rem; color: #57534e; }
.up-title { margin: 0 0 4px; font-weight: 600; color: #7c2d12; }
.up-note ul { margin: 0; padding-left: 18px; }
.up-note li { margin: 2px 0; }
.up-foot { margin: 6px 0 0; font-size: 0.82rem; color: #78716c; }
</style>
