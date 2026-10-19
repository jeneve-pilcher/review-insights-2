// Helpers for the reviews list and reply workflow (pure functions, no Vue).

export const FILTERS = [
  { id: 'all', label: 'All' },
  { id: 'low', label: 'Bad reviews (1–2★)' },
  { id: 'high', label: 'Good reviews (4–5★)' },
  { id: 'mid', label: 'Okay (3★)' },
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

export function filterReviews(items, { filter = 'all', source = 'all', replies = {} } = {}) {
  return (items ?? []).filter((r) => {
    if (source !== 'all' && r.source !== source) return false
    switch (filter) {
      case 'needs_reply': return !isUnrated(r) && !isReplied(replies, r.key)
      case 'replied': return !isUnrated(r) && isReplied(replies, r.key)
      case 'low': return r.rating != null && r.rating <= 2
      case 'mid': return r.rating === 3
      case 'high': return r.rating != null && r.rating >= 4
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
