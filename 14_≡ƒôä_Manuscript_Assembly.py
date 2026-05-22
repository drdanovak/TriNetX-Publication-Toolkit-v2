"""
05_Outcomes_Table.py — Phase 3 tool.

Generates a journal-style Table 2 outcomes table by parsing one or more
TriNetX MOA and/or KM exports.

This is a migrated v2 implementation that demonstrates the standardization
pattern every page follows:

1. Title + caption
2. Study context banner
3. Upload block with reuse of session-cached files
4. Parsed-summary banner
5. Edit-before-export data editor
6. Output preview (matching Word formatting)
7. Standardized downloads (CSV + DOCX)
8. Verify-against-source widget
9. Auto-generated narrative paragraph for Results
10. Check callout
11. Methods text block
12. Reproducibility footer
"""

from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, List

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
    EXPORT_MOA, EXPORT_KM, EXPORT_UNKNOWN,
    MOAExport, KMExport,
)
from utils.formatters import (
    fmt_p, fmt_pct, fmt_ratio_with_ci, fmt_count, fmt_count_pct,
    safe_float, safe_int, crosses_null,
)
from utils.exports import render_table_downloads, render_reproducibility_footer

st.set_page_config(page_title="Outcomes Table", page_icon="🧮", layout="wide")
ctx = ensure_context()

st.title("Outcomes Table Generator")
st.caption(
    "Builds a Table 2-style outcomes table from one or more TriNetX Measures of Association "
    "and/or Kaplan-Meier exports. Each outcome contributes a section with both cohort rows, "
    "events, risks, the chosen effect estimate, and a p-value."
)

render_context_banner(show_advanced=True)

# ---------------------------------------------------------------------------
# Upload block
# ---------------------------------------------------------------------------

st.markdown("### Upload outcome CSV files")
st.caption(
    "MOA exports populate Risk Ratio / Odds Ratio columns; KM exports populate Hazard "
    "Ratio. You can upload multiple files; the table will list each outcome as its own "
    "section."
)

session_uploads = [u for u in list_uploads() if u["type"] in {EXPORT_MOA, EXPORT_KM}]

col1, col2 = st.columns(2)
with col1:
    uploaded_files = st.file_uploader(
        "New uploads (MOA and/or KM CSVs)",
        type=["csv", "txt"],
        accept_multiple_files=True,
    )
with col2:
    if session_uploads:
        st.markdown("**From this session:**")
        reuse = st.multiselect(
            "Reuse session uploads",
            options=[u["name"] for u in session_uploads],
            default=[u["name"] for u in session_uploads],
        )
    else:
        reuse = []
        st.caption("No outcome files in this session yet.")


# ---------------------------------------------------------------------------
# Parse and classify
# ---------------------------------------------------------------------------

parsed: List[Dict[str, Any]] = []
parse_errors: List[str] = []


def add_parsed(name: str, raw_bytes: bytes):
    try:
        etype = detect_export_type(raw_bytes.decode("utf-8-sig", errors="replace"))
    except Exception as exc:
        parse_errors.append(f"{name}: could not detect export type ({exc})")
        return

    if etype == EXPORT_MOA:
        try:
            obj = parse_moa_csv(BytesIO(raw_bytes))
            parsed.append({
                "name": name, "type": EXPORT_MOA, "obj": obj, "raw": raw_bytes,
            })
            register_upload(f"moa_{name}", name, raw_bytes, EXPORT_MOA)
        except Exception as exc:
            parse_errors.append(f"{name}: MOA parse failed ({exc})")
    elif etype == EXPORT_KM:
        try:
            obj = parse_km_csv(BytesIO(raw_bytes))
            parsed.append({
                "name": name, "type": EXPORT_KM, "obj": obj, "raw": raw_bytes,
            })
            register_upload(f"km_{name}", name, raw_bytes, EXPORT_KM)
        except Exception as exc:
            parse_errors.append(f"{name}: KM parse failed ({exc})")
    else:
        parse_errors.append(f"{name}: file type unknown")


if uploaded_files:
    for f in uploaded_files:
        raw = f.read()
        add_parsed(f.name, raw)

for name in reuse:
    cached = next((u for u in session_uploads if u["name"] == name), None)
    if cached and not any(p["name"] == name for p in parsed):
        add_parsed(cached["name"], cached["bytes"])

if parse_errors:
    with st.expander("Parsing issues", expanded=True):
        for e in parse_errors:
            st.warning(e)

if not parsed:
    st.info("Upload at least one TriNetX outcome CSV (MOA or KM) to begin.")
    st.stop()

# Parsed-summary banner
n_moa = sum(1 for p in parsed if p["type"] == EXPORT_MOA)
n_km = sum(1 for p in parsed if p["type"] == EXPORT_KM)
st.success(
    f"Parsed **{len(parsed)}** outcome file(s): {n_moa} Measures of Association and {n_km} Kaplan-Meier."
)

# ---------------------------------------------------------------------------
# Editable metadata table
# ---------------------------------------------------------------------------

st.markdown("### Review and edit outcome metadata")
st.caption(
    "Rename the outcomes that will appear in the table, set the display order, and edit "
    "the section labels. The Include checkbox controls which rows appear in the final output."
)

meta_rows = []
for i, p in enumerate(parsed):
    obj = p["obj"]
    default_outcome = p["name"].rsplit(".", 1)[0].replace("_", " ").strip()
    if isinstance(obj, MOAExport):
        meta_rows.append({
            "Include": True,
            "Order": i + 1,
            "Outcome": default_outcome,
            "Section": "Primary outcomes",
            "Detected type": "Measures of Association",
            "Source file": p["name"],
        })
    else:
        meta_rows.append({
            "Include": True,
            "Order": i + 1,
            "Outcome": default_outcome,
            "Section": "Time-to-event outcomes",
            "Detected type": "Kaplan-Meier",
            "Source file": p["name"],
        })

metadata_df = pd.DataFrame(meta_rows)
edited_meta = st.data_editor(
    metadata_df,
    use_container_width=True,
    num_rows="fixed",
    column_config={
        "Include": st.column_config.CheckboxColumn(),
        "Order": st.column_config.NumberColumn(min_value=1, step=1),
        "Detected type": st.column_config.TextColumn(disabled=True),
        "Source file": st.column_config.TextColumn(disabled=True),
    },
    key="outcomes_meta_editor",
)

# ---------------------------------------------------------------------------
# Build the table
# ---------------------------------------------------------------------------

st.markdown("### Table preview")

include_or = st.checkbox("Include Odds Ratio column", value=False)
include_rd = st.checkbox("Include Risk Difference column", value=False)
show_source_col = st.checkbox("Include 'detected type' column (for QA only)", value=False)


def build_outcomes_rows(parsed, metadata: pd.DataFrame, ctx) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    metadata = metadata.sort_values("Order").reset_index(drop=True)

    current_section = None
    for _, meta in metadata.iterrows():
        if not meta["Include"]:
            continue
        section = str(meta["Section"]).strip() or "Outcomes"
        if section != current_section:
            rows.append({"_row_type": "section", "Outcome": section})
            current_section = section

        # Find the underlying parsed object
        p = next((x for x in parsed if x["name"] == meta["Source file"]), None)
        if p is None:
            continue
        obj = p["obj"]
        outcome_name = str(meta["Outcome"]).strip() or meta["Source file"]

        if isinstance(obj, MOAExport):
            _emit_moa_rows(rows, obj, outcome_name, ctx,
                           include_or=include_or, include_rd=include_rd,
                           show_source=show_source_col)
        elif isinstance(obj, KMExport):
            _emit_km_rows(rows, obj, outcome_name, ctx, show_source=show_source_col)

    return rows


def _emit_moa_rows(rows, moa: MOAExport, outcome_name, ctx,
                  include_or, include_rd, show_source):
    p_disp = fmt_p(moa.primary_p_value, style=ctx.p_style)
    rr_disp = fmt_ratio_with_ci(moa.risk_ratio_value,
                                 moa.risk_ratio_ci[0], moa.risk_ratio_ci[1],
                                 decimals=ctx.ratio_decimals)
    or_disp = fmt_ratio_with_ci(moa.odds_ratio_value,
                                 moa.odds_ratio_ci[0], moa.odds_ratio_ci[1],
                                 decimals=ctx.ratio_decimals)

    # Compute RD from risks if needed
    rd_disp = ""
    if include_rd and moa.cohort_1_risk is not None and moa.cohort_2_risk is not None:
        # Direction: treated minus control
        if ctx.treated_cohort == "1":
            rd = moa.cohort_1_risk - moa.cohort_2_risk
        else:
            rd = moa.cohort_2_risk - moa.cohort_1_risk
        rd_disp = fmt_pct(rd, decimals=ctx.pct_decimals)

    # Row 1: outcome name as anchor with effect estimate / p
    anchor_row = {
        "_row_type": "outcome_anchor",
        "Outcome": outcome_name,
        "Cohort": "",
        "Patients": "",
        "Events": "",
        "Risk": "",
        "Effect estimate (95% CI)": rr_disp,
        "p": p_disp,
    }
    if include_or:
        anchor_row["Odds Ratio (95% CI)"] = or_disp
    if include_rd:
        anchor_row["Risk Difference"] = rd_disp
    if show_source:
        anchor_row["Source"] = "MOA"
    rows.append(anchor_row)

    # Per-cohort rows
    c1_name = ctx.cohort_1_label or moa.cohort_1_label
    c2_name = ctx.cohort_2_label or moa.cohort_2_label

    rows.append({
        "_row_type": "cohort",
        "Outcome": "",
        "Cohort": c1_name,
        "Patients": fmt_count(moa.cohort_1_n),
        "Events": fmt_count(moa.cohort_1_events),
        "Risk": fmt_pct(moa.cohort_1_risk, decimals=ctx.pct_decimals),
        "Effect estimate (95% CI)": "",
        "p": "",
        **({"Odds Ratio (95% CI)": ""} if include_or else {}),
        **({"Risk Difference": ""} if include_rd else {}),
        **({"Source": ""} if show_source else {}),
    })
    rows.append({
        "_row_type": "cohort",
        "Outcome": "",
        "Cohort": c2_name,
        "Patients": fmt_count(moa.cohort_2_n),
        "Events": fmt_count(moa.cohort_2_events),
        "Risk": fmt_pct(moa.cohort_2_risk, decimals=ctx.pct_decimals),
        "Effect estimate (95% CI)": "",
        "p": "",
        **({"Odds Ratio (95% CI)": ""} if include_or else {}),
        **({"Risk Difference": ""} if include_rd else {}),
        **({"Source": ""} if show_source else {}),
    })


def _emit_km_rows(rows, km: KMExport, outcome_name, ctx, show_source):
    hr_disp = fmt_ratio_with_ci(km.hazard_ratio,
                                 km.hazard_ratio_ci[0], km.hazard_ratio_ci[1],
                                 decimals=ctx.ratio_decimals)
    p_disp = fmt_p(km.log_rank_p, style=ctx.p_style)

    anchor_row = {
        "_row_type": "outcome_anchor",
        "Outcome": outcome_name,
        "Cohort": "",
        "Patients": "",
        "Events": "",
        "Risk": "",
        "Effect estimate (95% CI)": hr_disp,
        "p": p_disp,
    }
    if show_source:
        anchor_row["Source"] = "KM"
    rows.append(anchor_row)

    rows.append({
        "_row_type": "cohort",
        "Outcome": "",
        "Cohort": ctx.cohort_1_label or km.cohort_1_label,
        "Patients": fmt_count(km.cohort_1_n),
        "Events": "",
        "Risk": "",
        "Effect estimate (95% CI)": "",
        "p": "",
        **({"Source": ""} if show_source else {}),
    })
    rows.append({
        "_row_type": "cohort",
        "Outcome": "",
        "Cohort": ctx.cohort_2_label or km.cohort_2_label,
        "Patients": fmt_count(km.cohort_2_n),
        "Events": "",
        "Risk": "",
        "Effect estimate (95% CI)": "",
        "p": "",
        **({"Source": ""} if show_source else {}),
    })


rows = build_outcomes_rows(parsed, edited_meta, ctx)

if not rows:
    st.info("Include at least one outcome to generate the table.")
    st.stop()


def rows_to_dataframe(rows):
    if not rows:
        return pd.DataFrame()
    columns = []
    for r in rows:
        for k in r.keys():
            if k != "_row_type" and k not in columns:
                columns.append(k)
    out = []
    for r in rows:
        row = {col: r.get(col, "") for col in columns}
        if r.get("_row_type") == "section":
            row[columns[0]] = f"— {r.get('Outcome', '')} —"
        out.append(row)
    return pd.DataFrame(out, columns=columns)


display_df = rows_to_dataframe(rows)

st.dataframe(display_df, hide_index=True, use_container_width=True)

# ---------------------------------------------------------------------------
# Downloads
# ---------------------------------------------------------------------------

render_table_downloads(
    display_df,
    prefix="outcomes_table",
    docx_title=ctx.study_title or "Outcomes Table",
)

# ---------------------------------------------------------------------------
# Verify against source
# ---------------------------------------------------------------------------

st.markdown("---")
for p in parsed:
    obj = p["obj"]
    if isinstance(obj, MOAExport):
        render_source_check(
            f"MOA parsed values from {p['name']}",
            pd.DataFrame([
                {"Field": "Cohort 1 N", "Value": str(obj.cohort_1_n)},
                {"Field": "Cohort 1 events", "Value": str(obj.cohort_1_events)},
                {"Field": "Cohort 1 risk", "Value": fmt_pct(obj.cohort_1_risk, decimals=4)},
                {"Field": "Cohort 2 N", "Value": str(obj.cohort_2_n)},
                {"Field": "Cohort 2 events", "Value": str(obj.cohort_2_events)},
                {"Field": "Cohort 2 risk", "Value": fmt_pct(obj.cohort_2_risk, decimals=4)},
                {"Field": "Primary p-value", "Value": f"{obj.primary_p_value} (from {obj.primary_p_source})"},
                {"Field": "Risk Ratio", "Value": fmt_ratio_with_ci(obj.risk_ratio_value, obj.risk_ratio_ci[0], obj.risk_ratio_ci[1])},
                {"Field": "Odds Ratio", "Value": fmt_ratio_with_ci(obj.odds_ratio_value, obj.odds_ratio_ci[0], obj.odds_ratio_ci[1])},
            ]),
        )
    elif isinstance(obj, KMExport):
        render_source_check(
            f"KM parsed values from {p['name']}",
            pd.DataFrame([
                {"Field": "Cohort 1 N", "Value": str(obj.cohort_1_n)},
                {"Field": "Cohort 2 N", "Value": str(obj.cohort_2_n)},
                {"Field": "Hazard Ratio", "Value": fmt_ratio_with_ci(obj.hazard_ratio, obj.hazard_ratio_ci[0], obj.hazard_ratio_ci[1])},
                {"Field": "Log-rank p", "Value": fmt_p(obj.log_rank_p, style="scientific")},
                {"Field": "PH assumption p", "Value": fmt_p(obj.ph_assumption_p, style="scientific")},
            ]),
        )

# ---------------------------------------------------------------------------
# Narrative summary for Results
# ---------------------------------------------------------------------------

def build_results_narrative(parsed, ctx) -> str:
    if not parsed:
        return ""
    pieces = []
    treated_label = ctx.treated_label
    control_label = ctx.control_label
    n_outcomes = len(parsed)
    pieces.append(
        f"We evaluated {n_outcomes} outcome{'s' if n_outcomes != 1 else ''} comparing "
        f"{treated_label} (treated/exposed) with {control_label} (comparison)."
    )
    for p in parsed:
        obj = p["obj"]
        outcome_name = p["name"].rsplit(".", 1)[0].replace("_", " ")
        if isinstance(obj, MOAExport):
            rr_str = fmt_ratio_with_ci(obj.risk_ratio_value,
                                        obj.risk_ratio_ci[0], obj.risk_ratio_ci[1],
                                        decimals=ctx.ratio_decimals)
            p_str = fmt_p(obj.primary_p_value, style=ctx.p_style)
            pieces.append(
                f"For {outcome_name}, the risk was "
                f"{fmt_pct(obj.cohort_1_risk, decimals=ctx.pct_decimals)} in {obj.cohort_1_label} "
                f"versus {fmt_pct(obj.cohort_2_risk, decimals=ctx.pct_decimals)} in {obj.cohort_2_label} "
                f"(risk ratio {rr_str}; p = {p_str})."
            )
        elif isinstance(obj, KMExport):
            hr_str = fmt_ratio_with_ci(obj.hazard_ratio,
                                        obj.hazard_ratio_ci[0], obj.hazard_ratio_ci[1],
                                        decimals=ctx.ratio_decimals)
            p_str = fmt_p(obj.log_rank_p, style=ctx.p_style)
            pieces.append(
                f"For {outcome_name}, the hazard ratio was {hr_str} (log-rank p = {p_str})."
            )
    return " ".join(pieces)


with st.expander("Results-section narrative (auto-generated)", expanded=False):
    narrative = build_results_narrative(parsed, ctx)
    st.markdown(narrative)
    st.download_button(
        "Download narrative (Markdown)",
        data=narrative.encode("utf-8"),
        file_name="results_narrative.md",
        mime="text/markdown",
    )

# ---------------------------------------------------------------------------
# Check + methods
# ---------------------------------------------------------------------------

render_check_callout(
    "If you combined MOA and KM outputs, make the effect-estimate column label explicit "
    "in the published table because risk ratios and hazard ratios answer different "
    "questions (cumulative incidence vs instantaneous hazard)."
)

render_methods_text(
    f"""The outcomes table was generated from {n_moa} Measures of Association and
{n_km} Kaplan-Meier TriNetX exports using the Outcomes Table tool of the TriNetX
Publication Toolkit v2. For each outcome, the table reports patient counts, event
counts, cohort risks, the requested effect estimate with 95% confidence interval,
and the p-value parsed from the appropriate section of the source export.""",
    title="Methods text for your manuscript",
)

render_reproducibility_footer("Outcomes Table")
