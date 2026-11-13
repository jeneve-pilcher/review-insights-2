// Remembers a person's competitor rows in this browser until they delete them, so logging out and in
// again (or closing the tab) does not lose them. Stored per account, so another person using the same
// computer never sees them. Nothing is sent anywhere: it is a plain note kept in this browser.
const PREFIX = 'ri_competitors_'
const MAX_ROWS = 5

const keyFor = (userId) => `${PREFIX}${String(userId || '').slice(0, 64)}`

function clean(rows) {
  return (Array.isArray(rows) ? rows : [])
    .slice(0, MAX_ROWS)
    .map((r) => ({
      name: String(r?.name ?? '').slice(0, 160),
      search_query: String(r?.search_query ?? "").slice(0, 2000),
    }))
}

export function loadCompetitors(userId, storage = globalThis.localStorage) {
  if (!userId) return []
  try {
    return clean(JSON.parse(storage.getItem(keyFor(userId)) || '[]'))
  } catch {
    return []
  }
}

export function saveCompetitors(userId, rows, storage = globalThis.localStorage) {
  if (!userId) return
  try {
    const cleaned = clean(rows)
    if (cleaned.length) storage.setItem(keyFor(userId), JSON.stringify(cleaned))
    else storage.removeItem(keyFor(userId)) // removing every row forgets the list
  } catch { /* private window or storage full: the list just isn't remembered */ }
}

export function forgetCompetitors(userId, storage = globalThis.localStorage) {
  if (!userId) return
  try { storage.removeItem(keyFor(userId)) } catch { /* nothing to do */ }
}
