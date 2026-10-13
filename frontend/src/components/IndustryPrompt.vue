<script setup>
import { onMounted, ref } from 'vue'
import { fetchIndustries, setIndustry } from '../api'
import { explainError } from '../utils/errors'
import { dismissForSession, dismissedThisSession, shouldPrompt } from '../utils/industryPrompt'
import IndustrySelect from './IndustrySelect.vue'

// "Choose your industry": shown on the dashboard to accounts that never picked one, so they get the right themes,
// graphs and revenue defaults instead of the casual-dining ones they are on by default.
const props = defineProps({
  current: { type: Object, required: true },
})
const emit = defineEmits(['saved'])

const industries = ref([])
const industry = ref(props.current.industry || 'casual_dining')
const dismissed = ref(dismissedThisSession())
const saving = ref(false)
const error = ref('')

onMounted(async () => {
  try {
    industries.value = (await fetchIndustries()).industries
  } catch {
    /* without the list there is nothing to choose from, so the prompt stays hidden */
  }
})

async function save() {
  saving.value = true
  error.value = ''
  try {
    await setIndustry(industry.value)
    emit('saved', { industry: industry.value, industry_set: true })
  } catch (err) {
    error.value = explainError(err, 'Could not save your industry')
  } finally {
    saving.value = false
  }
}

function notNow() {
  dismissForSession()
  dismissed.value = true
}
</script>

<template>
  <div v-if="industries.length && shouldPrompt(current, dismissed)" class="oc-card" style="margin-bottom: 16px">
    <strong>Choose your industry</strong>
    <p class="oc-note" style="margin: 4px 0 10px">
      You're on the default, casual dining. Choosing yours gives you the right themes, graphs and revenue defaults.
    </p>
    <IndustrySelect v-model="industry" :industries="industries" />
    <p v-if="error" class="status error">{{ error }}</p>
    <div class="analysis-form" style="margin-top: 10px">
      <button class="oc-btn" :disabled="saving" @click="save">Save industry</button>
      <button class="oc-link" type="button" @click="notNow">Not now</button>
    </div>
  </div>
</template>
