<script setup>
import { computed } from 'vue'

const props = defineProps({
  meta: { type: Object, default: null },
  // 'all'     = every review (written + star-only)
  // 'written' = written reviews only
  // 'both'    = counts and ratings use every review, language uses written ones
  uses: { type: String, default: 'both' },
})

const text = computed(() => {
  const m = props.meta
  if (!m) return ''
  const all = m.reviews_analyzed
  const written = m.reviews_with_text
  if (props.uses === 'all') return `Uses all ${all} reviews (written + star-only)`
  if (props.uses === 'written') return `Uses the ${written} written reviews (of ${all})`
  return `Counts & ratings: all ${all} reviews · Language: ${written} written`
})
</script>

<template>
  <span v-if="text" class="data-basis">{{ text }}</span>
</template>

<style>
.data-basis {
  display: inline-block;
  background: #eef6ff;
  color: #1a5f9e;
  border: 1px solid #d3e6f8;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 9px;
  border-radius: 999px;
  vertical-align: middle;
}
</style>
