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

// ---- Add many people from a spreadsheet (CSV)
const csv = ref('')
const sendInvites = ref(true)
const importing = ref(false)
const importResult = ref(null)

function onFile(event) {
  const file = event.target.files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => { csv.value = String(reader.result || '') }
  reader.readAsText(file)
}

async function importPeople() {
  importing.value = true
  importResult.value = null
  try {
    importResult.value = await orgApi.importMembers(csv.value, sendInvites.value)
    if (importResult.value.added) {
      csv.value = ''
      emit('changed')
    }
  } catch (err) {
    importResult.value = { added: 0, skipped: [], invite_problems: [], error: err?.response?.data?.detail || 'The import failed.' }
  } finally {
    importing.value = false
  }
}

async function add() {
  if (!email.value.trim()) return
  busy.value = true
  message.value = ''
  try {
    await orgApi.addMember(email.value.trim(), role.value)
    message.value = `Added ${email.value.trim()}. Ask them to sign up or log in with that email and they'll be connected automatically. No email is sent. To invite many people at once with an emailed link, use the spreadsheet import below.`
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
    <details class="oc-card" style="margin-bottom: 16px">
      <summary><strong>Add many people from a spreadsheet (CSV)</strong></summary>
      <p class="oc-note">
        The first row must be headers: <code>email</code> and, optionally, <code>role</code> (admin, manager or viewer; blank means viewer).
        Export your spreadsheet as CSV, then choose the file or paste it below (up to 200 people at a time).
      </p>
      <input type="file" accept=".csv,text/csv" @change="onFile" />
      <textarea v-model="csv" rows="5" style="width: 100%; margin-top: 8px" placeholder="email,role&#10;ann@company.com,manager&#10;bob@company.com,viewer"></textarea>
      <label style="display: block; margin: 6px 0">
        <input v-model="sendInvites" type="checkbox" /> Also email each person an invitation to choose a password
      </label>
      <p v-if="info.org.sso_domain" class="oc-note">
        People with an <strong>@{{ info.org.sso_domain }}</strong> address use your company's single sign-on, so they are added without an
        invitation email. They log in with "Continue with company SSO" and are connected to this team automatically.
      </p>
      <button class="oc-btn" :disabled="importing || !csv.trim()" @click="importPeople">Add everyone</button>
      <template v-if="importResult">
        <p v-if="importResult.error" class="status error">{{ importResult.error }}</p>
        <p v-else class="status analysis-note">
          Added {{ importResult.added }}{{ sendInvites ? `; invitations sent to ${importResult.invites_sent}` : '' }}{{ importResult.sso_people?.length ? `; ${importResult.sso_people.length} will sign in with SSO` : '' }}.
        </p>
        <ul v-if="importResult.skipped?.length" class="oc-note">
          <li v-for="s in importResult.skipped" :key="s.row">Row {{ s.row }} skipped: {{ s.reason }}</li>
        </ul>
        <ul v-if="importResult.invite_problems?.length" class="oc-note">
          <li v-for="p in importResult.invite_problems" :key="p.email">{{ p.email }}: no invitation sent ({{ p.reason }}). They were still added to the team.</li>
        </ul>
      </template>
    </details>
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
