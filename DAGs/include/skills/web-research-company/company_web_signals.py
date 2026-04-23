#!/usr/bin/env python3
"""
Company Web Signals Research Script
Fetches company overview, jobs, major announcements, product releases, C-suite hires,
strategic announcements, and company metrics using Exa API.
Stores results in GTM.PUBLIC.COMPANY_WEB_SIGNALS table in Snowflake.

Usage:
    python3 company_web_signals.py "Company Name" domain.com
    python3 company_web_signals.py companies.csv
"""

import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import requests
import snowflake.connector
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import yaml


class CompanyWebSignals:
    """Main class for company web research and Snowflake storage."""

    ORCHESTRATION_TOOLS = [
        'Apache Airflow', 'Airflow', 'Dagster', 'Prefect', 'Mage', 'Luigi'
    ]

    DATA_TOOLS = [
        'dbt', 'Dataform', 'Snowflake', 'Databricks', 'BigQuery', 'Redshift',
        'Fivetran', 'Airbyte', 'Stitch', 'Spark', 'Flink', 'Kafka',
        'Tableau', 'Looker', 'Power BI', 'AWS', 'GCP', 'Azure',
        'PostgreSQL', 'MySQL', 'MongoDB', 'S3', 'Glue'
    ]

    def __init__(self):
        """Initialize with Snowflake and Exa connections."""
        self.exa_api_key = os.getenv('EXA_API_KEY')
        if not self.exa_api_key:
            raise ValueError("EXA_API_KEY environment variable required")

        # Load Snowflake config from environment variables (for Astro deployment)
        # Falls back to YAML config file for local development
        if os.getenv('SNOWFLAKE_ACCOUNT'):
            # Running in Astro - use environment variables
            self.sf_config = {
                'account': os.getenv('SNOWFLAKE_ACCOUNT'),
                'user': os.getenv('SNOWFLAKE_USER'),
                'private_key_path': os.getenv('SNOWFLAKE_PRIVATE_KEY_PATH', '/usr/local/airflow/include/.ssh/rsa_key.p8'),
                'role': os.getenv('SNOWFLAKE_ROLE', 'GTMADMIN'),
                'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE', 'HUMANS'),
                'database': os.getenv('SNOWFLAKE_DATABASE', 'GTM')
            }
        else:
            # Running locally - use YAML config
            snowflake_config_path = Path.home() / ".snowflake/service_config.yaml"
            with open(snowflake_config_path) as f:
                config_data = yaml.safe_load(f)
                self.sf_config = config_data['snowflake']

        # Load private key
        private_key_path = Path(self.sf_config['private_key_path'])
        if str(private_key_path).startswith('~'):
            private_key_path = private_key_path.expanduser()
        with open(private_key_path, "rb") as key_file:
            p_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None,
                backend=default_backend()
            )

        self.private_key = p_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

    def get_snowflake_connection(self):
        """Create Snowflake connection."""
        return snowflake.connector.connect(
            account=self.sf_config['account'],
            user=self.sf_config['user'],
            private_key=self.private_key,
            role=self.sf_config['role'],
            warehouse=self.sf_config['warehouse'],
            database=self.sf_config['database']
        )

    def create_table_if_not_exists(self):
        """Create the COMPANY_WEB_SIGNALS table if it doesn't exist."""
        create_sql = """
        CREATE TABLE IF NOT EXISTS GTM.PUBLIC.COMPANY_WEB_SIGNALS (
            COMPANY_NAME VARCHAR(500),
            DOMAIN VARCHAR(500),
            RESEARCH_DATE TIMESTAMP_NTZ,
            COMPANY_OVERVIEW VARCHAR(16777216),
            JOBS VARIANT,
            MAJOR_ANNOUNCEMENTS VARIANT,
            PRODUCT_RELEASES VARIANT,
            C_SUITE_HIRES VARIANT,
            STRATEGIC_ANNOUNCEMENTS VARIANT,
            COMPANY_METRICS VARIANT
        )
        """

        try:
            conn = self.get_snowflake_connection()
            cursor = conn.cursor()
            cursor.execute(create_sql)
            conn.close()
            print(f"✓ Table GTM.PUBLIC.COMPANY_WEB_SIGNALS ready")
            return True
        except Exception as e:
            print(f"✗ Failed to create table: {e}")
            return False

    def _exa_search(self, query: str, num_results: int = 10,
                    start_published_date: Optional[str] = None) -> List[Dict]:
        """Execute Exa search via API."""
        url = "https://api.exa.ai/search"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.exa_api_key
        }

        payload = {
            "query": query,
            "numResults": num_results,
            "useAutoprompt": True,
            "type": "neural",
            "contents": {
                "text": {"maxCharacters": 1000}
            }
        }

        if start_published_date:
            payload["startPublishedDate"] = start_published_date

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get('results', [])
        except Exception as e:
            print(f"  ⚠ Exa search failed: {e}")
            return []

    def _extract_tools(self, text: str) -> Dict[str, List[str]]:
        """Extract orchestration and data tools from text."""
        text_lower = text.lower()

        orchestration = [t for t in self.ORCHESTRATION_TOOLS if t.lower() in text_lower]
        data_tools = [t for t in self.DATA_TOOLS if t.lower() in text_lower]

        return {
            "orchestration_tools": list(set(orchestration)),
            "data_tools": list(set(data_tools))
        }

    def _is_relevant(self, result: Dict, company_name: str, domain: str) -> bool:
        """Check if search result is relevant to the company."""
        text = (result.get('title', '') + ' ' + result.get('text', '') + ' ' +
                result.get('url', '')).lower()

        company_lower = company_name.lower()
        domain_parts = domain.replace('www.', '').split('.')[0].lower()

        return company_lower in text or domain_parts in text

    def research_company_overview(self, company_name: str, domain: str) -> str:
        """Research company overview."""
        print(f"  → Researching company overview...")

        about_results = self._exa_search(f"site:{domain} about OR company", num_results=3)
        desc_results = self._exa_search(
            f"{company_name} company overview industry",
            num_results=5,
            start_published_date=(datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
        )

        all_results = about_results + desc_results
        overview_text = "\n\n".join([
            f"{r.get('title', '')}\n{r.get('text', '')[:500]}"
            for r in all_results[:3]
        ])

        return overview_text if overview_text else "No overview found"

    def research_jobs(self, company_name: str, domain: str) -> List[Dict]:
        """Research job postings with tool extraction."""
        print(f"  → Researching job postings...")

        twelve_months_ago = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

        jobs_1 = self._exa_search(
            f"(site:greenhouse.io OR site:lever.co OR site:ashbyhq.com) {domain} "
            f"(data engineer OR data platform OR ML engineer OR analytics engineer)",
            num_results=10,
            start_published_date=twelve_months_ago
        )

        jobs_2 = self._exa_search(
            f"(site:greenhouse.io OR site:lever.co) {domain} (Airflow OR dagster OR prefect)",
            num_results=10,
            start_published_date=twelve_months_ago
        )

        jobs_3 = self._exa_search(
            f"site:linkedin.com/jobs {company_name} (data engineer OR Airflow)",
            num_results=10,
            start_published_date=twelve_months_ago
        )

        all_jobs = jobs_1 + jobs_2 + jobs_3
        seen_urls = set()
        unique_jobs = []

        for job in all_jobs:
            url = job.get('url', '')
            if url and url not in seen_urls and self._is_relevant(job, company_name, domain):
                seen_urls.add(url)
                full_text = job.get('title', '') + ' ' + job.get('text', '')
                tools = self._extract_tools(full_text)

                unique_jobs.append({
                    'title': job.get('title', ''),
                    'url': url,
                    'company': company_name,
                    'posted_date': job.get('publishedDate', ''),
                    'description': job.get('text', '')[:500],
                    'orchestration_tools': tools['orchestration_tools'],
                    'data_tools': tools['data_tools']
                })

        return unique_jobs[:20]

    def research_major_announcements(self, company_name: str, domain: str) -> List[Dict]:
        """Research major company announcements (acquisitions, expansions, major initiatives)."""
        print(f"  → Researching major announcements...")

        two_years_ago = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
        results = self._exa_search(
            f"{company_name} acquisition OR acquired OR expansion OR launches OR opens",
            num_results=15,
            start_published_date=two_years_ago
        )

        return [{
            'title': r.get('title', ''),
            'url': r.get('url', ''),
            'date': r.get('publishedDate', ''),
            'summary': r.get('text', '')[:1000]
        } for r in results if self._is_relevant(r, company_name, domain)]

    def research_product_releases(self, company_name: str, domain: str) -> List[Dict]:
        """Research product launches."""
        print(f"  → Researching product releases...")

        two_years_ago = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
        results = self._exa_search(
            f"{company_name} product launch OR release OR announces",
            num_results=15,
            start_published_date=two_years_ago
        )

        return [{
            'title': r.get('title', ''),
            'url': r.get('url', ''),
            'date': r.get('publishedDate', ''),
            'summary': r.get('text', '')[:1000]
        } for r in results if self._is_relevant(r, company_name, domain)]

    def research_c_suite_hires(self, company_name: str, domain: str) -> List[Dict]:
        """Research C-suite hires."""
        print(f"  → Researching C-suite hires...")

        two_years_ago = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
        results = self._exa_search(
            f"{company_name} (CEO OR CTO OR CFO) (hire OR appointed OR joins)",
            num_results=15,
            start_published_date=two_years_ago
        )

        return [{
            'title': r.get('title', ''),
            'url': r.get('url', ''),
            'date': r.get('publishedDate', ''),
            'summary': r.get('text', '')[:1000]
        } for r in results if self._is_relevant(r, company_name, domain)]

    def research_strategic_announcements(self, company_name: str, domain: str) -> List[Dict]:
        """Research strategic announcements."""
        print(f"  → Researching strategic announcements...")

        two_years_ago = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
        results = self._exa_search(
            f"{company_name} strategy OR partnership OR expansion",
            num_results=15,
            start_published_date=two_years_ago
        )

        return [{
            'title': r.get('title', ''),
            'url': r.get('url', ''),
            'date': r.get('publishedDate', ''),
            'summary': r.get('text', '')[:1000]
        } for r in results if self._is_relevant(r, company_name, domain)]

    def research_company_metrics(self, company_name: str, domain: str) -> List[Dict]:
        """Research company metrics (growth, funding, employee counts, public disclosures)."""
        print(f"  → Researching company metrics...")

        two_years_ago = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
        results = self._exa_search(
            f"{company_name} employees OR funding OR revenue OR growth OR valuation",
            num_results=10,
            start_published_date=two_years_ago
        )

        return [{
            'title': r.get('title', ''),
            'url': r.get('url', ''),
            'date': r.get('publishedDate', ''),
            'summary': r.get('text', '')[:1000]
        } for r in results if self._is_relevant(r, company_name, domain)]

    def research_company(self, company_name: str, domain: str) -> Optional[Dict]:
        """Execute full research for a company."""
        print(f"\n{'='*60}")
        print(f"Researching: {company_name} ({domain})")
        print(f"{'='*60}")

        try:
            overview = self.research_company_overview(company_name, domain)
            jobs = self.research_jobs(company_name, domain)
            major_announcements = self.research_major_announcements(company_name, domain)
            products = self.research_product_releases(company_name, domain)
            hires = self.research_c_suite_hires(company_name, domain)
            announcements = self.research_strategic_announcements(company_name, domain)
            metrics = self.research_company_metrics(company_name, domain)

            print(f"\n  ✓ Research complete:")
            print(f"    - Overview: {len(overview)} chars")
            print(f"    - Jobs: {len(jobs)} postings")
            print(f"    - Major announcements: {len(major_announcements)} found")
            print(f"    - Product releases: {len(products)} found")
            print(f"    - C-suite hires: {len(hires)} found")
            print(f"    - Strategic announcements: {len(announcements)} found")
            print(f"    - Company metrics: {len(metrics)} found")

            return {
                'company_name': company_name,
                'domain': domain,
                'research_date': datetime.now().isoformat(),
                'company_overview': overview,
                'jobs': jobs,
                'major_announcements': major_announcements,
                'product_releases': products,
                'c_suite_hires': hires,
                'strategic_announcements': announcements,
                'company_metrics': metrics
            }
        except Exception as e:
            print(f"\n  ✗ Failed to research {company_name}: {e}")
            return None

    def upsert_to_snowflake(self, data: Dict) -> bool:
        """Upsert company research data to Snowflake."""
        print(f"\n  → Upserting to Snowflake...")

        merge_sql = """
        MERGE INTO GTM.PUBLIC.COMPANY_WEB_SIGNALS AS target
        USING (
            SELECT
                %s AS COMPANY_NAME,
                %s AS DOMAIN,
                CURRENT_TIMESTAMP() AS RESEARCH_DATE,
                %s AS COMPANY_OVERVIEW,
                TO_VARIANT(PARSE_JSON(%s)) AS JOBS,
                TO_VARIANT(PARSE_JSON(%s)) AS MAJOR_ANNOUNCEMENTS,
                TO_VARIANT(PARSE_JSON(%s)) AS PRODUCT_RELEASES,
                TO_VARIANT(PARSE_JSON(%s)) AS C_SUITE_HIRES,
                TO_VARIANT(PARSE_JSON(%s)) AS STRATEGIC_ANNOUNCEMENTS,
                TO_VARIANT(PARSE_JSON(%s)) AS COMPANY_METRICS
        ) AS source
        ON target.DOMAIN = source.DOMAIN
        WHEN MATCHED THEN
            UPDATE SET
                target.COMPANY_NAME = source.COMPANY_NAME,
                target.RESEARCH_DATE = source.RESEARCH_DATE,
                target.COMPANY_OVERVIEW = source.COMPANY_OVERVIEW,
                target.JOBS = source.JOBS,
                target.MAJOR_ANNOUNCEMENTS = source.MAJOR_ANNOUNCEMENTS,
                target.PRODUCT_RELEASES = source.PRODUCT_RELEASES,
                target.C_SUITE_HIRES = source.C_SUITE_HIRES,
                target.STRATEGIC_ANNOUNCEMENTS = source.STRATEGIC_ANNOUNCEMENTS,
                target.COMPANY_METRICS = source.COMPANY_METRICS
        WHEN NOT MATCHED THEN
            INSERT (
                COMPANY_NAME, DOMAIN, RESEARCH_DATE, COMPANY_OVERVIEW,
                JOBS, MAJOR_ANNOUNCEMENTS, PRODUCT_RELEASES, C_SUITE_HIRES,
                STRATEGIC_ANNOUNCEMENTS, COMPANY_METRICS
            )
            VALUES (
                source.COMPANY_NAME, source.DOMAIN, source.RESEARCH_DATE, source.COMPANY_OVERVIEW,
                source.JOBS, source.MAJOR_ANNOUNCEMENTS, source.PRODUCT_RELEASES, source.C_SUITE_HIRES,
                source.STRATEGIC_ANNOUNCEMENTS, source.COMPANY_METRICS
            )
        """

        try:
            conn = self.get_snowflake_connection()
            cursor = conn.cursor()
            cursor.execute(merge_sql, (
                data['company_name'],
                data['domain'],
                data['company_overview'][:16777216],
                json.dumps(data['jobs']),
                json.dumps(data['major_announcements']),
                json.dumps(data['product_releases']),
                json.dumps(data['c_suite_hires']),
                json.dumps(data['strategic_announcements']),
                json.dumps(data['company_metrics'])
            ))
            conn.commit()
            cursor.close()
            conn.close()
            print(f"  ✓ Upserted {data['company_name']} to Snowflake")
            return True
        except Exception as e:
            print(f"  ✗ Failed to upsert: {e}")
            return False

    def process_companies(self, companies: List[Dict[str, str]]):
        """Process a list of companies."""
        total = len(companies)
        success = 0
        failed = 0

        print(f"\nProcessing {total} companies...")

        for i, company in enumerate(companies, 1):
            company_name = company.get('company_name')
            domain = company.get('domain')

            if not company_name or not domain:
                print(f"\n⚠ Skipping invalid entry {i}")
                failed += 1
                continue

            print(f"\n[{i}/{total}] Processing {company_name}...")

            data = self.research_company(company_name, domain)

            if data:
                if self.upsert_to_snowflake(data):
                    success += 1
                else:
                    failed += 1
            else:
                failed += 1

        print(f"\n{'='*60}")
        print(f"Complete: {success} succeeded, {failed} failed")
        print(f"{'='*60}\n")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Single company: python3 company_web_signals.py 'Company Name' domain.com")
        print("  Batch CSV: python3 company_web_signals.py companies.csv")
        sys.exit(1)

    client = CompanyWebSignals()

    if not client.create_table_if_not_exists():
        print("Failed to initialize table. Exiting.")
        sys.exit(1)

    if len(sys.argv) == 3:
        companies = [{'company_name': sys.argv[1], 'domain': sys.argv[2]}]
    else:
        import csv
        companies = []
        with open(sys.argv[1], 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                companies.append({
                    'company_name': row.get('company_name'),
                    'domain': row.get('domain')
                })

    client.process_companies(companies)


if __name__ == '__main__':
    main()
