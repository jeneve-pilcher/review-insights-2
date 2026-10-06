<script setup>
import { EFFECTIVE_DATE, SECTIONS, TERMS_VERSION, segments } from '../legal/terms'

function jump(id) {
  document.getElementById(`tos-${id}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
</script>

<template>
  <article class="tos">
    <h2>Terms of Service</h2>
    <p class="tos-meta">Version {{ TERMS_VERSION }} · Effective {{ EFFECTIVE_DATE }}</p>

    <nav class="tos-toc" aria-label="Sections">
      <button v-for="s in SECTIONS" :key="s.id" class="oc-link" @click="jump(s.id)">{{ s.title }}</button>
    </nav>

    <section v-for="s in SECTIONS" :id="`tos-${s.id}`" :key="s.id" class="tos-section">
      <h3>{{ s.title }}</h3>
      <template v-for="(b, i) in s.blocks" :key="i">
        <p v-if="b.type === 'p'">
          <template v-for="(seg, j) in segments(b.text)" :key="j">
            <mark v-if="seg.placeholder" class="tos-missing">{{ seg.text }}</mark>
            <template v-else>{{ seg.text }}</template>
          </template>
        </p>

        <ul v-else-if="b.type === 'list'">
          <li v-for="(item, k) in b.items" :key="k">
            <template v-for="(seg, j) in segments(item)" :key="j">
              <mark v-if="seg.placeholder" class="tos-missing">{{ seg.text }}</mark>
              <template v-else>{{ seg.text }}</template>
            </template>
          </li>
        </ul>

        <div v-else-if="b.type === 'topics'" class="tos-topics">
          <div v-for="t in b.items" :id="`tos-rely-${t.id}`" :key="t.id" class="tos-topic">
            <strong>{{ t.title }}.</strong>
            <template v-for="(seg, j) in segments(t.text)" :key="j">
              <mark v-if="seg.placeholder" class="tos-missing">{{ seg.text }}</mark>
              <template v-else> {{ seg.text }}</template>
            </template>
          </div>
        </div>
      </template>
    </section>
  </article>
</template>

<style>
.tos {
  font-size: 14px;
  line-height: 1.6;
  color: #222;
}

.tos h2 {
  margin: 0 0 4px;
}

.tos h3 {
  margin: 22px 0 8px;
  font-size: 16px;
}

.tos-meta {
  color: #777;
  font-size: 12px;
  margin: 0 0 12px;
}

.tos-toc {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  font-size: 13px;
  padding: 10px 14px;
  background: #f7f8fa;
  border: 1px solid #e4e6ea;
  border-radius: 8px;
}

.tos-topics {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.tos-topic {
  background: #faf8ff;
  border: 1px solid #e4defa;
  border-radius: 8px;
  padding: 10px 14px;
}

.tos ul {
  padding-left: 20px;
}

.tos li {
  margin-bottom: 6px;
}

.tos-missing {
  background: #fff3a8;
  color: #6b4e00;
  padding: 0 4px;
  border-radius: 3px;
  font-weight: 600;
}
</style>
