"""
Company Web Signals Ingest DAG (Parallel Batch Processing)

Orchestrates company research using Exa API with parallel batch processing.
Uses dynamic task mapping to process multiple companies concurrently.

Usage:
- Single company: airflow dags trigger company_web_signals_parallel -c '{"company_name": "Acme", "domain": "acme.com"}'
- Batch CSV: airflow dags trigger company_web_signals_parallel -c '{"csv_path": "/path/to/companies.csv"}'
- Batch list: airflow dags trigger company_web_signals_parallel -c '{"companies": [{"company_name": "A", "domain": "a.com"}, ...]}'
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.decorators import task
import sys

# Add the skills directory to Python path (in Astro, use /usr/local/airflow/include)
SKILLS_DIR = Path("/usr/local/airflow/include/skills/web-research-company")
sys.path.insert(0, str(SKILLS_DIR))

from company_web_signals import CompanyWebSignals


@task
def validate_and_prepare(**context) -> List[Dict[str, str]]:
    """Validate inputs and return list of companies to process."""
    conf = context.get('dag_run').conf or {}

    # Single company mode
    if 'company_name' in conf and 'domain' in conf:
        return [{'company_name': conf['company_name'], 'domain': conf['domain']}]

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
                if row.get('company_name') and row.get('domain'):
                    companies.append({
                        'company_name': row['company_name'],
                        'domain': row['domain']
                    })
        return companies

    raise ValueError(
        "Provide: {'company_name': 'X', 'domain': 'x.com'} OR "
        "{'csv_path': '/path.csv'} OR "
        "{'companies': [{'company_name': 'X', 'domain': 'x.com'}, ...]}"
    )


@task
def setup_table() -> bool:
    """Create Snowflake table if it doesn't exist."""
    client = CompanyWebSignals()
    if not client.create_table_if_not_exists():
        raise RuntimeError("Failed to create Snowflake table")
    return True


@task
def research_and_upsert_company(company: Dict[str, str]) -> Dict[str, any]:
    """Research a single company and upsert to Snowflake."""
    company_name = company.get('company_name')
    domain = company.get('domain')

    if not company_name or not domain:
        return {'status': 'skipped', 'reason': 'missing name or domain'}

    try:
        client = CompanyWebSignals()
        data = client.research_company(company_name, domain)

        if not data:
            return {
                'status': 'failed',
                'company_name': company_name,
                'reason': 'research failed'
            }

        success = client.upsert_to_snowflake(data)

        if success:
            return {
                'status': 'success',
                'company_name': company_name,
                'domain': domain,
                'jobs_found': len(data.get('jobs', [])),
                'announcements': len(data.get('major_announcements', []))
            }
        else:
            return {
                'status': 'failed',
                'company_name': company_name,
                'reason': 'upsert failed'
            }

    except Exception as e:
        return {
            'status': 'failed',
            'company_name': company_name,
            'reason': str(e)
        }


@task
def summarize_results(results: List[Dict]) -> None:
    """Print summary of batch processing results."""
    success = [r for r in results if r.get('status') == 'success']
    failed = [r for r in results if r.get('status') == 'failed']
    skipped = [r for r in results if r.get('status') == 'skipped']

    print(f"\n{'='*70}")
    print(f"Company Web Signals Ingest - Summary")
    print(f"{'='*70}")
    print(f"Total: {len(results)}")
    print(f"✓ Succeeded: {len(success)}")
    print(f"✗ Failed: {len(failed)}")
    print(f"⊘ Skipped: {len(skipped)}")

    if success:
        print(f"\nSuccessful companies:")
        for r in success[:10]:  # Show first 10
            jobs = r.get('jobs_found', 0)
            announcements = r.get('announcements', 0)
            print(f"  ✓ {r['company_name']:<30} ({jobs} jobs, {announcements} announcements)")
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
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'company_web_signals_parallel',
    default_args=default_args,
    description='Parallel company research ingest using Exa API',
    schedule=None,  # Manual trigger only (Airflow 3.x uses 'schedule' not 'schedule_interval')
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=['gtm', 'company-research', 'exa', 'snowflake', 'parallel'],
) as dag:

    # Prepare companies list
    companies = validate_and_prepare()

    # Setup Snowflake table
    table_ready = setup_table()

    # Research and upsert each company in parallel using dynamic task mapping
    results = research_and_upsert_company.expand(company=companies)

    # Summarize results
    summary = summarize_results(results)

    # DAG dependencies
    companies >> table_ready >> results >> summary
