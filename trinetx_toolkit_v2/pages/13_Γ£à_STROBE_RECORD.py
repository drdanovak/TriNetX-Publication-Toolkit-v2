"""
13_STROBE_RECORD.py — Phase 4 tool (NEW in v2).

The original v1 toolkit included STROBE, the general reporting standard for
observational studies. For TriNetX research the more appropriate standard is
RECORD — the REporting of studies Conducted using Observational
Routinely-collected health Data — which extends STROBE with items specifically
relevant to claims-data and EHR-based research.

This v2 tool combines both standards into a single checklist, marks each
item as STROBE, RECORD, or both, and produces:

- A scored checklist with per-item comments and tag-based feedback
- A coverage summary (percent fully addressed in each section)
- A downloadable CSV that meets reviewer expectations
- A Methods-section snippet referring to both standards
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

import pandas as pd
import streamlit as st

from utils.session import (
    ensure_context,
    render_context_banner,
    render_methods_text,
    render_check_callout,
)
from utils.exports import render_reproducibility_footer, _stamp_filename

st.set_page_config(page_title="STROBE + RECORD", page_icon="✅", layout="wide")
ctx = ensure_context()

st.title("STROBE + RECORD Checklist")
st.caption(
    "Combined reporting checklist for observational studies on routinely-collected health "
    "data. STROBE applies to all observational studies; RECORD items specifically address "
    "EHR/claims-based research like TriNetX."
)

render_context_banner()

# ---------------------------------------------------------------------------
# Checklist items
# ---------------------------------------------------------------------------

# Each item is (section, source, num, item_text, guidance, tag_options)
# source: "STROBE", "RECORD", or "BOTH"

CHECKLIST = [
    # Title & Abstract
    ("Title and Abstract", "STROBE", "1a",
     "Indicate the study's design with a commonly used term in the title or abstract.",
     "State cohort/case-control/cross-sectional explicitly.",
     ["Design not mentioned.", "Design referenced but unclear.", "Design clearly stated."]),
    ("Title and Abstract", "STROBE", "1b",
     "Provide in the abstract an informative and balanced summary of what was done and what was found.",
     "Cover purpose, design, key results, and conclusions.",
     ["Abstract incomplete.", "Abstract present but unbalanced.", "Balanced, complete abstract."]),
    ("Title and Abstract", "RECORD", "1.1",
     "Mention the type of data used in the title or abstract.",
     "E.g., 'using a federated electronic health record network'.",
     ["Data source not mentioned.", "Data source vague.", "Data source named in title/abstract."]),
    ("Title and Abstract", "RECORD", "1.2",
     "Specify the database name and the geographic region covered.",
     "E.g., 'TriNetX Diamond Network, United States and Europe'.",
     ["Database not named.", "Database named but coverage unclear.", "Database and geography fully specified."]),
    ("Title and Abstract", "RECORD", "1.3",
     "If applicable, the report should be linked to RECORD's reporting guidelines.",
     "A citation of Benchimol et al. RECORD 2015 is sufficient.",
     ["RECORD not cited.", "RECORD mentioned only in passing.", "RECORD cited and used as the reporting standard."]),

    # Introduction
    ("Introduction", "STROBE", "2",
     "Explain the scientific background and rationale for the investigation.",
     "Describe why the study was done.",
     ["Background missing.", "Background limited.", "Background well-contextualized."]),
    ("Introduction", "STROBE", "3",
     "State specific objectives, including any prespecified hypotheses.",
     "Be precise about what was tested.",
     ["Objectives vague.", "Objectives present, hypotheses missing.", "Objectives and hypotheses clear."]),

    # Methods - design
    ("Methods", "STROBE", "4",
     "Present key elements of study design early in the paper.",
     "Identify the type of study and key design features.",
     ["Design features missing.", "Design features partial.", "Design features clear."]),
    ("Methods", "STROBE", "5",
     "Describe the setting, locations, and relevant dates including periods of recruitment, exposure, follow-up, and data collection.",
     "Include calendar windows for cohort definition and follow-up.",
     ["Dates missing.", "Some dates given.", "All relevant dates given."]),
    ("Methods", "STROBE", "6a",
     "Give the eligibility criteria, and the sources and methods of selection of participants.",
     "Define inclusion/exclusion criteria explicitly.",
     ["Criteria vague.", "Criteria partial.", "Criteria complete."]),
    ("Methods", "RECORD", "6.1",
     "The methods of study population selection should be listed in detail, including codes used to define exposures, outcomes, and covariates.",
     "Provide ICD-10, CPT, LOINC, NDC codes in a table or supplement.",
     ["Codes not provided.", "Codes partially provided.", "Codes fully tabulated, including in supplement."]),
    ("Methods", "RECORD", "6.2",
     "Any validation studies of the codes or algorithms used to identify participants should be referenced.",
     "Cite published PPV/sensitivity studies of the codes used.",
     ["No validation cited.", "Validation cited briefly.", "Validation studies cited explicitly."]),
    ("Methods", "RECORD", "6.3",
     "If validation was conducted for this study, describe its results.",
     "Internal validation against chart review or registry.",
     ["Not addressed.", "Mentioned but not detailed.", "Internal validation described."]),
    ("Methods", "STROBE", "7",
     "Clearly define all outcomes, exposures, predictors, potential confounders, and effect modifiers.",
     "Give diagnostic criteria.",
     ["Definitions vague.", "Some definitions complete.", "All definitions clear."]),
    ("Methods", "RECORD", "7.1",
     "A complete list of codes and algorithms used to classify exposures, outcomes, confounders, and effect modifiers should be provided.",
     "Provide a downloadable supplement.",
     ["No code list.", "Partial code list.", "Complete code list provided."]),
    ("Methods", "STROBE", "8",
     "For each variable of interest, give sources of data and details of methods of assessment (measurement).",
     "Describe how each variable was captured and validated.",
     ["Sources not described.", "Sources partially described.", "Sources fully described."]),
    ("Methods", "STROBE", "9",
     "Describe any efforts to address potential sources of bias.",
     "Active comparators, negative controls, sensitivity analyses.",
     ["Bias not addressed.", "Bias addressed briefly.", "Bias mitigation comprehensive."]),
    ("Methods", "STROBE", "10",
     "Explain how the study size was arrived at.",
     "Power calculation or feasibility justification.",
     ["No rationale.", "Sample size mentioned.", "Sample size rationale provided."]),
    ("Methods", "STROBE", "11",
     "Explain how quantitative variables were handled in the analyses.",
     "Cut-points, transformations.",
     ["Not described.", "Partially described.", "Fully described."]),
    ("Methods", "STROBE", "12a",
     "Describe all statistical methods, including those used to control for confounding.",
     "PSM, IPW, regression adjustment.",
     ["Methods incomplete.", "Methods partial.", "Methods detailed."]),
    ("Methods", "STROBE", "12b",
     "Describe any methods used to examine subgroups and interactions.",
     "Test for interaction, pre-specified subgroups.",
     ["Subgroup methods missing.", "Subgroup methods partial.", "Subgroup methods detailed."]),
    ("Methods", "STROBE", "12c",
     "Explain how missing data were addressed.",
     "Complete-case, multiple imputation, missing-indicator.",
     ["Missing data not addressed.", "Briefly addressed.", "Explicit missing-data handling."]),
    ("Methods", "STROBE", "12d",
     "If applicable, explain how loss to follow-up was addressed.",
     "Censoring rules, sensitivity to follow-up duration.",
     ["Not addressed.", "Mentioned only.", "Explicit loss-to-follow-up handling."]),
    ("Methods", "STROBE", "12e",
     "Describe any sensitivity analyses.",
     "E-value, negative controls, alternative windows.",
     ["No sensitivity analyses.", "Sensitivity analyses limited.", "Sensitivity analyses comprehensive."]),
    ("Methods", "RECORD", "12.1",
     "Describe the extent to which the investigators had access to the database population used to create the study population.",
     "Confirm full vs limited access to the underlying records.",
     ["Access not stated.", "Access partially stated.", "Access fully described."]),
    ("Methods", "RECORD", "12.2",
     "Authors should provide information on the data cleaning methods used in the study.",
     "Document how the data were cleaned before analysis.",
     ["Not described.", "Briefly described.", "Cleaning methods detailed."]),
    ("Methods", "RECORD", "12.3",
     "State whether the study included person-level, institutional-level, or other data linkage across two or more databases.",
     "TriNetX studies are typically person-level within network.",
     ["Linkage not described.", "Linkage partial.", "Linkage fully described."]),

    # Results
    ("Results", "STROBE", "13",
     "Report numbers of individuals at each stage (eligible, included, follow-up, analyzed). Consider a flow diagram.",
     "Show attrition with reasons.",
     ["Numbers missing.", "Some numbers given.", "Full attrition with diagram."]),
    ("Results", "RECORD", "13.1",
     "Describe the algorithm used to construct the study cohort, perhaps by use of a flow diagram.",
     "Include eligibility checks specific to the data source.",
     ["Algorithm not given.", "Algorithm partial.", "Algorithm shown in diagram."]),
    ("Results", "STROBE", "14",
     "Give characteristics of study participants and information on exposures, confounders, and missing data.",
     "Provide Table 1.",
     ["Characteristics missing.", "Characteristics partial.", "Characteristics complete."]),
    ("Results", "STROBE", "15",
     "Report numbers of outcome events or summary measures over time.",
     "Tabulate outcomes.",
     ["Events not reported.", "Some events reported.", "Events fully reported."]),
    ("Results", "STROBE", "16",
     "Give unadjusted estimates and, if applicable, confounder-adjusted estimates with precision.",
     "Crude + adjusted with 95% CI.",
     ["Estimates incomplete.", "Estimates partial.", "Crude and adjusted reported."]),
    ("Results", "STROBE", "17",
     "Report other analyses done (subgroup, sensitivity).",
     "All secondary analyses.",
     ["No secondary analyses.", "Some reported.", "All reported."]),

    # Discussion
    ("Discussion", "STROBE", "18",
     "Summarize key results with reference to study objectives.",
     "Restate main findings.",
     ["Summary missing.", "Summary partial.", "Summary clear."]),
    ("Discussion", "STROBE", "19",
     "Discuss limitations, taking into account sources of potential bias or imprecision.",
     "Honest discussion of limitations.",
     ["Limitations missing.", "Limitations partial.", "Limitations comprehensive."]),
    ("Discussion", "RECORD", "19.1",
     "Discuss the implications of using data that were not created or collected to answer the specific research question(s).",
     "Acknowledge secondary use of data.",
     ["Not discussed.", "Briefly discussed.", "Fully discussed."]),
    ("Discussion", "STROBE", "20",
     "Give a cautious overall interpretation of results.",
     "Avoid causal language unless warranted.",
     ["Interpretation overreaches.", "Interpretation partial.", "Interpretation cautious and appropriate."]),
    ("Discussion", "STROBE", "21",
     "Discuss the generalizability (external validity) of the study results.",
     "Healthcare system, demographics, time period.",
     ["Generalizability not discussed.", "Partial.", "Generalizability discussed."]),

    # Other information
    ("Other Information", "STROBE", "22",
     "Give the source of funding and the role of funders for the present study.",
     "Funder role explicit.",
     ["Funding not stated.", "Funder role not specified.", "Funding and role complete."]),
    ("Other Information", "RECORD", "22.1",
     "Authors should provide information on how to access any supplemental information.",
     "Code lists, sensitivity analyses, full results.",
     ["Supplements unreferenced.", "Supplements referenced.", "Supplements clearly accessible."]),
    ("Other Information", "RECORD", "22.2",
     "Authors should specify the steps taken to ensure their data and code are reproducible.",
     "Code repository, data-access procedure.",
     ["Reproducibility not addressed.", "Partial.", "Reproducibility statement complete."]),
]

# ---------------------------------------------------------------------------
# State management
# ---------------------------------------------------------------------------

CHECKLIST_KEY = "strobe_record_v2"
if CHECKLIST_KEY not in st.session_state:
    st.session_state[CHECKLIST_KEY] = {
        "scores": [2] * len(CHECKLIST),
        "comments": [""] * len(CHECKLIST),
        "tags": [[] for _ in CHECKLIST],
    }
state = st.session_state[CHECKLIST_KEY]

# Sync length if checklist changed across versions
for k in ("scores", "comments", "tags"):
    while len(state[k]) < len(CHECKLIST):
        state[k].append(2 if k == "scores" else ("" if k == "comments" else []))
    state[k] = state[k][:len(CHECKLIST)]

# ---------------------------------------------------------------------------
# Toolbar
# ---------------------------------------------------------------------------

col_a, col_b, col_c = st.columns([2, 2, 2])
with col_a:
    show_incomplete_only = st.checkbox("Show incomplete only (score < 3)", value=False)
with col_b:
    filter_source = st.selectbox("Filter by source",
                                 options=["All", "STROBE only", "RECORD only", "Both"])
with col_c:
    filter_section = st.selectbox(
        "Filter by section",
        options=["All"] + sorted({item[0] for item in CHECKLIST}),
    )


SCORE_LABEL = {1: "1 — Not addressed", 2: "2 — Partially", 3: "3 — Fully addressed"}
SCORE_COLOR = {1: "#EF4444", 2: "#F59E0B", 3: "#10B981"}


# ---------------------------------------------------------------------------
# Render checklist grouped by section
# ---------------------------------------------------------------------------

st.markdown("---")

sections_in_order = []
for s, *_ in CHECKLIST:
    if s not in sections_in_order:
        sections_in_order.append(s)

section_to_items = defaultdict(list)
for i, item in enumerate(CHECKLIST):
    section_to_items[item[0]].append((i, item))

for section in sections_in_order:
    if filter_section != "All" and filter_section != section:
        continue

    items_for_section = section_to_items[section]
    if filter_source != "All":
        items_for_section = [
            (i, it) for i, it in items_for_section
            if (filter_source == "STROBE only" and it[1] == "STROBE")
            or (filter_source == "RECORD only" and it[1] == "RECORD")
            or (filter_source == "Both" and it[1] == "BOTH")
        ]
    if show_incomplete_only:
        items_for_section = [(i, it) for i, it in items_for_section if state["scores"][i] < 3]
    if not items_for_section:
        continue

    st.markdown(f"## {section}")

    for idx, (sec, source, num, text, guidance, tag_opts) in items_for_section:
        cols = st.columns([0.5, 3.5, 1.5, 2.5])
        with cols[0]:
            color = SCORE_COLOR[state["scores"][idx]]
            st.markdown(
                f"<div style='width:14px;height:14px;border-radius:50%;background:{color};"
                f"margin-top:8px'></div>",
                unsafe_allow_html=True,
            )
        with cols[1]:
            src_badge = {
                "STROBE": "#2C5F7C",
                "RECORD": "#7C5C2C",
                "BOTH": "#5C7C2C",
            }[source]
            st.markdown(
                f"<span style='font-weight:600'>{num}. {text}</span> "
                f"<span style='display:inline-block;padding:1px 6px;border-radius:3px;"
                f"background:{src_badge};color:white;font-size:0.7em;margin-left:6px'>{source}</span>",
                unsafe_allow_html=True,
            )
            st.caption(guidance)
        with cols[2]:
            state["scores"][idx] = st.radio(
                "Score",
                options=[1, 2, 3],
                format_func=lambda v: SCORE_LABEL[v],
                horizontal=False,
                index=state["scores"][idx] - 1,
                key=f"score_{idx}",
                label_visibility="collapsed",
            )
        with cols[3]:
            selected_tags = st.multiselect(
                "Issues",
                options=tag_opts,
                default=state["tags"][idx],
                key=f"tags_{idx}",
                label_visibility="collapsed",
            )
            state["tags"][idx] = selected_tags
            state["comments"][idx] = st.text_input(
                "Comment",
                value=state["comments"][idx],
                key=f"comment_{idx}",
                placeholder="Free-text note",
                label_visibility="collapsed",
            )

# ---------------------------------------------------------------------------
# Summary metrics
# ---------------------------------------------------------------------------

st.markdown("---")
st.subheader("Coverage summary")

n_items = len(CHECKLIST)
scores = state["scores"]
n_full = sum(1 for s in scores if s == 3)
n_partial = sum(1 for s in scores if s == 2)
n_none = sum(1 for s in scores if s == 1)
avg_score = sum(scores) / max(1, n_items)
pct_full = n_full / n_items * 100

c1, c2, c3, c4 = st.columns(4)
c1.metric("Items", n_items)
c2.metric("Fully addressed", f"{n_full} ({pct_full:.0f}%)")
c3.metric("Partially", n_partial)
c4.metric("Not addressed", n_none)

# Per-section breakdown
section_scores = defaultdict(list)
for i, (sec, *_rest) in enumerate(CHECKLIST):
    section_scores[sec].append(scores[i])

section_df = pd.DataFrame([
    {
        "Section": sec,
        "Items": len(sc),
        "Mean score": round(sum(sc) / len(sc), 2),
        "% fully": f"{sum(1 for x in sc if x == 3) / len(sc) * 100:.0f}%",
    }
    for sec, sc in section_scores.items()
])
st.dataframe(section_df, hide_index=True, use_container_width=True)

# Per-source breakdown
source_scores = defaultdict(list)
for i, (_, source, *_rest) in enumerate(CHECKLIST):
    source_scores[source].append(scores[i])

source_df = pd.DataFrame([
    {
        "Source": src,
        "Items": len(sc),
        "Mean score": round(sum(sc) / len(sc), 2),
        "% fully": f"{sum(1 for x in sc if x == 3) / len(sc) * 100:.0f}%",
    }
    for src, sc in source_scores.items()
])
st.dataframe(source_df, hide_index=True, use_container_width=True)

# ---------------------------------------------------------------------------
# Downloads
# ---------------------------------------------------------------------------

results_df = pd.DataFrame([
    {
        "Section": item[0],
        "Source": item[1],
        "Item #": item[2],
        "Item text": item[3],
        "Guidance": item[4],
        "Score": state["scores"][i],
        "Score label": SCORE_LABEL[state["scores"][i]],
        "Tags": "; ".join(state["tags"][i]),
        "Comment": state["comments"][i],
    }
    for i, item in enumerate(CHECKLIST)
])

st.markdown("---")
st.download_button(
    "Download checklist CSV",
    data=results_df.to_csv(index=False).encode("utf-8"),
    file_name=_stamp_filename("strobe_record_checklist", "csv"),
    mime="text/csv",
)

# ---------------------------------------------------------------------------
# Methods + check
# ---------------------------------------------------------------------------

render_check_callout(
    "STROBE and RECORD assess reporting completeness, not analytical adequacy. A fully "
    "addressed checklist confirms that the manuscript describes the study; it does not by "
    "itself confirm that the design was strong."
)

render_methods_text(
    """The manuscript was prepared in accordance with the STROBE guidelines for
observational studies and the RECORD extension for studies using routinely-collected
health data. Reporting completeness was assessed using the combined STROBE+RECORD
checklist in the TriNetX Publication Toolkit v2. The completed checklist is included
as Supplementary Material.""",
    title="Methods text for your manuscript",
)

render_reproducibility_footer("STROBE + RECORD Checklist")
