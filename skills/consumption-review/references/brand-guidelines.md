# Astronomer 2026 Brand Guidelines — Consumption Review Reference

## Colors (no # prefix in pptxgenjs)

| Token | Hex | Use |
|-------|-----|-----|
| DARK | `1D1D2C` | Primary slide background |
| MED | `555261` | Table header, secondary panels |
| LIGHT | `272638` | Card/row background (slightly lighter than DARK) |
| ALT | `222132` | Alternating table rows |
| BORDER | `3A3850` | Card borders, table borders, divider lines |
| MUTED | `9896A6` | Footer text, secondary body text, axis labels |
| PURPLE | `872DED` | Accent bars, Product Enrichment category, primary highlight |
| GOLD | `FFB32D` | Eyebrow labels, ATR/PLAN/AE field labels, attention stats |
| CREAM | `F0ECE5` | Body text on dark backgrounds |
| WHITE | `FFFFFF` | Titles, primary text |
| RED | `F03A47` | Orbital sphere, alert/error states, low success rates |
| BLUE | `2676FF` | Orbital sphere, dbt Transform category |
| GREEN | `19BA5A` | Orbital sphere, Website Publishing category, success states |
| TEAL | `13BDD7` | Orbital sphere, Compute cost bars, Content Ingestion category |

**Never use # prefix.** `color: "872DED"` ✓ — `color: "#872DED"` ✗ (corrupts file)

## Fonts

| Role | Font | Size | Notes |
|------|------|------|-------|
| Slide title | Arial Black | 28–34pt | League Gothic substitute |
| Stat value (large) | Arial Black | 26–32pt | |
| Card title | Arial Black | 12–14pt | |
| Eyebrow label | Courier New | 8–10pt | ALL CAPS, gold, charSpacing: 3 |
| Body / subtext | Calibri | 9–12pt | |
| Table cell | Calibri | 9–11pt | |
| Pipeline name | Courier New | 8.5–9pt | monospace for DAG names |
| ASTRONOMER wordmark | Courier New | 8pt | ALL CAPS, charSpacing: 2.5, cream |

## Slide layout rules

- **Background**: always `1D1D2C` (dark mode throughout)
- **Eyebrow**: x=0.5, y=0.28, Courier New, 9pt, gold (#FFB32D), charSpacing 3
- **Slide title**: x=0.5, y=0.52, Arial Black, 30pt, white
- **Horizontal rule under title**: x=0.5, y=1.2, w=9, h=0.025, fill BORDER
- **ASTRONOMER wordmark**: x=0.4, y=5.3, Courier New, 8pt, cream, charSpacing 2.5
- **Footer text**: same y=5.3, x=2.75, Calibri, 8pt, MUTED — sits right of wordmark on same line
- **Slide dimensions**: 10" × 5.625" (LAYOUT_16x9)
- **Margins**: 0.4–0.5" from all edges

## Orbital decoration (cover slide only)

Three concentric elliptical rings (white, 65% transparent) on the right half of the slide. Four colored spheres placed on the rings: Red, Blue (teal-ish), Green, Teal. Purple sphere at center. This is the Astronomer signature motif — always dark background only.

## Shadow factory (NEVER reuse option objects)

```javascript
const shadow = () => ({ type: "outer", blur: 10, offset: 3, angle: 135, color: "000000", opacity: 0.18 });
```

## Card anatomy

Every stat card and use-case card uses:
- Rectangle fill: `LIGHT` (`272638`)
- Border: `BORDER` (`3A3850`), 0.75pt
- Left accent bar: 0.05" wide, card's accent color
- Eyebrow: Courier New, 7–8pt, category color, charSpacing 1–2
- Title: Arial Black, appropriate size, white
- Body: Calibri, 9–10pt, cream

## Category color map

| Category | Color |
|----------|-------|
| Product Enrichment | PURPLE (`872DED`) |
| Content Ingestion | TEAL (`13BDD7`) |
| dbt Transform | BLUE (`2676FF`) |
| Website Publishing | GREEN (`19BA5A`) |
| Integrations | GOLD (`FFB32D`) |
| ML / AI | RED (`F03A47`) |
| CRM / Sync | MUTED (`9896A6`) |
| Data Ops | MED (`555261`) |
| Core Data | PURPLE (`872DED`) |

If more than 5 categories, pick the most distinct ones and combine smaller groups.
