# AI Agent Specification: Building New Tools for the TriNetX Publication Toolkit

This document tells you — an AI agent extending the TriNetX Publication
Toolkit v2 — exactly how to build a new tool that fits the toolkit's
architecture. Read this document **in full** before writing any code. The
toolkit's value comes from coherence; a tool that does not follow the
patterns below degrades the system rather than extending it.

---

## 1. What the toolkit is, and what it is not

The TriNetX Publication Toolkit is a Streamlit application that converts
TriNetX Analytics exports into manuscript-ready tables, figures, and rigor
diagnostics for observational studies. It is structured around **four phases
of a real-world data (RWD) study**:

| Phase | Purpose | Tool prefixes |
|---|---|---|
| 1 — Design | Decisions made before any data are pulled | `01_*` and `02_*` |
| 2 — Cohort | Construction and balance assessment | `03_*` and `04_*` |
| 3 — Outcomes | Effect estimation and presentation | `05_*` through `08_*` |
| 4 — Rigor & Reporting | Sensitivity, diagnostics, reporting standards | `09_*` through `13_*` |

A tool that does not produce a manuscript artifact or a rigor diagnostic
**does not belong in this toolkit**. Calculators, exploratory dashboards,
and quality-of-life utilities that don't connect to a manuscript should
live elsewhere.

The toolkit is **not** a general-purpose statistics platform. It assumes
the user has already run TriNetX Analytics and exported CSVs. The tool's
job is to translate those exports into outputs an investigator can
defensibly include in a peer-reviewed manuscript.

---

## 2. Before you start: decide whether the tool belongs

Answer these four questions in writing before you write code:

1. **What manuscript artifact does this tool produce?** A specific Table N,
   a specific Figure N, a Methods paragraph, a Limitations paragraph, a
   reporting checklist, or a supplementary protocol document. If the
   answer is "it just shows the user something useful," stop — that is not
   a manuscript artifact and the tool does not belong in this toolkit.

2. **Which TriNetX export does it consume?** Baseline CSV, MOA CSV, KM
   CSV, manual entry, or none (in which case it is a Phase 1 tool that
   takes only questionnaire input). If it requires a TriNetX format that
   does not yet have a parser in `utils/parsers.py`, you must extend the
   parser layer first (see Section 7), not write a one-off parser in your
   page.

3. **Which phase does it fit?** If it could plausibly fit in multiple
   phases, pick the *earliest* phase. Tools encountered earlier in the
   workflow have higher leverage because they shape later decisions.

4. **Does it produce something an existing tool already produces?** If
   yes, extend the existing tool. Do not create a parallel tool that
   produces a slightly different version of the same artifact — this is
   the failure mode that v2 was built to eliminate.

If you cannot answer all four questions clearly, the tool is not ready to
build. Stop and discuss with the user.

---

## 3. The non-negotiable architectural rules

These are the rules that make the toolkit a coherent system rather than a
collection of scripts. Violating any of them produces v1-style failure
modes that v2 was designed to prevent.

### Rule 1. Every tool imports from `utils/`

A tool **must not** implement its own:

- TriNetX file parser (use `utils.parsers`)
- P-value, percentage, ratio, or CI formatter (use `utils.formatters`)
- Cohort label or direction storage (use `utils.session`)
- Color palette, font, or figure-size preset (use `utils.figure_defaults`)
- PNG / SVG / DOCX / CSV download button (use `utils.exports`)

If you find yourself writing a function that already exists in `utils/`,
delete your version and use the shared one. If you need a helper that
*almost* exists in `utils/` but with a small tweak, extend the existing
helper rather than copying it.

### Rule 2. The study context is the single source of truth

Every tool must call `ensure_context()` at the top and `render_context_banner()`
immediately after the title. Cohort labels, treated/exposed direction,
outcome polarity, alpha, target power, p-value style, and decimal
preferences come from this context — never from per-page widgets.

Per-page widgets are allowed for *visual* overrides (palette selection in
a plotting tool's sidebar, for example), but the default must come from
the context.

### Rule 3. Uploaded files are shared across tools

When a tool accepts a TriNetX CSV, it must:

1. Offer the file uploader for new uploads
2. Offer a multiselect of files already uploaded this session (via
   `list_uploads(of_type=...)`)
3. Register every new upload via `register_upload(file_id, name,
   raw_bytes, detected_type)` so the next tool can use it

This prevents the v1 pattern of users uploading the same MOA CSV to five
different tools.

### Rule 4. Every output has a verify-against-source widget

Every numerical output that came from a TriNetX export must be paired with
a `render_source_check(label, content)` widget showing the parsed values.
The user must be able to see at a glance which cells of which CSV
section produced the numbers in the published table or figure.

### Rule 5. Every tool ends with the standard footer trio

The last three calls of every tool page (in order) are:

```python
render_check_callout("...")
render_methods_text("...", title="Methods text for your manuscript")
render_reproducibility_footer("Tool name")
```

The check callout is a one-sentence warning about the most common mistake
a user could make with this tool's output. The methods text is a
ready-to-paste sentence or paragraph. The footer prints toolkit version
and timestamp.

### Rule 6. Figures offer PNG and SVG; tables offer CSV and DOCX

Every figure call ends with `render_figure_downloads(fig, prefix=...)`.
Every table call ends with `render_table_downloads(df, prefix=..., docx_title=...)`.
Do not implement your own download buttons. Frontiers and most other
journals accept SVG; the shared helpers offer it by default.

### Rule 7. No silent failures on missing data

If a parsed TriNetX export is missing an expected section, the tool must
either:

- Explicitly raise an error with a message naming the missing section, or
- Render a clearly labeled placeholder in the output explaining that the
  field is absent

It must never produce a silently truncated table with empty cells in
columns the user is expecting values for. The v1 toolkit had this failure
mode; v2 must not.

### Rule 8. No hard-coded section row indices

The v1 Power calculator broke whenever TriNetX changed its export layout
because it indexed sections with hard-coded row numbers (`arr[10, 2]`).
A v2 tool that does this is broken on arrival. Always use
`parse_moa_csv()` or `parse_km_csv()` to get named-attribute access.

### Rule 9. No emoji shortcuts in code

Decorative emoji belong in page filenames (so Streamlit renders them in
the sidebar), section headings, and user-facing messages. They must not
appear in variable names, function names, or any value that could end up
in a CSV / DOCX export or a Methods paragraph. Journal Methods sections
do not contain emoji.

### Rule 10. Make every tool reproducible from a single CSV

A user who has the same TriNetX CSV(s), the same toolkit version, and
makes the same selections in the editor widgets must produce a byte-for-byte
identical output. No tool may depend on the current wall-clock time
(except for the timestamp in the download filename), random seeds, or any
external service.

---

## 4. The standardized page template

Every Streamlit page in `pages/` follows this 15-step template. Do not skip
steps. Do not reorder steps. If a step does not apply to your tool, leave
it out *and* leave a comment explaining why.

```python
"""
NN_emoji_Tool_Name.py — Phase X tool.

One-paragraph description of what the tool does and what manuscript
artifact it produces. Reference the four-phase placement.

This tool consumes: [Baseline CSV / MOA CSV / KM CSV / manual entry / none]
This tool produces: [Table N / Figure N / Methods paragraph / Limitations paragraph / checklist]
"""

# Step 1. Imports
from __future__ import annotations
from io import BytesIO  # only if parsing files
from typing import Any, Dict, List

import pandas as pd
import streamlit as st
# matplotlib only if producing a figure
import matplotlib.pyplot as plt

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
    parse_moa_csv,           # only the ones you actually use
    detect_export_type,
    EXPORT_MOA, EXPORT_KM, EXPORT_BASELINE,
    MOAExport, KMExport, BaselineExport,
)
from utils.formatters import (
    fmt_p, fmt_pct, fmt_ratio_with_ci, fmt_smd, fmt_count_pct,
    safe_float, safe_int, crosses_null, is_significant,
)
from utils.figure_defaults import (
    palette_colors, preset_size, FONT_CHOICES,
    PALETTES, FIGURE_PRESETS, DEFAULT_DPI,
)
from utils.exports import (
    render_figure_downloads, render_table_downloads,
    render_reproducibility_footer,
)

# Step 2. Page config + context
st.set_page_config(
    page_title="Your Tool",
    page_icon="🔧",  # see Section 5 for emoji choice
    layout="wide",
)
ctx = ensure_context()

# Step 3. Title and one-sentence caption
st.title("Your Tool Name")
st.caption(
    "One sentence. State what manuscript artifact this produces."
)

# Step 4. Context banner (always present)
render_context_banner()  # show_advanced=True ONLY on Home.py

# Step 5. (Optional) Methodological background expander
with st.expander("About this tool", expanded=False):
    st.markdown("""
    Brief explanation of the underlying method or reporting standard.
    Cite primary sources. This is where the user learns *why* the tool
    works the way it does.
    """)

# Step 6. Upload block (only for tools that consume TriNetX CSVs)
st.markdown("### Upload [TriNetX export type]")
session_uploads = list_uploads(of_type=EXPORT_MOA)  # or EXPORT_KM, EXPORT_BASELINE

col1, col2 = st.columns(2)
with col1:
    new_files = st.file_uploader(
        "New uploads",
        type=["csv", "txt"],
        accept_multiple_files=True,
    )
with col2:
    if session_uploads:
        reused = st.multiselect(
            "Reuse session uploads",
            options=[u["name"] for u in session_uploads],
            default=[u["name"] for u in session_uploads],
        )
    else:
        reused = []
        st.caption("No matching files cached this session.")

# Step 7. Parse uploaded files, registering each one for later tools
parsed = []
errors = []

def _add(name: str, raw: bytes):
    try:
        etype = detect_export_type(raw.decode("utf-8-sig", errors="replace"))
        if etype != EXPORT_MOA:  # or whichever you require
            errors.append(f"{name}: detected as {etype}, expected MOA")
            return
        obj = parse_moa_csv(BytesIO(raw))
        parsed.append({"name": name, "obj": obj})
        register_upload(f"moa_{name}", name, raw, EXPORT_MOA)
    except Exception as exc:
        errors.append(f"{name}: parse error ({exc})")

if new_files:
    for f in new_files:
        _add(f.name, f.read())
for name in reused:
    cached = next((u for u in session_uploads if u["name"] == name), None)
    if cached and not any(p["name"] == name for p in parsed):
        _add(cached["name"], cached["bytes"])

if errors:
    with st.expander("Parsing issues", expanded=True):
        for e in errors:
            st.warning(e)

if not parsed:
    st.info("Upload at least one [TriNetX export type] to continue.")
    st.stop()

# Step 8. Parsed-summary banner (one-line confirmation)
st.success(f"Parsed **{len(parsed)}** file(s) successfully.")

# Step 9. Edit-before-export data editor
# Every tool that produces a table or figure with multiple rows must
# expose them in a st.data_editor with an Include checkbox and an
# Order column. The user must be able to remove rows or reorder them
# before exporting.
st.markdown("### Review and edit")
edit_df = pd.DataFrame([...])
edited = st.data_editor(
    edit_df,
    use_container_width=True,
    num_rows="fixed",
    column_config={
        "Include": st.column_config.CheckboxColumn(),
        "Order": st.column_config.NumberColumn(min_value=1, step=1),
        # Disable computed columns so the user cannot accidentally fabricate values
        "Estimate": st.column_config.NumberColumn(disabled=True, format="%.3f"),
    },
)

# Step 10. Sidebar visual controls (only if producing a figure)
with st.sidebar:
    st.header("Plot options")
    palette_name = st.selectbox(
        "Palette",
        list(PALETTES.keys()),
        index=list(PALETTES.keys()).index(ctx.palette) if ctx.palette in PALETTES else 0,
    )
    color1, color2 = palette_colors(palette_name)
    # ...etc

# Step 11. Output preview
# Render the figure or table. Use the shared color palette and font.
fig, ax = plt.subplots(figsize=preset_size(ctx.figure_preset))
# ...build figure...
st.pyplot(fig)

# Step 12. Standardized downloads
render_figure_downloads(fig, prefix="your_tool", dpi=DEFAULT_DPI)
# OR for tables:
# render_table_downloads(df, prefix="your_table", docx_title="Table N")

# Step 13. Verify-against-source widgets
st.markdown("---")
for p in parsed:
    obj = p["obj"]
    render_source_check(
        f"Parsed values from {p['name']}",
        pd.DataFrame([
            {"Field": "Cohort 1 N", "Value": str(obj.cohort_1_n)},
            {"Field": "Risk Ratio", "Value": fmt_ratio_with_ci(
                obj.risk_ratio_value, obj.risk_ratio_ci[0], obj.risk_ratio_ci[1]
            )},
            # ...etc
        ]),
    )

# Step 14. Auto-generated narrative paragraph (optional but recommended)
with st.expander("Results-section narrative (auto-generated)", expanded=False):
    narrative = build_narrative(parsed, ctx)
    st.markdown(narrative)
    st.download_button(
        "Download narrative (Markdown)",
        data=narrative.encode("utf-8"),
        file_name="narrative.md",
        mime="text/markdown",
    )

# Step 15. Check + methods text + footer (the trio is mandatory)
render_check_callout(
    "One sentence describing the most common mistake a user could make with "
    "this tool's output, and how to avoid it."
)

render_methods_text(
    """A ready-to-paste Methods sentence or paragraph that accurately reflects
what this tool computed. Use placeholders ({n_files}, {cohort_label}) populated
from runtime values. Reference the toolkit version.""",
    title="Methods text for your manuscript",
)

render_reproducibility_footer("Your Tool Name")
```

---

## 5. Choosing the page filename and emoji

The filename determines where the tool appears in the Streamlit sidebar.
The format is:

```
NN_emoji_Tool_Name.py
```

Where:

- **NN** is a two-digit number determined by the phase, in this order:
  - `01`-`02`: Phase 1 (Design)
  - `03`-`04`: Phase 2 (Cohort)
  - `05`-`08`: Phase 3 (Outcomes)
  - `09`-`13`: Phase 4 (Rigor & Reporting)
  - `14`+: Reserved for new tools — pick the next free number within
    the appropriate phase range
- **emoji** is one decorative emoji that hints at the tool's function
- **Tool_Name** uses underscores between words, no spaces

If your new tool would push another tool out of its slot, renumber both.
Do not reuse a number.

Reserved emoji for the current phases:
- 📋 Pre-Analysis Plan
- ⚠️ Bias Check
- ❤️ Love Plot
- ⚖️ PSM Table
- 🧮 Outcomes Table
- 🌲 Forest Plot
- 📊 Two-Cohort Bar (and Multiple Comparisons)
- 📉 Kaplan-Meier Curve
- 🎯 Power / E-value / NNT
- 📐 Effect Size
- 🔬 KM Diagnostics
- ✅ STROBE + RECORD

When adding a new tool, pick a fresh emoji that does not already appear in
the toolkit.

---

## 6. The utility modules — full reference

Read this section as the API spec for `utils/`. If a function you need is
not listed here, it does not exist, and you must either extend the
appropriate module (see Section 7) or write your tool without it. Do not
implement local duplicates.

### `utils/session.py`

```python
# Get or create the live StudyContext
ensure_context() -> StudyContext
get_context() -> StudyContext
update_context(**kwargs) -> StudyContext

# UI components
render_context_banner(show_advanced=False) -> StudyContext
render_source_check(label: str, content) -> None
render_methods_text(text: str, title: str = "...") -> None
render_check_callout(text: str) -> None

# Upload registry
register_upload(file_id: str, name: str, raw_bytes: bytes, detected_type: str)
list_uploads(of_type: Optional[str] = None) -> List[Dict]
remove_upload(file_id: str)
clear_uploads()
upload_as_bytesio(file_id: str) -> Optional[io.BytesIO]
```

The `StudyContext` exposes these fields, all of which a tool may read but
should only write through `update_context()`:

```python
cohort_1_label: str
cohort_2_label: str
treated_cohort: str  # "1" or "2"
outcome_polarity: str  # "adverse" or "beneficial"
alpha: float
power_target: float
two_sided: bool
multiple_comparison_family: str
pct_decimals: int
ratio_decimals: int
smd_decimals: int
p_style: str  # "apa", "decimal", "scientific"
palette: str
font_family: str
figure_preset: str
study_title: str
investigator: str
uploads: Dict[str, Dict]

# Derived properties (use these, do not recompute):
ctx.treated_label   # str — name of treated cohort
ctx.control_label   # str — name of control cohort
ctx.outcome_is_adverse  # bool
```

### `utils/parsers.py`

```python
# Top-level parsers
parse_baseline_csv(uploaded) -> BaselineExport
parse_moa_csv(uploaded) -> MOAExport
parse_km_csv(uploaded) -> KMExport
detect_and_parse(uploaded) -> Union[BaselineExport, MOAExport, KMExport]
detect_export_type(text: str) -> str  # EXPORT_BASELINE / EXPORT_MOA / EXPORT_KM / EXPORT_UNKNOWN

# Export-type constants
EXPORT_BASELINE = "baseline"
EXPORT_MOA = "moa"
EXPORT_KM = "km"
EXPORT_UNKNOWN = "unknown"
```

Each returned dataclass exposes named attributes. **Use the attributes;
do not re-parse the underlying DataFrames.** Example:

```python
moa = parse_moa_csv(uploaded)
moa.cohort_1_label          # str
moa.cohort_1_n              # Optional[int]
moa.cohort_1_events         # Optional[int]
moa.cohort_1_risk           # Optional[float], normalized to proportion (0-1)
moa.primary_p_value         # Optional[float], typically from Risk Difference section
moa.primary_p_source        # str — which section the p came from
moa.risk_ratio_value        # Optional[float]
moa.risk_ratio_ci           # Tuple[Optional[float], Optional[float]]
moa.odds_ratio_value        # Optional[float]
moa.odds_ratio_ci           # Tuple[Optional[float], Optional[float]]
moa.cohort_statistics       # pd.DataFrame (the raw section, for verify-against-source)
moa.risk_difference         # Optional[pd.DataFrame]
moa.source_excerpt          # str — display in verify-against-source widget
moa.source_provenance       # Dict[str, Any] — which sections were found, etc.
```

```python
km = parse_km_csv(uploaded)
km.df                       # pd.DataFrame — survival time series (may be empty for summary-only exports)
km.cohort_1_label, km.cohort_2_label
km.cohort_1_n, km.cohort_2_n
km.hazard_ratio, km.hazard_ratio_ci
km.log_rank_p
km.ph_assumption_p          # Optional[float] — from TriNetX's Proportional Hazard Assumption / Proportionality section
km.max_days
```

```python
baseline = parse_baseline_csv(uploaded)
baseline.df                 # pd.DataFrame with all baseline rows
baseline.has_smd_columns    # bool
baseline.cohort_1_label, baseline.cohort_2_label
```

### `utils/formatters.py`

```python
# Safe coercion
safe_float(x, default=None) -> Optional[float]
safe_int(x, default=None) -> Optional[int]

# Core formatters (every returns str)
fmt_p(value, style="apa", na="") -> str
    # style="apa":        <.001, .034, .210
    # style="decimal":    <0.001, 0.034, 0.210
    # style="scientific": 0.00012 -> 1.2e-04

fmt_pct(value, decimals=2, na="") -> str         # Input is proportion (0-1)
fmt_pct_already(value, decimals=2, na="") -> str # Input is already in percent
fmt_ratio(value, decimals=2, na="") -> str
fmt_ci(lower, upper, decimals=2, sep=" to ", na="") -> str
fmt_ratio_with_ci(point, lower, upper, decimals=2, na="") -> str
fmt_smd(value, decimals=3, na="") -> str
fmt_count(value, na="") -> str                   # Thousands separator
fmt_count_pct(count, pct, count_decimals=0, pct_decimals=2, na="") -> str
fmt_mean_sd(mean, sd, decimals=2, na="") -> str

# Significance helpers
is_significant(p_value, alpha=0.05) -> Optional[bool]
significance_marker(p_value, alpha=0.05) -> str  # "*" or ""
stars_from_p(p_value) -> str                     # "***", "**", "*", ""
crosses_null(lower, upper, null=1.0) -> Optional[bool]
```

### `utils/figure_defaults.py`

```python
PALETTES: Dict[str, List[str]]           # 8 two-color palettes
EXTENDED_PALETTES: Dict[str, List[str]]  # multi-category palettes
FONT_CHOICES: List[str]                  # 7 font families
FIGURE_PRESETS: Dict[str, Tuple[float, float]]  # 6 size presets

palette_colors(name: str) -> Tuple[str, str]
preset_size(name: str) -> Tuple[float, float]

DEFAULT_DPI = 300
NULL_LINE_COLOR = "#2A2A2A"
NULL_LINE_STYLE = "--"
GRID_COLOR = "#DDDDDD"
SIGNIFICANT_COLOR = "#1F1F1F"
NONSIGNIFICANT_COLOR = "#9C9C9C"
```

### `utils/exports.py`

```python
figure_to_png_bytes(fig, dpi=300) -> bytes
figure_to_svg_bytes(fig) -> bytes
dataframe_to_docx_bytes(df, title=None) -> bytes

render_figure_downloads(fig, prefix, dpi=300, include_pdf=False)
render_table_downloads(df, prefix, docx_title=None, include_docx=True)
render_reproducibility_footer(tool_name, version="2.0.0")

DOCX_AVAILABLE: bool  # True if python-docx is installed
```

---

## 7. Extending the utility modules

If you need a helper that does not exist in `utils/`, add it to the
appropriate module. The decision tree:

- Number formatting → `utils/formatters.py`
- TriNetX file parsing → `utils/parsers.py`
- Study-level state → `utils/session.py`
- Color, font, figure-size → `utils/figure_defaults.py`
- Download buttons or file encoding → `utils/exports.py`
- Statistical computation that two or more tools share → create
  `utils/stats.py` if it does not exist, then add to it

When you extend a utility module:

1. Add the new function with a complete docstring matching the style of
   the existing functions in that module
2. Add the function to the `__init__.py` re-exports if other modules
   should be able to import it
3. Add a brief note to this document under Section 6
4. If the function has any subtlety (e.g., the way `fmt_p` drops leading
   zeros), include an inline example in the docstring

Never add a utility function inside a `pages/` file. If you find yourself
writing `def helper(...)` near the top of a page, ask whether other tools
will need this helper too — they probably will.

---

## 8. Adding a new TriNetX export type

If TriNetX adds a new export format, or you need to support a format the
toolkit currently doesn't handle, the procedure is:

1. **Inspect a real example.** Open the new CSV in a text editor and
   identify the section headers, the cohort identification rows, and the
   summary-statistics rows.

2. **Add a constant** to `utils/parsers.py`:
   ```python
   EXPORT_NEW_TYPE = "new_type"
   ```

3. **Add the section names** to the `SECTION_NAMES` set if your export
   contains section headers that should stop the section parser.

4. **Define a dataclass** that holds the parsed result, following the
   pattern of `MOAExport` and `KMExport`. Every field should be
   `Optional` if the source CSV could ever omit it.

5. **Write the parser**:
   ```python
   def parse_new_type_csv(uploaded) -> NewTypeExport:
       text = _read_uploaded(uploaded)
       rows = _csv_rows(text)
       # ... use _find_section, _rows_to_df, _find_col helpers ...
       return NewTypeExport(...)
   ```

6. **Update the dispatcher** `detect_export_type` and `detect_and_parse`
   to recognize the new format.

7. **Add unit tests** that round-trip a sample file through the parser
   and assert that key values come out correctly.

8. **Document the new type** in the table at Section 4 of
   `THEORETICAL_DESIGN.md` ("The unifying data model") and in the
   `README.md` repository-layout table.

---

## 9. Adding a new tool — full walkthrough

Suppose you are asked to build a "Cohort Attrition Diagram" tool. Here is
the end-to-end process.

### Step A. Frame the tool

- **Manuscript artifact produced:** CONSORT-style flow diagram (figure).
- **TriNetX export consumed:** None directly — user manually enters
  attrition counts derived from TriNetX query criteria.
- **Phase:** 2 (Cohort).
- **Existing tool overlap:** None — Love Plot and PSM Table assume the
  cohort is already constructed; this tool documents how it was
  constructed.

All four framing questions answer cleanly. Proceed.

### Step B. Choose filename and emoji

- Phase 2 slot, next free number: `03_*` and `04_*` are taken (Love Plot,
  PSM Table), so this is `04a` — no, do not use letters. Renumber:
  - Old `04_⚖️_PSM_Table.py` becomes `05_⚖️_PSM_Table.py`
  - New tool is `04_🔀_Cohort_Attrition.py`
  - All downstream Phase 3+ tools shift up by 1
- Emoji: 🔀 (not currently used)

Actually, the renumbering ripple is large. A practical alternative is to
add the tool at the end of Phase 2 with `04` and renumber only the new
tool's neighbor. Discuss with the user before doing a large renumbering.

### Step C. Implement

Follow the 15-step template in Section 4. The Cohort Attrition tool
specifically would:

1. Use `ensure_context()` and `render_context_banner()`.
2. Skip the upload block (no TriNetX file consumed).
3. Use `st.data_editor` for the attrition steps (Step name, N before, N
   after, Reason for exclusion).
4. Build a matplotlib figure showing the flow.
5. Call `render_figure_downloads(fig, prefix="cohort_attrition")`.
6. Render a verify-against-source widget showing the entered data as a
   table.
7. Auto-generate a Results-section sentence: "Of N patients meeting the
   broad eligibility criteria, M were excluded for reasons including
   X, Y, and Z; the final analytic cohort comprised K patients."
8. Provide the standard footer trio.

### Step D. Test against a realistic scenario

Before finalizing, walk through a realistic user session:

1. User opens Home, sets cohort labels and direction.
2. User opens the new tool — does it inherit the labels?
3. User fills in attrition data, generates the figure — does it render?
4. User downloads PNG and SVG — are both valid?
5. User opens the next tool (PSM Table) — does the new tool's output
   complement the PSM output without contradicting it?

If any answer is no, fix it before declaring the tool complete.

### Step E. Document the new tool

1. Update `Home.py`:
   - Add a row to the four-phase visual map
   - Add a row to the quick chooser table
2. Update `README.md`:
   - Add the new file to the repository-layout tree
3. Update `docs/THEORETICAL_DESIGN.md`:
   - Add the tool to the appropriate phase's bullet list
4. Update `assets/architecture_diagram.svg`:
   - Add a box for the new tool in the Phase 2 column
   - (Re-render the PNG preview)

A new tool that is not documented in all four places is incomplete.

---

## 10. Testing and verification

Before declaring any new tool complete, run these checks:

### Compile check

```bash
python3 -c "
import py_compile, os
for root, _, fs in os.walk('.'):
    if '__pycache__' in root: continue
    for f in fs:
        if f.endswith('.py'):
            py_compile.compile(os.path.join(root, f), doraise=True)
print('All compile.')
"
```

### Runtime check

```bash
streamlit run Home.py --server.headless true --server.port 8505 &
sleep 6
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8505/
pkill -f streamlit
```

The Home page should return HTTP 200. Manually navigate to your new tool
page in a browser to confirm it renders without exceptions.

### Realistic-data check

If your tool consumes TriNetX exports, run it against the canonical test
files in `/mnt/project/` or wherever the project keeps reference data.
Confirm:

1. Parser detects the file type correctly
2. Values shown in the output match values in the source CSV
3. Verify-against-source widget displays the right cells
4. Downloads produce valid files (open the DOCX in Word, the SVG in a
   browser, the PNG in an image viewer)

### Regression check

Run every other tool that consumes the same export type to confirm your
changes (especially if you modified `utils/parsers.py`) did not break
them.

---

## 11. Common failure modes to avoid

These are the mistakes most likely to creep into a new tool. Read the
list before you start coding, and again before you submit.

**Re-parsing files inside the page.** If you find yourself writing
`pd.read_csv(uploaded)` instead of `parse_moa_csv(uploaded)`, stop and
use the parser.

**Hard-coding cohort direction.** "Cohort 1 is treated" appears in v1
tools. In v2, always read direction from `ctx.treated_cohort`.

**Recomputing values the parser already extracted.** If you find yourself
slicing `df.iloc[0, 2]` to get a p-value, stop. The parser exposes it as
`moa.primary_p_value`.

**Building per-page download buttons.** The shared
`render_figure_downloads` and `render_table_downloads` exist for a
reason. Per-page download buttons produce inconsistent file naming and
miss SVG/DOCX.

**Skipping the source-check widget.** Reviewers asking "where did this
number come from?" is the single most common reason RWD manuscripts are
sent back. The source-check widget is the toolkit's structural answer to
that question. Do not skip it.

**Skipping the methods text.** Authors should never have to write the
Methods sentence for a tool's output from scratch. If your tool produces
a number that goes in a paper, your tool produces the Methods sentence
that describes it.

**Mixing effect estimates without labeling.** A forest plot showing both
HRs and RRs without an explicit x-axis label is a recipe for reader
confusion. Tools that combine effect types must label the axis or column
explicitly.

**Adding optional features at the cost of mandatory ones.** A clever
new visualization is not worth shipping if it required cutting the
verify-against-source widget to fit. The mandatory elements (context
banner, source check, methods text, footer trio) are mandatory.

**Producing outputs that depend on session-specific decisions.** If a
user reruns the tool a week later with the same CSV but slightly
different in-app selections, the output will differ. That is fine — but
the user must be able to see what was selected. Display every choice in
the output's verify section.

---

## 12. When to stop and ask the user

Stop and ask, instead of proceeding:

- If your proposed tool overlaps with an existing tool's responsibilities
- If your tool would require renumbering more than two existing pages
- If you cannot find an existing utility that does what you need, and
  you're unsure whether to extend an existing module or create a new one
- If the new tool requires a parser change that might affect existing
  tools
- If the test data you have does not cover an important configuration
  (e.g., you're building a KM-related tool but the test KM file is
  summary-only, no time series)
- If you are tempted to violate any of the Rule 1-10 architectural rules
  for "just this one tool"

The toolkit's value depends on consistency. A single tool that violates
the rules degrades the system for every future tool. When in doubt,
escalate.

---

## 13. Summary checklist

Before declaring a new tool ready:

- [ ] Tool framing answered all four questions in Section 2
- [ ] Filename, number, and emoji follow Section 5
- [ ] Page follows the 15-step template in Section 4
- [ ] Imports come from `utils/` — no local re-implementations
- [ ] Context banner present at top
- [ ] Uploads (if any) registered via `register_upload`
- [ ] Output uses shared palette / font / figure preset
- [ ] Downloads use `render_figure_downloads` / `render_table_downloads`
- [ ] Verify-against-source widget for every numerical output
- [ ] Footer trio present: check callout, methods text, reproducibility
- [ ] No emoji in CSV / DOCX exports or Methods text
- [ ] Tool compiles cleanly
- [ ] Streamlit boots and the page renders without exceptions
- [ ] Tested against real TriNetX exports
- [ ] Tool documented in Home.py, README.md, THEORETICAL_DESIGN.md,
      architecture_diagram.svg

If any item is unchecked, the tool is not ready. Fix the gap before
shipping.

---

_This specification document is part of the TriNetX Publication Toolkit v2
and should be updated whenever the architectural rules or utility APIs
change. Future AI agents extending the toolkit must read it in full
before writing any code._
