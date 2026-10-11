<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchIndustries } from '../api'
import { groupIndustries } from '../utils/industry'
import { PLATFORMS } from '../utils/links'
import { integrationsFor, saveOnboarding, splitPlatforms } from '../utils/onboarding'

// "Get started" from the nav or any purchase button: first the industry, then (optionally) the data sources used,
// then sign-up. Nothing is required beyond the industry, and everything can be changed or added later.
const props = defineProps({
  plan: { type: String, default: 'free' },
})
const emit = defineEmits(['close'])

const router = useRouter()
const step = ref(1)
const industries = ref([])
const industry = ref('')
const chosen = ref([])
const showMore = ref(false)
const loadFailed = ref(false)

onMounted(async () => {
  try {
    const data = await fetchIndustries()
    industries.value = data.industries
    industry.value = data.default
  } catch {
    loadFailed.value = true
    industry.value = 'casual_dining'
  }
})

const groups = computed(() => groupIndustries(industries.value))
const pack = computed(() => industries.value.find((i) => i.id === industry.value) ?? null)
const split = computed(() => splitPlatforms(PLATFORMS, pack.value, []))
const hasLists = computed(() => integrationsFor(pack.value).recommended.length > 0)
const planLabel = computed(() => (props.plan === 'pro' ? 'Pro' : 'Free'))

function toggle(id) {
  chosen.value = chosen.value.includes(id) ? chosen.value.filter((x) => x !== id) : [...chosen.value, id]
}

function pick(i) {
  if (!i.available) return
  industry.value = i.id
  chosen.value = []      // the sources on offer depend on the industry
  showMore.value = false
}

function finish(skip) {
  saveOnboarding({ industry: industry.value, sources: skip ? [] : chosen.value, plan: props.plan })
  emit('close')
  router.push({ path: '/signup', query: { plan: props.plan } })
}
</script>

<template>
  <div class="gs-backdrop" role="dialog" aria-modal="true" aria-label="Get started">
    <div class="gs-dialog">
      <div class="gs-body">
        <p class="gs-plan">Signing up for <strong>{{ planLabel }}</strong> · step {{ step }} of 2</p>

        <template v-if="step === 1">
          <h2 style="margin: 4px 0 6px">Which industry are you in?</h2>
          <p class="chart-desc">This sets the themes, graphs and revenue defaults you'll see. You can change it later.</p>
          <p v-if="loadFailed" class="status">Couldn't load the list of industries, so we'll start you with casual dining. You can change it later.</p>

          <div v-for="g in groups" :key="g.name" style="margin-bottom: 12px">
            <h4 style="margin: 8px 0 6px">{{ g.name }}</h4>
            <div class="gs-cards">
              <button
                v-for="i in g.items"
                :key="i.id"
                type="button"
                class="gs-card"
                :class="{ selected: industry === i.id, disabled: !i.available }"
                :disabled="!i.available"
                @click="pick(i)"
              >
                <strong>{{ i.label }}</strong>
                <span class="gs-note">{{ i.available ? i.description : 'Coming soon' }}</span>
              </button>
            </div>
          </div>
        </template>

        <template v-else>
          <h2 style="margin: 4px 0 6px">Which data sources do you use?</h2>
          <p class="chart-desc">
            <strong>Optional.</strong> Google reviews are always included. Tick the others you use and we'll ask for their
            links first. Skip this and add or change them any time.
          </p>

          <label class="gs-option gs-fixed"><input type="checkbox" checked disabled /> Google reviews <span class="gs-note">always included</span></label>

          <template v-if="hasLists">
            <label v-for="p in split.primary" :key="p.id" class="gs-option">
              <input type="checkbox" :checked="chosen.includes(p.id)" @change="toggle(p.id)" />
              {{ p.label }} <span v-if="plan !== 'pro'" class="gs-note">included with Pro</span>
            </label>
            <button v-if="split.more.length && !showMore" type="button" class="oc-link" @click="showMore = true">
              Show {{ split.more.length }} more platforms
            </button>
            <template v-if="showMore">
              <label v-for="p in split.more" :key="p.id" class="gs-option">
                <input type="checkbox" :checked="chosen.includes(p.id)" @change="toggle(p.id)" />
                {{ p.label }} <span v-if="plan !== 'pro'" class="gs-note">included with Pro</span>
              </label>
            </template>
          </template>
          <p v-else class="status">There are no extra platforms for this industry yet.</p>
        </template>
      </div>

      <div class="gs-footer">
        <template v-if="step === 1">
          <button class="run-btn" style="width: auto; padding: 9px 22px" :disabled="!industry" @click="step = 2">Continue</button>
          <button class="oc-btn" @click="emit('close')">Cancel</button>
        </template>
        <template v-else>
          <button class="run-btn" style="width: auto; padding: 9px 22px" @click="finish(false)">Continue to sign up</button>
          <button class="oc-btn" @click="finish(true)">Skip for now</button>
          <button class="oc-link" @click="step = 1">Back</button>
        </template>
      </div>
    </div>
  </div>
</template>

<style>
.gs-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(20, 20, 30, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  z-index: 1000;
}

.gs-dialog {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 640px;
  max-height: 92vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
}

.gs-body {
  overflow-y: auto;
  padding: 20px 24px;
}

.gs-footer {
  border-top: 1px solid #e4e6ea;
  padding: 14px 24px;
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.gs-plan {
  margin: 0;
  font-size: 12px;
  color: #777;
}

.gs-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
  gap: 10px;
}

.gs-card {
  text-align: left;
  border: 1px solid #d3d6db;
  background: white;
  border-radius: 8px;
  padding: 12px;
  cursor: pointer;
  font-family: inherit;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.gs-card.selected {
  border-color: var(--brand, #ff4b4b);
  box-shadow: 0 0 0 2px var(--brand-border, #e4defa);
}

.gs-card.disabled {
  opacity: 0.55;
  cursor: default;
}

.gs-note {
  font-size: 12px;
  color: #777;
}

.gs-option {
  display: block;
  padding: 6px 0;
  font-size: 14px;
}

.gs-fixed {
  color: #555;
}
</style>
