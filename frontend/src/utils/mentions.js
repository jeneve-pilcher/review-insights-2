// Default web-search words for a business: name + city, without the street address.
// (Mirrors the backend rule so the box can show what will be searched.)
export function defaultMentionTerms(query) {
  const parts = (query ?? '').split(',').map((p) => p.trim()).filter(Boolean)
  if (parts.length > 2) return `${parts[0]} ${parts[parts.length - 1]}`
  return parts.join(' ')
}

export function toneClass(sentiment) {
  if (typeof sentiment !== 'number') return ''
  if (sentiment >= 0.25) return 'mn-good'
  return sentiment <= -0.25 ? 'mn-bad' : 'mn-ok'
}

export function toneLabel(sentiment) {
  if (typeof sentiment !== 'number') return ''
  if (sentiment >= 0.25) return 'positive'
  return sentiment <= -0.25 ? 'negative' : 'neutral'
}

export const CATEGORY_LABELS = {
  reddit: 'Reddit',
  social: 'Social media',
  review_site: 'Other review/listing sites',
  news_blog: 'News & blogs',
  web: 'Other web',
}
