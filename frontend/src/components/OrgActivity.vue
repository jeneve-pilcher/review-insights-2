<script setup>
import { onMounted, ref } from 'vue'
import { orgApi } from '../api'
import { actionLabel, describeAudit, timeAgo } from '../utils/orgFormat'

const rows = ref([])
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    rows.value = await orgApi.audit()
  } catch (err) {
    error.value = err?.response?.data?.detail || 'Could not load the activity log.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <p class="oc-note">A record of who did what in this company: team changes, locations, budgets, manual checks and task updates.</p>
    <p v-if="loading" class="status">Loading…</p>
    <p v-else-if="error" class="status error">{{ error }}</p>
    <p v-else-if="!rows.length" class="status">No activity yet.</p>
    <div v-else class="oc-scroll">
      <table class="oc-table">
        <thead><tr><th>When</th><th>Who</th><th>What</th><th>Details</th></tr></thead>
        <tbody>
          <tr v-for="e in rows" :key="e.id">
            <td :title="e.created_at">{{ timeAgo(e.created_at) }}</td>
            <td>{{ e.user_email }}</td>
            <td>{{ actionLabel(e.action) }}<span v-if="e.target"> — <strong>{{ e.target }}</strong></span></td>
            <td class="oc-note" style="margin: 0">{{ describeAudit(e) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
