#!/usr/bin/env python3
"""
Test script for improved search prompts.
Tests the new 7-search strategy before merging into batch_account_research.py

Usage:
    python3 test_improved_searches.py "Company Name"
    python3 test_improved_searches.py "Company Name" --domain company.com
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from pathlib import Path
import time
import yaml

# Load API keys
EXA_API_KEY = os.environ.get('EXA_API_KEY')
BRAVE_API_KEY = os.environ.get('BRAVE_API_KEY')

# Snowflake imports
try:
    import snowflake.connector
    SNOWFLAKE_AVAILABLE = True
except ImportError:
    SNOWFLAKE_AVAILABLE = False
    print("⚠️  Warning: snowflake-connector-python not installed. Snowflake features disabled.")

def log(message: str):
    """Simple logger"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")


# =============================================================================
# SNOWFLAKE CONTEXT FETCHING
# =============================================================================

def get_snowflake_connection():
    """Get Snowflake connection using config file"""
    config_path = Path.home() / ".snowflake/service_config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Snowflake config not found: {config_path}")

    with open(config_path) as f:
        yaml_data = yaml.safe_load(f)

    # Handle nested config (snowflake: {...})
    config = yaml_data.get('snowflake', yaml_data)

    # Handle both 'private_key_path' and 'privateKeyPath' keys
    key_path = config.get('private_key_path') or config.get('privateKeyPath')
    if not key_path:
        raise KeyError("Neither 'private_key_path' nor 'privateKeyPath' found in config")

    private_key_path = Path(key_path).expanduser()

    # Load private key using cryptography library (same as batch_account_research.py)
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.backends import default_backend

    with open(private_key_path, 'rb') as key_file:
        key_data = key_file.read()

    private_key = serialization.load_pem_private_key(
        key_data,
        password=None,
        backend=default_backend()
    ).private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    return snowflake.connector.connect(
        account=config['account'],
        user=config['user'],
        private_key=private_key,
        warehouse=config['warehouse'],
        database=config['database'],
        schema=config.get('schema', 'PUBLIC'),
        role=config.get('role', 'ACCOUNTADMIN')
    )


def fetch_snowflake_context(company_name: str) -> Dict:
    """
    Fetch Snowflake context (contacts, MQLs, opps, Gong calls) for a company.
    Returns engagement data + full context
    """
    if not SNOWFLAKE_AVAILABLE:
        return {
            'status': 'unavailable',
            'error': 'snowflake-connector-python not installed'
        }

    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()

        # Find account by name
        cursor.execute("""
            SELECT ACCT_ID, ACCT_NAME, IS_CURRENT_CUST, PARENT_NAME
            FROM HQ.MODEL_CRM.SF_ACCOUNTS
            WHERE LOWER(ACCT_NAME) LIKE LOWER(%s)
            LIMIT 1
        """, (f"%{company_name}%",))

        account_row = cursor.fetchone()
        if not account_row:
            cursor.close()
            conn.close()
            return {
                'status': 'not_found',
                'message': f'No account found matching "{company_name}" in Salesforce'
            }

        acct_id, acct_name, is_customer, parent_name = account_row

        # Fetch contacts
        cursor.execute("""
            SELECT CONTACT_ID, TITLE, PRIMARY_DOMAIN, SOURCE, IS_EMPLOYEE
            FROM HQ.MODEL_CRM.SF_CONTACTS
            WHERE ACCT_ID = %s
            ORDER BY IS_EMPLOYEE DESC, TITLE
            LIMIT 100
        """, (acct_id,))
        contacts = [
            {
                'contact_id': row[0],
                'title': row[1],
                'domain': row[2],
                'source': row[3],
                'is_employee': row[4]
            }
            for row in cursor.fetchall()
        ]

        # Fetch MQLs
        cursor.execute("""
            SELECT CONTACT_ID, MQL_TS, REPORTING_CHANNEL, UTM_SOURCE, UTM_CAMPAIGN
            FROM HQ.MODEL_CRM.SF_MQLS
            WHERE ACCT_ID = %s
            ORDER BY MQL_TS DESC
            LIMIT 50
        """, (acct_id,))
        mqls = [
            {
                'contact_id': row[0],
                'mql_date': row[1].isoformat() if row[1] else None,
                'channel': row[2],
                'utm_source': row[3],
                'utm_campaign': row[4]
            }
            for row in cursor.fetchall()
        ]

        # Fetch opportunities
        cursor.execute("""
            SELECT OPP_ID, OPP_NAME, OPP_TYPE, CURRENT_STAGE_NAME, CLOSE_DATE, CREATED_DATE
            FROM HQ.MODEL_CRM.SF_OPPS
            WHERE ACCT_ID = %s
            ORDER BY CREATED_DATE DESC
            LIMIT 20
        """, (acct_id,))
        opps = [
            {
                'opp_id': row[0],
                'opp_name': row[1],
                'opp_type': row[2],
                'stage': row[3],
                'close_date': row[4].isoformat() if row[4] else None,
                'created_date': row[5].isoformat() if row[5] else None
            }
            for row in cursor.fetchall()
        ]

        # Fetch Gong calls
        cursor.execute("""
            SELECT CALL_ID, CALL_TITLE, SCHEDULED_TS, ATTENDEES,
                   LEFT(FULL_TRANSCRIPT, 2000) as transcript_preview
            FROM HQ.MODEL_CRM_SENSITIVE.GONG_CALL_TRANSCRIPTS
            WHERE ACCT_ID = %s
            ORDER BY SCHEDULED_TS DESC
            LIMIT 10
        """, (acct_id,))
        gong_calls = [
            {
                'call_id': row[0],
                'title': row[1],
                'date': row[2].isoformat() if row[2] else None,
                'attendees': row[3],
                'transcript_preview': row[4]
            }
            for row in cursor.fetchall()
        ]

        cursor.close()
        conn.close()

        return {
            'status': 'success',
            'acct_id': acct_id,
            'acct_name': acct_name,
            'is_customer': is_customer,
            'parent_name': parent_name,
            'contact_count': len(contacts),
            'mql_count': len(mqls),
            'opp_count': len(opps),
            'call_count': len(gong_calls),
            'contacts': contacts[:10],  # Top 10
            'mqls': mqls[:10],  # Top 10
            'opps': opps,
            'gong_calls': gong_calls,
            'latest_mql_date': mqls[0]['mql_date'] if mqls else None,
            'latest_call_date': gong_calls[0]['date'] if gong_calls else None
        }

    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }


# =============================================================================
# IMPROVED SEARCH FUNCTIONS
# =============================================================================

def search_1_company_research(company_name: str, domain: Optional[str] = None) -> Dict:
    """
    Search 1: Company overview
    UNCHANGED - this one works fine
    """
    log(f"[1/7] Searching: Company Research...")

    if not EXA_API_KEY:
        return {'status': 'error', 'error': 'EXA_API_KEY not set'}

    headers = {
        "x-api-key": EXA_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "query": f"{company_name} company about what we do",
        "numResults": 5,
        "type": "keyword",
        "contents": {"highlights": True}
    }

    try:
        response = requests.post(
            "https://api.exa.ai/search",
            headers=headers,
            json=payload,
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            return {
                'status': 'success',
                'results': data.get('results', []),
                'count': len(data.get('results', []))
            }
        else:
            return {'status': 'error', 'error': f'HTTP {response.status_code}'}

    except Exception as e:
        return {'status': 'error', 'error': str(e)}


def search_2_github_evidence(company_name: str, domain: Optional[str] = None) -> Dict:
    """
    Search 2: GitHub evidence (RENAMED from 'orchestration')
    NEW: Look for actual code repos, not generic articles
    """
    log(f"[2/7] Searching: GitHub Evidence...")

    if not EXA_API_KEY:
        return {'status': 'error', 'error': 'EXA_API_KEY not set'}

    # Try to derive GitHub slug from company name
    company_slug = company_name.lower().replace(' ', '-').replace('.', '')

    headers = {
        "x-api-key": EXA_API_KEY,
        "Content-Type": "application/json"
    }

    # Search for GitHub repos
    payload = {
        "query": f'site:github.com/{company_slug} OR site:github.com "{company_name}" (airflow OR dags OR workflows OR kubernetes OR terraform OR infrastructure)',
        "numResults": 5,
        "type": "keyword",
        "contents": {"highlights": True}
    }

    try:
        response = requests.post(
            "https://api.exa.ai/search",
            headers=headers,
            json=payload,
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            return {
                'status': 'success',
                'results': data.get('results', []),
                'count': len(data.get('results', []))
            }
        else:
            return {'status': 'error', 'error': f'HTTP {response.status_code}'}

    except Exception as e:
        return {'status': 'error', 'error': str(e)}


def search_3_hiring_expanded(company_name: str, domain: Optional[str] = None) -> Dict:
    """
    Search 3: Hiring + Tech Stack (EXPANDED)
    NOW: Primary source for tech stack detection from job requirements
    """
    log(f"[3/7] Searching: Hiring + Tech Stack...")

    if not EXA_API_KEY:
        return {'status': 'error', 'error': 'EXA_API_KEY not set'}

    headers = {
        "x-api-key": EXA_API_KEY,
        "Content-Type": "application/json"
    }

    # Build domain list for job boards
    job_sites = "site:greenhouse.io OR site:lever.co OR site:jobs.lever.co OR site:boards.greenhouse.io OR site:linkedin.com/jobs"
    if domain:
        job_sites += f" OR site:{domain}/careers"

    # Expanded to include more engineering roles
    payload = {
        "query": f'{company_name} ("data engineer" OR "platform engineer" OR "analytics engineer" OR "backend engineer" OR "infrastructure engineer" OR "SRE" OR "site reliability engineer") (requirements OR qualifications OR "experience with" OR "you will" OR responsibilities) {job_sites}',
        "numResults": 10,  # Increased to get more job postings
        "type": "keyword",
        "startPublishedDate": (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d'),
        "contents": {"highlights": True, "text": True}  # Get full text for tech stack extraction
    }

    try:
        response = requests.post(
            "https://api.exa.ai/search",
            headers=headers,
            json=payload,
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            return {
                'status': 'success',
                'results': data.get('results', []),
                'count': len(data.get('results', []))
            }
        else:
            return {'status': 'error', 'error': f'HTTP {response.status_code}'}

    except Exception as e:
        return {'status': 'error', 'error': str(e)}


def search_4_trigger_events(company_name: str, domain: Optional[str] = None) -> Dict:
    """
    Search 4: Trigger Events (FOCUSED from 'news')
    NOW: Only funding, M&A, exec hires - not generic news
    """
    log(f"[4/7] Searching: Trigger Events...")

    if not EXA_API_KEY:
        return {'status': 'error', 'error': 'EXA_API_KEY not set'}

    headers = {
        "x-api-key": EXA_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "query": f'{company_name} (funding OR "series A" OR "series B" OR "series C" OR acquired OR acquisition OR "new CEO" OR "new CTO" OR "new CDO" OR "Chief" OR hired OR appointed) (2025 OR 2026) (site:techcrunch.com OR site:crunchbase.com OR site:businesswire.com OR site:prnewswire.com OR site:linkedin.com)',
        "numResults": 5,
        "type": "keyword",
        "contents": {"highlights": True}
    }

    try:
        response = requests.post(
            "https://api.exa.ai/search",
            headers=headers,
            json=payload,
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            return {
                'status': 'success',
                'results': data.get('results', []),
                'count': len(data.get('results', []))
            }
        else:
            return {'status': 'error', 'error': f'HTTP {response.status_code}'}

    except Exception as e:
        return {'status': 'error', 'error': str(e)}


def search_5_engineering_blog(company_name: str, domain: Optional[str] = None) -> Dict:
    """
    Search 5: Engineering Blog (FOCUSED)
    NOW: Company domain only, architecture/tech stack posts
    """
    log(f"[5/7] Searching: Engineering Blog...")

    if not EXA_API_KEY:
        return {'status': 'error', 'error': 'EXA_API_KEY not set'}

    if not domain:
        log("  ⚠️  No domain provided, skipping domain-restricted search")
        return {'status': 'skipped', 'error': 'No domain provided'}

    headers = {
        "x-api-key": EXA_API_KEY,
        "Content-Type": "application/json"
    }

    # Try to guess medium slug
    company_slug = company_name.lower().replace(' ', '-').replace('.', '')

    payload = {
        "query": f'(site:{domain}/blog OR site:{domain}/engineering OR site:medium.com/@{company_slug} OR site:{company_slug}.medium.com) (architecture OR infrastructure OR "tech stack" OR "we use" OR "how we built" OR "data platform" OR migration) (airflow OR kubernetes OR spark OR dbt OR snowflake OR databricks OR python OR aws OR gcp)',
        "numResults": 5,
        "type": "keyword",
        "startPublishedDate": (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
        "contents": {"highlights": True}
    }

    try:
        response = requests.post(
            "https://api.exa.ai/search",
            headers=headers,
            json=payload,
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            return {
                'status': 'success',
                'results': data.get('results', []),
                'count': len(data.get('results', []))
            }
        else:
            return {'status': 'error', 'error': f'HTTP {response.status_code}'}

    except Exception as e:
        return {'status': 'error', 'error': str(e)}


def search_6_product_announcements(company_name: str, domain: Optional[str] = None) -> Dict:
    """
    Search 6: Product Announcements (MINOR IMPROVEMENTS)
    Mostly unchanged, added domain restriction
    """
    log(f"[6/7] Searching: Product Announcements...")

    if not EXA_API_KEY:
        return {'status': 'error', 'error': 'EXA_API_KEY not set'}

    headers = {
        "x-api-key": EXA_API_KEY,
        "Content-Type": "application/json"
    }

    domain_clause = f"site:{domain} OR " if domain else ""

    payload = {
        "query": f'{company_name} (launched OR announces OR "general availability" OR "now available" OR introducing OR "new product") (2025 OR 2026) ({domain_clause}site:producthunt.com OR site:techcrunch.com)',
        "numResults": 5,
        "type": "keyword",
        "startPublishedDate": (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
        "contents": {"highlights": True}
    }

    try:
        response = requests.post(
            "https://api.exa.ai/search",
            headers=headers,
            json=payload,
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            return {
                'status': 'success',
                'results': data.get('results', []),
                'count': len(data.get('results', []))
            }
        else:
            return {'status': 'error', 'error': f'HTTP {response.status_code}'}

    except Exception as e:
        return {'status': 'error', 'error': str(e)}


def search_7_case_studies(company_name: str, domain: Optional[str] = None) -> Dict:
    """
    Search 7: Vendor Case Studies (FOCUSED)
    NOW: Restrict to vendor domains for real case studies
    """
    log(f"[7/7] Searching: Case Studies...")

    if not EXA_API_KEY:
        return {'status': 'error', 'error': 'EXA_API_KEY not set'}

    headers = {
        "x-api-key": EXA_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "query": f'{company_name} ("case study" OR "customer story" OR "success story" OR "built with") (Snowflake OR Databricks OR dbt OR Airflow OR AWS OR GCP OR Azure) (site:snowflake.com OR site:databricks.com OR site:getdbt.com OR site:aws.amazon.com OR site:cloud.google.com OR site:azure.microsoft.com)',
        "numResults": 5,
        "type": "keyword",
        "contents": {"highlights": True}
    }

    try:
        response = requests.post(
            "https://api.exa.ai/search",
            headers=headers,
            json=payload,
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            return {
                'status': 'success',
                'results': data.get('results', []),
                'count': len(data.get('results', []))
            }
        else:
            return {'status': 'error', 'error': f'HTTP {response.status_code}'}

    except Exception as e:
        return {'status': 'error', 'error': str(e)}


# =============================================================================
# TECH STACK EXTRACTION FROM JOB POSTINGS
# =============================================================================

def extract_tech_stack_from_jobs(hiring_results: Dict) -> Dict:
    """
    Extract tech stack mentions from job posting highlights/text.
    This is where job postings become the primary tech stack source.
    """
    tech_keywords = {
        # Orchestration
        'airflow': 'Apache Airflow',
        'apache airflow': 'Apache Airflow',
        'dagster': 'Dagster',
        'prefect': 'Prefect',
        'luigi': 'Luigi',
        'argo': 'Argo Workflows',

        # Cloud
        'aws': 'AWS',
        'amazon web services': 'AWS',
        'gcp': 'Google Cloud',
        'google cloud': 'Google Cloud',
        'azure': 'Microsoft Azure',

        # Data Warehouse
        'snowflake': 'Snowflake',
        'databricks': 'Databricks',
        'redshift': 'Amazon Redshift',
        'bigquery': 'Google BigQuery',

        # Processing
        'spark': 'Apache Spark',
        'flink': 'Apache Flink',
        'kafka': 'Apache Kafka',

        # Transformation
        'dbt': 'dbt',
        'dataform': 'Dataform',

        # Container/Orchestration
        'kubernetes': 'Kubernetes',
        'docker': 'Docker',
        'terraform': 'Terraform',

        # Languages
        'python': 'Python',
        'scala': 'Scala',
        'java': 'Java',
        'sql': 'SQL',
    }

    tech_mentions = {}

    if hiring_results.get('status') != 'success':
        return tech_mentions

    for result in hiring_results.get('results', []):
        # Combine highlights and text
        text = ' '.join(result.get('highlights', []))
        if result.get('text'):
            text += ' ' + result.get('text', '')

        text_lower = text.lower()

        for keyword, tech_name in tech_keywords.items():
            if keyword in text_lower:
                if tech_name not in tech_mentions:
                    tech_mentions[tech_name] = {
                        'count': 0,
                        'sources': []
                    }
                tech_mentions[tech_name]['count'] += 1
                tech_mentions[tech_name]['sources'].append(result.get('url', 'unknown'))

    # Sort by count
    return dict(sorted(tech_mentions.items(), key=lambda x: x[1]['count'], reverse=True))


# =============================================================================
# MAIN TEST FUNCTION
# =============================================================================

def test_company(company_name: str, domain: Optional[str] = None):
    """Test all 7 improved searches + Snowflake context on a company"""

    log(f"\n{'='*80}")
    log(f"Testing Improved Search Prompts: {company_name}")
    if domain:
        log(f"Domain: {domain}")
    log(f"{'='*80}\n")

    if not EXA_API_KEY:
        log("❌ ERROR: EXA_API_KEY not set")
        log("   Set it with: export EXA_API_KEY='your-key-here'")
        return

    results = {}

    # Fetch Snowflake context FIRST
    log("="*80)
    log("FETCHING SALESFORCE/GONG DATA FROM SNOWFLAKE")
    log("="*80 + "\n")

    snowflake_context = fetch_snowflake_context(company_name)

    if snowflake_context.get('status') == 'success':
        log(f"✅ Found account in Salesforce: {snowflake_context['acct_name']}")
        log(f"   Customer: {'YES' if snowflake_context['is_customer'] else 'NO'}")
        log(f"   Contacts: {snowflake_context['contact_count']}")
        log(f"   MQLs: {snowflake_context['mql_count']}")
        log(f"   Opportunities: {snowflake_context['opp_count']}")
        log(f"   Gong Calls: {snowflake_context['call_count']}")
        if snowflake_context.get('latest_mql_date'):
            log(f"   Latest MQL: {snowflake_context['latest_mql_date']}")
        if snowflake_context.get('latest_call_date'):
            log(f"   Latest Call: {snowflake_context['latest_call_date']}")
    elif snowflake_context.get('status') == 'not_found':
        log(f"⚠️  {snowflake_context['message']}")
    elif snowflake_context.get('status') == 'unavailable':
        log(f"⚠️  Snowflake unavailable: {snowflake_context.get('error')}")
    else:
        log(f"❌ Snowflake error: {snowflake_context.get('error')}")

    log(f"\n{'='*80}")
    log("RUNNING WEB SEARCHES")
    log(f"{'='*80}\n")

    # Run all 7 searches
    results['company_research'] = search_1_company_research(company_name, domain)
    time.sleep(1)  # Rate limiting

    results['github_evidence'] = search_2_github_evidence(company_name, domain)
    time.sleep(1)

    results['hiring'] = search_3_hiring_expanded(company_name, domain)
    time.sleep(1)

    results['trigger_events'] = search_4_trigger_events(company_name, domain)
    time.sleep(1)

    results['engineering_blog'] = search_5_engineering_blog(company_name, domain)
    time.sleep(1)

    results['product_announcements'] = search_6_product_announcements(company_name, domain)
    time.sleep(1)

    results['case_studies'] = search_7_case_studies(company_name, domain)

    # Extract tech stack from job postings
    tech_stack = extract_tech_stack_from_jobs(results['hiring'])

    # Print summary
    log(f"\n{'='*80}")
    log("RESULTS SUMMARY")
    log(f"{'='*80}\n")

    for search_name, result in results.items():
        status = result.get('status', 'unknown')
        count = result.get('count', 0)

        if status == 'success':
            log(f"✅ {search_name:25} {count} results")
        elif status == 'skipped':
            log(f"⚠️  {search_name:25} SKIPPED - {result.get('error', 'unknown')}")
        else:
            log(f"❌ {search_name:25} FAILED - {result.get('error', 'unknown')}")

    # Print tech stack found in job postings
    if tech_stack:
        log(f"\n{'='*80}")
        log("TECH STACK FROM JOB POSTINGS (Primary Source)")
        log(f"{'='*80}\n")

        for tech, data in tech_stack.items():
            log(f"  {tech:20} mentioned {data['count']} times")
    else:
        log(f"\n⚠️  No tech stack found in job postings")

    # Print Snowflake engagement details
    if snowflake_context.get('status') == 'success':
        log(f"\n{'='*80}")
        log("SALESFORCE ENGAGEMENT DETAILS")
        log(f"{'='*80}\n")

        # Top contacts
        if snowflake_context.get('contacts'):
            log("--- TOP CONTACTS ---")
            for contact in snowflake_context['contacts'][:5]:
                employee_flag = " (Employee)" if contact.get('is_employee') else ""
                log(f"  • {contact.get('title', 'Unknown')}{employee_flag} - {contact.get('source', 'unknown source')}")

        # Recent MQLs
        if snowflake_context.get('mqls'):
            log("\n--- RECENT MQLs ---")
            for mql in snowflake_context['mqls'][:5]:
                log(f"  • {mql['mql_date']} - {mql.get('channel', 'unknown')} ({mql.get('utm_campaign', 'no campaign')})")

        # Opportunities
        if snowflake_context.get('opps'):
            log("\n--- OPPORTUNITIES ---")
            for opp in snowflake_context['opps']:
                log(f"  • {opp.get('opp_name')} - {opp.get('stage')} (created {opp.get('created_date', 'unknown')})")

        # Recent Gong calls
        if snowflake_context.get('gong_calls'):
            log("\n--- RECENT GONG CALLS ---")
            for call in snowflake_context['gong_calls']:
                log(f"  • {call.get('date')} - {call.get('title')}")
                if call.get('transcript_preview'):
                    log(f"    Preview: {call['transcript_preview'][:150]}...")

    # Print sample results
    log(f"\n{'='*80}")
    log("SAMPLE WEB SEARCH RESULTS (first result from each search)")
    log(f"{'='*80}\n")

    for search_name, result in results.items():
        if result.get('status') == 'success' and result.get('results'):
            first = result['results'][0]
            log(f"\n--- {search_name.upper()} ---")
            log(f"Title: {first.get('title', 'N/A')}")
            log(f"URL: {first.get('url', 'N/A')}")
            if first.get('highlights'):
                log(f"Highlight: {first['highlights'][0][:200]}...")

    # Save full results to file
    output_file = f"test_results_{company_name.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            'company_name': company_name,
            'domain': domain,
            'timestamp': datetime.now().isoformat(),
            'snowflake_context': snowflake_context,
            'web_search_results': results,
            'tech_stack_from_jobs': tech_stack
        }, f, indent=2)

    log(f"\n✅ Full results saved to: {output_file}")

    # Summary classification
    log(f"\n{'='*80}")
    log("ACCOUNT CLASSIFICATION")
    log(f"{'='*80}\n")

    if snowflake_context.get('status') == 'success':
        is_customer = snowflake_context.get('is_customer')
        has_opps = snowflake_context.get('opp_count', 0) > 0
        has_calls = snowflake_context.get('call_count', 0) > 0
        has_mqls = snowflake_context.get('mql_count', 0) > 0

        if is_customer:
            classification = "🟢 CUSTOMER"
        elif has_opps and has_calls:
            classification = "🟡 ENGAGED PROSPECT (Active Pipeline)"
        elif has_calls:
            classification = "🟡 ENGAGED PROSPECT (Evaluating)"
        elif has_mqls:
            classification = "🟠 WARM LEAD"
        else:
            classification = "⚪ COLD PROSPECT"

        log(f"Classification: {classification}")

        # Airflow signals
        airflow_signals = []
        if tech_stack.get('Apache Airflow'):
            airflow_signals.append(f"✅ Airflow in job postings ({tech_stack['Apache Airflow']['count']}x)")

        if any('airflow' in str(result).lower() for result in results.get('github_evidence', {}).get('results', [])):
            airflow_signals.append("✅ Airflow in GitHub repos")

        if any('airflow' in str(result).lower() for result in results.get('engineering_blog', {}).get('results', [])):
            airflow_signals.append("✅ Airflow in engineering blog")

        if any('airflow' in call.get('transcript_preview', '').lower() for call in snowflake_context.get('gong_calls', [])):
            airflow_signals.append("✅ Airflow mentioned in Gong calls")

        if airflow_signals:
            log(f"\n🎯 Airflow Signals Found:")
            for signal in airflow_signals:
                log(f"   {signal}")
        else:
            log(f"\n⚠️  No Airflow signals detected")
    else:
        log("Classification: ⚪ UNKNOWN (Not in Salesforce)")
        log("⚠️  Cannot classify without Salesforce data")


# =============================================================================
# CLI
# =============================================================================

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 test_improved_searches.py 'Company Name' [--domain company.com]")
        print("\nExamples:")
        print("  python3 test_improved_searches.py 'Komodo Health'")
        print("  python3 test_improved_searches.py 'Komodo Health' --domain komodohealth.com")
        print("  python3 test_improved_searches.py 'Airbnb' --domain airbnb.com")
        sys.exit(1)

    company_name = sys.argv[1]
    domain = None

    if len(sys.argv) >= 4 and sys.argv[2] == '--domain':
        domain = sys.argv[3]

    test_company(company_name, domain)
