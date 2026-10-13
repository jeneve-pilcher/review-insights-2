// Privacy Policy for Review Insights.
//
// THIS IS A STARTING DRAFT, NOT LEGAL ADVICE. It was written from what the app does today, so have a lawyer review it
// and check it against how you actually run the service (hosting, email provider, backups) before you rely on it.
// The company name and contact email come from COMPANY in ./terms.js; if they are blank the page highlights them.
//
// If what the app collects or shares changes (a new outside service, a new kind of data), change this text and PRIVACY_DATE.

export const PRIVACY_DATE = 'October 13, 2026'

const p = (text) => ({ type: 'p', text })
const list = (items) => ({ type: 'list', items })

export const PRIVACY_SECTIONS = [
  {
    id: 'summary',
    title: 'The short version',
    blocks: [
      list([
        'We collect what you give us (your email, your business and review-page links) and the public reviews of the business you ask us to look at.',
        'We do not sell personal information, and we do not run advertising trackers.',
        'A few outside services do part of the work for us. Section 4 lists each one and what it receives.',
        'Healthcare accounts: reply drafting is turned off, so no review text is sent to an AI model.',
        'You can delete your account yourself from your dashboard.',
      ]),
    ],
  },
  {
    id: 'who',
    title: '1. Who we are',
    blocks: [p('{{COMPANY_NAME}} runs Review Insights ("we", "us"). Questions about this policy or your data: {{CONTACT_EMAIL}}.')],
  },
  {
    id: 'collect',
    title: '2. What we collect',
    blocks: [
      p('Information you give us:'),
      list([
        'Account: your email address and a password. Passwords are handled by our sign-in provider, and we never see them in readable form.',
        'Your business: the name, address or Google Maps link you enter, your industry, and any Yelp, OpenTable, DoorDash, Uber Eats or Grubhub links you add.',
        'Company accounts: team members\' email addresses and roles, your locations, tasks and notes, and a log of who did what in the account.',
        'Reply drafts you choose to save.',
        'Your plan and usage credit: which plan you are on, your credit balance and a ledger of what each run cost.',
        'Your agreement to our Terms of Service: which version, and when.',
      ]),
      p('Payment details are collected and stored by Stripe. We never see or keep your card number. We keep Stripe\'s customer and subscription identifiers so we can show your plan and open the billing portal.'),
      p('Technical information: your browser keeps a sign-in session (and a few settings) so you stay logged in. Our servers handle the requests you make, and may log things like errors and timing to keep the service running.'),
    ],
  },
  {
    id: 'reviews',
    title: '3. Reviews we read',
    blocks: [
      p('When you run an analysis we fetch public reviews of the business you named from Google, plus Yelp and any other pages you connected. These are public posts written by other people.'),
      list([
        'Reviews are held in the server\'s memory for about 30 minutes so a second run does not fetch them again. They are not otherwise saved.',
        'What we do keep from a run depends on your account. Company accounts that use scheduled checks keep summary numbers for each check (ratings, counts, tone, rising topics) so you can see change over time.',
        'Company accounts also keep a short copy of recent low-star reviews as alerts so your team can follow up. The reviewer\'s name is not kept, and the text is cleaned of things that look like emails and phone numbers (best effort, so it can miss some) and cut to 500 characters.',
        'Reviews are used to produce your analysis. We do not use them to build profiles of the people who wrote them.',
      ]),
    ],
  },
  {
    id: 'sharing',
    title: '4. Who else handles your data',
    blocks: [
      p('We use these outside services. Each receives only what it needs for its job, and we do not sell your data to them or anyone else.'),
      list([
        'Supabase: our database and sign-in. It stores your account and the data in section 2.',
        'Stripe: takes payments and manages subscriptions and credit purchases.',
        'Outscraper: fetches Google and Yelp reviews. It receives the business name or address (or Maps link) for the location you analyse.',
        'Apify: fetches pages such as OpenTable, delivery apps and Zocdoc. It receives the page links you saved.',
        'Anthropic (the Claude AI models): drafts review replies when you ask it to. It receives the business name, the star rating and the text of the one review being answered, cleaned of things that look like emails and phone numbers first (best effort). Reply drafting is off for healthcare accounts.',
        'Our hosting and email providers: run the service and send alert emails, such as the address you gave for a location manager.',
      ]),
      p('We may also disclose information if the law requires it, or to protect our rights, or if the business is sold or merged (in which case this policy will keep applying until you are told otherwise).'),
    ],
  },
  {
    id: 'health',
    title: '5. Healthcare accounts',
    blocks: [
      p('For urgent care, dental and primary care accounts, reply drafting is switched off, because answering a patient\'s review can disclose health information, so review text is never sent to an AI model. Trends for these accounts are calculated on our own servers.'),
      p('Review Insights is not designed to receive patient health information. Please do not type any into the service, including in notes or tasks.'),
    ],
  },
  {
    id: 'keep',
    title: '6. How long we keep it, and deleting it',
    blocks: [
      p('We keep your account data while your account is open. You can use "Delete account" in your dashboard at any time: it cancels any active subscription and removes your sign-in. If you want something else removed, or you use a company account and need data about your team removed, email {{CONTACT_EMAIL}} and we will help.'),
      p('Stripe and our other providers may keep records they are required to keep (for example payment records) under their own policies. Backups can take some time to roll off.'),
    ],
  },
  {
    id: 'rights',
    title: '7. Your choices and rights',
    blocks: [
      p('You can ask us to give you a copy of your information, correct it, or delete it. Depending on where you live (for example California, the UK or the EU) the law may give you more rights, such as objecting to certain uses. Email {{CONTACT_EMAIL}} and we will respond within the time the law allows. You can leave out any review page you do not want us to read.'),
    ],
  },
  {
    id: 'security',
    title: '8. Keeping it safe',
    blocks: [
      p('Traffic to the service is encrypted in transit. Company data tables are locked so they are only reachable through our server, which checks who you are and what role you have before it returns anything. No system is perfectly secure, so we cannot promise absolute security.'),
    ],
  },
  {
    id: 'kids',
    title: '9. Children',
    blocks: [p('Review Insights is for businesses and is not meant for anyone under 18. We do not knowingly collect information from children.')],
  },
  {
    id: 'changes',
    title: '10. Changes',
    blocks: [p('If we change this policy in a way that matters, we will update the date above and, for big changes, tell account holders by email or in the app.')],
  },
]
