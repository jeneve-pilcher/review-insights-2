// Accounts that never chose an industry sit on the default (casual dining) without knowing. The dashboard asks them to
// choose, once, until they do. "Not now" hides the prompt for this browser session only.
const KEY = 'ri_industry_prompt_dismissed'

export function shouldPrompt(me, dismissed = false) {
  return Boolean(me && me.business_location && !me.industry_set && !dismissed)
}

export function dismissedThisSession(storage = globalThis.sessionStorage) {
  try { return storage.getItem(KEY) === '1' } catch { return false }
}

export function dismissForSession(storage = globalThis.sessionStorage) {
  try { storage.setItem(KEY, '1') } catch { /* storage can be unavailable */ }
}
