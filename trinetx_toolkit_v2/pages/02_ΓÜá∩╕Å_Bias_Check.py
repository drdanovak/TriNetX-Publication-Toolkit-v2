"""
02_Bias_Check.py — Phase 1 tool (NEW in v2).

A structured walk-through of the time-related biases that most frequently
contaminate observational TriNetX studies:

- **Immortal-time bias** — periods during which an exposed patient cannot
  experience the outcome by definition of the exposure are counted as
  exposed person-time, artificially lowering the exposed event rate.
- **Reverse causation** — exposure is measured AFTER the outcome could have
  begun, so the apparent cause may be a consequence.
- **Selection bias from prevalent users** — including patients who started
  exposure before study entry mixes incident-user and prevalent-user
  populations, often with very different risk profiles.
- **Look-back window adequacy** — covariates measured over an inadequately
  short window will miss conditions established before the look-back began,
  biasing balance assessments.
- **Outcome ascertainment asymmetry** — different cohorts may have
  different probabilities of being observed for the outcome (more visits,
  more lab tests).

The tool asks the user a structured set of questions, flags configurations
that are likely to produce bias, and outputs a Limitations-section paragraph.
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

st.set_page_config(page_title="Bias Check", page_icon="⚠️", layout="wide")
ctx = ensure_context()

st.title("Bias Check Questionnaire")
st.caption(
    "Identifies time-related and selection biases common in TriNetX studies, and produces "
    "Limitations-section text reflecting what was found."
)

render_context_banner()

st.markdown(
    """
This tool asks structured questions about how the cohort was assembled, how exposure
was ascertained, and how the outcome window was defined. Each section ends with a
**diagnostic flag**: green if no bias risk is detected, amber if mitigation is
recommended, red if the configuration likely produces bias and the analysis should
be reconsidered before submission.
"""
)

BCK_KEY = "bias_v2"
if BCK_KEY not in st.session_state:
    st.session_state[BCK_KEY] = {}
state: Dict = st.session_state[BCK_KEY]

flags: List[Dict] = []  # collected during the form for the final summary


def add_flag(severity: str, section: str, message: str, recommendation: str):
    """severity: 'green', 'amber', 'red'."""
    flags.append({
        "severity": severity,
        "section": section,
        "message": message,
        "recommendation": recommendation,
    })


def colored_badge(severity: str) -> str:
    colors = {
        "green": ("#10B981", "OK"),
        "amber": ("#F59E0B", "Review"),
        "red": ("#EF4444", "Critical"),
    }
    color, label = colors.get(severity, ("#999", severity))
    return (
        f"<span style='display:inline-block;padding:2px 8px;border-radius:4px;"
        f"background:{color};color:white;font-size:0.85em;font-weight:600'>{label}</span>"
    )


# ---------------------------------------------------------------------------
# 1. Immortal-time bias
# ---------------------------------------------------------------------------

st.markdown("### 1. Immortal-time bias")
st.caption(
    "Immortal time is a period of follow-up during which the outcome cannot occur by "
    "construction. The classic case is defining exposure as 'received drug X within 365 days "
    "of diagnosis' — the patient must survive long enough to receive the drug, so the exposed "
    "group is enriched for survivors."
)

q1 = st.radio(
    "Is exposure defined by an event that occurs AFTER index date?",
    ["No — exposure is established at or before index", "Yes", "Unsure"],
    index=0,
    key="bias_q1",
)
state["q1"] = q1

if q1 == "Yes":
    q1a = st.radio(
        "How is the period between index and exposure handled?",
        [
            "Person-time before exposure is counted as exposed (likely biased)",
            "Person-time before exposure is censored or assigned to control",
            "Time-varying exposure with clock-reset at exposure",
            "Other / not sure",
        ],
        key="bias_q1a",
    )
    state["q1a"] = q1a
    if q1a.startswith("Person-time before exposure is counted as exposed"):
        st.error("This configuration produces immortal-time bias. Re-define exposure as a time-varying covariate or shift the index date.")
        add_flag("red", "Immortal-time",
                 "Exposure is defined as a future event with person-time misclassified as exposed.",
                 "Use a target-trial-emulation new-user design, or treat exposure as time-varying with clock-reset.")
    elif q1a == "Other / not sure":
        st.warning("The handling of pre-exposure person-time should be documented explicitly in the manuscript.")
        add_flag("amber", "Immortal-time",
                 "Pre-exposure person-time handling is unclear.",
                 "State explicitly how pre-exposure person-time is classified.")
    else:
        st.success("Pre-exposure person-time is handled correctly.")
        add_flag("green", "Immortal-time", "Pre-exposure handling is appropriate.", "")
elif q1 == "Unsure":
    add_flag("amber", "Immortal-time", "User unsure whether exposure occurs after index.", "Review the exposure definition; if exposure can occur after index, use time-varying analysis.")
else:
    add_flag("green", "Immortal-time", "Exposure established at or before index.", "")


# ---------------------------------------------------------------------------
# 2. Reverse causation
# ---------------------------------------------------------------------------

st.markdown("---")
st.markdown("### 2. Reverse causation")
st.caption(
    "The outcome may have started — or its precursors may have been recorded — before "
    "the exposure. If the outcome window begins on the same date as exposure, prevalent "
    "outcomes can be misclassified as incident events."
)

q2 = st.radio(
    "When does the outcome ascertainment window begin?",
    [
        "Strictly after index (e.g., index + 1 day)",
        "On the index date",
        "Before the index date is allowed (any time)",
        "Unsure",
    ],
    key="bias_q2",
)
state["q2"] = q2

q2b = st.radio(
    "Are patients with a history of the outcome excluded?",
    ["Yes — excluded if outcome occurred before index (true incident design)",
     "Partially — excluded for some outcomes only",
     "No"],
    key="bias_q2b",
)
state["q2b"] = q2b

if q2 == "Before the index date is allowed (any time)":
    st.error("Allowing the outcome to occur before the exposure makes the analysis non-causal.")
    add_flag("red", "Reverse causation", "Outcome can precede exposure.", "Define outcome window to start strictly after index and exclude prevalent outcomes.")
elif q2 == "On the index date":
    st.warning("Same-day outcomes risk reverse causation. State whether index-day events are included.")
    add_flag("amber", "Reverse causation", "Outcomes on the index date are included.", "Consider starting the outcome window at index + 1 day.")
elif q2 == "Unsure":
    add_flag("amber", "Reverse causation", "Outcome window start unclear.", "Document the outcome window explicitly.")
else:
    add_flag("green", "Reverse causation", "Outcome window starts strictly after index.", "")

if q2b == "No":
    add_flag("amber", "Reverse causation", "Patients with a history of the outcome are not excluded.", "Consider an incident-outcome design that excludes prevalent cases.")
elif q2b.startswith("Partially"):
    add_flag("amber", "Reverse causation", "History exclusion applied inconsistently.", "Apply prevalent-outcome exclusion uniformly across all outcomes for consistency.")


# ---------------------------------------------------------------------------
# 3. Prevalent users
# ---------------------------------------------------------------------------

st.markdown("---")
st.markdown("### 3. Prevalent-user bias")
st.caption(
    "Including patients who already started exposure before study entry mixes incident-user "
    "(at-risk window beginning at first exposure) and prevalent-user populations. Prevalent "
    "users have survived early adverse events, biasing toward null."
)

q3 = st.radio(
    "Is exposure defined as new initiation (incident user design)?",
    ["Yes — patients with prior exposure are excluded",
     "Partially — only some lookback enforced",
     "No — prevalent users are included"],
    key="bias_q3",
)
state["q3"] = q3

if q3.startswith("Yes"):
    add_flag("green", "Prevalent-user", "Incident-user design enforced.", "")
elif q3.startswith("Partially"):
    add_flag("amber", "Prevalent-user", "Incident-user design partial.", "Either fully exclude prior users or report a separate prevalent-user sensitivity analysis.")
else:
    add_flag("red", "Prevalent-user", "Prevalent users are mixed with incident users.", "Restrict to incident users for the primary analysis; report prevalent-user as secondary.")


# ---------------------------------------------------------------------------
# 4. Look-back adequacy
# ---------------------------------------------------------------------------

st.markdown("---")
st.markdown("### 4. Look-back window adequacy")
st.caption(
    "Covariates measured over a short look-back will miss conditions established earlier. "
    "Patients with little prior data look healthier than they are, which inflates the "
    "apparent benefit of the exposure."
)

q4a = st.number_input("Look-back window (days)", min_value=0, max_value=3650, value=365, step=30, key="bias_q4a")
q4b = st.radio(
    "Is a minimum data-presence requirement applied (i.e., patients must have at least one healthcare encounter during the look-back)?",
    ["Yes", "No", "Partial"],
    key="bias_q4b",
)
state["q4a"] = q4a
state["q4b"] = q4b

if q4a < 180:
    add_flag("red", "Look-back",
             f"Look-back of {q4a} days is short.",
             "Use at least 365 days, or document why a shorter window is sufficient.")
elif q4a < 365:
    add_flag("amber", "Look-back",
             f"Look-back of {q4a} days is below conventional 365 days.",
             "Consider sensitivity analysis at 365 and 730 days.")
else:
    add_flag("green", "Look-back", f"Look-back of {q4a} days is reasonable.", "")

if q4b == "No":
    add_flag("amber", "Look-back",
             "No minimum data-presence requirement.",
             "Restrict to patients with at least one encounter during the look-back window; report attrition.")


# ---------------------------------------------------------------------------
# 5. Outcome ascertainment asymmetry
# ---------------------------------------------------------------------------

st.markdown("---")
st.markdown("### 5. Outcome ascertainment asymmetry")
st.caption(
    "If the exposed cohort sees the healthcare system more often than the comparator "
    "cohort, the outcome is more likely to be detected in the exposed group regardless of "
    "true biology. Detection bias and surveillance bias can both produce spurious effects."
)

q5 = st.radio(
    "Is the comparator likely to have similar healthcare utilization to the exposed cohort?",
    ["Yes — both are care-seeking populations under similar surveillance",
     "Probably — but not formally assessed",
     "No — exposed cohort likely has more contact with the system",
     "Unsure"],
    key="bias_q5",
)
state["q5"] = q5

q5b = st.checkbox("Negative-control outcomes are pre-specified", value=False, key="bias_q5b")
state["q5b"] = q5b

if q5 == "No — exposed cohort likely has more contact with the system":
    add_flag("red", "Outcome detection", "Detection bias likely.",
             "Use an active comparator with similar surveillance, or restrict analyses to outcomes ascertained the same way in both cohorts.")
elif q5 == "Unsure" or q5.startswith("Probably"):
    add_flag("amber", "Outcome detection", "Surveillance equivalence not formally assessed.",
             "Compare baseline encounter rates between cohorts and report.")
else:
    add_flag("green", "Outcome detection", "Cohorts under similar surveillance.", "")

if not q5b:
    add_flag("amber", "Outcome detection", "No negative-control outcomes pre-specified.",
             "Pre-specify negative-control outcomes to empirically test for residual confounding and surveillance bias.")
else:
    add_flag("green", "Negative controls", "Negative-control outcomes pre-specified.", "")


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

st.markdown("---")
st.subheader("Diagnostic summary")

red_flags = [f for f in flags if f["severity"] == "red"]
amber_flags = [f for f in flags if f["severity"] == "amber"]
green_flags = [f for f in flags if f["severity"] == "green"]

c1, c2, c3 = st.columns(3)
c1.metric("Critical", len(red_flags))
c2.metric("Review", len(amber_flags))
c3.metric("OK", len(green_flags))

if red_flags:
    st.error("Critical issues need to be addressed before the analysis can be defended as causal.")
elif amber_flags:
    st.warning("Some configurations need explicit justification or sensitivity analysis.")
else:
    st.success("No bias risks were flagged. Document the design decisions in the Methods section anyway.")

for f in red_flags + amber_flags + green_flags:
    cols = st.columns([1, 4, 4])
    with cols[0]:
        st.markdown(colored_badge(f["severity"]), unsafe_allow_html=True)
    with cols[1]:
        st.markdown(f"**{f['section']}** — {f['message']}")
    with cols[2]:
        if f["recommendation"]:
            st.caption(f["recommendation"])


# ---------------------------------------------------------------------------
# Limitations text
# ---------------------------------------------------------------------------

def build_limitations_paragraph(flags: List[Dict], state: Dict) -> str:
    pieces = []
    if any(f["section"] == "Immortal-time" and f["severity"] in {"amber", "red"} for f in flags):
        pieces.append(
            "exposure was defined as a future event relative to index date, with the "
            "potential for immortal-time bias if pre-exposure person-time is not handled "
            "appropriately"
        )
    if any(f["section"] == "Reverse causation" and f["severity"] in {"amber", "red"} for f in flags):
        pieces.append(
            "the outcome ascertainment window could permit reverse causation; outcomes "
            "occurring on or before the index date were excluded but the possibility of "
            "outcome precursors driving exposure cannot be fully excluded"
        )
    if any(f["section"] == "Prevalent-user" and f["severity"] in {"amber", "red"} for f in flags):
        pieces.append(
            "the analysis includes prevalent users in addition to incident users, which "
            "may attenuate effect estimates due to depletion of susceptibles"
        )
    if any(f["section"] == "Look-back" and f["severity"] in {"amber", "red"} for f in flags):
        pieces.append(
            f"the look-back window of {state.get('q4a', 0)} days may not capture all "
            "relevant historical comorbidities and exposures"
        )
    if any(f["section"] == "Outcome detection" and f["severity"] in {"amber", "red"} for f in flags):
        pieces.append(
            "the two cohorts may have differential healthcare utilization, raising the "
            "possibility of detection or surveillance bias"
        )
    if any(f["section"] == "Negative controls" and f["severity"] == "green" for f in flags):
        pieces.append(
            "pre-specified negative-control outcomes were used to empirically assess "
            "residual confounding and detection bias"
        )

    if not pieces:
        return (
            "We considered immortal-time bias, reverse causation, prevalent-user bias, "
            "look-back adequacy, and differential outcome ascertainment; no critical "
            "issues were identified."
        )
    return "Several potential sources of bias were considered: " + "; ".join(pieces) + "."


limitations = build_limitations_paragraph(flags, state)

st.markdown("---")
st.subheader("Limitations-section text")
st.markdown(f"> {limitations}")

st.download_button(
    "Download limitations paragraph (Markdown)",
    data=limitations.encode("utf-8"),
    file_name=_stamp_filename("limitations_paragraph", "md"),
    mime="text/markdown",
)

# Combined download with full diagnostic
def build_full_report(flags: List[Dict], limitations: str, ctx) -> str:
    lines = [
        "# Bias Check Diagnostic Report",
        "",
        f"_Generated by the TriNetX Publication Toolkit v2 on "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M')}_",
        "",
        f"**Study context.** {ctx.cohort_1_label} vs {ctx.cohort_2_label}; "
        f"treated/exposed = Cohort {ctx.treated_cohort}; outcome polarity = {ctx.outcome_polarity}.",
        "",
        "## Findings",
        "",
        "| Severity | Section | Finding | Recommendation |",
        "|---|---|---|---|",
    ]
    for f in flags:
        lines.append(
            f"| {f['severity'].upper()} | {f['section']} | {f['message']} | {f['recommendation'] or '—'} |"
        )
    lines.extend(["", "## Limitations-section text", "", limitations, ""])
    return "\n".join(lines)


report_md = build_full_report(flags, limitations, ctx)
st.download_button(
    "Download full diagnostic report (Markdown)",
    data=report_md.encode("utf-8"),
    file_name=_stamp_filename("bias_check_report", "md"),
    mime="text/markdown",
)

render_check_callout(
    "Bias diagnostics should be performed before the analysis is finalized. If a critical "
    "flag was raised, return to the Pre-Analysis Plan tool and revise the design before "
    "continuing."
)

render_methods_text(
    """We assessed risk of immortal-time bias, reverse causation, prevalent-user
bias, look-back adequacy, and differential outcome ascertainment using the Bias Check
questionnaire in the TriNetX Publication Toolkit v2. Identified risks and their
mitigations are reported in the Limitations section.""",
    title="Methods text for your manuscript",
)

render_reproducibility_footer("Bias Check")
