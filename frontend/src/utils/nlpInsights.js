// Turns the backend's raw language-analysis numbers into the plain-English
// sentences shown in each panel's "Language read" box. Pure functions, no Vue.
// Each item is { tone: 'info' | 'warn' | 'good', text: string }.

export function signed(n, digits = 2) {
  if (typeof n !== 'number') return '–'
  return (n > 0 ? '+' : '') + n.toFixed(digits)
}

export function sentimentLabel(score) {
  if (score >= 0.25) return 'positive'
  if (score <= -0.25) return 'negative'
  return 'mixed'
}

function plural(n, one, many) {
  return n === 1 ? one : many
}

function wordList(words, max = 3) {
  const list = (words ?? []).slice(0, max).map((w) => w.word ?? w.term ?? w)
  return list.length ? list.join(', ') : null
}

// ---- Review pace (uses every review, star-only included) -------------------
export function velocityReadItems(v) {
  if (!v) return []
  const items = []

  if (v.recent_per_week != null && v.earlier_per_week != null && v.earlier_per_week > 0) {
    const ratio = v.recent_per_week / v.earlier_per_week
    if (ratio <= 0.6) {
      items.push({
        tone: 'warn',
        text: `New reviews are slowing: about ${v.recent_per_week} per week lately vs ${v.earlier_per_week} before.`,
      })
    } else if (ratio >= 1.4) {
      items.push({
        tone: 'good',
        text: `Review pace is picking up: about ${v.recent_per_week} per week lately vs ${v.earlier_per_week} before.`,
      })
    } else {
      items.push({
        tone: 'info',
        text: `Review pace is steady at about ${v.recent_per_week} per week (${v.earlier_per_week} before).`,
      })
    }
  }

  if (v.days_since_last != null && v.days_since_last >= 30) {
    items.push({ tone: 'warn', text: `No new reviews in ${v.days_since_last} days.` })
  }
  return items
}

// ---- Sentiment Drift Matrix -------------------------------------------------
export function driftReadItems(result) {
  if (!result) return []
  const nlp = result.nlp
  const items = []

  if (nlp && nlp.reviews) {
    if (nlp.overall_sentiment != null) {
      items.push({
        tone: 'info',
        text: `Overall, your written reviews read ${sentimentLabel(nlp.overall_sentiment)} (${signed(nlp.overall_sentiment)} on a -1 to +1 scale).`,
      })
    }

    if (nlp.recent_sentiment != null && nlp.earlier_sentiment != null) {
      const delta = nlp.recent_sentiment - nlp.earlier_sentiment
      if (Math.abs(delta) >= 0.08) {
        items.push({
          tone: delta < 0 ? 'warn' : 'good',
          text: `In the last 4 weeks the tone is ${signed(nlp.recent_sentiment)} vs ${signed(nlp.earlier_sentiment)} before, so it is ${delta < 0 ? 'cooling ▼' : 'warming ▲'}.`,
        })
      } else {
        items.push({
          tone: 'info',
          text: `Tone has been steady: ${signed(nlp.recent_sentiment)} in the last 4 weeks vs ${signed(nlp.earlier_sentiment)} before.`,
        })
      }
    }

    if (nlp.drift_phrase_hits?.length) {
      const list = nlp.drift_phrase_hits.map((h) => `"${h.phrase}" ×${h.count}`).join(', ')
      items.push({ tone: 'warn', text: `Phrases that hint at decline showed up: ${list}.` })
    } else {
      items.push({ tone: 'good', text: 'No "used to be"-style decline phrases found in these reviews.' })
    }

    const words = wordList(nlp.top_words, 6)
    if (words) items.push({ tone: 'info', text: `Most-mentioned words: ${words}.` })
  }

  items.push(...velocityReadItems(result.velocity))
  return items
}

// ---- Weekly Themes & Sentiment ----------------------------------------------
function writtenCount(w) {
  return w.text_reviews ?? w.total_reviews
}

function weightedTone(rows) {
  const usable = rows.filter((w) => w.avg_sentiment != null)
  const total = usable.reduce((s, w) => s + writtenCount(w), 0)
  if (!total) return null
  return usable.reduce((s, w) => s + w.avg_sentiment * writtenCount(w), 0) / total
}

export function weeklyReadItems(weekly) {
  const solid = (weekly ?? []).filter((w) => w.avg_sentiment != null && writtenCount(w) >= 3)
  if (solid.length < 2) return []

  const worst = solid.reduce((a, b) => (b.avg_sentiment < a.avg_sentiment ? b : a))
  const best = solid.reduce((a, b) => (b.avg_sentiment > a.avg_sentiment ? b : a))
  if (worst.week_start === best.week_start) return []

  const items = [
    {
      tone: worst.avg_sentiment < 0 ? 'warn' : 'info',
      text: `Lowest-tone week: ${worst.week_start} (${signed(worst.avg_sentiment)}). People mentioned ${wordList(worst.top_words) ?? 'no standout words'}.`,
    },
    {
      tone: 'good',
      text: `Highest-tone week: ${best.week_start} (${signed(best.avg_sentiment)}). People mentioned ${wordList(best.top_words) ?? 'no standout words'}.`,
    },
  ]

  if (solid.length >= 6) {
    const last = weightedTone(solid.slice(-3))
    const before = weightedTone(solid.slice(-6, -3))
    if (last != null && before != null && Math.abs(last - before) >= 0.08) {
      items.push({
        tone: last < before ? 'warn' : 'good',
        text: `The last 3 weeks average ${signed(last)} vs ${signed(before)} in the 3 weeks before.`,
      })
    }
  }
  return items
}

// ---- Wait-Time Heatmap (also the free-tier teaser) --------------------------
export function heatmapReadItems(summary) {
  if (!summary || !summary.total_reviews) return []

  if (summary.mention_count === 0) {
    return [{ tone: 'good', text: 'No wait-time or slow-service language found in these reviews.' }]
  }

  const items = [
    {
      tone: summary.share_pct >= 10 ? 'warn' : 'info',
      text: `${summary.share_pct}% of written reviews (${summary.mention_count} of ${summary.total_reviews}) mention waiting or slow service.`,
    },
  ]
  if (summary.top_phrases?.length) {
    const list = summary.top_phrases.map((p) => `"${p.phrase}" ×${p.count}`).join(', ')
    items.push({ tone: 'info', text: `Most common phrases: ${list}.` })
  }
  if (summary.hotspot) {
    const h = summary.hotspot
    items.push({
      tone: 'warn',
      text: `Biggest hotspot: ${h.day}, ${h.hour} (${h.mentions} ${plural(h.mentions, 'mention', 'mentions')}).`,
    })
  }
  return items
}

// ---- Negative Review Alerts (also the free-tier teaser) ---------------------
export function negativeReadItems(summary) {
  if (!summary || !summary.total_reviews) return []

  if (summary.count === 0) {
    return [{ tone: 'good', text: 'No 1-2★ reviews in this window.' }]
  }

  const starOnly = summary.star_only_count ?? 0
  const extra = starOnly
    ? `, and ${starOnly} of them ${plural(starOnly, 'has', 'have')} no written comment`
    : ''
  const items = [
    {
      tone: summary.share_pct >= 15 ? 'warn' : 'info',
      text: `${summary.count} negative (1-2★) ${plural(summary.count, 'review', 'reviews')}: ${summary.share_pct}% of all reviews${extra}.`,
    },
  ]
  const terms = wordList(summary.top_terms, 5)
  if (terms) items.push({ tone: 'info', text: `Words most tied to the written negative reviews: ${terms}.` })
  return items
}

// ---- Competitor Semantic Share Matrix ---------------------------------------
function topTheme(themePct) {
  const entries = Object.entries(themePct ?? {})
  if (!entries.length) return [null, 0]
  return entries.reduce((a, b) => (b[1] > a[1] ? b : a))
}

export function competitorReadItems(result) {
  const businesses = result?.businesses ?? []
  if (businesses.length < 2) return []
  const items = []

  const own = businesses[0]
  if (own.tiers?.length) {
    const [theme, pct] = topTheme(own.tiers[0].theme_pct)
    if (theme && pct > 0) {
      items.push({ tone: 'info', text: `Your written ${own.tiers[0].tier}★ reviews lean most on "${theme}" (${pct}%).` })
    }
  }

  const gaps = []
  for (const c of businesses.slice(1)) {
    for (const row of (c.tiers ?? []).slice(1)) {
      const [theme, pct] = topTheme(row.theme_pct)
      if (theme && pct >= 25) gaps.push({ name: c.name, tier: row.tier, theme, pct })
    }
  }
  gaps.sort((a, b) => b.pct - a.pct)

  if (gaps.length) {
    for (const g of gaps.slice(0, 3)) {
      items.push({
        tone: 'good',
        text: `${g.name}'s written ${g.tier}★ reviews are ${g.pct}% about "${g.theme}": a gap you can target.`,
      })
    }
  } else {
    items.push({ tone: 'info', text: 'No competitor stands out with a dominant theme in its lower-rated reviews.' })
  }
  return items
}
