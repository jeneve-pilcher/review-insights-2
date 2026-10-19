// "Where revenue may be slipping away": the patterns Review Insights looks for, each described by what it really does.
// There are deliberately NO promised numbers here. The app reads reviews, not sales, so its dollar figures are estimates.
export const REVENUE_ITEMS = [
  {
    id: 'waits',
    icon: '⏱️',
    tone: 'tangerine',
    title: 'Waits at particular hours',
    look: 'Days and hours when good reviews drop and waiting is mentioned.',
    see: 'A day-by-hour heatmap with an estimated dollar figure per slot.',
    plan: 'Pro',
  },
  {
    id: 'themes',
    icon: '🔁',
    tone: 'coral',
    title: 'A complaint that keeps coming back',
    look: 'How often each theme in your industry comes up, week by week.',
    see: 'Themes flagged when they rise or fall, beside the weekly numbers.',
    plan: 'Pro',
  },
  {
    id: 'drift',
    icon: '📉',
    tone: 'amber',
    title: 'A rating that is quietly drifting',
    look: 'Weekly volume and tone, not just the star average.',
    see: 'Early-warning flags before the star rating itself moves.',
    plan: 'Included in Free',
  },
  {
    id: 'followup',
    icon: '✅',
    tone: 'apricot',
    title: 'Negative reviews nobody followed up on',
    look: '1\u20132\u2605 reviews, tagged by topic.',
    see: 'Draft replies to reviews (not healthcare), and filter good and bad reviews.',
    plan: 'Pro',
  },
  {
    id: 'platforms',
    icon: '🔀',
    tone: 'brand',
    title: 'One platform telling a different story',
    look: 'Ratings and tone on each platform you connect.',
    see: 'A side-by-side comparison, including delivery apps.',
    plan: 'Pro',
  },
]

export const REVENUE_NOTE =
  'Dollar figures are estimates from review patterns and assumptions like your average order value. We read reviews, not your sales, so use them to decide what to look at first.'
