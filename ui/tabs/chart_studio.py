# ui/tabs/chart_studio.py
"""
Chart Studio Tab – Manual chart creation and configuration UI.
This module provides the ChartManager class which renders chart configuration forms
and delegates chart creation to the ChartService.
"""

import time
import logging
from typing import Dict, Any, List, Optional, Tuple

import streamlit as st
import pandas as pd
import numpy as np

from services.chart_service import ChartService

logger = logging.getLogger(__name__)


class ChartManager:
    """
    UI manager for chart configuration and creation.

    This class handles the Streamlit UI for selecting chart types, configuring
    columns and options, and triggering chart generation. It delegates all
    chart creation logic to the ChartService.
    """

    # Chart types with display names (mirrored from ChartService for UI convenience)
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

    def __init__(
        self,
        df: pd.DataFrame,
        numeric_cols: List[str],
        categorical_cols: List[str],
        datetime_cols: List[str],
        key_prefix: str = "chart",
        chart_service: Optional[ChartService] = None,
    ):
        """
        Initialise the ChartManager.

        Args:
            df: The dataset.
            numeric_cols: List of numeric column names.
            categorical_cols: List of categorical column names.
            datetime_cols: List of datetime column names.
            key_prefix: Prefix for Streamlit widget keys to avoid collisions.
            chart_service: Optional ChartService instance; creates a default if not provided.
        """
        self.df = df
        self.numeric_cols = numeric_cols
        self.categorical_cols = categorical_cols
        self.datetime_cols = datetime_cols
        self.key_prefix = key_prefix
        self.chart_service = chart_service or ChartService()

    # ===== UI Helper Methods =====
    def _create_two_column_layout(self) -> Tuple:
        return st.columns(2)

    def _create_three_column_layout(self) -> Tuple:
        return st.columns(3)

    def _header(self, text: str, level: int = 2):
        if level == 2:
            st.subheader(text)
        elif level == 3:
            st.markdown(f"**{text}**")

    # ===== Selection Methods =====
    def _select_column(
        self,
        label: str,
        options: List[str],
        default_idx: int = 0,
        key_suffix: str = None,
        include_none: bool = False,
        **kwargs,
    ) -> Optional[str]:
        """Column selector with unique keys."""
        key = f"{self.key_prefix}_{key_suffix}"
        if include_none:
            options = ["None"] + list(options)
        choice = st.selectbox(label, options, index=default_idx, key=key, **kwargs)
        if include_none and choice == "None":
            return None
        return choice

    def _select_numeric(
        self,
        label: str,
        exclude: List[str] = None,
        include_none: bool = False,
        key_suffix: str = None,
        **kwargs,
    ) -> Optional[str]:
        options = [col for col in self.numeric_cols if col not in (exclude or [])]
        return self._select_column(label, options, include_none=include_none, key_suffix=key_suffix, **kwargs)

    def _select_categorical(
        self,
        label: str,
        include_none: bool = True,
        key_suffix: str = None,
        **kwargs,
    ) -> Optional[str]:
        return self._select_column(label, self.categorical_cols, include_none=include_none, key_suffix=key_suffix, **kwargs)

    def _multi_select_columns(
        self,
        label: str,
        options: List[str],
        max_selections: int = None,
        key_suffix: str = None,
        **kwargs,
    ) -> List[str]:
        key = f"{self.key_prefix}_{key_suffix}"
        return st.multiselect(label, options, max_selections=max_selections, key=key, **kwargs)

    def _multi_select_numeric(
        self,
        label: str,
        max_selections: int = None,
        exclude: List[str] = None,
        key_suffix: str = None,
        **kwargs,
    ) -> List[str]:
        key = f"{self.key_prefix}_{key_suffix}"
        options = [col for col in self.numeric_cols if col not in (exclude or [])]
        return st.multiselect(label, options, max_selections=max_selections, key=key, **kwargs)

    def _select_datetime(self, label: str, key_suffix: str = None, **kwargs) -> str:
        return self._select_column(label, self.datetime_cols, key_suffix=key_suffix, **kwargs)

    # ===== Essential Configuration Methods =====
    def _configure_essential_line(self, config: dict):
        self._header("Data Mapping")
        col1, col2 = self._create_two_column_layout()
        with col1:
            config['date_col'] = self._select_datetime("Time Column", key_suffix="line_date")
            config['value_cols'] = self._multi_select_numeric(
                "Metrics",
                max_selections=4,
                exclude=[config['date_col']] if config.get('date_col') in self.numeric_cols else None,
                key_suffix="line_values",
            )
        with col2:
            config['group_col'] = self._select_categorical("Group By", key_suffix="line_group")

    def _configure_essential_bar(self, config: dict):
        self._header("Data Mapping")
        col1, col2 = self._create_two_column_layout()
        with col1:
            config['x_col'] = self._select_column("Category Axis", self.df.columns, key_suffix="bar_x")
            config['y_cols'] = self._multi_select_numeric("Value Columns", max_selections=4, key_suffix="bar_y")
        with col2:
            config['color_col'] = self._select_categorical("Color Grouping", key_suffix="bar_color")
            if config['y_cols']:
                config['agg_func'] = self._select_column(
                    "Aggregation",
                    ['sum', 'mean', 'median', 'min', 'max', 'count'],
                    key_suffix="bar_agg",
                )
            else:
                config['agg_func'] = 'count'

    def _configure_essential_xy(self, config: dict, chart_type: str):
        self._header("Data Mapping")
        col1, col2 = self._create_two_column_layout()
        with col1:
            config['x_col'] = self._select_numeric("X Axis", key_suffix=f"{chart_type}_x")
            config['y_col'] = self._select_numeric("Y Axis", exclude=[config['x_col']], key_suffix=f"{chart_type}_y")
        with col2:
            color_options = self.categorical_cols + self.numeric_cols
            config['color_col'] = self._select_column("Color By", color_options, include_none=True, key_suffix=f"{chart_type}_color")
            if chart_type in ['bubble', 'scatter']:
                config['size_col'] = self._select_numeric("Size By", include_none=True, key_suffix=f"{chart_type}_size")

    def _configure_essential_histogram(self, config: dict):
        self._header("Data Mapping")
        col1, col2 = self._create_two_column_layout()
        with col1:
            config['x_col'] = self._select_column("Column", self.df.columns, key_suffix="hist_col")
        with col2:
            config['color_col'] = self._select_categorical("Color By", key_suffix="hist_color")

    def _configure_essential_pie(self, config: dict):
        self._header("Data Mapping")
        col1, col2 = self._create_two_column_layout()
        with col1:
            config['names_col'] = self._select_column("Category Column", self.df.columns, key_suffix="pie_names")
        with col2:
            config['values_col'] = self._select_numeric("Slice Values", include_none=True, key_suffix="pie_values")
            if config['values_col']:
                config['agg_func'] = self._select_column(
                    "Aggregation",
                    ['sum', 'mean', 'median', 'min', 'max', 'count'],
                    key_suffix="pie_agg",
                )
            else:
                config['agg_func'] = 'count'

    def _configure_essential_box_violin(self, config: dict, chart_type: str):
        self._header("Data Mapping")
        col1, col2 = self._create_two_column_layout()
        with col1:
            config['y_col'] = self._select_numeric("Value", key_suffix=f"{chart_type}_y")
            config['x_col'] = self._select_categorical("Group By", key_suffix=f"{chart_type}_x")
        with col2:
            config['color_col'] = self._select_categorical("Color By", key_suffix=f"{chart_type}_color")

    def _configure_essential_heatmap(self, config: dict):
        self._header("Data Mapping")
        config['numeric_cols'] = self._multi_select_numeric(
            "Numeric Variables",
            max_selections=15,
            key_suffix="heatmap_cols",
        )
        if len(config.get('numeric_cols', [])) >= 2:
            col1, col2 = self._create_two_column_layout()
            with col1:
                config['correlation_method'] = self._select_column(
                    "Correlation Method",
                    ['pearson', 'spearman'],
                    key_suffix="heatmap_method",
                )
            with col2:
                config['show_covariance'] = st.checkbox(
                    "Show covariance instead",
                    key=f"{self.key_prefix}_heatmap_covariance",
                )

    def _configure_essential_treemap(self, config: dict):
        self._header("Data Mapping")
        available_cols = self.categorical_cols + self.numeric_cols
        config['path'] = self._multi_select_columns(
            "Hierarchy Levels",
            available_cols,
            max_selections=4,
            key_suffix="treemap_path",
        )
        col1, col2 = self._create_two_column_layout()
        with col1:
            config['values'] = self._select_numeric("Size Represents", include_none=True, key_suffix="treemap_values")
            if config['values']:
                config['agg_func'] = self._select_column(
                    "Aggregation",
                    ['sum', 'mean', 'median', 'min', 'max', 'count'],
                    key_suffix="treemap_agg_func",
                )
            else:
                config['agg_func'] = 'count'
        with col2:
            config['color'] = self._select_categorical("Color Represents", include_none=True, key_suffix="treemap_color")

    def _configure_essential_gauge(self, config: dict):
        self._header("Data Mapping")
        col1, col2 = self._create_two_column_layout()
        with col1:
            config['value_col'] = self._select_numeric("Value Column", key_suffix="gauge_value")
        with col2:
            config['agg_func'] = self._select_column(
                "Aggregation",
                ["sum", "mean", "median", "min", "max", "count"],
                key_suffix="gauge_agg",
            )

    def _configure_essential_bubble_map(self, config: dict):
        lat_col, lon_col = self._auto_detect_geo_columns()
        self._header("📍 Core Mapping")
        col1, col2 = self._create_two_column_layout()
        with col1:
            default_lat_idx = self.numeric_cols.index(lat_col) if lat_col and lat_col in self.numeric_cols else 0
            config['lat_col'] = self._select_numeric("Latitude", default_idx=default_lat_idx, key_suffix="bm_lat")
            config['size_col'] = self._select_numeric("Bubble Size", include_none=True, key_suffix="bm_size")
        with col2:
            default_lon_idx = self.numeric_cols.index(lon_col) if lon_col and lon_col in self.numeric_cols else 0
            config['lon_col'] = self._select_numeric("Longitude", default_idx=default_lon_idx, key_suffix="bm_lon")
            color_options = self.categorical_cols + self.numeric_cols
            config['color_col'] = self._select_column("Color By", color_options, include_none=True, key_suffix="bm_color")
        col3, col4 = self._create_two_column_layout()
        with col3:
            config['text_col'] = self._select_column("Hover Text", self.df.columns, include_none=True, key_suffix="bm_text")
        with col4:
            group_options = ['Raw Points (No Grouping)'] + self.categorical_cols
            config['group_by'] = self._select_column("Group By", group_options, key_suffix="bm_group")
            if config['group_by'] == 'Raw Points (No Grouping)':
                config['group_by'] = None

    # ===== Chart-Specific Options =====
    def _configure_time_aggregation(self, config: dict):
        with st.expander("Time Aggregation", expanded=False):
            col1, col2 = self._create_two_column_layout()
            with col1:
                config['time_agg'] = st.selectbox(
                    "Frequency",
                    options=['raw', 'D', 'W', 'M', 'Q', 'Y'],
                    format_func={
                        'raw': 'Raw data (no aggregation)',
                        'D': 'Daily',
                        'W': 'Weekly',
                        'M': 'Monthly',
                        'Q': 'Quarterly',
                        'Y': 'Yearly',
                    }.get,
                    key=f"{self.key_prefix}_time_agg",
                )
            with col2:
                config['agg_func'] = st.selectbox(
                    "Aggregation method",
                    options=['mean', 'sum', 'median', 'min', 'max', 'count'],
                    key=f"{self.key_prefix}_agg_func",
                )

    def _configure_chart_options(self, config: dict):
        with st.expander("Chart Options", expanded=False):
            chart_type = config['type']
            if chart_type == 'line':
                self._configure_line_options(config)
            elif chart_type == 'bar':
                self._configure_bar_options(config)
            elif chart_type in ['scatter', 'bubble']:
                self._configure_scatter_bubble_options(config)
            elif chart_type == 'histogram':
                self._configure_histogram_options(config)
            elif chart_type in ['box', 'violin']:
                self._configure_box_violin_options(config)
            elif chart_type == 'pie':
                self._configure_pie_options(config)
            elif chart_type == 'heatmap':
                self._configure_heatmap_options(config)

    def _configure_line_options(self, config: dict):
        col1, col2 = self._create_two_column_layout()
        with col1:
            config['line_style'] = st.selectbox("Line style", ['solid', 'dash', 'dot'], key=f"{self.key_prefix}_line_style")
            config['show_markers'] = st.checkbox("Show data points", key=f"{self.key_prefix}_line_markers")
        with col2:
            config['connect_gaps'] = st.checkbox("Connect data gaps", key=f"{self.key_prefix}_line_gaps")
            if len(config.get('value_cols', [])) > 1:
                config['dual_yaxis'] = st.checkbox("Dual Y-axis", key=f"{self.key_prefix}_line_dual_y")

    def _configure_bar_options(self, config: dict):
        col1, col2 = self._create_two_column_layout()
        with col1:
            orientation_map = {'Vertical': 'v', 'Horizontal': 'h'}
            orientation_choice = st.radio(
                "Orientation",
                options=list(orientation_map.keys()),
                key=f"{self.key_prefix}_bar_orientation",
            )
            config['orientation'] = orientation_map[orientation_choice]
            config['barmode'] = st.selectbox(
                "Bar Layout",
                options=['group', 'stack', 'overlay'],
                key=f"{self.key_prefix}_bar_mode",
            )
            config['sort_bars'] = st.checkbox("Sort by Value", value=False, key=f"{self.key_prefix}_bar_sort")
            if config['sort_bars'] and config.get('y_cols'):
                config['sort_by'] = st.selectbox("Sort By", config['y_cols'], key=f"{self.key_prefix}_bar_sort_by")
                config['sort_descending'] = st.checkbox("Descending Order", value=True, key=f"{self.key_prefix}_bar_sort_desc")
        with col2:
            config['show_values'] = st.checkbox("Show Values on Bars", key=f"{self.key_prefix}_bar_show_values")
            if config['show_values']:
                config['value_position'] = st.selectbox(
                    "Value Position",
                    options=['auto', 'outside', 'inside'],
                    key=f"{self.key_prefix}_bar_value_pos",
                )
            if config.get('y_cols') and len(config['y_cols']) == 1:
                config['show_error_bars'] = st.checkbox("Show Error Bars", key=f"{self.key_prefix}_bar_errors")
                if config['show_error_bars']:
                    config['error_func'] = st.selectbox("Error Type", ['std', 'sem'], key=f"{self.key_prefix}_bar_error_func")

    def _configure_scatter_bubble_options(self, config: dict):
        col1, col2 = self._create_two_column_layout()
        with col1:
            config['trendline'] = st.selectbox("Trendline", [None, "ols", "lowess"], key=f"{self.key_prefix}_{config['type']}_trendline")
            config['log_x'] = st.checkbox("Log X Scale", key=f"{self.key_prefix}_{config['type']}_logx")
        with col2:
            config['log_y'] = st.checkbox("Log Y Scale", key=f"{self.key_prefix}_{config['type']}_logy")
            if config.get('size_col'):
                config['size_max'] = st.slider("Max Point Size", 10, 50, 20, key=f"{self.key_prefix}_{config['type']}_size_max")

    def _configure_histogram_options(self, config: dict):
        col1, col2 = self._create_two_column_layout()
        with col1:
            config['bins'] = st.slider("Bins", 5, 100, 30, key=f"{self.key_prefix}_hist_bins")
            config['histnorm'] = st.selectbox("Normalization", [None, 'percent', 'probability', 'density'], key=f"{self.key_prefix}_hist_norm")
            st.write("X-axis Range (optional):")
            use_custom_range = st.checkbox("Set custom range", key=f"{self.key_prefix}_hist_use_range")
            if use_custom_range and config.get('x_col'):
                col1_range, col2_range = st.columns(2)
                with col1_range:
                    config['range_x_min'] = st.number_input("Min", value=float(self.df[config['x_col']].min()), key=f"{self.key_prefix}_hist_range_min")
                with col2_range:
                    config['range_x_max'] = st.number_input("Max", value=float(self.df[config['x_col']].max()), key=f"{self.key_prefix}_hist_range_max")
                config['range_x'] = [config['range_x_min'], config['range_x_max']]
        with col2:
            config['marginal'] = st.selectbox("Marginal Plot", [None, "rug", "box", "violin"], key=f"{self.key_prefix}_hist_marginal")
            config['cumulative'] = st.checkbox("Cumulative", key=f"{self.key_prefix}_hist_cumulative")
            config['showlegend'] = st.checkbox("Show Legend", value=True, key=f"{self.key_prefix}_hist_legend")

    def _configure_box_violin_options(self, config: dict):
        col1, col2 = self._create_two_column_layout()
        with col1:
            config['points'] = st.selectbox("Show Points", ['outliers', 'all', 'suspectedoutliers', 'none'], key=f"{self.key_prefix}_{config['type']}_points")
        with col2:
            if config['type'] == 'box':
                config['notched'] = st.checkbox("Show Notches", key=f"{self.key_prefix}_box_notched")
            elif config['type'] == 'violin':
                config['box'] = st.checkbox("Show Box Plot", key=f"{self.key_prefix}_violin_box")
            config['showlegend'] = st.checkbox("Show Legend", value=True, key=f"{self.key_prefix}_{config['type']}_legend")

    def _configure_pie_options(self, config: dict):
        with st.expander("Pie Chart Options", expanded=False):
            col1, col2 = self._create_two_column_layout()
            with col1:
                config['hole'] = st.slider("Donut hole size", 0.0, 0.8, 0.0, 0.1, key=f"{self.key_prefix}_pie_hole")
                config['sort_slices'] = st.checkbox("Sort by size", value=True, key=f"{self.key_prefix}_pie_sort")
                config['showlegend'] = st.checkbox("Show Legend", value=True, key=f"{self.key_prefix}_pie_legend")
            with col2:
                config['textinfo'] = st.selectbox("Slice labels", ['label+percent', 'label', 'percent', 'value', 'none'], key=f"{self.key_prefix}_pie_text")
                config['text_position'] = st.selectbox("Label position", ['auto', 'inside', 'outside'], key=f"{self.key_prefix}_pie_text_pos")
            if config.get('names_col'):
                current_names = config['names_col']
                unique_count = self.df[current_names].nunique() if current_names in self.df.columns else 0
                if unique_count > 0:
                    st.divider()
                    st.write("**Slice Management**")
                    col3, col4 = self._create_two_column_layout()
                    with col3:
                        if unique_count > 8:
                            use_limit = st.checkbox("Limit slices", value=True, key=f"{self.key_prefix}_pie_use_limit")
                            if use_limit:
                                current_max = min(15, unique_count)
                                config['slice_limit'] = st.slider("Maximum slices", 3, current_max, min(8, current_max), key=f"{self.key_prefix}_pie_limit")
                        config['min_percent'] = st.slider("Minimum slice size (%)", 0.0, 10.0, 0.0, 0.5, key=f"{self.key_prefix}_pie_min_percent")
                    with col4:
                        config['group_others'] = st.checkbox("Group small slices as 'Other'", value=True, key=f"{self.key_prefix}_pie_group_others")
                        if unique_count <= 25:
                            unique_cats = self.df[current_names].unique()[:25]
                            config['pull_slices'] = st.multiselect(
                                "Emphasize slices",
                                unique_cats,
                                key=f"{self.key_prefix}_pie_pull",
                            )
                        else:
                            st.caption("Too many categories for slice emphasis")

    def _configure_heatmap_options(self, config: dict):
        with st.expander("Heatmap Options", expanded=False):
            col1, col2 = self._create_two_column_layout()
            with col1:
                config['lower_triangle'] = st.checkbox("Show only lower triangle", value=True, key=f"{self.key_prefix}_heatmap_lower")
                config['cluster_matrix'] = st.checkbox("Cluster similar variables", key=f"{self.key_prefix}_heatmap_cluster")
                color_scales = ['RdBu', 'Viridis', 'Plasma', 'Inferno', 'Blues', 'Reds', 'IceFire', 'Portland']
                config['color_scale'] = st.selectbox(
                    "Color scale",
                    color_scales,
                    key=f"{self.key_prefix}_heatmap_colorscale",
                )
                config['invert_colors'] = st.checkbox("Invert color scale", key=f"{self.key_prefix}_heatmap_invert")
            with col2:
                config['show_values'] = st.checkbox("Show correlation values", value=True, key=f"{self.key_prefix}_heatmap_values")
                config['show_significance'] = st.checkbox("Gray out non-significant", key=f"{self.key_prefix}_heatmap_sig")
                config['showlegend'] = st.checkbox("Show Legend", value=True, key=f"{self.key_prefix}_heatmap_legend")

    def _configure_gauge_range_expander(self, config: dict):
        with st.expander("Range Settings", expanded=False):
            st.write("**Minimum Value**")
            min_col1, min_col2 = st.columns([3, 2])
            with min_col1:
                min_source = st.radio("Min Source", ["Auto", "Fixed", "Column"], key=f"{self.key_prefix}_gauge_min_source", horizontal=True)
            with min_col2:
                if min_source == "Fixed":
                    config['min_fixed'] = st.number_input("Min Value", value=0.0, key=f"{self.key_prefix}_gauge_min_fixed")
                elif min_source == "Column":
                    config['min_col'] = self._select_numeric("Min Column", key_suffix="gauge_min_col")
            st.write("**Maximum Value**")
            max_col1, max_col2 = st.columns([3, 2])
            with max_col1:
                max_source = st.radio("Max Source", ["Auto", "Fixed", "Column"], key=f"{self.key_prefix}_gauge_max_source", horizontal=True)
            with max_col2:
                if max_source == "Fixed":
                    config['max_fixed'] = st.number_input("Max Value", value=100.0, key=f"{self.key_prefix}_gauge_max_fixed")
                elif max_source == "Column":
                    config['max_col'] = self._select_numeric("Max Column", key_suffix="gauge_max_col")

    def _configure_bubble_map_display(self, config: dict):
        with st.expander("Map Settings", expanded=False):
            col1, col2 = self._create_two_column_layout()
            with col1:
                config['projection_type'] = st.selectbox(
                    "Map Projection",
                    ["natural earth", "mercator", "orthographic", "equirectangular", "albers usa"],
                    key=f"{self.key_prefix}_bm_proj",
                )
                config['size_min'] = st.slider("Min Bubble Size", 4, 20, 8, key=f"{self.key_prefix}_bm_size_min")
                config['opacity'] = st.slider("Bubble Opacity", 0.1, 1.0, 0.7, 0.1, key=f"{self.key_prefix}_bm_opacity")
            with col2:
                config['scope'] = st.selectbox(
                    "Map Region",
                    ["world", "usa", "europe", "asia", "north america", "south america"],
                    key=f"{self.key_prefix}_bm_scope",
                )
                config['size_max'] = st.slider("Max Bubble Size", 20, 80, 40, key=f"{self.key_prefix}_bm_size_max")
                config['size_mode'] = st.selectbox(
                    "Size Scaling",
                    ['area', 'linear', 'diameter'],
                    format_func=lambda x: {'area': 'Area-Proportional', 'linear': 'Linear', 'diameter': 'Diameter-Proportional'}[x],
                    key=f"{self.key_prefix}_bm_size_mode",
                )
            col3, col4 = self._create_two_column_layout()
            with col3:
                config['auto_zoom'] = st.checkbox("Auto-zoom to data", key=f"{self.key_prefix}_bm_auto_zoom")
            with col4:
                if config['group_by'] is None:
                    config['apply_jitter'] = st.checkbox("Apply jitter to overlapping points", key=f"{self.key_prefix}_bm_jitter")
                    if config.get('apply_jitter'):
                        config['jitter_strength'] = st.slider("Jitter Strength", 0.001, 0.05, 0.01, 0.001, key=f"{self.key_prefix}_bm_jitter_strength")

    def _configure_advanced_settings(self, config: dict):
        with st.expander("Advanced Settings", expanded=False):
            col1, col2 = self._create_two_column_layout()
            with col1:
                config['title'] = st.text_input(
                    "Custom title",
                    placeholder="Auto-generated based on configuration",
                    key=f"{self.key_prefix}_title",
                )
                if config['type'] == 'line':
                    config['max_series'] = st.slider("Maximum series limit", 5, 100, 20, key=f"{self.key_prefix}_max_series")
            with col2:
                all_columns = self.df.columns.tolist()
                default_hover = []
                if config.get('date_col'):
                    default_hover.append(config['date_col'])
                if config.get('x_col'):
                    default_hover.append(config['x_col'])
                hover_selection = st.multiselect(
                    "Hover data columns",
                    options=all_columns,
                    default=default_hover[:2],
                    key=f"{self.key_prefix}_{config['type']}_hover",
                )
                config['hover_data'] = {col: True for col in hover_selection}
                if 'showlegend' not in config:
                    config['showlegend'] = st.checkbox("Show Legend", value=True, key=f"{self.key_prefix}_{config['type']}_legend")

    # ===== Chart Configuration Methods =====
    def configure_line(self) -> Dict[str, Any]:
        config = {"type": "line"}
        self._configure_essential_line(config)
        if config.get('date_col') in self.datetime_cols:
            self._configure_time_aggregation(config)
        self._configure_chart_options(config)
        self._configure_advanced_settings(config)
        return config

    def configure_bar(self) -> Dict[str, Any]:
        config = {"type": "bar"}
        self._configure_essential_bar(config)
        self._configure_chart_options(config)
        self._configure_advanced_settings(config)
        return config

    def configure_scatter(self) -> Dict[str, Any]:
        config = {"type": "scatter"}
        self._configure_essential_xy(config, "scatter")
        self._configure_chart_options(config)
        self._configure_advanced_settings(config)
        return config

    def configure_bubble(self) -> Dict[str, Any]:
        config = {"type": "bubble"}
        self._configure_essential_xy(config, "bubble")
        self._configure_chart_options(config)
        self._configure_advanced_settings(config)
        return config

    def configure_histogram(self) -> Dict[str, Any]:
        config = {"type": "histogram"}
        self._configure_essential_histogram(config)
        self._configure_chart_options(config)
        self._configure_advanced_settings(config)
        return config

    def configure_pie(self) -> Dict[str, Any]:
        config = {"type": "pie"}
        self._configure_essential_pie(config)
        self._configure_chart_options(config)
        self._configure_advanced_settings(config)
        return config

    def configure_box(self) -> Dict[str, Any]:
        config = {"type": "box"}
        self._configure_essential_box_violin(config, "box")
        self._configure_chart_options(config)
        self._configure_advanced_settings(config)
        return config

    def configure_violin(self) -> Dict[str, Any]:
        config = {"type": "violin"}
        self._configure_essential_box_violin(config, "violin")
        self._configure_chart_options(config)
        self._configure_advanced_settings(config)
        return config

    def configure_heatmap(self) -> Dict[str, Any]:
        config = {"type": "heatmap"}
        self._configure_essential_heatmap(config)
        self._configure_chart_options(config)
        self._configure_advanced_settings(config)
        return config

    def configure_treemap(self) -> Dict[str, Any]:
        config = {"type": "treemap"}
        self._configure_essential_treemap(config)
        with st.expander("Display Options", expanded=False):
            col1, col2 = self._create_two_column_layout()
            with col1:
                config['textinfo'] = st.selectbox("Label content", ['label+value', 'label+percent parent', 'label', 'value', 'none'], key=f"{self.key_prefix}_treemap_textinfo")
                if config.get('path'):
                    path_len = len(config['path'])
                    current_max = min(3, path_len)
                    config['maxdepth'] = st.slider("Max depth levels", -1, path_len, current_max, key=f"{self.key_prefix}_treemap_maxdepth")
            with col2:
                config['aggregate_small_categories'] = st.checkbox("Group small categories", key=f"{self.key_prefix}_treemap_aggregate")
                config['pathbar_visible'] = st.checkbox("Show navigation pathbar", key=f"{self.key_prefix}_treemap_pathbar_visible")
                config['showlegend'] = st.checkbox("Show Legend", value=True, key=f"{self.key_prefix}_treemap_legend")
        self._configure_advanced_settings(config)
        return config

    def configure_gauge(self) -> Dict[str, Any]:
        config = {"type": "gauge"}
        self._configure_essential_gauge(config)
        self._configure_gauge_range_expander(config)
        with st.expander("Target & Goal", expanded=False):
            self._configure_target_settings(config)
        with st.expander("Appearance", expanded=False):
            col_a, col_b = self._create_two_column_layout()
            with col_a:
                config['title'] = st.text_input("Title", key=f"{self.key_prefix}_gauge_title")
                config['units'] = st.text_input("Units", key=f"{self.key_prefix}_gauge_units")
            with col_b:
                config['decimals'] = st.number_input("Decimals", 0, 6, 2, key=f"{self.key_prefix}_gauge_decimals")
                config['gauge_height'] = st.number_input("Gauge Height", 200, 600, 300, key=f"{self.key_prefix}_gauge_height")
                config['showlegend'] = st.checkbox("Show Legend", value=False, key=f"{self.key_prefix}_gauge_legend")
        return config

    def configure_bubble_map(self) -> Dict[str, Any]:
        config = {"type": "bubble_map"}
        self._configure_essential_bubble_map(config)
        self._configure_bubble_map_display(config)
        self._configure_advanced_settings(config)
        return config

    def configure_card(self) -> Dict[str, Any]:
        config = {"type": "card"}
        col1, col2 = self._create_two_column_layout()
        with col1:
            config["value_col"] = self._select_numeric("Value Column", key_suffix="card_value")
        with col2:
            config["agg_func"] = self._select_column("Aggregation", ["sum", "mean", "median", "min", "max", "count"], key_suffix="card_agg")
        with st.expander("Display & Formatting", expanded=False):
            col_a, col_b = self._create_two_column_layout()
            with col_a:
                config["title"] = st.text_input("Title", key=f"{self.key_prefix}_card_title")
                config["prefix"] = st.text_input("Prefix", key=f"{self.key_prefix}_card_prefix")
            with col_b:
                config["decimals"] = st.number_input("Decimals", 0, 6, 2, key=f"{self.key_prefix}_card_decimals")
                config["human_format"] = st.checkbox("Compact formatting", key=f"{self.key_prefix}_card_human_format")
        return config

    def configure_kpi(self) -> Dict[str, Any]:
        config = {"type": "kpi"}
        col1, col2, col3 = self._create_three_column_layout()
        with col1:
            config["value_col"] = self._select_numeric("KPI Value", key_suffix="kpi_value")
        with col2:
            config["agg_func"] = self._select_column("Aggregation", ["sum", "mean", "median", "min", "max", "count"], key_suffix="kpi_agg")
        with col3:
            trend_opts = ["None"] + [col for col in (self.datetime_cols + self.numeric_cols) if col != config["value_col"]]
            trend_choice = self._select_column("Trend Axis", trend_opts, key_suffix="kpi_trend")
            config["trend_col"] = None if trend_choice == "None" else trend_choice
        with st.expander("Target & Goal", expanded=False):
            self._configure_target_settings(config)
        with st.expander("Display & Formatting", expanded=False):
            col_a, col_b = self._create_two_column_layout()
            with col_a:
                config["title"] = st.text_input("Title", key=f"{self.key_prefix}_kpi_title")
                config["prefix"] = st.text_input("Prefix", key=f"{self.key_prefix}_kpi_prefix")
            with col_b:
                config["decimals"] = st.number_input("Decimals", 0, 6, 2, key=f"{self.key_prefix}_kpi_decimals")
                config["human_format"] = st.checkbox("Compact formatting", key=f"{self.key_prefix}_kpi_human_format")
        return config

    def configure_custom_chart(self) -> Dict[str, Any]:
        config = {"type": "custom_chart"}
        dataset_context = self._generate_dataset_context()
        default_code = self._build_custom_chart_template(dataset_context)
        st.markdown("### 🎨 Custom Visualization Studio")
        st.caption("Write Python code to create custom visualizations with full control over every aspect")
        config['code'] = st.text_area(
            "Python Code",
            value=default_code,
            height=400,
            placeholder="# Write your Plotly code here...",
            help="Create 'fig' variable with your Plotly figure",
        )
        with st.expander("🚀 **Advanced Visualization Techniques**", expanded=False):
            tech_tabs = st.tabs(["Multi-Panel Dashboards", "Interactive Features", "Advanced Styling", "3D & Special Charts"])
            with tech_tabs[0]:
                st.markdown("**📊 Multi-Panel Dashboards**")
                st.code("""# Create a professional dashboard with subplots
    fig = make_subplots(
        rows=3, cols=3,
        specs=[
            [{"type": "scatter", "colspan": 2}, None, {"type": "indicator"}],
            [{"type": "bar"}, {"type": "heatmap"}, {"type": "pie"}],
            [{"type": "scatter3d", "colspan": 3}, None, None]
        ],
        subplot_titles=(
            "Main Time Series",
            "KPI Dashboard",
            "Category Distribution",
            "Correlation Matrix",
            "Market Share",
            "3D Cluster Analysis"
        ),
        vertical_spacing=0.08,
        horizontal_spacing=0.05
    )

    # Add traces to specific subplot positions
    fig.add_trace(
        go.Scatter(x=df['date'], y=df['revenue'], name='Revenue'),
        row=1, col=1
    )
    fig.add_trace(
        go.Indicator(
            mode="number+delta",
            value=df['revenue'].sum(),
            delta={'reference': df['revenue'].mean()},
            title={'text': "Total Revenue"}
        ),
        row=1, col=3
    )

    # Sync axes across subplots
    fig.update_xaxes(matches='x', row=1, col=1)
    fig.update_yaxes(matches='y', row=1, col=1)""", language='python')
            with tech_tabs[1]:
                st.markdown("**🎮 Interactive Features**")
                st.code("""# Add interactive controls and animations
    fig.update_layout(
        # Dropdown menu for different views
        updatemenus=[
            dict(
                type="dropdown",
                direction="down",
                buttons=list([
                    dict(label="Linear Scale",
                        method="update",
                        args=[{"visible": [True, False, False]},
                            {"yaxis.type": "linear"}]),
                    dict(label="Log Scale",
                        method="update",
                        args=[{"visible": [False, True, False]},
                            {"yaxis.type": "log"}]),
                    dict(label="Compare Both",
                        method="update",
                        args=[{"visible": [True, True, True]},
                            {"yaxis.type": "linear"}]),
                ]),
                showactive=True,
                x=0.1, y=1.15
            ),
            # Range slider for zooming
            dict(
                type="buttons",
                buttons=[
                    dict(label="Reset Zoom",
                        method="relayout",
                        args=["xaxis.autorange", True]),
                    dict(label="Last 30 Days",
                        method="relayout",
                        args=["xaxis.range", [df['date'].iloc[-30], df['date'].iloc[-1]]])
                ],
                x=0.8, y=1.15
            )
        ],
        # Slider for animation
        sliders=[dict(
            active=0,
            steps=[
                dict(method="animate", args=[[f"frame{k}"], {"mode": "immediate"}])
                for k in range(5)
            ],
            x=0.1, y=0.02
        )],
        # Range selector for time series
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all")
                ])
            ),
            rangeslider=dict(visible=True),
            type="date"
        ),
        # Advanced hover configuration
        hovermode="x unified",
        hoverdistance=100,
        spikedistance=1000
    )""", language='python')
            with tech_tabs[2]:
                st.markdown("**🎨 Advanced Styling & Formatting**")
                st.code("""# Professional styling for executive presentations
    fig.update_layout(
        # Theme and layout
        template="plotly_white+gridon",  # Custom combined template
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        # Typography system
        font=dict(
            family="Inter, -apple-system, BlinkMacSystemFont, sans-serif",
            size=12,
            color="#2D3748"
        ),
        title_font=dict(
            family="Inter, sans-serif",
            size=24,
            color="#1A202C",
            weight=600
        ),
        # Advanced annotations
        annotations=[
            dict(
                x=0.5, y=1.05,
                xref="paper", yref="paper",
                text="<b>EXECUTIVE DASHBOARD</b>",
                showarrow=False,
                font=dict(size=16, color="#4A5568")
            ),
            dict(
                x=0.02, y=-0.12,
                xref="paper", yref="paper",
                text="<i>Data Explorer Pro | BODZZ Analytics Platform</i>",
                showarrow=False,
                font=dict(size=10, color="#718096")
            )
        ],
        # Advanced legend
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="#E2E8F0",
            borderwidth=1,
            font=dict(size=11)
        ),
        # Grid styling
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(0, 0, 0, 0.07)",
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor="rgba(0, 0, 0, 0.1)",
            showline=True,
            linewidth=2,
            linecolor="#CBD5E0"
        ),
        # Margins and spacing
        margin=dict(t=100, b=80, l=80, r=40),
        autosize=True,
        height=600
    )

    # Advanced trace styling
    fig.update_traces(
        marker=dict(
            line=dict(width=1, color='white'),
            opacity=0.8,
            size=8
        ),
        line=dict(width=2.5, dash=None),
        selector=dict(type='scatter')
    )""", language='python')
            with tech_tabs[3]:
                st.markdown("**🌐 3D & Specialized Charts**")
                st.code("""# 3D Visualizations
    fig = go.Figure(data=[
        go.Scatter3d(
            x=df['x_col'],
            y=df['y_col'],
            z=df['z_col'],
            mode='markers',
            marker=dict(
                size=5,
                color=df['value_col'],
                colorscale='Viridis',
                opacity=0.8,
                colorbar=dict(title='Value')
            ),
            text=df['category_col'],
            hovertemplate='<b>%{text}</b><br>' +
                        'X: %{x:.2f}<br>' +
                        'Y: %{y:.2f}<br>' +
                        'Z: %{z:.2f}<br>' +
                        'Value: %{marker.color:.2f}<extra></extra>'
        )
    ])

    fig.update_layout(
        scene=dict(
            xaxis_title='X Axis',
            yaxis_title='Y Axis',
            zaxis_title='Z Axis',
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.5)
            )
        ),
        title='3D Scatter Plot'
    )

    # Parallel Coordinates Plot
    fig = px.parallel_coordinates(
        df,
        color=df['target_col'],
        dimensions=['feature_1', 'feature_2', 'feature_3', 'feature_4'],
        color_continuous_scale=px.colors.diverging.Tealrose,
        labels={'color': 'Target Value'},
        title='Parallel Coordinates - Feature Relationships'
    )

    # Sunburst Chart (Hierarchical)
    fig = px.sunburst(
        df,
        path=['region', 'country', 'city'],
        values='population',
        color='gdp_per_capita',
        color_continuous_scale='RdBu',
        title='Population Distribution by Region > Country > City'
    )

    # Radar Chart
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=df.iloc[0][['speed', 'accuracy', 'quality', 'reliability', 'cost']],
        theta=['Speed', 'Accuracy', 'Quality', 'Reliability', 'Cost'],
        fill='toself',
        name='Product A'
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=True
    )""", language='python')
        # Quick Reference
        with st.expander("📋 **Quick Reference & Cheat Sheet**", expanded=False):
            ref_col1, ref_col2 = st.columns(2)
            with ref_col1:
                st.markdown("**🎯 Essential Requirements**")
                st.markdown("""
                ```python
                # MUST create 'fig' variable
                fig = px.scatter(df, x='col1', y='col2')
                # Available variables:
                df      # Your dataset
                px      # Plotly Express (fast charts)
                go      # Plotly Graph Objects (full control)
                np      # NumPy (math operations)
                pd      # pandas (data manipulation)
                ```
                """)
                st.markdown("**🔧 Quick Templates**")
                st.code("""# Time Series
    fig = px.line(df, x='date', y='value', color='category')

    # Multi-Series Bar Chart
    fig = px.bar(df, x='category', y=['metric1', 'metric2'], barmode='group')

    # Correlation Matrix
    fig = px.imshow(df.corr(), color_continuous_scale='RdBu')

    # Geographic Map
    fig = px.scatter_geo(df, lat='latitude', lon='longitude', size='value')
    """, language='python')
            with ref_col2:
                st.markdown("**📊 Data Type Reference**")
                st.markdown("""
                ```python
                # Check column types:
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                category_cols = df.select_dtypes(include=['object', 'category']).columns
                date_cols = df.select_dtypes(include=['datetime64']).columns
                # Common operations:
                df['col'].fillna(0)           # Replace NaN
                df['col'].astype(str)         # Convert to string
                pd.to_datetime(df['date_col']) # Convert to datetime
                df.groupby('group_col').mean() # Group aggregation
                ```
                """)
                st.markdown("**🚨 Debugging Tips**")
                st.markdown("""
                - **Column doesn't exist**: Check exact spelling and case
                - **Mixed data types**: Use `df['col'].dtype` to check type
                - **Large dataset**: Sample with `df.sample(10000)`
                - **Slow rendering**: Reduce markers or use aggregation
                - **No figure shown**: Ensure 'fig' variable exists
                - **Missing imports**: Import needed modules at top
                """)
        with st.expander("🔍 **Data Exploration Helpers**", expanded=False):
            st.markdown("**Quick analysis functions (copy-paste ready):**")
            analysis_tabs = st.tabs(["Column Analysis", "Data Quality", "Statistical Tests"])
            with analysis_tabs[0]:
                st.code("""def analyze_column(column_name):
        \"\"\"Comprehensive column analysis\"\"\"
        if column_name not in df.columns:
            return f"Column '{column_name}' not found"
        col = df[column_name]
        result = {
            "column": column_name,
            "dtype": str(col.dtype),
            "non_null": col.count(),
            "total_rows": len(df),
            "null_pct": f"{(col.isnull().sum() / len(df)) * 100:.1f}%",
            "unique_values": col.nunique(),
            "unique_pct": f"{(col.nunique() / len(df)) * 100:.1f}%",
            "memory_usage": f"{col.memory_usage(deep=True) / 1024:.1f} KB"
        }
        # Type-specific statistics
        if pd.api.types.is_numeric_dtype(col):
            result.update({
                "min": f"{col.min():.2f}",
                "max": f"{col.max():.2f}",
                "mean": f"{col.mean():.2f}",
                "std": f"{col.std():.2f}",
                "median": f"{col.median():.2f}",
                "skewness": f"{col.skew():.2f}",
                "kurtosis": f"{col.kurtosis():.2f}",
                "zero_count": (col == 0).sum(),
                "negative_count": (col < 0).sum()
            })
        elif pd.api.types.is_datetime64_any_dtype(col):
            result.update({
                "range": f"{col.min().date()} to {col.max().date()}",
                "time_span": str(col.max() - col.min()),
                "unique_dates": col.dt.date.nunique()
            })
        elif pd.api.types.is_categorical_dtype(col) or pd.api.types.is_object_dtype(col):
            value_counts = col.value_counts()
            result.update({
                "top_5_values": dict(value_counts.head(5)),
                "most_common": value_counts.index[0] if not value_counts.empty else None,
                "most_common_pct": f"{(value_counts.iloc[0] / len(df)) * 100:.1f}%" if not value_counts.empty else None
            })
        return result

    # Usage:
    # print(analyze_column('revenue'))
    # print(analyze_column('category'))""", language='python')
            with analysis_tabs[1]:
                st.code("""def data_quality_report():
        \"\"\"Generate comprehensive data quality report\"\"\"
        report = []
        for col in df.columns:
            col_info = {
                "column": col,
                "dtype": str(df[col].dtype),
                "total": len(df),
                "non_null": df[col].count(),
                "null_count": df[col].isnull().sum(),
                "null_pct": f"{(df[col].isnull().sum() / len(df)) * 100:.1f}%",
                "unique": df[col].nunique()
            }
            # Data quality flags
            flags = []
            if df[col].isnull().sum() > 0:
                flags.append("MISSING_VALUES")
            if df[col].nunique() == 1:
                flags.append("CONSTANT_VALUE")
            if df[col].nunique() == len(df):
                flags.append("ALL_UNIQUE")
            col_info["quality_flags"] = flags
            report.append(col_info)
        return pd.DataFrame(report)

    # Usage:
    # quality_df = data_quality_report()
    # st.dataframe(quality_df)""", language='python')
            with analysis_tabs[2]:
                st.code("""def correlation_analysis():
        \"\"\"Calculate correlations and return significant relationships\"\"\"
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.empty or len(numeric_df.columns) < 2:
            return "Need at least 2 numeric columns"
        corr_matrix = numeric_df.corr()
        significant = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr = corr_matrix.iloc[i, j]
                if abs(corr) > 0.5:  # Strong correlation threshold
                    significant.append({
                        "feature1": corr_matrix.columns[i],
                        "feature2": corr_matrix.columns[j],
                        "correlation": f"{corr:.3f}",
                        "strength": "STRONG" if abs(corr) > 0.7 else "MODERATE",
                        "direction": "POSITIVE" if corr > 0 else "NEGATIVE"
                    })
        return pd.DataFrame(significant)

    # Usage:
    # correlations = correlation_analysis()
    # st.dataframe(correlations)""", language='python')
        return config

    def _generate_dataset_context(self) -> dict:
        sample_rows = 3 if len(self.df) >= 3 else len(self.df)
        first_numeric = self.numeric_cols[0] if self.numeric_cols else None
        second_numeric = self.numeric_cols[1] if len(self.numeric_cols) > 1 else first_numeric
        first_categorical = self.categorical_cols[0] if self.categorical_cols else None

        def format_columns(cols, limit=5):
            if not cols:
                return "None"
            if len(cols) <= limit:
                return ", ".join(cols)
            return ", ".join(cols[:limit]) + f" (+{len(cols)-limit} more)"

        sample_data = []
        if not self.df.empty:
            first_5_cols = self.df.columns
            for idx, row in self.df.head(sample_rows).iterrows():
                row_str = f"Row {idx}: " + " | ".join(
                    f"{col}: {str(row[col])}"
                    for col in first_5_cols
                )
                sample_data.append(row_str)

        return {
            "rows": len(self.df),
            "cols": len(self.df.columns),
            "num_numeric": len(self.numeric_cols),
            "numeric_cols_formatted": format_columns(self.numeric_cols),
            "num_categorical": len(self.categorical_cols),
            "categorical_cols_formatted": format_columns(self.categorical_cols),
            "num_datetime": len(self.datetime_cols),
            "datetime_cols_formatted": format_columns(self.datetime_cols),
            "sample_data": "\n".join(sample_data) if sample_data else "No data available",
            "first_numeric": first_numeric or "column_name",
            "second_numeric": second_numeric or "other_column",
            "first_categorical": first_categorical or "category_column",
        }

    def _build_custom_chart_template(self, context: dict) -> str:
        template = f'''# Data Explorer Pro - Custom Visualization
# BODZZ Analytics Platform v1.0.0 | Developed by Abdallah A Khames
#
# This template provides immediate visualization capabilities AND rich context
# for AI-assisted code generation. The structure is dual-purpose:
# - Human-readable documentation
# - AI-parseable metadata
#
# ============================================================================
# DATASET CONTEXT (Structured for Human & AI)
# ============================================================================
# Dataset Shape: {context['rows']} rows × {context['cols']} columns
#
# COLUMN OVERVIEW:
# Numeric Columns ({context['num_numeric']}):
#   {context['numeric_cols_formatted']}
#
# Categorical Columns ({context['num_categorical']}):
#   {context['categorical_cols_formatted']}
#
# Datetime Columns ({context['num_datetime']}):
#   {context['datetime_cols_formatted']}
#
# SAMPLE DATA (First {min(3, context['rows'])} rows):
# {context['sample_data']}
#
# ============================================================================
# QUICK START - Edit below this line
# ============================================================================

import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from plotly.subplots import make_subplots

# Available variables:
#   df     : Your dataset (pandas DataFrame)
#   px     : Plotly Express (quick charts)
#   go     : Plotly Graph Objects (advanced control)
#   np     : NumPy (numerical operations)
#   pd     : pandas (data manipulation)
#   make_subplots : Multi-panel dashboards

# ============================================
# EXAMPLE 1: Basic Visualization (Uncomment to use)
# ============================================
fig = px.scatter(
    df,
    x='{context['first_numeric']}',
    y='{context['second_numeric']}',
    title='Scatter Plot: {context['first_numeric']} vs {context['second_numeric']}'
)

# ============================================
# EXAMPLE 2: Multi-panel Dashboard (Advanced)
# ============================================
# fig = make_subplots(
#     rows=2, cols=2,
#     subplot_titles=(
#         f'Distribution of {context['first_numeric']}',
#         f'Correlation Heatmap',
#         f'Time Series (if date column exists)',
#         f'Categorical Breakdown'
#     ),
#     specs=[
#         [{{"type": "histogram"}}, {{"type": "heatmap"}}],
#         [{{"type": "scatter"}}, {{"type": "bar"}}]
#     ]
# )
#
# # Add traces to subplots
# fig.add_trace(go.Histogram(x=df['{context['first_numeric']}'], name='Hist'), row=1, col=1)
# fig.add_trace(go.Bar(x=df['{context['first_categorical']}'].value_counts().index[:10],
#                      y=df['{context['first_categorical']}'].value_counts().values[:10],
#                      name='Top Categories'), row=2, col=2)

# ============================================
# PRO TIPS:
# ============================================
# 1. Always create 'fig' variable - this is what gets displayed
# 2. Check column existence: if 'column_name' in df.columns
# 3. Handle missing data: df['col'].fillna(method) before plotting
# 4. For large datasets, sample: df_sample = df.sample(5000, random_state=42)
# 5. Use fig.update_layout() for custom styling
# 6. Add interactivity: fig.update_layout(hovermode='x unified')

# ============================================
# DATA ANALYSIS HELPERS (Uncomment as needed)
# ============================================
# def analyze_column(column_name):
#     """Quick column analysis - returns summary stats"""
#     if column_name not in df.columns:
#         return f"Column '{{column_name}}' not found"
#
#     col = df[column_name]
#     result = {{
#         "column": column_name,
#         "dtype": str(col.dtype),
#         "non_null": col.count(),
#         "null_pct": f"{{(col.isnull().sum() / len(df)) * 100:.1f}}%",
#         "unique_values": col.nunique(),
#     }}
#
#     if pd.api.types.is_numeric_dtype(col):
#         result.update({{
#             "min": f"{{col.min():.2f}}",
#             "max": f"{{col.max():.2f}}",
#             "mean": f"{{col.mean():.2f}}",
#             "std": f"{{col.std():.2f}}",
#             "q1": f"{{col.quantile(0.25):.2f}}",
#             "median": f"{{col.median():.2f}}",
#             "q3": f"{{col.quantile(0.75):.2f}}",
#         }})
#     elif pd.api.types.is_datetime64_any_dtype(col):
#         result.update({{
#             "range": f"{{col.min().date()}} to {{col.max().date()}}",
#             "time_span": str(col.max() - col.min())
#         }})
#     elif pd.api.types.is_categorical_dtype(col) or pd.api.types.is_object_dtype(col):
#         top_values = col.value_counts().head(5)
#         result["top_5_values"] = dict(top_values)
#
#     return result

# Example usage: print(analyze_column('{context['first_numeric']}'))

# ============================================
# FINAL CHART CUSTOMIZATION
# ============================================
# Uncomment and customize any of these:

# Professional styling
fig.update_layout(
    template="plotly_white",
    font_family="Arial",
    title_font_size=18,
    hoverlabel=dict(
        bgcolor="white",
        font_size=12,
        font_family="Arial"
    )
)

# Add company branding (subtle)
fig.add_annotation(
    x=1, y=1.02,
    xref="paper", yref="paper",
    text="📊 Data Explorer Pro | BODZZ",
    showarrow=False,
    font=dict(size=10, color="#667eea"),
    align="right"
)

# The 'fig' variable MUST exist for the final chart/dashboard to render
'''
        return template

    # ===== Core Methods =====
    def get_chart_types_display(self) -> Dict[str, str]:
        return self.CHART_TYPES

    def render_unified_chart_interface(self, chart_type: str) -> Dict[str, Any]:
        config_methods = {
            'histogram': self.configure_histogram,
            'scatter': self.configure_scatter,
            'bubble': self.configure_bubble,
            'line': self.configure_line,
            'bar': self.configure_bar,
            'box': self.configure_box,
            'pie': self.configure_pie,
            'violin': self.configure_violin,
            'heatmap': self.configure_heatmap,
            'treemap': self.configure_treemap,
            'bubble_map': self.configure_bubble_map,
            'card': self.configure_card,
            'kpi': self.configure_kpi,
            'gauge': self.configure_gauge,
            'custom_chart': self.configure_custom_chart,
        }
        if chart_type in config_methods:
            return config_methods[chart_type]()
        return {"type": chart_type}

    def manual_chart_interface(self):
        """Main UI for manual chart creation."""
        st.header("📈 Create Visualizations")

        selected_type = st.selectbox(
            "Choose visualization type",
            options=list(self.CHART_TYPES.keys()),
            format_func=lambda x: self.CHART_TYPES[x],
            key=f"{self.key_prefix}_manual_chart_type",
        )

        config = self.render_unified_chart_interface(selected_type)

        # Validate configuration using the service
        valid, msg = self.chart_service.validate_config(self.df, selected_type, config)
        errors = [] if valid else [msg]

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if errors:
                st.error("Configuration errors:\n" + "\n".join(f"• {e}" for e in errors))
                st.button("Generate Chart", type="primary", use_container_width=True, disabled=True)
            else:
                if st.button("Generate Chart", type="primary", use_container_width=True):
                    self._create_chart(selected_type, config)

    def _create_chart(self, chart_type: str, config: Dict[str, Any]):
        """Create chart using the ChartService and store in session state."""
        try:
            with st.spinner("Creating visualization..."):
                fig = self.chart_service.create_chart(self.df, chart_type, config)
                if fig:
                    st.session_state.current_chart = {
                        'figure': fig,
                        'config': config,
                        'type': chart_type,
                        'created_at': time.time(),
                    }
                    st.success("Chart created successfully")
                else:
                    st.error("Failed to create chart")
        except Exception as e:
            st.error(f"Failed to create chart: {str(e)}")

    def get_configuration(self, chart_type: str) -> Dict[str, Any]:
        return self.render_unified_chart_interface(chart_type)

    def get_configuration_preserved(self, chart_type: str, current_config: Dict[str, Any] = None) -> Dict[str, Any]:
        if chart_type in self.CHART_TYPES:
            new_config = self.render_unified_chart_interface(chart_type)
            if current_config:
                for key, new_value in new_config.items():
                    if new_value is not None:
                        current_config[key] = new_value
                return current_config
            return new_config
        return current_config or {"type": chart_type}

    # ===== Utility Methods =====
    def _auto_detect_geo_columns(self) -> tuple:
        lat_candidates = [col for col in self.df.columns if any(geo in col.lower() for geo in ['lat', 'latitude'])]
        lon_candidates = [col for col in self.df.columns if any(geo in col.lower() for geo in ['lon', 'long', 'longitude'])]
        default_lat = lat_candidates[0] if lat_candidates else (self.numeric_cols[0] if self.numeric_cols else None)
        default_lon = lon_candidates[0] if lon_candidates else (self.numeric_cols[1] if len(self.numeric_cols) > 1 else default_lat)
        return default_lat, default_lon

    def _configure_target_settings(self, config: dict):
        target_type = st.radio(
            "Target Source",
            ["None", "Fixed Value", "Column"],
            horizontal=True,
            key=f"{self.key_prefix}_target_type",
        )
        if target_type == "Fixed Value":
            config["target_value"] = st.number_input("Target Value", value=0.0, key=f"{self.key_prefix}_target_val")
        elif target_type == "Column":
            config["target_col"] = self._select_numeric("Target Column", key_suffix="target_col")
            config["target_agg"] = self._select_column(
                "Target Aggregation",
                ["mean", "sum", "median", "min", "max"],
                key_suffix="target_agg",
            )
        polarity = st.radio(
            "Goal Direction",
            ["Higher is Better", "Lower is Better"],
            horizontal=True,
            key=f"{self.key_prefix}_polarity",
        )
        config["polarity"] = "higher" if "Higher" in polarity else "lower"