<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchIndustries, saveLinks, setBusinessLocation, setIndustry } from '../api'
import { PLATFORMS, collectLinks, emptyLinks } from '../utils/links'
import { clearOnboarding, platformNames, recallOnboarding } from '../utils/onboarding'
import IndustrySelect from './IndustrySelect.vue'
import PlatformLinksFields from './PlatformLinksFields.vue'

// First-time setup: your Google business plus (on Pro) your other review pages, saved together.
const props = defineProps({
  canAddLinks: { type: Boolean, default: false },
  current: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['set'])

const location = ref('')
const links = ref(emptyLinks())
const industries = ref([])
const industry = ref('casual_dining')
const chosen = ref([])       // data sources the visitor said they use before signing up (optional)
const pack = computed(() => industries.value.find((i) => i.id === industry.value) ?? null)
const chosenNames = computed(() => platformNames(chosen.value, PLATFORMS))

onMounted(async () => {
  try {
    const data = await fetchIndustries()
    industries.value = data.industries
    // Start from what they picked on the landing page, if anything; the server re-checks it when it's saved.
    const answers = recallOnboarding()
    chosen.value = answers?.sources ?? []
    const wanted = answers?.industry
    industry.value = wanted && data.industries.some((i) => i.id === wanted && i.available) ? wanted : props.current?.industry || data.default
  } catch {
    /* the picker just stays empty and the default industry is used */
  }
})
const loading = ref(false)
const error = ref('')

async function handleSubmit() {
  const place = location.value.trim()
  if (!place) return
  loading.value = true
  error.value = ''
  try {
    // Pages first: they're checked all-or-nothing, so a typo in one never leaves a half-finished setup.
    const toSave = props.canAddLinks ? collectLinks(links.value, props.current) : {}
    const saved = Object.keys(toSave).length ? (await saveLinks(toSave)).links : {}
    await setBusinessLocation(place)
    if (industries.value.length) await setIndustry(industry.value)
    clearOnboarding()
    emit('set', { location: place, links: { ...saved, industry: industry.value, industry_set: industries.value.length > 0 } })
  } catch (err) {
    error.value = err?.response?.data?.detail || 'Could not save your setup.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="chart-section">
    <h3>📍 Set Your Business</h3>
    <p class="chart-desc">
      One-time setup: enter your business name/location, or paste its Google Maps URL for precision if the name is
      ambiguous. This is permanent for your account - all analysis will run against this business only. Contact support
      if you need it changed later.
    </p>

    <div class="analysis-form">
      <label class="field" style="flex: 1; min-width: 260px">
        <span>Business Location or Google Maps URL</span>
        <input
          v-model="location"
          type="text"
          placeholder="e.g. Joe's Pizza, Brooklyn NY - or paste a Google Maps link"
          @keyup.enter="handleSubmit"
        />
      </label>
    </div>

    <div style="margin-top: 14px">
      <IndustrySelect v-if="industries.length" v-model="industry" :industries="industries" />
    </div>

    <template v-if="canAddLinks">
      <h4 style="margin: 18px 0 4px">Other review pages (optional)</h4>
      <p class="chart-desc">
        Add your pages on other platforms to analyze those reviews alongside Google. Each is saved once, like your
        business. You can add the rest later from <strong>Your pages</strong> at the top.
      </p>
      <p v-if="chosenNames.length" class="oc-note">
        You said you use <strong>{{ chosenNames.join(', ') }}</strong>. Add those links here, or skip and add them any time.
      </p>
      <PlatformLinksFields v-model="links" :current="current" :pack="pack" :chosen="chosen" />
    </template>
    <p v-else class="oc-note" style="margin-top: 12px">
      Pro accounts can also connect Yelp, OpenTable, DoorDash, Uber Eats and Grubhub here.
    </p>

    <button class="run-btn" style="width: auto; padding: 10px 28px; margin-top: 14px" :disabled="loading" @click="handleSubmit">
      {{ loading ? 'Saving…' : 'Save (permanent)' }}
    </button>
    <p v-if="error" class="status error">{{ error }}</p>
  </section>
</template>
