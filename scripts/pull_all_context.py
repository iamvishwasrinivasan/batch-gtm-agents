import json
import subprocess
import csv

# Get top 10 accounts to start
result = subprocess.run([
    "python3", "snowflake_query.py",
    """SELECT acct_name, tier, mql_count, call_count, opp_count
    FROM GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT
    WHERE batch_tag = '4/7 comm old demo request play'
    ORDER BY priority_score DESC, acct_name
    LIMIT 10"""
], capture_output=True, text=True, cwd="/Users/vishwasrinivasan/batch-gtm-agents")

data = json.loads(result.stdout)
accounts = data['results']

print("Pulling full context for first 10 accounts...\n")

context_data = []

for i, acct in enumerate(accounts):
    acct_name = acct['ACCT_NAME']
    print(f"\n{i+1}. {acct_name}")
    print("=" * 80)

    # Get full account details (contacts, MQLs, recent call)
    try:
        account_result = subprocess.run([
            "python3", "query_account.py", acct_name
        ], capture_output=True, text=True, cwd="/Users/vishwasrinivasan/batch-gtm-agents", timeout=30)

        account_data = json.loads(account_result.stdout)

        # Get MQL details with campaign info
        mql_result = subprocess.run([
            "python3", "snowflake_query.py",
            f"""SELECT m.mql_ts, m.reporting_channel, m.utm_campaign, c.title,
                   sc.FIRST_NAME, sc.LAST_NAME
            FROM HQ.MODEL_CRM.SF_MQLS m
            JOIN HQ.MODEL_CRM.SF_ACCOUNTS a ON m.acct_id = a.acct_id
            JOIN HQ.MODEL_CRM.SF_CONTACTS c ON m.contact_id = c.contact_id
            JOIN HQ.IN_SALESFORCE.CONTACT sc ON m.contact_id = sc.ID
            WHERE a.acct_name = '{acct_name}'
            ORDER BY m.mql_ts DESC
            LIMIT 5"""
        ], capture_output=True, text=True, cwd="/Users/vishwasrinivasan/batch-gtm-agents", timeout=30)

        mql_data = json.loads(mql_result.stdout)

        # Get email correspondence if available
        email_result = subprocess.run([
            "python3", "snowflake_query.py",
            f"""SELECT email_correspondence
            FROM GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT
            WHERE acct_name = '{acct_name}'"""
        ], capture_output=True, text=True, cwd="/Users/vishwasrinivasan/batch-gtm-agents", timeout=30)

        email_data = json.loads(email_result.stdout)

        context = {
            'acct_name': acct_name,
            'tier': acct['TIER'],
            'mql_count': acct['MQL_COUNT'],
            'call_count': acct['CALL_COUNT'],
            'account_data': account_data,
            'mql_details': mql_data.get('results', []),
            'email_correspondence': email_data.get('results', [{}])[0].get('EMAIL_CORRESPONDENCE') if email_data.get('results') else None
        }

        context_data.append(context)

        # Print summary
        print(f"MQLs: {len(mql_data.get('results', []))}")
        if mql_data.get('results'):
            latest_mql = mql_data['results'][0]
            print(f"  Latest: {latest_mql.get('FIRST_NAME')} {latest_mql.get('LAST_NAME')} - {latest_mql.get('REPORTING_CHANNEL')}")
            if latest_mql.get('UTM_CAMPAIGN'):
                print(f"  Campaign: {latest_mql.get('UTM_CAMPAIGN')}")

        if account_data.get('recent_call'):
            call = account_data['recent_call']
            print(f"Recent call: {call['title']} ({call['date'][:7]})")
            print(f"  Preview: {call['preview'][:200]}...")

        if context['email_correspondence']:
            print(f"Email correspondence: Available")

    except Exception as e:
        print(f"Error pulling context: {e}")
        continue

# Save to JSON
with open('/Users/vishwasrinivasan/batch-gtm-agents/context_data_first10.json', 'w') as f:
    json.dump(context_data, f, indent=2)

print(f"\n\nSaved context data for {len(context_data)} accounts")
print("File: /Users/vishwasrinivasan/batch-gtm-agents/context_data_first10.json")
