import { selectable } from '../content/industries'
import { PLANS, splitPlatforms } from './onboarding'

// The sign-up flow on the front page: pick an industry, optionally say which data sources you use, choose a plan,
// then go on to the sign-up page. Plain functions so the rules can be tested.

// A link like /?industry=dental&plan=pro preselects things. Anything invalid is ignored.
export function readQuery(query) {
  const industry = typeof query?.industry === 'string' && selectable(query.industry) ? query.industry : null
  const plan = PLANS.includes(query?.plan) ? query.plan : null
  return { industry, plan }
}

export function canContinue(industryId) {
  return selectable(industryId)
}

// Where "Continue" goes. The plan travels in the URL as before; the industry and sources are kept in the browser.
export function signupTarget(plan) {
  return { path: '/signup', query: { plan: PLANS.includes(plan) ? plan : 'free' } }
}

// The sources to offer for the chosen industry: its recommended ones up front, the rest behind "show more".
export function sourcesFor(industry, platforms, chosen = []) {
  if (!industry?.available) return { primary: [], more: [] }
  return splitPlatforms(platforms, industry, chosen)
}

export function planLabel(plan) {
  return plan === 'pro' ? 'Pro' : 'Free'
}
