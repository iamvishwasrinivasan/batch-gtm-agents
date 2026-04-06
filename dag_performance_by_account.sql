-- DAG Performance Metrics by Account
-- Replicates the DAG Run Detail view shown in Airflow UI
--
-- Usage: Replace 'Apollo.io' with any account name
-- Time window: Last 90 days (adjust as needed)

WITH account_orgs AS (
  -- Get all Astro org_ids for the account
  SELECT
    ACCT_ID,
    ACCT_NAME,
    ORG_ID,
    ORG_NAME
  FROM HQ.MODEL_CRM.SF_ASTRO_ORGS
  WHERE LOWER(ACCT_NAME) LIKE LOWER('%Apollo.io%')  -- Replace with target account
    AND IS_REPORTING_EXCLUDED = FALSE
    AND IS_INTERNAL = FALSE
),

dag_stats AS (
  -- Aggregate DAG run metrics
  SELECT
    dr.DAGRUN_TYPE,
    dr.DAG_ID,
    COUNT(*) AS dag_run_count,
    ROUND(AVG(CASE WHEN dr.IS_SUCCESS THEN 1.0 ELSE 0.0 END) * 100, 2) AS success_rate_pct,
    ROUND(AVG(dr.RUN_DURATION) / 60.0, 2) AS avg_run_duration_min,
    ROUND(MAX(dr.RUN_DURATION) / 60.0, 2) AS max_run_duration_min,
    ROUND(PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY dr.RUN_DURATION) / 60.0, 2) AS p90_run_duration_min,
    MIN(dr.START_TS) AS first_run,
    MAX(dr.START_TS) AS last_run,
    dr.ORG_ID,
    dr.DEPLOYMENT_ID
  FROM HQ.MODEL_ASTRO.DAG_RUNS dr
  INNER JOIN account_orgs ao ON dr.ORG_ID = ao.ORG_ID
  WHERE dr.START_TS >= DATEADD(day, -90, CURRENT_TIMESTAMP())  -- Last 90 days
    AND dr.IS_MONITORING_DAG = FALSE  -- Exclude Astronomer monitoring DAGs
    AND dr.STATE IN ('success', 'failed')  -- Only completed runs
  GROUP BY
    dr.DAGRUN_TYPE,
    dr.DAG_ID,
    dr.ORG_ID,
    dr.DEPLOYMENT_ID
)

-- Final output matching the screenshot format
SELECT
  ds.DAGRUN_TYPE AS "Dagrun Type",
  ds.DAG_ID AS "Dag Id",
  ds.dag_run_count AS "DAG Run Count",
  ds.success_rate_pct || '%' AS "DAG Success Rate",
  ds.avg_run_duration_min AS "Avg Run Duration (Min)",
  ds.max_run_duration_min AS "Max Run Duration (Min)",
  ds.p90_run_duration_min AS "P90 Run Duration (Min)",
  ds.first_run AS "First Run",
  ds.last_run AS "Last Run",
  ao.ACCT_NAME AS "Account Name",
  ao.ORG_NAME AS "Org Name",
  ds.DEPLOYMENT_ID AS "Deployment ID"
FROM dag_stats ds
INNER JOIN account_orgs ao ON ds.ORG_ID = ao.ORG_ID
ORDER BY
  ds.DAGRUN_TYPE,
  ds.dag_run_count DESC,
  ds.success_rate_pct ASC  -- Show problem DAGs first
;

-- ALTERNATIVE: Get totals by dagrun type (summary view)
/*
SELECT
  ds.DAGRUN_TYPE,
  SUM(ds.dag_run_count) AS total_runs,
  ROUND(AVG(ds.success_rate_pct), 2) AS avg_success_rate,
  COUNT(DISTINCT ds.DAG_ID) AS unique_dags,
  ao.ACCT_NAME
FROM dag_stats ds
INNER JOIN account_orgs ao ON ds.ORG_ID = ao.ORG_ID
GROUP BY ds.DAGRUN_TYPE, ao.ACCT_NAME
ORDER BY ds.DAGRUN_TYPE;
*/
