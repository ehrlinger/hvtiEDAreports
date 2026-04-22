# Dataset EDA Report Tool — Project Specification v2.0

| | |
|---|---|
| **Version** | 2.0 |
| **Date** | April 2026 |
| **Prepared by** | John Ehrlinger, Senior Statistician · CORR / CCF Heart & Vascular Institute |
| **Assigned to** | Junior Data Scientist A · Junior Data Scientist B |
| **Reference repos** | github.com/ehrlinger/xportEDA · github.com/ehrlinger/hvtiPlotR |
| **GitHub repo** | github.com/ehrlinger/hvtiEDAreports |
| **Target platforms** | Windows 10/11 · macOS 13+ |
| **Stack** | Python 3.11+ · Quarto 1.5+ · plotnine · pandas · pyreadstat |
| **Interfaces** | CLI + Desktop Web UI |

---

## 1. Background & Purpose

Our group routinely delivers datasets to clinical collaborators and registry partners. Each delivery should be accompanied by an exploratory data analysis (EDA) report so recipients can immediately see what is in the data — distributions, missingness, outliers — without needing to write code.

Two existing codebases inform this project:

| Source | Language | What it contributes |
|---|---|---|
| [xportEDA](https://github.com/ehrlinger/xportEDA) | R / Shiny | Architecture: variable classification engine, faceted histogram and scatter-plot panels, data summary page, SAS xport file support. |
| [hvtiPlotR `hv_eda()`](https://github.com/ehrlinger/hvtiPlotR) | R / ggplot2 | Canonical per-variable figure style for CORR publications: scatter+LOESS for continuous, stacked bar for categorical, `(Missing)` as an explicit category. CCF HVI manuscript theme is the visual reference. |

The deliverable is a tool that a data scientist runs once per delivery to produce a polished HTML report and delivery package. End users (collaborators, registry partners) receive and open those files — they never interact with Python or the command line.

---

## 2. Goals & Non-Goals

### 2.1 Goals

- Produce a single self-contained HTML EDA report for any delivered dataset.
- Support SAS xport (`.xpt`), SAS binary (`.sas7bdat`), CSV, and pickle input formats.
- Replicate xportEDA's variable classification and panel layout logic in Python.
- Port `hv_eda()` figure style to plotnine: scatter+LOESS for continuous, stacked bar for categorical, missing shown explicitly.
- Apply a manuscript-quality visual theme consistent with CORR/HVI standards.
- Generate a delivery manifest (JSON + Markdown) and SHA-256 checksum file alongside every report.
- Provide two interfaces for the report generator:
  - CLI: `quarto render` with parameters, usable in scripts and pipelines.
  - Desktop Web UI: a local browser-based launcher that non-Python users can operate by double-clicking.
- Allow the Web UI user to download the report and manifest for handoff alongside the dataset.
- Package the tool for one-step installation on Windows and macOS.
- Integrate with the Azure DevOps delivery repo (integration point TBD at kick-off).

### 2.2 Non-Goals

- Interactive Shiny-style widgets. The output is a static HTML report.
- A publicly hosted web service.
- Datasets > ~150 variables (same practical limit as xportEDA).
- End users installing or running Python themselves.

---

## 3. System Overview

The tool has three layers. The data scientist (or an automated pipeline) operates layers 1 and 2. The end user only ever sees layer 3.

| Layer | Component | Description |
|---|---|---|
| 1 — Core | `eda/` Python package | Data loading, variable classification, plotnine figure factories, summary table, delivery manifest. No UI dependency. |
| 1 — Core | `eda_report.qmd` | Quarto document. Imports `eda/` functions, renders all sections. Driven entirely by parameters. |
| 2 — Launcher | CLI (`eda-report`) | Console entry point. Wraps `quarto render` with parameter injection. Usable standalone or in a pipeline. |
| 2 — Launcher | Web UI (`launcher/`) | Local FastAPI + browser UI. User picks a file, sets options, clicks Generate. Calls CLI under the hood. |
| 2 — Package | PyInstaller bundle | Packages Python + Quarto + all deps into a `.exe` (Windows) or `.app` (macOS). No Python install required. |
| 3 — Output | HTML report | Self-contained file delivered alongside the dataset. Opens in any browser. No network required. |
| 3 — Output | Delivery package | `_manifest.json`, `_manifest.md`, `.sha256` — written alongside the HTML report for every render. |

---

## 4. Detailed Technical Specification

### 4.1 Repository Structure

```
hvtiEDAreports/
  eda/                        # Core Python package
    __init__.py
    loader.py                 # Multi-format data ingestion
    classify.py               # Variable classification engine
    plots.py                  # plotnine figure factories (hv_eda port)
    theme.py                  # Manuscript theme constants (HVI reference)
    summary.py                # Summary statistics table
    delivery.py               # Manifest and checksum generation
  launcher/                   # Desktop web UI
    app.py                    # FastAPI application
    templates/index.html      # Single-page launcher UI
    static/                   # CSS / JS
  cli.py                      # CLI entry point (eda-report command)
  eda_report.qmd              # Quarto report template
  tests/
    conftest.py               # Shared synthetic fixtures
    test_classify.py
    test_loader.py
    test_plots.py
  installer/
    build_windows.spec        # PyInstaller spec (Windows)
    build_macos.spec          # PyInstaller spec (macOS)
    build.sh                  # Build script
  docs/
    spec_v2.0.md              # This document
  data/                       # Sample / test data (de-identified or synthetic only)
  requirements.txt
  environment.yml
  pyproject.toml
  README.md
```

### 4.2 Dependencies

| Package | Min version | Purpose |
|---|---|---|
| quarto | 1.5 | Report rendering (installed separately; bundled in packaged build) |
| pandas | 2.0 | Data manipulation |
| numpy | 1.26 | Numerical operations |
| plotnine | 0.13 | Grammar-of-graphics plotting (ggplot2 equivalent) |
| mizani | 0.11 | plotnine scales / formatting dependency |
| pyreadstat | 1.2 | SAS `.xpt` and `.sas7bdat` ingestion |
| great_tables | 0.14 | Formatted HTML summary table |
| fastapi | 0.110 | Local web UI server |
| uvicorn | 0.29 | ASGI server for FastAPI |
| jinja2 | 3.1 | HTML template rendering for web UI |
| click | 8.1 | CLI argument parsing |
| pyinstaller | 6.5 | Desktop application packaging |

### 4.3 Data Loading (`loader.py`)

Detect format from file extension and return a pandas DataFrame. Normalize all column names to strings on load.

| Extension | Library | Notes |
|---|---|---|
| `.csv` | `pandas.read_csv()` | Detect encoding; UTF-8 with latin-1 fallback |
| `.xpt` | `pyreadstat.read_xport()` | Preserve variable labels as column metadata |
| `.sas7bdat` | `pyreadstat.read_sas7bdat()` | Preserve variable labels |
| `.pkl` / `.pickle` | `pandas.read_pickle()` | Validate it is a DataFrame |
| `.parquet` | `pandas.read_parquet()` | Nice to have; low effort to add |

Variable labels from SAS files (stored in pyreadstat metadata) should be attached as a `column_labels` dict and used as axis titles in figures where available.

### 4.4 Variable Classification (`classify.py`)

Port the xportEDA classification rules exactly. Expose all thresholds as named constants at the top of the module.

```python
LOGICAL_MAX_UNIQUE   = 2    # <= this many unique non-null values → logical
CAT_MAX_UNIQUE       = 10   # > LOGICAL_MAX_UNIQUE and < this → categorical
CAT_SUPPRESS_LEVELS  = 20   # categorical vars with > this many levels:
                            #   classify but suppress panel figure (still in summary)
```

Classification rules (apply in order):

1. Any column with `<= LOGICAL_MAX_UNIQUE` unique **non-null** values (`dropna=True`) → logical. This includes `bool` dtype columns.
2. Any object / string / pandas `Categorical` dtype column → categorical. If unique levels `> CAT_SUPPRESS_LEVELS`, mark `suppress_figure=True`.
3. Any numeric column with unique count in `(LOGICAL_MAX_UNIQUE, CAT_MAX_UNIQUE)` → categorical.
4. All remaining numeric columns → continuous.

Return a dataclass:

```python
@dataclass
class ClassifiedDataset:
    df:             pd.DataFrame
    continuous:     list[str]
    categorical:    list[str]   # includes logical
    logical:        list[str]
    suppressed:     list[str]   # classified but no figure
    x_axis_var:     str         # auto-detected or user-supplied
    column_labels:  dict[str, str]  # from SAS metadata or empty
```

### 4.5 Time-axis Detection

Search column names (case-insensitive) for these keywords in priority order. First match wins.

```python
TIME_KEYWORDS = [
    'procdt', 'opdt', 'surgdt',       # procedure/surgery date — highest priority
    'date', 'dt',                      # generic date
    'time',                            # generic time
    'visit', 'day', 'month', 'year',   # temporal markers
]
```

If no keyword match, fall back to the first continuous variable. The detected variable is stored in `ClassifiedDataset.x_axis_var` and can be overridden via CLI flag or UI option.

> **Note for team:** John's CORR datasets use `procdt` as the standard time axis. Add any additional CCF-standard variable name patterns discovered in the Azure DevOps repo to this list (see §7, Open Question #4).

### 4.6 Plot Module (`plots.py`) — Porting `hv_eda()`

`hv_eda()` in hvtiPlotR is the canonical reference for per-variable figure style. **DS-B must read the R source at `github.com/ehrlinger/hvtiPlotR/blob/main/R/` before writing the Python equivalent.**

Key `hv_eda()` behaviors to preserve:

1. Continuous variables → scatter plot with LOESS smooth + confidence band.
2. Categorical/logical variables → stacked bar chart with count and proportion.
3. Missing values shown as an explicit `"(Missing)"` category, never silently dropped.
4. Variable label used as axis title when available.

> **plotnine LOESS note:** plotnine's `geom_smooth()` uses statsmodels for LOESS. The correct method keyword is `'lowess'` (not `'loess'`). Confidence bands require statsmodels >= 0.14 and behave differently from ggplot2's default span. Prototype this before committing to the `hv_eda()` visual comparison — manual confidence interval calculation may be needed.

#### 4.6.1 `theme.py` — Manuscript Theme

Define a plotnine theme function matching the hvtiPlotR manuscript aesthetic:

- White background; light horizontal grid lines acceptable; no vertical axis gridlines.
- Calibri or Arial font (CCF publication standard).
- Figure title from variable label, or column name if no label.
- ColorBrewer Set1 palette (or CCF palette if known).
- Default figure size: 6 × 4 inches, 150 dpi minimum.

#### 4.6.2 Panel Figures

| Function | Input variables | Geom | Notes |
|---|---|---|---|
| `categorical_panel()` | categorical + logical | `geom_bar(position='fill')` | Facet by variable; `ncols = max(2, min(4, floor(sqrt(n))))`; height scales with row count |
| `continuous_panel()` | continuous | `geom_point() + geom_smooth()` | X = `x_axis_var`; facet by variable; rug marks at axis floor for missing values |

#### 4.6.3 Single-Variable Figures

`single_var_plot(df, var, classified, theme_fn)` — returns one plotnine ggplot. Dispatches to scatter+LOESS or stacked bar based on classification. This is the direct Python port of `hv_eda()`.

### 4.7 Delivery Package (`delivery.py`)

For every render, three companion files are written to `output_dir` alongside the HTML report:

| File | Format | Description |
|---|---|---|
| `{stem}_manifest.json` | JSON | Machine-readable delivery record |
| `{stem}_manifest.md` | Markdown | Human-readable version |
| `{stem}.sha256` | Text | One-line checksum, POSIX `sha256sum` format |

The `.sha256` file follows the POSIX `sha256sum` convention: `<hex>  <filename>` (two spaces, filename only — no path), so recipients can verify with `sha256sum -c` on Linux/macOS or `certutil -hashfile` on Windows.

**Manifest structure:**

```json
{
  "tool_version": "1.0.0",
  "generated_at": "2026-04-22T14:31:00Z",
  "dataset": {
    "filename": "cabg_2025q1.xpt",
    "sha256": "a3f9...",
    "size_bytes": 2048576,
    "rows": 1242,
    "columns": 47
  },
  "report": {
    "filename": "cabg_2025q1_eda.html",
    "sha256": "b7c1..."
  },
  "variable_summary": {
    "continuous": 18,
    "categorical": 22,
    "logical": 5,
    "suppressed": 2
  },
  "parameters": {
    "x_axis_var": "procdt",
    "cat_unique_max": 10,
    "suppress_levels_above": 20,
    "report_title": "CABG Cohort 2025 Q1"
  }
}
```

**Implementation notes:**

- SHA-256 is computed for both the input dataset and the generated HTML report.
- Use `hashlib.sha256` with streaming reads (64 KB chunks) — do not load the whole file into memory.
- Filenames only — no paths — so the delivery package is portable. The Markdown manifest includes a note: *"Keep all files in the same directory for checksum verification."*

### 4.8 Quarto Report Template (`eda_report.qmd`)

All report parameters must be injectable via the `params` block. The report renders without any editing by the user.

```yaml
---
title: "Exploratory Data Analysis"
format:
  html:
    toc: true
    toc-depth: 3
    code-fold: true
    embed-resources: true     # single file, no external assets
    theme: cosmo              # confirm preferred theme at kick-off
params:
  data_file: "data/sample.csv"
  x_axis_var: null            # null = auto-detect
  report_title: null          # null = derive from filename
  cat_unique_max: 10
  suppress_levels_above: 20
  output_dir: "."
---
```

> **Note:** Use `embed-resources: true` — not `self-contained: true`, which is deprecated in Quarto 1.5+.

Report sections:

1. **Overview** — file name, dimensions, variable counts by type, parameter echo, data quality flags (all-missing columns, near-zero-variance columns).
2. **Categorical & Logical Variables** — `categorical_panel()` figure.
3. **Continuous Variables** — `continuous_panel()` figure.
4. **Variable Detail** — tabbed section, one tab per variable, `single_var_plot()` figure + inline statistics.
5. **Data Summary** — formatted `describe()` table via `great_tables`.

---

## 5. User Interfaces

### 5.1 CLI (`cli.py`)

Install as a console script entry point named `eda-report`. Target user: data scientist running from terminal or calling from a pipeline script.

```bash
# Basic usage
eda-report --data path/to/delivery.xpt

# With options
eda-report --data delivery.xpt \
           --x-axis procdt \
           --title "CABG Cohort 2025 Q1" \
           --output-dir ./reports/

# Help
eda-report --help
```

| Flag | Default | Description |
|---|---|---|
| `--data` / `-d` | (required) | Path to input data file |
| `--x-axis` | auto-detect | Column name to use as x-axis for continuous plots |
| `--title` | filename stem | Report title shown in HTML header |
| `--output-dir` / `-o` | same dir as data file | Directory to write output files |
| `--cat-max` | 10 | Unique-value threshold for categorical classification |
| `--suppress-above` | 20 | Level count above which categorical figures are suppressed |
| `--no-manifest` | False | Skip manifest and checksum generation |
| `--manifest-format` | `both` | `json`, `md`, or `both` |
| `--open` | False | Open the report in the default browser after rendering |
| `--quiet` / `-q` | False | Suppress progress output |

### 5.2 Desktop Web UI (`launcher/`)

Target user: collaborator or analyst who has received the packaged tool but does not use the command line. Runs as a local web server and opens automatically in the user's default browser. No internet connection required.

#### 5.2.1 Technology

- Backend: FastAPI + uvicorn, bound to `127.0.0.1` on a random available port.
- Frontend: Single HTML page (Jinja2 template). Vanilla JS only — no npm build step.
- The launcher starts the server and opens the browser automatically.

> **Architecture note:** Use WebSocket (not `StreamingResponse`) for render log output. `StreamingResponse` does not support the back-and-forth needed for cancel/status signals. Capture Quarto's stdout/stderr with `subprocess.Popen` and stream line-by-line via WebSocket.

#### 5.2.2 UI Requirements

- **File picker:** Browse button opening a native OS file dialog (filtered to `.xpt`, `.sas7bdat`, `.csv`, `.pkl`).
- **Options panel:** X-axis override (text field, pre-filled after file selection), Report title (text field), Output directory (text field or Browse button).
- **Generate button:** Disabled until a file is selected. Shows a spinner while Quarto renders.
- **Status area:** Live log output from the render process streamed to the page via WebSocket.
- **Delivery package section** (appears after successful render):
  - **Open Report** — opens the HTML file in the default browser.
  - **Download Report** — downloads the HTML via FastAPI `/download/{filename}` endpoint.
  - **Download Manifest** — downloads the JSON manifest.
  - Status note showing the checksum filename written to output directory.
- **Error display:** If render fails, show the last 20 lines of stderr in a red-bordered box.

#### 5.2.3 Download Endpoint

`GET /download/{filename}?output_dir=...` — serves files from `output_dir` only. Must include a path traversal guard: reject any `filename` whose resolved path escapes `output_dir`. Use `FileResponse` with `media_type='application/octet-stream'`.

### 5.3 Launcher Entry Points

| Platform | Packaged artifact | How user launches |
|---|---|---|
| Windows | `EDA Report.exe` | Double-click; browser opens automatically |
| macOS | `EDA Report.app` | Double-click from Applications or Finder |
| Developer | `python launcher/app.py` | Direct run; same behavior as packaged version |
| Pipeline / CI | `eda-report --data ...` | CLI; no browser; exit code 0 on success |

---

## 6. Packaging & Installation

### 6.1 PyInstaller Build

The packaged build must include Python, all pip dependencies, and a bundled Quarto binary. Quarto provides standalone binaries for Windows and macOS.

1. Download the platform Quarto binary and extract to `installer/quarto/`.
2. In the PyInstaller spec, add: `datas=[('installer/quarto', 'quarto')]`.
3. In `cli.py`, detect `sys._MEIPASS` (PyInstaller bundle) and set `QUARTO_PATH` to the bundled binary.
4. Build: `pyinstaller installer/build_windows.spec --clean --noconfirm`.
5. Test the resulting `.exe` on a clean Windows VM with no Python installed. This is the only valid acceptance test.
6. Repeat for macOS. Sign the `.app` with `codesign` if distributing outside the team (see §10, Open Question #7).

> **Bundle size note:** The Quarto standalone binary is ~100 MB; pandas/numpy/plotnine add another 100–150 MB. Expect the final bundle to be 300–400 MB. Flag if this is a problem for distribution.

### 6.2 Developer Installation

```bash
git clone https://github.com/ehrlinger/hvtiEDAreports.git
cd hvtiEDAreports

conda env create -f environment.yml
conda activate eda-report

# Install Quarto separately — https://quarto.org/docs/get-started/
# Verify: quarto --version  (should be >= 1.5)

pip install -e .

# Verify
eda-report --data data/sample.csv --open
```

---

## 7. Azure DevOps Integration

This section is intentionally incomplete. Review the Azure DevOps repo at kick-off and update before starting Phase 3.

Questions to resolve at kick-off:

1. Where in the delivery workflow does EDA report generation happen — post-delivery, CI pipeline, or manual step?
2. What is the naming convention for delivered datasets? (Determines default report title and output filename.)
3. Should the HTML report and manifest be committed back to the DevOps repo alongside the data, or delivered separately?
4. Are there additional CCF-standard variable name conventions in the existing codebase to add to `TIME_KEYWORDS`?
5. Does the DevOps repo already have a Python environment the `eda` package should be added to, or does this live in its own repo?

---

## 8. Phased Delivery Plan

| Phase | Deliverables | Owner | Days |
|---|---|---|---|
| 1 — Setup | Repo initialized; `environment.yml` + `requirements.txt` committed; skeleton `eda_report.qmd` renders empty; sample test data in `data/`; Azure DevOps review complete; `TIME_KEYWORDS` updated. | Both | 1–3 |
| 2 — Core package | `loader.py` (all formats); `classify.py` + `test_classify.py` (>90% coverage); time-axis detection; `ClassifiedDataset` dataclass; `delivery.py` (manifest + checksum); `test_loader.py`. | DS-A | 3–6 |
| 3 — Plots | `hv_eda()` R source reviewed and documented; `single_var_plot()` implemented and visually compared to R output; `categorical_panel()` and `continuous_panel()`; `theme.py`; `test_plots.py`. | DS-B | 4–8 |
| 4 — Quarto report | All `eda_report.qmd` sections wired; params fully functional; HTML renders cleanly; `embed-resources: true` verified. | Both | 7–10 |
| 5 — CLI | `cli.py` with all flags; `eda-report` entry point; `--open` flag; `--no-manifest` flag; exit codes; integration test. | DS-A | 9–11 |
| 6 — Web UI | FastAPI app; browser launcher; file picker; options panel; WebSocket log streaming; Open Report / Download Report / Download Manifest buttons; error display. | DS-B | 9–12 |
| 7 — Packaging | PyInstaller specs for Windows and macOS; bundled Quarto binary; tested on clean VMs; README install section. | Both | 12–15 |
| 8 — Review | Side-by-side comparison with xportEDA live demo and `hv_eda()` output; all acceptance criteria signed off; handoff to John. | Both | 15–17 |

---

## 9. Acceptance Criteria

| # | Criterion | Owner | Priority |
|---|---|---|---|
| 1 | `eda-report --data sample.xpt` produces a valid, self-contained HTML report with no errors. | Both | High |
| 2 | Variable classification matches xportEDA output on the same dataset (verified against shinyapps.io demo). | DS-A | High |
| 3 | Continuous figures use scatter+LOESS; categorical use stacked bar; missing shown as `(Missing)` — matching `hv_eda()` visual style. | DS-B | High |
| 4 | Faceted panels present for all eligible variables; suppressed variables excluded from panels but present in summary. | DS-B | High |
| 5 | Quarto params fully functional: title, x-axis, output-dir all overridable from CLI. | DS-A | High |
| 6 | Web UI launches in default browser on Windows and macOS with no command-line interaction. | DS-B | High |
| 7 | Packaged `.exe` runs on a clean Windows machine with no Python installed and produces a correct report. | Both | High |
| 8 | Packaged `.app` runs on a clean macOS machine with no Python installed and produces a correct report. | Both | High |
| 9 | SAS variable labels used as axis titles where available. | DS-A | Medium |
| 10 | Data summary table present and readable in HTML output. | DS-A | Medium |
| 11 | `pytest tests/` passes with >= 90% coverage on `classify.py` and `loader.py`. | DS-A | Medium |
| 12 | README allows a new team member to install and run from source in under 10 minutes. | DS-B | Medium |
| 13 | `--open` flag opens the rendered report in the default browser. | DS-A | Low |
| 14 | Azure DevOps integration point documented (even if not yet implemented). | Both | TBD |
| 15 | `delivery.py` generates `_manifest.json`, `_manifest.md`, and `.sha256` alongside the HTML report for every render. | DS-A | High |
| 16 | SHA-256 in the `.sha256` file verifies against the dataset with `sha256sum -c` on Linux/macOS. | DS-A | High |
| 17 | Web UI Download Report and Download Manifest buttons deliver files to the browser's download folder. | DS-B | Medium |
| 18 | `--no-manifest` suppresses manifest and checksum generation without error. | DS-A | Low |

---

## 10. Open Questions for Kick-off

| # | Question | Who resolves |
|---|---|---|
| 1 | Azure DevOps repo contents: where does EDA report generation fit in the delivery workflow? | John + team |
| 2 | Additional CCF-standard time/date column name conventions to add to `TIME_KEYWORDS`? | John |
| 3 | Preferred HTML theme (cosmo, flatly, lux, etc.)? | John |
| 4 | Sample `.xpt` file for testing — must be de-identified or synthetic. | John |
| 5 | Should output reports and manifests be committed back to the DevOps repo, or only delivered to the collaborator? | John |
| 6 | macOS code-signing: Apple Developer certificate available, or manual Gatekeeper bypass? | DS-B + IT |

---

## Appendix: Implementation Notes for the Team

These notes summarise key technical decisions made during spec review. Read before starting each phase.

**`embed-resources: true` (not `self-contained`)** — `self-contained: true` is deprecated in Quarto 1.5+. Use `embed-resources: true` in `eda_report.qmd`. Using the old key may silently produce a non-self-contained report.

**plotnine LOESS** — `geom_smooth(method='lowess')` is the correct keyword (not `'loess'`). Requires statsmodels >= 0.14 for confidence bands. Prototype against the R `hv_eda()` output before finalising Phase 3.

**WebSocket, not StreamingResponse** — The Web UI must use WebSocket for render log streaming. `StreamingResponse` does not support bidirectional communication needed for status/cancel. See `launcher/app.py` for the stub.

**`great_tables >= 0.14`** — The API changed significantly between 0.5 and 0.14. Pin to 0.14+ and do not implement a pandas Styler fallback.

**`bool` dtype in classification** — `bool` columns have exactly 2 unique values and correctly classify as logical under Rule 1, but only if `nunique()` is called with `dropna=True`. Explicitly use `dropna=True` everywhere unique counts are computed.

**SHA-256 streaming** — Use 64 KB read chunks (`BUFFER_SIZE = 65536`) for all checksum computation. Datasets can be large; do not load the full file into memory.

**Manifest uses filename only** — The manifest and `.sha256` file reference the dataset by filename only, not absolute path. The delivery package is meant to travel with the dataset. The Markdown manifest includes a note to keep all files in the same directory.

**macOS Gatekeeper** — Without an Apple Developer certificate, macOS will block the `.app` on first run. Users must right-click → Open to bypass. Document this clearly in the README for non-technical collaborators.

---

*End of Specification · v2.0 · April 2026 · CORR / CCF Heart & Vascular Institute*
