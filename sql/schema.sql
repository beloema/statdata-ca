-- STATDATA.CA - Development-only fresh database bootstrap.
-- WARNING: Review target DATABASE_URL before running psql.
-- This file is NOT a migration for an existing production database.

CREATE TABLE IF NOT EXISTS cpi (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL,
    region TEXT NOT NULL,
    unit TEXT NOT NULL,
    value NUMERIC NOT NULL,
    UNIQUE (date, region, unit)
);

CREATE TABLE IF NOT EXISTS interest_rates (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL,
    indicator TEXT NOT NULL,
    unit TEXT NOT NULL,
    value NUMERIC NOT NULL,
    UNIQUE (date, indicator)
);

CREATE TABLE IF NOT EXISTS exchange_rates (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL,
    currency TEXT NOT NULL,
    unit TEXT NOT NULL,
    value NUMERIC NOT NULL,
    UNIQUE (date, currency)
);

CREATE TABLE IF NOT EXISTS employment (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL,
    region TEXT NOT NULL,
    indicator TEXT NOT NULL,
    unit TEXT NOT NULL,
    value NUMERIC NOT NULL,
    UNIQUE (date, region, indicator)
);

CREATE TABLE IF NOT EXISTS gdp (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL,
    industry TEXT NOT NULL,
    unit TEXT NOT NULL,
    value NUMERIC NOT NULL,
    UNIQUE (date, industry)
);

CREATE TABLE IF NOT EXISTS population (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL,
    region TEXT NOT NULL,
    unit TEXT NOT NULL,
    value BIGINT NOT NULL,
    UNIQUE (date, region)
);

CREATE OR REPLACE VIEW inflation_yoy AS
SELECT
    current_cpi.date,
    'Percent' AS unit,
    ROUND((current_cpi.value / NULLIF(previous_cpi.value, 0) - 1) * 100, 1) AS value
FROM cpi AS current_cpi
JOIN cpi AS previous_cpi
  ON previous_cpi.date = (current_cpi.date - INTERVAL '1 year')::date
 AND previous_cpi.region = current_cpi.region
 AND previous_cpi.unit = current_cpi.unit
WHERE current_cpi.region = 'Canada';
