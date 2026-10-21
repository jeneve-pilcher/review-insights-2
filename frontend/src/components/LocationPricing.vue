<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchLocationPricing } from '../api'
import { STANDARD_TIERS, averagePerLocation, billedLocations, monthlyTotal, tierLabel, usd } from '../utils/locationPricing'

// The per-location price table and a small calculator. The numbers come from the server.
const props = defineProps({ start: { type: Number, default: 600 }, quiet: { type: Boolean, default: false } })

const tiers = ref(STANDARD_TIERS)       // shown straight away; replaced by the server's table when it answers
const failed = ref(false)
const count = ref(props.start)

onMounted(async () => {
  try {
    const live = (await fetchLocationPricing()).tiers
    if (Array.isArray(live) && live.length) tiers.value = live
  } catch {
    failed.value = true
  }
})

const total = computed(() => monthlyTotal(tiers.value, count.value))
const average = computed(() => averagePerLocation(tiers.value, count.value))
const billed = computed(() => billedLocations(tiers.value, count.value))
const entered = computed(() => Math.max(1, Math.floor(Number(count.value) || 0)))
</script>

<template>
  <section v-if="tiers.length" class="lp">
    <h3>Pricing by location</h3>
    <p class="lp-note">Every location is charged the price for your size, so the more locations you have, the less each one costs.</p>
    <table class="lp-table">
      <tbody>
        <tr v-for="t in tiers" :key="t.from">
          <td>{{ tierLabel(t) }}</td>
          <td>{{ usd(t.price_per_location) }} each / month</td>
        </tr>
      </tbody>
    </table>
    <label class="lp-calc">
      How many locations?
      <input v-model.number="count" type="number" min="1" step="1" />
    </label>
    <p class="lp-result">
      <strong>{{ usd(total) }}</strong> per month <span class="lp-note">(about {{ usd(average) }} per location)</span>
    </p>
    <p v-if="billed > entered" class="lp-note">At this size you'd pay the same as {{ billed }} locations, because that costs less than your count at the higher price.</p>
    <p class="lp-note">Standard prices. Contracts can agree different prices. Usage such as review pulls is charged separately from prepaid credit. Prices exclude any taxes.</p>
  </section>
</template>

<style>
.lp { margin: 0 0 18px; text-align: left; }
.lp h3 { margin: 0 0 4px; }
.lp-note { color: #78716c; font-size: 13px; margin: 4px 0; }
.lp-table { width: 100%; border-collapse: collapse; margin: 8px 0; font-size: 14px; }
.lp-table td { padding: 6px 8px; border-bottom: 1px solid #f1e4d8; }
.lp-calc { display: flex; align-items: center; gap: 10px; font-size: 14px; margin-top: 10px; }
.lp-calc input { width: 90px; }
.lp-result { margin: 8px 0; font-size: 16px; color: #7c2d12; }
@media (max-width: 520px) {
  .lp-table { font-size: 13px; }
  .lp-table td { padding: 6px 4px; }
  .lp-calc { flex-wrap: wrap; }
  .lp-calc input { width: 110px; font-size: 16px; }
  .lp-result { font-size: 15px; }
}
</style>
