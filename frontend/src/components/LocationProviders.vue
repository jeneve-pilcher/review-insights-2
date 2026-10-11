<script setup>
import { computed, onMounted, ref } from 'vue'
import { Bar } from 'vue-chartjs'
import { BarElement, CategoryScale, Chart as ChartJS, Legend, LinearScale, Title, Tooltip } from 'chart.js'
import { orgApi } from '../api'
import { changeText, changeTone, checkedText, levelMessage, providerChart, scoreText, verifiedText } from '../utils/providers'
import { explainError } from '../utils/errors'

ChartJS.register(Title, Tooltip, Legend, CategoryScale, LinearScale, BarElement)

// Individual-doctor numbers for one location (Zocdoc). What appears depends on the person's role: owners, admins and
// this location's manager see doctors by name; everyone else gets practice-level totals only.
const props = defineProps({
  locationId: { type: String, required: true },
})

const view = ref(null)
const error = ref('')

onMounted(async () => {
  try {
    view.value = await orgApi.providers(props.locationId)
  } catch (err) {
    error.value = explainError(err, 'Could not load provider data')
  }
})

const note = computed(() => levelMessage(view.value))
const chart = computed(() => providerChart(view.value?.providers))
const options = { responsive: true, maintainAspectRatio: false, scales: { y: { min: 1, max: 5, title: { display: true, text: 'Score (1-5)' } } } }
</script>

<template>
  <section v-if="error || (view && view.enabled)" class="chart-section">
    <h3>🩺 Providers</h3>
    <p v-if="error" class="status error">{{ error }}</p>

    <template v-else>
      <p class="chart-desc">
        Numbers for the individual doctors at this location, from their public Zocdoc pages ({{ checkedText(view.checked_at) }}).
        Review text is never kept, and doctors' names are shown only to people with permission.
      </p>
      <p v-if="note" class="status">{{ note }}</p>

      <div v-if="view.summary" class="oc-grid">
        <div class="oc-card oc-stat"><span class="label">Doctors tracked</span><span class="value">{{ view.summary.providers }}</span></div>
        <div class="oc-card oc-stat"><span class="label">Average rating</span><span class="value">{{ scoreText(view.summary.avg_rating) }}</span></div>
        <div class="oc-card oc-stat"><span class="label">Bedside manner</span><span class="value">{{ scoreText(view.summary.bedside) }}</span></div>
        <div class="oc-card oc-stat"><span class="label">Wait time</span><span class="value">{{ scoreText(view.summary.wait) }}</span></div>
      </div>

      <template v-if="view.level === 'full' && view.providers.length">
        <div style="height: 240px; margin: 14px 0"><Bar :data="chart" :options="options" /></div>
        <div class="oc-scroll">
          <table class="oc-table">
            <thead>
              <tr><th>Doctor</th><th>Reviews</th><th>Rating</th><th>Bedside</th><th>Wait</th><th>Verified</th><th>Lately vs before</th></tr>
            </thead>
            <tbody>
              <tr v-for="p in view.providers" :key="p.url">
                <td><strong>{{ p.name }}</strong><span v-if="p.specialty" class="oc-note" style="margin-left: 4px">{{ p.specialty }}</span></td>
                <td>{{ p.reviews }}</td>
                <td>{{ scoreText(p.avg_rating) }}</td>
                <td>{{ scoreText(p.bedside) }}</td>
                <td>{{ scoreText(p.wait) }}</td>
                <td>{{ verifiedText(p.verified_pct) }}</td>
                <td :class="`nlp-${changeTone(p.change)}`">{{ changeText(p.change) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p class="oc-note">Scores are out of 5. "Lately vs before" compares the last four weeks of reviews with earlier ones, and only appears with enough reviews in both. Only recent reviews are available from Zocdoc.</p>
      </template>
    </template>
  </section>
</template>
