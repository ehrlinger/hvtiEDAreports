"""
test_loader.py — Tests for eda.loader.

Coverage target: >= 90% of loader.py lines.

Uses temporary files so no real patient data is needed in the test suite.
"""

import pathlib
import pickle

import numpy as np
import pandas as pd
import pytest

from eda.loader import load_dataset


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Minimal DataFrame for round-trip tests."""
    return pd.DataFrame({
        "procdt": [20220101, 20220201, 20220301],
        "age":    [55.0, 62.0, 71.0],
        "status": ["alive", "dead", "alive"],
    })


@pytest.fixture
def csv_file(tmp_path, sample_df) -> pathlib.Path:
    p = tmp_path / "sample.csv"
    sample_df.to_csv(p, index=False)
    return p


@pytest.fixture
def pickle_file(tmp_path, sample_df) -> pathlib.Path:
    p = tmp_path / "sample.pkl"
    sample_df.to_pickle(p)
    return p


@pytest.fixture
def bad_pickle_file(tmp_path) -> pathlib.Path:
    """Pickle file containing a non-DataFrame object."""
    p = tmp_path / "bad.pkl"
    with open(p, "wb") as f:
        pickle.dump({"not": "a dataframe"}, f)
    return p


@pytest.fixture
def parquet_file(tmp_path, sample_df) -> pathlib.Path:
    p = tmp_path / "sample.parquet"
    sample_df.to_parquet(p, index=False)
    return p


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------

class TestCSVLoader:

    def test_csv_loads_correctly(self, csv_file, sample_df):
        df, labels = load_dataset(csv_file)
        assert list(df.columns) == list(sample_df.columns)
        assert len(df) == len(sample_df)

    def test_csv_returns_empty_labels(self, csv_file):
        _, labels = load_dataset(csv_file)
        assert labels == {}

    def test_csv_column_names_are_strings(self, csv_file):
        df, _ = load_dataset(csv_file)
        assert all(isinstance(c, str) for c in df.columns)

    def test_csv_latin1_fallback(self, tmp_path):
        """CSV with latin-1 encoding should load without error."""
        p = tmp_path / "latin1.csv"
        p.write_bytes("name,value\ncaf\xe9,1\n".encode("latin-1"))
        df, _ = load_dataset(p)
        assert len(df) == 1


# ---------------------------------------------------------------------------
# Pickle
# ---------------------------------------------------------------------------

class TestPickleLoader:

    def test_pickle_round_trip(self, pickle_file, sample_df):
        df, _ = load_dataset(pickle_file)
        pd.testing.assert_frame_equal(df, sample_df)

    def test_pickle_with_pkl_extension(self, pickle_file):
        df, _ = load_dataset(pickle_file)
        assert isinstance(df, pd.DataFrame)

    def test_bad_pickle_raises_type_error(self, bad_pickle_file):
        with pytest.raises(TypeError):
            load_dataset(bad_pickle_file)


# ---------------------------------------------------------------------------
# Parquet
# ---------------------------------------------------------------------------

class TestParquetLoader:

    def test_parquet_loads(self, parquet_file, sample_df):
        df, _ = load_dataset(parquet_file)
        assert list(df.columns) == list(sample_df.columns)


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class TestErrorHandling:

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_dataset(tmp_path / "does_not_exist.csv")

    def test_unsupported_extension_raises(self, tmp_path):
        p = tmp_path / "data.xlsx"
        p.touch()
        with pytest.raises(ValueError, match="Unsupported file format"):
            load_dataset(p)


# ---------------------------------------------------------------------------
# Column name normalization
# ---------------------------------------------------------------------------

class TestColumnNormalization:

    def test_integer_column_names_become_strings(self, tmp_path):
        df = pd.DataFrame({0: [1, 2], 1: [3, 4]})
        p = tmp_path / "int_cols.pkl"
        df.to_pickle(p)
        result, _ = load_dataset(p)
        assert all(isinstance(c, str) for c in result.columns)
