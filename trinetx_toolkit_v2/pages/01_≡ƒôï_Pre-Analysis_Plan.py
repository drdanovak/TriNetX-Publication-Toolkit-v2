"""
01_Pre-Analysis_Plan.py — Phase 1 tool (NEW in v2).

A structured questionnaire that captures the analytical decisions that should
be fixed BEFORE any data are pulled from TriNetX. The output is a
manuscript-quality Markdown document suitable for:

- OSF or clinicaltrials.gov registration
- Internal protocol archive
- An appendix to the manuscript demonstrating that the study followed a
  pre-specified plan rather than a post-hoc fishing expedition.

The questionnaire is organized in the order an investigator should think
about a study: research question, exposure, comparator, outcomes, time,
analytic strategy, sensitivity analyses, reporting standards.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

import streamlit as st

from utils.session import (
    ensure_context,
    render_context_banner,
    render_methods_text,
    render_check_callout,
)
from utils.exports import render_reproducibility_footer, _stamp_filename

st.set_page_config(page_title="Pre-Analysis Plan", page_icon="📋", layout="wide")
ctx = ensure_context()

st.title("Pre-Analysis Plan Generator")
st.caption(
    "A structured questionnaire that captures every analytical decision before any "
    "TriNetX data are pulled. Produces a Markdown protocol suitable for OSF "
    "registration or an appendix to the manuscript."
)

render_context_banner()

# ---------------------------------------------------------------------------
# Persistent state for the form
# ---------------------------------------------------------------------------

PAP_KEY = "pap_v2"
if PAP_KEY not in st.session_state:
    st.session_state[PAP_KEY] = {}
pap: Dict = st.session_state[PAP_KEY]


def field(key: str, label: str, kind: str = "text", **kwargs):
    """Render a field that writes back into the persistent dict."""
    default = pap.get(key, kwargs.get("value", ""))
    widget_key = f"pap_{key}"

    if kind == "text":
        v = st.text_input(label, value=str(default), key=widget_key, help=kwargs.get("help"))
    elif kind == "textarea":
        v = st.text_area(
            label, value=str(default), key=widget_key, height=kwargs.get("height", 100),
            help=kwargs.get("help"),
        )
    elif kind == "select":
        opts = kwargs["options"]
        default_idx = opts.index(default) if default in opts else 0
        v = st.selectbox(label, opts, index=default_idx, key=widget_key, help=kwargs.get("help"))
    elif kind == "multiselect":
        v = st.multiselect(
            label, kwargs["options"], default=default if isinstance(default, list) else [],
            key=widget_key, help=kwargs.get("help"),
        )
    elif kind == "number":
        v = st.number_input(
            label, value=float(default) if default else float(kwargs.get("default", 0)),
            min_value=kwargs.get("min_value", 0.0),
            max_value=kwargs.get("max_value", 1000000.0),
            step=kwargs.get("step", 1.0),
            key=widget_key, help=kwargs.get("help"),
        )
    elif kind == "date":
        v = st.date_input(label, value=default if default else datetime.today(), key=widget_key)
    else:
        v = default

    pap[key] = v
    return v


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------

st.markdown("### Section 1. Study identification")
col1, col2 = st.columns(2)
with col1:
    field("title", "Working title")
    field("investigator", "Lead investigator (and ORCID, optional)")
with col2:
    field("registration_date", "Date this protocol is finalized", kind="date")
    field("institution", "Institution")

st.markdown("### Section 2. Research question (PICO)")
col1, col2 = st.columns(2)
with col1:
    field("population", "P — Population", kind="textarea",
          help="Describe the eligible patients: clinical condition, age range, sex, healthcare setting, geography.")
    field("intervention", "I — Intervention / exposure", kind="textarea",
          help="Define exposure exactly: drug class, procedure, device, or condition. Include codes if known.")
with col2:
    field("comparator", "C — Comparator", kind="textarea",
          help="Active comparator (preferred), alternative treatment, or unexposed control. Justify the choice.")
    field("outcome_primary", "O — Primary outcome(s)", kind="textarea",
          help="Define each primary outcome with codes, ascertainment window, and outcome polarity.")

st.markdown("### Section 3. Index date and time windows")
col1, col2 = st.columns(2)
with col1:
    field("index_definition", "Index date definition", kind="textarea",
          help="Exactly when does follow-up start? First exposure? First diagnosis? Registration date?")
    field("lookback_window", "Look-back window (days)", kind="number",
          help="Days of prior data required before index to establish baseline covariates. 365 or 730 is common.",
          default=365, step=30.0)
with col2:
    field("washout_window", "Washout window (days)", kind="number",
          help="Days of exposure-free time required before index. Use 0 if new-user design is not enforced.",
          default=180, step=30.0)
    field("followup_window", "Follow-up window (days)", kind="number",
          help="Maximum follow-up time per patient. Censor at this point if no event has occurred.",
          default=365, step=30.0)

field("immortal_time_addressed", "How is immortal-time bias prevented?", kind="textarea",
      help="Required if the exposure definition includes time accrued after a clinical event. Describe the new-user / target-trial-emulation design.")

st.markdown("### Section 4. Secondary outcomes and subgroups")
col1, col2 = st.columns(2)
with col1:
    field("outcome_secondary", "Secondary outcomes", kind="textarea",
          help="List each secondary outcome with the same level of detail as the primary outcome.")
with col2:
    field("subgroups_planned", "Planned subgroup analyses", kind="textarea",
          help="List subgroups now and commit to testing for interaction. Post-hoc subgroups should be flagged as exploratory.")

field("negative_controls", "Negative-control outcomes", kind="textarea",
      help="Outcomes that should NOT be affected by exposure (e.g., ingrown toenails for a cardioprotective drug). Negative controls test residual confounding empirically.")

st.markdown("### Section 5. Analytic strategy")
col1, col2 = st.columns(2)
with col1:
    field("matching_strategy", "Matching strategy",
          kind="select",
          options=[
              "1:1 propensity score matching (greedy)",
              "1:1 propensity score matching (optimal)",
              "1:k propensity score matching",
              "Stratified by propensity score",
              "Inverse probability weighting",
              "No matching (covariate adjustment only)",
              "Other (describe in next field)",
          ])
    field("matching_caliper", "Matching caliper (SD of logit PS)", kind="number",
          default=0.1, step=0.05, help="0.1 to 0.25 of the SD of the logit of the propensity score is standard.")
with col2:
    field("balance_threshold", "SMD threshold for balance", kind="number",
          default=0.10, step=0.01, help="|SMD| above this threshold is considered imbalanced. 0.10 is conventional.")
    field("matching_strategy_other", "Other matching strategy (if needed)", kind="textarea")

field("covariates", "Covariates used for matching / adjustment", kind="textarea",
      help="List covariates explicitly. Specify whether continuous variables enter as linear, splined, or categorized.")

st.markdown("### Section 6. Effect estimation")
col1, col2 = st.columns(2)
with col1:
    field("primary_effect", "Primary effect estimand",
          kind="select",
          options=["Risk Ratio", "Odds Ratio", "Hazard Ratio", "Risk Difference", "Other"])
    field("alpha", "Alpha", kind="number", default=ctx.alpha, step=0.005)
with col2:
    field("multiple_comparison_method", "Multiple comparisons correction",
          kind="select",
          options=[
              "None — primary outcome is single, secondary outcomes pre-specified as exploratory",
              "Bonferroni",
              "Holm-Bonferroni",
              "Benjamini-Hochberg FDR",
              "Benjamini-Yekutieli FDR",
          ])
    field("two_sided", "Hypothesis testing",
          kind="select", options=["Two-sided", "One-sided (justify)"])

field("multiple_comparison_family", "What is the family of tests?", kind="textarea",
      help="A multiple-comparisons correction is only meaningful when the family of tests is pre-specified.")

st.markdown("### Section 7. Sensitivity analyses (pre-specified)")
field("sensitivity_analyses", "Sensitivity analyses", kind="multiselect",
      options=[
          "E-value for unmeasured confounding",
          "Negative-control outcomes",
          "Alternative washout windows",
          "Alternative look-back windows",
          "Alternative outcome ascertainment windows",
          "Subgroup analyses (per Section 4)",
          "Alternative matching algorithm",
          "Unmatched / adjusted-only secondary analysis",
          "Repeat analysis with different propensity-score model",
      ],
      help="Pre-specify which sensitivity analyses will be performed.")

st.markdown("### Section 8. Reporting and data sharing")
col1, col2 = st.columns(2)
with col1:
    field("reporting_standard", "Reporting standard",
          kind="select", options=["STROBE + RECORD", "STROBE only", "Other"])
    field("data_sharing", "Data-sharing statement",
          kind="select",
          options=[
              "Aggregated outputs only (TriNetX policy)",
              "De-identified individual-level via DUA",
              "No data sharing",
          ])
with col2:
    field("preregistration_target", "Pre-registration target",
          kind="select", options=["OSF", "ClinicalTrials.gov", "EU PAS Register", "Internal only", "None"])
    field("code_availability", "Code availability",
          kind="select", options=["Public repository", "On request", "Not applicable"])

field("limitations_anticipated", "Limitations anticipated at this stage", kind="textarea",
      help="Pre-specifying known limitations strengthens the manuscript Discussion.")

# ---------------------------------------------------------------------------
# Build the document
# ---------------------------------------------------------------------------

def render_value(v):
    if isinstance(v, list):
        return ", ".join(str(x) for x in v) if v else "_Not specified_"
    if v is None or v == "":
        return "_Not specified_"
    return str(v)


def build_protocol_markdown(pap: Dict, ctx) -> str:
    return f"""# Pre-Analysis Plan

**{render_value(pap.get('title'))}**

| Field | Value |
|---|---|
| Lead investigator | {render_value(pap.get('investigator'))} |
| Institution | {render_value(pap.get('institution'))} |
| Date finalized | {render_value(pap.get('registration_date'))} |
| Pre-registration target | {render_value(pap.get('preregistration_target'))} |

## 1. Research Question (PICO)

**Population.** {render_value(pap.get('population'))}

**Intervention / exposure.** {render_value(pap.get('intervention'))}

**Comparator.** {render_value(pap.get('comparator'))}

**Primary outcome(s).** {render_value(pap.get('outcome_primary'))}

## 2. Index Date and Time Windows

- **Index date definition.** {render_value(pap.get('index_definition'))}
- **Look-back window.** {render_value(pap.get('lookback_window'))} days
- **Washout window.** {render_value(pap.get('washout_window'))} days
- **Follow-up window.** {render_value(pap.get('followup_window'))} days

**Immortal-time bias.** {render_value(pap.get('immortal_time_addressed'))}

## 3. Secondary Outcomes and Subgroups

**Secondary outcomes.** {render_value(pap.get('outcome_secondary'))}

**Subgroups planned.** {render_value(pap.get('subgroups_planned'))}

**Negative-control outcomes.** {render_value(pap.get('negative_controls'))}

## 4. Analytic Strategy

- **Matching strategy.** {render_value(pap.get('matching_strategy'))} ({render_value(pap.get('matching_strategy_other'))})
- **Matching caliper.** {render_value(pap.get('matching_caliper'))} SD of logit PS
- **Balance threshold.** \\|SMD\\| ≤ {render_value(pap.get('balance_threshold'))}

**Covariates.** {render_value(pap.get('covariates'))}

## 5. Effect Estimation

- **Primary estimand.** {render_value(pap.get('primary_effect'))}
- **Alpha.** {render_value(pap.get('alpha'))}
- **Hypothesis testing.** {render_value(pap.get('two_sided'))}
- **Multiple-comparisons correction.** {render_value(pap.get('multiple_comparison_method'))}
- **Family of tests.** {render_value(pap.get('multiple_comparison_family'))}

## 6. Sensitivity Analyses (Pre-specified)

{render_value(pap.get('sensitivity_analyses'))}

## 7. Reporting and Data Sharing

- **Reporting standard.** {render_value(pap.get('reporting_standard'))}
- **Data-sharing statement.** {render_value(pap.get('data_sharing'))}
- **Code availability.** {render_value(pap.get('code_availability'))}

## 8. Anticipated Limitations

{render_value(pap.get('limitations_anticipated'))}

## 9. Study Context Snapshot

| Field | Value |
|---|---|
| Cohort 1 label | {ctx.cohort_1_label} |
| Cohort 2 label | {ctx.cohort_2_label} |
| Treated / exposed cohort | Cohort {ctx.treated_cohort} ({ctx.treated_label}) |
| Outcome polarity | {ctx.outcome_polarity} |

---

_Generated by the TriNetX Publication Toolkit v2 on {datetime.now().strftime('%Y-%m-%d %H:%M')}_.
"""


st.markdown("---")
st.subheader("Generated protocol")

doc = build_protocol_markdown(pap, ctx)

with st.expander("Preview", expanded=True):
    st.markdown(doc)

col1, col2 = st.columns(2)
with col1:
    st.download_button(
        "Download Markdown",
        data=doc.encode("utf-8"),
        file_name=_stamp_filename("pre_analysis_plan", "md"),
        mime="text/markdown",
        use_container_width=True,
    )
with col2:
    st.download_button(
        "Download plain-text",
        data=doc.encode("utf-8"),
        file_name=_stamp_filename("pre_analysis_plan", "txt"),
        mime="text/plain",
        use_container_width=True,
    )

# ---------------------------------------------------------------------------
# Check + methods
# ---------------------------------------------------------------------------

render_check_callout(
    "Pre-registration is most valuable when it is timestamped before TriNetX queries are run. "
    "Upload this document to OSF, your institutional repository, or the EU PAS register, and cite "
    "the registration in your Methods section."
)

render_methods_text(
    """The study was pre-specified in a protocol generated by the TriNetX Publication
Toolkit v2 (Pre-Analysis Plan tool) before any data were pulled from TriNetX. The protocol
defined the index date, look-back and washout windows, primary and secondary outcomes,
matching strategy, primary effect estimand, multiple-comparisons family, and a set of
pre-specified sensitivity analyses (including E-value analysis and negative-control
outcomes). The protocol is included as Supplementary Material.""",
    title="Methods text for your manuscript",
)

render_reproducibility_footer("Pre-Analysis Plan")
