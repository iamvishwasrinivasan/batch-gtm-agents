# Quick Deploy Guide - GTM Company Research to Astro

Your Astro deployment is created! Here's how to deploy your DAG.

## ✅ Deployment Created

- **Name**: GTM Company Research
- **Deployment ID**: `cmobw0oj52tef01ogr69z2wnk`
- **Airflow UI**: https://clqe2l32s023l01om0yi2nx2v.astronomer.run/d69z2wnk
- **Dashboard**: https://cloud.astronomer.io/cmo8usi269a5b01jud613djgt/deployments/cmobw0oj52tef01ogr69z2wnk

## Option 1: Deploy via Astro CLI (Recommended)

### 1. Install Docker Desktop

Since Podman had issues, install Docker Desktop:
```bash
brew install --cask docker
```

Then open Docker Desktop app and wait for it to start.

### 2. Deploy

```bash
cd ~/gtm-research-airflow
export ASTRO_API_TOKEN="eyJhbGciOiJSUzI1NiIsImtpZCI6ImNsb2Q0aGtqejAya3AwMWozdWNqbzJwOHIiLCJ0eXAiOiJKV1QifQ.eyJhcGlUb2tlbklkIjoiY21vYnZ0cGFqMnQ4djAxbnIyMW5lbG5mZyIsImF1ZCI6ImFzdHJvbm9tZXItZWUiLCJpYXQiOjE3NzY5NzI5NjgsImlzQXN0cm9ub21lckdlbmVyYXRlZCI6dHJ1ZSwiaXNJbnRlcm5hbCI6ZmFsc2UsImlzcyI6Imh0dHBzOi8vYXBpLmFzdHJvbm9tZXIuaW8iLCJraWQiOiJjbG9kNGhranowMmtwMDFqM3Vjam8ycDhyIiwicGVybWlzc2lvbnMiOlsiYXBpVG9rZW5JZDpjbW9idnRwYWoydDh2MDFucjIxbmVsbmZnIiwid29ya3NwYWNlSWQ6Y21vOHVzaTI2OWE1YjAxanVkNjEzZGpndCIsIm9yZ2FuaXphdGlvbklkOmNscWUybDMyczAyM2wwMW9tMHlpMm54MnYiLCJvcmdTaG9ydE5hbWU6Y2xxZTJsMzJzMDIzbDAxb20weWkybngydiJdLCJzY29wZSI6ImFwaVRva2VuSWQ6Y21vYnZ0cGFqMnQ4djAxbnIyMW5lbG5mZyB3b3Jrc3BhY2VJZDpjbW84dXNpMjY5YTViMDFqdWQ2MTNkamd0IG9yZ2FuaXphdGlvbklkOmNscWUybDMyczAyM2wwMW9tMHlpMm54MnYgb3JnU2hvcnROYW1lOmNscWUybDMyczAyM2wwMW9tMHlpMm54MnYiLCJzdWIiOiJjbWFlZDF1cXgwZHI2MDFtZ3duOTJ4Zm52IiwidmVyc2lvbiI6ImNtb2J2dHBhajJ0OHUwMW5yeDg3NjdtN3MifQ.A6udmBw5-Aouap7hF8n4R1UI0tiT4ddFOQzu-zLm-UVLtTEZ3kUQHYnR6uYICcXWq7d-YVFlpP-SSH1MDWyCm-OQGCaBBpz1DW6ot29h2Coy1x5UuL-dwZ6tUXeJsLYxoxDbEF9v552pRjRoPoI691HMUeLHOC0BfmHJtwMShSkMcZ01ZFhH252aNAL6LRHDo439-C1INosRtFA03Vqo2ZTjFCa-AMm4wR3Y_j9Uo5QVfBOuTU-uYB6T1JG5IU6LIVdAkh4pFnC7VMmqsTLl1HhlPoAIs1J2Zkm5HeMGR3gQSGignVwq0zyum42Q0Xk1SYhJeijAQooWpXxqTfqLPA"

astro deploy cmobw0oj52tef01ogr69z2wnk
```

This will:
1. Build the Docker image with your DAG and dependencies
2. Push it to Astro
3. Deploy in ~2-3 minutes

## Option 2: Deploy via Astro Cloud UI (If Docker fails)

### 1. Package your files

```bash
cd ~/gtm-research-airflow
zip -r gtm-research-deploy.zip dags/ include/ requirements.txt
```

### 2. Deploy via UI

1. Go to: https://cloud.astronomer.io/cmo8usi269a5b01jud613djgt/deployments/cmobw0oj52tef01ogr69z2wnk
2. Click "Deploy" → "Deploy Code"
3. Upload `gtm-research-deploy.zip`

**Note**: Astro Cloud prefers CLI deploys, so Option 1 is better if you can get Docker working.

## 🔑 Configure Environment Variables

Before running the DAG, you MUST add environment variables:

### Via Astro Cloud UI (Easiest)

1. Go to: https://cloud.astronomer.io/cmo8usi269a5b01jud613djgt/deployments/cmobw0oj52tef01ogr69z2wnk
2. Click "Environment" tab
3. Add these variables:

| Key | Value | Secret |
|-----|-------|--------|
| `EXA_API_KEY` | your-exa-api-key | ✅ Yes |
| `SNOWFLAKE_ACCOUNT` | GP21411.us-east-1 | ❌ No |
| `SNOWFLAKE_USER` | VISHWASRINIVASAN | ❌ No |
| `SNOWFLAKE_ROLE` | GTMADMIN | ❌ No |
| `SNOWFLAKE_WAREHOUSE` | HUMANS | ❌ No |
| `SNOWFLAKE_DATABASE` | GTM | ❌ No |

4. Click "Save" and restart the deployment

### Via Astro CLI

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

## 🔐 Add Snowflake Private Key

You need to make your Snowflake private key accessible to the deployment.

### Option A: Copy to include/ directory (Easier)

```bash
cd ~/gtm-research-airflow

# Create directory
mkdir -p include/.ssh

# Copy private key
cp ~/.ssh/rsa_key_unencrypted.p8 include/.ssh/rsa_key.p8

# Update company_web_signals.py to use the new path
```

Then edit `include/skills/web-research-company/company_web_signals.py`:

Find this line (around line 52):
```python
private_key_path = Path(self.sf_config['private_key_path']).expanduser()
```

Replace with:
```python
# In Astro, use environment variable or hardcoded path
private_key_path = Path(os.getenv('SNOWFLAKE_PRIVATE_KEY_PATH', '/usr/local/airflow/include/.ssh/rsa_key.p8'))
```

And update the Snowflake config loading (around line 47):
```python
# Read from environment variables instead of YAML
self.sf_config = {
    'account': os.getenv('SNOWFLAKE_ACCOUNT'),
    'user': os.getenv('SNOWFLAKE_USER'),
    'private_key_path': os.getenv('SNOWFLAKE_PRIVATE_KEY_PATH', '/usr/local/airflow/include/.ssh/rsa_key.p8'),
    'role': os.getenv('SNOWFLAKE_ROLE', 'GTMADMIN'),
    'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE', 'HUMANS'),
    'database': os.getenv('SNOWFLAKE_DATABASE', 'GTM')
}
```

**IMPORTANT**: Add to `.gitignore`:
```bash
echo "include/.ssh/" >> .gitignore
```

Then redeploy:
```bash
astro deploy cmobw0oj52tef01ogr69z2wnk
```

### Option B: Use Airflow Connections (More secure)

Create a Snowflake connection in Airflow UI and update the script to use it. This is more complex but better for production.

## ✅ Verify Deployment

### Check deployment status:
```bash
astro deployment list
```

### View logs:
```bash
astro deployment logs --deployment-id cmobw0oj52tef01ogr69z2wnk --follow
```

### Access Airflow UI:
Go to: https://clqe2l32s023l01om0yi2nx2v.astronomer.run/d69z2wnk

Login with the credentials shown in the Astro Cloud dashboard.

## 🚀 Run Your First DAG

### Via Airflow UI:

1. Go to Airflow UI: https://clqe2l32s023l01om0yi2nx2v.astronomer.run/d69z2wnk
2. Find `company_web_signals_parallel` DAG
3. Click the play button → "Trigger DAG w/ config"
4. Enter JSON:
   ```json
   {
     "company_name": "Trivelta",
     "domain": "trivelta.com"
   }
   ```
5. Click "Trigger"

### Via Astro CLI:

```bash
astro deployment airflow trigger company_web_signals_parallel \
  --deployment-id cmobw0oj52tef01ogr69z2wnk \
  --conf '{"company_name": "Trivelta", "domain": "trivelta.com"}'
```

## 🔍 Check Results in Snowflake

```sql
SELECT 
    COMPANY_NAME, 
    DOMAIN, 
    RESEARCH_DATE,
    ARRAY_SIZE(JOBS) as job_count
FROM GTM.PUBLIC.COMPANY_WEB_SIGNALS 
ORDER BY RESEARCH_DATE DESC 
LIMIT 10;
```

## 📝 Summary of What We Created

**Project location**: `~/gtm-research-airflow/`

**Files**:
- `dags/company_web_signals_dag_parallel.py` - The Airflow DAG
- `include/skills/web-research-company/company_web_signals.py` - Research logic
- `requirements.txt` - Python dependencies
- `.env` - Local environment variables (not deployed)

**Deployment**:
- Name: GTM Company Research
- ID: cmobw0oj52tef01ogr69z2wnk
- Region: eastus2 (Azure)
- Runtime: Airflow 3.2.0

## 🔧 Next Steps

1. **Install Docker Desktop** (if using Option 1)
2. **Deploy the code**: `astro deploy cmobw0oj52tef01ogr69z2wnk`
3. **Add environment variables** via Astro Cloud UI
4. **Update Snowflake config** in `company_web_signals.py` to use env vars
5. **Copy private key** to `include/.ssh/`
6. **Redeploy** after making changes
7. **Test with a single company** first
8. **Scale to batch processing**

## 📚 Additional Resources

- **Astro Docs**: https://www.astronomer.io/docs/astro/
- **Your Dashboard**: https://cloud.astronomer.io/cmo8usi269a5b01jud613djgt/deployments/cmobw0oj52tef01ogr69z2wnk
- **Airflow UI**: https://clqe2l32s023l01om0yi2nx2v.astronomer.run/d69z2wnk
- **Full Deployment Guide**: See `DEPLOYMENT_GUIDE.md` in this folder

---

**Need Help?**
- Check deployment logs: `astro deployment logs --deployment-id cmobw0oj52tef01ogr69z2wnk`
- View Airflow UI for DAG errors
- Check that all environment variables are set
