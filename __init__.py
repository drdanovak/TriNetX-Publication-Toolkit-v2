"""
12_KM_Diagnostics.py — Phase 4 tool (NEW in v2).

Tests whether the hazard ratio reported by TriNetX (or computed elsewhere)
is interpretable. The proportional hazards (PH) assumption is the central
assumption of the Cox model that underlies every hazard ratio. If hazards
are not proportional, the HR represents a time-weighted average that may be
misleading.

This tool provides two complementary diagnostics:

1. **Log-log plot.** Plots log(-log(S(t))) against log(t). Under PH, the
   two cohort curves are roughly parallel. Divergent, crossing, or
   converging curves signal PH violation.

2. **Numerical PH check.** Uses the proportional-hazard assumption
   p-value that TriNetX reports in the KM export. We surface and interpret
   it explicitly because authors often miss it. We also provide a
   reconstructed PH test from the survival table when TriNetX's value is
   missing, using a Grambsch-Therneau-style chi-square statistic on the
   schoenfeld-residual-like log-cumulative-hazard slope test.

The output is a diagnostic figure plus a Methods-section paragraph that
either supports the HR or recommends reporting time-varying effect
estimates.
"""

from __future__ import annotations

from io import BytesIO
import math

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
    upload_as_bytesio,
)
from utils.parsers import parse_km_csv, KMExport, _read_uploaded, detect_export_type, EXPORT_KM
from utils.figure_defaults import (
    palette_colors, preset_size, FONT_CHOICES, DEFAULT_DPI, PALETTES,
    FIGURE_PRESETS, NULL_LINE_COLOR,
)
from utils.formatters import fmt_p, fmt_ratio
from utils.exports import render_figure_downloads, render_reproducibility_footer

st.set_page_config(page_title="KM Diagnostics", page_icon="🔬", layout="wide")
ctx = ensure_context()

st.title("Kaplan-Meier Diagnostics")
st.caption(
    "Verifies the proportional-hazards assumption before reporting a hazard ratio. "
    "Produces a log-log plot and surfaces TriNetX's PH-assumption test value."
)

render_context_banner()

# ---------------------------------------------------------------------------
# Upload (or reuse session uploads)
# ---------------------------------------------------------------------------

st.markdown("### Upload a Kaplan-Meier export")
st.caption(
    "Use a TriNetX Kaplan-Meier CSV. If you already uploaded a KM file in another tool "
    "during this session, you can reuse it here."
)

km_uploads = list_uploads(of_type=EXPORT_KM)
options = ["Upload new file"] + [u["name"] for u in km_uploads]
choice = st.selectbox("Source", options, index=0)

km: KMExport = None
file_bytes: bytes = None
source_name: str = ""

if choice == "Upload new file":
    uploaded = st.file_uploader("TriNetX Kaplan-Meier CSV", type=["csv", "txt"])
    if uploaded is not None:
        raw = uploaded.read()
        file_bytes = raw
        try:
            etype = detect_export_type(raw.decode("utf-8-sig", errors="replace"))
            if etype != EXPORT_KM:
                st.error(
                    f"This file was classified as `{etype}`, not a Kaplan-Meier export. "
                    "Make sure you uploaded a TriNetX Kaplan-Meier CSV."
                )
                st.stop()
            km = parse_km_csv(BytesIO(raw))
            source_name = uploaded.name
            register_upload(
                file_id=f"km_{uploaded.name}",
                name=uploaded.name,
                raw_bytes=raw,
                detected_type=EXPORT_KM,
            )
        except Exception as exc:
            st.error(f"Could not parse the file: {exc}")
            st.stop()
else:
    selected = next((u for u in km_uploads if u["name"] == choice), None)
    if selected:
        file_bytes = selected["bytes"]
        try:
            km = parse_km_csv(BytesIO(file_bytes))
            source_name = selected["name"]
        except Exception as exc:
            st.error(f"Could not parse the cached file: {exc}")
            st.stop()

if km is None:
    st.info("Upload a Kaplan-Meier CSV to continue.")
    st.stop()

# ---------------------------------------------------------------------------
# Top-line summary
# ---------------------------------------------------------------------------

st.markdown("### Top-line PH assessment")

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Hazard Ratio", fmt_ratio(km.hazard_ratio, decimals=ctx.ratio_decimals) or "—")
    if km.hazard_ratio_ci != (None, None):
        lo, hi = km.hazard_ratio_ci
        if lo is not None and hi is not None:
            st.caption(f"95% CI: {fmt_ratio(lo, decimals=ctx.ratio_decimals)} to {fmt_ratio(hi, decimals=ctx.ratio_decimals)}")
with c2:
    st.metric("Log-rank p", fmt_p(km.log_rank_p, style=ctx.p_style) or "—")
    st.caption("Tests whether cohort survival differs at all.")
with c3:
    st.metric("PH assumption p", fmt_p(km.ph_assumption_p, style=ctx.p_style) or "—")
    st.caption("Tests whether PH holds. Higher is better.")

if km.ph_assumption_p is not None:
    if km.ph_assumption_p < 0.05:
        st.error(
            "**PH assumption rejected (p < .05).** The hazard ratio represents a "
            "time-weighted average and may be misleading. Consider reporting time-stratified "
            "hazard ratios (e.g., 0-90 days vs > 90 days) or using restricted mean survival "
            "time (RMST) as the primary estimand."
        )
    elif km.ph_assumption_p < 0.10:
        st.warning(
            "**PH assumption marginal (p < .10).** Inspect the log-log plot carefully. "
            "Report a sensitivity analysis with time-stratified or RMST analyses."
        )
    else:
        st.success(
            "**PH assumption supported (p ≥ .10).** The reported hazard ratio can be "
            "interpreted as a time-constant relative hazard."
        )
else:
    st.warning(
        "The TriNetX export does not include a PH-assumption p-value. The log-log plot "
        "below provides a visual check, but a formal test should be reported."
    )

# ---------------------------------------------------------------------------
# Log-log plot
# ---------------------------------------------------------------------------

st.markdown("---")
st.markdown("### Log-log plot")
st.caption(
    "Plot of log(-log(S(t))) against log(t). Under proportional hazards the two cohort "
    "curves are roughly parallel. Convergent, divergent, or crossing curves indicate that "
    "the PH assumption is violated."
)

with st.sidebar:
    st.header("Plot options")
    palette_name = st.selectbox("Palette", list(PALETTES.keys()),
                                 index=list(PALETTES.keys()).index(ctx.palette)
                                 if ctx.palette in PALETTES else 0)
    color1, color2 = palette_colors(palette_name)
    font_family = st.selectbox("Font family", FONT_CHOICES,
                                index=FONT_CHOICES.index(ctx.font_family)
                                if ctx.font_family in FONT_CHOICES else 0)
    preset = st.selectbox("Figure size preset", list(FIGURE_PRESETS.keys()),
                          index=list(FIGURE_PRESETS.keys()).index(ctx.figure_preset)
                          if ctx.figure_preset in FIGURE_PRESETS else 0)
    base_w, base_h = preset_size(preset)
    line_width = st.slider("Line width", 1.0, 4.0, 2.0, step=0.5)
    show_grid = st.checkbox("Show grid", value=True)


def make_loglog_plot_safe(km: KMExport, ctx):
    """Build the log-log diagnostic plot.

    Returns a tuple (fig, log_t, ll1, ll2) when the survival time-series
    is usable, or just `fig` when only an explanatory placeholder can be
    drawn (summary-only KM exports).
    """
    df = km.df

    if df.empty:
        fig, ax = plt.subplots(figsize=(base_w, base_h))
        ax.text(0.5, 0.5,
                "This KM export does not include the survival time-series.\n"
                "Re-export from TriNetX with the curve data, or use the\n"
                "PH-assumption p-value above as your primary diagnostic.",
                ha="center", va="center", transform=ax.transAxes,
                fontsize=10, color="#555")
        ax.axis("off")
        return fig

    s1_candidates = [c for c in df.columns
                     if "Cohort 1" in c and "Survival Probability" in c and "CI" not in c.upper()]
    s2_candidates = [c for c in df.columns
                     if "Cohort 2" in c and "Survival Probability" in c and "CI" not in c.upper()]

    if not s1_candidates or not s2_candidates:
        fig, ax = plt.subplots(figsize=(base_w, base_h))
        ax.text(0.5, 0.5, "Survival probability columns not found.",
                ha="center", va="center", transform=ax.transAxes)
        ax.axis("off")
        return fig

    t_col = "Time (Days)" if "Time (Days)" in df.columns else df.columns[0]

    t = pd.to_numeric(df[t_col], errors="coerce")
    s1 = pd.to_numeric(df[s1_candidates[0]], errors="coerce")
    s2 = pd.to_numeric(df[s2_candidates[0]], errors="coerce")

    mask = (t > 0) & s1.notna() & s2.notna() & (s1 > 0) & (s1 < 1) & (s2 > 0) & (s2 < 1)
    t, s1, s2 = t[mask], s1[mask], s2[mask]

    if len(t) < 3:
        fig, ax = plt.subplots(figsize=(base_w, base_h))
        ax.text(0.5, 0.5, "Not enough informative time-points for a log-log plot.",
                ha="center", va="center", transform=ax.transAxes)
        ax.axis("off")
        return fig

    log_t = np.log(t)
    ll1 = np.log(-np.log(s1))
    ll2 = np.log(-np.log(s2))

    fig, ax = plt.subplots(figsize=(base_w, base_h))
    ax.plot(log_t, ll1, color=color1, linewidth=line_width,
            label=ctx.cohort_1_label or "Cohort 1")
    ax.plot(log_t, ll2, color=color2, linewidth=line_width,
            label=ctx.cohort_2_label or "Cohort 2")
    ax.set_xlabel("log(Time in days)", fontname=font_family, fontsize=11)
    ax.set_ylabel("log(−log S(t))", fontname=font_family, fontsize=11)
    ax.set_title("Log-log diagnostic plot", fontname=font_family, fontsize=12, weight="bold")
    if show_grid:
        ax.grid(True, color="#DDDDDD", linewidth=0.6)
    ax.legend(loc="best", frameon=False, prop={"family": font_family})
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    return fig, log_t, ll1, ll2


result = make_loglog_plot_safe(km, ctx)

if isinstance(result, tuple):
    fig, log_t, ll1, ll2 = result
    st.pyplot(fig)

    # ---------------------------------------------------------------------------
    # Reconstructed numerical PH check from the curves
    # ---------------------------------------------------------------------------
    st.markdown("### Reconstructed numerical PH check")
    st.caption(
        "When TriNetX does not provide a PH-assumption p-value, this reconstructs an "
        "approximate test from the survival table. The slope of the difference "
        "log(-log S₁(t)) − log(-log S₂(t)) is regressed against log(t); a slope "
        "indistinguishable from zero is consistent with proportional hazards."
    )

    diff = ll1 - ll2
    n = len(diff)
    x = log_t.values
    y = diff.values

    x_bar = x.mean()
    y_bar = y.mean()
    sxx = ((x - x_bar) ** 2).sum()
    sxy = ((x - x_bar) * (y - y_bar)).sum()
    slope = sxy / sxx if sxx > 0 else float("nan")
    intercept = y_bar - slope * x_bar

    # SE of slope
    residuals = y - (intercept + slope * x)
    rss = (residuals ** 2).sum()
    if n > 2 and sxx > 0:
        sigma2 = rss / (n - 2)
        se_slope = math.sqrt(sigma2 / sxx)
        t_stat = slope / se_slope if se_slope > 0 else float("nan")
        # Approximate two-sided p from normal
        from math import erf, sqrt
        z = abs(t_stat)
        p_recon = 2 * (1 - 0.5 * (1 + erf(z / sqrt(2))))
    else:
        slope = float("nan")
        se_slope = float("nan")
        p_recon = float("nan")

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Slope of log(−log) difference", f"{slope:+.4f}" if not math.isnan(slope) else "—")
        st.caption("Zero is consistent with PH.")
    with m2:
        st.metric("SE", f"{se_slope:.4f}" if not math.isnan(se_slope) else "—")
    with m3:
        st.metric("Reconstructed PH p", fmt_p(p_recon, style=ctx.p_style) if not math.isnan(p_recon) else "—")

    if not math.isnan(p_recon):
        if p_recon < 0.05:
            st.warning(
                "Reconstructed PH test suggests the assumption is violated. This is an "
                "approximate test based on the discretized survival table and should be "
                "compared with the TriNetX-reported PH p-value when available."
            )
        else:
            st.success("Reconstructed PH test is consistent with the PH assumption.")

    render_figure_downloads(fig, prefix="km_loglog_diagnostic", dpi=DEFAULT_DPI)

else:
    fig = result
    st.pyplot(fig)
    p_recon = None
    slope = None

# ---------------------------------------------------------------------------
# Verify against source
# ---------------------------------------------------------------------------

st.markdown("---")
render_source_check(
    f"KM auxiliary sections from {source_name}",
    pd.DataFrame([
        {"Field": "Hazard Ratio", "Value": fmt_ratio(km.hazard_ratio, decimals=4)},
        {"Field": "HR CI lower", "Value": fmt_ratio(km.hazard_ratio_ci[0], decimals=4)},
        {"Field": "HR CI upper", "Value": fmt_ratio(km.hazard_ratio_ci[1], decimals=4)},
        {"Field": "Log-rank p", "Value": fmt_p(km.log_rank_p, style="scientific")},
        {"Field": "PH assumption p", "Value": fmt_p(km.ph_assumption_p, style="scientific")},
        {"Field": "Time points", "Value": str(km.source_provenance.get("n_time_points", 0))},
        {"Field": "Max days", "Value": str(km.max_days or "—")},
    ])
)

# ---------------------------------------------------------------------------
# Methods + check
# ---------------------------------------------------------------------------

if km.ph_assumption_p is None:
    ph_text = (
        "The TriNetX export did not include a numerical PH-assumption test; visual inspection "
        "of the log(−log S(t)) plot was used as the primary check."
    )
elif km.ph_assumption_p >= 0.10:
    ph_text = (
        f"The proportional-hazards assumption was supported "
        f"(TriNetX PH-assumption p = {fmt_p(km.ph_assumption_p, style=ctx.p_style)})."
    )
else:
    ph_text = (
        f"The proportional-hazards assumption was not supported "
        f"(TriNetX PH-assumption p = {fmt_p(km.ph_assumption_p, style=ctx.p_style)}); "
        f"a time-stratified or restricted-mean-survival-time analysis should be reported."
    )

render_check_callout(
    "The hazard ratio in your Outcomes Table and Forest Plot should be interpreted with the "
    "PH assumption in mind. If the assumption is rejected, qualify the HR in the manuscript "
    "or report a time-stratified estimate."
)

render_methods_text(
    f"""Before reporting the hazard ratio, the proportional-hazards assumption was
evaluated using a log(−log S(t)) plot and the TriNetX-reported PH-assumption test
within the KM Diagnostics tool of the TriNetX Publication Toolkit v2. {ph_text}""",
    title="Methods text for your manuscript",
)

render_reproducibility_footer("KM Diagnostics")
