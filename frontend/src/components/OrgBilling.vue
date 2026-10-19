<script setup>
import { computed, ref } from 'vue'
import { orgApi } from '../api'
import { tierLabel, usd } from '../utils/locationPricing'

// Owner only: the locations used under this company's agreement, and what that comes to. Billing is by invoice under the contract.
const props = defineProps({ info: { type: Object, required: true } })
const b = computed(() => props.info.billing)
const contract = computed(() => b.value?.contract ?? null)
const sub = computed(() => b.value?.subscription ?? { live: false, status: null, has_customer: false })
const busy = ref(false)
const error = ref('')

async function go(kind) {
  busy.value = true
  error.value = ''
  try {
    const { url } = kind === 'setup' ? await orgApi.billingCheckout() : await orgApi.billingPortal()
    window.location.href = url
  } catch (err) {
    error.value = err?.response?.data?.detail || 'Could not open billing.'
    busy.value = false
  }
}
</script>

<template>
  <section v-if="b" class="ob">
    <h3>Billing by location</h3>
    <p>
      Locations in use{{ b.accounts > 1 ? ` across your ${b.accounts} accounts on ${b.domain}` : '' }}:
      <strong>{{ b.locations_used }}</strong>.
      <template v-if="b.minimum_locations > b.locations_used">
        Your agreement bills a minimum of <strong>{{ b.minimum_locations }}</strong>.
      </template>
    </p>
    <p>
      Monthly amount at your rates: <strong>{{ usd(b.monthly_total) }}</strong>
      <span class="lp-note">({{ b.locations_billed }} billed, about {{ usd(b.average_per_location) }} each)</span>
    </p>

    <table class="lp-table">
      <tbody>
        <tr v-for="t in b.tiers" :key="t.from">
          <td>{{ tierLabel(t) }}</td>
          <td>{{ usd(t.price_per_location) }} each / month</td>
        </tr>
      </tbody>
    </table>
    <p class="lp-note">{{ b.custom_prices ? 'These are the prices in your agreement.' : 'These are the standard prices.' }}</p>

    <p v-if="b.organizations.length > 1" class="lp-note">
      Accounts counted:
      <template v-for="(o, i) in b.organizations" :key="o.name + o.owner_email">{{ i ? '; ' : '' }}{{ o.name }} ({{ o.locations }})</template>
    </p>
    <p v-if="contract?.starts_on || contract?.ends_on" class="lp-note">
      Agreement period: {{ contract.starts_on || 'start not set' }} to {{ contract.ends_on || 'no end date set' }}.
    </p>
    <p v-if="sub.live" class="status" style="color: #2e7d32">
      Billing is active{{ sub.status && sub.status !== 'active' ? ` (${sub.status})` : '' }}. You are charged monthly through Stripe for the
      locations you have. Adding or deleting a location changes the amount on your next invoice, prorated for the part of the month left.
    </p>
    <p v-else class="status error">
      Billing isn't set up{{ sub.status ? ` (last status: ${sub.status})` : '' }}.
      <template v-if="sub.required">You can't add locations until it is.</template>
    </p>
    <button v-if="!sub.live" class="oc-btn" :disabled="busy" @click="go('setup')">Set up billing</button>
    <button v-if="sub.has_customer" class="oc-btn" :disabled="busy" @click="go('portal')">Manage billing</button>
    <p v-if="error" class="status error">{{ error }}</p>
    <p class="lp-note">
      Charged monthly by card through Stripe at the amounts above. The first charge is for the locations you have when you set it up.
      Prices exclude any taxes. Questions about a charge: contact us.
    </p>
  </section>
  <p v-else class="status">Only the owner can see billing.</p>
</template>

<style>
.ob { max-width: 640px; }
</style>
