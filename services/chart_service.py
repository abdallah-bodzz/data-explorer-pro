# services/chart_service.py
"""
Chart Service – Centralises all chart operations.
Responsible for chart creation, validation, recommendation, and export.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

from core.charts.templates import (
    plot_plotly_histogram,
    plot_plotly_scatter,
    plot_plotly_pie_chart,
    plot_plotly_box_plot,
    plot_plotly_heatmap,
    plot_plotly_violin_plot,
    plot_plotly_correlation_matrix,
    plot_plotly_bubble_chart,
    plot_plotly_treemap,
    plot_plotly_bubble_map,
    plot_kpi,
    plot_card,
    plot_gauge,
    create_plotly_error_visualization,
    plot_custom_visualization,
)
from core.charts.bar_line import plot_plotly_line_chart, plot_plotly_bar_chart
from core.ai.echo_engine import EchoChartRecommender

logger = logging.getLogger(__name__)


class ChartService:
    """
    Service for all chart-related operations.

    This service provides a clean interface for the UI layer to create,
    validate, and export charts. It encapsulates the complexity of the
    underlying chart template functions and the Echo Engine recommender.
    """

    # Supported chart types with display names (consistent across the app)
    CHART_TYPES = {
        'histogram': '📊 Histogram',
        'line': '📈 Line Chart',
        'bar': '📶 Bar Chart',
        'scatter': '🔵 Scatter Plot',
        'bubble': '🫧 Bubble Chart',
        'box': '📦 Box Plot',
        'pie': '🥧 Pie Chart',
        'violin': '🎻 Violin Plot',
        'heatmap': '🔥 Heatmap',
        'treemap': '🌳 Treemap',
        'bubble_map': '🗺️ Bubble Map',
        'card': '📊 Card (Big Number)',
        'kpi': '🎯 KPI (Number + Trend + Target)',
        'gauge': '⏱️ Gauge Chart',
        'custom_chart': '🧑‍💻 Custom Charts',
    }

    # Mapping from chart type to required field names (used in validation)
    _REQUIRED_FIELDS = {
        'histogram': ['x_col'],
        'scatter': ['x_col', 'y_col'],
        'bubble': ['x_col', 'y_col', 'size_col'],
        'line': ['date_col', 'value_cols'],
        'bar': ['x_col'],
        'box': ['y_col'],
        'pie': ['names_col'],
        'violin': ['y_col'],
        'heatmap': ['x_col', 'y_col'],
        'treemap': ['path'],
        'bubble_map': ['lat_col', 'lon_col'],
        'custom_chart': ['code'],
        # Card, KPI, Gauge have their own validation logic (handled separately)
    }

    def __init__(self, state_manager=None):
        """
        Initialise the ChartService.

        Args:
            state_manager: Optional state manager for session state access.
                           Not used directly, but kept for future extension.
        """
        self.state = state_manager
        self._recommender = EchoChartRecommender()
        self._chart_functions = {
            'line': plot_plotly_line_chart,
            'histogram': plot_plotly_histogram,
            'scatter': plot_plotly_scatter,
            'bar': plot_plotly_bar_chart,
            'pie': plot_plotly_pie_chart,
            'box': plot_plotly_box_plot,
            'violin': plot_plotly_violin_plot,
            'heatmap': plot_plotly_heatmap,
            'bubble': plot_plotly_bubble_chart,
            'treemap': plot_plotly_treemap,
            'bubble_map': plot_plotly_bubble_map,
            'kpi': plot_kpi,
            'card': plot_card,
            'gauge': plot_gauge,
            'custom_chart': plot_custom_visualization,
        }

    # ----------------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------------

    def get_chart_types(self) -> Dict[str, str]:
        """
        Return the mapping of chart type keys to human-readable display names.

        Returns:
            Dictionary of chart_type -> display_name.
        """
        return self.CHART_TYPES.copy()

    def create_chart(self, df: pd.DataFrame, chart_type: str,
                     config: Dict[str, Any]) -> Optional[go.Figure]:
        """
        Create a Plotly figure from the given configuration.

        Args:
            df: The dataset to plot.
            chart_type: One of the supported chart types.
            config: Configuration dictionary (keys depend on chart type).

        Returns:
            Plotly figure object, or None if creation failed.

        Raises:
            ValueError: If chart_type is not supported or config is invalid.
        """
        if df is None or df.empty:
            logger.warning("create_chart called with empty DataFrame")
            return create_plotly_error_visualization("Dataset is empty")

        if chart_type not in self._chart_functions:
            logger.error(f"Unsupported chart type: {chart_type}")
            return create_plotly_error_visualization(
                f"Chart type '{chart_type}' is not supported."
            )

        # Validate configuration before creation
        valid, msg = self.validate_config(df, chart_type, config)
        if not valid:
            logger.warning(f"Validation failed for {chart_type}: {msg}")
            return create_plotly_error_visualization(f"Configuration error: {msg}")

        try:
            # Apply any smart defaults (e.g., auto-binning) before calling
            processed_config = self._apply_smart_defaults(df, chart_type, config)
            fig = self._chart_functions[chart_type](df, processed_config)

            if fig is None:
                logger.error(f"Chart function for {chart_type} returned None")
                return create_plotly_error_visualization("Chart creation returned no figure")

            # Optionally apply unified styling (already done inside templates)
            return fig

        except Exception as e:
            logger.exception(f"Error creating chart '{chart_type}': {e}")
            return create_plotly_error_visualization(f"Chart error: {str(e)}")

    def validate_config(self, df: pd.DataFrame, chart_type: str,
                        config: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate that the configuration is complete and references existing columns.

        Args:
            df: The dataset.
            chart_type: The chart type.
            config: Configuration dictionary.

        Returns:
            (is_valid, error_message)
        """
        if not config:
            return False, "Configuration is empty"

        # Special handling for custom charts – only need 'code'
        if chart_type == 'custom_chart':
            if not config.get('code', '').strip():
                return False, "Custom chart requires Python code"
            return True, ""

        # Card, KPI, Gauge have their own required fields
        if chart_type in ('card', 'kpi', 'gauge'):
            if not config.get('value_col'):
                return False, f"{chart_type} requires 'value_col'"
            if config['value_col'] not in df.columns:
                return False, f"Column '{config['value_col']}' not found"
            return True, ""

        # General validation using REQUIRED_FIELDS
        required = self._REQUIRED_FIELDS.get(chart_type, [])
        for field in required:
            if field not in config or not config[field]:
                return False, f"Missing required field: {field}"

            # For column-based fields, check existence
            if field in ('x_col', 'y_col', 'size_col', 'date_col',
                         'names_col', 'lat_col', 'lon_col'):
                col_name = config.get(field)
                if col_name and col_name not in df.columns:
                    return False, f"Column '{col_name}' not found"

            # Multi-select fields
            if field == 'value_cols':
                for col in config.get(field, []):
                    if col not in df.columns:
                        return False, f"Column '{col}' not found"
            if field == 'path':
                for col in config.get(field, []):
                    if col not in df.columns:
                        return False, f"Column '{col}' not found"

        return True, ""

    def recommend_charts(self, df: pd.DataFrame, user_prompt: str,
                         max_suggestions: int = 8) -> List[Dict[str, Any]]:
        """
        Get chart recommendations from the Echo Engine.

        Args:
            df: The dataset.
            user_prompt: Natural language prompt from the user.
            max_suggestions: Maximum number of recommendations.

        Returns:
            List of chart suggestion dictionaries.
        """
        if df is None or df.empty:
            logger.warning("recommend_charts called with empty DataFrame")
            return []

        try:
            return self._recommender.recommend_charts(
                df, user_prompt, max_suggestions
            )
        except Exception as e:
            logger.exception(f"Error getting chart recommendations: {e}")
            return []

    def create_chart_from_suggestion(self, df: pd.DataFrame,
                                     suggestion: Dict[str, Any]) -> Optional[go.Figure]:
        """
        Create a chart from an AI recommendation (uses core.ai.charts_utils).

        This is a wrapper around the existing `create_ai_plot_from_suggestion`
        function to keep the core logic intact while still exposing it via the service.

        Args:
            df: The dataset.
            suggestion: A chart suggestion dictionary (as returned by recommend_charts).

        Returns:
            Plotly figure, or None if creation fails.
        """
        if df is None or df.empty:
            logger.warning("create_chart_from_suggestion called with empty DataFrame")
            return None

        if not suggestion:
            return None

        try:
            from core.ai.charts_utils import create_ai_plot_from_suggestion
            return create_ai_plot_from_suggestion(df, suggestion)
        except ImportError as e:
            logger.error(f"Failed to import create_ai_plot_from_suggestion: {e}")
            return create_plotly_error_visualization(
                "AI chart creation module not available"
            )
        except Exception as e:
            logger.exception(f"Error creating chart from suggestion: {e}")
            return create_plotly_error_visualization(f"AI chart error: {str(e)}")

    # ----------------------------------------------------------------------
    # Export Methods
    # ----------------------------------------------------------------------

    def export_chart(self, fig: go.Figure, format: str = 'png',
                     width: int = 1200, height: int = 800) -> bytes:
        """
        Export a Plotly figure to image bytes.

        Args:
            fig: The Plotly figure.
            format: Image format ('png', 'jpeg', 'webp', 'svg', 'pdf').
            width: Image width in pixels.
            height: Image height in pixels.

        Returns:
            Image bytes.

        Raises:
            ValueError: If the figure is None or format is unsupported.
        """
        if fig is None:
            raise ValueError("Cannot export None figure")
        try:
            return fig.to_image(format=format, width=width, height=height)
        except Exception as e:
            logger.exception(f"Error exporting chart to {format}: {e}")
            raise ValueError(f"Export failed: {str(e)}")

    def chart_to_html(self, fig: go.Figure) -> str:
        """
        Generate an HTML snippet for embedding the chart.

        Args:
            fig: The Plotly figure.

        Returns:
            HTML string (without <html> wrapper).
        """
        if fig is None:
            return "<!-- No chart to render -->"
        try:
            return pio.to_html(fig, full_html=False, include_plotlyjs=False)
        except Exception as e:
            logger.exception(f"Error converting chart to HTML: {e}")
            return f"<!-- Error converting chart: {str(e)} -->"

    # ----------------------------------------------------------------------
    # Private Helpers
    # ----------------------------------------------------------------------

    def _apply_smart_defaults(self, df: pd.DataFrame, chart_type: str,
                              config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply intelligent defaults based on data characteristics.
        This is a lightweight version of the logic originally in chart_handlers.

        Args:
            df: The dataset.
            chart_type: The chart type.
            config: The user-provided configuration.

        Returns:
            Updated configuration dictionary.
        """
        if not config:
            return config

        config = config.copy()

        # Auto-color scale for numeric color columns
        if not config.get('color_scale'):
            color_col = config.get('color_col')
            if color_col and color_col in df.columns:
                if pd.api.types.is_numeric_dtype(df[color_col]):
                    config['color_scale'] = 'Viridis'
                else:
                    config['color_scale'] = 'Set3'

        # Histogram: auto-binning for high-cardinality numeric columns
        if chart_type == 'histogram' and config.get('x_col'):
            x_col = config['x_col']
            if x_col in df.columns and pd.api.types.is_numeric_dtype(df[x_col]):
                unique_ratio = df[x_col].nunique() / max(1, len(df))
                if unique_ratio > 0.9 and 'bins' not in config:
                    config['bins'] = min(50, max(10, len(df) // 20))

        # Scatter: auto-trendline for sufficient data
        if chart_type == 'scatter' and len(df) > 10:
            if 'trendline' not in config:
                config['trendline'] = 'lowess'

        return config

    # ----------------------------------------------------------------------
    # Optional: Status / Health Checks
    # ----------------------------------------------------------------------

    @staticmethod
    def is_chart_type_supported(chart_type: str) -> bool:
        """Return True if the chart type is supported."""
        return chart_type in ChartService.CHART_TYPES

    def get_supported_chart_types(self) -> List[str]:
        """Return a list of all supported chart type keys."""
        return list(self.CHART_TYPES.keys())