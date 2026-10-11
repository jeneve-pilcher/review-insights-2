<script setup>
import { computed } from 'vue'
import { groupIndustries } from '../utils/industry'

// The industry picker. Industries that aren't built yet are listed but can't be chosen.
const props = defineProps({
  modelValue: { type: String, default: '' },
  industries: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:modelValue'])

const groups = computed(() => groupIndustries(props.industries))
const selected = computed(() => props.industries.find((i) => i.id === props.modelValue))
</script>

<template>
  <div>
    <label class="field" style="display: block; max-width: 340px">
      <span>Industry</span>
      <select :value="modelValue" style="width: 100%; padding: 8px 10px" @change="emit('update:modelValue', $event.target.value)">
        <optgroup v-for="g in groups" :key="g.name" :label="g.name">
          <option v-for="i in g.items" :key="i.id" :value="i.id" :disabled="!i.available">
            {{ i.label }}{{ i.available ? '' : ' (coming soon)' }}
          </option>
        </optgroup>
      </select>
    </label>
    <small v-if="selected" class="oc-note" style="display: block; margin-top: 4px">
      {{ selected.description }} Sets the themes, graphs and revenue defaults you see.
    </small>
  </div>
</template>
