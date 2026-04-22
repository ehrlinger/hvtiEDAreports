"""
eda — Core package for hvtiEDAreports.

Provides data loading, variable classification, plotnine figure factories,
summary statistics, and delivery manifest generation. No UI dependency;
safe to import in CLI, Web UI, and Quarto contexts.
"""

from importlib.metadata import version, PackageNotFoundError
try:
    __version__ = version("hvtiEDAreports")
except PackageNotFoundError:
    __version__ = "0.1.0"  # fallback when running from source without install

from eda.loader import load_dataset
from eda.classify import classify_dataset, ClassifiedDataset
from eda.delivery import generate_delivery_package

__all__ = [
    "load_dataset",
    "classify_dataset",
    "ClassifiedDataset",
    "generate_delivery_package",
]
