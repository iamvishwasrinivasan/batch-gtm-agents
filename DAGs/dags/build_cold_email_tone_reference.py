"""
## Cold Email Tone Reference DAG

This DAG extracts high-quality, human-written outbound emails from top-performing sales reps
and loads them into GTM.PUBLIC.COLD_EMAIL_TONE for LLM tone training.

**Target Table:** GTM.PUBLIC.COLD_EMAIL_TONE

**To change filters:** Edit the EMAIL_FILTERS config below and redeploy with `astro deploy --dags`
"""

from airflow.decorators import dag
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from pendulum import datetime


# ============================================================================
# EMAIL FILTER CONFIGURATION
# Edit these values to change what emails get extracted
# ============================================================================

EMAIL_FILTERS = {
    # Top performing reps (by win rate)
    "top_reps": [
        "Adriano Sergian",
        "Iain Hayes",
        "Matthew Rizzo",
        "Rodrigo Pombo",
        "Nathan Cooley",
        "Kyle Wolff",
        "Pat Racy",
    ],

    # Date range (Q2 2026)
    "date_start": "2026-01-29",
    "date_end": "2026-04-29",

    # Body length constraints (chars)
    "body_length_min": 500,
    "body_length_max": 3000,

    # Quality filters
    "require_opportunity": True,  # Only emails tied to deals
    "exclude_apollo": True,       # Exclude Apollo automation
    "exclude_replies": True,      # Exclude Re:/Fwd:/FW:

    # Expected row count for validation (set to None to skip check)
    "expected_row_count": 346,
}


@dag(
    start_date=datetime(2026, 4, 29),
    schedule=None,  # Manual trigger only
    catchup=False,
    doc_md=__doc__,
    default_args={
        "owner": "GTM",
        "retries": 2,
    },
    tags=["gtm", "email", "llm-training", "manual"],
)
def build_cold_email_tone_reference():

    create_target_table = SnowflakeOperator(
        task_id="create_target_table",
        snowflake_conn_id="snowflake_default",
        sql="""
        CREATE TABLE IF NOT EXISTS GTM.PUBLIC.COLD_EMAIL_TONE (
            email_id VARCHAR,
            subject VARCHAR,
            body VARCHAR,
            sent_date DATE,
            owner_name VARCHAR,
            account_name VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
        );

        -- Truncate table to ensure clean load
        TRUNCATE TABLE GTM.PUBLIC.COLD_EMAIL_TONE;
        """,
    )

    # Build the rep filter SQL
    rep_unions = "\n            UNION ALL ".join([f"SELECT '{rep}' as name" for rep in EMAIL_FILTERS["top_reps"]])

    # Build conditional filters
    opp_filter = "AND e.OPP_ID IS NOT NULL" if EMAIL_FILTERS["require_opportunity"] else ""
    apollo_filter = """AND e.DESCRIPTION_RAW NOT LIKE '%apollo.io%'
            AND e.DESCRIPTION_RAW NOT LIKE '%Sent from Apollo%'""" if EMAIL_FILTERS["exclude_apollo"] else ""
    reply_filter = """AND e.SUBJECT NOT LIKE 'Re:%'
            AND e.SUBJECT NOT LIKE 'Fwd:%'
            AND e.SUBJECT NOT LIKE 'FW:%'""" if EMAIL_FILTERS["exclude_replies"] else ""

    extract_and_load_emails = SnowflakeOperator(
        task_id="extract_and_load_emails",
        snowflake_conn_id="snowflake_default",
        sql=f"""
        INSERT INTO GTM.PUBLIC.COLD_EMAIL_TONE (
            email_id,
            subject,
            body,
            sent_date,
            owner_name,
            account_name
        )
        WITH top_reps AS (
            {rep_unions}
        )
        SELECT
            e.TASK_ID as email_id,
            e.SUBJECT as subject,
            e.DESCRIPTION_RAW as body,
            e.EMAIL_DATE as sent_date,
            e.OWNER_NAME as owner_name,
            e.ACCT_NAME as account_name
        FROM HQ.MODEL_CRM_PII.SF_EMAILS_PII e
        JOIN top_reps r ON e.OWNER_NAME = r.name
        WHERE
            e.IS_OUTBOUND = TRUE
            AND e.EMAIL_DATE >= '{EMAIL_FILTERS["date_start"]}'
            AND e.EMAIL_DATE <= '{EMAIL_FILTERS["date_end"]}'
            {reply_filter}
            AND e.DESCRIPTION_RAW IS NOT NULL
            AND LENGTH(e.DESCRIPTION_RAW) BETWEEN {EMAIL_FILTERS["body_length_min"]} AND {EMAIL_FILTERS["body_length_max"]}
            {apollo_filter}
            {opp_filter}
        ORDER BY e.EMAIL_DATE DESC;
        """,
    )

    # Build validation SQL based on expected count
    if EMAIL_FILTERS["expected_row_count"]:
        expected = EMAIL_FILTERS["expected_row_count"]
        tolerance = int(expected * 0.02)  # 2% tolerance
        validation_sql = f"""
        SELECT COUNT(*) as row_count
        FROM GTM.PUBLIC.COLD_EMAIL_TONE;

        -- Validate we got the expected number of emails
        SELECT
            CASE
                WHEN COUNT(*) = {expected} THEN 'SUCCESS: Loaded exactly {expected} emails'
                WHEN COUNT(*) BETWEEN {expected - tolerance} AND {expected + tolerance}
                    THEN 'WARNING: Loaded ' || COUNT(*) || ' emails (expected {expected})'
                ELSE 'ERROR: Loaded ' || COUNT(*) || ' emails (expected {expected})'
            END as validation_result
        FROM GTM.PUBLIC.COLD_EMAIL_TONE;
        """
    else:
        validation_sql = """
        SELECT
            COUNT(*) as row_count,
            'SUCCESS: Loaded ' || COUNT(*) || ' emails (no validation threshold set)' as validation_result
        FROM GTM.PUBLIC.COLD_EMAIL_TONE;
        """

    validate_row_count = SnowflakeOperator(
        task_id="validate_row_count",
        snowflake_conn_id="snowflake_default",
        sql=validation_sql,
    )

    # Define dependencies
    create_target_table >> extract_and_load_emails >> validate_row_count


# Instantiate the DAG
dag_instance = build_cold_email_tone_reference()
