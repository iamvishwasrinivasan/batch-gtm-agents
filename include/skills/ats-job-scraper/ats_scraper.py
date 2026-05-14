#!/usr/bin/env python3
"""
ATS Job Scraper - Query public job endpoints for companies
Supports: Greenhouse, Lever, Ashby
"""

import requests
import json
import sys
import os
import re
import time
import csv
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import yaml
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import snowflake.connector


class ATSConfig:
    """Load ATS provider configurations."""

    def __init__(self, config_path: Path):
        with open(config_path) as f:
            self.config = json.load(f)

    def get_providers(self) -> List[str]:
        return list(self.config.keys())

    def get_api_url(self, provider: str, slug: str) -> str:
        return self.config[provider]['api_url'].format(slug=slug)

    def get_rate_limit(self, provider: str) -> int:
        return self.config[provider]['rate_limit_ms']


class ATSDetector:
    """Detect which ATS provider a company uses."""

    def __init__(self, config: ATSConfig):
        self.config = config

    def generate_slug_patterns(self, company_name: str, domain: str) -> List[str]:
        """Generate common slug variations to try."""
        slugs = []

        # Lowercase company name
        clean_name = company_name.lower().strip()
        # Remove common suffixes
        clean_name = re.sub(r'\s+(inc\.?|llc|ltd\.?|corp\.?)$', '', clean_name, flags=re.IGNORECASE)
        # Replace spaces with hyphens
        slug = re.sub(r'\s+', '-', clean_name)
        slugs.append(slug)

        # Remove hyphens (some providers use no separator)
        slugs.append(slug.replace('-', ''))

        # Domain prefix
        if domain:
            domain_slug = domain.split('.')[0].lower()
            if domain_slug not in slugs:
                slugs.append(domain_slug)

        # Add common variations
        if slug not in slugs:
            slugs.append(slug + '-inc')
            slugs.append(slug + '-careers')

        return slugs

    def try_direct_api(self, slug: str) -> Optional[Dict]:
        """Try all 3 ATS APIs with this slug."""
        for provider in self.config.get_providers():
            try:
                if provider == 'ashby':
                    # Ashby uses GraphQL
                    result = self._try_ashby_graphql(slug)
                    if result:
                        return result
                else:
                    # Standard REST API (Greenhouse, Lever)
                    url = self.config.get_api_url(provider, slug)
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        data = response.json()

                        # Check if response contains jobs
                        jobs = self._extract_jobs(provider, data)
                        if jobs:
                            return {
                                'ats_type': provider,
                                'slug': slug,
                                'jobs': jobs
                            }
            except Exception:
                continue

        return None

    def _try_ashby_graphql(self, slug: str) -> Optional[Dict]:
        """Try Ashby GraphQL API."""
        url = "https://jobs.ashbyhq.com/api/non-user-graphql?op=ApiJobBoardWithTeams"

        # GraphQL query to fetch job board with teams and postings
        query = """
        query ApiJobBoardWithTeams($organizationHostedJobsPageName: String!) {
            jobBoard: jobBoardWithTeams(
                organizationHostedJobsPageName: $organizationHostedJobsPageName
            ) {
                teams {
                    id
                    name
                }
                jobPostings {
                    id
                    title
                    teamId
                    locationName
                }
            }
        }
        """

        payload = {
            "operationName": "ApiJobBoardWithTeams",
            "variables": {
                "organizationHostedJobsPageName": slug
            },
            "query": query
        }

        try:
            response = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()

                # Check for GraphQL errors
                if data.get('errors'):
                    return None

                job_board = data.get('data', {}).get('jobBoard')
                if not job_board:
                    return None

                jobs = job_board.get('jobPostings', [])
                teams = {t['id']: t['name'] for t in job_board.get('teams', [])}

                if jobs:
                    # Add team names to jobs
                    for job in jobs:
                        team_id = job.get('teamId')
                        job['teamName'] = teams.get(team_id, '')

                    return {
                        'ats_type': 'ashby',
                        'slug': slug,
                        'jobs': jobs
                    }
        except Exception:
            pass

        return None

    def _extract_jobs(self, provider: str, data: Dict) -> List:
        """Extract jobs list from API response."""
        if provider == 'greenhouse':
            return data.get('jobs', [])
        elif provider == 'lever':
            # Lever returns array directly or in 'postings' key
            if isinstance(data, list):
                return data
            return data.get('postings', [])
        elif provider == 'ashby':
            # Ashby GraphQL response structure
            job_board = data.get('data', {}).get('jobBoard', {})
            return job_board.get('jobPostings', [])
        return []

    def detect(self, company_name: str, domain: str) -> Optional[Dict]:
        """Detect ATS provider for a company."""
        # Phase 1: Try direct API calls with common slugs
        slugs = self.generate_slug_patterns(company_name, domain)

        for slug in slugs:
            result = self.try_direct_api(slug)
            if result:
                print(f"  ✓ Detected via direct API: {result['ats_type']} (slug: {slug})")
                return result
            time.sleep(0.1)  # Small delay between attempts

        # Phase 2: Exa fallback would go here (not implemented yet - returns None for now)
        print(f"  ⚠ Could not detect ATS for {company_name}")
        return None


class ATSProvider:
    """Base class for ATS providers."""

    def parse_job(self, raw_data: Dict, ats_type: str, slug: str = '') -> Dict:
        """Normalize job data to common schema."""
        if ats_type == 'greenhouse':
            return self._parse_greenhouse(raw_data)
        elif ats_type == 'lever':
            return self._parse_lever(raw_data)
        elif ats_type == 'ashby':
            return self._parse_ashby(raw_data, slug)
        return {}

    def _parse_greenhouse(self, job: Dict) -> Dict:
        """Parse Greenhouse job posting."""
        location = job.get('location', {})
        if isinstance(location, dict):
            location = location.get('name', '')

        # Try to get department from departments array or metadata
        department = ''
        departments = job.get('departments', [])
        if departments:
            department = departments[0].get('name', '')
        else:
            # Try extracting from metadata (some boards use this)
            metadata = job.get('metadata')
            if metadata:
                for meta in metadata:
                    if 'department' in meta.get('name', '').lower():
                        department = meta.get('value', '')
                        break

        # Use first_published if available, fallback to created_at
        posted_date = job.get('first_published', job.get('created_at', ''))

        return {
            'id': str(job.get('id', '')),
            'title': job.get('title', ''),
            'department': department,
            'location': location,
            'posted_date': posted_date,
            'updated_date': job.get('updated_at', ''),
            'url': job.get('absolute_url', ''),
            'description': job.get('content', ''),  # Usually empty in board listings
            'job_type': '',
            'salary': ''
        }

    def _parse_lever(self, job: Dict) -> Dict:
        """Parse Lever job posting."""
        categories = job.get('categories', {})

        return {
            'id': job.get('id', ''),
            'title': job.get('text', ''),
            'department': categories.get('department', '') if isinstance(categories, dict) else '',
            'location': categories.get('location', '') if isinstance(categories, dict) else '',
            'posted_date': job.get('createdAt', ''),
            'updated_date': '',
            'url': job.get('hostedUrl', ''),
            'description': job.get('description', ''),
            'job_type': categories.get('commitment', '') if isinstance(categories, dict) else '',
            'salary': ''
        }

    def _parse_ashby(self, job: Dict, slug: str = '') -> Dict:
        """Parse Ashby job posting from GraphQL response."""
        # Construct job URL from ID and slug
        job_id = job.get('id', '')
        job_url = f"https://jobs.ashbyhq.com/{slug}/{job_id}" if job_id and slug else ''

        return {
            'id': job_id,
            'title': job.get('title', ''),
            'department': job.get('teamName', ''),  # From GraphQL enrichment
            'location': job.get('locationName', ''),
            'posted_date': job.get('publishedDate', ''),
            'updated_date': '',
            'url': job_url,
            'description': '',  # Not available in brief listing
            'job_type': job.get('employmentType', ''),
            'salary': ''
        }


class SnowflakeWriter:
    """Handle Snowflake database operations."""

    def __init__(self):
        self.conn = None

    def get_connection(self):
        """Create Snowflake connection."""
        if self.conn:
            return self.conn

        try:
            snowflake_config_path = Path.home() / ".snowflake/service_config.yaml"
            with open(snowflake_config_path) as f:
                config_data = yaml.safe_load(f)
                sf_config = config_data['snowflake']

            private_key_path = Path(sf_config['private_key_path']).expanduser()
            with open(private_key_path, "rb") as key_file:
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

            self.conn = snowflake.connector.connect(
                account=sf_config['account'],
                user=sf_config['user'],
                private_key=pkb,
                role=sf_config['role'],
                warehouse=sf_config['warehouse'],
                database=sf_config['database']
            )
            return self.conn
        except Exception as e:
            print(f"  ⚠ Snowflake connection failed: {e}")
            return None

    def upsert_jobs(self, company_name: str, domain: str, ats_type: str, jobs: List[Dict], scraped_date: str) -> bool:
        """Upsert jobs to Snowflake."""
        conn = self.get_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()

            # Create table if not exists
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS GTM.PUBLIC.ATS_JOB_POSTINGS (
                company_name VARCHAR,
                domain VARCHAR,
                ats_type VARCHAR,
                job_id VARCHAR,
                title VARCHAR,
                department VARCHAR,
                location VARCHAR,
                posted_date TIMESTAMP,
                updated_date TIMESTAMP,
                url VARCHAR,
                description TEXT,
                job_type VARCHAR,
                salary VARCHAR,
                scraped_date TIMESTAMP,
                PRIMARY KEY (company_name, job_id)
            )
            """
            cursor.execute(create_table_sql)

            # Delete existing jobs for this company before inserting new ones
            delete_sql = """
            DELETE FROM GTM.PUBLIC.ATS_JOB_POSTINGS
            WHERE company_name = %s
            """
            cursor.execute(delete_sql, (company_name,))

            # Insert jobs
            insert_sql = """
            INSERT INTO GTM.PUBLIC.ATS_JOB_POSTINGS (
                company_name, domain, ats_type, job_id, title, department,
                location, posted_date, updated_date, url, description,
                job_type, salary, scraped_date
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """

            for job in jobs:
                # Convert empty date strings to None for Snowflake
                posted_date = job['posted_date'] if job['posted_date'] else None
                updated_date = job['updated_date'] if job['updated_date'] else None

                cursor.execute(insert_sql, (
                    company_name, domain, ats_type, job['id'], job['title'],
                    job['department'], job['location'], posted_date,
                    updated_date, job['url'], job['description'],
                    job['job_type'], job['salary'], scraped_date
                ))

            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"  ⚠ Snowflake upsert failed: {e}")
            return False

    def close(self):
        """Close Snowflake connection."""
        if self.conn:
            self.conn.close()


class ATSScraper:
    """Main orchestrator."""

    def __init__(self):
        config_path = Path(__file__).parent / 'ats_config.json'
        self.config = ATSConfig(config_path)
        self.detector = ATSDetector(self.config)
        self.provider = ATSProvider()
        self.snowflake = SnowflakeWriter()

    def scrape_company(self, company_name: str, domain: str = '') -> Dict:
        """Scrape all jobs for one company."""
        print(f"→ Scraping {company_name}...")

        # Detect ATS and fetch jobs
        result = self.detector.detect(company_name, domain)

        if not result:
            return {
                'company_name': company_name,
                'domain': domain,
                'ats_type': None,
                'jobs': [],
                'total_jobs': 0,
                'departments': {},
                'scraped_date': datetime.now().isoformat()
            }

        # Parse and normalize jobs
        ats_type = result['ats_type']
        slug = result['slug']
        raw_jobs = result['jobs']
        jobs = [self.provider.parse_job(job, ats_type, slug) for job in raw_jobs]

        # Calculate department breakdown
        dept_counts = defaultdict(int)
        for job in jobs:
            dept = job.get('department', 'Unknown')
            if dept:
                dept_counts[dept] += 1

        # Sort departments by count
        sorted_depts = dict(sorted(dept_counts.items(), key=lambda x: x[1], reverse=True))

        scraped_date = datetime.now().isoformat()

        result_data = {
            'company_name': company_name,
            'domain': domain,
            'ats_type': ats_type,
            'jobs': jobs,
            'total_jobs': len(jobs),
            'departments': sorted_depts,
            'scraped_date': scraped_date
        }

        # Save to JSON
        self._save_json(company_name, result_data)

        # Save to Snowflake
        self._save_snowflake(company_name, domain, ats_type, jobs, scraped_date)

        print(f"  ✓ Found {len(jobs)} jobs")

        return result_data

    def _save_json(self, company_name: str, data: Dict):
        """Save results to JSON file."""
        # Detect if running in Airflow
        airflow_home = os.environ.get('AIRFLOW_HOME')
        if airflow_home:
            # Running in Airflow - save to mounted output directory
            output_base = Path(airflow_home) / "include" / "output" / "ats_jobs"
        else:
            # Running locally - save to Account Context
            output_base = Path.home() / "Account Context"

        account_dir = output_base / company_name
        account_dir.mkdir(parents=True, exist_ok=True)

        date_str = datetime.now().strftime('%Y-%m-%d')
        output_path = account_dir / f"ats_jobs_{date_str}.json"

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"  💾 Saved: {output_path}")

    def _save_snowflake(self, company_name: str, domain: str, ats_type: str, jobs: List[Dict], scraped_date: str):
        """Save results to Snowflake."""
        success = self.snowflake.upsert_jobs(company_name, domain, ats_type, jobs, scraped_date)
        if success:
            print(f"  💾 Saved to Snowflake: GTM.PUBLIC.ATS_JOB_POSTINGS")

    def scrape_bulk(self, companies: List[Dict]) -> List[Dict]:
        """Process multiple companies."""
        results = []
        total = len(companies)

        for i, company in enumerate(companies, 1):
            print(f"\n[{i}/{total}] Processing...")
            result = self.scrape_company(
                company.get('company_name', company.get('name', '')),
                company.get('domain', '')
            )
            results.append(result)

            # Rate limit between companies
            if i < total:
                time.sleep(0.3)

        return results

    def print_summary(self, results: List[Dict]):
        """Print summary of results."""
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)

        total_jobs = 0
        successful = 0
        failed = 0

        for result in results:
            company = result['company_name']
            ats_type = result['ats_type']
            job_count = result['total_jobs']

            if ats_type:
                successful += 1
                total_jobs += job_count

                # Top departments
                depts = result['departments']
                top_depts = list(depts.items())[:3]
                dept_str = ', '.join([f"{d} ({c})" for d, c in top_depts])

                # Most recent job
                recent_job = "N/A"
                if result['jobs']:
                    sorted_jobs = sorted(result['jobs'], key=lambda x: x.get('posted_date', ''), reverse=True)
                    if sorted_jobs:
                        recent_job = sorted_jobs[0].get('title', 'N/A')

                print(f"\n✓ {company} ({ats_type})")
                print(f"  Jobs: {job_count}")
                if dept_str:
                    print(f"  Departments: {dept_str}")
                print(f"  Recent: {recent_job}")

                # Show save location
                account_dir = Path.home() / "Account Context" / company
                date_str = datetime.now().strftime('%Y-%m-%d')
                print(f"  Saved: {account_dir}/ats_jobs_{date_str}.json")
            else:
                failed += 1
                print(f"\n✗ {company}")
                print(f"  Could not detect ATS")

        print(f"\n" + "="*60)
        print(f"Processed: {successful + failed} companies")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Total jobs: {total_jobs}")
        print("="*60)


def parse_args():
    """Parse command line arguments."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Single: python3 ats_scraper.py 'Company Name, domain.com'")
        print("  Multiple: python3 ats_scraper.py 'Company1,Company2,Company3'")
        print("  Bulk: python3 ats_scraper.py --file path/to/companies.csv")
        sys.exit(1)

    args = sys.argv[1]

    # Check if bulk file
    if args.startswith('--file'):
        file_path = args.split(None, 1)[1] if ' ' in args else sys.argv[2] if len(sys.argv) > 2 else None
        if not file_path:
            print("Error: --file requires a path")
            sys.exit(1)

        # Read CSV
        companies = []
        with open(Path(file_path).expanduser()) as f:
            reader = csv.DictReader(f)
            for row in reader:
                companies.append({
                    'company_name': row.get('company_name', row.get('name', '')),
                    'domain': row.get('domain', '')
                })

        return {'mode': 'bulk', 'companies': companies}

    # Check if comma-separated
    if ',' in args and not ('@' in args or '://' in args):  # Not a single company with comma in name
        companies = []
        for company in args.split(','):
            company = company.strip()
            if company:
                companies.append({'company_name': company, 'domain': ''})
        return {'mode': 'bulk', 'companies': companies}

    # Single company
    parts = args.split(',')
    company_name = parts[0].strip()
    domain = parts[1].strip() if len(parts) > 1 else ''

    return {
        'mode': 'single',
        'company_name': company_name,
        'domain': domain
    }


def main():
    """Main entry point."""
    args = parse_args()
    scraper = ATSScraper()

    if args['mode'] == 'single':
        result = scraper.scrape_company(args['company_name'], args['domain'])
        scraper.print_summary([result])
    else:
        results = scraper.scrape_bulk(args['companies'])
        scraper.print_summary(results)

    scraper.snowflake.close()


if __name__ == '__main__':
    main()
