"""
formatters.py — Shared number formatting for the TriNetX Publication Toolkit.

All numerical output in the toolkit flows through these helpers so that the
manuscript text reads consistently across tables, figures, and downloads.

Conventions:
- P-values use APA style by default: leading zero dropped, "<.001" for very
  small values, three decimal places otherwise.
- Percentages, ratios, and SMDs accept a `decimals` argument that defaults
  to the value held in the session-level number-formatting context.
- Every function returns a string and gracefully handles None, NaN, and
  non-finite values by returning the user-supplied `na` token.
"""

from __future__ import annotations

import math
from typing import Optional, Union

import numpy as np
import pandas as pd

Number = Optional[Union[float, int]]

# ---------------------------------------------------------------------------
# Safe coercion
# ---------------------------------------------------------------------------

def _is_missing(x) -> bool:
    if x is None:
        return True
    try:
        if isinstance(x, str):
            return x.strip() == ""
        if pd.isna(x):
            return True
        return not math.isfinite(float(x))
    except (TypeError, ValueError):
        return True


def safe_float(x, default: Optional[float] = None) -> Optional[float]:
    """Coerce to float, returning `default` when the value is unusable."""
    if _is_missing(x):
        return default
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def safe_int(x, default: Optional[int] = None) -> Optional[int]:
    if _is_missing(x):
        return default
    try:
        return int(float(x))
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# Core formatters
# ---------------------------------------------------------------------------

def fmt_p(value, style: str = "apa", na: str = "") -> str:
    """
    Format a p-value.

    style="apa" (default): drop leading zero, use "<.001" for small values.
        Examples: 0.00012 -> "<.001", 0.034 -> ".034", 0.21 -> ".21"
    style="decimal": fixed three-decimal format with leading zero.
        Examples: 0.00012 -> "<0.001", 0.034 -> "0.034", 0.21 -> "0.210"
    style="scientific": "%.3g" format. 0.00012 -> "0.00012", 1.2e-7 -> "1.2e-07"
    """
    v = safe_float(value)
    if v is None:
        return na
    if v < 0:
        return na
    if style == "apa":
        if v < 0.001:
            return "<.001"
        # APA: 3 decimal places, leading zero dropped for values < 1
        formatted = f"{v:.3f}"
        if v < 1:
            formatted = formatted.lstrip("0")
        return formatted
    if style == "decimal":
        if v < 0.001:
            return "<0.001"
        return f"{v:.3f}"
    if style == "scientific":
        return f"{v:.3g}"
    return f"{v:.3f}"


def fmt_pct(value, decimals: int = 2, na: str = "") -> str:
    """Format a proportion (0-1) as a percent string."""
    v = safe_float(value)
    if v is None:
        return na
    return f"{100 * v:.{decimals}f}%"


def fmt_pct_already(value, decimals: int = 2, na: str = "") -> str:
    """Format a value that is already expressed in percent units."""
    v = safe_float(value)
    if v is None:
        return na
    return f"{v:.{decimals}f}%"


def fmt_ratio(value, decimals: int = 2, na: str = "") -> str:
    """Format a risk ratio, odds ratio, or hazard ratio."""
    v = safe_float(value)
    if v is None:
        return na
    return f"{v:.{decimals}f}"


def fmt_ci(lower, upper, decimals: int = 2, sep: str = " to ", na: str = "") -> str:
    """Format a confidence interval as 'lower to upper'."""
    lo = safe_float(lower)
    hi = safe_float(upper)
    if lo is None or hi is None:
        return na
    return f"{lo:.{decimals}f}{sep}{hi:.{decimals}f}"


def fmt_ratio_with_ci(point, lower, upper, decimals: int = 2, na: str = "") -> str:
    """Format 'estimate (lower to upper)'."""
    p = fmt_ratio(point, decimals=decimals, na=na)
    ci = fmt_ci(lower, upper, decimals=decimals, na=na)
    if not p:
        return na
    if not ci:
        return p
    return f"{p} ({ci})"


def fmt_smd(value, decimals: int = 3, na: str = "") -> str:
    """Format a standardized mean difference, preserving sign."""
    v = safe_float(value)
    if v is None:
        return na
    return f"{v:+.{decimals}f}".replace("+0.", "0.").replace("+", "")  # no plus sign


def fmt_count(value, na: str = "") -> str:
    """Format an integer count with thousands separator."""
    v = safe_int(value)
    if v is None:
        return na
    return f"{v:,}"


def fmt_count_pct(count, pct, count_decimals: int = 0, pct_decimals: int = 2, na: str = "") -> str:
    """Format 'N (pp.pp%)' commonly used in Table 1 cells."""
    c = safe_int(count)
    p = safe_float(pct)
    if c is None and p is None:
        return na
    c_str = f"{c:,}" if c is not None else "—"
    p_str = f"{p:.{pct_decimals}f}%" if p is not None else "—"
    return f"{c_str} ({p_str})"


def fmt_mean_sd(mean, sd, decimals: int = 2, na: str = "") -> str:
    """Format 'mean (SD)' for continuous Table 1 rows."""
    m = safe_float(mean)
    s = safe_float(sd)
    if m is None:
        return na
    if s is None:
        return f"{m:.{decimals}f}"
    return f"{m:.{decimals}f} ({s:.{decimals}f})"


# ---------------------------------------------------------------------------
# Significance and direction helpers
# ---------------------------------------------------------------------------

def is_significant(p_value, alpha: float = 0.05) -> Optional[bool]:
    v = safe_float(p_value)
    if v is None:
        return None
    return v <= alpha


def significance_marker(p_value, alpha: float = 0.05) -> str:
    """Return '*' if significant, '' otherwise. Used in plot annotations."""
    sig = is_significant(p_value, alpha=alpha)
    return "*" if sig else ""


def stars_from_p(p_value) -> str:
    """Standard significance stars: <.001 ***; <.01 **; <.05 *; else empty."""
    v = safe_float(p_value)
    if v is None:
        return ""
    if v < 0.001:
        return "***"
    if v < 0.01:
        return "**"
    if v < 0.05:
        return "*"
    return ""


def crosses_null(lower, upper, null: float = 1.0) -> Optional[bool]:
    """Return True if the CI crosses the null value (default 1.0 for ratios)."""
    lo = safe_float(lower)
    hi = safe_float(upper)
    if lo is None or hi is None:
        return None
    return lo <= null <= hi
