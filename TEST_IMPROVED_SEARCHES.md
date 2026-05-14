# Test Script: Improved Search Prompts

This script tests the improved 7-search strategy before merging into `batch_account_research.py`.

## What Changed

### Key Improvements:
1. **Dropped generic "orchestration" search** → Added "github_evidence" search
2. **Expanded "hiring" search** → Now searches all engineering roles + extracts tech stack from job postings
3. **Focused "news" search** → Only trigger events (funding, M&A, exec hires)
4. **Domain restrictions** → Engineering blogs, job boards, vendor sites only
5. **Phrase matching** → "we use airflow" not just "airflow"

### The 7 Searches:

| # | Search | Purpose | Key Changes |
|---|--------|---------|-------------|
| 1 | company_research | Company overview | ✅ Unchanged |
| 2 | github_evidence | **NEW** - Code repos, not articles | ✅ Replaces generic orchestration |
| 3 | hiring | **PRIMARY TECH STACK SOURCE** | ✅ Expanded to all eng roles |
| 4 | trigger_events | Funding, M&A, exec hires | ✅ Focused from generic news |
| 5 | engineering_blog | Company domain only | ✅ Domain-restricted |
| 6 | product_announcements | Product launches | ⚠️ Minor improvements |
| 7 | case_studies | Vendor case studies | ✅ Vendor domains only |

## Usage

### Basic Test:
```bash
python3 test_improved_searches.py "Company Name"
```

### With Domain (recommended):
```bash
python3 test_improved_searches.py "Company Name" --domain company.com
```

### Examples:
```bash
# Test Komodo Health
python3 test_improved_searches.py "Komodo Health" --domain komodohealth.com

# Test Airbnb
python3 test_improved_searches.py "Airbnb" --domain airbnb.com

# Test a prospect (no domain yet)
python3 test_improved_searches.py "Some Startup"
```

## Output

### Console Output:
- ✅/❌ Status for each search
- Tech stack extracted from job postings
- Sample results from each search

### JSON Output:
- Full results saved to `test_results_company_name_TIMESTAMP.json`
- Includes all highlights, URLs, tech stack mentions

## What to Look For

### ✅ Good Signals (should see these):
1. **GitHub repos** from the company (search 2)
2. **Job postings from greenhouse.io/lever.co** (search 3)
3. **Tech stack from job requirements** (extracted automatically)
4. **Press releases from businesswire.com** for trigger events (search 4)
5. **Engineering blog posts from company domain** (search 5)
6. **Vendor case studies** (search 7)

### ❌ Bad Signals (should NOT see these):
1. ~~Generic Reddit/Medium articles about orchestration~~
2. ~~News about hiring (not actual job postings)~~
3. ~~Generic press releases/social posts~~
4. ~~Third-party blogs mentioning the company~~

## Test Companies

### Good Test Cases:

**1. Komodo Health** (known Airflow user)
```bash
python3 test_improved_searches.py "Komodo Health" --domain komodohealth.com
```
- Should find: Data Engineer job with Airflow requirement
- Should find: Engineering blog posts about data platform
- Expected tech stack: Databricks, Python, Airflow

**2. Netflix** (heavy Airflow user)
```bash
python3 test_improved_searches.py "Netflix" --domain netflix.com
```
- Should find: Multiple GitHub repos with Airflow
- Should find: Engineering blog about data platform
- Expected tech stack: Airflow, Spark, Python, AWS

**3. Airbnb** (created Airflow!)
```bash
python3 test_improved_searches.py "Airbnb" --domain airbnb.com
```
- Should find: GitHub repos (airbnb/airflow originally)
- Should find: Engineering blog posts about Airflow
- Expected tech stack: Airflow, Spark, Kubernetes, AWS

**4. Small Company** (test false positives)
```bash
python3 test_improved_searches.py "Smith Gardens" --domain smithgardens.com
```
- Should NOT find: Generic Airflow articles (like we saw before)
- Should find: Hiring signals (if any)
- Expected tech stack: Probably none (they're a nursery)

## Success Criteria

### Before merging, verify:
- [ ] GitHub search returns company repos, not random gists
- [ ] Hiring search returns job boards, not news articles
- [ ] Tech stack extraction finds tools from job requirements
- [ ] Trigger events only returns funding/M&A/exec hires
- [ ] Engineering blog only returns company domain posts
- [ ] Case studies only from vendor domains
- [ ] No generic Reddit/Medium articles about tools

### Compare to current system:
Run a company through both and compare signal quality:
```bash
# Old system (in batch_account_research.py)
python3 batch_account_research.py "Company Name"

# New system (this script)
python3 test_improved_searches.py "Company Name" --domain company.com
```

## Known Limitations

1. **Engineering blog search requires domain** - Will skip if no domain provided
2. **GitHub slug guessing** - May miss repos if company uses different naming
3. **Rate limiting** - Has 1 second delays between searches
4. **No validation filter** - This script doesn't include the `_is_signal_valid()` logic yet

## Next Steps

If tests look good:
1. Review output quality for 3-5 test companies
2. Compare signal quality to current system
3. Merge functions into `batch_account_research.py`
4. Update signal categorization logic
5. Re-run batch research on clean dataset

## Questions This Answers

1. **Do they use Airflow?** → hiring search (job reqs) + github_evidence
2. **Is Airflow mission-critical?** → engineering_blog + case_studies
3. **What's in their tech stack?** → hiring search (PRIMARY) + github + blog
4. **Trigger events?** → trigger_events + product_announcements
5. **C-suite changes?** → trigger_events (exec hires)
