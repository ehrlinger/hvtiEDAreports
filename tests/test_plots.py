"""
test_plots.py — Tests for eda.plots.

These tests are intentionally lightweight — they verify that figure factory
functions return plotnine ggplot objects without raising exceptions.
Visual correctness is validated manually against hv_eda() R reference output
(Acceptance Criterion #3).

DS-B: expand these tests as plots.py is implemented.
"""

import pytest


class TestHelpers:
    """Tests for pure helper functions that don't require plotnine."""

    def test_ncols_single_variable(self):
        from eda.plots import _ncols
        # n=1: max(2, min(4, floor(sqrt(1)))) = max(2,1) = 2
        assert _ncols(1) == 2

    def test_ncols_four_variables(self):
        from eda.plots import _ncols
        # n=4: max(2, min(4, floor(2))) = 2
        assert _ncols(4) == 2

    def test_ncols_nine_variables(self):
        from eda.plots import _ncols
        # n=9: max(2, min(4, floor(3))) = 3
        assert _ncols(9) == 3

    def test_ncols_sixteen_variables(self):
        from eda.plots import _ncols
        # n=16: max(2, min(4, floor(4))) = 4
        assert _ncols(16) == 4

    def test_ncols_twenty_five_variables(self):
        from eda.plots import _ncols
        # n=25: max(2, min(4, floor(5))) = 4 (capped at 4)
        assert _ncols(25) == 4

    def test_ncols_zero(self):
        from eda.plots import _ncols
        assert _ncols(0) == 1

    def test_axis_title_uses_label_when_available(self):
        from eda.plots import _axis_title
        assert _axis_title("age", {"age": "Age at Procedure (years)"}) == "Age at Procedure (years)"

    def test_axis_title_falls_back_to_column_name(self):
        from eda.plots import _axis_title
        assert _axis_title("age", {}) == "age"

    def test_add_missing_category_replaces_nan(self):
        import pandas as pd
        import numpy as np
        from eda.plots import _add_missing_category
        from eda.theme import MISSING_CATEGORY_LABEL

        s = pd.Series([1.0, np.nan, 2.0])
        result = _add_missing_category(s)
        assert MISSING_CATEGORY_LABEL in result.values

    def test_add_missing_category_no_nan_unchanged(self):
        import pandas as pd
        from eda.plots import _add_missing_category
        from eda.theme import MISSING_CATEGORY_LABEL

        s = pd.Series(["a", "b", "c"])
        result = _add_missing_category(s)
        assert MISSING_CATEGORY_LABEL not in result.values


class TestFigureFactories:
    """Smoke tests — verify functions return a ggplot object without errors."""

    @pytest.mark.skip(reason="Requires plots.py implementation")
    def test_single_var_continuous_returns_ggplot(self, synthetic_df, classified):
        from plotnine import ggplot
        from eda.plots import single_var_plot
        p = single_var_plot(synthetic_df, "age", classified)
        assert isinstance(p, ggplot)

    @pytest.mark.skip(reason="Requires plots.py implementation")
    def test_single_var_categorical_returns_ggplot(self, synthetic_df, classified):
        from plotnine import ggplot
        from eda.plots import single_var_plot
        p = single_var_plot(synthetic_df, "status", classified)
        assert isinstance(p, ggplot)

    @pytest.mark.skip(reason="Requires plots.py implementation")
    def test_categorical_panel_returns_ggplot(self, classified):
        from plotnine import ggplot
        from eda.plots import categorical_panel
        p = categorical_panel(classified)
        assert isinstance(p, ggplot)

    @pytest.mark.skip(reason="Requires plots.py implementation")
    def test_continuous_panel_returns_ggplot(self, classified):
        from plotnine import ggplot
        from eda.plots import continuous_panel
        p = continuous_panel(classified)
        assert isinstance(p, ggplot)

    @pytest.mark.skip(reason="Requires plots.py implementation")
    def test_missing_shown_in_categorical_plot(self, classified):
        """Categorical figure must include MISSING_CATEGORY_LABEL in the data."""
        import pandas as pd
        import numpy as np
        from eda.theme import MISSING_CATEGORY_LABEL
        from eda.plots import single_var_plot

        df = classified.df.copy()
        df.loc[df.index[0], "status"] = np.nan
        p = single_var_plot(df, "status", classified)
        # Extract the data from the ggplot and check for (Missing)
        assert MISSING_CATEGORY_LABEL in p.data["status"].values
