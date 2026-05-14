#!/usr/bin/env node
// Astronomer Consumption Review Deck Generator
// Usage: node deck_generator.js <config.json> <output.pptx>

"use strict";
const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

const [,, configPath, outputPath] = process.argv;
if (!configPath || !outputPath) {
  console.error("Usage: node deck_generator.js <config.json> <output.pptx>");
  process.exit(1);
}

const cfg = JSON.parse(fs.readFileSync(configPath, "utf8"));
const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.title = `${cfg.customer.name} Consumption Review`;

// ─── Brand Colors ──────────────────────────────────────────────────────────
const C = {
  DARK:   "1D1D2C",
  MED:    "555261",
  LIGHT:  "272638",
  ALT:    "222132",
  BORDER: "3A3850",
  MUTED:  "9896A6",
  PURPLE: "872DED",
  GOLD:   "FFB32D",
  CREAM:  "F0ECE5",
  WHITE:  "FFFFFF",
  RED:    "F03A47",
  BLUE:   "2676FF",
  GREEN:  "19BA5A",
  TEAL:   "13BDD7",
};

// ─── Fonts ─────────────────────────────────────────────────────────────────
const F = { HEADER: "Arial Black", BODY: "Calibri", MONO: "Courier New" };

// ─── Helpers ───────────────────────────────────────────────────────────────
const shadow = () => ({ type: "outer", blur: 10, offset: 3, angle: 135, color: "000000", opacity: 0.18 });

const CATEGORY_COLORS = {
  "Product Enrichment": C.PURPLE,
  "Content Ingestion":  C.TEAL,
  "dbt Transform":      C.BLUE,
  "Website Publishing": C.GREEN,
  "Integrations":       C.GOLD,
  "ML / AI":            C.RED,
  "CRM / Sync":         C.MUTED,
  "Data Ops":           C.MED,
  "Core Data":          C.PURPLE,
};

const COLOR_KEY_MAP = {
  PURPLE: C.PURPLE, TEAL: C.TEAL, BLUE: C.BLUE,
  GREEN: C.GREEN, GOLD: C.GOLD, RED: C.RED,
  MUTED: C.MUTED, MED: C.MED,
};

function eyebrow(slide, text, y = 0.28) {
  slide.addText(text, {
    x: 0.5, y, w: 9, h: 0.22,
    fontFace: F.MONO, fontSize: 9, color: C.GOLD,
    charSpacing: 3, margin: 0,
  });
}

function slideTitle(slide, text, y = 0.52) {
  slide.addText(text, {
    x: 0.5, y, w: 9, h: 0.65,
    fontFace: F.HEADER, fontSize: 30, color: C.WHITE, bold: false, margin: 0,
  });
}

function divider(slide, y = 1.2) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y, w: 9, h: 0.025,
    fill: { color: C.BORDER }, line: { type: "none" },
  });
}

function wordmark(slide, footerText = null) {
  slide.addText("ASTRONOMER", {
    x: 0.4, y: 5.3, w: 2.2, h: 0.2,
    fontFace: F.MONO, fontSize: 8, color: C.CREAM, charSpacing: 2.5, margin: 0,
  });
  if (footerText) {
    slide.addText(footerText, {
      x: 2.75, y: 5.3, w: 6.9, h: 0.2,
      fontFace: F.BODY, fontSize: 8, color: C.MUTED, margin: 0,
    });
  }
}

function addOrbital(slide) {
  const rings = [
    { x: 5.8, y: -1.2, w: 5.8, h: 5.8 },
    { x: 6.3, y: -0.5, w: 4.5, h: 4.5 },
    { x: 6.9, y:  0.2, w: 3.2, h: 3.2 },
  ];
  rings.forEach(r => {
    slide.addShape(pres.shapes.OVAL, {
      x: r.x, y: r.y, w: r.w, h: r.h,
      fill: { type: "none" },
      line: { color: C.WHITE, width: 0.75, transparency: 65 },
    });
  });
  const spheres = [
    { x: 8.6,  y: 0.05, w: 0.22, h: 0.22, color: C.RED   },
    { x: 9.55, y: 1.55, w: 0.28, h: 0.28, color: C.BLUE  },
    { x: 6.95, y: 2.9,  w: 0.20, h: 0.20, color: C.GREEN },
    { x: 9.5,  y: 0.3,  w: 0.18, h: 0.18, color: C.TEAL  },
  ];
  spheres.forEach(s => {
    slide.addShape(pres.shapes.OVAL, {
      x: s.x, y: s.y, w: s.w, h: s.h,
      fill: { color: s.color }, line: { type: "none" },
    });
  });
  slide.addShape(pres.shapes.OVAL, {
    x: 8.65, y: 1.3, w: 0.35, h: 0.35,
    fill: { color: C.PURPLE }, line: { type: "none" },
  });
}

// ═══════════════════════════════════════════════════════════════════════════
// SLIDE 1 — COVER
// ═══════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.DARK };
  const c = cfg.customer;

  addOrbital(s);

  s.addText(c.date_eyebrow || "CONSUMPTION REVIEW", {
    x: 0.5, y: 0.9, w: 5, h: 0.22,
    fontFace: F.MONO, fontSize: 9, color: C.GOLD, charSpacing: 3, margin: 0,
  });
  s.addText(c.name, {
    x: 0.5, y: 1.1, w: 6.5, h: 1.3,
    fontFace: F.HEADER, fontSize: 72, color: C.WHITE, bold: false, margin: 0,
  });
  s.addText("Consumption Review", {
    x: 0.5, y: 2.3, w: 6, h: 0.45,
    fontFace: F.BODY, fontSize: 18, color: C.CREAM, margin: 0,
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 2.88, w: 5.0, h: 0.025,
    fill: { color: C.PURPLE }, line: { type: "none" },
  });

  const atrParts = [
    { text: "ATR", options: { color: C.GOLD, bold: true } },
    { text: `  ${c.atr_date}     `, options: { color: C.CREAM } },
    { text: "PLAN", options: { color: C.GOLD, bold: true } },
    { text: `  ${c.plan}`, options: { color: C.CREAM } },
  ];
  s.addText(atrParts, {
    x: 0.5, y: 2.98, w: 8, h: 0.32,
    fontFace: F.BODY, fontSize: 11.5, margin: 0,
  });

  const aeParts = [
    { text: "AE", options: { color: C.GOLD, bold: true } },
    { text: `  ${c.ae}`, options: { color: C.CREAM } },
  ];
  if (c.rm) {
    aeParts.push({ text: "     RM", options: { color: C.GOLD, bold: true } });
    aeParts.push({ text: `  ${c.rm}`, options: { color: C.CREAM } });
  }
  s.addText(aeParts, {
    x: 0.5, y: 3.34, w: 8, h: 0.32,
    fontFace: F.BODY, fontSize: 11.5, margin: 0,
  });

  if (c.context_line) {
    s.addText(c.context_line, {
      x: 0.5, y: 3.8, w: 6, h: 0.28,
      fontFace: F.MONO, fontSize: 8.5, color: C.MUTED, charSpacing: 0.5, margin: 0,
    });
  }

  wordmark(s);
}

// ═══════════════════════════════════════════════════════════════════════════
// SLIDE 2 — ACCOUNT SNAPSHOT
// ═══════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.DARK };
  const sn = cfg.snapshot;

  eyebrow(s, "ACCOUNT OVERVIEW");
  slideTitle(s, "Account Snapshot");
  divider(s);

  function statCard(x, y, w, h, label, value, sub, valueColor = C.WHITE) {
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w, h, fill: { color: C.LIGHT },
      line: { color: C.BORDER, width: 0.75 }, shadow: shadow(),
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 0.05, h, fill: { color: C.PURPLE }, line: { type: "none" },
    });
    s.addText(label, {
      x: x + 0.15, y: y + 0.13, w: w - 0.2, h: 0.22,
      fontFace: F.MONO, fontSize: 8, color: C.GOLD, charSpacing: 1.5, margin: 0,
    });
    s.addText(value, {
      x: x + 0.15, y: y + 0.35, w: w - 0.2, h: 0.6,
      fontFace: F.HEADER, fontSize: 28, color: valueColor, bold: false, margin: 0,
    });
    if (sub) {
      s.addText(sub, {
        x: x + 0.15, y: y + 1.18, w: w - 0.2, h: 0.25,
        fontFace: F.BODY, fontSize: 9.5, color: C.MUTED, margin: 0,
      });
    }
  }

  const cardW = 2.9, cardH = 1.55, row1Y = 1.28, row2Y = 3.02, gap = 0.15, sx = 0.5;
  statCard(sx,              row1Y, cardW, cardH, "SUBSCRIPTION ARR", sn.arr, "Team Plan");
  statCard(sx+cardW+gap,    row1Y, cardW, cardH, "CREDIT BALANCE", sn.credit_balance, `of ${sn.license_granted} granted`);
  statCard(sx+2*(cardW+gap),row1Y, cardW, cardH, "LICENSE CONSUMED", sn.license_consumed_pct, sn.license_consumed_sub);
  statCard(sx,              row2Y, cardW, cardH, "UTILIZATION", sn.utilization, sn.utilization_sub, sn.utilization_alert ? C.GOLD : C.WHITE);
  statCard(sx+cardW+gap,    row2Y, cardW, cardH, "CREDITS EXHAUSTED", sn.credits_exhausted, sn.credits_exhausted_sub);
  statCard(sx+2*(cardW+gap),row2Y, cardW, cardH, "PROJECTED OVERAGE", sn.projected_overage, sn.projected_overage_sub);

  const footerText = `Data as of ${sn.data_date}  ·  Org ${sn.org_id}  ·  ${sn.cluster}`;
  wordmark(s, footerText);
}

// ═══════════════════════════════════════════════════════════════════════════
// SLIDE 3 — 12-MONTH TREND
// ═══════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.DARK };
  const tr = cfg.trend;

  eyebrow(s, "12-MONTH CONSUMPTION TREND");
  slideTitle(s, "Hosted Consumption: 12-Month Trend");
  divider(s);

  s.addChart(pres.charts.BAR, [
    { name: "Deployment", labels: tr.months, values: tr.deploy  },
    { name: "Compute",    labels: tr.months, values: tr.compute },
  ], {
    x: 0.4, y: 1.28, w: 6.8, h: 3.8,
    barDir: "col", barGrouping: "stacked",
    chartColors: [C.PURPLE, C.TEAL],
    chartArea: { fill: { color: C.DARK } },
    plotArea: { fill: { color: C.DARK } },
    catAxisLabelColor: C.MUTED, valAxisLabelColor: C.MUTED,
    catAxisLabelFontSize: 8, valAxisLabelFontSize: 8,
    catAxisLineShow: false, valAxisLineShow: false,
    valGridLine: { color: C.BORDER, size: 0.5 },
    catGridLine: { style: "none" },
    showLegend: true, legendPos: "b",
    legendColor: C.MUTED, legendFontSize: 9,
    showValue: false,
  });

  function trendStat(y, label, value, sub) {
    s.addShape(pres.shapes.RECTANGLE, {
      x: 7.4, y, w: 2.1, h: 0.95,
      fill: { color: C.LIGHT }, line: { color: C.BORDER, width: 0.75 }, shadow: shadow(),
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 7.4, y, w: 0.05, h: 0.95,
      fill: { color: C.GOLD }, line: { type: "none" },
    });
    s.addText(label, {
      x: 7.58, y: y + 0.06, w: 1.85, h: 0.18,
      fontFace: F.MONO, fontSize: 7, color: C.GOLD, charSpacing: 1, margin: 0,
    });
    s.addText(value, {
      x: 7.58, y: y + 0.24, w: 1.85, h: 0.38,
      fontFace: F.HEADER, fontSize: 20, color: C.WHITE, bold: false, margin: 0,
    });
    s.addText(sub, {
      x: 7.58, y: y + 0.62, w: 1.85, h: 0.26,
      fontFace: F.BODY, fontSize: 8, color: C.MUTED, margin: 0,
    });
  }

  trendStat(1.3,  "GROWTH",        tr.growth_label, tr.growth_note);
  trendStat(2.35, "PEAK MONTH",    tr.peak_label,   tr.peak_note);
  trendStat(3.4,  "COMPUTE SURGE", tr.surge_label,  tr.surge_note);

  wordmark(s, tr.footer);
}

// ═══════════════════════════════════════════════════════════════════════════
// SLIDE 4 — HOW THEY USE ASTRO
// ═══════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.DARK };
  const uc = cfg.use_cases;
  const customerName = cfg.customer.name;

  eyebrow(s, "HOW THEY USE ASTRO");
  slideTitle(s, `How ${customerName} Uses Astro`);
  divider(s);

  const n = uc.length;
  const gapX = 0.1;
  const totalW = 9.0;
  const cardW = (totalW - gapX * (n - 1)) / n;
  const cardH = 3.95;
  const startX = 0.5;
  const startY = 1.28;

  uc.forEach((card, i) => {
    const x = startX + i * (cardW + gapX);
    const color = COLOR_KEY_MAP[card.color_key] || C.PURPLE;

    s.addShape(pres.shapes.RECTANGLE, {
      x, y: startY, w: cardW, h: cardH,
      fill: { color: C.LIGHT }, line: { color: C.BORDER, width: 0.75 }, shadow: shadow(),
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: startY, w: cardW, h: 0.07,
      fill: { color }, line: { type: "none" },
    });
    s.addShape(pres.shapes.OVAL, {
      x: x + 0.15, y: startY + 0.17, w: 0.28, h: 0.28,
      fill: { color }, line: { type: "none" },
    });
    s.addText(card.label, {
      x: x + 0.08, y: startY + 0.55, w: cardW - 0.16, h: 0.22,
      fontFace: F.MONO, fontSize: 7, color, charSpacing: 0.5, margin: 0,
    });
    s.addText(card.title, {
      x: x + 0.08, y: startY + 0.78, w: cardW - 0.16, h: 0.55,
      fontFace: F.HEADER, fontSize: 13, color: C.WHITE, bold: false, margin: 0,
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: x + 0.08, y: startY + 1.35, w: cardW - 0.16, h: 0.02,
      fill: { color: C.BORDER }, line: { type: "none" },
    });
    s.addText(card.body, {
      x: x + 0.1, y: startY + 1.42, w: cardW - 0.2, h: 2.25,
      fontFace: F.BODY, fontSize: 9.5, color: C.CREAM,
      valign: "top", wrap: true, margin: 0,
    });
  });

  wordmark(s);
}

// ═══════════════════════════════════════════════════════════════════════════
// SLIDE 5 — PIPELINE INVENTORY
// ═══════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.DARK };
  const pipes = cfg.pipelines;

  eyebrow(s, "PIPELINE INVENTORY");
  slideTitle(s, "Pipeline Inventory");
  divider(s);

  function successColor(val) {
    if (val >= 95) return C.GREEN;
    if (val >= 85) return C.GOLD;
    return C.RED;
  }

  function catColor(cat) {
    return CATEGORY_COLORS[cat] || C.MUTED;
  }

  const headerFill = { color: C.MED };
  const headerStyle = {
    fontFace: F.MONO, fontSize: 8, color: C.GOLD,
    fill: headerFill, align: "left",
  };

  const headerRow = [
    { text: "PIPELINE",    options: { ...headerStyle } },
    { text: "RUNS",        options: { ...headerStyle, align: "center" } },
    { text: "SUCCESS",     options: { ...headerStyle, align: "center" } },
    { text: "AVG RUNTIME", options: { ...headerStyle, align: "center" } },
    { text: "CATEGORY",    options: { ...headerStyle } },
  ];

  const dataRows = pipes.map((p, idx) => {
    const fill = { color: idx % 2 === 0 ? C.LIGHT : C.ALT };
    const base = { fontFace: F.BODY, fontSize: 9.5, color: C.CREAM, fill };
    return [
      { text: p.name,    options: { ...base, fontFace: F.MONO, fontSize: 8.5 } },
      { text: p.runs,    options: { ...base, align: "center" } },
      { text: p.success, options: { ...base, align: "center", color: successColor(p.success_val || parseFloat(p.success)) } },
      { text: p.runtime, options: { ...base, align: "center" } },
      { text: p.category,options: { ...base, color: catColor(p.category) } },
    ];
  });

  s.addTable([headerRow, ...dataRows], {
    x: 0.5, y: 1.3, w: 9.0,
    rowH: 0.355,
    border: { type: "solid", pt: 0.5, color: C.BORDER },
    colW: [3.2, 0.8, 0.85, 1.1, 2.05],
  });

  wordmark(s, cfg.pipeline_footer || "Sorted by run count  ·  Scheduled runs, 90-day window");
}

// ─── Write file ────────────────────────────────────────────────────────────
const absOutput = path.resolve(outputPath);
pres.writeFile({ fileName: absOutput })
  .then(() => console.log(`✓  Written: ${absOutput}`))
  .catch(err => { console.error(err); process.exit(1); });
