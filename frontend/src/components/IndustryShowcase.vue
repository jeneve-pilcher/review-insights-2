<script setup>
import { computed } from 'vue'
import { EVERY_INDUSTRY, groupedIndustries, industryById, sourceChips } from '../content/industries'

// "Built for your industry": a card for every industry, and for the one selected, what it tracks, the graphs it gets
// and its data sources. This is both the marketing and the first step of getting started.
const props = defineProps({
  selected: { type: String, default: '' },
})
const emit = defineEmits(['select', 'start'])

const groups = groupedIndustries()
const current = computed(() => industryById(props.selected))
const chips = computed(() => sourceChips(current.value))

function pick(i) {
  if (i.available) emit('select', i.id)
}
</script>

<template>
  <section id="industries" class="ind-section">
    <h2>Built for your industry</h2>
    <p class="ind-sub">
      Pick yours. Each industry gets its own themes to watch, its own graphs and the data sources that fit it.
    </p>

    <div v-for="g in groups" :key="g.name" class="ind-group">
      <h3>{{ g.name }}</h3>
      <div class="ind-grid">
        <button
          v-for="i in g.items"
          :key="i.id"
          type="button"
          class="ind-card"
          :class="{ selected: selected === i.id, soon: !i.available }"
          :aria-pressed="selected === i.id"
          :disabled="!i.available"
          @click="pick(i)"
        >
          <strong>{{ i.label }}</strong>
          <span class="ind-blurb">{{ i.blurb }}</span>
          <span class="ind-pitch">{{ i.available ? i.pitch : 'Coming soon' }}</span>
        </button>
      </div>
    </div>

    <div v-if="current" class="ind-detail">
      <h3>{{ current.label }}</h3>
      <p class="ind-pitch">{{ current.pitch }}</p>

      <div class="ind-cols">
        <div>
          <h4>What it tracks</h4>
          <p class="ind-chips"><span v-for="t in current.themes" :key="t" class="ind-chip">{{ t }}</span></p>
          <h4>Data sources</h4>
          <p class="ind-chips"><span v-for="c in chips" :key="c" class="ind-chip">{{ c }}</span></p>
        </div>
        <div>
          <h4>Graphs and tools you get</h4>
          <ul>
            <li v-for="g in current.graphs" :key="g">{{ g }}</li>
          </ul>
          <p v-for="n in current.notes" :key="n" class="ind-note">{{ n }}</p>
        </div>
      </div>

      <h4>In every industry</h4>
      <ul class="ind-every">
        <li v-for="e in EVERY_INDUSTRY" :key="e">{{ e }}</li>
      </ul>

      <button class="run-btn ind-go" type="button" @click="emit('start')">Start with {{ current.label }}</button>
    </div>
    <p v-else class="ind-hint">Select an industry to see what you'd get.</p>
  </section>
</template>

<style>
.ind-section {
  padding: 48px 20px 24px;
  max-width: 1000px;
  margin: 0 auto;
}

.ind-section h2 {
  text-align: center;
  margin-bottom: 6px;
}

.ind-sub {
  text-align: center;
  color: #555;
  margin: 0 auto 24px;
  max-width: 620px;
}

.ind-group h3 {
  text-align: center;
  margin: 18px 0 8px;
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #777;
}

/* Flex, not a fixed grid: the cards in every row stretch to fill it, so a pair of cards (or a lone one) fills the whole
   row instead of leaving empty space at the end. */
.ind-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.ind-card {
  flex: 1 1 230px;
  text-align: center;
  align-items: center;
  background: white;
  border: 1px solid #e4e6ea;
  border-radius: 10px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  cursor: pointer;
  font-family: inherit;
}

.ind-card:hover:not(:disabled) {
  border-color: var(--brand, #ff4b4b);
}

.ind-card.selected {
  border-color: var(--brand, #ff4b4b);
  box-shadow: 0 0 0 2px var(--brand-border, #e4defa);
}

.ind-card.soon {
  opacity: 0.55;
  cursor: default;
}

.ind-blurb {
  font-size: 12px;
  color: #777;
}

.ind-pitch {
  font-size: 13px;
  color: #444;
}

.ind-detail {
  margin-top: 24px;
  background: white;
  border: 1px solid #e4e6ea;
  border-radius: 12px;
  padding: 22px 26px;
}

.ind-detail h3 {
  margin: 0 0 4px;
  text-align: center;
}

.ind-detail > .ind-pitch {
  text-align: center;
}

.ind-detail h4 {
  margin: 14px 0 6px;
  font-size: 13px;
  color: #777;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.ind-cols {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

@media (max-width: 720px) {
  .ind-cols {
    grid-template-columns: 1fr;
  }
}

.ind-detail ul {
  margin: 0;
  padding-left: 18px;
  font-size: 14px;
  color: #333;
}

.ind-detail li {
  margin-bottom: 6px;
}

.ind-chips {
  margin: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.ind-chip {
  background: var(--brand-soft, #faf8ff);
  border: 1px solid var(--brand-border, #e4defa);
  border-radius: 999px;
  padding: 2px 10px;
  font-size: 12px;
}

.ind-note {
  font-size: 12px;
  color: #666;
  margin: 8px 0 0;
}

.ind-go {
  display: block;
  width: auto;
  padding: 10px 24px;
  margin: 18px auto 0;
}

.ind-hint {
  text-align: center;
  color: #777;
  margin-top: 18px;
}
</style>
