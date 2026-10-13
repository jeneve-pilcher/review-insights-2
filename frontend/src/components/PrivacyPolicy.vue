<script setup>
import { segments } from '../legal/terms'
import { PRIVACY_DATE, PRIVACY_SECTIONS } from '../legal/privacy'
</script>

<template>
  <article class="pp">
    <h2>Privacy Policy</h2>
    <p class="pp-meta">Last updated {{ PRIVACY_DATE }}</p>

    <section v-for="s in PRIVACY_SECTIONS" :id="`pp-${s.id}`" :key="s.id" class="pp-section">
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
      </template>
    </section>
  </article>
</template>

<style>
.pp { max-width: 760px; margin: 0 auto; font-size: 15px; line-height: 1.65; color: #292524; text-align: left; }
.pp h2 { margin: 0 0 4px; }
.pp-meta { margin: 0 0 18px; color: #78716c; font-size: 13px; }
.pp-section { margin-top: 20px; }
.pp-section h3 { margin: 0 0 6px; font-size: 17px; color: #7c2d12; }
.pp-section p { margin: 6px 0; }
.pp-section ul { margin: 6px 0; padding-left: 20px; }
.pp-section li { margin: 4px 0; }
.pp .tos-missing { background: #fef3c7; padding: 0 3px; border-radius: 3px; }
</style>
