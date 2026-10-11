// What a visitor chose before signing up (industry, optional data sources, plan). It is kept in this browser for a
// few days so the first-time setup after sign-up can start from it. Presentational preferences only: nothing here is
// trusted by the server, which validates the industry again when it is saved.
const KEY = 'ri_onboarding'
const TTL_MS = 7 * 24 * 60 * 60 * 1000
const ID = /^[a-z][a-z_]{1,29}$/
export const PLANS = ['free', 'pro']

export function cleanOnboarding(input) {
  const industry = typeof input?.industry === 'string' && ID.test(input.industry) ? input.industry : null
  const sources = [...new Set((Array.isArray(input?.sources) ? input.sources : []).filter((s) => typeof s === 'string' && ID.test(s)))].slice(0, 12)
  const plan = PLANS.includes(input?.plan) ? input.plan : 'free'
  return { industry, sources, plan }
}

export function saveOnboarding(input, storage = globalThis.localStorage, now = Date.now()) {
  try { storage.setItem(KEY, JSON.stringify({ ...cleanOnboarding(input), savedAt: now })) } catch { /* storage can be unavailable */ }
}

export function recallOnboarding(storage = globalThis.localStorage, now = Date.now()) {
  try {
    const saved = JSON.parse(storage.getItem(KEY) ?? 'null')
    if (!saved || typeof saved.savedAt !== 'number' || now - saved.savedAt > TTL_MS || saved.savedAt > now + 60_000) return null
    return cleanOnboarding(saved)
  } catch {
    return null
  }
}

export function clearOnboarding(storage = globalThis.localStorage) {
  try { storage.removeItem(KEY) } catch { /* ignore */ }
}

// An industry's source lists, with safe defaults for one that declares none.
export function integrationsFor(pack) {
  const i = pack?.integrations
  return {
    recommended: Array.isArray(i?.recommended) ? i.recommended : [],
    optional: Array.isArray(i?.optional) ? i.optional : [],
    hidden: Array.isArray(i?.hidden) ? i.hidden : [],
  }
}

// Splits platforms into those to show up front (the industry's recommended ones, plus any the person said they use)
// and the rest, which sit behind "show more". With no industry information everything is shown, as before.
export function splitPlatforms(platforms, pack, chosen = []) {
  const { recommended, optional, hidden } = integrationsFor(pack)
  if (!recommended.length && !optional.length && !hidden.length) return { primary: platforms, more: [] }
  // Sources the industry doesn't use (OpenTable for a clinic) are not offered at all.
  const offered = platforms.filter((p) => !hidden.includes(p.id))
  const upFront = new Set([...recommended, ...chosen.filter((id) => !hidden.includes(id))])
  return { primary: offered.filter((p) => upFront.has(p.id)), more: offered.filter((p) => !upFront.has(p.id)) }
}

export function platformNames(ids, platforms) {
  return ids.map((id) => platforms.find((p) => p.id === id)?.label).filter(Boolean)
}
