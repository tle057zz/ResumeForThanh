-- Maven Fuzzy Factory Project - Step 4
-- Validate imported raw data.
SET search_path TO raw;
-- 1. Confirm row counts for all imported tables.
SELECT 'products' AS table_name, COUNT(*) AS row_count FROM raw.products
UNION ALL
SELECT 'website_sessions', COUNT(*) FROM raw.website_sessions
UNION ALL
SELECT 'website_pageviews', COUNT(*) FROM raw.website_pageviews
UNION ALL
SELECT 'orders', COUNT(*) FROM raw.orders
UNION ALL
SELECT 'order_items', COUNT(*) FROM raw.order_items
UNION ALL
SELECT 'order_item_refunds', COUNT(*) FROM raw.order_item_refunds
ORDER BY table_name;

-- 2. Check date ranges.
SELECT 'website_sessions' AS table_name, MIN(created_at) AS first_date, MAX(created_at) AS last_date
FROM raw.website_sessions
UNION ALL
SELECT 'website_pageviews', MIN(created_at), MAX(created_at)
FROM raw.website_pageviews
UNION ALL
SELECT 'orders', MIN(created_at), MAX(created_at)
FROM raw.orders
UNION ALL
SELECT 'order_items', MIN(created_at), MAX(created_at)
FROM raw.order_items
UNION ALL
SELECT 'order_item_refunds', MIN(created_at), MAX(created_at)
FROM raw.order_item_refunds
UNION ALL
SELECT 'products', MIN(created_at), MAX(created_at)
FROM raw.products
ORDER BY table_name;

-- 3. Check missing values in key fields.
SELECT
    COUNT(*) AS total_sessions,
    SUM(CASE WHEN website_session_id IS NULL THEN 1 ELSE 0 END) AS missing_session_id,
    SUM(CASE WHEN created_at IS NULL THEN 1 ELSE 0 END) AS missing_created_at,
    SUM(CASE WHEN user_id IS NULL THEN 1 ELSE 0 END) AS missing_user_id
FROM raw.website_sessions;

SELECT
    COUNT(*) AS total_orders,
    SUM(CASE WHEN order_id IS NULL THEN 1 ELSE 0 END) AS missing_order_id,
    SUM(CASE WHEN created_at IS NULL THEN 1 ELSE 0 END) AS missing_created_at,
    SUM(CASE WHEN website_session_id IS NULL THEN 1 ELSE 0 END) AS missing_website_session_id,
    SUM(CASE WHEN price_usd IS NULL THEN 1 ELSE 0 END) AS missing_price_usd,
    SUM(CASE WHEN cogs_usd IS NULL THEN 1 ELSE 0 END) AS missing_cogs_usd
FROM raw.orders;

-- 4. Check table relationships.
SELECT COUNT(*) AS orders_without_matching_session
FROM raw.orders o
LEFT JOIN raw.website_sessions s
    ON o.website_session_id = s.website_session_id
WHERE s.website_session_id IS NULL;

SELECT COUNT(*) AS pageviews_without_matching_session
FROM raw.website_pageviews pv
LEFT JOIN raw.website_sessions s
    ON pv.website_session_id = s.website_session_id
WHERE s.website_session_id IS NULL;

SELECT COUNT(*) AS order_items_without_matching_order
FROM raw.order_items oi
LEFT JOIN raw.orders o
    ON oi.order_id = o.order_id
WHERE o.order_id IS NULL;

SELECT COUNT(*) AS order_items_without_matching_product
FROM raw.order_items oi
LEFT JOIN raw.products p
    ON oi.product_id = p.product_id
WHERE p.product_id IS NULL;

SELECT COUNT(*) AS refunds_without_matching_order_item
FROM raw.order_item_refunds r
LEFT JOIN raw.order_items oi
    ON r.order_item_id = oi.order_item_id
WHERE oi.order_item_id IS NULL;
