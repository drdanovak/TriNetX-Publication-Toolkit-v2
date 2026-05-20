"""
parsers.py — Unified TriNetX export parsers.

In v1, each tool had its own parser. This made the toolkit fragile: a layout
change in TriNetX would break some tools and not others, and the same file
read by two tools could yield slightly different numbers. v2 consolidates
parsing into three canonical parsers, one per export type:

- parse_baseline_csv   ->  BaselineExport
- parse_moa_csv        ->  MOAExport
- parse_km_csv         ->  KMExport

Plus a dispatcher `detect_and_parse` that classifies an arbitrary CSV and
returns the appropriate dataclass.

Every parser returns a strongly typed result with:
- The cleaned DataFrame (or DataFrames, for multi-section files)
- The cohort names as TriNetX wrote them
- A short snippet of the source (`source_excerpt`) suitable for the
  "verify against source" widget
- A `source_provenance` dict explaining which sections were parsed and
  which rows were used.

This consolidation is what makes the v2 toolkit a coherent system rather
than ten independent scripts.
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Export-type identification
# ---------------------------------------------------------------------------

EXPORT_BASELINE = "baseline"
EXPORT_MOA = "moa"
EXPORT_KM = "km"
EXPORT_UNKNOWN = "unknown"

SECTION_NAMES = {
    "Cohort Statistics",
    "Risk Difference",
    "Risk Ratio",
    "Odds Ratio",
    "Hazard Ratio",
    "Kaplan-Meier",
    "Log-Rank Test",
    "Proportional Hazard Assumption",
    "Proportionality",
    "Graph Data Table",
    "Survival Data Table",
}

BASELINE_KEY_HEADERS = {"Characteristic ID", "Characteristic Name", "Before: Standardized Mean Difference"}
KM_KEY_HEADERS = {"Time (Days)", "Cohort 1: Survival Probability"}
MOA_KEY_SECTIONS = {"Cohort Statistics", "Risk Difference"}


# ---------------------------------------------------------------------------
# Return dataclasses
# ---------------------------------------------------------------------------

@dataclass
class BaselineExport:
    df: pd.DataFrame
    cohort_1_label: str
    cohort_2_label: str
    has_smd_columns: bool
    source_excerpt: str
    source_provenance: Dict[str, Any] = field(default_factory=dict)
    export_type: str = EXPORT_BASELINE


@dataclass
class MOAExport:
    cohort_statistics: pd.DataFrame
    risk_difference: Optional[pd.DataFrame]
    risk_ratio: Optional[pd.DataFrame]
    odds_ratio: Optional[pd.DataFrame]
    hazard_ratio: Optional[pd.DataFrame]
    cohort_1_label: str
    cohort_2_label: str
    cohort_1_n: Optional[int]
    cohort_2_n: Optional[int]
    cohort_1_events: Optional[int]
    cohort_2_events: Optional[int]
    cohort_1_risk: Optional[float]
    cohort_2_risk: Optional[float]
    primary_p_value: Optional[float]
    primary_p_source: str
    risk_ratio_value: Optional[float]
    risk_ratio_ci: Tuple[Optional[float], Optional[float]]
    odds_ratio_value: Optional[float]
    odds_ratio_ci: Tuple[Optional[float], Optional[float]]
    source_excerpt: str
    source_provenance: Dict[str, Any] = field(default_factory=dict)
    export_type: str = EXPORT_MOA


@dataclass
class KMExport:
    df: pd.DataFrame
    cohort_1_label: str
    cohort_2_label: str
    cohort_1_n: Optional[int]
    cohort_2_n: Optional[int]
    hazard_ratio: Optional[float]
    hazard_ratio_ci: Tuple[Optional[float], Optional[float]]
    log_rank_p: Optional[float]
    ph_assumption_p: Optional[float]
    max_days: Optional[int]
    source_excerpt: str
    source_provenance: Dict[str, Any] = field(default_factory=dict)
    export_type: str = EXPORT_KM


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def _decode(raw: Union[bytes, str]) -> str:
    if isinstance(raw, str):
        return raw
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _read_uploaded(uploaded) -> str:
    if hasattr(uploaded, "read"):
        try:
            uploaded.seek(0)
        except Exception:
            pass
        return _decode(uploaded.read())
    if isinstance(uploaded, (bytes, bytearray)):
        return _decode(bytes(uploaded))
    return str(uploaded)


def _csv_rows(text: str) -> List[List[str]]:
    rows: List[List[str]] = []
    for line in text.splitlines():
        try:
            parsed = next(csv.reader([line]))
        except StopIteration:
            parsed = []
        rows.append([cell.strip().replace("\ufeff", "") for cell in parsed])
    return rows


def _find_section(rows: List[List[str]], section_name: str) -> Tuple[int, List[List[str]]]:
    """Return (start_index, section_rows). start_index is -1 if not found.

    A section is identified by a row whose only non-empty cell equals
    `section_name`. The section's rows continue until another such
    single-cell section header is encountered, or the file ends.
    """
    def _is_section_header(row: List[str]) -> Optional[str]:
        nonempty = [c.strip() for c in row if c.strip()]
        if len(nonempty) == 1 and nonempty[0] in SECTION_NAMES:
            return nonempty[0]
        return None

    for i, row in enumerate(rows):
        if _is_section_header(row) == section_name:
            collected: List[List[str]] = []
            j = i + 1
            while j < len(rows):
                if _is_section_header(rows[j]) is not None:
                    break
                collected.append(rows[j])
                j += 1
            return i, collected
    return -1, []


def _rows_to_df(section_rows: List[List[str]]) -> pd.DataFrame:
    """Convert a section's rows into a DataFrame, dropping leading blank rows."""
    cleaned = [r for r in section_rows if any(cell.strip() for cell in r)]
    if not cleaned:
        return pd.DataFrame()
    width = max(len(r) for r in cleaned)
    padded = [r + [""] * (width - len(r)) for r in cleaned]
    header = padded[0]
    body = padded[1:]
    body = [r for r in body if any(cell.strip() for cell in r)]
    df = pd.DataFrame(body, columns=header)
    df.columns = [str(c).strip() for c in df.columns]
    return df


def _safe_float(x) -> Optional[float]:
    if x is None or (isinstance(x, str) and x.strip() in {"", "—", "N/A", "NA"}):
        return None
    try:
        return float(str(x).replace(",", "").replace("%", "").strip())
    except (TypeError, ValueError):
        return None


def _safe_int(x) -> Optional[int]:
    f = _safe_float(x)
    if f is None:
        return None
    return int(f)


def _find_col(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    """Find a column matching one of the candidate names.

    Strategy (in order):
    1. Exact case-insensitive match
    2. Whole-word case-insensitive match (so 'p' matches 'p' but not 'Patients')
    3. Substring match
    """
    if df is None or df.empty:
        return None
    lower = {c.lower(): c for c in df.columns}

    # 1. Exact match
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]

    # 2. Whole-word match
    for cand in candidates:
        pattern = re.compile(r"\b" + re.escape(cand) + r"\b", re.IGNORECASE)
        for c in df.columns:
            if pattern.search(c):
                return c

    # 3. Substring match (only for multi-character candidates)
    for cand in candidates:
        if len(cand) < 3:
            continue
        for c in df.columns:
            if cand.lower() in c.lower():
                return c
    return None


# ---------------------------------------------------------------------------
# Export-type detection
# ---------------------------------------------------------------------------

def detect_export_type(text: str) -> str:
    """Classify a TriNetX export as baseline, moa, km, or unknown."""
    rows = _csv_rows(text)
    flat = "\n".join(",".join(r) for r in rows[:100])  # peek at the top

    # KM tables have either a 'Time (Days)' column or Kaplan-Meier markers
    # in the title plus Log-Rank or Hazard Ratio sections.
    is_km_title = bool(re.search(r"kaplan[-\s]?meier", flat, re.IGNORECASE))
    has_survival_curve = "Time (Days)" in flat and "Survival Probability" in flat
    has_km_sections = ("Log-Rank Test" in flat or "Median Survival" in flat) and "Hazard Ratio" in flat

    if has_survival_curve or (is_km_title and has_km_sections):
        return EXPORT_KM

    # Baseline tables have Characteristic ID + SMD columns.
    if "Characteristic ID" in flat and "Standardized Mean Difference" in flat:
        return EXPORT_BASELINE

    # MOA tables have Cohort Statistics + Risk Difference sections.
    if "Cohort Statistics" in flat and ("Risk Difference" in flat or "Risk Ratio" in flat):
        return EXPORT_MOA

    return EXPORT_UNKNOWN


# ---------------------------------------------------------------------------
# Baseline parser
# ---------------------------------------------------------------------------

def parse_baseline_csv(uploaded) -> BaselineExport:
    text = _read_uploaded(uploaded)
    rows = _csv_rows(text)

    # Baseline tables are flat: a header row followed by data rows.
    # Some exports prepend a few metadata lines; find the header row.
    header_idx = None
    for i, row in enumerate(rows):
        if any("Characteristic ID" in c for c in row):
            header_idx = i
            break
    if header_idx is None:
        raise ValueError(
            "Could not find the 'Characteristic ID' header in the baseline file. "
            "Make sure this is a TriNetX Baseline Patient Characteristics export."
        )

    df = pd.read_csv(io.StringIO(text), skiprows=header_idx)
    df.columns = [str(c).strip() for c in df.columns]

    # Try to identify cohort names from the column labels.
    cohort_1_label = "Cohort 1"
    cohort_2_label = "Cohort 2"
    for c in df.columns:
        m = re.match(r"Cohort 1\s*Before:\s*(.+)", c) or re.match(r"Cohort 1\s*:", c)
        if m:
            cohort_1_label = "Cohort 1"
        m2 = re.match(r"Cohort 2\s*Before:\s*(.+)", c) or re.match(r"Cohort 2\s*:", c)
        if m2:
            cohort_2_label = "Cohort 2"

    has_smd = (
        "Before: Standardized Mean Difference" in df.columns
        and "After: Standardized Mean Difference" in df.columns
    )

    # Source excerpt: the first 6 columns of the first 5 rows
    excerpt_cols = list(df.columns[:6])
    excerpt = df.head(5)[excerpt_cols].to_string(index=False)

    return BaselineExport(
        df=df,
        cohort_1_label=cohort_1_label,
        cohort_2_label=cohort_2_label,
        has_smd_columns=has_smd,
        source_excerpt=excerpt,
        source_provenance={
            "header_row_index": header_idx,
            "n_rows_after_header": len(df),
            "smd_columns_present": has_smd,
        },
    )


# ---------------------------------------------------------------------------
# MOA parser
# ---------------------------------------------------------------------------

def parse_moa_csv(uploaded) -> MOAExport:
    text = _read_uploaded(uploaded)
    rows = _csv_rows(text)

    sections: Dict[str, pd.DataFrame] = {}
    section_starts: Dict[str, int] = {}
    for name in [
        "Cohort Statistics",
        "Risk Difference",
        "Risk Ratio",
        "Odds Ratio",
        "Hazard Ratio",
    ]:
        idx, body = _find_section(rows, name)
        if idx >= 0:
            sections[name] = _rows_to_df(body)
            section_starts[name] = idx

    if "Cohort Statistics" not in sections:
        raise ValueError(
            "Could not find the 'Cohort Statistics' section. This does not look like a "
            "TriNetX Measures of Association export."
        )

    cs = sections["Cohort Statistics"]
    name_col = _find_col(cs, ["Cohort Name", "Name", "Cohort"])
    n_col = _find_col(cs, ["Patients in Cohort", "Patients", "N"])
    events_col = _find_col(cs, ["Patients with Outcome", "Events", "Outcome"])
    risk_col = _find_col(cs, ["Risk", "Risk %", "Patients with Outcome %"])

    def _row(idx: int) -> Dict[str, Any]:
        if idx >= len(cs):
            return {}
        return cs.iloc[idx].to_dict()

    r1, r2 = _row(0), _row(1)

    cohort_1_label = str(r1.get(name_col, "Cohort 1")).strip() if name_col else "Cohort 1"
    cohort_2_label = str(r2.get(name_col, "Cohort 2")).strip() if name_col else "Cohort 2"

    c1_n = _safe_int(r1.get(n_col)) if n_col else None
    c2_n = _safe_int(r2.get(n_col)) if n_col else None
    c1_events = _safe_int(r1.get(events_col)) if events_col else None
    c2_events = _safe_int(r2.get(events_col)) if events_col else None
    c1_risk = _safe_float(r1.get(risk_col)) if risk_col else None
    c2_risk = _safe_float(r2.get(risk_col)) if risk_col else None

    # Risks are sometimes returned as percent (e.g., 1.17); normalize to proportion if >1.
    def _to_proportion(v: Optional[float]) -> Optional[float]:
        if v is None:
            return None
        if v > 1.0:
            return v / 100.0
        return v

    c1_risk = _to_proportion(c1_risk)
    c2_risk = _to_proportion(c2_risk)

    def _extract_estimate_and_p(section_df: Optional[pd.DataFrame]) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float]]:
        """Return (estimate, lower_ci, upper_ci, p_value) for a ratio section."""
        if section_df is None or section_df.empty:
            return None, None, None, None
        est_col = _find_col(section_df, ["Risk Ratio", "Odds Ratio", "Hazard Ratio", "Estimate", "Value"])
        lo_col = _find_col(section_df, ["95 % CI Lower", "95% CI Lower", "Lower 95% CI", "Lower 95 % CI", "Lower CI", "Lower"])
        hi_col = _find_col(section_df, ["95 % CI Upper", "95% CI Upper", "Upper 95% CI", "Upper 95 % CI", "Upper CI", "Upper"])
        p_col = _find_col(section_df, ["p-Value", "p Value", "p-value", "P", "p"])

        est = _safe_float(section_df.iloc[0].get(est_col)) if est_col else None
        lo = _safe_float(section_df.iloc[0].get(lo_col)) if lo_col else None
        hi = _safe_float(section_df.iloc[0].get(hi_col)) if hi_col else None
        p = _safe_float(section_df.iloc[0].get(p_col)) if p_col else None
        return est, lo, hi, p

    rr, rr_lo, rr_hi, rr_p = _extract_estimate_and_p(sections.get("Risk Ratio"))
    or_, or_lo, or_hi, or_p = _extract_estimate_and_p(sections.get("Odds Ratio"))
    _hr, hr_lo, hr_hi, hr_p = _extract_estimate_and_p(sections.get("Hazard Ratio"))

    # Per TriNetX convention, the test-statistic p-value is in the Risk Difference section.
    rd_section = sections.get("Risk Difference")
    rd_p = None
    if rd_section is not None and not rd_section.empty:
        p_col = _find_col(rd_section, ["p-Value", "p Value", "p-value", "p"])
        if p_col:
            rd_p = _safe_float(rd_section.iloc[0].get(p_col))

    primary_p_value = rd_p
    primary_p_source = "Risk Difference"
    if primary_p_value is None and rr_p is not None:
        primary_p_value = rr_p
        primary_p_source = "Risk Ratio"
    elif primary_p_value is None and or_p is not None:
        primary_p_value = or_p
        primary_p_source = "Odds Ratio"

    excerpt = cs.head(2).to_string(index=False)

    return MOAExport(
        cohort_statistics=cs,
        risk_difference=rd_section,
        risk_ratio=sections.get("Risk Ratio"),
        odds_ratio=sections.get("Odds Ratio"),
        hazard_ratio=sections.get("Hazard Ratio"),
        cohort_1_label=cohort_1_label,
        cohort_2_label=cohort_2_label,
        cohort_1_n=c1_n,
        cohort_2_n=c2_n,
        cohort_1_events=c1_events,
        cohort_2_events=c2_events,
        cohort_1_risk=c1_risk,
        cohort_2_risk=c2_risk,
        primary_p_value=primary_p_value,
        primary_p_source=primary_p_source,
        risk_ratio_value=rr,
        risk_ratio_ci=(rr_lo, rr_hi),
        odds_ratio_value=or_,
        odds_ratio_ci=(or_lo, or_hi),
        source_excerpt=excerpt,
        source_provenance={
            "sections_found": list(sections.keys()),
            "section_starts": section_starts,
            "primary_p_source": primary_p_source,
        },
    )


# ---------------------------------------------------------------------------
# KM parser
# ---------------------------------------------------------------------------

def parse_km_csv(uploaded) -> KMExport:
    text = _read_uploaded(uploaded)
    rows = _csv_rows(text)

    # KM exports usually contain auxiliary sections (Cohort Statistics,
    # Hazard Ratio, Log-Rank Test, Proportional Hazard Assumption / Proportionality)
    # plus, sometimes, a survival time series. Find the survival header row.
    header_idx = None
    for i, row in enumerate(rows):
        joined = ",".join(row)
        if "Time (Days)" in joined and "Survival Probability" in joined:
            header_idx = i
            break

    df = pd.DataFrame()
    if header_idx is not None:
        survival_rows: List[List[str]] = []
        j = header_idx
        while j < len(rows):
            r = rows[j]
            if r == [] or all(c.strip() == "" for c in r):
                if survival_rows:
                    break
                j += 1
                continue
            if any(c.strip() in SECTION_NAMES for c in r) and survival_rows:
                break
            survival_rows.append(r)
            j += 1

        df = _rows_to_df(survival_rows)
        for c in df.columns:
            if c != "":
                df[c] = pd.to_numeric(df[c], errors="coerce")
        if "Time (Days)" in df.columns:
            df = df.dropna(subset=["Time (Days)"]).sort_values("Time (Days)").reset_index(drop=True)
            fill_cols = [c for c in df.columns if "Survival Probability" in c]
            if fill_cols:
                df[fill_cols] = df[fill_cols].ffill()

    # Auxiliary sections
    _, cs_rows = _find_section(rows, "Cohort Statistics")
    cs_df = _rows_to_df(cs_rows) if cs_rows else pd.DataFrame()

    _, hr_rows = _find_section(rows, "Hazard Ratio")
    hr_df = _rows_to_df(hr_rows) if hr_rows else pd.DataFrame()

    _, lr_rows = _find_section(rows, "Log-Rank Test")
    lr_df = _rows_to_df(lr_rows) if lr_rows else pd.DataFrame()

    _, ph_rows = _find_section(rows, "Proportional Hazard Assumption")
    if not ph_rows:
        _, ph_rows = _find_section(rows, "Proportionality")
    ph_df = _rows_to_df(ph_rows) if ph_rows else pd.DataFrame()

    # Extract HR, log-rank p, PH p
    def _first(df_: pd.DataFrame, cands: List[str]) -> Optional[float]:
        if df_.empty:
            return None
        col = _find_col(df_, cands)
        if col is None:
            return None
        return _safe_float(df_.iloc[0].get(col))

    hr_value = _first(hr_df, ["Hazard Ratio", "Estimate", "Value"])
    hr_lo = _first(hr_df, ["95 % CI Lower", "95% CI Lower", "Lower 95% CI", "Lower 95 % CI", "Lower CI"])
    hr_hi = _first(hr_df, ["95 % CI Upper", "95% CI Upper", "Upper 95% CI", "Upper 95 % CI", "Upper CI"])

    log_rank_p = _first(lr_df, ["p-Value", "p Value", "p-value", "p"])
    ph_assumption_p = _first(ph_df, ["p-Value", "p Value", "p-value", "p"])

    # Cohort labels and N
    cohort_1_label = "Cohort 1"
    cohort_2_label = "Cohort 2"
    c1_n = c2_n = None
    if not cs_df.empty:
        name_col = _find_col(cs_df, ["Cohort Name", "Name"])
        n_col = _find_col(cs_df, ["Patients in Cohort", "Patients", "N"])
        if name_col and len(cs_df) >= 2:
            cohort_1_label = str(cs_df.iloc[0][name_col]).strip() or "Cohort 1"
            cohort_2_label = str(cs_df.iloc[1][name_col]).strip() or "Cohort 2"
        if n_col and len(cs_df) >= 2:
            c1_n = _safe_int(cs_df.iloc[0][n_col])
            c2_n = _safe_int(cs_df.iloc[1][n_col])

    max_days = int(df["Time (Days)"].max()) if not df.empty else None

    excerpt = df.head(8).to_string(index=False) if not df.empty else ""

    return KMExport(
        df=df,
        cohort_1_label=cohort_1_label,
        cohort_2_label=cohort_2_label,
        cohort_1_n=c1_n,
        cohort_2_n=c2_n,
        hazard_ratio=hr_value,
        hazard_ratio_ci=(hr_lo, hr_hi),
        log_rank_p=log_rank_p,
        ph_assumption_p=ph_assumption_p,
        max_days=max_days,
        source_excerpt=excerpt,
        source_provenance={
            "n_time_points": len(df),
            "max_days": max_days,
            "has_ph_section": not ph_df.empty,
            "has_logrank_section": not lr_df.empty,
            "has_hr_section": not hr_df.empty,
        },
    )


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

def detect_and_parse(uploaded):
    """Detect the export type and return the matching dataclass."""
    text = _read_uploaded(uploaded)
    etype = detect_export_type(text)
    if etype == EXPORT_BASELINE:
        return parse_baseline_csv(io.StringIO(text))
    if etype == EXPORT_MOA:
        return parse_moa_csv(io.StringIO(text))
    if etype == EXPORT_KM:
        return parse_km_csv(io.StringIO(text))
    raise ValueError(
        "Could not classify this file as a Baseline, Measures of Association, or "
        "Kaplan-Meier export. The expected section headers were not found."
    )
