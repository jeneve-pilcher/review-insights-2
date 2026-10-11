// Which statistics the strip shows: the owner's own file if there is one, otherwise the defaults. Only complete
// entries (a value and a label) are ever shown.
export function pickStats(ownModule, defaults) {
  const own = ownModule && Array.isArray(ownModule.stats) ? ownModule.stats : null
  const chosen = own ?? defaults ?? []
  return chosen.filter((s) => s && typeof s.value === 'string' && s.value.trim() && typeof s.label === 'string' && s.label.trim())
}

// A stat's source can link to its page. Only plain https links are ever used.
export function safeUrl(url) {
  return typeof url === 'string' && /^https:\/\/[^\s"'<>]+$/i.test(url) ? url : null
}
