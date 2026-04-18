---
name: account-research
description: Research a company for Astronomer sales fitness using Snowflake (SF_ACCOUNTS, SF_CONTACTS, SF_OPPS, LF_WEBSITE_VISITS, Gong transcripts), web search, and Apollo. Generates a fit score and AE brief. Snowflake is the primary intelligence source — web research fills gaps Snowflake can't answer.
version: 2.0.0
---

# Account Research Orchestrator

Research companies for Astronomer (Apache Airflow) sales fitness. Snowflake is the primary data source for CRM intelligence (contacts, buying signals, opp history, Leadfeeder visits, Gong transcripts, scores). Web research is the primary source for tech stack — HG Insights and DataFox signals in Salesforce are unreliable and must not be treated as verified. Always confirm stack via job postings, engineering blog, GitHub, and web search.

## Input
The user has provided: {{args}}

- Single company: `{COMPANY}, {DOMAIN}` (e.g., "Acme Corp, acme.com")
- Batch mode: `batch: /path/to/file.csv` (CSV with columns: company_name, domain)
- Batch force-rerun: `batch: /path/to/file.csv force`

## Constants
- **Prompts Directory**: `~/claude-work/research-assistant/prompts/`
- **Output Directory**: `~/claude-work/research-assistant/outputs/accounts/`
- **Apollo Field ID**: `{YOUR_APOLLO_RESEARCH_FIELD_ID}`

---

## SINGLE COMPANY MODE

### Step 1: Parse Input
Extract `COMPANY_NAME` and `DOMAIN`. Strip `http://`, `www.`, trailing slashes. If only a name is given, search for the domain first.

### Step 2: Snowflake Intelligence Dump

Run template check and Apollo key check in bash while simultaneously firing the first Snowflake query:

```bash
for f in ~/claude-work/research-assistant/prompts/01_fit_scoring.md \
          ~/claude-work/research-assistant/prompts/02_account_research.md; do
  [ -f "$(eval echo $f)" ] || { echo "TEMPLATE MISSING: $f — aborting."; exit 1; }
done
echo "TEMPLATES OK"
[ -n "$APOLLO_API_KEY" ] && echo "APOLLO: key set" || echo "APOLLO: no key"
```

**Query A — Account profile** (run immediately, domain match):
```sql
SELECT
  a.ACCT_ID, a.ACCT_NAME, a.ACCT_DOMAIN, a.ACCT_TYPE, a.ACCT_STATUS,
  a.IS_CURRENT_CUST, a.IS_CHURNED_CUST, a.CUSTOMER_SINCE_DATE,
  a.INDUSTRY, a.OWNER_NAME, a.SALES_REGION, a.SEGMENT_PLANNED,
  a.ICP_DESIGNATION_V2, a.ACCT_SCORE, a.ACCT_SCORE_POSITIVE_DRIVERS,
  a.ACCT_SCORE_NEGATIVE_DRIVERS, a.SMOKE_SCORE, a.FIRE_SCORE,
  a.LAST_MQL_DATE, a.LAST_COSMOS_DOC_VIEW_DATE, a.LAST_DAG_FACTORY_DOWNLOAD_DATE,
  a.BILLING_COUNTRY, a.SHIPPING_COUNTRY
FROM HQ.MODEL_CRM.SF_ACCOUNTS a
WHERE LOWER(a.ACCT_DOMAIN) LIKE LOWER('%{DOMAIN}%')
  AND a.ACCT_TYPE NOT IN ('Internal', 'Competitor')
ORDER BY a.IS_CURRENT_CUST DESC, a.ACCT_SCORE DESC NULLS LAST
LIMIT 5
```

Store: `SF_ACCT_ID`, `SF_ACCOUNT_FOUND` (true/false), all signal fields.

**After Query A resolves**, extract `SF_ACCT_ID` and fire Queries B–H in parallel:

**Query B — Contacts with person-level intent signals:**
```sql
SELECT
  c.TITLE, c.LEAD_SCORE_GRADE, c.CONTACT_STATUS,
  c.LAST_VISITED_PRICING_PAGE_DATE,
  c.LAST_VISITED_DEBUGGING_AIRFLOW_PAGE_DATE,
  c.LAST_VISITED_DEBUGGING_DAGS_PAGE_DATE,
  c.LAST_MQL_DATE, c.IS_OPTED_OUT_OF_EMAIL, c.CONTACT_URL,
  c.LAST_ACTIVITY_TS
FROM HQ.MODEL_CRM.SF_CONTACTS c
WHERE c.ACCT_ID = '{SF_ACCT_ID}'
  AND c.IS_DELETED = FALSE
ORDER BY c.LAST_ACTIVITY_TS DESC NULLS LAST
LIMIT 20
```
If `SF_ACCOUNT_FOUND=false`: skip, record "No Salesforce account found — contact intelligence unavailable."

**Query C — Leadfeeder website visits** (replaces entire Leadfeeder MCP):
```sql
SELECT
  v.VISIT_TS, v.LANDING_PAGE, v.PAGE_VIEW_COUNT,
  v.VISIT_DURATION, v.SOURCE, v.MEDIUM, v.CAMPAIGN_NAME,
  p.PAGE_URL, p.PAGE_NAME, p.PAGEVIEW_TS
FROM HQ.MODEL_CRM.LF_WEBSITE_VISITS v
JOIN HQ.MODEL_CRM.LF_PAGE_VIEWS p ON v.LF_VISIT_ID = p.LF_VISIT_ID
WHERE v.SF_ACCT_ID = '{SF_ACCT_ID}'
  AND v.VISIT_TS >= DATEADD(month, -6, CURRENT_DATE)
ORDER BY v.VISIT_TS DESC
LIMIT 200
```
If `SF_ACCOUNT_FOUND=false`: skip, record "No Leadfeeder data — account not in Salesforce."

**Query D — Opportunity history** (Airflow experience, competition, loss reasons):
```sql
SELECT
  o.OPP_NAME, o.CURRENT_STAGE_NAME, o.IS_WON, o.IS_LOST,
  o.LOSS_REASON, o.LOSS_DETAILS, o.COMPETITION, o.CLOUD_PROVIDER,
  o.AIRFLOW_COMMITMENT, o.AIRFLOW_EXPERIENCE,
  o.CURRENT_AIRFLOW_DEPLOYMENT_MODEL, o.CURRENT_AIRFLOW_VERSIONS,
  o.CURRENT_AIRFLOW_ENVIRONMENTS_COUNT, o.AIRFLOW_EXPERIENCE,
  o.CREATED_DATE, o.WON_DATE, o.LOST_DATE, o.TOTAL_ACV, o.NEW_BUSINESS_ACV,
  o.LEAD_SOURCE, o.DISCOVERY_MEETING_DATE
FROM HQ.MODEL_CRM.SF_OPPS o
WHERE o.ACCT_ID = '{SF_ACCT_ID}'
ORDER BY o.CREATED_DATE DESC
LIMIT 15
```
If `SF_ACCOUNT_FOUND=false`: skip, record "No opportunity history."

**Query E — Gong call enrichments (pre-computed Cortex signals, preferred):**
```sql
SELECT
  e.CALL_ID, e.ACCT_NAME, e.CALL_DATE,
  e.SENTIMENT_SCORE, e.DEAL_RISK,
  e.TECH_STACK, e.PAIN_POINTS, e.COMPETITORS, e.AIRFLOW_TOPICS,
  c.CALL_TITLE, c.CALL_URL, c.CALL_BRIEF, c.CALL_NEXT_STEPS,
  c.PRIMARY_EMPLOYEE, c.CALL_DURATION
FROM GTM.PUBLIC.GONG_CALL_ENRICHMENTS_V e
JOIN HQ.MODEL_CRM_SENSITIVE.GONG_CALLS c ON c.CALL_ID = e.CALL_ID AND c.IS_DELETED = FALSE
WHERE e.ACCT_ID = '{SF_ACCT_ID}'
ORDER BY e.CALL_DATE DESC
LIMIT 20
```
Set `ENRICHMENTS_FOUND = true` if any rows returned. This replaces reading raw transcripts for all accounts in your book.

**Query E-fallback — Raw Gong transcripts (only if ENRICHMENTS_FOUND=false):**
```sql
SELECT
  t.CALL_ID, t.CALL_TITLE, t.CALL_URL, t.SCHEDULED_TS,
  t.ACCT_NAME, t.OPP_NAME, c.OPP_STAGE_AT_CALL, c.CALL_DURATION,
  t.CALL_BRIEF, t.CALL_NEXT_STEPS, t.ATTENDEES,
  c.PRIMARY_EMPLOYEE, t.FULL_TRANSCRIPT
FROM HQ.MODEL_CRM_SENSITIVE.GONG_CALL_TRANSCRIPTS t
JOIN HQ.MODEL_CRM_SENSITIVE.GONG_CALLS c ON t.CALL_ID = c.CALL_ID
WHERE UPPER(t.ACCT_NAME) LIKE UPPER('%{COMPANY_NAME}%')
  AND c.IS_DELETED = FALSE
ORDER BY t.SCHEDULED_TS DESC
```
If count > 20: fetch metadata first (without `FULL_TRANSCRIPT`), then fetch transcripts in parallel batches of 10 CALL_IDs. If no results, try first word of company name or known abbreviations.

**Query F — Zendesk ticket enrichments (parallel with B–E):**
```sql
SELECT
  e.TICKET_ID, e.TICKET_DATE, e.PRIORITY, e.STATUS,
  e.SENTIMENT_SCORE, e.ISSUE_CATEGORY, e.URGENCY_SIGNAL,
  e.KEY_PHRASES, e.PRODUCT_AREA
FROM GTM.PUBLIC.ZD_TICKET_ENRICHMENTS_V e
WHERE e.ACCT_ID = '{SF_ACCT_ID}'
ORDER BY e.TICKET_DATE DESC
LIMIT 30
```
If `SF_ACCOUNT_FOUND=false`: skip. If no rows: note "No support tickets found."

**Query G — Astro org / trial history (parallel with B–F):**
```sql
SELECT
  o.ORG_ID, o.ORG_NAME, o.ASTRO_ORG_STATE,
  o.FREE_TRIAL_START_DATE, o.TRIAL_EXPIRED_DATE,
  o.IS_GUIDED_TRIAL_ORG, o.TRIAL_REASON,
  o.AIRFLOW_COMMITMENT, o.AIRFLOW_PAIN,
  o.PROPENSITY_TO_PURCHASE,
  o.DEPLOYMENT_CREATED_DATE, o.FIRST_CODE_PUSH_DATE,
  o.FIRST_TASK_SUCCESS_DATE, o.FIRST_NON_EXAMPLE_DAG_DATE,
  o.CLICKED_INSTALL_CLI_BUTTON_DATE,
  o.ADDED_PAYMENT_METHOD_DATE,
  o.ASTRO_FREE_TRIAL_CREDIT_USAGE, o.ASTRO_FREE_TRIAL_CREDITS_ISSUED,
  o.FIRST_VIEWED_PRICING_PAGE_DATE, o.ASTRO_PLAN_UPGRADE_REQUEST,
  o.CREATED_TS, o.SF_RECORD_URL
FROM HQ.MODEL_CRM.SF_ASTRO_ORGS o
WHERE o.ACCT_ID = '{SF_ACCT_ID}'
ORDER BY o.CREATED_TS DESC
```
If `SF_ACCOUNT_FOUND=false`: skip. If no rows: note "No Astro org / trial history found."
Key fields to surface: `AIRFLOW_COMMITMENT` (self-reported in trial signup — highly reliable), `TRIAL_REASON`, `AIRFLOW_PAIN`, org state, whether they pushed real code and had task success, credit usage vs. issued (low usage = trial stalled).

**Query H — Campaign member history (parallel with B–F):**
```sql
SELECT
  cm.STATUS, cm.HAS_RESPONDED, cm.CREATED_TS, cm.FIRST_RESPONDED_TS,
  cm.JOB_TITLE, cm.COMPANY_OR_ACCOUNT,
  cm.WEBINAR_NAME, cm.FUNNEL_NAME, cm.EBOOK_NAME,
  cm.UTM_SOURCE, cm.UTM_CAMPAIGN,
  cm.MQL_QUALIFICATION_DATE, cm.ASSIGNED_AE_NAME, cm.ASSIGNED_SDR_NAME,
  cm.REPORTING_CHANNEL,
  c.CAMPAIGN_NAME, c.TYPE
FROM HQ.MODEL_CRM.SF_CAMPAIGN_MEMBERS cm
JOIN HQ.MODEL_CRM.SF_CAMPAIGNS c ON cm.CAMPAIGN_ID = c.CAMPAIGN_ID
WHERE cm.ACCT_ID = '{SF_ACCT_ID}'
ORDER BY cm.CREATED_TS DESC
LIMIT 30
```
If `SF_ACCOUNT_FOUND=false`: skip. If no rows: note "No campaign member history found."
Interpret results: webinars attended = active Airflow practitioner, ebooks downloaded = topic interest, free trial campaigns = prior product evaluation, pricing form fills = budget exploration. Note the campaign name verbatim — it reveals exactly what content resonated.

**SF MCP Secondary Pass — Queries I, J, K (run AFTER Snowflake queries complete):**

> These three objects have no Snowflake equivalent. Only attempt if `SF_ACCOUNT_FOUND=true`. Run all three in parallel. **Skip the entire pass gracefully if SF MCP auth fails** (AuthDecryptError or similar) — note "SF MCP auth unavailable; re-run `sf org login web --alias joey` to restore." Do not block report generation on SF MCP.

**Query I — Inbound email history (SF MCP — no Snowflake equivalent):**

Use `mcp__salesforce__run_soql_query`:
```sql
SELECT Id, Subject, FromAddress, FromName, ToAddress, MessageDate, TextBody, Status
FROM EmailMessage
WHERE Incoming = true
  AND ActivityId IN (SELECT Id FROM Task WHERE WhatId = '{SF_ACCT_ID}' AND Type = 'Email')
ORDER BY MessageDate DESC
LIMIT 30
```
Also via `RelatedToId`:
```sql
SELECT Id, Subject, FromAddress, FromName, MessageDate, TextBody, Status
FROM EmailMessage
WHERE RelatedToId = '{SF_ACCT_ID}'
  AND Incoming = true
ORDER BY MessageDate DESC
LIMIT 30
```
Combine and deduplicate by `Id`. Store as `EMAIL_HISTORY`. If empty: note "No inbound email history found in Salesforce."

**Query J — Opportunity contact roles (SF MCP — no Snowflake equivalent):**

Use `mcp__salesforce__run_soql_query`:
```sql
SELECT Role, IsPrimary, Contact.Name, Contact.Title, Contact.Email, Opportunity.Name, Opportunity.StageName, Opportunity.CloseDate
FROM OpportunityContactRole
WHERE Opportunity.AccountId = '{SF_ACCT_ID}'
ORDER BY Opportunity.CloseDate DESC
LIMIT 30
```
If empty: note "No opportunity contact roles found." Key signal: IsPrimary=true + Role="Decision Maker" or "Economic Buyer" = budget owner.

**Query K — Activity / task history (SF MCP — no Snowflake equivalent):**

Use `mcp__salesforce__run_soql_query`:
```sql
SELECT Subject, Description, ActivityDate, Status, Type, Who.Name, Who.Title, Owner.Name, CreatedDate
FROM Task
WHERE WhatId = '{SF_ACCT_ID}'
  AND IsDeleted = false
ORDER BY ActivityDate DESC NULLS LAST
LIMIT 30
```
If empty: note "No logged activity history found." Filter out automated Type='Email' tasks — focus on Type='Call', 'Meeting', or non-trivial Description.

**Query L — Account + contact notes + prior research (Snowflake — GTM.PUBLIC, parallel with B–H):**

```sql
SELECT NOTE_ID, NOTE_DATE, NOTE_TYPE, CONTENT, SOURCE, CREATED_AT
FROM GTM.PUBLIC.ACCOUNT_NOTES
WHERE ACCT_ID = '{SF_ACCT_ID}'
ORDER BY NOTE_DATE DESC
LIMIT 30
```

```sql
SELECT NOTE_ID, CONTACT_NAME, NOTE_DATE, NOTE_TYPE, CONTENT, SOURCE, CREATED_AT
FROM GTM.PUBLIC.CONTACT_NOTES
WHERE ACCT_ID = '{SF_ACCT_ID}'
ORDER BY NOTE_DATE DESC
LIMIT 30
```

```sql
SELECT RESEARCH_DATE, SCORE, GRADE, CONFIDENCE, MC_GRADE, DAYS_SINCE_RESEARCH, IS_STALE
FROM GTM.PUBLIC.ACCOUNT_RESEARCH_LATEST_V
WHERE ACCT_ID = '{SF_ACCT_ID}'
```

Combine all three. If `SF_ACCOUNT_FOUND=false`: skip. If notes empty: note "No account/contact notes found in GTM."
Store prior research result as `PRIOR_RESEARCH` (score, grade, confidence, mc_grade, research_date, is_stale). Use in Step 6 changelog diff — compare new score/grade against `PRIOR_RESEARCH` values instead of parsing the local file.
These are the AE's primary interaction log (pre-call briefs, email drafts, meeting summaries) — richer and more reliable than native SF notes.

**Apollo pre-fetch** (parallel with B–F, skip if no key):
```bash
source ~/.zshrc && curl -s -X POST "https://api.apollo.io/v1/accounts/search" \
  -H "Content-Type: application/json" \
  -d "{\"api_key\": \"$APOLLO_API_KEY\", \"q_organization_name\": \"{COMPANY_NAME}\", \"per_page\": 10}" \
  | python3 -c "
import json, sys
data = json.load(sys.stdin)
for a in data.get('accounts', []):
    if '{DOMAIN}'.lower() in (a.get('domain') or '').lower():
        print(f'APOLLO_ID={a[\"id\"]}')
        break
else:
    print('APOLLO_ID=null')
"
```

### Step 3: Research Depth

All accounts always get FULL research depth. Proceed directly to Step 4.

> Note: HG_AIRFLOW, DATAFOX_AIRFLOW, APACHE_AIRFLOW_ROLES, and EVIDENCE_OF_AIRFLOW are unreliable and must not be used for stack confirmation.

### Step 4: Targeted Web Research

Launch a **single web research agent** to run all 7 research items below.

**Context to pass to the agent from Step 2:**
- CRM status, opp history, contact intent signals, any Airflow mentions from Gong discovery. Do NOT pass HG/DataFox/CF stack signals — agent must independently confirm stack via web.

**Use Exa MCP tools for all web research:**
- `mcp__exa__web_search_exa` — standard keyword searches
- `mcp__exa__web_search_advanced_exa` — searches requiring date filters or domain restrictions
- `mcp__exa__company_research_exa` — company background, funding, self-description
- `mcp__exa__crawling_exa` — fetch specific URLs (replaces WebFetch)

1. **Job postings** — three parallel Exa searches:
   ```
   mcp__exa__web_search_exa('{COMPANY_NAME} site:greenhouse.io OR site:lever.co OR site:ashbyhq.com data engineer OR data platform OR platform engineer OR ML engineer OR MLOps OR analytics engineer OR data infrastructure')
   mcp__exa__web_search_exa('{COMPANY_NAME} site:greenhouse.io OR site:lever.co OR site:ashbyhq.com Apache Airflow OR dagster OR prefect OR data orchestration')
   mcp__exa__web_search_exa('site:linkedin.com/jobs {COMPANY_NAME} data engineer OR data platform OR MLOps OR Apache Airflow')
   ```
   After results: `mcp__exa__crawling_exa` on up to 3 job posting URLs. Extract: named tools verbatim, orchestration mentions, cloud platform, pain point language, team name.

2. **Recent news + M&A** — two parallel Exa searches:
   ```
   mcp__exa__web_search_advanced_exa('{COMPANY_NAME} funding OR acquisition OR Series OR layoff OR "new CTO" OR "Chief Data Officer"', start_published_date='2025-03-09')
   mcp__exa__web_search_exa('{COMPANY_NAME} acquired OR "acquired by" OR merger OR IPO OR bankruptcy OR shutdown')
   ```
   Determine M&A STATUS: ACQUIRED / MERGER / IPO / BANKRUPTCY / SHUTDOWN / NONE FOUND.

3. **Orchestration evidence**:
   ```
   mcp__exa__web_search_exa('"Apache Airflow" OR "Airflow DAG" OR dagster OR prefect {COMPANY_NAME}')
   ```

4. **Company overview + website**:
   ```
   mcp__exa__company_research_exa('{COMPANY_NAME}')
   mcp__exa__crawling_exa('https://{DOMAIN}')
   ```
   Extract: self-description, data-intensity signals, customer segments, partner logos.

5. **Engineering blog** — discovery + fetch:
   ```
   mcp__exa__web_search_advanced_exa('{COMPANY_NAME} engineering blog OR data infrastructure OR data platform OR pipeline', start_published_date='2024-09-01')
   ```
   `mcp__exa__crawling_exa` on top 1-2 post URLs. Extract: tools named verbatim, architecture decisions, pain points.

6. **Case studies + GitHub**:
   ```
   mcp__exa__web_search_exa('{COMPANY_NAME} Snowflake OR Databricks OR dbt OR AWS OR Google Cloud OR Azure case study OR customer OR partner')
   mcp__exa__web_search_exa('site:github.com {COMPANY_NAME} airflow OR dbt OR dagster OR prefect OR data pipeline')
   ```
   If GitHub org found, `mcp__exa__crawling_exa` on it.

7. **Conference speakers**:
   ```
   mcp__exa__web_search_exa('{COMPANY_NAME} airflowsummit.org OR dbt Coalesce OR Data Council employee speaker')
   ```

### Step 5: Generate Report Directly

Read both prompt templates:
- `~/claude-work/research-assistant/prompts/01_fit_scoring.md`
- `~/claude-work/research-assistant/prompts/02_account_research.md`

**Do not assemble a RAW INTELLIGENCE intermediate block.** Feed all data directly into a single generation pass:

**Context to the model** (in this order for cache efficiency):
1. Prompt template 1 (fit scoring rubric)
2. Prompt template 2 (AE brief template)
3. Snowflake data block (structured, labeled by source table)
4. Web research findings

**Snowflake data block format** (compact, structured):
```
=== SNOWFLAKE: SF_ACCOUNTS ===
CRM status: {IS_CURRENT_CUST / IS_CHURNED_CUST / prospect}
Owner: {OWNER_NAME} | Region: {SALES_REGION} | Segment: {SEGMENT_PLANNED}
Industry: {INDUSTRY} | Country: {BILLING_COUNTRY}
ICP: {ICP_DESIGNATION_V2} | Acct Score: {ACCT_SCORE} ({ACCT_SCORE_POSITIVE_DRIVERS} / {ACCT_SCORE_NEGATIVE_DRIVERS})
Smoke: {SMOKE_SCORE} | Fire: {FIRE_SCORE}
Last MQL: {LAST_MQL_DATE} | Cosmos doc: {LAST_COSMOS_DOC_VIEW_DATE} | DAG factory: {LAST_DAG_FACTORY_DOWNLOAD_DATE}

=== SNOWFLAKE: SF_CONTACTS (top contacts by recency) ===
[For each contact: Title | Lead score | Pricing page visit: {date or none} | Airflow debug visit: {date or none} | DAG debug visit: {date or none} | MQL: {date or none} | Opted out: {yes/no}]

=== SNOWFLAKE: LF_WEBSITE_VISITS ===
[Total visits (last 6mo): N | First: {date} | Last: {date}]
[Page list: URL | date | duration — flag /pricing, /demo, /astro, /trial as HIGH intent]
[If none: "No Leadfeeder visits — not matched in Salesforce or no visits."]

=== SNOWFLAKE: SF_OPPS ===
[For each opp: Name | Stage | Won/Lost | ACV | Created | Close date]
[Loss reason: {LOSS_REASON} — {LOSS_DETAILS}]
[Competition: {COMPETITION}]
[Airflow experience: {AIRFLOW_EXPERIENCE} | Deployment model: {CURRENT_AIRFLOW_DEPLOYMENT_MODEL} | Versions: {CURRENT_AIRFLOW_VERSIONS} | Env count: {CURRENT_AIRFLOW_ENVIRONMENTS_COUNT}]
[Cloud provider: {CLOUD_PROVIDER}]

=== SNOWFLAKE: GONG_CALL_ENRICHMENTS (pre-computed Cortex signals — full transcripts) ===
[Found N enriched calls / No enrichments — falling back to raw transcripts]
[Consolidated tech stack across all calls: {deduplicated list}]
[Consolidated pain points: {deduplicated list}]
[Competitors mentioned: {deduplicated list}]
[Airflow topics: {deduplicated list}]
[Per call: Date | Sentiment: {score} | Deal risk: {low/medium/high} | Brief | Next steps | URL]

=== SNOWFLAKE: ZD_TICKET_ENRICHMENTS (support health signals) ===
[Found N enriched tickets / No tickets]
[Per ticket: Date | Priority | Status | Sentiment: {score} | Urgency: {signal} | Category | Product area | Key phrases]
[If none: "No support tickets for this account."]

=== SNOWFLAKE: SF_ASTRO_ORGS (trial / product history) ===
[Found N orgs / No Astro org history]
[For each org: Org name | State: {ASTRO_ORG_STATE} | Trial: {FREE_TRIAL_START_DATE} → {TRIAL_EXPIRED_DATE}]
[Self-reported at signup: Airflow commitment: {AIRFLOW_COMMITMENT} | Trial reason: {TRIAL_REASON} | Airflow pain: {AIRFLOW_PAIN}]
[Product milestones: Deployment created: {date} | Code pushed: {date} | Task success: {date} | Own DAG: {date} | Payment method: {date or none}]
[Credit usage: {ASTRO_FREE_TRIAL_CREDIT_USAGE} of {ASTRO_FREE_TRIAL_CREDITS_ISSUED} issued | Propensity to purchase: {score}]
[If none: "No Astro org or trial history found."]

=== SNOWFLAKE: SF_CAMPAIGN_MEMBERS (marketing interaction history) ===
[Found N campaign interactions / No campaign history]
[Chronological list, newest first: Date | Campaign name | Type | Status | Responded: yes/no | Job title at time | UTM campaign]
[Flag by type: Free Trial = prior product evaluation | Pricing = budget exploration | Webinar (Attended) = active practitioner | Ebook (Responded) = topic interest | Webinar (Registered, not attended) = weak signal]
[If none: "No campaign member history found."]

=== SNOWFLAKE: GONG_CALL_TRANSCRIPTS (raw fallback — only if no enrichments) ===
[Found N calls / No prior calls — cold outreach]
[For each call: Date | Participants | Brief | Next steps | Full transcript]

=== SF EMAIL: INBOUND EMAIL HISTORY (Salesforce MCP — EmailMessage, Incoming=true) ===
[Found N inbound emails / No inbound email history]
[Per email: Date | From: {name} <{email}> | Subject | Body preview (first 300 chars)]
[If none: "No inbound email history found in Salesforce."]

=== SF CRM: OPPORTUNITY CONTACT ROLES (Salesforce MCP — OpportunityContactRole) ===
[Found N contact roles / No contact roles found]
[Per role: Contact name | Title | Email | Role | IsPrimary | Opp name | Stage | Close date]
[Flag: IsPrimary=true + Role=Decision Maker/Economic Buyer = budget owner]
[If none: "No opportunity contact roles found."]

=== SF CRM: ACTIVITY / TASK HISTORY (Salesforce MCP — Task) ===
[Found N tasks / No logged activity]
[Per task: Date | Type | Subject | Owner (Astronomer rep) | Who (contact) + title | Description]
[Skip automated sequence emails — surface manually logged calls, meetings, notes]
[If none: "No logged activity history found in Salesforce."]

=== SNOWFLAKE: ACCOUNT_NOTES + CONTACT_NOTES (GTM.PUBLIC) ===
[Found N account notes / N contact notes / No notes found]
[Per note: Date | Type | Source | Content preview]
[If none: "No account/contact notes found in GTM — no prior interactions logged."]
```

In a single generation pass, produce:
1. Fit score section (using rubric from template 1)
2. Full AE brief (using template 2)

The fit scoring rubric uses tags `[EXA]`, `[LF]`, `[CR]` — map these to `[WEB]`, `[SF-LF]`, `[SF-CR]` respectively when Snowflake is the source.

### Step 6: Compose Final Report

Generate slug: lowercase, spaces → underscores, remove special chars. Check for collision.

Check for existing report at `~/claude-work/research-assistant/outputs/accounts/{SLUG}/report.md`. If found, extract prior score/grade and generate changelog entry if:
- Score changed ≥2 points, grade letter changed
- New LF visits to /pricing, /demo, /astro, /trial
- New SF_CONTACTS pricing page or Airflow debug visits
- New hiring signals mentioning Airflow/orchestration
- M&A event detected
- Opp stage changed
- Signal lost (job posting filled, contact departed, HG signal dropped)

```markdown
# Account Research Report: {COMPANY_NAME}

**Generated**: {TODAY_DATE}
**Website**: https://{DOMAIN}
**Sources**: Snowflake (SF_ACCOUNTS ✓/✗ | LF_VISITS ✓/✗ | SF_OPPS ✓/✗ | Gong ✓/✗ | Astro Orgs ✓/✗ | Campaigns ✓/✗) | SF Email ✓/✗ | Web Search ✓

[If M&A STATUS ≠ NONE FOUND:]
> **M&A ALERT: {M&A STATUS}**
> {1-2 sentence impact on outreach}

---
[Fit Score section]
---
[AE Brief section]
---
## Changelog
### {TODAY_DATE}
- [change or "First research generated. Grade: {GRADE}, Score: {SCORE}/20, Confidence: {CONFIDENCE}"]
[prior entries preserved, newest first]
```

### Step 7: Save Report

```bash
mkdir -p ~/claude-work/research-assistant/outputs/accounts/{SLUG}/
```
Overwrite: `~/claude-work/research-assistant/outputs/accounts/{SLUG}/report.md`

### Step 8a: Update Apollo

Skip if no `APOLLO_API_KEY`. Use `APOLLO_ID` from Step 2 pre-fetch if found; otherwise search by name + confirm by domain.

```bash
source ~/.zshrc
APOLLO_REPORT=$(python3 -c "
import re, sys
content = open(sys.argv[1]).read()
if len(content) <= 60000:
    print(content); exit(0)
truncated = re.sub(r'(### Full Transcripts\n).*', r'\1[Truncated — see local report.md]', content, flags=re.DOTALL)
if len(truncated) > 60000:
    truncated = truncated[:60000] + '\n\n[Truncated at 60,000 chars for Apollo]'
print(truncated)
" ~/claude-work/research-assistant/outputs/accounts/{SLUG}/report.md)

RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X PUT "https://api.apollo.io/v1/accounts/{APOLLO_ID}" \
  -H "Content-Type: application/json" \
  -d "{\"api_key\": \"$APOLLO_API_KEY\", \"typed_custom_fields\": {\"{YOUR_APOLLO_RESEARCH_FIELD_ID}\": $(echo "$APOLLO_REPORT" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))' )}}")
HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
[ "$HTTP_STATUS" = "200" ] && echo "Apollo: write succeeded" || echo "Apollo: write FAILED — HTTP $HTTP_STATUS"
```

### Step 8b: Sync to Snowflake

Always run this step — it is not conditional on Apollo success. Extract score/grade/confidence/mc_grade directly from the values computed during Step 5 (do not parse the markdown). Build a sources JSON from which queries returned data.

```bash
source ~/.zshrc && ~/.venvs/snowflake/bin/python3 \
  ~/claude-work/scripts/write_account_research.py \
  --acct-id     "{SF_ACCT_ID}" \
  --acct-name   "{COMPANY_NAME}" \
  --score       {SCORE} \
  --grade       {GRADE} \
  --confidence  {CONFIDENCE} \
  --mc-grade    {MC_GRADE} \
  --sources     '{{"sf_accounts": {SF_ACCOUNT_FOUND}, "lf_visits": {LF_VISITS_FOUND}, "sf_opps": {OPPS_FOUND}, "gong": {GONG_FOUND}, "astro_orgs": {ASTRO_ORGS_FOUND}, "campaigns": {CAMPAIGNS_FOUND}, "web": true, "apollo": {APOLLO_ID_FOUND}}}' \
  --report-file ~/claude-work/research-assistant/outputs/accounts/{SLUG}/report.md
```

Where each `{X_FOUND}` is `true` or `false` based on whether that query returned rows.
If `SF_ACCOUNT_FOUND=false`, use `""` for `--acct-id` and the script will still insert (ACCT_ID will be empty — acceptable for new prospects not yet in SF).
Log result: `Snowflake: write succeeded` or `Snowflake: write FAILED — {error}`. Do not block Step 9 on failure.

### Step 9: Present Results

If M&A STATUS ≠ NONE FOUND, output this first before anything else:
```
⚠️  M&A ALERT: {COMPANY_NAME}
{M&A STATUS} — {date}
{Plain-English: what happened, what the rep should do next.}
Source: {URL}
```

Then display the full report. Highlight fit score/grade, top buying signals, and changelog if re-run.

---

## BATCH MODE

### Batch Step 1: Load CSV
Columns: `company_name`, `domain`. Flexible with header names. Detect `force` flag.

### Batch Step 2: Bulk Snowflake Pre-fetch

**Skip the Leadfeeder MCP entirely.** Instead, pull SF_ACCOUNTS + LF data for all companies in a single query batch before spawning any subagents.

For each company, generate its slug and check for existing valid report (skip if complete and not force mode).

For the NEEDS_RUN companies, run one batch Snowflake query:
```sql
SELECT
  a.ACCT_ID, a.ACCT_NAME, a.ACCT_DOMAIN, a.ACCT_TYPE, a.ACCT_STATUS,
  a.IS_CURRENT_CUST, a.ICP_DESIGNATION_V2, a.ACCT_SCORE,
  a.SMOKE_SCORE, a.FIRE_SCORE, a.LAST_MQL_DATE,
  a.INDUSTRY, a.OWNER_NAME, a.BILLING_COUNTRY
FROM HQ.MODEL_CRM.SF_ACCOUNTS a
WHERE LOWER(a.ACCT_DOMAIN) IN ({comma-separated lowercased domains})
  AND a.ACCT_TYPE NOT IN ('Internal', 'Competitor')
```
This provides `SF_ACCT_ID` for the individual queries.

Also check Gong call counts for all companies in one query:
```sql
SELECT t.ACCT_NAME, COUNT(*) AS call_count
FROM HQ.MODEL_CRM_SENSITIVE.GONG_CALL_TRANSCRIPTS t
JOIN HQ.MODEL_CRM_SENSITIVE.GONG_CALLS c ON t.CALL_ID = c.CALL_ID
WHERE c.IS_DELETED = FALSE
  AND UPPER(t.ACCT_NAME) IN ({comma-separated uppercased names})
GROUP BY t.ACCT_NAME
```

### Batch Step 3: Process Companies (Groups of 5 Simultaneous Subagents)

For each group of up to 5 companies, spawn all subagents simultaneously.

Each subagent task must embed the full Step 2–7 instructions inline (substituting all variables). Pass the pre-fetched Snowflake summary for that company so the subagent can skip Query A (already done) and go straight to Queries B–E.

Key subagent instructions:
- `SF_ACCT_ID` is provided — skip Query A, use it directly for B–E
- All accounts use FULL research depth — run all 7 web research items
- Skip Steps 8a, 8b, and 9 (Apollo, Snowflake, display) — orchestrator handles these
- When finished respond with only: `"{COMPANY_NAME} complete"` or `"{COMPANY_NAME} error: [reason]"`
- Do NOT return the report in the response

**Verify each report** after subagent responds:
```bash
python3 -c "
import os, sys
path = os.path.expanduser('~/claude-work/research-assistant/outputs/accounts/{SLUG}/report.md')
if not os.path.exists(path): print('FAIL: file missing'); exit(1)
content = open(path).read()
missing = [s for s in ['# Account Research Report:', '**Generated**:', '**Sources**:'] if s not in content]
if missing or len(content) < 2000: print(f'FAIL: {missing or \"too short\"}'); exit(1)
print('OK')
" 2>&1
```

Retry once on failure. If still failing, mark FAILED and continue.

**Apollo sync** (orchestrator, after each verification OK):
Use Step 8a with substituted variables. Log result.

**Snowflake sync** (orchestrator, after each verification OK):
Use Step 8b with substituted variables. Log result.

**Append to batch run log**:
```
{TIMESTAMP} | {COMPANY_NAME} | {DOMAIN} | SUCCESS/FAILED | Apollo: ok/failed/skipped | Snowflake: ok/failed
```

Pause 2 seconds between groups. For >50 companies: chunks of 50, pause 10 seconds between chunks.

### Batch Step 4: Batch Summary

Write `~/claude-work/research-assistant/outputs/batch_summary.csv`:
```csv
company,domain,score,grade,confidence,score_change,key_change,research_depth,report_path,last_updated
```

Display: total processed / succeeded / failed, grade distribution, top 10 by score.

For any M&A alerts found across the batch:
```
--- M&A ALERTS ---
- Acme Corp — ACQUIRED by BigCo (March 2025) — may need re-routing
```

For failed companies, write `failed_rerun.csv` and display remediation block.

---

## Graceful Degradation

| Source | Failure Behavior |
|--------|-----------------|
| **SF_ACCOUNTS not found** | RESEARCH_DEPTH=FULL by default; skip Queries B–D; note "New prospect — not yet in Salesforce" |
| **LF_WEBSITE_VISITS empty** | Note "No Leadfeeder visits recorded" — do not attempt Leadfeeder MCP |
| **SF_OPPS empty** | Note "No opportunity history" — cold outreach confirmed |
| **Gong enrichments (no rows)** | Fall back to Query E-fallback (raw transcripts); note "Enrichments not available — using raw transcripts" |
| **Gong (no calls)** | Note "No prior calls — cold outreach" |
| **Web search (no results)** | Note per section; reduce confidence |
| **SF_ASTRO_ORGS empty** | Note "No Astro org or trial history found" — treat as no prior product evaluation |
| **SF_CAMPAIGN_MEMBERS empty** | Note "No campaign history found" — cold from a marketing perspective |
| **GTM.PUBLIC.ACCOUNT_NOTES / CONTACT_NOTES empty** | Note "No account/contact notes found in GTM" — normal for new prospects |
| **SF MCP auth failure (AuthDecryptError)** | Skip Queries I–K entirely; note "SF MCP auth expired — run `sf org login web --alias joey` to restore"; do NOT block report generation |
| **SF EmailMessage (no rows)** | Note "No inbound email history found in Salesforce" — do not error; email logging may not be enabled |
| **SF OpportunityContactRole (no rows)** | Note "No opportunity contact roles found" — common on older opps |
| **SF Task (no rows)** | Note "No logged activity history found" — reps may not log activities manually |
| **Apollo** | Skip write-back; report saves locally |
| **Common Room** | Note "Common Room not available"; SF_CONTACTS covers contact intent signals |

**Do NOT fall back to Leadfeeder MCP** — if the account isn't in Salesforce, it won't be in Leadfeeder either. The MCP is a slower path to the same data.

**Snowflake-first principle**: Snowflake is always available and never requires re-auth. Route every CRM query through Snowflake. SF MCP is only for three objects with no Snowflake equivalent: `EmailMessage`, `Task`, and `OpportunityContactRole`. Everything else — accounts, contacts, opps, campaigns, Gong, Leadfeeder, Zendesk, notes — comes from Snowflake.

---

## Important Guidelines

- Report file must be under 1,000,000 characters.
- Every claim tagged with its source: `(VERIFIED-SF)`, `(VERIFIED-WEB)`, `(VERIFIED-GONG)`, `(GENERATED)`.
- Preserve all prior changelog entries on re-runs.
- In batch mode, save incrementally after each company completes.
- Slug collision: append `_2`, `_3`, etc.
- **Primary sources of truth** (in order): Gong transcripts > web search (job postings, GitHub, blog) > Leadfeeder (LF_WEBSITE_VISITS) > SF first-party CRM (SF_CONTACTS, SF_OPPS).
- All SF 3rd-party enrichment fields (HG_*, CF_*, DATAFOX_*, hiring counts, NUMBER_OF_EMPLOYEES, ANNUAL_REVENUE, APOLLO_INTENT_*) have been removed from queries — get this from web search instead.
- `SF_OPPS.AIRFLOW_EXPERIENCE` and `CURRENT_AIRFLOW_DEPLOYMENT_MODEL` (human-entered discovery notes) are reliable — lead with them when present.
- SF_CONTACTS pricing page and Airflow debug page visits are person-level buying signals — flag any that occurred in last 30 days as HIGH urgency.
- SF_CONTACTS pricing page and Airflow debug page visits are person-level buying signals — flag any that occurred in last 30 days as HIGH urgency.

---

**Begin research for:** {{args}}
