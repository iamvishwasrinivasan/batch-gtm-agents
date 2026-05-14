#!/usr/bin/env python3
"""
Apollo Sequence Automation - End-to-End Flow

Takes a company name, finds contacts, generates personalized email copy,
creates sequence, and enrolls contacts - all without touching Apollo UI.

Flow:
1. Fetch account research from Snowflake
2. Search Apollo for contacts at company
3. Generate email copy based on research signals
4. Show preview and get approval
5. Create Apollo sequence with {{Email_Step_X}} variables
6. Write copy to each contact's custom fields
7. Enroll contacts in sequence

Usage:
    python3 apollo_sequence_automation.py "Smith Gardens"
    python3 apollo_sequence_automation.py "Smith Gardens" --contacts "Kyle Cornish,Kimberly Joslin"
    python3 apollo_sequence_automation.py "Smith Gardens" --auto-approve  # Skip preview
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

import requests
import snowflake.connector
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

# --- Config ---
API_KEY = os.environ.get('APOLLO_API_KEY')
BASE_URL = 'https://api.apollo.io/api/v1'
SNOWFLAKE_CONFIG = Path.home() / ".snowflake/service_config.yaml"
EMAIL_ACCOUNT_ID = "677eb30031d14101b078515e"  # vishwa.srinivasan@astronomer.io

# Custom field IDs
FIELD_IDS = {
    "subject_1": "69d6baa08ee9ea00153bb3c8",
    "step_1": "69d6b947814f5d0015ad8d0d",
    "step_2": "69d6b9550c13b10011beee6e",
    "step_3": "69d6b963fd54f60019020cdc",
    "step_4": "69d7d0b54025ad000d993367"
}


# --- Apollo API ---

def api_call(method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
    """Make Apollo API call"""
    url = f'{BASE_URL}{endpoint}'
    headers = {'x-api-key': API_KEY, 'Content-Type': 'application/json'}

    if method == 'GET':
        response = requests.get(url, headers=headers)
    elif method == 'POST':
        response = requests.post(url, headers=headers, json=data)
    elif method == 'PATCH':
        response = requests.patch(url, headers=headers, json=data)

    response.raise_for_status()
    return response.json()


def find_contacts(company_name: str) -> List[Dict[str, Any]]:
    """Search Apollo for contacts at company"""
    print(f"🔎 Searching Apollo for contacts at {company_name}...")

    response = api_call('POST', '/contacts/search', {
        "q_organization_name": company_name,
        "per_page": 50,
        "page": 1
    })

    contacts = []
    for c in response.get('contacts', []):
        contacts.append({
            'id': c['id'],
            'name': c['name'],
            'title': c.get('title', 'Unknown'),
            'email': c.get('email', 'No email'),
            'is_mql': 'MQL' in c.get('contact_stage_ids', [])
        })

    return contacts


def create_sequence(company_name: str, num_steps: int = 3) -> str:
    """Create Apollo sequence with email step variables"""
    print(f"\n✓ Creating sequence '{company_name} - Outreach'...")

    # Create sequence
    sequence_result = api_call('POST', '/emailer_campaigns', {
        "name": f"{company_name} - Outreach",
        "permissions": "private",
        "active": False
    })
    sequence_id = sequence_result['emailer_campaign']['id']

    # Create steps
    steps_config = [
        {"position": 1, "wait_time": 0, "note": "Initial outreach"},
        {"position": 2, "wait_time": 2, "note": "Follow-up"},
        {"position": 3, "wait_time": 3, "note": "Second follow-up"},
        {"position": 4, "wait_time": 4, "note": "Final touch"}
    ]

    for i, config in enumerate(steps_config[:num_steps], 1):
        subject = "{{Email_Subject_1}}" if i == 1 else "Re: {{Email_Subject_1}}"
        body = f"{{{{Email_Step_{i}}}}}"

        payload = {
            "emailer_campaign_id": sequence_id,
            "type": "auto_email",
            "position": config['position'],
            "wait_time": config['wait_time'],
            "wait_mode": "day",
            "note": config['note'],
            "emailer_template": {
                "subject": subject,
                "body_html": f"<p>{body}</p>",
                "send_email_from_email_account_id": EMAIL_ACCOUNT_ID
            }
        }

        result = api_call('POST', '/emailer_steps', payload)
        template_id = result.get('emailer_template', {}).get('id')

        # PATCH template to ensure body saves
        if template_id:
            api_call('PATCH', f'/emailer_templates/{template_id}', {
                "subject": subject,
                "body_html": f"<p>{body}</p>"
            })

    return sequence_id


def write_contact_copy(contact_id: str, copy: Dict[str, str]) -> None:
    """Write email copy to contact's custom fields"""
    field_mapping = {
        FIELD_IDS['subject_1']: copy['subject'],
        FIELD_IDS['step_1']: copy['step_1'],
        FIELD_IDS['step_2']: copy['step_2'],
        FIELD_IDS['step_3']: copy['step_3']
    }

    if 'step_4' in copy:
        field_mapping[FIELD_IDS['step_4']] = copy['step_4']

    api_call('PATCH', f'/contacts/{contact_id}', {
        "typed_custom_fields": field_mapping
    })


def enroll_contact(contact_id: str, sequence_id: str) -> None:
    """Enroll contact in sequence"""
    api_call('POST', '/emailer_touches', {
        "contact_ids": [contact_id],
        "emailer_campaign_id": sequence_id,
        "send_email_from_email_account_id": EMAIL_ACCOUNT_ID
    })


# --- Snowflake ---

def get_snowflake_connection():
    """Connect to Snowflake using key-pair auth"""
    key_path = Path.home() / ".ssh/rsa_key_unencrypted.p8"

    with open(key_path, "rb") as key_file:
        p_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )

    pkb = p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    return snowflake.connector.connect(
        user='VISHWASRINIVASAN',
        account='GP21411.us-east-1',
        private_key=pkb,
        role='GTMADMIN',
        warehouse='HUMANS',
        database='GTM',
        schema='PUBLIC'
    )


def fetch_research(company_name: str) -> Optional[Dict[str, Any]]:
    """Fetch account research from Snowflake"""
    print(f"🔍 Fetching research for {company_name}...")

    conn = get_snowflake_connection()
    cursor = conn.cursor()

    query = """
    SELECT
        acct_name,
        acct_id,
        tier,
        priority_score,
        orchestration_mentions,
        hiring_signals_count,
        key_signals,
        comprehensive_report,
        research_date,
        structured_signals,
        latest_mql_date
    FROM GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT
    WHERE LOWER(acct_name) = LOWER(%s)
    ORDER BY research_date DESC
    LIMIT 1
    """

    cursor.execute(query, (company_name,))
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if not row:
        return None

    return {
        'account_name': row[0],
        'acct_id': row[1],
        'tier': row[2],
        'priority_score': row[3],
        'orchestration_mentions': row[4],
        'hiring_signals_count': row[5],
        'key_signals': json.loads(row[6]) if row[6] else [],
        'comprehensive_report': row[7],
        'generated_at': row[8].isoformat() if row[8] else None,
        'structured_signals': row[9],
        'latest_mql_date': row[10]
    }


# --- Copy Generation (Using structured signals) ---

def get_gong_context(company_name: str) -> Optional[Dict]:
    """Fetch Gong call context if exists"""
    conn = get_snowflake_connection()
    cursor = conn.cursor()

    query = """
    SELECT call_date, enrichment_json
    FROM GTM.PUBLIC.GONG_CALL_ENRICHMENTS
    WHERE LOWER(acct_name) = LOWER(%s)
    ORDER BY call_date DESC
    LIMIT 1
    """

    cursor.execute(query, (company_name,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row:
        return {
            'call_date': row[0],
            'enrichment': json.loads(row[1]) if row[1] else {}
        }
    return None


def get_recent_webinars() -> List[Dict]:
    """Fetch recent webinars"""
    conn = get_snowflake_connection()
    cursor = conn.cursor()

    query = """
    SELECT webinar_title, webinar_date, webinar_tags
    FROM HQ.IN_NOTION.WEBINARS
    WHERE webinar_date >= DATEADD('month', -2, CURRENT_DATE)
    ORDER BY webinar_date DESC
    LIMIT 5
    """

    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    webinars = []
    for row in rows:
        webinars.append({
            'title': row[0],
            'date': row[1],
            'tags': json.loads(row[2]) if row[2] else []
        })
    return webinars


def analyze_structured_signals(structured_signals_json: str, company_name: str) -> Dict:
    """
    Analyze structured signals for quality and confidence

    Returns insights about orchestration eval, hiring, growth
    """
    try:
        signals = json.loads(structured_signals_json) if structured_signals_json else []
    except:
        signals = []

    # Filter to high-confidence signals (score >= 7, verified)
    high_conf = [s for s in signals if s.get('score', 0) >= 7 and s.get('verified', False)]

    # Categorize by source and category
    orchestration_signals = [s for s in high_conf if s.get('source') == 'orchestration']
    hiring_signals = [s for s in high_conf if s.get('source') == 'hiring' or s.get('category') == 'hiring_evidence']

    # Look for specific evidence categories
    has_orch_evidence = any(s.get('category') == 'orchestration_evidence' for s in orchestration_signals)
    has_engineering_culture = any(s.get('category') == 'engineering_culture' for s in orchestration_signals)

    # Extract growth signals from ALL signals (growth is often low-score but factual)
    growth_signal = None
    for s in signals:  # Check all signals, not just high_conf
        text = s.get('signal', '').lower()
        if '3 to 40 people' in text or '3 to 40 people in' in text:
            growth_signal = "3 to 40 people in 10 months"
            break
        elif '100+' in text and 'employees' in text:
            growth_signal = "100+ employees"
            break
        elif '8m+' in text and 'downloads' in text:
            growth_signal = "100+ employees, 8M+ downloads"
            break

    # Check for recent signals (last 90 days)
    from datetime import datetime, timedelta
    ninety_days_ago = datetime.now() - timedelta(days=90)
    recent_signals = []
    for s in high_conf:
        date_str = s.get('date')
        if date_str:
            try:
                signal_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                if signal_date > ninety_days_ago:
                    recent_signals.append(s)
            except:
                pass

    # Assess orchestration confidence
    orch_confidence = 'none'
    if len(orchestration_signals) >= 3 and has_orch_evidence:
        orch_confidence = 'high'
    elif len(orchestration_signals) >= 2 and len(recent_signals) > 0:
        orch_confidence = 'medium'
    elif len(orchestration_signals) >= 1:
        orch_confidence = 'low'

    return {
        'high_confidence_count': len(high_conf),
        'orchestration_signals': orchestration_signals,
        'hiring_signals': hiring_signals,
        'orch_confidence': orch_confidence,
        'has_orchestration_evidence': has_orch_evidence,
        'has_engineering_culture': has_engineering_culture,
        'growth_signal': growth_signal,
        'recent_signals': recent_signals,
        'has_hiring': len(hiring_signals) > 0
    }


def match_webinar_to_analysis(webinars: List[Dict], signal_analysis: Dict) -> Optional[Dict]:
    """Match relevant webinar based on signal analysis"""
    for webinar in webinars:
        tags = [tag.lower() for tag in webinar['tags']]

        # Match data quality to hiring/growth
        if 'data quality' in tags and (signal_analysis['has_hiring'] or signal_analysis['growth_signal']):
            return webinar

        # Match DAG authoring to orchestration evidence
        if 'dag authoring' in tags and signal_analysis['orch_confidence'] in ['high', 'medium']:
            return webinar

        # Match meta/state of airflow to general interest
        if 'meta' in tags and signal_analysis['orch_confidence'] != 'none':
            return webinar

    return None


def generate_email_copy(research: Dict[str, Any]) -> Dict[str, str]:
    """Generate email copy using structured signal analysis"""
    company = research['account_name'].title()  # Title-case for proper capitalization
    mql_date = research.get('latest_mql_date')
    has_mql = mql_date is not None

    # Parse and analyze structured signals
    structured_signals = research.get('structured_signals', '[]')
    analysis = analyze_structured_signals(structured_signals, company)

    # Get additional context
    gong = get_gong_context(company)
    webinars = get_recent_webinars()

    # Determine primary signal (priority order)
    # 1. Gong call (highest confidence)
    if gong:
        call_month = gong['call_date'].strftime('%B')
        pain_points = gong['enrichment'].get('pain_points', [])

        subject = "Quick reconnect"
        para1 = f"Last time we spoke in {call_month}, you were {pain_points[0] if pain_points else 'evaluating orchestration options'}. Saw you came back through this week."

    # 2. MQL + Growth signal (high confidence combo)
    elif has_mql and analysis['growth_signal']:
        subject = "Quick reconnect"
        para1 = f"You checked out Astronomer recently. Saw {company} went {analysis['growth_signal']}. That's the stage where pipeline reliability becomes a priority for most teams."

    # 3. High-confidence orchestration evaluation
    elif analysis['orch_confidence'] == 'high' and analysis['has_orchestration_evidence']:
        if has_mql:
            subject = "Orchestration eval"
            para1 = f"You checked out Astronomer recently. Saw {company} is evaluating orchestration options. Most teams tell us the deciding factor is whether they'll need a dedicated platform team to run it."
        else:
            subject = "Orchestration eval"
            para1 = f"Saw {company} is evaluating orchestration options. Most teams tell us the deciding factor is whether they'll need a dedicated platform team to run it."

    # 4. Medium-confidence orchestration (softer language)
    elif analysis['orch_confidence'] == 'medium':
        if has_mql:
            subject = "Data infrastructure"
            para1 = f"You checked out Astronomer recently. Saw {company} might be looking at data orchestration. Most teams at your stage are thinking about whether to build or buy."
        else:
            subject = "Data infrastructure"
            para1 = f"Noticed {company} might be looking at data orchestration. Most teams are thinking about whether to build or buy when it comes to pipeline infrastructure."

    # 5. Hiring signals (reliable alternative)
    elif analysis['has_hiring']:
        if has_mql:
            subject = "Scaling data team"
            para1 = f"You checked out Astronomer recently. Saw {company} is hiring data engineers. Most teams at this stage need reliable orchestration without dedicated platform engineers."
        else:
            subject = "Scaling data team"
            para1 = f"Saw {company} is hiring data engineers. That usually means infrastructure is getting real attention. Most teams at this stage need orchestration that doesn't require a dedicated infra team."

    # 6. Growth signal only
    elif analysis['growth_signal']:
        if has_mql:
            subject = "Quick reconnect"
            para1 = f"You checked out Astronomer recently. Saw {company} went {analysis['growth_signal']}. That's when most companies start thinking seriously about data infrastructure."
        else:
            subject = "Data infrastructure"
            para1 = f"Saw {company} went {analysis['growth_signal']}. That's when most companies start needing reliable orchestration without a dedicated platform team."

    # 7. Low confidence orchestration (very soft)
    elif analysis['orch_confidence'] == 'low':
        subject = "Data orchestration"
        para1 = f"I work with data teams at companies like {company}. Most teams need reliable orchestration that doesn't require a dedicated infra team."

    # 8. Cold outreach (no good signals)
    else:
        subject = "Data orchestration"
        para1 = f"I work with data teams and figured I'd reach out. Happy to show you what Astro does if orchestration is on your radar."

    # Build paragraph 2 with webinar context
    webinar = match_webinar_to_analysis(webinars, analysis)
    if webinar and analysis['growth_signal']:
        month = webinar['date'].strftime('%B')
        # Lowercase first char for natural sentence flow
        title = webinar['title'][0].lower() + webinar['title'][1:] if webinar['title'] else webinar['title']
        para2 = f"The {title} session in {month} covered this. Teams scaling that fast without dedicated platform engineers tend to spend more time fixing broken pipelines than building new ones."
    elif webinar and analysis['orch_confidence'] in ['high', 'medium']:
        month = webinar['date'].strftime('%B')
        # Lowercase first char for natural sentence flow
        title = webinar['title'][0].lower() + webinar['title'][1:] if webinar['title'] else webinar['title']
        para2 = f"The {title} session in {month} touched on this: most teams evaluating orchestration end up focused on whether they'll need dedicated engineers to maintain it. That tends to tip the decision one way or another."
    else:
        # No webinar, use generic value prop
        if analysis['has_hiring']:
            para2 = "When teams are scaling fast, the infrastructure work becomes a full-time job. Astro handles the Kubernetes, monitoring, and scaling so your team focuses on building pipelines instead."
        else:
            para2 = "Most teams we work with need reliable orchestration that doesn't require a dedicated infra team. That's what Astro does. Managed Airflow with zero ops burden."

    # CTA
    para3 = "Worth 15 minutes to see if there's a fit?"

    # Compose Step 1
    step_1 = f"""Hi {{{{first_name}}}},

{para1}

{para2}

{para3}

Vishwa"""

    # Simple follow-ups for steps 2 and 3
    step_2 = """Hi {{first_name}},

Quick follow-up on Astronomer.

Let me know if you want to see a quick walkthrough of how it compares to what you're running today.

Vishwa"""

    step_3 = """Hi {{first_name}},

Last note.

If timing's better down the road, happy to reconnect. Otherwise, good luck with your data stack.

Vishwa"""

    return {
        'subject': subject,
        'step_1': step_1,
        'step_2': step_2,
        'step_3': step_3
    }


# --- Interactive UI ---

def display_contacts(contacts: List[Dict]) -> None:
    """Display contact list"""
    print(f"\n✓ Found {len(contacts)} contacts:\n")

    for i, c in enumerate(contacts, 1):
        mql_badge = "✓" if c['is_mql'] else " "
        print(f"  {i}. {mql_badge} {c['name']} - {c['title']}")
    print()


def select_contacts(contacts: List[Dict], filter_names: Optional[List[str]] = None) -> List[Dict]:
    """Interactive contact selection"""
    if filter_names:
        # Filter by names provided
        selected = []
        for name in filter_names:
            for c in contacts:
                if name.lower() in c['name'].lower():
                    selected.append(c)
                    break
        return selected

    display_contacts(contacts)

    while True:
        choice = input("Target which contacts? (1,2 / all / cancel): ").strip().lower()

        if choice == 'cancel':
            return []
        elif choice == 'all':
            return contacts
        else:
            try:
                indices = [int(x.strip()) - 1 for x in choice.split(',')]
                return [contacts[i] for i in indices if 0 <= i < len(contacts)]
            except (ValueError, IndexError):
                print("Invalid selection. Try again.")


def display_copy_preview(copy: Dict[str, str], research: Dict[str, Any]) -> None:
    """Display email copy preview"""
    print("\n" + "━"*70)
    print("📧 GENERATED EMAIL COPY")
    print("━"*70 + "\n")

    print(f"SUBJECT: {copy['subject']}\n")

    for i in range(1, 5):
        key = f'step_{i}'
        if key in copy:
            print(f"{'─'*70}")
            print(f"STEP {i}:")
            print(f"{'─'*70}")
            print(copy[key])
            print()

    # Analyze signals for display
    structured_signals = research.get('structured_signals', '[]')
    analysis = analyze_structured_signals(structured_signals, research['account_name'])

    print("━"*70)
    print(f"Based on: {len(analysis['orchestration_signals'])} high-conf orchestration signals (confidence: {analysis['orch_confidence']}), "
          f"{len(analysis['hiring_signals'])} hiring signals, "
          f"tier: {research.get('tier', 'unknown')}")
    if analysis['growth_signal']:
        print(f"Growth signal: {analysis['growth_signal']}")
    print("━"*70 + "\n")


def approve_copy(auto_approve: bool = False) -> bool:
    """Get user approval for copy"""
    if auto_approve:
        return True

    while True:
        choice = input("Push and enroll? (y/n/edit): ").strip().lower()

        if choice == 'y':
            return True
        elif choice == 'n':
            return False
        elif choice == 'edit':
            print("\nPaste edited copy (JSON format):")
            print('{"subject": "...", "step_1": "...", "step_2": "...", "step_3": "..."}')
            # For now, just continue - can add edit functionality later
            return True
        else:
            print("Invalid choice. Use y/n/edit")


# --- Main Flow ---

def main():
    parser = argparse.ArgumentParser(description='Apollo Sequence Automation')
    parser.add_argument('company', help='Company name')
    parser.add_argument('--contacts', help='Comma-separated contact names to target')
    parser.add_argument('--auto-approve', action='store_true', help='Skip copy approval')
    parser.add_argument('--steps', type=int, default=3, choices=[3, 4], help='Number of steps (default: 3)')

    args = parser.parse_args()

    # 1. Fetch research
    research = fetch_research(args.company)
    if not research:
        print(f"❌ No research found for {args.company}")
        print(f"Run: /batch-account-research \"{args.company}\"")
        sys.exit(1)

    print(f"✓ Found research (tier: {research['tier']}, "
          f"score: {research['priority_score']}/10, "
          f"{research['orchestration_mentions']} signals)")

    # 2. Find contacts
    contacts = find_contacts(args.company)
    if not contacts:
        print(f"❌ No contacts found in Apollo for {args.company}")
        sys.exit(1)

    # 3. Select contacts
    filter_names = args.contacts.split(',') if args.contacts else None
    selected = select_contacts(contacts, filter_names)

    if not selected:
        print("❌ No contacts selected. Exiting.")
        sys.exit(0)

    print(f"\n📝 Targeting {len(selected)} contact(s)")

    # 4. Generate copy
    print("\n📝 Generating email copy...")
    copy = generate_email_copy(research)

    # 5. Show preview and get approval
    display_copy_preview(copy, research)

    if not approve_copy(args.auto_approve):
        print("❌ Cancelled by user")
        sys.exit(0)

    # 6. Create sequence
    sequence_id = create_sequence(args.company, args.steps)
    sequence_url = f"https://app.apollo.io/sequences/{sequence_id}"

    # 7. Enroll contacts
    print(f"\n✓ Enrolling {len(selected)} contact(s)...\n")

    for contact in selected:
        try:
            print(f"  → {contact['name']}...")
            write_contact_copy(contact['id'], copy)
            print(f"    ✓ Copy written")
            enroll_contact(contact['id'], sequence_id)
            print(f"    ✓ Enrolled in sequence")
        except Exception as e:
            print(f"    ❌ Error: {e}")

    # 8. Done
    print("\n" + "="*70)
    print("🎯 COMPLETE")
    print("="*70)
    print(f"\n{len(selected)} contact(s) enrolled and ready to send")
    print(f"Sequence: {sequence_url}")
    print(f"\nEmails will send automatically based on sequence timing.")


if __name__ == "__main__":
    main()
