-- ============================================================
-- 01_funnel_analysis.sql
-- Conversion funnel: Signup → Activation → Engagement → Paid → 90-day Retention
-- ============================================================

-- Overall funnel conversion rates
SELECT
    COUNT(*)                                          AS total_signups,
    SUM(activated)                                    AS activated,
    ROUND(100.0 * SUM(activated) / COUNT(*), 1)       AS activation_rate_pct,

    SUM(engaged)                                      AS engaged,
    ROUND(100.0 * SUM(engaged) / COUNT(*), 1)         AS engagement_rate_pct,

    SUM(converted)                                    AS paid_conversions,
    ROUND(100.0 * SUM(converted) / COUNT(*), 1)       AS paid_conversion_rate_pct,

    SUM(retained_90d)                                 AS retained_90d,
    ROUND(100.0 * SUM(retained_90d) / COUNT(*), 1)    AS retention_90d_rate_pct

FROM funnel_stages;


-- Drop-off at each stage (absolute counts)
SELECT 'Signed Up'           AS stage, 1 AS stage_order, COUNT(*) AS users FROM funnel_stages
UNION ALL
SELECT 'Activated (7d)',     2, SUM(activated)    FROM funnel_stages
UNION ALL
SELECT 'Engaged (power feature)', 3, SUM(engaged) FROM funnel_stages
UNION ALL
SELECT 'Converted to Paid',  4, SUM(converted)    FROM funnel_stages
UNION ALL
SELECT 'Retained 90d',       5, SUM(retained_90d) FROM funnel_stages
ORDER BY stage_order;


-- Funnel by acquisition channel
SELECT
    u.acquisition_channel,
    COUNT(*)                                             AS signups,
    ROUND(100.0 * SUM(f.activated)   / COUNT(*), 1)     AS activation_pct,
    ROUND(100.0 * SUM(f.engaged)     / COUNT(*), 1)     AS engagement_pct,
    ROUND(100.0 * SUM(f.converted)   / COUNT(*), 1)     AS paid_conversion_pct,
    ROUND(100.0 * SUM(f.retained_90d)/ COUNT(*), 1)     AS retention_90d_pct
FROM funnel_stages f
JOIN users u ON u.user_id = f.user_id
GROUP BY u.acquisition_channel
ORDER BY paid_conversion_pct DESC;
