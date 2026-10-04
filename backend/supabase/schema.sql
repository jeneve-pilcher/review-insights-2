-- Run this in your Supabase project's SQL editor (Database → SQL Editor).

create table if not exists public.profiles (
  id uuid references auth.users on delete cascade primary key,
  email text,
  company_name text,
  business_location text,
  tier text not null default 'free' check (tier in ('free', 'pro', 'enterprise')),
  stripe_customer_id text,
  stripe_subscription_id text,
  created_at timestamptz not null default now()
);

-- If you already ran this schema before `business_location` existed, run
-- this one line in the SQL Editor instead of the whole file:
--   alter table public.profiles add column if not exists business_location text;

alter table public.profiles enable row level security;

create policy "Users can view own profile"
  on public.profiles for select
  using (auth.uid() = id);

create policy "Users can update own profile"
  on public.profiles for update
  using (auth.uid() = id);

-- Auto-create a profile row whenever a new user signs up via Supabase Auth.
-- Users who authenticate via enterprise SSO (SAML/OIDC) are automatically
-- placed on the enterprise tier - no manual profile edit needed.
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, email, tier)
  values (
    new.id,
    new.email,
    case when new.is_sso_user then 'enterprise' else 'free' end
  );
  return new;
end;
$$ language plpgsql security definer;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- Optional: table to store saved analysis runs per user (mirrors the
-- FastAPI+Postgres version's run history, now backed by Supabase instead).
create table if not exists public.analysis_runs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users on delete cascade not null,
  chart_type text not null check (chart_type in ('sentiment_drift', 'wait_time_heatmap', 'competitor_share')),
  params jsonb not null,
  result jsonb not null,
  created_at timestamptz not null default now()
);

alter table public.analysis_runs enable row level security;

create policy "Users can view own runs"
  on public.analysis_runs for select
  using (auth.uid() = user_id);

create policy "Users can insert own runs"
  on public.analysis_runs for insert
  with check (auth.uid() = user_id);
