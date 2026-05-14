# Extract Company Metrics from Research Data

You are extracting structured, quantitative metrics from web research results. Be precise and include source confidence.

## Metrics to Extract

Extract the following metrics from the provided Exa search results:

### 1. Company Basics
```json
{
  "company_name": "Full legal name",
  "founded_year": 2009,
  "headquarters": "City, State/Country",
  "tagline": "Company tagline or positioning statement",
  "description": "One-line company description",
  "website": "https://..."
}
```

### 2. Size & Scale
```json
{
  "employees": {
    "current": 83,
    "previous": 81,
    "yoy_change_pct": 2.8,
    "yoy_change_abs": 4,
    "source": "LinkedIn | Crunchbase | Company website",
    "confidence": "high"
  },
  "revenue": {
    "amount": 26500000,
    "currency": "USD",
    "period": "annual",
    "source": "...",
    "confidence": "medium"
  },
  "customer_count": {
    "current": 10000,
    "description": "organizations",
    "source": "..."
  }
}
```

### 3. Funding & Ownership
```json
{
  "ownership_type": "private | public | subsidiary",
  "funding_total": 50000000,
  "last_round_date": "2024-03-15",
  "last_round_amount": 15000000,
  "key_investors": ["Koch Brothers Network", "..."],
  "source": "..."
}
```

### 4. Leadership Team
```json
{
  "executives": [
    {
      "name": "Brent Youngers",
      "title": "President",
      "linkedin": "https://...",
      "source": "LinkedIn"
    }
  ]
}
```

### 5. Growth Metrics
```json
{
  "website_traffic": {
    "monthly_visits": 33631,
    "mom_change_pct": 32.6,
    "yoy_change_pct": 354.5,
    "global_rank": 505153,
    "source": "SimilarWeb | Semrush"
  },
  "social_metrics": {
    "linkedin_followers": 3124,
    "linkedin_mom_change_pct": 1.7,
    "linkedin_yoy_change_pct": 15.3,
    "source": "..."
  }
}
```

### 6. Hiring Signals
```json
{
  "job_openings": {
    "current": 3,
    "previous_month": 2,
    "previous_quarter": 1,
    "previous_year": 4,
    "mom_change_pct": 50.0,
    "qoq_change_pct": 200.0,
    "yoy_change_pct": -25.0,
    "source": "Company careers page | LinkedIn Jobs"
  },
  "open_roles": [
    "Application Developer",
    "Political Analyst",
    "Product Manager"
  ],
  "workforce_breakdown": {
    "by_department": {
      "technical": {"count": 39, "pct": 27},
      "research": {"count": 11, "pct": 8}
    },
    "by_seniority": {
      "specialist": {"count": 40, "pct": 27},
      "manager": {"count": 16, "pct": 11}
    }
  },
  "talent_inbound": [
    {"company": "Freedom Partners", "count": 3}
  ],
  "talent_outbound": [
    {"company": "Amazon", "count": 6}
  ]
}
```

### 7. Tech Stack
```json
{
  "technologies": [
    {
      "name": "Apache Airflow",
      "category": "orchestration",
      "confidence": "high",
      "evidence_sources": ["job_description", "blog_post"],
      "mention_count": 23
    }
  ]
}
```

### 8. Product Metrics
```json
{
  "products": [
    {
      "name": "i360 Portal v4",
      "category": "Platform",
      "launch_date": "2025",
      "description": "Fully-integrated platform...",
      "source": "..."
    }
  ]
}
```

### 9. Employer Reputation
```json
{
  "glassdoor_rating": 3.5,
  "glassdoor_review_count": 68,
  "work_life_balance": 3.8,
  "compensation": 3.5,
  "culture": 3.3,
  "career_growth": 3.3,
  "source": "Glassdoor"
}
```

---

## Extraction Rules

1. **Only extract data you can verify** - Don't guess or estimate
2. **Track confidence levels**:
   - `high`: Direct statement from official source
   - `medium`: Derived from credible third-party
   - `low`: Indirect evidence or dated information
3. **Always include source** - Note where each metric came from
4. **Calculate growth rates** when you have before/after data:
   - MoM = ((current - prev_month) / prev_month) * 100
   - YoY = ((current - prev_year) / prev_year) * 100
5. **Use null for missing data** - Don't fill with zeros or guesses
6. **Normalize numbers**:
   - "83 employees" → 83
   - "$26.5M" → 26500000
   - "10K+ organizations" → 10000

---

## Input Data

You will receive Exa search results as structured JSON:
```json
{
  "company_research": {"results": [...]},
  "hiring": {"results": [...]},
  "news": {"results": [...]},
  "blog_posts": {"results": [...]},
  "website_crawl": {"results": [...]},
  "job_descriptions": [...]
}
```

Each result contains:
- `url`: Source URL
- `title`: Page title
- `text`: Full text content
- `highlights`: Key excerpts
- `publishedDate`: Publication date

---

## Output Format

Return a single JSON object with all extracted metrics following the schema above. Include a `metadata` section:

```json
{
  "metadata": {
    "extracted_at": "2026-03-31T16:00:00Z",
    "sources_analyzed": 42,
    "confidence_score": 0.85
  },
  "company_basics": {...},
  "size_and_scale": {...},
  "funding": {...},
  "leadership": {...},
  "growth_metrics": {...},
  "hiring_signals": {...},
  "tech_stack": {...},
  "products": {...},
  "employer_reputation": {...}
}
```

Be thorough but precise - quality over quantity.
