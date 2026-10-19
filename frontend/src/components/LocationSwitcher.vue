<script setup>
// Dashboard location switcher for company managers: pick one of the locations you manage and the dashboard shows it.
// Locations come from /api/org/locations, which already returns only the ones this person may see.
import { computed, onMounted, ref } from 'vue'
import { orgApi } from '../api'

const props = defineProps({
  modelValue: { type: String, default: '' },        // a location id, or "own" for the person's own business
  hasOwn: { type: Boolean, default: false },         // also offer "My own business"
})
const emit = defineEmits(['update:modelValue', 'loaded'])

const KEY = 'ri-active-location'
const locations = ref([])
const loading = ref(true)
const error = ref('')
const search = ref('')

function remembered() {
  try { return localStorage.getItem(KEY) || '' } catch { return '' }
}
function remember(v) {
  try { localStorage.setItem(KEY, v) } catch { /* private window: fine */ }
}

onMounted(async () => {
  try {
    const [info, locs] = await Promise.all([orgApi.get(), orgApi.locations()])
    locations.value = locs.filter((l) => l.is_active !== false)
    emit('loaded', info)
    const ids = new Set(locations.value.map((l) => l.id))
    const saved = remembered()
    const first = (saved && (ids.has(saved) || (saved === 'own' && props.hasOwn))) ? saved
      : (locations.value[0]?.id || (props.hasOwn ? 'own' : ''))
    if (first) emit('update:modelValue', first)
  } catch (err) {
    error.value = err?.response?.data?.detail || 'Could not load your locations.'
  } finally {
    loading.value = false
  }
})

function pick(v) {
  remember(v)
  emit('update:modelValue', v)
}

const many = computed(() => locations.value.length > 8)
const shown = computed(() => {
  const q = search.value.trim().toLowerCase()
  return q ? locations.value.filter((l) => `${l.name} ${l.region || ''} ${l.brand || ''}`.toLowerCase().includes(q)) : locations.value
})
const label = (l) => l.name + (l.region ? ` · ${l.region}` : '')
</script>

<template>
  <div class="ls">
    <p v-if="loading" class="status">Loading your locations…</p>
    <p v-else-if="error" class="status error">{{ error }}</p>
    <p v-else-if="!locations.length && !hasOwn" class="status">
      No locations are assigned to you yet. Ask your account administrator to set your email as the manager of a location.
    </p>
    <template v-else>
      <label class="ls-label" for="ls-select">Location</label>
      <input v-if="many" v-model="search" class="ls-search" type="search" placeholder="Search your locations" />
      <select id="ls-select" class="ls-select" :value="modelValue" @change="pick($event.target.value)">
        <option v-if="hasOwn" value="own">My own business</option>
        <option v-for="l in shown" :key="l.id" :value="l.id">{{ label(l) }}</option>
      </select>
      <span class="ls-count">{{ locations.length }} {{ locations.length === 1 ? 'location' : 'locations' }}</span>
    </template>
  </div>
</template>

<style scoped>
.ls { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin: 0 0 16px; }
.ls-label { font-weight: 600; }
.ls-select, .ls-search { padding: 8px 10px; border-radius: 8px; border: 1px solid var(--border, #d0d5dd); background: inherit; color: inherit; font: inherit; max-width: 100%; }
.ls-select { min-width: 220px; }
.ls-count { opacity: 0.7; font-size: 0.9em; }
</style>
