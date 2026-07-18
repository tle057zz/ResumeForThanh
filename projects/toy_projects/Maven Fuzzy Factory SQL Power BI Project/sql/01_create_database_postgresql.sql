-- Maven Fuzzy Factory Project - Step 2
-- PostgreSQL database setup

-- Part 1:
-- Run this while connected to your default PostgreSQL database, usually "postgres".
CREATE DATABASE maven_fuzzy_factory;

-- Part 2:
-- After the database is created, connect pgAdmin to the new database:
--   maven_fuzzy_factory
--
-- Then run the schema setup below.
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS analytics;

-- RAW will store the imported CSV tables.
-- ANALYTICS will store cleaned views and summary views for Power BI.
