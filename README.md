# Batch GTM Account Research System

Comprehensive account research automation combining Snowflake CRM data with Exa AI web intelligence to generate i360-style reports for sales teams.

## Overview

This system performs three-phase batch research on target accounts:

1. **Bulk Engagement Check** - Query Snowflake for MQLs, opportunities, and Gong calls
2. **Conditional Context Fetch** - Retrieve detailed CRM data for engaged accounts only
3. **Comprehensive Web Research** - Run 9 specialized Exa searches per account

### Key Features

- ✅ 9 comprehensive Exa searches per account (orchestration, hiring, blog posts, news, case studies, etc.)
- ✅ Airflow Mission Critical Assessment with A/B/C/D grading
- ✅ Structured signals with scoring and source tracking
- ✅ Tech stack detection with confidence levels
- ✅ All data stored in Snowflake (single source of truth)
- ✅ Optional automated report generation via Claude API

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│ 1. Data Collection                                       │
│    - 9 Exa searches per account (~5-8 seconds)          │
│    - Snowflake CRM context (contacts, MQLs, calls)      │
│    - Gong transcripts (full text)                       │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 2. Report Generation (Optional)                          │
│    - Claude API generates i360-style reports            │
│    - 9 sections with evidence-based analysis            │
│    - Airflow criticality scoring                        │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 3. Snowflake Storage                                     │
│    - GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT                 │
│    - 30 columns: metadata, signals, tech stack, report  │
│    - Queryable via Claude Desktop for reps              │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

```bash
# Python dependencies
pip3 install snowflake-connector-python cryptography requests anthropic

# Environment variables
export EXA_API_KEY="your-exa-key"
export ANTHROPIC_API_KEY="your-anthropic-key"  # Optional - for automated reports
```

### Snowflake Setup

1. Configure private key authentication at `~/.ssh/rsa_key_unencrypted.p8`
2. Ensure access to:
   - `HQ.MODEL_CRM.SF_ACCOUNTS`, `SF_CONTACTS`, `SF_MQLS`, `SF_OPPS`
   - `HQ.MODEL_CRM_SENSITIVE.GONG_CALL_TRANSCRIPTS`
   - `GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT` (created by script)

### Usage

**Basic batch research:**
```bash
python3 batch_account_research.py --accounts "CompanyA,CompanyB,CompanyC"
```

**From file:**
```bash
python3 batch_account_research.py --accounts-file accounts.txt
```

**What happens:**
- Collects comprehensive Exa data (9 searches per account)
- Fetches Snowflake CRM context for engaged accounts
- Saves all metadata to Snowflake
- If `ANTHROPIC_API_KEY` set: Generates comprehensive reports automatically
- If not set: Skips report generation (can generate manually via Claude Desktop)

## Performance

| Accounts | Time (3 workers) | Exa Cost | Claude API Cost | Total Cost |
|----------|-----------------|----------|-----------------|------------|
| 10 | ~1.5 min | $0.09 | $0.20 | $0.29 |
| 100 | ~15 min | $0.90 | $2.00 | $2.90 |
| 1000 | ~2.5 hours | $9.00 | $20.00 | $29.00 |

## Output

### Snowflake Table Schema

**`GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT`** (30 columns):

**Core Fields:**
- `acct_id`, `acct_name`, `tier`, `priority_score`
- `contact_count`, `mql_count`, `opp_count`, `call_count`
- `latest_mql_date`, `latest_call_date`

**Exa Research Metadata:**
- `orchestration_mentions` - Count of Airflow/Dagster/Prefect references
- `hiring_signals_count` - Job postings found
- `blog_post_count` - Engineering blog posts
- `product_announcement_count` - Product launches/releases
- `case_study_count` - Customer success stories
- `website_crawled` - Boolean flag
- `job_descriptions_crawled` - Count of detailed job crawls

**Structured Data:**
- `key_signals` - ARRAY of top signals with scoring
- `tech_stack` - ARRAY of technologies with confidence levels
- `comprehensive_report` - VARCHAR(16MB) full markdown report

**Performance Metrics:**
- `exa_search_time_sec`, `exa_searches_completed`, `exa_searches_failed`
- `processing_time_sec`, `status`, `error_message`

### Report Structure (9 Sections)

1. **Company Overview** - Founding, HQ, employees, revenue, leadership
2. **Airflow Mission Critical Assessment** - Grade (A/B/C/D), criticality analysis
3. **Recent News & Corporate Strategy** - Product updates, market position, priorities
4. **Data Orchestration & Hiring Intelligence** - Tech stack, job openings, talent flow
5. **Pain Points & Customer Challenges** - Industry challenges addressed
6. **Competitive Intelligence** - Market positioning, differentiation
7. **Web Presence & Growth Metrics** - Traffic, social metrics, employer ratings
8. **Product Suite Overview** - Core products and features
9. **Summary & Outlook** - Key takeaways, market strengths, 2026 outlook

## Exa Search Strategy (9 Searches)

### Batch A (5 parallel searches):
1. **Company Research** - Overview, metrics, leadership
2. **Orchestration** - Airflow/Dagster/Prefect mentions (12mo filter)
3. **Hiring** - Data engineer/platform engineer jobs (6mo filter, company job boards)
4. **News** - Corporate strategy, funding, acquisitions
5. **Blog Posts** - Engineering blogs about data infrastructure (18mo filter)

### Batch B (2 parallel searches):
6. **Product Announcements** - Launches, releases (12mo filter)
7. **Case Studies** - Customer stories, vendor partnerships (2 merged queries)

### Batch C (conditional):
8. **Website Crawl** - Homepage content (if domain provided)
9. **Job Descriptions** - Full job posting text (if hiring search found postings)

## Airflow Criticality Grading

### Grade A: Real-Time Critical
- Airflow downtime = immediate customer-facing outage
- Sub-minute latency requirements
- Examples: Fraud detection, recommendation engines

### Grade B: Mission-Critical Stack
- Airflow downtime delays operations and impacts SLAs
- Core business depends on pipelines (batch, hours-to-days)
- Examples: Daily reporting, ML training, data warehouse refreshes

### Grade C: Operational Tool
- Airflow used but not mission-critical
- Pipeline failures inconvenient but not blocking
- Examples: Internal analytics, ad-hoc data analysis

### Grade D: No Evidence
- No confirmed Airflow usage
- May use alternatives or no orchestration

## Querying Results (Claude Desktop)

Reps can ask Claude Desktop:

**Account Intelligence:**
- "Tell me about [company]"
- "What are [company]'s main pain points?"
- "How critical is Airflow to [company]?"

**Relationship Context:**
- "Summarize our relationship with [company]"
- "What did we discuss on the last call with [company]?"

**Strategic Analysis:**
- "Compare [company A] and [company B]"
- "Which accounts should I prioritize this quarter?"
- "Show me all Grade A Airflow accounts"

**Example SQL:**
```sql
SELECT acct_name, orchestration_mentions, comprehensive_report
FROM GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT
WHERE orchestration_mentions > 10
ORDER BY orchestration_mentions DESC;
```

## Configuration

### Rate Limiting

```python
# Conservative settings (free tier)
RateLimiter(rate_per_minute=60, burst=15)

# Enterprise settings
RateLimiter(rate_per_minute=300, burst=50)
```

### Search Configuration

```python
ExaSearchConfig(
    timeout_sec=15,
    max_retries=3,
    enable_website_crawl=True,
    enable_job_crawl=True,
    max_job_descriptions=2,
    news_months_back=12,
    hiring_months_back=6,
    orchestration_months_back=12,
    blog_months_back=18,
    product_months_back=12
)
```

## Manual Report Generation (No API Key)

If `ANTHROPIC_API_KEY` is not set, reports can be generated manually:

1. Run batch research (collects data only):
```bash
python3 batch_account_research.py --accounts "CompanyName"
```

2. Ask Claude Desktop:
```
"Generate a comprehensive report for CompanyName using data in Snowflake"
```

3. Claude queries `ACCOUNT_RESEARCH_OUTPUT` and generates report

**Benefits:**
- No API costs during testing/validation
- Flexibility to refine prompts
- Same quality as automated reports

## Project Structure

```
batch-gtm-agents/
├── batch_account_research.py    # Main script
├── prompts/                      # Report generation prompts
│   ├── README.md                # Prompt system documentation
│   ├── account_research_report_prompt.md
│   ├── airflow_mission_critical_assessment_prompt.md
│   └── extract_company_metrics_prompt.md
├── skills/                       # Claude skills (slash commands)
│   ├── astro-brand/              # Apply Astronomer brand to visual artifacts
│   ├── astro-docs/               # Search live Astronomer docs to answer product questions
│   ├── astro-org-user-lookup/    # Look up Astro product users from Snowflake
│   └── astro-pptx/               # Build branded Astronomer PowerPoint decks
├── README.md                    # This file
└── .gitignore                   # Excludes sensitive data
```

## Skills

Skills are Claude slash commands that automate specific GTM tasks. Install by copying the skill folder into `~/.claude/skills/`.

### `astro-brand`

Applies Astronomer's 2026 brand guidelines (colors, fonts, logo rules, writing style) to any visual artifact — PDFs, HTML pages, posters, Word docs. For PowerPoint output, use `astro-pptx` instead.

```
/astro-brand
```

### `astro-docs`

Searches astronomer.io and the live Astronomer docs to answer product questions. Always fetches current pages rather than relying on training data — critical since the product changes frequently (e.g., Astro Hybrid was retired). Handles pricing questions via a two-source approach: a bundled price book for structure + Snowflake Metronome queries for actual rates.

```
/astro-docs
```

**Setup:** Requires the `price-book.md` file to be present in `~/.claude/skills/astro-docs/` alongside `SKILL.md`. Also requires Snowflake access to `HQ.MODEL_FINANCE.METRONOME_RATE_CARDS` and `METRONOME_RATE_CARD_ITEMS` for pricing queries.

### `astro-org-user-lookup`

Looks up Astro product user names and email addresses for a customer org from Snowflake. Requires the `HQ_MODEL_ASTRO_PII_USERS_READER` role.

```
/astro-org-user-lookup [account name]
```

**Setup:** Requires Snowflake access and the `HQ_MODEL_ASTRO_PII_USERS_READER` role granted to your user.

### `astro-pptx`

Builds branded Astronomer PowerPoint presentations using python-pptx. Handles slide structure, dark/light mode layouts, font assignment, charts (matplotlib PNGs), and visual QA. Includes 8 named layout patterns from real Astronomer decks.

```
/astro-pptx
```

**Setup:** Requires `python-pptx` (`pip install python-pptx`). The `assets/` folder contains a real example deck for design reference. Fonts (League Gothic, Roboto, Roboto Mono) must be installed locally for full fidelity.

## Testing & Validation

**Test accounts:**
- Quickbase: Grade C (5 orchestration mentions, no-code platform)
- Grindr: Grade B (21 mentions, customer with 27 calls)
- GridX: Grade B (31 mentions, highest signal)

**Validation checklist:**
- ✅ All 9 sections present in reports
- ✅ (VERIFIED) and (ASSESSED) markers used appropriately
- ✅ Evidence-based Airflow grading
- ✅ Competitive intelligence included
- ✅ Actionable sales recommendations

## Future Enhancements

- [ ] Metric extraction function (employees, revenue, growth rates)
- [ ] Enhanced Gong transcript analysis in reports
- [ ] Saved query templates for common rep questions
- [ ] Airflow batch job for scheduled execution
- [ ] Dashboard for account prioritization

## Cost Optimization

**Current approach (hybrid):**
- Run batch data collection nightly ($0.009/account for Exa)
- Generate reports on-demand via Claude Desktop (no API cost)
- Automate reports only for strategic accounts

**Full automation:**
- Add ANTHROPIC_API_KEY to environment
- Reports auto-generate and save to Snowflake
- Cost: $0.03/account total

## Support

For questions or issues:
- Review prompt templates in `/prompts/README.md`
- Check Snowflake query examples in `~/claude-work/query_comprehensive_reports.sql`
- Test workflow documented in `~/claude-work/test_report_generation.md`

---

**Last Updated**: April 1, 2026
**Version**: 2.0 (Comprehensive Exa integration with optional report automation)
