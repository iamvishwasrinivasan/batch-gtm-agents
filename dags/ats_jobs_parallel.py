"""
ATS Job Scraper DAG (Parallel Batch Processing)

Orchestrates ATS job scraping for hiring signal intelligence.
Uses dynamic task mapping to process multiple companies concurrently.

Scrapes job postings from public ATS endpoints (Greenhouse, Lever, Ashby)
and stores results in Snowflake GTM.PUBLIC.ATS_JOB_POSTINGS table.

Usage:
- Single company: airflow dags trigger ats_jobs_parallel -c '{"company_name": "Astronomer", "domain": "astronomer.io"}'
- Batch CSV: airflow dags trigger ats_jobs_parallel -c '{"csv_path": "/path/to/companies.csv"}'
- Batch list: airflow dags trigger ats_jobs_parallel -c '{"companies": [{"company_name": "A", "domain": "a.com"}, ...]}'
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.decorators import task
import sys

# Add the ATS scraper skill directory to Python path
# Use /usr/local/airflow/include in Airflow containers
SKILLS_DIR = Path('/usr/local/airflow/include/skills/ats-job-scraper')
sys.path.insert(0, str(SKILLS_DIR))

from ats_scraper import ATSScraper


@task
def validate_and_prepare(**context) -> List[Dict[str, str]]:
    """Validate inputs and return list of companies to process."""
    conf = context.get('dag_run').conf or {}

    # Single company mode
    if 'company_name' in conf:
        domain = conf.get('domain', '')
        return [{'company_name': conf['company_name'], 'domain': domain}]

    # Direct list mode
    if 'companies' in conf:
        companies = conf['companies']
        if not isinstance(companies, list):
            raise ValueError("'companies' must be a list")
        return companies

    # CSV mode
    if 'csv_path' in conf:
        import csv
        csv_path = conf['csv_path']
        if not Path(csv_path).exists():
            raise ValueError(f"CSV file not found: {csv_path}")

        companies = []
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('company_name'):
                    companies.append({
                        'company_name': row['company_name'],
                        'domain': row.get('domain', '')
                    })
        return companies

    raise ValueError(
        "Provide: {'company_name': 'X', 'domain': 'x.com'} OR "
        "{'csv_path': '/path.csv'} OR "
        "{'companies': [{'company_name': 'X', 'domain': 'x.com'}, ...]}"
    )


@task
def setup_table() -> bool:
    """Ensure Snowflake table exists for ATS job postings."""
    # Table is created automatically by ATSScraper on first run
    # This task mainly serves as a checkpoint and logs the action
    print("ATS_JOB_POSTINGS table will be created on first scrape if not exists")
    return True


@task
def scrape_ats_jobs(company: Dict[str, str]) -> Dict[str, any]:
    """Scrape ATS job postings for a single company."""
    company_name = company.get('company_name')
    domain = company.get('domain', '')

    if not company_name:
        return {'status': 'skipped', 'reason': 'missing company name'}

    try:
        # Initialize scraper
        scraper = ATSScraper()

        # Scrape company
        result = scraper.scrape_company(company_name, domain)

        # Close Snowflake connection
        scraper.snowflake.close()

        # Check if ATS was detected
        if not result['ats_type']:
            return {
                'status': 'failed',
                'company_name': company_name,
                'reason': 'ATS not detected'
            }

        # Return success result
        return {
            'status': 'success',
            'company_name': company_name,
            'domain': domain,
            'ats_type': result['ats_type'],
            'jobs_found': result['total_jobs'],
            'departments': result['departments']
        }

    except Exception as e:
        return {
            'status': 'failed',
            'company_name': company_name,
            'reason': str(e)
        }


@task
def summarize_results(results: List[Dict]) -> None:
    """Print summary of ATS scraping results."""
    success = [r for r in results if r.get('status') == 'success']
    failed = [r for r in results if r.get('status') == 'failed']
    skipped = [r for r in results if r.get('status') == 'skipped']

    total_jobs = sum(r.get('jobs_found', 0) for r in success)

    print(f"\n{'='*70}")
    print(f"ATS Job Scraper - Summary")
    print(f"{'='*70}")
    print(f"Total companies: {len(results)}")
    print(f"✓ Succeeded: {len(success)}")
    print(f"✗ Failed: {len(failed)}")
    print(f"⊘ Skipped: {len(skipped)}")
    print(f"📊 Total jobs found: {total_jobs}")

    if success:
        print(f"\nSuccessful companies:")
        for r in success[:10]:  # Show first 10
            jobs = r.get('jobs_found', 0)
            ats = r.get('ats_type', 'unknown')
            depts = r.get('departments', {})
            top_dept = list(depts.keys())[0] if depts else 'N/A'
            top_dept_count = depts.get(top_dept, 0) if depts else 0
            print(f"  ✓ {r['company_name']:<30} ({ats}) - {jobs} jobs, top: {top_dept} ({top_dept_count})")
        if len(success) > 10:
            print(f"  ... and {len(success) - 10} more")

    if failed:
        print(f"\nFailed companies:")
        for r in failed[:10]:
            reason = r.get('reason', 'unknown')
            print(f"  ✗ {r.get('company_name', 'unknown'):<30} (Reason: {reason})")
        if len(failed) > 10:
            print(f"  ... and {len(failed) - 10} more")

    print(f"{'='*70}\n")

    if failed:
        raise RuntimeError(f"{len(failed)} companies failed to process")


# DAG definition
default_args = {
    'owner': 'vishwasrinivasan',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'ats_jobs_parallel',
    default_args=default_args,
    description='Parallel ATS job scraping for hiring signal intelligence',
    schedule=None,  # Manual trigger only (Airflow 3.x syntax)
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_tasks=8,  # Limit parallel scraping
    max_active_runs=1,   # One DAG run at a time
    tags=['gtm', 'ats', 'jobs', 'hiring-signals', 'parallel', 'snowflake'],
) as dag:

    # Prepare companies list
    companies = validate_and_prepare()

    # Setup Snowflake table (checkpoint)
    table_ready = setup_table()

    # Scrape ATS jobs for each company in parallel using dynamic task mapping
    results = scrape_ats_jobs.expand(company=companies)

    # Summarize results
    summary = summarize_results(results)

    # DAG dependencies
    companies >> table_ready >> results >> summary
