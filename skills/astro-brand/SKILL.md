---
name: astro-brand
description: >
  Applies Astronomer's 2026 brand guidelines to any visual artifact — slide decks, PDF one-pagers,
  HTML landing pages, posters, canvas designs, Word docs, or any other output with visual design.
  Use this skill whenever the user asks to create something visual for Astronomer and needs it to
  look on-brand. Triggers include: "one-pager", "PDF", "landing page", "poster", "infographic",
  "leave-behind", "sell sheet", "HTML page", "branded doc", or any request that mentions Astronomer
  branding. Also trigger when the user says "make it on-brand", "use our brand colors", or "apply
  Astronomer branding."

  NOTE: For PowerPoint / .pptx output specifically, use the astro-pptx skill instead — it has the
  full build system. This skill handles all other visual formats.
---

# Astronomer Brand Guidelines — Applied to Visual Artifacts

You are creating a visual artifact that must follow Astronomer's 2026 brand guidelines.
The guidelines below are the canonical reference — all hex values, font names, and rules are
extracted from the official brand guidelines and kept in sync.

---

## Colors

### Primary Palette

| Name | Hex | Use |
|------|-----|-----|
| New Moon 90 | `#1D1D2C` | Primary dark background |
| New Moon 80 | `#343247` | Secondary dark bg, dark cards |
| New Moon 70 | `#555261` | Body text on light bg, tertiary dark |
| Purple 60 | `#872DED` | Accent, links/CTAs on light bg |
| Gold 40 | `#FFB32D` | Accent, links/CTAs on dark bg |
| New Moon 10 | `#F0ECE5` | Light background, body text on dark |
| White | `#FFFFFF` | Light bg, headers on dark |

### Supporting Colors (accent/data only — never as background fills)

| Name | Hex | Use |
|------|-----|-----|
| Red 50 | `#F03A47` | Alerts, emphasis |
| Blue 50 | `#2676FF` | Data, technical callouts |
| Green 50 | `#19BA5A` | Success, positive metrics |
| Teal 50 | `#13BDD7` | Pipelines, integrations |

### Logo Colors
- On light backgrounds: `#2B215B` (deep purple)
- On dark backgrounds: `#FFFFFF` (white)

---

## Dark Mode vs. Light Mode

### Dark Mode (title pages, covers, CTAs, section dividers)

| Element | Color |
|---------|-------|
| Background | `#1D1D2C` (primary) or `#343247` (cards) |
| Headline | `#FFFFFF` |
| Eyebrow / label | `#FFB32D` (Gold) |
| Body copy | `#F0ECE5` (New Moon 10) |
| Accent / links | `#FFB32D` (Gold) |

### Light Mode (content, body, features)

| Element | Color |
|---------|-------|
| Background | `#FFFFFF` or `#F0ECE5` |
| Headline | `#343247` (New Moon 80) |
| Eyebrow / label | `#872DED` (Purple) |
| Body copy | `#555261` (New Moon 70) |
| Accent / links | `#872DED` (Purple) |

---

## Typography

| Font | Role | Notes |
|------|------|-------|
| **League Gothic** | All headlines and titles | Google Fonts — condensed, high-impact |
| **Roboto** | Body copy and paragraphs | Google Fonts — clean, readable |
| **Roboto Mono** | Eyebrows, labels, captions, code | ALL CAPS for eyebrows |

Do not substitute Inter, Albert Sans, Arial, or Calibri for these fonts.

### Sizes (adapt to format — these are slide-oriented baselines)

| Element | Font | Size |
|---------|------|------|
| Main title | League Gothic | 40–48pt |
| Section header | League Gothic | 28–36pt |
| Eyebrow label | Roboto Mono | 9–11pt (ALL CAPS) |
| Body text | Roboto | 13–15pt |
| Stat callout | League Gothic | 60–80pt |
| Caption / fine print | Roboto | 10–11pt |
| Code | Roboto Mono | 11–13pt |

---

## Writing Style

- **Sentence case with punctuation** for headers longer than 4 words.
  - Good: "The future of data orchestration is here."
  - OK (≤4 words): "Why Astronomer?" — Title Case, no punctuation
- **Oxford comma** always.
- No em dashes. Use commas or periods instead.
- Tone: direct, punchy, confident, data-forward.
- No jargon: no "leverage," "synergize," or "best-in-class."
- No exclamation points in headers.
- **McKinsey-style titles**: the headline makes the point, not just labels the topic.
  - Good: "95% of GenAI pilots stall before production."
  - Bad: "GenAI challenges"

---

## Brand Voice

The core brand voice framework is summarized below.

### We Are / We Are Not

| We Are | We Are Not |
|--------|------------|
| **Technical authority** — earned via specifics (100% of Airflow releases, 18 of top 25 committers) | **Credential-dropping** — don't substitute authority claims for substance |
| **Quantified** — every meaningful claim has a number ("2x", "30%+", "60%") | **Superlatives** — "best-in-class", "world-class", "game-changing" with nothing behind them |
| **Engineering-empathetic** — we speak to practitioners as peers who've lived the same pain | **Condescending** — never make the engineer feel bad for their current setup |
| **Outcome-forward** — value is in what the product enables, not the feature mechanics | **Feature-listing** — capabilities without connecting to real outcomes |
| **Calmly confident** — "This is the DevEx your team deserves." Stated simply, not hyperbolically | **Breathless or hype-driven** — urgency theater, exclamation points in headers |
| **Transparent** — honest about pricing complexity, sizing uncertainty, and internal process | **Evasive** — avoiding hard questions about cost or constraints to protect a close |
| **Genuinely curious** — earns the right to position by understanding the situation first | **Leading the witness** — asking questions only to set up a predetermined pitch |

### Tone by Context

Voice is constant. Tone flexes along three dimensions: **Formality** / **Energy** / **Technical Depth**.

| Context | Formality | Energy | Technical Depth |
|---------|-----------|--------|-----------------|
| Cold email — VP/exec | Medium | High | Low |
| Cold email — data engineer | Medium | High | Medium |
| Slide deck / demo | Medium-High | High | High |
| Enterprise proposal | High | Medium | High |
| Discovery call | Low-Medium | Curious/Warm | Low to start |
| Late-stage / negotiate | Medium | Low (obstacle removal) | Medium |
| Follow-up email | Medium | Medium | Low-Medium |
| Social / LinkedIn | Low-Medium | High | Low |
| Customer success / QBR | Medium | Warm | Medium |

### Prohibited Terms (apply to all copy in every artifact)

Never use: "managed Airflow" (say "commercial Airflow platform"), "leverage" (say "use"), "synergize",
"best-in-class", "world-class", "game-changing", "revolutionary", "seamless", "robust" (replace with
the specific capability), em dashes, "Astronomer provides" (say "Astro delivers" or reframe around outcome).

### Voice QA Checklist

Before declaring any written content done:
- [ ] Every meaningful claim has a number — no unsubstantiated superlatives
- [ ] Outcomes stated, not just features listed
- [ ] No prohibited terms (see above)
- [ ] Headers make the point (McKinsey-style), not just label the topic
- [ ] Tone matches the context (see matrix above)
- [ ] "Astro" for the platform, "Astronomer" for the company — not swapped

---

## Logo Rules

- Always bottom-left placement with consistent margins.
- Clear space: "A" rule — padding equal to the height of the "A" in "Astronomer."
- One color only. Never two-tone or gradient.
- Approved: `#2B215B` on light, `#FFFFFF` on dark.
- Never stretch, rotate, add shadow, or change color.
- Never use the icon and wordmark together.
- Never place on busy backgrounds or photography.
- **If the actual logo file isn't available**, write `"ASTRONOMER"` in Roboto Mono ALL CAPS at
  10–11pt in the approved color, bottom-left. This is the correct stand-in.

---

## Visual Motifs

- **Gold top stripe**: Thin gold bar spanning full width at top — use on almost every page/slide.
- **Orbits**: Arc and circle shapes in New Moon colors — dark backgrounds only.
- **Space Math / Grid**: Subtle dot or line grids as background texture.
- **Textures**: Semi-transparent rectangle overlays for depth.
- **Typography as design**: Large League Gothic type used as a graphic element.

---

## Format-Specific Application

### PDF One-Pager (via `pdf` skill or ReportLab/WeasyPrint)

- Dark header strip (`#1D1D2C`) with white League Gothic title + Gold 40 eyebrow.
- Body on white or NM10 background. Section headers in League Gothic NM80.
- Gold rule or Purple 60 accent lines to separate sections.
- "ASTRONOMER" wordmark bottom-left in Roboto Mono `#2B215B`.
- Single column or two-column grid — consistent left margin ~0.5".

### HTML Landing Page / Web Asset (via `frontend-design` skill)

- CSS variables for the palette (use exact hex values above).
- League Gothic loaded via Google Fonts CDN.
- Dark hero section (`#1D1D2C`) with white/gold text.
- Light content sections on white or `#F0ECE5`.
- Purple 60 for CTAs and interactive elements on light sections.
- Gold 40 for CTAs and links on dark sections.

### Canvas / Poster (via `canvas-design` skill)

- Same dark/light duality: dark for dramatic impact, light for informational.
- Gold stripe or accent shape as visual anchor.
- League Gothic as the dominant typographic element.
- No more than 3 colors from the palette on a single piece.

### Word Document (via `docx` skill)

- Cover page: dark NM90 background, white League Gothic title, Gold eyebrow.
- Body pages: white background, NM80 section headers, NM70 body text.
- Purple 60 for callout boxes or pull quotes (left border accent).
- Gold 40 sparingly for key stat callouts.

---

## Quality Check (all formats)

Before declaring done, verify:
- [ ] Only brand fonts used (League Gothic, Roboto, Roboto Mono).
- [ ] No off-brand colors (no generic blue, default gray, or red accents outside of Red 50).
- [ ] Dark sections have light text; light sections have dark text (no low-contrast combos).
- [ ] "ASTRONOMER" wordmark present bottom-left (if format supports it).
- [ ] Writing style: sentence case, Oxford comma, no jargon.
- [ ] Gold stripe or equivalent brand anchor element present.
