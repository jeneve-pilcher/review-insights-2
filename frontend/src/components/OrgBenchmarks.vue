<script setup>
import { computed, onMounted, ref } from 'vue'
import { orgApi } from '../api'
import { percentileClass, signed } from '../utils/orgFormat'
import OrgIndustryBenchmarks from './OrgIndustryBenchmarks.vue'

const props = defineProps({
  info: { type: Object, required: true },
})
const emit = defineEmits(['open'])

const groupBy = ref('all')
const data = ref(null)
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    data.value = await orgApi.benchmarks(groupBy.value)
  } catch (err) {
    error.value = err?.response?.data?.detail || 'Could not load benchmarks.'
  } finally {
    loading.value = false
  }
}

onMounted(load)

const metricKeys = computed(() => Object.keys(data.value?.metric_labels ?? {}))
const isManager = computed(() => props.info.role === 'manager')

function cell(row, key) {
  const m = row.metrics[key]
  if (!m) return '–'
  return m.rank ? `${m.value} (#${m.rank} of ${m.of})` : `${m.value}`
}

function vs(row, key) {
  const m = row.metrics[key]
  return m ? `${signed(m.vs_median)} vs median ${m.median}` : ''
}
</script>

<template>
  <div>
    <OrgIndustryBenchmarks @open="emit('open', $event)" />

    <div class="analysis-form" style="margin-bottom: 12px">
      <label class="field">
        <span>Compare each location against</span>
        <select v-model="groupBy" class="months-select" @change="load">
          <option value="all">Every location</option>
          <option value="brand">Locations of the same brand</option>
          <option value="region">Locations in the same region</option>
        </select>
      </label>
    </div>

    <p v-if="loading" class="status">Loading benchmarks…</p>
    <p v-else-if="error" class="status error">{{ error }}</p>

    <template v-else-if="data">
      <p class="oc-note">
        Rank 1 is the best in the group. Rankings and flags need at least {{ data.min_peers }} locations
        with data in a group.
        <span v-if="isManager"> You see your own location(s) compared with the group; other locations' names and numbers are hidden.</span>
      </p>
      <p v-if="data.awaiting_first_run.length" class="oc-note">
        Waiting for their first check: {{ data.awaiting_first_run.join(', ') }}
      </p>

      <div class="oc-grid">
        <div v-for="(g, key) in data.groups" :key="key" class="oc-card oc-stat">
          <span class="label">{{ key }}</span>
          <span class="value">{{ g.median.avg_rating ?? '–' }}<span v-if="g.median.avg_rating">★</span></span>
          <span class="sub">median rating · {{ g.count }} {{ g.count === 1 ? 'location' : 'locations' }}<span v-if="!g.rankable"> · too few to rank</span></span>
        </div>
      </div>

      <p v-if="!data.rows.length" class="status">No data yet. Run a check on your locations first.</p>

      <div v-else class="oc-scroll">
        <table class="oc-table">
          <thead>
            <tr>
              <th>Location</th>
              <th v-for="k in metricKeys" :key="k">{{ data.metric_labels[k] }}</th>
              <th>Flags</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in data.rows" :key="r.location_id">
              <td>
                <button class="oc-link" @click="emit('open', r.location_id)"><strong>{{ r.name }}</strong></button>
                <div class="oc-note" style="margin: 0">{{ r.group }}</div>
              </td>
              <td v-for="k in metricKeys" :key="k" :class="percentileClass(r.metrics[k]?.percentile)" :title="vs(r, k)">
                {{ cell(r, k) }}
              </td>
              <td>
                <span v-for="f in r.flags" :key="f" class="oc-chip warn">{{ f }}</span>
                <span v-if="!r.flags.length" class="oc-note">–</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>
