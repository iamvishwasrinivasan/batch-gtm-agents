-- Migration: Add email correspondence field to account research table
-- Run this in Snowflake BEFORE running updated batch_account_research.py

USE DATABASE GTM;
USE SCHEMA PUBLIC;

-- Add email correspondence column (stores JSON array of emails)
ALTER TABLE ACCOUNT_RESEARCH_OUTPUT ADD COLUMN email_correspondence VARCHAR;

-- Verify column was added
DESC TABLE ACCOUNT_RESEARCH_OUTPUT;

-- Test query to view email data after running updated script
-- SELECT
--   acct_name,
--   email_correspondence::VARIANT as emails
-- FROM ACCOUNT_RESEARCH_OUTPUT
-- WHERE email_correspondence IS NOT NULL
-- LIMIT 5;
