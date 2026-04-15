# Merge Summary: test_improved_searches.py → batch_account_research.py

## Date: April 14, 2026

## Overview
Successfully merged the improved v2 search prompts from `test_improved_searches.py` into the production `batch_account_research.py` script.

## Changes Made

### 1. Search Function Updates (7 searches)

#### ✅ Search 1: Company Research
- **Status**: UNCHANGED
- Kept existing query: `"{company_name} company overview"`

#### ✅ Search 2: Orchestration → GitHub Evidence
- **Old**: `_search_orchestration` - generic "data pipeline orchestration airflow dagster prefect"
- **New**: `_search_github_evidence` - targets actual GitHub repos
- **Query**: `site:github.com/{company_slug} OR site:github.com "{company_name}" (airflow OR dags OR workflows OR kubernetes OR terraform OR infrastructure)`
- **Improvement**: Finds actual code repos, not generic articles

#### ✅ Search 3: Hiring → Hiring + Tech Stack (Expanded)
- **Old**: 5 results, highlights only
- **New**: 10 results with full text extraction
- **Added**: `domain` parameter for company careers pages
- **Query**: Expanded to include more roles (SRE, analytics engineer, backend engineer)
- **Key**: Now includes `"contents": {"highlights": True, "text": True}` for tech stack extraction
- **Job sites**: greenhouse.io, lever.co, linkedin.com/jobs, plus company careers page

#### ✅ Search 4: News → Trigger Events (Focused)
- **Old**: `_search_news` - generic "corporate strategy news"
- **New**: `_search_trigger_events` - focused on funding/M&A/exec hires only
- **Query**: `(funding OR "series A/B/C" OR acquired OR "new CEO/CTO/CDO" OR hired) (2025 OR 2026) (site:techcrunch.com OR site:crunchbase.com OR site:businesswire.com)`
- **Improvement**: No more generic news, only high-signal events

#### ✅ Search 5: Blog Posts → Engineering Blog (Domain-Restricted)
- **Old**: `_search_blog_posts` - generic query across all sites
- **New**: `_search_engineering_blog` - company domain + Medium only
- **Added**: `domain` parameter (required)
- **Query**: `(site:{domain}/blog OR site:{domain}/engineering OR site:medium.com/@{slug}) (architecture OR "tech stack" OR "how we built") (airflow OR kubernetes OR dbt)`
- **Improvement**: Restricts to company's own blog, not third-party articles

#### ✅ Search 6: Product Announcements (Improved)
- **Old**: No domain filtering
- **New**: Added optional domain filtering
- **Query**: `{company_name} (launched OR announces OR "general availability") ({domain_clause}site:producthunt.com OR site:techcrunch.com)`

#### ✅ Search 7: Case Studies (Vendor Domain-Restricted)
- **Old**: 2 separate queries (generic + vendor), merged results
- **New**: Single query restricted to vendor domains only
- **Query**: `{company_name} ("case study" OR "customer story" OR "built with") (site:snowflake.com OR site:databricks.com OR site:getdbt.com OR site:aws.amazon.com)`
- **Improvement**: Only finds authentic case studies published by vendors

### 2. Tech Stack Extraction (NEW)

Added `extract_tech_stack_from_jobs()` function:
- Extracts tech stack from job posting full text
- Detects 24 technologies across 5 categories:
  - **Orchestration**: Airflow, Dagster, Prefect, Luigi, Argo
  - **Cloud**: AWS, GCP, Azure
  - **Data Warehouse**: Snowflake, Databricks, Redshift, BigQuery
  - **Processing**: Spark, Flink, Kafka
  - **Transformation**: dbt, Dataform
  - **Container/Infra**: Kubernetes, Docker, Terraform
  - **Languages**: Python, Scala, Java, SQL
- Returns: `{tech_name: {count: N, sources: [urls]}}`
- Added to `metadata['tech_stack_from_jobs']` in ExaResearchResult

### 3. Data Structure Updates

#### ResearchResult Dataclass
Added new fields:
```python
tech_stack_from_jobs: Optional[str] = None  # JSON text
classification: Optional[str] = None  # CUSTOMER, ENGAGED PROSPECT, etc.
airflow_signals: Optional[List[str]] = None
has_airflow_signal: Optional[bool] = None
```

#### ExaResearchResult Metadata
Added to metadata dict:
- `github_evidence_count`
- `trigger_events_count`
- `engineering_blog_count`
- `tech_stack_from_jobs`

### 4. Snowflake V2 Output (NEW)

Created `save_to_v2_gtm_batch_output()` function:
- Inserts into `HQ.GTM.V2_GTM_BATCH_OUTPUT`
- Schema matches DDL in `ddl_v2_gtm_batch_output.sql`
- Includes:
  - Snowflake context (SF_ACCT_ID, SF_IS_CUSTOMER, contacts, MQLs, opps, Gong calls)
  - Web search result counts (7 searches)
  - Full web search results as VARIANT
  - Tech stack from jobs as VARIANT
  - Classification & Airflow signals
  - RAW_JSON backup
- Uses `WHERE NOT EXISTS` for idempotency

### 5. Function Call Updates

#### In `fetch_exa_research_v2()`:
```python
# OLD Batch A
_search_orchestration(...)
_search_hiring(...)
_search_news(...)
_search_blog_posts(...)

# NEW Batch A
_search_github_evidence(...)
_search_hiring(..., domain)  # Added domain param
_search_trigger_events(...)
_search_engineering_blog(..., domain)  # Added domain param
```

#### In Batch B:
```python
_search_product_announcements(..., domain)  # Added domain param
```

### 6. Helper Functions

Added:
- `_count_results(search_result)` - Generic counter for any search result
- Updated metadata counters to use new search names

## Backward Compatibility

✅ Maintained:
- Legacy `fetch_exa_research()` function (v1) unchanged
- Existing `save_to_snowflake()` for `GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT` unchanged
- All existing dataclass fields preserved
- Brave Search fallback logic maintained

## Testing Checklist

- [x] Search functions updated with improved prompts
- [x] Tech stack extraction added
- [x] Data structures extended with v2 fields
- [x] Snowflake V2 insert function created
- [ ] Test on sample account (Trivelta)
- [ ] Verify Snowflake V2 table insert
- [ ] Verify tech stack extraction works
- [ ] Verify classification logic works

## Next Steps

1. Run DDL to create `HQ.GTM.V2_GTM_BATCH_OUTPUT` table
2. Test merged script on Trivelta: `python3 batch_account_research.py --accounts "Trivelta"`
3. Verify V2 table has data
4. Compare output quality vs old searches
5. Update calling code to use `save_to_v2_gtm_batch_output()`

## Files Modified

- `batch_account_research.py` - Main merge target
- `ddl_v2_gtm_batch_output.sql` - New Snowflake table DDL

## Files for Reference

- `test_improved_searches.py` - Source of improved prompts
- `test_results_trivelta_20260414_232522.json` - Example output with new schema
