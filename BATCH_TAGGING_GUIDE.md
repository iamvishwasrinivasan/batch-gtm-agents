# Batch Tagging Guide

## Overview

The `batch_tag` column allows you to organize account research by sales plays, campaigns, or events. This makes it easy to query subsets of accounts later.

## Setup

### 1. Add the column to Snowflake

Run the migration script **once**:

```bash
# Copy SQL and run in Snowflake
cat ~/batch-gtm-agents/add_batch_tag_column.sql
```

Or run directly in Snowflake:
```sql
ALTER TABLE GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT
ADD COLUMN batch_tag VARCHAR(255);
```

### 2. Use the --tag parameter

Tag your research batches when running:

```bash
# Tag by event
python3 batch_account_research.py --accounts "Apollo,Grindr,Quickbase" --tag "dreamforce_2026"

# Tag by sales play
python3 batch_account_research.py --accounts-file enterprise_targets.txt --tag "Q2_enterprise_outreach"

# Tag by vertical
python3 batch_account_research.py --accounts "FinTech1,FinTech2,FinTech3" --tag "fintech_vertical"
```

## Querying Tagged Batches

### Get all accounts from a specific play

```sql
SELECT 
    acct_name,
    tier,
    priority_score,
    orchestration_mentions,
    contact_count,
    mql_count,
    call_count
FROM GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT
WHERE batch_tag = 'Q2_enterprise_outreach'
ORDER BY priority_score DESC;
```

### High-signal accounts from a campaign

```sql
SELECT 
    acct_name,
    orchestration_mentions,
    hiring_signals_count,
    blog_post_count
FROM GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT
WHERE batch_tag = 'dreamforce_2026'
  AND orchestration_mentions > 20
ORDER BY orchestration_mentions DESC;
```

### Compare multiple plays

```sql
SELECT 
    batch_tag,
    COUNT(*) as account_count,
    AVG(orchestration_mentions) as avg_orchestration,
    AVG(priority_score) as avg_priority,
    SUM(CASE WHEN tier = 'customer' THEN 1 ELSE 0 END) as customer_count
FROM GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT
WHERE batch_tag IN ('Q1_retail', 'Q1_fintech', 'Q1_healthcare')
GROUP BY batch_tag
ORDER BY avg_priority DESC;
```

### Get emails from a specific play

```sql
SELECT 
    acct_name,
    email_correspondence
FROM GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT
WHERE batch_tag = 'deal_postmortem_march'
  AND email_correspondence IS NOT NULL;
```

### Find accounts needing follow-up

```sql
SELECT 
    acct_name,
    tier,
    orchestration_mentions,
    latest_call_date,
    mql_count
FROM GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT
WHERE batch_tag = 'Q2_enterprise_outreach'
  AND orchestration_mentions > 15
  AND call_count = 0  -- High signal but no calls yet
ORDER BY orchestration_mentions DESC;
```

### Tech stack analysis by play

```sql
SELECT 
    batch_tag,
    acct_name,
    tech_stack,
    orchestration_mentions
FROM GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT
WHERE batch_tag = 'data_observability_play'
  AND ARRAY_CONTAINS('airflow'::VARIANT, tech_stack)
ORDER BY orchestration_mentions DESC;
```

## Common Tag Naming Conventions

**By Quarter:**
- `Q2_2026_enterprise`
- `Q2_2026_smb`

**By Event:**
- `dreamforce_2026`
- `databricks_summit_march`
- `aws_reinvent_2025`

**By Vertical:**
- `fintech_vertical`
- `healthcare_vertical`
- `retail_vertical`

**By Sales Play:**
- `data_quality_play`
- `migration_play`
- `observability_play`

**By Deal Stage:**
- `deal_postmortem_Q1`
- `stalled_deals_review`
- `expansion_targets_Q2`

## Tips

1. **Use consistent naming:** Pick a convention and stick to it
2. **Tag at research time:** Don't forget --tag when running batch research
3. **Query regularly:** Use tags to track play performance over time
4. **Combine with other filters:** Tags + orchestration_mentions + tier = powerful segmentation
5. **Re-tag if needed:** Re-running research on an account updates its tag

## Example Workflow

```bash
# 1. Research conference attendees
python3 batch_account_research.py \
  --accounts-file ~/Downloads/aws_summit_leads.csv \
  --tag "aws_summit_april_2026"

# 2. Query high-priority accounts
SELECT acct_name, orchestration_mentions 
FROM GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT
WHERE batch_tag = 'aws_summit_april_2026'
  AND orchestration_mentions > 25
ORDER BY orchestration_mentions DESC;

# 3. Export for AE follow-up
SELECT 
    acct_name,
    contact_count,
    orchestration_mentions,
    key_signals[0] as top_signal
FROM GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT
WHERE batch_tag = 'aws_summit_april_2026'
  AND priority_score >= 7;
```

## Cortex Integration (Future)

Once you have tagged batches, you can use Snowflake Cortex to:
- Rank accounts by fit score using LLM functions
- Semantic search across research reports within a tag
- Auto-generate play summaries

Example Cortex query:
```sql
SELECT 
    acct_name,
    SNOWFLAKE.CORTEX.COMPLETE(
        'claude-3-5-sonnet',
        'Score this account for Airflow fit (0-10): ' || comprehensive_report
    ) as ai_fit_score
FROM GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT
WHERE batch_tag = 'Q2_enterprise_outreach'
LIMIT 10;
```
