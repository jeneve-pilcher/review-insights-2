// Browser-side safety helpers. The server is the real gatekeeper (backend/sanitize.py); these keep the page itself safe.

// Only plain web links are ever put in an href. This refuses javascript:, data:, vbscript: and the like, and
// anything with spaces or quote/angle-bracket characters in it.
export function safeHttpUrl(url) {
  if (typeof url !== 'string') return ''
  const u = url.trim()
  return /^https?:\/\/[^\s"'<>]+$/i.test(u) ? u : ''
}

// Removes control and invisible characters and collapses whitespace (single-line text).
export function cleanLine(text) {
  return String(text ?? '')
    .replace(/[\u0000-\u001f\u007f-\u009f​-‏‪-‮⁠-⁤⁦-⁩﻿]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

// Longest values the forms accept (the server enforces the same limits).
export const LIMITS = { name: 160, query: 2000, url: 500, email: 254, label: 120, message: 4000 }
