// Helpers for showing usage credit: money formatting, run-cost estimates, and plain-English lines.

export function formatUsd(n) {
  if (typeof n !== 'number' || Number.isNaN(n)) return '–'
  const abs = Math.abs(n)
  const sign = n < 0 ? '-' : ''
  if (abs > 0 && abs < 0.01) return `${sign}$${abs.toFixed(3)}`
  return `${sign}$${abs.toFixed(2)}`
}

// Worst-case cost of a run, from the server's rate card and review caps. It's an upper bound:
// anything served from the 30-minute cache is free, and most pulls return fewer reviews than the cap.
export function estimateRun(opts, info) {
  if (!info?.rates || !info?.caps) return null
  const { sources = ['google'], mentions = false, mentionPages = 2, competitors = 0 } = opts
  const r = info.rates
  const c = info.caps
  const lines = []
  const add = (label, usd) => usd > 0 && lines.push({ label, usd })

  add('Google reviews', c.google * r.google_review)
  if (sources.includes('yelp')) add('Yelp reviews', c.yelp * r.yelp_review)
  if (sources.includes('opentable')) add('OpenTable reviews', c.opentable * r.opentable_review)
  if (sources.includes('doordash')) add('DoorDash reviews', c.doordash * r.doordash_review)
  if (sources.includes('ubereats')) add('Uber Eats reviews', c.ubereats * r.ubereats_review)
  if (sources.includes('grubhub')) add('Grubhub reviews', c.grubhub * r.grubhub_review)
  const runFees = ['doordash', 'ubereats'].filter((s) => sources.includes(s)).length
  if (runFees) add('Apify run fees', runFees * (r.apify_run_start ?? 0))
  if (competitors > 0) add(`Competitor reviews (${competitors})`, competitors * c.google * r.google_review)
  if (mentions) add('Web searches', c.searches_per_page * Math.max(1, Math.min(5, mentionPages)) * r.web_search)

  return { upper: lines.reduce((s, l) => s + l.usd, 0), lines }
}

// "This run used $0.15: all from your plan allowance."
export function billingLine(billing, { company = false } = {}) {
  if (!billing) return ''
  if (!billing.cost_usd) return 'Reused a recent pull: no charge.'
  const cost = formatUsd(billing.cost_usd)
  if (company) return `This run used ${cost} of the company's credit.`
  const fromAllowance = billing.from_allowance_usd ?? 0
  const fromCredit = billing.from_credit_usd ?? 0
  if (fromCredit <= 0) return `This run used ${cost}, all from your plan allowance.`
  if (fromAllowance <= 0) return `This run used ${cost} of your credit.`
  return `This run used ${cost}: ${formatUsd(fromAllowance)} from your plan allowance and ${formatUsd(fromCredit)} from credit.`
}

export function packLabel(pack) {
  return `${formatUsd(pack.price_usd)} → ${formatUsd(pack.credit_usd)} of credit`
}

// "$4.20 of $20.00 spent this month · $15.80 left", or "... · no limit set".
export function limitLine(info) {
  if (!info) return ''
  const spent = formatUsd(info.spent_this_month_usd ?? 0)
  if (!info.monthly_limit_usd) return `${spent} spent this month · no limit set`
  return `${spent} of ${formatUsd(info.monthly_limit_usd)} spent this month · ${formatUsd(info.limit_remaining_usd ?? 0)} left`
}

export function limitPct(info) {
  if (!info || !info.monthly_limit_usd) return 0
  return Math.min(100, Math.round((100 * (info.spent_this_month_usd ?? 0)) / info.monthly_limit_usd))
}

// A warning when a run could cost more than what's available, or would run into the monthly limit.
export function estimateWarning(estimate, info) {
  if (!estimate || !info || info.enforced === false) return ''
  if (info.limit_reached) {
    return `You've reached your monthly spending limit of ${formatUsd(info.monthly_limit_usd)}, so this run will be refused until next month or until you raise it.`
  }
  if (info.monthly_limit_usd && info.limit_remaining_usd < estimate.upper) {
    return `This run could use up to ${formatUsd(estimate.upper)} but only ${formatUsd(info.limit_remaining_usd)} is left under your monthly limit of ${formatUsd(info.monthly_limit_usd)}. It will still run, and may take you slightly over, but the next run will be refused.`
  }
  if (info.available_usd >= estimate.upper) return ''
  if (info.available_usd < 0.1) return 'You have almost no allowance or credit left, so this run will be refused until you add credit.'
  return `This run could use up to ${formatUsd(estimate.upper)} but only ${formatUsd(info.available_usd)} is available. It will still run, but may take you slightly below zero, and the next run will be blocked until you add credit.`
}

export function ledgerLabel(row) {
  if (row.kind === 'purchase') return `Bought credit ${'+' + formatUsd(row.amount_usd)}`
  if (row.kind === 'usage') {
    const parts = []
    if (row.allowance_usd > 0) parts.push(`${formatUsd(row.allowance_usd)} allowance`)
    if (row.amount_usd < 0) parts.push(`${formatUsd(-row.amount_usd)} credit`)
    return `Used ${formatUsd(row.cost_usd)}${parts.length ? ` (${parts.join(' + ')})` : ''}`
  }
  return `${row.kind} ${formatUsd(row.amount_usd)}`
}

export function allowancePct(info) {
  if (!info || !info.allowance_usd) return 0
  return Math.min(100, Math.round((100 * info.allowance_used_usd) / info.allowance_usd))
}
