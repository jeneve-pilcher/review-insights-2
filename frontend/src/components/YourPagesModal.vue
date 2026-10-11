<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchIndustries, saveLinks, setIndustry } from '../api'
import { collectLinks, emptyLinks } from '../utils/links'
import IndustrySelect from './IndustrySelect.vue'
import PlatformLinksFields from './PlatformLinksFields.vue'

// Opens from "Your pages" in the top bar: add any review pages you didn't connect at setup.
const props = defineProps({
  current: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['saved', 'close'])

const links = ref(emptyLinks())
const industries = ref([])
const industry = ref(props.current?.industry || 'casual_dining')
const pack = computed(() => industries.value.find((i) => i.id === industry.value) ?? null)

onMounted(async () => {
  try {
    industries.value = (await fetchIndustries()).industries
  } catch {
    /* the picker just stays hidden */
  }
})
const saving = ref(false)
const error = ref('')

async function save() {
  const toSave = collectLinks(links.value, props.current)
  const industryChanged = industries.value.length > 0 && industry.value !== (props.current?.industry || 'casual_dining')
  if (!Object.keys(toSave).length && !industryChanged) {
    emit('close')
    return
  }
  saving.value = true
  error.value = ''
  try {
    const saved = Object.keys(toSave).length ? (await saveLinks(toSave)).links : {}
    if (industryChanged) {
      await setIndustry(industry.value)
      saved.industry = industry.value
    }
    emit('saved', saved)
    emit('close')
  } catch (err) {
    error.value = err?.response?.data?.detail || 'Could not save those pages.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="yp-backdrop" role="dialog" aria-modal="true" aria-label="Your pages">
    <div class="yp-dialog">
      <div class="yp-body">
        <h3 style="margin-top: 0">Your business</h3>
        <IndustrySelect v-if="industries.length" v-model="industry" :industries="industries" />
        <h4 style="margin: 18px 0 4px">Review pages</h4>
        <p class="chart-desc">Add the pages you want analyzed alongside Google. Each page is saved once.</p>
        <PlatformLinksFields v-model="links" :current="current" :pack="pack" />
        <p v-if="error" class="status error">{{ error }}</p>
      </div>
      <div class="yp-footer">
        <button class="run-btn" style="width: auto; padding: 9px 22px" :disabled="saving" @click="save">
          {{ saving ? 'Saving…' : 'Save' }}
        </button>
        <button class="oc-btn" :disabled="saving" @click="emit('close')">Close</button>
      </div>
    </div>
  </div>
</template>

<style>
.yp-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(20, 20, 30, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  z-index: 900;
}

.yp-dialog {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 620px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
}

.yp-body {
  overflow-y: auto;
  padding: 20px 24px;
}

.yp-footer {
  border-top: 1px solid #e4e6ea;
  padding: 14px 24px;
  display: flex;
  gap: 10px;
}
</style>
