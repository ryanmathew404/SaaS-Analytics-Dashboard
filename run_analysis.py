"""
Run all SQL analyses and output JSON data for the dashboard.
"""
import sqlite3, json, os

conn = sqlite3.connect("data/saas_analytics.db")
conn.row_factory = sqlite3.Row

def q(sql):
    rows = conn.execute(sql).fetchall()
    return [dict(r) for r in rows]

data = {}

# ── 1. KPI Summary ────────────────────────────────────────────────────────────
kpis_raw = q("""
SELECT
    COUNT(*) AS total_users,
    SUM(churned) AS churned,
    ROUND(100.0 * SUM(churned)/COUNT(*),1) AS churn_rate,
    ROUND(100.0 * (1-1.0*SUM(churned)/COUNT(*)),1) AS retention_rate,
    SUM(CASE WHEN plan != 'free' THEN 1 ELSE 0 END) AS paid_users,
    ROUND(100.0 * SUM(CASE WHEN plan!='free' THEN 1 ELSE 0 END)/COUNT(*),1) AS paid_conversion_rate
FROM users
""")[0]

mrr_raw = q("""
SELECT ROUND(SUM(mrr),0) AS total_mrr FROM subscriptions WHERE plan != 'free'
  AND (end_date IS NULL OR end_date >= '2024-06-01')
""")[0]

data['kpis'] = {
    "total_users": kpis_raw["total_users"],
    "paid_users": kpis_raw["paid_users"],
    "churn_rate": kpis_raw["churn_rate"],
    "retention_rate": kpis_raw["retention_rate"],
    "paid_conversion_rate": kpis_raw["paid_conversion_rate"],
    "total_mrr": int(mrr_raw["total_mrr"])
}

# ── 2. Funnel ─────────────────────────────────────────────────────────────────
funnel = q("""
SELECT 'Signed Up'           AS stage, 1 AS ord, COUNT(*) AS users FROM funnel_stages
UNION ALL SELECT 'Activated (7d)',          2, SUM(activated)    FROM funnel_stages
UNION ALL SELECT 'Used Power Feature',      3, SUM(engaged)      FROM funnel_stages
UNION ALL SELECT 'Converted to Paid',       4, SUM(converted)    FROM funnel_stages
UNION ALL SELECT 'Retained 90d',            5, SUM(retained_90d) FROM funnel_stages
ORDER BY ord
""")
data['funnel'] = funnel

# ── 3. Churn by plan ──────────────────────────────────────────────────────────
churn_by_plan = q("""
SELECT plan, COUNT(*) AS users, SUM(churned) AS churned,
       ROUND(100.0*SUM(churned)/COUNT(*),1) AS churn_rate_pct
FROM users GROUP BY plan ORDER BY churn_rate_pct DESC
""")
data['churn_by_plan'] = churn_by_plan

# ── 4. Churn by channel ───────────────────────────────────────────────────────
churn_by_channel = q("""
SELECT acquisition_channel AS channel, COUNT(*) AS users,
       ROUND(100.0*SUM(churned)/COUNT(*),1) AS churn_rate_pct
FROM users GROUP BY acquisition_channel ORDER BY churn_rate_pct DESC
""")
data['churn_by_channel'] = churn_by_channel

# ── 5. Feature vs Churn ───────────────────────────────────────────────────────
feature_engagement_churn = q("""
WITH upf AS (
  SELECT u.user_id, u.churned,
    CASE
      WHEN COUNT(DISTINCT CASE WHEN e.feature IN
          ('team_invite','api_access','automation_rule','integration_connect')
          THEN e.feature END) >= 2 THEN 'High Engagement'
      WHEN COUNT(DISTINCT CASE WHEN e.feature IN
          ('team_invite','api_access','automation_rule','integration_connect')
          THEN e.feature END) = 1 THEN 'Some Engagement'
      ELSE 'Low Engagement'
    END AS engagement_level
  FROM users u
  LEFT JOIN events e ON e.user_id=u.user_id AND e.event_type='feature_use'
  GROUP BY u.user_id, u.churned
)
SELECT engagement_level, COUNT(*) AS users,
       ROUND(100.0*SUM(churned)/COUNT(*),1) AS churn_rate_pct
FROM upf GROUP BY engagement_level ORDER BY churn_rate_pct DESC
""")
data['feature_engagement_churn'] = feature_engagement_churn

# ── 6. Feature usage (active vs churned) ─────────────────────────────────────
feature_retention = q("""
SELECT e.feature,
  ROUND(100.0 * COUNT(DISTINCT CASE WHEN u.churned=0 THEN e.user_id END)
        / NULLIF(COUNT(DISTINCT CASE WHEN u.churned=0 THEN u.user_id END),0), 1) AS active_pct,
  ROUND(100.0 * COUNT(DISTINCT CASE WHEN u.churned=1 THEN e.user_id END)
        / NULLIF(COUNT(DISTINCT CASE WHEN u.churned=1 THEN u.user_id END),0), 1) AS churned_pct
FROM events e JOIN users u ON u.user_id=e.user_id
WHERE e.event_type='feature_use'
GROUP BY e.feature ORDER BY active_pct DESC
""")
data['feature_retention'] = feature_retention

# ── 7. LTV by channel ─────────────────────────────────────────────────────────
ltv_by_channel = q("""
WITH tenure AS (
  SELECT u.user_id, u.acquisition_channel, s.mrr,
    CASE WHEN u.churned=1
      THEN MAX(0, CAST((julianday(u.churn_date)-julianday(u.signup_date))/30 AS INTEGER))
      ELSE CAST((julianday('2024-06-30')-julianday(u.signup_date))/30 AS INTEGER)
    END AS tenure_months
  FROM users u JOIN subscriptions s ON s.user_id=u.user_id
)
SELECT acquisition_channel AS channel,
       COUNT(*) AS customers,
       ROUND(AVG(mrr),2) AS avg_mrr,
       ROUND(AVG(tenure_months),1) AS avg_tenure_months,
       ROUND(AVG(mrr*tenure_months),2) AS avg_ltv
FROM tenure GROUP BY acquisition_channel ORDER BY avg_ltv DESC
""")
data['ltv_by_channel'] = ltv_by_channel

# ── 8. LTV by plan ────────────────────────────────────────────────────────────
ltv_by_plan = q("""
WITH tenure AS (
  SELECT u.user_id, u.plan, s.mrr,
    CASE WHEN u.churned=1
      THEN MAX(0, CAST((julianday(u.churn_date)-julianday(u.signup_date))/30 AS INTEGER))
      ELSE CAST((julianday('2024-06-30')-julianday(u.signup_date))/30 AS INTEGER)
    END AS tenure_months
  FROM users u JOIN subscriptions s ON s.user_id=u.user_id
)
SELECT plan, COUNT(*) AS customers, ROUND(AVG(mrr),2) AS avg_mrr,
       ROUND(AVG(tenure_months),1) AS avg_tenure_months,
       ROUND(AVG(mrr*tenure_months),2) AS avg_ltv
FROM tenure GROUP BY plan ORDER BY avg_ltv DESC
""")
data['ltv_by_plan'] = ltv_by_plan

# ── 9. MRR trend (monthly) ────────────────────────────────────────────────────
mrr_trend = q("""
SELECT strftime('%Y-%m', start_date) AS month,
       ROUND(SUM(mrr),0) AS mrr,
       COUNT(*) AS new_subs
FROM subscriptions WHERE plan!='free'
GROUP BY month ORDER BY month
""")
data['mrr_trend'] = mrr_trend

# ── 10. Engagement by channel ─────────────────────────────────────────────────
engagement_by_channel = q("""
SELECT u.acquisition_channel AS channel,
       COUNT(DISTINCT u.user_id) AS users,
       ROUND(1.0*COUNT(e.event_id)/COUNT(DISTINCT u.user_id),1) AS avg_events_per_user
FROM users u LEFT JOIN events e ON e.user_id=u.user_id
GROUP BY channel ORDER BY avg_events_per_user DESC
""")
data['engagement_by_channel'] = engagement_by_channel

# ── 11. Funnel by channel ─────────────────────────────────────────────────────
funnel_by_channel = q("""
SELECT u.acquisition_channel AS channel, COUNT(*) AS signups,
       ROUND(100.0*SUM(f.activated)/COUNT(*),1) AS activation_pct,
       ROUND(100.0*SUM(f.converted)/COUNT(*),1) AS paid_conversion_pct,
       ROUND(100.0*SUM(f.retained_90d)/COUNT(*),1) AS retention_90d_pct
FROM funnel_stages f JOIN users u ON u.user_id=f.user_id
GROUP BY channel ORDER BY paid_conversion_pct DESC
""")
data['funnel_by_channel'] = funnel_by_channel

# ── 12. Plan distribution ─────────────────────────────────────────────────────
plan_dist = q("""
SELECT plan, COUNT(*) AS users FROM users GROUP BY plan ORDER BY users DESC
""")
data['plan_distribution'] = plan_dist

conn.close()

# Write JSON
os.makedirs("dashboard", exist_ok=True)
with open("dashboard/data.json", "w") as f:
    json.dump(data, f, indent=2)

print("Analysis complete. data.json written.")
print("\n── KPIs ──────────────────────────────────")
for k,v in data['kpis'].items():
    print(f"  {k}: {v}")

print("\n── Funnel ────────────────────────────────")
total = data['funnel'][0]['users']
for row in data['funnel']:
    pct = round(100*row['users']/total,1)
    print(f"  {row['stage']}: {row['users']:,} ({pct}%)")

print("\n── Churn by Plan ─────────────────────────")
for row in data['churn_by_plan']:
    print(f"  {row['plan']}: {row['churn_rate_pct']}% churn")

print("\n── LTV by Channel ────────────────────────")
for row in data['ltv_by_channel']:
    print(f"  {row['channel']}: avg LTV ${row['avg_ltv']}")
