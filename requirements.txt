"""
06_Forest_Plot.py — Phase 3 tool.

Generates a publication-grade forest plot of RR/OR/HR estimates from one or
more TriNetX MOA and/or KM exports. This is a v2 migrated implementation
that uses the shared parser, palette, and export modules.

Key v2 features demonstrated:
- Session-cached uploads (no re-uploading the same file across tools)
- Cohort labels and direction inherited from the study context
- Palette and font inherited from session defaults
- PNG + SVG downloads via the shared exports module
- Verify-against-source widget
- Results narrative and Methods text snippets
"""

from __future__ import annotations

from io import BytesIO
from typing import List, Dict, Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from utils.session import (
    ensure_context,
    render_context_banner,
    render_methods_text,
    render_check_callout,
    render_source_check,
    register_upload,
    list_uploads,
)
from utils.parsers import (
    parse_moa_csv, parse_km_csv, detect_export_type,
    EXPORT_MOA, EXPORT_KM,
    MOAExport, KMExport,
)
from utils.formatters import fmt_ratio_with_ci, fmt_p, crosses_null, safe_float
from utils.figure_defaults import (
    palette_colors, preset_size, FONT_CHOICES,
    PALETTES, FIGURE_PRESETS, DEFAULT_DPI,
    NULL_LINE_COLOR, NULL_LINE_STYLE, CI_LINE_COLOR,
    SIGNIFICANT_COLOR, NONSIGNIFICANT_COLOR,
)
from utils.exports import render_figure_downloads, render_reproducibility_footer

st.set_page_config(page_title="Forest Plot", page_icon="🌲", layout="wide")
ctx = ensure_context()

st.title("Forest Plot Generator")
st.caption(
    "Multi-outcome forest plot of effect estimates with 95% confidence intervals. "
    "Pulls Risk Ratios from MOA exports and Hazard Ratios from KM exports."
)

render_context_banner()

# ---------------------------------------------------------------------------
# Upload (with session reuse)
# ---------------------------------------------------------------------------

st.markdown("### Upload outcome CSV files")

session_uploads = [u for u in list_uploads() if u["type"] in {EXPORT_MOA, EXPORT_KM}]

c1, c2 = st.columns(2)
with c1:
    uploaded_files = st.file_uploader(
        "TriNetX MOA / KM CSV files",
        type=["csv", "txt"],
        accept_multiple_files=True,
    )
with c2:
    if session_uploads:
        reuse = st.multiselect(
            "Reuse session uploads",
            options=[u["name"] for u in session_uploads],
            default=[u["name"] for u in session_uploads],
        )
    else:
        reuse = []
        st.caption("No outcome files cached this session.")

# Parse uploads
parsed: List[Dict[str, Any]] = []
errors: List[str] = []


def add_parsed(name: str, raw_bytes: bytes):
    try:
        etype = detect_export_type(raw_bytes.decode("utf-8-sig", errors="replace"))
    except Exception as exc:
        errors.append(f"{name}: {exc}")
        return
    try:
        if etype == EXPORT_MOA:
            obj = parse_moa_csv(BytesIO(raw_bytes))
            parsed.append({"name": name, "type": EXPORT_MOA, "obj": obj})
            register_upload(f"moa_{name}", name, raw_bytes, EXPORT_MOA)
        elif etype == EXPORT_KM:
            obj = parse_km_csv(BytesIO(raw_bytes))
            parsed.append({"name": name, "type": EXPORT_KM, "obj": obj})
            register_upload(f"km_{name}", name, raw_bytes, EXPORT_KM)
        else:
            errors.append(f"{name}: not recognized as MOA or KM")
    except Exception as exc:
        errors.append(f"{name}: parse error ({exc})")


if uploaded_files:
    for f in uploaded_files:
        add_parsed(f.name, f.read())

for name in reuse:
    cached = next((u for u in session_uploads if u["name"] == name), None)
    if cached and not any(p["name"] == name for p in parsed):
        add_parsed(cached["name"], cached["bytes"])

if errors:
    with st.expander("Parsing issues"):
        for e in errors:
            st.warning(e)

if not parsed:
    st.info("Upload at least one MOA or KM CSV to generate a forest plot.")
    st.stop()

n_moa = sum(1 for p in parsed if p["type"] == EXPORT_MOA)
n_km = sum(1 for p in parsed if p["type"] == EXPORT_KM)
st.success(f"Parsed {len(parsed)} outcome file(s): {n_moa} MOA and {n_km} KM.")

# ---------------------------------------------------------------------------
# Effect-measure selection
# ---------------------------------------------------------------------------

st.markdown("### Effect-measure selection")

# What estimates can we offer?
can_rr = any(p["type"] == EXPORT_MOA and p["obj"].risk_ratio_value is not None for p in parsed)
can_or = any(p["type"] == EXPORT_MOA and p["obj"].odds_ratio_value is not None for p in parsed)
can_hr = any(p["type"] == EXPORT_KM and p["obj"].hazard_ratio is not None for p in parsed)

available = []
if can_rr:
    available.append("Risk Ratio (MOA)")
if can_or:
    available.append("Odds Ratio (MOA)")
if can_hr:
    available.append("Hazard Ratio (KM)")
if can_rr and can_hr:
    available.append("Mixed: RR for MOA, HR for KM")

if not available:
    st.error("No usable effect estimates were found in the parsed files.")
    st.stop()

effect_choice = st.selectbox("Effect measure to plot", options=available)

# ---------------------------------------------------------------------------
# Build rows
# ---------------------------------------------------------------------------

def extract_estimate(p, choice) -> Dict[str, Any]:
    obj = p["obj"]
    name = p["name"].rsplit(".", 1)[0].replace("_", " ")
    if isinstance(obj, MOAExport):
        if "Risk Ratio" in choice:
            return {"label": name, "estimate": obj.risk_ratio_value,
                    "lo": obj.risk_ratio_ci[0], "hi": obj.risk_ratio_ci[1],
                    "p": obj.primary_p_value, "effect_type": "RR"}
        if "Odds Ratio" in choice:
            return {"label": name, "estimate": obj.odds_ratio_value,
                    "lo": obj.odds_ratio_ci[0], "hi": obj.odds_ratio_ci[1],
                    "p": obj.primary_p_value, "effect_type": "OR"}
        # Mixed but this is an MOA -> use RR
        if "Mixed" in choice:
            return {"label": name, "estimate": obj.risk_ratio_value,
                    "lo": obj.risk_ratio_ci[0], "hi": obj.risk_ratio_ci[1],
                    "p": obj.primary_p_value, "effect_type": "RR"}
    elif isinstance(obj, KMExport):
        if "Hazard Ratio" in choice or "Mixed" in choice:
            return {"label": name, "estimate": obj.hazard_ratio,
                    "lo": obj.hazard_ratio_ci[0], "hi": obj.hazard_ratio_ci[1],
                    "p": obj.log_rank_p, "effect_type": "HR"}
    return {}


rows = [extract_estimate(p, effect_choice) for p in parsed]
rows = [r for r in rows if r and r.get("estimate") is not None]

if not rows:
    st.warning("None of the parsed files provided the chosen effect estimate.")
    st.stop()

# Edit
st.markdown("### Edit labels and order")
edit_df = pd.DataFrame([{
    "Include": True, "Order": i + 1, "Outcome": r["label"],
    "Estimate": r["estimate"], "Lower CI": r["lo"], "Upper CI": r["hi"],
    "p": r["p"], "Type": r["effect_type"],
} for i, r in enumerate(rows)])

edited = st.data_editor(
    edit_df,
    use_container_width=True,
    num_rows="fixed",
    column_config={
        "Include": st.column_config.CheckboxColumn(),
        "Order": st.column_config.NumberColumn(min_value=1, step=1),
        "Estimate": st.column_config.NumberColumn(disabled=True, format="%.3f"),
        "Lower CI": st.column_config.NumberColumn(disabled=True, format="%.3f"),
        "Upper CI": st.column_config.NumberColumn(disabled=True, format="%.3f"),
        "p": st.column_config.NumberColumn(disabled=True, format="%.4g"),
        "Type": st.column_config.TextColumn(disabled=True),
    },
)

plot_df = edited[edited["Include"]].sort_values("Order").reset_index(drop=True)
if plot_df.empty:
    st.info("Include at least one outcome to render the forest plot.")
    st.stop()

# ---------------------------------------------------------------------------
# Sidebar visual options
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Plot options")
    palette_name = st.selectbox("Palette", list(PALETTES.keys()),
                                 index=list(PALETTES.keys()).index(ctx.palette) if ctx.palette in PALETTES else 0)
    sig_color, _ = palette_colors(palette_name)
    font_family = st.selectbox("Font family", FONT_CHOICES,
                                index=FONT_CHOICES.index(ctx.font_family) if ctx.font_family in FONT_CHOICES else 0)
    preset = st.selectbox("Figure preset", list(FIGURE_PRESETS.keys()),
                          index=list(FIGURE_PRESETS.keys()).index(ctx.figure_preset) if ctx.figure_preset in FIGURE_PRESETS else 0)
    fig_w, fig_h = preset_size(preset)
    fig_w = st.slider("Width (in)", 4.0, 12.0, float(fig_w), step=0.5)
    fig_h = st.slider("Height (in)", 2.5, 12.0, max(float(fig_h), 0.5 * len(plot_df) + 1.5), step=0.5)
    use_log = st.checkbox("Log-scale x-axis", value=True)
    show_values = st.checkbox("Show estimate + 95% CI text", value=True)
    show_grid = st.checkbox("Show grid", value=False)
    point_size = st.slider("Marker size", 4, 16, 8)
    line_width = st.slider("CI line width", 0.8, 4.0, 2.0, step=0.2)
    font_size = st.slider("Font size", 8, 18, 10)

# ---------------------------------------------------------------------------
# Build the plot
# ---------------------------------------------------------------------------

def make_forest_plot(df: pd.DataFrame) -> plt.Figure:
    n = len(df)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    estimates = df["Estimate"].astype(float).values
    los = df["Lower CI"].astype(float).values
    his = df["Upper CI"].astype(float).values
    labels = df["Outcome"].tolist()
    ps = df["p"].astype(float).values

    # Compute x-axis range
    finite_vals = np.array([v for v in np.concatenate([estimates, los, his]) if np.isfinite(v) and v > 0])
    if use_log and finite_vals.size > 0:
        x_min = max(finite_vals.min() * 0.7, 1e-3)
        x_max = max(finite_vals.max() * 1.4, 1.1)
    else:
        x_min = max(0.0, min(finite_vals.min() - 0.2, 0.5))
        x_max = max(finite_vals.max() + 0.2, 1.5)

    y_positions = np.arange(n)[::-1]

    for y, est, lo, hi, p in zip(y_positions, estimates, los, his, ps):
        sig = not crosses_null(lo, hi, null=1.0) if (lo is not None and hi is not None) else None
        color = sig_color if sig else NONSIGNIFICANT_COLOR
        if np.isfinite(lo) and np.isfinite(hi):
            ax.hlines(y, lo, hi, color=CI_LINE_COLOR, linewidth=line_width, zorder=2)
            ax.vlines([lo, hi], y - 0.08, y + 0.08, color=CI_LINE_COLOR, linewidth=line_width, zorder=2)
        if np.isfinite(est):
            ax.plot(est, y, "s", color=color, markersize=point_size,
                    markeredgecolor=color, zorder=3)

    ax.axvline(1.0, color=NULL_LINE_COLOR, linestyle=NULL_LINE_STYLE, linewidth=0.9, zorder=1)

    ax.set_yticks(y_positions)
    ax.set_yticklabels(labels, fontsize=font_size, fontname=font_family)

    if use_log:
        ax.set_xscale("log")
    ax.set_xlim(x_min, x_max)

    # Axis label
    effect_label = effect_choice if "Mixed" not in effect_choice else "Effect estimate"
    ax.set_xlabel(effect_label, fontsize=font_size, fontname=font_family, weight="bold", labelpad=8)

    if show_grid:
        ax.grid(axis="x", color="#DDDDDD", linewidth=0.5, zorder=0)

    # Value annotations on the right
    if show_values:
        # Convert axis to display coords for placing text outside the right edge
        text_xpos = 1.02  # axis fraction
        for y, est, lo, hi, p in zip(y_positions, estimates, los, his, ps):
            txt = (
                f"{est:.{ctx.ratio_decimals}f} ({lo:.{ctx.ratio_decimals}f}–{hi:.{ctx.ratio_decimals}f})  "
                f"p {fmt_p(p, style=ctx.p_style)}"
            )
            ax.text(text_xpos, y, txt, transform=ax.get_yaxis_transform(),
                    fontsize=font_size, fontname=font_family,
                    va="center", ha="left", clip_on=False)

    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.tick_params(axis="x", labelsize=font_size)
    ax.tick_params(axis="y", length=0)

    fig.tight_layout()
    return fig


fig = make_forest_plot(plot_df)
st.pyplot(fig)

render_figure_downloads(fig, prefix="forest_plot", dpi=DEFAULT_DPI)

# ---------------------------------------------------------------------------
# Verify against source
# ---------------------------------------------------------------------------

st.markdown("---")
parsed_summary = pd.DataFrame([
    {
        "Source file": p["name"],
        "Type": "MOA" if p["type"] == EXPORT_MOA else "KM",
        "Cohort 1 N": getattr(p["obj"], "cohort_1_n", None),
        "Cohort 2 N": getattr(p["obj"], "cohort_2_n", None),
    }
    for p in parsed
])
render_source_check("Parsed file summary", parsed_summary)

# ---------------------------------------------------------------------------
# Methods + check
# ---------------------------------------------------------------------------

n_outcomes = len(plot_df)
n_significant = int(sum(
    1 for _, r in plot_df.iterrows()
    if (r["Lower CI"] is not None and r["Upper CI"] is not None
        and not crosses_null(r["Lower CI"], r["Upper CI"], null=1.0))
))

render_check_callout(
    "Avoid mixing Risk Ratios, Odds Ratios, and Hazard Ratios on the same forest plot unless "
    "the x-axis label states explicitly that mixed effect estimates are shown. RRs and HRs "
    "answer different questions: RRs compare cumulative incidence, HRs compare instantaneous "
    "hazard."
)

render_methods_text(
    f"""A forest plot of {n_outcomes} outcomes was generated using the Forest Plot
tool of the TriNetX Publication Toolkit v2. The chosen effect measure was
**{effect_choice}**. Point estimates and 95% confidence intervals were parsed directly
from the TriNetX exports. Of the {n_outcomes} outcomes plotted, {n_significant} did not
include the null value of 1.0 within their 95% confidence interval.""",
    title="Methods text for your manuscript",
)

render_reproducibility_footer("Forest Plot")
