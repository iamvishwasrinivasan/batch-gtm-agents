#!/usr/bin/env python3
"""
Generate discovery call plan from Snowflake account research data + Gong transcripts.
Pulls from V2_GTM_BATCH_OUTPUT and analyzes Gong transcripts for context.
"""

import snowflake.connector
from datetime import datetime
import json
import os
import sys

def get_snowflake_connection():
    """Create Snowflake connection using private key auth."""
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization

    # Read private key
    with open(os.path.expanduser('~/.ssh/rsa_key_unencrypted.p8'), 'rb') as key_file:
        private_key_bytes = key_file.read()

    private_key = serialization.load_pem_private_key(
        private_key_bytes,
        password=None,
        backend=default_backend()
    )

    private_key_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    return snowflake.connector.connect(
        account='GP21411.us-east-1',
        user='VISHWASRINIVASAN',
        private_key=private_key_bytes,
        role='GTMADMIN',
        warehouse='HUMANS',
        database='HQ'
    )

def get_account_research(account_name):
    """Query Snowflake for account research data."""
    conn = get_snowflake_connection()

    query = """
    SELECT
        COMPANY_NAME,
        SF_ACCT_ID,
        SF_ACCT_NAME,
        SF_IS_CUSTOMER,
        SF_CONTACT_COUNT,
        SF_MQL_COUNT,
        SF_OPP_COUNT,
        SF_CALL_COUNT,
        SF_LATEST_MQL_DATE,
        SF_LATEST_CALL_DATE,
        SEARCH_COMPANY_RESEARCH_COUNT,
        SEARCH_HIRING_COUNT,
        SEARCH_ENGINEERING_BLOG_COUNT,
        SEARCH_PRODUCT_ANNOUNCEMENTS_COUNT,
        SEARCH_CASE_STUDIES_COUNT,
        TECH_STACK,
        CLASSIFICATION,
        AIRFLOW_SIGNALS,
        HAS_AIRFLOW_SIGNAL,
        RESEARCH_TIMESTAMP,
        RAW_JSON
    FROM GTM.PUBLIC.V2_GTM_BATCH_OUTPUT
    WHERE LOWER(COMPANY_NAME) = LOWER(%s)
    ORDER BY RESEARCH_TIMESTAMP DESC
    LIMIT 1
    """

    cursor = conn.cursor()
    cursor.execute(query, (account_name,))
    result = cursor.fetchone()

    if not result:
        cursor.close()
        conn.close()
        return None

    columns = [desc[0].lower() for desc in cursor.description]
    data = dict(zip(columns, result))

    # Parse JSON fields
    for field in ['tech_stack', 'classification', 'airflow_signals', 'raw_json']:
        if data.get(field):
            try:
                data[field] = json.loads(data[field])
            except:
                data[field] = {} if field == 'classification' else []

    # Map to expected structure for compatibility
    data['account_name'] = data.get('company_name')
    data['acct_id'] = data.get('sf_acct_id')
    data['contact_count'] = data.get('sf_contact_count', 0)
    data['mql_count'] = data.get('sf_mql_count', 0)
    data['opp_count'] = data.get('sf_opp_count', 0)
    data['call_count'] = data.get('sf_call_count', 0)
    data['latest_mql_date'] = data.get('sf_latest_mql_date')
    data['latest_call_date'] = data.get('sf_latest_call_date')
    data['hiring_signals_count'] = data.get('search_hiring_count', 0)
    data['blog_post_count'] = data.get('search_engineering_blog_count', 0)
    data['product_announcement_count'] = data.get('search_product_announcements_count', 0)
    data['case_study_count'] = data.get('search_case_studies_count', 0)
    data['orchestration_mentions'] = data.get('search_company_research_count', 0)
    data['research_date'] = data.get('research_timestamp')
    data['tier'] = 'customer' if data.get('sf_is_customer') else ('engaged_prospect' if data.get('sf_mql_count', 0) > 0 else 'cold_prospect')

    # Extract key signals from airflow_signals or classification
    if data.get('airflow_signals'):
        data['key_signals'] = [{'signal': s, 'score': 0} for s in data['airflow_signals'][:7]]
    else:
        data['key_signals'] = []

    # Determine Airflow grade from has_airflow_signal and classification
    if data.get('has_airflow_signal'):
        classification = data.get('classification', {})
        if isinstance(classification, dict):
            # Extract grade from classification logic - default to B if they have Airflow
            data['airflow_mission_critical_grade'] = 'B'
        else:
            data['airflow_mission_critical_grade'] = 'B'
    else:
        data['airflow_mission_critical_grade'] = 'D'

    cursor.close()
    conn.close()

    return data

def get_gong_transcripts(acct_id, limit=5):
    """
    Fetch recent Gong call transcripts directly from MODEL_CRM_SENSITIVE table.
    Returns list of transcript dicts with full text.
    """
    if not acct_id:
        return []

    conn = get_snowflake_connection()
    cursor = conn.cursor()

    query = """
    SELECT
        CALL_ID,
        CALL_TITLE,
        SCHEDULED_TS,
        ATTENDEES,
        FULL_TRANSCRIPT
    FROM HQ.MODEL_CRM_SENSITIVE.GONG_CALL_TRANSCRIPTS
    WHERE ACCT_ID = %s
    ORDER BY SCHEDULED_TS DESC
    LIMIT %s
    """

    cursor.execute(query, (acct_id, limit))
    rows = cursor.fetchall()

    transcripts = []
    for row in rows:
        transcripts.append({
            'call_id': row[0],
            'call_title': row[1],
            'scheduled_ts': row[2],
            'attendees': row[3],
            'full_transcript': row[4]
        })

    cursor.close()
    conn.close()

    return transcripts

def analyze_transcripts(transcripts):
    """
    Analyze Gong transcripts to extract key context for disco plan.
    Returns dict with insights extracted from transcripts.
    """
    if not transcripts:
        return {
            'pain_points': [],
            'tech_stack_mentioned': [],
            'stakeholders': set(),
            'open_questions': [],
            'what_was_pitched': [],
            'customer_goals': []
        }

    insights = {
        'pain_points': [],
        'tech_stack_mentioned': [],
        'stakeholders': set(),
        'open_questions': [],
        'what_was_pitched': [],
        'customer_goals': []
    }

    # Simple keyword extraction (could enhance with Claude API later)
    pain_keywords = ['problem', 'issue', 'challenge', 'pain', 'struggle', 'difficult', 'frustrating', 'broken']
    tech_keywords = ['airflow', 'snowflake', 'databricks', 'bigquery', 'redshift', 'kubernetes', 'k8s', 'docker',
                     'dbt', 'spark', 'kafka', 'postgres', 'mysql', 'aws', 'azure', 'gcp']
    pitch_keywords = ['astro', 'astronomer', 'managed airflow', 'cloud', 'saas']

    for transcript in transcripts:
        text = transcript.get('full_transcript', '').lower()
        title = transcript.get('call_title', '')
        attendees = transcript.get('attendees', '')
        date = transcript.get('scheduled_ts')

        # Extract stakeholders from attendees
        if attendees:
            for attendee in attendees.split(','):
                name = attendee.strip().replace('(employee)', '').strip()
                if name and '(' not in name:  # Avoid empty or malformed names
                    insights['stakeholders'].add(name)

        if not text:
            continue

        # Look for pain points (sentences containing pain keywords)
        sentences = text.split('.')
        for sentence in sentences:
            if any(keyword in sentence for keyword in pain_keywords):
                clean_sentence = sentence.strip()[:200]  # Limit length
                if len(clean_sentence) > 20:  # Avoid too short
                    insights['pain_points'].append({
                        'context': clean_sentence,
                        'call': title,
                        'date': date.strftime('%Y-%m-%d') if date else 'Unknown'
                    })

        # Extract tech stack mentions
        for tech in tech_keywords:
            if tech in text:
                insights['tech_stack_mentioned'].append(tech)

        # What we pitched
        if any(keyword in text for keyword in pitch_keywords):
            insights['what_was_pitched'].append(f"{title} ({date.strftime('%Y-%m-%d') if date else 'Unknown'})")

    # Deduplicate tech stack
    insights['tech_stack_mentioned'] = list(set(insights['tech_stack_mentioned']))
    insights['stakeholders'] = list(insights['stakeholders'])

    # Limit pain points to top 5 most recent
    insights['pain_points'] = insights['pain_points'][:5]

    return insights

def generate_contextual_questions(data, insights):
    """
    Generate discovery questions informed by Gong transcript analysis.
    """
    biz_questions = []
    tech_questions = []

    # Reference recent calls
    if data.get('latest_call_date'):
        latest_date = data['latest_call_date']
        if isinstance(latest_date, datetime):
            latest_date_str = latest_date.strftime('%b %d')
        else:
            latest_date_str = 'your recent call'

        # Check for specific pain points mentioned
        if insights['pain_points']:
            pain = insights['pain_points'][0]  # Most recent
            biz_questions.append(f"Following up from the {pain['call']} call - has the situation with {pain['context'][:80]}... changed?")
        else:
            biz_questions.append(f"Since our {latest_date_str} call, what's been the biggest priority for your data team?")

    # Tech stack specific questions
    tech_mentioned = insights['tech_stack_mentioned']
    if 'airflow' in tech_mentioned:
        tech_questions.append("You mentioned running Airflow - what version and how is it deployed? (OSS, MWAA, Composer, etc.)")
        tech_questions.append("What's your current process for upgrading Airflow versions?")
    elif tech_mentioned:
        top_tech = ', '.join(tech_mentioned[:3])
        tech_questions.append(f"Saw you're using {top_tech} - how do you orchestrate pipelines across these systems?")

    # Reference stakeholders
    if insights['stakeholders']:
        stakeholder_names = ', '.join(insights['stakeholders'][:2])
        biz_questions.append(f"Is {stakeholder_names} still the key decision maker(s) for data infrastructure, or has the team structure changed?")

    # Fill in standard questions if needed
    if len(biz_questions) < 4:
        biz_questions.extend([
            "What are your current data orchestration challenges?",
            "Who owns data infrastructure decisions on your team?",
            "What does success look like for your data team this quarter/year?"
        ])

    if len(tech_questions) < 5:
        tech_questions.extend([
            "Can you share scale: roughly how many pipelines, tasks, daily runs?",
            "How do you handle CI/CD for your data pipelines today?",
            "What's your current observability/monitoring setup for data pipelines?",
            "What are the biggest pain points with your current orchestration setup?"
        ])

    return biz_questions[:6], tech_questions[:6]

def generate_call_focus(data, insights):
    """Generate call focus based on data + transcript insights."""
    if insights['pain_points']:
        top_pain = insights['pain_points'][0]['context'][:100]
        return f"They've mentioned challenges with: '{top_pain}' - dig into this and position Astro as the solution to their specific pain."

    grade = data.get('airflow_mission_critical_grade', 'C')
    if 'airflow' in insights['tech_stack_mentioned']:
        return "They're already on Airflow - focus on operational pain points (upgrades, scaling, support) and position Astro as the enterprise solution."
    elif grade in ['A', 'B']:
        return "Mission-critical data infrastructure - emphasize reliability, enterprise support, and removing operational burden from their team."
    else:
        return "Discovery mode - understand their current setup, pain points, and assess Airflow fit for their use cases."

def generate_disco_plan_with_context(account_name, data, insights):
    """Generate the full discovery plan markdown with Gong context."""
    today = datetime.now().strftime("%Y-%m-%d")
    research_date = data.get('research_date')
    if research_date:
        research_date = research_date.strftime("%Y-%m-%d")
    else:
        research_date = "Unknown"

    # Check if research is stale
    research_warning = ""
    if data.get('research_date'):
        days_old = (datetime.now().date() - data['research_date'].date()).days
        if days_old > 30:
            research_warning = f"\n> ⚠️  **Research is {days_old} days old** - consider refreshing with `/batch-account-research {account_name}`\n"

    tier = data.get('tier', 'Unknown')
    grade = data.get('airflow_mission_critical_grade', 'Unknown')
    grade_explanation = {
        'A': 'Real-time critical (downtime = customer outage)',
        'B': 'Mission-critical batch (core business depends on pipelines)',
        'C': 'Operational tool (used but not critical)',
        'D': 'No evidence of Airflow usage'
    }

    # Extract key technologies
    tech_stack = data.get('tech_stack', [])
    if isinstance(tech_stack, dict):
        tech_stack = []
    # Combine with tech mentioned in calls
    all_tech = set(tech_stack + insights['tech_stack_mentioned'])
    key_techs = list(all_tech)[:8] if all_tech else ['No tech stack data']

    # Format signals
    signals = data.get('key_signals', [])
    signals_text = ""
    for i, signal in enumerate(signals[:7], 1):
        score = signal.get('score', 0)
        signal_text = signal.get('signal', 'N/A')
        signals_text += f"{i}. **[Score: {score}]** {signal_text}\n"

    if not signals_text:
        signals_text = "No signals available\n"

    # Generate contextual questions
    biz_questions, tech_questions = generate_contextual_questions(data, insights)

    # Call focus
    call_focus = generate_call_focus(data, insights)

    # Format dates
    latest_mql = data.get('latest_mql_date')
    if latest_mql:
        latest_mql = latest_mql.strftime("%Y-%m-%d")
    else:
        latest_mql = "N/A"

    latest_call = data.get('latest_call_date')
    if latest_call:
        latest_call = latest_call.strftime("%Y-%m-%d")
    else:
        latest_call = "N/A"

    # Build markdown
    md = f"""# Discovery Call Plan: {account_name}

**Date:** {today}
**Research Date:** {research_date}
**Tier:** {tier}
**Airflow Grade:** {grade} - {grade_explanation.get(grade, 'Unknown')}
{research_warning}
---

## Pre-Call Research Summary

### Company Overview
- **Tech Stack:** {', '.join(key_techs)}
- **Team Signals:** {data.get('hiring_signals_count', 0)} data engineering job postings

### Engagement History
- **Contacts:** {data.get('contact_count', 0)}
- **MQLs:** {data.get('mql_count', 0)} (latest: {latest_mql})
- **Opportunities:** {data.get('opp_count', 0)}
- **Gong Calls:** {data.get('call_count', 0)} (latest: {latest_call})

### Key Stakeholders (from recent calls)
"""

    if insights['stakeholders']:
        for stakeholder in insights['stakeholders'][:5]:
            md += f"- {stakeholder}\n"
    else:
        md += "- No stakeholder data available\n"

    md += "\n### Recent Call Context\n"
    if insights['pain_points']:
        md += "\n**Pain Points Mentioned:**\n"
        for pain in insights['pain_points'][:3]:
            md += f"- **[{pain['call']} - {pain['date']}]** {pain['context']}\n"
    else:
        md += "- No transcript analysis available\n"

    if insights['what_was_pitched']:
        md += "\n**What We've Already Pitched:**\n"
        for pitch in insights['what_was_pitched'][:3]:
            md += f"- {pitch}\n"

    md += f"\n### Key Signals (Priority Order)\n{signals_text}"

    md += "\n---\n\n## Discovery Questions\n\n### Business Questions\n"

    for i, q in enumerate(biz_questions, 1):
        md += f"{i}. {q}\n"

    md += "\n### Technical Questions\n"
    for i, q in enumerate(tech_questions, 1):
        md += f"{i}. {q}\n"

    md += "\n---\n\n## Success Criteria\n\n**By end of call, we should know:**\n\n"
    md += f"- [ ] Current orchestration tool & pain points\n"
    md += f"- [ ] Decision-making process & timeline\n"
    md += f"- [ ] Technical requirements & constraints\n"
    md += f"- [ ] Budget/procurement process\n"
    md += f"- [ ] Key stakeholders & next steps\n"

    md += "\n---\n\n## Notes Section\n\n**Key Takeaways:**\n-\n\n**Action Items:**\n-\n\n**Follow-up:**\n-\n\n---\n\n**Call Focus:** "
    md += call_focus

    return md

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_disco_plan_v2.py <account_name>")
        sys.exit(1)

    account_name = " ".join(sys.argv[1:])

    print(f"Generating contextual discovery plan for {account_name}...")

    # Get research data
    data = get_account_research(account_name)

    if not data:
        print(f"❌ No research data found for {account_name}")
        print(f"Run research first: python3 batch_account_research.py --accounts \"{account_name}\"")
        sys.exit(1)

    # Get Gong transcripts
    print(f"Fetching Gong transcripts...")
    transcripts = get_gong_transcripts(data.get('acct_id'), limit=5)
    print(f"Found {len(transcripts)} recent Gong calls")

    # Analyze transcripts
    print(f"Analyzing transcripts...")
    insights = analyze_transcripts(transcripts)
    print(f"  - {len(insights['pain_points'])} pain points identified")
    print(f"  - {len(insights['stakeholders'])} stakeholders extracted")
    print(f"  - {len(insights['tech_stack_mentioned'])} technologies mentioned")

    # Generate plan
    disco_plan = generate_disco_plan_with_context(account_name, data, insights)

    # Save to Account Context folder
    account_folder = f"/Users/vishwasrinivasan/Account Context/{account_name}"
    os.makedirs(account_folder, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"disco_plan_{today}.md"
    filepath = os.path.join(account_folder, filename)

    with open(filepath, 'w') as f:
        f.write(disco_plan)

    print(f"\n✅ Discovery plan saved to: {filepath}")

    # Print summary
    grade = data.get('airflow_mission_critical_grade', 'Unknown')
    tier = data.get('tier', 'Unknown')

    print(f"""
## Discovery Plan Generated: {account_name}

**Quick Context:**
- Tier: {tier}
- Airflow grade: {grade}
- Gong calls analyzed: {len(transcripts)}
- Key stakeholders: {', '.join(insights['stakeholders'][:3]) if insights['stakeholders'] else 'None identified'}
- Last call: {data.get('latest_call_date').strftime('%Y-%m-%d') if data.get('latest_call_date') else 'N/A'}

**Call Focus:**
{generate_call_focus(data, insights)}
""")

if __name__ == "__main__":
    main()
