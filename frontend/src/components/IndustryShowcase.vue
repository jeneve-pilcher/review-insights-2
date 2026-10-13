<script setup>
import { computed, ref, watch } from 'vue'
import { EVERY_INDUSTRY, groupedIndustries, industryById, industryHover, sourceChips, sourceHover, themeDetail, themeHover } from '../content/industries'
import { canHover } from '../utils/hover'

// "Built for your industry": a card for every industry, and for the one selected, what it tracks, the graphs it gets and
// its data sources. Hover a tag to see the trends it finds; click it to go to the buy section.
const props = defineProps({
  selected: { type: String, default: '' },
})
const emit = defineEmits(['select', 'start'])

const groups = groupedIndustries()
const current = computed(() => industryById(props.selected))
const chips = computed(() => sourceChips(current.value))
const hoverCapable = canHover()

function pick(i) {
  if (i.available) emit('select', i.id)
}

// Choose this industry and go straight to the buy section (plan and data sources).
function buy(i) {
  emit('select', i.id)
  emit('start')
}

function startCurrent() {
  if (current.value) buy(current.value)
}

function hoverText(type, key) {
  return type === 'theme' ? themeHover(themeDetail(current.value, key)) : sourceHover(key)
}

// With a mouse: hover shows the trends, click goes to the buy section. On a touch screen there is no hover, so the first
// tap shows the same explanation (with a button) and a second tap on the same tag goes to the buy section.
const openChip = ref(null)
watch(() => props.selected, () => { openChip.value = null })

function isOpen(type, key) {
  return openChip.value?.type === type && openChip.value?.key === key
}

function tagClick(type, key) {
  if (hoverCapable || isOpen(type, key)) {
    startCurrent()
    return
  }
  openChip.value = { type, key }
}

const touchExplainer = computed(() => {
  const open = openChip.value
  if (hoverCapable || !open || !current.value) return null
  const text = hoverText(open.type, open.key)
  return text ? { title: open.key, text } : null
})
</script>

<template>
  <section id="industries" class="ind-section">
    <h2>Built for your industry</h2>
    <p class="ind-sub">
      Pick yours. Each industry gets its own themes to watch, its own graphs and the data sources that fit it.
    </p>

    <div v-for="g in groups" :key="g.name" class="ind-group" :class="`grp-${g.name.toLowerCase()}`">
      <h3>{{ g.name }}</h3>
      <div class="ind-grid">
        <div v-for="i in g.items" :key="i.id" class="ind-card" :class="{ selected: selected === i.id, soon: !i.available }">
          <button type="button" class="ind-card-main" :aria-pressed="selected === i.id" :disabled="!i.available" @click="pick(i)">
            <strong>{{ i.label }}</strong>
            <span class="ind-blurb">{{ i.blurb }}</span>
            <span class="ind-pitch">{{ i.available ? i.pitch : 'Coming soon' }}</span>
          </button>
          <span v-if="i.available" class="ind-tagwrap ind-center">
            <button type="button" class="ind-buy" :aria-describedby="`tip-card-${i.id}`" @click="buy(i)">Get started with {{ i.label }} &rarr;</button>
            <span :id="`tip-card-${i.id}`" class="ind-hover" role="tooltip">{{ industryHover(i) }}</span>
          </span>
        </div>
      </div>
    </div>

    <div v-if="current" class="ind-detail">
      <h3>{{ current.label }}</h3>
      <p class="ind-pitch">{{ current.pitch }}</p>

      <div class="ind-cols">
        <div>
          <h4>What it tracks <span class="ind-tip">hover a tag to see the trends it finds, click it to get started</span></h4>
          <p class="ind-chips">
            <span v-for="(t, n) in current.themes" :key="t" class="ind-tagwrap">
              <button type="button" class="ind-chip ind-tag" :class="{ open: isOpen('theme', t) }" :aria-describedby="`tip-theme-${n}`" @click="tagClick('theme', t)">{{ t }}</button>
              <span :id="`tip-theme-${n}`" class="ind-hover" role="tooltip">{{ hoverText('theme', t) }}</span>
            </span>
          </p>
          <h4>Data sources</h4>
          <p class="ind-chips">
            <span v-for="(c, n) in chips" :key="c" class="ind-tagwrap">
              <button type="button" class="ind-chip ind-tag" :class="{ open: isOpen('source', c) }" :aria-describedby="`tip-source-${n}`" @click="tagClick('source', c)">{{ c }}</button>
              <span :id="`tip-source-${n}`" class="ind-hover" role="tooltip">{{ hoverText('source', c) }}</span>
            </span>
          </p>
        </div>
        <div>
          <h4>Graphs and tools you get</h4>
          <ul>
            <li v-for="g in current.graphs" :key="g">{{ g }}</li>
          </ul>
          <p v-for="n in current.notes" :key="n" class="ind-note">{{ n }}</p>
        </div>
      </div>

      <div v-if="touchExplainer" class="ind-explain" role="status">
        <strong>{{ touchExplainer.title }}:</strong> {{ touchExplainer.text }}
        <button type="button" class="ind-buy" @click="startCurrent">Get started with {{ current.label }} &rarr;</button>
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


.grp-restaurants { --grp: #f97316; --grp-text: #b45309; }
.grp-healthcare { --grp: #f59e0b; --grp-text: #92580a; }
.grp-other { --grp: #c2410c; --grp-text: #9a3412; }
.grp-retail { --grp: #ea580c; --grp-text: #9a3412; }

.ind-group h3 {
  text-align: center;
  margin: 18px 0 8px;
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--grp-text, #777);
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
  border-top: 3px solid var(--grp, var(--brand, #ff4b4b));
  border-radius: 10px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ind-card:hover:not(.soon) {
  border-color: var(--brand, #ff4b4b);
}

.ind-card-main {
  background: none;
  border: 0;
  padding: 0;
  width: 100%;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  text-align: center;
  font-family: inherit;
  color: inherit;
  cursor: pointer;
}

.ind-card-main:disabled {
  cursor: default;
}

.ind-buy {
  background: var(--brand-soft, #faf8ff);
  border: 1px solid var(--brand-border, #e4defa);
  border-radius: 999px;
  padding: 4px 14px;
  font-family: inherit;
  font-size: 12px;
  font-weight: 600;
  color: var(--brand, #ff4b4b);
  cursor: pointer;
}

.ind-buy:hover {
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

.ind-tag {
  cursor: pointer;
  font-family: inherit;
  color: inherit;
}

.ind-tag:hover {
  border-color: var(--brand, #ff4b4b);
}

.ind-tag.open {
  background: var(--brand-border, #e4defa);
  border-color: var(--brand, #ff4b4b);
  font-weight: 600;
}

.ind-tip {
  font-size: 11px;
  text-transform: none;
  letter-spacing: 0;
  font-weight: 400;
  margin-left: 6px;
}

/* The hover card: shown on mouse hover and on keyboard focus, so it works without a mouse too. */
.ind-tagwrap {
  position: relative;
  display: inline-block;
}

.ind-hover {
  display: none;
  position: absolute;
  bottom: calc(100% + 8px);
  left: 0;
  width: 280px;
  max-width: 80vw;
  z-index: 20;
  padding: 10px 12px;
  background: #222;
  color: #fff;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 400;
  line-height: 1.4;
  text-align: left;
  text-transform: none;
  letter-spacing: 0;
  pointer-events: none;
}

.ind-center .ind-hover {
  left: 50%;
  transform: translateX(-50%);
}

.ind-tagwrap:hover .ind-hover,
.ind-tagwrap:focus-within .ind-hover {
  display: block;
}

.ind-explain {
  margin: 14px 0 0;
  padding: 10px 14px;
  background: var(--brand-soft, #faf8ff);
  border-left: 3px solid var(--brand, #ff4b4b);
  border-radius: 6px;
  font-size: 14px;
  color: #333;
}

.ind-explain .ind-buy {
  display: block;
  margin-top: 8px;
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
