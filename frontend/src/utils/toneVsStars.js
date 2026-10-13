// Tone versus star rating, one dot per WEEK, with a fitted straight line (weighted least squares).
// Each week is weighted by how many written reviews it had, so a week with one comment counts for less than a week with twenty.
// x = the week's average star rating (every review that week); y = the week's average tone of the written reviews (-1 to 1).
export const MIN_WEEKS = 6
export const FAR_BELOW = -0.2

export function toneStarFit(weekly) {
  const points = (weekly ?? [])
    .filter((w) => w && w.avg_sentiment != null && w.rolling_avg_rating != null && w.text_reviews > 0)
    .map((w) => ({ week: w.week_start, stars: w.rolling_avg_rating, tone: w.avg_sentiment, n: w.text_reviews, reviews: w.total_reviews }))
  if (points.length < MIN_WEEKS) return { status: 'too_few', points, weeks: points.length }

  const sw = points.reduce((a, p) => a + p.n, 0)
  const xbar = points.reduce((a, p) => a + p.n * p.stars, 0) / sw
  const ybar = points.reduce((a, p) => a + p.n * p.tone, 0) / sw
  const sxx = points.reduce((a, p) => a + p.n * (p.stars - xbar) ** 2, 0)
  const syy = points.reduce((a, p) => a + p.n * (p.tone - ybar) ** 2, 0)
  const sxy = points.reduce((a, p) => a + p.n * (p.stars - xbar) * (p.tone - ybar), 0)
  // No spread in stars (or in tone) means there is nothing to fit.
  if (sxx < 1e-9 || syy < 1e-9) return { status: 'flat', points, weeks: points.length }

  const slope = sxy / sxx
  const intercept = ybar - slope * xbar
  const r = sxy / Math.sqrt(sxx * syy)
  const xs = points.map((p) => p.stars)
  const lo = Math.min(...xs)
  const hi = Math.max(...xs)
  const harsher = points
    .map((p) => ({ ...p, gap: p.tone - (intercept + slope * p.stars) }))
    .filter((p) => p.n >= 2 && p.gap <= FAR_BELOW)
    .sort((a, b) => a.gap - b.gap)
    .slice(0, 3)
  return {
    status: 'ok', points, weeks: points.length, slope, intercept, r,
    line: [{ x: lo, y: intercept + slope * lo }, { x: hi, y: intercept + slope * hi }],
    harsher,
  }
}

export function strengthWord(r) {
  const a = Math.abs(r)
  if (a < 0.2) return 'little'
  if (a < 0.5) return 'a moderate'
  return 'a strong'
}

// Plain-English reading. Says what the line shows, and that it is not proof of cause.
export function readFit(fit) {
  if (fit.status === 'too_few') return `Needs at least ${MIN_WEEKS} weeks that have written reviews. This has ${fit.weeks}.`
  if (fit.status === 'flat') return 'Every week has about the same star rating or the same tone, so there is no line to draw yet.'
  const word = strengthWord(fit.r)
  const link = word === 'little' ? 'little link' : `${word} link`
  const dir = fit.r >= 0 ? 'Weeks with higher stars also had warmer wording.' : 'Higher-star weeks had cooler wording, which is unusual.'
  const per = `Each extra star went with about ${Math.abs(fit.slope).toFixed(2)} ${fit.slope >= 0 ? 'more' : 'less'} on the tone scale.`
  return word === 'little'
    ? `Across ${fit.weeks} weeks there is little link between stars and wording (r = ${fit.r.toFixed(2)}), so one can move without the other.`
    : `Across ${fit.weeks} weeks there is ${link} between stars and wording (r = ${fit.r.toFixed(2)}). ${dir} ${per}`
}
