// Who uses it, described by what each person uses it FOR (not by their account permission level). Every item describes
// something the app really does.
export const ROLES = [
  {
    id: 'owner',
    icon: '🏪',
    tone: 'burnt',
    title: 'Owner or general manager',
    purpose: 'spot drifting ratings and the complaints that need attention',
    uses: ['Sentiment drift and revenue signals', 'Negative reviews as tasks (Pro)', 'Industry themes, week by week'],
  },
  {
    id: 'operations',
    icon: '🗺️',
    tone: 'amber',
    title: 'Operations, regional or district manager',
    purpose: 'see which locations need a visit',
    uses: ['Benchmarks and a theme-by-location grid', 'Which locations mention each theme most', 'One task list for all locations'],
  },
  {
    id: 'marketing',
    icon: '📣',
    tone: 'coral',
    title: 'Marketing or reputation manager',
    purpose: 'track sentiment, platforms and competitors',
    uses: ['Platform comparison', 'Competitor share matrix (Pro)', 'Draft replies you post yourself (not healthcare)'],
  },
  {
    id: 'experience',
    icon: '🤝',
    tone: 'apricot',
    title: 'Guest or patient experience lead',
    purpose: 'turn negative reviews into work that gets done',
    uses: ['1\u20132\u2605 reviews become tagged tasks', 'Assign, note and resolve', 'A log of who did what'],
  },
  {
    id: 'location',
    icon: '🏬',
    tone: 'tangerine',
    title: 'Location or store manager',
    purpose: 'manage their own location only',
    uses: ['Run checks for their location', 'Their tasks and alerts', 'Industry graphs for their location'],
  },
  {
    id: 'leadership',
    icon: '📊',
    tone: 'brand',
    title: 'Executives, finance and brand leadership',
    purpose: 'see the company picture, view-only',
    uses: ['Company-wide numbers and trends', 'Revenue signals in plain English (Pro)', 'Location benchmarks'],
  },
]

export const ROLES_NOTE =
  'In healthcare, replies are off and doctor-level numbers are optional, shown only to people you permit.'
