# Company Web Signals - Astro Deployment Guide

## Project Structure

```
gtm-research-airflow/
├── dags/
│   └── company_web_signals_dag_parallel.py    # Main DAG
├── include/
│   └── skills/
│       └── web-research-company/
│           └── company_web_signals.py          # Research logic
├── .env                                         # Environment variables (local only)
├── requirements.txt                             # Python dependencies
├── Dockerfile                                   # Astro runtime config
└── airflow_settings.yaml                        # Airflow config
```

## Setup Instructions

### 1. Configure Environment Variables (Local Testing)

Edit `.env` file:
```bash
EXA_API_KEY=your-actual-exa-api-key
```

### 2. Add Snowflake Config

Create `~/.snowflake/service_config.yaml`:
```yaml
snowflake:
  account: "GP21411.us-east-1"
  user: "VISHWASRINIVASAN"
  private_key_path: "~/.ssh/rsa_key_unencrypted.p8"
  role: "GTMADMIN"
  warehouse: "HUMANS"
  database: "GTM"
```

### 3. Test Locally (Optional)

```bash
cd ~/gtm-research-airflow
astro dev start
```

Access Airflow UI at: http://localhost:8080
- Username: `admin`
- Password: `admin`

### 4. Create a Deployment on Astro

```bash
export ASTRO_API_TOKEN="your-token-here"
astro deployment create --name "GTM Research" --executor celery
```

This will create a deployment and return a deployment ID.

### 5. Set Environment Variables in Astro Deployment

You need to add environment variables to your Astro deployment:

**Option A: Via Astro CLI**
```bash
# Get your deployment ID
astro deployment list

# Set EXA_API_KEY
astro deployment variable create --deployment-id <deployment-id> \
  --key EXA_API_KEY \
  --value "your-exa-api-key" \
  --secret
```

**Option B: Via Astro Cloud UI**
1. Go to https://cloud.astronomer.io
2. Navigate to your workspace → Deployments → GTM Research
3. Go to "Environment" tab
4. Add environment variable:
   - Key: `EXA_API_KEY`
   - Value: your Exa API key
   - Check "Secret" checkbox

### 6. Add Snowflake Config to Deployment

Since Astro deployments don't have access to your local `~/.snowflake/service_config.yaml`, you have two options:

**Option A: Use Environment Variables**

Update `company_web_signals.py` to read from env vars:
```python
# In __init__ method, replace the YAML loading with:
self.sf_config = {
    'account': os.getenv('SNOWFLAKE_ACCOUNT'),
    'user': os.getenv('SNOWFLAKE_USER'),
    'private_key_path': '/usr/local/airflow/include/.ssh/rsa_key.p8',
    'role': os.getenv('SNOWFLAKE_ROLE', 'GTMADMIN'),
    'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE', 'HUMANS'),
    'database': os.getenv('SNOWFLAKE_DATABASE', 'GTM')
}
```

Then add environment variables to deployment:
```bash
astro deployment variable create --deployment-id <id> --key SNOWFLAKE_ACCOUNT --value "GP21411.us-east-1"
astro deployment variable create --deployment-id <id> --key SNOWFLAKE_USER --value "VISHWASRINIVASAN"
astro deployment variable create --deployment-id <id> --key SNOWFLAKE_ROLE --value "GTMADMIN"
astro deployment variable create --deployment-id <id> --key SNOWFLAKE_WAREHOUSE --value "HUMANS"
astro deployment variable create --deployment-id <id> --key SNOWFLAKE_DATABASE --value "GTM"
```

**Option B: Copy SSH Key and Config to include/ Directory**

```bash
# Create directories
mkdir -p include/.snowflake
mkdir -p include/.ssh

# Copy files
cp ~/.snowflake/service_config.yaml include/.snowflake/
cp ~/.ssh/rsa_key_unencrypted.p8 include/.ssh/rsa_key.p8

# Update company_web_signals.py to use the new paths
# In __init__ method:
snowflake_config_path = Path("/usr/local/airflow/include/.snowflake/service_config.yaml")
```

**IMPORTANT:** If using Option B, add these to `.gitignore`:
```
include/.snowflake/
include/.ssh/
```

### 7. Deploy to Astro

```bash
# From project directory
astro deploy
```

You'll be prompted to select a deployment. Choose "GTM Research".

### 8. Verify Deployment

```bash
# Check deployment status
astro deployment list

# View deployment logs
astro deployment logs --deployment-id <deployment-id>
```

## Using the DAG

### Trigger via Astro Cloud UI

1. Go to https://cloud.astronomer.io
2. Navigate to your workspace → Deployments → GTM Research
3. Click "Open Airflow"
4. Find `company_web_signals_parallel` DAG
5. Click "Trigger DAG w/ config"
6. Enter JSON config:

**Single company:**
```json
{
  "company_name": "Trivelta",
  "domain": "trivelta.com"
}
```

**Multiple companies:**
```json
{
  "companies": [
    {"company_name": "Trivelta", "domain": "trivelta.com"},
    {"company_name": "GridX", "domain": "gridx.ai"}
  ]
}
```

### Trigger via Astro CLI

```bash
# Get deployment details
astro deployment list

# Trigger the DAG
astro deployment airflow trigger company_web_signals_parallel \
  --deployment-id <deployment-id> \
  --conf '{"company_name": "Trivelta", "domain": "trivelta.com"}'
```

## Monitoring

### View DAG Runs
```bash
astro deployment airflow list-runs company_web_signals_parallel --deployment-id <deployment-id>
```

### Check Logs
```bash
astro deployment logs --deployment-id <deployment-id> --follow
```

### Query Results in Snowflake
```sql
-- Check recent research
SELECT 
    COMPANY_NAME, 
    DOMAIN, 
    RESEARCH_DATE,
    ARRAY_SIZE(JOBS) as job_count,
    ARRAY_SIZE(MAJOR_ANNOUNCEMENTS) as announcement_count
FROM GTM.PUBLIC.COMPANY_WEB_SIGNALS 
ORDER BY RESEARCH_DATE DESC 
LIMIT 10;
```

## Troubleshooting

### "EXA_API_KEY not found"
- Ensure environment variable is set in Astro deployment
- Check: Deployment → Environment tab in Astro UI

### "Snowflake connection failed"
- Verify Snowflake config is accessible in deployment
- Check private key path is correct
- Ensure environment variables are set (if using Option A)

### "Module not found: company_web_signals"
- Verify `include/skills/web-research-company/company_web_signals.py` exists
- Check the path in the DAG file matches `/usr/local/airflow/include/skills/web-research-company`

### DAG not showing up
- Check deployment logs: `astro deployment logs --deployment-id <id>`
- Look for parsing errors
- Verify all dependencies in `requirements.txt` are installed

## Updating the DAG

1. Make changes to files in `dags/` or `include/`
2. Deploy updates:
   ```bash
   astro deploy
   ```
3. Changes are typically live within 1-2 minutes

## Scheduled Runs (Optional)

To run automatically (e.g., weekly refresh of key accounts):

1. Edit the DAG file:
   ```python
   schedule_interval='@weekly'  # or '@daily', '0 0 * * 0' (cron)
   ```

2. Add a default companies list or pull from Snowflake table:
   ```python
   @task
   def get_default_companies():
       """Pull companies from Snowflake for scheduled runs."""
       # Query your accounts table
       pass
   ```

3. Redeploy: `astro deploy`

## Cost Optimization

- **Executor**: Use Celery for parallel processing or KubernetesExecutor for better isolation
- **Worker resources**: Adjust in Deployment → Resources (start with Small workers)
- **Exa API**: Monitor usage to avoid overages
- **Snowflake**: Consider using auto-suspend warehouse

## Best Practices

1. **Test locally first**: `astro dev start` before deploying
2. **Start small**: Test with 1-2 companies before large batches
3. **Monitor logs**: Watch for Exa API rate limits
4. **Version control**: Commit changes to git before deploying
5. **Environment variables**: Use secrets for API keys (don't commit to git)

---

**Next Steps:**
1. Set EXA_API_KEY in deployment
2. Configure Snowflake access
3. Deploy: `astro deploy`
4. Test with a single company
5. Scale to batch processing
