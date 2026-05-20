<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 1000" font-family="Helvetica, Arial, sans-serif">
  <!-- Background -->
  <rect width="1200" height="1000" fill="#FAFAF7"/>

  <!-- Title -->
  <text x="600" y="38" text-anchor="middle" font-size="22" font-weight="700" fill="#1A1A1A">
    TriNetX Publication Toolkit — Architecture
  </text>
  <text x="600" y="62" text-anchor="middle" font-size="13" fill="#555">
    Layered design: TriNetX exports flow through shared parsers into a study context that every tool reads from
  </text>

  <!-- LAYER 1: TriNetX exports (top) -->
  <g>
    <rect x="50" y="95" width="1100" height="100" rx="6" fill="#FFFFFF" stroke="#2C5F7C" stroke-width="1.5"/>
    <text x="70" y="120" font-size="12" font-weight="700" fill="#2C5F7C" letter-spacing="1.5">LAYER 1 &#8226; TRINETX EXPORTS</text>

    <g transform="translate(70,135)">
      <rect width="240" height="48" rx="4" fill="#EAF2F6" stroke="#2C5F7C"/>
      <text x="120" y="20" text-anchor="middle" font-size="12" font-weight="600" fill="#1A1A1A">Baseline Patient Characteristics</text>
      <text x="120" y="38" text-anchor="middle" font-size="10" fill="#555">CSV with before/after SMDs</text>
    </g>
    <g transform="translate(330,135)">
      <rect width="240" height="48" rx="4" fill="#EAF2F6" stroke="#2C5F7C"/>
      <text x="120" y="20" text-anchor="middle" font-size="12" font-weight="600" fill="#1A1A1A">Measures of Association</text>
      <text x="120" y="38" text-anchor="middle" font-size="10" fill="#555">RR, OR, RD, p-values, risks</text>
    </g>
    <g transform="translate(590,135)">
      <rect width="240" height="48" rx="4" fill="#EAF2F6" stroke="#2C5F7C"/>
      <text x="120" y="20" text-anchor="middle" font-size="12" font-weight="600" fill="#1A1A1A">Kaplan-Meier Tables</text>
      <text x="120" y="38" text-anchor="middle" font-size="10" fill="#555">Time, survival, HR, log-rank</text>
    </g>
    <g transform="translate(850,135)">
      <rect width="240" height="48" rx="4" fill="#EAF2F6" stroke="#2C5F7C"/>
      <text x="120" y="20" text-anchor="middle" font-size="12" font-weight="600" fill="#1A1A1A">User-entered values</text>
      <text x="120" y="38" text-anchor="middle" font-size="10" fill="#555">Manual outcomes, ratios, p</text>
    </g>
  </g>

  <!-- Arrows down -->
  <g stroke="#2C5F7C" stroke-width="1.5" fill="none">
    <line x1="190" y1="195" x2="190" y2="225" marker-end="url(#arr)"/>
    <line x1="450" y1="195" x2="450" y2="225" marker-end="url(#arr)"/>
    <line x1="710" y1="195" x2="710" y2="225" marker-end="url(#arr)"/>
    <line x1="970" y1="195" x2="970" y2="225" marker-end="url(#arr)"/>
  </g>

  <defs>
    <marker id="arr" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto">
      <path d="M0,0 L10,5 L0,10 z" fill="#2C5F7C"/>
    </marker>
    <marker id="arr2" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto">
      <path d="M0,0 L10,5 L0,10 z" fill="#7C5C2C"/>
    </marker>
    <marker id="arr3" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto">
      <path d="M0,0 L10,5 L0,10 z" fill="#5C7C2C"/>
    </marker>
  </defs>

  <!-- LAYER 2: Shared utilities -->
  <g>
    <rect x="50" y="235" width="1100" height="115" rx="6" fill="#FFFFFF" stroke="#7C5C2C" stroke-width="1.5"/>
    <text x="70" y="260" font-size="12" font-weight="700" fill="#7C5C2C" letter-spacing="1.5">LAYER 2 &#8226; SHARED UTILITIES (utils/)</text>

    <g transform="translate(70,275)">
      <rect width="200" height="60" rx="4" fill="#FBF3E5" stroke="#7C5C2C"/>
      <text x="100" y="22" text-anchor="middle" font-size="12" font-weight="600" fill="#1A1A1A">parsers.py</text>
      <text x="100" y="40" text-anchor="middle" font-size="10" fill="#555">One parser per export type;</text>
      <text x="100" y="52" text-anchor="middle" font-size="10" fill="#555">used by every tool</text>
    </g>
    <g transform="translate(290,275)">
      <rect width="200" height="60" rx="4" fill="#FBF3E5" stroke="#7C5C2C"/>
      <text x="100" y="22" text-anchor="middle" font-size="12" font-weight="600" fill="#1A1A1A">formatters.py</text>
      <text x="100" y="40" text-anchor="middle" font-size="10" fill="#555">fmt_p, fmt_pct, fmt_ratio,</text>
      <text x="100" y="52" text-anchor="middle" font-size="10" fill="#555">fmt_ci, fmt_smd</text>
    </g>
    <g transform="translate(510,275)">
      <rect width="200" height="60" rx="4" fill="#FBF3E5" stroke="#7C5C2C"/>
      <text x="100" y="22" text-anchor="middle" font-size="12" font-weight="600" fill="#1A1A1A">session.py</text>
      <text x="100" y="40" text-anchor="middle" font-size="10" fill="#555">Study context; cohort labels;</text>
      <text x="100" y="52" text-anchor="middle" font-size="10" fill="#555">direction; cached uploads</text>
    </g>
    <g transform="translate(730,275)">
      <rect width="200" height="60" rx="4" fill="#FBF3E5" stroke="#7C5C2C"/>
      <text x="100" y="22" text-anchor="middle" font-size="12" font-weight="600" fill="#1A1A1A">figure_defaults.py</text>
      <text x="100" y="40" text-anchor="middle" font-size="10" fill="#555">Palettes, fonts, DPI,</text>
      <text x="100" y="52" text-anchor="middle" font-size="10" fill="#555">figure-size presets</text>
    </g>
    <g transform="translate(950,275)">
      <rect width="180" height="60" rx="4" fill="#FBF3E5" stroke="#7C5C2C"/>
      <text x="90" y="22" text-anchor="middle" font-size="12" font-weight="600" fill="#1A1A1A">exports.py</text>
      <text x="90" y="40" text-anchor="middle" font-size="10" fill="#555">PNG / SVG / CSV /</text>
      <text x="90" y="52" text-anchor="middle" font-size="10" fill="#555">DOCX / HTML / Markdown</text>
    </g>
  </g>

  <!-- Arrow down -->
  <g stroke="#7C5C2C" stroke-width="1.5" fill="none">
    <line x1="600" y1="350" x2="600" y2="380" marker-end="url(#arr2)"/>
  </g>

  <!-- LAYER 3: The four-phase tool layer -->
  <g>
    <rect x="50" y="390" width="1100" height="475" rx="6" fill="#FFFFFF" stroke="#5C7C2C" stroke-width="1.5"/>
    <text x="70" y="415" font-size="12" font-weight="700" fill="#5C7C2C" letter-spacing="1.5">LAYER 3 &#8226; FOUR-PHASE TOOL LAYER</text>

    <!-- Phase 1: Design -->
    <g transform="translate(70,430)">
      <rect width="245" height="415" rx="4" fill="#F4F8EC" stroke="#5C7C2C"/>
      <text x="122" y="22" text-anchor="middle" font-size="13" font-weight="700" fill="#3F5A1F">PHASE 1 &#8226; DESIGN</text>
      <text x="122" y="38" text-anchor="middle" font-size="10" font-style="italic" fill="#555">Before any data are pulled</text>

      <g transform="translate(12,55)">
        <rect width="220" height="62" rx="3" fill="#FFFFFF" stroke="#5C7C2C"/>
        <text x="110" y="20" text-anchor="middle" font-size="11" font-weight="700" fill="#1A1A1A">Pre-Analysis Plan</text>
        <text x="110" y="34" text-anchor="middle" font-size="9.5" fill="#555">PICO, index date, washout,</text>
        <text x="110" y="46" text-anchor="middle" font-size="9.5" fill="#555">outcomes, sensitivity plan</text>
        <text x="110" y="58" text-anchor="middle" font-size="8.5" font-style="italic" fill="#5C7C2C">NEW (tool F)</text>
      </g>

      <g transform="translate(12,127)">
        <rect width="220" height="62" rx="3" fill="#FFFFFF" stroke="#5C7C2C"/>
        <text x="110" y="20" text-anchor="middle" font-size="11" font-weight="700" fill="#1A1A1A">Bias Check Questionnaire</text>
        <text x="110" y="34" text-anchor="middle" font-size="9.5" fill="#555">Immortal-time, reverse</text>
        <text x="110" y="46" text-anchor="middle" font-size="9.5" fill="#555">causation, selection bias</text>
        <text x="110" y="58" text-anchor="middle" font-size="8.5" font-style="italic" fill="#5C7C2C">NEW (tool J)</text>
      </g>

      <text x="122" y="220" text-anchor="middle" font-size="10" fill="#555">Outputs: Markdown protocol,</text>
      <text x="122" y="234" text-anchor="middle" font-size="10" fill="#555">limitations text, decision log</text>
    </g>

    <!-- Phase 2: Cohort -->
    <g transform="translate(330,430)">
      <rect width="245" height="415" rx="4" fill="#F4F8EC" stroke="#5C7C2C"/>
      <text x="122" y="22" text-anchor="middle" font-size="13" font-weight="700" fill="#3F5A1F">PHASE 2 &#8226; COHORT</text>
      <text x="122" y="38" text-anchor="middle" font-size="10" font-style="italic" fill="#555">Construction and balance</text>

      <g transform="translate(12,55)">
        <rect width="220" height="50" rx="3" fill="#FFFFFF" stroke="#5C7C2C"/>
        <text x="110" y="20" text-anchor="middle" font-size="11" font-weight="700" fill="#1A1A1A">PSM Table Generator</text>
        <text x="110" y="36" text-anchor="middle" font-size="9.5" fill="#555">Journal Table 1, before/after PSM</text>
      </g>

      <g transform="translate(12,115)">
        <rect width="220" height="50" rx="3" fill="#FFFFFF" stroke="#5C7C2C"/>
        <text x="110" y="20" text-anchor="middle" font-size="11" font-weight="700" fill="#1A1A1A">Love Plot Generator</text>
        <text x="110" y="36" text-anchor="middle" font-size="9.5" fill="#555">SMD visualization, balance metrics</text>
      </g>

      <text x="122" y="220" text-anchor="middle" font-size="10" fill="#555">Outputs: Table 1 DOCX,</text>
      <text x="122" y="234" text-anchor="middle" font-size="10" fill="#555">Love plot, balance diagnostics</text>
    </g>

    <!-- Phase 3: Outcomes -->
    <g transform="translate(590,430)">
      <rect width="245" height="415" rx="4" fill="#F4F8EC" stroke="#5C7C2C"/>
      <text x="122" y="22" text-anchor="middle" font-size="13" font-weight="700" fill="#3F5A1F">PHASE 3 &#8226; OUTCOMES</text>
      <text x="122" y="38" text-anchor="middle" font-size="10" font-style="italic" fill="#555">Estimation and presentation</text>

      <g transform="translate(12,55)">
        <rect width="220" height="46" rx="3" fill="#FFFFFF" stroke="#5C7C2C"/>
        <text x="110" y="20" text-anchor="middle" font-size="11" font-weight="700" fill="#1A1A1A">Outcomes Table Generator</text>
        <text x="110" y="35" text-anchor="middle" font-size="9.5" fill="#555">Table 2 from MOA + KM exports</text>
      </g>

      <g transform="translate(12,111)">
        <rect width="220" height="46" rx="3" fill="#FFFFFF" stroke="#5C7C2C"/>
        <text x="110" y="20" text-anchor="middle" font-size="11" font-weight="700" fill="#1A1A1A">Forest Plot Generator</text>
        <text x="110" y="35" text-anchor="middle" font-size="9.5" fill="#555">RR / OR / HR with 95% CI</text>
      </g>

      <g transform="translate(12,167)">
        <rect width="220" height="46" rx="3" fill="#FFFFFF" stroke="#5C7C2C"/>
        <text x="110" y="20" text-anchor="middle" font-size="11" font-weight="700" fill="#1A1A1A">Two-Cohort Bar Graphs</text>
        <text x="110" y="35" text-anchor="middle" font-size="9.5" fill="#555">Absolute risks side-by-side</text>
      </g>

      <g transform="translate(12,223)">
        <rect width="220" height="46" rx="3" fill="#FFFFFF" stroke="#5C7C2C"/>
        <text x="110" y="20" text-anchor="middle" font-size="11" font-weight="700" fill="#1A1A1A">Kaplan-Meier Curve Maker</text>
        <text x="110" y="35" text-anchor="middle" font-size="9.5" fill="#555">Publication survival curves</text>
      </g>

      <text x="122" y="305" text-anchor="middle" font-size="10" fill="#555">Outputs: Tables 1-2, forest,</text>
      <text x="122" y="319" text-anchor="middle" font-size="10" fill="#555">bar, KM figures (PNG + SVG)</text>
    </g>

    <!-- Phase 4: Rigor -->
    <g transform="translate(850,430)">
      <rect width="280" height="415" rx="4" fill="#F4F8EC" stroke="#5C7C2C"/>
      <text x="140" y="22" text-anchor="middle" font-size="13" font-weight="700" fill="#3F5A1F">PHASE 4 &#8226; RIGOR &amp; REPORTING</text>
      <text x="140" y="38" text-anchor="middle" font-size="10" font-style="italic" fill="#555">Stress tests and submission</text>

      <g transform="translate(12,55)">
        <rect width="256" height="40" rx="3" fill="#FFFFFF" stroke="#5C7C2C"/>
        <text x="128" y="17" text-anchor="middle" font-size="11" font-weight="700" fill="#1A1A1A">Power, E-value, NNT/NNH</text>
        <text x="128" y="32" text-anchor="middle" font-size="9.5" fill="#555">Sensitivity to unmeasured confounding</text>
      </g>

      <g transform="translate(12,105)">
        <rect width="256" height="40" rx="3" fill="#FFFFFF" stroke="#5C7C2C"/>
        <text x="128" y="17" text-anchor="middle" font-size="11" font-weight="700" fill="#1A1A1A">Effect Size Calculator</text>
        <text x="128" y="32" text-anchor="middle" font-size="9.5" fill="#555">Standardized effect translations</text>
      </g>

      <g transform="translate(12,155)">
        <rect width="256" height="40" rx="3" fill="#FFFFFF" stroke="#5C7C2C"/>
        <text x="128" y="17" text-anchor="middle" font-size="11" font-weight="700" fill="#1A1A1A">Multiple Comparisons</text>
        <text x="128" y="32" text-anchor="middle" font-size="9.5" fill="#555">Bonferroni, Holm, BH, BY</text>
      </g>

      <g transform="translate(12,205)">
        <rect width="256" height="50" rx="3" fill="#FFFFFF" stroke="#5C7C2C"/>
        <text x="128" y="18" text-anchor="middle" font-size="11" font-weight="700" fill="#1A1A1A">KM Diagnostics</text>
        <text x="128" y="32" text-anchor="middle" font-size="9.5" fill="#555">log-log plot, PH numerical test</text>
        <text x="128" y="46" text-anchor="middle" font-size="8.5" font-style="italic" fill="#5C7C2C">NEW (tool B)</text>
      </g>

      <g transform="translate(12,265)">
        <rect width="256" height="50" rx="3" fill="#FFFFFF" stroke="#5C7C2C"/>
        <text x="128" y="18" text-anchor="middle" font-size="11" font-weight="700" fill="#1A1A1A">STROBE + RECORD Checklist</text>
        <text x="128" y="32" text-anchor="middle" font-size="9.5" fill="#555">Routinely-collected health data standard</text>
        <text x="128" y="46" text-anchor="middle" font-size="8.5" font-style="italic" fill="#5C7C2C">NEW (tool G)</text>
      </g>

      <text x="140" y="345" text-anchor="middle" font-size="10" fill="#555">Outputs: adjusted p-values, sensitivity</text>
      <text x="140" y="359" text-anchor="middle" font-size="10" fill="#555">tables, reporting checklist</text>
    </g>
  </g>

  <!-- Bottom layer: Manuscript artifacts -->
  <g stroke="#5C7C2C" stroke-width="1.5" fill="none">
    <line x1="600" y1="865" x2="600" y2="895" marker-end="url(#arr3)"/>
  </g>

  <g>
    <rect x="50" y="905" width="1100" height="70" rx="6" fill="#FFFFFF" stroke="#3D3D3D" stroke-width="1.5"/>
    <text x="70" y="930" font-size="12" font-weight="700" fill="#3D3D3D" letter-spacing="1.5">LAYER 4 &#8226; MANUSCRIPT ARTIFACTS</text>
    <text x="600" y="955" text-anchor="middle" font-size="12" fill="#1A1A1A">
      Tables 1-2 (DOCX) &#8226; Forest / KM / Bar figures (PNG + SVG) &#8226; Pre-analysis plan (MD) &#8226; STROBE+RECORD checklist (CSV) &#8226; Methods text blocks
    </text>
  </g>
</svg>
