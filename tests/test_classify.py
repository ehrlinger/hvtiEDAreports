"""
test_classify.py — Tests for eda.classify.

Coverage target: >= 90% of classify.py lines.

Tests are grouped by classification rule, time-axis detection,
edge cases, and the ClassifiedDataset API.
"""

import numpy as np
import pandas as pd
import pytest

from eda.classify import (
    ClassifiedDataset,
    classify_dataset,
    _detect_time_axis,
    CAT_MAX_UNIQUE,
    CAT_SUPPRESS_LEVELS,
    LOGICAL_MAX_UNIQUE,
    TIME_KEYWORDS,
)


# ---------------------------------------------------------------------------
# Classification rules
# ---------------------------------------------------------------------------

class TestClassificationRules:

    def test_boolean_dtype_is_logical(self, synthetic_df):
        """bool dtype columns should always classify as logical."""
        result = classify_dataset(synthetic_df)
        assert "flag" in result.logical

    def test_low_cardinality_string_is_logical(self, synthetic_df):
        """String column with 2 unique values should classify as logical."""
        result = classify_dataset(synthetic_df)
        assert "gender" in result.logical

    def test_low_cardinality_string_is_in_categorical(self, synthetic_df):
        """Logical columns should also appear in categorical."""
        result = classify_dataset(synthetic_df)
        assert "gender" in result.categorical

    def test_medium_cardinality_string_is_categorical(self, synthetic_df):
        """String column with 3 unique values should classify as categorical."""
        result = classify_dataset(synthetic_df)
        assert "status" in result.categorical
        assert "status" not in result.logical

    def test_numeric_low_cardinality_is_categorical(self, synthetic_df):
        """Numeric column with 4 unique values should classify as categorical."""
        result = classify_dataset(synthetic_df)
        assert "asa_class" in result.categorical
        assert "asa_class" not in result.continuous

    def test_high_cardinality_numeric_is_continuous(self, synthetic_df):
        """Numeric column with 50 unique values should classify as continuous."""
        result = classify_dataset(synthetic_df)
        assert "age" in result.continuous

    def test_suppressed_column_not_in_plottable(self, synthetic_df):
        """Columns with > CAT_SUPPRESS_LEVELS levels should be suppressed."""
        result = classify_dataset(synthetic_df)
        assert "free_text" in result.suppressed
        assert "free_text" not in result.plottable_categorical

    def test_suppressed_column_still_in_categorical(self, synthetic_df):
        """Suppressed columns should still appear in categorical (for summary)."""
        result = classify_dataset(synthetic_df)
        assert "free_text" in result.categorical

    def test_all_variables_accounted_for(self, synthetic_df):
        """Every column should appear in exactly one primary classification list."""
        result = classify_dataset(synthetic_df)
        all_classified = set(result.continuous) | set(result.categorical)
        assert all_classified == set(synthetic_df.columns)

    def test_logical_subset_of_categorical(self, synthetic_df):
        """logical must be a subset of categorical."""
        result = classify_dataset(synthetic_df)
        assert set(result.logical).issubset(set(result.categorical))

    def test_suppressed_subset_of_categorical(self, synthetic_df):
        """suppressed must be a subset of categorical."""
        result = classify_dataset(synthetic_df)
        assert set(result.suppressed).issubset(set(result.categorical))


# ---------------------------------------------------------------------------
# Missing values
# ---------------------------------------------------------------------------

class TestMissingValues:

    def test_column_with_nan_classifies_by_nonmissing_values(self):
        """unique count for classification should use dropna=True."""
        df = pd.DataFrame({"x": [1.0, 2.0, np.nan, np.nan]})
        result = classify_dataset(df)
        # 2 unique non-null values → logical
        assert "x" in result.logical

    def test_all_missing_column_does_not_crash(self, all_missing_df):
        """A completely missing column should not raise an exception."""
        result = classify_dataset(all_missing_df)
        # Should appear somewhere; exact classification is implementation-defined
        all_vars = set(result.continuous) | set(result.categorical)
        assert "empty" in all_vars


# ---------------------------------------------------------------------------
# Threshold overrides
# ---------------------------------------------------------------------------

class TestThresholdOverrides:

    def test_custom_cat_max(self, synthetic_df):
        """Raising cat_unique_max should reclassify asa_class as continuous."""
        result = classify_dataset(synthetic_df, cat_unique_max=50)
        assert "asa_class" in result.continuous

    def test_custom_suppress_above(self, synthetic_df):
        """Raising suppress_levels_above should un-suppress free_text."""
        result = classify_dataset(synthetic_df, suppress_levels_above=100)
        assert "free_text" not in result.suppressed


# ---------------------------------------------------------------------------
# Time-axis detection
# ---------------------------------------------------------------------------

class TestTimeAxisDetection:

    def test_procdt_detected_as_time_axis(self, synthetic_df):
        """'procdt' should match the highest-priority TIME_KEYWORDS entry."""
        result = classify_dataset(synthetic_df)
        assert result.x_axis_var == "procdt"

    def test_manual_x_axis_override(self, synthetic_df):
        """Caller-supplied x_axis_var should override auto-detection."""
        result = classify_dataset(synthetic_df, x_axis_var="age")
        assert result.x_axis_var == "age"

    def test_detect_time_axis_keyword_match(self):
        """_detect_time_axis should match case-insensitively."""
        cols = ["PatientAge", "OPDT", "BMI"]
        # 'opdt' is in TIME_KEYWORDS; should be detected
        assert _detect_time_axis(cols) == "OPDT"

    def test_detect_time_axis_fallback(self):
        """_detect_time_axis should fall back to first column when no keyword matches."""
        cols = ["alpha", "beta", "gamma"]
        assert _detect_time_axis(cols) == "alpha"

    def test_detect_time_axis_empty(self):
        """_detect_time_axis should return '' for an empty list."""
        assert _detect_time_axis([]) == ""


# ---------------------------------------------------------------------------
# ClassifiedDataset API
# ---------------------------------------------------------------------------

class TestClassifiedDatasetAPI:

    def test_variable_type_continuous(self, synthetic_df):
        result = classify_dataset(synthetic_df)
        assert result.variable_type("age") == "continuous"

    def test_variable_type_logical(self, synthetic_df):
        result = classify_dataset(synthetic_df)
        assert result.variable_type("gender") == "logical"

    def test_variable_type_categorical(self, synthetic_df):
        result = classify_dataset(synthetic_df)
        assert result.variable_type("status") == "categorical"

    def test_variable_type_suppressed(self, synthetic_df):
        result = classify_dataset(synthetic_df)
        assert result.variable_type("free_text") == "categorical (suppressed)"

    def test_n_properties(self, synthetic_df):
        result = classify_dataset(synthetic_df)
        assert result.n_continuous == len(result.continuous)
        assert result.n_categorical == len(result.categorical)
        assert result.n_logical == len(result.logical)
        assert result.n_suppressed == len(result.suppressed)

    def test_column_labels_attached(self, synthetic_df, sas_labels):
        result = classify_dataset(synthetic_df, column_labels=sas_labels)
        assert result.column_labels["age"] == "Age at Procedure (years)"
