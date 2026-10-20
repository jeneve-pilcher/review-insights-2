// Helpers for the reviews list and reply workflow (pure functions, no Vue).

export const FILTERS = [
  { id: 'all', label: 'All' },
  { id: 'low', label: '1–2★' },
  { id: 'high', label: '3–5★' },
  { id: 'needs_reply', label: 'Needs a reply' },
  { id: 'replied', label: 'Replied' },
  { id: 'web', label: 'No stars (web, Uber Eats)' },
]

// Internet mentions: unrated written items from around the web. They can be read, never replied to here.
export function isWeb(item) {
  return item.source === 'web'
}

// Written items with no star rating: web mentions and Uber Eats. They can be read but never replied to here.
export function isUnrated(item) {
  return item.source === 'web' || item.source === 'ubereats' || item.rating === null
}

export function isReplied(replies, key) {
  return replies?.[key]?.status === 'sent'
}

// Does the review's text contain this word or phrase? (Not case sensitive. An empty search matches everything.)
export function matchesText(item, query) {
  const q = (query ?? '').trim().toLowerCase()
  if (!q) return true
  return String(item.text ?? '').toLowerCase().includes(q)
}

export function filterReviews(items, { filter = 'all', source = 'all', replies = {}, query = '' } = {}) {
  return (items ?? []).filter((r) => {
    if (source !== 'all' && r.source !== source) return false
    if (!matchesText(r, query)) return false
    switch (filter) {
      case 'needs_reply': return !isUnrated(r) && !isReplied(replies, r.key)
      case 'replied': return !isUnrated(r) && isReplied(replies, r.key)
      case 'low': return r.rating != null && r.rating <= 2
      case 'high': return r.rating != null && r.rating >= 3
      case 'web': return isUnrated(r)
      default: return true
    }
  })
}

export function countByFilter(items, replies = {}) {
  const out = {}
  for (const f of FILTERS) out[f.id] = filterReviews(items, { filter: f.id, replies }).length
  return out
}

// The words and phrases that come up most in these reviews, to filter by with one click. A word or two-word phrase counts once per
// review, and only those in at least `minReviews` reviews are offered. Plain counting: no model involved.
const STOP = new Set(('a about after again all also am an and any are as at be because been before being but by can could did do does '
  + 'doing down for from get got had has have he her here him his how i if in into is it its just me more most my no not of on one or our '
  + 'out over really she so some than that the their them then there these they this to too up us very was we were what when where which '
  + 'while who will with would you your were been place').split(' '))

export function topPhrases(items, { max = 12, minReviews = 2 } = {}) {
  const words = new Map()
  const pairs = new Map()
  for (const r of items ?? []) {
    const toks = String(r.text ?? '').toLowerCase().match(/[a-z']+/g) ?? []
    const seenW = new Set()
    const seenP = new Set()
    toks.forEach((w, i) => {
      if (w.length >= 4 && !STOP.has(w)) seenW.add(w)
      const nx = toks[i + 1]
      if (nx && w.length >= 3 && nx.length >= 3 && !STOP.has(w) && !STOP.has(nx)) seenP.add(`${w} ${nx}`)
    })
    seenW.forEach((w) => words.set(w, (words.get(w) ?? 0) + 1))
    seenP.forEach((p) => pairs.set(p, (pairs.get(p) ?? 0) + 1))
  }
  const pick = (m) => [...m.entries()].filter(([, n]) => n >= minReviews).sort((x, y) => y[1] - x[1] || x[0].localeCompare(y[0]))
  const out = pick(pairs).slice(0, Math.ceil(max / 2)).map(([text, count]) => ({ text, count }))
  const covered = new Set(out.flatMap((o) => o.text.split(' ')))
  for (const [text, count] of pick(words)) {
    if (out.length >= max) break
    if (!covered.has(text)) out.push({ text, count })
  }
  return out.sort((x, y) => y.count - x.count)
}

// Where a person goes to post the reply. Google has no direct review link here, so we open a
// Maps search for the business; Yelp uses the saved business page.
export function reviewPageUrl(item, { businessLocation, yelpUrl, opentableUrl, doordashUrl, grubhubUrl } = {}) {
  if (isUnrated(item)) return item.url || null
  if (item.source === 'yelp') return yelpUrl || null
  if (item.source === 'opentable') return opentableUrl || null
  if (item.source === 'doordash') return doordashUrl || null
  if (item.source === 'grubhub') return grubhubUrl || null
  if (!businessLocation) return null
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(businessLocation)}`
}

const PLATFORM_LABELS = { google: 'Google', yelp: 'Yelp', opentable: 'OpenTable', doordash: 'DoorDash', grubhub: 'Grubhub', ubereats: 'Uber Eats', web: 'Web' }

export function platformLabel(source) {
  return PLATFORM_LABELS[source] ?? 'Google'
}

export function wordCount(text) {
  const t = (text ?? '').trim()
  return t ? t.split(/\s+/).length : 0
}

export function replyStatusLabel(reply) {
  if (!reply) return ''
  return reply.status === 'sent' ? 'Replied' : 'Draft saved'
}
