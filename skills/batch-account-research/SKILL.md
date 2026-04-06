---
name: batch-account-research
description: Run comprehensive account research - Exa searches, Snowflake CRM data, Gong transcripts, email correspondence. Saves to Snowflake and generates i360-style reports.
args: Company names (comma-separated) or "--accounts-file path/to/file.txt" (e.g., "Apollo,Grindr,Quickbase")
---

You are running batch account research for: **{{args}}**

# What This Does

Runs comprehensive account research pipeline:
1. **9 Exa searches per account** - orchestration tools, hiring, news, blog posts, case studies, website crawl
2. **Snowflake CRM context** - contacts, MQLs, opportunities, Gong call transcripts, email correspondence
3. **Airflow Mission Critical grading** - A/B/C/D assessment of Airflow criticality
4. **Saves to Snowflake** - `GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT`
5. **Optional reports** - i360-style comprehensive reports (if ANTHROPIC_API_KEY set)

# Execution

Parse args to determine invocation:

## If comma-separated company names:
```bash
cd /Users/vishwasrinivasan/batch-gtm-agents && python3 batch_account_research.py --accounts "{{args}}"
```

## If args start with "--accounts-file":
```bash
cd /Users/vishwasrinivasan/batch-gtm-agents && python3 batch_account_research.py {{args}}
```

**Let the script run to completion.** It shows real-time progress:
- Account X/Y processing
- Exa searches completed/failed
- Processing time per account

# Output Format

After completion, summarize:

```
## Batch Research Complete

**Accounts Processed:** X/Y successful
**Total Time:** X minutes
**Exa Searches:** X completed, Y failed
**Reports Generated:** X (or "Skipped - no API key set")

### Results:
1. **CompanyA** - Tier: engaged_prospect, Orchestration: 31 mentions, Priority: 8/10, Grade: B
   - 83 contacts, 4 MQLs, 3 opps, 5 calls, 12 emails
2. **CompanyB** - Tier: customer, Orchestration: 21 mentions, Priority: 7/10, Grade: B
   - 45 contacts, 2 MQLs, 1 opp, 3 calls, 8 emails
3. **CompanyC** - Tier: cold_prospect, Orchestration: 5 mentions, Priority: 3/10, Grade: C
   - 10 contacts, 0 MQLs, 0 opps, 0 calls, 0 emails

**Data saved to:** GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT

### Costs:
- Exa API: $X.XX ($0.009 per account)
- Claude API: $X.XX ($0.02 per report, if enabled)
- Total: $X.XX

### Next Steps:
- View reports: `/snowflake-gtm-query show me the report for CompanyA`
- Query results: `python3 ~/batch-gtm-agents/query_account.py "CompanyA"`
- See all high-signal accounts: `/snowflake-gtm-query accounts with >20 orchestration mentions`
- Check email history: `/snowflake-gtm-query show emails for CompanyA`
```

If any accounts failed, list them with error messages.

# What Gets Saved to Snowflake

**GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT** table contains:

**Engagement:**
- contact_count, mql_count, opp_count, call_count
- latest_mql_date, latest_call_date
- **email_correspondence** (JSON array) - Salesforce Task emails with subject, date, preview

**Signals:**
- orchestration_mentions (Airflow/Dagster/Prefect references)
- hiring_signals_count (data engineer jobs)
- blog_post_count, product_announcement_count, case_study_count

**Structured Data:**
- key_signals (ARRAY) - top signals with scores
- tech_stack (ARRAY) - technologies with confidence levels
- comprehensive_report (TEXT) - full 9-section report

**Airflow Grading:**
- **Grade A:** Real-time critical (downtime = customer outage)
- **Grade B:** Mission-critical batch (core business depends on pipelines)
- **Grade C:** Operational tool (used but not critical)
- **Grade D:** No evidence of Airflow usage

# Email Correspondence Details

**What's collected:**
- Emails from Salesforce Tasks (TYPE='Email')
- Subject, date, and preview (first 500 chars of description)
- Only for engaged accounts (those with MQLs or calls)
- Up to 1000 emails per batch, sorted by most recent

**Use cases:**
- Deal post-mortems (see final emails in closed/lost deals)
- Response time analysis
- Communication cadence tracking
- Contact engagement scoring

# Error Handling

**Missing API key:**
```
Warning: EXA_API_KEY not set
→ Set it: export EXA_API_KEY="your-key"
```

**Snowflake connection failed:**
```
Error: Cannot connect to Snowflake
→ Check private key exists: ls ~/.ssh/rsa_key_unencrypted.p8
```

**Missing email column:**
```
Error: Column 'email_correspondence' does not exist
→ Run migration: Run add_email_column_to_research_table.sql in Snowflake
```

**Account not found:**
- Script logs warning and continues with other accounts
- Suggest checking company name spelling

**Rate limiting:**
- Script has built-in rate limiting (60 req/min)
- If hitting limits, will auto-retry with backoff

# Performance Expectations

| Accounts | Time (3 workers) | Exa Cost | Claude Cost | Total |
|----------|-----------------|----------|-------------|-------|
| 3 | ~30 sec | $0.03 | $0.06 | $0.09 |
| 10 | ~1.5 min | $0.09 | $0.20 | $0.29 |
| 50 | ~7 min | $0.45 | $1.00 | $1.45 |

# Pro Tips

- **Optimal batch size:** 10-50 accounts per run (~2-8 minutes)
- **Cost savings:** Run without ANTHROPIC_API_KEY to skip report generation; generate reports manually later via `/snowflake-gtm-query`
- **Data freshness:** Re-run for accounts older than 30 days
- **Priority scoring:** Auto-scored 1-10 based on engagement + signals
- **Query results:** Use `/snowflake-gtm-query` or `query_account.py` after completion
- **Email analysis:** Query `email_correspondence` column with `::VARIANT` and `FLATTEN()` for detailed analysis

# Common Workflows

**Before customer calls:**
```
/batch-account-research Apollo,Grindr,Quickbase
→ Get fresh research + email history for tomorrow's meetings
```

**Conference attendees:**
```
/batch-account-research --accounts-file ~/Downloads/dreamforce_leads.txt
→ Research all leads from event
```

**Deal post-mortem:**
```
/batch-account-research CapstoneInvestmentAdvisors
→ Review full email correspondence to understand what happened
```

**Refresh stale data:**
```
/snowflake-gtm-query accounts researched >30 days ago
→ Get list, then re-run research
```

---

**After script completes**, parse output and format the summary above. Include success/failure counts, costs, engagement metrics (including email counts), and suggested next actions.
