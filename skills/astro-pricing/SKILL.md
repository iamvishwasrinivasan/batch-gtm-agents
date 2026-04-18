---
name: astro-pricing
description: Answer any question about Astronomer pricing, tiers, deal sizing, discounts, add-ons, or cost estimates. Use this skill for questions like "what does Astro cost?", "what's the difference between Team and Business pricing?", "how much is Remote Execution?", "what's included in Enterprise?", "how do I size a deal?", "what are the credit rates for X cluster type?", or any time someone needs actual dollar amounts, tier comparison, or deal structure guidance. Always uses Metronome (Snowflake) as the authoritative source for list prices — never quotes rates from memory or training data.
---

# Astro Pricing

The goal is to give an accurate, grounded answer using the actual list prices from Metronome — not training data, which may be stale.

## Step 1: Read the price book for structure

Read the price book to understand the conceptual model before quoting any numbers:

```
~/.claude/skills/astro-pricing/price-book.md
```

This explains how pricing works: component structure, what drives cost, tier multiplier mechanics, deal sizing rules of thumb, and Private Cloud model. Use it to frame the answer correctly.

## Step 2: Query Metronome (Snowflake) for actual list prices

The price book does not contain specific dollar amounts. Query Metronome directly for real per-hour rates by component, tier, cloud, and region:

```sql
-- All rate cards (find the right plan)
SELECT RATE_CARD_NAME, RATE_CARD_ID, UPLIFT_PCT
FROM HQ.MODEL_FINANCE.METRONOME_RATE_CARDS
WHERE IS_INTERNAL = FALSE AND IS_TRIAL = FALSE
ORDER BY UPLIFT_PCT;

-- Line items for a specific rate card
SELECT PRODUCT_ITEM_NAME, PRICING_GROUP_KEYS, UNIT_PRICE
FROM HQ.MODEL_FINANCE.METRONOME_RATE_CARD_ITEMS
WHERE RATE_CARD_ID = '<rate_card_id>'
  AND IS_ACTIVE = TRUE
ORDER BY PRODUCT_ITEM_NAME;
```

Known rate card IDs (April 2026): Developer `c2dcead1`, Team Annual `874d3b20`, Business `a51c7043`, Enterprise `786ad160`. See price-book.md for full table.

**Always use Metronome for actual prices** — never quote rates from memory or training data, as they change by tier, region, and contract.

## Step 3: Supplement with live web search if needed

If the question requires public-facing details (e.g., plan comparison page copy, feature availability by tier, what's listed on the pricing page), do a targeted Exa search:

- `site:astronomer.io pricing`
- `site:astronomer.io/docs <add-on name>`

Fetch the relevant page with WebFetch to pull current copy.

## Step 4: Answer the question

Answer directly with actual numbers from Metronome. Include:
- The relevant tier(s) and their rate card IDs
- Per-unit or per-hour rates for the components in question
- Deal sizing guidance from the price book if relevant
- Source note (Metronome + date queried) so the user knows it's live data
