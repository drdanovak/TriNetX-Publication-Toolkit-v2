"""
TriNetX Publication Toolkit — shared utilities.

This package provides the four foundational modules that every tool depends on:

- parsers:          One parser per TriNetX export type
- formatters:       Shared number-formatting helpers
- session:          The unified study context
- figure_defaults:  Palette, fonts, figure-size presets
- exports:          PNG / SVG / CSV / DOCX download helpers

Tools should import from this package rather than re-implementing any of
these functions, so that the toolkit behaves as a single coherent system.
"""

from . import formatters, session, parsers, figure_defaults, exports  # noqa: F401

__version__ = "2.0.0"
