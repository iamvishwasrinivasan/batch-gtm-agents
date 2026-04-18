---
name: astro-docs
description: Search Astronomer's live website and technical docs to answer questions about how Astronomer or Astro works. Use this skill whenever someone asks how a feature works in Astro or Astronomer, what a specific concept means (deployments, clusters, workspaces, executors, etc.), how to configure or set something up, what the difference is between deployment types, or any product-specific question about the Astronomer platform. Also trigger for questions like "does Astro support X?", "what's the difference between X and Y in Astro?", "how does Astro handle Z?", or any time someone wants a factual answer about Astronomer features. ALWAYS use this skill for Astronomer/Astro product questions — never answer from memory alone, since the product changes frequently (e.g. Astro Hybrid was retired; current products are Astro and Astro Private Cloud). For pricing, tiers, or deal sizing questions, use the astro-pricing skill instead.
---

# Astro Docs Search

The goal is to give an accurate, up-to-date answer grounded in what the live docs actually say — not training data, which may be stale.

## Step 1: Find the right doc pages

Use Exa to search within astronomer.io for the topic. Run 1-2 targeted searches:

- For feature/concept questions: search `site:astronomer.io/docs <topic>`
- For product/pricing questions: search `site:astronomer.io <topic>`

Pick the 1-3 most relevant URLs from the results.

## Step 2: Fetch and read the pages

Use WebFetch on each URL with a prompt focused on what the user actually asked. Be specific in the prompt so you extract the right information (e.g. "What are the networking options for dedicated clusters on AWS?" not just "summarize this page").

If a fetched page links to a more specific sub-page that looks more relevant, fetch that too.

## Step 3: Answer the question

Answer directly and concisely based on what you fetched. If the docs were unclear or incomplete, say so. Always include the source URL(s) so the user can read further.

## Tips

- The docs live at `https://www.astronomer.io/docs/` — most feature questions are answered there
- The main site `https://www.astronomer.io/` covers pricing tiers, deployment models, and product overview
- If the first search doesn't surface the right page, try rephrasing (e.g. "VNet peering" vs "private networking Azure")
- For questions comparing options (e.g. PrivateLink vs VPC peering), often a single overview page covers both — fetch that first before drilling into sub-pages
