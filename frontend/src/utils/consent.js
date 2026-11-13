// Cookie consent. The visitor's choice ('accepted' or 'rejected') is remembered for a year, in localStorage with a
// small first-party cookie as a backup. Until they accept, no analytics, pixel or other third-party script is added.
import { TRACKERS } from '../content/trackers'

export const CONSENT_KEY = 'ri_cookie_consent'
export const OPEN_EVENT = 'ri-open-cookie-settings'
const YEAR_MS = 365 * 24 * 60 * 60 * 1000

// Only these IDs are ever put into a script address or code: letters, digits, dash and underscore.
const SAFE_ID = /^[A-Za-z0-9_-]{4,40}$/

function readCookie() {
  try {
    const m = document.cookie.split('; ').find((c) => c.startsWith(CONSENT_KEY + '='))
    return m ? decodeURIComponent(m.slice(CONSENT_KEY.length + 1)) : null
  } catch { return null }
}

function parse(raw) {
  try {
    const v = JSON.parse(raw)
    if ((v.choice === 'accepted' || v.choice === 'rejected') && Date.now() - Number(v.at) < YEAR_MS) return v.choice
  } catch { /* not a saved choice */ }
  return null
}

// 'accepted', 'rejected', or null (never asked, or the choice is more than a year old).
export function getConsent() {
  let raw = null
  try { raw = localStorage.getItem(CONSENT_KEY) } catch { /* storage blocked */ }
  return parse(raw) || parse(readCookie())
}

function save(choice) {
  const raw = JSON.stringify({ choice, at: Date.now() })
  try { localStorage.setItem(CONSENT_KEY, raw) } catch { /* the cookie below still remembers it */ }
  try {
    document.cookie = `${CONSENT_KEY}=${encodeURIComponent(raw)}; max-age=${Math.floor(YEAR_MS / 1000)}; path=/; SameSite=Lax${location.protocol === 'https:' ? '; Secure' : ''}`
  } catch { /* ignore */ }
}

let loaded = false

function addScript(src) {
  const s = document.createElement('script')
  s.async = true
  s.src = src
  document.head.appendChild(s)
}

// Adds the optional scripts, and only if the visitor has accepted. Safe to call any number of times.
export function loadTrackers() {
  if (loaded || getConsent() !== 'accepted') return false
  loaded = true
  const ga = TRACKERS.googleAnalyticsId
  if (SAFE_ID.test(ga)) {
    window.dataLayer = window.dataLayer || []
    window.gtag = function gtag() { window.dataLayer.push(arguments) }  // eslint-disable-line prefer-rest-params
    window.gtag('js', new Date())
    window.gtag('config', ga, { anonymize_ip: true })
    addScript(`https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(ga)}`)
  }
  const px = TRACKERS.metaPixelId
  if (SAFE_ID.test(px)) {
    // The standard Meta Pixel loader, written out so it only runs after consent.
    if (!window.fbq) {
      const q = []
      const fbq = function fbq() { fbq.callMethod ? fbq.callMethod.apply(fbq, arguments) : fbq.queue.push(arguments) }  // eslint-disable-line prefer-rest-params
      fbq.push = fbq; fbq.loaded = true; fbq.version = '2.0'; fbq.queue = q
      window.fbq = window._fbq = fbq
      addScript('https://connect.facebook.net/en_US/fbevents.js')
    }
    window.fbq('init', px)
    window.fbq('track', 'PageView')
  }
  return true
}

export function accept() {
  save('accepted')
  loadTrackers()
}

// Rejecting never loads anything. If the visitor had accepted before, the scripts already on this page are removed by
// reloading it, and the cookies those services set on this site are deleted.
export function reject() {
  const wasAccepted = getConsent() === 'accepted'
  save('rejected')
  if (!wasAccepted && !loaded) return
  try {
    const host = location.hostname
    const parts = host.split('.')
    const domains = ['', host, '.' + host, parts.length > 2 ? '.' + parts.slice(-2).join('.') : '']
    for (const c of document.cookie.split('; ')) {
      const name = c.split('=')[0]
      if (/^(_ga|_gid|_gat|_fbp|_fbc)/.test(name)) {
        for (const d of domains) document.cookie = `${name}=; max-age=0; path=/${d ? '; domain=' + d : ''}`
      }
    }
  } catch { /* ignore */ }
  location.reload()
}

// "Cookie settings" links call this to show the banner again.
export function openCookieSettings() {
  window.dispatchEvent(new Event(OPEN_EVENT))
}
