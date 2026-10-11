-- Corporate (multi-location) tables. Run once in Supabase -> SQL Editor.
-- Only the backend (service role) touches these tables, so row-level security is
-- switched on with no policies: nobody can read them through the public API.

create table if not exists public.organizations (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  owner_id uuid not null,
  monthly_budget_reviews integer not null default 5000,
  created_at timestamptz not null default now()
);

create table if not exists public.org_members (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  user_id uuid,
  email text not null,
  role text not null check (role in ('owner','admin','manager','viewer')),
  created_at timestamptz not null default now(),
  unique (org_id, email)
);
create index if not exists org_members_user_idx on public.org_members (user_id);
create index if not exists org_members_email_idx on public.org_members (email);

create table if not exists public.locations (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  name text not null,
  brand text,
  region text,
  google_query text not null,
  yelp_url text,
  manager_email text,
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);
create index if not exists locations_org_idx on public.locations (org_id);

create table if not exists public.location_snapshots (
  id uuid primary key default gen_random_uuid(),
  location_id uuid not null references public.locations(id) on delete cascade,
  run_at timestamptz not null default now(),
  months integer,
  reviews_total integer,
  reviews_google integer,
  reviews_yelp integer,
  reviews_text integer,
  avg_rating numeric,
  avg_rating_google numeric,
  avg_rating_yelp numeric,
  prev_avg_rating numeric,
  low_star_pct numeric,
  recent_per_week numeric,
  earlier_per_week numeric,
  days_since_last integer,
  avg_sentiment numeric,
  wait_share_pct numeric,
  negative_count integer,
  rising_topics jsonb not null default '[]'::jsonb,
  signals jsonb not null default '[]'::jsonb,
  notes jsonb not null default '[]'::jsonb,
  fresh_reviews integer not null default 0
);
create index if not exists snapshots_loc_idx on public.location_snapshots (location_id, run_at desc);

create table if not exists public.review_alerts (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  location_id uuid not null references public.locations(id) on delete cascade,
  review_key text not null,
  source text,
  rating integer,
  review_date text,
  text text,
  has_text boolean not null default true,
  status text not null default 'open' check (status in ('open','acknowledged','resolved')),
  assigned_to text,
  note text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (location_id, review_key)
);
create index if not exists alerts_org_idx on public.review_alerts (org_id, status);

create table if not exists public.audit_log (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  user_id uuid,
  user_email text,
  action text not null,
  target text,
  detail jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists audit_org_idx on public.audit_log (org_id, created_at desc);

create table if not exists public.usage_events (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  location_id uuid,
  reviews integer not null,
  kind text,
  created_at timestamptz not null default now()
);
create index if not exists usage_org_idx on public.usage_events (org_id, created_at);

create table if not exists public.review_replies (
  id uuid primary key default gen_random_uuid(),
  scope text not null,
  review_key text not null,
  source text,
  rating integer,
  review_date text,
  reply_text text not null default '',
  status text not null default 'draft' check (status in ('draft','sent')),
  updated_by text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (scope, review_key)
);
create index if not exists replies_scope_idx on public.review_replies (scope);

alter table public.organizations enable row level security;
alter table public.org_members enable row level security;
alter table public.locations enable row level security;
alter table public.location_snapshots enable row level security;
alter table public.review_alerts enable row level security;
alter table public.audit_log enable row level security;
alter table public.usage_events enable row level security;
alter table public.review_replies enable row level security;

-- Terms of Service acceptance (which version each person agreed to, and when).
alter table public.profiles add column if not exists terms_version text;
alter table public.profiles add column if not exists terms_accepted_at timestamptz;

-- OpenTable pages (single accounts keep them on the profile; companies per location).
alter table public.profiles add column if not exists opentable_url text;
alter table public.locations add column if not exists opentable_url text;

-- ---------------------------------------------------------------------------------------------
-- Usage credits: prepaid balances, a ledger of every change, and Stripe credit purchases.
-- scope = 'user:<id>' for a single account or 'org:<id>' for a company.
create table if not exists public.credit_wallets (
  scope text primary key,
  balance_usd numeric not null default 0,
  updated_at timestamptz not null default now()
);

create table if not exists public.credit_ledger (
  id uuid primary key default gen_random_uuid(),
  scope text not null,
  kind text not null check (kind in ('purchase','usage','adjustment','refund')),
  amount_usd numeric not null,          -- change to the credit balance (negative = spent)
  cost_usd numeric not null default 0,  -- the API cost this entry covers
  allowance_usd numeric not null default 0, -- part of that cost paid from the monthly plan allowance
  description text,
  ref text,
  balance_after numeric not null,
  created_at timestamptz not null default now()
);
create index if not exists ledger_scope_idx on public.credit_ledger (scope, created_at desc);
-- A purchase (Stripe session) can only ever be credited once.
create unique index if not exists ledger_purchase_ref_idx on public.credit_ledger (ref) where kind = 'purchase';

create table if not exists public.credit_purchases (
  id uuid primary key default gen_random_uuid(),
  session_id text not null unique,
  scope text not null,
  user_id text,
  user_email text,
  price_usd numeric not null,
  credit_usd numeric not null,
  status text not null default 'pending' check (status in ('pending','paid')),
  created_at timestamptz not null default now(),
  paid_at timestamptz
);
create index if not exists purchases_scope_idx on public.credit_purchases (scope, status);

-- Atomically applies a credit change: locks the wallet, never lets spending go below the floor,
-- writes the ledger row, and returns the new balance. A repeated purchase ref fails (23505).
create or replace function public.credit_apply(
  p_scope text, p_amount numeric, p_kind text, p_cost numeric, p_allowance numeric,
  p_description text, p_ref text, p_floor numeric
) returns numeric language plpgsql as $$
declare
  old_balance numeric;
  new_balance numeric;
begin
  insert into public.credit_wallets (scope, balance_usd) values (p_scope, 0) on conflict (scope) do nothing;
  select balance_usd into old_balance from public.credit_wallets where scope = p_scope for update;
  if p_amount < 0 then
    new_balance := least(old_balance, greatest(old_balance + p_amount, p_floor));
  else
    new_balance := old_balance + p_amount;
  end if;
  insert into public.credit_ledger (scope, kind, amount_usd, cost_usd, allowance_usd, description, ref, balance_after)
    values (p_scope, p_kind, new_balance - old_balance, p_cost, p_allowance, p_description, p_ref, new_balance);
  update public.credit_wallets set balance_usd = new_balance, updated_at = now() where scope = p_scope;
  return new_balance;
end $$;

alter table public.credit_wallets enable row level security;
alter table public.credit_ledger enable row level security;
alter table public.credit_purchases enable row level security;

-- DoorDash, Uber Eats and Grubhub pages.
alter table public.profiles add column if not exists doordash_url text;
alter table public.profiles add column if not exists ubereats_url text;
alter table public.profiles add column if not exists grubhub_url text;
alter table public.locations add column if not exists doordash_url text;
alter table public.locations add column if not exists ubereats_url text;
alter table public.locations add column if not exists grubhub_url text;

-- Monthly spending limit for a company, in dollars of credit. Empty = no limit. (Replaces the old review-count budget.)
alter table public.organizations add column if not exists monthly_budget_usd numeric;

-- A monthly spending limit (dollars of API usage) for individual accounts. Empty = no limit.
alter table public.profiles add column if not exists monthly_limit_usd numeric;

-- White-label branding (set by an administrator when a deal is signed) and industry packs.
alter table public.organizations add column if not exists white_label boolean not null default false;
alter table public.organizations add column if not exists brand_name text;
alter table public.organizations add column if not exists brand_primary text;
alter table public.organizations add column if not exists brand_accent text;
alter table public.organizations add column if not exists brand_logo_url text;
alter table public.organizations add column if not exists sso_domain text;
alter table public.organizations add column if not exists industry text;
alter table public.profiles add column if not exists industry text;
create unique index if not exists organizations_sso_domain_idx on public.organizations (lower(sso_domain)) where sso_domain is not null;

-- A compact industry summary saved with every check, so company pages can compare locations by industry theme.
alter table public.location_snapshots add column if not exists industry jsonb;

-- Healthcare: provider-level (individual doctor) data is OFF unless an administrator turns it on for a company.
alter table public.organizations add column if not exists provider_data_enabled boolean not null default false;
alter table public.locations add column if not exists provider_links jsonb not null default '[]'::jsonb;
alter table public.location_snapshots add column if not exists providers jsonb;
alter table public.location_snapshots add column if not exists providers_checked_at timestamptz;
