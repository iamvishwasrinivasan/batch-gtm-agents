# Alumni Apollo Workflow

Automated workflow for populating personalized email sequences for Astro alumni prospects in Apollo.

## Overview

This workflow allows sales reps to automatically generate personalized 3-step email sequences for alumni prospects (people who used Astro at their previous company and have moved to a new company).

## Features

- **Snowflake Integration**: Pulls alumni prospects directly from `GTM.PUBLIC.ALUMNI_PROSPECTS` table
- **Personalized Emails**: Generates 3 email steps with:
  - Personalized company transitions (old company → new company)
  - Dynamic time phrases (recently, a few months ago, last year, a couple years ago)
  - AI tooling + Blueprint product messaging
  - 6 different style variations for natural variety
- **Apollo Integration**: Populates custom fields in Apollo for sequence use
- **Sequence Enrollment**: Automatically adds contacts to Apollo sequences

## Prerequisites

1. **Apollo API Access**
   - API key configured in `apollo_config.py`
   - EMAIL_ACCOUNT_ID configured in `apollo_config.py`

2. **Snowflake Access**
   - Snowflake query script at `~/batch-gtm-agents/snowflake_query.py`
   - Access to `GTM.PUBLIC.ALUMNI_PROSPECTS` table

3. **Python Dependencies**
   ```bash
   pip install requests
   ```

## Scripts

### 1. `populate_alumni_emails.py` (Master Script)

One command to export from Snowflake and populate all email steps.

**Usage:**
```bash
python3 populate_alumni_emails.py "Rep Name"
```

**Examples:**
```bash
python3 populate_alumni_emails.py "Joey Kenney"
python3 populate_alumni_emails.py "Vishwa Srinivasan"
python3 populate_alumni_emails.py "Joseph Mason"
```

**What it does:**
1. Exports alumni prospects for the specified rep from Snowflake
2. Creates a CSV in `~/Downloads/`
3. Runs all 3 email population scripts
4. Reports results

### 2. `add_email_drafts_to_apollo.py`

Populates `Email_Step_1` custom field in Apollo.

**Usage:**
```bash
python3 add_email_drafts_to_apollo.py <csv_file>
```

**Example:**
```bash
python3 add_email_drafts_to_apollo.py "Joey_Kenney_Alumni_Prospects.csv"
```

### 3. `add_email_step2_to_apollo.py`

Populates `Email_Step_2` custom field in Apollo (follow-up about team differences).

**Usage:**
```bash
python3 add_email_step2_to_apollo.py <csv_file>
```

### 4. `add_email_step3_to_apollo.py`

Populates `Email_Step_3` custom field in Apollo (final "thoughts?" touch-base).

**Usage:**
```bash
python3 add_email_step3_to_apollo.py <csv_file>
```

### 5. `add_to_specific_sequence.py`

Enrolls contacts from CSV into an Apollo sequence.

**Usage:**
```bash
python3 add_to_specific_sequence.py <csv_file> <sequence_id>
```

**Example:**
```bash
python3 add_to_specific_sequence.py "Joey_Kenney_Alumni_Prospects.csv" "69e7a4152f0c6000219d6f18"
```

**Finding your sequence ID:**
- Go to your sequence in Apollo
- Copy the ID from the URL: `https://app.apollo.io/#/sequences/YOUR_SEQUENCE_ID`

## Email Content

### Email Step 1 - Introduction
- Mentions they used Astro at old company
- Notes their move to new company with timing
- Asks about Airflow landscape at new company
- Introduces AI tooling (for developers) and Blueprint (for non-developers)
- 6 style variations

### Email Step 2 - Follow-up
- Asks about biggest difference between old and new data teams
- Ties to understanding team composition and tooling needs
- 6 style variations

### Email Step 3 - Touch-base
- Brief final follow-up
- Variations: "Thoughts?", "Any thoughts on this?", "Bumping this. Any thoughts?"
- 6 style variations

## Apollo Custom Fields

The scripts populate these Apollo custom fields:
- `Email_Step_1` (ID: 69d6b947814f5d0015ad8d0d)
- `Email_Step_2` (ID: 69d6b9550c13b10011beee6e)
- `Email_Step_3` (ID: 69d6b963fd54f60019020cdc)

**To use in sequences:**
Add `{{Email_Step_1}}`, `{{Email_Step_2}}`, `{{Email_Step_3}}` in your sequence steps.

## Workflow Example

### Complete workflow for a new rep:

```bash
# Step 1: Populate email variables
python3 populate_alumni_emails.py "Joey Kenney"

# Step 2: Enroll in sequence (optional)
python3 add_to_specific_sequence.py \
  "/Users/vishwasrinivasan/Downloads/Joey_Kenney_Alumni_Prospects.csv" \
  "YOUR_SEQUENCE_ID"
```

### Results:
```
Total prospects: 141
Successfully updated: 84
Not found in Apollo: 10
Missing emails: 47
```

## Time Phrase Logic

The scripts automatically determine the time phrase based on `MONTHS_SINCE_JOB_CHANGE`:

- **0-3 months**: "recently"
- **4-6 months**: "a few months ago"
- **7-18 months**: "last year"
- **18+ months**: "a couple years ago"

## Company Name Normalization

Company names are automatically normalized by removing:
- Legal suffixes (Inc., LLC, Ltd., Corporation, etc.)
- Parenthetical content (e.g., "CRED" from "Dreamplug Technologies (CRED)")

## CSV Column Support

Scripts handle both formats:
- **Title Case**: `First Name`, `Last Name`, `New Email`, etc.
- **Uppercase**: `FIRST_NAME`, `LAST_NAME`, `NEW_EMAIL`, etc.

## Common Issues

### Apollo API Rate Limits
- Limit: 600 calls per hour for contact updates
- If hit, wait 1 hour and re-run
- Each contact requires 3 API calls (one per email step)

### Contacts Not Found in Apollo
- Contacts must exist in Apollo's database
- Use Apollo's enrichment to find them first
- Or manually create contact records

### Job Change Flags
- Apollo may flag alumni prospects with "recent job change"
- These must be manually added to sequences
- This is a safety feature to prevent sending to wrong emails

## Support

For issues or questions:
- Check the script output for detailed error messages
- Verify Apollo API credentials in `apollo_config.py`
- Verify Snowflake access and query script path

## License

Internal Astronomer Sales Tool
