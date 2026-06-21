"""
Plotly visualization functions - Production version
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import logging
from typing import Optional, List, Tuple, Any, Dict, Literal, Union
import warnings
import streamlit as st

logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')

# ============================================================================
# COLOR PALETTE DEFINITIONS (MOVED TO TOP FOR ACCESSIBILITY)
# ============================================================================

COLOR_PALETTES = {
    'Plotly': px.colors.qualitative.Plotly,
    'Viridis': px.colors.sequential.Viridis,
    'Plasma': px.colors.sequential.Plasma,
    'Inferno': px.colors.sequential.Inferno,
    'Magma': px.colors.sequential.Magma,
    'Cividis': px.colors.sequential.Cividis,
    'Rainbow': px.colors.sequential.Rainbow,
    'Turbo': px.colors.sequential.Turbo,
    'Blues': px.colors.sequential.Blues,
    'Reds': px.colors.sequential.Reds,
    'Greens': px.colors.sequential.Greens,
    'Greys': px.colors.sequential.Greys,
    'Oranges': px.colors.sequential.Oranges,
    'Purples': px.colors.sequential.Purples,
    'Custom 1': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'],
    'Custom 2': ['#3366CC', '#DC3912', '#FF9900', '#109618', '#990099']
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_plotly_error_visualization(message: str) -> go.Figure:
    """Creates a Plotly figure displaying an error message."""
    fig = go.Figure()
    fig.add_annotation(
        x=0.5, y=0.5,
        text=f"<b>VISUALIZATION ERROR</b><br>{message}<br><i>Check data types and column names</i>",
        showarrow=False,
        font=dict(size=14, color="red"),
        align="center",
        xref="paper", yref="paper"
    )
    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    return fig


def validate_columns(df: pd.DataFrame, columns: List[str]) -> Tuple[bool, str]:
    """Validates that all specified columns exist in the DataFrame."""
    missing_cols = [col for col in columns if col is not None and col not in df.columns]
    if missing_cols:
        return False, f"Missing columns: {', '.join(missing_cols)}"
    return True, ""


def safe_numeric_conversion(series: pd.Series) -> Tuple[pd.Series, bool]:
    """Safely converts a series to numeric, returns series and success flag."""
    try:
        if pd.api.types.is_numeric_dtype(series):
            return series, True
        
        if pd.api.types.is_datetime64_any_dtype(series):
            return series, True

        numeric_series = pd.to_numeric(series, errors='coerce')
        if numeric_series.isnull().all() and not series.isnull().all():
            return pd.Series(dtype=float), False

        return numeric_series, True
    except Exception:
        return pd.Series(dtype=float), False


def _aggregate_series(series: pd.Series, func: str) -> float:
    """Unified aggregation logic for series with proper NaN handling"""
    if func == "count":
        return series.count()
    elif func == "sum":
        return series.sum()
    elif func == "mean":
        return series.mean()
    elif func == "median":
        return series.median()
    elif func == "min":
        return series.min()
    elif func == "max":
        return series.max()
    else:
        raise ValueError(f"Unknown aggregation function: {func}")


def _human_format(number: float, precision: int = 1) -> str:
    """Enhanced number formatting with configurable precision and NaN handling"""
    if pd.isna(number) or number is None:
        return "N/A"
    
    if abs(number) < 0.01 and number != 0:
        return f"{number:.2e}"
    
    is_negative = number < 0
    abs_number = abs(number)
    
    units = ['', 'K', 'M', 'B', 'T']
    unit_index = 0
    
    while abs_number >= 1000.0 and unit_index < len(units) - 1:
        unit_index += 1
        abs_number /= 1000.0
    
    if abs_number == int(abs_number):
        result = f"{int(abs_number):,}{units[unit_index]}"
    else:
        result = f"{abs_number:,.{precision}f}{units[unit_index]}"
    
    return f"-{result}" if is_negative else result


def _format_number_locale_safe(num: float, decimals: int) -> str:
    """Format number with thousands separator, locale-independent."""
    if num is None:
        return "N/A"
    
    return f"{num:,.{decimals}f}"


# ============================================================================
# UNIFIED STYLING FUNCTIONS
# ============================================================================

def _ensure_styling_defaults(config: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure config has all required styling keys with sensible defaults"""
    defaults = {
        'grid_mode': 'plotly_normal',
        'show_legend': True,
        'legend_position': 'top',
        'color_palette': 'Plotly',
        'template': 'plotly_white',
        'grid_width': 1.0,
        'grid_color': 'lightgray',
        'grid_style': 'solid',
        'font_family': 'Arial',
        'font_size': 12,
        'font_color': '#333333',
        'title_font_size': 16,
        'dark_mode': False
    }
    
    for key, default_value in defaults.items():
        if key not in config:
            config[key] = default_value
    
    return config


def _get_chart_specific_styling(chart_type: str) -> Dict[str, Any]:
    """Get chart-specific styling overrides"""
    styling = {
        'default': {
            'margin': dict(t=60, b=60, l=80, r=80),
            'font_family': 'Arial',
            'title_font_size': 16,
            'hovermode': 'closest'
        },
        'line': {
            'margin': dict(t=80, b=60, l=80, r=80),
            'hovermode': 'x unified'
        },
        'histogram': {
            'margin': dict(t=60, b=60, l=80, r=80),
            'bargap': 0.1
        },
        'pie': {
            'margin': dict(t=50, b=50, l=50, r=50),
            'hovermode': 'closest'
        },
        'scatter': {
            'margin': dict(t=60, b=60, l=80, r=80),
            'hovermode': 'closest'
        },
        'bar': {
            'margin': dict(t=60, b=60, l=80, r=80),
            'bargap': 0.1
        },
        'box': {
            'margin': dict(t=60, b=60, l=80, r=80)
        },
        'violin': {
            'margin': dict(t=60, b=60, l=80, r=80)
        },
        'heatmap': {
            'margin': dict(t=60, b=60, l=80, r=80)
        },
        'bubble': {
            'margin': dict(t=60, b=60, l=80, r=80),
            'hovermode': 'closest'
        },
        'treemap': {
            'margin': dict(t=50, b=50, l=25, r=25),
            'hovermode': 'closest'
        },
        'bubble_map': {
            'margin': dict(t=60, b=20, l=20, r=20),
            'hovermode': 'closest'
        },
        'kpi': {
            'margin': dict(t=40, b=40, l=40, r=40),
            'hovermode': False
        },
        'card': {
            'margin': dict(t=40, b=20, l=20, r=20),
            'hovermode': False
        },
        'gauge': {
            'margin': dict(t=50, b=20, l=20, r=20),
            'hovermode': False
        }
    }
    
    # Handle unknown chart types gracefully
    if chart_type not in styling:
        logger.debug(f"Unknown chart type '{chart_type}', using default styling")
        return styling['default']
    
    return styling.get(chart_type, styling['default'])


def _get_color_sequence(config: Dict[str, Any]) -> List[str]:
    """Get color sequence from config with fallback to Plotly default"""
    palette_name = config.get('color_palette', 'Plotly')
    color_sequence = COLOR_PALETTES.get(
        palette_name,
        COLOR_PALETTES['Plotly']  # Default fallback
    )
    return color_sequence

def _apply_template(fig: go.Figure, config: Dict[str, Any], chart_styling: Dict[str, Any]) -> go.Figure:
    """Apply final template and styling with proper precedence"""
    template = config.get('template', 'plotly_white')
    valid_templates = ['plotly', 'plotly_white', 'plotly_dark',
                      'ggplot2', 'seaborn', 'simple_white', 'none']
    
    if template != 'none' and template in valid_templates:
        fig.update_layout(template=template)
    elif template not in valid_templates and template != 'none':
        logger.warning(f"Invalid template '{template}', using 'plotly_white'")
        fig.update_layout(template='plotly_white')
    
    fig.update_layout(**chart_styling)
    
    return fig


def apply_unified_styling(fig: go.Figure, config: Dict[str, Any], chart_type: str) -> go.Figure:
    """
    Apply consistent styling across all chart types using unified configuration
    
    Args:
        fig: Plotly figure to style
        config: Styling configuration dictionary
        chart_type: Type of chart ('bar', 'line', 'scatter', etc.)
    
    Returns:
        Styled Plotly figure
    """
    # Handle unknown chart types gracefully
    supported_chart_types = [
        'bar', 'line', 'histogram', 'scatter', 'pie', 'box', 'violin',
        'heatmap', 'bubble', 'treemap', 'bubble_map', 'kpi', 'card', 'gauge'
    ]
    
    if chart_type not in supported_chart_types:
        logger.debug(f"Unsupported chart type '{chart_type}', defaulting to 'bar' styling")
        chart_type = 'default'
    
    config = _ensure_styling_defaults(config)
    chart_styling = _get_chart_specific_styling(chart_type)
    
    # fig = _apply_grid_styling(fig, config)
    # fig = _apply_legend_styling(fig, config, chart_type)
    # fig = _apply_font_styling(fig, config)
    # fig = _apply_color_palette(fig, config, chart_type)
    # fig = _apply_dark_mode(fig, config)
    fig = _apply_template(fig, config, chart_styling)
    
    return fig


# ============================================================================
# CHART FUNCTIONS
# ============================================================================

def plot_plotly_histogram(df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
    """Plot histogram that intelligently handles numeric, categorical, and datetime data."""
    x_col = config.get('x_col')
    color_col = config.get('color_col')
    
    valid, error_msg = validate_columns(df, [x_col])
    if not valid:
        return create_plotly_error_visualization(error_msg)
    
    if color_col:
        valid, error_msg = validate_columns(df, [color_col])
        if not valid:
            return create_plotly_error_visualization(error_msg)

    try:
        plot_df = df.copy()
        original_size = len(plot_df)
        x_series = plot_df[x_col]
        x_dtype = x_series.dtype
        
        is_numeric = pd.api.types.is_numeric_dtype(x_dtype)
        is_datetime = pd.api.types.is_datetime64_any_dtype(x_dtype)
        is_boolean = pd.api.types.is_bool_dtype(x_dtype)
        is_timedelta = pd.api.types.is_timedelta64_dtype(x_dtype)
        
        if not (is_numeric or is_datetime):
            numeric_series = pd.to_numeric(x_series, errors='coerce')
            numeric_non_null = numeric_series.notna().sum()
            
            if numeric_non_null > 0:
                if numeric_non_null == len(x_series):
                    plot_df[x_col] = numeric_series
                    is_numeric = True
                else:
                    numeric_ratio = numeric_non_null / len(x_series)
                    if numeric_ratio >= 0.8:
                        plot_df[x_col] = numeric_series
                        is_numeric = True
        
        if is_timedelta:
            plot_df[x_col] = plot_df[x_col].dt.total_seconds()
            is_numeric = True
        
        if is_boolean:
            plot_df[x_col] = plot_df[x_col].astype(str)
        
        is_discrete = not (is_numeric or is_datetime)
        
        plot_df = plot_df.dropna(subset=[x_col])
        
        if plot_df.empty:
            return create_plotly_error_visualization(f"No valid data in column '{x_col}' after conversion.")
        
        final_size = len(plot_df)
        if final_size < original_size:
            loss_pct = ((original_size - final_size) / original_size) * 100
            logger.info(f"Histogram: Dropped {original_size - final_size} rows ({loss_pct:.1f}%) from '{x_col}'")
        
        if is_datetime:
            default_title = f"Time Distribution of {x_col}"
        elif is_discrete:
            default_title = f"Count of {x_col} by Category"
        else:
            default_title = f"Distribution of {x_col}"
        
        color_sequence = _get_color_sequence(config)
        
        fig_kwargs = {
            'data_frame': plot_df,
            'x': x_col,
            'title': config.get('title', default_title)
        }
        
        bins = config.get('bins')
        if bins is not None:
            try:
                fig_kwargs['nbins'] = int(bins)
            except (ValueError, TypeError):
                logger.warning(f"Invalid bins value '{bins}', using Plotly default")
        elif is_datetime and 'nbins' not in fig_kwargs:
            date_range = plot_df[x_col].max() - plot_df[x_col].min()
            days_range = date_range.days
            
            if days_range > 365 * 5:
                fig_kwargs['nbins'] = 60
            elif days_range > 365:
                fig_kwargs['nbins'] = 52
            elif days_range > 30:
                fig_kwargs['nbins'] = 30
            elif days_range > 1:
                fig_kwargs['nbins'] = 24
            else:
                fig_kwargs['nbins'] = 24
        
        optional_params = ['histnorm', 'marginal', 'range_x']
        for param in optional_params:
            if config.get(param) is not None:
                fig_kwargs[param] = config[param]
        
        if color_col:
            fig_kwargs['color'] = color_col
            color_is_numeric = pd.api.types.is_numeric_dtype(plot_df[color_col])
            color_as_discrete = config.get('color_as_discrete', not color_is_numeric)
            
            if color_is_numeric:
                if color_as_discrete:
                    fig_kwargs['color_discrete_sequence'] = color_sequence
                else:
                    fig_kwargs['color_continuous_scale'] = px.colors.sequential.Viridis
            else:
                fig_kwargs['color_discrete_sequence'] = color_sequence
        else:
            fig_kwargs['color_discrete_sequence'] = [color_sequence[0]]
        
        if is_datetime:
            fig_kwargs.update({
                'labels': {x_col: 'Date/Time'}
            })
        
        fig = px.histogram(**fig_kwargs)
        
        if not color_col:
            fig.update_traces(marker_color=color_sequence[0])
        
        if is_datetime:
            fig.update_xaxes(title_text='Date/Time')
        elif is_discrete:
            fig.update_xaxes(title_text='Categories')
        else:
            fig.update_xaxes(title_text=x_col)
        
        if fig_kwargs.get('histnorm') in ['percent', 'probability']:
            fig.update_yaxes(title_text='Percentage')
        elif is_discrete:
            fig.update_yaxes(title_text='Count')
        else:
            fig.update_yaxes(title_text='Frequency')
        
        fig = apply_unified_styling(fig, config, 'histogram')
        
        for trace in fig.data:
            if hasattr(trace, 'marker') and trace.marker:
                if hasattr(trace.marker, 'color') and trace.marker.color is None:
                    trace.marker.color = color_sequence[0]
        
        return fig

    except Exception as e:
        logger.error(f"Error plotting histogram: {e}")
        return create_plotly_error_visualization(f"Unable to create histogram: {str(e)}")


def plot_plotly_scatter(df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
    """Plot scatter plot with enhanced color palette support"""
    x_col = config.get('x_col')
    y_col = config.get('y_col')
    color_col = config.get('color_col')
    size_col = config.get('size_col')
    
    cols_to_validate = [x_col, y_col]
    optional_cols = [color_col, size_col]
    cols_to_validate.extend([col for col in optional_cols if col is not None])
    
    valid, error_msg = validate_columns(df, cols_to_validate)
    if not valid:
        return create_plotly_error_visualization(error_msg)

    try:
        plot_df = df.copy()
        numeric_cols = []
        if size_col:
            numeric_cols.append(size_col)
        
        for col in set([x_col, y_col] + numeric_cols):
            numeric_data, success = safe_numeric_conversion(plot_df[col])
            if not success:
                return create_plotly_error_visualization(f"Column '{col}' must be numeric.")
            plot_df[col] = numeric_data

        plot_df = plot_df.dropna(subset=[x_col, y_col])
        if plot_df.empty:
            return create_plotly_error_visualization("No valid data remains after filtering.")

        color_sequence = _get_color_sequence(config)
        
        fig_kwargs = {
            'data_frame': plot_df,
            'x': x_col,
            'y': y_col,
            'color': color_col,
            'size': size_col,
            'trendline': config.get('trendline'),
            'log_x': config.get('log_x', False),
            'log_y': config.get('log_y', False),
        }
        
        if color_col:
            fig_kwargs['color_discrete_sequence'] = color_sequence
        
        fig_kwargs = {k: v for k, v in fig_kwargs.items() if v is not None}
        
        fig = px.scatter(**fig_kwargs)
        
        if not color_col and not size_col:
            fig.update_traces(marker_color=color_sequence[0])
        
        if config.get('title'):
            fig.update_layout(title_text=config.get('title'))
        else:
            title_text = f"{y_col} vs {x_col}"
            fig.update_layout(title_text=title_text)

        fig = apply_unified_styling(fig, config, 'scatter')

        return fig

    except Exception as e:
        logger.error(f"Error creating scatter plot: {str(e)}", exc_info=True)
        return create_plotly_error_visualization(f"Scatter plot error: {str(e)}")


def _prepare_pie_data(df: pd.DataFrame, names_col: str, values_col: Optional[str], 
                     agg_func: str, missing_label: str) -> Tuple[pd.DataFrame, str, str]:
    """Prepare data for pie chart"""
    if not values_col:
        value_counts = df[names_col].value_counts()
        agg_df = value_counts.rename_axis(names_col).reset_index(name='count')
        values_col_for_plot = 'count'
        default_title = f"Distribution of {names_col}"
    else:
        numeric_series, success = safe_numeric_conversion(df[values_col])
        if not success:
            raise ValueError(f"Column '{values_col}' must be numeric.")
        
        valid_mask = ~numeric_series.isna()
        plot_df = df[valid_mask].copy()
        plot_df[values_col] = numeric_series[valid_mask]
        
        if (plot_df[values_col] < 0).any():
            raise ValueError(f"Column '{values_col}' contains negative values.")
        
        agg_mapping = {
            'sum': 'sum',
            'mean': 'mean',
            'median': 'median',
            'min': 'min',
            'max': 'max'
        }
        
        if agg_func not in agg_mapping:
            logger.warning(f"Invalid agg_func '{agg_func}', defaulting to 'sum'")
            agg_func = 'sum'
        
        agg_df = plot_df.groupby(names_col, observed=True)[values_col].agg(agg_mapping[agg_func]).reset_index()
        values_col_for_plot = values_col
        default_title = f"{agg_func.upper()} of {values_col} by {names_col}"
    
    agg_df[names_col] = (
        agg_df[names_col]
        .astype(str)
        .replace('', missing_label)
        .replace('nan', missing_label)
    )
    
    return agg_df, values_col_for_plot, default_title


def _process_pie_slices(agg_df: pd.DataFrame, names_col: str, values_col: str, 
                       config: Dict[str, Any]) -> pd.DataFrame:
    """Process pie slices with filtering, limiting, and grouping"""
    total = agg_df[values_col].sum()
    if total <= 0:
        raise ValueError(f"Total {values_col} is zero or negative.")
    
    agg_df['percentage'] = (agg_df[values_col] / total) * 100
    
    min_percent = config.get('min_percent', 0)
    if min_percent > 0:
        initial_count = len(agg_df)
        agg_df = agg_df[agg_df['percentage'] >= min_percent].copy()
        if len(agg_df) == 0:
            raise ValueError(f"No slices remain after filtering out slices < {min_percent}%")
        logger.info(f"Filtered out {initial_count - len(agg_df)} slices below {min_percent}%")
    
    slice_limit = config.get('slice_limit')
    group_others = config.get('group_others', True)
    
    if slice_limit and len(agg_df) > slice_limit:
        if group_others:
            keep_count = slice_limit - 1
            if keep_count < 1:
                agg_df = agg_df.nlargest(1, values_col)
            else:
                agg_df_sorted = agg_df.nlargest(keep_count, values_col)
                other_mask = ~agg_df[names_col].isin(agg_df_sorted[names_col])
                other_df = agg_df[other_mask]
                other_sum = other_df[values_col].sum()
                other_percentage = other_df['percentage'].sum()
                
                if len(other_df) > 0 and other_sum > 0:
                    other_row = pd.DataFrame({
                        names_col: ['Other'],
                        values_col: [other_sum],
                        'percentage': [other_percentage]
                    })
                    agg_df = pd.concat([agg_df_sorted, other_row], ignore_index=True)
                    logger.info(f"Grouped {len(other_df)} slices into 'Other' category ({other_percentage:.1f}%)")
                else:
                    agg_df = agg_df_sorted
        else:
            agg_df = agg_df.nlargest(slice_limit, values_col)
            logger.info(f"Truncated to top {slice_limit} slices (no 'Other' category)")
    
    sort_slices = config.get('sort_slices', True)
    if sort_slices:
        if 'Other' in agg_df[names_col].values:
            other_row = agg_df[agg_df[names_col] == 'Other']
            main_rows = agg_df[agg_df[names_col] != 'Other'].sort_values(
                values_col, ascending=False
            )
            agg_df = pd.concat([main_rows, other_row], ignore_index=True)
        else:
            agg_df = agg_df.sort_values(values_col, ascending=False)
    
    return agg_df


def plot_plotly_pie_chart(df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
    """Production-ready pie chart with comprehensive slice management"""
    names_col = config.get('names_col')
    values_col = config.get('values_col')
    
    valid, error_msg = validate_columns(df, [names_col])
    if not valid:
        return create_plotly_error_visualization(error_msg)
    
    if values_col:
        valid, error_msg = validate_columns(df, [values_col])
        if not valid:
            return create_plotly_error_visualization(error_msg)
    
    # FIX: Changed 'text_info' to 'textinfo' to match chart_handlers.py
    textinfo = config.get('textinfo', 'label+percent')
    valid_text_info = {
        'label', 'value', 'percent', 'text', 'label+value', 'label+percent',
        'value+percent', 'label+value+percent', 'percent+label', 'none'
    }
    if textinfo != 'none' and textinfo not in valid_text_info:
        logger.warning(f"Invalid textinfo: {textinfo}. Using 'label+percent'")
        textinfo = 'label+percent'
    
    try:
        missing_label = config.get('missing_label', '<Missing>')
        if missing_label in df[names_col].values:
            logger.warning(f"Missing label '{missing_label}' conflicts with existing category names")
        
        agg_df, values_col_for_plot, default_title = _prepare_pie_data(
            df, names_col, values_col, config.get('agg_func', 'sum'), missing_label
        )
        
        if len(agg_df) == 0:
            return create_plotly_error_visualization("No data available after cleaning")
        
        agg_df = _process_pie_slices(agg_df, names_col, values_col_for_plot, config)
        
        color_sequence = _get_color_sequence(config)
        
        pull_array = []
        pull_slices = config.get('pull_slices', {})
        pull_categories = set(pull_slices.keys()) if isinstance(pull_slices, dict) else set(pull_slices or [])
        
        for category in agg_df[names_col]:
            if isinstance(pull_slices, dict):
                pull_array.append(pull_slices.get(category, 0))
            elif category in pull_categories:
                pull_array.append(0.1)
            else:
                pull_array.append(0)
        
        if pull_slices:
            available_categories = set(agg_df[names_col])
            missing = pull_categories - available_categories
            if missing:
                logger.warning(f"Pull slices not found in data: {missing}")
        
        fig = px.pie(
            agg_df,
            names=names_col,
            values=values_col_for_plot,
            hole=config.get('hole', 0.0),
            color_discrete_sequence=color_sequence,
            color_discrete_map=config.get('color_discrete_map')
        )
        
        fig.update_traces(
            textposition=config.get('text_position', 'inside'),
            textinfo=textinfo,  # FIX: Changed to textinfo
            pull=pull_array if any(pull_array) else None
        )
        
        final_title = config.get('title', default_title)
        hole = config.get('hole', 0.0)
        if hole > 0 and not config.get('title'):
            final_title += " (Donut)"
        
        if values_col_for_plot == 'count':
            hovertemplate = (
                "<b>%{label}</b><br>"
                "Count: %{value:,}<br>"
                "Percentage: %{percent:.1%}<br>"
                "<extra></extra>"
            )
        else:
            hovertemplate = (
                "<b>%{label}</b><br>"
                "Value: %{value:,.2f}<br>"
                "Percentage: %{percent:.1%}<br>"
                "<extra></extra>"
            )
        
        fig.update_traces(hovertemplate=hovertemplate)
        
        fig.update_layout(
            title_text=final_title,
            showlegend=config.get('showlegend', True)
        )
        
        fig = apply_unified_styling(fig, config, 'pie')
        
        return fig
        
    except Exception as e:
        logger.error(f"Error plotting pie chart: {e}")
        return create_plotly_error_visualization(f"Pie chart error: {str(e)}")


def plot_plotly_box_plot(df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
    """Plot box plot with enhanced color palette support"""
    y_col = config.get('y_col')
    x_col = config.get('x_col')
    color_col = config.get('color_col')
    
    valid, error_msg = validate_columns(df, [y_col])
    if not valid:
        return create_plotly_error_visualization(error_msg)
    
    if x_col:
        valid, error_msg = validate_columns(df, [x_col])
        if not valid:
            return create_plotly_error_visualization(error_msg)
    
    if color_col:
        valid, error_msg = validate_columns(df, [color_col])
        if not valid:
            return create_plotly_error_visualization(error_msg)

    try:
        plot_df = df.copy()
        numeric_data, success = safe_numeric_conversion(plot_df[y_col])
        if not success:
            return create_plotly_error_visualization(f"Column '{y_col}' must be numeric.")
        plot_df[y_col] = numeric_data
        plot_df = plot_df.dropna(subset=[y_col])

        if plot_df.empty:
            return create_plotly_error_visualization(f"No valid numeric data in column '{y_col}' for box plot.")

        color_sequence = _get_color_sequence(config)
        
        fig_kwargs = {
            'data_frame': plot_df,
            'y': y_col,
            'notched': config.get('notched', False),
            'points': config.get('points', 'outliers'),
            'title': f'Box Plot of {y_col.replace("_", " ").title()}'
        }
        
        if x_col:
            fig_kwargs['x'] = x_col
            fig_kwargs['title'] += f' by {x_col.replace("_", " ").title()}'
        
        if color_col:
            fig_kwargs['color'] = color_col
            fig_kwargs['color_discrete_sequence'] = color_sequence

        fig = px.box(**fig_kwargs)
        
        fig = apply_unified_styling(fig, config, 'box')
        
        return fig

    except Exception as e:
        logger.error(f"Error plotting box plot: {e}")
        return create_plotly_error_visualization(f"Box plot error: {str(e)}")


def plot_plotly_heatmap(df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
    """Correlation heatmap - replaces generic heatmap with statistical focus"""
    numeric_cols = config.get('numeric_cols', [])
    correlation_method = config.get('correlation_method', 'pearson')
    show_covariance = config.get('show_covariance', False)
    
    if not numeric_cols:
        return create_plotly_error_visualization("No numeric columns selected")
    
    if len(numeric_cols) < 2:
        return create_plotly_error_visualization("Need at least 2 numeric columns for correlation")
    
    valid, error_msg = validate_columns(df, numeric_cols)
    if not valid:
        return create_plotly_error_visualization(error_msg)

    try:
        plot_df = df[numeric_cols].copy()
        plot_df = plot_df.dropna()
        
        if len(plot_df) < 3:
            return create_plotly_error_visualization("Not enough data points after removing missing values")
        
        if show_covariance:
            matrix = plot_df.cov()
            matrix_title = "Covariance Matrix"
            zmin = None
            zmax = None
            hover_template = "Covariance: %{z:.3f}<br>%{x} vs %{y}<extra></extra>"
        else:
            matrix = plot_df.corr(method=correlation_method)
            matrix_title = f"{correlation_method.title()} Correlation Matrix"
            zmin = -1.0
            zmax = 1.0
            hover_template = "Correlation: %{z:.3f}<br>%{x} vs %{y}<extra></extra>"
        
        if config.get('cluster_matrix', False):
            try:
                from scipy.cluster.hierarchy import linkage, leaves_list
                from scipy.spatial.distance import squareform
                
                distance_matrix = 1 - np.abs(matrix.values)
                np.fill_diagonal(distance_matrix, 0)
                linkage_matrix = linkage(squareform(distance_matrix), method='average')
                reorder_indices = leaves_list(linkage_matrix)
                matrix = matrix.iloc[reorder_indices, reorder_indices]
            except ImportError:
                logger.warning("SciPy not available for clustering, returning original matrix")
        
        if config.get('lower_triangle', True) and not config.get('cluster_matrix', False):
            lower_matrix = matrix.copy()
            mask = np.triu(np.ones_like(matrix, dtype=bool), k=1)
            lower_matrix.values[mask] = np.nan
            matrix = lower_matrix
        
        significance_mask = None
        if config.get('show_significance', False) and not show_covariance:
            significance_mask = _calculate_significance_mask(plot_df, correlation_method)
            if config.get('lower_triangle', True):
                significance_mask = _get_lower_triangle_matrix(significance_mask)
        
        heatmap_kwargs = {
            'z': matrix.values,
            'x': matrix.columns,
            'y': matrix.index,
            'colorscale': config.get('color_scale', 'RdBu'),
            'hoverongaps': False,
            'hoverinfo': 'text',
            'text': matrix.values if config.get('show_values', True) else None,
            'texttemplate': "%{text:.2f}" if config.get('show_values', True) else "",
            'textfont': {"size": 10},
        }
        
        if not significance_mask:
            heatmap_kwargs['zmin'] = zmin
            heatmap_kwargs['zmax'] = zmax
        
        fig = go.Figure(data=go.Heatmap(**heatmap_kwargs))
        
        fig.update_traces(
            hovertemplate=hover_template
        )
        
        if significance_mask is not None:
            fig = _apply_significance_styling(fig, matrix, significance_mask)
        
        method_display = "Covariance" if show_covariance else f"{correlation_method.title()} Correlation"
        title = f"{method_display} Matrix"
        if config.get('cluster_matrix'):
            title += " (Clustered)"
        if config.get('lower_triangle'):
            title += " (Lower Triangle)"
        
        fig.update_layout(
            title=title,
            xaxis_title="Variables",
            yaxis_title="Variables",
            xaxis={'side': 'bottom'},
            height=500 + len(numeric_cols) * 20,
            width=500 + len(numeric_cols) * 20
        )
        
        if config.get('invert_colors', False):
            fig.update_traces(colorscale=config.get('color_scale', 'RdBu') + '_r')
        
        fig = apply_unified_styling(fig, config, 'heatmap')
        
        return fig

    except Exception as e:
        logger.error(f"Error plotting correlation heatmap: {e}")
        return create_plotly_error_visualization(f"Correlation heatmap error: {str(e)}")


def _calculate_significance_mask(df: pd.DataFrame, method: str = 'pearson') -> pd.DataFrame:
    """Calculate p-values for correlations and return significance mask"""
    try:
        from scipy.stats import pearsonr, spearmanr
        
        n_vars = len(df.columns)
        p_matrix = np.ones((n_vars, n_vars))
        
        for i in range(n_vars):
            for j in range(i, n_vars):
                if i == j:
                    p_matrix[i, j] = 0
                else:
                    col1 = df.iloc[:, i]
                    col2 = df.iloc[:, j]
                    
                    valid_mask = ~(col1.isna() | col2.isna())
                    if valid_mask.sum() < 3:
                        p_matrix[i, j] = 1.0
                        p_matrix[j, i] = 1.0
                        continue
                    
                    x_vals = col1[valid_mask]
                    y_vals = col2[valid_mask]
                    
                    try:
                        if method == 'pearson':
                            _, p_value = pearsonr(x_vals, y_vals)
                        else:
                            _, p_value = spearmanr(x_vals, y_vals)
                        
                        p_matrix[i, j] = p_value
                        p_matrix[j, i] = p_value
                    except Exception:
                        p_matrix[i, j] = 1.0
                        p_matrix[j, i] = 1.0
        
        significance_mask = p_matrix > 0.05
        return pd.DataFrame(significance_mask, index=df.columns, columns=df.columns)
        
    except ImportError:
        logger.warning("SciPy not available for significance testing")
        return pd.DataFrame(np.zeros((len(df.columns), len(df.columns)),
                            index=df.columns, columns=df.columns), dtype=bool)
    except Exception as e:
        logger.warning(f"Significance calculation failed: {e}")
        return pd.DataFrame(np.zeros((len(df.columns), len(df.columns)),
                            index=df.columns, columns=df.columns), dtype=bool)


def _get_lower_triangle_matrix(matrix: pd.DataFrame) -> pd.DataFrame:
    """Return only the lower triangle of the matrix (with NaN in upper)"""
    lower_matrix = matrix.copy()
    mask = np.triu(np.ones_like(matrix, dtype=bool), k=1)
    lower_matrix.values[mask] = np.nan
    return lower_matrix


def _apply_significance_styling(fig: go.Figure, matrix: pd.DataFrame, significance_mask: pd.DataFrame) -> go.Figure:
    """Apply gray styling to non-significant correlations"""
    try:
        non_sig_values = matrix.where(significance_mask)
        
        fig.add_trace(go.Heatmap(
            z=non_sig_values.values,
            x=matrix.columns,
            y=matrix.index,
            colorscale=[(0, 'rgba(200,200,200,0.3)'), (1, 'rgba(200,200,200,0.3)')],
            showscale=False,
            hoverinfo='skip',
            text=non_sig_values.values,
            texttemplate="%{text:.2f}",
            textfont={"size": 10, "color": 'rgba(100,100,100,0.7)'}
        ))
        
        fig.data = fig.data[::-1]
        
    except Exception as e:
        logger.warning(f"Could not apply significance styling: {e}")
    
    return fig


def plot_plotly_violin_plot(df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
    """Plot violin plot with enhanced color palette support"""
    y_col = config.get('y_col')
    x_col = config.get('x_col')
    color_col = config.get('color_col')
    
    cols_to_validate = [y_col]
    if x_col:
        cols_to_validate.append(x_col)
    if color_col:
        cols_to_validate.append(color_col)

    valid, error_msg = validate_columns(df, cols_to_validate)
    if not valid:
        return create_plotly_error_visualization(error_msg)

    try:
        plot_df = df.copy()
        numeric_data, success = safe_numeric_conversion(plot_df[y_col])
        if not success:
            return create_plotly_error_visualization(f"Column '{y_col}' must be numeric.")
        plot_df[y_col] = numeric_data
        plot_df = plot_df.dropna(subset=[y_col])

        if plot_df.empty:
            return create_plotly_error_visualization(f"No valid numeric data in column '{y_col}' for violin plot.")

        color_sequence = _get_color_sequence(config)
        
        fig_kwargs = {
            'data_frame': plot_df,
            'y': y_col,
            'box': True
        }

        title = f'Violin Plot: {y_col.replace("_", " ").title()}'
        if x_col:
            fig_kwargs['x'] = x_col
            title += f' by {x_col.replace("_", " ").title()}'
        if color_col:
            fig_kwargs['color'] = color_col
            fig_kwargs['color_discrete_sequence'] = color_sequence
            title += f' (colored by {color_col.replace("_", " ").title()})'

        fig_kwargs['title'] = title
        fig = px.violin(**fig_kwargs)
        
        fig = apply_unified_styling(fig, config, 'violin')
        
        return fig
    except Exception as e:
        logger.error(f"Error plotting violin plot: {e}")
        return create_plotly_error_visualization(f"Violin plot error: {str(e)}")


def plot_plotly_correlation_matrix(df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
    """Plot correlation matrix with enhanced color palette support"""
    try:
        columns = config.get('columns')
        if columns:
            valid, error_msg = validate_columns(df, columns)
            if not valid:
                return create_plotly_error_visualization(error_msg)
            numeric_df = df[columns]
        else:
            numeric_df = df.select_dtypes(include=[np.number])

        if numeric_df.empty:
            return create_plotly_error_visualization("No numeric columns found for correlation matrix.")

        corr_matrix = numeric_df.corr()
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale='RdBu',
            zmid=0,
            text=np.round(corr_matrix.values, 2),
            texttemplate="%{text}",
            textfont={"size": 10},
            hoverongaps=False
        ))

        fig.update_layout(
            title='Correlation Matrix',
            xaxis_title='Variables',
            yaxis_title='Variables'
        )
        
        fig = apply_unified_styling(fig, config, 'heatmap')
        
        return fig
    except Exception as e:
        logger.error(f"Error plotting correlation matrix: {e}")
        return create_plotly_error_visualization(f"Correlation matrix error: {str(e)}")


def plot_plotly_bubble_chart(df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
    """Plot bubble chart with enhanced color palette support"""
    x_col = config.get('x_col')
    y_col = config.get('y_col')
    size_col = config.get('size_col')
    color_col = config.get('color_col')
    
    valid, error_msg = validate_columns(df, [x_col, y_col, size_col])
    if not valid:
        return create_plotly_error_visualization(error_msg)

    if color_col:
        valid, error_msg = validate_columns(df, [color_col])
        if not valid:
            return create_plotly_error_visualization(error_msg)

    try:
        plot_df = df.copy()
        
        numeric_data_x, success_x = safe_numeric_conversion(plot_df[x_col])
        if not success_x:
            return create_plotly_error_visualization(f"Column '{x_col}' must be numeric.")
        plot_df[x_col] = numeric_data_x

        numeric_data_y, success_y = safe_numeric_conversion(plot_df[y_col])
        if not success_y:
            return create_plotly_error_visualization(f"Column '{y_col}' must be numeric.")
        plot_df[y_col] = numeric_data_y

        numeric_data_size, success_size = safe_numeric_conversion(plot_df[size_col])
        if not success_size:
            return create_plotly_error_visualization(f"Column '{size_col}' must be numeric.")
        
        plot_df[size_col] = numeric_data_size.abs()

        plot_df = plot_df.dropna(subset=[x_col, y_col, size_col])

        if plot_df.empty:
            return create_plotly_error_visualization(f"No valid data in columns '{x_col}', '{y_col}', and '{size_col}' for bubble chart.")

        color_sequence = _get_color_sequence(config)
        
        fig_kwargs = {
            'data_frame': plot_df,
            'x': x_col,
            'y': y_col,
            'size': size_col,
            'hover_name': config.get('hover_name'),
            'log_x': config.get('log_x', False),
            'size_max': config.get('size_max', 60),
            'title': f'Bubble Chart: {y_col.replace("_", " ").title()} vs {x_col.replace("_", " ").title()}'
        }

        if color_col:
            fig_kwargs['color'] = color_col
            fig_kwargs['color_discrete_sequence'] = color_sequence

        fig = px.scatter(**fig_kwargs)
        
        if not color_col:
            fig.update_traces(marker_color=color_sequence[0])
        
        fig = apply_unified_styling(fig, config, 'bubble')
        
        return fig

    except Exception as e:
        logger.error(f"Error plotting bubble chart: {e}")
        return create_plotly_error_visualization(f"Bubble chart error: {str(e)}")


def plot_plotly_treemap(df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
    """Enhanced treemap with simplified styling and better performance"""
    path = config.get('path', [])
    values = config.get('values')
    color = config.get('color')
    
    if not path:
        return create_plotly_error_visualization("Please specify at least one path column for treemap hierarchy")
    
    valid, error_msg = validate_columns(df, path)
    if not valid:
        return create_plotly_error_visualization(error_msg)
    
    if values and values != 'count':
        valid, error_msg = validate_columns(df, [values])
        if not valid:
            return create_plotly_error_visualization(error_msg)
    
    if color:
        valid, error_msg = validate_columns(df, [color])
        if not valid:
            return create_plotly_error_visualization(error_msg)

    try:
        plot_df = df.copy()
        
        for col in path:
            # Convert categorical to string to allow new categories
            if pd.api.types.is_categorical_dtype(plot_df[col]):
                plot_df[col] = plot_df[col].astype(str)
            plot_df[col] = plot_df[col].fillna('Unknown')
                    
        if config.get('aggregate_small_categories'):
            max_categories = config.get('max_categories', 20)
            for col in path:
                if plot_df[col].nunique() > max_categories:
                    top_categories = plot_df[col].value_counts().head(max_categories - 1).index
                    plot_df[col] = plot_df[col].where(plot_df[col].isin(top_categories), 'Other')
        
        if not values:
            count_df = plot_df.groupby(path).size().reset_index(name='count')
            plot_df = count_df
            values = 'count'
        else:
            agg_func = config.get('agg_func', 'sum')
            if agg_func != 'sum' and values != 'count':
                agg_df = plot_df.groupby(path)[values].agg(agg_func).reset_index()
                plot_df = agg_df
        
        if values and values != 'count':
            numeric_data, success = safe_numeric_conversion(plot_df[values])
            if not success:
                return create_plotly_error_visualization(f"Column '{values}' must be numeric for treemap values.")
            plot_df[values] = numeric_data
        
        if color:
            plot_df[color] = plot_df[color].fillna('Unknown' if not pd.api.types.is_numeric_dtype(plot_df[color]) else 0)
            
            if pd.api.types.is_numeric_dtype(plot_df[color]):
                color_numeric, success = safe_numeric_conversion(plot_df[color])
                if success:
                    plot_df[color] = color_numeric
        
        plot_df = plot_df.dropna(subset=path + ([values] if values and values != 'count' else []))
        
        if plot_df.empty:
            return create_plotly_error_visualization("No valid data remains after filtering.")
        
        color_sequence = _get_color_sequence(config)
        
        fig_kwargs = {
            'data_frame': plot_df,
            'path': path,
            'title': config.get('title', f"Treemap by {' → '.join(path)}")
        }
        
        if values:
            fig_kwargs['values'] = values
        
        if color:
            fig_kwargs['color'] = color
            if pd.api.types.is_numeric_dtype(plot_df[color]):
                fig_kwargs['color_continuous_scale'] = config.get('color_scale', 'Viridis')
            else:
                plot_df[color] = plot_df[color].astype(str)
                if config.get('color_discrete_map'):
                    fig_kwargs['color_discrete_map'] = config.get('color_discrete_map')
                else:
                    fig_kwargs['color_discrete_sequence'] = color_sequence
        
        hover_data = {}
        if config.get('hover_data'):
            hover_cols = config.get('hover_data', [])
            for col in hover_cols:
                if col in plot_df.columns:
                    hover_data[col] = True
        
        if hover_data:
            fig_kwargs['hover_data'] = hover_data
        
        fig = px.treemap(**fig_kwargs)
        
        if config.get('branchvalues'):
            fig.update_traces(branchvalues=config['branchvalues'])
        
        if config.get('maxdepth') is not None:
            fig.update_traces(maxdepth=config['maxdepth'])
        
        if config.get('textinfo'):
            fig.update_traces(textinfo=config['textinfo'])
        
        pathbar_config = {}
        if 'pathbar_visible' in config:
            pathbar_config['visible'] = config['pathbar_visible']
        
        if config.get('pathbar_side'):
            pathbar_config['side'] = config['pathbar_side']
        
        if pathbar_config:
            fig.update_traces(pathbar=pathbar_config)
        
        fig.update_layout(
            margin=dict(t=50, l=25, r=25, b=25)
        )
        
        fig = apply_unified_styling(fig, config, 'treemap')
        
        return fig
        
    except Exception as e:
        logger.error(f"Error plotting treemap: {e}")
        return create_plotly_error_visualization(f"Treemap error: {str(e)}")


def _auto_detect_geo_columns(df: pd.DataFrame) -> tuple:
    """Auto-detect geographic columns"""
    lat_candidates = [col for col in df.columns if any(geo in col.lower() for geo in ['lat', 'latitude'])]
    lon_candidates = [col for col in df.columns if any(geo in col.lower() for geo in ['lon', 'long', 'longitude'])]
    
    default_lat = lat_candidates[0] if lat_candidates else None
    default_lon = lon_candidates[0] if lon_candidates else None
    
    return default_lat, default_lon


def plot_plotly_bubble_map(df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
    """Final optimized bubble map plotting with full styling integration"""
    if not config.get('lat_col') or not config.get('lon_col'):
        lat_col, lon_col = _auto_detect_geo_columns(df)
        if lat_col and lon_col:
            config['lat_col'] = lat_col
            config['lon_col'] = lon_col
        else:
            return create_plotly_error_visualization(
                "Could not auto-detect latitude/longitude columns. Please specify them manually."
            )
    
    fig = create_bubble_map_from_dataframe(df=df, config=config)
    
    if fig is not None and isinstance(fig, go.Figure):
        fig = apply_unified_styling(fig, config, 'bubble_map')
        return fig
    
    return create_plotly_error_visualization("Bubble map creation failed")


def create_bubble_map_from_dataframe(
    df: pd.DataFrame,
    config: Dict[str, Any]
) -> go.Figure:
    """
    Final optimized bubble map with enhanced hover and performance
    """
    lat_col = config.get('lat_col')
    lon_col = config.get('lon_col')
    
    if not lat_col or not lon_col:
        return create_plotly_error_visualization(
            "Please specify latitude and longitude columns"
        )
    
    cols_to_validate = [lat_col, lon_col]
    if config.get('size_col') and config['size_col'] != 'count':
        cols_to_validate.append(config['size_col'])
    if config.get('color_col'):
        cols_to_validate.append(config['color_col'])
    if config.get('text_col'):
        cols_to_validate.append(config['text_col'])
    
    valid, error_msg = validate_columns(df, [col for col in cols_to_validate if col])
    if not valid or df.empty:
        return create_plotly_error_visualization(error_msg or "Empty DataFrame.")
    
    try:
        plot_df = df.copy()
        
        numeric_cols = [lat_col, lon_col, config.get('size_col'), config.get('color_col')]
        for col in numeric_cols:
            if col and col in plot_df.columns:
                numeric_data, success = safe_numeric_conversion(plot_df[col])
                if success:
                    plot_df[col] = numeric_data
        
        valid_coords = (
            (plot_df[lat_col] >= -90) & (plot_df[lat_col] <= 90) &
            (plot_df[lon_col] >= -180) & (plot_df[lon_col] <= 180)
        )
        plot_df = plot_df[valid_coords]
        
        if plot_df.empty:
            return create_plotly_error_visualization(
                "No valid coordinates found. Latitudes must be between -90 and 90, longitudes between -180 and 180."
            )
        
        if config.get('apply_jitter', False) and config.get('group_by') == 'Raw Points (No Grouping)':
            jitter_strength = config.get('jitter_strength', 0.01)
            plot_df = _apply_coordinate_jitter(plot_df, lat_col, lon_col, jitter_strength)
        
        group_by = config.get('group_by')
        if group_by and group_by != 'Raw Points (No Grouping)':
            plot_df = _apply_geographic_grouping(plot_df, config)
        
        required_cols = [lat_col, lon_col] + ([config['size_col']] if config.get('size_col') and config['size_col'] in plot_df.columns else [])
        plot_df = plot_df.dropna(subset=required_cols)
        
        if plot_df.empty:
            return create_plotly_error_visualization("No valid data after processing.")
        
        logger.info(f"Bubble map: {len(plot_df)} points after processing (grouping: {group_by}, jitter: {config.get('apply_jitter', False)})")
        
        return _create_optimized_bubble_map(plot_df, config)
        
    except Exception as e:
        logger.error(f"Error creating bubble map: {e}")
        return create_plotly_error_visualization(f"Bubble map error: {str(e)}")


def _apply_coordinate_jitter(df: pd.DataFrame, lat_col: str, lon_col: str, strength: float = 0.01) -> pd.DataFrame:
    """Apply customizable jitter to prevent coordinate overlap"""
    jittered_df = df.copy()
    
    # Use deterministic seed based on data hash
    data_hash = hash(str(df[[lat_col, lon_col]].values.tobytes())) % 10000
    rng = np.random.default_rng(data_hash)
    
    jittered_df[lat_col] = jittered_df[lat_col] + rng.uniform(-strength, strength, len(jittered_df))
    jittered_df[lon_col] = jittered_df[lon_col] + rng.uniform(-strength, strength, len(jittered_df))
    
    jittered_df[lat_col] = jittered_df[lat_col].clip(-90, 90)
    jittered_df[lon_col] = jittered_df[lon_col].clip(-180, 180)
    
    logger.info(f"Applied jitter (strength: {strength}) to {len(jittered_df)} points")
    return jittered_df


def _apply_geographic_grouping(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """Apply geographic grouping with optimized aggregation"""
    lat_col = config['lat_col']
    lon_col = config['lon_col']
    group_by = config.get('group_by')
    size_col = config.get('size_col')
    agg_func = config.get('agg_func', 'sum')
    text_col = config.get('text_col')
    color_col = config.get('color_col')
    
    group_cols = [group_by] if group_by and group_by != 'Raw Points (No Grouping)' else []
    
    agg_dict = {
        lat_col: 'mean',
        lon_col: 'mean'
    }
    
    if size_col and size_col != 'count':
        agg_dict[size_col] = agg_func
    else:
        agg_dict['_count'] = 'size'
    
    if text_col and text_col not in group_cols:
        if pd.api.types.is_numeric_dtype(df[text_col]):
            agg_dict[text_col] = agg_func
        else:
            agg_dict[text_col] = lambda x: x.mode()[0] if not x.mode().empty else x.iloc[0]
    
    if color_col and color_col not in group_cols:
        if pd.api.types.is_numeric_dtype(df[color_col]):
            agg_dict[color_col] = 'mean'
        else:
            agg_dict[color_col] = lambda x: x.mode()[0] if not x.mode().empty else x.iloc[0]
    
    grouped_df = df.groupby(group_cols).agg(agg_dict).reset_index()
    
    if not size_col or size_col == 'count':
        grouped_df = grouped_df.rename(columns={'_count': 'count'})
        config['size_col'] = 'count'
    
    logger.info(f"Grouped {len(df)} points into {len(grouped_df)} groups by '{group_by}'")
    return grouped_df


def _create_optimized_bubble_map(df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
    """Create optimized bubble map with enhanced hover and original value display"""
    lat_col = config['lat_col']
    lon_col = config['lon_col']
    size_col = config.get('size_col')
    color_col = config.get('color_col')
    text_col = config.get('text_col')
    
    lat = df[lat_col].tolist()
    lon = df[lon_col].tolist()
    
    color_sequence = _get_color_sequence(config)
    
    size_min = config.get('size_min', 8)
    size_max = config.get('size_max', 40)
    
    if size_col and size_col in df.columns:
        original_size_values = df[size_col].tolist()
        sizes = _smart_size_scaling(original_size_values, config.get('size_mode', 'area'), size_min, size_max)
    else:
        sizes = [size_min] * len(df)
        original_size_values = [1] * len(df)
    
    color = None
    color_continuous = False
    if color_col and color_col in df.columns:
        color = df[color_col].tolist()
        color_continuous = pd.api.types.is_numeric_dtype(df[color_col])
    
    hover_texts = []
    if text_col and text_col in df.columns:
        hover_texts = df[text_col].astype(str).tolist()
    elif not size_col:
        hover_texts = [f"Point {i+1} (Fixed Size)" for i in range(len(df))]
    else:
        hover_texts = [f"{size_col}: {val}" for val in original_size_values]
    
    customdata = []
    for i in range(len(df)):
        row_data = [original_size_values[i], lat[i], lon[i]]
        if color_col:
            row_data.append(color[i] if color else None)
        customdata.append(row_data)
    
    title = config.get('title')
    if not title:
        size_display = size_col if size_col else "Fixed Size"
        color_display = f" by {color_col}" if color_col else ""
        title = f"Bubble Map of {size_display}{color_display}"
    
    fig = go.Figure()
    
    if color and color_continuous:
        fig.add_trace(go.Scattergeo(
            lon=lon,
            lat=lat,
            text=hover_texts,
            customdata=customdata,
            marker=dict(
                size=sizes,
                color=color,
                colorscale=config.get('color_scale', 'Viridis'),
                showscale=True,
                sizemode='area',
                sizeref=2.0 * max(sizes) / (size_max ** 2) if sizes else 1.0,
                opacity=config.get('opacity', 0.7),
                line=dict(width=0.5, color='darkgray')
            ),
            hovertemplate=(
                "<b>%{text}</b><br>" +
                (f"{color_col}: %{{marker.color:.2f}}<br>" if color_continuous else "") +
                (f"{size_col}: %{{customdata[0]:.2f}}<br>" if size_col else "Fixed Size<br>") +
                "Lat: %{customdata[1]:.4f}<br>Lon: %{customdata[2]:.4f}<extra></extra>"
            ),
            name=""
        ))
    elif color and not color_continuous:
        unique_colors = list(set(color))
        
        for i, color_val in enumerate(unique_colors):
            mask = [c == color_val for c in color]
            subset_indices = [j for j in range(len(color)) if mask[j]]
            
            subset_lon = [lon[j] for j in subset_indices]
            subset_lat = [lat[j] for j in subset_indices]
            subset_texts = [hover_texts[j] for j in subset_indices]
            subset_sizes = [sizes[j] for j in subset_indices]
            subset_customdata = [customdata[j] for j in subset_indices]
            
            fig.add_trace(go.Scattergeo(
                lon=subset_lon,
                lat=subset_lat,
                text=subset_texts,
                customdata=subset_customdata,
                marker=dict(
                    size=subset_sizes,
                    color=color_sequence[i % len(color_sequence)],
                    sizemode='area',
                    sizeref=2.0 * max(sizes) / (size_max ** 2) if sizes else 1.0,
                    opacity=config.get('opacity', 0.7),
                    line=dict(width=0.5, color='darkgray')
                ),
                name=str(color_val),
                hovertemplate=(
                    "<b>%{text}</b><br>" +
                    f"{color_col}: {color_val}<br>" +
                    (f"{size_col}: %{{customdata[0]:.2f}}<br>" if size_col else "Fixed Size<br>") +
                    "Lat: %{customdata[1]:.4f}<br>Lon: %{customdata[2]:.4f}<extra></extra>"
                )
            ))
    else:
        fig.add_trace(go.Scattergeo(
            lon=lon,
            lat=lat,
            text=hover_texts,
            customdata=customdata,
            marker=dict(
                size=sizes,
                color=color_sequence[0],
                sizemode='area',
                sizeref=2.0 * max(sizes) / (size_max ** 2) if sizes else 1.0,
                opacity=config.get('opacity', 0.7),
                line=dict(width=0.5, color='darkgray')
            ),
            hovertemplate=(
                "<b>%{text}</b><br>" +
                (f"{size_col}: %{{customdata[0]:.2f}}<br>" if size_col else "Fixed Size<br>") +
                "Lat: %{customdata[1]:.4f}<br>Lon: %{customdata[2]:.4f}<extra></extra>"
            ),
            name=""
        ))
    
    geo_config = dict(
        scope=config.get('scope', 'world'),
        projection_type=config.get('projection_type', 'natural earth'),
        showland=True,
        landcolor="rgb(240, 240, 240)",
        showcountries=True,
        countrycolor="white",
        showocean=True,
        oceancolor="rgb(204, 229, 255)",
        showframe=False,
        showcoastlines=True,
        coastlinecolor="white"
    )
    
    if config.get('auto_zoom', True) and len(df) > 0:
        geo_config['fitbounds'] = "locations"
    
    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor='center'),
        geo=geo_config,
        showlegend=config.get('show_legend', bool(color and not color_continuous)),
        height=500,
        margin=dict(t=60, b=20, l=20, r=20)
    )
    
    return fig


def _smart_size_scaling(sizes: List[float], size_mode: str, size_min: int = 8, size_max: int = 40) -> List[float]:
    """Apply perceptually accurate size scaling with configurable range"""
    if not sizes:
        return []
    
    if len(sizes) > 10:
        q1, q3 = np.percentile(sizes, [25, 75])
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        filtered_sizes = [s for s in sizes if lower_bound <= s <= upper_bound]
        if filtered_sizes:
            min_val, max_val = min(filtered_sizes), max(filtered_sizes)
        else:
            min_val, max_val = min(sizes), max(sizes)
    else:
        min_val, max_val = min(sizes), max(sizes)
    
    if max_val == min_val:
        return [size_max] * len(sizes)
    
    if size_mode == 'area':
        scaled = [np.sqrt((s - min_val) / (max_val - min_val)) for s in sizes]
    elif size_mode == 'diameter':
        scaled = [(s - min_val) / (max_val - min_val) for s in sizes]
    else:
        scaled = [(s - min_val) / (max_val - min_val) for s in sizes]
    
    return [size_min + (size_max - size_min) * s for s in scaled]


# ============================================================================
# CARD, KPI, AND GAUGE FUNCTIONS
# ============================================================================

def _calculate_target_value(df: pd.DataFrame, config: Dict[str, Any]) -> Optional[float]:
    """Calculate target value with proper error handling"""
    if config.get("target_value") is not None:
        return float(config["target_value"])
    elif config.get("target_col"):
        tcol = config["target_col"]
        tagg = config.get("target_agg", "mean")
        try:
            return _aggregate_series(df[tcol], tagg)
        except KeyError:
            raise ValueError(f"Target column '{tcol}' not found in DataFrame")
        except Exception as e:
            raise ValueError(f"Error calculating target: {str(e)}")
    return None


def _get_kpi_color_logic(current_value: float, target_value: float, polarity: str = "higher") -> Dict[str, Any]:
    """Determine KPI colors based on performance vs target with polarity support"""
    if polarity == "higher":
        meets_target = current_value >= target_value
        color = "rgba(34,197,94,0.25)" if meets_target else "rgba(239,68,68,0.25)"
        delta_config = dict(
            reference=target_value,
            relative=False,
            increasing=dict(color="#16a34a"),
            decreasing=dict(color="#dc2626")
        )
    else:
        meets_target = current_value <= target_value
        color = "rgba(34,197,94,0.25)" if meets_target else "rgba(239,68,68,0.25)"
        delta_config = dict(
            reference=target_value,
            relative=False,
            increasing=dict(color="#dc2626"),
            decreasing=dict(color="#16a34a")
        )
    
    return {
        "bg_color": color,
        "delta_config": delta_config,
        "meets_target": meets_target
    }


def _generate_smart_title(config: dict) -> str:
    """
    Return a human-readable title for cards / KPIs.
    """
    if config.get("title"):
        return config["title"]

    col = config.get("value_col", "Value")
    agg = config.get("agg_func", "sum").lower()
    pref = config.get("prefix", "")
    suff = config.get("suffix", "")
    polarity = config.get("polarity", "higher") if config.get("type") == "kpi" else None

    human_col = " ".join(w.capitalize() for w in col.replace("_", " ").split())

    agg_map = {"sum": "Total", "mean": "Average", "median": "Median",
               "min": "Minimum", "max": "Maximum", "count": "Count of"}
    agg_prefix = agg_map.get(agg, "")

    polarity_hint = ""
    if polarity == "lower":
        polarity_hint = " (Lower is Better)"
    elif polarity == "higher":
        polarity_hint = " (Higher is Better)"

    unit_flair = ""
    if pref or suff:
        unit_flair = f" ({pref}{suff.strip('%')})".rstrip()

    return f"{agg_prefix} {human_col}{unit_flair}{polarity_hint}".strip()


def plot_card(df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
    """
    Ultra-minimal big-number card using go.Indicator.
    """
    value_col = config.get("value_col")
    if value_col not in df.columns:
        return create_plotly_error_visualization(f"Column '{value_col}' not found")

    agg_func = config.get("agg_func", "sum")
    try:
        value = _aggregate_series(df[value_col], agg_func)
    except Exception as e:
        return create_plotly_error_visualization(str(e))
    if pd.isna(value):
        value = 0.0

    title = _generate_smart_title(config)
    prefix = config.get("prefix", "")
    suffix = config.get("suffix", "")
    decimals = config.get("decimals", 2)
    human = config.get("human_format", True)
    title = config.get("title") or title

    number_fmt = "" if human else f",.{decimals}f"

    fig = go.Figure(
        go.Indicator(
            mode="number",
            value=value,
            title={"text": f"<b>{title}</b>"},
            number={"prefix": prefix, "suffix": suffix, "valueformat": number_fmt},
            domain={"x": [0, 1], "y": [0, 1]},
        )
    )

    fig.update_layout(
        margin=dict(t=40, b=20, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis={"visible": False},
        yaxis={"visible": False},
    )
    
    fig = apply_unified_styling(fig, config, 'card')
    
    return fig


def plot_kpi(df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
    """KPI with go.Indicator and optional background sparkline"""
    try:
        value_col = config["value_col"]
        
        if value_col not in df.columns:
            raise ValueError(f"Column '{value_col}' not found in DataFrame")
        
        agg_func = config.get("agg_func", "sum")
        kpi_value = _aggregate_series(df[value_col], agg_func)
        
        if pd.isna(kpi_value):
            kpi_value = 0
            logger.warning(f"KPI value for '{value_col}' with '{agg_func}' is NaN, using 0")

        target_value = _calculate_target_value(df, config)
        
        polarity = config.get("polarity", "higher")
        color_logic = None
        
        if target_value is not None:
            color_logic = _get_kpi_color_logic(kpi_value, target_value, polarity)
        
        trend_col = config.get("trend_col")
        has_sparkline = False
        plot_df = None
        
        if trend_col and trend_col in df.columns:
            plot_df = df.sort_values(trend_col).copy()
            plot_df = plot_df.dropna(subset=[trend_col, value_col])
            has_sparkline = len(plot_df) >= 2
        
        fig = go.Figure()
        
        if has_sparkline and plot_df is not None:
            bg_color = color_logic["bg_color"] if color_logic else "rgba(59, 130, 246, 0.15)"
            line_color = "rgba(59, 130, 246, 0.5)" if not color_logic else (
                "rgba(34, 197, 94, 0.6)" if color_logic["meets_target"] else "rgba(239, 68, 68, 0.6)"
            )
            
            fig.add_trace(
                go.Scatter(
                    x=plot_df[trend_col],
                    y=plot_df[value_col],
                    mode="lines",
                    fill="tozeroy",
                    fillcolor=bg_color,
                    line=dict(color=line_color, width=1.5),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )
            
            y_min = plot_df[value_col].min()
            y_max = plot_df[value_col].max()
            y_padding = (y_max - y_min) * 0.1
            
            if target_value is not None:
                data_range = y_max - y_min
                if data_range > 0:
                    if (target_value >= y_min - data_range * 0.5 and
                        target_value <= y_max + data_range * 0.5):
                        fig.add_hline(
                            y=target_value,
                            line_dash="dash",
                            line_color="rgba(220, 38, 38, 0.4)",
                            line_width=1,
                            opacity=0.6
                        )
        
        title = _generate_smart_title(config)
        prefix = config.get("prefix", "")
        suffix = config.get("suffix", "")
        decimals = config.get("decimals", 2)
        title = config.get("title") or title
        delta_relative = config.get("delta_relative", False)
        use_human_format = config.get("human_format", True)
        
        if use_human_format:
            formatted_value = _human_format(kpi_value, decimals)
            number_config = {
                "prefix": prefix,
                "suffix": suffix,
            }
            display_value = f"{prefix}{formatted_value}{suffix}"
        else:
            number_format = f",.{decimals}f"
            number_config = {
                "prefix": prefix,
                "suffix": suffix,
                "valueformat": number_format,
            }
            display_value = None
        
        indicator_mode = "number"
        if target_value is not None:
            indicator_mode = "number+delta"
        
        delta_config = None
        if target_value is not None and color_logic:
            delta_value = kpi_value - target_value
            
            if delta_relative and target_value != 0:
                delta_config = {
                    "reference": target_value,
                    "relative": True,
                    "valueformat": ".1f",
                    "position": "bottom",
                }
            else:
                delta_config = {
                    "reference": target_value,
                    "relative": False,
                    "position": "bottom",
                }
                
                if use_human_format:
                    delta_config["valueformat"] = ""
                else:
                    delta_config["valueformat"] = f",.{decimals}f"
            
            delta_config.update(color_logic["delta_config"])
        
        indicator_trace = go.Indicator(
            mode=indicator_mode,
            value=kpi_value,
            title={
                "text": f"<b>{title}</b>",
            },
            number=number_config,
            domain={"x": [0, 1], "y": [0, 1]}
        )
        
        if delta_config:
            indicator_trace.delta = delta_config
        
        fig.add_trace(indicator_trace)
        
        layout_config = {
            'paper_bgcolor': "rgba(0,0,0,0)",
            'plot_bgcolor': "rgba(0,0,0,0)",
        }
        
        if has_sparkline:
            layout_config.update({
                'xaxis': {
                    'visible': False,
                    'showgrid': False,
                    'showticklabels': False,
                    'zeroline': False
                },
                'yaxis': {
                    'visible': False,
                    'showgrid': False,
                    'showticklabels': False,
                    'zeroline': False
                }
            })
        
        fig.update_layout(**layout_config)
        
        fig = apply_unified_styling(fig, config, 'kpi')
        
        return fig
        
    except Exception as e:
        logger.error(f"Error plotting KPI: {str(e)}")
        return create_plotly_error_visualization(f"KPI error: {str(e)}")


# ----------------------------------------------------------------------
# GAUGE FUNCTIONS
# ----------------------------------------------------------------------
PALETTES = {
    "normal": {
        "good": "#34d399",
        "bad": "#f87171",
        "neutral": "#3b82f6",
        "threshold": "#ef4444",
        "step_colors": {
            "good": "#bbf7d0",
            "warning": "#fde68a",
            "bad": "#fecaca"
        }
    },
    "colorblind": {
        "good": "#1f77b4",
        "bad": "#ff7f0e",
        "neutral": "#3b82f6",
        "threshold": "#d97706",
        "step_colors": {
            "good": "#a8d8ea",
            "warning": "#ffdfba",
            "bad": "#ffb3ba"
        }
    }
}


def plot_gauge(df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
    """
    Returns a fully-styled Plotly gauge with proper validation and formatting.
    """
    value_col = config["value_col"]
    if value_col not in df.columns:
        return create_plotly_error_visualization(f"Column '{value_col}' not found")

    if "value_pre_agg" in config:
        try:
            value = float(config["value_pre_agg"])
        except (ValueError, TypeError):
            value = 0.0
    else:
        agg = config.get("agg_func", "sum")
        try:
            value = _aggregate_series(df[value_col], agg)
        except Exception as e:
            return create_plotly_error_visualization(str(e))
    
    if pd.isna(value):
        value = 0.0

    min_val = _resolve_bound(df, config.get("min_source"), config.get("min_fixed"),
                             config.get("min_col"), config.get("min_agg", config.get("agg_func", "sum")))
    max_val = _resolve_bound(df, config.get("max_source"), config.get("max_fixed"),
                             config.get("max_col"), config.get("max_agg", config.get("agg_func", "sum")))

    if min_val is None:
        min_val = 0.0
    if max_val is None:
        if value < 0:
            max_val = 0.0
        else:
            max_val = max(value * 2, value + 1, 1.0)

    if min_val >= max_val:
        mid = min_val
        min_val = mid - abs(mid) * 0.1
        max_val = mid + abs(mid) * 0.1
        if min_val == max_val:
            min_val, max_val = -1, 1

    target = _resolve_target(df, config, config.get("agg_func", "sum"))
    
    if target is not None:
        if pd.isna(target):
            return create_plotly_error_visualization("Target value is invalid (NaN)")
        if not (min_val <= target <= max_val):
            return create_plotly_error_visualization(
                f"Target ({target:.2f}) is outside gauge range [{min_val:.2f}, {max_val:.2f}]"
            )

    cb_safe = config.get("colour_blind_safe", False)
    palette = _get_palette(cb_safe)

    polarity = config.get("polarity", "higher")
    strict_comparison = config.get("strict_comparison", False)
    meets_target = _check_target_met(value, target, polarity, strict_comparison)

    human_format = config.get("human_format", False)
    units = config.get("units", "")
    decimals = config.get("decimals", 2)
    title = config.get("title") or _generate_smart_title(config)

    show_ticks = config.get("show_ticks", True)
    gauge_kw = {
        "axis": {
            "range": [min_val, max_val],
            "tickwidth": 1 if show_ticks else 0,
            "tickcolor": "darkgray" if show_ticks else "rgba(0,0,0,0)",
            "visible": show_ticks
        },
        "bar": {
            "color": config.get("bar_color") or _pick_bar_color(meets_target, palette)
        },
        "bgcolor": "rgba(0,0,0,0)",
        "borderwidth": 2 if not config.get("hide_bezel", False) else 0,
        "bordercolor": "gray",
        "steps": _build_steps(min_val, max_val, target, polarity, palette),
    }

    if target is not None:
        gauge_kw["threshold"] = {
            "line": {"color": palette["threshold"], "width": 4},
            "thickness": 0.75,
            "value": target,
        }

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            number={},
            gauge=gauge_kw,
            title={
                "text": title,
            },
        )
    )

    if human_format:
        human_value = _format_number_human(value)
        fig.add_annotation(
            x=0.5, y=0.48,
            xref="paper", yref="paper",
            text=f"<b>{human_value}{units}</b>",
            showarrow=False,
            align="center"
        )
        fig.data[0].number = {"suffix": ""}
    else:
        fig.data[0].number = {
            "suffix": units,
            "valueformat": f",.{decimals}f",
        }

    if target is not None and config.get("show_target_label", False):
        target_display = _format_number_human(target) if human_format else _format_number_locale_safe(target, decimals)
        label_y = 0.02 if not human_format else 0.15
        fig.add_annotation(
            x=0.5, y=label_y,
            xref="paper", yref="paper",
            text=f"Target: {target_display}{units}",
            showarrow=False,
            font={"color": "#6b7280"},
            align="center",
        )

    if target is not None and config.get("show_delta", False):
        delta_val = value - target
        fig.data[0].delta = {
            "reference": target,
            "relative": False,
            "position": "bottom",
            "valueformat": f",.{decimals}f" if not human_format else "",
        }
        fig.data[0].mode = "gauge+number+delta"

    if target is not None:
        accessibility_text = f"{title}: {_format_number_human(value) if human_format else _format_number_locale_safe(value, decimals)}{units} (target {_format_number_human(target) if human_format else _format_number_locale_safe(target, decimals)}{units})"
    else:
        accessibility_text = f"{title}: {_format_number_human(value) if human_format else _format_number_locale_safe(value, decimals)}{units}"
    
    fig.add_annotation(
        text=f"<extra>{accessibility_text}</extra>",
        showarrow=False,
        opacity=0,
        xref="paper", yref="paper",
        x=-10, y=-10
    )

    fig.update_layout(
        margin=dict(t=50, b=20, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_family="Inter, system-ui, sans-serif",
        height=config.get("gauge_height", 300),
        hovermode="closest",
    )
    
    fig = apply_unified_styling(fig, config, 'gauge')
    
    return fig


# ----------------------------------------------------------------------
# GAUGE HELPER FUNCTIONS
# ----------------------------------------------------------------------
from functools import lru_cache

@lru_cache(maxsize=2)
def _get_palette(cb_safe: bool) -> dict:
    """Cached palette retrieval."""
    return PALETTES["colorblind" if cb_safe else "normal"]


def _resolve_bound(df, source, fixed, col, agg):
    """Resolve min/max boundary from config."""
    if source == "fixed" and fixed is not None:
        return float(fixed)
    if source == "column" and col and col in df.columns:
        try:
            return float(_aggregate_series(df[col], agg))
        except Exception:
            pass
    return None


def _resolve_target(df, config, agg):
    """Resolve target value from config."""
    src = config.get("target_source")
    if src == "fixed":
        target_val = config.get("target_fixed")
        return float(target_val) if target_val is not None else None
    if src == "column":
        target_col = config.get("target_col")
        if target_col and target_col in df.columns:
            try:
                return float(_aggregate_series(df[target_col], config.get("target_agg", agg)))
            except Exception:
                pass
    return None


def _check_target_met(value, target, polarity, strict):
    """Check if value meets target based on polarity and comparison mode."""
    if target is None:
        return None
    
    if polarity == "higher":
        return value > target if strict else value >= target
    else:
        return value < target if strict else value <= target


def _pick_bar_color(meets_target, palette):
    """Pick the bar color based on whether target is met."""
    if meets_target is None:
        return palette["neutral"]
    return palette["good"] if meets_target else palette["bad"]


def _build_steps(min_val, max_val, target, polarity, palette):
    """Build color steps for gauge background using target as threshold."""
    if target is None:
        return []
    
    step_colors = palette["step_colors"]
    range_span = max_val - min_val
    
    if range_span <= 0:
        return []
    
    min_step_size = range_span * 0.05
    eps = max(range_span * 1e-6, 1e-12)
    
    safe_target = max(min_val + eps, min(target, max_val - eps))
    
    if abs(safe_target - min_val) < min_step_size:
        mid_point = min_val + (range_span * 0.3)
    elif abs(max_val - safe_target) < min_step_size:
        mid_point = max_val - (range_span * 0.3)
    else:
        mid_point = safe_target
    
    if polarity == "higher":
        return [
            {"range": [min_val, mid_point], "color": step_colors["bad"]},
            {"range": [mid_point, max_val], "color": step_colors["good"]},
        ]
    else:
        return [
            {"range": [min_val, mid_point], "color": step_colors["good"]},
            {"range": [mid_point, max_val], "color": step_colors["bad"]},
        ]


def _format_number_human(num: float) -> str:
    """Format large numbers with K/M/B suffixes."""
    if abs(num) >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B"
    elif abs(num) >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif abs(num) >= 1_000:
        return f"{num / 1_000:.1f}K"
    else:
        return f"{num:.1f}"


def plot_custom_visualization(df, config):
    """Execute custom Python code to create visualization."""
    code = config.get('code', '').strip()
    
    if not code:
        return create_plotly_error_visualization("No code provided")
    
    # Clean code indentation
    import textwrap
    try:
        code = textwrap.dedent(code).strip()
    except:
        pass
    
    # Create execution environment
    env = {
        'df': df.copy(),
        'px': px,
        'go': go,
        'np': np,
        'pd': pd,
        'st': st
    }
    
    try:
        # Execute code
        exec(code, env)
        
        # Find the figure
        fig = None
        for name in ['fig', 'figure', 'FIG', 'chart']:
            if name in env and env[name] is not None:
                fig = env[name]
                break
        
        if fig is None:
            return create_plotly_error_visualization(
                "No 'fig' variable created\n\n"
                "Your code must create a Plotly figure:\n"
                "fig = px.scatter(df, ...)"
            )
        
        # Apply unified styling to custom charts too
        fig = apply_unified_styling(fig, config, 'default')
        
        return fig
        
    except IndentationError:
        return create_plotly_error_visualization(
            "Indentation error\n\n"
            "Check that all lines use consistent spacing (4 spaces recommended)"
        )
        
    except SyntaxError as e:
        return create_plotly_error_visualization(
            f"Syntax error: {str(e)[:100]}"
        )
        
    except Exception as e:
        return create_plotly_error_visualization(
            f"Error: {str(e)[:150]}"
        )        


# ============================================================================
# EXPORT FUNCTIONS
# ============================================================================

__all__ = [
    'plot_plotly_histogram',
    'plot_plotly_bar_chart',
    'plot_plotly_line_chart',
    'plot_plotly_scatter',
    'plot_plotly_pie_chart',
    'plot_plotly_box_plot',
    'plot_plotly_heatmap',
    'plot_plotly_violin_plot',
    'plot_plotly_correlation_matrix',
    'plot_plotly_bubble_chart',
    'create_plotly_error_visualization',
    'validate_columns',
    'safe_numeric_conversion',
    'plot_plotly_treemap',
    'plot_plotly_bubble_map',
    'create_bubble_map_from_dataframe',
    'plot_kpi',
    'plot_card',
    'plot_gauge',
    'apply_unified_styling',
    '_get_color_sequence',  # Added for bar_line_charts integration
    'plot_custom_visualization',
]