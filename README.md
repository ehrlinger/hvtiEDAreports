# hvtiEDAreports

**Dataset EDA Report Tool** — CORR / CCF Heart & Vascular Institute

Generates a polished, self-contained HTML exploratory data analysis (EDA) report
for any dataset delivered to clinical collaborators or registry partners. Recipients
open a single HTML file in any browser — no Python, no setup required.

[![CI](https://github.com/ehrlinger/hvtiEDAreports/actions/workflows/ci.yml/badge.svg)](https://github.com/ehrlinger/hvtiEDAreports/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Quarto 1.5+](https://img.shields.io/badge/quarto-1.5+-blue.svg)](https://quarto.org/)

---

## Related repositories

| Repo | Language | Role |
|---|---|---|
| [xportEDA](https://github.com/ehrlinger/xportEDA) | R / Shiny | Architecture reference: variable classification, panel layout, SAS xport support |
| [hvtiPlotR](https://github.com/ehrlinger/hvtiPlotR) | R / ggplot2 | Figure style reference: `hv_eda()` per-variable plot canon |

---

## Features

- Supports `.xpt`, `.sas7bdat`, `.csv`, and `.pkl` input formats
- Classifies variables automatically (continuous, categorical, logical)
- Scatter + LOESS figures for continuous variables; stacked bar for categorical
- Missing values shown as an explicit `(Missing)` category — never dropped
- SAS variable labels used as axis titles where available
- Generates a delivery manifest (JSON + Markdown) and SHA-256 checksum alongside every report
- Two interfaces: CLI for pipelines, desktop Web UI for non-Python users
- Packaged as a standalone `.exe` (Windows) or `.app` (macOS) — no Python install required for end users

---

## Quick start (developer)

### Prerequisites

- [Conda](https://docs.conda.io/en/latest/miniconda.html) or [Mamba](https://mamba.readthedocs.io/)
- [Quarto 1.5+](https://quarto.org/docs/get-started/) — install separately and ensure `quarto` is on your `PATH`

### Install

```bash
git clone https://github.com/ehrlinger/hvtiEDAreports.git
cd hvtiEDAreports

conda env create -f environment.yml
conda activate eda-report

pip install -e .
```

### Verify

```bash
eda-report --data data/sample.csv --open
```

---

## Usage

### CLI

```bash
# Minimal — auto-detects x-axis, derives title from filename
eda-report --data path/to/delivery.xpt

# Full options
eda-report --data delivery.xpt \
           --x-axis procdt \
           --title "CABG Cohort 2025 Q1" \
           --output-dir ./reports/ \
           --open

# Skip manifest and checksum (pipeline use)
eda-report --data delivery.xpt --no-manifest
```

| Flag | Default | Description |
|---|---|---|
| `--data` / `-d` | *(required)* | Path to input data file |
| `--x-axis` | auto-detect | Column name for x-axis on continuous plots |
| `--title` | filename stem | Report title shown in HTML header |
| `--output-dir` / `-o` | same dir as data | Directory to write output files |
| `--cat-max` | 10 | Unique-value threshold for categorical classification |
| `--suppress-above` | 20 | Level count above which categorical figures are suppressed |
| `--no-manifest` | False | Skip manifest and checksum generation |
| `--manifest-format` | `both` | `json`, `md`, or `both` |
| `--open` | False | Open report in default browser after rendering |
| `--quiet` / `-q` | False | Suppress progress output |

### Desktop Web UI

Run `EDA Report.exe` (Windows) or `EDA Report.app` (macOS). A browser window opens
automatically. Pick your data file, set options, click **Generate**.

Developer launch:

```bash
python launcher/app.py
```

---

## Output files

For each render, three files are written to `output_dir` alongside the HTML report:

| File | Description |
|---|---|
| `{stem}_eda.html` | Self-contained EDA report |
| `{stem}_manifest.json` | Machine-readable delivery record (dimensions, variable counts, parameters, checksums) |
| `{stem}_manifest.md` | Human-readable version of the manifest |
| `{stem}.sha256` | SHA-256 checksum of the input dataset (`sha256sum -c` compatible) |

> Keep all files in the same directory for checksum verification.

---

## Project structure

```
hvtiEDAreports/
  eda/                  # Core Python package (no UI dependency)
    loader.py           # Multi-format data ingestion
    classify.py         # Variable classification engine
    plots.py            # plotnine figure factories (hv_eda port)
    theme.py            # Manuscript theme (HVI reference)
    summary.py          # Summary statistics table
    delivery.py         # Manifest and checksum generation
  launcher/             # Desktop web UI
    app.py              # FastAPI application
    templates/
      index.html        # Single-page launcher UI
    static/             # CSS / JS
  cli.py                # eda-report CLI entry point
  eda_report.qmd        # Quarto report template
  tests/
    conftest.py
    test_classify.py
    test_loader.py
    test_plots.py
  installer/
    build_windows.spec  # PyInstaller spec (Windows)
    build_macos.spec    # PyInstaller spec (macOS)
    build.sh            # Build script
  data/                 # Sample / test data (de-identified or synthetic only)
  requirements.txt
  environment.yml
  pyproject.toml
```

---

## Development

### Running tests

```bash
pytest tests/ -v --cov=eda --cov-report=term-missing
```

Coverage target: ≥ 90% on `classify.py` and `loader.py`.

### Code style

```bash
ruff check .
ruff format .
```

---

## Building the packaged application

See `installer/build.sh`. Requires PyInstaller and a bundled Quarto binary in
`installer/quarto/`. Tested on clean Windows 10/11 and macOS 13+ VMs with no
Python pre-installed.

```bash
# Windows (run in PowerShell)
pyinstaller installer/build_windows.spec --clean --noconfirm

# macOS
pyinstaller installer/build_macos.spec --clean --noconfirm
```

---

## Specification

Full project specification: `docs/spec_v2.0.md`

---

## Authors

John Ehrlinger — Senior Statistician, CORR / CCF Heart & Vascular Institute

---

## License

MIT
