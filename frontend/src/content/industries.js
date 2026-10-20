// What the front page says about each industry. The facts (labels, themes, data sources, what's switched on) mirror the
// server's industry list; a test fails if the two ever disagree. Everything else is marketing copy: it describes what is
// actually built and promises no outcomes.
export const GROUP_ORDER = ['Restaurants', 'Healthcare', 'Other', 'Retail', 'Hospitality']

export const SOURCE_NAMES = { yelp: 'Yelp', opentable: 'OpenTable', doordash: 'DoorDash', ubereats: 'Uber Eats', grubhub: 'Grubhub' }

export const EVERY_INDUSTRY = [
  "Sentiment drift: weekly review volume and tone, with early-warning flags",
  "Revenue signals in plain English: what is worth acting on first (Pro)",
  "Your industry's trends, flagged only when there is enough evidence",
  "Filter reviews by stars, words and phrases, and draft replies outside healthcare (Pro)"
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
      "Reviews filtered by stars, words and phrases"
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
    "provider_level": false,
    "themeDetails": [
      {
        "label": "Wait times",
        "examples": [
          "wait",
          "waited",
          "waiting",
          "line",
          "long time"
        ]
      },
      {
        "label": "Order accuracy",
        "examples": [
          "wrong order",
          "wrong",
          "missing",
          "forgot",
          "mistake"
        ]
      },
      {
        "label": "Portions & value",
        "examples": [
          "portion",
          "portions",
          "small",
          "tiny",
          "overpriced"
        ]
      },
      {
        "label": "Staff friendliness",
        "examples": [
          "friendly",
          "rude",
          "attitude",
          "welcoming",
          "unfriendly"
        ]
      },
      {
        "label": "Families & kids",
        "examples": [
          "kids",
          "children",
          "family",
          "high chair",
          "kid-friendly"
        ]
      },
      {
        "label": "Cleanliness",
        "examples": [
          "clean",
          "dirty",
          "filthy",
          "sticky",
          "bathroom"
        ]
      },
      {
        "label": "Noise & atmosphere",
        "examples": [
          "loud",
          "noisy",
          "noise",
          "atmosphere",
          "vibe"
        ]
      },
      {
        "label": "Takeout & delivery",
        "examples": [
          "delivery",
          "takeout",
          "take out",
          "to-go",
          "to go"
        ]
      }
    ]
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
      "Reviews filtered by stars, words and phrases"
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
    "provider_level": false,
    "themeDetails": [
      {
        "label": "Pacing between courses",
        "examples": [
          "pacing",
          "paced",
          "rushed",
          "between courses",
          "took forever"
        ]
      },
      {
        "label": "Service & attentiveness",
        "examples": [
          "attentive",
          "inattentive",
          "sommelier",
          "server",
          "waiter"
        ]
      },
      {
        "label": "Ambiance & noise",
        "examples": [
          "ambiance",
          "ambience",
          "atmosphere",
          "decor",
          "romantic"
        ]
      },
      {
        "label": "Value for price",
        "examples": [
          "overpriced",
          "not worth",
          "worth it",
          "worth the",
          "expensive"
        ]
      },
      {
        "label": "Special occasions",
        "examples": [
          "anniversary",
          "birthday",
          "special occasion",
          "celebrate",
          "celebration"
        ]
      },
      {
        "label": "Food & tasting menu",
        "examples": [
          "tasting menu",
          "dish",
          "dishes",
          "flavor",
          "flavors"
        ]
      },
      {
        "label": "Wine & drinks",
        "examples": [
          "wine",
          "pairing",
          "pairings",
          "cocktail",
          "cocktails"
        ]
      },
      {
        "label": "Reservations & seating",
        "examples": [
          "reservation",
          "reserved",
          "booked",
          "booking",
          "seated"
        ]
      }
    ]
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
      "Reviews filtered by stars, words and phrases",
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
    "provider_level": true,
    "themeDetails": [
      {
        "label": "Wait times",
        "examples": [
          "wait",
          "waited",
          "waiting",
          "hours",
          "an hour"
        ]
      },
      {
        "label": "Quoted vs actual wait",
        "examples": [
          "quoted",
          "estimated wait",
          "online check-in",
          "online check in",
          "check-in time"
        ]
      },
      {
        "label": "Front desk & staff",
        "examples": [
          "front desk",
          "receptionist",
          "reception",
          "staff",
          "rude"
        ]
      },
      {
        "label": "Provider communication",
        "examples": [
          "doctor",
          "provider",
          "nurse",
          "practitioner",
          "physician assistant"
        ]
      },
      {
        "label": "Billing & insurance",
        "examples": [
          "bill",
          "billing",
          "insurance",
          "copay",
          "co-pay"
        ]
      },
      {
        "label": "Cleanliness",
        "examples": [
          "clean",
          "dirty",
          "filthy",
          "bathroom",
          "restroom"
        ]
      },
      {
        "label": "Children",
        "examples": [
          "kids",
          "child",
          "children",
          "pediatric",
          "son"
        ]
      },
      {
        "label": "Testing & imaging",
        "examples": [
          "x-ray",
          "xray",
          "lab",
          "labs",
          "test"
        ]
      },
      {
        "label": "Hours & convenience",
        "examples": [
          "open late",
          "weekend",
          "weekends",
          "parking",
          "location"
        ]
      }
    ]
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
      "Reviews filtered by stars, words and phrases",
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
    "provider_level": true,
    "themeDetails": [
      {
        "label": "Scheduling & access",
        "examples": [
          "appointment",
          "scheduling",
          "schedule",
          "rescheduled",
          "cancelled"
        ]
      },
      {
        "label": "Wait & punctuality",
        "examples": [
          "wait",
          "waited",
          "waiting room",
          "on time",
          "late"
        ]
      },
      {
        "label": "Comfort & gentleness",
        "examples": [
          "gentle",
          "painless",
          "numb",
          "numbing",
          "hurt"
        ]
      },
      {
        "label": "Hygienists & staff",
        "examples": [
          "hygienist",
          "assistant",
          "front desk",
          "receptionist",
          "staff"
        ]
      },
      {
        "label": "Billing & insurance",
        "examples": [
          "bill",
          "billing",
          "insurance",
          "charged",
          "cost"
        ]
      },
      {
        "label": "Explaining treatment",
        "examples": [
          "explained",
          "explain",
          "options",
          "treatment plan",
          "unnecessary"
        ]
      },
      {
        "label": "Cleanliness",
        "examples": [
          "clean",
          "dirty",
          "sterile",
          "spotless",
          "modern"
        ]
      },
      {
        "label": "Children",
        "examples": [
          "kids",
          "child",
          "children",
          "pediatric",
          "son"
        ]
      },
      {
        "label": "Emergency & same-day",
        "examples": [
          "emergency",
          "same day",
          "same-day",
          "urgent",
          "toothache"
        ]
      }
    ]
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
      "Reviews filtered by stars, words and phrases",
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
    "provider_level": true,
    "themeDetails": [
      {
        "label": "Getting appointments",
        "examples": [
          "appointment",
          "scheduling",
          "weeks",
          "booked",
          "new patient"
        ]
      },
      {
        "label": "Wait in the office",
        "examples": [
          "wait",
          "waited",
          "waiting room",
          "running late",
          "behind schedule"
        ]
      },
      {
        "label": "Bedside manner",
        "examples": [
          "listened",
          "dismissive",
          "rushed",
          "compassionate",
          "caring"
        ]
      },
      {
        "label": "Follow-up & results",
        "examples": [
          "follow up",
          "follow-up",
          "referral",
          "referred",
          "test results"
        ]
      },
      {
        "label": "Phone & portal",
        "examples": [
          "portal",
          "phone",
          "voicemail",
          "hold",
          "message"
        ]
      },
      {
        "label": "Billing & insurance",
        "examples": [
          "bill",
          "billing",
          "insurance",
          "copay",
          "charged"
        ]
      },
      {
        "label": "Front desk & nurses",
        "examples": [
          "front desk",
          "receptionist",
          "nurse",
          "medical assistant",
          "staff"
        ]
      },
      {
        "label": "Continuity of care",
        "examples": [
          "different doctor",
          "turnover",
          "left the practice",
          "new doctor",
          "seen by"
        ]
      }
    ]
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
      "Reviews filtered by stars, words and phrases"
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
    "provider_level": false,
    "themeDetails": [
      {
        "label": "Service",
        "examples": [
          "service",
          "staff",
          "rude",
          "friendly",
          "helpful"
        ]
      },
      {
        "label": "Quality",
        "examples": [
          "quality",
          "poor quality",
          "excellent",
          "great quality",
          "broken"
        ]
      },
      {
        "label": "Price & value",
        "examples": [
          "price",
          "expensive",
          "cheap",
          "overpriced",
          "value"
        ]
      },
      {
        "label": "Wait times",
        "examples": [
          "wait",
          "waited",
          "waiting",
          "line",
          "slow"
        ]
      },
      {
        "label": "Cleanliness",
        "examples": [
          "clean",
          "dirty",
          "filthy",
          "spotless"
        ]
      }
    ]
  },
  {
    "id": "retail",
    "label": "Retail",
    "group": "Retail",
    "available": true,
    "blurb": "Any store",
    "pitch": "Stock, checkout lines, returns, prices and staff help.",
    "themes": [
      "Stock & availability",
      "Checkout & lines",
      "Returns & refunds",
      "Price & value",
      "Staff help",
      "Product quality",
      "Store layout & cleanliness",
      "Online orders & pickup"
    ],
    "graphs": [
      "Your themes week by week: stock, checkout lines, returns, price, staff help",
      "Google and Yelp side by side",
      "Reviews filtered by stars, words and phrases"
    ],
    "integrations": {
      "recommended": [
        "yelp"
      ],
      "optional": [
        "doordash",
        "ubereats",
        "grubhub"
      ],
      "hidden": [
        "opentable"
      ]
    },
    "notes": [
      "Draft replies to reviews, which you read and post yourself."
    ],
    "replies_allowed": true,
    "provider_level": false,
    "themeDetails": [
      {
        "label": "Stock & availability",
        "examples": [
          "out of stock",
          "sold out",
          "no stock",
          "empty shelves",
          "didn't have"
        ]
      },
      {
        "label": "Checkout & lines",
        "examples": [
          "checkout",
          "check out",
          "register",
          "cashier",
          "line"
        ]
      },
      {
        "label": "Returns & refunds",
        "examples": [
          "return",
          "returns",
          "refund",
          "exchange",
          "receipt"
        ]
      },
      {
        "label": "Price & value",
        "examples": [
          "price",
          "prices",
          "expensive",
          "cheap",
          "overpriced"
        ]
      },
      {
        "label": "Staff help",
        "examples": [
          "staff",
          "employee",
          "associate",
          "helpful",
          "unhelpful"
        ]
      },
      {
        "label": "Product quality",
        "examples": [
          "quality",
          "poor quality",
          "broken",
          "damaged",
          "defective"
        ]
      },
      {
        "label": "Store layout & cleanliness",
        "examples": [
          "clean",
          "dirty",
          "messy",
          "cluttered",
          "organized"
        ]
      },
      {
        "label": "Online orders & pickup",
        "examples": [
          "online order",
          "pickup",
          "pick up",
          "curbside",
          "delivery"
        ]
      }
    ]
  },
  {
    "id": "hospitality",
    "label": "Hotels & lodging",
    "group": "Hospitality",
    "available": true,
    "blurb": "Hotels, motels & inns",
    "pitch": "Room cleanliness, check-in, sleep, staff, location and fees.",
    "themes": [
      "Room cleanliness",
      "Check-in & check-out",
      "Beds, noise & sleep",
      "Staff & service",
      "Location & parking",
      "Pool, gym & amenities",
      "Breakfast & dining",
      "Price & fees"
    ],
    "graphs": [
      "Your themes week by week: cleanliness, check-in, sleep, staff, price and fees",
      "Google and Yelp side by side",
      "Reviews filtered by stars, words and phrases"
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
      "Draft replies to reviews, which you read and post yourself."
    ],
    "replies_allowed": true,
    "provider_level": false,
    "themeDetails": [
      {
        "label": "Room cleanliness",
        "examples": [
          "clean",
          "dirty",
          "filthy",
          "stains",
          "stained"
        ]
      },
      {
        "label": "Check-in & check-out",
        "examples": [
          "check-in",
          "check in",
          "checkin",
          "check-out",
          "check out"
        ]
      },
      {
        "label": "Beds, noise & sleep",
        "examples": [
          "bed",
          "mattress",
          "pillow",
          "pillows",
          "sheets"
        ]
      },
      {
        "label": "Staff & service",
        "examples": [
          "staff",
          "friendly",
          "helpful",
          "unhelpful",
          "rude"
        ]
      },
      {
        "label": "Location & parking",
        "examples": [
          "location",
          "walkable",
          "walking distance",
          "parking",
          "valet"
        ]
      },
      {
        "label": "Pool, gym & amenities",
        "examples": [
          "pool",
          "gym",
          "fitness",
          "hot tub",
          "spa"
        ]
      },
      {
        "label": "Breakfast & dining",
        "examples": [
          "breakfast",
          "buffet",
          "continental",
          "coffee",
          "restaurant"
        ]
      },
      {
        "label": "Price & fees",
        "examples": [
          "price",
          "expensive",
          "overpriced",
          "worth",
          "value"
        ]
      }
    ]
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

// What you'll find from each data source, shown when its tag is hovered. Plain descriptions of what is actually built.
export const SOURCE_TRENDS = {
  Google: 'Rating and tone over time, plus when complaints cluster by day and hour. Always included.',
  Yelp: 'Star ratings and tone over time, side by side with Google.',
  OpenTable: 'Food, service, ambience and value scores over time, so you can see which one is slipping.',
  DoorDash: 'Delivery star ratings and tone over time, next to your other platforms.',
  'Uber Eats': "Tone over time from written reviews. They have no stars, so they're never counted in your ratings.",
  Grubhub: 'Delivery star ratings and tone over time, next to your other platforms.',
}

export function sourceHover(name) {
  return SOURCE_TRENDS[name] ?? ''
}

// What a theme tag finds: the real words it looks for and the trend it reports.
export function themeHover(detail) {
  if (!detail || !detail.examples?.length) return ''
  const words = detail.examples.map((w) => `\u201c${w}\u201d`).join(', ')
  return `Trends we find: how often ${words} come up in written reviews, week by week. We flag it when it rises or falls over the last four weeks, and show how reviews that mention it rate compared with the rest, once there are enough reviews to say so.`
}

// What an industry's tag finds: its main themes, tracked the same way.
export function industryHover(industry) {
  if (!industry?.available || !industry.themes?.length) return ''
  const top = industry.themes.slice(0, 4).join(', ')
  return `Trends you'll find: ${top}${industry.themes.length > 4 ? ' and more' : ''}. Each is tracked week by week and flagged when it rises or falls over the last four weeks.`
}

export function themeDetail(industry, label) {
  return industry?.themeDetails?.find((d) => d.label === label) ?? null
}
