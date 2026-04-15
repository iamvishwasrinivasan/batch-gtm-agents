-- V2 GTM Batch Research Output Table
-- Stores comprehensive account research results from test_improved_searches.py

CREATE OR REPLACE TABLE GTM.PUBLIC.V2_GTM_BATCH_OUTPUT (
    -- Primary Keys & Metadata
    BATCH_RUN_ID VARCHAR(100),                      -- Unique ID for each batch run
    COMPANY_NAME VARCHAR(500) NOT NULL,
    DOMAIN VARCHAR(500),
    RESEARCH_TIMESTAMP TIMESTAMP_NTZ NOT NULL,
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),

    -- Snowflake Context (Salesforce/Gong Data)
    SF_STATUS VARCHAR(50),                          -- success, not_found, unavailable, error
    SF_ACCT_ID VARCHAR(50),
    SF_ACCT_NAME VARCHAR(500),
    SF_IS_CUSTOMER BOOLEAN,
    SF_PARENT_NAME VARCHAR(500),
    SF_CONTACT_COUNT INT,
    SF_MQL_COUNT INT,
    SF_OPP_COUNT INT,
    SF_CALL_COUNT INT,
    SF_LATEST_MQL_DATE TIMESTAMP_NTZ,
    SF_LATEST_CALL_DATE TIMESTAMP_NTZ,

    -- Nested Snowflake Data (JSON)
    SF_CONTACTS VARIANT,                            -- Array of contact objects
    SF_MQLS VARIANT,                                -- Array of MQL objects
    SF_OPPS VARIANT,                                -- Array of opportunity objects
    SF_GONG_CALLS VARIANT,                          -- Array of Gong call objects

    -- Web Search Results Summary
    SEARCH_COMPANY_RESEARCH_COUNT INT DEFAULT 0,
    SEARCH_GITHUB_EVIDENCE_COUNT INT DEFAULT 0,
    SEARCH_HIRING_COUNT INT DEFAULT 0,
    SEARCH_TRIGGER_EVENTS_COUNT INT DEFAULT 0,
    SEARCH_ENGINEERING_BLOG_COUNT INT DEFAULT 0,
    SEARCH_PRODUCT_ANNOUNCEMENTS_COUNT INT DEFAULT 0,
    SEARCH_CASE_STUDIES_COUNT INT DEFAULT 0,

    -- Web Search Results (Full JSON)
    WEB_SEARCH_COMPANY_RESEARCH VARIANT,
    WEB_SEARCH_GITHUB_EVIDENCE VARIANT,
    WEB_SEARCH_HIRING VARIANT,
    WEB_SEARCH_TRIGGER_EVENTS VARIANT,
    WEB_SEARCH_ENGINEERING_BLOG VARIANT,
    WEB_SEARCH_PRODUCT_ANNOUNCEMENTS VARIANT,
    WEB_SEARCH_CASE_STUDIES VARIANT,

    -- Tech Stack Extraction (from job postings)
    TECH_STACK VARIANT,                             -- Object with tech names and counts

    -- Account Classification (computed)
    CLASSIFICATION VARCHAR(100),                    -- CUSTOMER, ENGAGED PROSPECT, WARM LEAD, COLD PROSPECT
    AIRFLOW_SIGNALS VARIANT,                        -- Array of Airflow signal strings
    HAS_AIRFLOW_SIGNAL BOOLEAN,

    -- Full Raw Output (backup)
    RAW_JSON VARIANT,                               -- Complete JSON output from script

    -- Constraints
    CONSTRAINT PK_V2_GTM_BATCH PRIMARY KEY (COMPANY_NAME, RESEARCH_TIMESTAMP)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS IDX_V2_GTM_BATCH_ACCT_ID
    ON GTM.PUBLIC.V2_GTM_BATCH_OUTPUT(SF_ACCT_ID);

CREATE INDEX IF NOT EXISTS IDX_V2_GTM_BATCH_CLASSIFICATION
    ON GTM.PUBLIC.V2_GTM_BATCH_OUTPUT(CLASSIFICATION);

CREATE INDEX IF NOT EXISTS IDX_V2_GTM_BATCH_AIRFLOW
    ON GTM.PUBLIC.V2_GTM_BATCH_OUTPUT(HAS_AIRFLOW_SIGNAL);

-- Comment on table
COMMENT ON TABLE GTM.PUBLIC.V2_GTM_BATCH_OUTPUT IS
'V2 batch account research output combining Snowflake (SF/Gong) data with 7 targeted web searches.
Replaces manual research process with automated comprehensive account profiling.
Source: test_improved_searches.py';

-- Column comments
COMMENT ON COLUMN GTM.PUBLIC.V2_GTM_BATCH_OUTPUT.BATCH_RUN_ID IS
'Unique identifier for batch processing runs (e.g., 20260414_quarterly_pipeline)';

COMMENT ON COLUMN GTM.PUBLIC.V2_GTM_BATCH_OUTPUT.SF_CONTACTS IS
'Array of contact objects with title, domain, source, is_employee';

COMMENT ON COLUMN GTM.PUBLIC.V2_GTM_BATCH_OUTPUT.SF_GONG_CALLS IS
'Array of Gong call objects with call_id, title, date, attendees, transcript_preview (first 2000 chars)';

COMMENT ON COLUMN GTM.PUBLIC.V2_GTM_BATCH_OUTPUT.TECH_STACK IS
'Tech stack extracted from job postings. Format: {"Tech Name": {"count": N, "sources": [urls]}}';

COMMENT ON COLUMN GTM.PUBLIC.V2_GTM_BATCH_OUTPUT.AIRFLOW_SIGNALS IS
'Array of Airflow detection signals: job postings, GitHub repos, blog posts, Gong calls';

COMMENT ON COLUMN GTM.PUBLIC.V2_GTM_BATCH_OUTPUT.RAW_JSON IS
'Complete JSON output from test_improved_searches.py for debugging/reprocessing';
