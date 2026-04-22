"""
plots.py — plotnine figure factories.

Python port of hv_eda() from hvtiPlotR.

IMPORTANT: Read the R source before implementing this module.
  github.com/ehrlinger/hvtiPlotR/blob/main/R/

Key behaviors to preserve (from hv_eda())
------------------------------------------
1. Continuous variables  → scatter plot with LOESS smooth + confidence band.
   X-axis = ClassifiedDataset.x_axis_var
2. Categorical / logical → stacked bar chart (count + proportion).
3. Missing values shown as an explicit "(Missing)" category — never dropped.
   See theme.MISSING_CATEGORY_LABEL.
4. Variable label used as axis title when available in column_labels.

Notes on plotnine LOESS
-----------------------
plotnine's geom_smooth() uses statsmodels for LOESS.  The correct method
keyword is 'lowess' (not 'loess').  Confidence bands require statsmodels >= 0.14.
Prototype before committing to compare output with the R reference.
"""

from __future__ import annotations

import math

import pandas as pd

from eda.classify import ClassifiedDataset
from eda.theme import hvi_theme, MISSING_CATEGORY_LABEL


# ---------------------------------------------------------------------------
# Panel figures (multi-variable faceted)
# ---------------------------------------------------------------------------

def categorical_panel(classified: ClassifiedDataset):
    """Stacked bar panel for all plottable categorical and logical variables.

    Faceted by variable.  ncols = max(2, min(4, floor(sqrt(n)))).
    Height scales with row count.

    Parameters
    ----------
    classified:
        Output of classify_dataset().

    Returns
    -------
    plotnine.ggplot

    TODO: implement
    - Melt plottable_categorical columns into long form.
    - Replace NaN with MISSING_CATEGORY_LABEL before melting.
    - geom_bar(position='fill') faceted by variable name.
    - Apply hvi_theme().
    - Use column_labels for strip titles where available.
    """
    raise NotImplementedError


def continuous_panel(classified: ClassifiedDataset):
    """Scatter + LOESS panel for all continuous variables.

    X-axis = classified.x_axis_var.
    Faceted by variable.  ncols = max(2, min(4, floor(sqrt(n)))).
    Rug marks at axis floor indicate observations with missing values.

    Parameters
    ----------
    classified:
        Output of classify_dataset().

    Returns
    -------
    plotnine.ggplot

    TODO: implement
    - Melt continuous columns (excluding x_axis_var) into long form.
    - geom_point() + geom_smooth(method='lowess') faceted by variable.
    - geom_rug() for rows where the y variable is NaN.
    - Apply hvi_theme().
    - Use column_labels for strip titles where available.
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Single-variable figure — direct port of hv_eda()
# ---------------------------------------------------------------------------

def single_var_plot(
    df: pd.DataFrame,
    var: str,
    classified: ClassifiedDataset,
):
    """Return one plotnine ggplot for *var*, dispatching on classification.

    - Continuous → scatter + LOESS (x = x_axis_var)
    - Categorical / logical → stacked bar
    - Missing shown explicitly as MISSING_CATEGORY_LABEL

    Parameters
    ----------
    df:
        Source DataFrame.
    var:
        Column name to plot.
    classified:
        ClassifiedDataset for context (x_axis_var, column_labels, etc.)

    Returns
    -------
    plotnine.ggplot

    TODO: implement — dispatch to _continuous_plot() or _categorical_plot()
    based on classified.variable_type(var).
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Helpers (private)
# ---------------------------------------------------------------------------

def _ncols(n: int) -> int:
    """Compute panel column count: max(2, min(4, floor(sqrt(n))))."""
    if n <= 0:
        return 1
    return max(2, min(4, math.floor(math.sqrt(n))))


def _axis_title(var: str, column_labels: dict[str, str]) -> str:
    """Return variable label if available, else the column name."""
    return column_labels.get(var, var)


def _add_missing_category(series: pd.Series) -> pd.Series:
    """Replace NaN with MISSING_CATEGORY_LABEL, cast to string Categorical."""
    return series.fillna(MISSING_CATEGORY_LABEL).astype(str)


def _continuous_plot(df: pd.DataFrame, var: str, classified: ClassifiedDataset):
    """Scatter + LOESS for a single continuous variable.  TODO: implement."""
    raise NotImplementedError


def _categorical_plot(df: pd.DataFrame, var: str, classified: ClassifiedDataset):
    """Stacked bar for a single categorical / logical variable.  TODO: implement."""
    raise NotImplementedError
