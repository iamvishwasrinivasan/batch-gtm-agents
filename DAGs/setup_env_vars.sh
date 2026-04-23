#!/bin/bash
# Set up environment variables for Astro deployment

set -e

DEPLOYMENT_ID="cmobw0oj52tef01ogr69z2wnk"

export ASTRO_API_TOKEN="eyJhbGciOiJSUzI1NiIsImtpZCI6ImNsb2Q0aGtqejAya3AwMWozdWNqbzJwOHIiLCJ0eXAiOiJKV1QifQ.eyJhcGlUb2tlbklkIjoiY21vYnZ0cGFqMnQ4djAxbnIyMW5lbG5mZyIsImF1ZCI6ImFzdHJvbm9tZXItZWUiLCJpYXQiOjE3NzY5NzI5NjgsImlzQXN0cm9ub21lckdlbmVyYXRlZCI6dHJ1ZSwiaXNJbnRlcm5hbCI6ZmFsc2UsImlzcyI6Imh0dHBzOi8vYXBpLmFzdHJvbm9tZXIuaW8iLCJraWQiOiJjbG9kNGhranowMmtwMDFqM3Vjam8ycDhyIiwicGVybWlzc2lvbnMiOlsiYXBpVG9rZW5JZDpjbW9idnRwYWoydDh2MDFucjIxbmVsbmZnIiwid29ya3NwYWNlSWQ6Y21vOHVzaTI2OWE1YjAxanVkNjEzZGpndCIsIm9yZ2FuaXphdGlvbklkOmNscWUybDMyczAyM2wwMW9tMHlpMm54MnYiLCJvcmdTaG9ydE5hbWU6Y2xxZTJsMzJzMDIzbDAxb20weWkybngydiJdLCJzY29wZSI6ImFwaVRva2VuSWQ6Y21vYnZ0cGFqMnQ4djAxbnIyMW5lbG5mZyB3b3Jrc3BhY2VJZDpjbW84dXNpMjY5YTViMDFqdWQ2MTNkamd0IG9yZ2FuaXphdGlvbklkOmNscWUybDMyczAyM2wwMW9tMHlpMm54MnYgb3JnU2hvcnROYW1lOmNscWUybDMyczAyM2wwMW9tMHlpMm54MnYiLCJzdWIiOiJjbWFlZDF1cXgwZHI2MDFtZ3duOTJ4Zm52IiwidmVyc2lvbiI6ImNtb2J2dHBhajJ0OHUwMW5yeDg3NjdtN3MifQ.A6udmBw5-Aouap7hF8n4R1UI0tiT4ddFOQzu-zLm-UVLtTEZ3kUQHYnR6uYICcXWq7d-YVFlpP-SSH1MDWyCm-OQGCaBBpz1DW6ot29h2Coy1x5UuL-dwZ6tUXeJsLYxoxDbEF9v552pRjRoPoI691HMUeLHOC0BfmHJtwMShSkMcZ01ZFhH252aNAL6LRHDo439-C1INosRtFA03Vqo2ZTjFCa-AMm4wR3Y_j9Uo5QVfBOuTU-uYB6T1JG5IU6LIVdAkh4pFnC7VMmqsTLl1HhlPoAIs1J2Zkm5HeMGR3gQSGignVwq0zyum42Q0Xk1SYhJeijAQooWpXxqTfqLPA"

echo "🔑 Setting up environment variables for Astro deployment"
echo "========================================================="
echo ""

# Check if EXA_API_KEY is provided
if [ -z "$1" ]; then
    echo "❌ Error: Please provide your EXA_API_KEY as the first argument"
    echo ""
    echo "Usage: ./setup_env_vars.sh YOUR_EXA_API_KEY"
    echo ""
    echo "Example:"
    echo "  ./setup_env_vars.sh exa_abc123xyz"
    exit 1
fi

EXA_KEY="$1"

echo "Creating environment variables..."
echo ""

# EXA_API_KEY (secret)
echo "→ Setting EXA_API_KEY..."
astro deployment variable create \
  --deployment-id "$DEPLOYMENT_ID" \
  --key EXA_API_KEY \
  --value "$EXA_KEY" \
  --secret

# Snowflake variables
echo "→ Setting SNOWFLAKE_ACCOUNT..."
astro deployment variable create \
  --deployment-id "$DEPLOYMENT_ID" \
  --key SNOWFLAKE_ACCOUNT \
  --value "GP21411.us-east-1"

echo "→ Setting SNOWFLAKE_USER..."
astro deployment variable create \
  --deployment-id "$DEPLOYMENT_ID" \
  --key SNOWFLAKE_USER \
  --value "VISHWASRINIVASAN"

echo "→ Setting SNOWFLAKE_ROLE..."
astro deployment variable create \
  --deployment-id "$DEPLOYMENT_ID" \
  --key SNOWFLAKE_ROLE \
  --value "GTMADMIN"

echo "→ Setting SNOWFLAKE_WAREHOUSE..."
astro deployment variable create \
  --deployment-id "$DEPLOYMENT_ID" \
  --key SNOWFLAKE_WAREHOUSE \
  --value "HUMANS"

echo "→ Setting SNOWFLAKE_DATABASE..."
astro deployment variable create \
  --deployment-id "$DEPLOYMENT_ID" \
  --key SNOWFLAKE_DATABASE \
  --value "GTM"

echo ""
echo "✅ Environment variables configured!"
echo ""
echo "The deployment will restart automatically in ~1 minute."
echo ""
echo "🔗 Next: Open Airflow and test the DAG"
echo "   https://clqe2l32s023l01om0yi2nx2v.astronomer.run/d69z2wnk"
