#!/bin/bash
# Deploy Company Web Signals DAG to Astro

set -e

echo "🚀 Deploying GTM Company Research to Astro"
echo "============================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running!"
    echo ""
    echo "Please:"
    echo "1. Install Docker Desktop: brew install --cask docker"
    echo "2. Open Docker Desktop and wait for it to start"
    echo "3. Run this script again"
    exit 1
fi

echo "✓ Docker is running"

# Set API token
export ASTRO_API_TOKEN="eyJhbGciOiJSUzI1NiIsImtpZCI6ImNsb2Q0aGtqejAya3AwMWozdWNqbzJwOHIiLCJ0eXAiOiJKV1QifQ.eyJhcGlUb2tlbklkIjoiY21vYnZ0cGFqMnQ4djAxbnIyMW5lbG5mZyIsImF1ZCI6ImFzdHJvbm9tZXItZWUiLCJpYXQiOjE3NzY5NzI5NjgsImlzQXN0cm9ub21lckdlbmVyYXRlZCI6dHJ1ZSwiaXNJbnRlcm5hbCI6ZmFsc2UsImlzcyI6Imh0dHBzOi8vYXBpLmFzdHJvbm9tZXIuaW8iLCJraWQiOiJjbG9kNGhranowMmtwMDFqM3Vjam8ycDhyIiwicGVybWlzc2lvbnMiOlsiYXBpVG9rZW5JZDpjbW9idnRwYWoydDh2MDFucjIxbmVsbmZnIiwid29ya3NwYWNlSWQ6Y21vOHVzaTI2OWE1YjAxanVkNjEzZGpndCIsIm9yZ2FuaXphdGlvbklkOmNscWUybDMyczAyM2wwMW9tMHlpMm54MnYiLCJvcmdTaG9ydE5hbWU6Y2xxZTJsMzJzMDIzbDAxb20weWkybngydiJdLCJzY29wZSI6ImFwaVRva2VuSWQ6Y21vYnZ0cGFqMnQ4djAxbnIyMW5lbG5mZyB3b3Jrc3BhY2VJZDpjbW84dXNpMjY5YTViMDFqdWQ2MTNkamd0IG9yZ2FuaXphdGlvbklkOmNscWUybDMyczAyM2wwMW9tMHlpMm54MnYgb3JnU2hvcnROYW1lOmNscWUybDMyczAyM2wwMW9tMHlpMm54MnYiLCJzdWIiOiJjbWFlZDF1cXgwZHI2MDFtZ3duOTJ4Zm52IiwidmVyc2lvbiI6ImNtb2J2dHBhajJ0OHUwMW5yeDg3NjdtN3MifQ.A6udmBw5-Aouap7hF8n4R1UI0tiT4ddFOQzu-zLm-UVLtTEZ3kUQHYnR6uYICcXWq7d-YVFlpP-SSH1MDWyCm-OQGCaBBpz1DW6ot29h2Coy1x5UuL-dwZ6tUXeJsLYxoxDbEF9v552pRjRoPoI691HMUeLHOC0BfmHJtwMShSkMcZ01ZFhH252aNAL6LRHDo439-C1INosRtFA03Vqo2ZTjFCa-AMm4wR3Y_j9Uo5QVfBOuTU-uYB6T1JG5IU6LIVdAkh4pFnC7VMmqsTLl1HhlPoAIs1J2Zkm5HeMGR3gQSGignVwq0zyum42Q0Xk1SYhJeijAQooWpXxqTfqLPA"

echo "✓ API token set"

# Deploy
echo ""
echo "📦 Building and deploying..."
echo "This will take 2-3 minutes..."
echo ""

astro deploy cmobw0oj52tef01ogr69z2wnk

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🔗 Next steps:"
echo "1. Go to: https://cloud.astronomer.io/cmo8usi269a5b01jud613djgt/deployments/cmobw0oj52tef01ogr69z2wnk"
echo "2. Click 'Environment' tab"
echo "3. Add environment variables:"
echo "   - EXA_API_KEY (your Exa API key) - mark as Secret"
echo "   - SNOWFLAKE_ACCOUNT = GP21411.us-east-1"
echo "   - SNOWFLAKE_USER = VISHWASRINIVASAN"
echo "   - SNOWFLAKE_ROLE = GTMADMIN"
echo "   - SNOWFLAKE_WAREHOUSE = HUMANS"
echo "   - SNOWFLAKE_DATABASE = GTM"
echo "4. Save and wait for deployment to restart (~1 min)"
echo "5. Open Airflow: https://clqe2l32s023l01om0yi2nx2v.astronomer.run/d69z2wnk"
echo "6. Trigger 'company_web_signals_parallel' DAG with config:"
echo "   {\"company_name\": \"Trivelta\", \"domain\": \"trivelta.com\"}"
echo ""
echo "📊 Check results in Snowflake:"
echo "SELECT * FROM GTM.PUBLIC.COMPANY_WEB_SIGNALS ORDER BY RESEARCH_DATE DESC LIMIT 10;"
