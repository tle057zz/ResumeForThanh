-- Maven Fuzzy Factory Project - Step 3
-- Create raw tables before importing CSV files in pgAdmin.

SET search_path TO raw;

CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY,
    created_at TIMESTAMP,
    product_name TEXT
);

CREATE TABLE IF NOT EXISTS website_sessions (
    website_session_id INTEGER PRIMARY KEY,
    created_at TIMESTAMP,
    user_id INTEGER,
    is_repeat_session INTEGER,
    utm_source TEXT,
    utm_campaign TEXT,
    utm_content TEXT,
    device_type TEXT,
    http_referer TEXT
);

CREATE TABLE IF NOT EXISTS website_pageviews (
    website_pageview_id INTEGER PRIMARY KEY,
    created_at TIMESTAMP,
    website_session_id INTEGER,
    pageview_url TEXT
);

CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY,
    created_at TIMESTAMP,
    website_session_id INTEGER,
    user_id INTEGER,
    primary_product_id INTEGER,
    items_purchased INTEGER,
    price_usd NUMERIC(10, 2),
    cogs_usd NUMERIC(10, 2)
);

CREATE TABLE IF NOT EXISTS order_items (
    order_item_id INTEGER PRIMARY KEY,
    created_at TIMESTAMP,
    order_id INTEGER,
    product_id INTEGER,
    is_primary_item INTEGER,
    price_usd NUMERIC(10, 2),
    cogs_usd NUMERIC(10, 2)
);

CREATE TABLE IF NOT EXISTS order_item_refunds (
    order_item_refund_id INTEGER PRIMARY KEY,
    created_at TIMESTAMP,
    order_item_id INTEGER,
    order_id INTEGER,
    refund_amount_usd NUMERIC(10, 2)
);
