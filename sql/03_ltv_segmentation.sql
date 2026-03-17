-- ============================================================
-- 03_ltv_segmentation.sql
-- Customer Lifetime Value and segmentation analysis
-- ============================================================

-- Average LTV by acquisition channel
-- LTV = MRR × average tenure in months
WITH tenure AS (
    SELECT
        u.user_id,
        u.acquisition_channel,
        u.plan,
        s.mrr,
        CASE
            WHEN u.churned = 1
            THEN CAST((julianday(u.churn_date) - julianday(u.signup_date)) / 30 AS INTEGER)
            ELSE CAST((julianday('2024-06-30') - julianday(u.signup_date)) / 30 AS INTEGER)
        END AS tenure_months
    FROM users u
    JOIN subscriptions s ON s.user_id = u.user_id
)
SELECT
    acquisition_channel,
    COUNT(*)                                         AS customers,
    ROUND(AVG(mrr), 2)                               AS avg_mrr,
    ROUND(AVG(tenure_months), 1)                     AS avg_tenure_months,
    ROUND(AVG(mrr * tenure_months), 2)               AS avg_ltv,
    ROUND(SUM(mrr * tenure_months), 2)               AS total_revenue
FROM tenure
GROUP BY acquisition_channel
ORDER BY avg_ltv DESC;


-- LTV by plan
WITH tenure AS (
    SELECT
        u.user_id,
        u.plan,
        s.mrr,
        CASE
            WHEN u.churned = 1
            THEN CAST((julianday(u.churn_date) - julianday(u.signup_date)) / 30 AS INTEGER)
            ELSE CAST((julianday('2024-06-30') - julianday(u.signup_date)) / 30 AS INTEGER)
        END AS tenure_months
    FROM users u
    JOIN subscriptions s ON s.user_id = u.user_id
)
SELECT
    plan,
    COUNT(*)                                          AS customers,
    ROUND(AVG(mrr), 2)                                AS avg_mrr,
    ROUND(AVG(tenure_months), 1)                      AS avg_tenure_months,
    ROUND(AVG(mrr * tenure_months), 2)                AS avg_ltv,
    ROUND(SUM(mrr * tenure_months) / 1000.0, 1)       AS total_revenue_k
FROM tenure
GROUP BY plan
ORDER BY avg_ltv DESC;


-- Monthly Recurring Revenue (MRR) trend
SELECT
    strftime('%Y-%m', s.start_date)  AS month,
    ROUND(SUM(s.mrr), 2)             AS new_mrr,
    COUNT(*)                          AS new_subscribers
FROM subscriptions s
WHERE s.plan != 'free'
GROUP BY month
ORDER BY month;


-- High-value segment: enterprise + growth users by country
SELECT
    u.country,
    COUNT(*)                                          AS customers,
    ROUND(AVG(s.mrr), 2)                              AS avg_mrr,
    ROUND(SUM(s.mrr), 2)                              AS total_mrr
FROM users u
JOIN subscriptions s ON s.user_id = u.user_id
WHERE u.plan IN ('growth', 'enterprise')
GROUP BY u.country
ORDER BY total_mrr DESC;
