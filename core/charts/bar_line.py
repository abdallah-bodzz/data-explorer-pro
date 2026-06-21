"""
Production-Ready Bar and Line Chart Module - Enhanced with Area Charts, Flexible X-axis, and Multi-Y-axis Support
"""

from typing import List, Optional, Literal, Dict, Any, Tuple, Union
from dataclasses import dataclass, field
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from enum import Enum
import logging
import numpy as np
from plotly.subplots import make_subplots

logger = logging.getLogger(__name__)

# ============================================================================
# 1. TYPED CONFIGURATION - ENHANCED
# ============================================================================

class AggFunc(str, Enum):
    """Supported aggregation functions"""
    SUM = 'sum'
    MEAN = 'mean'
    MEDIAN = 'median'
    COUNT = 'count'
    MIN = 'min'
    MAX = 'max'


class BarMode(str, Enum):
    """Bar chart display modes"""
    GROUP = 'group'
    STACK = 'stack'
    OVERLAY = 'overlay'


class ErrorFunc(str, Enum):
    """Supported error bar functions"""
    STD = 'std'
    SEM = 'sem'
    NONE = 'none'


class XAxisType(str, Enum):
    """X-axis data type handling"""
    AUTO = 'auto'
    DATETIME = 'datetime'
    LINEAR = 'linear'
    CATEGORY = 'category'
    LOG = 'log'


class FillMode(str, Enum):
    """Fill modes for area charts"""
    NONE = 'none'
    TOZEROY = 'tozeroy'
    TONEXTY = 'tonexty'
    TOSELF = 'toself'
    TONEXT = 'tonext'


@dataclass
class BarChartConfig:
    """Type-safe configuration for bar charts"""
    x_col: str
    y_cols: List[str] = None
    color_col: Optional[str] = None
    agg_func: AggFunc = AggFunc.SUM
    orientation: Literal['v', 'h'] = 'v'
    barmode: BarMode = BarMode.GROUP
    show_values: bool = False
    value_position: Literal['outside', 'inside', 'auto'] = 'outside'
    sort_bars: bool = True
    sort_descending: bool = True
    sort_by: Optional[str] = None
    category_limit: Optional[int] = None
    show_error_bars: bool = False
    error_func: ErrorFunc = ErrorFunc.STD
    title: Optional[str] = None
    value_format: str = '.2f'
    hover_data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate configuration on initialization"""
        self.y_cols = self.y_cols or []
        
        if self.agg_func == AggFunc.COUNT and self.y_cols:
            raise ValueError("Cannot specify y_cols with 'count' aggregation")
        
        if self.sort_by and self.sort_by not in self.y_cols and self.sort_by != 'count':
            raise ValueError(f"sort_by '{self.sort_by}' must be in y_cols or 'count'")


@dataclass(frozen=True)
class LineChartConfig:
    """Enhanced line chart configuration with flexible x-axis and area chart support"""
    x_col: str  # Changed from date_col to be more general
    value_cols: List[str]
    group_col: Optional[str] = None
    time_agg: str = 'raw'  # For backward compatibility
    agg_func: str = 'mean'
    show_markers: bool = True
    connect_gaps: bool = False
    dual_yaxis: bool = False
    line_style: str = 'solid'
    max_series: int = 20
    title: Optional[str] = None
    fill: FillMode = FillMode.NONE  # Area chart support
    x_axis_type: XAxisType = XAxisType.AUTO  # Flexible x-axis
    yaxis_assignments: Optional[List[str]] = None  # Custom y-axis assignments
    line_width: int = 2
    opacity: float = 0.8
    
    def __post_init__(self):
        """Validate with flexible x-axis and enhanced dual y-axis"""
        if not self.x_col:
            raise ValueError("x_col is required")
        if not self.value_cols:
            raise ValueError("value_cols cannot be empty")
        if len(self.value_cols) > 20:
            raise ValueError(f"Too many metrics: {len(self.value_cols)} (max 20)")
        
        # Enhanced dual y-axis: allow more than 2 metrics
        if self.dual_yaxis and self.group_col:
            raise ValueError("dual_yaxis not supported with grouping")
        
        if self.agg_func not in ['mean', 'sum', 'median', 'min', 'max', 'count']:
            raise ValueError(f"Invalid agg_func: {self.agg_func}")
        
        # Keep time_agg validation for backward compatibility
        if self.time_agg not in ['raw', 'D', 'W', 'M', 'Q', 'Y', 'daily', 'weekly', 'monthly', 'quarterly', 'yearly']:
            raise ValueError(f"Invalid time_agg: {self.time_agg}")
        
        # Validate yaxis_assignments if provided
        if self.yaxis_assignments:
            if len(self.yaxis_assignments) != len(self.value_cols):
                raise ValueError(f"yaxis_assignments must have same length as value_cols ({len(self.value_cols)})")
            valid_axes = {'y', 'y2', 'y3'}
            for axis in self.yaxis_assignments:
                if axis not in valid_axes:
                    raise ValueError(f"Invalid yaxis: {axis}. Must be one of {valid_axes}")


@dataclass
class PreparedBarData:
    """Container for processed bar chart data"""
    df: pd.DataFrame
    x_col: str
    y_col: str
    color_col: Optional[str]
    error_col: Optional[str] = None
    is_multi_metric: bool = False
    preserved_hover_cols: List[str] = None


# ============================================================================
# 2. DATA PREPARATION (Bar Charts) - UNCHANGED
# ============================================================================

def validate_columns(df: pd.DataFrame, columns: List[str]) -> Tuple[bool, str]:
    """Validate that columns exist in dataframe"""
    missing = [col for col in columns if col is not None and col not in df.columns]
    if missing:
        return False, f"Missing columns: {', '.join(missing)}"
    return True, ""


def limit_categories(df: pd.DataFrame, x_col: str, limit: Optional[int]) -> pd.DataFrame:
    """Keep only top N categories by frequency"""
    if not limit or limit <= 0:
        return df
    
    top_categories = df[x_col].value_counts().head(limit).index
    return df[df[x_col].isin(top_categories)].copy()


def _calculate_errors(df: pd.DataFrame, group_cols: List[str], y_col: str, error_func: ErrorFunc) -> Tuple[pd.DataFrame, str]:
    """Calculate error bars based on specified function"""
    if error_func == ErrorFunc.STD:
        error_df = df.groupby(group_cols)[y_col].std().reset_index()
        error_col = 'std'
    elif error_func == ErrorFunc.SEM:
        grouped = df.groupby(group_cols)[y_col]
        error_df = (grouped.std() / grouped.count().sqrt()).reset_index()
        error_col = 'sem'
    else:
        return None, None
    
    error_df.columns = group_cols + [error_col]
    return error_df, error_col


def prepare_frequency_data(df: pd.DataFrame, config: BarChartConfig) -> PreparedBarData:
    """Prepare data for frequency/count bar chart"""
    if config.color_col:
        group_cols = [config.x_col, config.color_col]
        agg_df = df.groupby(group_cols).size().reset_index(name='count')
        preserved_hover_cols = []
        if config.hover_data:
            preserved_hover_cols = [col for col in config.hover_data.keys() if col in group_cols]
    else:
        agg_df = df[config.x_col].value_counts().reset_index()
        agg_df.columns = [config.x_col, 'count']
        preserved_hover_cols = [config.x_col] if config.hover_data and config.x_col in config.hover_data else []
    
    if config.sort_bars:
        sort_col = config.sort_by if config.sort_by else 'count'
        agg_df = agg_df.sort_values(sort_col, ascending=not config.sort_descending)
    
    return PreparedBarData(
        df=agg_df,
        x_col=config.x_col,
        y_col='count',
        color_col=config.color_col,
        preserved_hover_cols=preserved_hover_cols
    )


def prepare_single_metric_data(df: pd.DataFrame, config: BarChartConfig) -> PreparedBarData:
    """Prepare data for single metric aggregation"""
    y_col = config.y_cols[0]
    group_cols = [config.x_col]
    if config.color_col and config.color_col != config.x_col:
        group_cols.append(config.color_col)
    
    preserved_hover_cols = []
    if config.hover_data:
        preserved_hover_cols = [col for col in config.hover_data.keys() if col in group_cols]
    
    if config.agg_func == AggFunc.COUNT:
        agg_df = df.groupby(group_cols).size().reset_index(name='count')
        y_col = 'count'
    else:
        agg_df = df.groupby(group_cols)[y_col].agg(config.agg_func.value).reset_index()
        
        if config.show_error_bars:
            error_df, error_col = _calculate_errors(df, group_cols, y_col, config.error_func)
            if error_df is not None:
                agg_df = agg_df.merge(error_df, on=group_cols)
            else:
                agg_df[error_col] = None
    
    if config.sort_bars and not config.color_col:
        sort_col = config.sort_by if config.sort_by else y_col
        agg_df = agg_df.sort_values(sort_col, ascending=not config.sort_descending)
    
    return PreparedBarData(
        df=agg_df,
        x_col=config.x_col,
        y_col=y_col,
        color_col=config.color_col,
        error_col=error_col if config.show_error_bars else None,
        preserved_hover_cols=preserved_hover_cols
    )


def prepare_multi_metric_data(df: pd.DataFrame, config: BarChartConfig) -> PreparedBarData:
    """Prepare data for multi-metric comparison"""
    group_cols = [config.x_col]
    if config.color_col and config.color_col != config.x_col:
        group_cols.append(config.color_col)
    
    preserved_hover_cols = []
    if config.hover_data:
        preserved_hover_cols = [col for col in config.hover_data.keys() if col in group_cols]
    
    dtype_map = {col: df[col].dtype for col in config.y_cols}
    agg_dict = {y: config.agg_func.value for y in config.y_cols}
    agg_df = df.groupby(group_cols).agg(agg_dict).reset_index()
    
    melted_df = agg_df.melt(
        id_vars=group_cols,
        value_vars=config.y_cols,
        var_name='metric',
        value_name='value'
    )
    
    for col in config.y_cols:
        mask = melted_df['metric'] == col
        if mask.any():
            try:
                melted_df.loc[mask, 'value'] = melted_df.loc[mask, 'value'].astype(dtype_map[col])
            except (ValueError, TypeError):
                pass
    
    if config.color_col:
        final_color_col = 'metric'
        melted_df['x_color_combo'] = melted_df[config.x_col].astype(str) + ' - ' + melted_df[config.color_col].astype(str)
        final_x_col = 'x_color_combo'
    else:
        final_color_col = 'metric'
        final_x_col = config.x_col
    
    if config.sort_bars and not config.color_col:
        if config.sort_by:
            sort_col = config.sort_by
        else:
            sort_col = config.y_cols[0]
        
        sort_df = agg_df[[config.x_col, sort_col]].sort_values(
            sort_col,
            ascending=not config.sort_descending
        )
        category_order = sort_df[config.x_col].tolist()
        melted_df[final_x_col] = pd.Categorical(
            melted_df[final_x_col],
            categories=category_order,
            ordered=True
        )
        melted_df = melted_df.sort_values(final_x_col)
    
    return PreparedBarData(
        df=melted_df,
        x_col=final_x_col,
        y_col='value',
        color_col=final_color_col,
        preserved_hover_cols=preserved_hover_cols,
        is_multi_metric=True
    )


def prepare_data(df: pd.DataFrame, config: BarChartConfig) -> PreparedBarData:
    """Main data preparation dispatcher"""
    processed_df = limit_categories(df, config.x_col, config.category_limit)
    
    if not config.y_cols:
        return prepare_frequency_data(processed_df, config)
    elif len(config.y_cols) == 1:
        return prepare_single_metric_data(processed_df, config)
    else:
        return prepare_multi_metric_data(processed_df, config)


# ============================================================================
# 3. BAR CHART VISUALIZATION - UNCHANGED
# ============================================================================

def _build_hovertemplate(config: BarChartConfig, data: PreparedBarData, hover_cols: List[str]) -> str:
    """DRY method for building hovertemplate"""
    hovertemplate_parts = []
    
    if config.orientation == 'v':
        hovertemplate_parts.extend([
            f"{data.y_col}: %{{y:{config.value_format}}}"
        ])
    else:
        hovertemplate_parts.extend([
            f"{data.y_col}: %{{x:{config.value_format}}}"
        ])
    
    for i, col in enumerate(hover_cols):
        hovertemplate_parts.append(f"{col}: %{{customdata[{i}]}}")
    
    hovertemplate_parts.append("<extra></extra>")
    return "<br>".join(hovertemplate_parts)


def _get_text_position(config: BarChartConfig) -> str:
    """Smart text positioning with overflow prevention"""
    if config.value_position != 'auto':
        return config.value_position
    
    return 'inside' if config.orientation == 'h' else 'outside'


def create_simple_bar_chart(data: PreparedBarData, config: BarChartConfig) -> go.Figure:
    """Use plotly.express for simple cases"""
    bar_args = {
        'data_frame': data.df,
        'x': data.x_col if config.orientation == 'v' else data.y_col,
        'y': data.y_col if config.orientation == 'v' else data.x_col,
        'color': data.color_col,
        'orientation': config.orientation,
        'barmode': config.barmode.value,
    }
    
    fig = px.bar(**bar_args)
    
    if config.show_values:
        text_col = data.y_col if config.orientation == 'v' else data.x_col
        fig.update_traces(
            texttemplate=f'%{{text:{config.value_format}}}',
            textposition=_get_text_position(config),
            text=data.df[text_col]
        )
    
    return fig


def create_advanced_bar_chart(data: PreparedBarData, config: BarChartConfig) -> go.Figure:
    """Use graph_objects for advanced features"""
    fig = go.Figure()
    category_col = data.x_col
    value_col = data.y_col
    available_hover_cols = data.preserved_hover_cols or []
    allow_error_bars = data.error_col and not data.is_multi_metric
    
    if data.color_col:
        groups = data.df[data.color_col].dropna().unique()
        for group in groups:
            group_df = data.df[data.df[data.color_col] == group].copy()
            
            if config.orientation == 'v':
                x_vals = group_df[category_col]
                y_vals = group_df[value_col]
            else:
                x_vals = group_df[value_col]
                y_vals = group_df[category_col]

            trace_kwargs = {
                'name': str(group),
                'x': x_vals,
                'y': y_vals,
                'orientation': config.orientation,
            }
            
            if available_hover_cols:
                trace_kwargs['customdata'] = group_df[available_hover_cols].values
                trace_kwargs['hovertemplate'] = _build_hovertemplate(
                    config, data, available_hover_cols
                )
            
            if allow_error_bars:
                error_values = group_df[data.error_col].fillna(0)
                if config.orientation == 'v':
                    trace_kwargs['error_y'] = dict(type='data', array=error_values, visible=True)
                else:
                    trace_kwargs['error_x'] = dict(type='data', array=error_values, visible=True)
            
            if config.show_values:
                display_vals = y_vals if config.orientation == 'v' else x_vals
                trace_kwargs['text'] = [f'{v:{config.value_format}}' for v in display_vals]
                trace_kwargs['textposition'] = _get_text_position(config)
            
            fig.add_trace(go.Bar(**trace_kwargs))
    else:
        if config.orientation == 'v':
            x_vals = data.df[category_col]
            y_vals = data.df[value_col]
        else:
            x_vals = data.df[value_col]
            y_vals = data.df[category_col]

        trace_kwargs = {
            'x': x_vals,
            'y': y_vals,
            'orientation': config.orientation,
        }
        
        if available_hover_cols:
            trace_kwargs['customdata'] = data.df[available_hover_cols].values
            trace_kwargs['hovertemplate'] = _build_hovertemplate(
                config, data, available_hover_cols
            )
        
        if allow_error_bars:
            error_values = data.df[data.error_col].fillna(0)
            if config.orientation == 'v':
                trace_kwargs['error_y'] = dict(type='data', array=error_values, visible=True)
            else:
                trace_kwargs['error_x'] = dict(type='data', array=error_values, visible=True)
        
        if config.show_values:
            display_vals = y_vals if config.orientation == 'v' else x_vals
            trace_kwargs['text'] = [f'{v:{config.value_format}}' for v in display_vals]
            trace_kwargs['textposition'] = _get_text_position(config)
        
        fig.add_trace(go.Bar(**trace_kwargs))
    
    fig.update_layout(barmode=config.barmode.value)
    return fig


def create_base_figure(data: PreparedBarData, config: BarChartConfig) -> go.Figure:
    """Hybrid approach: Use px for simple cases, go for advanced features"""
    use_simple = (
        not config.show_error_bars and 
        not config.hover_data and
        not config.show_values
    )
    
    if use_simple:
        return create_simple_bar_chart(data, config)
    else:
        return create_advanced_bar_chart(data, config)


def apply_styling(fig: go.Figure, data: PreparedBarData, config: BarChartConfig) -> go.Figure:
    """Apply styling and layout to figure"""
    if config.title:
        title = config.title
    elif not config.y_cols:
        title = f"Count of {config.x_col}"
    elif len(config.y_cols) == 1:
        title = f"{config.agg_func.value.title()} of {config.y_cols[0]} by {config.x_col}"
    else:
        title = f"Multiple Metrics by {config.x_col}"
    
    if config.show_error_bars:
        title += f" (± {config.error_func.value})"
    
    fig.update_layout(
        title_text=title,
        xaxis_title=data.x_col if config.orientation == 'v' else data.y_col,
        yaxis_title=data.y_col if config.orientation == 'v' else data.x_col,
        template='plotly_white',
        hovermode='x unified' if config.orientation == 'v' else 'y unified'
    )
    
    return fig


# ============================================================================
# 4. BAR CHART MAIN ENTRY POINT - UNCHANGED
# ============================================================================

def plot_bar_chart(df: pd.DataFrame, config: BarChartConfig) -> go.Figure:
    """
    Create a bar chart with comprehensive options.
    """
    try:
        cols_to_check = [config.x_col] + config.y_cols
        if config.color_col:
            cols_to_check.append(config.color_col)
        if config.hover_data:
            cols_to_check.extend(config.hover_data.keys())
        
        valid, error_msg = validate_columns(df, list(set(cols_to_check)))
        if not valid:
            return _create_error_figure(error_msg)
        
        prepared_data = prepare_data(df, config)
        fig = create_base_figure(prepared_data, config)
        fig = apply_styling(fig, prepared_data, config)
        
        return fig
        
    except Exception as e:
        logger.error(f"Bar chart error: {str(e)}", exc_info=True)
        return _create_error_figure(f"Bar chart error: {str(e)}")


def plot_plotly_bar_chart(df: pd.DataFrame, config_dict: Dict[str, Any]) -> go.Figure:
    """
    Legacy wrapper that accepts dict config for backward compatibility.
    """
    try:
        config_dict = config_dict.copy()
        
        if 'hover_data' in config_dict and isinstance(config_dict['hover_data'], list):
            hover_dict = {}
            for col in config_dict['hover_data']:
                if col in df.columns:
                    hover_dict[col] = True
            config_dict['hover_data'] = hover_dict
        
        bar_config = BarChartConfig(
            x_col=config_dict['x_col'],
            y_cols=config_dict.get('y_cols', []),
            color_col=config_dict.get('color_col'),
            agg_func=AggFunc(config_dict.get('agg_func', 'sum')),
            orientation=config_dict.get('orientation', 'v'),
            barmode=BarMode(config_dict.get('barmode', 'group')),
            show_values=config_dict.get('show_values', False),
            value_position=config_dict.get('value_position', 'outside'),
            sort_bars=config_dict.get('sort_bars', True),
            category_limit=config_dict.get('category_limit'),
            show_error_bars=config_dict.get('show_error_bars', False),
            error_func=ErrorFunc(config_dict.get('error_func', 'std')),
            title=config_dict.get('title'),
            value_format=config_dict.get('value_format', '.2f'),
            hover_data=config_dict.get('hover_data')
        )
        
        return plot_bar_chart(df, bar_config)
        
    except (ValueError, KeyError) as e:
        logger.error(f"Invalid bar chart configuration: {str(e)}")
        return _create_error_figure(f"Invalid configuration: {str(e)}")


# ============================================================================
# 5. ENHANCED LINE/AREA CHART FUNCTIONS
# ============================================================================

def _detect_x_axis_type(x_series: pd.Series, config_type: XAxisType) -> XAxisType:
    """Detect appropriate x-axis type from data"""
    if config_type != XAxisType.AUTO:
        return config_type
    
    # Auto-detection logic
    if pd.api.types.is_datetime64_any_dtype(x_series):
        return XAxisType.DATETIME
    elif pd.api.types.is_numeric_dtype(x_series):
        # Check if it looks like categorical integers
        unique_ratio = x_series.nunique() / len(x_series)
        if unique_ratio < 0.3 and x_series.nunique() < 20:
            return XAxisType.CATEGORY
        return XAxisType.LINEAR
    elif pd.api.types.is_categorical_dtype(x_series) or pd.api.types.is_object_dtype(x_series):
        return XAxisType.CATEGORY
    else:
        # Default to linear for unknown types
        return XAxisType.LINEAR


def _generate_smart_title(df: pd.DataFrame, config: LineChartConfig) -> str:
    """Generate title with x-axis handling"""
    if len(config.value_cols) == 1:
        metric_desc = f"{config.value_cols[0]}"
    else:
        metric_desc = f"{', '.join(config.value_cols[:-1])} & {config.value_cols[-1]}"
    
    if config.group_col:
        group_sample = df[config.group_col].dropna().unique()[:3]
        group_desc = f"by {config.group_col}"
        if len(group_sample) > 1:
            group_desc += f" ({', '.join(map(str, group_sample[:2]))}{'...' if len(group_sample) > 2 else ''})"
    else:
        group_desc = ""
    
    # Handle different x-axis types
    x_vals = df[config.x_col].dropna()
    if len(x_vals) == 0:
        x_desc = "(No valid x values)"
    else:
        if config.x_axis_type == XAxisType.DATETIME:
            try:
                date_min = pd.to_datetime(x_vals).min()
                date_max = pd.to_datetime(x_vals).max()
                x_desc = f"({date_min.strftime('%b %Y')} to {date_max.strftime('%b %Y')})"
            except:
                x_desc = f"by {config.x_col}"
        else:
            x_desc = f"by {config.x_col}"
    
    agg_desc = ""
    if config.time_agg != 'raw' and config.x_axis_type == XAxisType.DATETIME:
        agg_map = {
            'D': 'Daily', 'W': 'Weekly', 'M': 'Monthly',
            'Q': 'Quarterly', 'Y': 'Yearly',
            'daily': 'Daily', 'weekly': 'Weekly', 'monthly': 'Monthly',
            'quarterly': 'Quarterly', 'yearly': 'Yearly'
        }
        agg_desc = f" - {agg_map.get(config.time_agg, config.time_agg)}"
    
    title_parts = [metric_desc]
    if group_desc:
        title_parts.append(group_desc)
    title_parts.append(x_desc)
    
    main_title = " | ".join(title_parts)
    subtitle = f"{agg_desc}".strip()
    
    if subtitle:
        return f"<b>{main_title}</b><br><sub>{subtitle}</sub>"
    else:
        return f"<b>{main_title}</b>"


def _smart_legend_position(series_count: int) -> tuple[float, float, str]:
    """Smart legend positioning based on series count"""
    if series_count <= 4:
        return 1.02, 1, 'v'
    elif series_count <= 8:
        return 0, 1, 'v'
    elif series_count <= 12:
        return 1.02, 0.5, 'v'
    else:
        return 0.5, -0.1, 'h'


def _smart_y_title(col_name: str) -> str:
    """Auto-detect units/context for Y-axis"""
    col_lower = col_name.lower()
    if any(unit in col_lower for unit in ['$', 'usd', 'revenue', 'sales', 'price', 'cost']):
        return f"{col_name}<br>(USD)"
    elif any(unit in col_lower for unit in ['%', 'rate', 'ratio', 'percentage']):
        return f"{col_name}<br>(%)"
    elif any(unit in col_lower for unit in ['count', 'number', 'quantity', 'units']):
        return f"{col_name}<br>(Count)"
    elif any(unit in col_lower for unit in ['time', 'duration', 'hours', 'minutes']):
        return f"{col_name}<br>(Time)"
    else:
        return f"<b>{col_name}</b>"


def _smart_date_format(time_agg: str) -> str:
    """Smart date format for hover"""
    if time_agg in ['M', 'Q', 'Y', 'monthly', 'quarterly', 'yearly']:
        return '%Y-%m'
    else:
        return '%Y-%m-%d'


def _validate_columns(df: pd.DataFrame, config: LineChartConfig) -> None:
    """Check required columns exist"""
    required = [config.x_col] + config.value_cols
    if config.group_col:
        required.append(config.group_col)
    
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise KeyError(f"Columns not found: {', '.join(missing)}")


def _prepare_data(df: pd.DataFrame, config: LineChartConfig) -> tuple[pd.DataFrame, List[Dict[str, Any]], int, List[str]]:
    """
    Enhanced data preparation for flexible x-axis types
    """
    warnings = []
    
    cols = [config.x_col] + config.value_cols
    if config.group_col:
        cols.append(config.group_col)
    
    work_df = df[cols].copy()
    original_len = len(work_df)
    
    # Detect and handle x-axis type
    x_axis_type = _detect_x_axis_type(work_df[config.x_col], config.x_axis_type)
    
    if x_axis_type == XAxisType.DATETIME:
        work_df[config.x_col] = pd.to_datetime(work_df[config.x_col], errors='coerce')
        null_dates = work_df[config.x_col].isna().sum()
        
        if null_dates > 0:
            work_df = work_df.dropna(subset=[config.x_col])
            pct = (null_dates / original_len) * 100
            warnings.append(f"{null_dates} invalid dates removed ({pct:.1f}%)")
        
        # Apply time aggregation only for datetime
        if config.time_agg != 'raw':
            work_df = _aggregate_time(work_df, config, warnings)
    elif x_axis_type == XAxisType.CATEGORY:
        # Ensure categorical type for better performance
        work_df[config.x_col] = work_df[config.x_col].astype(str)
    elif x_axis_type == XAxisType.LINEAR:
        # Ensure numeric type
        work_df[config.x_col] = pd.to_numeric(work_df[config.x_col], errors='coerce')
    
    if len(work_df) == 0:
        raise ValueError("No valid data points found")
    
    work_df = work_df.sort_values(config.x_col)
    
    trace_specs = _compute_trace_specs(work_df, config, warnings, x_axis_type)
    series_count = len(trace_specs)
    
    return work_df, trace_specs, series_count, warnings


def _aggregate_time(df: pd.DataFrame, config: LineChartConfig, warnings: List[str]) -> pd.DataFrame:
    """Time aggregation using pandas resample"""
    freq_map = {
        'daily': 'D', 'weekly': 'W', 'monthly': 'M',
        'quarterly': 'Q', 'yearly': 'Y'
    }
    freq = freq_map.get(config.time_agg, config.time_agg)
    
    agg_dict = {col: config.agg_func for col in config.value_cols}
    
    if config.group_col:
        agg_df = (df.set_index(config.x_col)
                   .groupby(config.group_col, observed=True)
                   .resample(freq)
                   .agg(agg_dict)
                   .reset_index())
    else:
        agg_df = (df.set_index(config.x_col)
                   .resample(freq)
                   .agg(agg_dict)
                   .reset_index())
    
    if len(agg_df) == 0:
        raise ValueError(f"Aggregation ({freq}) produced no data")
    
    warnings.append(f"Aggregated {len(df):,} → {len(agg_df):,} points ({freq})")
    return agg_df


def _compute_trace_specs(df: pd.DataFrame, config: LineChartConfig, warnings: List[str], x_axis_type: XAxisType) -> List[Dict[str, Any]]:
    """Pre-compute data subsets for each trace with y-axis assignment"""
    specs = []
    
    # Determine y-axis assignments for dual y-axis mode
    yaxis_assignments = config.yaxis_assignments or []
    if config.dual_yaxis and not yaxis_assignments:
        # Smart assignment: alternate between y and y2
        yaxis_assignments = ['y' if i % 2 == 0 else 'y2' for i in range(len(config.value_cols))]
    
    if config.group_col:
        groups = df.groupby(config.group_col, observed=True)
        for col_idx, col in enumerate(config.value_cols):
            for group_name, group_df in groups:
                trace_data = group_df[[config.x_col, col]].dropna()
                valid_count = len(trace_data)
                
                if valid_count < 2:
                    warnings.append(f"'{col} - {group_name}' has only {valid_count} point(s), skipped")
                    continue
                
                # Determine yaxis
                yaxis = yaxis_assignments[col_idx] if yaxis_assignments else 'y'
                
                specs.append({
                    'name': f"{col} - {group_name}",
                    'metric': col,
                    'group': group_name,
                    'data': trace_data,
                    'point_count': valid_count,
                    'yaxis': yaxis
                })
    else:
        for idx, col in enumerate(config.value_cols):
            trace_data = df[[config.x_col, col]].dropna()
            valid_count = len(trace_data)
            
            if valid_count < 2:
                warnings.append(f"'{col}' has only {valid_count} point(s), skipped")
                continue
            
            # Determine yaxis for dual y-axis
            if config.dual_yaxis:
                yaxis = yaxis_assignments[idx] if idx < len(yaxis_assignments) else 'y'
            else:
                yaxis = 'y'
            
            specs.append({
                'name': col,
                'metric': col,
                'group': None,
                'data': trace_data,
                'point_count': valid_count,
                'yaxis': yaxis
            })
    
    return specs


def _render_chart(df: pd.DataFrame, trace_specs: List[Dict[str, Any]], config: LineChartConfig, x_axis_type: XAxisType) -> go.Figure:
    """Render chart with pre-computed data and area chart support"""
    # Create figure with subplots for dual y-axis
    if config.dual_yaxis:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
    else:
        fig = go.Figure()
    
    points_total = sum(spec['point_count'] for spec in trace_specs)
    use_markers = config.show_markers and points_total < 500
    mode = 'lines+markers' if use_markers else 'lines'
    
    dash_map = {'solid': 'solid', 'dash': 'dash', 'dot': 'dot', 'dashdot': 'dashdot'}
    dash = dash_map.get(config.line_style, 'solid')
    
    # Determine hover format based on x-axis type
    if x_axis_type == XAxisType.DATETIME:
        date_format = _smart_date_format(config.time_agg)
        x_hover_template = f"X: %{{x|{date_format}}}<br>"
    else:
        x_hover_template = "X: %{x}<br>"
    
    # Track y-axes for formatting
    y_axes_used = set()
    
    for i, spec in enumerate(trace_specs):
        trace_data = spec['data']
        yaxis = spec['yaxis']
        is_secondary = yaxis.startswith('y') and yaxis != 'y'
        
        # Area chart fill configuration
        fill = None
        fillcolor = None
        if config.fill != FillMode.NONE:
            fill = config.fill.value
            # Use semi-transparent color based on trace index
            colors = px.colors.qualitative.Plotly
            fillcolor = colors[i % len(colors)].replace('rgb', 'rgba').replace(')', f', {config.opacity})')
        
        if config.dual_yaxis and is_secondary:
            fig.add_trace(
                go.Scatter(
                    x=trace_data[config.x_col],
                    y=trace_data[spec['metric']],
                    mode=mode,
                    name=spec['name'],
                    line=dict(dash=dash, width=config.line_width),
                    connectgaps=config.connect_gaps,
                    fill=fill,
                    fillcolor=fillcolor,
                    hovertemplate=(
                        f"<b>{spec['name']}</b><br>"
                        f"{x_hover_template}"
                        "Value: %{y:,.2f}<extra></extra>"
                    )
                ),
                secondary_y=True
            )
        else:
            fig.add_trace(
                go.Scatter(
                    x=trace_data[config.x_col],
                    y=trace_data[spec['metric']],
                    mode=mode,
                    name=spec['name'],
                    line=dict(dash=dash, width=config.line_width),
                    connectgaps=config.connect_gaps,
                    fill=fill,
                    fillcolor=fillcolor,
                    hovertemplate=(
                        f"<b>{spec['name']}</b><br>"
                        f"{x_hover_template}"
                        "Value: %{y:,.2f}<extra></extra>"
                    )
                )
            )
        
        y_axes_used.add(yaxis)
    
    return fig


def _finalize_layout(fig: go.Figure, config: LineChartConfig, series_count: int, df: pd.DataFrame, x_axis_type: XAxisType) -> None:
    """Apply production-ready layout with flexible x-axis"""
    smart_title = config.title or _generate_smart_title(df, config)
    legend_x, legend_y, legend_orientation = _smart_legend_position(series_count)
    
    # Base layout
    layout = dict(
        title=dict(
            text=smart_title,
            x=0.5,
            xanchor='center',
            font=dict(size=18, color='#2c3e50'),
            pad=dict(t=20)
        ),
        hovermode='x unified',
        uirevision='constant',
        template='plotly_white',  # Consistent styling
        font=dict(family='Arial, sans-serif', size=12, color='#2c3e50'),
        legend=dict(
            orientation=legend_orientation,
            x=legend_x,
            y=legend_y,
            xanchor='left' if legend_orientation == 'v' else 'center',
            yanchor='top' if legend_orientation == 'v' else 'bottom',
            borderwidth=1,
            font=dict(color='#2c3e50'),
            itemwidth=40,
            groupclick='toggleitem',
            tracegroupgap=8
        ),
        margin=dict(
            l=80,
            r=120 if legend_orientation == 'v' else 40,
            t=100,
            b=80 if legend_orientation == 'h' else 60
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=650
    )
    
    # Configure x-axis based on type
    xaxis_config = dict(
        title=f"<b>{config.x_col}</b>",
        showgrid=True,
        gridcolor='#bdc3c7',
        gridwidth=1,
        zeroline=False
    )
    
    if x_axis_type == XAxisType.DATETIME:
        xaxis_config.update({
            'type': 'date',
            'rangeselector': dict(
                buttons=[
                    dict(count=1, label='1d', step='day', stepmode='backward'),
                    dict(count=7, label='1w', step='day', stepmode='backward'),
                    dict(count=1, label='1m', step='month', stepmode='backward'),
                    dict(count=3, label='3m', step='month', stepmode='backward'),
                    dict(count=6, label='6m', step='month', stepmode='backward'),
                    dict(count=1, label='YTD', step='year', stepmode='todate'),
                    dict(count=1, label='1y', step='year', stepmode='backward'),
                    dict(step='all', label='All')
                ],
                bgcolor='rgba(255,255,255,0.9)',
                activecolor='#1f77b4',
                x=0.01,
                y=1.1,
                xanchor='left',
                yanchor='bottom'
            ),
            'rangeslider': dict(
                visible=True,
                thickness=0.05,
                bgcolor='rgba(0,0,0,0.05)'
            )
        })
    elif x_axis_type == XAxisType.CATEGORY:
        xaxis_config['type'] = 'category'
        xaxis_config['tickangle'] = -45 if len(df[config.x_col].unique()) > 10 else 0
    elif x_axis_type == XAxisType.LOG:
        xaxis_config['type'] = 'log'
    else:  # LINEAR or default
        xaxis_config['type'] = 'linear'
    
    layout['xaxis'] = xaxis_config
    
    # Configure y-axes
    if config.dual_yaxis:
        # Get unique y-axes from traces
        y_axes = set()
        for trace in fig.data:
            if hasattr(trace, 'yaxis'):
                y_axes.add(trace.yaxis)
        
        y_axes = sorted(list(y_axes))
        
        # Configure primary y-axis
        if len(config.value_cols) == 1:
            primary_title = _smart_y_title(config.value_cols[0])
        else:
            primary_title = "Primary Values"
        
        layout['yaxis'] = dict(
            title=primary_title,
            showgrid=True,
            gridcolor='#bdc3c7',
            gridwidth=1,
            zeroline=False,
            side='left'
        )
        
        # Configure secondary y-axis if used
        if len(y_axes) > 1 or 'y2' in [trace.yaxis for trace in fig.data if hasattr(trace, 'yaxis')]:
            layout['yaxis2'] = dict(
                title="Secondary Values",
                overlaying='y',
                side='right',
                showgrid=False,
                gridcolor='#bdc3c7',
                zeroline=False
            )
    else:
        # Single y-axis
        if len(config.value_cols) == 1:
            y_title = _smart_y_title(config.value_cols[0])
        else:
            y_title = "Values"
        
        layout['yaxis'] = dict(
            title=y_title,
            showgrid=True,
            gridcolor='#bdc3c7',
            gridwidth=1,
            zeroline=False
        )
    
    fig.update_layout(**layout)


def _add_warnings(fig: go.Figure, warnings: List[str]) -> None:
    """Add warnings as subtle bottom annotation"""
    if not warnings:
        return
    
    display_warnings = warnings[:3]
    if len(warnings) > 3:
        display_warnings.append(f"...and {len(warnings) - 3} more")
    
    text = "ℹ️ " + " • ".join(display_warnings)
    
    fig.add_annotation(
        text=text,
        xref="paper", yref="paper",
        x=0.5, y=-0.18,
        showarrow=False,
        font=dict(size=9, color="#666"),
        align="center",
        xanchor='center'
    )
    
    fig.update_layout(margin=dict(b=fig.layout.margin.b + 40))


def _build_chart(df: pd.DataFrame, config: LineChartConfig) -> tuple[go.Figure, List[str]]:
    """Main orchestration - validate → prepare → render"""
    _validate_columns(df, config)
    plot_df, trace_specs, series_count, warnings = _prepare_data(df, config)
    
    if series_count > config.max_series:
        raise ValueError(
            f"Too many series ({series_count} > {config.max_series}). "
            f"Filter data or reduce metrics/groups before plotting."
        )
    
    # Detect x-axis type for final layout
    x_axis_type = _detect_x_axis_type(plot_df[config.x_col], config.x_axis_type)
    
    fig = _render_chart(plot_df, trace_specs, config, x_axis_type)
    _finalize_layout(fig, config, series_count, plot_df, x_axis_type)
    
    return fig, warnings


# ============================================================================
# 6. LINE/AREA CHART MAIN ENTRY POINT
# ============================================================================

def plot_plotly_line_chart(df: pd.DataFrame, config_dict: Dict[str, Any]) -> go.Figure:
    """
    Enhanced line/area chart with flexible x-axis and dual y-axis support.
    """
    try:
        # Process config with enhanced options
        processed_config = config_dict.copy()
        
        # Handle backward compatibility: date_col -> x_col
        if 'date_col' in processed_config and 'x_col' not in processed_config:
            processed_config['x_col'] = processed_config.pop('date_col')
        
        # Set default fill for area charts
        if processed_config.get('chart_type') == 'area' and 'fill' not in processed_config:
            processed_config['fill'] = 'tozeroy'
        
        # Handle fill mode conversion
        if 'fill' in processed_config:
            if isinstance(processed_config['fill'], str):
                try:
                    processed_config['fill'] = FillMode(processed_config['fill'])
                except ValueError:
                    processed_config['fill'] = FillMode.TOZEROY
        
        # Handle x_axis_type conversion
        if 'x_axis_type' in processed_config:
            if isinstance(processed_config['x_axis_type'], str):
                try:
                    processed_config['x_axis_type'] = XAxisType(processed_config['x_axis_type'])
                except ValueError:
                    processed_config['x_axis_type'] = XAxisType.AUTO
        
        # Filter config to valid fields
        config_fields = LineChartConfig.__dataclass_fields__.keys()
        filtered_config = {k: v for k, v in processed_config.items() if k in config_fields}
        
        config = LineChartConfig(**filtered_config)
        
        fig, warnings = _build_chart(df, config)
        
        if warnings:
            _add_warnings(fig, warnings)
        
        return fig
        
    except ValueError as e:
        logger.error(f"Line chart config error: {str(e)}")
        return _create_error_figure(f"Config Error: {e}")
    except KeyError as e:
        logger.error(f"Line chart column error: {str(e)}")
        return _create_error_figure(f"Missing Column: {e}")
    except Exception as e:
        logger.error(f"Line chart failed: {str(e)}", exc_info=True)
        return _create_error_figure(f"Error: {e}")


# ============================================================================
# 7. AREA CHART SPECIFIC FUNCTION
# ============================================================================

def plot_plotly_area_chart(df: pd.DataFrame, config_dict: Dict[str, Any]) -> go.Figure:
    """
    Create area chart (special case of line chart with fill).
    """
    config_dict = config_dict.copy()
    
    # Ensure fill is set for area chart
    if 'fill' not in config_dict:
        config_dict['fill'] = 'tozeroy'
    
    # Call the enhanced line chart function
    return plot_plotly_line_chart(df, config_dict)


# ============================================================================
# 8. UTILITY FUNCTIONS
# ============================================================================

def _create_error_figure(message: str) -> go.Figure:
    """Create a unified error visualization figure"""
    fig = go.Figure()
    fig.add_annotation(
        text=f"<b>Chart Error</b><br><br>{message}",
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=14, color="#dc3545"),
        align="center",
        bgcolor="rgba(220, 53, 69, 0.1)",
        bordercolor="#dc3545",
        borderwidth=2,
        borderpad=20
    )
    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor='white',
        height=400,
        margin=dict(t=40, b=40, l=40, r=40),
        template='plotly_white'
    )
    return fig


# ============================================================================
# 9. EXPORT FUNCTIONS
# ============================================================================

__all__ = [
    'plot_plotly_bar_chart',
    'plot_plotly_line_chart',
    'plot_plotly_area_chart',  # NEW
    'BarChartConfig',
    'LineChartConfig',
    'AggFunc',
    'BarMode',
    'ErrorFunc',
    'XAxisType',  # NEW
    'FillMode',  # NEW
]