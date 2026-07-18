-- Maven Fuzzy Factory Project - Step 5
-- Create analytics views for Power BI.

CREATE SCHEMA IF NOT EXISTS analytics;

DROP VIEW IF EXISTS analytics.monthly_performance;
CREATE VIEW analytics.monthly_performance AS
SELECT
    DATE_TRUNC('month', s.created_at)::date AS month,
    COUNT(DISTINCT s.website_session_id) AS sessions,
    COUNT(DISTINCT o.order_id) AS orders,
    COALESCE(SUM(o.price_usd), 0) AS revenue,
    COALESCE(SUM(o.cogs_usd), 0) AS cogs,
    COALESCE(SUM(o.price_usd - o.cogs_usd), 0) AS gross_profit,
    ROUND(
        COUNT(DISTINCT o.order_id)::numeric
        / NULLIF(COUNT(DISTINCT s.website_session_id), 0),
        4
    ) AS conversion_rate,
    ROUND(
        COALESCE(SUM(o.price_usd), 0)
        / NULLIF(COUNT(DISTINCT o.order_id), 0),
        2
    ) AS average_order_value,
    ROUND(
        COALESCE(SUM(o.price_usd), 0)
        / NULLIF(COUNT(DISTINCT s.website_session_id), 0),
        2
    ) AS revenue_per_session
FROM raw.website_sessions s
LEFT JOIN raw.orders o
    ON s.website_session_id = o.website_session_id
GROUP BY DATE_TRUNC('month', s.created_at)::date;

DROP VIEW IF EXISTS analytics.marketing_performance;
CREATE VIEW analytics.marketing_performance AS
SELECT
    COALESCE(s.utm_source, 'direct') AS utm_source,
    COALESCE(s.utm_campaign, 'none') AS utm_campaign,
    COALESCE(s.utm_content, 'none') AS utm_content,
    s.device_type,
    s.is_repeat_session,
    COUNT(DISTINCT s.website_session_id) AS sessions,
    COUNT(DISTINCT o.order_id) AS orders,
    COALESCE(SUM(o.price_usd), 0) AS revenue,
    COALESCE(SUM(o.cogs_usd), 0) AS cogs,
    COALESCE(SUM(o.price_usd - o.cogs_usd), 0) AS gross_profit,
    ROUND(
        COUNT(DISTINCT o.order_id)::numeric
        / NULLIF(COUNT(DISTINCT s.website_session_id), 0),
        4
    ) AS conversion_rate,
    ROUND(
        COALESCE(SUM(o.price_usd), 0)
        / NULLIF(COUNT(DISTINCT s.website_session_id), 0),
        2
    ) AS revenue_per_session
FROM raw.website_sessions s
LEFT JOIN raw.orders o
    ON s.website_session_id = o.website_session_id
GROUP BY
    COALESCE(s.utm_source, 'direct'),
    COALESCE(s.utm_campaign, 'none'),
    COALESCE(s.utm_content, 'none'),
    s.device_type,
    s.is_repeat_session;

DROP VIEW IF EXISTS analytics.product_performance;
CREATE VIEW analytics.product_performance AS
SELECT
    p.product_id,
    p.product_name,
    COUNT(DISTINCT oi.order_item_id) AS units_sold,
    COALESCE(SUM(oi.price_usd), 0) AS revenue,
    COALESCE(SUM(oi.cogs_usd), 0) AS cogs,
    COALESCE(SUM(oi.price_usd - oi.cogs_usd), 0) AS gross_profit,
    COUNT(DISTINCT r.order_item_refund_id) AS refunded_items,
    COALESCE(SUM(r.refund_amount_usd), 0) AS refund_amount,
    ROUND(
        COUNT(DISTINCT r.order_item_refund_id)::numeric
        / NULLIF(COUNT(DISTINCT oi.order_item_id), 0),
        4
    ) AS refund_rate
FROM raw.products p
LEFT JOIN raw.order_items oi
    ON p.product_id = oi.product_id
LEFT JOIN raw.order_item_refunds r
    ON oi.order_item_id = r.order_item_id
GROUP BY
    p.product_id,
    p.product_name;

DROP VIEW IF EXISTS analytics.landing_page_performance;
CREATE VIEW analytics.landing_page_performance AS
WITH first_pageview AS (
    SELECT
        website_session_id,
        pageview_url AS landing_page,
        ROW_NUMBER() OVER (
            PARTITION BY website_session_id
            ORDER BY created_at, website_pageview_id
        ) AS pageview_rank
    FROM raw.website_pageviews
),
session_pageview_counts AS (
    SELECT
        website_session_id,
        COUNT(*) AS pageviews
    FROM raw.website_pageviews
    GROUP BY website_session_id
)
SELECT
    fp.landing_page,
    COUNT(DISTINCT s.website_session_id) AS sessions,
    COUNT(DISTINCT o.order_id) AS orders,
    SUM(CASE WHEN spc.pageviews = 1 THEN 1 ELSE 0 END) AS bounced_sessions,
    ROUND(
        SUM(CASE WHEN spc.pageviews = 1 THEN 1 ELSE 0 END)::numeric
        / NULLIF(COUNT(DISTINCT s.website_session_id), 0),
        4
    ) AS bounce_rate,
    ROUND(
        COUNT(DISTINCT o.order_id)::numeric
        / NULLIF(COUNT(DISTINCT s.website_session_id), 0),
        4
    ) AS conversion_rate,
    COALESCE(SUM(o.price_usd), 0) AS revenue
FROM raw.website_sessions s
JOIN first_pageview fp
    ON s.website_session_id = fp.website_session_id
    AND fp.pageview_rank = 1
JOIN session_pageview_counts spc
    ON s.website_session_id = spc.website_session_id
LEFT JOIN raw.orders o
    ON s.website_session_id = o.website_session_id
GROUP BY fp.landing_page;
