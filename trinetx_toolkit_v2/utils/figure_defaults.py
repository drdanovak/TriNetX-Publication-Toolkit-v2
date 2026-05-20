"""
figure_defaults.py — Shared visual defaults for the TriNetX Publication Toolkit.

Every figure-producing tool reads palette, font, and figure-size choices from
here, with the per-tool ability to override. This guarantees that a forest
plot, a KM curve, and a two-cohort bar graph from the same study session
share the same color scheme and typography by default.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# Color palettes
# ---------------------------------------------------------------------------

PALETTES: Dict[str, List[str]] = {
    "Classic TriNetX": ["#8e44ad", "#27ae60"],
    "Colorblind-safe (Wong)": ["#0072B2", "#D55E00"],
    "Tol (bright)": ["#4477AA", "#EE6677"],
    "Blue-Green": ["#1B9E77", "#7570B3"],
    "Slate / Amber": ["#334155", "#D97706"],
    "Teal / Coral": ["#0F766E", "#E76F51"],
    "High-Contrast": ["#000000", "#E69F00"],
    "Grayscale": ["#3A3A3A", "#9C9C9C"],
}

EXTENDED_PALETTES: Dict[str, List[str]] = {
    # Multi-category palettes for outputs with > 2 series (e.g., subgroup plots)
    "Tol (vibrant)": ["#4477AA", "#EE6677", "#228833", "#CCBB44", "#66CCEE", "#AA3377"],
    "Okabe-Ito": ["#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7"],
    "Slate gradient": ["#0F172A", "#1E293B", "#334155", "#475569", "#64748B", "#94A3B8"],
}


def palette_colors(name: str) -> Tuple[str, str]:
    pal = PALETTES.get(name, PALETTES["Classic TriNetX"])
    return pal[0], pal[1]


# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------

FONT_CHOICES: List[str] = [
    "Arial",
    "Helvetica",
    "Times New Roman",
    "Georgia",
    "Calibri",
    "Source Sans Pro",
    "DejaVu Sans",
]

# Frontiers prefers Arial-family for figures and Times for tables; defaults
# below match this convention.
DEFAULT_FIGURE_FONT = "Arial"
DEFAULT_TABLE_FONT = "Times New Roman"


# ---------------------------------------------------------------------------
# Figure-size presets
# ---------------------------------------------------------------------------

FIGURE_PRESETS: Dict[str, Tuple[float, float]] = {
    "Journal column (single)": (3.5, 3.0),
    "Journal column (1.5x)": (5.0, 3.5),
    "Journal page (double)": (7.2, 4.5),
    "Poster (landscape)": (10.0, 6.0),
    "Slide (16:9)": (10.0, 5.625),
    "Square preview": (5.0, 5.0),
}


def preset_size(name: str) -> Tuple[float, float]:
    return FIGURE_PRESETS.get(name, FIGURE_PRESETS["Journal column (single)"])


# ---------------------------------------------------------------------------
# DPI and other constants
# ---------------------------------------------------------------------------

DEFAULT_DPI = 300                # Frontiers minimum for raster figures
SVG_DEFAULT = True               # All tools should offer SVG download
NULL_LINE_COLOR = "#2A2A2A"      # Color of x=1 reference line in forest plots
NULL_LINE_STYLE = "--"
GRID_COLOR = "#DDDDDD"
ANNOTATION_COLOR = "#222222"
CI_LINE_COLOR = "#1F1F1F"

# Significance state colors (used in forest plots to flag CI-crosses-null)
SIGNIFICANT_COLOR = "#1F1F1F"        # solid black
NONSIGNIFICANT_COLOR = "#9C9C9C"     # mid-grey
