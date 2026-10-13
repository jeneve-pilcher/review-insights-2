Review Insights - ALL updates, v30 (a more colourful front page)
================================================================================================
This zip holds the FINAL version of every file changed by all updates so far, EXCEPT frontend/src/content/stats.js
(your own statistics file, which is yours and is never included). Apply it ONCE.
It includes everything from v5 to v29. NO NEW SQL. No new packages. No router change.

*** BEFORE UNZIPPING: back up your landing page ***
      cp frontend/src/views/LandingView.vue ~/LandingView.backup14.vue

1) From your project root:      unzip -o ~/Downloads/review-insights-all-updates-v30.zip
2) Rebuild:                     docker compose down && docker compose up --build

WHAT CHANGED IN v30 (colour and pictures only; no wording or behaviour changes)
- SHADES OF ORANGE: each card in "Who uses it" and "Where revenue may be slipping away" has its own shade (coral, tangerine,
  amber, apricot, burnt orange, and your brand colour). Each section has its own soft tint (peach and pale amber). The statistics
  cards and industry groups also use different oranges. Nothing outside the orange family, apart from the Retail group, now orange like the others.
- PICTURES: every card has a small illustration drawn for it (a clock and bars for waits, speech bubbles for a repeating complaint,
  a falling line for drift, map pins, an inbox with a tick, overlapping review cards; a storefront for the owner, a route for
  operations, a megaphone for marketing, a heart in a speech bubble for guest experience, a building with a pin for a location,
  rising bars for leadership). They are original vector drawings, not photos, so there is nothing to download and they stay sharp.
  Each is coloured in its card's shade.
- Small text uses a darker shade of each orange (all 4.5:1 or better on white).
- New files: frontend/src/theme/tones.css and frontend/src/components/CardArt.vue.

- SHORTER COPY: the hero, the section subtitles, every card line and both footnotes are tightened. Every card keeps its title,
  "We look at" / "You see" (or "Uses it to" / "What they look at"), its plan, and the estimate and healthcare notes.

- INTERNET MENTIONS made simple (Run Analysis form): one tick, "Include internet mentions (news, blogs, forums, social; about 2 cents)".
  The "words to search for" box and the "depth" box are gone; it always runs 2 pages. The business name is found for you.
  FIX: if a business was saved as a Google Maps link, the web search used to be run on the whole link (useless). It now uses the
  name in the link (e.g. "Starbucks"). If a link has no readable name (a short maps.app.goo.gl link), the run says so and charges nothing.
  Files: frontend/src/components/UnifiedAnalysisForm.vue, frontend/src/utils/mentions.js, backend/analysis/mentions.py, backend/analysis/pipeline.py.
  Tip: a business saved as "Name, street, city" searches name + city, which is better than a bare name for chains.

- INTERNET MENTIONS ARE NOW PER STORE (not the whole company, and not every store of the brand in a city). The search uses the
  business name plus the STREET ADDRESS and city, and a result is kept only if it points at that store: it mentions the street
  address, or the street name in the right city ("the Starbucks on Main St in Carmel"). The address comes from what you saved
  ("Name, street, city"), or, for a Google Maps link, from the address Google returns during the reviews pull. If no street can be
  found, the run says so, and falls back to the name (and city, if known).
  TRADE-OFF: web posts rarely include a street address, so a single store often gets only a handful of mentions, or none. That is
  the honest result: the web cannot be searched by exact store the way Google Maps reviews can. An empty result means no web post
  was found that clearly points at this store.
  CAVEAT: reading the address from the reviews pull assumes Outscraper returns the place's name/address with the reviews. I could not
  call Outscraper from here to confirm. If you see the "couldn't find this store's street address" note on a Maps-link location, save it
  as "Name, street, city" and tell me, and I will fix the lookup.
  Files: backend/analysis/mentions.py, outscraper_client.py, pipeline.py, main.py, corporate/routes.py.

- AI SUMMARIES REPLACE TREND FLAGS AND EARLY WARNINGS (every industry EXCEPT healthcare).
  REMOVED for non-healthcare accounts: the "watch this / good news / worth a look" theme flags and the rising/falling chips, and the
  Sentiment Drift alert list and red alert points. The week-by-week numbers, charts and tables are all kept.
  ADDED: a "Summary" panel at the top of the results (dashboard and each company location) with three short paragraphs: What's changing /
  What to look at first / What's going well. Written by an AI model from numbers worked out by the app plus a small sample of recent
  written reviews.
  HEALTHCARE: unchanged. It keeps the statistical flags and drift alerts, no summary is generated, and review text is never sent to an AI
  provider.
  STILL THERE (not removed): the Revenue signals panel and the Trends panel (topic shifts), because you asked about flags and early
  warnings. Tell me if you want those replaced as well.
  WHAT IS SENT TO THE AI: counts and averages (rating, recent vs earlier, each theme's share and rating) and at most 20 recent written
  reviews, each cut to 280 characters, with emails and phone numbers removed, and no reviewer names or links. Nothing is stored by us beyond a
  30-minute in-memory cache of the summary text.
  A summary needs at least 10 written reviews; below that the panel says so instead of guessing.
  COST: about $0.004 per fresh summary (setting RATE_AI_SUMMARY_USD), shown in the run estimate and the usage line. A repeat run on the same
  reviews inside 30 minutes is free. The scheduled company checks do NOT generate summaries, so they cost nothing extra.
  SETUP: uses the same ANTHROPIC_API_KEY as reply drafts (no new package). Optional: AI_SUMMARY_MODEL (defaults to REPLY_MODEL, a small
  fast model). With no key, the panel says the summary is unavailable and the charts still work.
  TERMS OF SERVICE: the data-sharing and accuracy wording was updated (frontend/src/legal/terms.js). Have your lawyer read it; I am not one.
  FRONT PAGE: "early warnings" and "flagged" wording was changed to describe the summary (and says healthcare uses flags instead).
  Files: backend/analysis/ai_summary.py (new), industry_trends.py, pipeline.py, credits/rates.py, main.py, corporate/routes.py;
  frontend AiSummary.vue (new), DashboardView.vue, LocationDetail.vue, IndustryPanel.vue, SentimentDriftChart.vue, utils/credits.js,
  content/industries.js, content/revenue.js, legal/terms.js.

- STRIPE FIX (backend/billing.py): "Manage subscription: No active subscription found" and duplicate customers/subscriptions.
  CAUSE: the profile had no stripe_customer_id (the "checkout completed" webhook missed it; a later "subscription updated" webhook set the
  Pro tier but never saved the customer). Also, every click on Upgrade created a NEW Stripe customer and could create another subscription.
  NOW: (1) Manage subscription looks for a live subscription under your email in Stripe if none is linked, links it, and opens the portal.
  (2) Upgrade reuses your saved Stripe customer, and refuses (with a clear message) if you already have an active subscription.
  (3) The webhook now also handles "subscription created" and saves the customer and subscription ids whenever a subscription is active.
  NOTE: this REPLACES backend/billing.py. If you edited that file yourself, merge by hand. Webhook secret and keys are unchanged.
  Stripe test mode: you can cancel the extra test subscriptions and delete the extra test customers; nothing real is charged.

- "ACCOUNT ALREADY EXISTS, LOG IN INSTEAD" on the sign-up page.
REMOVED BEFORE HOSTING: AI SUMMARIES AND INTERNET MENTIONS (switched off, not deleted)
  - backend/features.py and frontend/src/content/features.js each hold two switches, both now false. Off means not shown, not run,
    not charged, and the mentions search is never called (even if an old browser tab asks for it).
  - With AI summaries off, the earlier behaviour is back for every industry: statistical trend flags and sentiment-drift alerts
    (healthcare was already on them). The front-page wording (industry list, hover text, the two revenue cards) is restored to match.
  - Privacy Policy edited to match: no mention searches, and Anthropic is described as used only for reply drafts (off for healthcare).
  - NOT changed: the Terms still contain conditional wording about web mentions and AI summaries ("if you turn it on", "only if enabled"),
    and the required "Internet mentions are a sample" topic. They are accurate while the features are off, and removing that topic would
    break the Terms' own required-topics check. Ask a lawyer if you want them trimmed.
  - Left in place but unused: AiSummary.vue, MentionsPanel.vue, backend/analysis/ai_summary.py, mentions.py, mentions_client.py. To bring
    a feature back, set its switch to true in BOTH files, and update the Privacy Policy and Terms first.
  - ANTHROPIC_API_KEY is now only for AI-drafted review replies and is optional.

NEW: HOSTING ON RENDER (render.yaml, DEPLOY-RENDER.md, backend/Dockerfile)
  - DEPLOY-RENDER.md is a step-by-step guide (GitHub -> Supabase SQL -> Stripe -> Render blueprint -> env vars -> webhook -> test -> live).
    It replaces the old DEPLOY.md, which is out of date (you can delete DEPLOY.md).
  - render.yaml now creates TWO services: the Docker backend and the static frontend (with the rewrite that lets /login and /dashboard
    work), and lists every secret as "ask me in the dashboard". It adds APIFY_API_TOKEN and ANTHROPIC_API_KEY, which the old file missed.
  - backend/Dockerfile: installs CPU-only PyTorch (the default wheel is multi-GB of GPU code) and listens on Render's $PORT.
  - NOT TESTED on Render. The backend plan is set to 2 GB because of the PyTorch model; that size is my estimate, not a measurement.
  - Order matters: backend first, then VITE_API_BASE_URL on the frontend and a rebuild, then FRONTEND_URL/CORS_ORIGINS, then the Stripe webhook.

NEW: COMPETITORS WORK FROM A GOOGLE MAPS LINK TYPED INTO EITHER BOX (and the "no location" warning is gone)
  - Cause I found: a link typed into the competitor's NAME box left the location box empty, so the row was silently skipped. Now a row
    with one box filled uses it as the location, a link in the name box is the location (the name is read from the link), and
    only rows with both boxes empty are left out. utils/competitors.js (page) and analysis/competitor_input.py (server) do this.
  - If a Maps link still returns nothing, the server retries once with the place id inside the link (0x...:0x...). I believe
    Outscraper accepts that form but have NOT confirmed it against the live service.
  - If a competitor still has nothing, the Competitor panel now says why ("no Google reviews were found in the last N months", or
    "no written reviews"). Competitors compare GOOGLE reviews only; each is a separate pull.

NEW: PEOPLE MUST AGREE TO THE TERMS AND PRIVACY POLICY WHEN THEY CREATE AN ACCOUNT
  - SignupView.vue (edited again, because you asked for this): a required tick box with links to both documents; the Sign up button is
    disabled until it is ticked. The version and time of agreement are also saved on the new account (Supabase user metadata:
    agreed_terms_version, agreed_privacy_date, agreed_at).
  - The Terms of Service now also sit at the bottom of the front page (opens in place, #terms) next to the Privacy Policy, so people can
    read both BEFORE signing up. The sign-up links open them in a new tab.
  - The check at first login still applies and is the server-side record: that screen now shows the Terms AND the Privacy Policy and the tick
    box covers both. TERMS_VERSION is now 2026-10-13, so EVERYONE (including you and existing accounts) is asked to agree once more.
  - Limit: the tick box is enforced in the page. The server still only records the Terms version, not a separate privacy version; changing
    the privacy policy later means bumping TERMS_VERSION to ask people again.
  - Back up SignupView.vue first if you changed it since the last zip:  cp frontend/src/views/SignupView.vue ~/SignupView.backup.vue

NEW: PRIVACY POLICY (a draft - have a lawyer review it)
  - Bottom of the front page: a "Privacy Policy" section that opens in place (no popup; no router change), with a footer link and
    a "Privacy Policy" link in the dashboard footer. Text lives in legal/privacy.js; page in components/PrivacyPolicy.vue.
  - Written from what the app does today: what is collected, that reviews are only held in memory for ~30 minutes (company
    accounts also keep check summaries and scrubbed low-star alert text, no reviewer names), who else handles data (Supabase,
    Stripe, Outscraper, Apify, Anthropic, hosting and email), healthcare accounts getting no AI summaries or replies, deleting
    your account, rights, security, children, changes.
  - YOU MUST DO: set COMPANY_NAME and CONTACT_EMAIL in legal/terms.js (blank ones show highlighted on the page). Also set
    PRIVACY_POLICY there, for example:  our Privacy Policy, linked at the bottom of our front page   (the Terms refer to it).
    NOTE: this zip includes terms.js, which would replace your copy; if you had already filled in COMPANY, copy those values back.
  - Check these against reality: the "hosting and email providers" line (name yours if you want), whether deleting an account removes
    everything you hold for company accounts (I could not read supabase_client.delete_user here, so the policy only promises the
    sign-in removal and cancelling the subscription), and whether you want to add Anthropic's no-training-on-API-data point.
  - I did not add a link on the sign-up page (you asked that SignupView.vue not be edited again).

CHANGED STATISTIC (confirmed with you): "6 review sites" -> "71%"
  - Front page strip now says: "71% of consumers read local reviews on Google, the most-used review site, so your Google reviews
    shape how you are seen online." Source line stays BrightLocal, 2026. I read the 71% on BrightLocal's 2026 survey page
    (it was 83% in 2025). The "so ... shape how you are seen online" part is my wording, not BrightLocal's: they measure where
    people read reviews, not search ranking. Edit it in content/defaultStats.js if you want it plainer.
  - If you have your own frontend/src/content/stats.js, it still wins, so change the "6" entry there yourself.

NEW: NO MORE LONG MAPS LINKS ON SCREEN
  - utils/placeName.js shows the place name from a Google Maps link ("Starbucks"), or "your business" if the link has no name.
    Used in the Competitor panel ("Compares Starbucks against the competitors..." - the "(your account's business)" aside is gone),
    the Run Analysis intro and the Negative reviews intro. Text that isn't a link is shown as typed. Nothing is changed in what is
    saved or sent. Short share links (maps.app.goo.gl) carry no name, so those show "your business".

NEW: TONE VS STAR RATING, BY WEEK (and clearer "by week" labels)
  - New chart "Tone vs star rating" (components/ToneVsStarsChart.vue, utils/toneVsStars.js), on the dashboard and each location
    page, under Weekly Themes. One dot per calendar week: average stars (x) against average tone of the written reviews (y,
    -1 to 1), with a dashed straight-line fit across weeks. Weeks with more written reviews get bigger dots and count for
    more in the fit. It states the correlation (r) in plain words, and lists weeks where the wording was well below what the
    stars suggest. Needs at least 6 weeks with written reviews, otherwise it says so.
  - It says "not proof that one causes the other". Stars use every review that week; tone uses written reviews only.
  - A "BY WEEK" badge now sits on the Sentiment Drift, Weekly Themes and Tone vs stars charts, and their x axes read
    "Week starting (Monday)". The Wait-Time heatmap is by day and hour, so it has no badge.
  - The fit maths was tested here (perfect line, too few weeks, no variation, empty weeks). The chart itself has NOT been seen
    in a browser: the line is drawn as a second scatter series, so check it renders.

RETAIL IS NOW BUILT (one retail type: any store)
  - backend/analysis/industries.py: Retail is available, with 8 themes (stock, checkout lines, returns, price, staff help,
    product quality, store layout and cleanliness, online orders and pickup) and 4 headline numbers. Yelp is recommended;
    DoorDash, Uber Eats and Grubhub are optional; OpenTable is hidden. Those delivery-app links work on any store page the
    app lists, but I have NOT tested them on a non-restaurant store.
  - frontend/src/content/industries.js: Retail mirrors the backend exactly (checked by comparing the two). stats.js is not touched.
  - The theme word lists are my own starting set. They are not tuned on real store reviews, so expect to adjust them.

"NOT AVAILABLE" REVIEW SITES, PER INDUSTRY (no link boxes for sites we cannot pull)
  - New: content/platformNotes.js and components/UnavailablePlatforms.vue, shown on the front page's Get started card and in
    first-time setup and "Your pages". Only Yelp, OpenTable, DoorDash, Uber Eats and Grubhub (plus Google and internet
    mentions) get link boxes.
  - Restaurants: Tripadvisor, Facebook, Resy.   Clinics: Healthgrades, Vitals, RateMDs, Facebook, Better Business Bureau.
    Other: Facebook, BBB, Trustpilot.   Retail: Facebook, Amazon, Trustpilot, BBB.
  - Wording is deliberately two-tiered. I read the terms for Tripadvisor (bars robots/scrapers), Meta (bars automated
    collection), Amazon (restricts data mining/robots; I saw this as a fragment) and BBB (personal, non-commercial use only,
    no compiling its data), so those say "its terms ...". I did NOT verify Trustpilot, Healthgrades, Vitals, RateMDs or Resy,
    so they only say "no approved data source yet". Have a lawyer confirm before you rely on any of this.

  This zip now includes frontend/src/views/SignupView.vue (the same page as before plus the notice), frontend/src/utils/accountExists.js
  (the check) and LoginView.vue (pre-fills the email from /login?email=...). Nothing else to run.
  Supabase does not say "this email exists" when "Confirm email" is on: it returns a success whose user has an EMPTY identities list.
  accountExists.js recognises both that and the "User already registered" error.
  Privacy trade-off: this tells anyone who types an email whether it has an account. That is what you asked for; it is also what
  Supabase hides by default. If that matters later, show a neutral message ("Check your email, or log in if you already have an account").

NOT TESTED IN A BROWSER: I could not run the page here. The files were checked for balanced markup and unchanged wording,
so please look at the front page after rebuilding and tell me what to adjust.

EARLIER (v29), unchanged:

1) NEW HERO: "Uncover where revenue may be slipping away", under the line "Review intelligence for restaurants, healthcare
   practices and more". It names the patterns the product reads for (waits at particular hours, a complaint that keeps
   coming back, a rating that is quietly drifting) and ends with: "Revenue figures are estimates from review patterns, not
   measurements of your sales." No figures, no promises.
2) NEW SECTION "Where revenue may be slipping away", after the statistics. Six patterns, each with "We look at", "You see"
   and which plan has it:
      Waits at particular hours (Pro)                 A complaint that keeps coming back (Pro)
      A rating that is quietly drifting (Free)        A location falling behind (Pro and Enterprise)
      Negative reviews nobody followed up on (Pro)    One platform telling a different story (Pro)
   Only the wait-time heatmap is described as having a dollar figure, because it is the only part of the product that does.
   The nav has a new "Revenue" link.
3) TWO EARLIER CLAIMS CORRECTED. The industry list said revenue signals come "with the estimated revenue at stake", and the
   leadership card said "revenue estimates in plain English". Neither was accurate: only the wait-time heatmap has dollar
   figures; the Revenue signals panel ranks what to act on but does not price it. They now say so.

HOW THE PRODUCT'S REVENUE FIGURE WORKS (for your reference; unchanged)
  For each day/hour slot where good reviews dropped and wait language appears: estimated shortfall in reviews x 20
  customers per review (an assumption) x your average order value. The app reads reviews, not sales, so it is an estimate.
