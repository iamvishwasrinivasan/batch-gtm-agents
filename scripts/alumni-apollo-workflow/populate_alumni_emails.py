#!/usr/bin/env python3
"""
Master script to export alumni prospects from Snowflake and populate Apollo email variables.
Usage: python3 populate_alumni_emails.py "Rep Name" [--rep-name "Rep Name"]
Example: python3 populate_alumni_emails.py "Joey Kenney"
Example: python3 populate_alumni_emails.py "Nathan Cooley" --rep-name "Nathan Cooley"
"""

import sys
import json
import csv
import subprocess
import os
import argparse

# Try to import rep config to validate rep names
try:
    from rep_config import REP_EMAIL_ACCOUNTS
    SUPPORTS_MULTI_REP = True
except ImportError:
    SUPPORTS_MULTI_REP = False
    REP_EMAIL_ACCOUNTS = {}

def export_from_snowflake(rep_name):
    """Export prospects for a specific rep from Snowflake."""
    print(f"Exporting alumni prospects for {rep_name} from Snowflake...")

    query = f"""
    SELECT
        FIRST_NAME,
        LAST_NAME,
        NEW_COMPANY,
        OLD_COMPANY,
        OLD_ACCT_STATUS,
        ROLE_AT_OLD_ORG,
        OLD_ORG_ARR,
        OLD_ORG_PLAN,
        LOGIN_COUNT,
        GONG_CALLS,
        ZD_TICKETS,
        LAST_LOGIN,
        TENURE_MONTHS,
        NEW_TITLE,
        NEW_EMAIL,
        EMAIL_TYPE,
        LINKEDIN_URL,
        NEW_CO_EMPLOYEES,
        NEW_CO_COUNTRY,
        MONTHS_SINCE_JOB_CHANGE,
        MATCH_METHOD,
        SF_ACCOUNT_EXISTS,
        SF_ACCOUNT_OWNER,
        SF_ACCOUNT_URL,
        NEW_CO_IS_ASTRO_CUSTOMER
    FROM GTM.PUBLIC.ALUMNI_PROSPECTS
    WHERE SF_ACCOUNT_OWNER = '{rep_name}'
    ORDER BY MONTHS_SINCE_JOB_CHANGE
    """

    # Run Snowflake query
    result = subprocess.run(
        ['python3', f'{os.path.expanduser("~")}/batch-gtm-agents/scripts/snowflake_query.py', query],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"Error querying Snowflake: {result.stderr}")
        return None

    # Parse JSON result
    data = json.loads(result.stdout)

    if not data.get('success'):
        print(f"Query failed: {data.get('error')}")
        return None

    results = data.get('results', [])
    print(f"✓ Found {len(results)} prospects for {rep_name}")

    if not results:
        print("No prospects found for this rep")
        return None

    # Write to CSV
    csv_file = f'/Users/vishwasrinivasan/Downloads/{rep_name.replace(" ", "_")}_Alumni_Prospects.csv'
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print(f"✓ Created CSV: {csv_file}")
    return csv_file

def populate_email_variables(csv_file):
    """Run the three email population scripts."""
    scripts = [
        'add_email_drafts_to_apollo.py',
        'add_email_step2_to_apollo.py',
        'add_email_step3_to_apollo.py'
    ]

    script_dir = '/Users/vishwasrinivasan/Scripts'

    for script in scripts:
        print(f"\n{'='*70}")
        print(f"Running {script}...")
        print('='*70)

        result = subprocess.run(
            ['python3', f'{script_dir}/{script}', csv_file],
            cwd=script_dir
        )

        if result.returncode != 0:
            print(f"✗ {script} failed")
            return False

    return True

def main():
    parser = argparse.ArgumentParser(
        description='Export alumni prospects from Snowflake and populate Apollo email variables',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export and populate for a rep
  python3 populate_alumni_emails.py "Joey Kenney"

  # For multi-rep sequence enrollment (stores rep name for later use)
  python3 populate_alumni_emails.py "Nathan Cooley" --rep-name "Nathan Cooley"

Available reps (from rep_config.py):
""" + ("\n".join([f"  - {rep}" for rep in REP_EMAIL_ACCOUNTS.keys()]) if SUPPORTS_MULTI_REP else "  (rep_config.py not found)")
    )
    parser.add_argument('rep_name', help='Rep name to query Snowflake alumni prospects')
    parser.add_argument('--rep-name', dest='sending_rep', help='Rep name for sequence enrollment (stores for later use with add_to_specific_sequence.py)')

    args = parser.parse_args()
    rep_name = args.rep_name

    # Validate sending_rep if provided
    if args.sending_rep and SUPPORTS_MULTI_REP:
        if args.sending_rep not in REP_EMAIL_ACCOUNTS:
            print(f"Error: '{args.sending_rep}' not found in rep_config.py")
            print(f"Available reps: {', '.join(REP_EMAIL_ACCOUNTS.keys())}")
            sys.exit(1)
        print(f"✓ Validated sending rep: {args.sending_rep}")

    print("="*70)
    print("ALUMNI EMAIL POPULATION SCRIPT")
    print("="*70)
    print(f"Rep (Snowflake query): {rep_name}")
    if args.sending_rep:
        print(f"Rep (Sequence sender): {args.sending_rep}")
    print()

    # Step 1: Export from Snowflake
    csv_file = export_from_snowflake(rep_name)

    if not csv_file:
        print("\nExiting due to export failure")
        sys.exit(1)

    # Step 2: Populate email variables in Apollo
    print("\n" + "="*70)
    print("POPULATING APOLLO EMAIL VARIABLES")
    print("="*70)

    success = populate_email_variables(csv_file)

    if success:
        print("\n" + "="*70)
        print("✓ COMPLETE")
        print("="*70)
        print(f"All email variables populated for {rep_name}'s prospects")
        print(f"CSV saved to: {csv_file}")
        print()
        print("Next step: Enroll in sequence")
        if args.sending_rep:
            print(f'  python3 add_to_specific_sequence.py "{os.path.basename(csv_file)}" "<SEQUENCE_ID>" --rep-name "{args.sending_rep}"')
        else:
            print(f'  python3 add_to_specific_sequence.py "{os.path.basename(csv_file)}" "<SEQUENCE_ID>"')
    else:
        print("\n✗ Failed to populate all email variables")
        sys.exit(1)

if __name__ == '__main__':
    main()
