// The review pages an account can connect, in the order they're shown. One list, used by first-time
// setup and by the "Your pages" form, so the wording and examples never drift apart.
export const PLATFORMS = [
  { id: 'yelp', column: 'yelp_url', label: 'Yelp', placeholder: 'https://www.yelp.com/biz/your-business-city', help: 'Reviews with star ratings.' },
  { id: 'opentable', column: 'opentable_url', label: 'OpenTable', placeholder: 'https://www.opentable.com/r/your-restaurant-city', help: 'Reviews from diners who booked and dined.' },
  { id: 'doordash', column: 'doordash_url', label: 'DoorDash', placeholder: 'https://www.doordash.com/store/your-restaurant-city-123456/', help: 'Customer reviews with star ratings.' },
  { id: 'ubereats', column: 'ubereats_url', label: 'Uber Eats', placeholder: 'https://www.ubereats.com/store/your-restaurant/abc123', help: 'No star ratings, so these are read for tone but never counted in your ratings.' },
  { id: 'grubhub', column: 'grubhub_url', label: 'Grubhub', placeholder: 'https://www.grubhub.com/restaurant/your-restaurant/123456/', help: 'Customer reviews with star ratings. Uses a community-built scraper, so it needs the most attention.' },
]

export const COLUMNS = PLATFORMS.map((p) => p.column)

export function emptyLinks() {
  return Object.fromEntries(COLUMNS.map((c) => [c, '']))
}

// Only what's new: typed, non-blank, and not already saved (saved pages are set once).
export function collectLinks(form, current = {}) {
  const out = {}
  for (const column of COLUMNS) {
    const value = String(form?.[column] ?? '').trim()
    if (value && !current?.[column]) out[column] = value
  }
  return out
}

export function savedPlatforms(current) {
  return PLATFORMS.filter((p) => current?.[p.column])
}

export function missingPlatforms(current) {
  return PLATFORMS.filter((p) => !current?.[p.column])
}
