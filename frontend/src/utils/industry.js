// Helpers for the industry panel: chart data and plain-English text from the server's industry result.
export const PALETTE = ['#7c5ce0', '#2ecc71', '#e67e22', '#3498db', '#e74c3c', '#f1c40f', '#1abc9c', '#95a5a6']
export const SUB_COLORS = { food: '#e67e22', service: '#3498db', ambience: '#7c5ce0', value: '#2ecc71' }
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

export function weekLabel(iso) {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso ?? '')
  return m ? `${MONTHS[Number(m[2]) - 1]} ${Number(m[3])}` : String(iso ?? '')
}

export function pct(v) {
  return v == null ? '–' : `${Math.round(v * 100)}%`
}

// Industries grouped for a <select>, in the order the server lists them.
export function groupIndustries(list) {
  const groups = []
  for (const item of list ?? []) {
    let g = groups.find((x) => x.name === item.group)
    if (!g) groups.push((g = { name: item.group, items: [] }))
    g.items.push(item)
  }
  return groups
}

// Which themes start selected: flagged ones first (the server already sorts them), only those actually mentioned.
export function defaultSelection(trends, n = 4) {
  return (trends?.themes ?? []).filter((t) => t.mentions > 0).slice(0, n).map((t) => t.id)
}

export function chartSeries(trends, selectedIds) {
  if (!trends || trends.status !== 'ok') return { labels: [], datasets: [] }
  const picked = trends.themes.filter((t) => selectedIds.includes(t.id))
  return {
    labels: trends.weeks.map(weekLabel),
    datasets: picked.map((t) => {
      const color = PALETTE[trends.themes.indexOf(t) % PALETTE.length]
      return {
        label: t.label, data: t.series.map((v) => (v == null ? null : Math.round(v * 100))),
        borderColor: color, backgroundColor: color, spanGaps: true, tension: 0.25, pointRadius: 2, borderWidth: 2,
      }
    }),
  }
}

export function subSeries(sub) {
  if (!sub || sub.status !== 'ok') return { labels: [], datasets: [] }
  return {
    labels: sub.weeks.map(weekLabel),
    datasets: sub.series.map((s) => ({
      label: s.label, data: s.weekly, borderColor: SUB_COLORS[s.key], backgroundColor: SUB_COLORS[s.key],
      spanGaps: true, tension: 0.25, pointRadius: 2, borderWidth: 2,
    })),
  }
}

export function toneClass(tone) {
  return { 'watch this': 'warn', 'good news': 'good', 'worth a look': 'info' }[tone] ?? 'info'
}

export function compareText(theme) {
  if (theme.recent_share == null || theme.earlier_share == null) return 'not enough history'
  return `${pct(theme.recent_share)} lately vs ${pct(theme.earlier_share)} before`
}

export function ratingText(theme) {
  if (theme.rating_with == null || theme.rating_without == null) return '–'
  return `${theme.rating_with}★ vs ${theme.rating_without}★`
}

// What to say instead of a graph when there isn't enough data.
export function trendsMessage(trends) {
  if (!trends) return ''
  if (trends.status === 'too_few') return `Industry trends need at least ${trends.minimum} written reviews in the window; this one has ${trends.reviews}. Try a longer window.`
  if (trends.status === 'ok' && !trends.weeks.length) return 'These reviews have no dates, so only overall totals can be shown, not trends over time.'
  return ''
}

export function subratingsMessage(sub) {
  if (!sub) return ''
  if (sub.status === 'no_data') return 'Connect your OpenTable page to see food, service, ambience and value scores over time.'
  if (sub.status === 'too_few') return `Sub-ratings need at least ${sub.minimum} OpenTable reviews; there are ${sub.n} so far.`
  return ''
}
