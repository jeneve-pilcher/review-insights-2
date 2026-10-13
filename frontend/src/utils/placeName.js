// What to show for a business on screen. A Google Maps link is long and unreadable, so show the place name in it
// ("Starbucks") instead, or "your business" when the link has no name. Text that isn't a link is shown as typed.
export function shortBusinessName(query) {
  const q = String(query ?? '').trim()
  if (!q) return 'your business'
  if (!/^https?:\/\//i.test(q)) return q
  const m = q.match(/\/maps\/place\/([^/@?]+)/)
  if (!m) return 'your business'
  let name = m[1].replace(/\+/g, ' ')
  try { name = decodeURIComponent(name) } catch { /* keep the raw text */ }
  return name.trim() || 'your business'
}
