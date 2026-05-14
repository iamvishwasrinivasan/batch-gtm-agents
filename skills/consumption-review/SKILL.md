---
name: consumption-review
description: >
  Generate a polished Astronomer consumption review deck (.pptx) for a customer ahead of renewal or QBR.
  Use this skill any time Vishwa or an AE says "consumption review", "QBR deck", "renewal deck",
  "create a deck for [customer]", "build a review for [account]", or provides DAG run CSVs and
  account/consumption screenshots and wants a slide deck. Also trigger when someone says "prep for
  my Acelab meeting" or similar — if data files are present and the context is customer-facing,
  assume a consumption review is needed. The skill produces a 5-slide minimum deck: Cover, Account
  Snapshot, 12-Month Consumption Trend, How They Use Astro, and Pipeline Inventory.
---

# Consumption Review Deck Skill

You are generating a professional customer-facing PowerPoint consumption review deck for an Astronomer account, following Astronomer's 2026 brand guidelines. The output is a `.pptx` file delivered to the outputs folder.

## Before you start

1. Read `references/brand-guidelines.md` — it has the exact hex colors, fonts, and layout rules.
2. Read `references/slide-structure.md` — it defines the minimum 5 slides and what goes on each.
3. Read the PPTX skill at `/sessions/great-beautiful-bardeen/mnt/.claude/skills/pptx/pptxgenjs.md` for API reference.

## Inputs to expect

The user will typically provide some combination of:
- **Account summary screenshot(s)** — ARR, subscription plan, utilization %, credit balance, ATR date, projected overage
- **Consumption trend screenshot** — stacked bar chart showing monthly hosted consumption by cost type (Deployment, Compute) over the last 12 months
- **DAG Run Detail CSV(s)** — typically one for 90 days and one for 365 days, with columns: `Dagrun Type`, `Dag Id`, `DAG Run Count`, `DAG Success Rate`, `Avg Run Duration (Min)`
- **Customer name** and any deal context (AE name, ATR date, plan)

If any inputs are missing, infer what you can and flag gaps in a brief note before proceeding.

## Step 1: Extract account data

Read the account screenshots visually. Pull out:
- Subscription ARR, Credit Balance, License Granted total, License Consumed %
- Utilization %, Projected Full Credit Use Date, Projected Overages
- ATR date, Plan (Team/Business/Enterprise), deployment type (Hosted/Hybrid), cloud provider (GCP/AWS/Azure)
- Org ID, Cluster Type
- Recent 30-day stats if visible: successful task count, usage amount, DAG count, user count

## Step 2: Analyze the consumption trend

Read the consumption chart screenshot. Extract:
- Monthly totals for the last 12 months
- Split between Deployment and Compute cost types (estimate visually if not labeled)
- Key stats: growth from first to peak month, peak month and value, compute surge %

If the chart is not provided, ask the user or leave the chart slide with placeholder data.

## Step 3: Analyze DAG run data

Parse both CSVs with Python. The CSV rows use a "fill-down" pattern for `Dagrun Type` — blank cells inherit the value from the last non-blank row above. Parse accordingly.

```python
import csv

def load_dag_data(filepath):
    data = {}
    current_type = None
    with open(filepath) as f:
        for row in csv.DictReader(f):
            t = row['Dagrun Type'].strip()
            if t:
                current_type = t
            dag = row['Dag Id'].strip()
            if not dag or dag == 'Total':
                continue
            data[(current_type, dag)] = {
                'runs': int(float(row['DAG Run Count'])),
                'success': float(row['DAG Success Rate']),
                'avg_min': float(row['Avg Run Duration (Min)']),
            }
    return data
```

From the data, derive:
- **Use case categories**: Group DAGs by their domain. Read DAG names carefully — names like `dbt_staging`, `pdf_scraping_directus_files_dag`, `assign_taxonomy_parents`, `export_to_cimulate` tell a clear product story. Aim for 4–6 categories.
- **Pipeline inventory**: Top 8–10 scheduled DAGs by run count (excluding generic system DAGs like `health_check` unless they're meaningful). Include name, 90-day runs, success %, avg runtime (formatted as `Xm Ys`), and category.
- **Rate acceleration**: Compare 90-day rate/day vs annualized 365-day rate/day. If certain pipelines show a 1.5x+ increase in frequency, this is conversation-worthy (it drives deployment cost).

Use DAG name semantics to infer the customer's business. A company with `leed_v5_scoring`, `masterformat_tagging`, and `assign_taxonomy_parents_to_products` is clearly in construction/materials data — not generic SaaS. Let that industry context inform the use case copy.

## Step 4: Generate the deck

Install dependencies if needed:
```bash
cd /path/to/working-dir && npm install pptxgenjs
```

Write a JSON config file with all the deck data, then use `scripts/deck_generator.js` to produce the PPTX:

```bash
node /path/to/consumption-review-skill/scripts/deck_generator.js deck_config.json output.pptx
```

The script reads the config and produces a fully-styled deck. See `references/slide-structure.md` for the config schema.

## Step 5: QA

Convert to images and visually inspect every slide:

```bash
python3 /sessions/great-beautiful-bardeen/mnt/.claude/skills/pptx/scripts/office/soffice.py --headless --convert-to pdf output.pptx
rm -f slide-*.jpg && pdftoppm -jpeg -r 150 output.pdf slide
```

Check for:
- Footer text overlapping the ASTRONOMER wordmark (they should be on the same line, wordmark left, footer right)
- Text overflow or truncation in stat cards and pipeline table
- Orbital spheres clipped at slide edges
- Eyebrow labels readable (Courier New, gold, all-caps, ~9pt)

Fix any issues, regenerate, and re-verify.

## Step 6: Deliver

Copy the final PPTX to `/sessions/great-beautiful-bardeen/mnt/outputs/` and share a download link.

---

## Writing style for slide copy

Headers are **topics, not insights**. "Account Snapshot" not "Acelab is over-licensed". "Pipeline Inventory" not "High-frequency enrichment drives cost". Let the numbers tell the story — the header is just the label.

Use DAG names in body copy. "assign_taxonomy_parents_to_products drives 3,500+ runs" is more credible than "product classification pipelines run frequently." The specificity shows you did the work.

Keep stat card subtext honest and brief. "burning above license pace" is fine. Don't editorialize beyond what the data supports.
