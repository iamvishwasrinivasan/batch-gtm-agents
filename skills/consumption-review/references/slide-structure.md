# Minimum Slide Structure — Consumption Review

Based on the Vivian Health consumption review as the reference example of "what good looks like."
Five slides minimum. Each slide is described below with its purpose, required elements, and the JSON config schema the deck_generator.js script expects.

---

## Slide 1: Cover

**Purpose**: Set the stage — company, date, deal context. Dark and bold.

**Required elements**:
- Date eyebrow (e.g., "APRIL 2026")
- Customer name in large title font
- "Consumption Review" subtitle
- Purple horizontal divider line
- ATR date, Plan (type/deployment/cloud) on one line
- AE name (and RM if known)
- Optional: cluster/DAG context line in muted monospace
- Orbital rings decoration (right side)
- ASTRONOMER wordmark (bottom left)

**JSON config key**: `customer`
```json
{
  "name": "Acelab",
  "date_eyebrow": "APRIL 2026",
  "atr_date": "Apr 29, 2026",
  "plan": "Team / Hosted / GCP",
  "ae": "Vishwa Srinivasan",
  "rm": "",
  "context_line": "Shared Cluster · GCP · 60 active DAGs · ATR in 13 days"
}
```

---

## Slide 2: Account Snapshot

**Purpose**: Give the customer (and AE) an instant read on the health of the account — consumption position, license burn, and renewal risk.

**Required elements**:
- Eyebrow: "ACCOUNT OVERVIEW"
- Title: "Account Snapshot"
- 6 stat cards in a 3×2 grid:
  - Row 1: Subscription ARR | Credit Balance | License Consumed
  - Row 2: Utilization | Credits Exhausted (projected date) | Projected Overage
- Footer: data-as-of date, org ID, cluster info

**Design notes**: Utilization above 120% should display in gold to signal heat. Projected Overage of $0 can stay white — it's a relief, not a warning.

**JSON config key**: `snapshot`
```json
{
  "arr": "$11,961",
  "credit_balance": "$3,856",
  "license_granted": "$13,290",
  "license_consumed_pct": "71%",
  "license_consumed_sub": "9,433 credits used",
  "utilization": "148%",
  "utilization_sub": "burning above license pace",
  "utilization_alert": true,
  "credits_exhausted": "Jun 26",
  "credits_exhausted_sub": "projected full use date",
  "projected_overage": "$0",
  "projected_overage_sub": "through Apr renewal",
  "data_date": "Apr 16, 2026",
  "org_id": "cm98j96wf1vid01mumkqp0m5m",
  "cluster": "GCP Shared Cluster"
}
```

---

## Slide 3: 12-Month Consumption Trend

**Purpose**: Show the growth story — where consumption started, where it peaked, and what's driving it (Deployment vs Compute).

**Required elements**:
- Eyebrow: "12-MONTH CONSUMPTION TREND"
- Title: "Hosted Consumption: 12-Month Trend"
- Stacked bar chart: Deployment (purple `872DED`) + Compute (teal `13BDD7`)
  - 12 monthly bars (most recent month can be partial, marked with *)
  - Legend at bottom
  - Dark background, muted axis labels, subtle grid lines
- 3 right-side stat callout cards:
  - Growth (e.g., "3.4x" from first to peak month)
  - Peak Month (e.g., "Feb '26" + dollar amount)
  - Compute Surge (e.g., "+2,047%" compute spend change)
- Footer: asterisk note for partial month

**JSON config key**: `trend`
```json
{
  "months": ["May '25","Jun '25","Jul '25","Aug '25","Sep '25","Oct '25","Nov '25","Dec '25","Jan '26","Feb '26","Mar '26","Apr '26*"],
  "deploy":  [448, 465, 549, 501, 515, 562, 543, 660, 700, 1050, 1000, 434],
  "compute": [27,  28,  30,  30,  30,  33,  34,  106, 247, 580,  530,  380],
  "growth_label": "3.4x",
  "growth_note": "May '25 to Feb '26 peak",
  "peak_label": "Feb '26",
  "peak_note": "$1,630 consumed",
  "surge_label": "+2,047%",
  "surge_note": "compute spend since May '25",
  "footer": "* Apr '26 partial month  ·  Deployment includes scheduler + worker costs"
}
```

**How to compute key stats**:
- Growth: total[peak] / total[first_month] — round to 1 decimal
- Compute surge: (compute[last_full] - compute[first]) / compute[first] * 100
- Peak month: argmax of (deploy[i] + compute[i])

---

## Slide 4: How They Use Astro

**Purpose**: Demonstrate value — show that this isn't just a scheduler, it's the backbone of their data platform. Make the AE look smart in the room.

**Required elements**:
- Eyebrow: "HOW THEY USE ASTRO"
- Title: "How [Customer] Uses Astro"
- 4–6 use-case category cards (5 is ideal for 16:9 layout)
- Each card: color bar + dot, category eyebrow, card title (short), divider, body copy (2–4 sentences using actual DAG names and run counts)

**Card layout**: Equal-width columns spanning full slide, cards fill vertically from below title to near bottom.

**JSON config key**: `use_cases` (array)
```json
[
  {
    "color_key": "PURPLE",
    "label": "PRODUCT ENRICHMENT",
    "title": "Taxonomy & Classification",
    "body": "assign_taxonomy_parents_to_products drives 3,500+ runs in 90 days. convert_metric_units runs in lockstep — normalizing product specs at scale."
  },
  {
    "color_key": "TEAL",
    "label": "CONTENT INGESTION",
    "title": "PDF & Video Extraction",
    "body": "pdf_scraping_directus_files_dag pulls specs from manufacturer PDFs. fetch_youtube_transcripts processes 622 videos to enrich product context."
  }
]
```

**Deriving use cases from DAG names**: Group DAGs by semantic domain. Look for:
- dbt_ prefixes → Data Transformation
- _website_, import_to_, export_ → Publishing/Integrations
- _tagging, _scoring, _classification → Enrichment
- pdf_, fetch_, ingest_, scraping_ → Content Ingestion
- sfdc_, crm_, slack_ → CRM/Sync
- _pipeline (data), postgres_, mysql_ → Core Data
- _ml_, _ai_, _model_, _agent_ → ML/AI

The body copy should use real DAG names and actual run counts. This is what makes the slide feel earned.

---

## Slide 5: Pipeline Inventory

**Purpose**: Give the technical champion a reference table. Shows breadth of usage and opens conversation about reliability (low success rates) and runtime outliers.

**Required elements**:
- Eyebrow: "PIPELINE INVENTORY"
- Title: "Pipeline Inventory"
- Table: 8–12 rows, sorted by 90-day run count descending
- Columns: Pipeline | Runs | Success | Avg Runtime | Category
- Header row: MED background, gold text
- Alternating row colors: LIGHT and ALT
- Pipeline names in Courier New (monospace)
- Success % colored: green (≥95%), amber (85–94%), red (<85%)
- Category names colored by category color map
- Footer: sort note, window note, exclusions

**JSON config key**: `pipelines` (array) + `pipeline_footer`
```json
{
  "pipelines": [
    { "name": "assign_taxonomy_parents_to_products", "runs": "3,514", "success": "99.5%", "runtime": "6m 00s", "category": "Product Enrichment", "success_val": 99.5 },
    { "name": "convert_metric_units", "runs": "3,530", "success": "99.5%", "runtime": "3m 28s", "category": "Product Enrichment", "success_val": 99.5 }
  ],
  "pipeline_footer": "Sorted by run count  ·  Scheduled runs, 90-day window  ·  health_check excluded"
}
```

**Success color logic** (based on `success_val`):
- ≥ 95: GREEN (`19BA5A`)
- 85–94.99: GOLD (`FFB32D`)
- < 85: RED (`F03A47`)

**Runtime formatting**: Convert decimal minutes to `Xm Ys` format.
```python
def fmt_runtime(minutes):
    m = int(minutes)
    s = round((minutes - m) * 60)
    return f"{m}m {s:02d}s"
```

---

## Full config schema

```json
{
  "customer": { ... },
  "snapshot": { ... },
  "trend": { ... },
  "use_cases": [ ... ],
  "pipelines": [ ... ],
  "pipeline_footer": "..."
}
```

Save this as `deck_config.json` and run:
```bash
node /path/to/skill/scripts/deck_generator.js deck_config.json output_filename.pptx
```
