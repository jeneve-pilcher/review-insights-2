// What the front page says about each industry. The facts (labels, themes, data sources, what's switched on) mirror the
// server's industry list; a test fails if the two ever disagree. Everything else is marketing copy: it describes what is
// actually built and promises no outcomes.
export const GROUP_ORDER = ['Restaurants', 'Healthcare', 'Other', 'Retail']

export const SOURCE_NAMES = { yelp: 'Yelp', opentable: 'OpenTable', doordash: 'DoorDash', ubereats: 'Uber Eats', grubhub: 'Grubhub' }

export const EVERY_INDUSTRY = [
  "Sentiment drift: weekly review volume and tone, with early-warning flags",
  "Revenue signals in plain English, with the estimated revenue at stake (Pro)",
  "Your industry's trends, flagged only when there is enough evidence",
  "Negative reviews become tasks you can assign and track (Pro)",
  "Many locations? A company view with benchmarks, tasks and a team (Pro and Enterprise)"
]

export const INDUSTRIES = [
  {
    "id": "casual_dining",
    "label": "Casual dining",
    "group": "Restaurants",
    "available": true,
    "blurb": "Sit-down and fast-casual restaurants",
    "pitch": "Catch waits, order mistakes and delivery problems early.",
    "themes": [
      "Wait times",
      "Order accuracy",
      "Portions & value",
      "Staff friendliness",
      "Families & kids",
      "Cleanliness",
      "Noise & atmosphere",
      "Takeout & delivery"
    ],
    "graphs": [
      "A wait-time heatmap by day and hour, with the revenue estimated to be at stake",
      "Your themes week by week: waits, order mistakes, portions and value, takeout and delivery",
      "Google, Yelp, DoorDash, Uber Eats and Grubhub side by side",
      "Negative reviews turned into tasks, tagged with what they're about"
    ],
    "integrations": {
      "recommended": [
        "yelp",
        "doordash",
        "ubereats",
        "grubhub"
      ],
      "optional": [
        "opentable"
      ],
      "hidden": []
    },
    "notes": [
      "Draft replies to reviews, which you read and post yourself."
    ],
    "replies_allowed": true,
    "provider_level": false
  },
  {
    "id": "fine_dining",
    "label": "Fine dining",
    "group": "Restaurants",
    "available": true,
    "blurb": "Upscale and reservation-led restaurants",
    "pitch": "Watch pacing, ambiance and value, with OpenTable's own scores.",
    "themes": [
      "Pacing between courses",
      "Service & attentiveness",
      "Ambiance & noise",
      "Value for price",
      "Special occasions",
      "Food & tasting menu",
      "Wine & drinks",
      "Reservations & seating"
    ],
    "graphs": [
      "OpenTable food, service, ambience and value scores over time",
      "Your themes week by week: pacing between courses, ambiance and noise, value for price, special occasions, wine",
      "OpenTable, Yelp and Google side by side",
      "Negative reviews turned into tasks, tagged with what they're about"
    ],
    "integrations": {
      "recommended": [
        "opentable",
        "yelp"
      ],
      "optional": [
        "doordash",
        "ubereats",
        "grubhub"
      ],
      "hidden": []
    },
    "notes": [
      "Draft replies to reviews, which you read and post yourself."
    ],
    "replies_allowed": true,
    "provider_level": false
  },
  {
    "id": "urgent_care",
    "label": "Urgent care",
    "group": "Healthcare",
    "available": true,
    "blurb": "Walk-in and urgent care clinics",
    "pitch": "Track waits, quoted times and billing surprises across your clinics.",
    "themes": [
      "Wait times",
      "Quoted vs actual wait",
      "Front desk & staff",
      "Provider communication",
      "Billing & insurance",
      "Cleanliness",
      "Children",
      "Testing & imaging",
      "Hours & convenience"
    ],
    "graphs": [
      "Your themes week by week: waits, quoted versus actual times, billing and insurance, provider communication, testing",
      "Compare clinics side by side and see which one stands out on each theme",
      "Negative reviews turned into tasks, tagged with what they're about",
      "Optional: numbers for individual doctors from Zocdoc, switched on by your account administrator and shown only to the people you permit"
    ],
    "integrations": {
      "recommended": [
        "yelp"
      ],
      "optional": [],
      "hidden": [
        "opentable",
        "doordash",
        "ubereats",
        "grubhub"
      ]
    },
    "notes": [
      "Clinical words like “pain” aren't read as complaints.",
      "Replies are off for healthcare by design: a public reply can disclose protected health information."
    ],
    "replies_allowed": false,
    "provider_level": true
  },
  {
    "id": "dental",
    "label": "Dental",
    "group": "Healthcare",
    "available": true,
    "blurb": "Dental practices",
    "pitch": "Track scheduling, comfort, treatment explanations and billing.",
    "themes": [
      "Scheduling & access",
      "Wait & punctuality",
      "Comfort & gentleness",
      "Hygienists & staff",
      "Billing & insurance",
      "Explaining treatment",
      "Cleanliness",
      "Children",
      "Emergency & same-day"
    ],
    "graphs": [
      "Your themes week by week: scheduling, comfort and gentleness, explaining treatment, billing and insurance, cleanliness",
      "Compare practices side by side and see which one stands out on each theme",
      "Negative reviews turned into tasks, tagged with what they're about",
      "Optional: numbers for individual doctors from Zocdoc, switched on by your account administrator and shown only to the people you permit"
    ],
    "integrations": {
      "recommended": [
        "yelp"
      ],
      "optional": [],
      "hidden": [
        "opentable",
        "doordash",
        "ubereats",
        "grubhub"
      ]
    },
    "notes": [
      "Clinical words like “pain” aren't read as complaints.",
      "Replies are off for healthcare by design: a public reply can disclose protected health information."
    ],
    "replies_allowed": false,
    "provider_level": true
  },
  {
    "id": "primary_care",
    "label": "Primary care",
    "group": "Healthcare",
    "available": true,
    "blurb": "Family and primary care practices",
    "pitch": "Track getting appointments, follow-up, communication and billing.",
    "themes": [
      "Getting appointments",
      "Wait in the office",
      "Bedside manner",
      "Follow-up & results",
      "Phone & portal",
      "Billing & insurance",
      "Front desk & nurses",
      "Continuity of care"
    ],
    "graphs": [
      "Your themes week by week: getting appointments, follow-up and results, phone and portal, bedside manner, billing",
      "Compare practices side by side and see which one stands out on each theme",
      "Negative reviews turned into tasks, tagged with what they're about",
      "Optional: numbers for individual doctors from Zocdoc, switched on by your account administrator and shown only to the people you permit"
    ],
    "integrations": {
      "recommended": [
        "yelp"
      ],
      "optional": [],
      "hidden": [
        "opentable",
        "doordash",
        "ubereats",
        "grubhub"
      ]
    },
    "notes": [
      "Clinical words like “pain” aren't read as complaints.",
      "Replies are off for healthcare by design: a public reply can disclose protected health information."
    ],
    "replies_allowed": false,
    "provider_level": true
  },
  {
    "id": "general",
    "label": "Other / not listed",
    "group": "Other",
    "available": true,
    "blurb": "Any other business",
    "pitch": "A general set of themes for any business that isn't listed yet.",
    "themes": [
      "Service",
      "Quality",
      "Price & value",
      "Wait times",
      "Cleanliness"
    ],
    "graphs": [
      "Your themes week by week: service, quality, price and value, waits, cleanliness",
      "Google and Yelp side by side",
      "Negative reviews turned into tasks, tagged with what they're about"
    ],
    "integrations": {
      "recommended": [
        "yelp"
      ],
      "optional": [
        "opentable",
        "doordash",
        "ubereats",
        "grubhub"
      ],
      "hidden": []
    },
    "notes": [
      "Draft replies to reviews, which you read and post yourself."
    ],
    "replies_allowed": true,
    "provider_level": false
  },
  {
    "id": "retail",
    "label": "Retail",
    "group": "Retail",
    "available": false,
    "blurb": "Stores",
    "pitch": "Stock, checkout lines, returns and staff help.",
    "themes": [],
    "graphs": [],
    "integrations": {
      "recommended": [],
      "optional": [],
      "hidden": []
    },
    "notes": [],
    "replies_allowed": true,
    "provider_level": false
  }
]

export function industryById(id) {
  return INDUSTRIES.find((i) => i.id === id) ?? null
}

export function selectable(id) {
  return Boolean(industryById(id)?.available)
}

export function groupedIndustries() {
  return GROUP_ORDER.map((name) => ({ name, items: INDUSTRIES.filter((i) => i.group === name) })).filter((g) => g.items.length)
}

// The data sources named on the page for an industry: Google always, then its recommended ones.
export function sourceChips(industry) {
  if (!industry?.available) return []
  return ['Google', ...(industry.integrations?.recommended ?? []).map((id) => SOURCE_NAMES[id] ?? id)]
}
