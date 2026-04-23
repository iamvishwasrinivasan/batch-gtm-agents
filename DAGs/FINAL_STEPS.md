# Final Deployment Steps

## ✅ Completed So Far

1. ✅ Astro CLI installed
2. ✅ Astro project created at `~/gtm-research-airflow/`
3. ✅ Deployment created: **GTM Company Research** (`cmobw0oj52tef01ogr69z2wnk`)
4. ✅ DAG code prepared with parallel processing
5. ✅ Skill code updated to use environment variables
6. ✅ Snowflake private key copied to `include/.ssh/`
7. ✅ Deploy scripts created

## 🚀 Next: Deploy to Astro

### Option 1: Using the Deploy Script (Recommended)

1. **Install and start Docker Desktop**:
   ```bash
   # Install
   brew install --cask docker
   
   # Open Docker Desktop app
   open -a Docker
   
   # Wait ~30 seconds for Docker to start
   ```

2. **Run the deploy script**:
   ```bash
   cd ~/gtm-research-airflow
   ./deploy.sh
   ```
   
   This will build and deploy your DAG (~2-3 minutes).

### Option 2: Manual Deploy Command

If the script doesn't work:

```bash
cd ~/gtm-research-airflow

export ASTRO_API_TOKEN="eyJhbGciOiJSUzI1NiIsImtpZCI6ImNsb2Q0aGtqejAya3AwMWozdWNqbzJwOHIiLCJ0eXAiOiJKV1QifQ.eyJhcGlUb2tlbklkIjoiY21vYnZ0cGFqMnQ4djAxbnIyMW5lbG5mZyIsImF1ZCI6ImFzdHJvbm9tZXItZWUiLCJpYXQiOjE3NzY5NzI5NjgsImlzQXN0cm9ub21lckdlbmVyYXRlZCI6dHJ1ZSwiaXNJbnRlcm5hbCI6ZmFsc2UsImlzcyI6Imh0dHBzOi8vYXBpLmFzdHJvbm9tZXIuaW8iLCJraWQiOiJjbG9kNGhranowMmtwMDFqM3Vjam8ycDhyIiwicGVybWlzc2lvbnMiOlsiYXBpVG9rZW5JZDpjbW9idnRwYWoydDh2MDFucjIxbmVsbmZnIiwid29ya3NwYWNlSWQ6Y21vOHVzaTI2OWE1YjAxanVkNjEzZGpndCIsIm9yZ2FuaXphdGlvbklkOmNscWUybDMyczAyM2wwMW9tMHlpMm54MnYiLCJvcmdTaG9ydE5hbWU6Y2xxZTJsMzJzMDIzbDAxb20weWkybngydiJdLCJzY29wZSI6ImFwaVRva2VuSWQ6Y21vYnZ0cGFqMnQ4djAxbnIyMW5lbG5mZyB3b3Jrc3BhY2VJZDpjbW84dXNpMjY5YTViMDFqdWQ2MTNkamd0IG9yZ2FuaXphdGlvbklkOmNscWUybDMyczAyM2wwMW9tMHlpMm54MnYgb3JnU2hvcnROYW1lOmNscWUybDMyczAyM2wwMW9tMHlpMm54MnYiLCJzdWIiOiJjbWFlZDF1cXgwZHI2MDFtZ3duOTJ4Zm52IiwidmVyc2lvbiI6ImNtb2J2dHBhajJ0OHUwMW5yeDg3NjdtN3MifQ.A6udmBw5-Aouap7hF8n4R1UI0tiT4ddFOQzu-zLm-UVLtTEZ3kUQHYnR6uYICcXWq7d-YVFlpP-SSH1MDWyCm-OQGCaBBpz1DW6ot29h2Coy1x5UuL-dwZ6tUXeJsLYxoxDbEF9v552pRjRoPoI691HMUeLHOC0BfmHJtwMShSkMcZ01ZFhH252aNAL6LRHDo439-C1INosRtFA03Vqo2ZTjFCa-AMm4wR3Y_j9Uo5QVfBOuTU-uYB6T1JG5IU6LIVdAkh4pFnC7VMmqsTLl1HhlPoAIs1J2Zkm5HeMGR3gQSGignVwq0zyum42Q0Xk1SYhJeijAQooWpXxqTfqLPA"

astro deploy cmobw0oj52tef01ogr69z2wnk
```

## 🔑 Configure Environment Variables

After deployment completes, you **must** add environment variables.

### Method A: Using the Script (Fastest)

```bash
cd ~/gtm-research-airflow
./setup_env_vars.sh YOUR_EXA_API_KEY
```

Replace `YOUR_EXA_API_KEY` with your actual Exa API key.

### Method B: Via Astro Cloud UI

1. Go to: https://cloud.astronomer.io/cmo8usi269a5b01jud613djgt/deployments/cmobw0oj52tef01ogr69z2wnk
2. Click **Environment** tab
3. Click **+ Environment Variable**
4. Add each variable:

| Key | Value | Secret |
|-----|-------|--------|
| `EXA_API_KEY` | your-exa-api-key | ✅ Check |
| `SNOWFLAKE_ACCOUNT` | `GP21411.us-east-1` | ❌ Uncheck |
| `SNOWFLAKE_USER` | `VISHWASRINIVASAN` | ❌ Uncheck |
| `SNOWFLAKE_ROLE` | `GTMADMIN` | ❌ Uncheck |
| `SNOWFLAKE_WAREHOUSE` | `HUMANS` | ❌ Uncheck |
| `SNOWFLAKE_DATABASE` | `GTM` | ❌ Uncheck |

5. Click **Save Changes**
6. Wait ~1 minute for deployment to restart

### Method C: Via Astro CLI

```bash
export ASTRO_API_TOKEN="your-token"
DEPLOYMENT_ID="cmobw0oj52tef01ogr69z2wnk"

astro deployment variable create --deployment-id $DEPLOYMENT_ID --key EXA_API_KEY --value "your-key" --secret
astro deployment variable create --deployment-id $DEPLOYMENT_ID --key SNOWFLAKE_ACCOUNT --value "GP21411.us-east-1"
astro deployment variable create --deployment-id $DEPLOYMENT_ID --key SNOWFLAKE_USER --value "VISHWASRINIVASAN"
astro deployment variable create --deployment-id $DEPLOYMENT_ID --key SNOWFLAKE_ROLE --value "GTMADMIN"
astro deployment variable create --deployment-id $DEPLOYMENT_ID --key SNOWFLAKE_WAREHOUSE --value "HUMANS"
astro deployment variable create --deployment-id $DEPLOYMENT_ID --key SNOWFLAKE_DATABASE --value "GTM"
```

## ✅ Verify Deployment

### Check logs:
```bash
astro deployment logs --deployment-id cmobw0oj52tef01ogr69z2wnk --follow
```

### Check deployment status:
```bash
astro deployment list
```

## 🎯 Test the DAG

### Via Airflow UI:

1. Go to: **https://clqe2l32s023l01om0yi2nx2v.astronomer.run/d69z2wnk**
2. Find the `company_web_signals_parallel` DAG
3. Click the **▶ play button** → "Trigger DAG w/ config"
4. Enter test config:
   ```json
   {
     "company_name": "Trivelta",
     "domain": "trivelta.com"
   }
   ```
5. Click **Trigger**
6. Watch the DAG run (takes ~30-60 seconds)

### Via Astro CLI:

```bash
export ASTRO_API_TOKEN="your-token"

astro deployment airflow trigger company_web_signals_parallel \
  --deployment-id cmobw0oj52tef01ogr69z2wnk \
  --conf '{"company_name": "Trivelta", "domain": "trivelta.com"}'
```

## 🔍 Check Results

### In Snowflake:

```sql
-- View recent research
SELECT 
    COMPANY_NAME, 
    DOMAIN, 
    RESEARCH_DATE,
    ARRAY_SIZE(JOBS) as job_count,
    ARRAY_SIZE(MAJOR_ANNOUNCEMENTS) as announcements,
    ARRAY_SIZE(PRODUCT_RELEASES) as products
FROM GTM.PUBLIC.COMPANY_WEB_SIGNALS 
ORDER BY RESEARCH_DATE DESC 
LIMIT 10;

-- See tech stack for a company
SELECT 
    COMPANY_NAME,
    JOBS[0]:orchestration_tools AS orchestration,
    JOBS[0]:data_tools AS data_tools
FROM GTM.PUBLIC.COMPANY_WEB_SIGNALS 
WHERE DOMAIN = 'trivelta.com';

-- Find companies using Airflow
SELECT 
    COMPANY_NAME,
    DOMAIN,
    JOBS[0]:orchestration_tools
FROM GTM.PUBLIC.COMPANY_WEB_SIGNALS 
WHERE ARRAY_CONTAINS('Airflow'::VARIANT, JOBS[0]:orchestration_tools);
```

## 🚀 Run Batch Processing

Once a single company test works, try a batch:

```json
{
  "companies": [
    {"company_name": "Trivelta", "domain": "trivelta.com"},
    {"company_name": "GridX", "domain": "gridx.ai"},
    {"company_name": "Databricks", "domain": "databricks.com"}
  ]
}
```

Or create a CSV and use:
```json
{
  "csv_path": "/usr/local/airflow/include/companies.csv"
}
```

## 📊 What the DAG Researches

For each company:
- ✅ Company overview & industry
- ✅ Job postings (last 12 months) with tech stack extraction
- ✅ Acquisitions (last 2 years)
- ✅ Product launches (last 2 years)
- ✅ C-suite hires (last 2 years)
- ✅ Strategic announcements (last 2 years)
- ✅ Company metrics (funding, revenue, growth)

## 🔄 Update Workflow

Make changes and redeploy:
```bash
cd ~/gtm-research-airflow
# Edit files...
./deploy.sh
```

## 📁 Project Files

```
~/gtm-research-airflow/
├── deploy.sh                           # Deploy script
├── setup_env_vars.sh                   # Env vars setup script
├── FINAL_STEPS.md                      # This file
├── QUICK_DEPLOY.md                     # Quick reference
├── DEPLOYMENT_GUIDE.md                 # Full documentation
├── dags/
│   └── company_web_signals_dag_parallel.py
└── include/
    ├── .ssh/
    │   └── rsa_key.p8                  # Snowflake private key
    └── skills/
        └── web-research-company/
            └── company_web_signals.py  # Updated for env vars
```

## 🔗 Important Links

- **Deployment Dashboard**: https://cloud.astronomer.io/cmo8usi269a5b01jud613djgt/deployments/cmobw0oj52tef01ogr69z2wnk
- **Airflow UI**: https://clqe2l32s023l01om0yi2nx2v.astronomer.run/d69z2wnk
- **Deployment ID**: `cmobw0oj52tef01ogr69z2wnk`

## ❓ Troubleshooting

### Docker not running
```bash
open -a Docker
# Wait 30 seconds
docker info  # Should show Docker details
```

### EXA_API_KEY error
Ensure you've set the environment variable in Astro (see "Configure Environment Variables" above).

### Snowflake connection error
- Check that all SNOWFLAKE_* environment variables are set
- Verify private key exists at `include/.ssh/rsa_key.p8`
- Check Snowflake credentials are correct

### DAG not showing in Airflow
- Check deployment logs for parsing errors
- Verify requirements.txt has all dependencies
- Look for import errors in logs

## 🎉 Success Checklist

- [ ] Docker Desktop installed and running
- [ ] Code deployed: `./deploy.sh` completed successfully
- [ ] Environment variables configured (EXA_API_KEY + Snowflake config)
- [ ] Test DAG triggered with single company
- [ ] Results visible in Snowflake `GTM.PUBLIC.COMPANY_WEB_SIGNALS`
- [ ] Ready for batch processing!

---

**Quick Command Reference:**

```bash
# Deploy
cd ~/gtm-research-airflow && ./deploy.sh

# Setup env vars
./setup_env_vars.sh YOUR_EXA_API_KEY

# Check logs
astro deployment logs --deployment-id cmobw0oj52tef01ogr69z2wnk --follow

# Trigger DAG
astro deployment airflow trigger company_web_signals_parallel \
  --deployment-id cmobw0oj52tef01ogr69z2wnk \
  --conf '{"company_name": "X", "domain": "x.com"}'
```
