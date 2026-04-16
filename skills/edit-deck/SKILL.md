---
name: edit-deck
description: >
  Edit the Astronomer GTM AI pitch deck by updating deck_content.json and
  running edit_deck.py to regenerate the PPTX in seconds. Use this skill
  whenever Vishwa wants to update the GTM AI pitch deck — changing a slide
  title, updating a deal in the Early Results cards (ACV, close date, body
  text), editing What's Next bullet items, or any other content change.
  Trigger on phrases like "update the deck", "change the close date",
  "add a deal", "edit slide 2", "update the ACV", "fix the Vivian card",
  "change what's next", or any request that implies editing the pitch deck.
  This is much faster than rebuilding from scratch — just a JSON edit + one
  script run.
---

# Edit Deck Skill

This skill updates the Astronomer GTM AI C-suite pitch deck by editing
`deck_content.json` and running `edit_deck.py`. The whole workflow takes
under 10 seconds and requires no XML work for standard content changes.

## Deck location

All files live in the user's outputs folder:

```
mnt/outputs/gtm_ai_deck/
├── deck_content.json     ← edit this
├── edit_deck.py          ← run this
├── template_base/        ← do not touch (clean unpacked template)
├── template_original.pptx
└── GTM_AI_Pitch.pptx    ← output
```

## Deck structure (4 slides)

| Slide | Content | JSON key |
|-------|---------|----------|
| 1 | Title + subtitle | `slide1` |
| 2 | Early Results — 3 deal cards | `slide2` |
| 3 | What's Next — 4 bullet items | `slide3` |
| 4 | Proposed Structure — org diagram | `slide4` |

The org diagram on slide 4 is structural (static shapes). Only the slide
title is editable via JSON. To change the diagram itself, XML editing is
needed — see the "Structural changes" section below.

## Standard workflow (content updates)

### Step 1: Read the current content

```bash
cat /sessions/relaxed-nice-gauss/mnt/outputs/gtm_ai_deck/deck_content.json
```

Understand what's there before making changes.

### Step 2: Edit deck_content.json

Use the Edit tool to make targeted changes. The schema is:

```json
{
  "output_filename": "GTM_AI_Pitch.pptx",

  "slide1": {
    "title": "GTM AI",
    "subtitle": "Building the AI-Powered AE Motion at Astronomer"
  },

  "slide2": {
    "title": "Early Results",
    "cards": [
      {
        "header": "Company Name",
        "acv": "86k ACV",
        "acv_color": "FFB32D",
        "subtitle": "One-line context (close date, deal type, etc.)",
        "body": "2-3 sentences on what Claude did and the outcome."
      }
    ]
  },

  "slide3": {
    "title": "What\u2019s Next",
    "items": [
      {
        "header": "Bold item header",
        "body": "1-2 sentences of supporting detail."
      }
    ]
  },

  "slide4": {
    "title": "Proposed Structure"
  }
}
```

**ACV color guide:**
- `"FFB32D"` — Astronomer gold, use for the hero/highlight deal
- `"FFFFFF"` — white, use for secondary deals

**Encoding special characters in JSON:**
- Em dash → `\u2014`
- Right single quote / apostrophe → `\u2019`
- Left/right double quotes → `\u201C` / `\u201D`

### Step 3: Run the script

```bash
cd /sessions/relaxed-nice-gauss/mnt/outputs/gtm_ai_deck && python edit_deck.py
```

This copies the base template, applies all JSON edits via targeted regex
on the slide XML, and packs a fresh PPTX. Takes ~3 seconds.

### Step 4: Visual QA

Convert only the slides that changed:

```bash
mkdir -p /sessions/relaxed-nice-gauss/qa_edit
soffice --headless --convert-to pdf --outdir /sessions/relaxed-nice-gauss/qa_edit/ \
  /sessions/relaxed-nice-gauss/mnt/outputs/gtm_ai_deck/GTM_AI_Pitch.pptx
rm -f /sessions/relaxed-nice-gauss/qa_edit/slide-*.jpg
pdftoppm -jpeg -r 150 /sessions/relaxed-nice-gauss/qa_edit/GTM_AI_Pitch.pdf \
  /sessions/relaxed-nice-gauss/qa_edit/slide
```

Read the relevant slide images to confirm the change looks right. You don't
need to re-inspect slides that didn't change.

### Step 5: Deliver

Link to the output file:

```
[View GTM_AI_Pitch.pptx](computer:///sessions/relaxed-nice-gauss/mnt/outputs/gtm_ai_deck/GTM_AI_Pitch.pptx)
```

---

## Common edits (quick reference)

**Update a deal close date:**
Find the card in `slide2.cards`, edit `"subtitle"`.

**Update an ACV number:**
Find the card in `slide2.cards`, edit `"acv"`. Change `"acv_color"` to
`"FFB32D"` if it's the highlight deal, `"FFFFFF"` otherwise.

**Add a new deal (replace an existing card):**
Replace that card object in `slide2.cards` entirely. The script always
renders exactly 3 cards — it maps `card1/card2/card3` positionally.

**Add/remove a What's Next item:**
Edit `slide3.items`. Up to ~5 items fit comfortably; beyond that the text
gets small. The script renders all items in order.

**Rename a slide:**
Edit the `"title"` field in the relevant slide key.

---

## Structural changes (need XML editing)

Some changes can't be done via JSON and require direct XML work on the
unpacked template. If the user asks for any of these, do NOT use this
skill's JSON workflow — fall back to the PPTX editing skill:

- Adding a 4th card to slide 2 (template only has 3 card shapes)
- Changing the org diagram layout on slide 4 (shapes/connectors are static)
- Adding a 5th slide
- Changing font sizes or colors of existing elements
- Reorganizing the slide order

After making structural changes, update `template_base/` so the script
uses the new structure going forward:

```bash
cp -r /sessions/relaxed-nice-gauss/template_fresh_unpacked \
      /sessions/relaxed-nice-gauss/mnt/outputs/gtm_ai_deck/template_base
```

---

## Shape ID reference (for XML debugging)

If the script prints a WARNING that a shape wasn't found, these are the
IDs to verify in the slide XML:

| Slide file | Shape | ID |
|------------|-------|----|
| slide1.xml | Title | 79 |
| slide1.xml | Subtitle | 80 |
| slide5.xml | Slide title | 103 |
| slide5.xml | Card 1 | 104 |
| slide5.xml | Card 2 | 105 |
| slide5.xml | Card 3 | 106 |
| slide7.xml | Slide title | 119 |
| slide7.xml | Right column body | 120 |
| slide3.xml | Slide title | 91 |
