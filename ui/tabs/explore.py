# data_dashboard.py
"""
Dataset Overview Dashboard
Clean data visualization with consistent styling and robust error handling
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def safe_truncate(text, max_len=25):
    """Safely truncate text for display."""
    text = str(text)
    return text[:max_len-3] + "..." if len(text) > max_len else text

def apply_chart_theme(fig):
    """Apply consistent theme to all charts."""
    fig.update_layout(
        template="plotly_white",
        font=dict(size=12),
        margin=dict(t=40, b=40, l=40, r=40),
        hoverlabel=dict(font_size=12)
    )
    return fig

def validate_column(df, col_name, expected_type=None):
    """Validate column exists and has correct type."""
    if col_name not in df.columns:
        return False, f"Column '{col_name}' not found"
    
    if expected_type == "numeric" and not pd.api.types.is_numeric_dtype(df[col_name]):
        return False, f"Column '{col_name}' is not numeric"
    
    if expected_type == "datetime" and not pd.api.types.is_datetime64_any_dtype(df[col_name]):
        return False, f"Column '{col_name}' is not datetime"
    
    return True, ""

# ============================================================================
# DASHBOARD COMPONENTS
# ============================================================================

def render_dataset_dashboard(df: pd.DataFrame) -> None:
    """
    Main dashboard renderer - clean data exploration interface
    """
    if df is None or df.empty:
        st.warning("No data available for dashboard")
        return
    
    # Store original row count
    total_rows = len(df)
    
    # ==================== TOP HEADER METRICS ====================
    render_dashboard_header(df, total_rows)
    
    # ==================== MAIN DASHBOARD LAYOUT ====================
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # LEFT COLUMN: Key Visualizations
        render_quick_visualizations(df)
        
    with col2:
        # RIGHT COLUMN: Insights & Health
        render_insights_panel(df)
    
    # ==================== DATA PROFILING SECTION ====================
    st.markdown("---")
    render_data_profiling_section(df)
    
    # ==================== INTERACTIVE DATA EXPLORER ====================
    if total_rows >= 5:
        st.markdown("---")
        render_interactive_data_explorer(df)
    else:
        st.info(f"Dataset has {total_rows} rows - showing full dataset view")
        st.dataframe(df, use_container_width=True, height=300)

def render_dashboard_header(df: pd.DataFrame, total_rows: int) -> None:
    """Render the top metrics header row."""
    st.markdown("### 📊 Dataset Dashboard")
    
    # Compute key metrics
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns
    date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
    
    missing_values = df.isnull().sum().sum()
    missing_pct = (missing_values / (len(df) * len(df.columns))) * 100 if df.size > 0 else 0
    duplicate_rows = df.duplicated().sum()
    duplicate_pct = (duplicate_rows / len(df)) * 100 if len(df) > 0 else 0
    
    # Create 4-column metrics grid
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📈 Dataset Size",
            value=f"{total_rows:,} × {len(df.columns)}",
            delta=f"{len(numeric_cols)} numeric, {len(categorical_cols)} categorical"
        )
    
    with col2:
        quality_color = "normal" if missing_pct < 5 else "inverse"
        st.metric(
            label="🔍 Data Quality",
            value=f"{100 - missing_pct:.1f}%",
            delta=f"{missing_values:,} missing" if missing_values > 0 else "No missing",
            delta_color=quality_color
        )
    
    with col3:
        duplicate_color = "normal" if duplicate_pct < 1 else "inverse"
        st.metric(
            label="🔄 Duplicates",
            value=f"{duplicate_rows:,}",
            delta=f"{duplicate_pct:.1f}%" if duplicate_rows > 0 else "None",
            delta_color=duplicate_color
        )
    
    with col4:
        memory_mb = df.memory_usage(deep=True).sum() / (1024 ** 2)
        st.metric(
            label="💾 Memory",
            value=f"{memory_mb:.1f} MB",
            delta=f"{len(date_cols)} date col(s)" if date_cols else "No dates"
        )

def render_quick_visualizations(df: pd.DataFrame) -> None:
    """Render automatic visualizations."""
    st.markdown("### 📈 Quick Visualizations")
    
    # Get column types
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
    
    # Create tabs for different visualization types
    viz_tabs = st.tabs(["📊 Distributions", "📈 Correlations", "🏷️ Categories", "📅 Time Series"])
    
    with viz_tabs[0]:  # Distributions
        if numeric_cols:
            selected_col = st.selectbox(
                "Select numeric column",
                numeric_cols,
                key="dist_col_select"
            )
            
            if selected_col:
                with st.spinner("Generating distribution analysis..."):
                    fig = create_distribution_plot(df, selected_col)
                    st.plotly_chart(fig, use_container_width=True, height=400)
                    
                    # Quick stats for the selected column
                    data = df[selected_col].dropna()
                    col1, col2, col3, col4 = st.columns(4)
                    with col1: st.metric("Mean", f"{data.mean():.2f}")
                    with col2: st.metric("Std Dev", f"{data.std():.2f}")
                    with col3: st.metric("Skewness", f"{data.skew():.2f}")
                    with col4: st.metric("Missing", f"{df[selected_col].isnull().sum()}")
        else:
            st.info("No numeric columns for distribution plots")
    
    with viz_tabs[1]:  # Correlations
        if len(numeric_cols) >= 2:
            with st.spinner("Calculating correlations..."):
                fig = create_correlation_heatmap(df[numeric_cols])
                st.plotly_chart(fig, use_container_width=True, height=450)
                
                # Top correlations
                top_corr = find_top_correlations(df[numeric_cols])
                if top_corr:
                    st.markdown("**🔗 Top Correlations:**")
                    cols = st.columns(min(3, len(top_corr)))
                    for idx, ((col1, col2), corr) in enumerate(top_corr[:3]):
                        with cols[idx]:
                            corr_color = "🟢" if corr > 0 else "🔴"
                            st.caption(f"{corr_color} **{safe_truncate(col1)}** ↔ **{safe_truncate(col2)}**: **{corr:.2f}**")
        else:
            st.info("Need at least 2 numeric columns for correlation analysis")
    
    with viz_tabs[2]:  # Categories
        if categorical_cols:
            # Filter columns with reasonable number of unique values
            cat_options = [c for c in categorical_cols if 1 < df[c].nunique() < 50]
            if cat_options:
                selected_col = st.selectbox(
                    "Select categorical column",
                    cat_options,
                    key="cat_col_select"
                )
                
                if selected_col:
                    with st.spinner("Analyzing categories..."):
                        fig = create_category_plot(df, selected_col)
                        st.plotly_chart(fig, use_container_width=True, height=400)
                        
                        # Category statistics
                        cat_stats = df[selected_col].value_counts()
                        st.caption(f"**{cat_stats.shape[0]}** unique values • **{cat_stats.iloc[0]}** is most frequent ({cat_stats.iloc[0]/len(df)*100:.1f}%)")
            else:
                st.info("No categorical columns with 2-50 unique values")
        else:
            st.info("No categorical columns available")
    
    with viz_tabs[3]:  # Time Series
        if date_cols and numeric_cols:
            date_col = st.selectbox("Date Column", date_cols, key="date_col_select")
            value_col = st.selectbox("Value Column", numeric_cols, key="value_col_select")
            
            if date_col and value_col:
                with st.spinner("Creating time series analysis..."):
                    fig = create_time_series_plot(df, date_col, value_col)
                    st.plotly_chart(fig, use_container_width=True, height=400)
                    
                    # Time range info
                    date_series = pd.to_datetime(df[date_col].dropna())
                    if not date_series.empty:
                        st.caption(f"**Date Range:** {date_series.min().date()} to {date_series.max().date()} • **Days:** {(date_series.max() - date_series.min()).days}")
        else:
            st.info("Need both date and numeric columns for time series")



# ----------------------------------------------------------------------------
# 4. Render Function (with grouped issues)
# ----------------------------------------------------------------------------
def render_insights_panel(df: pd.DataFrame) -> None:
    """Enhanced insights panel with staged to‑do list and hard‑capped health score."""
    st.markdown("### 💡 Insights & Health")

    health = compute_data_health_score(df)
    issues = identify_data_issues(df)
    recommendations = generate_recommendations(df, issues)

    with st.container(border=True):
        # ---- Health Score with context ----
        score = health["score"]
        dtype = health["dataset_type"]
        cap_note = " (capped)" if health["capped"] else ""
        st.markdown(f"### Health Score: **{score:.0f}/100**{cap_note}  ·  *{dtype} dataset*")

        if score >= 80:
            st.progress(score/100, text="✅ Excellent")
        elif score >= 60:
            st.progress(score/100, text="ℹ️ Good")
        elif score >= 40:
            st.progress(score/100, text="⚠️ Fair")
        else:
            st.progress(score/100, text="🔴 Poor")

        if health["capped"]:
            st.caption(f"⚠️ Score capped due to: {', '.join(health['caps'])}")

        # ---- Grouped Issues by Category ----
        if issues:
            st.markdown("#### ⚠️ Key Issues")
            # Define categories and their display names
            category_groups = {
                "missing": "Missing Values",
                "duplicates_exact": "Exact Duplicates",
                "duplicates_fuzzy": "Near‑Duplicates",
                "near_constant": "Nearly Constant Columns",
                "negative_values": "Negative Values",
                "high_correlation": "High Correlations",
                "redundant_columns": "Redundant Columns",
                "date_format": "Date Format Issues",
                "outliers": "Outliers",
                "imbalance": "Imbalanced Targets"
            }
            # Group issues by category
            grouped = {}
            for issue in issues:
                cat = issue.get("category", "other")
                grouped.setdefault(cat, []).append(issue)

            # Display each group in an expander
            for cat, cat_issues in grouped.items():
                display_name = category_groups.get(cat, cat.replace("_", " ").title())
                with st.expander(f"{display_name} ({len(cat_issues)})"):
                    for issue in cat_issues:
                        sev = issue["severity"]
                        icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}.get(sev, "⚪")
                        st.markdown(f"**{icon} {sev.upper()}:** {issue['issue']}")
                        st.caption(f"‣ {issue['impact']}")
                        if issue.get("columns") and len(issue["columns"]) <= 3:
                            st.caption(f"‣ Columns: {', '.join(issue['columns'])}")
        else:
            st.success("No significant issues detected.")

        # ---- Staged Recommendations ----
        if recommendations:
            st.markdown("#### 🎯 Recommended Actions")
            stages = {"quick": "⚡ Quick Wins", "critical": "🛠️ Critical Fixes", "analysis": "🔍 Analysis Prep"}
            current_stage = None
            for rec in recommendations:
                if rec["stage"] != current_stage:
                    current_stage = rec["stage"]
                    st.markdown(f"**{stages[current_stage]}**")
                st.markdown(f"**{rec['step']}.** {rec['action']}  \n*{rec['reason']}*")
                if rec.get("code"):
                    with st.expander("Show code"):
                        st.code(rec["code"], language="python")
        else:
            st.info("No specific recommendations – dataset looks ready.")

        # ---- Quick Stats ----
        st.markdown("#### 📋 Quick Stats")
        col1, col2 = st.columns(2)
        with col1:
            numeric_cnt = len(df.select_dtypes(include=[np.number]).columns)
            cat_cnt = len(df.select_dtypes(include=['object', 'category']).columns)
            st.metric("Numeric", numeric_cnt, delta=f"{numeric_cnt/len(df.columns)*100:.0f}%")
            st.metric("Categorical", cat_cnt, delta=f"{cat_cnt/len(df.columns)*100:.0f}%")
        with col2:
            missing_pct = (df.isnull().sum().sum() / df.size) * 100
            unique_ratio = df.nunique().mean() / len(df) * 100
            st.metric("Missing", f"{missing_pct:.1f}%")
            st.metric("Uniqueness", f"{unique_ratio:.1f}%")

def render_data_profiling_section(df: pd.DataFrame) -> None:
    """Render comprehensive data profiling."""
    st.markdown("### 🔍 Data Profiling")
    
    profiling_tabs = st.tabs(["📊 Column Analysis", "📈 Statistical Summary", "❓ Missing Analysis", "🔄 Data Types"])
    
    with profiling_tabs[0]:
        render_column_analysis(df)
    
    with profiling_tabs[1]:
        render_statistical_summary(df)
    
    with profiling_tabs[2]:
        render_missing_analysis(df)
    
    with profiling_tabs[3]:
        render_data_type_analysis(df)

def render_interactive_data_explorer(df: pd.DataFrame) -> None:
    """Render interactive data explorer with safe slider bounds."""
    st.markdown("### 🔎 Interactive Data Explorer")
    
    col_explorer1, col_explorer2 = st.columns([1, 3])
    
    with col_explorer1:
        st.markdown("#### Column Filters")
        all_columns = df.columns.tolist()
        selected_columns = st.multiselect(
            "Select columns to display",
            all_columns,
            default=all_columns[:min(8, len(all_columns))],
            key="column_selector"
        )
        
        st.markdown("#### Row Filters")
        max_rows_available = len(df)
        
        if max_rows_available >= 10:
            max_rows = st.slider(
                "Max rows to show",
                min_value=10,
                max_value=min(500, max_rows_available),
                value=min(100, max_rows_available),
                key="row_limit"
            )
        else:
            st.info(f"Showing all {max_rows_available} rows")
            max_rows = max_rows_available
        
        if selected_columns:
            sort_by = st.selectbox("Sort by", [None] + selected_columns)
            if sort_by:
                ascending = st.checkbox("Ascending", value=True)
    
    with col_explorer2:
        if selected_columns:
            display_df = df[selected_columns].copy()
            
            if sort_by and sort_by in display_df.columns:
                display_df = display_df.sort_values(by=sort_by, ascending=ascending)
            
            if len(display_df) > max_rows:
                display_df = display_df.head(max_rows)
            
            try:
                st.dataframe(
                    display_df.style.format(precision=2),
                    use_container_width=True,
                    height=400
                )
            except:
                st.dataframe(display_df, use_container_width=True, height=400)

# ============================================================================
# CHART CREATION FUNCTIONS
# ============================================================================

def create_distribution_plot(df: pd.DataFrame, column: str) -> go.Figure:
    """Create distribution plot with histogram, KDE, and box plot."""
    data = df[column].dropna()
    is_numeric = pd.api.types.is_numeric_dtype(data)
    
    if not is_numeric or len(data) < 3:
        # Fallback for non-numeric or small data
        value_counts = df[column].value_counts().head(15)
        fig = px.bar(
            x=value_counts.values,
            y=[safe_truncate(str(v)) for v in value_counts.index],
            orientation='h',
            title=f"Distribution of {safe_truncate(column, 30)}",
            labels={'x': 'Count', 'y': column},
            color=value_counts.values,
            color_continuous_scale='Viridis'
        )
        fig.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
        return apply_chart_theme(fig)
    
    # Create subplots: histogram+KDE on top, box plot below
    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.7, 0.3],
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=(f"Distribution of {safe_truncate(column, 30)}", "Spread & Outliers")
    )
    
    # Histogram with density
    fig.add_trace(
        go.Histogram(
            x=data,
            nbinsx=min(40, int(len(data)**0.5)),
            name="Frequency",
            marker_color="#4A90E2",
            histnorm='probability density',
            hovertemplate="Value: %{x}<br>Density: %{y:.3f}<extra></extra>"
        ),
        row=1, col=1
    )
    
    # KDE overlay (only if enough data)
    if len(data) >= 10:
        try:
            from scipy.stats import gaussian_kde
            kde = gaussian_kde(data)
            x_range = np.linspace(data.min(), data.max(), 200)
            kde_y = kde(x_range)
            
            fig.add_trace(
                go.Scatter(
                    x=x_range, y=kde_y,
                    mode='lines',
                    name='Density Curve',
                    line=dict(color='#D0021B', width=2),
                    hovertemplate="Value: %{x}<br>Density: %{y:.3f}<extra></extra>"
                ),
                row=1, col=1
            )
        except:
            pass  # Skip KDE if fails
    
    # Box plot with outliers
    fig.add_trace(
        go.Box(
            x=data,
            name="Distribution",
            marker_color="#4A90E2",
            boxpoints='suspectedoutliers',
            jitter=0.3,
            pointpos=-1.8,
            hoverinfo="x"
        ),
        row=2, col=1
    )
    
    # Add statistics annotation
    q1, q3 = np.percentile(data, [25, 75])
    iqr = q3 - q1
    stats_text = f"""
    <b>Statistics</b><br>
    Mean: {data.mean():.2f}<br>
    Median: {data.median():.2f}<br>
    Std: {data.std():.2f}<br>
    IQR: {iqr:.2f}<br>
    Range: {data.min():.2f} - {data.max():.2f}
    """
    
    fig.add_annotation(
        text=stats_text,
        xref="paper", yref="paper",
        x=0.98, y=0.7,
        xanchor="right",
        showarrow=False,
        font=dict(size=10),
        align="left",
        bordercolor="#cccccc",
        borderwidth=1,
        borderpad=6,
    )
    
    fig.update_layout(height=500)
    return apply_chart_theme(fig)

def create_correlation_heatmap(df_numeric: pd.DataFrame) -> go.Figure:
    """Create correlation heatmap with clustering."""
    if df_numeric.empty or len(df_numeric.columns) < 2:
        fig = go.Figure()
        fig.add_annotation(
            text="Insufficient numeric columns",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14)
        )
        return apply_chart_theme(fig)
    
    corr = df_numeric.corr().round(3)
    
    # Apply clustering for better organization
    try:
        from scipy.cluster import hierarchy
        Z = hierarchy.linkage(corr, method='ward')
        dendro = hierarchy.dendrogram(Z, no_plot=True)
        idx = dendro['leaves']
        corr = corr.iloc[idx, idx]
    except:
        pass
    
    # Mask upper triangle
    mask = np.triu(np.ones_like(corr, dtype=bool))
    
    # Truncate long column names for display
    display_cols = [safe_truncate(col) for col in corr.columns]
    
    fig = go.Figure(data=go.Heatmap(
        z=corr.mask(mask),
        x=display_cols,
        y=display_cols,
        colorscale='RdBu_r',
        zmid=0,
        zmin=-1,
        zmax=1,
        text=corr.mask(mask),
        texttemplate="%{text:.2f}",
        textfont=dict(size=10),
        hovertemplate="<b>%{y}</b> ↔ <b>%{x}</b><br>Correlation: <b>%{z:.3f}</b><extra></extra>"
    ))
    
    fig.update_layout(
        title="Correlation Matrix",
        height=max(400, len(corr) * 35),
        xaxis_tickangle=-45,
        coloraxis_colorbar=dict(
            title="Correlation",
            tickvals=[-1, -0.5, 0, 0.5, 1],
            ticktext=["-1.0", "-0.5", "0", "0.5", "1.0"]
        )
    )
    
    return apply_chart_theme(fig)

def find_top_correlations(df_numeric: pd.DataFrame, top_n: int = 5) -> list:
    """Find top positive and negative correlations."""
    if len(df_numeric.columns) < 2:
        return []
    
    corr_matrix = df_numeric.corr()
    correlations = []
    
    for i in range(len(corr_matrix.columns)):
        for j in range(i+1, len(corr_matrix.columns)):
            col1 = corr_matrix.columns[i]
            col2 = corr_matrix.columns[j]
            corr = corr_matrix.iloc[i, j]
            
            if not pd.isna(corr):
                correlations.append(((col1, col2), corr))
    
    # Sort by absolute value
    correlations.sort(key=lambda x: abs(x[1]), reverse=True)
    return correlations[:top_n]

def create_category_plot(df: pd.DataFrame, column: str) -> go.Figure:
    """Create categorical plot with cumulative percentage."""
    counts = df[column].value_counts()
    
    # Limit to top 15 categories for readability
    if len(counts) > 15:
        top_counts = counts.head(15)
        other_count = counts[15:].sum()
        top_counts = pd.concat([top_counts, pd.Series({'Other': other_count})])
        counts = top_counts
    
    # Calculate percentages and cumulative
    percentages = (counts / counts.sum() * 100).round(1)
    cumulative = percentages.cumsum()
    
    # Truncate labels for display
    display_labels = [safe_truncate(str(label)) for label in counts.index]
    
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Bar chart (primary y-axis)
    fig.add_trace(
        go.Bar(
            x=display_labels,
            y=counts.values,
            name="Count",
            marker_color="#4A90E2",
            hovertemplate="<b>%{x}</b><br>Count: %{y}<br>Percent: %{customdata}%<extra></extra>",
            customdata=percentages.values
        ),
        secondary_y=False
    )
    
    # Cumulative line (secondary y-axis)
    fig.add_trace(
        go.Scatter(
            x=display_labels,
            y=cumulative.values,
            name="Cumulative %",
            mode='lines+markers',
            line=dict(color='#D0021B', width=2),
            marker=dict(size=6),
            hovertemplate="<b>%{x}</b><br>Cumulative: %{y:.1f}%<extra></extra>",
        ),
        secondary_y=True
    )
    
    fig.update_layout(
        title=f"Distribution of {safe_truncate(column, 30)}",
        xaxis_title=column,
        height=400,
        hovermode="x unified"
    )
    
    fig.update_yaxes(
        title_text="Count",
        secondary_y=False,
        title_font=dict(color="#4A90E2")
    )
    
    fig.update_yaxes(
        title_text="Cumulative %",
        secondary_y=True,
        range=[0, 105],
        title_font=dict(color='#D0021B')
    )
    
    return apply_chart_theme(fig)

def create_time_series_plot(df: pd.DataFrame, date_col: str, value_col: str) -> go.Figure:
    """Create time series with moving averages."""
    # Create a clean working copy
    ts_data = pd.DataFrame({
        'date': pd.to_datetime(df[date_col]),
        'value': df[value_col]
    }).dropna().sort_values('date')
    
    if len(ts_data) < 2:
        fig = go.Figure()
        fig.add_annotation(
            text="Insufficient time series data",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14)
        )
        return apply_chart_theme(fig)
    
    fig = go.Figure()
    
    # Original series
    fig.add_trace(go.Scatter(
        x=ts_data['date'],
        y=ts_data['value'],
        mode='lines',
        name='Original',
        line=dict(color='#4A90E2', width=1.5),
        hovertemplate="Date: %{x|%Y-%m-%d}<br>Value: %{y:.2f}<extra></extra>"
    ))
    
    # 7-day moving average
    if len(ts_data) >= 7:
        ma7 = ts_data['value'].rolling(window=7, center=True, min_periods=1).mean()
        fig.add_trace(go.Scatter(
            x=ts_data['date'],
            y=ma7,
            mode='lines',
            name='7-Day Avg',
            line=dict(color='#7ED321', width=2.5),
            hovertemplate="Date: %{x|%Y-%m-%d}<br>7-Day Avg: %{y:.2f}<extra></extra>"
        ))
    
    # 30-day moving average (if enough data)
    if len(ts_data) >= 30:
        ma30 = ts_data['value'].rolling(window=30, center=True, min_periods=1).mean()
        fig.add_trace(go.Scatter(
            x=ts_data['date'],
            y=ma30,
            mode='lines',
            name='30-Day Avg',
            line=dict(color='#D0021B', width=2.5),
            hovertemplate="Date: %{x|%Y-%m-%d}<br>30-Day Avg: %{y:.2f}<extra></extra>"
        ))
    
    # Highlight recent data point
    last_point = ts_data.iloc[-1]
    fig.add_trace(go.Scatter(
        x=[last_point['date']],
        y=[last_point['value']],
        mode='markers',
        name='Latest',
        marker=dict(color='#F5A623', size=10, symbol='diamond'),
        hovertemplate="Latest:<br>Date: %{x|%Y-%m-%d}<br>Value: %{y:.2f}<extra></extra>"
    ))
    
    # Add trend annotation
    if len(ts_data) >= 10:
        try:
            x_numeric = pd.to_numeric(ts_data['date'])
            y = ts_data['value'].values
            z = np.polyfit(x_numeric, y, 1)
            trend = "📈 Upward" if z[0] > 0 else "📉 Downward" if z[0] < 0 else "➡️ Flat"
            
            fig.add_annotation(
                text=f"Trend: {trend}",
                xref="paper", yref="paper",
                x=0.02, y=0.98,
                xanchor="left",
                showarrow=False,
                font=dict(size=12),
                bordercolor="#cccccc",
                borderwidth=1
            )
        except:
            pass
    
    fig.update_layout(
        title=f"{safe_truncate(value_col, 30)} over Time",
        xaxis_title="Date",
        yaxis_title=value_col,
        hovermode="x unified",
        height=400
    )
    
    return apply_chart_theme(fig)

# ============================================================================
# FINAL ENHANCED INSIGHTS PANEL (v3)
# ============================================================================

import pandas as pd
import numpy as np
import streamlit as st
from itertools import combinations

# ----------------------------------------------------------------------------
# Helper: infer dataset type
# ----------------------------------------------------------------------------
def _infer_dataset_type(df: pd.DataFrame) -> str:
    date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
    if date_cols and len(df) > 10000:
        return "transactional"
    if df.nunique().mean() / len(df) < 0.1:
        return "aggregated"
    return "general"

# ----------------------------------------------------------------------------
# Helper: severity based on ratio and dataset size
# ----------------------------------------------------------------------------
def _severity(ratio: float, n_rows: int, thresholds=(0.01, 0.05, 0.10)) -> str:
    if n_rows < 1000:
        crit, high, med = thresholds
    elif n_rows < 100000:
        crit, high, med = (t * 2 for t in thresholds)   # more forgiving
    else:
        crit, high, med = (t * 3 for t in thresholds)
    if ratio > crit:
        return "critical"
    if ratio > high:
        return "high"
    if ratio > med:
        return "medium"
    return "low"

# ----------------------------------------------------------------------------
# Helper: sample large dataframes for expensive ops
# ----------------------------------------------------------------------------
def _sample_if_large(df: pd.DataFrame, max_rows=50000):
    """Return a sampled copy if dataframe is large, else the original."""
    if len(df) > max_rows:
        return df.sample(n=max_rows, random_state=42)
    return df

# ----------------------------------------------------------------------------
# 1. Health Score (with hard caps and a positive bonus)
# ----------------------------------------------------------------------------
def compute_data_health_score(df: pd.DataFrame) -> dict:
    """
    Returns health score (0-100) and whether any critical caps were applied.
    """
    if df.empty:
        return {"score": 0, "capped": True, "reason": "Dataset empty"}

    dataset_type = _infer_dataset_type(df)
    score = 100
    caps_applied = []

    # ---- Penalties (linear) ----
    missing_pct = (df.isnull().sum().sum() / df.size) * 100
    if dataset_type == "transactional":
        score -= missing_pct * 0.8
    elif dataset_type == "aggregated":
        score -= missing_pct * 0.3
    else:
        score -= missing_pct * 0.4

    dup_pct = (df.duplicated().sum() / len(df)) * 100
    score -= dup_pct * 0.2

    const_cols = [col for col in df.columns if df[col].nunique() == 1]
    score -= len(const_cols) * 3

    high_card_cols = [
        col for col in df.select_dtypes(include=['object']).columns
        if df[col].nunique() > len(df) * 0.9
    ]
    score -= len(high_card_cols) * 2

    # ---- Hard caps (critical failures override) ----
    if dup_pct > 30:
        score = min(score, 40)
        caps_applied.append("duplicates >30%")
    if missing_pct > 40 and dataset_type == "transactional":
        score = min(score, 35)
        caps_applied.append("missing >40% in transactional data")
    if len(const_cols) > 0.5 * len(df.columns):
        score = min(score, 50)
        caps_applied.append(">50% columns are constant")
    if df.shape[1] == 0:
        score = 0
        caps_applied.append("no columns")

    # ---- Positive signal: good mix + potential target ----
    has_date = any(pd.api.types.is_datetime64_any_dtype(df[c]) for c in df.columns)
    target_keywords = ['target', 'label', 'value', 'amount', 'price', 'sales', 'score']
    has_target_like = any(
        any(k in col.lower() for k in target_keywords)
        for col in df.select_dtypes(include=[np.number]).columns
    )
    if has_date and has_target_like:
        score += 8
    elif has_date or has_target_like:
        score += 3

    score = max(0, min(100, round(score)))
    return {
        "score": score,
        "dataset_type": dataset_type,
        "capped": len(caps_applied) > 0,
        "caps": caps_applied
    }

# ----------------------------------------------------------------------------
# 2. Issue Detection (deep, with sampling for large data)
# ----------------------------------------------------------------------------
def identify_data_issues(df: pd.DataFrame) -> list:
    """
    Returns list of issues with keys: issue, severity, impact, columns, category.
    """
    issues = []
    if df.empty:
        return [{
            "issue": "Dataset is empty",
            "severity": "critical",
            "impact": "No analysis possible",
            "category": "empty"
        }]

    # Use a sampled copy for expensive operations if needed
    df_sampled = _sample_if_large(df, max_rows=50000)
    n_rows = len(df)          # original count, not sampled
    n_rows_sampled = len(df_sampled)

    # ---- Missing values in important columns ----
    important_keywords = ['date', 'time', 'id', 'key', 'target', 'label', 'value', 'amount', 'price']
    for col in df.columns:
        miss_ratio = df[col].isnull().mean()
        if miss_ratio == 0:
            continue
        col_lower = col.lower()
        importance = any(k in col_lower for k in important_keywords)
        if importance:
            severity = _severity(miss_ratio, n_rows, thresholds=(0.02, 0.05, 0.10))
        else:
            severity = _severity(miss_ratio, n_rows, thresholds=(0.05, 0.10, 0.20))

        if severity == "low" and miss_ratio < 0.01:
            continue

        impact = f"{miss_ratio*100:.1f}% missing"
        if importance:
            if 'date' in col_lower:
                impact += " – breaks time‑based analysis"
            elif 'id' in col_lower or 'key' in col_lower:
                impact += " – may cause failed joins"
            elif 'target' in col_lower or 'label' in col_lower:
                impact += " – rows will be dropped in supervised learning"

        issues.append({
            "issue": f"{col}: {miss_ratio*100:.1f}% missing",
            "severity": severity,
            "impact": impact,
            "columns": [col],
            "category": "missing"
        })

    # ---- Exact duplicates ----
    dup_exact = df.duplicated().sum()
    if dup_exact > 0:
        ratio = dup_exact / n_rows
        issues.append({
            "issue": f"{dup_exact:,} exact duplicate rows ({ratio*100:.1f}%)",
            "severity": _severity(ratio, n_rows, thresholds=(0.05, 0.10, 0.20)),
            "impact": "Skews aggregations and over‑represents repeated records",
            "columns": None,
            "category": "duplicates_exact"
        })

    # ---- Fuzzy duplicates (improved column selection) ----
    if n_rows < 20000:  # only run on reasonably sized datasets
        text_cols = df.select_dtypes(include=['object']).columns
        # Choose a text column with moderate cardinality (not ID, not constant)
        candidate_cols = []
        for col in text_cols:
            uniq = df[col].nunique()
            if 5 < uniq < 0.5 * n_rows and uniq > 1:
                candidate_cols.append((col, uniq))
        if candidate_cols:
            # pick the one with highest uniqueness (most potential for fuzzy)
            candidate_cols.sort(key=lambda x: x[1], reverse=True)
            sample_col = candidate_cols[0][0]
            normalized = df[sample_col].astype(str).str.lower().str.strip()
            # count rows that become duplicates after normalization, minus exact duplicates
            norm_dup = normalized.duplicated(keep=False).sum() - df[sample_col].duplicated(keep=False).sum()
            if norm_dup > 0:
                ratio = norm_dup / n_rows
                issues.append({
                    "issue": f"Potential near‑duplicates in '{sample_col}' ({norm_dup} rows after normalizing case/space)",
                    "severity": "medium" if ratio > 0.05 else "low",
                    "impact": "These may represent the same entity with slight variations",
                    "columns": [sample_col],
                    "category": "duplicates_fuzzy"
                })

    # ---- Nearly constant columns (>90% same value) ----
    for col in df.columns:
        if df[col].nunique() == 1:
            continue
        top_pct = df[col].value_counts(normalize=True).iloc[0] * 100
        if top_pct > 90:
            issues.append({
                "issue": f"'{col}' is nearly constant ({top_pct:.1f}% same value)",
                "severity": "low",
                "impact": "Provides little information; might still be useful for segmentation",
                "columns": [col],
                "category": "near_constant"
            })

    # ---- Negative values in positive‑only fields ----
    positive_keywords = ['price', 'cost', 'amount', 'age', 'quantity', 'count', 'revenue', 'sales']
    for col in df.select_dtypes(include=[np.number]).columns:
        if any(k in col.lower() for k in positive_keywords):
            neg_count = (df[col] < 0).sum()
            if neg_count > 0:
                ratio = neg_count / n_rows
                issues.append({
                    "issue": f"'{col}' has {neg_count} negative values ({ratio*100:.1f}%)",
                    "severity": _severity(ratio, n_rows, thresholds=(0.01, 0.05, 0.10)),
                    "impact": "Negative values in a field that should be non‑negative may indicate data entry errors",
                    "columns": [col],
                    "category": "negative_values"
                })

    # ---- Near‑perfect correlations (threshold 0.975, limit to top 5 pairs) ----
    numeric_cols = df_sampled.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) >= 2:
        corr_matrix = df_sampled[numeric_cols].corr().abs()
        pairs = []
        for i, j in combinations(range(len(numeric_cols)), 2):
            val = corr_matrix.iloc[i, j]
            if val > 0.975 and not np.isnan(val):
                pairs.append((numeric_cols[i], numeric_cols[j], val))
        # sort descending by correlation
        pairs.sort(key=lambda x: x[2], reverse=True)
        for col1, col2, val in pairs[:5]:
            issues.append({
                "issue": f"'{col1}' and '{col2}' are highly correlated ({val:.3f})",
                "severity": "medium",
                "impact": "May indicate duplicate information; could cause multicollinearity",
                "columns": [col1, col2],
                "category": "high_correlation"
            })

    # ---- Columns >80% identical to another column (redundancy) ----
    all_cols = df.columns.tolist()
    if len(all_cols) <= 20:   # avoid explosion
        for i, j in combinations(range(len(all_cols)), 2):
            col1, col2 = all_cols[i], all_cols[j]
            if df[col1].dtype == df[col2].dtype:
                equal_ratio = (df[col1] == df[col2]).mean()
                if 0.8 < equal_ratio < 1.0:
                    issues.append({
                        "issue": f"'{col1}' and '{col2}' are {equal_ratio*100:.1f}% identical",
                        "severity": "low",
                        "impact": "May be redundant; consider consolidating",
                        "columns": [col1, col2],
                        "category": "redundant_columns"
                    })

    # ---- Inconsistent date formats ----
    for col in df.select_dtypes(include=['object']).columns:
        sample = df[col].dropna().head(100).astype(str)
        if len(sample) == 0:
            continue
        parsed = pd.to_datetime(sample, errors='coerce')
        success = parsed.notna().sum()
        if 0 < success < len(sample):
            issues.append({
                "issue": f"'{col}' has mixed date formats ({success}/{len(sample)} parsed)",
                "severity": "medium",
                "impact": "Inconsistent formats will cause parsing errors in time analysis",
                "columns": [col],
                "category": "date_format"
            })

    # ---- Outliers (IQR method) ----
    for col in df_sampled.select_dtypes(include=[np.number]).columns:
        q1 = df_sampled[col].quantile(0.25)
        q3 = df_sampled[col].quantile(0.75)
        iqr = q3 - q1
        if iqr > 0:
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            outlier_count = ((df_sampled[col] < lower) | (df_sampled[col] > upper)).sum()
            outlier_ratio = outlier_count / n_rows_sampled
            if outlier_ratio > 0.01:
                issues.append({
                    "issue": f"'{col}' has ~{outlier_count} outliers ({outlier_ratio*100:.1f}% of sample)",
                    "severity": _severity(outlier_ratio, n_rows, thresholds=(0.05, 0.10, 0.20)),
                    "impact": "Outliers can skew statistics and affect models",
                    "columns": [col],
                    "category": "outliers"
                })

    # ---- Imbalanced binary columns ----
    for col in df.select_dtypes(include=[np.number, 'bool']).columns:
        if df[col].nunique() == 2:
            vc = df[col].value_counts(normalize=True)
            if max(vc) > 0.9:
                issues.append({
                    "issue": f"Binary column '{col}' is imbalanced ({max(vc)*100:.1f}% in one class)",
                    "severity": "high" if max(vc) > 0.95 else "medium",
                    "impact": "Models may ignore minority class; consider rebalancing",
                    "columns": [col],
                    "category": "imbalance"
                })

    # Sort by severity
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    issues.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 4))
    return issues[:15]  # a few more because we'll group them

# ----------------------------------------------------------------------------
# 3. Recommendations (staged to‑do list)
# ----------------------------------------------------------------------------
def generate_recommendations(df: pd.DataFrame, issues: list) -> list:
    """
    Returns list of recommendations, each with:
        step: int (order)
        stage: "quick", "critical", "analysis"
        action: str
        reason: str
        code: optional str
    """
    recs = []
    used_categories = set()

    def add_rec(step, stage, action, reason, code=None, cat=None):
        if cat and cat in used_categories:
            return
        recs.append({"step": step, "stage": stage, "action": action, "reason": reason, "code": code})
        if cat:
            used_categories.add(cat)

    # STAGE 1: QUICK WINS
    step = 1
    const_cols = [col for col in df.columns if df[col].nunique() == 1]
    if const_cols:
        add_rec(step, "quick",
                f"Drop {len(const_cols)} constant column(s)",
                "They provide no information and waste memory.",
                f"df.drop({const_cols}, axis=1, inplace=True)",
                cat="constant")

    dup_exact = df.duplicated().sum()
    if dup_exact > 0:
        add_rec(step, "quick",
                f"Remove {dup_exact:,} exact duplicate rows",
                "Duplicates bias aggregations and models.",
                "df.drop_duplicates(inplace=True)",
                cat="duplicates_exact")

    date_issues = [i for i in issues if i.get("category") == "date_format"]
    if date_issues:
        col = date_issues[0]["columns"][0]
        add_rec(step, "quick",
                f"Convert '{col}' to datetime",
                "Unlock time‑based analysis.",
                f"df['{col}'] = pd.to_datetime(df['{col}'], errors='coerce')",
                cat="date_format")

    # STAGE 2: CRITICAL FIXES
    step = 2
    critical_missing = [i for i in issues if i["category"] == "missing" and i["severity"] in ("critical", "high")]
    if critical_missing:
        cols = [i["columns"][0] for i in critical_missing[:3]]
        add_rec(step, "critical",
                f"Address missing values in {cols}",
                "High missingness in important columns will break analyses.",
                f"# e.g., df['{cols[0]}'].fillna(df['{cols[0]}'].median(), inplace=True)",
                cat="missing_critical")

    neg_issues = [i for i in issues if i["category"] == "negative_values"]
    if neg_issues:
        cols = [i["columns"][0] for i in neg_issues[:2]]
        add_rec(step, "critical",
                f"Investigate negative values in {cols}",
                "These may be data entry errors and affect calculations.",
                f"df[df['{cols[0]}'] < 0]   # review rows",
                cat="negative")

    fuzzy_issues = [i for i in issues if i["category"] == "duplicates_fuzzy"]
    if fuzzy_issues:
        col = fuzzy_issues[0]["columns"][0]
        add_rec(step, "critical",
                f"Consolidate near‑duplicates in '{col}'",
                "Similar entries may represent the same entity.",
                f"# Normalize and then drop_duplicates\ndf['{col}_norm'] = df['{col}'].str.lower().str.strip()\ndf.drop_duplicates(subset=['{col}_norm'], inplace=True)",
                cat="fuzzy")

    # STAGE 3: ANALYSIS PREP
    step = 3
    outlier_issues = [i for i in issues if i["category"] == "outliers"]
    if outlier_issues:
        cols = [i["columns"][0] for i in outlier_issues[:2]]
        add_rec(step, "analysis",
                f"Cap or transform outliers in {cols}",
                "Extreme values can skew models.",
                f"df['{cols[0]}'] = df['{cols[0]}'].clip(upper=df['{cols[0]}'].quantile(0.99))",
                cat="outliers")

    high_corr_issues = [i for i in issues if i["category"] == "high_correlation"]
    if high_corr_issues:
        add_rec(step, "analysis",
                "Check for multicollinearity among highly correlated features",
                "High correlations (>0.9) can destabilise regression models.",
                "# Compute correlation matrix and consider dropping one of each pair",
                cat="multicollinearity")

    imbalance_issues = [i for i in issues if i["category"] == "imbalance"]
    if imbalance_issues:
        col = imbalance_issues[0]["columns"][0]
        add_rec(step, "analysis",
                f"Address class imbalance in '{col}'",
                "Models may ignore minority class.",
                "Consider SMOTE, class weights, or stratified sampling.",
                cat="imbalance")

    # Deduplicate and sort by step
    seen = set()
    unique_recs = []
    for rec in recs:
        if rec["action"] not in seen:
            seen.add(rec["action"])
            unique_recs.append(rec)
    unique_recs.sort(key=lambda x: x["step"])
    return unique_recs



# ============================================================================
# PROFILING FUNCTIONS
# ============================================================================

def render_column_analysis(df: pd.DataFrame) -> None:
    """Render detailed column analysis."""
    column_info = []
    
    for col in df.columns:
        col_info = {
            "Column": col,
            "Type": str(df[col].dtype),
            "Non-Null": df[col].count(),
            "Null %": f"{(df[col].isnull().sum() / len(df)) * 100:.1f}%",
            "Unique": df[col].nunique(),
            "Sample": safe_truncate(str(df[col].iloc[0]) if not pd.isna(df[col].iloc[0]) else "N/A")
        }
        
        if pd.api.types.is_numeric_dtype(df[col]):
            col_info["Min"] = f"{df[col].min():.2f}" if not df[col].empty else "N/A"
            col_info["Max"] = f"{df[col].max():.2f}" if not df[col].empty else "N/A"
            col_info["Mean"] = f"{df[col].mean():.2f}" if not df[col].empty else "N/A"
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            if not df[col].empty:
                col_info["Range"] = f"{df[col].min().date()} to {df[col].max().date()}"
            else:
                col_info["Range"] = "N/A"
        
        column_info.append(col_info)
    
    analysis_df = pd.DataFrame(column_info)
    st.dataframe(analysis_df, use_container_width=True, height=300)

def render_statistical_summary(df: pd.DataFrame) -> None:
    """Render statistical summary."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    if len(numeric_cols) > 0:
        desc_stats = df[numeric_cols].describe().T
        desc_stats['skew'] = df[numeric_cols].skew()
        desc_stats['kurtosis'] = df[numeric_cols].kurtosis()
        
        st.dataframe(
            desc_stats.style.format("{:.2f}"),
            use_container_width=True,
            height=300
        )
    else:
        st.info("No numeric columns for statistical summary")

def render_missing_analysis(df: pd.DataFrame) -> None:
    """Render missing value analysis."""
    missing_data = df.isnull().sum()
    missing_pct = (missing_data / len(df)) * 100
    
    missing_df = pd.DataFrame({
        'Column': missing_data.index,
        'Missing Count': missing_data.values,
        'Missing %': missing_pct.values
    }).sort_values('Missing %', ascending=False)
    
    missing_df = missing_df[missing_df['Missing Count'] > 0]
    
    if len(missing_df) > 0:
        st.dataframe(
            missing_df.style.bar(subset=['Missing %'], color='#ff6961'),
            use_container_width=True,
            height=300
        )
        
        # Visualize missing pattern
        top_missing = missing_df.head(10).copy()
        top_missing['Column'] = top_missing['Column'].apply(safe_truncate)
        
        fig = px.bar(
            top_missing,
            x='Column',
            y='Missing %',
            title="Top Columns with Missing Values",
            color='Missing %',
            color_continuous_scale='reds'
        )
        fig.update_layout(height=300, xaxis_tickangle=-45)
        fig = apply_chart_theme(fig)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.success("✅ No missing values found")

def render_data_type_analysis(df: pd.DataFrame) -> None:
    """Render data type distribution analysis."""
    dtype_counts = {}
    for col in df.columns:
        dtype = str(df[col].dtype)
        if dtype.startswith('int') or dtype.startswith('float'):
            dtype_key = 'Numeric'
        elif dtype.startswith('datetime'):
            dtype_key = 'Date/Time'
        elif dtype == 'object' or dtype.startswith('category'):
            dtype_key = 'Categorical'
        elif dtype == 'bool':
            dtype_key = 'Boolean'
        else:
            dtype_key = 'Other'
        
        dtype_counts[dtype_key] = dtype_counts.get(dtype_key, 0) + 1
    
    if dtype_counts:
        # Create donut chart
        fig = px.pie(
            names=list(dtype_counts.keys()),
            values=list(dtype_counts.values()),
            title="Data Type Distribution",
            hole=0.4,
            color_discrete_sequence=["#4A90E2", '#7ED321', '#D0021B', '#F5A623', '#9013FE']
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=350, showlegend=False)
        fig = apply_chart_theme(fig)
        st.plotly_chart(fig, use_container_width=True)
        
        # Summary
        total_cols = len(df.columns)
        for dtype, count in dtype_counts.items():
            pct = (count / total_cols) * 100
            st.caption(f"**{dtype}**: {count} column(s) ({pct:.0f}%)")
    else:
        st.info("No data available for type analysis")