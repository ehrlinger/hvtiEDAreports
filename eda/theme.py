"""
theme.py — Manuscript-quality plotnine theme for CORR / HVI publications.

Matches the visual style established in hvtiPlotR's hv_eda() output.

Reference: github.com/ehrlinger/hvtiPlotR
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Font — Calibri is the CCF publication standard; Arial is the fallback.
FONT_FAMILY: str = "Calibri"
FONT_FAMILY_FALLBACK: str = "Arial"

# Figure dimensions (inches)
FIGURE_WIDTH: float = 6.0
FIGURE_HEIGHT: float = 4.0
FIGURE_DPI: int = 150

# ColorBrewer Set1 (7 colors) — use as default discrete palette.
# Replace with official CCF palette if/when provided.
COLORBREWER_SET1: list[str] = [
    "#E41A1C",  # red
    "#377EB8",  # blue
    "#4DAF4A",  # green
    "#984EA3",  # purple
    "#FF7F00",  # orange
    "#FFFF33",  # yellow
    "#A65628",  # brown
]

MISSING_CATEGORY_LABEL: str = "(Missing)"
"""Explicit label for missing values in categorical figures."""


# ---------------------------------------------------------------------------
# Theme factory
# ---------------------------------------------------------------------------

def hvi_theme():
    """Return a plotnine theme matching the HVI manuscript aesthetic.

    Characteristics
    ---------------
    - White background
    - Light horizontal grid lines; no vertical grid lines
    - Calibri / Arial font
    - Minimal axis chrome

    Usage
    -----
    >>> p = (ggplot(df, aes("x", "y")) + geom_point() + hvi_theme())

    TODO: implement using plotnine.theme() and element_* overrides.
    See plotnine docs: https://plotnine.org/reference/theme.html
    """
    # TODO: implement
    raise NotImplementedError
