<script setup>
import { ref } from 'vue'
import { orgApi } from '../api'
import { ROLE_LABELS } from '../utils/orgFormat'

const props = defineProps({
  info: { type: Object, required: true },
})
const emit = defineEmits(['changed'])

const email = ref('')
const role = ref('manager')
const message = ref('')
const busy = ref(false)

async function add() {
  if (!email.value.trim()) return
  busy.value = true
  message.value = ''
  try {
    await orgApi.addMember(email.value.trim(), role.value)
    message.value = `Added ${email.value.trim()}. Ask them to sign up or log in with that email and they'll be connected automatically. No email is sent.`
    email.value = ''
    emit('changed')
  } catch (err) {
    message.value = err?.response?.data?.detail || 'Could not add that person.'
  } finally {
    busy.value = false
  }
}

async function changeRole(member, newRole) {
  message.value = ''
  try {
    await orgApi.updateMember(member.id, newRole)
    emit('changed')
  } catch (err) {
    message.value = err?.response?.data?.detail || 'Could not change the role.'
    emit('changed')
  }
}

async function remove(member) {
  if (!window.confirm(`Remove ${member.email}? They lose access immediately.`)) return
  message.value = ''
  try {
    await orgApi.removeMember(member.id)
    emit('changed')
  } catch (err) {
    message.value = err?.response?.data?.detail || 'Could not remove them.'
  }
}
</script>

<template>
  <div>
    <section class="oc-card" style="margin-bottom: 16px">
      <h4 style="margin-top: 0">Add someone</h4>
      <div class="analysis-form">
        <label class="field" style="min-width: 240px">
          <span>Email</span>
          <input v-model="email" type="text" placeholder="gm@company.com" @keyup.enter="add" />
        </label>
        <label class="field">
          <span>Role</span>
          <select v-model="role" class="months-select">
            <option value="manager">Manager (own locations)</option>
            <option value="viewer">Viewer (read-only)</option>
            <option v-if="info.can.manage_admins" value="admin">Admin (everything but billing)</option>
          </select>
        </label>
        <button class="oc-btn" :disabled="busy" @click="add">Add</button>
      </div>
      <p class="oc-note">
        A manager is tied to a location by the manager email on that location. Managers and viewers can
        be on any plan, including Free.
      </p>
    </section>
    <p v-if="message" class="status analysis-note">{{ message }}</p>

    <div class="oc-scroll">
      <table class="oc-table">
        <thead><tr><th>Email</th><th>Role</th><th>Status</th><th></th></tr></thead>
        <tbody>
          <tr v-for="m in info.members" :key="m.id">
            <td>{{ m.email }}</td>
            <td>
              <span v-if="m.role === 'owner'" class="oc-chip">{{ ROLE_LABELS.owner }}</span>
              <select
                v-else
                class="months-select"
                :value="m.role"
                :disabled="m.role === 'admin' && !info.can.manage_admins"
                @change="changeRole(m, $event.target.value)"
              >
                <option value="admin" :disabled="!info.can.manage_admins">Admin</option>
                <option value="manager">Manager</option>
                <option value="viewer">Viewer</option>
              </select>
            </td>
            <td>{{ m.user_id ? 'Joined' : 'Invited (not signed in yet)' }}</td>
            <td>
              <button v-if="m.role !== 'owner'" class="oc-btn danger" @click="remove(m)">Remove</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
