<script setup>
import { computed, onMounted, ref } from 'vue'
import { orgApi } from '../api'
import { explainError } from '../utils/errors'
import { ROLE_LABELS, visibleTabs } from '../utils/orgFormat'
import LocationDetail from './LocationDetail.vue'
import OrgActivity from './OrgActivity.vue'
import OrgBenchmarks from './OrgBenchmarks.vue'
import OrgBilling from './OrgBilling.vue'
import OrgLocations from './OrgLocations.vue'
import OrgOverview from './OrgOverview.vue'
import OrgSetup from './OrgSetup.vue'
import OrgTasks from './OrgTasks.vue'
import OrgTeam from './OrgTeam.vue'

const props = defineProps({
  me: { type: Object, required: true },
})

const info = ref(null)
const loading = ref(true)
const notMember = ref(false)
const error = ref('')
const tab = ref('overview')
const openLocationId = ref(null)

async function load() {
  loading.value = true
  error.value = ''
  notMember.value = false
  try {
    info.value = await orgApi.get()
  } catch (err) {
    if (err?.response?.status === 403) notMember.value = true
    else error.value = explainError(err, 'Could not load your company')
  } finally {
    loading.value = false
  }
}

// Quietly re-read budget/usage after something changed, without blanking the screen.
async function refresh() {
  try {
    info.value = await orgApi.get()
  } catch {
    /* keep showing what we have */
  }
}

onMounted(load)

const tabs = computed(() => visibleTabs(info.value?.can, Boolean(info.value?.billing)))
</script>

<template>
  <section class="oc-console">
    <p v-if="loading" class="status">Loading your company…</p>
    <OrgSetup v-else-if="notMember" :tier="me.tier" @created="load" />
    <p v-else-if="error" class="status error">{{ error }}</p>

    <template v-else-if="info">
      <div class="oc-head">
        <h2>🏢 {{ info.org.name }}</h2>
        <span class="oc-role">{{ ROLE_LABELS[info.role] }}</span>
      </div>

      <LocationDetail
        :info="info"
        v-if="openLocationId"
        :location-id="openLocationId"
        @back="openLocationId = null"
        @changed="refresh"
      />

      <template v-else>
        <div class="oc-tabs">
          <button
            v-for="t in tabs"
            :key="t.id"
            class="oc-tab"
            :class="{ active: tab === t.id }"
            @click="tab = t.id"
          >
            {{ t.label }}
          </button>
        </div>

        <OrgOverview v-if="tab === 'overview'" :info="info" @open="openLocationId = $event" @changed="refresh" />
        <OrgLocations v-else-if="tab === 'locations'" :info="info" @open="openLocationId = $event" @changed="refresh" />
        <OrgBenchmarks v-else-if="tab === 'benchmarks'" :info="info" @open="openLocationId = $event" />
        <OrgTasks v-else-if="tab === 'tasks'" :info="info" />
        <OrgTeam v-else-if="tab === 'team'" :info="info" @changed="refresh" />
        <OrgActivity v-else-if="tab === 'activity'" />
        <OrgBilling v-else-if="tab === 'billing'" :info="info" />
      </template>
    </template>
  </section>
</template>

<style>
.oc-console {
  margin-top: 6px;
}

.oc-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}

.oc-head h2 {
  margin: 0;
  font-size: 20px;
}

.oc-role {
  background: #efeaff;
  color: #5b3fc4;
  font-size: 12px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 999px;
}

.oc-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 18px;
  border-bottom: 1px solid #e4e6ea;
}

.oc-tab {
  border: none;
  background: none;
  padding: 9px 16px;
  font-size: 14px;
  cursor: pointer;
  color: #666;
  border-bottom: 3px solid transparent;
}

.oc-tab.active {
  color: #1a1a1a;
  font-weight: 700;
  border-bottom-color: var(--brand, #ff4b4b);
}

.oc-card {
  background: #f7f8fa;
  border: 1px solid #e4e6ea;
  border-radius: 10px;
  padding: 14px 16px;
}

.oc-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}

.oc-stat .label {
  display: block;
  font-size: 12px;
  color: #666;
}

.oc-stat .value {
  display: block;
  font-size: 22px;
  font-weight: 700;
}

.oc-stat .sub {
  display: block;
  font-size: 11px;
  color: #888;
}

.oc-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.oc-table th {
  text-align: left;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: #888;
  padding: 6px 8px;
  border-bottom: 1px solid #e4e6ea;
}

.oc-table td {
  padding: 8px;
  border-bottom: 1px solid #eef0f3;
  vertical-align: top;
}

.oc-scroll {
  overflow-x: auto;
}

.oc-good { color: #1e8e4e; font-weight: 700; }
.oc-ok { color: #8a6200; font-weight: 700; }
.oc-bad { color: #c0392b; font-weight: 700; }

.oc-chip {
  display: inline-block;
  background: #eef0f3;
  color: #444;
  font-size: 11px;
  padding: 2px 9px;
  border-radius: 999px;
  margin: 0 4px 4px 0;
}

.oc-chip.warn { background: #fff1dc; color: #a35a00; }

.oc-link {
  background: none;
  border: none;
  color: #1a5f9e;
  cursor: pointer;
  padding: 0;
  font-size: inherit;
  text-decoration: underline;
}

.oc-btn {
  border: 1px solid #d3d6db;
  background: white;
  border-radius: 6px;
  padding: 4px 11px;
  font-size: 12px;
  cursor: pointer;
}

.oc-btn:disabled {
  opacity: 0.5;
  cursor: default;
}

.oc-btn.danger {
  color: #c0392b;
  border-color: #f0c4be;
}

.oc-bar {
  height: 10px;
  background: #e4e6ea;
  border-radius: 5px;
  overflow: hidden;
}

.oc-bar > div {
  height: 100%;
  background: var(--accent, #7c5ce0);
}

.oc-bar.over > div {
  background: #e74c3c;
}

.oc-note {
  font-size: 12px;
  color: #777;
  margin: 8px 0;
}
</style>
