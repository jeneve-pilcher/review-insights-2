<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { industryById } from '../content/industries'
import { PLATFORMS } from '../utils/links'
import { saveOnboarding } from '../utils/onboarding'
import { canContinue, planLabel, signupTarget, sourcesFor } from '../utils/startFlow'

// Getting started, right on the page (no popup): your industry (chosen above), the plan, and, optionally, which data
// sources you use. Then on to sign-up. Nothing but the industry is required, and everything can be changed later.
const props = defineProps({
  industry: { type: String, default: '' },
  plan: { type: String, default: 'free' },
})
const emit = defineEmits(['update:plan'])

const router = useRouter()
const chosen = ref([])
const showMore = ref(false)
const current = computed(() => industryById(props.industry))
const split = computed(() => sourcesFor(current.value, PLATFORMS))
const ready = computed(() => canContinue(props.industry))

// The sources on offer depend on the industry, so start again when it changes.
watch(() => props.industry, () => { chosen.value = []; showMore.value = false })

function toggle(id) {
  chosen.value = chosen.value.includes(id) ? chosen.value.filter((x) => x !== id) : [...chosen.value, id]
}

function go(skip) {
  if (!ready.value) return
  saveOnboarding({ industry: props.industry, sources: skip ? [] : chosen.value, plan: props.plan })
  router.push(signupTarget(props.plan))
}
</script>

<template>
  <section id="start" class="gsp-section">
    <h2>Get started</h2>

    <p v-if="!current" class="gsp-wait">Choose your industry above to continue.</p>

    <div v-else class="gsp-card">
      <p class="gsp-line">
        Industry: <strong>{{ current.label }}</strong>
        <a href="#industries" class="gsp-change">change</a>
      </p>

      <fieldset class="gsp-plan">
        <legend>Plan</legend>
        <label><input type="radio" name="plan" value="free" :checked="plan === 'free'" @change="emit('update:plan', 'free')" /> Free <span class="gsp-note">$0</span></label>
        <label><input type="radio" name="plan" value="pro" :checked="plan === 'pro'" @change="emit('update:plan', 'pro')" /> Pro <span class="gsp-note">$49 / month</span></label>
      </fieldset>

      <h4>Which data sources do you use? <span class="gsp-note">Optional: add or change these any time</span></h4>
      <p class="gsp-note">Google reviews are always included. Tick any others you use and we'll ask for their links first.</p>
      <template v-if="split.primary.length || split.more.length">
        <label v-for="p in split.primary" :key="p.id" class="gsp-option">
          <input type="checkbox" :checked="chosen.includes(p.id)" @change="toggle(p.id)" /> {{ p.label }}
          <span v-if="plan !== 'pro'" class="gsp-note">included with Pro</span>
        </label>
        <button v-if="split.more.length && !showMore" type="button" class="oc-link" @click="showMore = true">
          Show {{ split.more.length }} more platforms
        </button>
        <template v-if="showMore">
          <label v-for="p in split.more" :key="p.id" class="gsp-option">
            <input type="checkbox" :checked="chosen.includes(p.id)" @change="toggle(p.id)" /> {{ p.label }}
            <span v-if="plan !== 'pro'" class="gsp-note">included with Pro</span>
          </label>
        </template>
      </template>
      <p v-else class="gsp-note">There are no extra platforms for this industry yet.</p>

      <div class="gsp-actions">
        <button class="run-btn" type="button" :disabled="!ready" @click="go(false)">
          Continue to sign up ({{ planLabel(plan) }})
        </button>
        <button class="oc-btn" type="button" :disabled="!ready" @click="go(true)">Skip the sources</button>
      </div>
    </div>
  </section>
</template>

<style>
.gsp-section {
  padding: 24px 20px 40px;
  max-width: 640px;
  margin: 0 auto;
}

.gsp-section h2 {
  text-align: center;
}

.gsp-wait {
  text-align: center;
  color: #777;
}

.gsp-card {
  background: white;
  border: 1px solid #e4e6ea;
  border-radius: 12px;
  padding: 22px 26px;
}

.gsp-line {
  margin: 0 0 12px;
}

.gsp-change {
  margin-left: 8px;
  font-size: 13px;
  color: var(--brand, #ff4b4b);
}

.gsp-plan {
  border: 1px solid #e4e6ea;
  border-radius: 8px;
  margin: 0 0 12px;
  display: flex;
  gap: 24px;
}

.gsp-card h4 {
  margin: 14px 0 4px;
}

.gsp-note {
  font-size: 12px;
  color: #777;
  font-weight: 400;
}

.gsp-option {
  display: block;
  padding: 5px 0;
  font-size: 14px;
}

.gsp-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 18px;
}

.gsp-actions .run-btn {
  width: auto;
  padding: 10px 22px;
}
</style>
