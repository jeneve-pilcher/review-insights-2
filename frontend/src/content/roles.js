// Who uses it, described by what each person uses it FOR (not by their account permission level). Every item describes
// something the app really does.
export const ROLES = [
  {
    id: 'owner',
    icon: '🏪',
    tone: 'burnt',
    title: 'Owner or general manager',
    purpose: 'spot a drifting rating and the complaints that need attention',
    uses: ['Sentiment drift: weekly rating and tone', 'Industry themes, week by week', 'Negative reviews flagged on your dashboard (Pro)'],
  },
  {
    id: 'marketing',
    icon: '📣',
    tone: 'coral',
    title: 'Marketing or reputation manager',
    purpose: 'track sentiment, platforms and competitors',
    uses: ['Platform comparison (Pro)', 'Competitor share matrix (Pro)', 'Draft replies you post yourself (Pro, not healthcare)'],
  },
  {
    id: 'experience',
    icon: '🤝',
    tone: 'apricot',
    title: 'Guest or patient experience lead',
    purpose: 'see what people complain about and make sure it gets answered',
    uses: ['Negative reviews with the topics people raise (Pro)', 'Draft replies to reviews, filtered to the good or the bad (Pro, not healthcare)', 'Wait-time patterns by hour (Pro)'],
  },
]

export const ROLES_NOTE =
  'In healthcare, reply drafts are off.'
