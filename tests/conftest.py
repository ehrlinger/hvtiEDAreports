"""
conftest.py — Shared pytest fixtures for hvtiEDAreports tests.

Provides synthetic DataFrames that cover all classification cases without
requiring real patient data.  All test data is fully synthetic.
"""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def synthetic_df() -> pd.DataFrame:
    """A small synthetic DataFrame covering all variable classification cases.

    Columns
    -------
    procdt       int  — 10 unique values; should be detected as time axis
    age          float — 50 unique values; continuous
    bmi          float — 50 unique values; continuous; includes NaN
    los          float — 50 unique values; continuous
    status       str  — 3 unique values; categorical
    gender       str  — 2 unique values; logical
    asa_class    int  — 4 unique values; categorical (numeric low-cardinality)
    flag         bool — 2 unique values; logical
    free_text    str  — 50 unique values; categorical; should be suppressed
    """
    rng = np.random.default_rng(42)
    n = 50

    df = pd.DataFrame({
        "procdt":    rng.integers(20200101, 20231231, n),
        "age":       rng.uniform(18, 90, n),
        "bmi":       np.where(rng.random(n) < 0.1, np.nan, rng.uniform(18, 45, n)),
        "los":       rng.uniform(1, 30, n),
        "status":    rng.choice(["alive", "dead", "lost"], n),
        "gender":    rng.choice(["M", "F"], n),
        "asa_class": rng.choice([1, 2, 3, 4], n),
        "flag":      rng.choice([True, False], n),
        "free_text": [f"note_{i}" for i in range(n)],  # 50 unique → suppressed
    })
    return df


@pytest.fixture
def all_missing_df() -> pd.DataFrame:
    """DataFrame with one completely missing column — edge case for classification."""
    return pd.DataFrame({
        "x":    [1.0, 2.0, 3.0],
        "empty": [None, None, None],
    })


@pytest.fixture
def sas_labels() -> dict[str, str]:
    """Sample SAS variable labels matching synthetic_df columns."""
    return {
        "procdt":    "Procedure Date",
        "age":       "Age at Procedure (years)",
        "bmi":       "Body Mass Index",
        "los":       "Length of Stay (days)",
        "status":    "Patient Status",
        "gender":    "Sex",
        "asa_class": "ASA Physical Status Class",
        "flag":      "Complication Flag",
    }


@pytest.fixture
def classified(synthetic_df, sas_labels):
    """Pre-classified synthetic dataset (requires classify_dataset to be implemented)."""
    from eda.classify import classify_dataset
    return classify_dataset(synthetic_df, column_labels=sas_labels)
