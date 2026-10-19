// Review sites we do NOT pull from, shown per industry so nobody wonders why a platform has no link box.
// Two honest reasons, and the wording must stay accurate:
//   'terms'  : we read the site's own terms and they bar automated collection (or compiling its data).
//   'nosource': we have no approved way to get the data yet. We have NOT claimed their terms forbid it.
export const UNAVAILABLE = {
  tripadvisor: { label: 'Tripadvisor', reason: 'terms', why: 'its terms prohibit robots, scrapers and other automated collection' },
  facebook: { label: 'Facebook', reason: 'terms', why: 'Meta bars collecting data from its products by automated means' },
  amazon: { label: 'Amazon', reason: 'terms', why: 'its conditions of use restrict data mining, robots and similar extraction tools' },
  bbb: { label: 'Better Business Bureau', reason: 'terms', why: 'its terms limit use to personal, non-commercial use and bar compiling its data' },
  booking: { label: 'Booking.com', reason: 'nosource', why: 'we have no approved data source for it yet' },
  expedia: { label: 'Expedia', reason: 'nosource', why: 'we have no approved data source for it yet' },
  trustpilot: { label: 'Trustpilot', reason: 'nosource', why: 'we have no approved data source for it yet' },
  healthgrades: { label: 'Healthgrades', reason: 'nosource', why: 'we have no approved data source for it yet' },
  vitals: { label: 'Vitals', reason: 'nosource', why: 'we have no approved data source for it yet' },
  ratemds: { label: 'RateMDs', reason: 'nosource', why: 'we have no approved data source for it yet' },
  resy: { label: 'Resy', reason: 'nosource', why: 'we have no approved data source for it yet' },
}

const CLINIC = ['healthgrades', 'vitals', 'ratemds', 'facebook', 'bbb']
export const UNAVAILABLE_BY_INDUSTRY = {
  casual_dining: ['tripadvisor', 'facebook', 'resy'],
  fine_dining: ['tripadvisor', 'facebook', 'resy'],
  urgent_care: CLINIC,
  dental: CLINIC,
  primary_care: CLINIC,
  general: ['facebook', 'bbb', 'trustpilot'],
  retail: ['facebook', 'amazon', 'trustpilot', 'bbb'],
  hospitality: ['tripadvisor', 'booking', 'expedia', 'facebook'],
}

export function unavailableFor(industryId) {
  return (UNAVAILABLE_BY_INDUSTRY[industryId] ?? []).map((k) => ({ id: k, ...UNAVAILABLE[k] }))
}
