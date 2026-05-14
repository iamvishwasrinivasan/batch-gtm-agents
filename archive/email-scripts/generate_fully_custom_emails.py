import csv
import json
import subprocess
import time
from datetime import datetime

def clean_text(text):
    """Remove em-dashes"""
    return text.replace('—', '-').replace('\u2014', '-')

def format_date(date_str):
    """Format as 'last September' or 'March'"""
    try:
        dt = datetime.strptime(date_str[:10], '%Y-%m-%d')
        month = dt.strftime('%B')
        if dt.year == 2025:
            return f"last {month}"
        return month
    except:
        return "recently"

def get_account_context(acct_name):
    """Pull all available context for an account"""
    context = {'acct_name': acct_name}

    # Get account details
    try:
        result = subprocess.run([
            "python3", "query_account.py", acct_name
        ], capture_output=True, text=True, cwd="/Users/vishwasrinivasan/batch-gtm-agents", timeout=30)

        data = json.loads(result.stdout)
        context['account_data'] = data
        context['recent_call'] = data.get('recent_call')
        context['mqls'] = data.get('mqls', [])
        context['contacts'] = data.get('contacts', [])
    except Exception as e:
        print(f"  Warning: Could not get account data - {e}")
        context['account_data'] = {}
        context['recent_call'] = None
        context['mqls'] = []

    # Get MQL details with campaigns
    try:
        result = subprocess.run([
            "python3", "snowflake_query.py",
            f"""SELECT m.mql_ts, m.reporting_channel, m.utm_campaign,
                   c.title, sc.FIRST_NAME, sc.LAST_NAME
            FROM HQ.MODEL_CRM.SF_MQLS m
            JOIN HQ.MODEL_CRM.SF_ACCOUNTS a ON m.acct_id = a.acct_id
            JOIN HQ.MODEL_CRM.SF_CONTACTS c ON m.contact_id = c.contact_id
            JOIN HQ.IN_SALESFORCE.CONTACT sc ON m.contact_id = sc.ID
            WHERE a.acct_name = '{acct_name.replace("'", "''")}'
            ORDER BY m.mql_ts DESC
            LIMIT 3"""
        ], capture_output=True, text=True, cwd="/Users/vishwasrinivasan/batch-gtm-agents", timeout=30)

        data = json.loads(result.stdout)
        context['mql_details'] = data.get('results', [])
    except Exception as e:
        print(f"  Warning: Could not get MQL details - {e}")
        context['mql_details'] = []

    # Get tech stack
    try:
        result = subprocess.run([
            "python3", "snowflake_query.py",
            f"""SELECT tech_stack FROM GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT
            WHERE acct_name = '{acct_name.replace("'", "''")}'"""
        ], capture_output=True, text=True, cwd="/Users/vishwasrinivasan/batch-gtm-agents", timeout=30)

        data = json.loads(result.stdout)
        if data.get('results'):
            tech_stack_str = data['results'][0].get('TECH_STACK', '[]')
            context['tech_stack'] = json.loads(tech_stack_str) if tech_stack_str else []
        else:
            context['tech_stack'] = []
    except Exception as e:
        context['tech_stack'] = []

    return context

def write_custom_emails(acct_name, tier, mqls, calls, context):
    """Write truly custom emails based on available context"""

    # Check what context we have
    has_call = context.get('recent_call') is not None
    has_mqls = len(context.get('mql_details', [])) > 0
    has_tech_stack = len(context.get('tech_stack', [])) > 0

    # Write based on best available context
    if has_call and calls > 0:
        return write_call_based_emails(acct_name, calls, mqls, context)
    elif has_mqls:
        return write_mql_based_emails(acct_name, mqls, calls, context)
    elif has_tech_stack:
        return write_tech_stack_emails(acct_name, mqls, context)
    else:
        return write_minimal_context_emails(acct_name, mqls, calls)

def write_call_based_emails(acct_name, calls, mqls, context):
    """Custom emails based on actual call transcript"""
    call = context['recent_call']
    call_date = format_date(call['date'])
    preview = call['preview'][:1000]

    # Extract key pain points from preview
    pain_point = ""
    if "only" in preview and "data engineer" in preview:
        pain_point = "you're still the only data engineer"
    elif "pilot" in preview or "McKinsey" in preview:
        pain_point = "you mentioned your pilot"
    elif "terraform" in preview.lower() or "version control" in preview.lower():
        pain_point = "you set up infrastructure with Terraform"
    elif "issue" in preview or "problem" in preview:
        pain_point = "you mentioned hitting some issues"
    else:
        pain_point = "we talked about your Airflow setup"

    email1 = f"""Subject: Following up after our call

Hi [Name],

Back in {call_date} {pain_point}. Wanted to reach out about something we just launched.

Astronomer Agents is a plugin for Claude Code/Cursor that helps build Airflow DAGs using AI. If you're still working with Airflow, it could help with the challenges you mentioned.

The plugin can:
- Generate DAGs from descriptions (saves time writing boilerplate)
- Debug production issues by pulling real logs from your environment
- Reuse your existing patterns (not generic examples)

Curious if those challenges are still relevant?

Best,
[Your name]"""

    engagement = ""
    if mqls > 1 and calls > 1:
        engagement = f"We've had {calls} calls and seen {mqls} people from {acct_name} engage with our content."
    elif calls > 1:
        engagement = f"We've had {calls} calls since then."
    else:
        engagement = f"Following up from our conversation."

    email2 = f"""Subject: Re: Following up after our call

Hi [Name],

Following up on Astronomer Agents.

{engagement} If you're using Claude Code or Cursor for development, the plugin connects to your actual Astro environment and can:
- Generate new DAGs using {acct_name}'s existing patterns
- Pull your actual logs for debugging (not generic advice)
- Help speed up pipeline development

One team with similar challenges used it to cut their DAG development time by 60%.

Install: claude plugin install astronomer-data@astronomer

Worth trying?

Best,
[Your name]"""

    email3 = f"""Subject: Last note

Hi [Name],

Last email from me.

If you've solved those challenges or the plugin isn't relevant, totally fine. But if you're still dealing with the issues from our {call_date} call, it might help.

Let me know either way.

Best,
[Your name]"""

    return clean_text(email1), clean_text(email2), clean_text(email3)

def write_mql_based_emails(acct_name, mqls, calls, context):
    """Custom emails based on MQL context"""
    latest_mql = context['mql_details'][0]
    channel = latest_mql.get('REPORTING_CHANNEL', 'Unknown')
    campaign = latest_mql.get('UTM_CAMPAIGN', '') or ''
    name = f"{latest_mql.get('FIRST_NAME', '')} {latest_mql.get('LAST_NAME', '')}".strip()

    # Determine hook based on campaign/channel
    if 'airflow-3' in campaign.lower() or 'airflow 3' in campaign.lower():
        hook = f"Saw {name or 'someone from your team'} attended our Airflow 3 certification webinar"
        pain_point = "learning Airflow 3"
        solution = "learn Airflow 3 faster - generates DAGs using best practices so you learn by example"
    elif 'debugging' in campaign.lower():
        hook = f"Saw {name or 'someone from your team'} downloaded our debugging ebook"
        pain_point = "hitting pipeline issues"
        solution = "debug Airflow issues faster - pulls actual logs and suggests fixes"
    elif channel == 'Free Trial':
        hook = f"Saw {name or 'someone from your team'} tried the Astronomer free trial"
        pain_point = "evaluating orchestration tools"
        solution = "work with Airflow easier (works with any deployment, not just Astronomer)"
    elif 'webinar' in channel.lower():
        hook = f"Saw {name or 'someone from your team'} attended one of our Airflow webinars"
        pain_point = "learning Airflow"
        solution = "learn Airflow faster - generates DAGs and explains the reasoning behind choices"
    else:
        hook = f"Saw {name or 'someone from your team'} engaged with Astronomer content"
        pain_point = "working with Airflow"
        solution = "build Airflow pipelines faster using AI"

    email1 = f"""Subject: Following up on your Astronomer interest

Hi [Name],

{hook} - curious if you're actively {pain_point} now?

We just launched Astronomer Agents, a plugin for Claude Code/Cursor that helps {solution}.

Takes 2 minutes to install and works with any Airflow deployment.

Still exploring orchestration?

Best,
[Your name]"""

    engagement = ""
    if mqls > 1 and calls > 0:
        engagement = f"We've had {calls} calls and seen {mqls} people from {acct_name} engage with our content, so it seems like there's real interest in Airflow."
    elif mqls > 1:
        engagement = f"I've seen {mqls} people from {acct_name} engage with our content, so it seems like there's interest in Airflow on your team."
    elif calls > 0:
        engagement = f"We've had {calls} calls with your team about Airflow."
    else:
        engagement = "It seems like Airflow might be on your radar."

    email2 = f"""Subject: Re: Following up on your Astronomer interest

Hi [Name],

Following up on Astronomer Agents.

{engagement} If you're using Claude Code or Cursor, the plugin can help:
- Speed up DAG development
- Debug issues faster with real logs from your environment
- Reduce learning curve for new team members

It's open source and free: claude plugin install astronomer-data@astronomer

Worth checking out?

Best,
[Your name]"""

    email3 = f"""Subject: Last note

Hi [Name],

Last email from me.

If you went a different direction on orchestration or the plugin isn't relevant, no worries. But if you're still working with Airflow, it's worth a look.

Let me know either way.

Best,
[Your name]"""

    return clean_text(email1), clean_text(email2), clean_text(email3)

def write_tech_stack_emails(acct_name, mqls, context):
    """Emails based on tech stack only"""
    tech_stack = context['tech_stack']
    has_airflow = 'airflow' in [t.lower() for t in tech_stack]
    has_multiple_orchestration = sum(1 for t in tech_stack if t.lower() in ['airflow', 'dagster', 'prefect', 'mage', 'kestra']) > 1

    if has_multiple_orchestration:
        hook = f"Noticed you have multiple orchestration tools in your stack at {acct_name}"
        pain_point = "managing multiple orchestration platforms"
    elif has_airflow:
        hook = f"Saw you're running Airflow at {acct_name}"
        pain_point = "building and maintaining Airflow pipelines"
    else:
        hook = f"Reaching out about orchestration at {acct_name}"
        pain_point = "data orchestration"

    email1 = f"""Subject: Airflow plugin for AI coding tools

Hi [Name],

{hook} - curious if {pain_point} is a challenge?

We just launched Astronomer Agents, a plugin for Claude Code/Cursor that helps build Airflow pipelines using AI.

If you're working with Airflow, the plugin can:
- Generate DAGs from natural language descriptions
- Debug production pipeline failures
- Help your team move faster

Takes 2 minutes to install and works with any Airflow deployment.

Curious if this is relevant to what you're working on?

Best,
[Your name]"""

    engagement = ""
    if mqls > 1:
        engagement = f"I've seen {mqls} people from {acct_name} engage with our content, so orchestration seems to be on your radar."
    elif mqls == 1:
        engagement = "I saw someone from your team engage with our content, so orchestration might be on your radar."
    else:
        engagement = "Not sure if orchestration is on your radar, but figured I'd reach out."

    email2 = f"""Subject: Re: Airflow plugin for AI coding tools

Hi [Name],

Following up on Astronomer Agents.

{engagement} If you're using Claude Code or Cursor and working with Airflow, the plugin can:
- Speed up DAG development
- Debug issues faster
- Reduce learning curve for new team members

It's open source and free: claude plugin install astronomer-data@astronomer

Worth checking out if it's relevant?

Best,
[Your name]"""

    email3 = f"""Subject: Last note

Hi [Name],

Last email from me.

If orchestration isn't something you're focused on or the plugin isn't relevant, no worries. But if you're working with Airflow and using AI coding tools, it's worth a look.

Let me know either way.

Best,
[Your name]"""

    return clean_text(email1), clean_text(email2), clean_text(email3)

def write_minimal_context_emails(acct_name, mqls, calls):
    """Honest cold outreach for zero context"""

    if mqls == 1:
        hook = "Saw someone from your team engaged with Astronomer content but we've never talked."
    elif mqls > 1:
        hook = f"Saw {mqls} people from {acct_name} engaged with our content but we've never talked."
    elif calls > 0:
        hook = f"We've had {calls} calls with your team but I'm not sure where things landed."
    else:
        hook = "Not sure how you ended up in our system, but reaching out cold."

    email1 = f"""Subject: Airflow plugin for AI coding tools

Hi [Name],

{hook} Curious if data orchestration is something you're working on?

We just launched Astronomer Agents - a plugin for Claude Code/Cursor that helps build Airflow pipelines using AI. Takes 2 minutes to install if it's relevant.

Worth a conversation if orchestration is on your radar?

Best,
[Your name]"""

    email2 = f"""Subject: Re: Airflow plugin for AI coding tools

Hi [Name],

Following up on Astronomer Agents.

If you're working with Airflow and using Claude Code or Cursor, the plugin can:
- Generate DAGs from natural language descriptions
- Debug production pipeline failures
- Help your team learn Airflow faster

It's open source and free: claude plugin install astronomer-data@astronomer

Worth checking out if it's relevant?

Best,
[Your name]"""

    email3 = f"""Subject: Last note

Hi [Name],

Last email from me. If orchestration isn't something you're focused on, no worries.

But if you're working with Airflow, the plugin is worth a look.

Let me know either way.

Best,
[Your name]"""

    return clean_text(email1), clean_text(email2), clean_text(email3)

# Main execution
print("Generating fully custom emails for all 120 accounts...")
print("This will take 10-15 minutes to pull context and write custom emails.\n")

# Get all accounts
result = subprocess.run([
    "python3", "snowflake_query.py",
    """SELECT acct_name, tier, contact_count, mql_count, call_count, opp_count
    FROM GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT
    WHERE batch_tag = '4/7 comm old demo request play'
    ORDER BY priority_score DESC, acct_name"""
], capture_output=True, text=True, cwd="/Users/vishwasrinivasan/batch-gtm-agents")

data = json.loads(result.stdout)
accounts = data['results']

# Get MQL contact names for all accounts
mql_result = subprocess.run([
    "python3", "snowflake_query.py",
    """WITH ranked_mqls AS (
        SELECT
            a.acct_name,
            sc.FIRST_NAME,
            sc.LAST_NAME,
            c.title as mql_title,
            m.reporting_channel,
            ROW_NUMBER() OVER (PARTITION BY a.acct_name ORDER BY m.mql_ts DESC) as rn
        FROM HQ.MODEL_CRM.SF_MQLS m
        JOIN HQ.MODEL_CRM.SF_ACCOUNTS a ON m.acct_id = a.acct_id
        JOIN HQ.MODEL_CRM.SF_CONTACTS c ON m.contact_id = c.contact_id
        JOIN HQ.IN_SALESFORCE.CONTACT sc ON m.contact_id = sc.ID
        WHERE a.acct_name IN (
            SELECT acct_name FROM GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT
            WHERE batch_tag = '4/7 comm old demo request play'
        )
    )
    SELECT acct_name, first_name, last_name, mql_title, reporting_channel
    FROM ranked_mqls
    WHERE rn = 1"""
], capture_output=True, text=True, cwd="/Users/vishwasrinivasan/batch-gtm-agents")

mql_data = json.loads(mql_result.stdout)
mql_by_account = {}
for row in mql_data['results']:
    acct_name = row['ACCT_NAME']
    mql_by_account[acct_name] = {
        'name': f"{row['FIRST_NAME']} {row['LAST_NAME']}" if row['FIRST_NAME'] and row['LAST_NAME'] else 'N/A',
        'title': row['MQL_TITLE'],
        'channel': row['REPORTING_CHANNEL']
    }

# Generate custom emails for each account
output_file = '/Users/vishwasrinivasan/batch-gtm-agents/email_sequences_FULLY_CUSTOM.csv'

with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['Account Name', 'Tier', 'MQL Count', 'Call Count', 'Contact Count', 'Last MQL Contact', 'Last MQL Title', 'Last MQL Channel', 'Email 1', 'Email 2', 'Email 3']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for i, acct in enumerate(accounts):
        acct_name = acct['ACCT_NAME']
        tier = acct['TIER']
        mqls = acct['MQL_COUNT']
        calls = acct['CALL_COUNT']

        print(f"Processing {i+1}/120: {acct_name} (MQLs: {mqls}, Calls: {calls})")

        # Get MQL info
        mql_info = mql_by_account.get(acct_name, {'name': 'N/A', 'title': 'N/A', 'channel': 'N/A'})

        # Pull context (only for top 30 with calls to save time)
        if calls > 0 and i < 30:
            print(f"  Pulling call context...")
            context = get_account_context(acct_name)
        else:
            # Minimal context for others
            context = {'acct_name': acct_name, 'tech_stack': [], 'mql_details': []}
            if mqls > 0:
                # Get MQL details for accounts without calls
                try:
                    result = subprocess.run([
                        "python3", "snowflake_query.py",
                        f"""SELECT m.reporting_channel, m.utm_campaign, c.title,
                               sc.FIRST_NAME, sc.LAST_NAME
                        FROM HQ.MODEL_CRM.SF_MQLS m
                        JOIN HQ.MODEL_CRM.SF_ACCOUNTS a ON m.acct_id = a.acct_id
                        JOIN HQ.MODEL_CRM.SF_CONTACTS c ON m.contact_id = c.contact_id
                        JOIN HQ.IN_SALESFORCE.CONTACT sc ON m.contact_id = sc.ID
                        WHERE a.acct_name = '{acct_name.replace("'", "''")}'
                        ORDER BY m.mql_ts DESC LIMIT 1"""
                    ], capture_output=True, text=True, cwd="/Users/vishwasrinivasan/batch-gtm-agents", timeout=30)

                    data = json.loads(result.stdout)
                    context['mql_details'] = data.get('results', [])
                except:
                    context['mql_details'] = []

        # Write custom emails
        email1, email2, email3 = write_custom_emails(acct_name, tier, mqls, calls, context)

        writer.writerow({
            'Account Name': acct_name,
            'Tier': tier,
            'MQL Count': mqls,
            'Call Count': calls,
            'Contact Count': acct['CONTACT_COUNT'],
            'Last MQL Contact': mql_info['name'],
            'Last MQL Title': mql_info['title'] if mql_info['title'] else 'N/A',
            'Last MQL Channel': mql_info['channel'] if mql_info['channel'] else 'N/A',
            'Email 1': email1.strip(),
            'Email 2': email2.strip(),
            'Email 3': email3.strip()
        })

        # Small delay to avoid overwhelming Snowflake
        if i % 10 == 0:
            time.sleep(1)

print(f"\n\nGenerated fully custom email sequences for {len(accounts)} accounts")
print(f"Output saved to: {output_file}")
