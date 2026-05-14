# Company Web Signals DAG for Astro

Airflow DAG to ingest company research data using the `web-research-company` skill and store in Snowflake.

## What This Is

An Astro (Apache Airflow) project that orchestrates company research at scale:
- Uses Exa API to research companies
- Extracts tech stack from job postings
- Finds announcements, funding, C-suite hires
- Stores everything in Snowflake: `GTM.PUBLIC.COMPANY_WEB_SIGNALS`

## Quick Start

### Deploy to Astro

```bash
cd DAGs/

# Deploy to your Astro workspace
astro deploy <your-deployment-id>
```

### Required Environment Variables

Set these in your Astro deployment:

- `EXA_API_KEY` - Your Exa API key (secret)
- `SNOWFLAKE_ACCOUNT` - Your Snowflake account
- `SNOWFLAKE_USER` - Your Snowflake username
- `SNOWFLAKE_ROLE` - Snowflake role (e.g., GTMADMIN)
- `SNOWFLAKE_WAREHOUSE` - Snowflake warehouse (e.g., HUMANS)
- `SNOWFLAKE_DATABASE` - Database name (e.g., GTM)

### Required: Snowflake Private Key

1. Copy your Snowflake private key to `include/.ssh/rsa_key.p8`
2. **DO NOT commit this to git** (already in .gitignore)

## Trigger the DAG

### Single Company

```json
{
  "company_name": "Acme Corp",
  "domain": "acme.com"
}
```

### Multiple Companies

```json
{
  "companies": [
    {"company_name": "Acme", "domain": "acme.com"},
    {"company_name": "GridX", "domain": "gridx.ai"}
  ]
}
```

## What Gets Researched

For each company:
- Company Overview
- Job Postings (last 12 months) with tech stack
- Major Announcements (last 2 years)
- Product Releases (last 2 years)
- C-Suite Hires (last 2 years)
- Strategic Announcements (last 2 years)
- Company Metrics

## Based On

This DAG uses the `web-research-company` skill from `../skills/web-research-company/`
