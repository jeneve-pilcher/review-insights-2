<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { emptyLinks, missingPlatforms, savedPlatforms } from '../utils/links'
import { splitPlatforms } from '../utils/onboarding'

// The optional review-page fields. Pages already saved show as connected (they're set once). The rest are inputs:
// the industry's recommended platforms (and any the person said they use) up front, the others behind "show more".
// The parent owns the values (v-model) and does the saving.
const props = defineProps({
  modelValue: { type: Object, default: () => emptyLinks() },
  current: { type: Object, default: () => ({}) },
  pack: { type: Object, default: null },
  chosen: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:modelValue'])

const local = reactive({ ...emptyLinks(), ...props.modelValue })
watch(local, () => emit('update:modelValue', { ...local }), { deep: true })

const showMore = ref(false)
const saved = computed(() => savedPlatforms(props.current))
const missing = computed(() => missingPlatforms(props.current))
const split = computed(() => splitPlatforms(missing.value, props.pack, props.chosen))
// Never hide a field that already has something typed in it.
const hiddenMore = computed(() => (showMore.value ? [] : split.value.more.filter((p) => !local[p.column])))
const visibleMore = computed(() => split.value.more.filter((p) => showMore.value || local[p.column]))
</script>

<template>
  <div>
    <div v-for="p in saved" :key="p.id" class="oc-note" style="margin: 4px 0">
      ✓ <strong>{{ p.label }}</strong> connected <span class="muted">{{ current[p.column] }}</span>
    </div>

    <label v-for="p in [...split.primary, ...visibleMore]" :key="p.id" class="field" style="display: block; margin: 10px 0">
      <span>{{ p.label }} page (optional)</span>
      <input v-model="local[p.column]" type="text" :placeholder="p.placeholder" style="width: 100%" />
      <small class="oc-note" style="display: block">{{ p.help }}</small>
    </label>

    <button v-if="hiddenMore.length" type="button" class="oc-link" @click="showMore = true">
      Show {{ hiddenMore.length }} more platform{{ hiddenMore.length === 1 ? '' : 's' }}
    </button>

    <p v-if="!missing.length" class="oc-note">Every page is connected. Contact support if one needs to change.</p>
  </div>
</template>
