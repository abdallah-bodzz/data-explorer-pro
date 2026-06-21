# ai_charts_utils.py - ENHANCED CANONICAL SCHEMA AUTHORITY
"""
Chart utilities for Data Explorer Pro - Unified chart generation with family-aware normalization.
Single source of truth for field names, chart families, and production mapping.
"""

import pandas as pd
import logging
from typing import Dict, Any, List, Optional, Tuple, Set, Union
import re
import json
import hashlib
import plotly.express as px
import plotly.graph_objects as go
import time
import numpy as np
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

try:
    from core.charts.templates import (
        plot_plotly_histogram,
        plot_plotly_scatter,
        plot_plotly_pie_chart,
        plot_plotly_box_plot,
        plot_plotly_heatmap,
        plot_plotly_violin_plot,
        plot_plotly_bubble_chart,
        plot_plotly_treemap,
        plot_plotly_bubble_map,
        plot_plotly_correlation_matrix,
        plot_card,
        plot_kpi,
        plot_gauge,
    )
except ImportError as e:
    logger.warning(f"Import failed: {e}")

try:
    from core.charts.bar_line import plot_plotly_line_chart, plot_plotly_bar_chart
except ImportError as e:
    logger.warning(f"Import failed for bar_line_charts: {e}")

# ============================================================================
# ENUMS & DATA CLASSES FOR BETTER TYPE SAFETY
# ============================================================================

class ChartFamily(Enum):
    """Chart family classification."""
    XY = "xy"
    METRIC = "metric"
    HIERARCHICAL = "hierarchical"
    GEOSPATIAL = "geospatial"
    SPECIAL = "special"

class AggregationMethod(Enum):
    """Supported aggregation methods."""
    SUM = "sum"
    MEAN = "mean"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    MEDIAN = "median"
    FIRST = "first"
    LAST = "last"
    AUTO = "auto"

@dataclass
class ChartValidationResult:
    """Structured validation result."""
    is_valid: bool
    message: str
    level: str  # 'success', 'warning', 'error'
    missing_fields: List[str] = None
    invalid_columns: List[str] = None
    
    def __post_init__(self):
        if self.missing_fields is None:
            self.missing_fields = []
        if self.invalid_columns is None:
            self.invalid_columns = []

# ============================================================================
# CANONICAL SCHEMA - ENHANCED WITH ALL CHART TYPES
# ============================================================================

SUPPORTED_CHART_TYPES: Set[str] = {
    "histogram", "bar", "line", "scatter", "box", "pie",
    "violin", "bubble", "treemap", "heatmap",
    "card", "kpi", "gauge", "bubble_map", "correlation_matrix"
}

# Expanded aliases for better AI understanding
CHART_TYPE_ALIASES: Dict[str, str] = {
    # Histogram aliases
    "histogram": "histogram", "hist": "histogram", "distribution": "histogram", "freq": "histogram",
    # Bar chart aliases
    "bar": "bar", "barchart": "bar", "column": "bar", "column_chart": "bar",
    # Line chart aliases
    "line": "line", "linechart": "line", "timeseries": "line", "trend": "line", "series": "line",
    # Scatter plot aliases
    "scatter": "scatter", "scatterplot": "scatter", "xyplot": "scatter", "correlation_plot": "scatter",
    # Box plot aliases
    "box": "box", "boxplot": "box", "box_plot": "box", "box_and_whisker": "box",
    # Pie chart aliases
    "pie": "pie", "piechart": "pie", "donut": "pie", "circle": "pie", "circular": "pie",
    # Violin plot aliases
    "violin": "violin", "violinplot": "violin", "violin_plot": "violin",
    # Bubble chart aliases
    "bubble": "bubble", "bubblechart": "bubble", "bubble_plot": "bubble",
    # Treemap aliases
    "treemap": "treemap", "tree_map": "treemap", "hierarchy": "treemap", "tree": "treemap",
    # Heatmap aliases
    "heatmap": "heatmap", "heat_map": "heatmap", "matrix": "heatmap",
    # Card aliases
    "card": "card", "big_number": "card", "metric": "card", "single_metric": "card", "value_card": "card",
    # KPI aliases
    "kpi": "kpi", "key_performance_indicator": "kpi", "performance": "kpi", "indicator": "kpi",
    # Gauge aliases
    "gauge": "gauge", "meter": "gauge", "dial": "gauge", "progress": "gauge", "speedometer": "gauge",
    # Bubble map aliases
    "bubble_map": "bubble_map", "geo_bubble": "bubble_map", "map": "bubble_map", 
    "geographic": "bubble_map", "choropleth": "bubble_map", "geo": "bubble_map",
    # Correlation matrix aliases
    "correlation_matrix": "correlation_matrix", "correlation": "correlation_matrix", 
    "correlation_heatmap": "correlation_matrix", "corr_matrix": "correlation_matrix",
}

# ============================================================================
# ENHANCED CHART FAMILIES SYSTEM
# ============================================================================

CHART_FAMILIES: Dict[str, Dict[str, Any]] = {
    # XY Charts: Standard x-y relationships (most common)
    ChartFamily.XY.value: {
        'name': 'XY Charts',
        'charts': ['bar', 'line', 'scatter', 'histogram', 'box', 'violin', 'heatmap', 'bubble'],
        'required': ['x'],
        'optional': ['y', 'color', 'size', 'facet_col', 'text'],
        'field_mapping': {
            'x_axis': 'x', 'x_col': 'x', 'x_field': 'x', 'x_column': 'x', 'category': 'x',
            'y_axis': 'y', 'y_col': 'y', 'y_field': 'y', 'y_column': 'y', 'value': 'y',
            'series': 'color', 'group_by': 'color', 'category_color': 'color', 'group': 'color',
            'bubble_size': 'size', 'marker_size': 'size', 'size_field': 'size',
        },
        'description': 'Compare values, track trends, show distributions and relationships',
        'icon': '📊'
    },
    
    # Metric Charts: Single value displays (KPI focused)
    ChartFamily.METRIC.value: {
        'name': 'Metric Charts',
        'charts': ['card', 'kpi', 'gauge'],
        'required': ['value_col'],
        'optional': ['agg_func', 'target_value', 'prefix', 'suffix', 'comparison_period'],
        'field_mapping': {
            'value': 'value_col', 'metric': 'value_col', 'measure': 'value_col',
            'y': 'value_col', 'measurement': 'value_col', 'key_metric': 'value_col',
            'target': 'target_value', 'goal': 'target_value', 'threshold': 'target_value',
            'aggregation': 'agg_func', 'agg': 'agg_func', 'function': 'agg_func',
        },
        'description': 'Display key performance indicators and single metrics',
        'icon': '🎯'
    },
    
    # Hierarchical Charts: Nested relationships
    ChartFamily.HIERARCHICAL.value: {
        'name': 'Hierarchical Charts',
        'charts': ['treemap'],
        'required': ['path'],
        'optional': ['values', 'color', 'agg_func', 'text', 'hover_data'],
        'field_mapping': {
            'hierarchy': 'path', 'levels': 'path', 'categories': 'path',
            'x': 'path', 'breadcrumb': 'path', 'tree_path': 'path', 'structure': 'path',
            'size': 'values', 'value': 'values', 'weight': 'values',
        },
        'description': 'Show part-to-whole relationships with hierarchy',
        'icon': '🌳'
    },
    
    # Geospatial Charts: Geographic data
    ChartFamily.GEOSPATIAL.value: {
        'name': 'Geospatial Charts',
        'charts': ['bubble_map'],
        'required': ['lat_col', 'lon_col'],
        'optional': ['size_col', 'color_col', 'text_col', 'hover_name'],
        'field_mapping': {
            'latitude': 'lat_col', 'lat': 'lat_col', 'y': 'lat_col', 'lat_field': 'lat_col',
            'longitude': 'lon_col', 'lon': 'lon_col', 'long': 'lon_col', 'x': 'lon_col', 'lon_field': 'lon_col',
            'bubble_size': 'size_col', 'marker_size': 'size_col',
            'color_field': 'color_col', 'marker_color': 'color_col',
        },
        'description': 'Visualize data on maps with geographic context',
        'icon': '🗺️'
    },
    
    # Special Charts: Unique requirements
    ChartFamily.SPECIAL.value: {
        'name': 'Special Charts',
        'charts': ['correlation_matrix', 'pie'],
        'required': [],
        'optional': ['x', 'y', 'columns', 'color', 'text'],
        'field_mapping': {},
        'description': 'Specialized visualizations with unique data requirements',
        'icon': '✨'
    }
}

# Enhanced requirements with better descriptions
CHART_REQUIREMENTS: Dict[str, Dict[str, Any]] = {
    "histogram": {
        "required": ["x"],
        "optional": ["color", "facet_col", "nbins"],
        "description": "Distribution of a single numeric variable"
    },
    "bar": {
        "required": ["x"],
        "optional": ["y", "color", "orientation"],
        "description": "Comparison across categories"
    },
    "line": {
        "required": ["x", "y"],
        "optional": ["color", "line_group", "markers"],
        "description": "Trends over time or sequence"
    },
    "scatter": {
        "required": ["x", "y"],
        "optional": ["color", "size", "text", "hover_name"],
        "description": "Relationship between two numeric variables"
    },
    "box": {
        "required": ["y"],
        "optional": ["x", "color", "points"],
        "description": "Statistical summary and outliers"
    },
    "pie": {
        "required": ["x"],
        "optional": ["y", "color", "hole"],
        "description": "Composition of parts to a whole"
    },
    "violin": {
        "required": ["y"],
        "optional": ["x", "color", "box"],
        "description": "Distribution density with kernel estimation"
    },
    "bubble": {
        "required": ["x", "y"],
        "optional": ["size", "color", "text"],
        "description": "Three-dimensional relationship visualization"
    },
    "treemap": {
        "required": ["path"],
        "optional": ["values", "color", "text"],
        "description": "Hierarchical data with nested rectangles"
    },
    "heatmap": {
        "required": ["x", "y"],
        "optional": ["z", "color", "text"],
        "description": "Matrix visualization with color intensity"
    },
    "card": {
        "required": ["value_col"],
        "optional": ["agg_func", "prefix", "suffix"],
        "description": "Single metric display"
    },
    "kpi": {
        "required": ["value_col"],
        "optional": ["target_value", "agg_func", "prefix", "suffix"],
        "description": "Key performance indicator with target"
    },
    "gauge": {
        "required": ["value_col"],
        "optional": ["target_value", "min_value", "max_value", "agg_func"],
        "description": "Progress towards target"
    },
    "bubble_map": {
        "required": ["lat_col", "lon_col"],
        "optional": ["size_col", "color_col", "text_col"],
        "description": "Geographic data with bubble size encoding"
    },
    "correlation_matrix": {
        "required": [],
        "optional": ["columns", "method", "annot"],
        "description": "Correlation between multiple numeric variables"
    }
}

# Enhanced canonical defaults with better descriptions
CANONICAL_DEFAULTS: Dict[str, Any] = {
    "chart_type": "histogram",
    "x": None,
    "y": None,
    "value_col": None,
    "lat_col": None,
    "lon_col": None,
    "color": None,
    "size": None,
    "text": None,
    "facet_col": None,
    "path": None,
    "columns": None,
    "agg_func": "sum",
    "target_value": None,
    "min_value": None,
    "max_value": None,
    "prefix": "",
    "suffix": "",
    "sort": "none",
    "title": "",
    "description": "",
    "code": "",
    "id": "",
    "hover_data": None,
    "hover_name": None,
    "_normalized": False,
    "_family": None,
    "_normalized_at": None,
}

# ============================================================================
# FAMILY HELPER FUNCTIONS (ENHANCED)
# ============================================================================

def _get_chart_family(chart_type: str) -> str:
    """Determine which family a chart type belongs to with fallback."""
    for family, info in CHART_FAMILIES.items():
        if chart_type in info['charts']:
            return family
    return ChartFamily.XY.value  # Default to XY family

def _get_family_info(chart_type: str) -> Dict[str, Any]:
    """Get detailed family information for a chart type."""
    family = _get_chart_family(chart_type)
    return CHART_FAMILIES.get(family, CHART_FAMILIES[ChartFamily.XY.value])

def _apply_family_mapping(raw: Dict[str, Any], base: Dict[str, Any], family: str):
    """Apply family-specific field mapping intelligently."""
    family_info = CHART_FAMILIES.get(family, {})
    mapping = family_info.get('field_mapping', {})
    
    # Map fields based on family mapping
    for raw_key, raw_value in raw.items():
        if raw_key in mapping and raw_value is not None:
            target_key = mapping[raw_key]
            base[target_key] = raw_value
        elif raw_key in base and raw_value is not None:
            base[raw_key] = raw_value
    
    # Special intelligent handling for each family
    if family == ChartFamily.METRIC.value:
        # If y is provided but value_col isn't, map y to value_col
        if not base.get('value_col') and raw.get('y'):
            base['value_col'] = raw['y']
            base['y'] = None
        
        # Ensure agg_func is valid
        if base.get('agg_func') == 'auto':
            base['agg_func'] = 'sum'
    
    elif family == ChartFamily.HIERARCHICAL.value:
        # If x is provided but path isn't, convert x to single-item path
        if not base.get('path') and raw.get('x'):
            base['path'] = [raw['x']]
            base['x'] = None
        
        # Ensure path is always a list
        if base.get('path') and not isinstance(base['path'], list):
            base['path'] = [base['path']]
        
        # FIX: Map y/values to values field for hierarchical charts
        if not base.get('values'):
            if raw.get('values'):
                base['values'] = raw['values']
            elif raw.get('y'):
                base['values'] = raw['y']
            elif raw.get('value_col'):
                base['values'] = raw['value_col']
        
        # Set agg_func for hierarchical charts
        if base.get('agg_func') == 'auto':
            base['agg_func'] = 'sum'
    
    elif family == ChartFamily.GEOSPATIAL.value:
        # Map x/y to lon/lat as fallback with intelligent detection
        if not base.get('lat_col') and raw.get('y'):
            base['lat_col'] = raw['y']
        if not base.get('lon_col') and raw.get('x'):
            base['lon_col'] = raw['x']
        
        # Map size to size_col for geospatial charts
        if not base.get('size_col') and raw.get('size'):
            base['size_col'] = raw['size']
        
        # Try to detect geographic columns from names
        if base.get('lat_col') and 'lon' in str(base['lat_col']).lower():
            # Probably swapped
            lat = base['lat_col']
            lon = base.get('lon_col')
            if lon and 'lat' in str(lon).lower():
                base['lat_col'], base['lon_col'] = lon, lat
    
    elif family == ChartFamily.XY.value:
        # Ensure x is present for XY charts
        if not base.get('x') and raw.get('category'):
            base['x'] = raw['category']
        
        # Map values to y for XY charts
        if not base.get('y') and raw.get('values'):
            base['y'] = raw['values']
        
        # Handle date column detection for line charts
        if base.get('chart_type') == 'line' and base.get('x'):
            # Could check if x is date-like later
            pass

def _generate_chart_title(chart: Dict[str, Any], family: str) -> str:
    """Generate intelligent chart title based on family and fields."""
    chart_type = chart.get('chart_type', 'chart').title().replace('_', ' ')
    
    # Get family info for icon
    family_info = CHART_FAMILIES.get(family, {})
    family_icon = family_info.get('icon', '📊')
    
    if family == ChartFamily.METRIC.value and chart.get('value_col'):
        agg_func = chart.get('agg_func', 'sum').title()
        return f"{family_icon} {chart_type}: {agg_func} of {chart['value_col']}"
    
    elif family == ChartFamily.HIERARCHICAL.value and chart.get('path'):
        path_display = ' → '.join(chart['path'][:3])
        if len(chart['path']) > 3:
            path_display += f" (+{len(chart['path'])-3})"
        return f"{family_icon} {chart_type}: {path_display}"
    
    elif family == ChartFamily.GEOSPATIAL.value:
        if chart.get('lat_col') and chart.get('lon_col'):
            return f"{family_icon} Map: {chart['lat_col']} × {chart['lon_col']}"
        elif chart.get('x') and chart.get('y'):
            return f"{family_icon} Map: {chart['x']} × {chart['y']}"
    
    elif chart.get('x') and chart.get('y'):
        return f"{family_icon} {chart_type}: {chart['y']} by {chart['x']}"
    
    elif chart.get('x'):
        return f"{family_icon} {chart_type} of {chart['x']}"
    
    elif chart.get('value_col'):
        return f"{family_icon} {chart_type}: {chart['value_col']}"
    
    else:
        return f"{family_icon} {chart_type} Visualization"

def _generate_chart_description(chart: Dict[str, Any], family: str) -> str:
    """Generate informative chart description."""
    chart_type = chart.get('chart_type', 'chart')
    family_info = CHART_FAMILIES.get(family, {})
    
    # Get base description
    base_desc = CHART_REQUIREMENTS.get(chart_type, {}).get('description', 'Data visualization')
    
    # Add context based on fields
    context_parts = []
    
    if family == ChartFamily.METRIC.value and chart.get('target_value'):
        context_parts.append(f"Target: {chart['target_value']}")
    
    if chart.get('agg_func') and chart.get('agg_func') != 'sum':
        context_parts.append(f"Aggregation: {chart['agg_func']}")
    
    if context_parts:
        return f"{base_desc} ({', '.join(context_parts)})"
    
    return base_desc

def _create_chart_id(chart_config: Dict[str, Any]) -> str:
    """Create unique, readable chart ID."""
    chart_type = chart_config.get('chart_type', 'chart')
    timestamp = str(time.time()).replace('.', '')[:10]
    
    # Use meaningful parts for ID
    id_parts = [chart_type]
    
    if chart_config.get('x'):
        x_safe = re.sub(r'[^a-zA-Z0-9]', '', str(chart_config['x']))[:15]
        id_parts.append(x_safe)
    
    if chart_config.get('y'):
        y_safe = re.sub(r'[^a-zA-Z0-9]', '', str(chart_config['y']))[:15]
        id_parts.append(y_safe)
    
    if chart_config.get('value_col'):
        val_safe = re.sub(r'[^a-zA-Z0-9]', '', str(chart_config['value_col']))[:15]
        id_parts.append(val_safe)
    
    id_string = "_".join(filter(None, id_parts))
    
    if not id_string:
        id_string = chart_type
    
    # Add hash for uniqueness
    hash_part = hashlib.md5(f"{id_string}_{timestamp}".encode()).hexdigest()[:6]
    
    return f"chart_{id_string}_{hash_part}".lower()

def _generate_chart_code(chart: Dict[str, Any]) -> str:
    """Generate production-ready chart code."""
    chart_type = chart.get('chart_type', 'histogram')
    title = chart.get('title', 'Chart')
    
    # Map chart types to production functions
    function_map = {
        'line': 'plot_plotly_line_chart',
        'bar': 'plot_plotly_bar_chart',
        'scatter': 'plot_plotly_scatter',
        'histogram': 'plot_plotly_histogram',
        'pie': 'plot_plotly_pie_chart',
        'box': 'plot_plotly_box_plot',
        'violin': 'plot_plotly_violin_plot',
        'heatmap': 'plot_plotly_heatmap',
        'bubble': 'plot_plotly_bubble_chart',
        'treemap': 'plot_plotly_treemap',
        'card': 'plot_card',
        'kpi': 'plot_kpi',
        'gauge': 'plot_gauge',
        'bubble_map': 'plot_plotly_bubble_map',
        'correlation_matrix': 'plot_plotly_correlation_matrix',
    }
    
    function_name = function_map.get(chart_type, 'plot_plotly_histogram')
    
    # Build config dictionary
    config_lines = []
    
    if chart_type in ["card", "kpi", "gauge"] and chart.get('value_col'):
        config_lines.append(f'    "value_col": "{chart["value_col"]}",')
        if chart.get('agg_func') and chart['agg_func'] != 'sum':
            config_lines.append(f'    "agg_func": "{chart["agg_func"]}",')
        if chart.get('target_value'):
            config_lines.append(f'    "target_value": {chart["target_value"]},')
    
    elif chart_type == "bubble_map":
        if chart.get('lat_col'):
            config_lines.append(f'    "lat_col": "{chart["lat_col"]}",')
        if chart.get('lon_col'):
            config_lines.append(f'    "lon_col": "{chart["lon_col"]}",')
        if chart.get('size_col'):
            config_lines.append(f'    "size_col": "{chart["size_col"]}",')
    
    elif chart_type == "treemap":
        if chart.get('path'):
            config_lines.append(f'    "path": {chart["path"]},')
        if chart.get('values'):
            config_lines.append(f'    "values": "{chart["values"]}",')
    
    else:  # XY charts
        if chart.get('x'):
            config_lines.append(f'    "x_col": "{chart["x"]}",')
        if chart.get('y'):
            config_lines.append(f'    "y_col": "{chart["y"]}",')
        if chart.get('color'):
            config_lines.append(f'    "color_col": "{chart["color"]}",')
        if chart.get('size'):
            config_lines.append(f'    "size_col": "{chart["size"]}",')
    
    # Always add title
    config_lines.append(f'    "title": "{title}",')
    
    # Join config lines
    config_str = "\n".join(config_lines)
    
    return f"""# Data Explorer Pro - Professional Chart
# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

fig = {function_name}(df, {{
{config_str}
}})
# note: '{function_name}' is a custom wrapper around plotly express functions with enhanced defaults and styling for Data Explorer Pro, developed by dev 'Abdallah A Khames'

# Display the chart
fig.show()
"""

# ============================================================================
# ENHANCED NORMALIZATION FUNCTION
# ============================================================================

def normalize_ai_response(raw_response: Any) -> Dict[str, Any]:
    """
    Convert any AI response to canonical schema with family awareness.
    
    Handles:
    - String JSON responses
    - Dict responses
    - Partial/malformed responses
    - Family-specific field mapping
    """
    # Handle empty responses
    if not raw_response:
        return _create_empty_chart()
    
    # Convert string to dict if needed
    if isinstance(raw_response, str):
        raw_response = _parse_raw_response(raw_response)
    
    if not isinstance(raw_response, dict):
        logger.warning(f"Response is not dict: {type(raw_response)}")
        return _create_empty_chart()
    
    # Get chart type and normalize
    chart_type = raw_response.get('chart_type', 'histogram')
    if chart_type:
        chart_type = str(chart_type).lower().strip()
        chart_type = CHART_TYPE_ALIASES.get(chart_type, chart_type)
    
    # Validate chart type
    if chart_type not in SUPPORTED_CHART_TYPES:
        logger.warning(f"Unsupported chart type: {chart_type}, defaulting to histogram")
        chart_type = "histogram"
    
    # Determine family
    family = _get_chart_family(chart_type)
    family_info = CHART_FAMILIES.get(family, {})
    
    # Create family-specific base configuration
    if family == ChartFamily.METRIC.value:
        base = {
            'chart_type': chart_type,
            'value_col': None,
            'agg_func': 'sum',
            'target_value': None,
            'prefix': '',
            'suffix': '',
            'title': '',
            'description': '',
            'x': None,
            'y': None
        }
    elif family == ChartFamily.HIERARCHICAL.value:
        base = {
            'chart_type': chart_type,
            'path': [],
            'values': None,
            'color': None,
            'agg_func': 'sum',
            'title': '',
            'description': '',
            'x': None,
            'y': None
        }
    elif family == ChartFamily.GEOSPATIAL.value:
        base = {
            'chart_type': chart_type,
            'lat_col': None,
            'lon_col': None,
            'size_col': None,
            'color_col': None,
            'title': '',
            'description': '',
            'x': None,
            'y': None
        }
    else:  # XY or special
        base = {
            'chart_type': chart_type,
            'x': None,
            'y': None,
            'color': None,
            'size': None,
            'text': None,
            'facet_col': None,
            'title': '',
            'description': ''
        }
    
    # Apply family-specific mapping
    _apply_family_mapping(raw_response, base, family)
    
    # Fill in missing defaults
    for key, default_value in CANONICAL_DEFAULTS.items():
        if key not in base:
            base[key] = default_value
    
    # Override with any direct values from raw response
    for key, value in raw_response.items():
        if value is not None and key in base:
            base[key] = value
    
    # Clean and normalize field values
    _clean_chart_fields(base)
    
    # Special array handling
    if family == ChartFamily.HIERARCHICAL.value and isinstance(base.get('path'), str):
        base['path'] = [base['path']]
    
    # Generate missing fields
    if not base.get('id'):
        base['id'] = _create_chart_id(base)
    
    if not base.get('title'):
        base['title'] = _generate_chart_title(base, family)
    
    if not base.get('description'):
        base['description'] = _generate_chart_description(base, family)
    
    if not base.get('code'):
        base['code'] = _generate_chart_code(base)
    
    # Add metadata
    base['_normalized'] = True
    base['_family'] = family
    base['_normalized_at'] = time.time()
    base['_family_name'] = family_info.get('name', 'Unknown')
    
    # Add source if available
    if '_source' in raw_response:
        base['_source'] = raw_response['_source']
    
    return base

def _parse_raw_response(text: str) -> Dict[str, Any]:
    """Parse raw text response into dict with error recovery."""
    if not text:
        return {}
    
    # Try to extract JSON from text
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError as e:
            logger.debug(f"JSON parse failed, trying to fix: {e}")
            # Try to fix common JSON issues
            fixed = _fix_json_issues(json_match.group())
            try:
                return json.loads(fixed)
            except:
                pass
    
    # Fallback: extract key-value pairs
    result = {}
    lines = text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if ':' in line:
            try:
                key, value = line.split(':', 1)
                key = key.strip().strip('"\'').strip()
                value = value.strip().strip('"\'').strip()
                
                # Convert numeric strings
                if value.isdigit():
                    value = int(value)
                elif value.replace('.', '', 1).isdigit() and value.count('.') == 1:
                    value = float(value)
                elif value.lower() in ['true', 'false']:
                    value = value.lower() == 'true'
                elif value.lower() == 'null':
                    value = None
                
                if key and value is not None:
                    result[key] = value
            except:
                continue
    
    return result

def _fix_json_issues(json_str: str) -> str:
    """Fix common JSON issues from AI responses."""
    fixes = [
        # Remove trailing commas
        (r',\s*([}\]])', r'\1'),
        # Fix unquoted keys
        (r'(\s*)(\w+)(\s*):', r'\1"\2"\3:'),
        # Replace Python constants
        (r'\bNone\b', 'null'),
        (r'\bTrue\b', 'true'),
        (r'\bFalse\b', 'false'),
        # Remove comments
        (r'//.*', ''),
        (r'/\*.*?\*/', '', re.DOTALL),
    ]
    
    for pattern, replacement in fixes:
        if len(pattern) == 3:
            json_str = re.sub(pattern[0], replacement, json_str, flags=pattern[2])
        else:
            json_str = re.sub(pattern, replacement, json_str)
    
    return json_str

def _clean_chart_fields(chart: Dict[str, Any]):
    """Clean and normalize chart field values."""
    for field in ["x", "y", "value_col", "lat_col", "lon_col", "color", "size", "text", "title", "description"]:
        if field in chart:
            value = chart[field]
            if value in [None, "", "null", "None"]:
                chart[field] = None
            elif isinstance(value, str):
                chart[field] = value.strip()
                # Remove excessive whitespace
                chart[field] = re.sub(r'\s+', ' ', chart[field])
    
    # Clean path array
    if chart.get('path'):
        if isinstance(chart['path'], list):
            chart['path'] = [str(item).strip() for item in chart['path'] if item]
        else:
            chart['path'] = [str(chart['path']).strip()]

def _create_empty_chart() -> Dict[str, Any]:
    """Create a properly formatted empty chart."""
    empty = CANONICAL_DEFAULTS.copy()
    empty["id"] = f"chart_empty_{int(time.time())}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:6]}"
    empty["title"] = "Empty Chart"
    empty["description"] = "No chart data available"
    empty["_normalized"] = True
    empty["_empty"] = True
    empty["_created_at"] = time.time()
    return empty

# ============================================================================
# ENHANCED VALIDATION SYSTEM
# ============================================================================

def validate_chart_possibility(chart_config: Dict[str, Any], df: pd.DataFrame) -> ChartValidationResult:
    """
    Validate if a chart is possible with the given data.
    Returns structured validation result.
    """
    chart_type = chart_config.get('chart_type')
    if not chart_type:
        return ChartValidationResult(
            is_valid=False,
            message="Missing chart_type",
            level="error",
            missing_fields=["chart_type"]
        )
    
    # Get family and requirements
    family = chart_config.get('_family') or _get_chart_family(chart_type)
    family_info = CHART_FAMILIES.get(family, {})
    chart_reqs = CHART_REQUIREMENTS.get(chart_type, {})
    
    required_fields = family_info.get('required', []) + chart_reqs.get('required', [])
    missing_fields = []
    invalid_columns = []
    warnings = []
    
    # Check required fields
    for field in required_fields:
        if not chart_config.get(field):
            missing_fields.append(field)
    
    if missing_fields:
        return ChartValidationResult(
            is_valid=False,
            message=f"{chart_type} requires: {', '.join(missing_fields)}",
            level="error",
            missing_fields=missing_fields
        )
    
    # Validate fields against dataframe
    validation_checks = {
        ChartFamily.METRIC.value: _validate_metric_chart,
        ChartFamily.HIERARCHICAL.value: _validate_hierarchical_chart,
        ChartFamily.GEOSPATIAL.value: _validate_geospatial_chart,
        ChartFamily.XY.value: _validate_xy_chart,
        ChartFamily.SPECIAL.value: _validate_special_chart,
    }
    
    validator = validation_checks.get(family, _validate_xy_chart)
    return validator(chart_config, df, chart_type, family)

def _validate_metric_chart(chart: Dict, df: pd.DataFrame, chart_type: str, family: str) -> ChartValidationResult:
    """Validate metric charts (card, kpi, gauge)."""
    invalid_columns = []
    warnings = []
    
    # Check value column
    value_col = chart.get('value_col')
    if value_col and value_col not in df.columns:
        invalid_columns.append(f"value_col: '{value_col}'")
    
    # Check target value type
    target = chart.get('target_value')
    if target and isinstance(target, str) and target in df.columns:
        warnings.append("'target_value' should be a number, not column name")
    
    # Check aggregation function
    agg_func = chart.get('agg_func', 'sum')
    if agg_func not in [a.value for a in AggregationMethod]:
        warnings.append(f"Aggregation '{agg_func}' may not be supported")
    
    if invalid_columns:
        return ChartValidationResult(
            is_valid=False,
            message=f"Invalid columns: {', '.join(invalid_columns)}",
            level="error",
            invalid_columns=invalid_columns
        )
    
    return ChartValidationResult(
        is_valid=True,
        message="Valid metric chart",
        level="warning" if warnings else "success",
        invalid_columns=invalid_columns
    )

def _validate_hierarchical_chart(chart: Dict, df: pd.DataFrame, chart_type: str, family: str) -> ChartValidationResult:
    """Validate hierarchical charts (treemap)."""
    invalid_columns = []
    
    # Check path columns
    path = chart.get('path', [])
    if not isinstance(path, list):
        return ChartValidationResult(
            is_valid=False,
            message="'path' must be an array",
            level="error"
        )
    
    for col in path:
        if col not in df.columns:
            invalid_columns.append(f"path: '{col}'")
    
    # Check values column if provided
    values = chart.get('values')
    if values and values not in df.columns:
        invalid_columns.append(f"values: '{values}'")
    
    if invalid_columns:
        return ChartValidationResult(
            is_valid=False,
            message=f"Invalid columns: {', '.join(invalid_columns)}",
            level="error",
            invalid_columns=invalid_columns
        )
    
    return ChartValidationResult(
        is_valid=True,
        message="Valid hierarchical chart",
        level="success"
    )

def _validate_geospatial_chart(chart: Dict, df: pd.DataFrame, chart_type: str, family: str) -> ChartValidationResult:
    """Validate geospatial charts (bubble_map)."""
    invalid_columns = []
    
    # Check required columns
    lat_col = chart.get('lat_col')
    lon_col = chart.get('lon_col')
    
    if lat_col and lat_col not in df.columns:
        invalid_columns.append(f"lat_col: '{lat_col}'")
    
    if lon_col and lon_col not in df.columns:
        invalid_columns.append(f"lon_col: '{lon_col}'")
    
    # Check optional columns
    for field in ['size_col', 'color_col', 'text_col']:
        col = chart.get(field)
        if col and col not in df.columns:
            invalid_columns.append(f"{field}: '{col}'")
    
    if invalid_columns:
        return ChartValidationResult(
            is_valid=False,
            message=f"Invalid columns: {', '.join(invalid_columns)}",
            level="error",
            invalid_columns=invalid_columns
        )
    
    return ChartValidationResult(
        is_valid=True,
        message="Valid geospatial chart",
        level="success"
    )

def _validate_xy_chart(chart: Dict, df: pd.DataFrame, chart_type: str, family: str) -> ChartValidationResult:
    """Validate XY charts (bar, line, scatter, etc.)."""
    invalid_columns = []
    warnings = []
    
    # Check required columns
    required_map = {
        'histogram': ['x'],
        'bar': ['x'],
        'line': ['x', 'y'],
        'scatter': ['x', 'y'],
        'box': ['y'],
        'violin': ['y'],
        'bubble': ['x', 'y'],
        'heatmap': ['x', 'y'],
        'pie': ['x'],
    }
    
    required = required_map.get(chart_type, ['x'])
    for field in required:
        col = chart.get(field)
        if col and col not in df.columns:
            invalid_columns.append(f"{field}: '{col}'")
    
    # Check optional columns
    for field in ['color', 'size', 'text', 'facet_col']:
        col = chart.get(field)
        if col and col not in df.columns:
            warnings.append(f"Optional column '{field}' not found: '{col}'")
    
    # Check data types
    if chart.get('x') in df.columns:
        x_col = chart['x']
        if chart_type == 'line' and not pd.api.types.is_datetime64_any_dtype(df[x_col]):
            warnings.append(f"X column '{x_col}' may not be datetime for line chart")
    
    if invalid_columns:
        return ChartValidationResult(
            is_valid=False,
            message=f"Invalid columns: {', '.join(invalid_columns)}",
            level="error",
            invalid_columns=invalid_columns
        )
    
    return ChartValidationResult(
        is_valid=True,
        message="Valid XY chart",
        level="warning" if warnings else "success"
    )

def _validate_special_chart(chart: Dict, df: pd.DataFrame, chart_type: str, family: str) -> ChartValidationResult:
    """Validate special charts (correlation_matrix, etc.)."""
    if chart_type == 'correlation_matrix':
        # Auto-detects numeric columns
        numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
        if len(numeric_cols) < 2:
            return ChartValidationResult(
                is_valid=False,
                message="Need at least 2 numeric columns for correlation matrix",
                level="error"
            )
        return ChartValidationResult(
            is_valid=True,
            message=f"Valid correlation matrix ({len(numeric_cols)} numeric columns)",
            level="success"
        )
    
    return ChartValidationResult(
        is_valid=True,
        message=f"Valid {chart_type} chart",
        level="success"
    )

def validate_canonical_chart(canonical: Dict[str, Any], df: pd.DataFrame) -> Tuple[bool, str]:
    """Backward-compatible validation function."""
    result = validate_chart_possibility(canonical, df)
    return result.is_valid, result.message

def validate_and_explain_chart(df: pd.DataFrame, chart_config: Dict[str, Any]) -> Dict[str, Any]:
    """Comprehensive chart validation with explanations."""
    result = {
        'valid': False,
        'errors': [],
        'warnings': [],
        'suggestions': [],
        'family': None,
        'requirements_met': False,
    }
    
    chart_type = chart_config.get('chart_type')
    if not chart_type:
        result['errors'].append("Missing chart type")
        return result
    
    # Get family info
    family = _get_chart_family(chart_type)
    result['family'] = family
    family_info = CHART_FAMILIES.get(family, {})
    
    if chart_type not in SUPPORTED_CHART_TYPES:
        result['errors'].append(f"Unsupported chart type: {chart_type}")
        # Suggest similar
        similar = [t for t in SUPPORTED_CHART_TYPES if chart_type in t or t in chart_type]
        if similar:
            result['suggestions'].append(f"Try: {', '.join(similar[:3])}")
        return result
    
    # Check columns exist
    missing_cols = []
    for field in ['x', 'y', 'value_col', 'lat_col', 'lon_col', 'color', 'size', 'text']:
        col = chart_config.get(field)
        if col and col not in df.columns:
            missing_cols.append(f"{field}: '{col}'")
    
    if missing_cols:
        result['errors'].append(f"Missing columns: {', '.join(missing_cols)}")
        
        # Suggest similar column names
        for missing in missing_cols:
            field, col = missing.split(": ")
            col = col.strip("'")
            similar = [c for c in df.columns if col.lower() in c.lower() or c.lower() in col.lower()]
            if similar:
                result['suggestions'].append(f"For '{col}', try: {', '.join(similar[:2])}")
    
    # Check data types for key fields
    if chart_config.get('x') in df.columns:
        x_col = chart_config['x']
        if chart_type == 'line' and not pd.api.types.is_datetime64_any_dtype(df[x_col]):
            result['warnings'].append(f"X column '{x_col}' may not be optimal for line chart (not datetime)")
    
    if chart_config.get('y') in df.columns:
        y_col = chart_config['y']
        if chart_type in ['histogram', 'box', 'violin'] and not pd.api.types.is_numeric_dtype(df[y_col]):
            result['warnings'].append(f"Y column '{y_col}' should be numeric for {chart_type}")
    
    # Check for aggregation needs
    if chart_type in ['bar', 'pie'] and chart_config.get('y'):
        if df.duplicated(subset=[chart_config.get('x')]).any():
            result['suggestions'].append(f"Consider aggregation for '{chart_config.get('y')}'")
    
    result['valid'] = len(result['errors']) == 0
    result['requirements_met'] = len(result['errors']) == 0
    
    return result

# ============================================================================
# ENHANCED PRODUCTION CHART ADAPTER
# ============================================================================

class ProductionChartAdapter:
    """Maps AI configs to production chart functions with intelligent defaults."""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self._memoized_figs = {}
    
    def create_chart(self, config: Dict[str, Any]) -> go.Figure:
        """Convert AI config → production chart with caching."""
        chart_id = config.get('id')
        
        # Check cache
        if chart_id and chart_id in self._memoized_figs:
            logger.debug(f"Using cached figure for {chart_id}")
            return self._memoized_figs[chart_id]
        
        chart_type = config.get('chart_type')
        
        try:
            # Validate first
            validation = validate_chart_possibility(config, self.df)
            if not validation.is_valid:
                logger.warning(f"Chart validation failed: {validation.message}")
                return self._create_validation_error_figure(validation)
            
            # Map to production config
            production_config = self._map_config(config)
            
            # Create chart
            fig = self._call_production_function(chart_type, production_config)
            
            # Cache if has ID
            if chart_id:
                self._memoized_figs[chart_id] = fig
            
            return fig
            
        except Exception as e:
            logger.error(f"Production chart failed: {e}")
            return self._create_error_figure(f"Chart creation error: {str(e)[:100]}")
    
    def _map_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Map AI config to production config with intelligent defaults."""
        chart_type = config.get('chart_type')
        
        # Family-specific mappers
        mapper_map = {
            'line': self._map_line,
            'bar': self._map_bar,
            'scatter': self._map_scatter,
            'histogram': self._map_histogram,
            'pie': self._map_pie,
            'box': self._map_box,
            'violin': self._map_violin,
            'heatmap': self._map_heatmap,
            'bubble': self._map_bubble,
            'treemap': self._map_treemap,
            'card': self._map_card,
            'kpi': self._map_kpi,
            'gauge': self._map_gauge,
            'bubble_map': self._map_bubble_map,
            'correlation_matrix': self._map_correlation_matrix,
        }
        
        mapper = mapper_map.get(chart_type)
        if not mapper:
            raise ValueError(f"No mapper for {chart_type}")
        
        mapped = mapper(config)
        
        # Always add title
        if 'title' not in mapped or not mapped['title']:
            mapped['title'] = config.get('title', f"{chart_type.title()} Chart")
        
        return mapped
    
    def _map_line(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Map line chart config."""
        return {
            'date_col': config.get('x'),
            'value_cols': [config.get('y')] if config.get('y') else [],
            'group_col': config.get('color'),
            'title': config.get('title', ''),
            'line_shape': 'linear',
            'markers': True,
        }
    
    def _map_bar(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Map bar chart config."""
        return {
            'x_col': config.get('x'),
            'y_cols': [config.get('y')] if config.get('y') else [],
            'color_col': config.get('color'),
            'title': config.get('title', ''),
            'orientation': 'v',
            'barmode': 'group',
        }
    
    def _map_scatter(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Map scatter plot config."""
        return {
            'x_col': config.get('x'),
            'y_col': config.get('y'),
            'color_col': config.get('color'),
            'size_col': config.get('size'),
            'title': config.get('title', ''),
            'trendline': 'ols' if config.get('show_trendline') else None,
        }
    
    def _map_histogram(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Map histogram config."""
        return {
            'x_col': config.get('x'),
            'color_col': config.get('color'),
            'title': config.get('title', ''),
            'nbins': 30,
            'histnorm': 'probability density',
        }
    
    def _map_pie(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Map pie chart config."""
        agg_func = config.get('agg_func', 'sum')
        if agg_func == 'auto':
            agg_func = 'sum'
            
        return {
            'names_col': config.get('x'),
            'values_col': config.get('y'),
            'agg_func': agg_func,
            'title': config.get('title', ''),
            'hole': 0.3 if config.get('donut') else 0,
        }
    
    def _map_box(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Map box plot config."""
        return {
            'y_col': config.get('y'),
            'x_col': config.get('x'),
            'color_col': config.get('color'),
            'title': config.get('title', ''),
            'points': 'outliers',
        }
    
    def _map_violin(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Map violin plot config."""
        return self._map_box(config)
    
    def _map_heatmap(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Map heatmap config."""
        return {
            'numeric_cols': [config.get('x'), config.get('y')] if config.get('x') and config.get('y') else [],
            'title': config.get('title', ''),
            'annot': True,
            'fmt': '.2f',
        }
    
    def _map_bubble(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Map bubble chart config."""
        return {
            'x_col': config.get('x'),
            'y_col': config.get('y'),
            'size_col': config.get('size') or config.get('y'),
            'color_col': config.get('color'),
            'title': config.get('title', ''),
            'size_max': 50,
        }
    
    def _map_treemap(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Map treemap config with categorical handling fix."""
        path = config.get('path')
        if not path:
            path = [config.get('x')] if config.get('x') else []
        
        agg_func = config.get('agg_func', 'sum')
        if agg_func == 'auto':
            agg_func = 'sum'
            
        return {
            'path': path,
            'values': config.get('y'),
            'color': config.get('color'),
            'agg_func': agg_func,
            'title': config.get('title', ''),
        }
    
    def _map_card(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Map card config."""
        agg_func = config.get('agg_func', 'sum')
        if agg_func == 'auto':
            agg_func = 'sum'
            
        return {
            'value_col': config.get('value_col') or config.get('y'),
            'agg_func': agg_func,
            'title': config.get('title', ''),
            'prefix': config.get('prefix', ''),
            'suffix': config.get('suffix', ''),
            'font_size': '2em',
        }
    
    def _map_kpi(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Map KPI config."""
        agg_func = config.get('agg_func', 'sum')
        if agg_func == 'auto':
            agg_func = 'sum'
            
        return {
            'value_col': config.get('value_col') or config.get('y'),
            'agg_func': agg_func,
            'title': config.get('title', ''),
            'prefix': config.get('prefix', ''),
            'suffix': config.get('suffix', ''),
            'target_value': config.get('target_value'),
            'target_col': config.get('target_col'),
            'polarity': config.get('polarity', 'higher'),
        }
    
    def _map_gauge(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Map gauge config."""
        agg_func = config.get('agg_func', 'sum')
        if agg_func == 'auto':
            agg_func = 'sum'
            
        return {
            'value_col': config.get('value_col') or config.get('y'),
            'agg_func': agg_func,
            'title': config.get('title', ''),
            'min_fixed': config.get('min_value'),
            'max_fixed': config.get('max_value'),
            'target_fixed': config.get('target_value'),
            'target_col': config.get('target_col'),
            'polarity': config.get('polarity', 'higher'),
        }
    
    def _map_bubble_map(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Map bubble map config."""
        return {
            'lat_col': config.get('lat_col') or config.get('x'),
            'lon_col': config.get('lon_col') or config.get('y'),
            'size_col': config.get('size'),
            'color_col': config.get('color'),
            'title': config.get('title', ''),
            'scope': 'world',
            'projection': 'natural earth',
        }
    
    def _map_correlation_matrix(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Map correlation matrix config."""
        columns = config.get('columns')
        if not columns:
            numeric_cols = [
                col for col in self.df.columns 
                if pd.api.types.is_numeric_dtype(self.df[col])
            ]
            columns = numeric_cols
        
        return {
            'columns': columns,
            'title': config.get('title', ''),
            'method': 'pearson',
            'annot': True,
        }
    
    def _call_production_function(self, chart_type: str, config: Dict[str, Any]) -> go.Figure:
        """Call production chart function with error handling."""
        chart_dispatcher = {
            'line': plot_plotly_line_chart,
            'bar': plot_plotly_bar_chart,
            'scatter': plot_plotly_scatter,
            'histogram': plot_plotly_histogram,
            'pie': plot_plotly_pie_chart,
            'box': plot_plotly_box_plot,
            'violin': plot_plotly_violin_plot,
            'heatmap': plot_plotly_heatmap,
            'bubble': plot_plotly_bubble_chart,
            'treemap': plot_plotly_treemap,
            'card': plot_card,
            'kpi': plot_kpi,
            'gauge': plot_gauge,
            'bubble_map': plot_plotly_bubble_map,
            'correlation_matrix': plot_plotly_correlation_matrix,
        }
        
        if chart_type not in chart_dispatcher:
            # Try to find similar chart type
            similar = self._find_similar_chart_type(chart_type)
            if similar:
                logger.warning(f"Chart type '{chart_type}' not found, using '{similar}' instead")
                return self._call_production_function(similar, config)
            else:
                raise ValueError(f"No production function for {chart_type}")
        
        try:
            return chart_dispatcher[chart_type](self.df, config)
        except Exception as e:
            logger.error(f"Chart function {chart_type} failed: {e}")
            # Try basic fallback
            return self._fallback_to_basic_plot(chart_type, config)
    
    def _find_similar_chart_type(self, chart_type: str) -> Optional[str]:
        """Find similar chart type for fallback."""
        similar_map = {
            'area': 'line',
            'donut': 'pie',
            'column': 'bar',
            'density': 'histogram',
            'radar': 'line',
            'waterfall': 'bar',
        }
        return similar_map.get(chart_type)
    
    def _fallback_to_basic_plot(self, chart_type: str, config: Dict[str, Any]) -> go.Figure:
        """Fallback to basic plotly express when specialized function fails."""
        try:
            x = config.get('x')
            y = config.get('y')
            
            if chart_type == 'histogram' and x:
                fig = px.histogram(self.df, x=x, color=config.get('color'))
            elif chart_type == 'scatter' and x and y:
                fig = px.scatter(self.df, x=x, y=y, color=config.get('color'))
            elif chart_type == 'line' and x and y:
                fig = px.line(self.df, x=x, y=y, color=config.get('color'))
            elif chart_type == 'bar' and x:
                fig = px.bar(self.df, x=x, y=y if y else None, color=config.get('color'))
            elif chart_type == 'box' and y:
                fig = px.box(self.df, y=y, x=x, color=config.get('color'))
            elif chart_type == 'pie' and x:
                fig = px.pie(self.df, names=x, values=y)
            elif chart_type == 'violin' and y:
                fig = px.violin(self.df, y=y, x=x, color=config.get('color'))
            elif chart_type == 'bubble' and x and y:
                fig = px.scatter(self.df, x=x, y=y, size=config.get('size'), color=config.get('color'))
            elif chart_type == 'heatmap' and x and y:
                fig = px.density_heatmap(self.df, x=x, y=y)
            elif chart_type == 'treemap' and x:
                # Basic treemap fallback
                fig = px.treemap(self.df, path=[x], values=y)
            else:
                raise ValueError(f"Cannot create fallback for {chart_type}")
            
            fig.update_layout(title=config.get('title', f'{chart_type.title()} Chart'))
            
            # Try to apply basic styling
            try:
                from core.charts.templates import apply_unified_styling
                fig = apply_unified_styling(fig, config, chart_type)
            except:
                pass
            
            return fig
        except Exception as e:
            logger.error(f"Fallback also failed: {e}")
            return self._create_error_figure(f"Chart creation failed: {str(e)[:100]}")
    
    def _create_validation_error_figure(self, validation: ChartValidationResult) -> go.Figure:
        """Create error visualization for validation failures."""
        error_text = f"<b>⚠️ Validation Error</b><br>{validation.message}"
        if validation.missing_fields:
            error_text += f"<br>Missing: {', '.join(validation.missing_fields)}"
        
        return self._create_error_figure(error_text)
    
    def _create_error_figure(self, error_text: str) -> go.Figure:
        """Create professional error visualization."""
        fig = go.Figure()
        
        fig.add_annotation(
            x=0.5,
            y=0.5,
            text=error_text,
            showarrow=False,
            font=dict(size=14, color="#e74c3c"),
            align="center",
            xref="paper",
            yref="paper",
            bordercolor="#e74c3c",
            borderwidth=2,
            borderpad=10,
            bgcolor="rgba(231, 76, 60, 0.1)",
        )
        
        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            height=300,
            margin=dict(l=20, r=20, t=20, b=20),
            plot_bgcolor="rgba(0,0,0,0)",
        )
        
        return fig

# ============================================================================
# DATA PROCESSOR (ENHANCED)
# ============================================================================

class ChartDataProcessor:
    """Intelligent data processing for chart creation."""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self._processed_cache = {}
    
    def prepare_for_chart(self, chart_config: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any], List[str]]:
        """Prepare data for chart with caching."""
        cache_key = self._create_cache_key(chart_config)
        if cache_key in self._processed_cache:
            return self._processed_cache[cache_key]
        
        chart_type = chart_config.get('chart_type', 'histogram')
        warnings = []
        
        processor_map = {
            'bar': self._prepare_bar,
            'line': self._prepare_line,
            'scatter': self._prepare_scatter,
            'histogram': self._prepare_histogram,
            'pie': self._prepare_pie,
            'box': self._prepare_box,
            'violin': self._prepare_violin,
            'heatmap': self._prepare_heatmap,
            'treemap': self._prepare_treemap,
            'bubble': self._prepare_bubble,
            'card': self._prepare_card,
            'kpi': self._prepare_kpi,
            'gauge': self._prepare_gauge,
            'bubble_map': self._prepare_bubble_map,
            'correlation_matrix': self._prepare_correlation_matrix,
        }
        
        if chart_type in processor_map:
            try:
                result = processor_map[chart_type](chart_config)
                self._processed_cache[cache_key] = result
                return result
            except Exception as e:
                logger.error(f"Data processing failed for {chart_type}: {e}")
                warnings.append(f"Data processing failed: {str(e)[:100]}")
                return self.df, chart_config, warnings
        
        warnings.append(f"Unsupported chart type: {chart_type}")
        return self.df, chart_config, warnings
    
    def _create_cache_key(self, config: Dict[str, Any]) -> str:
        """Create cache key from config."""
        parts = [
            config.get('chart_type', ''),
            config.get('x', ''),
            config.get('y', ''),
            config.get('value_col', ''),
            str(config.get('agg_func', '')),
        ]
        return hashlib.md5('_'.join(parts).encode()).hexdigest()[:16]
    
    def _prepare_bar(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced bar chart data preparation."""
        x = config.get('x')
        y = config.get('y')
        color = config.get('color')
        agg_func = config.get('aggregation', 'sum')
        warnings = []
        
        if not x:
            return {'data': self.df, 'config': config, 'warnings': ['Missing X column']}
        
        group_cols = [col for col in [x, color] if col and col in self.df.columns]
        
        if not group_cols:
            return {'data': self.df, 'config': config, 'warnings': ['No grouping columns']}
        
        # Check if aggregation is needed
        needs_agg = False
        if y and y in self.df.columns:
            # Check for duplicate x values
            if self.df[x].duplicated().any():
                needs_agg = True
            elif color and self.df.duplicated(subset=[x, color]).any():
                needs_agg = True
        
        if needs_agg:
            try:
                processed_df = self.df.groupby(group_cols, as_index=False)[y].agg(agg_func)
                warnings.append(f"Aggregated using {agg_func}")
                config['_processed'] = True
                config['_agg_func'] = agg_func
            except Exception as e:
                warnings.append(f"Aggregation failed: {str(e)[:50]}")
                processed_df = self.df
        else:
            processed_df = self.df
        
        return {'data': processed_df, 'config': config, 'warnings': warnings}
    
    def _prepare_line(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced line chart preparation."""
        x = config.get('x')
        y = config.get('y')
        warnings = []
        
        if not x or not y:
            return {'data': self.df, 'config': config, 'warnings': ['Line chart requires X and Y']}
        
        # Sort by x for line charts
        if x in self.df.columns:
            try:
                processed_df = self.df.sort_values(x).copy()
                config['_sorted'] = True
                
                # Check for datetime x-axis
                if pd.api.types.is_datetime64_any_dtype(processed_df[x]):
                    config['_is_timeseries'] = True
                    warnings.append("Timeseries detected - consider resampling for large datasets")
            except Exception as e:
                warnings.append(f"Sorting failed: {str(e)[:50]}")
                processed_df = self.df
        else:
            processed_df = self.df
        
        # Handle missing values for line charts
        if processed_df[y].isnull().any():
            missing_count = processed_df[y].isnull().sum()
            processed_df = processed_df.dropna(subset=[x, y])
            warnings.append(f"Removed {missing_count} missing values for clean line")
        
        return {'data': processed_df, 'config': config, 'warnings': warnings}
    
    def _prepare_scatter(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced scatter plot preparation."""
        return self._prepare_line(config)  # Similar preparation
    
    def _prepare_pie(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced pie chart preparation."""
        x = config.get('x')
        y = config.get('y')
        warnings = []
        
        if not x:
            return {'data': self.df, 'config': config, 'warnings': ['Missing X column']}
        
        # Handle categorical columns
        if pd.api.types.is_categorical_dtype(self.df[x]):
            self.df[x] = self.df[x].astype(str)
        
        # Limit categories
        unique_count = self.df[x].nunique()
        if unique_count > 20:
            warnings.append(f"Pie chart has {unique_count} categories - consider bar chart")
            # Group small categories
            value_counts = self.df[x].value_counts()
            top_categories = value_counts.nlargest(10).index
            self.df[x] = self.df[x].apply(lambda val: val if val in top_categories else 'Other')
        
        if y and y in self.df.columns:
            agg_func = config.get('aggregation', 'sum')
            try:
                processed_df = self.df.groupby(x, as_index=False)[y].agg(agg_func)
                warnings.append(f"Aggregated using {agg_func}")
                config['_processed'] = True
            except Exception as e:
                warnings.append(f"Aggregation failed: {str(e)[:50]}")
                processed_df = self.df
        else:
            processed_df = self.df[x].value_counts().reset_index()
            processed_df.columns = [x, '_count']
            config['_y_actual'] = '_count'
            warnings.append("Using category counts")
        
        return {'data': processed_df, 'config': config, 'warnings': warnings}
    
    def _prepare_heatmap(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced heatmap preparation."""
        x = config.get('x')
        y = config.get('y')
        warnings = []
        
        if not x or not y:
            return {'data': self.df, 'config': config, 'warnings': ['Heatmap requires X and Y']}
        
        try:
            # Pivot for heatmap
            pivot_df = self.df.groupby([x, y]).size().reset_index(name='_count')
            
            # Fill missing combinations
            x_categories = self.df[x].unique()
            y_categories = self.df[y].unique()
            
            config['_z_actual'] = '_count'
            config['_processed'] = True
            warnings.append(f"Heatmap: {len(x_categories)}×{len(y_categories)} matrix")
            
            return {'data': pivot_df, 'config': config, 'warnings': warnings}
        except Exception as e:
            warnings.append(f"Heatmap failed: {str(e)[:50]}")
            return {'data': self.df, 'config': config, 'warnings': warnings}
    
    def _prepare_treemap(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced treemap preparation with proper categorical handling."""
        warnings = []
        
        # Find categorical columns for hierarchy
        categorical_cols = []
        for col in self.df.columns:
            if pd.api.types.is_categorical_dtype(self.df[col]):
                # Handle categorical dtype - convert to string
                self.df[col] = self.df[col].astype(str)
                categorical_cols.append(col)
            elif self.df[col].dtype == "object":
                categorical_cols.append(col)
        
        if not categorical_cols:
            return {'data': self.df, 'config': config, 'warnings': ['No categorical columns for treemap hierarchy']}
        
        # Use x as first level if specified, else use first categorical
        x = config.get('x')
        if x and x in categorical_cols:
            first_level = x
        else:
            first_level = categorical_cols[0]
        
        # Build hierarchy: up to 4 levels
        hierarchy = [first_level]
        remaining = [c for c in categorical_cols if c != first_level]
        hierarchy.extend(remaining[:3])  # Add up to 3 more levels
        
        # Handle NaN values in hierarchy columns
        for col in hierarchy:
            if col in self.df.columns:
                # Replace NaN with 'Unknown' - safe now that we've converted categoricals
                self.df[col] = self.df[col].fillna('Unknown')
        
        # Find value column
        y = config.get('y')
        if y and y in self.df.columns and pd.api.types.is_numeric_dtype(self.df[y]):
            value_col = y
        else:
            numeric_cols = [
                col for col in self.df.columns 
                if pd.api.types.is_numeric_dtype(self.df[col])
            ]
            if numeric_cols:
                value_col = numeric_cols[0]
            else:
                value_col = None
                warnings.append("No numeric column found for treemap values, using counts")
        
        # Update config with hierarchy
        config['path'] = hierarchy
        if value_col:
            config['values'] = value_col
        
        warnings.append(f"Treemap hierarchy: {' → '.join(hierarchy)}")
        
        return {'data': self.df, 'config': config, 'warnings': warnings}
    
    def _prepare_card(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced card preparation."""
        value_col = config.get('value_col') or config.get('y')
        warnings = []
        
        if not value_col:
            return {'data': self.df, 'config': config, 'warnings': ['Card requires value column']}
        
        if value_col not in self.df.columns:
            warnings.append(f"Column '{value_col}' not found")
        
        # Calculate basic stats for context
        if value_col in self.df.columns:
            series = self.df[value_col].dropna()
            if not series.empty:
                config['_stats'] = {
                    'count': len(series),
                    'mean': series.mean(),
                    'min': series.min(),
                    'max': series.max(),
                }
        
        return {'data': self.df, 'config': config, 'warnings': warnings}
    
    def _prepare_kpi(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced KPI preparation."""
        result = self._prepare_card(config)
        
        # Add target validation
        target_col = config.get('target_col')
        if target_col and target_col not in self.df.columns:
            result['warnings'].append(f"Target column '{target_col}' not found")
        
        return result
    
    def _prepare_gauge(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced gauge preparation."""
        return self._prepare_kpi(config)
    
    def _prepare_bubble_map(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced bubble map preparation."""
        lat_col = config.get('lat_col')
        lon_col = config.get('lon_col')
        warnings = []
        
        # Try to auto-detect lat/lon if not provided
        if not lat_col or not lon_col:
            lat_candidates = [col for col in self.df.columns if any(geo in col.lower() for geo in ['lat', 'latitude'])]
            lon_candidates = [col for col in self.df.columns if any(geo in col.lower() for geo in ['lon', 'long', 'longitude'])]
            
            if lat_candidates and lon_candidates:
                lat_col = lat_candidates[0]
                lon_col = lon_candidates[0]
                config['lat_col'] = lat_col
                config['lon_col'] = lon_col
                warnings.append(f"Auto-detected: lat={lat_col}, lon={lon_col}")
            else:
                warnings.append("Bubble map requires lat/lon columns")
        
        if lat_col and lat_col not in self.df.columns:
            warnings.append(f"Latitude column '{lat_col}' not found")
        
        if lon_col and lon_col not in self.df.columns:
            warnings.append(f"Longitude column '{lon_col}' not found")
        
        # Validate coordinate ranges
        if lat_col in self.df.columns and lon_col in self.df.columns:
            lat_series = self.df[lat_col].dropna()
            lon_series = self.df[lon_col].dropna()
            
            if not lat_series.empty and not lon_series.empty:
                lat_min, lat_max = lat_series.min(), lat_series.max()
                lon_min, lon_max = lon_series.min(), lon_series.max()
                
                if not (-90 <= lat_min <= 90 and -90 <= lat_max <= 90):
                    warnings.append(f"Latitude range ({lat_min:.2f} to {lat_max:.2f}) may be invalid")
                if not (-180 <= lon_min <= 180 and -180 <= lon_max <= 180):
                    warnings.append(f"Longitude range ({lon_min:.2f} to {lon_max:.2f}) may be invalid")
        
        return {'data': self.df, 'config': config, 'warnings': warnings}
    
    def _prepare_correlation_matrix(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced correlation matrix preparation."""
        warnings = []
        
        # Find numeric columns if not specified
        if not config.get('columns'):
            numeric_cols = [
                col for col in self.df.columns 
                if pd.api.types.is_numeric_dtype(self.df[col])
            ]
            if numeric_cols:
                config['columns'] = numeric_cols
                warnings.append(f"Using {len(numeric_cols)} numeric columns")
            else:
                warnings.append("No numeric columns found for correlation matrix")
        
        return {'data': self.df, 'config': config, 'warnings': warnings}

# ============================================================================
# CHART CREATION FUNCTIONS
# ============================================================================

def create_ai_plot_from_suggestion(df: pd.DataFrame, suggestion: Dict[str, Any]) -> go.Figure:
    """
    Create plot from AI suggestion with enhanced error handling.
    
    Args:
        df: Dataframe to plot
        suggestion: AI-generated chart suggestion
        
    Returns:
        Plotly Figure or error visualization
    """
    try:
        # Normalize with family awareness
        canonical = normalize_ai_response(suggestion)
        
        # Validate
        validation = validate_chart_possibility(canonical, df)
        if not validation.is_valid:
            logger.warning(f"Validation failed: {validation.message}")
            adapter = ProductionChartAdapter(df)
            return adapter._create_validation_error_figure(validation)
        
        # Create chart
        adapter = ProductionChartAdapter(df)
        fig = adapter.create_chart(canonical)
        
        if not fig:
            return _create_error_visualization("Failed to create chart")
        
        return fig
        
    except Exception as e:
        logger.error(f"Chart creation failed: {e}")
        return _create_error_visualization(f"Chart creation error: {str(e)[:100]}")

# ============================================================================
# LEGACY SUPPORT & FALLBACK
# ============================================================================

def _create_chart_with_processed_data_legacy(df: pd.DataFrame, config: Dict[str, Any], warnings: List[str]) -> go.Figure:
    """Legacy chart creation for fallback."""
    chart_type = config.get('chart_type', 'histogram')
    x = config.get('x')
    y = config.get('y')
    
    try:
        if chart_type == 'line' and x and y:
            fig = px.line(df, x=x, y=y, color=config.get('color'))
        elif chart_type == 'scatter' and x and y:
            fig = px.scatter(df, x=x, y=y, color=config.get('color'), size=config.get('size'))
        elif chart_type == 'histogram' and x:
            fig = px.histogram(df, x=x, color=config.get('color'))
        elif chart_type == 'bar' and x:
            y_actual = config.get('_y_actual') or y
            if y_actual:
                fig = px.bar(df, x=x, y=y_actual, color=config.get('color'))
            else:
                fig = px.bar(df, x=x, color=config.get('color'))
        elif chart_type == 'pie' and x:
            y_actual = config.get('_y_actual') or y
            if y_actual in df.columns:
                fig = px.pie(df, names=x, values=y_actual)
            else:
                fig = px.pie(df, names=x)
        elif chart_type == 'box' and y:
            fig = px.box(df, y=y, x=config.get('x'), color=config.get('color'))
        elif chart_type == 'violin' and y:
            fig = px.violin(df, y=y, x=config.get('x'), color=config.get('color'))
        elif chart_type == 'treemap' and x:
            # Handle categorical columns in fallback
            if pd.api.types.is_categorical_dtype(df[x]):
                df[x] = df[x].astype(str)
            fig = px.treemap(df, path=[x], values=y)
        elif x and y:
            fig = px.scatter(df, x=x, y=y)
        elif x:
            fig = px.histogram(df, x=x)
        else:
            raise ValueError("No valid configuration")
        
        # Apply basic styling
        fig.update_layout(
            font=dict(family="Arial", size=12),
            plot_bgcolor='white'
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Legacy chart failed: {e}")
        return _create_error_visualization(f"Legacy chart failed: {str(e)[:100]}")

def _create_error_visualization(error_text: str) -> go.Figure:
    """Create professional error visualization."""
    fig = go.Figure()
    
    fig.add_annotation(
        x=0.5,
        y=0.5,
        text=f"<b>⚠️ Chart Error</b><br>{error_text}",
        showarrow=False,
        font=dict(size=14, color="#e74c3c"),
        align="center",
        xref="paper",
        yref="paper",
        bordercolor="#e74c3c",
        borderwidth=2,
        borderpad=10,
        bgcolor="rgba(231, 76, 60, 0.1)",
    )
    
    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        height=300,
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor="rgba(0,0,0,0)",
    )
    
    return fig

# ============================================================================
# CHART TYPE DETECTION & RECOMMENDATION
# ============================================================================

def detect_suitable_chart_types(df: pd.DataFrame, user_prompt: str = "") -> Dict[str, Dict[str, Any]]:
    """
    Detect which chart types make sense for this data with confidence scoring.
    
    Returns:
        Dict mapping chart type to recommendation details
    """
    recommendations = {}
    
    # Get column types
    numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
    categorical_cols = [
        col for col in df.columns 
        if df[col].dtype == "object" or pd.api.types.is_categorical_dtype(df[col])
    ]
    
    # Analyze user prompt for intent
    prompt_lower = user_prompt.lower() if user_prompt else ""
    
    # Single metric recommendations
    if len(numeric_cols) == 1 and not any(word in prompt_lower for word in ['compare', 'trend', 'distribution']):
        metric_col = numeric_cols[0]
        recommendations['card'] = {
            'confidence': 0.9,
            'reason': f"Single numeric column '{metric_col}' perfect for metric display",
            'columns': [metric_col],
            'sample_config': {'chart_type': 'card', 'value_col': metric_col}
        }
        recommendations['kpi'] = {
            'confidence': 0.8,
            'reason': f"Single metric '{metric_col}' suitable for KPI",
            'columns': [metric_col],
            'sample_config': {'chart_type': 'kpi', 'value_col': metric_col}
        }
    
    # Geographic data detection
    lat_patterns = ['lat', 'latitude', 'y_coord']
    lon_patterns = ['lon', 'long', 'longitude', 'x_coord']
    lat_cols = [col for col in df.columns if any(pattern in col.lower() for pattern in lat_patterns)]
    lon_cols = [col for col in df.columns if any(pattern in col.lower() for pattern in lon_patterns)]
    if lat_cols and lon_cols:
        recommendations['bubble_map'] = {
            'confidence': 0.95,
            'reason': f"Geographic columns detected: {lat_cols[0]}, {lon_cols[0]}",
            'columns': [lat_cols[0], lon_cols[0]],
            'sample_config': {'chart_type': 'bubble_map', 'lat_col': lat_cols[0], 'lon_col': lon_cols[0]}
        }
    
    # Hierarchy detection for treemap
    if len(categorical_cols) >= 2:
        recommendations['treemap'] = {
            'confidence': 0.8,
            'reason': f"{len(categorical_cols)} categorical columns available for hierarchy",
            'columns': categorical_cols[:4],
            'sample_config': {'chart_type': 'treemap', 'path': categorical_cols[:3]}
        }
    
    # Correlation analysis
    if len(numeric_cols) >= 3:
        recommendations['correlation_matrix'] = {
            'confidence': 0.85,
            'reason': f"{len(numeric_cols)} numeric columns for correlation analysis",
            'columns': numeric_cols,
            'sample_config': {'chart_type': 'correlation_matrix', 'columns': numeric_cols[:5]}
        }
    
    # Time series detection
    date_patterns = ['date', 'time', 'year', 'month', 'day', 'timestamp', 'datetime']
    date_cols = [col for col in df.columns if any(pattern in col.lower() for pattern in date_patterns)]
    if date_cols and numeric_cols:
        recommendations['line'] = {
            'confidence': 0.9,
            'reason': f"Date column '{date_cols[0]}' with numeric data for time series",
            'columns': [date_cols[0], numeric_cols[0]],
            'sample_config': {'chart_type': 'line', 'x': date_cols[0], 'y': numeric_cols[0]}
        }
    
    # Comparison charts
    if categorical_cols and numeric_cols:
        recommendations['bar'] = {
            'confidence': 0.85,
            'reason': f"Categorical '{categorical_cols[0]}' and numeric '{numeric_cols[0]}' for comparison",
            'columns': [categorical_cols[0], numeric_cols[0]],
            'sample_config': {'chart_type': 'bar', 'x': categorical_cols[0], 'y': numeric_cols[0]}
        }
        recommendations['box'] = {
            'confidence': 0.75,
            'reason': f"Distribution comparison for '{numeric_cols[0]}' by '{categorical_cols[0]}'",
            'columns': [categorical_cols[0], numeric_cols[0]],
            'sample_config': {'chart_type': 'box', 'x': categorical_cols[0], 'y': numeric_cols[0]}
        }
    
    # Distribution charts
    if numeric_cols:
        recommendations['histogram'] = {
            'confidence': 0.8,
            'reason': f"Numeric column '{numeric_cols[0]}' for distribution analysis",
            'columns': [numeric_cols[0]],
            'sample_config': {'chart_type': 'histogram', 'x': numeric_cols[0]}
        }
    
    # Relationship charts
    if len(numeric_cols) >= 2:
        recommendations['scatter'] = {
            'confidence': 0.9,
            'reason': f"Two numeric columns '{numeric_cols[0]}' and '{numeric_cols[1]}' for relationship",
            'columns': numeric_cols[:2],
            'sample_config': {'chart_type': 'scatter', 'x': numeric_cols[0], 'y': numeric_cols[1]}
        }
        recommendations['heatmap'] = {
            'confidence': 0.7,
            'reason': f"Multiple numeric columns for matrix visualization",
            'columns': numeric_cols[:4],
            'sample_config': {'chart_type': 'heatmap', 'x': numeric_cols[0], 'y': numeric_cols[1]}
        }
    
    # Sort by confidence
    sorted_recs = dict(sorted(recommendations.items(), key=lambda x: x[1]['confidence'], reverse=True))
    
    return sorted_recs

def get_chart_recommendation_for_data(df: pd.DataFrame, focus_column: str = None) -> List[Dict[str, Any]]:
    """
    Get chart recommendations for specific data characteristics.
    
    Args:
        df: DataFrame to analyze
        focus_column: Optional specific column to focus on
        
    Returns:
        List of recommended chart configurations
    """
    recommendations = []
    
    if focus_column and focus_column in df.columns:
        col_series = df[focus_column]
        
        # Numeric column recommendations
        if pd.api.types.is_numeric_dtype(col_series):
            recommendations.append({
                'chart_type': 'histogram',
                'x': focus_column,
                'title': f'Distribution of {focus_column}',
                'description': f'Histogram showing distribution of {focus_column}',
                'confidence': 0.9
            })
            
            # Check for time companion
            date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
            if date_cols:
                recommendations.append({
                    'chart_type': 'line',
                    'x': date_cols[0],
                    'y': focus_column,
                    'title': f'{focus_column} over time',
                    'description': f'Time series of {focus_column}',
                    'confidence': 0.85
                })
        
        # Categorical column recommendations
        elif col_series.dtype == 'object' or pd.api.types.is_categorical_dtype(col_series):
            recommendations.append({
                'chart_type': 'bar',
                'x': focus_column,
                'title': f'Counts by {focus_column}',
                'description': f'Bar chart showing frequency of {focus_column}',
                'confidence': 0.8
            })
            
            # Find numeric companion
            numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
            if numeric_cols:
                recommendations.append({
                    'chart_type': 'box',
                    'x': focus_column,
                    'y': numeric_cols[0],
                    'title': f'{numeric_cols[0]} by {focus_column}',
                    'description': f'Box plot comparing {numeric_cols[0]} across {focus_column}',
                    'confidence': 0.75
                })
    
    return recommendations[:5]  # Return top 5

# ============================================================================
# COMPATIBILITY FUNCTIONS
# ============================================================================

def normalize_suggestion_fields(sugg: Dict, df: pd.DataFrame = None) -> Dict:
    """Compatibility function - normalize suggestion fields."""
    return normalize_ai_response(sugg)

def normalize_chart_type(t: Optional[str]) -> str:
    """Normalize chart type string."""
    if not t:
        return "histogram"
    t = t.strip().lower()
    return CHART_TYPE_ALIASES.get(t, t)

def ensure_suggestion_id(sugg: dict, index: int, prefix: str = "chart") -> str:
    """Ensure suggestion has unique ID."""
    if 'id' in sugg and sugg['id']:
        return sugg['id']
    
    canonical = normalize_ai_response(sugg)
    return canonical['id']

def get_chart_family_info(chart_type: str) -> Dict[str, Any]:
    """Get detailed information about a chart's family."""
    family = _get_chart_family(chart_type)
    return {
        'family': family,
        'family_name': CHART_FAMILIES.get(family, {}).get('name', 'Unknown'),
        'icon': CHART_FAMILIES.get(family, {}).get('icon', '📊'),
        'description': CHART_FAMILIES.get(family, {}).get('description', ''),
        'charts_in_family': CHART_FAMILIES.get(family, {}).get('charts', []),
    }

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Schema constants
    "SUPPORTED_CHART_TYPES",
    "CHART_TYPE_ALIASES",
    "CHART_FAMILIES",
    "CHART_REQUIREMENTS",
    "CANONICAL_DEFAULTS",
    
    # Core functions
    "normalize_ai_response",
    "validate_canonical_chart",
    "validate_chart_possibility",
    "validate_and_explain_chart",
    "ChartValidationResult",
    
    # Chart creation
    "create_ai_plot_from_suggestion",
    "ProductionChartAdapter",
    "ChartDataProcessor",
    
    # Detection & recommendation
    "detect_suitable_chart_types",
    "get_chart_recommendation_for_data",
    "get_chart_family_info",
    
    # Compatibility
    "normalize_suggestion_fields",
    "normalize_chart_type",
    "ensure_suggestion_id",
    
    # ChartFamily enum
    "ChartFamily",
    
    # Error handling
    "_create_error_visualization",
]