<script setup>
import { computed, reactive } from 'vue'
import { setPlatformUrl } from '../api'

const props = defineProps({
  opentableUrl: { type: String, default: null },
  theforkUrl: { type: String, default: null },
  doordashUrl: { type: String, default: null },
  ubereatsUrl: { type: String, default: null },
  grubhubUrl: { type: String, default: null },
})
const emit = defineEmits(['saved'])

const PLATFORMS = [
  {
    id: 'opentable',
    label: 'OpenTable',
    placeholder: 'https://www.opentable.com/r/your-restaurant-city',
    help: 'Reviews from diners who booked and dined through OpenTable.',
  },
  {
    id: 'thefork',
    label: 'TheFork (Europe)',
    placeholder: 'https://www.thefork.com/restaurant/your-restaurant-r123456',
    help: "Verified diner reviews. TheFork only shows about its 20 most recent reviews, and scores out of 10 are converted to 5 stars.",
  },
  {
    id: 'doordash',
    label: 'DoorDash',
    placeholder: 'https://www.doordash.com/store/your-restaurant-city-123456/',
    help: 'Customer reviews with star ratings from your DoorDash store page.',
  },
  {
    id: 'ubereats',
    label: 'Uber Eats',
    placeholder: 'https://www.ubereats.com/store/your-restaurant/abc123',
    help: 'Uber Eats reviews have no star ratings, so they are read for tone but never counted in your ratings. Your store\'s own rating is shown separately.',
  },
  {
    id: 'grubhub',
    label: 'Grubhub',
    placeholder: 'https://www.grubhub.com/restaurant/your-restaurant/123456/',
    help: 'Customer reviews with star ratings. This one uses a community-built scraper, so it is the most likely to need attention.',
  },
]
const SAVED = { opentable: 'opentableUrl', thefork: 'theforkUrl', doordash: 'doordashUrl', ubereats: 'ubereatsUrl', grubhub: 'grubhubUrl' }

// Only ask about the platforms that haven't been saved yet.
const missing = computed(() => PLATFORMS.filter((p) => !props[SAVED[p.id]]))

const state = reactive({
  opentable: { link: '', saving: false, error: '' },
  thefork: { link: '', saving: false, error: '' },
  doordash: { link: '', saving: false, error: '' },
  ubereats: { link: '', saving: false, error: '' },
  grubhub: { link: '', saving: false, error: '' },
})

async function save(platform) {
  const s = state[platform.id]
  if (!s.link.trim()) return
  s.saving = true
  s.error = ''
  try {
    const saved = await setPlatformUrl(platform.id, s.link.trim())
    emit('saved', saved)
  } catch (err) {
    s.error = err?.response?.data?.detail || 'Could not save that link.'
  } finally {
    s.saving = false
  }
}
</script>

<template>
  <section v-if="missing.length" class="chart-section">
    <h3>🍽️ Add your reservation and delivery pages</h3>
    <p class="chart-desc">
      Optional: add your restaurant's page on OpenTable, TheFork, DoorDash, Uber Eats or Grubhub to
      analyze those reviews alongside Google and Yelp. Each is saved once for this account. Reviews are collected through
      Apify, so you'll need an Apify key set up on the server.
    </p>
    <div v-for="p in missing" :key="p.id" style="margin-bottom: 12px">
      <div class="analysis-form">
        <label class="field" style="flex: 1; min-width: 260px">
          <span>{{ p.label }} page link</span>
          <input v-model="state[p.id].link" type="text" :placeholder="p.placeholder" @keyup.enter="save(p)" />
        </label>
        <button class="run-btn" :disabled="state[p.id].saving" @click="save(p)">
          {{ state[p.id].saving ? 'Saving…' : `Save ${p.label.split(' ')[0]} page` }}
        </button>
      </div>
      <div class="oc-note">{{ p.help }}</div>
      <p v-if="state[p.id].error" class="status error">{{ state[p.id].error }}</p>
    </div>
  </section>
</template>
