// Default web-search words for a business: name + city, without the street address.
// (Mirrors the backend rule so the box can show what will be searched.)
export function defaultMentionTerms(query) {
  const q = (query ?? '').trim()
  if (/^https?:\/\//i.test(q)) {
    // A Google Maps link: the business name is in the link. No readable name means nothing to search for.
    const m = q.match(/\/maps\/place\/([^/@?]+)/)
    if (!m) return ''
    try { return decodeURIComponent(m[1].replace(/\+/g, ' ')).trim() } catch { return m[1].replace(/\+/g, ' ') }
  }
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
  delivery: 'Delivery app',
}

// ---- Search depth and its (approximate) cost -------------------------------------------------
// One pull = 2 searches (open web + Reddit) per page of depth; each page is about 10 results.
// Outscraper's published rate is roughly half a cent per search after a small free allowance;
// check your own plan, this is only an estimate.
export const SEARCH_PRICE_USD = 0.005
export const SEARCHES_PER_PAGE = 2
export const MAX_PAGES = 5

export function clampPages(value) {
  if (value === null || value === undefined || value === '') return 2 // not provided: use the default depth
  const n = Math.round(Number(value))
  if (!Number.isFinite(n)) return 2
  return Math.max(1, Math.min(MAX_PAGES, n))
}

export function estimateSearches(pages) {
  return SEARCHES_PER_PAGE * clampPages(pages)
}

export function estimateCostUsd(pages) {
  return Math.round(estimateSearches(pages) * SEARCH_PRICE_USD * 1000) / 1000
}

export function formatCost(usd) {
  return `$${usd.toFixed(3)}`
}
