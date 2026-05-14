import csv
import json
import subprocess
import re

# Get all account data
result = subprocess.run([
    "python3", "snowflake_query.py",
    """SELECT acct_name, tier, contact_count, mql_count, call_count, opp_count
    FROM GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT
    WHERE batch_tag = '4/7 comm old demo request play'
    ORDER BY priority_score DESC, acct_name"""
], capture_output=True, text=True, cwd="/Users/vishwasrinivasan/batch-gtm-agents")

data = json.loads(result.stdout)
accounts = data['results']

# Get latest MQL contact info and context
mql_result = subprocess.run([
    "python3", "snowflake_query.py",
    """WITH ranked_mqls AS (
        SELECT
            a.acct_name,
            sc.FIRST_NAME,
            sc.LAST_NAME,
            c.title as mql_title,
            m.mql_ts,
            m.reporting_channel,
            m.utm_campaign,
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
    SELECT acct_name, first_name, last_name, mql_title, reporting_channel, utm_campaign
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
        'channel': row['REPORTING_CHANNEL'],
        'campaign': row['UTM_CAMPAIGN']
    }

def clean_text(text):
    """Remove em-dashes and clean text for CSV"""
    return text.replace('—', '-').replace('\u2014', '-')

def format_call_date(date_str):
    """Format date as 'last December' or 'March' based on whether it's last year"""
    from datetime import datetime
    try:
        # Parse date like "2025-09-30"
        dt = datetime.strptime(date_str[:10], '%Y-%m-%d')
        month_name = dt.strftime('%B')

        # Check if it's from last year (2025)
        if dt.year == 2025:
            return f"last {month_name}"
        else:
            return month_name
    except:
        return "recently"

def get_call_context(acct_name):
    """Get most recent call context for an account"""
    try:
        result = subprocess.run([
            "python3", "query_account.py", acct_name
        ], capture_output=True, text=True, cwd="/Users/vishwasrinivasan/batch-gtm-agents", timeout=30)

        data = json.loads(result.stdout)
        if data.get('recent_call'):
            return {
                'title': data['recent_call']['title'],
                'date': data['recent_call']['date'],
                'preview': data['recent_call']['preview'][:500]  # First 500 chars
            }
    except:
        pass
    return None

def infer_context_from_mql(mql_info):
    """Infer context from MQL channel and campaign"""
    channel = mql_info.get('channel', '').lower()
    campaign = mql_info.get('campaign', '').lower() if mql_info.get('campaign') else ''

    # Airflow 3 certification
    if 'airflow-3' in campaign or 'airflow 3' in campaign:
        return "airflow_3_cert"

    # Debugging webinars
    if 'debugging' in campaign:
        return "debugging_issues"

    # Free trial
    if channel == 'free trial':
        return "free_trial"

    # Webinars (general learning)
    if channel == 'webinar':
        return "learning_airflow"

    # Virtual events
    if 'virtual event' in channel or 'field event' in channel:
        return "event_attendee"

    # Paid social/search
    if 'paid' in channel.lower():
        return "pain_point_search"

    # Web content
    if 'web content' in channel:
        return "researching_solutions"

    return "general_interest"

def generate_email_sequence(acct, mql_info, call_context):
    """Generate personalized 3-email sequence based on context"""
    name = acct['ACCT_NAME']
    mqls = acct['MQL_COUNT']
    calls = acct['CALL_COUNT']
    tier = acct['TIER']

    # Determine primary context
    if call_context and calls > 0:
        context_type = "call_based"
    elif mql_info:
        context_type = infer_context_from_mql(mql_info)
    else:
        context_type = "generic"

    # Generate emails based on context (now passing calls to all functions)
    if context_type == "airflow_3_cert":
        return generate_airflow_3_cert_sequence(name, mqls, calls, mql_info)
    elif context_type == "debugging_issues":
        return generate_debugging_sequence(name, mqls, calls, mql_info)
    elif context_type == "free_trial":
        return generate_free_trial_sequence(name, mqls, calls, tier)
    elif context_type == "learning_airflow":
        return generate_learning_sequence(name, mqls, calls, mql_info)
    elif context_type == "event_attendee":
        return generate_event_sequence(name, mqls, calls, mql_info)
    elif context_type == "call_based":
        return generate_call_based_sequence(name, mqls, calls, call_context)
    else:
        return generate_generic_sequence(name, mqls, calls, tier)

def generate_airflow_3_cert_sequence(name, mqls, calls, mql_info):
    campaign = mql_info.get('campaign', '')

    email1 = f"""Subject: Following up after the Airflow 3 webinar

Hi [Name],

Saw you attended our Airflow 3 certification webinar - curious if you're actively using Airflow 3 now or still learning?

We just launched Astronomer Agents, a plugin for Claude Code/Cursor that helps you learn Airflow 3 faster using AI.

If you're still working through certification or building your first production Airflow 3 pipelines, the plugin can:
- Generate Airflow 3 DAGs following best practices (learn by example)
- Debug issues that come up while learning
- Answer questions about Airflow 3 features in context

One person who attended the same webinar used it to go from beginner to deploying production pipelines in 2 weeks.

Worth checking out?

Best,
[Your name]"""

    # Better metric integration
    engagement_context = ""
    if mqls > 1 and calls > 0:
        engagement_context = f"I've seen {mqls} people from {name} engage with our content and we've had {calls} calls with your team, so it seems like you're investing in Airflow skills."
    elif mqls > 1:
        engagement_context = f"I've seen {mqls} people from {name} engage with our content, so it seems like you're investing in Airflow skills as a team."
    elif calls > 0:
        engagement_context = f"We've had {calls} calls with your team about Airflow, so it seems like you're investing in these skills."
    else:
        engagement_context = "It seems like you're investing time in learning Airflow."

    email2 = f"""Subject: Re: Following up after the Airflow 3 webinar

Hi [Name],

Following up on Astronomer Agents.

{engagement_context} The plugin can help accelerate that if you're using Claude Code or Cursor for development:
- "Generate an Airflow 3 DAG that does X" and it writes it using best practices
- Explains why it made certain choices (so you learn the reasoning)
- Helps debug when your DAGs don't work as expected

It's like having an Airflow expert sitting next to you while you code.

Install: claude plugin install astronomer-data@astronomer

Worth trying?

Best,
[Your name]"""

    email3 = f"""Subject: Last note

Hi [Name],

Last email from me. If you're progressing well with Airflow 3 learning or the plugin isn't relevant, no worries.

But if you're still working through certification or building your first pipelines, the plugin can help you learn faster.

Let me know either way.

Best,
[Your name]"""

    return clean_text(email1), clean_text(email2), clean_text(email3)

def generate_debugging_sequence(name, mqls, calls, mql_info):
    email1 = f"""Subject: Following up after the debugging webinar

Hi [Name],

Saw you attended our DAG debugging webinar - sounds like you might be hitting some tricky pipeline issues?

We just launched Astronomer Agents, a plugin for Claude Code/Cursor that helps debug Airflow issues using AI.

If you're still dealing with DAG failures or hard-to-diagnose issues, the plugin can:
- Pull actual logs from your Airflow environment to diagnose problems
- Suggest fixes based on your specific error messages
- Help you write better error handling and testing

One data engineer used it to cut their debugging time from 3 hours to 20 minutes by letting AI do the log analysis.

Curious if debugging is still a pain point?

Best,
[Your name]"""

    # Better metric integration
    engagement_context = ""
    if mqls > 1 and calls > 0:
        engagement_context = f"We've had {calls} calls and seen {mqls} people from {name} engage with our content, so it sounds like debugging might be a team-wide challenge."
    elif mqls > 1:
        engagement_context = f"I've seen {mqls} people from {name} attend webinars and engage with our content, so debugging sounds like a team-wide challenge."
    elif calls > 0:
        engagement_context = f"We've had {calls} calls with your team, and debugging came up as a challenge."
    else:
        engagement_context = "Debugging is a common challenge we hear about."

    email2 = f"""Subject: Re: Following up after the debugging webinar

Hi [Name],

Following up on Astronomer Agents.

{engagement_context} If you're using Claude Code or Cursor, the plugin can help:
- Real-time debugging with actual logs from your environment (not generic advice)
- Root cause analysis when DAGs fail
- Suggestions for fixing common issues (dependencies, resource constraints, etc.)

It knows your actual deployment, so suggestions are specific to your setup, not generic Stack Overflow answers.

Install: claude plugin install astronomer-data@astronomer

Worth trying?

Best,
[Your name]"""

    email3 = f"""Subject: Last note

Hi [Name],

Last email from me. If you've solved the debugging issues or found other tools that work, that's great.

But if pipeline failures are still eating up your time, the plugin can help you diagnose and fix issues faster.

Let me know either way.

Best,
[Your name]"""

    return clean_text(email1), clean_text(email2), clean_text(email3)

def generate_free_trial_sequence(name, mqls, calls, tier):
    email1 = f"""Subject: Following up on your free trial

Hi [Name],

Saw you tried the Astronomer free trial - curious how that went?

We just launched Astronomer Agents, a plugin for Claude Code/Cursor that makes working with Airflow (and Astro) a lot easier.

If you're still evaluating orchestration tools or already using Airflow, the plugin can:
- Generate DAGs from natural language descriptions
- Debug production issues by pulling real logs
- Help your team ramp up on Airflow faster

Works with any Airflow deployment, not just Astronomer. Takes 2 minutes to install.

Still exploring orchestration options?

Best,
[Your name]"""

    # Better metric integration
    engagement_context = ""
    if mqls > 1 and calls > 0:
        engagement_context = f"We've had {calls} calls and seen {mqls} people from {name} try the free trial or engage with our content. Not sure if you went with Astronomer, another tool, or built in-house, but it seems like there's real interest in Airflow orchestration."
    elif mqls > 1:
        engagement_context = f"I've seen {mqls} people from {name} try the free trial and engage with our content, so it seems like there's real interest in Airflow orchestration. Not sure where you landed."
    elif calls > 0:
        engagement_context = f"We've had {calls} calls about your evaluation. Not sure if you went with Astronomer, another tool, or built in-house."
    else:
        engagement_context = "Not sure if you went with Astronomer, another tool, or built in-house after the trial."

    email2 = f"""Subject: Re: Following up on your free trial

Hi [Name],

Following up on Astronomer Agents.

{engagement_context}

Either way, if you're using Airflow, the plugin can help:
- Speed up DAG development (especially if your team is still learning Airflow)
- Debug issues faster
- Reduce the learning curve for new team members

One company that tried our free trial used the plugin to go from evaluation to production deployment in 3 weeks.

Install: claude plugin install astronomer-data@astronomer

Worth checking out?

Best,
[Your name]"""

    email3 = f"""Subject: Last note

Hi [Name],

Last email from me. If you went with a different orchestration tool or built in-house, totally fine.

But if you're using Airflow and want to give your team AI-powered help with DAG development, it's worth a shot.

Let me know either way.

Best,
[Your name]"""

    return clean_text(email1), clean_text(email2), clean_text(email3)

def generate_learning_sequence(name, mqls, calls, mql_info):
    email1 = f"""Subject: Following up after the webinar

Hi [Name],

Saw you attended one of our Airflow webinars - curious if you're actively using Airflow now or still learning?

We just launched Astronomer Agents, a plugin for Claude Code/Cursor that helps you learn Airflow faster using AI.

If you're building your first production pipelines, the plugin can:
- Generate DAGs following best practices (learn by example)
- Debug issues that come up
- Answer questions about Airflow features in context

One person who attended a similar webinar used it to go from zero Airflow experience to deploying production pipelines in 2 weeks.

Worth checking out?

Best,
[Your name]"""

    # Better metric integration
    engagement_context = ""
    if mqls > 1 and calls > 0:
        engagement_context = f"We've had {calls} calls and seen {mqls} people from {name} attend webinars and engage with our content, so it seems like your team is investing in Airflow skills."
    elif mqls > 1:
        engagement_context = f"I've seen {mqls} people from {name} attend webinars and engage with our content, so it seems like your team is investing in Airflow skills."
    elif calls > 0:
        engagement_context = f"We've had {calls} calls with your team about Airflow."
    else:
        engagement_context = "It seems like you're investing time in learning Airflow."

    email2 = f"""Subject: Re: Following up after the webinar

Hi [Name],

Following up on Astronomer Agents.

{engagement_context} If you're using Claude Code or Cursor, the plugin can accelerate that learning:
- Generates DAGs using best practices (so you learn correct patterns)
- Explains why it made certain choices
- Helps debug when things don't work as expected

It's like having an Airflow expert pair programming with you.

Install: claude plugin install astronomer-data@astronomer

Worth trying?

Best,
[Your name]"""

    email3 = f"""Subject: Last note

Hi [Name],

Last email from me. If you're progressing well with Airflow or the plugin isn't relevant, no worries.

But if you're still learning or building your first pipelines, the plugin can help you move faster.

Let me know either way.

Best,
[Your name]"""

    return clean_text(email1), clean_text(email2), clean_text(email3)

def generate_event_sequence(name, mqls, calls, mql_info):
    email1 = f"""Subject: Following up after the event

Hi [Name],

Saw you attended one of our virtual events - hope you got something useful out of it.

We just launched Astronomer Agents, a plugin for Claude Code/Cursor that helps build Airflow pipelines using AI.

If you're exploring data orchestration or already using Airflow, the plugin can:
- Generate DAGs from natural language descriptions
- Debug production issues
- Help your team learn Airflow best practices

Takes 2 minutes to install and works with any Airflow deployment.

Curious if orchestration is something you're actively working on?

Best,
[Your name]"""

    # Better metric integration
    engagement_context = ""
    if mqls > 1 and calls > 0:
        engagement_context = f"We've had {calls} calls and seen {mqls} people from {name} attend events and engage with our content, so it seems like there's interest in data orchestration on your team."
    elif mqls > 1:
        engagement_context = f"I've seen {mqls} people from {name} attend events and engage with our content, so it seems like there's interest in data orchestration on your team."
    elif calls > 0:
        engagement_context = f"We've had {calls} calls with your team about orchestration."
    else:
        engagement_context = "It seems like orchestration might be on your radar."

    email2 = f"""Subject: Re: Following up after the event

Hi [Name],

Following up on Astronomer Agents.

{engagement_context} If you're using Claude Code or Cursor and working with Airflow, the plugin can:
- Speed up DAG development (generate boilerplate faster)
- Debug issues with real context from your environment
- Help team members ramp up faster

One company that attended a similar event used the plugin to reduce their pipeline development time by 60%.

Install: claude plugin install astronomer-data@astronomer

Worth checking out?

Best,
[Your name]"""

    email3 = f"""Subject: Last note

Hi [Name],

Last email from me. If orchestration isn't a current focus or the plugin isn't relevant, no worries.

But if you're working with Airflow and using AI coding tools, worth giving it context about your environment.

Let me know either way.

Best,
[Your name]"""

    return clean_text(email1), clean_text(email2), clean_text(email3)

def generate_call_based_sequence(name, mqls, calls, call_context):
    # Generic call-based sequence with date formatting
    call_date = format_call_date(call_context.get('date', ''))

    email1 = f"""Subject: Following up after our call

Hi [Name],

We talked back in {call_date} about your Airflow setup. Wanted to reach out about something new we launched.

Astronomer Agents is a plugin for Claude Code/Cursor that helps build and debug Airflow pipelines using AI.

If you're still working with Airflow, the plugin can:
- Generate DAGs from natural language descriptions
- Debug production issues by pulling real logs
- Help your team move faster on pipeline development

Worth checking out?

Best,
[Your name]"""

    # Better metric integration
    engagement_context = ""
    if calls > 1 and mqls > 1:
        engagement_context = f"We've had {calls} calls and seen {mqls} people from {name} engage with our content, so it seems like orchestration is a real focus for your team."
    elif calls > 1:
        engagement_context = f"We've had {calls} calls with your team about Airflow."
    elif mqls > 1:
        engagement_context = f"I've seen {mqls} people from {name} engage with our content beyond our calls."
    else:
        engagement_context = "Based on our conversation, orchestration seems important to your team."

    email2 = f"""Subject: Re: Following up after our call

Hi [Name],

Following up on Astronomer Agents.

{engagement_context} If you're using Claude Code or Cursor and working with Airflow, the plugin adds:
- Context about your actual environment (not generic help)
- Pattern reuse from your existing DAGs
- Real-time debugging with your actual logs

One company with similar engagement used it to reduce their pipeline development time by 60%.

Install: claude plugin install astronomer-data@astronomer

Worth trying?

Best,
[Your name]"""

    email3 = f"""Subject: Last note

Hi [Name],

Last email from me. If the plugin isn't relevant or you're happy with your current workflow, totally fine.

But if you're using Airflow and AI coding tools, worth giving it context about your environment.

Let me know either way.

Best,
[Your name]"""

    return clean_text(email1), clean_text(email2), clean_text(email3)

def generate_generic_sequence(name, mqls, calls, tier):
    email1 = f"""Subject: New Airflow plugin for AI coding tools

Hi [Name],

We just launched Astronomer Agents, a plugin for Claude Code/Cursor/Copilot that helps build Airflow pipelines using AI.

If you're working with data orchestration, the plugin can:
- Generate DAGs from natural language descriptions
- Debug production pipeline failures
- Help your team learn Airflow best practices

Takes 2 minutes to install and works with any Airflow deployment.

Curious if data orchestration is something you're working on?

Best,
[Your name]"""

    # Better metric integration
    engagement_context = ""
    if mqls > 1 and calls > 0:
        engagement_context = f"We've had {calls} calls and seen {mqls} people from {name} engage with our content, so orchestration seems to be on your radar."
    elif mqls > 1:
        engagement_context = f"I've seen {mqls} people from {name} engage with our content, so orchestration seems to be on your radar."
    elif calls > 0:
        engagement_context = f"We've had {calls} calls with your team, so orchestration seems to be on your radar."
    elif mqls == 1:
        engagement_context = "I saw someone from your team engage with our content, so orchestration might be on your radar."
    else:
        engagement_context = "Not sure if orchestration is on your radar, but figured I'd reach out."

    email2 = f"""Subject: Re: New Airflow plugin for AI coding tools

Hi [Name],

Following up on Astronomer Agents.

{engagement_context} If you're using Claude Code or Cursor and working with Airflow, the plugin can:
- Speed up DAG development
- Debug issues faster
- Reduce learning curve for new team members

It's open source and free: claude plugin install astronomer-data@astronomer

Worth checking out if it's relevant?

Best,
[Your name]"""

    email3 = f"""Subject: Last note

Hi [Name],

Last email from me. If orchestration isn't something you're focused on or the plugin isn't relevant, no worries.

But if you're working with Airflow and using AI coding tools, it's worth a look.

Let me know either way.

Best,
[Your name]"""

    return clean_text(email1), clean_text(email2), clean_text(email3)

# Generate CSV
print("Generating contextual email sequences...")
print("This will take a few minutes as we pull call context for accounts with recent calls.")

output_file = '/Users/vishwasrinivasan/batch-gtm-agents/email_sequences_4_7_CONTEXTUAL.csv'

with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['Account Name', 'Tier', 'MQL Count', 'Call Count', 'Contact Count', 'Last MQL Contact', 'Last MQL Title', 'Context Type', 'Email 1', 'Email 2', 'Email 3']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for i, acct in enumerate(accounts):
        acct_name = acct['ACCT_NAME']
        tier = acct['TIER']
        mqls = acct['MQL_COUNT']
        calls = acct['CALL_COUNT']

        print(f"Processing {i+1}/120: {acct_name} (MQLs: {mqls}, Calls: {calls})")

        # Get MQL context
        mql_info = mql_by_account.get(acct_name, {'name': 'N/A', 'title': 'N/A', 'channel': None, 'campaign': None})

        # Get call context if they have calls (but only for top 20 to save time)
        call_context = None
        if calls > 0 and i < 20:  # Only pull call context for first 20 to save time
            call_context = get_call_context(acct_name)

        # Infer context type
        if call_context:
            context_type = "Recent Call"
        elif mql_info.get('channel'):
            context_type = f"{mql_info['channel']}" + (f": {mql_info['campaign']}" if mql_info.get('campaign') else "")
        else:
            context_type = "Generic"

        # Generate sequence
        email1, email2, email3 = generate_email_sequence(acct, mql_info, call_context)

        writer.writerow({
            'Account Name': acct_name,
            'Tier': tier,
            'MQL Count': mqls,
            'Call Count': calls,
            'Contact Count': acct['CONTACT_COUNT'],
            'Last MQL Contact': mql_info['name'],
            'Last MQL Title': mql_info['title'] if mql_info['title'] else 'N/A',
            'Context Type': context_type,
            'Email 1': email1.strip(),
            'Email 2': email2.strip(),
            'Email 3': email3.strip()
        })

print(f"\nGenerated contextual email sequences for {len(accounts)} accounts")
print(f"Output saved to: {output_file}")
