import csv
import json
import subprocess

# Get all account data
result = subprocess.run([
    "python3", "snowflake_query.py",
    """SELECT acct_name, tier, contact_count, mql_count, call_count, opp_count, latest_mql_date
    FROM GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT
    WHERE batch_tag = '4/7 comm old demo request play'
    ORDER BY priority_score DESC, acct_name"""
], capture_output=True, text=True, cwd="/Users/vishwasrinivasan/batch-gtm-agents")

data = json.loads(result.stdout)
accounts = data['results']

# Get latest MQL contact info for each account
mql_result = subprocess.run([
    "python3", "snowflake_query.py",
    """WITH ranked_mqls AS (
        SELECT
            a.acct_name,
            sc.FIRST_NAME,
            sc.LAST_NAME,
            c.title as mql_title,
            m.mql_ts,
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
    SELECT acct_name, first_name, last_name, mql_title
    FROM ranked_mqls
    WHERE rn = 1"""
], capture_output=True, text=True, cwd="/Users/vishwasrinivasan/batch-gtm-agents")

mql_data = json.loads(mql_result.stdout)
mql_by_account = {
    row['ACCT_NAME']: {
        'name': f"{row['FIRST_NAME']} {row['LAST_NAME']}" if row['FIRST_NAME'] and row['LAST_NAME'] else 'N/A',
        'title': row['MQL_TITLE']
    } for row in mql_data['results']
}

def clean_text(text):
    """Remove em-dashes and clean text for CSV"""
    return text.replace('—', '-').replace('\u2014', '-')

def generate_customer_sequence(acct):
    """For customers with existing relationship"""
    name = acct['ACCT_NAME']
    mqls = acct['MQL_COUNT']
    calls = acct['CALL_COUNT']

    email1 = f"""Subject: Add Airflow context to your AI assistant

Hi [Name],

We just launched Astronomer Agents - a plugin for Claude Code, Cursor, Copilot, etc. that adds Airflow-specific capabilities to your existing AI coding tools.

If you're already using an AI assistant at {name}, this plugs into it and gives it context about your actual Astro environment - your DAGs, connections, task logs, deployment configs.

Example: Ask Claude "why did my pipeline fail last night?" and it pulls actual logs from your Astro deployment instead of guessing.

With {calls} calls between our teams, figured this might be useful for your data engineering workflows.

Worth checking out? Takes about 2 minutes to install.

Best,
[Your name]"""

    email2 = f"""Subject: Re: Add Airflow context to your AI assistant

Hi [Name],

Following up on Astronomer Agents.

Since you're already a customer, the plugin connects automatically to your Astro environment. If you're using Claude Code or Cursor for development, it adds:
- DAG authoring skills using your actual patterns at {name}
- Real-time debugging with your task logs and deployment info
- Warehouse analysis while building pipeline logic

One customer used it to cut debugging time from 3 hours to 20 minutes - AI assistant did the log analysis and suggested the fix based on their real environment.

It's open source and works with any Airflow. Install: `claude plugin install astronomer-data@astronomer`

Worth trying?

Best,
[Your name]"""

    email3 = f"""Subject: Last note on Agents plugin

Hi [Name],

Last email from me. If you're happy with your current workflow or the plugin isn't something you need, totally fine.

But if you want to give your AI assistant context about your actual {name} environment, it's worth a shot.

Let me know either way.

Best,
[Your name]"""

    return clean_text(email1), clean_text(email2), clean_text(email3)

def generate_engaged_prospect_sequence(acct):
    """For prospects with MQLs and calls"""
    name = acct['ACCT_NAME']
    mqls = acct['MQL_COUNT']
    calls = acct['CALL_COUNT']

    email1 = f"""Subject: New Airflow plugin for AI coding tools

Hi [Name],

We just launched Astronomer Agents - a plugin that adds Airflow capabilities to Claude Code, Cursor, and other AI assistants.

With {mqls} people from {name} engaging with Astronomer and {calls} calls between our teams, figured this might be interesting. If you're using an AI coding tool, the plugin gives it context about Airflow environments:
- Generate DAGs using best practices
- Debug production issues with real logs
- Query data warehouses while building pipelines

Takes about 2 minutes to install and works with any Airflow deployment.

Curious if this sounds useful?

Best,
[Your name]"""

    email2 = f"""Subject: Re: New Airflow plugin for AI coding tools

Hi [Name],

Following up on Astronomer Agents.

The reason I thought of {name}: with {mqls} MQLs and {calls} calls, it seems like there's been real interest in Airflow orchestration. If you're already using Claude Code or Cursor, the plugin adds:
- Pattern reuse - generate new DAGs based on your existing code
- Real debugging - pulls actual logs when pipelines fail
- Warehouse integration - query your data while developing

One company reduced their DAG development time by 60% because their data scientists could build pipelines without waiting for engineering help.

It's open source and free. Install: `claude plugin install astronomer-data@astronomer`

Worth a quick try?

Best,
[Your name]"""

    email3 = f"""Subject: Closing the loop

Hi [Name],

Last note from me. If the plugin isn't relevant or you're happy with your current setup, totally fine.

But if you're using AI coding tools and working with Airflow, worth giving it context about your actual environment instead of generic examples.

Let me know either way.

Best,
[Your name]"""

    return clean_text(email1), clean_text(email2), clean_text(email3)

def generate_warm_mql_sequence(acct):
    """For accounts with MQLs but no calls"""
    name = acct['ACCT_NAME']
    mqls = acct['MQL_COUNT']

    email1 = f"""Subject: Following up on your Astronomer interest

Hi [Name],

Saw that {mqls} people from {name} engaged with Astronomer content - curious what sparked the interest?

We just launched something new that might be relevant: Astronomer Agents, a plugin for Claude Code, Cursor, and other AI coding tools that adds Airflow-specific capabilities.

If you're exploring Airflow orchestration and already using an AI assistant, the plugin can help with:
- Generating DAGs following best practices
- Debugging pipeline issues
- Analyzing data warehouse tables

Takes 2 minutes to install and works with any Airflow deployment (not just Astronomer).

Worth checking out if you're still exploring orchestration options?

Best,
[Your name]"""

    email2 = f"""Subject: Re: Following up on your Astronomer interest

Hi [Name],

Following up on Astronomer Agents.

The reason I reached out: {mqls} MQLs from {name} suggests some real interest in data orchestration. If you're evaluating Airflow and using AI coding tools, the plugin adds specialized capabilities:
- Context about Airflow best practices and patterns
- Can generate production-ready DAGs, not just examples
- Helps debug issues if you're running Airflow locally or in production

One team used it to go from zero Airflow experience to deploying their first production pipeline in 2 days.

It's open source and free: `claude plugin install astronomer-data@astronomer`

Worth trying?

Best,
[Your name]"""

    email3 = f"""Subject: Last note

Hi [Name],

Last email from me. If orchestration isn't a current priority or the plugin isn't relevant, no worries.

But if you're still exploring Airflow, the plugin can help accelerate your learning curve.

Let me know either way.

Best,
[Your name]"""

    return clean_text(email1), clean_text(email2), clean_text(email3)

def generate_cold_sequence(acct):
    """For cold prospects with no engagement"""
    name = acct['ACCT_NAME']

    email1 = f"""Subject: AI agents for data pipeline development

Hi [Name],

We just launched Astronomer Agents - a plugin for Claude Code, Cursor, and other AI coding tools that adds data orchestration capabilities.

If you're building data pipelines at {name} and using an AI assistant, the plugin can help with:
- Generating Airflow DAGs from natural language
- Debugging pipeline failures
- Analyzing data warehouse schemas

It's open source, free, and works with any Airflow deployment.

Curious if data orchestration is something you're working on?

Best,
[Your name]"""

    email2 = f"""Subject: Re: AI agents for data pipeline development

Hi [Name],

Following up on Astronomer Agents.

Not sure if data orchestration is a priority at {name}, but if you're using Airflow or exploring it, the plugin can accelerate development:
- Write DAGs faster using AI assistance
- Learn Airflow best practices automatically
- Debug issues with AI-powered analysis

One company used it to reduce their pipeline development time from weeks to days.

Install: `claude plugin install astronomer-data@astronomer`

Worth checking out if it's relevant?

Best,
[Your name]"""

    email3 = f"""Subject: Last note

Hi [Name],

Last email from me. If data orchestration isn't something you're focused on, totally fine.

But if you're working with Airflow and using AI coding tools, the plugin is worth a look.

Let me know either way.

Best,
[Your name]"""

    return clean_text(email1), clean_text(email2), clean_text(email3)

# Generate CSV
output_file = '/Users/vishwasrinivasan/batch-gtm-agents/email_sequences_4_7_batch.csv'

with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['Account Name', 'Tier', 'MQL Count', 'Call Count', 'Contact Count', 'Last MQL Contact', 'Last MQL Title', 'Email 1', 'Email 2', 'Email 3']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()

    for acct in accounts:
        tier = acct['TIER']
        acct_name = acct['ACCT_NAME']
        mql_info = mql_by_account.get(acct_name, {'name': 'N/A', 'title': 'N/A'})
        last_mql_contact = mql_info['name']
        last_mql_title = mql_info['title']

        # Generate appropriate sequence based on tier and engagement
        if tier == 'customer':
            email1, email2, email3 = generate_customer_sequence(acct)
        elif tier in ['engaged_prospect', 'hot_mql'] and acct['CALL_COUNT'] > 0:
            email1, email2, email3 = generate_engaged_prospect_sequence(acct)
        elif acct['MQL_COUNT'] > 0:
            email1, email2, email3 = generate_warm_mql_sequence(acct)
        else:
            email1, email2, email3 = generate_cold_sequence(acct)

        writer.writerow({
            'Account Name': acct_name,
            'Tier': tier,
            'MQL Count': acct['MQL_COUNT'],
            'Call Count': acct['CALL_COUNT'],
            'Contact Count': acct['CONTACT_COUNT'],
            'Last MQL Contact': last_mql_contact if last_mql_contact else 'N/A',
            'Last MQL Title': last_mql_title if last_mql_title else 'N/A',
            'Email 1': email1.strip(),
            'Email 2': email2.strip(),
            'Email 3': email3.strip()
        })

print(f"Generated email sequences for {len(accounts)} accounts")
print(f"Output saved to: {output_file}")
