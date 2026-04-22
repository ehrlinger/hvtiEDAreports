"""
summary.py — Summary statistics table for the EDA report.

Produces a formatted HTML table via great_tables (>= 0.14).
Used in the "Data Summary" section of eda_report.qmd.
"""

from __future__ import annotations

import pandas as pd

from eda.classify import ClassifiedDataset


def summary_table(classified: ClassifiedDataset):
    """Build a formatted summary statistics table.

    Includes all variables (continuous, categorical, logical, suppressed).
    For each variable: type, n, n_missing, pct_missing, and type-specific
    statistics (mean/SD/median/IQR for continuous; mode/n_levels for categorical).

    Returns a great_tables GT object suitable for embedding in a Quarto HTML report.

    TODO: implement
    - Compute per-variable statistics from classified.df.
    - Build a pandas DataFrame with one row per variable.
    - Render with great_tables.GT(), applying the HVI color scheme.
    - Fallback: return a pandas Styler if great_tables is unavailable.
    """
    raise NotImplementedError


def _variable_stats(series: pd.Series, var_type: str) -> dict:
    """Compute summary statistics for a single variable.

    Parameters
    ----------
    series:
        Column data.
    var_type:
        One of 'continuous', 'categorical', 'logical'.

    Returns
    -------
    dict with keys appropriate to var_type.

    TODO: implement
    """
    raise NotImplementedError
