"""
SaaS Product Analytics Dataset Generator
Generates a realistic anonymized SaaS dataset modeled on common
e-commerce/subscription business patterns (similar to Kaggle SaaS datasets).
"""

import sqlite3
import random
import csv
import os
from datetime import datetime, timedelta

random.seed(42)

# ── Config ──────────────────────────────────────────────────────────────────
N_USERS          = 5000
START_DATE       = datetime(2023, 1, 1)
END_DATE         = datetime(2024, 6, 30)
DB_PATH          = "data/saas_analytics.db"

CHANNELS         = ["organic_search", "paid_search", "referral", "social", "direct", "email_campaign"]
CHANNEL_WEIGHTS  = [0.30, 0.22, 0.18, 0.12, 0.10, 0.08]

PLANS            = ["free", "starter", "growth", "enterprise"]
PLAN_PRICES      = {"free": 0, "starter": 29, "growth": 99, "enterprise": 349}

COUNTRIES        = ["US", "CA", "UK", "DE", "AU", "FR", "IN", "BR"]
COUNTRY_WEIGHTS  = [0.38, 0.12, 0.11, 0.09, 0.07, 0.06, 0.10, 0.07]

FEATURES         = [
    "dashboard_view", "report_export", "team_invite",
    "api_access", "automation_rule", "integration_connect",
    "custom_field", "bulk_import"
]

# Retention probability by plan (monthly survival)
RETENTION_BY_PLAN = {"free": 0.60, "starter": 0.78, "growth": 0.88, "enterprise": 0.94}

# Feature usage correlates with retention (high-engagement features)
POWER_FEATURES   = {"team_invite", "api_access", "automation_rule", "integration_connect"}

def rand_date(start, end):
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))

def weighted_choice(choices, weights):
    total = sum(weights)
    r = random.uniform(0, total)
    upto = 0
    for c, w in zip(choices, weights):
        upto += w
        if r <= upto:
            return c
    return choices[-1]

# ── Build tables ─────────────────────────────────────────────────────────────
os.makedirs("data", exist_ok=True)
conn = sqlite3.connect(DB_PATH)
cur  = conn.cursor()

cur.executescript("""
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS subscriptions;
DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS funnel_stages;

CREATE TABLE users (
    user_id          INTEGER PRIMARY KEY,
    signup_date      TEXT,
    acquisition_channel TEXT,
    country          TEXT,
    plan             TEXT,
    churned          INTEGER,   -- 1 = churned, 0 = active
    churn_date       TEXT
);

CREATE TABLE subscriptions (
    sub_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id          INTEGER,
    plan             TEXT,
    mrr              REAL,
    start_date       TEXT,
    end_date         TEXT       -- NULL if still active
);

CREATE TABLE events (
    event_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id          INTEGER,
    event_type       TEXT,
    feature          TEXT,
    event_date       TEXT
);

CREATE TABLE funnel_stages (
    user_id          INTEGER PRIMARY KEY,
    signed_up        INTEGER DEFAULT 0,
    activated        INTEGER DEFAULT 0,   -- used any feature within 7 days
    engaged          INTEGER DEFAULT 0,   -- used power feature within 30 days
    converted        INTEGER DEFAULT 0,   -- upgraded from free
    retained_90d     INTEGER DEFAULT 0    -- still active at 90 days
);
""")
conn.commit()

# ── Generate users ────────────────────────────────────────────────────────────
users        = []
subscriptions = []
events_rows  = []
funnel_rows  = []

for uid in range(1, N_USERS + 1):
    signup_date = rand_date(START_DATE, END_DATE - timedelta(days=90))

    channel = weighted_choice(CHANNELS, CHANNEL_WEIGHTS)
    country = weighted_choice(COUNTRIES, COUNTRY_WEIGHTS)

    # Plan assignment – most start free, some go straight to paid
    start_plan_roll = random.random()
    if start_plan_roll < 0.55:
        plan = "free"
    elif start_plan_roll < 0.75:
        plan = "starter"
    elif start_plan_roll < 0.90:
        plan = "growth"
    else:
        plan = "enterprise"

    # Churn logic (monthly survival)
    months_available = max(1, ((END_DATE - signup_date).days) // 30)
    monthly_survival = RETENTION_BY_PLAN[plan]
    churned = 0
    churn_date = None
    churn_month = None

    for m in range(months_available):
        if random.random() > monthly_survival:
            churned = 1
            churn_date = (signup_date + timedelta(days=30 * (m + 1))).strftime("%Y-%m-%d")
            churn_month = m + 1
            break

    users.append((uid, signup_date.strftime("%Y-%m-%d"), channel, country, plan, churned, churn_date))

    # Subscription record
    sub_end = churn_date
    subscriptions.append((uid, plan, PLAN_PRICES[plan],
                          signup_date.strftime("%Y-%m-%d"), sub_end))

    # ── Generate events ──────────────────────────────────────────────────────
    # Event count correlates with plan & whether they churned
    if churned:
        active_days = churn_month * 30
    else:
        active_days = (END_DATE - signup_date).days

    base_events = {"free": 8, "starter": 20, "growth": 40, "enterprise": 70}[plan]
    if churned:
        base_events = max(2, base_events // 3)

    n_events = max(1, int(random.gauss(base_events, base_events * 0.3)))

    user_features_used = set()
    activated = 0
    for _ in range(n_events):
        days_offset = random.randint(0, max(1, active_days - 1))
        ev_date = signup_date + timedelta(days=days_offset)
        if ev_date > END_DATE:
            ev_date = END_DATE

        feature = random.choice(FEATURES)
        user_features_used.add(feature)

        if days_offset <= 7:
            activated = 1

        events_rows.append((uid, "feature_use", feature, ev_date.strftime("%Y-%m-%d")))

    # Add page-view events
    n_views = random.randint(3, 30)
    for _ in range(n_views):
        days_offset = random.randint(0, max(1, active_days - 1))
        ev_date = signup_date + timedelta(days=days_offset)
        if ev_date > END_DATE:
            ev_date = END_DATE
        events_rows.append((uid, "page_view", None, ev_date.strftime("%Y-%m-%d")))

    # ── Funnel ───────────────────────────────────────────────────────────────
    engaged     = 1 if user_features_used & POWER_FEATURES else 0
    converted   = 1 if plan != "free" else 0
    retained_90 = 0
    if not churned:
        retained_90 = 1
    elif churn_month and churn_month > 3:
        retained_90 = 1

    funnel_rows.append((uid, 1, activated, engaged, converted, retained_90))

# ── Bulk insert ────────────────────────────────────────────────────────────────
cur.executemany(
    "INSERT INTO users VALUES (?,?,?,?,?,?,?)", users)
cur.executemany(
    "INSERT INTO subscriptions (user_id, plan, mrr, start_date, end_date) VALUES (?,?,?,?,?)",
    subscriptions)
cur.executemany(
    "INSERT INTO events (user_id, event_type, feature, event_date) VALUES (?,?,?,?)",
    events_rows)
cur.executemany(
    "INSERT INTO funnel_stages VALUES (?,?,?,?,?,?)", funnel_rows)

conn.commit()

# ── Export CSVs ─────────────────────────────────────────────────────────────
for table in ["users", "subscriptions", "events", "funnel_stages"]:
    rows = cur.execute(f"SELECT * FROM {table}").fetchall()
    cols = [d[0] for d in cur.description]
    with open(f"data/{table}.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        w.writerows(rows)
    print(f"  ✓ {table}.csv  ({len(rows)} rows)")

conn.close()
print(f"\nDatabase saved to {DB_PATH}")
print("Dataset generation complete.")
