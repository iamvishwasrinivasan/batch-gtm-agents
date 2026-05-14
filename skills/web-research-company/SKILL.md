---
name: web-research-company
description: Research a company using Exa web search and store results in Snowflake GTM.PUBLIC.COMPANY_WEB_SIGNALS table
trigger_phrases:
  - research company
  - web research
  - company signals
---

# Web Research Company Skill

Research a company's web signals (jobs, acquisitions, product launches, executive hires, strategic news) using Exa API and store in Snowflake.

## Usage

```bash
python3 company_web_signals.py "Company Name" domain.com
```

Or batch mode:
```bash
python3 company_web_signals.py companies.csv
```

## What it does

1. **Researches company overview** - What the company does, industry, business model
2. **Finds job postings** (last 12 months):
   - Searches Greenhouse, Lever, Ashby, LinkedIn for data engineering roles
   - Extracts tech stack: orchestration tools (Airflow, Dagster, Prefect)
   - Extracts data tools (dbt, Snowflake, Spark, etc.)
3. **Finds acquisitions** (last 2 years) - M&A activity
4. **Finds product launches** (last 2 years) - New products, features
5. **Finds C-suite hires** (last 2 years) - CEO, CTO, CFO, etc.
6. **Finds strategic announcements** (last 2 years) - Partnerships, expansions
7. **Finds SEC filings** (last 2 years) - 10-K reports for public companies

## Output

Stores one row per company in `GTM.PUBLIC.COMPANY_WEB_SIGNALS`:
- COMPANY_NAME, DOMAIN, RESEARCH_DATE
- COMPANY_OVERVIEW (text)
- JOBS (JSON array with orchestration_tools and data_tools tags)
- ACQUISITIONS (JSON array)
- PRODUCT_RELEASES (JSON array)
- C_SUITE_HIRES (JSON array)
- STRATEGIC_ANNOUNCEMENTS (JSON array)
- SEC_FILINGS (JSON array)

## Example

```bash
python3 company_web_signals.py "Trivelta" trivelta.com
```

Results in Snowflake:
```sql
SELECT * FROM GTM.PUBLIC.COMPANY_WEB_SIGNALS WHERE DOMAIN = 'trivelta.com'
```

Rep can then query:
```sql
-- Find companies hiring for Airflow
SELECT COMPANY_NAME, JOBS 
FROM GTM.PUBLIC.COMPANY_WEB_SIGNALS 
WHERE JOBS[0]:orchestration_tools[0]::STRING = 'Airflow';

-- See their full tech stack
SELECT COMPANY_NAME, JOBS[0]:data_tools 
FROM GTM.PUBLIC.COMPANY_WEB_SIGNALS 
WHERE DOMAIN = 'trivelta.com';
```

## Requirements

- EXA_API_KEY environment variable
- Snowflake config at ~/.snowflake/service_config.yaml
- Python packages: snowflake-connector-python, cryptography, requests, pyyaml

## Setup

1. Set EXA_API_KEY:
```bash
export EXA_API_KEY="your-key-here"
```

2. Ensure Snowflake config exists at `~/.snowflake/service_config.yaml`:
```yaml
snowflake:
  account: "GP21411.us-east-1"
  user: "VISHWASRINIVASAN"
  private_key_path: "~/.ssh/rsa_key_unencrypted.p8"
  role: "GTMADMIN"
  warehouse: "HUMANS"
  database: "GTM"
```

3. Install dependencies:
```bash
pip install snowflake-connector-python cryptography requests pyyaml
```

## Batch CSV Format

For batch processing, create a CSV with headers:
```
company_name,domain
Trivelta,trivelta.com
GridX,gridx.ai
```

Then run:
```bash
python3 company_web_signals.py companies.csv
```
