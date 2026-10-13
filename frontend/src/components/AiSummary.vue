<script setup>
import { computed } from 'vue'

// An AI-written summary of what is changing in the reviews, and what to look at first.
// It replaces the "watch this / good news" flags and the drift alerts for every industry except healthcare.
const props = defineProps({ result: { type: Object, default: null } })

const status = computed(() => props.result?.status ?? null)
// Three short paragraphs, each starting with "Label:" (what's changing / what to look at first / what's going well).
const paragraphs = computed(() =>
  (props.result?.text ?? '')
    .split(/\n+/)
    .map((p) => p.trim())
    .filter(Boolean)
    .map((p) => {
      const m = p.match(/^([^:]{3,40}):\s*(.*)$/)
      return m ? { label: m[1], body: m[2] } : { label: '', body: p }
    }),
)
</script>

<template>
  <section v-if="status && status !== 'healthcare'" class="chart-section ai-summary">
    <h3>✨ Summary</h3>

    <template v-if="status === 'ok'">
      <div v-for="(p, i) in paragraphs" :key="i" class="ai-para">
        <strong v-if="p.label">{{ p.label }}</strong> {{ p.body }}
      </div>
      <p class="oc-note ai-note">
        Written by an AI model from your numbers and a small sample of recent reviews
        ({{ result.written }} written reviews over {{ result.months }} months). It can be wrong, so check it against the charts below.
      </p>
    </template>
    <p v-else-if="status === 'too_few'" class="status">
      A summary needs at least {{ result.minimum }} written reviews in this window; there are {{ result.written }} so far.
      With fewer, any "trend" would be guesswork.
    </p>
    <p v-else class="status">The summary is unavailable right now. The charts and numbers below are unaffected.</p>
  </section>
</template>

<style>
.ai-summary {
  border-left: 4px solid var(--brand, #ff4b4b);
}

.ai-para {
  margin: 0 0 10px;
  font-size: 14px;
  line-height: 1.5;
  color: #222;
}

.ai-para strong {
  color: #c2260c;
}

.ai-note {
  margin-top: 8px;
}
</style>
