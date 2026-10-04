# Deploying Review Insights

Three external services to set up first, then the backend deploys as a
Docker image on Render (or Railway/Fly, same Dockerfile).

## 1. Supabase

1. Create a project at https://supabase.com.
2. In the SQL Editor, run `backend/supabase/schema.sql` — this creates the
   `profiles` and `analysis_runs` tables, RLS policies, and the trigger that
   auto-creates a profile row on signup.
3. Grab these from **Project Settings → API**:
   - Project URL → `SUPABASE_URL` (backend) / `VITE_SUPABASE_URL` (frontend)
   - `anon` public key → `VITE_SUPABASE_ANON_KEY` (frontend only)
   - `service_role` key → `SUPABASE_SERVICE_ROLE_KEY` (backend only — **never** put this in the frontend)
   - JWT Secret (under **JWT Settings**) → `SUPABASE_JWT_SECRET` (backend)
4. Decide on email confirmation: **Authentication → Providers → Email** —
   toggle "Confirm email" off if you want instant signup during testing.
5. **Enterprise SSO (SAML/OIDC)**: this is a paid Supabase add-on (Team or
   Enterprise Supabase plan) and may need to be turned on for your project
   by contacting Supabase support — it's not available by default on
   Free/Pro Supabase plans. Once enabled:
   - Go to **Authentication → URL Configuration** and make sure your
     frontend's real domain is listed under both **Site URL** and
     **Redirect URLs** (SSO redirects will fail otherwise).
   - When you close a deal with an enterprise customer, get their IdP's
     SAML metadata (a URL or downloaded XML file — ask their IT team) and
     their company's email domain, then run:
     ```bash
     cd backend
     python scripts/manage_sso.py create \
         --domain theircompany.com \
         --metadata-url https://their-idp.example.com/metadata.xml
     ```
   - Anyone who signs in via that domain's SSO is automatically placed on
     the `enterprise` tier (handled by the `handle_new_user` trigger in
     `schema.sql`, which checks Supabase's native `is_sso_user` flag).
   - `python scripts/manage_sso.py list` shows all registered connections;
     `delete --provider-id <id>` removes one if a contract ends.

## 2. Stripe

1. Create a Product ("Pro Plan") with a recurring $49/month Price in the
   Stripe Dashboard. Copy the Price ID → `STRIPE_PRICE_ID_PRO`.
2. Copy your API secret key (test mode to start) → `STRIPE_SECRET_KEY`.
3. Add a webhook endpoint pointing at
   `https://<your-backend-domain>/api/billing/webhook`, subscribed to:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   Copy its signing secret → `STRIPE_WEBHOOK_SECRET`.
4. In test mode, use Stripe's test card `4242 4242 4242 4242` (any future
   expiry/CVC) to run through checkout end to end before going live.

## 3. Outscraper

Get your API key from https://outscraper.com → `OUTSCRAPER_API_KEY`.

## 4. Backend deploy (Render)

`render.yaml` is at the repo root.

1. Push this repo to GitHub.
2. Render dashboard → **New → Blueprint**, point at the repo.
3. Render builds `backend/Dockerfile`. Fill in the env vars marked
   `sync: false` in the dashboard (Supabase keys, Stripe keys, Outscraper key).
4. Once deployed, update `CORS_ORIGINS` and `FRONTEND_URL` to your real
   frontend domain.
5. Update the Stripe webhook URL to point at the live Render URL.

(Railway/Fly work the same way — point them at `backend/Dockerfile` and set
the same env vars. See the previous project's `DEPLOY.md` pattern if you
need platform-specific steps.)

## 5. Frontend deploy

Build via `frontend/Dockerfile` (nginx) or `npm run build` and host the
`dist/` folder anywhere static (Netlify, Vercel, Cloudflare Pages, Render
Static Site). Before building, set:

```
VITE_API_BASE_URL=https://<your-backend-domain>
VITE_SUPABASE_URL=https://your-project-ref.supabase.co
VITE_SUPABASE_ANON_KEY=<your anon key>
```

Vite inlines these at build time, so they must be set before `npm run build`
runs, not after.

## 6. End-to-end check

1. Sign up on the live frontend (free tier).
2. Run the Sentiment Drift chart with a real business.
3. Click Upgrade → complete Stripe test checkout → confirm the webhook
   fires and your Supabase `profiles.tier` flips to `pro` (check the table
   in Supabase directly if the UI doesn't reflect it — helps isolate
   webhook vs. frontend issues).
4. Confirm the two Pro charts unlock.
5. Test **Manage subscription** → cancel → confirm tier reverts to `free`.
