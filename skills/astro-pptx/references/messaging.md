# Astronomer Messaging, Positioning, and Proof Points

Use this file when building sales, customer-facing, or external decks. Pull stats, narratives,
and customer proof from here rather than making things up.

---

## Core Positioning

**One-liner:** Unified orchestration. The fastest path to trusted data and production AI.

**Company narrative:** Astronomer is the commercial platform for Apache Airflow. We've moved
from "managed Airflow" to "the data engineering company" — the platform that powers the
context layer enterprises need to run AI in production.

**Three product pillars:**
- **BUILD** — Ship faster with AI-native developer tools
- **RUN** — Reliable, performant, enterprise-grade execution
- **OBSERVE** — Full lineage, alerting, data quality, and cost control

**Astro Engine differentiators (vs. MWAA and GCC):**
- 2x parallel load per worker (pipelines stay reliable under spikes)
- 30%+ more DAG runs for the same spend
- 3-4x faster task starts (fresher data, faster)
- 10x delivery speed with AI-driven developer tools
- Intelligent auto-scaling of task-optimized workers
- Faster RCA with built-in lineage, asset catalog, and AI log summaries

---

## Key Industry Stats (cite sources when using in decks)

| Stat | Source |
|------|--------|
| 95% of GenAI pilots fail at achieving measurable AI, often stalling before production | MIT Report, 2025 |
| 32% of Airflow users have GenAI or MLOps use cases in production | Astronomer survey |
| 62% of Astro customers have GenAI/MLOps in production (vs. 32% industry avg.) | Astronomer data |
| 80% of Airflow users are turning to AI to address productivity challenges — only 9% are satisfied | Astronomer survey |
| 46% of organizations say Airflow problems halt their entire operation | Astronomer survey |
| Apache Airflow: 30M monthly downloads, 3K contributors | Apache Foundation |
| 100% of Airflow releases driven by Astronomer | Astronomer |

---

## Competitive Benchmarks (vs. MWAA and GCC)

From internal benchmarking study (Astro vs. GCC vs. MWAA):

- **Max concurrency (Astro Executor): 22** vs. GCC: 11, MWAA: 15, Astro+Celery: 17
- **Workers needed for same workload:** MWAA: 9, GCP: 5, Astro+Celery: 4, Astro+Astro: 5
- Astro Executor handles **double the GCC workload** and **20x the MWAA workload** at max scale
- **85%+ reduction in DAG failures** from Redis faults vs. Celery on OSS/GCC/MWAA
- Astro delivers **30% more DAG runs per dollar** than alternatives at comparable price points
- Concurrency tuning on GCC and MWAA is brittle — Astro has wide tolerance ranges, much more forgiving

Key message: Astro is the most reliable AND most scalable option. MWAA is cheapest at tiny
scale but breaks down under load. GCC caps out early. Astro scales without sharding.

---

## Customer Proof Points

### Autodesk
- **Challenge:** Fragmented environments, complex PII handling across disparate pipelines (Oozie)
- **Solution:** Standardized orchestration, rapid test environment setup, governance, multi-tenancy, CI/CD
- **Results:** 33% faster deployment cycles, 60% reduction in tech debt, 90% data quality increase
- **Quote:** "This success wouldn't have been possible without the powerful capabilities of Astronomer." — Bhavesh Jaisinghani, Data Engineering Manager

### Apache Airflow ecosystem (proof of market)
Uber, Stripe, Apple, OpenAI/ChatGPT, Ford, Wix, Robinhood, Anthropic, LinkedIn, GitHub Copilot, Bloomberg, Notion — all running critical workflows on Airflow.

### Trusted by (Astro customers)
Northern Trust, Adobe, DataStax, Foot Locker, T. Rowe Price, Activision, Autodesk

---

## Narrative Arcs (for structuring decks)

These are the core perception shifts Astronomer drives in customer conversations.

### 1. The AI production problem
- **Before:** 95% of GenAI pilots fail. Teams build experiments, not production systems.
- **After:** Orchestration is the missing layer. It turns AI experiments into production outcomes.
- **Use for:** Executive/economic buyer decks, AI-focused pitches

### 2. Unified control plane
- **Before:** Teams run analytics, ML, and AI on separate platforms with different operating models.
- **After:** One orchestration layer unifies all data and AI workflows. Fewer tools, faster delivery.
- **Use for:** Platform consolidation deals, expansion conversations

### 3. Legacy migration (LegMod)
- **Before:** Migrating off our legacy scheduler feels like a risky, multi-year project.
- **After:** Airflow + Astro is the neutral layer that lets you run anywhere, lock into nothing.
- **Use for:** Displacement of Control-M, Informatica, cron, MWAA, GCC

### 4. Enterprise reliability
- **Before:** Pipeline failures cascade into missed SLAs and lost revenue. We have no DR.
- **After:** Astro delivers HA/DR built in. Pipelines stay running even during infrastructure disruptions.
- **Use for:** Enterprise procurement, security-first accounts, financial services

### 5. AI-native development
- **Before:** Generic AI tools give marginal gains. Manual work still dominates.
- **After:** The entire pipeline lifecycle — dev to monitoring to remediation — is enhanced by AI that understands your specific environment.
- **Use for:** Data engineering teams evaluating developer productivity tools

---

## Q1 FY27 Product Highlights

For roadmap or "what's coming" slides:

| Feature | Status | What it does |
|---------|--------|--------------|
| Sub-Second API-Triggered Pipelines | Q1 Private Preview | <1s startup, <1s inter-task latency. For ML inference, fraud detection, agentic AI. |
| Worker Sizing Recommendation System | Q1 Preview | Proactive right-sizing suggestions to cut costs and improve performance. |
| One-Click Disaster Recovery | Q1 GA (AWS) | Self-service DR, cross-region replication, automated failover and failback. |
| No-Code DAG Authoring | Q1 | Build pipelines without writing Python. Expands Airflow to non-engineers. |
| Astro Private Cloud 2.0 | Q1 | Enhanced private cloud deployment with improved networking and isolation. |
| Root Cause Analysis Agent | Q1 | AI agent that diagnoses pipeline failures and surfaces fixes automatically. |
| Astro AI in the Tools Engineers Use | Q1 | AI assistance in IDE, CLI, and Astronomer UI — Airflow-aware, not generic. |

---

## AI Developer Tooling (from Tech Deck FY27)

Two surfaces, same underlying Airflow intelligence:

| | Astro IDE | Open-Source Agent Tooling |
|--|-----------|---------------------------|
| **Setup** | Zero setup, browser-based | One command install |
| **Strength** | Integrated testing, CI/CD, one-click deploys | Full control over environment and model choice |
| **Ideal for** | Onboarding, guided workflows, teams new to Airflow | Local-first workflows, teams with approved AI tooling |
| **Works in** | Astro platform | Claude Code, Cursor, VS Code, 25+ other tools |

Both share: DAG authoring/testing/debugging, Airflow 2→3 migration, data lineage tracing, human-in-the-loop workflows, table profiling.

Key stat: **80% of Airflow users are turning to AI to write DAGs faster, but generic tools fail** because they don't know your connections, existing DAGs, or Airflow best practices.

---

## Build vs. Buy — TCO Framing

Use when displacing OSS Airflow or making the case against "just use MWAA":

**The hidden costs of OSS Airflow:**
- Set up Kubernetes/Celery cluster, configure monitoring (Prometheus/Grafana), manually scale nodes, clean metadata DB — all ops overhead that compounds
- Upgrade a new Airflow version: investigate impact, set up test env, coordinate prod window, manual rollback if needed — teams defer upgrades for months

**The hidden costs of MWAA/GCC:**
- MWAA local runner is buggy; setup complexity wastes hours before writing a single DAG
- GCC: limited local dev tools, manual CI/CD via cloud storage upload
- Neither supports in-place Airflow 2.x → 3.x upgrades; no rollback support
- MWAA/GCC SLA covers infrastructure only — not the Airflow service itself

**With Astro:**
- Dev to production: define Snowflake connection in Environment Manager once, write DAG in IDE with AI, test in-browser, one-click deploy
- Upgrades: in-place, zero downtime, built-in rollback
- SLA covers the Airflow service (99.5%), not just infra

**Discovery questions for TCO conversations:**
- "How many Airflow environments do you run, and what's monthly infra spend across dev/staging/prod?"
- "How many engineers are dedicated to managing Airflow vs. building pipelines?"
- "When was your last Airflow upgrade, and what prevented you from doing it more frequently?"
- "How many pipeline failures per week, and how much engineering time goes into resolving them?"

---

## Feature Entitlements by Tier

For sizing and proposal conversations. Key differences that drive tier decisions:

| Feature | Team | Business | Enterprise | Enterprise Business Critical |
|---------|------|----------|------------|------------------------------|
| SSO Enforcement | | ✓ | ✓ | ✓ |
| CI/CD Enforcement | | ✓ | ✓ | ✓ |
| DAG-level RBAC | | | ✓ | ✓ |
| IP Access List | | | ✓ | ✓ |
| SCIM | | | ✓ | ✓ |
| Executive Dashboards | | | ✓ | ✓ |
| Disaster Recovery | | | | ✓ |
| Support availability | 24x5 | 24x7 | 24x7 | 24x7 |
| Initial response SLA | 6 hours | 1 hour | 1 hour | 30 minutes |

**Tier selection shortcut:**
- Need SSO or CI/CD enforcement → Business minimum
- Multiple teams, DAG-level access control, or compliance requirements → Enterprise
- DR requirement or <30 min SLA → Enterprise Business Critical
- "How critical are these pipelines when something breaks?" is the right framing question for tier selection

---

## Key Personas

| Persona | What they care about | How to speak to them |
|---------|---------------------|---------------------|
| Data engineer | Reliability, developer experience, not getting paged at 2am | Technical, specific, outcome-focused. Show you understand Airflow deeply. |
| Platform / data platform team | Governance, cost control, enterprise-wide standards | Unified control plane, security, observability, scalability. |
| VP/Director of Data (economic buyer) | AI strategy, time to value, competitive pressure | Business outcomes, ROI, risk reduction. Use the stat-heavy slides. |

---

## What to Avoid in Copy

- No em dashes. Use periods or commas.
- No "leverage," "synergize," "best-in-class," "world-class," "game-changing."
- Don't say "managed Airflow" — say "commercial Airflow platform" or "the data engineering company."
- Don't say "Astronomer provides" — say "Astro" or be direct about the outcome.
- Avoid passive voice in headers.
