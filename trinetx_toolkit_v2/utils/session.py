"""
session.py — Unified study context for the TriNetX Publication Toolkit.

A single `StudyContext` lives in `st.session_state["study"]` and is read and
written by every tool. The context holds:

- Cohort labels and direction (which cohort is treated/exposed)
- Outcome polarity (adverse vs beneficial)
- Statistical settings (alpha, target power, multiple-comparisons family)
- Number formatting (percent decimals, ratio decimals, p-value style)
- Visual defaults (palette, font family, figure-size preset)
- The uploaded files themselves, classified by detected type

This eliminates the v1 failure mode where a user uploaded the same TriNetX
CSV to multiple tools with inconsistent cohort direction or labels.

Every tool MUST do three things at the top of the page:
1. Call `ensure_context()` to create or read the context.
2. Render `render_context_banner()` so the user can see and edit cohort
   labels / direction without leaving the page.
3. Use `register_upload()` when a file is uploaded so other tools see it.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any

import streamlit as st


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_PALETTE = "Classic TriNetX"
DEFAULT_FONT = "Arial"
DEFAULT_FIGURE_PRESET = "Journal column (single)"
DEFAULT_ALPHA = 0.05
DEFAULT_POWER = 0.80
DEFAULT_PCT_DECIMALS = 2
DEFAULT_RATIO_DECIMALS = 2
DEFAULT_SMD_DECIMALS = 3
DEFAULT_P_STYLE = "apa"


# ---------------------------------------------------------------------------
# Context object
# ---------------------------------------------------------------------------

@dataclass
class StudyContext:
    """Single source of truth for everything that varies per study."""

    # Cohort labels
    cohort_1_label: str = "Cohort 1"
    cohort_2_label: str = "Cohort 2"

    # Which cohort is treated/exposed: "1" or "2"
    treated_cohort: str = "1"

    # Outcome polarity: "adverse" (lower risk is better in treated) or "beneficial"
    outcome_polarity: str = "adverse"

    # Statistical settings
    alpha: float = DEFAULT_ALPHA
    power_target: float = DEFAULT_POWER
    two_sided: bool = True
    multiple_comparison_family: str = "All primary outcomes"

    # Number formatting
    pct_decimals: int = DEFAULT_PCT_DECIMALS
    ratio_decimals: int = DEFAULT_RATIO_DECIMALS
    smd_decimals: int = DEFAULT_SMD_DECIMALS
    p_style: str = DEFAULT_P_STYLE

    # Visual defaults
    palette: str = DEFAULT_PALETTE
    font_family: str = DEFAULT_FONT
    figure_preset: str = DEFAULT_FIGURE_PRESET

    # Study identification (used in exports)
    study_title: str = ""
    investigator: str = ""

    # Uploads: dict mapping file_id -> {"name", "bytes", "type", "uploaded_at"}
    uploads: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # ----- Derived helpers -----------------------------------------------

    @property
    def treated_label(self) -> str:
        return self.cohort_1_label if self.treated_cohort == "1" else self.cohort_2_label

    @property
    def control_label(self) -> str:
        return self.cohort_2_label if self.treated_cohort == "1" else self.cohort_1_label

    @property
    def outcome_is_adverse(self) -> bool:
        return self.outcome_polarity == "adverse"

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["uploads"] = {
            k: {kk: vv for kk, vv in v.items() if kk != "bytes"}
            for k, v in self.uploads.items()
        }
        return d


# ---------------------------------------------------------------------------
# Session-state access
# ---------------------------------------------------------------------------

CONTEXT_KEY = "study"


def ensure_context() -> StudyContext:
    """Create a StudyContext if missing; return the current one."""
    if CONTEXT_KEY not in st.session_state:
        st.session_state[CONTEXT_KEY] = StudyContext()
    return st.session_state[CONTEXT_KEY]


def get_context() -> StudyContext:
    return ensure_context()


def update_context(**kwargs) -> StudyContext:
    """Update one or more fields on the live context."""
    ctx = ensure_context()
    for k, v in kwargs.items():
        if hasattr(ctx, k):
            setattr(ctx, k, v)
    return ctx


# ---------------------------------------------------------------------------
# Upload registry
# ---------------------------------------------------------------------------

def register_upload(file_id: str, name: str, raw_bytes: bytes, detected_type: str) -> None:
    """Make an uploaded file available to other tools in this session."""
    ctx = ensure_context()
    ctx.uploads[file_id] = {
        "name": name,
        "bytes": raw_bytes,
        "type": detected_type,
        "uploaded_at": datetime.utcnow().isoformat(),
    }


def list_uploads(of_type: Optional[str] = None) -> List[Dict[str, Any]]:
    ctx = ensure_context()
    items = []
    for fid, meta in ctx.uploads.items():
        if of_type is None or meta.get("type") == of_type:
            entry = dict(meta)
            entry["file_id"] = fid
            items.append(entry)
    return items


def remove_upload(file_id: str) -> None:
    ctx = ensure_context()
    ctx.uploads.pop(file_id, None)


def clear_uploads() -> None:
    ctx = ensure_context()
    ctx.uploads.clear()


def upload_as_bytesio(file_id: str) -> Optional[io.BytesIO]:
    """Return a BytesIO that a parser can read like a file upload."""
    ctx = ensure_context()
    meta = ctx.uploads.get(file_id)
    if meta is None:
        return None
    buf = io.BytesIO(meta["bytes"])
    buf.name = meta["name"]
    return buf


# ---------------------------------------------------------------------------
# UI: the context banner shown at the top of every tool page
# ---------------------------------------------------------------------------

def render_context_banner(show_advanced: bool = False) -> StudyContext:
    """
    Render the study-context banner used at the top of every tool.

    Returns the live StudyContext so the calling page can use values from it.
    """
    ctx = ensure_context()

    with st.expander(
        "Study context (cohort labels, direction, outcome polarity, alpha)",
        expanded=False,
    ):
        st.caption(
            "These settings are shared across every tool in this session. Edit them once "
            "and they will propagate to all tables, figures, and downloads."
        )

        col1, col2 = st.columns(2)
        with col1:
            ctx.cohort_1_label = st.text_input(
                "Cohort 1 label",
                value=ctx.cohort_1_label,
                key="ctx_cohort1",
                help="The first cohort as defined in the TriNetX analysis.",
            )
            ctx.cohort_2_label = st.text_input(
                "Cohort 2 label",
                value=ctx.cohort_2_label,
                key="ctx_cohort2",
            )

        with col2:
            ctx.treated_cohort = st.radio(
                "Which cohort is the treated/exposed group?",
                options=["1", "2"],
                format_func=lambda x: f"{ctx.cohort_1_label} (Cohort 1)" if x == "1" else f"{ctx.cohort_2_label} (Cohort 2)",
                index=0 if ctx.treated_cohort == "1" else 1,
                key="ctx_direction",
                help=(
                    "Affects sign of risk differences, direction of NNT/NNH, "
                    "and reference category in ratios."
                ),
            )
            ctx.outcome_polarity = st.radio(
                "Outcome polarity",
                options=["adverse", "beneficial"],
                format_func=lambda x: (
                    "Adverse (lower risk in treated is better)"
                    if x == "adverse"
                    else "Beneficial (higher risk in treated is better)"
                ),
                index=0 if ctx.outcome_polarity == "adverse" else 1,
                key="ctx_polarity",
            )

        if show_advanced:
            st.markdown("---")
            st.caption("Statistical and formatting settings")
            c1, c2, c3 = st.columns(3)
            with c1:
                ctx.alpha = st.number_input(
                    "Alpha", min_value=0.0001, max_value=0.5, value=float(ctx.alpha),
                    step=0.005, format="%.4f", key="ctx_alpha",
                )
                ctx.power_target = st.number_input(
                    "Target power", min_value=0.01, max_value=0.99, value=float(ctx.power_target),
                    step=0.01, key="ctx_power",
                )
            with c2:
                ctx.pct_decimals = st.number_input(
                    "Percent decimals", min_value=0, max_value=4, value=int(ctx.pct_decimals),
                    key="ctx_pctdec",
                )
                ctx.ratio_decimals = st.number_input(
                    "Ratio decimals", min_value=1, max_value=4, value=int(ctx.ratio_decimals),
                    key="ctx_ratiodec",
                )
            with c3:
                ctx.smd_decimals = st.number_input(
                    "SMD decimals", min_value=2, max_value=4, value=int(ctx.smd_decimals),
                    key="ctx_smddec",
                )
                ctx.p_style = st.selectbox(
                    "P-value style",
                    options=["apa", "decimal", "scientific"],
                    index=["apa", "decimal", "scientific"].index(ctx.p_style),
                    key="ctx_pstyle",
                )

    return ctx


def render_source_check(label: str, content) -> None:
    """
    Render the 'verify against source' widget used at the bottom of every
    tool that parses TriNetX exports.
    """
    with st.expander(f"Verify against source: {label}", expanded=False):
        st.caption(
            "This shows the section of the TriNetX export the tool actually read from. "
            "Compare against the original CSV to confirm the right cells were parsed."
        )
        if hasattr(content, "to_html"):
            st.dataframe(content, use_container_width=True, hide_index=True)
        else:
            st.code(str(content))


def render_methods_text(text: str, title: str = "Methods text for your manuscript") -> None:
    """Render a copy-friendly Methods-section snippet at the foot of a tool."""
    with st.expander(title, expanded=False):
        st.caption(
            "A ready-to-paste sentence or paragraph reflecting what this tool computed. "
            "Edit to fit your manuscript voice."
        )
        st.markdown(text)
        st.download_button(
            label="Download methods text (Markdown)",
            data=text.encode("utf-8"),
            file_name="methods_text.md",
            mime="text/markdown",
            use_container_width=False,
        )


def render_check_callout(text: str) -> None:
    """Render the 'check before submission' callout."""
    st.info(f"**Check before submission:** {text}")
