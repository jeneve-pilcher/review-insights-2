// Provider-level (individual doctor) data. It is only ever shown to people the server says may see it.
export function levelMessage(view) {
  if (!view || !view.enabled) return ''
  if (view.level === 'summary') return "You can see practice-level totals here. Individual doctors are visible to owners, admins and the location's manager."
  if (!view.providers.length) return view.links?.length ? 'Doctor pages are saved. Their numbers appear after the next check (or press Run now).' : 'No doctor pages have been added for this location yet. Add Zocdoc doctor links by editing the location.'
  return ''
}

export function scoreText(v) {
  return v == null ? '–' : Number(v).toFixed(1)
}

export function changeText(v) {
  if (v == null) return '–'
  if (Math.abs(v) < 0.05) return 'steady'
  return `${v > 0 ? '+' : ''}${v.toFixed(1)}`
}

export function changeTone(v) {
  return v == null ? 'info' : v <= -0.3 ? 'warn' : v >= 0.3 ? 'good' : 'info'
}

export function verifiedText(v) {
  return v == null ? '–' : `${Math.round(v)}%`
}

// Bedside manner and wait-time scores side by side for each doctor (both out of 5).
export function providerChart(providers) {
  const rows = (providers ?? []).filter((p) => p.bedside != null || p.wait != null)
  return {
    labels: rows.map((p) => p.name),
    datasets: [
      { label: 'Bedside manner', data: rows.map((p) => p.bedside), backgroundColor: '#3498db' },
      { label: 'Wait time', data: rows.map((p) => p.wait), backgroundColor: '#e67e22' },
    ],
  }
}

// "https://www.zocdoc.com/doctor/jane-doe-md-12345" lines <-> a list
export function linksFromText(text) {
  return String(text ?? '').split(/\r?\n/).map((l) => l.trim()).filter(Boolean)
}

export function linksToText(links) {
  return (links ?? []).join('\n')
}

export function checkedText(iso, now = Date.now()) {
  if (!iso) return 'not refreshed yet'
  const days = Math.floor((now - new Date(iso).getTime()) / 86_400_000)
  return days <= 0 ? 'refreshed today' : days === 1 ? 'refreshed yesterday' : `refreshed ${days} days ago`
}
