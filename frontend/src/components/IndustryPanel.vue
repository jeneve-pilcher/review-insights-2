<script setup>
import ByWeekBadge from './ByWeekBadge.vue'
import { computed, ref, watch } from 'vue'
import { Line } from 'vue-chartjs'
import {
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LineElement,
  LinearScale,
  PointElement,
  Title,
  Tooltip,
} from 'chart.js'
import { kpiChangeText, kpiTone, kpiValueText, singleKpis } from '../utils/industryOrg'
import { chartSeries, compareText, pointDetail, toneWord, defaultSelection, pct, ratingText, subSeries, subratingsMessage, toneClass, trendsMessage } from '../utils/industry'

ChartJS.register(Title, Tooltip, Legend, CategoryScale, LinearScale, PointElement, LineElement)

// This industry's own themes and graphs: how often each theme comes up week by week, whether it's rising or falling,
// and (fine dining) OpenTable's food / service / ambience / value scores over time.
const props = defineProps({
  result: { type: Object, default: null },
  meta: { type: Object, default: null },
  locked: { type: Boolean, default: false },
})

const trends = computed(() => props.result?.trends ?? null)
const sub = computed(() => props.result?.subratings ?? null)
const pack = computed(() => props.result?.pack ?? null)
const kpis = computed(() => singleKpis(pack.value, trends.value, sub.value))

const selected = ref([])
watch(trends, (t) => { selected.value = defaultSelection(t) }, { immediate: true })

function toggle(id) {
  selected.value = selected.value.includes(id) ? selected.value.filter((x) => x !== id) : [...selected.value, id]
}

const trendData = computed(() => chartSeries(trends.value, selected.value))
const subData = computed(() => subSeries(sub.value))
const trendNote = computed(() => trendsMessage(trends.value))
const subNote = computed(() => subratingsMessage(sub.value))
const mentioned = computed(() => (trends.value?.themes ?? []).filter((t) => t.mentions > 0))

const clicked = ref(null)
watch(trends, () => { clicked.value = null })
const detail = computed(() => (clicked.value ? pointDetail(trends.value, clicked.value.themeId, clicked.value.index) : null))

const trendOptions = {
  responsive: true,
  onClick: (_event, elements, chart) => {
    if (!elements.length) return
    const { datasetIndex, index } = elements[0]
    clicked.value = { themeId: chart.data.datasets[datasetIndex].themeId, index }
  },
  onHover: (event, elements) => { event.native.target.style.cursor = elements.length ? 'pointer' : 'default' },
  maintainAspectRatio: false,
  scales: { y: { beginAtZero: true, ticks: { callback: (v) => `${v}%` }, title: { display: true, text: 'Share of written reviews' } } },
  plugins: { tooltip: { callbacks: { label: (c) => `${c.dataset.label}: ${c.parsed.y}% of reviews that week` } } },
}
const subOptions = {
  responsive: true,
  maintainAspectRatio: false,
  scales: { y: { min: 1, max: 5, title: { display: true, text: 'Average score (1-5)' } } },
}
</script>

<template>
  <section class="chart-section">
    <h3>🏷️ {{ pack ? `${pack.label} trends` : 'Industry trends' }}<ByWeekBadge /></h3>

    <p v-if="locked" class="chart-desc">
      Industry trends (the themes and graphs for your kind of business) are a Pro feature.
    </p>
    <p v-else-if="!result" class="chart-desc">Run an analysis to see the themes that matter for your industry.</p>

    <template v-else>
      <p class="chart-desc">
        How often each {{ pack.label.toLowerCase() }} theme comes up in written reviews, week by week<template v-if="trends?.flags_enabled">,
        and whether it's rising or falling lately. A theme is only flagged when there's enough evidence, since a jump from one
        mention to two isn't a trend</template><template v-else>. See the summary above for what's changing</template>.
        Based on {{ trends?.reviews ?? 0 }} written reviews.
      </p>

      <div v-if="kpis.length" class="oc-grid" style="margin-bottom: 10px">
        <div v-for="k in kpis" :key="k.id" class="oc-card oc-stat">
          <span class="label">{{ k.label }}</span>
          <span class="value">{{ kpiValueText(k) }}</span>
          <span class="sub" :class="`nlp-${kpiTone(k)}`">{{ kpiChangeText(k) || '&nbsp;' }}</span>
        </div>
      </div>

      <p v-if="trendNote" class="status">{{ trendNote }}</p>

      <template v-if="trends && trends.status === 'ok'">
        <template v-if="trends.flags_enabled">
          <ul v-if="trends.alerts.length" class="nlp-list" style="padding-left: 0; list-style: none">
            <li v-for="a in trends.alerts" :key="a.theme" class="nlp-item" :class="`nlp-${toneClass(a.tone)}`">{{ a.text }}</li>
          </ul>
          <p v-else-if="trends.can_compare" class="status">No theme has moved enough lately to flag. That's steady.</p>
          <p v-else class="status">Not enough older reviews yet to say what's changing, so no themes are flagged.</p>
        </template>

        <div v-if="trends.weeks.length" style="margin: 14px 0 6px">
          <button
            v-for="t in mentioned"
            :key="t.id"
            class="oc-btn"
            :style="selected.includes(t.id) ? 'opacity: 1; font-weight: 600' : 'opacity: 0.55'"
            style="margin: 0 6px 6px 0"
            @click="toggle(t.id)"
          >
            {{ t.label }}
          </button>
          <div style="height: 280px"><Line :data="trendData" :options="trendOptions" /></div>
          <p class="oc-note" style="margin-top: 6px">Click a dot to see that week's tone and the written reviews behind it.</p>

          <div v-if="detail" class="point-detail">
            <h4>{{ detail.theme }} · week of {{ detail.week }}</h4>
            <p class="chart-desc">
              {{ detail.hits }} of {{ detail.total }} written reviews that week mention it<template v-if="detail.rating != null">, averaging {{ detail.rating }}★</template>.
              <template v-if="detail.tone != null">Their language reads <strong>{{ toneWord(detail.tone) }}</strong> ({{ detail.tone }} on a scale of −1 to +1).</template>
            </p>
            <p v-if="!detail.reviews.length" class="status">No written reviews mention it that week.</p>
            <ul v-else class="point-reviews">
              <li v-for="(r, i) in detail.reviews" :key="i">
                <div class="point-review-meta">
                  {{ r.rating }}★ · {{ r.date }}<template v-if="r.tone != null"> · {{ toneWord(r.tone) }}</template>
                </div>
                <div>{{ r.text }}</div>
              </li>
            </ul>
            <button class="oc-btn" type="button" @click="clicked = null">Close</button>
          </div>
        </div>

        <div class="oc-scroll">
          <table class="oc-table" style="margin-top: 10px">
            <thead>
              <tr><th>Theme</th><th>Share of reviews</th><th>Lately vs before</th><th>Rating when mentioned</th></tr>
            </thead>
            <tbody>
              <tr v-for="t in mentioned" :key="t.id">
                <td><strong>{{ t.label }}</strong> <span v-if="t.flag" class="oc-chip">{{ t.flag }}</span></td>
                <td>{{ pct(t.share) }} ({{ t.mentions }})</td>
                <td>{{ compareText(t) }}</td>
                <td>{{ ratingText(t) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>

      <template v-if="sub">
        <h4 style="margin: 22px 0 6px">OpenTable scores over time</h4>
        <p v-if="subNote" class="status">{{ subNote }}</p>
        <template v-else-if="sub.status === 'ok'">
          <p class="chart-desc">
            A diner can love the food and still rate the value low, which the overall star rating hides.
            <strong v-if="sub.weakest">Weakest: {{ sub.weakest.label }} ({{ sub.weakest.average }}).</strong>
          </p>
          <div style="height: 240px"><Line :data="subData" :options="subOptions" /></div>
        </template>
      </template>
    </template>
  </section>
</template>

<style>
.point-detail { margin-top: 12px; padding: 12px 14px; border: 1px solid rgba(128,128,128,0.35); border-radius: 10px; }
.point-reviews { list-style: none; padding: 0; margin: 8px 0; display: grid; gap: 6px; }
.point-reviews li { border: 1px solid rgba(128,128,128,0.3); border-radius: 8px; padding: 6px 8px; font-size: 0.88rem; line-height: 1.4; }
.point-review-meta { font-size: 0.78rem; opacity: 0.75; margin-bottom: 2px; }
</style>
