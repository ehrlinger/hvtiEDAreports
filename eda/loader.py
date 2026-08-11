"""
loader.py — Multi-format data ingestion.

Detects format from file extension and returns a pandas DataFrame.
All column names are normalized to strings on load.
Variable labels from SAS files are attached as a ``column_labels`` dict
and passed through to ClassifiedDataset for use as axis titles.

Supported formats
-----------------
.csv          pandas.read_csv()       UTF-8 with latin-1 fallback
.xpt          pyreadstat.read_xport() Preserves SAS variable labels
.sas7bdat     pyreadstat.read_sas7bdat() Preserves SAS variable labels
.pkl / .pickle pandas.read_pickle()   Must be a DataFrame
.parquet      pandas.read_parquet()   Optional; low-effort addition
"""

from __future__ import annotations

import pathlib
from typing import Any

import pandas as pd
import pyreadstat


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_dataset(path: str | pathlib.Path) -> tuple[pd.DataFrame, dict[str, str]]:
    """Load a dataset from *path* and return ``(df, column_labels)``.

    Parameters
    ----------
    path:
        Path to the data file.  Extension determines the reader.

    Returns
    -------
    df:
        DataFrame with all column names coerced to ``str``.
    column_labels:
        Mapping of column name → SAS variable label.  Empty dict for
        non-SAS formats.

    Raises
    ------
    ValueError
        If the file extension is not supported.
    TypeError
        If a pickle file does not contain a DataFrame.
    FileNotFoundError
        If *path* does not exist.
    """
    path = pathlib.Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")

    suffix = path.suffix.lower()

    dispatch: dict[str, Any] = {
        ".csv": _load_csv,
        ".xpt": _load_xpt,
        ".sas7bdat": _load_sas7bdat,
        ".pkl": _load_pickle,
        ".pickle": _load_pickle,
        ".parquet": _load_parquet,
    }

    loader_fn = dispatch.get(suffix)
    if loader_fn is None:
        raise ValueError(f"Unsupported file format: '{suffix}'. Supported: {', '.join(dispatch)}")

    df, column_labels = loader_fn(path)
    df.columns = [str(c) for c in df.columns]
    return df, column_labels


# ---------------------------------------------------------------------------
# Format-specific readers (private)
# ---------------------------------------------------------------------------


def _load_csv(path: pathlib.Path) -> tuple[pd.DataFrame, dict[str, str]]:
    """Load CSV with UTF-8 / latin-1 encoding fallback."""
    # Attempt UTF-8; fall back to latin-1 on UnicodeDecodeError
    try:
        df = pd.read_csv(path, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="latin-1")
    return df, {}


def _load_xpt(path: pathlib.Path) -> tuple[pd.DataFrame, dict[str, str]]:
    """Load SAS xport (.xpt) via pyreadstat, preserving variable labels."""
    df, meta = pyreadstat.read_xport(str(path))
    # column_names_to_labels is exactly what we want: dict[column_name → label]
    column_labels = meta.column_names_to_labels or {}
    return df, column_labels


def _load_sas7bdat(path: pathlib.Path) -> tuple[pd.DataFrame, dict[str, str]]:
    """Load SAS binary (.sas7bdat) via pyreadstat, preserving variable labels."""
    df, meta = pyreadstat.read_sas7bdat(str(path))
    column_labels = meta.column_names_to_labels or {}
    return df, column_labels


def _load_pickle(path: pathlib.Path) -> tuple[pd.DataFrame, dict[str, str]]:
    """Load a pickled DataFrame. Raises TypeError if contents are not a DataFrame."""
    df = pd.read_pickle(path)
    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            f"Pickle file does not contain a DataFrame. "
            f"Got {type(df).__name__} instead."
        )
    return df, {}


def _load_parquet(path: pathlib.Path) -> tuple[pd.DataFrame, dict[str, str]]:
    """Load a Parquet file via pandas."""
    df = pd.read_parquet(path)
    return df, {}
