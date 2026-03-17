-- ============================================================
-- 02_churn_retention.sql
-- Churn rate by plan, channel, and feature engagement
-- ============================================================

-- Overall churn rate
SELECT
    COUNT(*)                                      AS total_users,
    SUM(churned)                                  AS churned_users,
    COUNT(*) - SUM(churned)                       AS active_users,
    ROUND(100.0 * SUM(churned) / COUNT(*), 1)     AS churn_rate_pct,
    ROUND(100.0 * (1 - 1.0*SUM(churned)/COUNT(*)), 1) AS retention_rate_pct
FROM users;


-- Churn rate by plan
SELECT
    plan,
    COUNT(*)                                       AS users,
    SUM(churned)                                   AS churned,
    ROUND(100.0 * SUM(churned) / COUNT(*), 1)      AS churn_rate_pct
FROM users
GROUP BY plan
ORDER BY churn_rate_pct DESC;


-- Churn rate by acquisition channel
SELECT
    acquisition_channel,
    COUNT(*)                                       AS users,
    SUM(churned)                                   AS churned,
    ROUND(100.0 * SUM(churned) / COUNT(*), 1)      AS churn_rate_pct
FROM users
GROUP BY acquisition_channel
ORDER BY churn_rate_pct DESC;


-- Feature engagement vs churn: do users who use power features churn less?
WITH user_power_features AS (
    SELECT
        u.user_id,
        u.churned,
        CASE
            WHEN COUNT(DISTINCT CASE WHEN e.feature IN
                ('team_invite','api_access','automation_rule','integration_connect')
                THEN e.feature END) >= 2
            THEN 'High Engagement'
            WHEN COUNT(DISTINCT CASE WHEN e.feature IN
                ('team_invite','api_access','automation_rule','integration_connect')
                THEN e.feature END) = 1
            THEN 'Some Engagement'
            ELSE 'Low Engagement'
        END AS engagement_level
    FROM users u
    LEFT JOIN events e ON e.user_id = u.user_id AND e.event_type = 'feature_use'
    GROUP BY u.user_id, u.churned
)
SELECT
    engagement_level,
    COUNT(*)                                        AS users,
    SUM(churned)                                    AS churned,
    ROUND(100.0 * SUM(churned) / COUNT(*), 1)       AS churn_rate_pct
FROM user_power_features
GROUP BY engagement_level
ORDER BY churn_rate_pct DESC;


-- Feature usage frequency vs retention (churned vs active)
SELECT
    e.feature,
    ROUND(AVG(CASE WHEN u.churned = 0 THEN 1.0 ELSE 0 END) * 100, 1) AS pct_active_users_use,
    ROUND(AVG(CASE WHEN u.churned = 1 THEN 1.0 ELSE 0 END) * 100, 1) AS pct_churned_users_use,
    COUNT(DISTINCT e.user_id) AS unique_users
FROM events e
JOIN users u ON u.user_id = e.user_id
WHERE e.event_type = 'feature_use'
GROUP BY e.feature
ORDER BY pct_active_users_use DESC;
