# Airflow Mission Critical Assessment Framework

Evaluate how mission-critical Apache Airflow is to a company's operations using this scoring framework.

---

## Scoring Scale

### **Grade A: Real-Time Critical** 🔴
**Definition**: Airflow downtime = immediate customer-facing outage

**Criteria:**
- Customer-facing applications depend on Airflow-orchestrated pipelines in real-time
- Sub-minute or sub-second latency requirements
- Airflow orchestrates streaming/near-real-time data flows
- Revenue directly tied to pipeline uptime (e.g., fraud detection, recommendation engines)

**Examples:**
- Real-time fraud detection systems
- Live recommendation engines
- Streaming analytics platforms
- Real-time bidding/advertising platforms

**Airflow Criticality**: **High**

---

### **Grade B: Mission-Critical Stack** 🟡
**Definition**: Airflow downtime delays operations and impacts SLAs

**Criteria:**
- Core business operations depend on Airflow pipelines (but not real-time)
- Pipeline failures delay customer deliverables (hours to days)
- Used for mission-critical batch workflows (ETL, reporting, ML training)
- Tech stack shows deep integration (Snowflake + dbt + Airflow pattern)
- Customer SLAs tied to data freshness

**Examples:**
- Daily reporting dashboards
- ML model training pipelines
- Customer data warehouse refreshes
- Political campaign data updates (T+1 delivery)

**Airflow Criticality**: **Medium to High**

---

### **Grade C: Operational Tool** 🟢
**Definition**: Airflow is used but not mission-critical

**Criteria:**
- Airflow orchestrates nice-to-have workflows
- Pipeline failures are inconvenient but not blocking
- Used for internal analytics, not customer-facing
- Could be replaced without major business disruption
- Mentioned in tech stack but not in product descriptions

**Examples:**
- Internal reporting pipelines
- Ad-hoc data analysis workflows
- Non-critical ETL jobs
- Development/testing environments only

**Airflow Criticality**: **Low to Medium**

---

### **Grade D: No Evidence** ⚪
**Definition**: No confirmed Airflow usage

**Criteria:**
- No mentions in job descriptions, blog posts, or tech stack
- No orchestration patterns detected
- May use alternative tools (Dagster, Prefect, Luigi) or no orchestration

**Airflow Criticality**: **None**

---

## Assessment Template

Use this structure for your assessment:

```markdown
## Airflow Mission Critical Assessment

### Score: **[A/B/C/D] ([Grade Name])**

### Airflow Criticality: **[High/Medium/Low/None]**

### The "Why":

[Company name] operates a **[business model description]** where [explain data pipeline criticality]. However, Airflow appears to serve as **[role description]** rather than **[alternative role]**. **(VERIFIED)**

**Evidence for [Criticality Level]**:

1. **[Evidence Category]**: [Company]'s tech stack [explicitly includes / mentions / references] Apache Airflow [context]. **(VERIFIED)**
   - [Supporting detail from job description/blog/etc.]
   - [Quote or specific evidence]

2. **[Business Model Pattern]**: The company [describe batch vs real-time patterns]:
   - "[Quote about data refresh cycles]" **(VERIFIED)**
   - "[Quote about update frequency]" **(VERIFIED)**
   - This indicates [scheduled batch / real-time / hybrid] pipeline execution.

3. **[Customer Impact Analysis]**: [Company]'s core value proposition includes [describe]:
   - [Use case 1] **(VERIFIED)**
   - [Use case 2] **(VERIFIED)**
   - These workflows operate on [seconds/minutes/hours/days] timescales, not [alternative timescale].

4. **[Tech Stack Integration]**: [Company] uses [complementary technologies] alongside Airflow:
   - [Tech 1] (for [purpose]) **(VERIFIED)**
   - [Tech 2] (for [purpose]) **(VERIFIED)**
   - This suggests Airflow [orchestrates / executes / monitors] data processing.

5. **[Data Freshness SLAs]**: [If available from research]
   - [Data type]: "[Update frequency]" **(VERIFIED)**
   - [Customer expectation]: [T+0 / T+1 / T+7 delivery]

**Business Model Context**: [Company] serves [customer segments] who need [accurate/fast/comprehensive] data for [decision timescale]. The platform enables "[quoted value prop]" through [batch-processed / real-time / hybrid] data operations. **(VERIFIED)**

**Conclusion**: Airflow is [mission-critical / important / supplementary] to **[Company]'s [specific workflows]** but serves a **[primary / supporting / experimental] role**. Pipeline failures would [immediate impact / delay / inconvenience] [customer operations / internal analytics / product development], but [would / wouldn't] immediately halt customer operations. The real "mission-critical engine" is [core system], with Airflow orchestrating the pipelines that [keep it current / feed it / monitor it].
```

---

## Evidence Hierarchy (Strongest to Weakest)

1. **Job descriptions mentioning Airflow** ✅ STRONGEST
   - "Maintain Apache Airflow DAGs for data pipelines"
   - "Debug Airflow workflow failures"

2. **Engineering blog posts about Airflow architecture** ✅ STRONG
   - "We migrated from Cron to Airflow to orchestrate..."
   - "How we scaled Airflow to 10,000 DAGs"

3. **Case studies mentioning data pipelines** ✅ MODERATE
   - "Daily data refreshes powered by..."
   - Customer quotes about data latency

4. **Tech stack aggregators** ✅ MODERATE
   - BuiltWith, StackShare, Datanyze listings
   - GitHub repository dependencies

5. **Conference talks / presentations** ✅ MODERATE
   - "Our team uses Airflow for..."

6. **News articles mentioning data infrastructure** ✅ WEAK
   - Indirect references without specifics

7. **Social media / Twitter mentions** ✅ WEAK
   - Employee tweets about using Airflow

---

## Key Questions to Answer

1. **Is Airflow confirmed in use?** (CONFIRMED / LIKELY / NOT FOUND)
2. **What does Airflow orchestrate?** (ETL, ML training, reporting, etc.)
3. **What's the customer impact window?** (seconds, minutes, hours, days)
4. **Is it batch or streaming?** (Scheduled DAGs vs continuous)
5. **What's the complementary stack?** (Snowflake, dbt, Spark, etc.)
6. **What happens if Airflow goes down?**
   - Customers immediately impacted? → Grade A
   - Delayed deliverables / missed SLAs? → Grade B
   - Internal inconvenience only? → Grade C

---

## Examples from Real Assessments

### Example 1: i360 (Grade B)
- **Evidence**: Job description: "Experience with Apache Airflow"
- **Business model**: Political data analytics with T+1 delivery SLAs
- **Data patterns**: "Daily model updates", "Monthly phone updates"
- **Stack**: Snowflake + dbt + Airflow → classic batch ETL pattern
- **Conclusion**: Mission-critical for data refresh, but batch-oriented (not real-time)

### Example 2: Grindr (Grade A/B - needs more evidence)
- **Evidence**: 21 orchestration mentions, customer-facing product
- **Business model**: Social app with real-time features
- **Unknown**: Whether Airflow orchestrates real-time or batch workflows
- **Stack**: AWS + Airflow + Databricks → could be batch or streaming

---

## Output Format

Return markdown following the template above, with:
- Clear grade assignment (A/B/C/D)
- Numbered evidence points with **(VERIFIED)** marks
- Quotes from source material
- Balanced conclusion that acknowledges uncertainty where it exists
