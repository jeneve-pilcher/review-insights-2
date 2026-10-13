// Can this device hover? Phones and tablets can't, so a tag that explains itself on hover needs a tap-to-explain
// fallback there. Without matchMedia (or on any error) we assume a mouse.
export function canHover(win = globalThis.window) {
  try {
    return typeof win?.matchMedia === 'function' ? Boolean(win.matchMedia('(hover: hover)').matches) : true
  } catch {
    return true
  }
}
