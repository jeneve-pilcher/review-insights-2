<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { repliesApi } from '../api'
import { CATEGORY_LABELS, toneClass, toneLabel } from '../utils/mentions'
import {
  FILTERS,
  countByFilter,
  filterReviews,
  platformLabel,
  replyStatusLabel,
  reviewPageUrl,
  wordCount,
} from '../utils/replies'

const props = defineProps({
  reviewList: { type: Object, default: null },
  // Set for a company location; empty for a single business.
  locationId: { type: String, default: null },
  businessLocation: { type: String, default: null },
  yelpUrl: { type: String, default: null },
  opentableUrl: { type: String, default: null },
  doordashUrl: { type: String, default: null },
  grubhubUrl: { type: String, default: null },
  // Healthcare: answering a patient's review can disclose protected health information, so replies are switched off.
  repliesOff: { type: Boolean, default: false },
})

const PAGE = 10
const filter = ref('all')
const source = ref('all')
const shownCount = ref(PAGE)

const replies = ref({})
const canSave = ref(true)
const engine = ref('template')
const loadError = ref('')
const editors = reactive({})

async function loadReplies() {
  loadError.value = ''
  try {
    const res = await repliesApi.list(props.locationId)
    replies.value = res.replies
    canSave.value = res.can_save
    engine.value = res.engine
  } catch (err) {
    loadError.value = err?.response?.data?.detail || 'Could not load saved replies.'
  }
}

watch(() => props.locationId, loadReplies, { immediate: true })

const items = computed(() => props.reviewList?.items ?? [])
const sources = computed(() => [...new Set(items.value.map((r) => r.source))])
const counts = computed(() => countByFilter(items.value, replies.value))
const filtered = computed(() => filterReviews(items.value, { filter: filter.value, source: source.value, replies: replies.value }))
const shown = computed(() => filtered.value.slice(0, shownCount.value))

function setFilter(id) {
  filter.value = id
  shownCount.value = PAGE
}

function ensure(key, text = '') {
  if (!editors[key]) {
    editors[key] = { open: false, text, tone: 'friendly', busy: false, warnings: [], note: '', engine: '', error: '', message: '' }
  }
  return editors[key]
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    const box = document.createElement('textarea')
    box.value = text
    document.body.appendChild(box)
    box.select()
    const ok = document.execCommand('copy')
    document.body.removeChild(box)
    return ok
  }
}

async function draft(item, quick = false) {
  const e = ensure(item.key)
  e.busy = true
  e.error = ''
  e.message = ''
  try {
    const res = await repliesApi.draft({
      location_id: props.locationId,
      review_key: item.key,
      source: item.source,
      rating: item.rating,
      text: item.text,
      tone: e.tone,
    })
    e.text = res.text
    e.warnings = res.warnings
    e.note = res.note || ''
    e.engine = res.engine
    e.open = true
    if (quick) e.message = (await copyText(res.text)) ? 'Draft copied. Paste it on the platform, then mark it as sent.' : 'Draft ready. Use Copy.'
  } catch (err) {
    e.error = err?.response?.data?.detail || 'Could not draft a reply.'
  } finally {
    e.busy = false
  }
}

function editSaved(item) {
  const e = ensure(item.key, replies.value[item.key].reply_text)
  e.text = replies.value[item.key].reply_text
  e.open = true
}

async function save(item, status) {
  const e = editors[item.key]
  if (!e || !e.text.trim()) return
  if (status === 'sent' && !window.confirm(
    `Mark as sent? Only do this after you've pasted the reply on ${platformLabel(item.source)}. This app can't post it for you.`
  )) return
  e.busy = true
  e.error = ''
  try {
    const saved = await repliesApi.save({
      location_id: props.locationId,
      review_key: item.key,
      source: item.source,
      rating: item.rating,
      review_date: item.date,
      text: e.text,
      status,
    })
    replies.value = { ...replies.value, [item.key]: saved }
    e.message = status === 'sent' ? 'Marked as sent.' : 'Draft saved.'
    if (status === 'sent') e.open = false
  } catch (err) {
    e.error = err?.response?.data?.detail || 'Could not save.'
  } finally {
    e.busy = false
  }
}

async function copy(item) {
  const e = editors[item.key]
  e.message = (await copyText(e.text)) ? 'Copied.' : 'Could not copy automatically. Select the text and copy it.'
}

const pageUrl = (item) => reviewPageUrl(item, {
    businessLocation: props.businessLocation,
    yelpUrl: props.yelpUrl,
    opentableUrl: props.opentableUrl,
    doordashUrl: props.doordashUrl,
    grubhubUrl: props.grubhubUrl,
  })
const stars = (n) => (n == null ? '' : '★'.repeat(n) + '☆'.repeat(5 - n))
</script>

<template>
  <section class="chart-section">
    <div class="title-row">
      <h3>💬 Reviews &amp; draft replies</h3>
      <span class="data-basis">Every review (and web mention) in your window, newest first</span>
    </div>
    <p v-if="repliesOff" class="status error">
      Replies are turned off for healthcare accounts. Answering a patient's review in public can disclose protected health
      information, even just by confirming the person was a patient. Follow up with the person privately, offline.
    </p>
    <p v-else class="chart-desc">
      Draft a reply to any review, edit it, then copy it and post it on the platform. Drafts are
      {{ engine === 'ai' ? 'written by AI from the review text (personal details removed first)' : 'built from a standard template, since AI drafting is not set up' }};
      always read before posting. <strong>This app can't post replies for you</strong>: direct posting
      needs each platform's approved API access. "Mark as sent" just records that you posted it, so
      your team can see what's been answered. Web mentions are listed here too, but they have no stars
      and can't be replied to from this app.
    </p>

    <p v-if="!reviewList" class="status">Run analysis above to see your reviews.</p>
    <p v-else-if="loadError" class="status error">{{ loadError }}</p>

    <template v-else>
      <p v-if="!canSave" class="status">You can read replies here, but your role can't draft or save them.</p>

      <div class="rr-filters">
        <button
          v-for="f in FILTERS"
          :key="f.id"
          class="rr-chip"
          :class="{ active: filter === f.id }"
          @click="setFilter(f.id)"
        >
          {{ f.label }} <span class="rr-count">{{ counts[f.id] }}</span>
        </button>
        <select v-if="sources.length > 1" v-model="source" class="months-select rr-source" @change="shownCount = PAGE">
          <option value="all">All platforms</option>
          <option v-for="s in sources" :key="s" :value="s">{{ platformLabel(s) }}</option>
        </select>
      </div>
      <p v-if="reviewList.total > reviewList.shown" class="oc-note">
        Showing the newest {{ reviewList.shown }} of {{ reviewList.total }} reviews.
      </p>

      <p v-if="!filtered.length" class="status">No reviews match this filter.</p>

      <div v-for="item in shown" :key="item.key" class="rr-card">
        <div class="rr-head">
          <span v-if="item.rating != null" class="rr-stars" :class="item.rating <= 2 ? 'low' : item.rating === 3 ? 'mid' : 'high'">{{ stars(item.rating) }}</span>
          <span class="rr-chip static">{{ platformLabel(item.source) }}</span>
          <template v-if="item.rating == null">
            <span class="rr-chip static">{{ CATEGORY_LABELS[item.category] ?? item.category }}</span>
            <span class="mn-tone" :class="toneClass(item.sentiment)">{{ toneLabel(item.sentiment) }}</span>
            <span class="oc-note" style="margin: 0">{{ item.domain }}</span>
          </template>
          <span class="rr-date">{{ String(item.date || 'date unknown').slice(0, 10) }}</span>
          <span v-if="replies[item.key]" class="rr-chip static" :class="replies[item.key].status === 'sent' ? 'done' : 'draft'">
            {{ replyStatusLabel(replies[item.key]) }}
          </span>
        </div>
        <p v-if="item.has_text" class="rr-text">{{ item.text }}</p>
        <p v-else class="rr-text rr-none">Star rating only, no written comment.</p>

        <!-- web mentions and Uber Eats (no stars): read-only -->
        <div v-if="item.rating == null || repliesOff" class="rr-actions">
          <a v-if="item.url" class="oc-btn rr-link" :href="item.url" target="_blank" rel="noopener noreferrer">Open page ↗</a>
          <span v-if="repliesOff" class="oc-note" style="margin: 0">Replies are off for healthcare accounts.</span>
          <span v-else class="oc-note" style="margin: 0">No stars and no reply from here: this isn't a star review on a platform you can answer from this app.</span>
        </div>

        <!-- editor -->
        <div v-else-if="editors[item.key]?.open" class="rr-editor">
          <textarea v-model="editors[item.key].text" rows="4" class="rr-textarea"></textarea>
          <div class="oc-note">
            {{ wordCount(editors[item.key].text) }} words
            <span v-if="editors[item.key].engine"> · {{ editors[item.key].engine === 'ai' ? 'AI draft' : 'template draft' }}</span>
          </div>
          <p v-if="editors[item.key].note" class="oc-note">{{ editors[item.key].note }}</p>
          <div v-for="w in editors[item.key].warnings" :key="w" class="rr-warning">⚠️ {{ w }}</div>
          <div class="rr-actions">
            <select v-model="editors[item.key].tone" class="months-select rr-tone" :disabled="editors[item.key].busy">
              <option value="friendly">Friendly</option>
              <option value="professional">Professional</option>
              <option value="apologetic">Apologetic</option>
            </select>
            <button class="oc-btn" :disabled="editors[item.key].busy" @click="draft(item)">Redraft</button>
            <button class="oc-btn" @click="copy(item)">Copy</button>
            <a v-if="pageUrl(item)" class="oc-btn rr-link" :href="pageUrl(item)" target="_blank" rel="noopener noreferrer">
              Open {{ platformLabel(item.source) }} ↗
            </a>
            <button class="oc-btn" :disabled="editors[item.key].busy" @click="save(item, 'draft')">Save draft</button>
            <button class="oc-btn primary" :disabled="editors[item.key].busy" @click="save(item, 'sent')">Mark as sent</button>
            <button class="oc-btn" @click="editors[item.key].open = false">Close</button>
          </div>
        </div>

        <!-- saved reply, collapsed -->
        <div v-else-if="replies[item.key]" class="rr-saved">
          <strong>{{ replies[item.key].status === 'sent' ? 'Your reply' : 'Saved draft' }}:</strong>
          {{ replies[item.key].reply_text }}
          <div v-if="canSave"><button class="oc-btn" @click="editSaved(item)">Edit</button></div>
        </div>

        <!-- no reply yet -->
        <div v-else-if="canSave" class="rr-actions">
          <button class="oc-btn" :disabled="editors[item.key]?.busy" @click="draft(item)">
            {{ editors[item.key]?.busy ? 'Drafting…' : 'Draft reply' }}
          </button>
          <button class="oc-btn" :disabled="editors[item.key]?.busy" @click="draft(item, true)">Quick reply (draft + copy)</button>
        </div>

        <p v-if="editors[item.key]?.error" class="status error">{{ editors[item.key].error }}</p>
        <p v-if="editors[item.key]?.message" class="oc-note">{{ editors[item.key].message }}</p>
      </div>

      <button v-if="filtered.length > shownCount" class="oc-btn" style="margin-top: 8px" @click="shownCount += PAGE">
        Show {{ Math.min(PAGE, filtered.length - shownCount) }} more
      </button>
    </template>
  </section>
</template>

<style>
.rr-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  margin-bottom: 10px;
}

.rr-chip {
  border: 1px solid #d3d6db;
  background: white;
  border-radius: 999px;
  padding: 4px 12px;
  font-size: 12px;
  cursor: pointer;
}

.rr-chip.active {
  background: #1a1a1a;
  border-color: #1a1a1a;
  color: white;
}

.rr-chip.static {
  cursor: default;
  background: #eef0f3;
  border-color: #eef0f3;
  padding: 2px 9px;
}

.rr-chip.static.done { background: #e3f6ea; color: #1e7a45; border-color: #e3f6ea; }
.rr-chip.static.draft { background: #fff4d6; color: #8a6200; border-color: #fff4d6; }

.rr-count {
  opacity: 0.7;
  margin-left: 2px;
}

.rr-source {
  width: auto;
}

.rr-card {
  border: 1px solid #e4e6ea;
  border-radius: 10px;
  padding: 12px 14px;
  margin-bottom: 10px;
  background: white;
}

.rr-head {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.rr-stars {
  letter-spacing: 1px;
  font-size: 14px;
}

.rr-stars.low { color: #e74c3c; }
.rr-stars.mid { color: #f1a30f; }
.rr-stars.high { color: #2ecc71; }

.rr-date {
  color: #888;
  font-size: 12px;
}

.rr-text {
  margin: 8px 0;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
}

.rr-none {
  color: #888;
  font-style: italic;
}

.rr-editor {
  background: var(--brand-soft, #faf8ff);
  border: 1px solid var(--brand-border, #e4defa);
  border-radius: 8px;
  padding: 10px;
  margin-top: 6px;
}

.rr-textarea {
  width: 100%;
  font-family: inherit;
  font-size: 13px;
  line-height: 1.5;
  border: 1px solid #d3d6db;
  border-radius: 6px;
  padding: 8px;
  box-sizing: border-box;
}

.rr-warning {
  background: #fff8e6;
  border: 1px solid #f2d98a;
  border-radius: 6px;
  padding: 6px 10px;
  font-size: 12px;
  margin: 6px 0;
}

.rr-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  margin-top: 8px;
}

.rr-tone {
  width: auto;
}

.rr-link {
  text-decoration: none;
  color: inherit;
}

.rr-saved {
  background: #f5fcf8;
  border: 1px solid #cdeedb;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 13px;
  white-space: pre-wrap;
}

.oc-btn.primary {
  background: #1a1a1a;
  color: white;
  border-color: #1a1a1a;
}
</style>
