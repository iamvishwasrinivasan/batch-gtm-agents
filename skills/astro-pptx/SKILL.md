---
name: astro-pptx
description: >
  Creates branded Astronomer PowerPoint presentations (.pptx) following the 2026 Astronomer Brand
  Guidelines. Use this skill whenever the user asks to make a slide deck, PowerPoint, presentation,
  or PPTX — especially for sales decks, customer-facing materials, prospect decks, QBRs, pitch decks,
  demo decks, or internal Astronomer presentations. Also trigger when the user says things like "make
  me a deck about X", "put together some slides for Y", "build a presentation for [account]", or
  "I have a meeting with [company] and need slides." Always save output to ~/Downloads/. Always run
  visual QA before declaring done.
---

# Astro PPTX

You're creating a branded Astronomer PowerPoint. The output must feel like it came from Astronomer's
marketing team — polished, on-brand, and ready to send to a customer.

## Step 1: Gather requirements

Ask the user these questions upfront in a single message:

1. **Mode**: Dark mode, light mode, or mixed (dark title/closing, light content slides)?
   Default to mixed if not specified.
2. **Title & purpose**: What's the deck title, and who's the audience?
   (e.g., "intro demo for Acme Corp's data engineering team")
3. **Specific slides or content**: Any sections or slides they definitely want?
   You'll fill the rest with good judgment.

Don't write a single line of code until you have at least the title and purpose.

---

## Step 2: Plan the slide structure

For sales/customer-facing decks, adapt this structure to the situation. Use judgment —
not every deck needs every slide.

| # | Slide | Mode |
|---|-------|------|
| 1 | Title (deck title, audience/account, date) | Dark |
| 2 | Agenda | Light |
| 3 | About Astronomer | Light |
| 4 | The problem / challenge | Light |
| 5 | The Astronomer platform | Light |
| 6 | How it works / architecture | Light |
| 7 | Key features or use cases (2–3) | Light |
| 8 | Customer proof / logos | Light |
| 9 | Next steps / CTA | Dark |
| 10 | Thank you + contact | Dark |

---

## Step 3: Build the deck with python-pptx

Install if needed:
```bash
python3 -m pip install python-pptx -q
# macOS with Homebrew Python: python3 -m pip install python-pptx --break-system-packages -q
```

Read `references/brand.md` before writing any code — it has all hex values, font names,
dark/light mode rules, and layout patterns.

If the user has provided a brand guidelines PPTX, you can also read it directly for additional context:
```bash
python3 -m markitdown "<path-to-brand-guidelines.pptx>"
```

### Slide setup
```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

prs = Presentation()
prs.slide_width = Inches(13.33)
prs.slide_height = Inches(7.5)
```

### Font assignment rules (apply without exception)

Every text element falls into exactly one of three roles. Choose the font by role, not by context:

| Role | Font | Size range | Notes |
|------|------|-----------|-------|
| Slide titles, section headers | League Gothic | 28–48pt | No bold — letterform provides weight |
| Stat callouts, price values, big numbers | League Gothic | 13–72pt | **ALL numeric/price values use League Gothic — no exceptions** |
| Eyebrows, column headers, labels, captions | Roboto Mono | 8–11pt | ALWAYS ALL CAPS |
| Body copy, table labels, footnotes | Roboto | 8–15pt | Sentence case |

**Critical — the most common mistake:**  
In pricing tables, comparison tables, and waterfall rows, every value cell (the right-side number) must use **League Gothic**, regardless of row type (list price, discount, subtotal, total). Do not use Roboto for price values just because they're in a "normal" or "discount" row. Color changes by row type (e.g. Gold for discounts, White for list price), but the font is always League Gothic.

```python
# CORRECT — all waterfall value cells use League Gothic
if style == 'total':
    vc, vs, vf = WHITE, 17, 'League Gothic'
elif style == 'subtotal':
    vc, vs, vf = GOLD, 15, 'League Gothic'
elif '−' in val:          # discount row
    vc, vs, vf = GOLD, 13, 'League Gothic'
else:                      # list price row
    vc, vs, vf = WHITE, 13, 'League Gothic'

# WRONG — Roboto on price values, even at small sizes
elif '−' in val:
    vc, vs, vf = GOLD, 11, 'Roboto'   # ← never do this
```

### Charts and data visualizations

- **Always render charts as matplotlib PNG, then embed as image.** Never use native python-pptx charts — they render poorly in PowerPoint and Google Slides.
- Apply brand colors to every chart element: `BG_F = (0x1D/255, 0x1D/255, 0x2C/255)` for figure background, `PANEL_F` for axes background, brand accent colors for bars/lines.
- Set `mpl.rcParams['text.parse_math'] = False` at the top of every matplotlib script — this prevents `$` signs from being treated as LaTeX math delimiters and getting stripped from labels and legends.
- Position bar/column labels so they never overlap reference lines: `label_y = max(val + offset, reference_line + clearance)`.
- Use `Roboto Mono` for axis tick labels and value labels; `Roboto` for axis titles and legends.

### Editability — native shapes for everything except charts

- Charts and sparklines: matplotlib PNG, embedded as image (not editable, that's fine).
- Everything else — titles, body text, table rows, stat boxes, pricing waterfalls, feature grids — must be **native python-pptx text boxes and shapes**, so the user can edit them directly in PowerPoint or Google Slides without touching the script.
- Never use matplotlib to render a table or text layout that could be done natively.

### Every slide must have a visual element
Never produce a plain white slide with just text. Use at least one of:
- A colored header band or footer bar
- A background color fill (dark or light)
- Decorative arc/circle shapes (Orbit motif)
- A colored left column or side accent strip
- Icon placeholder shapes in brand colors

### Layout variety
Don't repeat the same layout on consecutive slides. `references/brand.md` has 8 named layouts
with exact specs — use them as your primary vocabulary. Quick reference:

| Layout | Best for |
|--------|----------|
| Gold top stripe | Almost every slide — thin brand header |
| Big statement (full purple bg) | Thesis, mission, bold section openers |
| Split: dark col left + card grid right | System overviews, feature breakdowns |
| Before / After split | Problem → solution, old vs. new |
| Giant stat left + content right | Key metrics, proof points |
| Dark callout on light bg | Examples, output callouts |
| 2×3 roadmap grid | What's next, feature roadmaps |
| Use case (numbered) | Use case walkthroughs, process flows |

A real example deck lives at `assets/all-hands-example.pptx` — read it for design inspiration.

---

## Step 4: Save and QA

Save to `~/Downloads/<deck-slug>.pptx` (kebab-case, descriptive name).

### Voice QA (do this before visual QA)

Check all slide copy against Astronomer's brand voice. Full guidelines in `references/brand.md`.

**We Are / We Are Not — quick check:**
- [ ] Every claim has a number — no unsubstantiated superlatives ("best-in-class", "world-class")
- [ ] Outcomes stated, not just features listed
- [ ] No prohibited terms: no "managed Airflow", "leverage", "synergize", "game-changing", em dashes, "Astronomer provides"
- [ ] Headers make the point (McKinsey-style: "Build data pipelines 10x faster" not "Developer Tools")
- [ ] Headers >4 words use sentence case with punctuation; ≤4 words may use Title Case without punctuation
- [ ] Oxford comma used everywhere
- [ ] No exclamation points in headers
- [ ] Tone matches the audience (see matrix below)
- [ ] "Astro" for the platform, "Astronomer" for the company — not swapped

**Tone by deck type:**

| Deck type | Formality | Energy | Technical depth |
|-----------|-----------|--------|-----------------|
| Exec / VP intro or pitch | Medium-High | High | Low — lead with outcomes |
| Data engineering team | Medium | High | High — benchmarks, comparisons |
| QBR / customer success | Medium | Warm | Medium |
| Internal / all-hands | Low-Medium | High | Medium |
| Enterprise proposal | High | Medium | High |

**Prohibited copy patterns:**
- Generic AI claims ("AI-powered") → specify the behavior ("Airflow-aware code generation that knows your existing connections")
- Feature lists without outcomes → always connect to what it means for the engineer's day
- Softened competitive claims → if Astro is faster, state the number and the comparison

Visual QA is required. Use **qlmanage** (macOS native PPTX renderer — same engine as Keynote/Preview, closest to PowerPoint/Google Slides). Do NOT use LibreOffice for QC; it substitutes fonts differently and gives a misleading picture.

```python
import subprocess, pathlib

QC_DIR = pathlib.Path('/tmp/pptx_qc')
QC_DIR.mkdir(exist_ok=True)

# Clear stale previews
for old in QC_DIR.glob('ql_*.png'):
    old.unlink()

out = '/path/to/file.pptx'
subprocess.run(
    ['qlmanage', '-t', '-s', '1920', '-o', str(QC_DIR), out],
    capture_output=True, text=True
)
thumb = QC_DIR / (pathlib.Path(out).name + '.png')
if thumb.exists():
    thumb.rename(QC_DIR / 'ql_slide1.png')
```

**Note:** qlmanage only renders slide 1 for PPTX files. For multi-slide QC, save per-figure PNGs during generation (pass `qc_path=` to your `embed_fig()` helper) and review slide 2+ by opening the file in PowerPoint or Google Slides.

Inspect every rendered image. Look for:
- Text cut off or overflowing its box
- Overlapping elements (labels on top of reference lines, values outside table cells)
- Font inconsistency — all price/stat values must be League Gothic, all eyebrows Roboto Mono ALL CAPS, all body Roboto
- Low contrast (light text on light bg, or dark text on dark bg)
- Leftover placeholder text (`[COMPANY]`, `xxxx`, `lorem`, etc.)
- Inconsistent margins
- Dollar signs or special characters missing (check matplotlib legend/labels if so — add `mpl.rcParams['text.parse_math'] = False`)

Fix anything found, re-render, and re-check. Do not declare done until a full pass is clean.

---

## Step 5: Report

Tell the user:
- Full path to the saved file
- Brief summary of slides and design decisions
- Note if any fonts require installation for full fidelity (League Gothic, Roboto, Roboto Mono)

---

## Reference

| File | Contents | When to read |
|------|----------|--------------|
| `references/brand.md` | Colors, fonts, dark/light rules, layouts, logo rules | Always — before writing any code |
| `references/messaging.md` | Core positioning, stats, proof points, customer stories, narrative arcs, persona guide | For sales/customer-facing decks, or whenever you need accurate Astronomer claims |
