// Per-location pricing, worked out from the table the server publishes (so the page and Stripe use the same numbers).
// Volume pricing: every location is charged the price of the tier the company's size falls in. Nobody pays more than a bigger
// company would: if the start of a bigger tier costs less in total, the company is billed as if it had that many locations.
// The standard table, shown if the server cannot be reached so the public page never goes blank. Keep it equal to the server's
// default in backend/corporate/pricing.py (the server's own table replaces it whenever it answers).
export const STANDARD_TIERS = [
  { from: 1, to: 249, price_per_location: 49 },
  { from: 250, to: 499, price_per_location: 39 },
  { from: 500, to: 999, price_per_location: 29 },
  { from: 1000, to: null, price_per_location: 19 },
]

export function rateFor(tiers, count) {
  let price = null
  for (const t of tiers ?? []) if (count >= t.from) price = t.price_per_location
  return price
}

export function billedLocations(tiers, count) {
  const n = Math.max(1, Math.floor(Number(count) || 0))
  let best = n
  let bestCost = n * (rateFor(tiers, n) ?? 0)
  for (const t of tiers ?? []) {
    if (t.from > n && t.from * t.price_per_location < bestCost) {
      best = t.from
      bestCost = t.from * t.price_per_location
    }
  }
  return best
}

export function monthlyTotal(tiers, count) {
  const b = billedLocations(tiers, count)
  return Math.round(b * (rateFor(tiers, b) ?? 0) * 100) / 100
}

export function averagePerLocation(tiers, count) {
  const n = Math.max(1, Math.floor(Number(count) || 0))
  return Math.round((monthlyTotal(tiers, n) / n) * 100) / 100
}

export function tierLabel(t) {
  if (t.to == null) return `${t.from}+ locations`
  return t.from === t.to ? `Location ${t.from}` : `Locations ${t.from} to ${t.to}`
}

export function usd(n) {
  return Number(n).toLocaleString('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: Number.isInteger(n) ? 0 : 2 })
}
