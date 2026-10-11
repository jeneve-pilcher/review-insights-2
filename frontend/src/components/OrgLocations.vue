<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { orgApi } from '../api'
import { linksFromText, linksToText } from '../utils/providers'
import { csvPreview, ratingClass, timeAgo } from '../utils/orgFormat'

const props = defineProps({
  info: { type: Object, required: true },
})
// Doctor pages are an opt-in feature (an administrator turns it on) for healthcare industries.
const providersOn = computed(() => Boolean(props.info.org.provider_data_enabled && props.info.org.pack?.provider_level))
const emit = defineEmits(['open', 'changed'])

const rows = ref([])
const loading = ref(true)
const error = ref('')
const message = ref('')

const blank = () => ({ name: '', google_query: '', brand: '', region: '', yelp_url: '', opentable_url: '', doordash_url: '', ubereats_url: '', grubhub_url: '', manager_email: '', provider_links_text: '' })
const form = ref(blank())
const editingId = ref(null)
const saving = ref(false)
const running = reactive({})

async function load() {
  loading.value = true
  error.value = ''
  try {
    rows.value = await orgApi.locations()
  } catch (err) {
    error.value = err?.response?.data?.detail || 'Could not load locations.'
  } finally {
    loading.value = false
  }
}

onMounted(load)

async function submit() {
  saving.value = true
  message.value = ''
  try {
    const body = Object.fromEntries(Object.entries(form.value).map(([k, v]) => [k, v.trim()]))
    delete body.provider_links_text
    if (providersOn.value) body.provider_links = linksFromText(form.value.provider_links_text)
    if (editingId.value) await orgApi.updateLocation(editingId.value, body)
    else await orgApi.addLocation(body)
    message.value = editingId.value ? 'Location updated.' : 'Location added. Its first check runs within about half an hour, or press Run now.'
    form.value = blank()
    editingId.value = null
    await load()
    emit('changed')
  } catch (err) {
    message.value = err?.response?.data?.detail || 'Could not save the location.'
  } finally {
    saving.value = false
  }
}

function edit(row) {
  editingId.value = row.id
  form.value = {
    name: row.name,
    google_query: row.google_query,
    brand: row.brand || '',
    region: row.region || '',
    yelp_url: row.yelp_url || '',
    opentable_url: row.opentable_url || '',
    doordash_url: row.doordash_url || '',
    ubereats_url: row.ubereats_url || '',
    grubhub_url: row.grubhub_url || '',
    provider_links_text: linksToText(row.provider_links),
    manager_email: row.manager_email || '',
  }
  message.value = ''
}

function cancelEdit() {
  editingId.value = null
  form.value = blank()
}

async function remove(row) {
  if (!window.confirm(`Delete ${row.name}? Its history and tasks are removed too.`)) return
  try {
    await orgApi.deleteLocation(row.id)
    await load()
    emit('changed')
  } catch (err) {
    message.value = err?.response?.data?.detail || 'Could not delete the location.'
  }
}

async function run(row) {
  running[row.id] = true
  message.value = ''
  try {
    const res = await orgApi.runLocation(row.id)
    message.value =
      `${row.name}: checked. ${res.new_alerts} new negative review${res.new_alerts === 1 ? '' : 's'}` +
      `${res.emailed ? ' (manager emailed)' : ''}; ${res.fresh_reviews} reviews bought.`
    await load()
    emit('changed')
  } catch (err) {
    message.value = err?.response?.data?.detail || 'The check failed.'
  } finally {
    running[row.id] = false
  }
}

// ---- CSV import
const csv = ref('')
const importResult = ref(null)
const importing = ref(false)
const preview = computed(() => csvPreview(csv.value))

function onFile(event) {
  const file = event.target.files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => {
    csv.value = String(reader.result || '')
  }
  reader.readAsText(file)
}

async function importCsv() {
  importing.value = true
  importResult.value = null
  try {
    importResult.value = await orgApi.importLocations(csv.value)
    if (importResult.value.added) {
      csv.value = ''
      await load()
      emit('changed')
    }
  } catch (err) {
    importResult.value = { added: 0, skipped: [], error: err?.response?.data?.detail || 'Import failed.' }
  } finally {
    importing.value = false
  }
}
</script>

<template>
  <div>
    <p v-if="message" class="status analysis-note">{{ message }}</p>

    <section v-if="info.can.manage_locations" class="oc-card" style="margin-bottom: 18px">
      <h4 style="margin-top: 0">{{ editingId ? 'Edit location' : 'Add a location' }}</h4>
      <div class="analysis-form">
        <label class="field"><span>Name</span><input v-model="form.name" type="text" placeholder="Downtown" /></label>
        <label class="field" style="min-width: 260px">
          <span>Google search (name + address)</span>
          <input v-model="form.google_query" type="text" placeholder="Acme Grill, 123 Main St, Austin TX" />
        </label>
        <label class="field"><span>Brand</span><input v-model="form.brand" type="text" /></label>
        <label class="field"><span>Region</span><input v-model="form.region" type="text" /></label>
        <label class="field"><span>Yelp page (optional)</span><input v-model="form.yelp_url" type="text" placeholder="https://www.yelp.com/biz/..." /></label>
        <label class="field"><span>OpenTable page (optional)</span><input v-model="form.opentable_url" type="text" placeholder="https://www.opentable.com/r/..." /></label>
        <label class="field"><span>DoorDash page (optional)</span><input v-model="form.doordash_url" type="text" placeholder="https://www.doordash.com/store/...-123456/" /></label>
        <label class="field"><span>Uber Eats page (optional)</span><input v-model="form.ubereats_url" type="text" placeholder="https://www.ubereats.com/store/.../abc123" /></label>
        <label class="field"><span>Grubhub page (optional)</span><input v-model="form.grubhub_url" type="text" placeholder="https://www.grubhub.com/restaurant/.../123456/" /></label>
        <label v-if="providersOn" class="field" style="grid-column: 1 / -1">
          <span>Zocdoc doctor pages (one link per line, up to 10)</span>
          <textarea v-model="form.provider_links_text" rows="3" placeholder="https://www.zocdoc.com/doctor/jane-doe-md-12345"></textarea>
          <small class="oc-note">Provider-level numbers for these doctors appear on the location's page. Each refresh is billed per result, so scheduled checks refresh them at most weekly.</small>
        </label>
        <label class="field"><span>Manager email</span><input v-model="form.manager_email" type="text" placeholder="gm@company.com" /></label>
        <button class="oc-btn" :disabled="saving" @click="submit">{{ editingId ? 'Save changes' : 'Add location' }}</button>
        <button v-if="editingId" class="oc-btn" @click="cancelEdit">Cancel</button>
      </div>
      <p class="oc-note">
        Negative reviews for a location are emailed to its manager (or to the owner if none is set) and
        appear on the Tasks tab. Managers see only their own location.
      </p>

      <details style="margin-top: 10px">
        <summary><strong>Import many locations from a spreadsheet (CSV)</strong></summary>
        <p class="oc-note">
          First row = headers: <code>name, google_query</code> required; optional
          <code>brand, region, yelp_url, opentable_url, doordash_url, ubereats_url, grubhub_url, manager_email</code>. (Also understood: address, yelp, opentable, doordash, ubereats, grubhub, manager.)
          Export your spreadsheet as CSV, then choose the file or paste it below.
        </p>
        <input type="file" accept=".csv,text/csv" @change="onFile" />
        <textarea v-model="csv" rows="5" style="width: 100%; margin-top: 8px" placeholder="name,brand,region,google_query,manager_email"></textarea>
        <p v-if="csv" class="oc-note">
          Found {{ preview.rows }} data row{{ preview.rows === 1 ? '' : 's' }} · columns: {{ preview.headers.join(', ') || 'none' }}
        </p>
        <button class="oc-btn" :disabled="importing || !csv.trim()" @click="importCsv">Import</button>
        <template v-if="importResult">
          <p v-if="importResult.error" class="status error">{{ importResult.error }}</p>
          <p v-else class="oc-note" style="color: #333">
            Added {{ importResult.added }}; skipped {{ importResult.skipped.length }}.
          </p>
          <ul v-if="importResult.skipped && importResult.skipped.length" class="oc-note">
            <li v-for="s in importResult.skipped" :key="s.row">Row {{ s.row }}: {{ s.reason }}</li>
          </ul>
        </template>
      </details>
    </section>

    <p v-if="loading" class="status">Loading locations…</p>
    <p v-else-if="error" class="status error">{{ error }}</p>
    <p v-else-if="!rows.length" class="status">No locations yet.</p>

    <div v-else class="oc-scroll">
      <table class="oc-table">
        <thead>
          <tr>
            <th>Location</th><th>Manager</th><th>Rating</th><th>Reviews</th><th>Tasks</th><th>Checked</th><th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in rows" :key="r.id">
            <td>
              <button class="oc-link" @click="emit('open', r.id)"><strong>{{ r.name }}</strong></button>
              <div class="oc-note" style="margin: 0">
                {{ [r.brand, r.region].filter(Boolean).join(' · ') }}
                <span v-if="r.top_theme" class="oc-chip" :title="`${r.top_theme.label} is ${r.top_theme.flag} lately`">
                  {{ r.top_theme.flag === 'rising' ? '↑' : '↓' }} {{ r.top_theme.label }}
                </span>
                <span v-if="r.yelp_url" class="oc-chip">+ Yelp</span>
                <span v-if="r.opentable_url" class="oc-chip">+ OpenTable</span>
                <span v-if="r.doordash_url" class="oc-chip">+ DoorDash</span>
                <span v-if="r.ubereats_url" class="oc-chip">+ Uber Eats</span>
                <span v-if="r.grubhub_url" class="oc-chip">+ Grubhub</span>
                <span v-if="!r.is_active" class="oc-chip warn">paused</span>
              </div>
            </td>
            <td>{{ r.manager_email || '–' }}</td>
            <td :class="ratingClass(r.snapshot?.avg_rating)">{{ r.snapshot?.avg_rating ?? '–' }}</td>
            <td>{{ r.snapshot?.reviews_total ?? '–' }}</td>
            <td>{{ r.open_alerts }}</td>
            <td>{{ timeAgo(r.snapshot?.run_at) }}</td>
            <td style="white-space: nowrap">
              <button v-if="info.can.run_location" class="oc-btn" :disabled="running[r.id]" @click="run(r)">
                {{ running[r.id] ? 'Checking…' : 'Run now' }}
              </button>
              <button class="oc-btn" @click="emit('open', r.id)">Open</button>
              <template v-if="info.can.manage_locations">
                <button class="oc-btn" @click="edit(r)">Edit</button>
                <button class="oc-btn danger" @click="remove(r)">Delete</button>
              </template>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
