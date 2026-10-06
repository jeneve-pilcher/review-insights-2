<script setup>
import { ref } from 'vue'
import { acceptTerms } from '../api'
import { TERMS_VERSION } from '../legal/terms'
import TermsOfService from './TermsOfService.vue'

const props = defineProps({
  // 'accept' = must agree to continue; 'read' = just reading, with a Close button.
  mode: { type: String, default: 'read' },
})
const emit = defineEmits(['accepted', 'close', 'decline'])

const agreed = ref(false)
const saving = ref(false)
const error = ref('')

async function accept() {
  if (!agreed.value) return
  saving.value = true
  error.value = ''
  try {
    emit('accepted', await acceptTerms(TERMS_VERSION))
  } catch (err) {
    error.value = err?.response?.data?.detail || 'Could not record your agreement. Please try again.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="tg-backdrop" role="dialog" aria-modal="true" aria-label="Terms of Service">
    <div class="tg-dialog">
      <div class="tg-body">
        <p v-if="mode === 'accept'" class="tg-intro">
          Please read and agree to our Terms of Service to continue. The section
          <strong>“Before you rely on it”</strong> explains what the service can and can't be relied on for.
        </p>
        <TermsOfService />
      </div>

      <div class="tg-footer">
        <template v-if="mode === 'accept'">
          <label class="source-check">
            <input v-model="agreed" type="checkbox" />
            I have read and agree to these Terms of Service (version {{ TERMS_VERSION }}).
          </label>
          <div class="tg-buttons">
            <button class="run-btn" style="width: auto; padding: 9px 22px" :disabled="!agreed || saving" @click="accept">
              {{ saving ? 'Saving…' : 'Agree and continue' }}
            </button>
            <button class="oc-btn" :disabled="saving" @click="emit('decline')">I don't agree (log out)</button>
          </div>
        </template>
        <button v-else class="oc-btn" @click="emit('close')">Close</button>
        <p v-if="error" class="status error">{{ error }}</p>
      </div>
    </div>
  </div>
</template>

<style>
.tg-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(20, 20, 30, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  z-index: 1000;
}

.tg-dialog {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 780px;
  max-height: 92vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
}

.tg-body {
  overflow-y: auto;
  padding: 20px 24px;
}

.tg-intro {
  background: #fff8e6;
  border: 1px solid #f2d98a;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 13px;
  margin: 0 0 14px;
}

.tg-footer {
  border-top: 1px solid #e4e6ea;
  padding: 14px 24px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.tg-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  align-items: center;
}
</style>
