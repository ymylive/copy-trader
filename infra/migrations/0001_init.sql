-- Initial schema for Copy Trader
-- Requires: PostgreSQL 16 + TimescaleDB extension

CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─────────────────────────────────────────────────────────────
-- users
CREATE TABLE users (
    id              BIGSERIAL PRIMARY KEY,
    username        TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    email           TEXT,
    phone           TEXT,
    invite_code     TEXT UNIQUE,
    referred_by     BIGINT REFERENCES users(id) ON DELETE SET NULL,
    level           INT NOT NULL DEFAULT 0,
    referral_rate   NUMERIC(5,4) NOT NULL DEFAULT 0.10,
    totp_secret     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────
-- exchange_accounts
CREATE TABLE exchange_accounts (
    id                  BIGSERIAL PRIMARY KEY,
    user_id             BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    alias               TEXT NOT NULL,
    tier                TEXT NOT NULL DEFAULT 'standard',  -- standard / express
    exchange            TEXT NOT NULL,                     -- binance/okx/gate/bitget/hyperliquid
    uid                 TEXT,
    api_key_enc         TEXT,
    api_secret_enc      TEXT,
    passphrase_enc      TEXT,
    leverage_default    INT NOT NULL DEFAULT 10,
    status              TEXT NOT NULL DEFAULT 'inactive',  -- active/inactive/disabled
    egress_ips          TEXT[] NOT NULL DEFAULT '{}',
    activated_at        TIMESTAMPTZ,
    service_expires_at  TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, alias)
);

-- ─────────────────────────────────────────────────────────────
-- subscription_resources
CREATE TABLE subscription_resources (
    id                BIGSERIAL PRIMARY KEY,
    user_id           BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    sku               TEXT NOT NULL,  -- order_slot / follow_slot / lead_role / express_slot
    bound_account_id  BIGINT REFERENCES exchange_accounts(id) ON DELETE SET NULL,
    purchase_time     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at        TIMESTAMPTZ NOT NULL,
    auto_renew        BOOLEAN NOT NULL DEFAULT FALSE,
    coupon_id         BIGINT,
    paid_amount       NUMERIC(20,8) NOT NULL DEFAULT 0
);

-- ─────────────────────────────────────────────────────────────
-- wallet
CREATE TABLE wallet_balances (
    user_id   BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    currency  TEXT NOT NULL DEFAULT 'USDT',
    amount    NUMERIC(20,8) NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, currency)
);

CREATE TABLE wallet_transactions (
    id         BIGSERIAL PRIMARY KEY,
    user_id    BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type       TEXT NOT NULL,  -- deposit / withdraw / consume / refund / referral
    currency   TEXT NOT NULL DEFAULT 'USDT',
    amount     NUMERIC(20,8) NOT NULL,
    ref_sku    TEXT,
    meta       JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX ix_wallet_tx_user ON wallet_transactions(user_id, created_at DESC);

-- ─────────────────────────────────────────────────────────────
-- traders
CREATE TABLE traders (
    id              BIGSERIAL PRIMARY KEY,
    source          TEXT NOT NULL,
    external_id     TEXT NOT NULL,
    display_name    TEXT,
    exchange        TEXT,            -- 该交易员的实际交易所
    meta            JSONB NOT NULL DEFAULT '{}',
    stats           JSONB NOT NULL DEFAULT '{}',
    last_active_at  TIMESTAMPTZ,
    listed          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (source, external_id)
);
CREATE INDEX ix_traders_listed ON traders(listed, last_active_at DESC);

-- ─────────────────────────────────────────────────────────────
-- copy_configs
CREATE TABLE copy_configs (
    id                   BIGSERIAL PRIMARY KEY,
    user_id              BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    exchange_account_id  BIGINT NOT NULL REFERENCES exchange_accounts(id) ON DELETE CASCADE,
    trader_id            BIGINT NOT NULL REFERENCES traders(id) ON DELETE RESTRICT,
    reverse              BOOLEAN NOT NULL DEFAULT FALSE,
    name                 TEXT NOT NULL DEFAULT '配置1',
    money_mode           TEXT NOT NULL DEFAULT 'fixed',         -- fixed/full/compound
    money_param          JSONB NOT NULL DEFAULT '{}',
    multiplier           NUMERIC(8,4) NOT NULL DEFAULT 1,
    initial_strategy     TEXT NOT NULL DEFAULT 'none',          -- none/only_loss/all
    direction_limit      TEXT NOT NULL DEFAULT 'both',          -- both/long_only/short_only
    open_trigger         JSONB NOT NULL DEFAULT '{"kind":"market"}',
    add_trigger          JSONB NOT NULL DEFAULT '{"kind":"market"}',
    tp                   JSONB NOT NULL DEFAULT '{"enabled":false}',
    sl                   JSONB NOT NULL DEFAULT '{"enabled":false}',
    loss_threshold       JSONB NOT NULL DEFAULT '{}',
    safety_cushion       JSONB NOT NULL DEFAULT '{}',
    refill               JSONB NOT NULL DEFAULT '{}',
    symbol_blacklist     TEXT[] NOT NULL DEFAULT '{}',
    symbol_whitelist     TEXT[] NOT NULL DEFAULT '{}',
    notify_channels      TEXT[] NOT NULL DEFAULT '{}',
    notify_types         TEXT[] NOT NULL DEFAULT '{}',
    status               TEXT NOT NULL DEFAULT 'running',       -- running/paused/stopped
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX ix_copy_configs_user_status ON copy_configs(user_id, status);
CREATE INDEX ix_copy_configs_trader ON copy_configs(trader_id, status);

-- ─────────────────────────────────────────────────────────────
-- copy_orders
CREATE TABLE copy_orders (
    id                   BIGSERIAL PRIMARY KEY,
    copy_config_id       BIGINT NOT NULL REFERENCES copy_configs(id) ON DELETE CASCADE,
    exchange_account_id  BIGINT NOT NULL REFERENCES exchange_accounts(id),
    exchange_order_id    TEXT,
    symbol               TEXT NOT NULL,
    side                 TEXT NOT NULL,
    action               TEXT NOT NULL,  -- open/increase/reduce/close
    qty                  NUMERIC(20,8) NOT NULL,
    px                   NUMERIC(20,8),
    status               TEXT NOT NULL DEFAULT 'pending',
    source_event_id      TEXT,
    error                TEXT,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX ix_copy_orders_config ON copy_orders(copy_config_id, created_at DESC);

-- ─────────────────────────────────────────────────────────────
-- positions_snapshots (hypertable)
CREATE TABLE positions_snapshots (
    ts                   TIMESTAMPTZ NOT NULL,
    exchange_account_id  BIGINT NOT NULL,
    symbol               TEXT NOT NULL,
    side                 TEXT NOT NULL,
    qty                  NUMERIC(20,8) NOT NULL,
    entry_px             NUMERIC(20,8),
    lev                  NUMERIC(8,2),
    margin               NUMERIC(20,8),
    unrealized_pnl       NUMERIC(20,8)
);
SELECT create_hypertable('positions_snapshots', 'ts', if_not_exists => TRUE);
CREATE INDEX ix_pos_snap_account_ts ON positions_snapshots(exchange_account_id, ts DESC);

-- ─────────────────────────────────────────────────────────────
-- nav_curve (hypertable)
CREATE TABLE nav_curve (
    ts                   TIMESTAMPTZ NOT NULL,
    exchange_account_id  BIGINT NOT NULL,
    total_balance        NUMERIC(20,8) NOT NULL,
    realized_pnl         NUMERIC(20,8) NOT NULL DEFAULT 0,
    unrealized_pnl       NUMERIC(20,8) NOT NULL DEFAULT 0
);
SELECT create_hypertable('nav_curve', 'ts', if_not_exists => TRUE);
CREATE INDEX ix_nav_account_ts ON nav_curve(exchange_account_id, ts DESC);

-- ─────────────────────────────────────────────────────────────
-- notifications_log
CREATE TABLE notifications_log (
    id        BIGSERIAL PRIMARY KEY,
    user_id   BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    channel   TEXT NOT NULL,
    type      TEXT NOT NULL,
    payload   JSONB NOT NULL DEFAULT '{}',
    status    TEXT NOT NULL DEFAULT 'pending',
    sent_at   TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────
-- login_history
CREATE TABLE login_history (
    id        BIGSERIAL PRIMARY KEY,
    user_id   BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ip        INET,
    geo       TEXT,
    ua        TEXT,
    ts        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX ix_login_hist_user ON login_history(user_id, ts DESC);

-- ─────────────────────────────────────────────────────────────
-- referral_records
CREATE TABLE referral_records (
    id           BIGSERIAL PRIMARY KEY,
    inviter_id   BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    invitee_id   BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    registered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    paid_amount  NUMERIC(20,8) NOT NULL DEFAULT 0,
    commission   NUMERIC(20,8) NOT NULL DEFAULT 0,
    status       TEXT NOT NULL DEFAULT 'pending'
);

-- ─────────────────────────────────────────────────────────────
-- coupons
CREATE TABLE coupons (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT REFERENCES users(id) ON DELETE CASCADE,
    code        TEXT UNIQUE,
    discount    NUMERIC(5,4) NOT NULL,    -- 0.85 = 85折
    sku_scope   TEXT[] NOT NULL DEFAULT '{}',
    expires_at  TIMESTAMPTZ,
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
