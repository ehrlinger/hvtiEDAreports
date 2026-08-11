"""
classify.py — Variable classification engine.

Ports the xportEDA classification rules to Python.  All thresholds are
named constants at module level so they can be overridden via CLI params
or the Quarto params block without touching the logic.

Classification rules (applied in order)
----------------------------------------
1. <= LOGICAL_MAX_UNIQUE unique non-null values  →  logical
2. object / string / bool / Categorical dtype    →  categorical
   If unique levels > CAT_SUPPRESS_LEVELS: suppress_figure = True
3. Numeric with unique count in
   (LOGICAL_MAX_UNIQUE, CAT_MAX_UNIQUE)          →  categorical
4. All remaining numeric                         →  continuous

Time-axis detection
-------------------
Column names are searched (case-insensitive) against TIME_KEYWORDS in
priority order.  First match becomes x_axis_var.  Falls back to the
first continuous variable.  Can be overridden by the caller.

Reference: github.com/ehrlinger/xportEDA
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


# ---------------------------------------------------------------------------
# Thresholds — override via CLI / Quarto params
# ---------------------------------------------------------------------------

LOGICAL_MAX_UNIQUE: int = 2
"""Columns with <= this many unique non-null values are classified as logical."""

CAT_MAX_UNIQUE: int = 10
"""Numeric columns with unique count in (LOGICAL_MAX_UNIQUE, CAT_MAX_UNIQUE)
are classified as categorical."""

CAT_SUPPRESS_LEVELS: int = 20
"""Categorical columns with > this many unique levels get suppress_figure=True.
They still appear in the summary table."""

TIME_KEYWORDS: list[str] = [
    "procdt",
    "opdt",
    "surgdt",  # procedure / surgery date — highest priority
    "date",
    "dt",  # generic date
    "time",  # generic time
    "visit",
    "day",
    "month",
    "year",  # temporal markers
]
"""Column name substrings searched in priority order for x-axis auto-detection.
Add any CCF-standard date/time column name patterns discovered in the
Azure DevOps delivery repo to this list (see spec §4.5)."""


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class ClassifiedDataset:
    """Output of :func:`classify_dataset`.

    Attributes
    ----------
    df:
        The input DataFrame (unchanged).
    continuous:
        Column names classified as continuous numeric.
    categorical:
        Column names classified as categorical (includes logical).
    logical:
        Subset of ``categorical`` with <= LOGICAL_MAX_UNIQUE unique values.
    suppressed:
        Categorical columns with > CAT_SUPPRESS_LEVELS unique levels.
        Classified but excluded from panel figures; present in summary.
    x_axis_var:
        Column used as the x-axis for continuous scatter plots.
        Auto-detected from TIME_KEYWORDS or overridden by caller.
    column_labels:
        Mapping of column name → SAS variable label (empty for non-SAS input).
    """

    df: pd.DataFrame
    continuous: list[str] = field(default_factory=list)
    categorical: list[str] = field(default_factory=list)
    logical: list[str] = field(default_factory=list)
    suppressed: list[str] = field(default_factory=list)
    x_axis_var: str = ""
    column_labels: dict[str, str] = field(default_factory=dict)

    # Convenience properties

    @property
    def n_continuous(self) -> int:
        return len(self.continuous)

    @property
    def n_categorical(self) -> int:
        return len(self.categorical)

    @property
    def n_logical(self) -> int:
        return len(self.logical)

    @property
    def n_suppressed(self) -> int:
        return len(self.suppressed)

    @property
    def plottable_categorical(self) -> list[str]:
        """Categorical columns that have a panel figure (not suppressed)."""
        return [c for c in self.categorical if c not in self.suppressed]

    def variable_type(self, col: str) -> str:
        """Return the classification label for *col* as a string."""
        if col in self.logical:
            return "logical"
        if col in self.suppressed:
            return "categorical (suppressed)"
        if col in self.categorical:
            return "categorical"
        if col in self.continuous:
            return "continuous"
        return "unknown"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def classify_dataset(
    df: pd.DataFrame,
    column_labels: dict[str, str] | None = None,
    x_axis_var: str | None = None,
    cat_unique_max: int = CAT_MAX_UNIQUE,
    suppress_levels_above: int = CAT_SUPPRESS_LEVELS,
    logical_max_unique: int = LOGICAL_MAX_UNIQUE,
) -> ClassifiedDataset:
    """Classify every column in *df* and detect the time axis.

    Parameters
    ----------
    df:
        Input DataFrame.  Column names must already be strings.
    column_labels:
        SAS variable labels from loader metadata.  Pass ``None`` or ``{}``
        for non-SAS input.
    x_axis_var:
        Override auto-detection and force this column as the x-axis.
    cat_unique_max:
        Unique-value threshold separating categorical from continuous.
    suppress_levels_above:
        Categorical columns with more levels than this are suppressed.
    logical_max_unique:
        Unique-value threshold for logical classification.

    Returns
    -------
    ClassifiedDataset
    """

    if column_labels is None:
        column_labels = {}

    continuous: list[str] = []
    categorical: list[str] = []
    logical: list[str] = []
    suppressed: list[str] = []

    for col in df.columns:
        series = df[col]
        # nunique() drops NaNs by default → exactly the "unique non-null" count
        n_unique = series.nunique()
        dtype = series.dtype

        # Rule 1: logical (bool dtype or <= logical_max_unique unique values)
        # Uses dtype.kind == "b" instead of pd.api.types.is_bool_dtype
        if dtype.kind == "b" or n_unique <= logical_max_unique:
            logical.append(col)
            categorical.append(col)
        # Rule 2: object / string / Categorical dtype
        # Uses dtype.kind == "O" (covers object + string) + explicit isinstance for CategoricalDtype
        # (replaces pd.api.types.is_object_dtype / is_string_dtype / is_categorical_dtype)
        elif dtype.kind == "O" or isinstance(dtype, pd.CategoricalDtype):
            categorical.append(col)
            if n_unique > suppress_levels_above:
                suppressed.append(col)
        # Rules 3+4: numeric
        # Uses dtype.kind in ("i", "f", "u", "c") instead of pd.api.types.is_numeric_dtype
        elif dtype.kind in ("i", "f", "u", "c"):
            if logical_max_unique < n_unique <= cat_unique_max:
                # Rule 3
                categorical.append(col)
                if n_unique > suppress_levels_above:
                    suppressed.append(col)
            else:
                # Rule 4
                continuous.append(col)
        else:
            # Fallback for other dtypes (datetime64, etc.) — treat as categorical
            categorical.append(col)
            if n_unique > suppress_levels_above:
                suppressed.append(col)

    # Time-axis detection (unless caller overrode it)
    if x_axis_var is None:
        x_axis_var = _detect_time_axis(continuous)

    return ClassifiedDataset(
        df=df,
        continuous=continuous,
        categorical=categorical,
        logical=logical,
        suppressed=suppressed,
        x_axis_var=x_axis_var,
        column_labels=column_labels,
    )


def _detect_time_axis(
    continuous: list[str],
    keywords: list[str] = TIME_KEYWORDS,
) -> str:
    """Return the best time-axis column from *continuous*.

    Searches column names (case-insensitive) against *keywords* in order.
    Falls back to ``continuous[0]`` if no keyword matches.
    Returns an empty string if *continuous* is empty.

    Parameters
    ----------
    continuous:
        List of continuous column names to search.
    keywords:
        Ordered list of substrings to match against column names.
    """
    if not continuous:
        return ""
    for kw in keywords:
        kwl = kw.lower()
        for col in continuous:
            if kwl in col.lower():
                return col
    # No keyword match → first continuous variable
    return continuous[0]