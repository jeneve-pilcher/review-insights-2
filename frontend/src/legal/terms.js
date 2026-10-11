// Terms of Service for Review Insights.
//
// THIS IS A STARTING DRAFT, NOT LEGAL ADVICE. Have a lawyer review it before you rely on it,
// and fill in the company details below. Anything left blank shows up highlighted in the
// document so it can't be missed.
//
// Whenever you change the meaning of these terms, change TERMS_VERSION: everyone is then
// asked to agree again, and their agreement is recorded against the new version.

export const TERMS_VERSION = '2026-10-06'
export const EFFECTIVE_DATE = 'October 6, 2026'

// Set to false to show the terms without requiring people to accept them first.
export const REQUIRE_ACCEPTANCE = true

// ---- FILL THESE IN -----------------------------------------------------------------------
export const COMPANY = {
  COMPANY_NAME: '', // e.g. 'Acme Insights LLC'
  CONTACT_EMAIL: '', // where people can reach you about these terms
  GOVERNING_LAW: '', // e.g. 'the laws of the State of Indiana, USA, and the courts located in Hamilton County'
  REFUND_POLICY: '', // e.g. 'Subscriptions can be cancelled at any time and stay active until the end of the paid period. Fees are not refunded except where required by law.'
  PRIVACY_POLICY: '', // e.g. 'our Privacy Policy at https://example.com/privacy'
  CREDIT_POLICY: '', // e.g. 'Credit does not expire while your account is open and is not refundable, except where required by law.'
}
// -------------------------------------------------------------------------------------------

export const PLACEHOLDER_LABELS = {
  COMPANY_NAME: 'company name',
  CONTACT_EMAIL: 'contact email',
  GOVERNING_LAW: 'governing law and courts',
  REFUND_POLICY: 'refund and cancellation policy',
  PRIVACY_POLICY: 'privacy policy',
  CREDIT_POLICY: 'usage credit expiry and refund policy',
}

// Splits text into plain pieces and {{TOKEN}} pieces, filling in the ones you've set and
// flagging the ones you haven't.
export function segments(text, company = COMPANY) {
  return String(text)
    .split(/(\{\{[A-Z_]+\}\})/)
    .filter((part) => part !== '')
    .map((part) => {
      const m = part.match(/^\{\{([A-Z_]+)\}\}$/)
      if (!m) return { text: part, placeholder: false }
      const value = (company[m[1]] ?? '').trim()
      if (value) return { text: value, placeholder: false }
      return { text: `[${PLACEHOLDER_LABELS[m[1]] ?? m[1]}: not set yet]`, placeholder: true }
    })
}

export function placeholdersLeft(company = COMPANY) {
  return Object.keys(PLACEHOLDER_LABELS).filter((k) => !(company[k] ?? '').trim())
}

// Has this person agreed to the current version?
export function needsAcceptance(me, version = TERMS_VERSION) {
  return Boolean(me) && me.terms_version !== version
}

// ---- The document ------------------------------------------------------------------------
// blocks: { type: 'p', text } | { type: 'list', items: [...] } | { type: 'topics', items: [{ id, title, text }] }
export const SECTIONS = [
  {
    id: 'agreement',
    title: '1. Agreement',
    blocks: [
      {
        type: 'p',
        text: 'These terms are an agreement between you and {{COMPANY_NAME}} ("we", "us"). By creating an account or using Review Insights ("the service") you agree to them. If you use the service for a company, you confirm that you can accept these terms on that company\'s behalf.',
      },
    ],
  },
  {
    id: 'service',
    title: '2. What the service does',
    blocks: [
      {
        type: 'p',
        text: 'Review Insights collects publicly available reviews of a business (currently from Google and, if you add them, Yelp, OpenTable, DoorDash, Uber Eats and Grubhub) and, if you turn it on, web search results that mention the business. It then analyzes them to show rating and volume trends, language and topic findings, signals worth a look, rankings between locations, and tasks for negative reviews. It can also draft replies for you to edit and post yourself.',
      },
      {
        type: 'p',
        text: 'The service is an analysis and workflow tool. It does not control, edit or remove reviews anywhere, and it does not act on your behalf on any review platform.',
      },
    ],
  },
  {
    id: 'accounts',
    title: '3. Accounts, teams and invitations',
    blocks: [
      {
        type: 'list',
        items: [
          'You are responsible for activity on your account and for keeping your login secure. Tell us promptly if you think it has been misused.',
          'In a company account, the owner and admins decide who is added and what role they have (owner, admin, manager or viewer). Managers see only the locations assigned to them; viewers can read but not change anything.',
          'Adding someone to a company does not send them an email. They join when they sign up or log in using exactly the email address you entered, so check addresses carefully: anyone who controls that address can join with that role.',
          'Removing someone, or changing their role, takes effect immediately. You are responsible for removing people who should no longer have access.',
        ],
      },
    ],
  },
  {
    id: 'rely',
    title: '4. Before you rely on it',
    blocks: [
      {
        type: 'p',
        text: 'Please read this section carefully. It explains what the service can and cannot be relied on for.',
      },
      {
        type: 'topics',
        items: [
          {
            id: 'data',
            title: 'Review data comes from third parties and can be incomplete or wrong',
            text: 'We obtain reviews through outside data providers and scraping services, not directly from the platforms, and some of those services are small or community-run, so they can break or change without notice. We limit how many reviews are pulled per business, and when a time window is cut short by that limit we say so, but older reviews may then be missing. Platforms can hide, filter, delay or remove reviews (for example, Yelp does not show every review it receives), change their format, or block access, so the numbers here can differ from what a platform shows. Uber Eats reviews have no star ratings, so they are read for tone but never counted in your ratings or review totals. Reviews with a star rating but no comment are counted in volumes and ratings but contain no text to analyze.',
          },
          {
            id: 'estimates',
            title: 'Scores, signals and dollar figures are indicators, not facts or predictions',
            text: 'Revenue and "revenue drag" figures are rough estimates built from review patterns and numbers you type in (such as average order value); we cannot see your sales. "Rating gain" figures are simple arithmetic on your own reviews, not forecasts. Tone and topic scoring is automated and can misread sarcasm, slang or very short comments. Trend and signal checks use statistical thresholds, so some flagged patterns will be chance and some real patterns will be missed. Industry themes and graphs are found by matching words and phrases in written reviews, so they can miss unusual wording or catch an unrelated use of a word, and a flagged trend can still be chance. We do not promise that acting on any signal will improve your ratings, search ranking or revenue.',
          },
          {
            id: 'time',
            title: 'Times of day come from when a review was posted',
            text: 'Day-and-hour views use the time a review was posted, which is only a rough stand-in for when the visit happened. Some platforms provide only a date, so time-of-day analysis uses Google reviews only.',
          },
          {
            id: 'mentions',
            title: 'Internet mentions are a sample',
            text: 'Mentions come from web search results (headlines and short snippets). They are not exhaustive; posts on some social networks rarely appear; some results may be unrelated to your business; and a mention\'s tone is judged from a short snippet. In your analysis they are treated as unrated written items: they appear alongside reviews and are included in the tone and language findings, but they are never counted as star reviews or included in ratings, review totals or time-of-day views. Reviews from Uber Eats are treated the same way. Open the page and read it before acting on it.',
          },
          {
            id: 'replies',
            title: 'Draft replies are only drafts, and we do not post them',
            text: 'Drafts are written by an AI service (if enabled) or from a built-in template, and may be inaccurate, off-tone or unsuitable. Our warnings about risky wording (such as promises of refunds) are not complete. You must read and edit every reply before you use it. The service cannot post to Google, Yelp or any other platform: you copy a reply and post it yourself, and "Mark as sent" only records that you did. You are responsible for everything you publish, including following each platform\'s rules and the law (for example, never offering rewards in exchange for reviews where a platform forbids it, and never revealing a customer\'s personal details).',
          },
          {
            id: 'alerts',
            title: 'Alerts, tasks and automatic checks are best-effort',
            text: 'Automatic checks run on a schedule (by default about once a day) and can be delayed or skipped, for example when a monthly spending limit has been reached or its credit balance has been used, a data source is down or errors, or our servers restart. A review may be reported late or missed, and alert emails can fail or land in spam. Do not rely on the service as your only way to learn about urgent matters such as food-safety, health, safety or legal complaints.',
          },
          {
            id: 'privacy',
            title: 'Personal details are removed on a best-effort basis',
            text: 'We remove things that look like email addresses, phone numbers and order numbers from review text we display or send onward, and we do not show reviewers\' names. This filter is not perfect: names and other personal details written inside a review may remain. Review text is public content from the platforms where it was posted.',
          },
          {
            id: 'advice',
            title: 'Not professional advice',
            text: 'Nothing in the service is legal, financial, tax, employment, medical or other professional advice. Decisions you make using it are yours. For healthcare businesses the service reads public reviews only: never enter or upload patient information, and note that replies are turned off for healthcare accounts because answering a patient\'s review can disclose protected health information.',
          },
          {
            id: 'providers',
            title: 'Some features use outside services',
            text: 'To run the service we rely on providers for hosting and the database, payments, email, review and web-search data collection, and (only if enabled) AI drafting. When AI drafting is on, the text of the review you are replying to, with emails, phone numbers and order numbers removed, is sent to the AI provider to produce a draft. These providers can have outages or change their terms, which can affect the service. Where provider-level data about individual doctors is enabled, it comes from the doctors\' public pages and is shown only to the people your company has given access.',
          },
        ],
      },
    ],
  },
  {
    id: 'platforms',
    title: '5. Review platforms and their rules',
    blocks: [
      {
        type: 'list',
        items: [
          'Google, Yelp and other platforms own and control their reviews and have their own terms. We are not affiliated with them, and their names and marks belong to their owners.',
          'You are responsible for using the service, and anything you do with the results, in line with those platforms\' terms and with the law that applies to you. Platforms may restrict or change how their public data can be collected or used.',
          'If a platform, a legal requirement or a provider requires it, we may change, limit or stop a data source or feature, with or without notice.',
        ],
      },
    ],
  },
  {
    id: 'use',
    title: '6. Acceptable use',
    blocks: [
      { type: 'p', text: 'You agree not to:' },
      {
        type: 'list',
        items: [
          'use the service to write, buy, sell, trade or manipulate fake or incentivized reviews, or to break any platform\'s rules;',
          'use it to harass, intimidate or try to identify a reviewer;',
          'break the law, or use it for a business you are not authorized to represent;',
          'enter, upload or paste patient information or other protected health information into the service;',
          'try to disrupt, probe or overload the service, share your login, or resell the service or its data without our written permission.',
        ],
      },
    ],
  },
  {
    id: 'data',
    title: '7. Your data and privacy',
    blocks: [
      {
        type: 'p',
        text: 'You keep ownership of the information you give us (such as business details, locations, notes and replies). You give us permission to store and process it to run the service for you. We store account details, location settings, review summaries over time, tasks, saved replies and an activity log. You can delete your account in the app, which also cancels any active subscription; for data a company holds, or to ask us to remove something, contact {{CONTACT_EMAIL}}.',
      },
      { type: 'p', text: 'More about how personal information is handled: {{PRIVACY_POLICY}}.' },
    ],
  },
  {
    id: 'billing',
    title: '8. Plans, billing and limits',
    blocks: [
      {
        type: 'list',
        items: [
          'Some features are free and some need a paid plan. Paid plans renew automatically through our payment provider until you cancel from "Manage subscription".',
          'Refunds and cancellation: {{REFUND_POLICY}}',
          'Usage credit: paid plans include a monthly usage allowance, which is spent first. Heavier use, and everything a company account runs, is paid from prepaid credit that you buy in packs. The price of a pack and the credit it gives are shown before you buy, and each run deducts the usage it actually needs (data pulls, web searches and AI drafts), shown before and after the run. Pulls served from a recent copy are free. A single run can take a balance slightly below zero, and further runs are blocked until credit is added. You can also set a monthly spending limit (for your own account, or for a company if you are its owner): once the limit is reached, usage stops until the next month or until you raise it, and the run that crosses the limit finishes, so spending can go slightly over it. {{CREDIT_POLICY}}',
          'To keep costs predictable, the service applies limits, such as the number of reviews pulled per business, optional per-company monthly spending limits and credit balances (automatic checks pause when either is used up), daily limits on reply drafts, and a maximum number of locations. We may adjust these limits.',
        ],
      },
    ],
  },
  {
    id: 'availability',
    title: '9. Availability and changes',
    blocks: [
      {
        type: 'p',
        text: 'We work to keep the service running but do not promise it will always be available or error-free, and outside providers can interrupt it. We may add, change or remove features. If we make a change that matters to these terms, we will update the version and ask you to agree again.',
      },
    ],
  },
  {
    id: 'warranty',
    title: '10. No warranties',
    blocks: [
      {
        type: 'p',
        text: 'To the fullest extent the law allows, the service is provided "as is" and "as available", without warranties of any kind, including accuracy, completeness, fitness for a particular purpose and non-infringement.',
      },
    ],
  },
  {
    id: 'liability',
    title: '11. Limit of liability',
    blocks: [
      {
        type: 'p',
        text: 'To the fullest extent the law allows, we are not liable for indirect, incidental, special or consequential losses, or for lost profits, revenue, data or goodwill, arising from your use of the service. Our total liability for any claim is limited to the amount you paid us in the 12 months before the claim (or $100 if you have paid nothing). Some places do not allow these limits, so they apply only as far as the law permits.',
      },
    ],
  },
  {
    id: 'termination',
    title: '12. Ending your use',
    blocks: [
      {
        type: 'p',
        text: 'You can stop using the service and delete your account at any time. We may suspend or end access if you break these terms, if required by law or by a provider, or if continuing would put the service or others at risk.',
      },
    ],
  },
  {
    id: 'changes',
    title: '13. Changes to these terms',
    blocks: [
      {
        type: 'p',
        text: 'We may update these terms. When we do, we will change the version shown below and ask you to agree to the new version before you continue. Using the service after agreeing means you accept the updated terms.',
      },
    ],
  },
  {
    id: 'law',
    title: '14. Governing law and contact',
    blocks: [
      { type: 'p', text: 'These terms are governed by {{GOVERNING_LAW}}.' },
      { type: 'p', text: 'Questions about these terms: {{CONTACT_EMAIL}}.' },
    ],
  },
]

// The "Before you rely on it" topics every version of the terms must keep.
export const REQUIRED_RELY_TOPICS = ['data', 'estimates', 'time', 'mentions', 'replies', 'alerts', 'privacy', 'advice', 'providers']
