Review Insights - ALL updates, v4 (adds Terms of Service)
=========================================================
Adds a Terms of Service (with a "Before you rely on it" section), a link to it in the
dashboard footer, and a one-time "agree to continue" step that records which version each
person agreed to and when. This zip holds the FINAL version of every file changed by all
updates so far. Apply it ONCE, whether or not you applied earlier zips.

It does NOT include .env files, Dockerfiles, docker-compose.yml, .gitignore,
requirements.txt or package.json. No new packages are needed.

1) From your project root (the folder containing backend/ and frontend/):

       unzip -o ~/Downloads/review-insights-all-updates-v4.zip

   Use the terminal command. Do NOT drag folders in Finder (its "Replace" deletes files
   this zip doesn't contain).

2) In Supabase -> SQL Editor, run ONCE (paste the WHOLE file; it is safe to run twice):

       alter table public.profiles add column if not exists yelp_url text;

       -- then open backend/supabase/corporate.sql, copy ALL of it, paste it, Run.
       -- It now also adds terms_version / terms_accepted_at to profiles.

   RUN THIS BEFORE STEP 4. Until the terms columns exist, people cannot record their
   agreement and will be stuck on the "agree to continue" screen.

3) *** FILL IN YOUR COMPANY DETAILS ***  (frontend/src/legal/terms.js, the COMPANY block)

       COMPANY_NAME, CONTACT_EMAIL, GOVERNING_LAW, REFUND_POLICY, PRIVACY_POLICY

   Anything left blank is shown highlighted in yellow inside the document so it can't be
   missed. Do not launch with yellow text showing.

4) Rebuild:

       docker compose down
       docker compose up --build

IMPORTANT
- The Terms are a starting draft, NOT legal advice. Have a lawyer review them (especially
  sections 5, 10, 11 and 14) before you rely on them.
- You also need a PRIVACY POLICY. The terms point to it, and you handle review text and
  personal data. This zip does not include one.
- Change TERMS_VERSION in terms.js whenever the meaning of the terms changes: everyone is
  then asked to agree again.
- The terms are shown on the dashboard. Your landing and signup pages are not part of this
  zip, so add a link to the terms there too (people should be able to read them before
  signing up).
- To turn off the agree-to-continue step, set REQUIRE_ACCEPTANCE = false in terms.js.
