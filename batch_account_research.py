#!/usr/bin/env python3
"""
Batch Account Research with Snowflake Integration

Three-phase process:
1. Bulk engagement check (MQLs/calls) - single Snowflake query
2. Conditional Snowflake context - only for engaged accounts
3. Parallel web research (Exa) - ALL accounts

Outputs:
- Snowflake table: GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT
- JSON files: ~/claude-work/batch-research-output/{date}/{company}/

Usage:
    python3 batch_account_research.py --accounts "GridX,ollietot"
    python3 batch_account_research.py --accounts-file accounts.txt
"""

import os
import sys
import json
import argparse
import time
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

import snowflake.connector
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import requests
import anthropic

# --- Config ---
SNOWFLAKE_CONFIG = Path.home() / ".snowflake/service_config.yaml"
EXA_API_KEY = os.getenv("EXA_API_KEY")
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OUTPUT_DIR = Path.home() / "claude-work/batch-research-output"
SNOWFLAKE_TABLE = "GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT"

# --- Data Models ---

@dataclass
class Account:
    acct_id: str
    acct_name: str
    acct_type: str
    is_current_customer: bool
    customer_since_date: Optional[datetime] = None
    parent_name: Optional[str] = None

@dataclass
class Contact:
    contact_id: str
    title: Optional[str]
    primary_domain: str
    source: Optional[str]
    is_employee: bool

@dataclass
class MQL:
    contact_id: str
    mql_date: datetime
    reporting_channel: str
    utm_source: Optional[str]

@dataclass
class Opportunity:
    opp_id: str
    opp_name: str
    opp_type: str
    stage: str
    close_date: Optional[datetime]
    created_date: datetime

@dataclass
class TranscriptMeta:
    call_id: str
    call_title: str
    scheduled_ts: datetime
    attendees: str
    full_transcript: Optional[str] = None

@dataclass
class AccountContext:
    account: Account
    contacts: List[Contact]
    mqls: List[MQL]
    opportunities: List[Opportunity]
    transcripts: List[TranscriptMeta]
    has_sf_context: bool

@dataclass
class ResearchResult:
    acct_id: Optional[str]
    acct_name: str
    tier: str
    priority_score: int
    has_sf_context: bool
    contact_count: int
    mql_count: int
    opp_count: int
    call_count: int
    latest_mql_date: Optional[datetime]
    latest_call_date: Optional[datetime]
    key_signals: List[str]
    tech_stack: List[str]
    report_json_path: str
    processing_time_sec: float
    status: str
    error_message: Optional[str] = None
    exa_metadata: Optional[Dict] = None  # v2: Enhanced Exa metadata
    comprehensive_report: Optional[str] = None  # v2: i360-style comprehensive report
    structured_signals: Optional[str] = None  # v2: Full structured signals as JSON text
    structured_tech_stack: Optional[str] = None  # v2: Full tech stack with confidence as JSON text
    batch_tag: Optional[str] = None  # Tag for grouping research batches

# --- Exa v2 Infrastructure ---

@dataclass
class ExaSearchConfig:
    """Configuration for comprehensive Exa research"""
    timeout_sec: int = 15
    max_retries: int = 3
    retry_backoff_base: float = 2.0
    enable_website_crawl: bool = True
    enable_job_crawl: bool = True
    max_job_descriptions: int = 2
    news_months_back: int = 12
    hiring_months_back: int = 6
    orchestration_months_back: int = 12
    blog_months_back: int = 18
    product_months_back: int = 12

@dataclass
class ExaResearchResult:
    """Return type for v2 comprehensive Exa research"""
    status: str  # 'success', 'partial', 'failed'
    key_signals: List[Dict]  # Top 20 structured signals with metadata
    tech_stack: List[Dict]   # Enriched tech stack with confidence
    search_results: Dict     # Full results per search type
    metadata: Dict           # Timing, counts, errors

    def to_legacy_format(self) -> Dict:
        """Convert v2 format to v1 for backward compatibility"""
        return {
            'status': self.status,
            'key_signals': [s['signal'] for s in self.key_signals[:5]],
            'tech_stack': [t['technology'] for t in self.tech_stack[:10]],
            'summary': f"Found {self.metadata.get('searches_completed', 0)} search results"
        }

class RateLimiter:
    """Token bucket rate limiter for API calls"""

    def __init__(self, rate_per_minute: int = 60, burst: int = 10):
        self.rate = rate_per_minute
        self.burst = burst
        self.tokens = burst
        self.last_update = time.time()
        self._lock = __import__('threading').Lock()

    def acquire(self, tokens: int = 1) -> float:
        """
        Acquire tokens for API call.
        Returns: wait time in seconds (0 if no wait needed)
        """
        with self._lock:
            now = time.time()
            elapsed = now - self.last_update

            # Add tokens based on time elapsed
            self.tokens = min(
                self.burst,
                self.tokens + (elapsed * self.rate / 60.0)
            )
            self.last_update = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return 0.0
            else:
                # Calculate wait time needed
                tokens_needed = tokens - self.tokens
                wait_time = (tokens_needed * 60.0) / self.rate
                time.sleep(wait_time)
                self.tokens = 0
                return wait_time

class CircuitBreaker:
    """Circuit breaker for API failure handling"""

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half_open
        self._lock = __import__('threading').Lock()

    def record_success(self):
        """Record successful API call"""
        with self._lock:
            self.failure_count = 0
            if self.state == 'half_open':
                self.state = 'closed'

    def record_failure(self):
        """Record failed API call"""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.state = 'open'
                log(f"⚠️  Circuit breaker OPEN after {self.failure_count} failures. Pausing for {self.timeout}s...")

    def can_proceed(self) -> bool:
        """Check if API calls can proceed"""
        with self._lock:
            if self.state == 'closed':
                return True
            elif self.state == 'open':
                # Check if timeout has elapsed
                if self.last_failure_time:
                    elapsed = time.time() - self.last_failure_time
                    if elapsed >= self.timeout:
                        self.state = 'half_open'
                        self.failure_count = 0
                        log("Circuit breaker HALF_OPEN - retrying...")
                        return True
                return False
            else:  # half_open
                return True

# --- Utilities ---

def log(msg: str):
    """Print timestamped log"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def slugify(name: str) -> str:
    """Convert company name to filesystem-safe slug"""
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9\s]', '', slug)
    slug = re.sub(r'\s+', '_', slug)
    return slug

def get_snowflake_connection():
    """Create Snowflake connection using private key auth"""
    with open(Path.home() / ".ssh/rsa_key_unencrypted.p8", 'rb') as key_file:
        p_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )

    private_key_bytes = p_key.private_bytes(
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

# --- Phase 1: Bulk Engagement Check ---

def bulk_check_engagement(account_list: List[str]) -> Dict[str, dict]:
    """
    Phase 1: Single query to check MQL/call counts for all accounts.
    Returns: {account_name: {acct_id, mql_count, call_count, ...}}
    """
    log(f"Phase 1: Checking engagement for {len(account_list)} accounts...")

    conn = get_snowflake_connection()
    cursor = conn.cursor()

    # Build query with LIKE clauses for fuzzy matching
    where_clauses = ' OR '.join([f'LOWER(a.ACCT_NAME) LIKE %s' for _ in account_list])
    query = f'''
    SELECT
        a.ACCT_ID,
        a.ACCT_NAME,
        a.ACCT_TYPE,
        a.IS_CURRENT_CUST,
        a.CUSTOMER_SINCE_DATE,
        a.PARENT_NAME,
        COUNT(DISTINCT c.CONTACT_ID) as contact_count,
        COUNT(DISTINCT m.CONTACT_ID) as mql_count,
        COUNT(DISTINCT o.OPP_ID) as opp_count,
        COUNT(DISTINCT g.CALL_ID) as call_count,
        MAX(m.MQL_TS) as latest_mql_date,
        MAX(g.SCHEDULED_TS) as latest_call_date
    FROM HQ.MODEL_CRM.SF_ACCOUNTS a
    LEFT JOIN HQ.MODEL_CRM.SF_CONTACTS c ON a.ACCT_ID = c.ACCT_ID
    LEFT JOIN HQ.MODEL_CRM.SF_MQLS m ON a.ACCT_ID = m.ACCT_ID
    LEFT JOIN HQ.MODEL_CRM.SF_OPPS o ON a.ACCT_ID = o.ACCT_ID
    LEFT JOIN HQ.MODEL_CRM_SENSITIVE.GONG_CALL_TRANSCRIPTS g ON a.ACCT_ID = g.ACCT_ID
    WHERE {where_clauses}
    GROUP BY a.ACCT_ID, a.ACCT_NAME, a.ACCT_TYPE, a.IS_CURRENT_CUST, a.CUSTOMER_SINCE_DATE, a.PARENT_NAME
    '''

    try:
        # Use LIKE patterns with wildcards
        like_patterns = tuple([f'%{name.lower()}%' for name in account_list])
        cursor.execute(query, like_patterns)
        results = cursor.fetchall()

        # Build engagement map keyed by user-provided account name (for easier lookup)
        engagement_map = {}
        for row in results:
            sf_name = row[1]
            sf_name_lower = sf_name.lower()

            # Match this result to the original user-provided account name
            matched_user_name = None
            for user_name in account_list:
                if user_name.lower() in sf_name_lower or sf_name_lower in user_name.lower():
                    matched_user_name = user_name.lower()
                    break

            if matched_user_name:
                engagement_map[matched_user_name] = {
                    'acct_id': row[0],
                    'acct_name': row[1],
                    'acct_type': row[2],
                    'is_current_cust': row[3],
                    'customer_since_date': row[4],
                    'parent_name': row[5],
                    'contact_count': row[6],
                    'mql_count': row[7],
                    'opp_count': row[8],
                    'call_count': row[9],
                    'latest_mql_date': row[10],
                    'latest_call_date': row[11],
                    'has_engagement': row[7] > 0 or row[9] > 0  # has MQLs or calls
                }

        engaged_count = sum(1 for data in engagement_map.values() if data['has_engagement'])
        log(f"Phase 1: Found {len(engagement_map)} accounts in Snowflake, {engaged_count} with MQLs/calls")

        cursor.close()
        conn.close()
        return engagement_map

    except Exception as e:
        log(f"Phase 1 ERROR: {e}")
        cursor.close()
        conn.close()
        return {}

# --- Phase 2: Conditional Snowflake Context ---

def bulk_fetch_snowflake_context(acct_ids: List[str]) -> Dict[str, AccountContext]:
    """
    Phase 2: Bulk fetch Snowflake context for engaged accounts only.
    Returns: {acct_id: AccountContext}
    """
    if not acct_ids:
        return {}

    log(f"Phase 2: Fetching Snowflake context for {len(acct_ids)} engaged accounts...")

    conn = get_snowflake_connection()
    cursor = conn.cursor()
    contexts = {}

    try:
        placeholders = ', '.join(['%s' for _ in acct_ids])

        # Fetch contacts
        cursor.execute('''
            SELECT ACCT_ID, CONTACT_ID, TITLE, PRIMARY_DOMAIN, SOURCE, IS_EMPLOYEE
            FROM HQ.MODEL_CRM.SF_CONTACTS
            WHERE ACCT_ID IN ({})
            ORDER BY ACCT_ID, IS_EMPLOYEE DESC, TITLE
            LIMIT 1000
        '''.format(placeholders), tuple(acct_ids))
        contact_rows = cursor.fetchall()

        # Fetch MQLs
        cursor.execute('''
            SELECT ACCT_ID, CONTACT_ID, MQL_TS, REPORTING_CHANNEL, UTM_SOURCE
            FROM HQ.MODEL_CRM.SF_MQLS
            WHERE ACCT_ID IN ({})
            ORDER BY ACCT_ID, MQL_TS DESC
            LIMIT 1000
        '''.format(placeholders), tuple(acct_ids))
        mql_rows = cursor.fetchall()

        # Fetch opportunities
        cursor.execute('''
            SELECT ACCT_ID, OPP_ID, OPP_NAME, OPP_TYPE, CURRENT_STAGE_NAME,
                   CLOSE_DATE, CREATED_DATE
            FROM HQ.MODEL_CRM.SF_OPPS
            WHERE ACCT_ID IN ({})
            ORDER BY ACCT_ID, CREATED_DATE DESC
            LIMIT 1000
        '''.format(placeholders), tuple(acct_ids))
        opp_rows = cursor.fetchall()

        # Fetch Gong transcripts with full text
        cursor.execute('''
            SELECT ACCT_ID, CALL_ID, CALL_TITLE, SCHEDULED_TS, ATTENDEES, FULL_TRANSCRIPT
            FROM HQ.MODEL_CRM_SENSITIVE.GONG_CALL_TRANSCRIPTS
            WHERE ACCT_ID IN ({})
            ORDER BY ACCT_ID, SCHEDULED_TS DESC
            LIMIT 1000
        '''.format(placeholders), tuple(acct_ids))
        transcript_rows = cursor.fetchall()

        # Fetch email correspondence from Salesforce
        cursor.execute('''
            SELECT
                o.ACCOUNT_ID,
                t.ID as email_id,
                t.SUBJECT,
                t.CREATED_DATE,
                LEFT(t.DESCRIPTION, 500) as description_preview
            FROM IN_SALESFORCE.OPPORTUNITY o
            INNER JOIN IN_SALESFORCE.TASK t ON o.ID = t.WHAT_ID
            WHERE o.ACCOUNT_ID IN ({})
              AND t.TYPE = 'Email'
            ORDER BY o.ACCOUNT_ID, t.CREATED_DATE DESC
            LIMIT 1000
        '''.format(placeholders), tuple(acct_ids))
        email_rows = cursor.fetchall()

        # Group by account_id
        contacts_by_acct = {}
        for row in contact_rows:
            acct_id = row[0]
            if acct_id not in contacts_by_acct:
                contacts_by_acct[acct_id] = []
            contacts_by_acct[acct_id].append(Contact(
                contact_id=row[1],
                title=row[2],
                primary_domain=row[3],
                source=row[4],
                is_employee=row[5]
            ))

        mqls_by_acct = {}
        for row in mql_rows:
            acct_id = row[0]
            if acct_id not in mqls_by_acct:
                mqls_by_acct[acct_id] = []
            mqls_by_acct[acct_id].append(MQL(
                contact_id=row[1],
                mql_date=row[2],
                reporting_channel=row[3],
                utm_source=row[4]
            ))

        opps_by_acct = {}
        for row in opp_rows:
            acct_id = row[0]
            if acct_id not in opps_by_acct:
                opps_by_acct[acct_id] = []
            opps_by_acct[acct_id].append(Opportunity(
                opp_id=row[1],
                opp_name=row[2],
                opp_type=row[3],
                stage=row[4],
                close_date=row[5],
                created_date=row[6]
            ))

        transcripts_by_acct = {}
        for row in transcript_rows:
            acct_id = row[0]
            if acct_id not in transcripts_by_acct:
                transcripts_by_acct[acct_id] = []
            transcripts_by_acct[acct_id].append(TranscriptMeta(
                call_id=row[1],
                call_title=row[2],
                scheduled_ts=row[3],
                attendees=row[4],
                full_transcript=row[5]
            ))

        emails_by_acct = {}
        for row in email_rows:
            acct_id = row[0]
            if acct_id not in emails_by_acct:
                emails_by_acct[acct_id] = []
            emails_by_acct[acct_id].append({
                'email_id': row[1],
                'subject': row[2],
                'date': row[3].isoformat() if row[3] else None,
                'preview': row[4]
            })

        log(f"Phase 2: Fetched {len(contact_rows)} contacts, {len(mql_rows)} MQLs, {len(opp_rows)} opps, {len(transcript_rows)} calls, {len(email_rows)} emails")

        cursor.close()
        conn.close()
        return {
            'contacts_by_acct': contacts_by_acct,
            'mqls_by_acct': mqls_by_acct,
            'opps_by_acct': opps_by_acct,
            'transcripts_by_acct': transcripts_by_acct,
            'emails_by_acct': emails_by_acct
        }

    except Exception as e:
        log(f"Phase 2 ERROR: {e}")
        cursor.close()
        conn.close()
        return {}

# --- Phase 3: Web Research (Exa) ---

# Exa v2: Individual Search Functions

def _execute_search_with_retry(
    search_func,
    config: ExaSearchConfig,
    circuit_breaker: CircuitBreaker,
    *args,
    **kwargs
) -> Dict:
    """Exponential backoff retry wrapper for Exa API calls"""
    for attempt in range(config.max_retries):
        if not circuit_breaker.can_proceed():
            return {'status': 'error', 'error': 'circuit_breaker_open'}

        try:
            response = search_func(*args, **kwargs)
            if response.status_code == 200:
                circuit_breaker.record_success()
                return {'status': 'success', 'data': response.json()}
            elif response.status_code == 429:
                circuit_breaker.record_failure()
                wait = config.retry_backoff_base ** attempt
                log(f"⚠️  Rate limit hit, waiting {wait}s...")
                time.sleep(wait)
            else:
                circuit_breaker.record_failure()
                return {'status': 'error', 'error': f'http_{response.status_code}'}
        except requests.Timeout:
            circuit_breaker.record_failure()
            if attempt == config.max_retries - 1:
                return {'status': 'error', 'error': 'timeout'}
        except Exception as e:
            circuit_breaker.record_failure()
            return {'status': 'error', 'error': str(e)}

    return {'status': 'error', 'error': 'max_retries_exceeded'}

def _claude_web_search_fallback(query: str, company_name: str) -> Dict:
    """
    Fallback to Claude API for web search when Exa fails.
    Uses Claude's extended thinking + web search to gather information.
    """
    if not ANTHROPIC_API_KEY:
        return {'status': 'error', 'error': 'anthropic_api_key_not_set'}

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        # Use Claude to perform web search and extract highlights
        search_prompt = f"""Search the web for: {query}

Extract the most relevant findings about {company_name}. Return your response as a JSON object with this structure:
{{
    "results": [
        {{
            "title": "result title",
            "url": "result url",
            "highlights": ["key point 1", "key point 2", "key point 3"]
        }}
    ]
}}

Focus on factual, specific information. Each highlight should be a complete sentence or fact."""

        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": search_prompt
            }]
        )

        # Parse Claude's response
        content = response.content[0].text

        # Try to extract JSON from the response
        try:
            # Find JSON object in the response
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                data = json.loads(json_str)
                return {'status': 'success', 'data': data, 'source': 'claude_fallback'}
            else:
                # If no JSON found, create a simple structure from the text
                return {
                    'status': 'success',
                    'data': {
                        'results': [{
                            'title': f'{company_name} research via Claude',
                            'highlights': [content[:500]]  # Use first 500 chars as highlight
                        }]
                    },
                    'source': 'claude_fallback'
                }
        except json.JSONDecodeError:
            # If JSON parsing fails, return raw content as highlight
            return {
                'status': 'success',
                'data': {
                    'results': [{
                        'title': f'{company_name} research via Claude',
                        'highlights': [content[:500]]
                    }]
                },
                'source': 'claude_fallback'
            }

    except Exception as e:
        return {'status': 'error', 'error': f'claude_fallback_failed: {str(e)}'}

def _brave_search_fallback(query: str, company_name: str) -> Dict:
    """
    Fallback to Brave Search API when Exa fails.
    Uses Brave Web Search to gather information.
    """
    if not BRAVE_API_KEY:
        return {'status': 'error', 'error': 'brave_api_key_not_set'}

    try:
        headers = {
            "X-Subscription-Token": BRAVE_API_KEY,
            "Accept": "application/json"
        }

        params = {
            "q": query,
            "count": 5,  # Number of results
            "text_decorations": False,
            "search_lang": "en"
        }

        response = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers=headers,
            params=params,
            timeout=15
        )

        if response.status_code != 200:
            return {'status': 'error', 'error': f'brave_http_{response.status_code}'}

        data = response.json()

        # Transform Brave results to match Exa format
        results = []
        if 'web' in data and 'results' in data['web']:
            for result in data['web']['results'][:5]:
                results.append({
                    'title': result.get('title', ''),
                    'url': result.get('url', ''),
                    'highlights': [result.get('description', '')]
                })

        return {
            'status': 'success',
            'data': {
                'results': results
            },
            'source': 'brave_fallback'
        }

    except Exception as e:
        return {'status': 'error', 'error': f'brave_fallback_failed: {str(e)}'}

def _search_company_research(
    company_name: str,
    config: ExaSearchConfig,
    rate_limiter: RateLimiter,
    circuit_breaker: CircuitBreaker
) -> Dict:
    """Search 1: Company research overview"""
    rate_limiter.acquire()

    # Use Brave if Exa key not available
    if not EXA_API_KEY:
        return _brave_search_fallback(f"{company_name} company overview business model", company_name)

    headers = {
        "x-api-key": EXA_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "query": f"{company_name} company overview",
        "numResults": 5,
        "type": "keyword",
        "contents": {"highlights": True}
    }

    def make_request():
        return requests.post(
            "https://api.exa.ai/search",
            headers=headers,
            json=payload,
            timeout=config.timeout_sec
        )

    result = _execute_search_with_retry(make_request, config, circuit_breaker)

    # Fallback to Brave if Exa fails
    if result.get('status') != 'success':
        log(f"[{company_name}] Exa failed for company research, falling back to Brave Search...")
        return _brave_search_fallback(f"{company_name} company overview business model", company_name)

    return result

def _search_orchestration(
    company_name: str,
    config: ExaSearchConfig,
    rate_limiter: RateLimiter,
    circuit_breaker: CircuitBreaker
) -> Dict:
    """Search 2: Orchestration evidence (Airflow, Dagster, Prefect)"""
    rate_limiter.acquire()

    # Use Brave if Exa key not available
    if not EXA_API_KEY:
        return _brave_search_fallback(f"{company_name} data pipeline orchestration airflow dagster prefect", company_name)

    # Calculate date filter (12 months back)
    start_date = (datetime.now() - timedelta(days=30 * config.orchestration_months_back)).strftime('%Y-%m-%d')

    headers = {
        "x-api-key": EXA_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "query": f"{company_name} data pipeline orchestration airflow dagster prefect",
        "numResults": 5,
        "type": "keyword",
        "startPublishedDate": start_date,
        "contents": {"highlights": True}
    }

    def make_request():
        return requests.post(
            "https://api.exa.ai/search",
            headers=headers,
            json=payload,
            timeout=config.timeout_sec
        )

    result = _execute_search_with_retry(make_request, config, circuit_breaker)

    # Fallback to Brave if Exa fails
    if result.get('status') != 'success':
        log(f"[{company_name}] Exa failed for orchestration search, falling back to Brave Search...")
        return _brave_search_fallback(f"{company_name} data pipeline orchestration airflow dagster prefect", company_name)

    return result

def _search_hiring(
    company_name: str,
    config: ExaSearchConfig,
    rate_limiter: RateLimiter,
    circuit_breaker: CircuitBreaker
) -> Dict:
    """Search 3: Hiring signals (data engineer, platform engineer jobs)"""
    rate_limiter.acquire()

    # Use Brave if Exa key not available
    if not EXA_API_KEY:
        return _brave_search_fallback(f"{company_name} hiring data engineer platform engineer jobs", company_name)

    # Calculate date filter (6 months back)
    start_date = (datetime.now() - timedelta(days=30 * config.hiring_months_back)).strftime('%Y-%m-%d')

    headers = {
        "x-api-key": EXA_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "query": f"{company_name} hiring data engineer platform engineer",
        "numResults": 5,
        "type": "keyword",
        "category": "company",
        "startPublishedDate": start_date,
        "contents": {"highlights": True}
    }

    def make_request():
        return requests.post(
            "https://api.exa.ai/search",
            headers=headers,
            json=payload,
            timeout=config.timeout_sec
        )

    result = _execute_search_with_retry(make_request, config, circuit_breaker)

    # Fallback to Brave if Exa fails
    if result.get('status') != 'success':
        log(f"[{company_name}] Exa failed for hiring search, falling back to Brave Search...")
        return _brave_search_fallback(f"{company_name} hiring data engineer platform engineer jobs", company_name)

    return result

def _search_news(
    company_name: str,
    config: ExaSearchConfig,
    rate_limiter: RateLimiter,
    circuit_breaker: CircuitBreaker
) -> Dict:
    """Search 4: Recent news and corporate strategy"""
    rate_limiter.acquire()

    # Use Brave if Exa key not available
    if not EXA_API_KEY:
        return _brave_search_fallback(f"{company_name} corporate strategy news 2025 2026", company_name)

    headers = {
        "x-api-key": EXA_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "query": f"{company_name} corporate strategy news 2025 2026",
        "numResults": 5,
        "type": "keyword",
        "contents": {"highlights": True}
    }

    def make_request():
        return requests.post(
            "https://api.exa.ai/search",
            headers=headers,
            json=payload,
            timeout=config.timeout_sec
        )

    result = _execute_search_with_retry(make_request, config, circuit_breaker)

    # Fallback to Brave if Exa fails
    if result.get('status') != 'success':
        log(f"[{company_name}] Exa failed for news search, falling back to Brave Search...")
        return _brave_search_fallback(f"{company_name} corporate strategy news 2025 2026", company_name)

    return result

def _search_blog_posts(
    company_name: str,
    config: ExaSearchConfig,
    rate_limiter: RateLimiter,
    circuit_breaker: CircuitBreaker
) -> Dict:
    """Search 5: Engineering blog posts about data infrastructure"""
    rate_limiter.acquire()

    # Use Brave if Exa key not available
    if not EXA_API_KEY:
        return _brave_search_fallback(f"{company_name} engineering blog data infrastructure pipeline platform", company_name)

    # Calculate date filter (18 months back)
    start_date = (datetime.now() - timedelta(days=30 * config.blog_months_back)).strftime('%Y-%m-%d')

    headers = {
        "x-api-key": EXA_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "query": f"{company_name} engineering blog data infrastructure pipeline platform",
        "numResults": 5,
        "type": "keyword",
        "startPublishedDate": start_date,
        "contents": {"highlights": True}
    }

    def make_request():
        return requests.post(
            "https://api.exa.ai/search",
            headers=headers,
            json=payload,
            timeout=config.timeout_sec
        )

    result = _execute_search_with_retry(make_request, config, circuit_breaker)

    # Fallback to Brave if Exa fails
    if result.get('status') != 'success':
        log(f"[{company_name}] Exa failed for blog posts search, falling back to Brave Search...")
        return _brave_search_fallback(f"{company_name} engineering blog data infrastructure pipeline platform", company_name)

    return result

def _search_product_announcements(
    company_name: str,
    config: ExaSearchConfig,
    rate_limiter: RateLimiter,
    circuit_breaker: CircuitBreaker
) -> Dict:
    """Search 6: Product launches and announcements"""
    rate_limiter.acquire()

    # Use Brave if Exa key not available
    if not EXA_API_KEY:
        return _brave_search_fallback(f"{company_name} product launch announcement new feature release", company_name)

    # Calculate date filter (12 months back)
    start_date = (datetime.now() - timedelta(days=30 * config.product_months_back)).strftime('%Y-%m-%d')

    headers = {
        "x-api-key": EXA_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "query": f"{company_name} product launch announcement new feature release",
        "numResults": 5,
        "type": "keyword",
        "startPublishedDate": start_date,
        "contents": {"highlights": True}
    }

    def make_request():
        return requests.post(
            "https://api.exa.ai/search",
            headers=headers,
            json=payload,
            timeout=config.timeout_sec
        )

    result = _execute_search_with_retry(make_request, config, circuit_breaker)

    # Fallback to Brave if Exa fails
    if result.get('status') != 'success':
        log(f"[{company_name}] Exa failed for product announcements search, falling back to Brave Search...")
        return _brave_search_fallback(f"{company_name} product launch announcement new feature release", company_name)

    return result

def _search_case_studies(
    company_name: str,
    config: ExaSearchConfig,
    rate_limiter: RateLimiter,
    circuit_breaker: CircuitBreaker
) -> Dict:
    """Search 7: Case studies and customer stories (2 queries merged)"""
    rate_limiter.acquire()

    # Use Brave if Exa key not available
    if not EXA_API_KEY:
        return _brave_search_fallback(f"{company_name} case study customer story Snowflake Databricks dbt AWS", company_name)

    headers = {
        "x-api-key": EXA_API_KEY,
        "Content-Type": "application/json"
    }

    # Query A: Generic case studies
    payload_a = {
        "query": f"{company_name} case study customer story",
        "numResults": 3,
        "type": "keyword",
        "contents": {"highlights": True}
    }

    # Query B: Vendor-specific case studies
    rate_limiter.acquire()  # Second query needs token
    payload_b = {
        "query": f"{company_name} Snowflake OR Databricks OR dbt OR AWS OR Google Cloud OR Azure case study OR customer OR partner",
        "numResults": 3,
        "type": "keyword",
        "contents": {"highlights": True}
    }

    def make_request_a():
        return requests.post(
            "https://api.exa.ai/search",
            headers=headers,
            json=payload_a,
            timeout=config.timeout_sec
        )

    def make_request_b():
        return requests.post(
            "https://api.exa.ai/search",
            headers=headers,
            json=payload_b,
            timeout=config.timeout_sec
        )

    # Execute both queries
    result_a = _execute_search_with_retry(make_request_a, config, circuit_breaker)
    result_b = _execute_search_with_retry(make_request_b, config, circuit_breaker)

    # Merge results
    if result_a['status'] == 'success' or result_b['status'] == 'success':
        merged_results = []
        if result_a['status'] == 'success':
            merged_results.extend(result_a['data'].get('results', []))
        if result_b['status'] == 'success':
            merged_results.extend(result_b['data'].get('results', []))

        return {
            'status': 'success',
            'data': {'results': merged_results}
        }
    else:
        # Both Exa queries failed, fallback to Brave
        log(f"[{company_name}] Exa failed for case studies search, falling back to Brave Search...")
        return _brave_search_fallback(f"{company_name} case study customer story Snowflake Databricks dbt AWS", company_name)

def _crawl_website(
    domain: str,
    config: ExaSearchConfig,
    rate_limiter: RateLimiter,
    circuit_breaker: CircuitBreaker
) -> Dict:
    """Search 8: Crawl company website homepage"""
    rate_limiter.acquire()

    headers = {
        "x-api-key": EXA_API_KEY,
        "Content-Type": "application/json"
    }

    # Ensure domain has https://
    url = domain if domain.startswith('http') else f"https://{domain}"

    payload = {
        "urls": [url],
        "text": {"maxCharacters": 5000}
    }

    def make_request():
        return requests.post(
            "https://api.exa.ai/contents",
            headers=headers,
            json=payload,
            timeout=config.timeout_sec
        )

    return _execute_search_with_retry(make_request, config, circuit_breaker)

def _crawl_job_description(
    url: str,
    config: ExaSearchConfig,
    rate_limiter: RateLimiter,
    circuit_breaker: CircuitBreaker
) -> Dict:
    """Search 9: Crawl job description page"""
    rate_limiter.acquire()

    headers = {
        "x-api-key": EXA_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "urls": [url],
        "text": {"maxCharacters": 5000}
    }

    def make_request():
        return requests.post(
            "https://api.exa.ai/contents",
            headers=headers,
            json=payload,
            timeout=config.timeout_sec
        )

    return _execute_search_with_retry(make_request, config, circuit_breaker)

def _extract_job_urls_from_hiring_results(hiring_result: Dict, max_urls: int = 2) -> List[str]:
    """Extract job posting URLs from hiring search results"""
    if hiring_result.get('status') != 'success':
        return []

    urls = []
    results = hiring_result.get('data', {}).get('results', [])

    for result in results[:max_urls]:
        url = result.get('url')
        if url and ('jobs' in url.lower() or 'careers' in url.lower()):
            urls.append(url)

    return urls[:max_urls]

# Exa v2: Signal and Tech Stack Aggregation

def _is_signal_valid(signal_text: str, url: str, company_name: str) -> tuple:
    """
    Validate if a signal is actually about the company.

    Returns: (is_valid: bool, reason: str)
    """
    signal_lower = signal_text.lower()
    url_lower = url.lower()
    company_lower = company_name.lower()

    # Extract company domain (e.g., "Smith Gardens" -> "smithgardens")
    company_domain = ''.join(company_name.lower().split())

    # BLOCKLIST: Filter out obvious garbage
    garbage_domains = [
        'amazon.com',
        'linkedin.com/jobs',
        'indeed.com',
        'glassdoor.com',
        'github.com/gist',
        'stackoverflow.com',
        'reddit.com',
        'medium.com/@',
        'dev.to'
    ]

    garbage_phrases = [
        'click the button below',
        'continue shopping',
        'conditions of use',
        'privacy policy',
        '© 1996-2025',
        'any time (5,',
        'past month (',
        'past week (',
        'job type',
        'full-time (',
        'part-time ('
    ]

    # Check for garbage
    for domain in garbage_domains:
        if domain in url_lower:
            return (False, f"garbage_domain:{domain}")

    for phrase in garbage_phrases:
        if phrase in signal_lower:
            return (False, f"garbage_phrase:{phrase[:20]}")

    # Filter out too-generic content
    if len(signal_text) < 50:
        return (False, "too_short")

    # Check if signal is about the company
    # Accept if: company name in text OR company domain in URL
    company_in_text = company_lower in signal_lower
    company_in_url = company_domain in url_lower

    if company_in_text or company_in_url:
        return (True, "verified")

    # Special case: Website crawl results are always valid (they're from company site)
    if company_domain in url_lower and any(ext in url_lower for ext in ['.com', '.io', '.co', '.net']):
        return (True, "company_domain")

    return (False, "no_company_mention")

def _aggregate_signals(search_results: Dict, company_name: str) -> List[Dict]:
    """
    Extract and score top 20 signals from all searches.

    NOW WITH VALIDATION: Filters out garbage and non-company-specific results.

    Signal scoring priority (1-10):
    - Orchestration mentions: 9
    - Job description details: 9
    - Hiring signals: 8
    - Case studies/vendor mentions: 7
    - Engineering blog posts: 6
    - Product announcements: 5
    - Recent news: 4
    - Company research: 3
    """
    signals = []
    filtered_count = 0
    filter_reasons = {}

    # Define score by source
    source_scores = {
        'orchestration': 9,
        'job_descriptions': 9,
        'hiring': 8,
        'case_studies': 7,
        'blog_posts': 6,
        'product_announcements': 5,
        'news': 4,
        'company_research': 3,
        'website_crawl': 3
    }

    # Extract from each search type
    for search_type, result in search_results.items():
        if result.get('status') != 'success':
            continue

        score = source_scores.get(search_type, 3)

        # Handle different result structures
        if search_type == 'job_descriptions':
            # Job descriptions is a list of crawl results
            for job_result in result.get('data', []):
                if isinstance(job_result, dict) and job_result.get('status') == 'success':
                    job_data = job_result.get('data', {})
                    for item in job_data.get('results', []):
                        text = item.get('text', '')[:300]
                        url = item.get('url', '')

                        if text:
                            # VALIDATION: Check if signal is valid
                            is_valid, reason = _is_signal_valid(text, url, company_name)
                            if is_valid:
                                signals.append({
                                    'signal': text,
                                    'source': 'job_description',
                                    'url': url,
                                    'date': None,
                                    'score': 9,
                                    'category': 'hiring_evidence',
                                    'verified': True
                                })
                            else:
                                filtered_count += 1
                                filter_reasons[reason] = filter_reasons.get(reason, 0) + 1

        elif search_type in ['website_crawl']:
            # Content crawl results (always valid - from company domain)
            data = result.get('data', {})
            for item in data.get('results', []):
                text = item.get('text', '')[:300]
                url = item.get('url', '')

                if text and len(text) > 50:  # Basic length check
                    signals.append({
                        'signal': text,
                        'source': search_type,
                        'url': url,
                        'date': None,
                        'score': score,
                        'category': 'company_info',
                        'verified': True  # Website crawl is always verified
                    })
        else:
            # Search results with highlights
            data = result.get('data', {})
            for item in data.get('results', []):
                highlights = item.get('highlights', [])
                url = item.get('url', '')
                published_date = item.get('publishedDate')

                for highlight in highlights[:2]:  # Top 2 highlights per result
                    if highlight and len(highlight) > 20:
                        # VALIDATION: Check if signal is valid
                        is_valid, reason = _is_signal_valid(highlight, url, company_name)

                        if is_valid:
                            signals.append({
                                'signal': highlight[:300],
                                'source': search_type,
                                'url': url,
                                'date': published_date,
                                'score': score,
                                'category': _categorize_signal(search_type, highlight),
                                'verified': True
                            })
                        else:
                            filtered_count += 1
                            filter_reasons[reason] = filter_reasons.get(reason, 0) + 1

    # Sort by score descending, then by date (most recent first)
    signals.sort(key=lambda s: (s['score'], s['date'] or ''), reverse=True)

    # Log data quality metrics
    if filtered_count > 0:
        print(f"    [Validation] Filtered {filtered_count} irrelevant signals:")
        for reason, count in sorted(filter_reasons.items(), key=lambda x: x[1], reverse=True):
            print(f"      - {reason}: {count}")

    verified_signals = [s for s in signals if s.get('verified', False)]
    print(f"    [Quality] {len(verified_signals)} verified signals, {filtered_count} filtered")

    return signals[:20]  # Top 20 signals

def _categorize_signal(search_type: str, text: str) -> str:
    """Categorize signal based on search type and content"""
    text_lower = text.lower()

    if 'airflow' in text_lower or 'dagster' in text_lower or 'prefect' in text_lower:
        return 'orchestration_evidence'
    elif search_type == 'hiring':
        return 'hiring_evidence'
    elif search_type == 'case_studies':
        return 'vendor_relationship'
    elif search_type == 'blog_posts':
        return 'engineering_culture'
    elif search_type == 'product_announcements':
        return 'product_news'
    elif search_type == 'news':
        return 'corporate_news'
    else:
        return 'general'

def _aggregate_tech_stack(validated_signals: List[Dict]) -> List[Dict]:
    """
    Extract and deduplicate technology mentions with confidence scores.
    NOW ONLY USES VALIDATED SIGNALS - no garbage data.

    Source reliability (0.0-1.0):
    - Job descriptions: 1.0
    - Orchestration search: 0.9
    - Engineering blog: 0.8
    - Case studies: 0.8
    - Hiring search: 0.7
    - Website crawl: 0.6
    - Company research: 0.5
    - Product announcements: 0.4
    - News: 0.3
    """

    # Tech catalog by category
    TECH_CATALOG = {
        'orchestration': ['airflow', 'apache airflow', 'dagster', 'prefect', 'mage', 'kestra', 'temporal', 'argo workflows'],
        'data_warehouse': ['snowflake', 'databricks', 'redshift', 'bigquery', 'synapse'],
        'etl': ['fivetran', 'stitch', 'airbyte', 'dbt', 'matillion'],
        'cloud': ['aws', 'amazon web services', 'gcp', 'google cloud', 'azure', 'microsoft azure'],
        'streaming': ['kafka', 'apache kafka', 'kinesis', 'pubsub', 'confluent'],
        'containerization': ['kubernetes', 'k8s', 'docker', 'eks', 'gke', 'aks'],
        'programming': ['python', 'scala', 'java', 'spark', 'pyspark', 'sql'],
        'monitoring': ['datadog', 'prometheus', 'grafana', 'splunk']
    }

    # Source weights
    source_weights = {
        'job_description': 1.0,
        'orchestration': 0.9,
        'blog_posts': 0.8,
        'case_studies': 0.8,
        'hiring': 0.7,
        'website_crawl': 0.6,
        'company_research': 0.5,
        'product_announcements': 0.4,
        'news': 0.3
    }

    # Track mentions: {tech: {category, sources, weighted_count}}
    tech_mentions = {}

    # Scan ONLY validated signals
    for signal in validated_signals:
        signal_text = signal.get('signal', '')
        source_type = signal.get('source', 'unknown')
        weight = source_weights.get(source_type, 0.3)

        signal_text_lower = signal_text.lower()

        # Match against tech catalog
        for category, techs in TECH_CATALOG.items():
            for tech in techs:
                if tech.lower() in signal_text_lower:
                    # Count occurrences
                    count = signal_text_lower.count(tech.lower())
                    weighted_count = count * weight

                    if tech not in tech_mentions:
                        tech_mentions[tech] = {
                            'category': category,
                            'sources': [],
                            'weighted_count': 0,
                            'mention_count': 0
                        }

                    if source_type not in tech_mentions[tech]['sources']:
                        tech_mentions[tech]['sources'].append(source_type)
                    tech_mentions[tech]['weighted_count'] += weighted_count
                    tech_mentions[tech]['mention_count'] += count

    # Convert to list with confidence
    tech_stack = []
    for tech, data in tech_mentions.items():
        # Calculate confidence based on weighted count
        if data['weighted_count'] >= 1.5:
            confidence = 'high'
        elif data['weighted_count'] >= 0.8:
            confidence = 'medium'
        else:
            confidence = 'low'

        tech_stack.append({
            'technology': tech,
            'category': data['category'],
            'confidence': confidence,
            'sources': list(set(data['sources'])),  # Dedupe sources
            'mention_count': data['mention_count']
        })

    # Sort by weighted count descending
    tech_stack.sort(key=lambda t: tech_mentions[t['technology']]['weighted_count'], reverse=True)

    return tech_stack

# Helper functions for metadata counting

def _count_orchestration_mentions(search_results: Dict) -> int:
    """Count orchestration tool mentions across all searches"""
    count = 0
    orchestration_tools = ['airflow', 'dagster', 'prefect', 'mage', 'kestra']

    for result in search_results.values():
        if result.get('status') != 'success':
            continue

        data = result.get('data', {})
        all_text = ''

        # Handle different result structures
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and item.get('status') == 'success':
                    for res in item.get('data', {}).get('results', []):
                        all_text += ' ' + res.get('text', '')
        else:
            for item in data.get('results', []):
                all_text += ' ' + ' '.join(item.get('highlights', []))

        all_text_lower = all_text.lower()
        for tool in orchestration_tools:
            count += all_text_lower.count(tool)

    return count

def _count_hiring_signals(search_results: Dict) -> int:
    """Count hiring-related results"""
    hiring_result = search_results.get('hiring', {})
    if hiring_result.get('status') == 'success':
        return len(hiring_result.get('data', {}).get('results', []))
    return 0

def _count_blog_posts(search_results: Dict) -> int:
    """Count blog post results"""
    blog_result = search_results.get('blog_posts', {})
    if blog_result.get('status') == 'success':
        return len(blog_result.get('data', {}).get('results', []))
    return 0

def _count_product_announcements(search_results: Dict) -> int:
    """Count product announcement results"""
    product_result = search_results.get('product_announcements', {})
    if product_result.get('status') == 'success':
        return len(product_result.get('data', {}).get('results', []))
    return 0

def _count_case_studies(search_results: Dict) -> int:
    """Count case study results"""
    case_result = search_results.get('case_studies', {})
    if case_result.get('status') == 'success':
        return len(case_result.get('data', {}).get('results', []))
    return 0

# Exa v2: Main comprehensive research function

def fetch_exa_research_v2(
    company_name: str,
    domain: Optional[str] = None,
    rate_limiter: Optional[RateLimiter] = None,
    config: Optional[ExaSearchConfig] = None,
    circuit_breaker: Optional[CircuitBreaker] = None
) -> ExaResearchResult:
    """
    Execute comprehensive 9-search Exa research pattern.
    Falls back to Brave Search if EXA_API_KEY not configured.

    Returns ExaResearchResult with:
    - Top 20 structured signals with metadata
    - Enriched tech stack with confidence scores
    - Full search results per type
    - Timing and completion metadata
    """
    if not EXA_API_KEY and not BRAVE_API_KEY:
        return ExaResearchResult(
            status='failed',
            key_signals=[],
            tech_stack=[],
            search_results={},
            metadata={'error': 'Neither EXA_API_KEY nor BRAVE_API_KEY configured'}
        )

    # Initialize config and rate limiter
    config = config or ExaSearchConfig()
    rate_limiter = rate_limiter or RateLimiter(rate_per_minute=60, burst=15)
    circuit_breaker = circuit_breaker or CircuitBreaker(failure_threshold=5, timeout=60)

    start_time = time.time()
    search_results = {}

    # BATCH A: 5 parallel searches (core research)
    log(f"[{company_name}] Batch A: Running 5 core searches...")
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(_search_company_research, company_name, config, rate_limiter, circuit_breaker): 'company_research',
            executor.submit(_search_orchestration, company_name, config, rate_limiter, circuit_breaker): 'orchestration',
            executor.submit(_search_hiring, company_name, config, rate_limiter, circuit_breaker): 'hiring',
            executor.submit(_search_news, company_name, config, rate_limiter, circuit_breaker): 'news',
            executor.submit(_search_blog_posts, company_name, config, rate_limiter, circuit_breaker): 'blog_posts',
        }

        for future in as_completed(futures):
            search_type = futures[future]
            try:
                search_results[search_type] = future.result()
            except Exception as e:
                search_results[search_type] = {'status': 'error', 'error': str(e)}

    # BATCH B: 2 parallel searches (supplementary)
    log(f"[{company_name}] Batch B: Running 2 supplementary searches...")
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(_search_product_announcements, company_name, config, rate_limiter, circuit_breaker): 'product_announcements',
            executor.submit(_search_case_studies, company_name, config, rate_limiter, circuit_breaker): 'case_studies',
        }

        for future in as_completed(futures):
            search_type = futures[future]
            try:
                search_results[search_type] = future.result()
            except Exception as e:
                search_results[search_type] = {'status': 'error', 'error': str(e)}

    # BATCH C: Conditional searches (website + job descriptions)
    conditional_futures = {}

    if domain and config.enable_website_crawl:
        log(f"[{company_name}] Batch C: Crawling website {domain}...")
        search_results['website_crawl'] = _crawl_website(domain, config, rate_limiter, circuit_breaker)

    if config.enable_job_crawl and search_results.get('hiring', {}).get('status') == 'success':
        job_urls = _extract_job_urls_from_hiring_results(
            search_results['hiring'],
            max_urls=config.max_job_descriptions
        )

        if job_urls:
            log(f"[{company_name}] Batch C: Crawling {len(job_urls)} job descriptions...")
            with ThreadPoolExecutor(max_workers=len(job_urls)) as executor:
                job_futures = {
                    executor.submit(_crawl_job_description, url, config, rate_limiter, circuit_breaker): url
                    for url in job_urls
                }

                job_crawls = []
                for future in as_completed(job_futures):
                    try:
                        job_crawls.append(future.result())
                    except Exception as e:
                        job_crawls.append({'status': 'error', 'error': str(e)})

                search_results['job_descriptions'] = {
                    'status': 'success',
                    'data': job_crawls
                }

    # Aggregate results
    log(f"[{company_name}] Aggregating signals and tech stack...")
    key_signals = _aggregate_signals(search_results, company_name)
    tech_stack = _aggregate_tech_stack(key_signals)  # Use validated signals only

    # Build metadata
    elapsed = time.time() - start_time
    searches_completed = sum(
        1 for r in search_results.values()
        if isinstance(r, dict) and r.get('status') == 'success'
    )
    searches_failed = len(search_results) - searches_completed

    metadata = {
        'total_time_sec': round(elapsed, 2),
        'searches_completed': searches_completed,
        'searches_failed': searches_failed,
        'orchestration_mentions': _count_orchestration_mentions(search_results),
        'hiring_signals_count': _count_hiring_signals(search_results),
        'blog_post_count': _count_blog_posts(search_results),
        'product_announcement_count': _count_product_announcements(search_results),
        'case_study_count': _count_case_studies(search_results),
        'website_crawled': 'website_crawl' in search_results and search_results['website_crawl'].get('status') == 'success',
        'job_descriptions_crawled': len(search_results.get('job_descriptions', []))
    }

    # Determine overall status
    if searches_completed >= 7:
        status = 'success'
    elif searches_completed >= 4:
        status = 'partial'
    else:
        status = 'failed'

    log(f"[{company_name}] ✓ Research complete: {searches_completed}/9 searches successful ({elapsed:.1f}s)")

    return ExaResearchResult(
        status=status,
        key_signals=key_signals,
        tech_stack=tech_stack,
        search_results=search_results,
        metadata=metadata
    )

# Exa v1: Legacy single-query function (backward compatibility)

def fetch_exa_research(company_name: str, domain: str = None) -> dict:
    """
    Fetch web research from Exa AI.
    Returns: {status, key_signals, tech_stack, summary}
    """
    if not EXA_API_KEY:
        return {
            'status': 'skipped',
            'key_signals': [],
            'tech_stack': [],
            'summary': 'Exa API key not configured'
        }

    try:
        # Search query
        query = f"{company_name} company news product launches funding technology stack"

        headers = {
            "x-api-key": EXA_API_KEY,
            "Content-Type": "application/json"
        }

        payload = {
            "query": query,
            "numResults": 5,
            "type": "auto",
            "contents": {
                "highlights": True
            }
        }

        response = requests.post(
            "https://api.exa.ai/search",
            headers=headers,
            json=payload,
            timeout=15
        )

        if response.status_code != 200:
            return {
                'status': 'failed',
                'key_signals': [],
                'tech_stack': [],
                'summary': f'Exa API error: {response.status_code}'
            }

        data = response.json()
        results = data.get('results', [])

        # Extract signals from highlights
        signals = []
        tech_stack = []

        for result in results[:3]:
            highlights = result.get('highlights', [])
            for highlight in highlights[:2]:
                if highlight and len(highlight) > 20:
                    signals.append(highlight[:200])  # Truncate long highlights

        # Simple tech stack detection from text
        all_text = ' '.join([h for r in results for h in r.get('highlights', [])])
        tech_keywords = ['Snowflake', 'dbt', 'Airflow', 'Kubernetes', 'AWS', 'GCP', 'Azure', 'Python', 'React', 'PostgreSQL']
        for tech in tech_keywords:
            if tech.lower() in all_text.lower():
                tech_stack.append(tech)

        return {
            'status': 'success',
            'key_signals': signals[:5],  # Top 5 signals
            'tech_stack': list(set(tech_stack)),  # Dedupe
            'summary': f"Found {len(results)} web results"
        }

    except Exception as e:
        return {
            'status': 'failed',
            'key_signals': [],
            'tech_stack': [],
            'summary': f'Exa error: {str(e)}'
        }

# --- Comprehensive Report Generation ---

def generate_comprehensive_report(
    account_name: str,
    snowflake_context: Dict[str, Any],
    exa_metadata: Dict[str, Any],
    key_signals: List[str],
    tech_stack: List[str]
) -> Optional[str]:
    """
    Generate i360-style comprehensive research report using Claude API.

    Returns markdown report or None if generation fails.
    """
    if not ANTHROPIC_API_KEY:
        log(f"[{account_name}] Skipping report generation - ANTHROPIC_API_KEY not set")
        return None

    try:
        # Build prompt with all research data
        prompt = f"""Generate a comprehensive account research report following the i360 style.

**Account Name**: {account_name}

**Snowflake CRM Context**:
- Tier: {snowflake_context.get('tier')}
- Contacts: {snowflake_context.get('contact_count', 0)}
- MQLs: {snowflake_context.get('mql_count', 0)}
- Opportunities: {snowflake_context.get('opp_count', 0)}
- Gong Calls: {snowflake_context.get('call_count', 0)}

**Exa Web Research Metadata**:
- Orchestration mentions: {exa_metadata.get('orchestration_mentions', 0)}
- Hiring signals: {exa_metadata.get('hiring_signals_count', 0)}
- Blog posts found: {exa_metadata.get('blog_post_count', 0)}
- Product announcements: {exa_metadata.get('product_announcement_count', 0)}
- Case studies: {exa_metadata.get('case_study_count', 0)}
- Website crawled: {exa_metadata.get('website_crawled', False)}

**Key Signals from Web Research**:
{chr(10).join(f'- {signal}' for signal in key_signals[:10])}

**Tech Stack Detected**:
{', '.join(tech_stack[:15])}

---

Generate a comprehensive research report with these sections:

1. **Company Overview** - Company description, founded, headquarters, key metrics if found, leadership
2. **Airflow Mission Critical Assessment** - Score (A/B/C/D), criticality level, evidence-based analysis
3. **Recent News & Corporate Strategy** - Product updates, market position, strategic priorities
4. **Data Orchestration & Hiring Intelligence** - Confirmed tech stack, Airflow evidence, workforce insights
5. **Pain Points & Customer Challenges** - Industry challenges the company addresses
6. **Competitive Intelligence** - Market positioning and differentiation
7. **Web Presence & Growth Metrics** - Known metrics and engagement indicators
8. **Product Suite Overview** - Core products and features
9. **Summary & Outlook** - Key takeaways and 2026 outlook

Use **(VERIFIED)** markers for facts directly from research. Use **(ASSESSED)** for analytical conclusions.

Keep the tone professional and analytical. Focus on evidence-based insights relevant to Astronomer's sales team.

Generate the report now as markdown."""

        # Call Claude API
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            temperature=0.3,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        # Extract text from response
        report_text = message.content[0].text if message.content else None

        if report_text:
            log(f"[{account_name}] ✓ Generated comprehensive report ({len(report_text):,} chars)")
            return report_text
        else:
            log(f"[{account_name}] ⚠️  Report generation returned empty")
            return None

    except Exception as e:
        log(f"[{account_name}] ⚠️  Report generation failed: {e}")
        return None

# --- Classification ---

def classify_account(engagement_data: dict, sf_context: Optional[dict]) -> tuple:
    """
    Classify account into tier and priority score.
    Returns: (tier, priority_score)
    """
    is_customer = engagement_data.get('is_current_cust', False)
    mql_count = engagement_data.get('mql_count', 0)
    call_count = engagement_data.get('call_count', 0)
    opp_count = engagement_data.get('opp_count', 0)
    latest_mql = engagement_data.get('latest_mql_date')

    # Check for active deals
    active_deal = False
    if sf_context and opp_count > 0:
        opps = sf_context.get('opps_by_acct', {}).get(engagement_data['acct_id'], [])
        active_deal = any(opp.stage in ["Stage 3", "Stage 4", "Stage 5"] for opp in opps)

    # Classification logic
    if is_customer:
        return ("customer", 10)
    elif active_deal:
        return ("active_deal", 9)
    elif call_count > 0 or opp_count > 0:
        return ("engaged_prospect", 7)
    elif latest_mql:
        # Handle both timezone-aware and naive datetimes
        try:
            if latest_mql.tzinfo is not None:
                cutoff = datetime.now(timezone.utc) - timedelta(days=30)
            else:
                cutoff = datetime.now() - timedelta(days=30)

            if latest_mql > cutoff:
                return ("hot_mql", 8)
        except:
            pass
        return ("warm_mql", 5)
    elif mql_count > 0:
        return ("warm_mql", 5)
    elif engagement_data.get('contact_count', 0) > 0:
        return ("known_prospect", 3)
    else:
        return ("cold_prospect", 1)

# --- Research Single Account ---

def research_single_account(
    account_name: str,
    engagement_data: Optional[dict],
    sf_context: Optional[dict],
    rate_limiter: Optional[RateLimiter] = None,
    exa_config: Optional[ExaSearchConfig] = None,
    circuit_breaker: Optional[CircuitBreaker] = None,
    batch_tag: Optional[str] = None
) -> ResearchResult:
    """
    Phase 3: Research single account with web + conditional Snowflake enrichment.
    """
    start_time = time.time()

    try:
        # Extract domain for website crawl
        domain = None
        if engagement_data:
            # Try to extract from contacts or account data
            contacts = sf_context.get('contacts_by_acct', {}).get(engagement_data.get('acct_id'), []) if sf_context else []
            if contacts:
                domain = contacts[0].primary_domain

        # Web research v2 (ALWAYS run) - comprehensive 9-search pattern
        exa_v2_result = fetch_exa_research_v2(
            company_name=account_name,
            domain=domain,
            rate_limiter=rate_limiter,
            config=exa_config,
            circuit_breaker=circuit_breaker
        )

        # Convert v2 result to legacy format for report compatibility
        exa_result = exa_v2_result.to_legacy_format()

        # Classify account
        has_sf_context = engagement_data is not None and engagement_data.get('has_engagement', False)

        # Extract transcripts from sf_context if available
        transcripts = []
        if engagement_data and sf_context:
            acct_id_for_lookup = engagement_data.get('acct_id')
            if acct_id_for_lookup and 'transcripts_by_acct' in sf_context:
                transcripts = sf_context['transcripts_by_acct'].get(acct_id_for_lookup, [])

        # Extract emails from sf_context if available
        emails = []
        if engagement_data and sf_context:
            acct_id_for_lookup = engagement_data.get('acct_id')
            if acct_id_for_lookup and 'emails_by_acct' in sf_context:
                emails = sf_context['emails_by_acct'].get(acct_id_for_lookup, [])

        if engagement_data:
            tier, priority = classify_account(engagement_data, sf_context)
            acct_id = engagement_data.get('acct_id')
            contact_count = engagement_data.get('contact_count', 0)
            mql_count = engagement_data.get('mql_count', 0)
            opp_count = engagement_data.get('opp_count', 0)
            call_count = engagement_data.get('call_count', 0)
            latest_mql = engagement_data.get('latest_mql_date')
            latest_call = engagement_data.get('latest_call_date')
        else:
            # Account not found in Snowflake
            tier, priority = ("cold_prospect", 1)
            acct_id = None
            contact_count = mql_count = opp_count = call_count = 0
            latest_mql = latest_call = None

        # Save JSON report
        date_str = datetime.now().strftime('%Y-%m-%d')
        slug = slugify(account_name)
        report_dir = OUTPUT_DIR / date_str / slug
        report_dir.mkdir(parents=True, exist_ok=True)

        # Format transcripts for JSON output
        transcripts_json = []
        for t in transcripts:
            transcripts_json.append({
                'call_id': t.call_id,
                'call_title': t.call_title,
                'scheduled_ts': t.scheduled_ts.isoformat() if t.scheduled_ts else None,
                'attendees': t.attendees,
                'full_transcript': t.full_transcript
            })

        report_data = {
            'account_name': account_name,
            'acct_id': acct_id,
            'tier': tier,
            'priority_score': priority,
            'has_sf_context': has_sf_context,
            'counts': {
                'contacts': contact_count,
                'mqls': mql_count,
                'opportunities': opp_count,
                'calls': call_count,
                'emails': len(emails)
            },
            'transcripts': transcripts_json,
            'emails': emails,
            'web_research': exa_result,
            'generated_at': datetime.now().isoformat()
        }

        json_path = report_dir / "raw_data.json"
        with open(json_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)

        # Create markdown report
        md_path = report_dir / "report.md"
        with open(md_path, 'w') as f:
            f.write(f"# {account_name} - Account Research\\n\\n")
            f.write(f"**Tier:** {tier}\\n")
            f.write(f"**Priority Score:** {priority}/10\\n")
            f.write(f"**Snowflake Context:** {'Yes' if has_sf_context else 'No'}\\n\\n")

            if has_sf_context:
                f.write(f"## CRM Summary\\n\\n")
                f.write(f"- **Contacts:** {contact_count}\\n")
                f.write(f"- **MQLs:** {mql_count}\\n")
                f.write(f"- **Opportunities:** {opp_count}\\n")
                f.write(f"- **Gong Calls:** {call_count}\\n")
                f.write(f"- **Emails:** {len(emails)}\\n\\n")

                # Add transcripts if available
                if transcripts:
                    f.write(f"## Gong Call Transcripts\\n\\n")
                    for t in transcripts:
                        f.write(f"### {t.call_title}\\n\\n")
                        f.write(f"- **Date:** {t.scheduled_ts.strftime('%Y-%m-%d %H:%M') if t.scheduled_ts else 'N/A'}\\n")
                        f.write(f"- **Attendees:** {t.attendees}\\n")
                        f.write(f"- **Call ID:** {t.call_id}\\n\\n")
                        if t.full_transcript:
                            # Truncate very long transcripts in markdown
                            transcript_preview = t.full_transcript[:2000] + "..." if len(t.full_transcript) > 2000 else t.full_transcript
                            f.write(f"**Transcript:**\\n\\n{transcript_preview}\\n\\n")
                        f.write(f"---\\n\\n")

                # Add emails if available
                if emails:
                    f.write(f"## Email Correspondence\\n\\n")
                    for e in emails[:20]:  # Show up to 20 most recent emails
                        date_str = e.get('date', 'N/A')
                        if date_str != 'N/A':
                            date_str = date_str[:10]  # Just the date part (YYYY-MM-DD)
                        subject = e.get('subject', '(no subject)')
                        preview = e.get('preview', '')
                        f.write(f"### {date_str} - {subject}\\n\\n")
                        if preview:
                            f.write(f"{preview}\\n\\n")
                        f.write(f"---\\n\\n")

            f.write(f"## Web Research Signals\\n\\n")
            for signal in exa_result['key_signals']:
                f.write(f"- {signal}\\n")

            if exa_result['tech_stack']:
                f.write(f"\\n## Tech Stack\\n\\n")
                f.write(f"{', '.join(exa_result['tech_stack'])}\\n")

        # Generate comprehensive i360-style report (skip if no API key)
        comprehensive_report = None
        if ANTHROPIC_API_KEY:
            log(f"[{account_name}] Generating comprehensive report...")
            comprehensive_report = generate_comprehensive_report(
                account_name=account_name,
                snowflake_context={
                    'tier': tier,
                    'contact_count': contact_count,
                    'mql_count': mql_count,
                    'opp_count': opp_count,
                    'call_count': call_count
                },
                exa_metadata=exa_v2_result.metadata,
                key_signals=exa_result['key_signals'],
                tech_stack=exa_result['tech_stack']
            )
        else:
            log(f"[{account_name}] Skipping report generation (ANTHROPIC_API_KEY not set)")

        elapsed = time.time() - start_time

        # Serialize v2 structured data to JSON strings
        structured_signals_json = json.dumps(exa_v2_result.key_signals) if exa_v2_result.key_signals else None
        structured_tech_stack_json = json.dumps(exa_v2_result.tech_stack) if exa_v2_result.tech_stack else None

        return ResearchResult(
            acct_id=acct_id,
            acct_name=account_name,
            tier=tier,
            priority_score=priority,
            has_sf_context=has_sf_context,
            contact_count=contact_count,
            mql_count=mql_count,
            opp_count=opp_count,
            call_count=call_count,
            latest_mql_date=latest_mql,
            latest_call_date=latest_call,
            key_signals=exa_result['key_signals'],
            tech_stack=exa_result['tech_stack'],
            report_json_path=str(json_path),
            processing_time_sec=elapsed,
            status='success',
            exa_metadata=exa_v2_result.metadata,  # v2: Enhanced metadata
            comprehensive_report=comprehensive_report,  # v2: i360-style report
            structured_signals=structured_signals_json,  # v2: Full structured signals
            structured_tech_stack=structured_tech_stack_json,  # v2: Full tech stack with confidence
            batch_tag=batch_tag  # Tag for this research batch
        )

    except Exception as e:
        elapsed = time.time() - start_time
        log(f"ERROR researching {account_name}: {e}")
        return ResearchResult(
            acct_id=None,
            acct_name=account_name,
            tier='cold_prospect',
            priority_score=0,
            has_sf_context=False,
            contact_count=0,
            mql_count=0,
            opp_count=0,
            call_count=0,
            latest_mql_date=None,
            latest_call_date=None,
            key_signals=[],
            tech_stack=[],
            report_json_path='',
            processing_time_sec=elapsed,
            status='failed',
            error_message=str(e),
            exa_metadata=None,
            comprehensive_report=None,
            structured_signals=None,
            structured_tech_stack=None,
            batch_tag=batch_tag
        )

# --- Save to Snowflake ---

def save_to_snowflake(results: List[ResearchResult]):
    """Save research results to Snowflake table"""
    if not results:
        return

    log(f"Saving {len(results)} results to Snowflake...")

    # Get private key
    with open(Path.home() / ".ssh/rsa_key_unencrypted.p8", 'rb') as key_file:
        p_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )

    private_key_bytes = p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    conn = snowflake.connector.connect(
        account='GP21411.us-east-1',
        user='VISHWASRINIVASAN',
        private_key=private_key_bytes,
        role='GTMADMIN',
        warehouse='HUMANS',
        database='GTM',
        schema='PUBLIC'
    )
    cursor = conn.cursor()

    for result in results:
        try:
            # Convert arrays to JSON strings
            import json
            key_signals_json = json.dumps(result.key_signals)
            tech_stack_json = json.dumps(result.tech_stack)

            # Extract v2 metadata if available
            exa_metadata = getattr(result, 'exa_metadata', None) or {}
            comprehensive_report = getattr(result, 'comprehensive_report', None)
            structured_signals = getattr(result, 'structured_signals', None)
            structured_tech_stack = getattr(result, 'structured_tech_stack', None)

            # Extract emails from the JSON file
            email_correspondence_json = None
            if result.report_json_path and Path(result.report_json_path).exists():
                try:
                    with open(result.report_json_path, 'r') as f:
                        report_data = json.load(f)
                        emails = report_data.get('emails', [])
                        if emails:
                            email_correspondence_json = json.dumps(emails)
                except Exception as e:
                    log(f"Warning: Could not read emails from {result.report_json_path}: {e}")

            # MERGE on acct_name to avoid duplicate rows on re-runs
            cursor.execute('''
            MERGE INTO ACCOUNT_RESEARCH_OUTPUT tgt
            USING (
                SELECT
                    %s AS acct_id, %s AS acct_name, %s AS tier, %s AS priority_score,
                    %s AS has_sf_context, %s AS contact_count, %s AS mql_count,
                    %s AS opp_count, %s AS call_count,
                    %s AS latest_mql_date, %s AS latest_call_date,
                    PARSE_JSON(%s) AS key_signals, PARSE_JSON(%s) AS tech_stack,
                    %s AS report_json_path,
                    %s AS processing_time_sec, %s AS status, %s AS error_message,
                    %s AS orchestration_mentions, %s AS hiring_signals_count,
                    %s AS blog_post_count, %s AS product_announcement_count,
                    %s AS case_study_count, %s AS website_crawled,
                    %s AS job_descriptions_crawled,
                    %s AS exa_search_time_sec, %s AS exa_searches_completed,
                    %s AS exa_searches_failed,
                    %s AS comprehensive_report,
                    %s AS structured_signals, %s AS structured_tech_stack,
                    %s AS email_correspondence,
                    %s AS batch_tag
            ) src ON tgt.acct_name = src.acct_name
            WHEN MATCHED THEN UPDATE SET
                acct_id = src.acct_id, tier = src.tier,
                priority_score = src.priority_score,
                has_sf_context = src.has_sf_context,
                contact_count = src.contact_count, mql_count = src.mql_count,
                opp_count = src.opp_count, call_count = src.call_count,
                latest_mql_date = src.latest_mql_date,
                latest_call_date = src.latest_call_date,
                key_signals = src.key_signals, tech_stack = src.tech_stack,
                report_json_path = src.report_json_path,
                processing_time_sec = src.processing_time_sec,
                status = src.status, error_message = src.error_message,
                orchestration_mentions = src.orchestration_mentions,
                hiring_signals_count = src.hiring_signals_count,
                blog_post_count = src.blog_post_count,
                product_announcement_count = src.product_announcement_count,
                case_study_count = src.case_study_count,
                website_crawled = src.website_crawled,
                job_descriptions_crawled = src.job_descriptions_crawled,
                exa_search_time_sec = src.exa_search_time_sec,
                exa_searches_completed = src.exa_searches_completed,
                exa_searches_failed = src.exa_searches_failed,
                comprehensive_report = src.comprehensive_report,
                structured_signals = src.structured_signals,
                structured_tech_stack = src.structured_tech_stack,
                email_correspondence = src.email_correspondence,
                batch_tag = src.batch_tag
            WHEN NOT MATCHED THEN INSERT (
                acct_id, acct_name, tier, priority_score,
                has_sf_context, contact_count, mql_count, opp_count, call_count,
                latest_mql_date, latest_call_date,
                key_signals, tech_stack, report_json_path,
                processing_time_sec, status, error_message,
                orchestration_mentions, hiring_signals_count, blog_post_count,
                product_announcement_count, case_study_count,
                website_crawled, job_descriptions_crawled,
                exa_search_time_sec, exa_searches_completed, exa_searches_failed,
                comprehensive_report, structured_signals, structured_tech_stack,
                email_correspondence, batch_tag
            ) VALUES (
                src.acct_id, src.acct_name, src.tier, src.priority_score,
                src.has_sf_context, src.contact_count, src.mql_count,
                src.opp_count, src.call_count,
                src.latest_mql_date, src.latest_call_date,
                src.key_signals, src.tech_stack, src.report_json_path,
                src.processing_time_sec, src.status, src.error_message,
                src.orchestration_mentions, src.hiring_signals_count,
                src.blog_post_count, src.product_announcement_count,
                src.case_study_count, src.website_crawled,
                src.job_descriptions_crawled,
                src.exa_search_time_sec, src.exa_searches_completed,
                src.exa_searches_failed,
                src.comprehensive_report, src.structured_signals,
                src.structured_tech_stack,
                src.email_correspondence,
                src.batch_tag
            )
            ''', (
                result.acct_id, result.acct_name, result.tier, result.priority_score,
                result.has_sf_context, result.contact_count, result.mql_count,
                result.opp_count, result.call_count,
                result.latest_mql_date, result.latest_call_date,
                key_signals_json, tech_stack_json, result.report_json_path,
                result.processing_time_sec, result.status, result.error_message,
                exa_metadata.get('orchestration_mentions', 0),
                exa_metadata.get('hiring_signals_count', 0),
                exa_metadata.get('blog_post_count', 0),
                exa_metadata.get('product_announcement_count', 0),
                exa_metadata.get('case_study_count', 0),
                exa_metadata.get('website_crawled', False),
                exa_metadata.get('job_descriptions_crawled', 0),
                exa_metadata.get('total_time_sec', 0.0),
                exa_metadata.get('searches_completed', 0),
                exa_metadata.get('searches_failed', 0),
                comprehensive_report,
                structured_signals,
                structured_tech_stack,
                email_correspondence_json,
                result.batch_tag
            ))
            log(f"✓ Saved {result.acct_name} to Snowflake")
        except Exception as e:
            log(f"ERROR saving {result.acct_name} to Snowflake: {e}")

    conn.commit()
    cursor.close()
    conn.close()
    log(f"✅ Saved {len(results)} results to {SNOWFLAKE_TABLE}")

# --- Main Batch Research ---

def batch_research(account_list: List[str], batch_tag: Optional[str] = None) -> List[ResearchResult]:
    """
    Main entry point: Three-phase batch research with v2 comprehensive Exa.
    """
    log(f"Starting batch research for {len(account_list)} accounts...")
    if batch_tag:
        log(f"Batch tag: {batch_tag}")

    # Create shared rate limiter and config for entire batch
    # Circuit breaker is per-account so failures in one don't cascade to others
    rate_limiter = RateLimiter(rate_per_minute=60, burst=15)  # Conservative for free tier
    exa_config = ExaSearchConfig()

    # Phase 1: Bulk engagement check
    engagement_map = bulk_check_engagement(account_list)

    # Phase 2: Conditional Snowflake context (only for engaged accounts)
    engaged_acct_ids = [
        data['acct_id'] for data in engagement_map.values()
        if data.get('has_engagement', False)
    ]

    sf_context = bulk_fetch_snowflake_context(engaged_acct_ids) if engaged_acct_ids else {}

    # Phase 3: Parallel research (web for ALL accounts) with v2 comprehensive Exa
    log(f"Phase 3: Running comprehensive web research for {len(account_list)} accounts...")
    log(f"         Using 9-search pattern per account (orchestration, hiring, blog posts, etc.)")
    results = []

    with ThreadPoolExecutor(max_workers=3) as executor:  # Conservative: 3 accounts at a time
        futures = {}
        for account_name in account_list:
            # engagement_map is now keyed by user-provided name (lowercased)
            engagement_data = engagement_map.get(account_name.lower())

            futures[executor.submit(
                research_single_account,
                account_name,
                engagement_data,
                sf_context,
                rate_limiter,  # Shared across all accounts
                exa_config,
                CircuitBreaker(failure_threshold=5, timeout=60),  # Per-account isolation
                batch_tag  # Pass tag to each account
            )] = account_name

        for future in as_completed(futures):
            account_name = futures[future]
            try:
                result = future.result()
                results.append(result)
                log(f"[{result.acct_name}] {result.tier} - {result.status} ({result.processing_time_sec:.1f}s)")
            except Exception as e:
                log(f"ERROR: {account_name} - {e}")

    # Save results to Snowflake
    save_to_snowflake(results)

    log(f"\\n✅ Completed {len(results)}/{len(account_list)} accounts")
    if batch_tag:
        log(f"Query this batch: SELECT * FROM GTM.PUBLIC.ACCOUNT_RESEARCH_OUTPUT WHERE batch_tag = '{batch_tag}'")
    return results

# --- CLI ---

def main():
    parser = argparse.ArgumentParser(description="Batch Account Research")
    parser.add_argument('--accounts', type=str, help='Comma-separated list of account names')
    parser.add_argument('--accounts-file', type=str, help='File containing account names (one per line)')
    parser.add_argument('--tag', type=str, help='Optional tag to label this batch (e.g., "Q2_enterprise", "dreamforce_leads")')

    args = parser.parse_args()

    # Parse account list
    if args.accounts:
        account_list = [a.strip() for a in args.accounts.split(',')]
    elif args.accounts_file:
        with open(args.accounts_file, 'r') as f:
            account_list = [line.strip() for line in f if line.strip()]
    else:
        print("Error: Must provide --accounts or --accounts-file")
        sys.exit(1)

    # Run batch research
    results = batch_research(account_list, batch_tag=args.tag)

    # Summary
    print("\\n=== Summary ===")
    print(f"Total accounts: {len(account_list)}")
    print(f"Successful: {sum(1 for r in results if r.status == 'success')}")
    print(f"Failed: {sum(1 for r in results if r.status == 'failed')}")
    print(f"\\nOutput: {OUTPUT_DIR}/{datetime.now().strftime('%Y-%m-%d')}/")
    print(f"Snowflake: {SNOWFLAKE_TABLE}")

if __name__ == "__main__":
    main()
