"""
Home.py — TriNetX Publication Toolkit v2 landing page.

The Home page is the single place where the user sets the study context
(cohort labels, direction, outcome polarity, alpha) once for the whole
session. Every tool inherits these values via the shared session state.

The Home page also organizes tools by RWD study phase rather than by
chronological numbering, so users encounter them in the order they should
use them.
"""

import streamlit as st
import pandas as pd

from utils.session import ensure_context, render_context_banner
from utils.exports import render_reproducibility_footer

st.set_page_config(
    page_title="TriNetX Publication Toolkit v2",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

ctx = ensure_context()

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title("TriNetX Publication Toolkit")
st.caption(
    "Version 2.0 · A coherent suite for converting TriNetX exports into manuscript-ready "
    "tables, figures, and rigor diagnostics."
)

st.markdown(
    """
This toolkit is organized around the **four phases of a real-world data study**:
**Design**, **Cohort**, **Outcomes**, and **Rigor & Reporting**. Each tool reads
from a shared *study context* that you set once on this page — cohort labels,
direction, outcome polarity, alpha — and propagates to every table, figure, and
download in the session.

If you are new to the toolkit, set the study context first, then move through
the phases in order. If you already know which tool you need, use the quick
chooser further down.
"""
)

# ---------------------------------------------------------------------------
# Set study context (advanced mode shown on Home)
# ---------------------------------------------------------------------------

st.header("1. Set the study context")
st.caption(
    "Set this once and every tool will inherit it. You can revise these values "
    "later from any tool's context banner."
)
ctx = render_context_banner(show_advanced=True)

st.markdown("---")

# ---------------------------------------------------------------------------
# Four-phase visual map
# ---------------------------------------------------------------------------

st.header("2. Work through the four phases")
st.caption("Each phase has its own tools and produces its own outputs.")

phase_cols = st.columns(4)

with phase_cols[0]:
    st.markdown("### Phase 1 · Design")
    st.caption("Before any data are pulled.")
    st.markdown(
        """
- **Pre-Analysis Plan** (new) — PICO, index date, washout, outcomes
- **Bias Check** (new) — immortal-time, reverse-causation, selection
"""
    )

with phase_cols[1]:
    st.markdown("### Phase 2 · Cohort")
    st.caption("Construction and balance.")
    st.markdown(
        """
- **PSM Table** — journal Table 1
- **Love Plot** — covariate balance
"""
    )

with phase_cols[2]:
    st.markdown("### Phase 3 · Outcomes")
    st.caption("Estimation and presentation.")
    st.markdown(
        """
- **Outcomes Table** — Table 2
- **Forest Plot** — RR / OR / HR
- **Two-Cohort Bar** — absolute risks
- **Kaplan-Meier Curve** — survival
"""
    )

with phase_cols[3]:
    st.markdown("### Phase 4 · Rigor & Reporting")
    st.caption("Stress tests and submission.")
    st.markdown(
        """
- **Power / E-value / NNT**
- **Effect Size**
- **Multiple Comparisons**
- **KM Diagnostics** (new) — PH check
- **STROBE + RECORD** (new) — checklist
"""
    )

st.markdown("---")

# ---------------------------------------------------------------------------
# Quick chooser
# ---------------------------------------------------------------------------

st.header("3. Quick chooser")
st.caption("If you know exactly what you need, pick from the table below.")

chooser = pd.DataFrame(
    [
        ["Pre-register the study design", "Pre-Analysis Plan", "Phase 1", "—"],
        ["Identify and document bias risks", "Bias Check", "Phase 1", "—"],
        ["Build a Table 1 (before/after PSM)", "PSM Table", "Phase 2", "Baseline CSV"],
        ["Visualize covariate balance", "Love Plot", "Phase 2", "Baseline CSV"],
        ["Build a Table 2 (outcomes)", "Outcomes Table", "Phase 3", "MOA + KM CSVs"],
        ["Forest plot of RR/OR/HR", "Forest Plot", "Phase 3", "MOA / KM CSVs"],
        ["Absolute-risk bar chart", "Two-Cohort Bar", "Phase 3", "MOA CSVs"],
        ["Survival curve", "Kaplan-Meier Curve", "Phase 3", "KM CSV"],
        ["Power, E-values, NNT/NNH", "Power & Sensitivity", "Phase 4", "MOA CSVs"],
        ["Standardized effect sizes", "Effect Size", "Phase 4", "Manual entry"],
        ["Correct p-values across outcomes", "Multiple Comparisons", "Phase 4", "MOA CSVs"],
        ["Check proportional hazards", "KM Diagnostics", "Phase 4", "KM CSV"],
        ["Reporting checklist", "STROBE + RECORD", "Phase 4", "Manuscript"],
    ],
    columns=["Goal", "Tool", "Phase", "Primary input"],
)
st.dataframe(chooser, hide_index=True, use_container_width=True)

# ---------------------------------------------------------------------------
# Export guide
# ---------------------------------------------------------------------------

st.markdown("---")
st.header("4. TriNetX export guide")
exports_df = pd.DataFrame(
    [
        [
            "Baseline Patient Characteristics CSV",
            "Table 1, balance diagnostics",
            "PSM Table, Love Plot",
        ],
        [
            "Measures of Association CSV",
            "Risks, RR/OR, p-values",
            "Outcomes Table, Forest Plot, Two-Cohort Bar, Multiple Comparisons, Power & Sensitivity",
        ],
        [
            "Kaplan-Meier CSV",
            "Survival, HRs, log-rank p, PH p",
            "Kaplan-Meier Curve, KM Diagnostics, Outcomes Table, Forest Plot",
        ],
        [
            "Manual entry",
            "Curated values from outside TriNetX",
            "Effect Size, Forest Plot, Multiple Comparisons",
        ],
    ],
    columns=["TriNetX export", "Use for", "Compatible tools"],
)
st.table(exports_df)

# ---------------------------------------------------------------------------
# Methods language
# ---------------------------------------------------------------------------

st.markdown("---")
st.header("5. Suggested Methods text")
st.caption("Copy into your manuscript Methods section and adapt.")
st.markdown(
    """
> Manuscript figures, tables, and rigor diagnostics were prepared from TriNetX
> Analytics exports using the TriNetX Publication Toolkit (v2), a Streamlit
> application providing a unified study-context layer, shared TriNetX parsers,
> and per-phase tools for cohort construction, outcome presentation, and rigor
> evaluation. Pre-specification documents, bias diagnostics, sensitivity
> analyses, and reporting checklists were generated within the same session
> against the same export files used to produce the manuscript's tables and
> figures.
"""
)

render_reproducibility_footer("Home")
