import { PALETTE, SUB_COLORS, weekLabel } from './industry'

// Helpers for the industry numbers and graphs on the company pages and the dashboard.

// ---- headline numbers
export function kpiValueText(k) {
  if (k.value == null) return '–'
  return k.unit === 'pct' ? `${Math.round(k.value * 100)}%` : k.value.toFixed(1)
}

// "+2.1 pts" for a share, "+0.3" for a score; empty when there is nothing to compare.
export function kpiChangeText(k) {
  if (k.change == null) return ''
  const v = k.unit === 'pct' ? k.change * 100 : k.change
  if (Math.abs(v) < (k.unit === 'pct' ? 0.5 : 0.05)) return 'steady'
  return `${v > 0 ? '+' : ''}${v.toFixed(1)}${k.unit === 'pct' ? ' pts' : ''}`
}

// Scores have a clear direction (higher is better). A theme's share doesn't: mentioning "service" can be praise or a
// complaint, so shares are shown without a good/bad color.
export function kpiTone(k) {
  if (k.unit !== 'score' || k.change == null) return 'info'
  return k.change >= 0.2 ? 'good' : k.change <= -0.2 ? 'warn' : 'info'
}

// The same headline numbers for a single location (the dashboard), from its own trends and OpenTable scores.
export function singleKpis(pack, trends, sub) {
  return (pack?.kpis ?? []).map((spec) => {
    let value = null
    let change = null
    if (spec.kind === 'theme' && trends?.status === 'ok') {
      const t = trends.themes.find((x) => x.id === spec.key)
      value = t ? t.share : null
      change = t ? t.change : null
    } else if (spec.kind === 'sub' && sub?.status === 'ok') {
      const s = sub.series.find((x) => x.key === spec.key)
      value = s ? s.average : null
      change = s ? s.change : null
    }
    return { id: spec.id, label: spec.label, kind: spec.kind, unit: spec.kind === 'theme' ? 'pct' : 'score', value, change }
  }).filter((k) => k.value != null)
}

// ---- charts
export function companyTrendData(trend) {
  if (!trend || !trend.dates?.length) return { labels: [], datasets: [] }
  return {
    labels: trend.dates.map(weekLabel),
    datasets: trend.series.map((s, i) => ({
      label: s.label, data: s.values.map((v) => (v == null ? null : Math.round(v * 100))),
      borderColor: PALETTE[i % PALETTE.length], backgroundColor: PALETTE[i % PALETTE.length],
      spanGaps: true, tension: 0.25, pointRadius: 2, borderWidth: 2,
    })),
  }
}

const SUB_LABELS = { food: 'Food', service: 'Service', ambience: 'Ambience', value: 'Value' }

export function subByLocationData(sub) {
  if (!sub) return { labels: [], datasets: [] }
  return {
    labels: sub.rows.map((r) => r.name),
    datasets: sub.keys.map((k) => ({ label: SUB_LABELS[k] ?? k, data: sub.rows.map((r) => r.scores[k]), backgroundColor: SUB_COLORS[k] })),
  }
}

// The company's most-mentioned theme, location by location.
export function themeByLocationData(roll) {
  const top = roll?.rankings?.[0]
  if (!top || !roll.theme_grid) return { label: '', labels: [], datasets: [] }
  const rows = roll.theme_grid.rows.filter((r) => r.shares[top.theme] != null)
  return {
    label: top.label,
    labels: rows.map((r) => r.name),
    datasets: [{ label: `Share of written reviews mentioning ${top.label.toLowerCase()}`, data: rows.map((r) => Math.round(r.shares[top.theme] * 100)), backgroundColor: PALETTE[0] }],
  }
}

// ---- the theme x location grid: darker = more of that location's reviews mention the theme
export function cellStyle(share) {
  if (share == null) return { background: '#f5f5f5', color: '#aaa' }
  const alpha = Math.min(0.75, Math.max(0.04, share * 1.6))
  return { background: `rgba(231, 76, 60, ${alpha.toFixed(2)})`, color: alpha > 0.45 ? '#fff' : '#222' }
}

export function cellText(share) {
  return share == null ? '–' : `${Math.round(share * 100)}%`
}

export function flagMark(flag) {
  return flag === 'rising' ? ' ↑' : flag === 'falling' ? ' ↓' : ''
}

// ---- messages instead of an empty screen
export function industryNote(roll) {
  if (!roll) return ''
  if (roll.status === 'ok') {
    return roll.stale_locations ? `${roll.stale_locations} location${roll.stale_locations === 1 ? ' was' : 's were'} last checked under a different industry and will be included after the next check.` : ''
  }
  if (roll.stale_locations) return `Your locations were last checked under a different industry. Their industry numbers appear after the next check (or press Run now on a location).`
  if (roll.locations_total === 0) return 'Add locations to see industry numbers here.'
  return 'Industry numbers appear after a location has been checked with enough written reviews (at least 6). Press Run now on a location to check it.'
}

export function trendNote(trend) {
  return trend && trend.dates?.length ? '' : 'The trend line appears after your locations have been checked in at least two different weeks.'
}

// ---- tasks tagged with the industry's themes
export function themeCounts(alerts, pack) {
  const labels = Object.fromEntries((pack?.themes ?? []).map((t) => [t.id, t.label]))
  const counts = {}
  for (const a of alerts ?? []) for (const id of a.themes ?? []) if (labels[id]) counts[id] = (counts[id] ?? 0) + 1
  return Object.entries(counts).map(([id, count]) => ({ id, label: labels[id], count })).sort((a, b) => b.count - a.count || a.label.localeCompare(b.label))
}

export function filterByTheme(alerts, themeId) {
  return themeId ? (alerts ?? []).filter((a) => (a.themes ?? []).includes(themeId)) : alerts ?? []
}
