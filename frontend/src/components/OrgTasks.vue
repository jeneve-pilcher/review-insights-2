<script setup>
import { onMounted, reactive, ref } from 'vue'
import { orgApi } from '../api'

const props = defineProps({
  info: { type: Object, required: true },
})

const status = ref('open')
const alerts = ref([])
const loading = ref(true)
const error = ref('')
const message = ref('')
const edits = reactive({})
const busy = reactive({})

const SOURCE_LABELS = { google: 'Google', yelp: 'Yelp' }
const STATUS_LABELS = { open: 'Open', acknowledged: 'In progress', resolved: 'Resolved' }

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
      Every new 1–2★ review (Google and Yelp, including star-only ratings) becomes a task for its
      location. Tell the right person, add a note once you've followed up, then mark it resolved.
      Personal details are removed from the text.
    </p>
    <p v-if="message" class="status error">{{ message }}</p>

    <p v-if="loading" class="status">Loading tasks…</p>
    <p v-else-if="error" class="status error">{{ error }}</p>
    <p v-else-if="!alerts.length" class="status">Nothing here. 🎉</p>

    <div v-for="a in alerts" :key="a.id" class="oc-card" style="margin-bottom: 10px">
      <div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: center">
        <strong>{{ a.location_name }}</strong>
        <span class="oc-bad">{{ a.rating }}★</span>
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
