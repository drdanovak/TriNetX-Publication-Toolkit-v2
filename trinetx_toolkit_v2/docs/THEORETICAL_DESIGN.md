# TriNetX Publication Toolkit v2 — Unified Theoretical Design

## The problem the toolkit solves

Real-world data (RWD) studies built on TriNetX face a recurring tension. The
platform makes it fast to define cohorts, match them, and export outcome
tables, but the same speed encourages investigators to skip the rigor
checkpoints that govern observational research: a stable study design fixed
before any analysis is run, a defensible identification strategy, transparent
reporting of how the cohort was built, and structured sensitivity analyses
that test whether the results survive plausible perturbations.

The Publication Toolkit exists to make those rigor checkpoints
**reproducible, lightweight, and integrated with the same TriNetX exports**
that already populate the manuscript's tables and figures. Each tool produces
either a manuscript-ready artifact, a rigor diagnostic, or a reporting
checkpoint, and every tool reads from the same set of TriNetX export files so
that a single study session yields a coherent set of outputs.

## The four phases of an RWD study and the toolkit's coverage

The toolkit organizes its ten core tools and four new rigor modules around
the four phases of an observational study, in the order they should be
performed.

### Phase 1. Design (before any data are pulled)

The questions an investigator answers in this phase determine whether the
study can support causal-style conclusions or only descriptive ones. The
toolkit contributes:

- **Pre-Analysis Plan Generator (new, tool F)** — a structured questionnaire
  that captures the PICO question, the index-date construction, washout and
  look-back windows, primary and secondary outcomes, planned subgroup and
  sensitivity analyses, and the multiple-comparisons family. It exports a
  PDF/Markdown document suitable for OSF registration or for an internal
  protocol record. This anchors every later decision.

- **Bias Check Questionnaire (new, tool J)** — a structured walk-through of
  index-date timing, exposure ascertainment window, and outcome ascertainment
  window. It flags configurations that produce immortal-time bias, reverse
  causation, or selection effects, and proposes text for the Limitations
  section.

### Phase 2. Cohort construction and balance

The investigator pulls baseline characteristics and verifies that matching
has produced exchangeable cohorts.

- **PSM Table Generator** — produces the journal-style Table 1 before and
  after matching.
- **Love Plot Generator** — visualizes covariate balance and computes
  before/after SMD diagnostics.
- **Cohort Attrition Diagram** — (extension, not in v2 core but supported by
  the architecture) — produces a CONSORT-style flow diagram from a small
  editable table.

### Phase 3. Outcome estimation

The investigator translates TriNetX MOA and Kaplan-Meier exports into
manuscript artifacts.

- **Outcomes Table Generator** — Table 2-style outcomes table with cohort
  rows, events, risks, and effect estimates.
- **Forest Plot Generator** — multi-outcome RR/OR/HR display.
- **Two-Cohort Bar Graphs** — absolute risks side-by-side.
- **Kaplan-Meier Curve Maker** — publication-grade survival curves.

### Phase 4. Rigor checks and reporting

The investigator stress-tests the findings and prepares the manuscript.

- **Power, E-value, NNT/NNH** — sensitivity to unmeasured confounding,
  absolute clinical impact, and statistical adequacy.
- **Effect Size Calculator** — standardized effect-size translations.
- **Multiple Comparisons Correction Tool** — Bonferroni, Holm, BH, BY.
- **Kaplan-Meier Diagnostics (new, tool B)** — log-log plot and a numerical
  proportional hazards check, so the HR reported in the Outcomes Table is
  defensible.
- **STROBE + RECORD Checklist (new, tool G)** — STROBE coverage extended
  with the RECORD addendum specifically for routinely-collected health
  data, which is the appropriate reporting standard for TriNetX work.

## The unifying data model

Every tool draws from the same four input categories, and every tool reads
them through the same shared parser layer (`utils/parsers.py`). This single
parser layer is the technical embodiment of the unified design: a TriNetX
baseline CSV looks identical whether it is feeding the PSM Table Generator
or the Love Plot Generator, and an MOA CSV looks identical whether it is
feeding the Outcomes Table or the Multiple Comparisons tool.

| Input category | Source | Tools that consume it |
|---|---|---|
| Baseline Patient Characteristics CSV | TriNetX | PSM Table, Love Plot |
| Measures of Association CSV | TriNetX | Outcomes Table, Forest Plot, Two-Cohort Bar, Multiple Comparisons, Power/E-value, Effect Size |
| Kaplan-Meier CSV | TriNetX | KM Curve, KM Diagnostics, Outcomes Table, Forest Plot |
| Study context (cohort labels, direction, alpha, outcome polarity) | User | Every tool, via shared session state |

## Shared session context

A unified study context lives in `st.session_state` and is set once per
session on the Home page. Every tool reads from it and writes back to it.
This eliminates the most common error mode in v1 (cohort direction reversed
between tools) and makes a single uploaded file usable by every tool that
needs it without re-uploading.

The context includes:

- Cohort 1 label and Cohort 2 label
- Which cohort is treated/exposed (direction)
- Whether the outcome polarity is adverse or beneficial
- Alpha and target power
- Multiple-comparisons family definition
- Number formatting (percent decimals, ratio decimals, p-value style)
- Visual defaults (palette, font family, figure size)
- The uploaded files themselves, organized by detected type

## The rigor philosophy embedded in the design

Three principles run through every tool:

1. **Source transparency.** Every numerical output is tagged with its
   source: a value parsed from a TriNetX export, or a value computed by the
   toolkit (Wilson CI, E-value, Cohen's h, adjusted p-value). Reviewers and
   authors can tell at a glance which numbers came from where.

2. **Methods text alongside outputs.** Every tool concludes with a
   ready-to-paste sentence or paragraph describing what was done, in
   language compatible with a journal Methods section. The user does not
   need to reconstruct the analytical pipeline from memory.

3. **Verify before export.** Every output includes a collapsible "verify
   against source" widget that shows the exact section of the TriNetX
   export that was parsed. The "P-values don't match expectations"
   troubleshooting case is addressed structurally rather than through
   documentation.

## Why this matters for the Frontiers in Immunology submission

The Technology and Code article type expects a coherent system, not a
collection of scripts. The unified data model, the shared session context,
and the rigor philosophy above are what make the toolkit a single piece of
software with a defensible Methods section, rather than ten scripts that
happen to live in the same repository. The new rigor tools (Pre-Analysis
Plan, Bias Check, KM Diagnostics, STROBE+RECORD) are also the items most
likely to be cited as concrete contributions by peer reviewers, because
they fill gaps that TriNetX itself does not address.
