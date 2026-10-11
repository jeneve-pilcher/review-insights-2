// Small pure helpers for the company console (no Vue), so they can be tested on their own.

export const ROLE_LABELS = {
  owner: 'Owner',
  admin: 'Admin',
  manager: 'Manager',
  viewer: 'Viewer',
}

const ACTION_LABELS = {
  org_create: 'Created the organization',
  member_add: 'Added a team member',
  member_role_change: 'Changed a role',
  member_remove: 'Removed a team member',
  location_add: 'Added a location',
  location_update: 'Edited a location',
  location_delete: 'Deleted a location',
  locations_import: 'Imported locations',
  run_manual: 'Refreshed a location',
  alert_update: 'Updated a task',
  budget_change: 'Changed the monthly spending limit',
  reply_sent: 'Marked a review reply as sent',
  credit_purchase: 'Bought company credit',
}

export function actionLabel(action) {
  return ACTION_LABELS[action] ?? action
}

export function signed(n, digits = 2) {
  if (typeof n !== 'number') return '–'
  return (n > 0 ? '+' : '') + n.toFixed(digits)
}

export function timeAgo(iso, now = new Date()) {
  if (!iso) return 'never'
  const then = new Date(iso)
  if (Number.isNaN(then.getTime())) return 'unknown'
  const seconds = Math.max(0, (now - then) / 1000)
  if (seconds < 60) return 'just now'
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
  return `${Math.floor(seconds / 86400)}d ago`
}

export function ratingClass(value) {
  if (typeof value !== 'number') return ''
  if (value >= 4.3) return 'oc-good'
  return value >= 3.8 ? 'oc-ok' : 'oc-bad'
}

export function percentileClass(p) {
  if (typeof p !== 'number') return ''
  if (p >= 67) return 'oc-good'
  return p >= 34 ? 'oc-ok' : 'oc-bad'
}

// How much of the monthly spending limit is used (0 when there is no limit).
export function usagePct(usage) {
  if (!usage || !usage.budget_usd) return 0
  return Math.min(100, Math.round((100 * usage.spent_usd) / usage.budget_usd))
}

function limitLabel(value) {
  return value == null ? 'no limit' : `$${Number(value).toFixed(2)}`
}

export function describeAudit(entry) {
  const d = entry.detail ?? {}
  switch (entry.action) {
    case 'locations_import':
      return `${d.added ?? 0} added, ${d.skipped ?? 0} skipped`
    case 'budget_change':
      return `${limitLabel(d.from)} → ${limitLabel(d.to)}`
    case 'member_add':
      return d.role ? `as ${d.role}` : ''
    case 'member_role_change':
      return `${d.from} → ${d.to}`
    case 'member_remove':
      return d.role ? `was ${d.role}` : ''
    case 'credit_purchase':
      return `${'$' + Number(d.price_usd ?? 0).toFixed(2)} bought ${'$' + Number(d.credit_usd ?? 0).toFixed(2)} of credit`
    case 'reply_sent':
      return `${d.source === 'yelp' ? 'Yelp' : 'Google'} ${d.rating ?? ''}★ review`.trim()
    case 'run_manual':
      return `${d.new_alerts ?? 0} new alert${d.new_alerts === 1 ? '' : 's'}, ${d.fresh_reviews ?? 0} reviews bought`
    case 'alert_update':
      return Object.entries(d)
        .map(([k, v]) => `${k.replace('_', ' ')}: ${v.from ?? '–'} → ${v.to ?? '–'}`)
        .join('; ')
    case 'location_update':
      return (d.fields ?? []).join(', ')
    default:
      return ''
  }
}

// Which tabs a person sees, given what the server says they can do.
export function visibleTabs(can) {
  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'locations', label: 'Locations' },
    { id: 'benchmarks', label: 'Benchmarks' },
    { id: 'tasks', label: 'Tasks' },
  ]
  if (can?.manage_members) tabs.push({ id: 'team', label: 'Team' })
  if (can?.view_audit) tabs.push({ id: 'activity', label: 'Activity' })
  return tabs
}

// Tiny CSV parser for the preview in the import box (the server does the real validation).
export function csvPreview(text, max = 3) {
  const lines = (text || '').trim().split(/\r?\n/).filter(Boolean)
  if (lines.length < 2) return { headers: [], rows: 0, sample: [] }
  const headers = lines[0].split(',').map((h) => h.trim())
  return { headers, rows: lines.length - 1, sample: lines.slice(1, 1 + max) }
}

// Points for a tiny inline chart (SVG polyline). Newest value is last.
export function sparkline(values, width = 240, height = 48, pad = 4) {
  const nums = (values ?? []).filter((v) => typeof v === 'number')
  if (nums.length < 2) return ''
  const min = Math.min(...nums)
  const max = Math.max(...nums)
  const span = max - min || 1
  return nums
    .map((v, i) => {
      const x = pad + (i * (width - 2 * pad)) / (nums.length - 1)
      const y = height - pad - ((v - min) * (height - 2 * pad)) / span
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')
}
