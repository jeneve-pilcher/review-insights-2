<script setup>
defineProps({
  title: { type: String, default: 'Language read' },
  // [{ tone: 'info' | 'warn' | 'good', text: '...' }]
  items: { type: Array, default: () => [] },
  technique: { type: String, default: '' },
})
</script>

<template>
  <div v-if="items.length" class="nlp-callout">
    <div class="nlp-callout-head">
      <strong>{{ title }}</strong>
    </div>
    <ul class="nlp-list">
      <li v-for="(item, i) in items" :key="i" class="nlp-item" :class="`nlp-${item.tone}`">
        {{ item.text }}
      </li>
    </ul>
    <p v-if="technique" class="nlp-technique">How it works: {{ technique }}</p>
  </div>
</template>

<style>
.nlp-badge {
  display: inline-block;
  background: #efeaff;
  color: #5b3fc4;
  border: 1px solid #d9d0fb;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 999px;
  vertical-align: middle;
  letter-spacing: 0.02em;
}

.nlp-callout {
  background: var(--brand-soft, #faf8ff);
  border: 1px solid var(--brand-border, #e4defa);
  border-radius: 10px;
  padding: 12px 16px;
  margin: 0 0 18px;
}

.nlp-callout-head {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  margin-bottom: 8px;
}

.nlp-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.nlp-item {
  font-size: 13px;
  line-height: 1.45;
  padding-left: 18px;
  position: relative;
  color: #333;
}

.nlp-item::before {
  content: '';
  position: absolute;
  left: 2px;
  top: 6px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #9aa0aa;
}

.nlp-item.nlp-warn::before { background: #e67e22; }
.nlp-item.nlp-good::before { background: #2ecc71; }
.nlp-item.nlp-info::before { background: var(--accent, #7c5ce0); }

.nlp-technique {
  margin: 10px 0 0;
  font-size: 11px;
  color: #8a8f99;
  line-height: 1.4;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.title-row h3 {
  margin: 0;
}
</style>
