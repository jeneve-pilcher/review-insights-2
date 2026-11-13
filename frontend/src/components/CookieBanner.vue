<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { accept, getConsent, loadTrackers, OPEN_EVENT, reject } from '../utils/consent'

const show = ref(false)
const current = ref(null)

function reopen() { current.value = getConsent(); show.value = true }

onMounted(() => {
  current.value = getConsent()
  if (current.value === 'accepted') loadTrackers()   // they accepted on an earlier visit
  else if (current.value === null) show.value = true // never asked (or the choice expired): ask, and load nothing
  window.addEventListener(OPEN_EVENT, reopen)
})
onBeforeUnmount(() => window.removeEventListener(OPEN_EVENT, reopen))

function onAccept() { accept(); current.value = 'accepted'; show.value = false }
function onReject() { show.value = false; reject() }
</script>

<template>
  <div v-if="show" class="cookie-banner" role="dialog" aria-modal="false" aria-labelledby="cookie-title">
    <div class="cookie-text">
      <strong id="cookie-title">Cookies</strong>
      <p>
        We use essential storage to keep you signed in and remember your settings. With your permission we would also
        use analytics and advertising cookies. None of those load unless you accept, and rejecting them changes nothing
        about how the service works.
        <a href="/#privacy">Privacy policy</a>
      </p>
    </div>
    <div class="cookie-actions">
      <button type="button" class="cookie-btn" @click="onReject">Reject</button>
      <button type="button" class="cookie-btn cookie-accept" @click="onAccept">Accept</button>
    </div>
  </div>
</template>

<style>
.cookie-banner {
  position: fixed;
  left: 12px;
  right: 12px;
  bottom: 12px;
  z-index: 10000;
  max-width: 760px;
  margin: 0 auto;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px 20px;
  padding: 14px 18px;
  background: #fff;
  color: #222;
  border: 1px solid #d6d3d1;
  border-radius: 12px;
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.18);
  font-size: 14px;
  line-height: 1.45;
}
.cookie-text { flex: 1 1 320px; min-width: 0; }
.cookie-text p { margin: 4px 0 0; }
.cookie-actions { display: flex; gap: 10px; flex: 0 0 auto; }
/* Reject and Accept look equally easy to press. */
.cookie-btn {
  min-width: 96px;
  padding: 10px 18px;
  border-radius: 8px;
  border: 1px solid #1f2937;
  background: #fff;
  color: #1f2937;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
}
.cookie-accept { background: #1f2937; color: #fff; }
@media (max-width: 520px) {
  .cookie-actions { width: 100%; }
  .cookie-btn { flex: 1; }
}
</style>
