# Astronomer 2026 Brand Guidelines

## Colors

### Primary Palette

| Name | Hex | Use |
|------|-----|-----|
| New Moon 90 | `#1D1D2C` | Primary dark background (title slides, closing slides) |
| New Moon 80 | `#343247` | Secondary dark background, dark cards |
| New Moon 70 | `#555261` | Tertiary dark, body text on light |
| Purple 60 | `#872DED` | Accent, links/CTAs on light bg |
| Gold 40 | `#FFB32D` | Accent, links/CTAs on dark bg |
| New Moon 10 | `#F0ECE5` | Light background, body text on dark |
| New Moon 05 | `#FAF8F5` | Lightest background, light panel fills |
| White | `#FFFFFF` | Light bg, headers on dark |

### Supporting Colors

| Name | Hex | Use |
|------|-----|-----|
| Red 50 | `#F03A47` | Alerts, emphasis (accent/data only — never background fills) |
| Blue 50 | `#2676FF` | Data, technical (accent/data only — never background fills) |
| Green 50 | `#19BA5A` | Success, positive metrics (accent/data only — never background fills) |
| Teal 50 | `#13BDD7` | Data pipelines, integrations (accent/data only — never background fills) |

### Logo Colors
- On light backgrounds: `#2B215B` (deep purple)
- On dark backgrounds: `#FFFFFF` (white)

---

## Dark Mode Rules

Use for: title slide, closing slide, CTA slide, section dividers.

| Element | Color |
|---------|-------|
| Background | New Moon 90 `#1D1D2C` (primary) or New Moon 80 `#343247` (cards/secondary) |
| Slide title | White `#FFFFFF` |
| Eyebrow / label | Gold 40 `#FFB32D` |
| Body copy | New Moon 10 `#F0ECE5` |
| Accent / CTA / links | Gold 40 `#FFB32D` |
| Decorative shapes | New Moon 70 `#555261` or Purple 60 `#872DED` |

---

## Light Mode Rules

Use for: content slides, feature slides, data slides.

| Element | Color |
|---------|-------|
| Background | White `#FFFFFF` or New Moon 10 `#F0ECE5` |
| Slide title | New Moon 80 `#343247` |
| Eyebrow / label | Purple 60 `#872DED` |
| Body copy | New Moon 70 `#555261` |
| Accent / CTA / links | Purple 60 `#872DED` |
| Decorative shapes | New Moon 10 `#F0ECE5` or Purple 60 `#872DED` |

---

## Typography

### Fonts (all from the brand PPTX, all available on Google Fonts)

| Font | Use | Google Fonts URL |
|------|-----|-----------------|
| **League Gothic** | ALL headers and titles — default font | https://fonts.google.com/specimen/League+Gothic |
| **Roboto** | Body copy and paragraphs | https://fonts.google.com/specimen/Roboto |
| **Roboto Mono** | Eyebrows, labels, captions, code | https://fonts.google.com/specimen/Roboto+Mono |

These are the three canonical brand fonts. Do not use Inter, Albert Sans, or any other font
unless the user explicitly requests it.

### Font Sizes

| Element | Font | Size | Notes |
|---------|------|------|-------|
| Slide title | League Gothic | 40–48pt | League Gothic has no bold variant — weight comes from the letterform |
| Section header | League Gothic | 28–36pt | |
| Eyebrow / label | Roboto Mono | 9–11pt | ALL CAPS |
| Body text | Roboto | 13–15pt | Regular |
| Stat callout number | League Gothic | 60–72pt | |
| Caption / fine print | Roboto | 10–11pt | Muted color |
| Code / DAG names | Roboto Mono | 11–13pt | |

---

## Writing Style

- **Sentence case with punctuation** for all headers longer than 4 words.
  - Good: "The future of data orchestration is here."
  - Good: "Why Astronomer?"  ← under 4 words, Title Case OK, no punctuation
- **Oxford comma** required.
- **No em dashes** (--). Use periods or commas instead.
- Tone: direct, punchy, confident, data-forward. Compression over completeness. Write for data engineers first, economic buyers second.
- No corporate jargon: "leverage," "synergize," "best-in-class," buzzword stacking.
- Never use exclamation points in headers.
- **McKinsey-style slide titles**: the title should make the point, not just label the topic.
  - Good: "95% of GenAI pilots stall before production."
  - Bad: "GenAI challenges"

---

## Logo Rules

- Always placed **bottom-left** on slides, with consistent margins.
- Clear space: use the "A" rule — minimum padding equal to the height of the "A" in "Astronomer"
- One color only: never two-tone or gradient
- Approved colors: `#2B215B` on light, `#FFFFFF` on dark
- Never stretch, rotate, add shadow, or change color
- Never place on busy backgrounds or photography
- Never use the icon and wordmark together on the same slide
- **Never recreate or approximate the logo in python-pptx.** Instead, write `"ASTRONOMER"` in Roboto Mono, all caps, at ~10–11pt in the approved color, bottom-left. This is the correct stand-in when the actual logo file is unavailable.

---

## Proven Slide Layouts (from real Astronomer decks)

These patterns appear in actual Astronomer presentations. Use them as your primary layout
vocabulary — they're battle-tested and on-brand.

A real example deck is bundled at `assets/all-hands-example.pptx`. Read it with:
```bash
python3 -m markitdown assets/all-hands-example.pptx
```

### 1. Gold top stripe
A thin gold bar (`#FFB32D`, ~0.08" tall) spanning full slide width at the very top.
Appears on nearly every slide as a consistent brand header element.
```python
box(slide, 0, 0, 13.33, 0.08, fill=GOLD)
```

### 2. Big statement slide (full accent color)
Entire background is Purple 60 (`#872DED`). White League Gothic text fills ~80% of the slide height.
Right ~25% of slide is a slightly darker purple column for visual weight.
Use for thesis statements, mission slides, and bold section openers.

### 3. Split: dark column left + content grid right
Left ~35% of slide: NM80 background with huge League Gothic text (e.g. "THE\nSYSTEM").
Right ~65%: NM10/cream background with a 2×2 or 2×3 card grid.
Each card has a purple left border strip (~0.05" wide) and Roboto Bold heading.
Bottom of right panel: NM80 callout box with Gold eyebrow label + body text.

### 4. Before / After split
Two equal columns on a dark background.
- Left column: NM70 header band + muted content (the "before" state)
- Right column: Purple 60 header band + positive content (the "after" state)
Both headers use Roboto Bold in ALL CAPS, white text.
Content uses bullet-style Roboto body text.

### 5. Giant stat left + vertical rule + content right
Left ~30% of slide: one enormous League Gothic number in Gold (80–100pt).
Small Roboto label below the number.
Purple vertical rule (thin, full content height) divides left from right.
Right ~65%: Roboto Bold subheadings with indented bullet points below each.

### 6. Dark callout card on light background
On a light (NM10) slide, a full NM80 card occupies the right ~50%.
Gold eyebrow label at top of card. Content in NM10/white body text.
Purple border on the card's left or all sides.
Use for "example" or "output" callouts alongside a how-it-works list on the left.

### 7. 2×3 roadmap grid (dark bg)
Dark NM80 background with oversized League Gothic headline at top.
Six equal cards below in a 2-column grid.
Each card: NM70 fill, purple left border (~0.05" wide), Roboto Bold heading, small body text.
Last card can say "And more to come!" to leave the grid open.

### 8. Use case layout (dark bg, numbered)
Gold top stripe. Gold ALL CAPS eyebrow (e.g. "USE CASE 01").
Large bold League Gothic headline across full width.
Content area splits into left (process/how-it-works) and right (example/evidence).

## Text Alignment

- **All text is left-aligned.** Never center body text or paragraph copy.
- Centering is only acceptable for isolated stat callout numbers on a dedicated stat slide.
- Consistent left margin: keep content starting at the same x-coordinate across slides (~0.75–0.85").

---

## Design Elements (decorative motifs)

- **Space Math / Grid**: Use evenly-spaced lines or dot grids as subtle background texture
- **Orbits**: Arc and circle shapes in New Moon colors — only use on dark backgrounds. Spheres/dots should sit precisely ON the orbital paths, not floating freely.
- **Textures**: Semi-transparent rectangle overlays to add depth
- **Iconography**: Simple line-style icons (use text characters or Unicode symbols as proxies)
- **ASCII graphics**: For technical/architecture slides, monospaced text art works well

### python-pptx: Creating Orbit decorative elements
```python
from pptx.util import Inches, Pt, Emu
from pptx.enum.shapes import MSO_SHAPE_TYPE
import pptx.oxml.ns as nsmap
from lxml import etree

# Add a circle arc as orbit decoration
# Use MSO_SHAPE.OVAL for full circles, adjust size/position for partial overlap effect
from pptx.util import Inches
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_THEME_COLOR

def add_orbit_circle(slide, left, top, width, height, color_hex, line_width_pt=1.5, fill=False):
    shape = slide.shapes.add_shape(
        1,  # MSO_SHAPE_TYPE.OVAL = 9, but add_shape uses autoshape type. Use 9 for oval.
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    shape.line.color.rgb = RGBColor.from_string(color_hex.lstrip('#'))
    shape.line.width = Pt(line_width_pt)
    if fill:
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor.from_string(color_hex.lstrip('#'))
    else:
        shape.fill.background()
    return shape
```

---

## python-pptx: Text box with eyebrow + title pattern

This is the core pattern for most slides:

```python
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

def add_eyebrow_title(slide, eyebrow_text, title_text, left, top, width,
                       eyebrow_color, title_color, dark_mode=False):
    # Eyebrow
    tb_eye = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(0.4))
    tf_eye = tb_eye.text_frame
    tf_eye.word_wrap = False
    p_eye = tf_eye.paragraphs[0]
    run_eye = p_eye.add_run()
    run_eye.text = eyebrow_text.upper()
    run_eye.font.name = "Roboto Mono"
    run_eye.font.size = Pt(10)
    run_eye.font.color.rgb = RGBColor.from_string(eyebrow_color.lstrip('#'))

    # Title
    tb_title = slide.shapes.add_textbox(Inches(left), Inches(top + 0.45), Inches(width), Inches(1.5))
    tf_title = tb_title.text_frame
    tf_title.word_wrap = True
    p_title = tf_title.paragraphs[0]
    run_title = p_title.add_run()
    run_title.text = title_text
    run_title.font.name = "League Gothic"
    run_title.font.size = Pt(44)
    run_title.font.color.rgb = RGBColor.from_string(title_color.lstrip('#'))
```
