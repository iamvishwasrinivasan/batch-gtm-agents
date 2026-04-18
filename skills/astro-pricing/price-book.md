# Astronomer Pricing: How It Works
*Conceptual field guide for AEs, SAs, and Sales Engineering*
**Source of Truth for actual rates:** Metronome (Snowflake: `HQ.MODEL_FINANCE.METRONOME_RATE_CARD_ITEMS`)
**Last Updated:** April 2026

> This document explains the pricing model and mechanics. For actual list prices, query Metronome. Use DealHub or the Astro Pricing Calculator to build customer quotes.

---

## Two Products, Two Models

| Product | Model | Key Principle |
|---------|-------|---------------|
| **Astro (Hosted)** | Consumption-based | Metered hourly; pay for what you use |
| **Astro Private Cloud** | Subscription | Fixed annual fee + unit prices for capacity beyond entitlements |

**Remote Execution** is an add-on to Astro Hosted, available only on **Enterprise and Enterprise Business Critical tiers**.

> Most common rep mistake: quoting prices without factoring in tier and region. The same infrastructure has a different price at every tier and in every cloud region. Always use the calculator or Metronome for real numbers.

---

## Astro Hosted: What Drives the Bill

Every Astro Hosted bill is some combination of three infrastructure components plus add-ons.

### Component 1: Clusters

The infrastructure environment where deployments run.

- **Standard clusters** — free; excluded from the tier multiplier base
- **Dedicated clusters** — priced; cost varies by tier and cloud provider/region

### Component 2: Deployments

An individual Airflow environment (scheduler + DAG processor). Runs continuously, billed hourly.

**The dials:**
- **Size** — Small, Medium, Large, Extra Large. Small combines scheduler + DAG processor into one process. Medium+ separates them into their own pods with independent compute.
- **Config** — Standard (single scheduler replica) vs. High Availability (two replicas, ~doubles deployment cost, adds failover)
- **Tier** — each tier step adds roughly 20–35% to the deployment price
- **Cloud + region** — prices vary; the calculator and Metronome handle this automatically

**Sizing guidance:** Most production workloads start at Medium HA. Small = dev or low-volume. Large/XL = heavy DAG parsing (hundreds of DAGs) or high concurrency requirements.

Remote deployments (Enterprise/EBC only) are billed at the small deployment rate. The scheduler gets all the compute on remote deployments — make sure customers planning remote execution understand this.

### Component 3: Task Execution

#### Workers

Workers execute tasks. This is the **variable portion** of the bill — they only run (and charge) when tasks are actively executing.

**The dials:**
- **Worker size** — A5 through A160. A5 = 1 vCPU / 2 GiB RAM (smallest); A160 = 32 vCPU / 64 GiB RAM (largest). Each step roughly doubles resources and price.
- **Tier** — prices scale with tier; relative gaps between sizes stay consistent
- **Additional Triggerer** — optional; priced per hour (rate varies by tier)
- **Worker Storage** — 10 GiB included per worker; additional storage charged per GiB/hr

When sizing a deal, ask about the customer's workload profile: tasks per day, average task duration, peak concurrency. The difference between small and large workers can significantly change the total bill.

#### Kubernetes Executor (KE) / Kubernetes Pod Operator (KPO)

Billed as equivalent A5 units. Astro measures total CPU + Memory allocated across KE/KPO pods and rounds up to the nearest A5 (1 CPU = 1 A5). Ephemeral storage limits above 0.25 GiB/pod incur additional charges.

### Network Chargeback

Pipeline traffic (to databases, APIs, cloud storage, third-party tools) is passed through at cost — no markup, no tier multiplier, no discount. Pipelines routing within the same cloud or via private networking cost less than cross-cloud or public internet traffic.

---

## Remote Execution

Priced on two dimensions:
1. **Fixed annual cost** — remote deployment or remote HA deployment, billed by the second
2. **Variable task minutes** — consumed by RE Agents executing tasks; volume-based tiering (more task minutes = lower per-minute rate)

Pricing is the same across Enterprise and EBC tiers. Customers can deploy as many RE Agents as they need, sized and scaled independently.

---

## Astro Observe

End-to-end lineage, data quality monitoring, and pipeline health.

- Available on **Team, Business, Enterprise** (annual contracts only)
- **Not available** on Developer or pay-as-you-go
- **Pricing:** 15% uplift on deployments + workers + remote execution, after the tier multiplier is applied
- **Clusters excluded** — Observe monitors pipeline execution, not infrastructure plumbing

---

## Tiers: The Biggest Pricing Lever

Tier selection does two things simultaneously:
1. Unlocks platform capabilities (governance controls, security features, support SLA)
2. Sets the price multiplier applied to the entire infrastructure bill

There is no way to add features from a higher tier to a lower tier. These are not separate decisions.

### What the Multiplier Applies To

The entire infrastructure base: dedicated clusters (including DR clusters) + deployments + workers.

**Not multiplied:** Standard clusters (free), add-ons (IDE tokens, DR pass-through), network chargeback, remote execution task minutes.

### Tier Capabilities and Multipliers

For current tier multipliers and plan-level rate card IDs, query Metronome:

```sql
-- All active, non-internal, non-trial rate cards with uplift
SELECT RATE_CARD_NAME, RATE_CARD_ID, UPLIFT_PCT
FROM HQ.MODEL_FINANCE.METRONOME_RATE_CARDS
WHERE IS_INTERNAL = FALSE AND IS_TRIAL = FALSE
ORDER BY UPLIFT_PCT;
```

Known rate card IDs (April 2026):

| Plan | Rate Card ID | Uplift |
|------|-------------|--------|
| Basic PayGo V2 (Developer) | `c2dcead1-0e73-43b2-be55-6cf28867cccd` | 0% |
| Team PayGo V2 | `3ac72f02-2642-4a7d-add9-fbdf0d31a5e1` | 20% |
| Basic Annual V2 (Developer) | `6082c4e2-b493-42a1-a9a8-3022e86ea82f` | 0% |
| Team Annual V2 | `874d3b20-41a9-40f6-9ab2-f667f2636762` | 20% |
| Business Annual V2 | `a51c7043-626d-4fa5-b8b9-33cf6c75bcf2` | 50% |
| Enterprise Annual V2 | `786ad160-b50a-482b-b5f3-57ac1ac7337b` | 100% |

> **Tier selection is a requirements conversation, not a cost conversation.** If a customer needs DAG-level RBAC → Enterprise. If they need 30-min P1 response → EBC. Lead with requirements, then show the price.

---

## How a Bill Comes Together

The structure is always the same, regardless of tier or region:

1. **Sum the infrastructure base** — add up hourly rates for clusters + deployments + workers, convert to monthly (730 hrs/month)
2. **Apply the tier multiplier** — multiplied total covers platform capabilities, support, and success services included at that tier
3. **Add Observe (if applicable)** — 15% uplift on the tier-multiplied deployments + workers subtotal
4. **Add-ons sit on top** — IDE tokens, DR, and other add-ons are calculated separately, not multiplied

The multiplied total is not a separate support line item. It is the tier-adjusted price for the entire platform.

---

## Add-Ons (Not Subject to Tier Multiplier)

### Astro IDE

Available on all plans. Two dimensions:
- **AI tokens** — prompt tokens and response tokens, pure usage-based (rates in Metronome)
- **Ephemeral deployments** — each session spins up a small deployment, billed at that tier's small deployment rate

### Disaster Recovery

Available **only on Enterprise Business Critical**:
- **Fixed** — second "warm" cluster + 12.5% uplift on cluster, deployment, and worker pricing (vs. Enterprise rates). Discounts apply only to the cluster line item.
- **Pass-through** — cross-region DB replication and object storage replication at cost

---

## Astro Private Cloud: Subscription Model

Fixed annual subscription with defined entitlements. Pay unit prices only for capacity beyond what's included.

### Base Platform: $250K/year

Includes:
- Astro Private Cloud control plane (unlimited instances; manages thousands of deployments across multiple data planes)
- 3 production Airflow deployments
- 3 non-production Airflow deployments
- 2 data planes
- Enterprise Support

### Unit Prices for Additional Capacity

| Item | Price |
|------|-------|
| Additional production deployment | $30K/year |
| Additional data plane | $110K/year |

> Counts are **maximum allowed running instances**, not a consumption commitment. Customers buy capacity, not usage.

### Center of Excellence (CoE): $60K

200 hours of advisory services (migration planning, architecture design, operational best practices).

**Year 1 discount to $0 applies for:**
- Net new logos
- Customers migrating from open source Airflow support

**Does NOT apply to:** Customers upgrading from Astronomer Software to APC. Also not included or discounted through IBM.

### Business Critical Support: 50% of ACV

Adds 30-min P1 response SLA, dedicated support resources, priority escalation. Standard support (2-year term) included in base price.

### Long-Term Support: 50% of ACV for Year 3

Extends support for the APC product version beyond the standard 2-year coverage window.

---

## Deal Sizing: Rules of Thumb

### Astro Hosted

| ACV Range | Profile |
|-----------|---------|
| $50–100K | Business or Enterprise, 2–5 deployments, moderate workers, standard clusters |
| $100–250K | Enterprise, dedicated clusters, multiple deployments, significant compute, likely Observe |
| $250K+ | Enterprise or EBC, multiple dedicated clusters, 10+ deployments, heavy compute, Observe, potentially DR |

### Astro Private Cloud

- **Entry point:** $250K. Most year-1 deals land $250–350K with CoE at $0.
- **Growth levers:** Additional prod deployments ($30K), data planes ($110K), Business Critical support (50% ACV)
- **Large footprint (>50 prod deployments):** Consider Enterprise License Agreement (ELA) — talk to sales leadership

---

## Discounting

For discount thresholds, approval tiers, and order form guidance, see the Deal Playbook. For non-standard terms, contact Austin Beattie.

---

## Getting Actual List Prices from Metronome

For specific per-hour rates for any component, tier, cloud, or region:

```sql
-- Get all line items for a specific rate card
SELECT PRODUCT_ITEM_NAME, PRICING_GROUP_KEYS, UNIT_PRICE, UPLIFT_PCT
FROM HQ.MODEL_FINANCE.METRONOME_RATE_CARD_ITEMS
WHERE RATE_CARD_ID = '<rate_card_id>'
  AND IS_ACTIVE = TRUE
ORDER BY PRODUCT_ITEM_NAME;

-- Find a customer's current rate card
SELECT RATE_CARD_ID, RATE_CARD_NAME, UPLIFT_PCT, START_TS, END_TS
FROM HQ.MODEL_FINANCE.METRONOME_CONTRACTS
WHERE ASTRO_ORG_ID = '<org_id>'
  AND IS_ACTIVE = TRUE;

-- Derive what a customer is actually paying per scheduler config
SELECT e.SCHEDULER_SIZE, e.IS_HA, e.REGION, e.CLOUD_PROVIDER,
       rci.UNIT_PRICE,
       rci.UNIT_PRICE * 730 AS monthly_cost_730hrs
FROM HQ.MODEL_FINANCE.METRONOME_DEPLOYMENT_EVENTS e
JOIN HQ.MODEL_FINANCE.METRONOME_RATE_CARD_ITEMS rci
    ON e.PRICING_GROUP_OBJECT_HASH = rci.PRICING_GROUP_OBJECT_HASH
WHERE e.ASTRO_ORG_ID = '<org_id>'
  AND rci.RATE_CARD_ID = '<rate_card_id>'
GROUP BY 1,2,3,4,5,6;
```

Always scope `METRONOME_RATE_CARD_ITEMS` to the customer's `RATE_CARD_ID` before joining on `PRICING_GROUP_OBJECT_HASH` — otherwise you'll pull rates from other plans.

---

## Common Pricing Mistakes

1. **Quoting reference prices as actual prices.** Published prices are AWS us-east-1 at a specific tier. Use Metronome or the calculator for anything else.
2. **Forgetting the tier multiplier.** An Enterprise customer's bill is 2x their raw infrastructure spend — the most common source of sticker shock.
3. **Undersizing worker estimates.** Workers are the variable cost. Slightly overestimate to avoid budget surprises.
4. **Confusing Astro Hosted and Private Cloud.** Different products, different models. Route the customer to the right model first.
5. **Pitching EBC when Enterprise is sufficient.** EBC is significantly more expensive. Only lead with EBC for customers who genuinely need DR, 99.95% SLA, or 30-min P1 response.
