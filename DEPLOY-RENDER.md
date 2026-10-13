# Hosting Review Insights on Render

This replaces the old `DEPLOY.md` (which predates the Anthropic and Apify keys, the new SQL and the scheduler). Plan on about an hour the first time.

**What you end up with:** two things on Render, both from one GitHub repo.
1. `review-insights-backend`: the API (Docker). This is the part that costs money to run.
2. `review-insights-frontend`: the website (static files).

Supabase (database and sign-in) and Stripe (payments) stay where they are. Nothing here has been run on Render by me, so follow the checks at the end of each step and tell me what you see if one fails.

---

## 0. Before you start

- A GitHub account, and a Render account (render.com, sign in with GitHub).
- Keys you already have from local use: Supabase (URL, anon key, service-role key, JWT secret), Outscraper, Apify, Anthropic, Stripe.
- **Use test keys first.** Stripe test keys, a test price, a test webhook. Switch to live only after step 9 passes.
- **Rotate the Outscraper key** that was hard-coded in the old `dashboard.py`, since it has been in a file. Get a new one at outscraper.com and use only the new one.
- Do **not** commit `backend/.env` or `frontend/.env`. The repo's `.gitignore` already skips them. Check with `git status` before you push.

## 1. Put the project on GitHub

From the project folder on your Mac (the one that holds `backend/`, `frontend/` and `render.yaml`):

```bash
git status                # backend/.env and frontend/.env must NOT be listed
git add .
git commit -m "Prepare for Render"
git remote add origin https://github.com/<you>/review-insights.git   # create the empty repo on github.com first
git push -u origin main
```

If `git status` lists a `.env` file, stop and run `git rm --cached backend/.env frontend/.env` first.

## 2. Supabase (one time)

1. SQL Editor: paste and run `backend/supabase/schema.sql`, then paste and run `backend/supabase/corporate.sql` (all of it). Running them again later is safe.
2. Authentication -> Providers -> Email: decide on "Confirm email". On means people must click an email link before logging in (recommended for a real launch).
3. Authentication -> URL Configuration: set **Site URL** and add a **Redirect URL** for your final website address (`https://your-site.onrender.com` for now, your own domain later). If this is wrong, confirmation links and sign-in redirects fail.
4. Project Settings -> API: note the Project URL, the `anon` key, the `service_role` key and the JWT secret.

## 3. Stripe (test mode)

1. Product "Pro", recurring $49 / month. Copy its **Price ID** (`price_...`).
2. Settings -> Billing -> **Customer portal**: activate it. Without this, "Manage subscription" shows an error. (Test and live modes are set up separately.)
3. Copy the **secret key** (`sk_test_...`).
4. The webhook is created in step 8, once the backend has an address.

Keep every Stripe value in the same mode. A test secret key with a live price ID (or the reverse) is the cause of "No active subscription found".

## 4. Create the services on Render

1. Render dashboard -> **New** -> **Blueprint** -> choose your repo. Render reads `render.yaml` and proposes two services.
2. It asks for every value marked `sync: false`. Fill these now:

| Name | Where it comes from |
|---|---|
| `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET` | Supabase, step 2 |
| `OUTSCRAPER_API_KEY`, `APIFY_API_TOKEN` | Your accounts |
| `ANTHROPIC_API_KEY` | Optional. Only used for AI-drafted review replies; without it the app falls back to template replies |
| `STRIPE_SECRET_KEY`, `STRIPE_PRICE_ID_PRO` | Stripe, step 3 |
| `STRIPE_WEBHOOK_SECRET` | Leave blank for now (step 8) |
| `CORS_ORIGINS`, `FRONTEND_URL` | Leave blank for now (step 7) |
| `SMTP_*` | Optional. Blank means alert emails are only written to the log |
| `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` | Supabase (the anon key is the public one, never the service-role key) |
| `VITE_API_BASE_URL` | Leave blank for now (step 6) |

3. Click **Apply**. The backend takes a while to build the first time, because it downloads PyTorch and the review-theme model into the image. Do not worry about the frontend failing or looking broken yet.

**Memory:** the backend runs a PyTorch model, so I set it to the 2 GB "standard" plan in `render.yaml`. I have not measured the real memory use. If the service restarts or shows "out of memory" in its logs, move up a size. Check Render's pricing page for the current sizes and prices.

## 5. Check the backend

When the backend shows **Live**, open `https://<your-backend>.onrender.com/api/health`. You should see a small OK response. If the deploy failed, open its **Logs** and send me the last 30 lines.

## 6. Tell the frontend where the backend is

Frontend service -> **Environment** -> set `VITE_API_BASE_URL` to the backend address, `https://<your-backend>.onrender.com`, with no slash on the end. Then **Manual Deploy** -> **Deploy latest commit**. These values are baked in when the site is built, so they only take effect after a rebuild.

## 7. Tell the backend where the website is

Backend service -> **Environment**:

- `FRONTEND_URL` = `https://<your-frontend>.onrender.com`
- `CORS_ORIGINS` = the same address. For several, separate with commas and **no spaces**. No trailing slash on any of them.

Save. The backend restarts by itself. (If CORS is wrong you will see "blocked by CORS policy" in the browser, and nothing loads.) `FRONTEND_URL` is also where Stripe sends people back after paying, so it must be the real https address, not localhost.

## 8. Stripe webhook

1. Stripe -> Developers -> Webhooks -> **Add endpoint**.
2. URL: `https://<your-backend>.onrender.com/api/billing/webhook`
3. Events: `checkout.session.completed`, `customer.subscription.created`, `customer.subscription.updated`, `customer.subscription.deleted`.
4. Copy the **signing secret** (`whsec_...`) into the backend's `STRIPE_WEBHOOK_SECRET`, save, and let it restart.

Credit-pack purchases do not use the webhook; the app confirms them itself.

## 9. Test it end to end

Open your frontend address and:
1. Sign up (tick the Terms), confirm the email if that is on, log in, and accept the Terms screen.
2. Set your business, run an analysis. The first run is slow while the model warms up.
3. Upgrade with Stripe's test card `4242 4242 4242 4242` (any future date, any CVC). The account should turn Pro, and "Manage subscription" should open Stripe's portal.
4. Add a competitor and run again.
5. Open the front page and check the footer Terms and Privacy Policy.

## 10. Go live

1. In Stripe, switch to live mode and repeat step 3 and step 8 with **live** values (live key, live price ID, new live webhook and its secret). Put all three in Render and save.
2. Optional custom domain: Render -> the frontend service -> Settings -> Custom Domains, follow the DNS steps. Then update Supabase (Site URL and Redirect URLs) and the backend's `FRONTEND_URL` and `CORS_ORIGINS` to the new address, and the Stripe webhook if you also give the backend its own domain.
3. Fill in `COMPANY_NAME`, `CONTACT_EMAIL` and `PRIVACY_POLICY` in `frontend/src/legal/terms.js`, push, and let the site rebuild.

---

## Things to know

- **Keep the backend on a paid, always-on plan.** Scheduled checks for company accounts run inside the backend process. A free service goes to sleep and they stop. Run only one instance of the backend; with more than one, set `ENABLE_SCHEDULER=false` on all but one.
- **Review caching is in memory** (about 30 minutes). A restart empties it, which only means the next run pulls reviews again.
- **Pushing changes:** `git push` to the connected branch redeploys automatically.
- **Rebuilding the frontend** is needed whenever a `VITE_` value changes.

## If something goes wrong

| What you see | Likely cause |
|---|---|
| Page loads but every action fails; "blocked by CORS" in the browser console | `CORS_ORIGINS` doesn't exactly match the website address (https, no slash, no spaces) |
| Everything points at `localhost` | `VITE_API_BASE_URL` not set, or the frontend wasn't rebuilt after setting it |
| "Could not find the 'industry' column" | `corporate.sql` wasn't run in Supabase |
| "No active subscription found" | Stripe test and live values mixed, or the webhook secret/endpoint is wrong |
| "Manage subscription" errors | Stripe Customer portal not activated in that mode |
| Backend keeps restarting, logs mention memory | Plan too small; move up a size |
| Confirmation email link goes to the wrong place | Supabase Site URL / Redirect URLs |
| Backend build fails near PyTorch | Send me the last lines of the build log |
| First request after a quiet spell is slow | The service was asleep or the model was loading |
