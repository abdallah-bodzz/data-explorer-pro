# app.py
"""
Data Explorer Pro - Main Application
Professional data analysis and visualization platform with AI copilot.
Developed by Abdallah A Khames for BODZZ.
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import warnings
warnings.filterwarnings('ignore')

# Import handlers (UI tabs)
from ui.tabs.data_prep import DatasetManager, render_filter_panel
from ui.tabs.ai_copilot import render_ai_copilot_tab
from ui.tabs.chart_studio import ChartManager
import ui.tabs.report_builder as report_builder
from ui.tabs.relationships import render_relationships_tab
from ui.tabs.scripts import render_scripts_tab

# Import utility functions
from reporting.html_export import export_ai_interface, export_chart_interface

# Import the dashboard
from ui.tabs.explore import render_dataset_dashboard

# Import UI components
from ui.components.ui_components import CSS_STYLES, get_main_header_html, premium_header

# Ensure charts directory exists
CHARTS_DIR = "charts"
os.makedirs(CHARTS_DIR, exist_ok=True)

# Constants
VERSION = "1.0.0"
DEVELOPER = "Abdallah A Khames"
COMPANY = "BODZZ"
YEAR = "2026"

# ============================================================================
# SESSION STATE MANAGEMENT (ROBUST & COMPLETE)
# ============================================================================

class SessionStateManager:
    """Robust session state management with complete initialization."""
    
    @staticmethod
    def init():
        """Initialize ALL session state variables with complete defaults."""
        defaults = {
            # Dataset Management
            'dataset': None,
            'original_dataset': None,
            'base_dataset': None,
            'dataset_metadata': None,
            
            # Chart Management
            'current_chart': None,
            'chart_history': [],
            
            # AI Configuration
            'ai_model': 'EchoEngine',
            'api_key': '',
            'ai_EchoEngine_mode': True,
            'use_filtered_for_ai': True,
            
            # Chat State
            'chat_history': [],
            
            # Filter State
            'filter_state': {
                'filters': {},
                'null_handling': {},
                'logic_mode': "AND",
                'logic_groups': [],
                'applied': True,
            },
            'filter_history': [],
            'live_update_mode': True,
            
            # Report Builder
            'report_builder_story': "",
            'report_builder_charts': [],
            
            # Relationship State
            'relationship_datasets': {'main': None},
            'relationship_links': [],
            'join_result': None,
            'join_filters_migrated': False,
            
            # UI State
            'show_clear_confirmation': False,
            'show_save_dialog': False,
        }
        
        # Set defaults for any missing keys
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    @staticmethod
    def validate_dataset_integrity(df: pd.DataFrame) -> dict:
        """Validate dataset integrity and return issues."""
        issues = []
        
        if df is None:
            return {'valid': False, 'issues': ['Dataset is None']}
        
        if df.empty:
            return {'valid': False, 'issues': ['Dataset is empty']}
        
        # Check for problematic columns
        for col in df.columns:
            if any(char in col for char in ['\n', '\r', '\t', '\0']):
                issues.append(f"Column '{col}' contains control characters")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues
        }
    
    @staticmethod
    def reset_analysis(preserve_filters=True):
        """Reset analysis state while preserving dataset and relationships."""
        # Store current filter state if requested
        if preserve_filters and 'filter_state' in st.session_state:
            saved_filters = st.session_state.filter_state.copy()
        else:
            saved_filters = {
                'filters': {},
                'null_handling': {},
                'logic_mode': "AND",
                'logic_groups': [],
                'applied': True,
            }
        
        # Reset chart and analysis state
        st.session_state.current_chart = None
        st.session_state.chart_history = []
        st.session_state.chat_history = []
        
        # Reset filter state
        st.session_state.filter_state = saved_filters
        st.session_state.filter_history = []
        st.session_state.live_update_mode = True
        
        # Clear join result
        st.session_state.join_result = None
        st.session_state.join_filters_migrated = False
        
        # Reset report builder
        st.session_state.report_builder_story = ""
        st.session_state.report_builder_charts = []
        
        # Reset dataset to original if available
        if st.session_state.original_dataset is not None:
            st.session_state.dataset = st.session_state.original_dataset.copy()
            st.session_state.base_dataset = st.session_state.original_dataset.copy()
    
    @staticmethod
    def clear_all():
        """Clear all state - with confirmation and preservation of AI settings."""
        # Store AI settings to preserve
        settings_to_preserve = {
            'ai_model': st.session_state.get('ai_model', 'EchoEngine'),
            'api_key': st.session_state.get('api_key', ''),
            'ai_EchoEngine_mode': st.session_state.get('ai_EchoEngine_mode', True),
        }
        
        # Clear ALL Streamlit session state keys
        keys_to_preserve = set(settings_to_preserve.keys())
        for key in list(st.session_state.keys()):
            if key not in keys_to_preserve:
                del st.session_state[key]
        
        # Restore settings
        for key, value in settings_to_preserve.items():
            st.session_state[key] = value
        
        # Re-initialize defaults
        SessionStateManager.init()

# ============================================================================
# SIDEBAR COMPONENTS (PROFESSIONAL WITH BRANDING)
# ============================================================================

def render_sidebar():
    """Renders a clean, professional sidebar."""
    with st.sidebar:
        # Professional header with company branding
        from ui.components.ui_components import render_sidebar_header, render_sidebar_footer
        from ui.components.ui_components import render_dataset_info, render_empty_dataset_state, render_ai_settings, render_confirmation_dialog
        
        render_sidebar_header(COMPANY)
        
        # Dataset information section
        if st.session_state.dataset is not None:
            render_dataset_info()
        else:
            render_empty_dataset_state()
        
        st.markdown("---")
        
        # AI Configuration Section
        render_ai_settings()
        
        # Confirmation dialog
        render_confirmation_dialog()
        
        # Professional footer with developer and company info
        render_sidebar_footer(VERSION, DEVELOPER, COMPANY, YEAR)

# ============================================================================
# MAIN CONTENT COMPONENTS (PROFESSIONAL)
# ============================================================================

def render_upload_section():
    """Renders a clean upload section for initial data loading."""
    st.markdown(premium_header(
        title="Welcome to Data Explorer Pro",
        subtitle="Please initialize your workspace by importing a primary dataset or selecting a pre-configured template to begin your analysis.",
    ), unsafe_allow_html=True)
    
    # Professional upload section
    with st.container(border=True):
        st.markdown("### 📤 Upload Your Data")
        DatasetManager.upload_widget()
    
    st.markdown("---")
    
def render_current_chart():
    """Renders the current chart with professional styling."""
    if not st.session_state.current_chart:
        return
    
    st.markdown("---")
    
    # Chart display
    try:
        fig = st.session_state.current_chart['figure']
        st.plotly_chart(fig, use_container_width=True)

        # Professional export section
        st.markdown("---")
        export_chart_interface()
        
    except Exception as e:
        st.error(f"❌ Failed to render chart: {e}")
        
def get_column_types(df: pd.DataFrame):
    """Get column types for the dataframe."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()
    datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
    return numeric_cols, categorical_cols, datetime_cols

def render_main_interface():
    """Renders the clean main analysis interface."""
    df = st.session_state.dataset
    if df is None:
        st.error("No dataset loaded. Please load a dataset first.")
        return
    
    numeric_cols, categorical_cols, datetime_cols = get_column_types(df)

    # PROFESSIONAL TAB INTERFACE
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "**Explore Data**",
        "**AI Copilot**",
        "**Chart Studio**",
        "**Data Preparation**",
        "**Report Builder**"
    ])

    with tab1:
        # ==================== EXPLORE DATA TAB ====================
        render_explore_data_tab(df)
        
    with tab2:
        # ==================== AI COPILOT TAB ====================
        _render_ai_copilot_tab(df)
        
    with tab3:
        # ==================== CHART STUDIO TAB ====================
        render_chart_studio_tab(df, numeric_cols, categorical_cols, datetime_cols)
        
    with tab4:
        # ==================== DATA PREPARATION TAB ====================
        render_data_preparation_tab(df)
        
    with tab5:
        # ==================== REPORT BUILDER TAB ====================
        render_report_builder_tab()

def render_explore_data_tab(df):
    """Render Explore Data tab."""
    st.markdown(premium_header(
        title="Data Exploration",
        subtitle="A comprehensive view of your data health, distribution, and structural integrity.",
    ), unsafe_allow_html=True)
    
    # Main dashboard
    render_dataset_dashboard(df)

def _render_ai_copilot_tab(df):
    """Render AI Copilot tab with clean toggle only."""
    st.markdown(premium_header(
        title="AI Copilot",
        subtitle="Get AI-powered insights and automated visualizations from your data.",
    ), unsafe_allow_html=True)
    
    # Simple toggle
    use_filtered_data = st.toggle(
        "🔍 Use filtered data", 
        value=st.session_state.get('use_filtered_for_ai', True),
        help="Analyze filtered data (ON) or original data (OFF)"
    )
    
    st.session_state.use_filtered_for_ai = use_filtered_data
    
    # Use appropriate dataset
    if use_filtered_data:
        df_to_use = df
    else:
        df_to_use = st.session_state.original_dataset
    
    if df_to_use is None:
        st.error("Dataset not available for analysis")
        return
    
    # Switch temporarily and render
    original_dataset_backup = st.session_state.dataset
    st.session_state.dataset = df_to_use
    render_ai_copilot_tab()
    st.session_state.dataset = original_dataset_backup
    export_ai_interface()

def render_chart_studio_tab(df, numeric_cols, categorical_cols, datetime_cols):
    """Render Chart Studio tab."""
    st.markdown(premium_header(
        title="Chart Studio",
        subtitle="Create custom visualizations with full control"
    ), unsafe_allow_html=True)
    
    # Data source toggle
    use_filtered = st.toggle(
        "🔍 Use filtered data", 
        value=True,
        help="Use filtered data (ON) or current original unfiltered data (OFF)"
    )
    
    if not use_filtered:
        df_to_use = st.session_state.original_dataset
    else:
        df_to_use = df
    
    if df_to_use is None:
        st.error("Dataset not available for chart creation")
        return
    
    # Chart builder
    chart_manager = ChartManager(df_to_use, numeric_cols, categorical_cols, datetime_cols)
    chart_manager.manual_chart_interface()
    
    # Current chart display
    if st.session_state.current_chart:
        render_current_chart()
# Add to the import section
from core.data.operations import render_data_operations_tab
def render_data_preparation_tab(df):
    """Render Data Preparation tab - clean and organized."""
    st.markdown(premium_header(
        title="Data Preparation",
        subtitle="Clean, filter, transform and prepare your data for analysis.",
    ), unsafe_allow_html=True)
    
    # Use sub-tabs for clarity - NOW 3 TABS
    prep_tab1, prep_tab2, prep_tab3, prep_tab4= st.tabs([
        "**Dataset Filters**", 
        "**Data Modeling**",
        "**Data Operations**" ,
        "**Run Ready Scripts**"  # NEW TAB
    ])
    
    with prep_tab1:
        # ===== FILTERS SUB-TAB =====
        st.header("🔍 dataset filters")
        st.markdown("""
        Apply complex filters to your dataset with an intuitive interface.  
        *Handle null values, set logic modes, and manage filter groups for precise data slicing.*
        """)

        render_filter_panel()
    
    with prep_tab2:
        # ===== MODELING SUB-TAB =====
        st.header("🔗 Data Modeling & Joins")
        st.markdown("""
        Combine multiple datasets through joins to create unified views for analysis.  
        *Build relationships between tables and generate integrated datasets.*
        """)
        render_modeling_joins()
    
    with prep_tab3:
        # ===== DATA OPERATIONS SUB-TAB =====
        st.header("⚙️ Data Operations")
        st.markdown("""
        Perform advanced data transformations and operations on your dataset.  
        *Clean, reshape, aggregate, create new columns, and manipulate data for analysis.*
        """)

        render_data_operations_tab()

    with prep_tab4:
        # ===== RUN READY SCRIPTS SUB-TAB =====
        st.header("🚀 Run Ready Scripts")
        st.markdown("""
        Execute pre-built, ready-to-run data transformation scripts on your dataset.  
        *Automate data transformations and operations for efficient data processing.*
        """)
        render_scripts_tab()


def render_modeling_joins():
    """Render modeling and joins section."""

    
    # Check if we need to migrate filters after previous join
    if st.session_state.join_result is not None and not st.session_state.join_filters_migrated:
        st.warning("⚠️ Dataset changed after join - filters have been reset")
        st.session_state.filter_state = {
            'filters': {},
            'null_handling': {},
            'logic_mode': "AND",
            'logic_groups': [],
            'applied': True
        }
        st.session_state.join_filters_migrated = True
    
    # Render the relationships tab
    render_relationships_tab()

def render_report_builder_tab():
    """Render Report Builder tab."""
    
    # Professional header
    st.markdown(premium_header(
        title="Professional Report Builder",
        subtitle="Create stunning, data-driven reports with clear narratives and compelling visualizations"
    ), unsafe_allow_html=True)
    
    report_builder.render_report_builder_tab()

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point."""
    # Set page configuration with company branding, professional title, and custom menu, including a detailed About section with company and developer information. (we would update the links to the actual repository and issue tracker for Data Explorer Pro)
    st.set_page_config(
        page_title=f"Data Explorer Pro - {COMPANY}",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://github.com/bodzz/data-explorer-pro',
            'Report a bug': 'https://github.com/bodzz/data-explorer-pro/issues',
            'About': f"""
            # Data Explorer Pro v{VERSION}
            
            **Professional Data Analysis Platform**
            
            **Developed by:** {DEVELOPER}
            **Company:** {COMPANY}
            **Year:** {YEAR}
            
            Built with Streamlit, Plotly, and AI-powered insights.
            
            Features:
            - 📊 Interactive data exploration
            - 🤖 AI-powered analysis
            - 📈 Professional charting
            - 🔧 Advanced data preparation
            - 📋 Report generation
            
            © {YEAR} {COMPANY} - All rights reserved.
            """
        }
    )
    
    # Apply CSS styles
    st.markdown(CSS_STYLES, unsafe_allow_html=True)
    
    # Initialize session state
    SessionStateManager.init()

    # Success message handling
    if st.session_state.get('promote_success_message'):
        st.success(st.session_state.promote_success_message)
        st.session_state.promote_success_message = None

    # Render main header
    st.markdown(
        get_main_header_html(COMPANY, VERSION, DEVELOPER, YEAR), 
        unsafe_allow_html=True
    )
    
    st.markdown("---")
    
    render_sidebar() # Sidebar with professional components and branding

    if st.session_state.dataset is None:
        render_upload_section() # Main content for upload section
    else:
        render_main_interface() # Main content for analysis interface

if __name__ == "__main__":
    main() # Run the main application, entry point for Data Explorer Pro, a professional data analysis platform with AI copilot, developed by Abdallah A Khames for BODZZ.