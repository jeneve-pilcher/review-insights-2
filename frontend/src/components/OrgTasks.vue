<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { orgApi } from '../api'
import { filterByTheme, themeCounts } from '../utils/industryOrg'

const props = defineProps({
  info: { type: Object, required: true },
})

const status = ref('open')
const themeFilter = ref('')
const alerts = ref([])
const loading = ref(true)
const error = ref('')
const message = ref('')
const edits = reactive({})
const busy = reactive({})

const SOURCE_LABELS = { google: 'Google', yelp: 'Yelp', opentable: 'OpenTable', doordash: 'DoorDash', grubhub: 'Grubhub' }
const STATUS_LABELS = { open: 'Open', acknowledged: 'In progress', resolved: 'Resolved' }

// The industry's themes, so tasks can be filtered by what the review is about.
const themeChips = computed(() => themeCounts(alerts.value, props.info.org.pack))
const themeLabels = computed(() => Object.fromEntries((props.info.org.pack?.themes ?? []).map((t) => [t.id, t.label])))
const shown = computed(() => filterByTheme(alerts.value, themeFilter.value))

async function load() {
  loading.value = true
  error.value = ''
  try {
    alerts.value = await orgApi.alerts(status.value || undefined)
    for (const a of alerts.value) edits[a.id] = { assigned_to: a.assigned_to || '', note: a.note || '' }
  } catch (err) {
    error.value = err?.response?.data?.detail || 'Could not load tasks.'
  } finally {
    loading.value = false
  }
}

onMounted(load)

async function save(alert, nextStatus) {
  busy[alert.id] = true
  message.value = ''
  try {
    await orgApi.updateAlert(alert.id, {
      ...(nextStatus ? { status: nextStatus } : {}),
      assigned_to: edits[alert.id].assigned_to.trim(),
      note: edits[alert.id].note,
    })
    await load()
  } catch (err) {
    message.value = err?.response?.data?.detail || 'Could not save.'
  } finally {
    busy[alert.id] = false
  }
}
</script>

<template>
  <div>
    <div class="analysis-form" style="margin-bottom: 12px">
      <label class="field">
        <span>Show</span>
        <select v-model="status" class="months-select" @change="load">
          <option value="open">Open</option>
          <option value="acknowledged">In progress</option>
          <option value="resolved">Resolved</option>
          <option value="">Everything</option>
        </select>
      </label>
    </div>
    <p class="oc-note">
      Every new 1–2★ review (Google, Yelp, OpenTable, DoorDash and Grubhub, including star-only ratings) becomes a task for its
      location. Tell the right person, add a note once you've followed up, then mark it resolved.
      Personal details are removed from the text.
    </p>
    <p v-if="message" class="status error">{{ message }}</p>

    <p v-if="loading" class="status">Loading tasks…</p>
    <p v-else-if="error" class="status error">{{ error }}</p>
    <p v-else-if="!alerts.length" class="status">Nothing here. 🎉</p>

    <div v-if="themeChips.length" style="margin: 0 0 12px">
      <span class="oc-note" style="margin-right: 6px">What it's about ({{ info.org.pack.label }}):</span>
      <button class="oc-btn" style="margin: 0 6px 6px 0" :style="themeFilter === '' ? 'font-weight: 600' : 'opacity: 0.6'" @click="themeFilter = ''">All</button>
      <button
        v-for="c in themeChips"
        :key="c.id"
        class="oc-btn"
        style="margin: 0 6px 6px 0"
        :style="themeFilter === c.id ? 'font-weight: 600' : 'opacity: 0.6'"
        @click="themeFilter = themeFilter === c.id ? '' : c.id"
      >
        {{ c.label }} ({{ c.count }})
      </button>
    </div>

    <div v-for="a in shown" :key="a.id" class="oc-card" style="margin-bottom: 10px">
      <div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: center">
        <strong>{{ a.location_name }}</strong>
        <span class="oc-bad">{{ a.rating }}★</span>
        <span v-for="t in a.themes" :key="t" class="oc-chip">{{ themeLabels[t] ?? t }}</span>
        <span class="oc-chip">{{ SOURCE_LABELS[a.source] ?? a.source }}</span>
        <span class="oc-note" style="margin: 0">{{ String(a.review_date || '').slice(0, 10) }}</span>
        <span class="oc-chip" :class="{ warn: a.status === 'open' }">{{ STATUS_LABELS[a.status] }}</span>
      </div>
      <p v-if="a.has_text" style="margin: 8px 0">{{ a.text }}</p>
      <p v-else class="oc-note" style="font-style: italic">Star rating only, no written comment.</p>

      <div v-if="info.can.update_alert" class="analysis-form">
        <label class="field" style="min-width: 200px">
          <span>Assigned to (team email)</span>
          <input v-model="edits[a.id].assigned_to" type="text" placeholder="gm@company.com" />
        </label>
        <label class="field" style="flex: 1; min-width: 220px">
          <span>Note</span>
          <input v-model="edits[a.id].note" type="text" placeholder="What was done?" />
        </label>
      </div>
      <div v-if="info.can.update_alert" style="margin-top: 8px; display: flex; gap: 6px; flex-wrap: wrap">
        <button class="oc-btn" :disabled="busy[a.id]" @click="save(a, null)">Save note / assignee</button>
        <button v-if="a.status === 'open'" class="oc-btn" :disabled="busy[a.id]" @click="save(a, 'acknowledged')">Start working on it</button>
        <button v-if="a.status !== 'resolved'" class="oc-btn" :disabled="busy[a.id]" @click="save(a, 'resolved')">Mark resolved</button>
        <button v-else class="oc-btn" :disabled="busy[a.id]" @click="save(a, 'open')">Reopen</button>
      </div>
      <p v-else-if="a.note" class="oc-note">Note: {{ a.note }}</p>
    </div>
  </div>
</template>
