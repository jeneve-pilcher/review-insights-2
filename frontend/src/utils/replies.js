// Helpers for the reviews list and reply workflow (pure functions, no Vue).

export const FILTERS = [
  { id: 'all', label: 'All' },
  { id: 'needs_reply', label: 'Needs a reply' },
  { id: 'low', label: '1–2★' },
  { id: 'mid', label: '3★' },
  { id: 'high', label: '4–5★' },
  { id: 'replied', label: 'Replied' },
]

export function isReplied(replies, key) {
  return replies?.[key]?.status === 'sent'
}

export function filterReviews(items, { filter = 'all', source = 'all', replies = {} } = {}) {
  return (items ?? []).filter((r) => {
    if (source !== 'all' && r.source !== source) return false
    switch (filter) {
      case 'needs_reply': return !isReplied(replies, r.key)
      case 'replied': return isReplied(replies, r.key)
      case 'low': return r.rating <= 2
      case 'mid': return r.rating === 3
      case 'high': return r.rating >= 4
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
export function reviewPageUrl(item, { businessLocation, yelpUrl } = {}) {
  if (item.source === 'yelp') return yelpUrl || null
  if (!businessLocation) return null
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(businessLocation)}`
}

export function platformLabel(source) {
  return source === 'yelp' ? 'Yelp' : 'Google'
}

export function wordCount(text) {
  const t = (text ?? '').trim()
  return t ? t.split(/\s+/).length : 0
}

export function replyStatusLabel(reply) {
  if (!reply) return ''
  return reply.status === 'sent' ? 'Replied' : 'Draft saved'
}
