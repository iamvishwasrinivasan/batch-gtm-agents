---
name: gtm-snowflake-apollo
description: Create personalized Apollo email sequences with automatic contact enrollment
invocable: user
---

You are automating Apollo email sequence creation for: **{{args}}**

# What This Does

End-to-end Apollo sequence automation:
1. **Fetches research** from Snowflake GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT
2. **Finds contacts** at the company via Apollo API
3. **Generates personalized email copy** based on research signals
4. **Shows preview** and gets approval
5. **Creates sequence** with {{Email_Step_X}} variables
6. **Writes copy** to each contact's custom fields
7. **Enrolls contacts** in sequence - ready to send

No Apollo UI needed. Entire flow runs via API.

# Execution

Parse args to determine invocation:

## Company name only (interactive):
```bash
cd /Users/vishwasrinivasan/batch-gtm-agents && python3 apollo_sequence_automation.py "{{args}}"
```

## With specific contacts:
```bash
cd /Users/vishwasrinivasan/batch-gtm-agents && python3 apollo_sequence_automation.py "Company Name" --contacts "Contact1,Contact2"
```

## Auto-approve (skip preview):
```bash
cd /Users/vishwasrinivasan/batch-gtm-agents && python3 apollo_sequence_automation.py "{{args}}" --auto-approve
```

## 4-step sequence (default is 3):
```bash
cd /Users/vishwasrinivasan/batch-gtm-agents && python3 apollo_sequence_automation.py "{{args}}" --steps 4
```

**Let the script run interactively.** It will:
- Show found contacts
- Ask which to target
- Show generated email copy
- Ask for approval before pushing

# Output Format

After completion, summarize:

```
## Apollo Sequence Complete

**Company:** Smith Gardens
**Contacts Enrolled:** 2/2 successful
**Sequence:** https://app.apollo.io/sequences/69d7d660b2a5070015542c91

### Enrolled Contacts:
1. **Kyle Cornish** - VP Data Engineering
   - Copy written to custom fields
   - Enrolled in sequence
2. **Kimberly Joslin** - Director Analytics
   - Copy written to custom fields
   - Enrolled in sequence

### Email Copy Summary:
- **Subject:** Orchestration evaluation
- **Angle:** Orchestration tools comparison (based on 31 mentions)
- **Tone:** Conversational, executive presence
- **Steps:** 3 emails over 5 days

### Next Steps:
- Emails will send automatically based on sequence timing
- Monitor in Apollo: https://app.apollo.io/sequences/69d7d660b2a5070015542c91
- Track responses in Salesforce
```

If contacts couldn't be enrolled, list them with error messages.

# Email Copy Generation

Copy is generated based on research signals:

**Orchestration evaluation (>15 mentions):**
- Subject: "Orchestration evaluation"
- Angle: Airflow vs Dagster comparison
- Focus: Astro as managed Airflow with modern features

**Team growth (>5 hiring signals):**
- Subject: "Scaling data infrastructure"  
- Angle: Infrastructure overhead reduction
- Focus: Astro for growing teams

**M&A activity:**
- Subject: "Recent acquisition"
- Angle: Pipeline consolidation post-acquisition
- Focus: Astro for M&A integration

**General data (default):**
- Subject: "Data orchestration"
- Angle: Reliable orchestration without ops burden
- Focus: Astro for Snowflake/Databricks stacks

All copy follows best practices:
- Natural, conversational tone
- No markdown, bullets, or AI formatting
- Executive presence
- Short, punchy sentences
- Personalization via {{first_name}} variables

# Prerequisites

**Research must exist:**
```bash
/batch-account-research "Company Name"
```

If research doesn't exist, script will error and suggest running batch research first.

**Apollo contacts must exist:**
- Company must have contacts in Apollo
- Script searches by company name
- Shows all found contacts for selection

**Environment variables:**
- APOLLO_API_KEY (in ~/.claude/settings.json)
- Snowflake credentials (key-pair auth via ~/.ssh/rsa_key_unencrypted.p8)

# Error Handling

**No research found:**
```
❌ No research found for Smith Gardens
Run: /batch-account-research "Smith Gardens"
```

**No contacts found:**
```
❌ No contacts found in Apollo for Smith Gardens
→ Check company name spelling
→ Or search Apollo UI to verify contacts exist
```

**Contact enrollment failed:**
```
✓ Copy written
❌ Enrollment failed: Contact already in sequence
→ Common - contact may be in another active sequence
→ Remove from other sequence first
```

**API rate limiting:**
- Script has no built-in rate limiting (yet)
- If hitting limits, wait 60 seconds and retry

# Interactive Flow Example

```bash
$ /gtm-snowflake-apollo "Smith Gardens"

🔍 Fetching research for Smith Gardens...
✓ Found research (tier: hot_mql, score: 8/10, 13 signals)

🔎 Searching Apollo for contacts at Smith Gardens...

✓ Found 3 contacts:

  1. ✓ Kyle Cornish - VP Data Engineering
  2.   Kimberly Joslin - Director Analytics
  3.   John Smith - Data Engineer

Target which contacts? (1,2 / all / cancel): 1,2

📝 Targeting 2 contact(s)

📝 Generating email copy...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📧 GENERATED EMAIL COPY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SUBJECT: Recent acquisition

STEP 1:
Hi {{first_name}},

Saw the news about Smith Gardens' recent acquisition. Big moment 
for the team.

As you're integrating systems and likely evaluating data infrastructure, 
worth 15 minutes to show how other recent M&A situations have used 
Astro to consolidate pipelines quickly?

Vishwa

[...steps 2 and 3...]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Based on: 0 orchestration mentions, 0 hiring signals, tier: hot_mql
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Push and enroll? (y/n/edit): y

✓ Creating sequence 'Smith Gardens - Outreach'...

✓ Enrolling 2 contact(s)...

  → Kyle Cornish...
    ✓ Copy written
    ✓ Enrolled in sequence
  → Kimberly Joslin...
    ✓ Copy written
    ✓ Enrolled in sequence

======================================================================
🎯 COMPLETE
======================================================================

2 contact(s) enrolled and ready to send
Sequence: https://app.apollo.io/sequences/69d7d660b2a5070015542c91

Emails will send automatically based on sequence timing.
```

# Common Workflows

**Single contact, auto-approve:**
```
/gtm-snowflake-apollo "GridX" --contacts "John Doe" --auto-approve
```

**All contacts at company:**
```
/gtm-snowflake-apollo "Apollo.io"
→ Select "all" when prompted
```

**4-step sequence for high-value account:**
```
/gtm-snowflake-apollo "Databricks" --steps 4
```

**Research + Sequence in one flow:**
```
/batch-account-research "NewCorp"
/gtm-snowflake-apollo "NewCorp"
```

# Pro Tips

- **Run research first** - Better signals = better copy
- **Preview always** - Don't auto-approve until you trust the templates
- **Target MQLs** - Script shows ✓ badge for MQLs
- **Edit after fact** - Can edit copy in Apollo UI even after enrollment
- **Sequence timing** - Default: Day 0, Day 2, Day 5 (can't change via API yet)
- **Multiple sequences** - Script creates new sequence each time (by design)

# Integration with Batch Research

Best practice workflow:

```bash
# 1. Research accounts
/batch-account-research "GridX,Apollo,Vercel"

# 2. Query high-value accounts
/snowflake-gtm-query accounts with tier = 'hot_mql' and orchestration_mentions > 20

# 3. Create sequences for top accounts
/gtm-snowflake-apollo "GridX"
/gtm-snowflake-apollo "Apollo"

# 4. Track in CRM
→ Sequences auto-sync to Salesforce
→ Responses logged as Tasks
```

---

**After script completes**, parse output and format the summary above. Include sequence URL, enrolled contacts (with success/failure), email angle used, and next steps.
