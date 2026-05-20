# TriNetX Publication Toolkit v2

A coherent Streamlit suite for converting TriNetX exports into manuscript-ready
tables, figures, and rigor diagnostics.

## What's new in v2

v2 reorganizes the toolkit around the four phases of a real-world data study
— **Design**, **Cohort**, **Outcomes**, and **Rigor & Reporting** — and adds
four new rigor tools that fill the most critical gaps in the v1 toolkit:

| New tool | Phase | What it does |
|---|---|---|
| **Pre-Analysis Plan** | Design | Captures PICO, index date, washout, outcomes, and sensitivity analyses before any data are pulled; produces an OSF-ready protocol. |
| **Bias Check** | Design | Walks through immortal-time, reverse causation, prevalent-user, look-back, and detection biases; flags critical configurations; produces Limitations-section text. |
| **KM Diagnostics** | Rigor | Tests the proportional-hazards assumption with a log-log plot and a numerical PH test before hazard ratios are reported. |
| **STROBE + RECORD** | Rigor | Combined reporting checklist; RECORD extends STROBE specifically for routinely-collected health data and is the appropriate reporting standard for TriNetX research. |

v2 also introduces a **shared utilities layer** that every tool depends on —
unified parsers, formatters, palettes, and exports — so the toolkit behaves
as a single piece of software rather than a collection of scripts.

## Architecture

See `assets/architecture_diagram.svg` for the full diagram. In summary:

```
LAYER 1 — TriNetX exports (Baseline CSV, MOA CSV, KM CSV, manual entry)
LAYER 2 — Shared utilities (parsers, formatters, session, figure_defaults, exports)
LAYER 3 — Four-phase tool layer (Design, Cohort, Outcomes, Rigor & Reporting)
LAYER 4 — Manuscript artifacts (Tables 1-2, figures, protocol, checklist, methods text)
```

## Repository layout

```
trinetx_toolkit_v2/
├── Home.py                         # Landing page; sets the study context
├── README.md                       # This file
├── pages/                          # Streamlit multi-page app
│   ├── 01_📋_Pre-Analysis_Plan.py  # NEW (tool F)
│   ├── 02_⚠️_Bias_Check.py          # NEW (tool J)
│   ├── 03_❤️_Love_Plot.py           # (migrate from v1; see MIGRATION_GUIDE)
│   ├── 04_⚖️_PSM_Table.py           # (migrate from v1)
│   ├── 05_🧮_Outcomes_Table.py     # Fully migrated to v2 pattern (reference impl)
│   ├── 06_🌲_Forest_Plot.py        # Fully migrated to v2 pattern (reference impl)
│   ├── 07_📊_Two-Cohort_Bar.py     # (migrate from v1)
│   ├── 08_📉_Kaplan_Meier_Curve.py # (migrate from v1)
│   ├── 09_🎯_Power_E-value_NNT.py  # (migrate from v1)
│   ├── 10_📐_Effect_Size.py        # (migrate from v1)
│   ├── 11_📊_Multiple_Comparisons.py  # (migrate from v1)
│   ├── 12_🔬_KM_Diagnostics.py     # NEW (tool B)
│   └── 13_✅_STROBE_RECORD.py      # NEW (tool G)
├── utils/                          # Shared utilities (the heart of v2)
│   ├── __init__.py
│   ├── parsers.py                  # One parser per TriNetX export type
│   ├── formatters.py               # fmt_p, fmt_pct, fmt_ratio, fmt_ci, fmt_smd
│   ├── session.py                  # StudyContext; cohort labels; direction
│   ├── figure_defaults.py          # Palettes, fonts, figure-size presets
│   └── exports.py                  # PNG / SVG / CSV / DOCX exports
├── assets/
│   └── architecture_diagram.svg    # Publication-ready architecture figure
└── docs/
    ├── THEORETICAL_DESIGN.md       # The unifying conceptual framework
    └── MIGRATION_GUIDE.md          # How to port the remaining v1 tools
```

## Quick start

```bash
pip install -r requirements.txt   # streamlit, pandas, matplotlib, python-docx, lifelines, scipy, statsmodels, plotly
streamlit run Home.py
```

## Recommended workflow

1. **Open Home.py.** Set the study context once: cohort labels, which cohort
   is treated/exposed, outcome polarity, alpha, target power. Every tool
   inherits these values for the rest of the session.

2. **Phase 1 — Design (BEFORE pulling data).** Use the **Pre-Analysis Plan**
   tool to lock in the PICO question and time windows. Run the **Bias Check**
   to surface time-related bias risks early.

3. **Phase 2 — Cohort.** Upload the Baseline CSV once; both the **PSM Table**
   and **Love Plot** tools will see it through the shared session.

4. **Phase 3 — Outcomes.** Upload MOA and KM CSVs once; **Outcomes Table**,
   **Forest Plot**, **Two-Cohort Bar**, and **Kaplan-Meier Curve** will all
   see them.

5. **Phase 4 — Rigor & Reporting.** Run **Power / E-value / NNT** for
   sensitivity. Run **Multiple Comparisons** if many outcomes were tested.
   Run **KM Diagnostics** before reporting any hazard ratio. Finish with the
   **STROBE + RECORD** checklist.

## The shared utilities — why they matter

v1 had ten tools, each with its own TriNetX parser, its own cohort-label text
field, its own decimal-formatting logic, its own download buttons. v2
consolidates these into five modules:

- `utils/parsers.py` — Three canonical parsers (`parse_baseline_csv`,
  `parse_moa_csv`, `parse_km_csv`) plus a dispatcher (`detect_and_parse`).
  Every tool reads the same MOA or KM file the same way, so a forest plot
  and a multiple-comparisons output from the same study cannot disagree.

- `utils/session.py` — A `StudyContext` dataclass in `st.session_state`.
  Cohort labels, treated/exposed direction, outcome polarity, alpha, and
  formatting preferences are set once and read by every tool.

- `utils/formatters.py` — One function per number type
  (`fmt_p`, `fmt_pct`, `fmt_ratio_with_ci`, `fmt_smd`, etc.). APA-style
  p-values, consistent CI formatting, and consistent decimal places across
  every table and figure.

- `utils/figure_defaults.py` — Color palettes, fonts, and figure-size
  presets. A forest plot and a KM curve from the same session share the
  same color scheme by default.

- `utils/exports.py` — Standardized PNG + SVG download buttons, plus
  DOCX/CSV for tabular outputs. Every figure offers SVG (Frontiers accepts
  SVG); every table offers a Word-ready DOCX.

## For the Frontiers manuscript

The architecture diagram (`assets/architecture_diagram.svg`) is suitable as
Figure 1 of the Technology and Code manuscript. The theoretical design
document (`docs/THEORETICAL_DESIGN.md`) provides the Methods-section
framework for the manuscript: a system whose four-phase organization, shared
data model, and rigor philosophy together make it a coherent piece of
software rather than ten scripts.

## License and citation

Open-source under the same license as the v1 toolkit. When citing in a
manuscript, please reference the Frontiers in Immunology Technology and Code
article describing the system (citation to be added on acceptance).
