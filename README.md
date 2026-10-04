# Review Insights

A tiered SaaS dashboard built on Outscraper review data:

- **Free ($0):** Sentiment Drift Matrix (Chart 1)
- **Pro ($49/mo):** all three charts, including Wait-Time Revenue Heatmap
  and Competitor Semantic Share Matrix
- **Enterprise (custom):** everything in Pro + a contact-sales flow + optional
  SAML/OIDC SSO (customers log in via their own company IdP; anyone who
  authenticates via SSO is automatically placed on the enterprise tier)

## Stack

- **Backend:** FastAPI. Verifies Supabase-issued JWTs, gates endpoints by
  subscription tier, fetches/analyzes Outscraper reviews (VADER sentiment +
  a local zero-shot model for theme classification — no per-tenant API key
  needed), and handles Stripe checkout + webhooks.
- **Auth & DB:** Supabase (Postgres + Auth). `profiles.tier` is the source
  of truth for what a user can access; Stripe webhooks keep it in sync.
- **Frontend:** Vue 3 + Vite + vue-router. Landing/pricing page, Supabase
  auth, a dashboard with three chart components (Chart.js + custom
  HTML/CSS for the heatmap grid).
- **Payments:** Stripe Checkout (subscription) + Billing Portal (self-serve
  cancel/manage).

## The three charts

1. **Sentiment Drift Matrix** — weekly volume of your top-3 dominant star
   tiers plotted against a rolling average rating on a second axis, with
   automatic alerts when the #1 tier drops while #2/#3 rise alongside
   "used to be" / "formula change" style language.
2. **Wait-Time Revenue Heatmap** — day-of-week × hour-of-day grid showing
   the proportional mix of your top-3 tiers per time slot, plus a heuristic
   dollar estimate of revenue drag during degraded windows (based on your
   average order value and an assumed reviews-to-customers ratio — **not**
   a certified financial figure).
3. **Competitor Semantic Share Matrix** — for your business and up to 5
   competitors, breaks down what's driving each of their top-3 dominant
   tiers by theme (Product Quality, Pricing, Weekend Communication, Staff
   Behavior), plus a lightweight keyword/topic signal per tier (word
   frequency, not full topic modeling) so you can see exactly where a
   competitor is vulnerable.

## Other features

- **Unified analysis form** — one shared "Run Analysis" button loads the
  Sentiment Drift chart and (on Pro/Enterprise) the Wait-Time heatmap
  together for a given business, instead of running each separately.
- **Negative Review Alerts (Pro/Enterprise)** — surfaces recent 1-2★
  reviews with author names removed and review text run through best-effort
  PII redaction (emails, phone numbers, order numbers). New negative
  reviews from the last 24 hours also trigger an email alert (via SMTP,
  configurable in `.env` — logs to console instead if not configured) so a
  manager can respond quickly.
- **Forgot / reset password** — standard Supabase-backed flow, linked from
  both the login screen and the dashboard top bar.
- **Enterprise SSO** — see the dedicated section below.

## Setup

See [`DEPLOY.md`](./DEPLOY.md) for the full Supabase/Stripe/Outscraper
setup and Render deployment steps. Quick local version once those three
services are configured:

```bash
# Backend
cd backend
cp .env.example .env   # fill in Supabase/Stripe/Outscraper values
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
cp .env.example .env   # fill in VITE_* values
npm install
npm run dev
```

Or via Docker, once your `backend/.env` is filled in and
`VITE_SUPABASE_URL` / `VITE_SUPABASE_ANON_KEY` are exported in your shell:

```bash
docker compose up --build
```

## Known limitations / next steps

- The revenue-drag dollar figure and the drift/wait-time keyword triggers
  are heuristics meant to surface a signal worth investigating — they are
  not validated financial or statistical models. Treat them as a starting
  point for a manual look, not a number to report upward as fact.
- The enterprise contact form only logs to stdout right now — wire it up to
  an email provider or CRM before relying on it in production.
- No background jobs: `/api/analyze/*` endpoints scrape + classify
  synchronously. Fine for a single business at a time; consider a queue if
  you expect concurrent heavy usage (e.g. the competitor chart hitting 6
  businesses at once).
- Chart 2/3 visuals are built with Chart.js + custom CSS grids as the
  closest practical equivalents to the requested exotic chart types — not
  a specialized visualization library. Good enough to ship and iterate on,
  but expect to want visual polish over time.
