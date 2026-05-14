---
name: disco-plan
description: >
  Generate a structured discovery call plan by pulling account research from
  Snowflake GTM V2_GTM_BATCH_OUTPUT table. Creates a markdown brief with
  pre-call research summary, tailored questions (business + technical),
  talking points, success criteria, and next steps. Saved to the account's
  Account Context folder. Use when preparing for discovery calls, follow-ups,
  or any customer conversation where you need a research-backed call plan.
---

# Disco Plan Skill

Generates a comprehensive discovery call plan by pulling account research from
Snowflake and creating a structured markdown brief tailored to the account's
situation, tech stack, and orchestration maturity.

## Input

Account name (required):
```
/disco-plan Acelab
```

The skill will:
1. Query `GTM.PUBLIC.V2_GTM_BATCH_OUTPUT` for the account
2. Pull all research data (signals, tech stack, CRM engagement, Gong calls)
3. Generate a tailored discovery plan
4. Save to `/Users/vishwasrinivasan/Account Context/[Company Name]/disco_plan_[date].md`

## Execution

Run the discovery plan generator script:

```bash
cd /Users/vishwasrinivasan/batch-gtm-agents && python3 generate_disco_plan.py "{{args}}"
```

The script will:
1. Query Snowflake V2_GTM_BATCH_OUTPUT for the account
2. Generate a tailored discovery plan with all sections
3. Save to `/Users/vishwasrinivasan/Account Context/[Company Name]/disco_plan_[date].md`
4. Display a summary

**Let the script run to completion** - it handles Snowflake auth via externalbrowser.

---

## Output Structure

The generated plan includes these sections:

```markdown
# Discovery Call Plan: [Company Name]

**Date:** [Today's date]
**Research Date:** [When research was run]
**Tier:** [customer/engaged_prospect/cold_prospect]
**Airflow Grade:** [A/B/C/D with explanation]

---

## Pre-Call Research Summary

### Company Overview
- **Current Orchestration:** [From tech stack - Airflow/Dagster/Prefect/etc.]
- **Orchestration Mentions:** [Count] references across web presence
- **Data Stack:** [Key technologies from tech_stack]
- **Team Signals:** [Hiring signals - data engineers, etc.]

### Engagement History
- **Contacts:** [count]
- **MQLs:** [count] (latest: [date])
- **Opportunities:** [count]
- **Gong Calls:** [count] (latest: [date])
- **Email Threads:** [count]

### Key Signals (Priority Order)
[List top 5-7 signals from key_signals with scores]

---

## Discovery Questions

### Business Questions
[Generate 4-6 questions tailored to their situation, such as:]
- What are your current data orchestration challenges?
- [If they use Airflow] What version are you on? How are you managing it?
- [If they use competitor] What's working well? What's frustrating?
- What triggered this conversation? [Reference any recent signal]
- Who owns data infrastructure decisions?
- What does success look like for your data team this quarter?

### Technical Questions
[Generate 4-6 technical questions based on their stack:]
- Current data platform? [Reference known tech from tech_stack]
- Pipeline complexity? (DAG count, task count, frequency)
- Deployment process? (CI/CD, testing, environments)
- Observability/monitoring setup?
- [If relevant] How are you handling [specific use case from signals]?
- Pain points with current setup?

---

## Talking Points & Value Props

### Tailored to Their Situation
[Based on orchestration_mentions, tech_stack, and signals:]

**If Grade A/B (Mission Critical):**
- Reliability & enterprise support
- Managed infrastructure
- Compliance & security

**If Using OSS Airflow:**
- Upgrade path & version management
- Remove infrastructure burden
- Built by Airflow committers

**If Using Competitor:**
- Airflow ecosystem advantage
- Flexibility & extensibility
- Cost comparison

**Based on Key Signals:**
[List 3-4 value props tied to their specific signals, e.g.:]
- "Saw you're hiring data engineers - Astro reduces operational overhead"
- "Noticed [product announcement] - Airflow scales with your growth"

---

## Success Criteria

**By end of call, we should know:**
- [ ] Current orchestration tool & pain points
- [ ] Decision-making process & timeline
- [ ] Technical requirements & constraints
- [ ] Budget/procurement process
- [ ] Key stakeholders & next steps

---

## Proposed Next Steps

[Tailor based on tier and engagement:]

**If cold/first call:**
1. Technical deep-dive with their data engineers
2. Share relevant case study: [Link to similar company]
3. Astro demo focused on [their use case]

**If engaged/follow-up:**
1. POC/trial discussion
2. Architecture review with their team
3. Pricing conversation

---

## Notes Section
[Leave blank for call notes]

**Key Takeaways:**
- 

**Action Items:**
- 

**Follow-up:**
- 
```

The script automatically saves the file and displays a summary with quick context and call focus recommendation.

---

## Customization Logic

### Orchestration Tool Detection

From `tech_stack`, identify current tool:
- If "Airflow" → Ask about version, deployment, pain points
- If "Dagster" → Positioning questions (why Dagster, what's missing)
- If "Prefect" → Positioning questions
- If "Luigi/Oozie/legacy" → Modernization angle
- If none/unknown → Discovery mode (what are you using today?)

### Question Tailoring by Grade

**Grade A (Real-time Critical):**
- Focus on reliability, SLAs, support
- Uptime requirements
- Incident response

**Grade B (Mission Critical Batch):**
- Focus on scalability, cost optimization
- Team productivity
- Deployment velocity

**Grade C (Operational Tool):**
- Focus on ease of use, getting started
- Team enablement
- Cost vs DIY

**Grade D (No Airflow Evidence):**
- Discovery mode: what are they using?
- Education on Airflow benefits
- Use case fit assessment

### Value Prop Selection by Signals

Map signals to value props:
- "real-time" → Stream processing with Airflow
- "mlops" → ML pipeline orchestration
- "data quality" → Observability & data quality checks
- "scale" → Enterprise scalability
- "hiring" → Reduce operational burden
- "compliance" → SOC2, HIPAA, security

---

## Error Handling

**Account not found:**
```
❌ No research data found for [Company]
Run research first: /batch-account-research [Company]
```

**Missing key fields:**
- Gracefully handle null/empty fields
- Note in plan: "No [X] data available - ask during call"

**Old research data:**
```
⚠️  Research is [N] days old (from [date])
Consider refreshing: /batch-account-research [Company]
```

Warn if `research_date` > 30 days old.

---

## Pro Tips

- **Before customer calls:** Run this + review recent Gong transcripts
- **For follow-ups:** Review previous disco plan notes section
- **Multi-stakeholder calls:** Note different personas (eng vs exec) in plan
- **Demo prep:** Combine with `/demo-prep` skill for full prep workflow
- **Team sharing:** Plans saved to Account Context for easy handoff

---

## Future Enhancements

- Pull recent Gong call transcripts and summarize
- Auto-detect persona (technical vs business) and adjust questions
- Suggest relevant case studies based on industry/tech stack
- Integration with calendar (auto-generate plans for today's calls)
- Post-call: Update notes section with `/disco-debrief` skill
