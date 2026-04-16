#!/usr/bin/env python3
"""
Generate discovery call plan from Snowflake account research data.
Pulls from V2_GTM_BATCH_OUTPUT and creates tailored markdown brief.
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

def detect_orchestration_tool(tech_stack):
    """Detect current orchestration tool from tech stack."""
    if not tech_stack:
        return "Unknown"

    # Look for orchestration tools in tech stack
    orch_tools = []
    for tech in tech_stack:
        tech_name = tech.get('technology', '').lower()
        if any(tool in tech_name for tool in ['airflow', 'dagster', 'prefect', 'luigi', 'oozie', 'temporal']):
            orch_tools.append(tech.get('technology'))

    return ", ".join(orch_tools) if orch_tools else "Unknown"

def generate_business_questions(data):
    """Generate tailored business questions based on account data."""
    questions = []

    # Base questions
    questions.append("What are your current data orchestration challenges?")

    # Tool-specific questions
    current_tool = detect_orchestration_tool(data.get('tech_stack', []))
    if 'airflow' in current_tool.lower():
        questions.append("What version of Airflow are you running? How are you managing it?")
        questions.append("What's your current deployment and upgrade process like?")
    elif current_tool != "Unknown":
        questions.append(f"You're using {current_tool} - what's working well? What's been frustrating?")
    else:
        questions.append("What tools are you currently using for data orchestration?")

    # Signal-based questions
    if data.get('hiring_signals_count', 0) > 0:
        questions.append("I noticed you're hiring data engineers - what's driving that growth?")

    if data.get('orchestration_mentions', 0) > 20:
        questions.append("Orchestration seems core to your stack - what triggered this conversation?")

    # Standard questions
    questions.append("Who owns data infrastructure decisions on your team?")
    questions.append("What does success look like for your data team this quarter/year?")

    return questions[:6]  # Max 6 questions

def generate_technical_questions(data):
    """Generate tailored technical questions based on tech stack."""
    questions = []

    # Data platform
    tech_stack = data.get('tech_stack', [])
    platforms = [t['technology'] for t in tech_stack if any(p in t['technology'].lower() for p in ['snowflake', 'databricks', 'bigquery', 'redshift'])]
    if platforms:
        questions.append(f"Saw you're on {', '.join(platforms[:2])} - any other data platforms in use?")
    else:
        questions.append("What data platforms are you using? (warehouse, lakes, etc.)")

    # Pipeline complexity
    questions.append("Can you share scale: roughly how many pipelines, tasks, daily runs?")
    questions.append("How do you handle CI/CD for your data pipelines today?")

    # Observability
    questions.append("What's your current observability/monitoring setup for data pipelines?")

    # Use case specific
    signals = data.get('key_signals', [])
    if signals:
        top_signal = signals[0]
        signal_text = top_signal.get('signal', '')
        if 'real-time' in signal_text.lower():
            questions.append("What real-time/streaming use cases are you supporting?")
        elif 'ml' in signal_text.lower() or 'model' in signal_text.lower():
            questions.append("How are you orchestrating ML pipelines and model training?")
        elif 'quality' in signal_text.lower():
            questions.append("How do you handle data quality checks and validation today?")

    # Pain points
    questions.append("What are the biggest pain points with your current orchestration setup?")

    return questions[:6]  # Max 6 questions

def generate_talking_points(data):
    """Generate tailored talking points based on account data."""
    points = []
    grade = data.get('airflow_mission_critical_grade', 'C')
    current_tool = detect_orchestration_tool(data.get('tech_stack', []))

    # Grade-based positioning
    if grade in ['A', 'B']:
        points.append("**Enterprise reliability:** 99.9% uptime SLA, 24/7 support, compliance certifications (SOC2, HIPAA, etc.)")
        points.append("**Remove infrastructure burden:** Fully managed Airflow - no K8s management, auto-scaling, automated upgrades")

    # Tool-based positioning
    if 'airflow' in current_tool.lower():
        points.append("**Seamless upgrade path:** Migrate from OSS to Astro without rewriting DAGs")
        points.append("**Built by Airflow creators:** 8 of top 10 Airflow committers work at Astronomer")
        points.append("**Version management:** Easy testing of new Airflow versions before production rollout")
    elif current_tool != "Unknown":
        points.append("**Airflow ecosystem advantage:** Largest community (2000+ operators), battle-tested at scale")
        points.append("**Flexibility without lock-in:** Pure Python, extensible, portable across clouds")

    # Signal-based value props
    signals = data.get('key_signals', [])
    for signal in signals[:3]:
        signal_text = signal.get('signal', '').lower()
        if 'hiring' in signal_text or data.get('hiring_signals_count', 0) > 0:
            points.append("**Reduce operational overhead:** Free up data engineers to build pipelines, not manage infrastructure")
            break

    for signal in signals[:3]:
        signal_text = signal.get('signal', '').lower()
        if 'scale' in signal_text or 'growth' in signal_text:
            points.append("**Proven at scale:** Powers data infrastructure at companies like DoorDash, Coinbase, Grammarly")
            break

    if data.get('orchestration_mentions', 0) > 30:
        points.append("**Your orchestration maturity:** With 30+ orchestration mentions, you understand the value - Astro takes it to the next level")

    return points

def generate_success_criteria(data):
    """Generate success criteria checklist."""
    criteria = [
        "Current orchestration tool & pain points",
        "Decision-making process & timeline",
        "Technical requirements & constraints",
        "Budget/procurement process",
        "Key stakeholders & next steps"
    ]
    return criteria

def generate_next_steps(data):
    """Generate proposed next steps based on tier."""
    tier = data.get('tier', 'cold_prospect')

    if tier == 'customer':
        return [
            "Schedule technical deep-dive with their data engineering team",
            "Upsell/expansion opportunity assessment",
            "Executive business review planning"
        ]
    elif tier == 'engaged_prospect' or data.get('mql_count', 0) > 0:
        return [
            "POC/trial discussion with specific success criteria",
            "Architecture review session with their team",
            "Pricing conversation based on their scale"
        ]
    else:
        return [
            "Technical deep-dive with data engineers",
            "Share relevant case study (similar industry/use case)",
            "Live Astro demo focused on their specific pain points"
        ]

def generate_call_focus(data):
    """Generate 1-2 sentence call focus recommendation."""
    grade = data.get('airflow_mission_critical_grade', 'C')
    current_tool = detect_orchestration_tool(data.get('tech_stack', []))

    if 'airflow' in current_tool.lower():
        return "They're already on Airflow - focus on operational pain points (upgrades, scaling, support) and position Astro as the enterprise solution."
    elif grade in ['A', 'B']:
        return "Mission-critical data infrastructure - emphasize reliability, enterprise support, and removing operational burden from their team."
    elif data.get('orchestration_mentions', 0) > 20:
        return "High orchestration maturity - focus on scaling challenges and how Astro accelerates their data team's productivity."
    else:
        return "Discovery mode - understand their current setup, pain points, and assess Airflow fit for their use cases."

def generate_disco_plan(account_name, data):
    """Generate the full discovery plan markdown."""
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

    current_tool = detect_orchestration_tool(data.get('tech_stack', []))

    # Extract key technologies
    tech_stack = data.get('tech_stack', [])
    key_techs = [t['technology'] for t in tech_stack[:8]] if tech_stack else ['No tech stack data']

    # Format signals
    signals = data.get('key_signals', [])
    signals_text = ""
    for i, signal in enumerate(signals[:7], 1):
        score = signal.get('score', 0)
        signal_text = signal.get('signal', 'N/A')
        signals_text += f"{i}. **[Score: {score}]** {signal_text}\n"

    if not signals_text:
        signals_text = "No signals available\n"

    # Generate questions and talking points
    biz_questions = generate_business_questions(data)
    tech_questions = generate_technical_questions(data)
    talking_points = generate_talking_points(data)
    success_criteria = generate_success_criteria(data)
    next_steps = generate_next_steps(data)
    call_focus = generate_call_focus(data)

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
- **Current Orchestration:** {current_tool}
- **Orchestration Mentions:** {data.get('orchestration_mentions', 0)} references across web presence
- **Data Stack:** {', '.join(key_techs)}
- **Team Signals:** {data.get('hiring_signals_count', 0)} data engineering job postings

### Engagement History
- **Contacts:** {data.get('contact_count', 0)}
- **MQLs:** {data.get('mql_count', 0)} (latest: {latest_mql})
- **Opportunities:** {data.get('opp_count', 0)}
- **Gong Calls:** {data.get('call_count', 0)} (latest: {latest_call})
- **Email Threads:** {len(data.get('email_correspondence', []))}

### Key Signals (Priority Order)
{signals_text}

---

## Discovery Questions

### Business Questions
"""

    for i, q in enumerate(biz_questions, 1):
        md += f"{i}. {q}\n"

    md += "\n### Technical Questions\n"
    for i, q in enumerate(tech_questions, 1):
        md += f"{i}. {q}\n"

    md += "\n---\n\n## Talking Points & Value Props\n\n### Tailored to Their Situation\n\n"

    for point in talking_points:
        md += f"- {point}\n"

    md += "\n---\n\n## Success Criteria\n\n**By end of call, we should know:**\n\n"

    for criterion in success_criteria:
        md += f"- [ ] {criterion}\n"

    md += "\n---\n\n## Proposed Next Steps\n\n"

    for i, step in enumerate(next_steps, 1):
        md += f"{i}. {step}\n"

    md += """
---

## Notes Section

**Key Takeaways:**
-

**Action Items:**
-

**Follow-up:**
-

---

**Call Focus:** """ + call_focus

    return md

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_disco_plan.py <account_name>")
        sys.exit(1)

    account_name = " ".join(sys.argv[1:])

    print(f"Generating discovery plan for {account_name}...")

    # Get research data
    data = get_account_research(account_name)

    if not data:
        print(f"❌ No research data found for {account_name}")
        print(f"Run research first: /batch-account-research {account_name}")
        sys.exit(1)

    # Generate plan
    disco_plan = generate_disco_plan(account_name, data)

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
    current_tool = detect_orchestration_tool(data.get('tech_stack', []))
    grade = data.get('airflow_mission_critical_grade', 'Unknown')
    tier = data.get('tier', 'Unknown')

    top_signal = "N/A"
    if data.get('key_signals'):
        top_signal = data['key_signals'][0].get('signal', 'N/A')[:80]

    latest_activity = data.get('latest_call_date') or data.get('latest_mql_date')
    if latest_activity:
        latest_activity = latest_activity.strftime("%Y-%m-%d")
    else:
        latest_activity = "No recent activity"

    call_focus = generate_call_focus(data)

    print(f"""
## Discovery Plan Generated: {account_name}

**Quick Context:**
- Tier: {tier}
- Current tool: {current_tool}
- Airflow grade: {grade}
- Key signal: {top_signal}
- Last activity: {latest_activity}

**Call Focus:**
{call_focus}
""")

if __name__ == "__main__":
    main()
