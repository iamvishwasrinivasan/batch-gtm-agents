-- Migration: Add v2 structured research fields
-- Run this in Snowflake to add the new VARCHAR columns for structured signals and tech stack

USE DATABASE GTM;
USE SCHEMA PUBLIC;

ALTER TABLE ACCOUNT_RESEARCH_OUTPUT ADD COLUMN structured_signals VARCHAR;
ALTER TABLE ACCOUNT_RESEARCH_OUTPUT ADD COLUMN structured_tech_stack VARCHAR;

-- Verify columns were added
DESC TABLE ACCOUNT_RESEARCH_OUTPUT;

-- Example query to view the new structured data
-- SELECT
--   acct_name,
--   structured_signals::VARIANT as signals,
--   structured_tech_stack::VARIANT as tech
-- FROM ACCOUNT_RESEARCH_OUTPUT
-- WHERE structured_signals IS NOT NULL
-- LIMIT 5;
