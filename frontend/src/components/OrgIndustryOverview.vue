<script setup>
import { computed, onMounted, ref } from 'vue'
import { Line } from 'vue-chartjs'
import { CategoryScale, Chart as ChartJS, Legend, LineElement, LinearScale, PointElement, Title, Tooltip } from 'chart.js'
import { orgApi } from '../api'
import { companyTrendData, cellStyle, cellText, flagMark, industryNote, kpiChangeText, kpiTone, kpiValueText, trendNote } from '../utils/industryOrg'
import { explainError } from '../utils/errors'

ChartJS.register(Title, Tooltip, Legend, CategoryScale, LinearScale, PointElement, LineElement)

// The company Overview's industry section: headline numbers, how the company's themes are moving week by week, and
// a grid showing which locations mention which theme. Built from each location's latest checks.
const emit = defineEmits(['open'])
const roll = ref(null)
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    roll.value = await orgApi.industry()
  } catch (err) {
    error.value = explainError(err, 'Could not load the industry numbers')
  } finally {
    loading.value = false
  }
})

const note = computed(() => industryNote(roll.value))
const trend = computed(() => companyTrendData(roll.value?.theme_trend))
const trendMessage = computed(() => trendNote(roll.value?.theme_trend))
const options = {
  responsive: true,
  maintainAspectRatio: false,
  scales: { y: { beginAtZero: true, ticks: { callback: (v) => `${v}%` }, title: { display: true, text: 'Share of written reviews' } } },
}
</script>

<template>
  <section class="chart-section">
    <h3>🏷️ {{ roll?.pack ? `${roll.pack.label}: company numbers` : 'Industry numbers' }}</h3>
    <p v-if="loading" class="status">Loading…</p>
    <p v-else-if="error" class="status error">{{ error }}</p>

    <template v-else-if="roll">
      <p v-if="note" class="status">{{ note }}</p>

      <template v-if="roll.status === 'ok'">
        <div class="oc-grid">
          <div v-for="k in roll.kpis" :key="k.id" class="oc-card oc-stat">
            <span class="label">{{ k.label }}</span>
            <span class="value">{{ kpiValueText(k) }}</span>
            <span class="sub" :class="`nlp-${kpiTone(k)}`">{{ kpiChangeText(k) || '&nbsp;' }}</span>
            <span class="sub">{{ k.locations }} location{{ k.locations === 1 ? '' : 's' }}</span>
          </div>
        </div>
        <p class="oc-note">
          Shares are the percentage of written reviews that mention each theme (weighted by how many written reviews each
          location has). Scores are OpenTable scores out of 5. Change compares the last four weeks with before.
        </p>

        <h4 style="margin: 16px 0 6px">Themes over time</h4>
        <p v-if="trendMessage" class="status">{{ trendMessage }}</p>
        <div v-else style="height: 260px"><Line :data="trend" :options="options" /></div>

        <h4 style="margin: 18px 0 6px">Which locations mention which theme</h4>
        <div class="oc-scroll">
          <table class="oc-table">
            <thead>
              <tr>
                <th>Location</th>
                <th v-for="t in roll.theme_grid.themes" :key="t.id">{{ t.label }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in roll.theme_grid.rows" :key="r.location_id">
                <td>
                  <button class="oc-link" @click="emit('open', r.location_id)"><strong>{{ r.name }}</strong></button>
                  <span v-if="r.region" class="oc-note" style="margin-left: 4px">{{ r.region }}</span>
                </td>
                <td v-for="t in roll.theme_grid.themes" :key="t.id" :style="cellStyle(r.shares[t.id])" style="text-align: center">
                  {{ cellText(r.shares[t.id]) }}{{ flagMark(r.flags[t.id]) }}
                </td>
              </tr>
              <tr>
                <td><strong>Company</strong></td>
                <td v-for="t in roll.theme_grid.themes" :key="t.id" style="text-align: center; font-weight: 600">{{ cellText(roll.theme_grid.company[t.id]) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p class="oc-note">Darker = more of that location's reviews mention the theme. ↑ means it is rising lately, ↓ falling.</p>
      </template>
    </template>
  </section>
</template>
