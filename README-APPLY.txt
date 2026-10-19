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
NEW: COMPANIES ARE CHARGED BY LOCATION THROUGH STRIPE (contracts adjust the terms) - RUN THE SQL
  1. Run the updated backend/supabase/corporate.sql in Supabase (organizations get stripe_customer_id, stripe_subscription_id, billing_status;
     new billing_contracts table). Set ADMIN_EMAILS=you@yourcompany.com on the backend for the operator Billing section.
  2. How a company is charged: the owner opens the Billing tab -> Set up billing -> Stripe Checkout. It is ONE monthly subscription per company.
     The price is a VOLUME tiered price (every location pays the tier rate for the company's size), created in Stripe automatically from the tier table (no Stripe dashboard setup, no new price ID);
     the quantity is the number of locations, set by the server from the database. Adding, importing or deleting locations updates the quantity in
     Stripe and the difference is prorated on the next invoice. Stripe's own tier maths produces the charge, and the same table drives the
     public calculator, so they agree. Owners manage the card / cancel from "Manage billing" (Stripe's portal).
  3. Billing must be set up BEFORE adding locations (402 "Set up billing first"). REQUIRE_ORG_BILLING=false turns that rule off for testing;
     logins in ADMIN_EMAILS skip it. Companies that already had locations are blocked from adding more until they set up billing.
  4. Tiers (placeholders): ALL locations pay the rate for the company's size: 1-249 $49, 250-499 $39, 500-999 $29, 1,000+ $19. Override with
     LOCATION_PRICE_TIERS=1:49,250:39,500:29,1000:19. 600 locations = 600 x $29 = $17,400 / month ($29 each). 1,000 = $19,000 ($19 each).
     NO CLIFFS: nobody is billed more than they would be at the start of a bigger tier (a company is billed "as if" it had that many
     locations when that costs less). Result: 199-250 locations all cost $9,750; 400-500 cost $14,500; 656-1,000 cost $19,000 (flat); then $19 each
     above 1,000. Those flat stretches follow from your prices; change the prices if you do not want them. The Billing tab shows the locations billed.
     Changing the table makes a NEW Stripe price (Stripe volume mode): companies already subscribed keep the price they signed up on. If you
     subscribed any test company under the earlier graduated price, cancel it and set billing up again. Tiers are public on the landing
     page (under Plans) and on the Enterprise contact page.
  5. Contracts (operator section, per email domain): a minimum number of locations that is billed even when fewer are used, optional custom tiers,
     dates, notes. They are applied when the customer FIRST sets up billing (the Stripe price and quantity come from them). Changing a contract
     later does NOT change an existing subscription's price (the quantity minimum is still enforced on every sync). To change a live customer's
     price, change it in the Stripe dashboard or cancel and re-subscribe.
  6. A person whose email domain has a contract can create a company without buying Pro. gmail/outlook etc. cannot have contracts.
  7. Webhook: the same Stripe webhook (checkout.session.completed + customer.subscription.created/updated/deleted) records each company's billing
     status. Company subscriptions are recognised by org_id in the metadata; Pro subscriptions are unchanged.
  8. NOT TESTED against Stripe or in a browser. Tested here: price/quantity logic and the Stripe calls using a stand-in for Stripe.
     Test-mode run: create a company, Set up billing with card 4242 4242 4242 4242, add a location, and look in Stripe for the new quantity.
  9. NOT built: lockout when payment fails or the subscription is cancelled (status is recorded; adding locations is blocked, existing locations keep
     working); sales tax; the operator page shows the amount the tiers give, not what Stripe actually charged; if the Stripe quantity update fails it
     is only logged and the next add/delete corrects it; Contact-sales form still only writes to the server log.
 10. If you unzipped an earlier v30, backend/corporate/org_billing.py is replaced by this version. MAX_LOCATIONS_PER_ORG default is 5,000.
     Scheduled checks are paced by MAX_RUNS_PER_TICK (default 10 per 30 min); raise it for big customers.

PRICE TABLE NEVER GOES BLANK ON THE PUBLIC PAGES
  - The tier table + calculator (under Plans on the front page, and on the Enterprise page) now shows the standard prices straight away and
    swaps in the server's table when it answers. Before, it hid itself if the backend could not be reached (for example a sleeping server
    or no backend running locally). If you override LOCATION_PRICE_TIERS, also update STANDARD_TIERS in utils/locationPricing.js.
  - If you do not see it, your LandingView.vue is older than this zip: LandingView.vue must be the one from this zip (it imports LocationPricing).

CONTACT SALES NOW GOES TO YOUR EMAIL (needs SMTP) AND IS SAVED
  - The Enterprise "Contact sales" form emails the request to SALES_EMAIL (default jenevepilcher189@gmail.com; set the env var to change it)
    with the sender's address in the body, and ALSO saves it in a new table, contact_requests: RUN THE UPDATED backend/supabase/corporate.sql.
  - IT ONLY EMAILS IF SMTP IS SET UP: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM on the backend (SendGrid, Postmark, SES,
    or a Gmail app password all work). Without them nothing is emailed: the request is only saved in the table and printed in the server log.
    Look in Supabase -> Table editor -> contact_requests to check. These are the same settings as alert emails.
  - Abuse limits: 5 per sender email per hour and 40 in total per hour; fields are length-capped and cleaned. Edited: main.py, new
    contact_sales.py, EnterpriseContactView.vue (shows the server's message). Tested with stand-ins for email and the database, not for real.

REPLIES: GOOD / BAD REVIEW FILTERS, AND THE FRONT PAGE NO LONGER SAYS "MARKED SENT"
  - Reviews & draft replies (single dashboard and company locations) now has filter buttons right after All: "Bad reviews (1-2 stars)" and
    "Good reviews (4-5 stars)", then Okay (3 stars), Needs a reply, Replied. They work with the existing platform dropdown and show counts.
    Good/bad is decided by the star rating, not by the wording. Edited: utils/replies.js (labels and order only).
  - Front page: the revenue card and the experience-lead role card no longer mention marking replies sent. The in-app "Mark as sent"
    button, the Replied filter and the Terms wording about it are unchanged.

HOSPITALITY IS NOW BUILT (one type: Hotels & lodging)
  - backend/analysis/industries.py: "hospitality" with 8 themes (room cleanliness, check-in and check-out, beds/noise/sleep, staff, location and
    parking, pool/gym/amenities, breakfast and dining, price and fees) and 4 headline numbers. Yelp is recommended; OpenTable and the delivery apps
    are hidden (they do not apply to a place to stay). Reply drafts are on. Starting average booking value is $180: a PLACEHOLDER, edit it.
  - frontend/src/content/industries.js mirrors it (checked by comparing the two); new "Hospitality" group on the front page (orange tint in
    IndustryShowcase.vue). platformNotes.js: Tripadvisor and Facebook (terms bar automated collection) plus Booking.com and Expedia (no approved
    data source yet; I have NOT claimed their terms forbid it) are listed as not available for hotels.
  - The theme word lists are my own starting set, not tuned on real hotel reviews. The "average order value" box is called that for hotels too.
  - Back up LandingView.vue first as usual (this change does not touch it).

NEW: ADD MANY PEOPLE AT ONCE (bulk logins by spreadsheet)
  - Company dashboard -> Team -> "Add many people from a spreadsheet (CSV)". Columns: email (required), role (admin / manager / viewer; blank =
    viewer). Up to 200 per upload. Each valid row is added to the team like the one-at-a-time form. With "Also email each person an
    invitation" ticked, Supabase creates the login and emails a link; the person lands on a "Choose a password" screen (on /login?invited=1),
    then the dashboard (they still accept the Terms there). Anyone who already has a login is just added. Bad rows are listed, not fatal.
  - Backend: corporate/bulk_members.py, route POST /api/org/members/import. Frontend: OrgTeam.vue, LoginView.vue (password screen), api.js.
  - YOU MUST DO, in Supabase: Authentication -> URL Configuration -> add <your frontend address>/login to Redirect URLs. Without it the link
    in the invitation is rejected. Also: Supabase's built-in email sender allows only a few emails an hour; for a real roll-out add your own
    SMTP under Authentication -> SMTP settings (SendGrid, Postmark, SES...). These invitations do NOT use this app's SMTP_* settings.
  - Managers are still tied to locations by the manager email on each location. Importing people does not set that.
  - NOT tested against Supabase or in a browser (the backend row handling was tested with a stand-in for Supabase). Single sign-on
    (Supabase SSO by company domain) already exists on the login page. In bulk add, anyone whose email is on the company's SSO domain is added to the
    team WITHOUT an invitation email (no password); they log in with "Continue with company SSO" and are matched by email on first sign-in.
    The SSO domain is set by you with scripts/set_branding.py (--sso-domain), and the SSO connection itself in Supabase (Authentication ->
    SSO, a paid Supabase feature). Not tested against a real SSO provider.

NEW: MANAGERS SWITCH LOCATIONS ON THE MAIN DASHBOARD
  - A person whose company role is "manager" now lands on the normal dashboard (not the Company page) with a Location dropdown at the top.
    The list is only the locations whose manager_email is their login email (the server already enforces this). Picking one shows that
    location's full dashboard (reviews and replies, language panels, charts). The last pick is remembered in that browser. Over 8 locations
    adds a search box. If they also have their own business set up, "My own business" is an extra option.
  - The Company tab stays available (renamed tab "My locations" for the dashboard side) for alerts/tasks.
  - New: components/LocationSwitcher.vue. Changed: views/DashboardView.vue, components/LocationDetail.vue (embedded prop hides "Back").
  - A manager is matched by email, so each location's manager_email must be the same email they sign up with.
  - NOT tested in a browser (tags checked for balance only). Owners/admins/viewers still use the Company page.

LANDING PAGE NOW SINGLE-BUSINESS ONLY (company page no longer advertised)
  - "Who uses it" has 3 cards (owner/GM, marketing, guest/patient experience), each listing only things the single-business dashboard does,
    with (Pro) where the dashboard locks it. Operations, location-manager and leadership cards are gone. Edited: content/roles.js,
    RolesSection.vue subtitle, LandingView.vue (hero line, Enterprise card), content/industries.js (every-industry list), EnterpriseContactView.vue
    (price table removed from that page; LocationPricing.vue stays in the zip, unused).
  - Task assignment wording is gone from the landing page: the revenue card, experience role and every-industry list say "draft replies to reviews" (not healthcare); industry lists say
    "Negative reviews flagged and tagged". The "A location falling behind" card was removed from the revenue section (content/revenue.js).
  - The landing page no longer promises email alerts (they only send if SMTP_* is set on the backend). Terms/Privacy still mention alert emails
    in cautious wording; the app still sends them when SMTP is configured.
  - Location tier prices are public: a table + calculator under the Plans cards (LandingView.vue) and on the Enterprise contact page;
    Enterprise card says "Volume pricing by location". Prices come from the backend (/api/pricing/locations); if it is unreachable the landing block hides.
  - The app itself is NOT changed: paid users and invited members still see the Company tab and the manager location switcher.
  - Competitors (up to 6) stay on the Pro card. Back up LandingView.vue before unzipping.

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
