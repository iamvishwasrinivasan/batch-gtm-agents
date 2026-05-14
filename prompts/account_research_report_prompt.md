# Account Research Report Generation Prompt

You are generating a comprehensive account research report. Use the provided raw data from:
1. Snowflake CRM context (contacts, MQLs, opportunities, Gong calls)
2. Exa web research results (9 searches: company, orchestration, hiring, news, blog posts, products, case studies, website crawl, job descriptions)

## Report Structure

Generate a report with these sections:

### 1. Company Overview
- Company name and one-line description
- Founded, headquarters, employee count (with YoY change if available)
- Revenue (if found)
- Ownership/funding
- Key leadership team (names and titles)
- Tagline/positioning statement
- Mark each fact with **(VERIFIED)** if directly sourced

### 2. Airflow Mission Critical Assessment

**Framework:**
```
Score: A/B/C/D (scale)
- A = Airflow downtime = customer-facing outage (real-time)
- B = Mission-critical stack, Airflow downtime delays operations
- C = Airflow is used but not mission-critical
- D = No evidence of Airflow usage

Airflow Criticality: High/Medium/Low

The "Why":
[3-5 paragraph analysis with evidence]
- Confirmed Airflow usage evidence
- Business model context (batch vs real-time)
- Customer impact window (seconds/minutes/hours/days)
- Complementary tech stack
- Conclusion about role in customer operations
```

### 3. Recent News & Corporate Strategy (2025-2026)

Subsections:
- **Product & Platform Updates**: New features, launches
- **Market Position**: Customer counts, success metrics, case studies
- **Funding & Growth**: Recent rounds, acquisitions
- **2025-2026 Corporate Priorities**: Strategic focus areas

### 4. Data Orchestration & Hiring Intelligence

Subsections:
- **Apache Airflow Evidence**: CONFIRMED / NOT FOUND (with evidence)
- **Technology Stack**: Organized by category
  - Data Orchestration & Workflow
  - Cloud Infrastructure & Data Platforms
  - Data Transformation & Processing
  - Analytics & BI
  - Machine Learning & AI
  - Development & DevOps
  - Application Stack
- **Current Job Openings**: Count with trends (MoM, QoQ, YoY if available)
- **Workforce Breakdown**: By department and seniority
- **Talent Flow Patterns**: Inbound sources, outbound destinations
- **Geographic Presence**: Office locations

### 5. Pain Points & Customer Challenges

**Format:**
```
**Industry Challenges [Company] Addresses**:

1. **[Pain Point Name]**: **(VERIFIED)**
   - Challenge: [Description]
   - [Company] Solution: [How they address it]
   - Quote or evidence
```

### 6. Competitive Intelligence

- Market positioning statement
- Key competitors
- Competitive differentiation (3-5 bullet points)

### 7. Web Presence & Growth Metrics

- Monthly website visits (with MoM/YoY change)
- Social media following (LinkedIn, etc. with growth %)
- Employer rating (Glassdoor/similar)
- Top traffic sources

### 8. Product Suite Overview

Organize products by category with brief descriptions.

### 9. Summary & Outlook

- Paragraph summarizing market position
- **Key Takeaways**: Numbered list (6-8 items) with **(VERIFIED)** marks
- **Technical Capabilities**: Bullet list
- **Market Position Strengths**: Bullet list
- **Outlook for 2026**: Forward-looking paragraph

---

## Style Guidelines

1. **Verification marks**: Add **(VERIFIED)** after every fact directly sourced from research
2. **Quantitative precision**: Include exact numbers with growth percentages
   - Good: "83 employees (+2.8% YoY, +4 people)"
   - Bad: "around 80 employees"
3. **Source evidence**: When making claims, cite supporting evidence
4. **Balanced tone**: Professional, analytical, fact-based
5. **Growth metrics format**: Always show MoM (Month-over-Month) and YoY (Year-over-Year) when available
6. **Unknown data**: If data not found, write "Data not available" rather than guessing

---

## Input Data Structure

You will receive:

```json
{
  "account_name": "Company Name",
  "snowflake_context": {
    "tier": "customer",
    "contacts": 93,
    "mqls": 4,
    "opportunities": 13,
    "calls": 27,
    "transcripts": [...]
  },
  "exa_research": {
    "orchestration_mentions": 21,
    "hiring_signals_count": 0,
    "blog_post_count": 5,
    "product_announcement_count": 0,
    "case_study_count": 6,
    "website_crawled": true,
    "search_results": {
      "company_research": {...},
      "orchestration": {...},
      "hiring": {...},
      "news": {...},
      "blog_posts": {...},
      "product_announcements": {...},
      "case_studies": {...},
      "website_crawl": {...},
      "job_descriptions": [...]
    },
    "key_signals": [
      {
        "signal": "Text excerpt",
        "source": "blog_posts",
        "url": "https://...",
        "date": "2026-02-15",
        "score": 9,
        "category": "orchestration_evidence"
      }
    ],
    "tech_stack": [
      {
        "technology": "Apache Airflow",
        "category": "orchestration",
        "confidence": "high",
        "sources": ["blog_posts", "job_descriptions"],
        "mention_count": 23
      }
    ]
  }
}
```

---

## Output Format

Generate markdown report following the 9-section structure above. Use headers, bullet points, bold text, and code blocks for readability. Each section should be comprehensive but concise - aim for substance over length.
