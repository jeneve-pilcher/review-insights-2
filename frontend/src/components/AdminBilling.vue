<script setup>
import { computed, onMounted, ref } from 'vue'
import { adminApi } from '../api'
import { explainError } from '../utils/errors'
import { tierLabel, usd } from '../utils/locationPricing'

// Operator only. One row per customer email domain: locations in use, what the contract bills, and the contract terms.
const data = ref(null)
const open = ref(false)
const error = ref('')
const saving = ref(false)
const editing = ref(null) // the contract form, or null
const detail = ref('')

async function load() {
  error.value = ''
  try {
    data.value = await adminApi.billing()
  } catch (err) {
    // Not an operator, or the contracts table doesn't exist yet: say nothing in the first case.
    if (err?.response?.status !== 404) error.value = explainError(err, 'Could not load billing')
  }
}
onMounted(load)

const lines = computed(() => data.value?.lines ?? [])

function edit(line) {
  const c = line.contract ?? {}
  editing.value = {
    domain: line.domain ?? '',
    company_name: c.company_name ?? (line.domain ? line.label : ''),
    minimum_locations: c.minimum_locations ?? 0,
    price_tiers: c.price_tiers ?? '',
    starts_on: c.starts_on ?? '',
    ends_on: c.ends_on ?? '',
    notes: c.notes ?? '',
    existing: Boolean(line.contract),
  }
}
function addNew() {
  editing.value = { domain: '', company_name: '', minimum_locations: 0, price_tiers: '', starts_on: '', ends_on: '', notes: '', existing: false }
}

async function save() {
  const f = editing.value
  saving.value = true
  error.value = ''
  try {
    await adminApi.saveContract(f.domain, {
      company_name: f.company_name, minimum_locations: Number(f.minimum_locations) || 0,
      price_tiers: f.price_tiers, starts_on: f.starts_on, ends_on: f.ends_on, notes: f.notes,
    })
    editing.value = null
    await load()
  } catch (err) {
    error.value = explainError(err, 'Could not save the contract')
  } finally {
    saving.value = false
  }
}

async function remove() {
  saving.value = true
  try {
    await adminApi.deleteContract(editing.value.domain)
    editing.value = null
    await load()
  } catch (err) {
    error.value = explainError(err, 'Could not remove the contract')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <section v-if="data" class="ab">
    <button class="oc-link ab-toggle" type="button" @click="open = !open">
      {{ open ? '▾' : '▸' }} Billing (operator): {{ data.totals.locations_used }} locations in use, {{ usd(data.totals.monthly_total) }} / month
    </button>

    <div v-if="open">
      <p class="lp-note">
        Locations are counted per customer email domain (the owner's, or the SSO domain), adding all their accounts together. Public mail
        domains such as gmail.com are listed one account at a time and cannot have a contract. The amount uses the contract's prices and
        minimum if there is one, otherwise the standard prices.
      </p>

      <table class="ab-table">
        <thead>
          <tr><th>Customer</th><th>Accounts</th><th>In use</th><th>Minimum</th><th>Billed</th><th>Per month</th><th></th></tr>
        </thead>
        <tbody>
          <template v-for="l in lines" :key="l.key">
            <tr>
              <td>
                <button class="oc-link" type="button" @click="detail = detail === l.key ? '' : l.key">{{ l.label }}</button>
                <div v-if="l.domain" class="lp-note">{{ l.domain }}{{ l.custom_prices ? ' · custom prices' : '' }}</div>
                <div v-if="l.price_tiers_invalid" class="status error">Contract prices are not valid, so standard prices were used.</div>
              </td>
              <td>{{ l.accounts }}</td>
              <td>{{ l.locations_used }}</td>
              <td>{{ l.minimum_locations || '–' }}</td>
              <td>{{ l.locations_billed }}</td>
              <td><strong>{{ usd(l.monthly_total) }}</strong></td>
              <td><button v-if="l.domain" class="oc-btn" type="button" @click="edit(l)">{{ l.contract ? 'Contract' : 'Add contract' }}</button></td>
            </tr>
            <tr v-if="detail === l.key">
              <td colspan="7" class="lp-note">
                <div v-for="o in l.organizations" :key="o.name + o.owner_email">{{ o.name }} · {{ o.owner_email }} · {{ o.locations }} locations</div>
                <div>
                  Prices:
                  <template v-for="(t, i) in l.tiers" :key="t.from">{{ i ? '; ' : '' }}{{ tierLabel(t) }} {{ usd(t.price_per_location) }}</template>
                </div>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
      <p v-if="!lines.length" class="lp-note">No companies yet.</p>

      <div class="ab-actions">
        <button class="oc-btn" type="button" @click="addNew">+ Contract for a domain</button>
        <button class="oc-btn" type="button" @click="adminApi.exportCsv()">Download CSV</button>
      </div>

      <form v-if="editing" class="ab-form" @submit.prevent="save">
        <h4>Contract</h4>
        <label class="field"><span>Email domain</span><input v-model="editing.domain" type="text" placeholder="acme.com" :disabled="editing.existing" required /></label>
        <label class="field"><span>Company name</span><input v-model="editing.company_name" type="text" /></label>
        <label class="field"><span>Minimum locations billed (0 = none)</span><input v-model.number="editing.minimum_locations" type="number" min="0" /></label>
        <label class="field"><span>Custom prices (blank = standard). Format: first location of each tier : dollars each</span><input v-model="editing.price_tiers" type="text" placeholder="1:45,500:35,1500:15" /></label>
        <label class="field"><span>Starts</span><input v-model="editing.starts_on" type="text" placeholder="2026-11-01" /></label>
        <label class="field"><span>Ends</span><input v-model="editing.ends_on" type="text" placeholder="2027-10-31" /></label>
        <label class="field"><span>Notes</span><textarea v-model="editing.notes" rows="2"></textarea></label>
        <button class="run-btn" type="submit" style="width: auto; padding: 8px 20px" :disabled="saving">{{ saving ? 'Saving…' : 'Save contract' }}</button>
        <button class="oc-btn" type="button" :disabled="saving" @click="editing = null">Cancel</button>
        <button v-if="editing.existing" class="oc-btn" type="button" :disabled="saving" @click="remove">Remove contract</button>
      </form>
      <p v-if="error" class="status error">{{ error }}</p>
    </div>
  </section>
  <p v-else-if="error" class="status error">{{ error }}</p>
</template>

<style>
.ab { margin: 10px 0 18px; padding: 10px 14px; border: 1px solid #fdba74; border-radius: 10px; background: #fffaf5; }
.ab-toggle { font-weight: 600; color: #7c2d12; }
.ab-table { width: 100%; border-collapse: collapse; font-size: 13px; margin: 8px 0; }
.ab-table th, .ab-table td { padding: 6px 8px; border-bottom: 1px solid #f1e4d8; text-align: left; vertical-align: top; }
.ab-actions { display: flex; gap: 10px; margin: 8px 0; }
.ab-form { margin-top: 10px; max-width: 520px; }
</style>
