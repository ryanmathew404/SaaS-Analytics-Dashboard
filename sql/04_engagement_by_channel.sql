-- ============================================================
-- 04_engagement_by_channel.sql
-- Feature engagement and activity patterns by acquisition channel
-- ============================================================

-- Average events per user by channel
SELECT
    u.acquisition_channel,
    COUNT(DISTINCT u.user_id)                          AS users,
    COUNT(e.event_id)                                  AS total_events,
    ROUND(1.0 * COUNT(e.event_id) / COUNT(DISTINCT u.user_id), 1) AS avg_events_per_user,
    COUNT(DISTINCT CASE WHEN e.event_type = 'feature_use' THEN e.event_id END) AS feature_uses,
    ROUND(1.0 * COUNT(DISTINCT CASE WHEN e.event_type = 'feature_use' THEN e.event_id END)
        / COUNT(DISTINCT u.user_id), 1)                AS avg_feature_uses_per_user
FROM users u
LEFT JOIN events e ON e.user_id = u.user_id
GROUP BY u.acquisition_channel
ORDER BY avg_events_per_user DESC;


-- Top features by unique users (overall)
SELECT
    feature,
    COUNT(DISTINCT user_id)   AS unique_users,
    COUNT(*)                  AS total_uses,
    ROUND(1.0 * COUNT(*) / COUNT(DISTINCT user_id), 1) AS uses_per_user
FROM events
WHERE event_type = 'feature_use'
GROUP BY feature
ORDER BY unique_users DESC;


-- Feature adoption by plan tier
SELECT
    u.plan,
    e.feature,
    COUNT(DISTINCT e.user_id)  AS users_using_feature,
    COUNT(*)                    AS total_uses
FROM events e
JOIN users u ON u.user_id = e.user_id
WHERE e.event_type = 'feature_use'
GROUP BY u.plan, e.feature
ORDER BY u.plan, total_uses DESC;


-- Weekly active users (WAU) trend
SELECT
    strftime('%Y-W%W', event_date)  AS week,
    COUNT(DISTINCT user_id)          AS wau
FROM events
GROUP BY week
ORDER BY week;
