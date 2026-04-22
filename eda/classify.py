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
    "procdt", "opdt", "surgdt",       # procedure / surgery date — highest priority
    "date", "dt",                      # generic date
    "time",                            # generic time
    "visit", "day", "month", "year",   # temporal markers
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
    # TODO: implement
    # Steps:
    #   1. For each column, count unique non-null values (dropna=True).
    #   2. Apply rules in order (see module docstring).
    #      - bool dtype counts as logical regardless of unique count.
    #   3. Detect x_axis_var via _detect_time_axis() unless overridden.
    #   4. Populate and return ClassifiedDataset.
    raise NotImplementedError


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
    # TODO: implement
    raise NotImplementedError
