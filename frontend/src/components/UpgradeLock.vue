<script setup>
import { useRouter } from 'vue-router'

defineProps({ chartName: { type: String, required: true } })
const router = useRouter()

function goToPricing() {
  router.push({ path: '/', hash: '#pricing' })
}
</script>

<template>
  <div class="upgrade-lock">
    <div class="lock-icon">🔒</div>
    <h4>{{ chartName }} is a Pro feature</h4>
    <p>Upgrade to Pro ($49/mo) to unlock this chart, or go Enterprise for custom scope.</p>
    <button class="run-btn" @click="goToPricing">See plans</button>
  </div>
</template>
