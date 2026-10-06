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
