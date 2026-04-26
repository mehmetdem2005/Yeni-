-- Crypto Paper Bot V3 — Supabase/Postgres Schema
-- Run this in Supabase SQL Editor.
-- This schema is for paper-trade and analytics first, not live-money trading.

create extension if not exists pgcrypto;

-- =========================================================
-- Helpers
-- =========================================================

create or replace function set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

-- =========================================================
-- Settings
-- =========================================================

create table if not exists app_settings (
  id uuid primary key default gen_random_uuid(),
  key text not null unique,
  value_json jsonb not null default '{}'::jsonb,
  is_secret boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

drop trigger if exists trg_app_settings_updated_at on app_settings;
create trigger trg_app_settings_updated_at
before update on app_settings
for each row execute function set_updated_at();

-- =========================================================
-- Market Data
-- =========================================================

create table if not exists candles (
  id uuid primary key default gen_random_uuid(),
  symbol text not null,
  timeframe text not null,
  open_time timestamptz not null,
  open numeric not null,
  high numeric not null,
  low numeric not null,
  close numeric not null,
  volume numeric not null,
  source text not null default 'binance',
  created_at timestamptz not null default now(),
  unique(symbol, timeframe, open_time)
);

create index if not exists idx_candles_symbol_tf_time on candles(symbol, timeframe, open_time desc);

-- =========================================================
-- Indicator / Family / Confidence Logs
-- =========================================================

create table if not exists indicator_snapshots (
  id uuid primary key default gen_random_uuid(),
  symbol text not null,
  timeframe text not null,
  candle_time timestamptz,
  indicator_name text not null,
  raw_value numeric,
  normalized_score numeric,
  family text,
  comment text,
  payload_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_indicator_snapshots_symbol_time on indicator_snapshots(symbol, created_at desc);

create table if not exists family_snapshots (
  id uuid primary key default gen_random_uuid(),
  symbol text not null,
  timeframe text not null default '1h',
  family_name text not null,
  family_score numeric not null,
  contribution_hint numeric,
  comment text,
  payload_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_family_snapshots_symbol_time on family_snapshots(symbol, created_at desc);

create table if not exists confidence_snapshots (
  id uuid primary key default gen_random_uuid(),
  symbol text,
  confidence_type text not null, -- trade_confidence | system_confidence | health | proof_strength
  confidence_score numeric not null,
  component_scores_json jsonb not null default '{}'::jsonb,
  weights_json jsonb not null default '{}'::jsonb,
  explanation text,
  created_at timestamptz not null default now()
);

create index if not exists idx_confidence_snapshots_type_time on confidence_snapshots(confidence_type, created_at desc);

-- =========================================================
-- Signals and Paper Trades
-- =========================================================

create table if not exists signal_log (
  id uuid primary key default gen_random_uuid(),
  signal_time timestamptz not null default now(),
  symbol text not null,
  timeframe text not null default '1h',
  indicator_score numeric,
  ai_prediction numeric,
  trade_confidence numeric,
  system_confidence numeric,
  decision text not null,
  explanation text,
  payload_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_signal_log_symbol_time on signal_log(symbol, signal_time desc);

create table if not exists paper_wallets (
  id uuid primary key default gen_random_uuid(),
  name text not null default 'default',
  starting_balance numeric not null default 10000,
  cash numeric not null default 10000,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(name)
);

drop trigger if exists trg_paper_wallets_updated_at on paper_wallets;
create trigger trg_paper_wallets_updated_at
before update on paper_wallets
for each row execute function set_updated_at();

insert into paper_wallets(name, starting_balance, cash)
values ('default', 10000, 10000)
on conflict (name) do nothing;

create table if not exists paper_positions (
  id uuid primary key default gen_random_uuid(),
  wallet_name text not null default 'default',
  symbol text not null,
  status text not null, -- OPEN | CLOSED
  opened_at timestamptz not null default now(),
  closed_at timestamptz,
  entry_price numeric not null,
  close_price numeric,
  qty numeric not null,
  notional numeric not null,
  stop_loss numeric not null,
  take_profit numeric not null,
  pnl numeric,
  reason text,
  decision_payload_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

drop trigger if exists trg_paper_positions_updated_at on paper_positions;
create trigger trg_paper_positions_updated_at
before update on paper_positions
for each row execute function set_updated_at();

create index if not exists idx_paper_positions_status on paper_positions(status, opened_at desc);
create index if not exists idx_paper_positions_symbol on paper_positions(symbol, opened_at desc);

create table if not exists equity_points (
  id uuid primary key default gen_random_uuid(),
  wallet_name text not null default 'default',
  created_at timestamptz not null default now(),
  equity numeric not null,
  cash numeric not null,
  open_value numeric not null default 0,
  realized_pnl numeric not null default 0
);

create index if not exists idx_equity_points_time on equity_points(wallet_name, created_at desc);

-- =========================================================
-- Backtest / Reports
-- =========================================================

create table if not exists backtest_runs (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  status text not null default 'PENDING',
  config_json jsonb not null default '{}'::jsonb,
  metrics_json jsonb not null default '{}'::jsonb,
  started_at timestamptz,
  finished_at timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists backtest_trades (
  id uuid primary key default gen_random_uuid(),
  run_id uuid references backtest_runs(id) on delete cascade,
  symbol text not null,
  entry_time timestamptz not null,
  exit_time timestamptz,
  entry_price numeric not null,
  exit_price numeric,
  qty numeric,
  pnl numeric,
  reason text,
  payload_json jsonb not null default '{}'::jsonb
);

-- =========================================================
-- News / AI Commentary / Assistant
-- =========================================================

create table if not exists news_items (
  id uuid primary key default gen_random_uuid(),
  source text not null,
  title text not null,
  link text,
  published_at timestamptz,
  summary text,
  sentiment text,
  sentiment_score numeric,
  impact_score numeric,
  related_symbols text[] not null default '{}',
  ai_comment text,
  payload_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique(source, title)
);

create index if not exists idx_news_items_published on news_items(published_at desc);

create table if not exists ai_commentary (
  id uuid primary key default gen_random_uuid(),
  commentary_type text not null, -- homepage | news | trade | assistant
  content text not null,
  model text,
  provider text,
  context_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_ai_commentary_type_time on ai_commentary(commentary_type, created_at desc);

create table if not exists assistant_messages (
  id uuid primary key default gen_random_uuid(),
  role text not null, -- user | assistant | system
  content text not null,
  provider text,
  model text,
  context_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

-- =========================================================
-- Whale / Order Flow
-- =========================================================

create table if not exists whale_events (
  id uuid primary key default gen_random_uuid(),
  symbol text not null,
  event_type text not null, -- wall | imbalance | big_trade | sweep | volume_spike
  side text, -- buy | sell | both
  price numeric,
  qty numeric,
  notional numeric,
  score numeric,
  explanation text,
  payload_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_whale_events_symbol_time on whale_events(symbol, created_at desc);

-- =========================================================
-- Logs
-- =========================================================

create table if not exists event_logs (
  id uuid primary key default gen_random_uuid(),
  channel text not null default 'system',
  level text not null default 'INFO',
  message text not null,
  user_explanation text,
  payload_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_event_logs_channel_time on event_logs(channel, created_at desc);

-- =========================================================
-- Security baseline
-- =========================================================

-- RLS should be enabled before public frontend access.
-- For first private/admin deployment, use service role only from backend.

alter table app_settings enable row level security;
alter table candles enable row level security;
alter table indicator_snapshots enable row level security;
alter table family_snapshots enable row level security;
alter table confidence_snapshots enable row level security;
alter table signal_log enable row level security;
alter table paper_wallets enable row level security;
alter table paper_positions enable row level security;
alter table equity_points enable row level security;
alter table backtest_runs enable row level security;
alter table backtest_trades enable row level security;
alter table news_items enable row level security;
alter table ai_commentary enable row level security;
alter table assistant_messages enable row level security;
alter table whale_events enable row level security;
alter table event_logs enable row level security;
