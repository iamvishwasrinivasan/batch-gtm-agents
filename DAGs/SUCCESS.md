# 🎉 Deployment Successful!

Your Company Web Signals DAG is now live on Astro!

## ✅ What's Deployed

- **DAG**: `company_web_signals_parallel` with parallel processing
- **Skill**: `web-research-company` code in `include/`
- **SSH Key**: Snowflake private key for authentication
- **Environment Variables**: All configured ✓

## 🔗 Access Your Deployment

**Airflow UI**: https://cmobw0oj52tef01ogr69z2wnk.nk.astronomer.run/d69z2wnk

**Deployment Dashboard**: https://cloud.astronomer.io/cmo8usi269a5b01jud613djgt/deployments/cmobw0oj52tef01ogr69z2wnk

## 🚀 Test Your DAG

### Option 1: Via Airflow UI (Recommended)

1. Go to: https://cmobw0oj52tef01ogr69z2wnk.nk.astronomer.run/d69z2wnk
2. Find the `company_web_signals_parallel` DAG
3. Click the **▶️ play button** → "Trigger DAG w/ config"
4. Enter this test config:
   ```json
   {
     "company_name": "Trivelta",
     "domain": "trivelta.com"
   }
   ```
5. Click **Trigger**
6. Watch the DAG run (takes ~30-60 seconds)

### Option 2: Via CLI

```bash
export ASTRO_API_TOKEN="your-token"
astro deployment airflow trigger company_web_signals_parallel \
  --deployment-id cmobw0oj52tef01ogr69z2wnk \
  --conf '{"company_name": "Trivelta", "domain": "trivelta.com"}'
```

## 🔍 Check Results in Snowflake

After the DAG runs successfully:

```sql
-- View the research
SELECT 
    COMPANY_NAME, 
    DOMAIN, 
    RESEARCH_DATE,
    ARRAY_SIZE(JOBS) as jobs_found,
    ARRAY_SIZE(MAJOR_ANNOUNCEMENTS) as announcements,
    ARRAY_SIZE(PRODUCT_RELEASES) as products,
    ARRAY_SIZE(C_SUITE_HIRES) as hires
FROM GTM.PUBLIC.COMPANY_WEB_SIGNALS 
WHERE DOMAIN = 'trivelta.com'
ORDER BY RESEARCH_DATE DESC;

-- Check tech stack
SELECT 
    COMPANY_NAME,
    JOBS[0]:orchestration_tools AS orchestration_tools,
    JOBS[0]:data_tools AS data_tools
FROM GTM.PUBLIC.COMPANY_WEB_SIGNALS 
WHERE DOMAIN = 'trivelta.com';

-- Find all companies using Airflow
SELECT 
    COMPANY_NAME,
    DOMAIN
FROM GTM.PUBLIC.COMPANY_WEB_SIGNALS 
WHERE ARRAY_CONTAINS('Airflow'::VARIANT, JOBS[0]:orchestration_tools);
```

## 📊 What Gets Researched

For each company:
- ✅ Company overview & industry
- ✅ Job postings (last 12 months) with tech stack extraction
  - Orchestration: Airflow, Dagster, Prefect, Mage, Luigi
  - Data tools: dbt, Snowflake, Databricks, BigQuery, etc.
- ✅ Major announcements (last 2 years)
- ✅ Product releases (last 2 years)
- ✅ C-suite hires (last 2 years)
- ✅ Strategic announcements (last 2 years)
- ✅ Company metrics (funding, revenue, growth)

## 🚀 Batch Processing

Once a single company works, try batch mode:

### Multiple companies:
```json
{
  "companies": [
    {"company_name": "Trivelta", "domain": "trivelta.com"},
    {"company_name": "GridX", "domain": "gridx.ai"},
    {"company_name": "Databricks", "domain": "databricks.com"}
  ]
}
```

### CSV file:
1. Create `companies.csv`:
   ```csv
   company_name,domain
   Trivelta,trivelta.com
   GridX,gridx.ai
   Databricks,databricks.com
   ```
2. Upload to deployment (via include/ or mount)
3. Trigger with:
   ```json
   {
     "csv_path": "/usr/local/airflow/include/companies.csv"
   }
   ```

## 🔄 Updating the DAG

Make changes locally and redeploy:

```bash
cd ~/gtm-research-airflow

# Make your changes...

# Deploy
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
export ASTRO_API_TOKEN="your-token"
astro deploy cmobw0oj52tef01ogr69z2wnk
```

## 📈 Monitoring

### Check deployment logs:
```bash
astro deployment logs --deployment-id cmobw0oj52tef01ogr69z2wnk --follow
```

### View DAG runs:
Go to Airflow UI → DAGs → company_web_signals_parallel → Graph

### Check task logs:
Click on any task in the Graph view to see detailed logs

## 🐛 Troubleshooting

### "EXA_API_KEY not found"
- Check environment variables are set in deployment
- Go to Dashboard → Environment tab

### "Snowflake connection failed"
- Verify all SNOWFLAKE_* env vars are set
- Check private key exists at `include/.ssh/rsa_key.p8`

### "Module not found: company_web_signals"
- Verify `include/skills/web-research-company/company_web_signals.py` exists
- Check deployment logs for errors

### DAG not showing
- Wait 1-2 minutes after deployment
- Check for parsing errors in Airflow UI
- View deployment logs

## 📝 Environment Variables Configured

✅ `EXA_API_KEY` - Your Exa API key (secret)  
✅ `SNOWFLAKE_ACCOUNT` - GP21411.us-east-1  
✅ `SNOWFLAKE_USER` - VISHWASRINIVASAN  
✅ `SNOWFLAKE_ROLE` - GTMADMIN  
✅ `SNOWFLAKE_WAREHOUSE` - HUMANS  
✅ `SNOWFLAKE_DATABASE` - GTM  

## 🎯 Next Steps

1. ✅ **Test with a single company** (Trivelta)
2. ✅ **Check results in Snowflake**
3. ✅ **Try batch mode** with 3-5 companies
4. ✅ **Integrate into your workflow**

## 📚 Project Files

All files are in: `~/gtm-research-airflow/`

Key files:
- `dags/company_web_signals_dag_parallel.py` - The DAG
- `include/skills/web-research-company/company_web_signals.py` - Research logic
- `include/.ssh/rsa_key.p8` - Snowflake auth key
- `requirements.txt` - Python dependencies
- `Dockerfile` - Container configuration

## 🎉 Success Checklist

- [x] Astro project created
- [x] Deployment created on Astro
- [x] DAG deployed successfully
- [x] Environment variables configured
- [x] Snowflake private key included
- [ ] Test DAG with single company ← **DO THIS NEXT**
- [ ] Verify results in Snowflake
- [ ] Run batch processing

---

**Ready to test!** Go to the Airflow UI and trigger your first company research:
👉 https://cmobw0oj52tef01ogr69z2wnk.nk.astronomer.run/d69z2wnk
