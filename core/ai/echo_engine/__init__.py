"""
Echo Engine v1.0.0 - DEP Insight Engine by BODZZ
Professional-grade local analytics with consultant-grade narratives.
Production-ready with memory safety and business intelligence.
"""

from .engine import (
    # Main classes
    EchoChartRecommender,
)

# Public API
__all__ = [
    # Main classes
    "EchoChartRecommender",
]

# Metadata
__version__ = "1.0.0"
__author__ = "BODZZ Analytics"
__description__ = "Professional local analytics engine with consultant-grade narratives"

# Performance warnings
import warnings
warnings.filterwarnings('ignore', category=RuntimeWarning)