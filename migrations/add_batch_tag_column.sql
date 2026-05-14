-- Add batch_tag column to ACCOUNT_RESEARCH_OUTPUT table
-- Allows querying subsets of research by campaign/play
-- Usage: Run this in Snowflake before using --tag parameter

ALTER TABLE GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT
ADD COLUMN batch_tag VARCHAR(255);

-- Add index for faster queries
CREATE INDEX IF NOT EXISTS idx_batch_tag
ON GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT(batch_tag);

-- Verify column was added
SELECT batch_tag FROM GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT LIMIT 1;
