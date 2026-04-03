# Email Integration - Implementation Summary

**Completed:** 2026-04-03

## What Was Added

Email correspondence from Salesforce Tasks is now automatically included in all batch account research outputs.

---

## Changes Made

### 1. SQL Migration (`add_email_column_to_research_table.sql`)
- Adds `email_correspondence` VARCHAR column to `GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT`
- **Run this FIRST before running the updated Python script**

### 2. Python Updates (`batch_account_research.py`)

#### Phase 2: Fetch Email Context (line ~430)
- Added query to fetch emails from `IN_SALESFORCE.TASK` where TYPE='Email'
- Joins via `OPPORTUNITY.ID` to get `ACCOUNT_ID`
- Groups emails by account

#### Phase 3: Include in Output (line ~1710)
- Extracts emails from `sf_context` for each account
- Adds emails to JSON report (`raw_data.json`)
- Adds email section to markdown report (`report.md`)

#### Save to Snowflake (line ~1960)
- Reads emails from JSON file
- Serializes to JSON string
- Saves to `email_correspondence` column

---

## How To Use

### Step 1: Run SQL Migration
```sql
-- In Snowflake UI
USE DATABASE GTM;
USE SCHEMA PUBLIC;
ALTER TABLE ACCOUNT_RESEARCH_OUTPUT ADD COLUMN email_correspondence VARCHAR;
```

### Step 2: Run Batch Research
```bash
python3 batch_account_research.py --accounts "Capstone Investment Advisors"
```

### Step 3: Query Email Data

**Local JSON File:**
```bash
cat ~/claude-work/batch-research-output/2026-04-03/capstone_investment_advisors/raw_data.json
```

**Snowflake UI:**
```sql
SELECT 
    acct_name,
    email_correspondence::VARIANT as emails
FROM GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT
WHERE acct_name = 'Capstone Investment Advisors';
```

**Parse Specific Fields:**
```sql
SELECT 
    acct_name,
    email.value:subject::STRING as subject,
    email.value:date::TIMESTAMP as email_date,
    email.value:preview::STRING as preview
FROM GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT,
LATERAL FLATTEN(input => TRY_PARSE_JSON(email_correspondence)) email
WHERE acct_name = 'Capstone Investment Advisors'
ORDER BY email_date DESC;
```

---

## What You Get

### JSON Output (`raw_data.json`)
```json
{
  "account_name": "Capstone Investment Advisors",
  "counts": {
    "emails": 10
  },
  "emails": [
    {
      "email_id": "00T...",
      "subject": "Re: Capstone / Astronomer Partnership",
      "date": "2026-04-02T14:22:53+00:00",
      "preview": "From: vishwa.srinivasan@astronomer.io\nTo: sschatteman@capstoneco.com..."
    }
  ]
}
```

### Markdown Report (`report.md`)
```markdown
## CRM Summary
- Contacts: 12
- MQLs: 3
- Opportunities: 1
- Gong Calls: 5
- Emails: 10

## Email Correspondence

### 2026-04-02 - Re: Capstone / Astronomer Partnership
From: vishwa.srinivasan@astronomer.io
To: sschatteman@capstoneco.com...
```

### Snowflake Table
- `email_correspondence` column contains JSON array of all emails
- Queryable via `::VARIANT` and `FLATTEN()` for analysis

---

## Email Data Structure

Each email contains:
- `email_id` - Salesforce Task ID
- `subject` - Email subject line
- `date` - When email was created (ISO 8601 timestamp)
- `preview` - First 500 characters of DESCRIPTION field (includes From/To/Body)

---

## Use Cases

### 1. Deal Post-Mortem
"What happened with the Capstone deal?" → See final emails showing rejection

### 2. Response Time Analysis
Calculate time between outbound emails and prospect replies

### 3. Communication Cadence
Track email frequency during different deal stages

### 4. Contact Engagement
Identify which contacts are most responsive via email

---

## Testing

**Test with Capstone:**
```bash
python3 batch_account_research.py --accounts "Capstone Investment Advisors"

# Verify:
# 1. JSON file has 'emails' array with 10+ items
# 2. Markdown report has "Email Correspondence" section
# 3. Snowflake table has non-null email_correspondence
```

**Check Snowflake:**
```sql
SELECT 
    acct_name,
    COUNT(email.value) as email_count
FROM GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT,
LATERAL FLATTEN(input => TRY_PARSE_JSON(email_correspondence)) email
WHERE email_correspondence IS NOT NULL
GROUP BY acct_name
ORDER BY email_count DESC;
```

---

## Notes

- Emails are fetched only for **engaged accounts** (those with MQLs or calls)
- Up to 1000 emails per batch, sorted by most recent first
- Preview limited to 500 chars to keep file sizes manageable
- Full DESCRIPTION available in JSON but not in markdown (too verbose)
- HubSpot emails are **NOT** included (only Salesforce Task emails)

---

## Next Steps

1. ✅ Run SQL migration in Snowflake
2. ✅ Code changes complete
3. ⏭️ Test with one account (Capstone)
4. ⏭️ Verify output in JSON, markdown, and Snowflake
5. ⏭️ Run on full account list if test passes
