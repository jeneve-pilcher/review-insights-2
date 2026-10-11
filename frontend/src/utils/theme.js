import '../theme/theme.css'

// White-label theming: a company's colors become CSS variables for its people only.
export const DEFAULT_TITLE = 'Review Insights'
const VARS = { primary: '--brand', hover: '--brand-hover', soft: '--brand-soft', border: '--brand-border', accent: '--accent' }
const HEX = /^#[0-9a-f]{6}$/i
const STORE_KEY = 'ri_brand'

// Only valid six-digit hex colors are ever applied, so a bad value can't inject anything into the page.
export function cssVarsFor(palette) {
  const out = {}
  if (!palette || !HEX.test(palette.primary ?? '')) return out
  for (const [key, cssVar] of Object.entries(VARS)) if (HEX.test(palette[key] ?? '')) out[cssVar] = palette[key]
  return out
}

export function clearBranding(root = document.documentElement) {
  for (const cssVar of Object.values(VARS)) root.style.removeProperty(cssVar)
}

// Applies a company's branding, or restores the default look when there is none. Returns true if it applied.
export function applyBranding(branding, root = document.documentElement) {
  clearBranding(root)
  const vars = cssVarsFor(branding?.palette)
  for (const [cssVar, value] of Object.entries(vars)) root.style.setProperty(cssVar, value)
  return Object.keys(vars).length > 0
}

export function brandTitle(branding) {
  const name = typeof branding?.name === 'string' ? branding.name.trim() : ''
  return name || DEFAULT_TITLE
}

// Logos must be https links; anything else is ignored rather than loaded.
export function safeLogo(branding) {
  const url = branding?.logo_url
  return typeof url === 'string' && /^https:\/\/[^\s"'<>]+$/i.test(url) ? url : null
}

// Remembered only so the login page isn't unbranded for a moment on a return visit. Presentational data only.
export function rememberBrand(branding, storage = globalThis.localStorage) {
  try { storage.setItem(STORE_KEY, JSON.stringify(branding)) } catch { /* storage can be unavailable */ }
}

export function forgetBrand(storage = globalThis.localStorage) {
  try { storage.removeItem(STORE_KEY) } catch { /* ignore */ }
}

export function recallBrand(storage = globalThis.localStorage) {
  try {
    const saved = JSON.parse(storage.getItem(STORE_KEY) ?? 'null')
    return saved && Object.keys(cssVarsFor(saved.palette)).length ? saved : null
  } catch {
    return null
  }
}

// "anna@acme.com" -> "acme.com" (only once it looks like a real domain)
export function emailDomain(email) {
  const domain = String(email ?? '').trim().split('@')[1]?.toLowerCase() ?? ''
  return /^[a-z0-9-]+(\.[a-z0-9-]+)+$/.test(domain) ? domain : ''
}
