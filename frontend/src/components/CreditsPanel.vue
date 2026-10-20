<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { creditsApi } from '../api'
import { explainError } from '../utils/errors'
import { allowancePct, formatUsd, ledgerLabel, limitLine, limitPct, packLabel } from '../utils/credits'
import { timeAgo } from '../utils/orgFormat'

const props = defineProps({
  // 'user' = your own account (plan allowance, then credit); 'org' = the company's shared credit.
  scope: { type: String, default: 'user' },
})
const emit = defineEmits(['loaded'])

const route = useRoute()
const router = useRouter()
const info = ref(null)
const loading = ref(true)
const error = ref('')
const message = ref('')
const buying = ref('')
const isOrg = computed(() => props.scope === 'org')
const pct = computed(() => allowancePct(info.value))
const limitText = computed(() => limitLine(info.value))
const limitPercent = computed(() => limitPct(info.value))

// The monthly spending limit: the same control for your own account and for a company.
const limitInput = ref('')
const savingLimit = ref(false)
const limitMessage = ref('')

async function saveLimit() {
  const blank = limitInput.value === '' || limitInput.value === null
  const n = blank ? null : Number(limitInput.value)
  if (!blank && (!Number.isFinite(n) || n <= 0)) {
    limitMessage.value = 'Enter an amount above $0, or leave it blank for no limit.'
    return
  }
  savingLimit.value = true
  limitMessage.value = ''
  try {
    await creditsApi.setLimit(n, props.scope)
    limitMessage.value = n === null ? 'Limit removed.' : 'Saved.'
    await load()
  } catch (err) {
    limitMessage.value = err?.response?.data?.detail || 'Could not save the limit.'
  } finally {
    savingLimit.value = false
  }
}

async function load() {
  try {
    info.value = await creditsApi.get(props.scope)
    limitInput.value = info.value.monthly_limit_usd ?? ''
    emit('loaded', info.value)
  } catch (err) {
    error.value = explainError(err, 'Could not load your credit')
  } finally {
    loading.value = false
  }
}

// Coming back from Stripe: add the credit for that payment (the server re-checks it with Stripe).
async function handleReturn() {
  const q = route.query
  if (q.credits === 'cancelled' && !isOrg.value) message.value = "Purchase cancelled. You weren't charged."
  if (q.credits === 'success' && q.session_id && (q.scope ?? 'user') === props.scope) {
    try {
      const res = await creditsApi.confirm(String(q.session_id))
      message.value =
        res.status !== 'paid'
          ? "Your payment is still processing. Reload in a moment and it will be added."
          : res.credited
            ? `Thank you! ${formatUsd(res.credit_usd)} of credit was added.`
            : 'That payment was already added to your balance.'
    } catch (err) {
      error.value = err?.response?.data?.detail || 'Could not confirm that payment.'
    }
    router.replace({ query: {} })
  }
  if (q.credits === 'cancelled') router.replace({ query: {} })
}

async function buy(pack) {
  buying.value = pack.id
  error.value = ''
  try {
    const { checkout_url } = await creditsApi.checkout(pack.id, props.scope)
    window.location.href = checkout_url
  } catch (err) {
    error.value = err?.response?.data?.detail || 'Could not start checkout.'
    buying.value = ''
  }
}

onMounted(async () => {
  await handleReturn()
  await load()
})
defineExpose({ reload: load })
</script>

<template>
  <section class="chart-section">
    <div class="title-row">
      <h3>💳 {{ isOrg ? 'Company credit' : 'Usage & credit' }}</h3>
    </div>

    <p v-if="loading" class="status">Loading…</p>
    <p v-if="message" class="status success">{{ message }}</p>
    <p v-if="error" class="status error">{{ error }}</p>

    <template v-if="info">
      <p v-if="!info.enforced" class="chart-desc">Usage billing is switched off, so nothing is charged.</p>

      <template v-else>
        <p class="chart-desc">
          <template v-if="isOrg">
            Everything your team runs (scheduled checks, manual checks, deep dives and AI reply drafts) is paid from
            this shared credit. When it runs out, automatic checks pause until the owner adds more.
          </template>
          <template v-else>
            Your plan includes a monthly usage allowance, spent first. Heavy use after that comes from prepaid credit.
            Credit pays for what each run actually uses (review and web-search data, AI drafts), shown before and after
            every run. Repeat clicks within 30 minutes are free.
          </template>
        </p>

        <div class="oc-grid">
          <div class="oc-card oc-stat">
            <span class="label">Credit balance</span>
            <span class="value" :class="{ 'rating-low': info.balance_usd < 0 }">{{ formatUsd(info.balance_usd) }}</span>
          </div>
          <div v-if="!isOrg" class="oc-card oc-stat">
            <span class="label">Plan allowance left</span>
            <span class="value">{{ formatUsd(info.allowance_remaining_usd) }}</span>
            <span class="sub">of {{ formatUsd(info.allowance_usd) }} this month</span>
          </div>
          <div class="oc-card oc-stat">
            <span class="label">Available now</span>
            <span class="value">{{ formatUsd(info.available_usd) }}</span>
          </div>
        </div>

        <div v-if="!isOrg && info.allowance_usd" class="oc-bar" :title="`${pct}% of this month's allowance used`" style="margin: 8px 0">
          <div class="oc-bar-fill" :style="{ width: pct + '%' }"></div>
        </div>

        <div v-if="info.can_buy">
          <div class="oc-note">Buy credit. Each pack shows what you pay and the credit you get:</div>
          <div class="oc-actions">
            <button v-for="p in info.packs" :key="p.id" class="oc-btn" :disabled="buying !== ''" @click="buy(p)">
              {{ buying === p.id ? 'Opening checkout…' : packLabel(p) }}
            </button>
          </div>
        </div>
        <p v-else class="oc-note">
          <template v-if="isOrg">Only the company owner can add credit.</template>
          <template v-else>Credit is for Pro and Enterprise accounts. Upgrade to add credit when you need more than the free allowance.</template>
        </p>

        <details v-if="info.recent.length" style="margin-top: 10px">
          <summary class="oc-note">Recent activity</summary>
          <table class="oc-table">
            <tbody>
              <tr v-for="(r, i) in info.recent" :key="i">
                <td class="muted">{{ timeAgo(r.created_at) }}</td>
                <td>{{ ledgerLabel(r) }}</td>
                <td class="muted">{{ r.description }}</td>
                <td>{{ formatUsd(r.balance_after) }}</td>
              </tr>
            </tbody>
          </table>
        </details>
      </template>
    </template>
  </section>
</template>
