<script setup>
import { computed, onMounted, ref } from 'vue'
import { Bar } from 'vue-chartjs'
import { BarElement, CategoryScale, Chart as ChartJS, Legend, LinearScale, Title, Tooltip } from 'chart.js'
import { orgApi } from '../api'
import { cellText, flagMark, industryNote, subByLocationData, themeByLocationData } from '../utils/industryOrg'
import { explainError } from '../utils/errors'

ChartJS.register(Title, Tooltip, Legend, CategoryScale, LinearScale, BarElement)

// The Benchmarks page's industry section: which locations stand out on each of the industry's themes, and (for
// industries that use them) OpenTable's scores side by side.
const emit = defineEmits(['open'])
const roll = ref(null)
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    roll.value = await orgApi.industry()
  } catch (err) {
    error.value = explainError(err, 'Could not load the industry rankings')
  } finally {
    loading.value = false
  }
})

const note = computed(() => industryNote(roll.value))
const subData = computed(() => subByLocationData(roll.value?.subratings))
const themeData = computed(() => themeByLocationData(roll.value))
const pctOptions = { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, ticks: { callback: (v) => `${v}%` } } } }
const scoreOptions = { responsive: true, maintainAspectRatio: false, scales: { y: { min: 1, max: 5, title: { display: true, text: 'Score (1-5)' } } } }
</script>

<template>
  <section class="chart-section">
    <h3>🏷️ {{ roll?.pack ? `${roll.pack.label}: where locations stand out` : 'Industry rankings' }}</h3>
    <p v-if="loading" class="status">Loading…</p>
    <p v-else-if="error" class="status error">{{ error }}</p>

    <template v-else-if="roll">
      <p v-if="note" class="status">{{ note }}</p>

      <template v-if="roll.status === 'ok'">
        <div v-if="roll.rankings.length" class="oc-grid">
          <div v-for="r in roll.rankings" :key="r.theme" class="oc-card">
            <strong>{{ r.label }}</strong>
            <span class="oc-note" style="margin-left: 6px">company {{ cellText(r.company) }}</span>
            <ol style="margin: 6px 0 0; padding-left: 18px; font-size: 13px">
              <li v-for="h in r.highest" :key="h.location_id">
                <button class="oc-link" @click="emit('open', h.location_id)">{{ h.name }}</button>
                {{ cellText(h.share) }}{{ flagMark(h.flag) }}
              </li>
            </ol>
          </div>
        </div>
        <p class="oc-note">Locations with the highest share of written reviews mentioning each theme. ↑ means rising lately.</p>

        <template v-if="themeData.labels.length">
          <h4 style="margin: 16px 0 6px">{{ themeData.label }}, by location</h4>
          <div style="height: 240px"><Bar :data="themeData" :options="pctOptions" /></div>
        </template>

        <template v-if="roll.subratings">
          <h4 style="margin: 18px 0 6px">OpenTable scores, by location</h4>
          <div style="height: 260px"><Bar :data="subData" :options="scoreOptions" /></div>
          <p class="oc-note">Only locations with an OpenTable page connected and enough scored reviews appear here.</p>
        </template>
      </template>
    </template>
  </section>
</template>
