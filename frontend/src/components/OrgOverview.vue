<script setup>
import { computed, onMounted, ref } from 'vue'
import { orgApi } from '../api'
import { ratingClass, signed, usagePct } from '../utils/orgFormat'

const props = defineProps({
  info: { type: Object, required: true },
})
const emit = defineEmits(['open', 'changed'])

const data = ref(null)
const loading = ref(true)
const error = ref('')

const budgetInput = ref(props.info.org.monthly_budget_reviews)
const savingBudget = ref(false)
const budgetMessage = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    data.value = await orgApi.overview()
  } catch (err) {
    error.value = err?.response?.data?.detail || 'Could not load the overview.'
  } finally {
    loading.value = false
  }
}

onMounted(load)

const usage = computed(() => data.value?.usage ?? props.info.usage)
const pct = computed(() => usagePct(usage.value))

async function saveBudget() {
  const n = Number(budgetInput.value)
  if (!Number.isInteger(n) || n < 0) {
    budgetMessage.value = 'Enter a whole number of reviews (0 or more).'
    return
  }
  savingBudget.value = true
  budgetMessage.value = ''
  try {
    await orgApi.setBudget(n)
    budgetMessage.value = 'Saved.'
    emit('changed')
    await load()
  } catch (err) {
    budgetMessage.value = err?.response?.data?.detail || 'Could not save the budget.'
  } finally {
    savingBudget.value = false
  }
}
</script>

<template>
  <div>
    <p v-if="loading" class="status">Loading the overview…</p>
    <p v-else-if="error" class="status error">{{ error }}</p>

    <template v-else-if="data">
      <div class="oc-card" style="margin-bottom: 16px">
        <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px">
          <strong>Monthly review budget</strong>
          <span class="oc-note" style="margin: 0">
            {{ usage.used.toLocaleString() }} of {{ usage.budget.toLocaleString() }} reviews bought ·
            about ${{ usage.est_cost_usd }} so far
          </span>
        </div>
        <div class="oc-bar" :class="{ over: usage.over }" style="margin-top: 8px">
          <div :style="{ width: pct + '%' }"></div>
        </div>
        <p v-if="usage.over" class="oc-note" style="color: #c0392b">
          The budget has been used, so automatic checks are paused until next month or until it's raised.
        </p>
        <p class="oc-note">
          Locations refresh automatically every {{ info.limits.monitor_interval_hours }} hours using the last
          {{ info.limits.monitor_months }} months of reviews. Repeat pulls inside 30 minutes are free.
        </p>
        <div v-if="info.can.set_budget" class="analysis-form" style="margin-top: 8px">
          <label class="field">
            <span>Monthly budget (reviews)</span>
            <input v-model.number="budgetInput" type="number" min="0" step="500" />
          </label>
          <button class="oc-btn" :disabled="savingBudget" @click="saveBudget">Save budget</button>
          <span v-if="budgetMessage" class="oc-note">{{ budgetMessage }}</span>
        </div>
      </div>

      <div class="oc-grid">
        <div class="oc-card oc-stat">
          <span class="label">Locations</span>
          <span class="value">{{ data.totals.locations }}</span>
          <span class="sub">
            {{ data.totals.with_data }} with data<span v-if="data.totals.awaiting_first_run">,
              {{ data.totals.awaiting_first_run }} waiting for their first check</span>
          </span>
        </div>
        <div class="oc-card oc-stat">
          <span class="label">Average rating</span>
          <span class="value" :class="ratingClass(data.totals.avg_rating)">
            {{ data.totals.avg_rating ?? '–' }}<span v-if="data.totals.avg_rating">★</span>
          </span>
          <span class="sub">weighted by review count</span>
        </div>
        <div class="oc-card oc-stat">
          <span class="label">Reviews</span>
          <span class="value">{{ data.totals.reviews_total.toLocaleString() }}</span>
          <span class="sub">in the monitoring window</span>
        </div>
        <div class="oc-card oc-stat">
          <span class="label">1–2★ share</span>
          <span class="value">{{ data.totals.low_star_pct ?? '–' }}<span v-if="data.totals.low_star_pct != null">%</span></span>
        </div>
        <div class="oc-card oc-stat">
          <span class="label">Open tasks</span>
          <span class="value">{{ data.totals.open_alerts }}</span>
          <span class="sub">negative reviews to follow up</span>
        </div>
      </div>

      <p v-if="!data.totals.with_data" class="status">
        No location has been checked yet. Add locations on the Locations tab: the first automatic
        check runs within about half an hour, or press "Run now" on a location.
      </p>

      <template v-else>
        <h4>⚠️ Needs attention</h4>
        <p v-if="!data.attention.length" class="status">Nothing stands out right now.</p>
        <div v-for="a in data.attention" :key="a.location_id" class="oc-card" style="margin-bottom: 8px">
          <div style="display: flex; justify-content: space-between; gap: 8px; flex-wrap: wrap">
            <div>
              <button class="oc-link" @click="emit('open', a.location_id)"><strong>{{ a.name }}</strong></button>
              <span class="oc-note"> {{ [a.brand, a.region].filter(Boolean).join(' · ') }}</span>
            </div>
            <div>
              <span :class="ratingClass(a.avg_rating)">{{ a.avg_rating }}★</span>
              <span v-if="a.rating_change != null" class="oc-note"> ({{ signed(a.rating_change) }} since last check)</span>
            </div>
          </div>
          <span v-for="r in a.reasons" :key="r" class="oc-chip warn">{{ r }}</span>
        </div>

        <template v-if="data.shared_topics.length">
          <h4 style="margin-top: 22px">🔁 Problems showing up at several locations</h4>
          <p class="oc-note">Rising complaints that appear in more than one location's recent reviews.</p>
          <div v-for="t in data.shared_topics" :key="t.term" class="oc-card" style="margin-bottom: 6px">
            <strong>“{{ t.term }}”</strong> at {{ t.locations }} {{ t.locations === 1 ? 'location' : 'locations' }}
            <span class="oc-note"> — {{ t.names.join(', ') }}</span>
          </div>
        </template>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 18px; margin-top: 22px">
          <div v-for="grp in [{ title: 'By brand', rows: data.by_brand }, { title: 'By region', rows: data.by_region }]" :key="grp.title">
            <h4>{{ grp.title }}</h4>
            <div class="oc-scroll">
              <table class="oc-table">
                <thead>
                  <tr><th>Group</th><th>Locations</th><th>Rating</th><th>1–2★</th><th>Tasks</th></tr>
                </thead>
                <tbody>
                  <tr v-for="g in grp.rows" :key="g.key">
                    <td>{{ g.key }}</td>
                    <td>{{ g.locations }}</td>
                    <td :class="ratingClass(g.avg_rating)">{{ g.avg_rating ?? '–' }}</td>
                    <td>{{ g.low_star_pct ?? '–' }}%</td>
                    <td>{{ g.open_alerts }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 18px; margin-top: 22px">
          <div>
            <h4>📉 Biggest drops</h4>
            <p v-if="!data.drops.length" class="oc-note">No location got worse since its last check.</p>
            <div v-for="d in data.drops" :key="d.location_id" class="oc-note" style="color: #333">
              <button class="oc-link" @click="emit('open', d.location_id)">{{ d.name }}</button>
              <span class="oc-bad"> {{ signed(d.change) }}★</span> → {{ d.avg_rating }}★
            </div>
          </div>
          <div>
            <h4>📈 Biggest gains</h4>
            <p v-if="!data.gains.length" class="oc-note">No location improved since its last check.</p>
            <div v-for="d in data.gains" :key="d.location_id" class="oc-note" style="color: #333">
              <button class="oc-link" @click="emit('open', d.location_id)">{{ d.name }}</button>
              <span class="oc-good"> {{ signed(d.change) }}★</span> → {{ d.avg_rating }}★
            </div>
          </div>
        </div>
      </template>
    </template>
  </div>
</template>
