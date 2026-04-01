# Account Research Report Generation System

This directory contains prompt templates for generating comprehensive, i360-style account research reports.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│ 1. Data Collection (DONE ✅)                            │
│    - batch_account_research.py                          │
│    - 9 Exa searches per account                         │
│    - Snowflake CRM context                              │
│    - Gong transcripts                                   │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 2. Metric Extraction (TODO 🔨)                          │
│    - Extract structured data from search results        │
│    - Employee count, revenue, growth rates              │
│    - Job openings, talent flow                          │
│    - Website traffic, social metrics                    │
│    - Uses: extract_company_metrics_prompt.md            │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 3. Airflow Assessment (TODO 🔨)                         │
│    - Score: A/B/C/D                                     │
│    - Mission-criticality analysis                       │
│    - Evidence-based reasoning                           │
│    - Uses: airflow_mission_critical_assessment_prompt.md│
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 4. Report Synthesis (TODO 🔨)                           │
│    - Combine metrics + assessment + raw research        │
│    - Generate 9-section narrative report                │
│    - Add (VERIFIED) marks                               │
│    - Uses: account_research_report_prompt.md            │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 5. Output                                                │
│    - Markdown report (i360-style)                       │
│    - Save to Account Context folder                     │
│    - Store in Snowflake (optional)                      │
└─────────────────────────────────────────────────────────┘
```

---

## Current State (What We Have)

### ✅ **Data Collection Layer** - COMPLETE

**File**: `/Users/vishwasrinivasan/scripts/batch_account_research.py`

**What it does:**
- Runs 9 comprehensive Exa searches per account:
  1. Company research overview
  2. Orchestration evidence (Airflow, Dagster, Prefect)
  3. Hiring signals (job postings)
  4. Corporate news and strategy
  5. Engineering blog posts
  6. Product announcements
  7. Case studies and customer stories
  8. Website crawl
  9. Job description details
- Fetches Snowflake CRM context (contacts, MQLs, opps, Gong calls)
- Saves to Snowflake: `GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT`
- Saves JSON files: `~/claude-work/batch-research-output/`

**Output quality:**
- 21 orchestration mentions for Grindr ✅
- 7/9 searches successful per account ✅
- Tech stack with confidence scores ✅
- Structured signals with scoring ✅

**What's missing:**
- ❌ Reports are just raw data + transcripts
- ❌ No narrative synthesis
- ❌ No Airflow mission-critical assessment
- ❌ No growth metrics extraction (employees, revenue, traffic)
- ❌ No competitive analysis

---

## Next Steps (What We Need to Build)

### 🔨 **Step 2: Metric Extraction Function**

**Goal**: Extract structured quantitative metrics from Exa search results

**Function to create**: `extract_company_metrics()`

**Prompt**: `extract_company_metrics_prompt.md`

**Input**:
```python
exa_search_results = {
    "company_research": {...},
    "hiring": {...},
    "news": {...},
    "blog_posts": {...},
    "website_crawl": {...},
    "job_descriptions": [...]
}
```

**Output**:
```python
{
    "employees": {"current": 83, "yoy_change_pct": 2.8},
    "revenue": {"amount": 26500000, "confidence": "medium"},
    "website_traffic": {"monthly_visits": 33631, "yoy_change_pct": 354.5},
    "job_openings": {"current": 3, "qoq_change_pct": 200.0},
    "leadership": [{"name": "CEO Name", "title": "CEO"}],
    ...
}
```

**Implementation approach:**
- Use Claude API or direct LLM calls
- Feed search results + extraction prompt
- Parse structured JSON output
- Validate and store in new Snowflake columns

---

### 🔨 **Step 3: Airflow Assessment Function**

**Goal**: Generate "Airflow Mission Critical Assessment" section with scoring

**Function to create**: `assess_airflow_criticality()`

**Prompt**: `airflow_mission_critical_assessment_prompt.md`

**Input**:
```python
{
    "company_name": "i360",
    "orchestration_mentions": 12,
    "search_results": {...},
    "tech_stack": [...]
}
```

**Output**:
```python
{
    "grade": "B",
    "grade_name": "Mission-Critical Stack, Airflow Support",
    "criticality": "Medium",
    "reasoning": "i360 operates a mission-critical political...",
    "evidence_points": [
        "Confirmed Apache Airflow usage in job descriptions",
        "Daily model updates using machine learning",
        ...
    ]
}
```

---

### 🔨 **Step 4: Report Synthesis Function**

**Goal**: Combine all data into i360-style narrative report

**Function to create**: `generate_comprehensive_report()`

**Prompt**: `account_research_report_prompt.md`

**Input**:
```python
{
    "account_name": "Grindr",
    "snowflake_context": {...},
    "exa_research": {...},
    "extracted_metrics": {...},
    "airflow_assessment": {...}
}
```

**Output**: Markdown report with 9 sections
1. Company Overview
2. Airflow Mission Critical Assessment
3. Recent News & Corporate Strategy
4. Data Orchestration & Hiring Intelligence
5. Pain Points & Customer Challenges
6. Competitive Intelligence
7. Web Presence & Growth Metrics
8. Product Suite Overview
9. Summary & Outlook

**Save to**: `/Users/vishwasrinivasan/Account Context/{company_name}/`

---

## Prompt Files Reference

| Prompt File | Purpose | Used By |
|------------|---------|---------|
| `extract_company_metrics_prompt.md` | Extract structured data (employees, revenue, growth) | Metric extraction function |
| `airflow_mission_critical_assessment_prompt.md` | Score Airflow criticality (A/B/C/D) | Assessment function |
| `account_research_report_prompt.md` | Generate full narrative report | Report synthesis function |

---

## Example Usage (Future)

```python
# After batch_account_research.py runs...

# Step 2: Extract metrics
metrics = extract_company_metrics(
    exa_search_results=exa_result.search_results,
    company_name="Grindr"
)

# Step 3: Assess Airflow criticality
assessment = assess_airflow_criticality(
    company_name="Grindr",
    orchestration_mentions=exa_result.metadata['orchestration_mentions'],
    search_results=exa_result.search_results,
    tech_stack=exa_result.tech_stack
)

# Step 4: Generate comprehensive report
report_md = generate_comprehensive_report(
    account_name="Grindr",
    snowflake_context=sf_context,
    exa_research=exa_result,
    extracted_metrics=metrics,
    airflow_assessment=assessment
)

# Step 5: Save to Account Context folder
save_path = f"/Users/vishwasrinivasan/Account Context/{company_name}/{company_name}_research_{date}.md"
with open(save_path, 'w') as f:
    f.write(report_md)
```

---

## Comparison: Current vs Target

### **Current Output (Grindr)**
```markdown
# Grindr - Account Research

**Tier:** customer
**Priority Score:** 10/10

## CRM Summary
- **Contacts:** 93
- **MQLs:** 4
- **Opportunities:** 13
- **Gong Calls:** 27

## Gong Call Transcripts
[20 pages of raw transcripts...]

## Web Research Signals
- "The Astronomer Blog: Data Orchestration..."
- "Grindr Goes 'AI-First'..."
```

### **Target Output (i360-style)**
```markdown
# Company Research Report: Grindr

**Generated**: 2026-03-31 16:43:00

---

## Company Overview

**Grindr** is the world's largest social networking app for gay, bi, trans, and queer people, serving millions of users globally with location-based discovery and communication features. **(VERIFIED)**

**Founded**: 2009 **(VERIFIED)**
**Headquarters**: West Hollywood, California **(VERIFIED)**
**Employees**: 500+ (+15.2% YoY) **(VERIFIED)**
**Public**: NASDAQ: GRND (IPO November 2022) **(VERIFIED)**

---

## Airflow Mission Critical Assessment

### Score: **A (Real-Time Critical)**

### Airflow Criticality: **High**

### The "Why":

Grindr operates a **real-time social networking platform** where millisecond-level latency is critical for user experience. Apache Airflow orchestrates mission-critical data pipelines including ML model training for matching algorithms, content moderation workflows, and user analytics. **(VERIFIED)**

**Evidence for High Criticality**:

1. **Confirmed Apache Airflow Usage**: Grindr's engineering blog and job postings explicitly mention Apache Airflow for data pipeline orchestration. **(VERIFIED)**

2. **ML Model Pipeline**: "We use Airflow to orchestrate daily retraining of our recommendation models using fresh user interaction data..." **(VERIFIED)**

[... continues with detailed analysis ...]

---

## Recent News & Corporate Strategy (2025-2026)

### Product & Platform Updates

**AI-First Strategy**: Grindr announced in January 2026 its pivot to becoming an "AI-first" platform, using machine learning for content moderation, profile recommendations, and user safety features. **(VERIFIED)**

[... continues ...]
```

---

## Implementation Priority

1. **Phase 1** (Week 1): Build metric extraction function
2. **Phase 2** (Week 1): Build Airflow assessment function
3. **Phase 3** (Week 2): Build report synthesis function
4. **Phase 4** (Week 2): Integrate into batch_account_research.py
5. **Phase 5** (Week 3): Test with 10 accounts and refine prompts

---

## Questions?

1. **Where do reports get saved?**
   - Primary: `/Users/vishwasrinivasan/Account Context/{company}/`
   - Backup: Snowflake (new column: `comprehensive_report_md`)

2. **How long does this take?**
   - Data collection: 4-8 seconds per account (already built)
   - Metric extraction: ~5 seconds (LLM call)
   - Airflow assessment: ~5 seconds (LLM call)
   - Report synthesis: ~10 seconds (LLM call)
   - **Total: ~30 seconds per account**

3. **Can reps ask questions about these reports?**
   - Yes! Reports saved in Account Context folders
   - Claude Desktop can read them
   - Structured data also in Snowflake for queries

4. **What about costs?**
   - Exa API: 9 searches × $0.001 = $0.009 per account
   - Claude API (report generation): ~$0.02 per account
   - **Total: ~$0.03 per account**
   - 1000 accounts = $30

---

Last updated: 2026-03-31
