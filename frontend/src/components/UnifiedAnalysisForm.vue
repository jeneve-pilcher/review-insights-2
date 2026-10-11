<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { analyzeAll } from '../api'
import { estimateRun, estimateWarning, formatUsd } from '../utils/credits'
import { MAX_PAGES, clampPages, defaultMentionTerms, estimateCostUsd, estimateSearches, formatCost } from '../utils/mentions'
import { MAX_MONTHS, parseMonths } from '../utils/months'

const props = defineProps({
  businessLocation: { type: String, required: true },
  months: { type: Number, default: 6 },
  // Only Pro/Enterprise ever see the Wait-Time Heatmap that uses these two
  // values - no point showing them to a Free-tier user.
  showRevenueInputs: { type: Boolean, default: false },
  // Pro/Enterprise: optional competitors, analyzed in the same click.
  showCompetitors: { type: Boolean, default: false },
  // Pro/Enterprise with a saved Yelp page: lets the user tick Yelp (one extra pull).
  yelpUrl: { type: String, default: null },
  // Pro/Enterprise with a saved OpenTable, DoorDash, Uber Eats or Grubhub page: each can be ticked (one extra pull each).
  opentableUrl: { type: String, default: null },
  doordashUrl: { type: String, default: null },
  ubereatsUrl: { type: String, default: null },
  grubhubUrl: { type: String, default: null },
  // Average order value to start from: each industry has its own (a fine-dining check is not a casual one).
  defaultAov: { type: Number, default: 35 },
  // The account's credit summary (rates, caps, balance), used to show what a run could cost.
  creditInfo: { type: Object, default: null },
  // Pro/Enterprise: optionally search the web for mentions (two extra searches).
  showMentions: { type: Boolean, default: false },
  // Which pulled platform(s) the panels analyze: 'combined' | 'google' | 'yelp'.
  view: { type: String, default: 'combined' },
})

const emit = defineEmits(['result', 'update:months'])

// Free-typed number of months (1 to 60). We only tell the parent about valid numbers.
const monthsText = ref(String(props.months))
const monthsCheck = computed(() => parseMonths(monthsText.value))

watch(
  () => props.months,
  (m) => {
    if (monthsCheck.value.value !== m) monthsText.value = String(m)
  }
)

function onMonthsInput(event) {
  monthsText.value = event.target.value
  if (monthsCheck.value.valid) emit('update:months', monthsCheck.value.value)
}

const avgOrderValue = ref(props.defaultAov)
let aovTouched = false      // once someone types their own number, the industry default no longer overwrites it
watch(() => props.defaultAov, (v) => { if (!aovTouched) avgOrderValue.value = v })
const multiplier = ref(20)
const loading = ref(false)
const error = ref('')

const competitors = ref([])
const includeYelp = ref(true)
// Optional platforms the account has saved a page for. Each ticked one is one extra pull (through Apify).
const includes = reactive({ opentable: true, doordash: true, ubereats: true, grubhub: true })
const EXTRA = [
  { id: 'opentable', label: 'OpenTable', prop: 'opentableUrl', hint: 'about a tenth of a cent per review' },
  { id: 'doordash', label: 'DoorDash', prop: 'doordashUrl', hint: 'a fraction of a cent per review' },
  { id: 'ubereats', label: 'Uber Eats', prop: 'ubereatsUrl', hint: 'written reviews with no stars, so never counted in your ratings' },
  { id: 'grubhub', label: 'Grubhub', prop: 'grubhubUrl', hint: 'about half a cent per review' },
]
const extraPlatforms = computed(() => EXTRA.filter((p) => props[p.prop]))

// Which review sources this run pulls: Google always, plus each saved platform that's ticked.
const sourcesToPull = computed(() => {
  const list = ['google']
  if (props.yelpUrl && includeYelp.value) list.push('yelp')
  for (const p of EXTRA) if (props[p.prop] && includes[p.id]) list.push(p.id)
  return list
})
const includeMentions = ref(false)
const mentionTerms = ref('')
const mentionPages = ref(2)
const runEstimate = computed(() =>
  estimateRun(
    {
      sources: sourcesToPull.value,
      mentions: props.showMentions && includeMentions.value,
      mentionPages: clampPages(mentionPages.value),
      competitors: competitors.value.filter((c) => c.search_query.trim()).length,
    },
    props.creditInfo,
  ),
)
const estimateBreakdown = computed(() =>
  runEstimate.value ? runEstimate.value.lines.map((line) => `${line.label} ${formatUsd(line.usd)}`).join(' + ') : '',
)
const runWarning = computed(() => estimateWarning(runEstimate.value, props.creditInfo))
const searchEstimate = computed(() => ({ searches: estimateSearches(mentionPages.value), cost: formatCost(estimateCostUsd(mentionPages.value)) }))
const mentionPlaceholder = computed(() => defaultMentionTerms(props.businessLocation))

function addCompetitor() {
  if (competitors.value.length >= 5) return
  competitors.value.push({ name: `Competitor ${competitors.value.length + 1}`, search_query: '' })
}

function removeCompetitor(index) {
  competitors.value.splice(index, 1)
}

// `viewOverride` lets the dashboard's view switch re-run instantly with a new view.
async function runAnalysis(viewOverride) {
  if (!monthsCheck.value.valid) {
    error.value = monthsCheck.value.message
    return
  }
  loading.value = true
  error.value = ''
  try {
    const data = await analyzeAll({
      months: monthsCheck.value.value,
      avgOrderValue: avgOrderValue.value,
      reviewsToCustomersMultiplier: multiplier.value,
      sources: sourcesToPull.value,
      view: typeof viewOverride === 'string' ? viewOverride : props.view,
      mentions: props.showMentions && includeMentions.value,
      mentionPages: clampPages(mentionPages.value),
      mentionTerms: props.showMentions && includeMentions.value && mentionTerms.value.trim() ? mentionTerms.value.trim() : null,
      competitors: props.showCompetitors
        ? competitors.value
            .filter((c) => c.search_query.trim())
            .map((c) => ({ name: c.name.trim() || 'Competitor', search_query: c.search_query.trim() }))
        : [],
    })
    emit('result', { data })
  } catch (err) {
    error.value = err?.response?.data?.detail || 'Something went wrong.'
  } finally {
    loading.value = false
  }
}

defineExpose({ runAnalysis })
</script>

<template>
  <section class="chart-section unified-form">
    <h3>🔎 Run Analysis</h3>
    <p class="chart-desc">
      Your Google reviews for <strong>{{ businessLocation }}</strong> are pulled once (plus Yelp and any reservation or delivery pages
      you add and tick below) and shared by every panel, all from this one button. A shorter time
      window runs faster and uses fewer scraping credits.
    </p>

    <div class="analysis-form">
      <label class="field">
        <span>Analyze the last (months)</span>
        <input
          class="months-input"
          :class="{ invalid: !monthsCheck.valid }"
          type="number"
          inputmode="numeric"
          min="1"
          :max="MAX_MONTHS"
          step="1"
          required
          :value="monthsText"
          @input="onMonthsInput"
        />
      </label>
      <template v-if="showRevenueInputs">
        <label class="field">
          <span>Avg. order value ($)</span>
          <input v-model.number="avgOrderValue" type="number" min="0" step="0.5" @input="aovTouched = true" />
        </label>
        <label class="field">
          <span>Est. customers per review</span>
          <input v-model.number="multiplier" type="number" min="1" />
        </label>
      </template>
    </div>

    <div v-if="showCompetitors" class="competitor-inputs" style="margin-top: 14px">
      <p class="chart-desc" style="margin-bottom: 8px">
        <strong>Optional: compare against competitors in the same click.</strong> Your own reviews
        are pulled once and shared; each competitor you add is one extra pull. Paste a Google Maps
        link if a name is ambiguous.
      </p>
      <div v-for="(c, i) in competitors" :key="i" class="competitor-row">
        <input v-model="c.name" type="text" placeholder="Competitor name" class="competitor-name" />
        <input v-model="c.search_query" type="text" placeholder="Location, or a Google Maps URL" class="competitor-query" />
        <button class="remove-btn" @click="removeCompetitor(i)">✕</button>
      </div>
      <button v-if="competitors.length < 5" class="add-btn" @click="addCompetitor">+ Add competitor</button>
    </div>

    <div v-if="yelpUrl" class="source-picker">
      <label class="source-check">
        <input v-model="includeYelp" type="checkbox" />
        Include Yelp reviews <span class="source-hint">(one extra review pull)</span>
      </label>
    </div>

    <div v-for="p in extraPlatforms" :key="p.id" class="source-picker">
      <label class="source-check">
        <input v-model="includes[p.id]" type="checkbox" />
        Include {{ p.label }} reviews <span class="source-hint">(one extra pull through Apify, {{ p.hint }})</span>
      </label>
    </div>

    <div v-if="showMentions" class="source-picker">
      <label class="source-check">
        <input v-model="includeMentions" type="checkbox" />
        Include internet mentions <span class="source-hint">(news, blogs, forums, social; two extra web searches)</span>
      </label>
      <div v-if="includeMentions" style="margin-top: 6px">
        <input v-model="mentionTerms" type="text" class="months-input" maxlength="200" :placeholder="mentionPlaceholder" />
        <div class="oc-note">Words to search for. Leave blank to search: <strong>{{ mentionPlaceholder }}</strong></div>
        <label class="field" style="margin-top: 8px; max-width: 220px">
          <span>Depth (pages per search)</span>
          <input v-model.number="mentionPages" class="months-input" type="number" min="1" :max="MAX_PAGES" step="1" />
        </label>
        <div class="oc-note">
          Each page is about 10 results. This will run about <strong>{{ searchEstimate.searches }} web searches (roughly {{ searchEstimate.cost }})</strong>;
          a repeat click inside 30 minutes is free. Google returns a sample of the web, not everything, so more pages find more but never all.
        </div>
      </div>
    </div>

    <div v-if="runEstimate && creditInfo?.enforced" class="oc-note" style="margin-top: 14px">
      Estimated cost: <strong>up to about {{ formatUsd(runEstimate.upper) }}</strong>
      <span v-if="estimateBreakdown">({{ estimateBreakdown }})</span>.
      Anything from a recent pull is free, and most runs cost less than this ceiling.
      You have <strong>{{ formatUsd(creditInfo.available_usd) }}</strong> available.
    </div>
    <p v-if="runWarning" class="status error" style="margin-top: 6px">{{ runWarning }}</p>

    <button class="run-btn" style="width: auto; padding: 10px 28px; margin-top: 16px" @click="runAnalysis()" :disabled="loading">
      {{ loading ? 'Analyzing…' : 'Run Analysis' }}
    </button>

    <p v-if="!monthsCheck.valid" class="status error" style="margin-top: 6px">{{ monthsCheck.message }}</p>
    <p v-else class="oc-note" style="margin-top: 6px">
      Any whole number of months, up to {{ MAX_MONTHS }}. Longer windows pull more reviews (there's a cap) and cost more.
    </p>
    <p v-if="error && monthsCheck.valid" class="status error">{{ error }}</p>
  </section>
</template>

<style>
.source-picker {
  margin-top: 14px;
  font-size: 13px;
}

.source-check {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.source-hint {
  color: #888;
  font-size: 12px;
}

.months-input {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #d3d6db;
  border-radius: 6px;
  font-size: 13px;
  font-family: inherit;
  background: white;
}

.months-input.invalid {
  border-color: #e74c3c;
  background: #fff6f5;
}

.months-select {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #d3d6db;
  border-radius: 6px;
  font-size: 13px;
  font-family: inherit;
  background: white;
}
</style>
