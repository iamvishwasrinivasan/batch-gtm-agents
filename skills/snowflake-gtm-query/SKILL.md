---
name: snowflake-gtm-query
description: Query Snowflake GTM data - accounts, MQLs, Gong call transcripts, research, DAG runs, product usage
args: Natural language question (e.g., "who MQL'd at Americor", "summarize gong calls", "show accounts with >100 DAGs")
---

You are answering this Snowflake query: **{{args}}**

# Available Data Sources

## 1. Local Research Files (Check First!)
Location: `~/claude-work/batch-research-output/YYYY-MM-DD/[account_slug]/`

Contains:
- Account classification (tier, priority)
- Engagement counts (contacts, MQLs, opps, calls)
- Gong call transcripts (full text)
- Web research signals (orchestration mentions, tech stack)
- Generated from `batch_account_research.py`

**When to use:** Account research questions where fresh data isn't critical

## 2. Snowflake Tables

### HQ.MODEL_CRM.SF_ACCOUNTS
- ACCT_ID, ACCT_NAME, ACCT_TYPE
- IS_CURRENT_CUST, CUSTOMER_SINCE_DATE
- PARENT_NAME

### HQ.MODEL_CRM.SF_CONTACTS
- CONTACT_ID, ACCT_ID
- TITLE, PRIMARY_DOMAIN
- IS_EMPLOYEE, SOURCE

### HQ.MODEL_CRM.SF_MQLS
- CONTACT_ID, ACCT_ID
- MQL_TS, REPORTING_CHANNEL
- UTM_SOURCE, UTM_MEDIUM, UTM_CAMPAIGN

### HQ.MODEL_CRM.SF_OPPS
- OPP_ID, ACCT_ID
- OPP_NAME, OPP_TYPE
- CURRENT_STAGE_NAME, CLOSE_DATE, CREATED_DATE

### HQ.MODEL_CRM_SENSITIVE.GONG_CALL_TRANSCRIPTS
- CALL_ID, ACCT_ID
- CALL_TITLE, SCHEDULED_TS
- ATTENDEES, FULL_TRANSCRIPT

### GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT
- acct_id, acct_name, tier, priority_score
- contact_count, mql_count, opp_count, call_count
- orchestration_mentions, hiring_signals_count
- key_signals (ARRAY), tech_stack (ARRAY)
- structured_signals (VARCHAR JSON), structured_tech_stack (VARCHAR JSON)
- comprehensive_report (TEXT)
- research_date (TIMESTAMP)

**Connection details:**
- Account: GP21411.us-east-1
- User: VISHWASRINIVASAN
- Role: GTMADMIN
- Warehouse: HUMANS
- Database: HQ (or GTM for research table)
- Auth: Private key at `~/.ssh/rsa_key_unencrypted.p8`

# Workflow

## Step 1: Understand the Question

Categorize the query type:

### Account Research Questions
- "Who MQL'd at [company]?"
- "Who did we talk to last at [company]?"
- "Show me contacts at [company]"
- "What's the latest with [company]?"

**Action:** Check local research files first (if <30 days old), then query Snowflake

### Batch Research Analytics
- "Which accounts have high orchestration mentions?"
- "Show me all accounts researched this week"
- "Which prospects MQL'd in Q2?"
- "What companies are using Databricks?"

**Action:** Query GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT

### CRM Analytics
- "How many MQLs this quarter?"
- "Which accounts have open opportunities?"
- "Show me all customer accounts"

**Action:** Query HQ.MODEL_CRM tables

### Product/Usage Questions
- "Show me accounts with >100 DAGs"
- "Which customers use Kubernetes executor?"
- "What's the compute usage for [company]?"

**Action:** Query product usage tables (if available) or ACCOUNT_RESEARCH_OUTPUT

## Step 2: Execute Query

### For Account Research Questions:

1. **Try local files first:**
   ```bash
   ls ~/claude-work/batch-research-output/2026-*/
   ```
   Find the account folder (slugified name)
   Read `raw_data.json` if found and recent

2. **If no local data, use helper script for account lookups:**
   ```bash
   python3 ~/batch-gtm-agents/query_account.py "Company Name"
   ```

3. **For ALL other queries, use generic SQL helper:**
   ```bash
   python3 ~/batch-gtm-agents/snowflake_query.py "SELECT ... FROM ... WHERE ..."
   ```
   
   Examples:
   - Gong calls: `python3 ~/batch-gtm-agents/snowflake_query.py "SELECT CALL_TITLE, SCHEDULED_TS, ATTENDEES, FULL_TRANSCRIPT FROM HQ.MODEL_CRM_SENSITIVE.GONG_CALL_TRANSCRIPTS WHERE LOWER(ACCT_NAME) LIKE '%detroit lions%' ORDER BY SCHEDULED_TS DESC LIMIT 5"`
   - MQL analytics: `python3 ~/batch-gtm-agents/snowflake_query.py "SELECT COUNT(*) as mql_count, REPORTING_CHANNEL FROM HQ.MODEL_CRM.SF_MQLS WHERE MQL_TS >= '2026-01-01' GROUP BY REPORTING_CHANNEL"`
   - Research data: `python3 ~/batch-gtm-agents/snowflake_query.py "SELECT acct_name, tier, orchestration_mentions FROM GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT WHERE orchestration_mentions > 50 ORDER BY orchestration_mentions DESC LIMIT 10"`
   
   **IMPORTANT:** ALWAYS use this helper script. NEVER write inline Python for Snowflake queries.

## Step 3: Format Output

### For Account Details:
```
## Account Name
**Type:** Prospect | Customer
**Tier:** engaged_prospect (Priority: 7/10)

**Engagement:**
- 83 contacts
- 4 MQLs (most recent: April 29, 2025)
- 3 opportunities
- 5 Gong calls (most recent: March 17, 2025)

**MQLs:**
1. Principal Analytics Engineer - April 29, 2025 (Paid Social, dbt + Airflow webinar)
2. ...

**Most Recent Call:** [Title] - March 17, 2025
Attendees: Liam Jones, Andrei Avramescu, Lahav Peles
[Brief summary]
```

### For Analytics Queries:
Use tables with clear headers and totals

### For Research Queries:
Highlight key insights (orchestration mentions, tech stack, signals)

## Step 4: Cite Data Source

Always end with:
- "Data from: Local research (2026-04-01)" OR
- "Data from: Snowflake query (HQ.MODEL_CRM.SF_MQLS)" OR
- "Data from: Batch research table (GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT)"

# Common Query Patterns

## Account Lookups
**Input:** "who MQL'd at Americor"
**Action:** Check local → query SF_MQLS + SF_CONTACTS
**Output:** List with names, dates, channels

**Input:** "latest call with monday.com"
**Action:** Check local → query GONG_CALL_TRANSCRIPTS
**Output:** Call summary with preview

## Research Analytics
**Input:** "accounts with high orchestration mentions"
**Action:** Query ACCOUNT_RESEARCH_OUTPUT WHERE orchestration_mentions > 50
**Output:** Table sorted by orchestration_mentions DESC

**Input:** "who uses Snowflake"
**Action:** Query ACCOUNT_RESEARCH_OUTPUT, parse structured_tech_stack JSON
**Output:** List of accounts with Snowflake in tech stack

## CRM Analytics
**Input:** "MQLs this quarter"
**Action:** Query SF_MQLS WHERE MQL_TS >= '2026-04-01'
**Output:** Count + breakdown by channel

# Safety Rules

- ✅ SELECT queries only (read-only)
- ❌ No INSERT, UPDATE, DELETE, DROP, TRUNCATE
- ✅ Use LIMIT by default (100 rows max unless specified)
- ✅ Sanitize user input in SQL (use parameterized queries)
- ✅ Timeout queries after 30 seconds
- ✅ Handle "account not found" gracefully

# Error Handling

- **Account not found:** Suggest checking spelling or running batch research
- **Table doesn't exist:** List available tables
- **Connection failed:** Check credentials or suggest retrying
- **Query timeout:** Suggest adding WHERE clause or LIMIT
- **No results:** Confirm with user and suggest broader search

# Pro Tips

- For large result sets, summarize top 10 and offer to export full CSV
- When showing tech stack, highlight orchestration tools (Airflow, Prefect, Dagster)
- Parse structured_signals JSON to show sources and confidence scores
- For Gong transcripts, show preview first, offer full transcript if needed
- Link account questions to batch research insights when relevant
