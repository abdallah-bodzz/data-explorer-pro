# ui/tabs/data_prep.py
"""
Data Preparation Tab – UI for loading, filtering, and managing datasets.
All business logic is delegated to DataService.
"""

import streamlit as st
import pandas as pd
import numpy as np
import time
import json
import traceback
import re
from copy import deepcopy
from datetime import datetime, timedelta
from typing import Tuple, Optional, Dict, Any, List
import warnings

warnings.filterwarnings('ignore')

# Import DataService
from services.data_service import DataService

# Constants
MAX_UPLOAD_SIZE_MB = 100
SUPPORTED_FILE_TYPES = ['csv', 'xlsx', 'xls', 'json', 'tsv', 'txt', 'dat', 'parquet']
DEFAULT_SAMPLING_THRESHOLD = 50_000
DEFAULT_COMPLEXITY_THRESHOLD = 4.0

# Import external modules (UI helpers)
try:
    from core.data.connectors import DataSourceConnector, SuccessHandler
except ImportError:
    DataSourceConnector = None
    SuccessHandler = None

# Smart sampler for UI complexity display (not for actual sampling)
try:
    from core.data.sampler import enhanced_smart_sampling_score, analyze_data_characteristics
except ImportError:
    enhanced_smart_sampling_score = None
    analyze_data_characteristics = None


# ─── Service instance ──────────────────────────────────────────────────────

_DATA_SERVICE = None

def _get_data_service() -> DataService:
    """Get or create the global DataService instance."""
    global _DATA_SERVICE
    if _DATA_SERVICE is None:
        _DATA_SERVICE = DataService()
    return _DATA_SERVICE


# ─── Utility Functions ────────────────────────────────────────────────────

def safe_render(func, fallback_message="Component failed", *args, **kwargs):
    """Safely execute rendering functions with error handling."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        st.error(f"❌ {fallback_message}: {str(e)[:80]}")
        if st.session_state.get('debug_mode', False):
            with st.expander("Technical Details"):
                st.code(traceback.format_exc())
        return None


def quick_validate_dataframe(df: pd.DataFrame) -> Dict:
    """Quick validation of dataframe integrity with detailed feedback."""
    if df is None:
        return {'valid': False, 'issues': ['DataFrame is None'], 'warnings': []}

    if not isinstance(df, pd.DataFrame):
        return {'valid': False, 'issues': ['Not a pandas DataFrame'], 'warnings': []}

    if df.empty:
        return {'valid': False, 'issues': ['DataFrame is empty'], 'warnings': []}

    issues = []
    warnings = []

    # Check for duplicate column names
    if df.columns.duplicated().any():
        dup_cols = df.columns[df.columns.duplicated()].tolist()
        warnings.append(f"Duplicate column names: {dup_cols}")

    # Check for problematic column names
    for col in df.columns:
        col_str = str(col)
        if any(char in col_str for char in ['\n', '\r', '\t', '\0']):
            issues.append(f"Column '{col}' contains control characters")

        if col_str.strip() != col_str:
            warnings.append(f"Column '{col}' has leading/trailing spaces")

    # Check memory usage
    try:
        memory_mb = df.memory_usage(deep=True).sum() / (1024 ** 2)
        if memory_mb > 100:
            warnings.append(f"Large memory usage: {memory_mb:.1f}MB (consider sampling)")
    except:
        pass

    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'warnings': warnings,
        'row_count': len(df),
        'column_count': len(df.columns)
    }


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def get_column_types(df: pd.DataFrame):
    """Enhanced column type detection."""
    if df is None or df.empty:
        return [], [], []

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()
    datetime_cols = df.select_dtypes(include=['datetime64', 'timedelta64']).columns.tolist()

    return numeric_cols, categorical_cols, datetime_cols


def validate_dataset(df: pd.DataFrame) -> Dict:
    """Enhanced dataset validation using DataService."""
    data_service = _get_data_service()
    return data_service.validate_dataset(df)


def get_data_summary() -> Dict:
    """Get comprehensive data summary using DataService."""
    data_service = _get_data_service()
    df = st.session_state.get('dataset')
    if df is None:
        return {'status': 'no_data', 'message': 'No dataset loaded'}
    return data_service.get_dataset_summary(df)


def render_data_status():
    """Render enhanced data status indicator."""
    summary = get_data_summary()
    if summary.get('status') == 'no_data':
        return "📭 No data loaded"

    status_parts = []
    source_type = summary.get('source_type', 'unknown')
    icon_map = {
        'file_upload': '📁',
        'sample_data': '🌟',
        'sql': '🗄️',
        'web_url': '🌐',
        'api': '🔌',
    }
    icon = icon_map.get(source_type, '📊')
    status_parts.append(icon)
    status_parts.append(f"{summary.get('row_count', 0):,} rows")
    if summary.get('filter_active', False):
        status_parts.append(f"🎛️ {summary.get('filter_count', 0)} filter(s)")
    if summary.get('sampling_applied', False):
        status_parts.append("🎯 Sampled")
    return " • ".join(status_parts)


def quick_data_actions():
    """Render quick data action buttons."""
    df = st.session_state.get('dataset')
    if df is None:
        st.info("📭 No dataset loaded")
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📋 Summary", use_container_width=True):
            summary = get_data_summary()
            with st.expander("📊 Dataset Summary", expanded=True):
                for key, value in summary.items():
                    if key not in ['status', 'sampling_info']:
                        st.write(f"**{key.replace('_', ' ').title()}:** {value}")

    with col2:
        if st.button("🔍 Validate", use_container_width=True):
            validation = validate_dataset(df)
            with st.expander("✅ Data Validation", expanded=True):
                if validation['valid']:
                    st.success("✅ Data validation passed")
                else:
                    st.error("❌ Validation issues found")

                for issue in validation.get('issues', []):
                    st.error(f"• {issue}")
                for warning in validation.get('warnings', []):
                    st.warning(f"• {warning}")

    with col3:
        if st.button("🧹 Clean", use_container_width=True):
            data_service = _get_data_service()
            cleaned_df = data_service.remove_duplicates(df)

            if cleaned_df is not None:
                st.session_state.dataset = cleaned_df
                st.session_state.base_dataset = cleaned_df.copy()
                st.success(f"✅ Removed {len(df) - len(cleaned_df)} duplicates")
                st.rerun()

    with col4:
        if st.button("📤 Export", use_container_width=True):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            col_exp1, col_exp2 = st.columns(2)
            with col_exp1:
                csv_data = df.to_csv(index=False)
                st.download_button(
                    "💾 CSV",
                    csv_data,
                    f"dataset_{timestamp}.csv",
                    "text/csv",
                    use_container_width=True
                )
            with col_exp2:
                json_data = df.to_json(orient='records', indent=2)
                st.download_button(
                    "📄 JSON",
                    json_data,
                    f"dataset_{timestamp}.json",
                    "application/json",
                    use_container_width=True
                )


# ─── IMPORT CONFIGURATION MANAGER ────────────────────────────────────────

class ImportConfigManager:
    """Professional import configuration with smart sampling integration (UI only)."""

    @staticmethod
    def render_import_config(uploaded_file) -> Dict:
        """Main method – render clean import configuration UI."""
        config = {}

        file_ext = uploaded_file.name.split('.')[-1].lower() if '.' in uploaded_file.name else ''
        file_size_mb = uploaded_file.size / (1024 * 1024)

        with st.expander("⚙️ Import Configuration", expanded=False):
            preview_df = st.session_state.get('preview_df')

            basic_tab, advanced_tab = st.tabs(["📋 Basic Settings", "⚙️ Advanced Settings"])

            with basic_tab:
                config.update(ImportConfigManager._render_basic_settings(
                    uploaded_file, file_ext, file_size_mb, preview_df
                ))

            with advanced_tab:
                config.update(ImportConfigManager._render_advanced_settings(
                    file_ext, file_size_mb, preview_df
                ))

        return config

    @staticmethod
    def _render_basic_settings(uploaded_file, file_ext: str, file_size_mb: float,
                              preview_df: Optional[pd.DataFrame] = None) -> Dict:
        """Essential settings that most users need."""
        config = {}

        st.markdown("#### File Settings")

        if file_ext in ['csv', 'tsv', 'txt']:
            col1, col2 = st.columns(2)

            with col1:
                separator_map = {
                    "Comma (CSV)": ",",
                    "Semicolon": ";",
                    "Tab (TSV)": "\t",
                    "Pipe": "|"
                }
                separator_choice = st.selectbox(
                    "Field Separator",
                    options=list(separator_map.keys()),
                    index=0,
                    help="Character that separates columns in your file"
                )
                config['separator'] = separator_map[separator_choice]

            with col2:
                config['encoding'] = st.selectbox(
                    "Text Encoding",
                    options=["utf-8", "latin-1", "cp1252", "iso-8859-1"],
                    index=0,
                    help="Character encoding (UTF-8 works for most files)"
                )

        elif file_ext in ['xlsx', 'xls']:
            try:
                uploaded_file.seek(0)
                xls = pd.ExcelFile(uploaded_file, engine='openpyxl')
                sheet_names = xls.sheet_names
                uploaded_file.seek(0)

                if len(sheet_names) == 1:
                    st.info(f"📄 Found 1 worksheet: **{sheet_names[0]}**")
                    config['sheet'] = sheet_names[0]
                else:
                    config['sheet'] = st.selectbox(
                        f"Select Worksheet ({len(sheet_names)} available)",
                        options=sheet_names,
                        index=0,
                        help="Choose which worksheet to load data from"
                    )
            except Exception:
                st.warning("⚠️ Could not read Excel file structure")
                config['sheet'] = 0

        elif file_ext == 'json':
            st.info("📄 JSON files will be loaded with automatic parsing")
        elif file_ext == 'parquet':
            st.success("📦 Parquet detected - optimized loading enabled")

        st.markdown("---")

        # SMART SAMPLING SECTION (UI display only)
        st.markdown("#### 🎯 Smart Sampling")

        complexity_score = None
        if preview_df is not None and not preview_df.empty:
            try:
                if enhanced_smart_sampling_score is not None and analyze_data_characteristics is not None:
                    complexity_score = enhanced_smart_sampling_score(preview_df)
                    data_analysis = analyze_data_characteristics(preview_df)

                    st.session_state.complexity_score = complexity_score
                    st.session_state.data_analysis = data_analysis

                    with st.container(border=True):
                        col_score, col_status = st.columns([3, 1])
                        with col_score:
                            st.markdown(f"**Data Complexity: {complexity_score:.1f}/10**")
                            progress_value = complexity_score / 10
                            if complexity_score > 7.5:
                                color = "#ef4444"
                            elif complexity_score > 5.0:
                                color = "#f59e0b"
                            else:
                                color = "#10b981"

                            st.markdown(f"""
                            <div style="background-color: #f3f4f6; border-radius: 8px; padding: 2px; margin: 8px 0;">
                                <div style="background-color: {color}; width: {progress_value*100}%;
                                         height: 20px; border-radius: 6px;">
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                        with col_status:
                            if complexity_score > 7.5:
                                st.error("⚠️ High")
                            elif complexity_score > 5.0:
                                st.warning("⚠️ Medium")
                            else:
                                st.success("✅ Low")

                    with st.expander("📊 Data Characteristics", expanded=False):
                        col_char1, col_char2 = st.columns(2)
                        with col_char1:
                            st.caption(f"**Rows:** {len(preview_df):,}")
                            st.caption(f"**Columns:** {len(preview_df.columns)}")
                            missing_pct = data_analysis.get("missing_data", {}).get("total_null_percentage", 0)
                            if missing_pct > 0.1:
                                st.warning(f"**Missing:** {missing_pct:.1%}")
                            else:
                                st.caption(f"**Missing:** {missing_pct:.1%}")

                        with col_char2:
                            avg_skew = data_analysis.get("numerical", {}).get("average_abs_skewness", 0)
                            if avg_skew > 1.0:
                                st.warning(f"**Skew:** {avg_skew:.1f}")
                            else:
                                st.caption(f"**Skew:** {avg_skew:.1f}")

                            cat_imbalance = data_analysis.get("categorical", {}).get("imbalance", {})
                            if cat_imbalance:
                                max_imbalance = max([v.get("imbalance_ratio", 1) for v in cat_imbalance.values()])
                                if max_imbalance > 10:
                                    st.warning(f"**Imbalance:** {max_imbalance:.0f}x")
                                else:
                                    st.caption(f"**Imbalance:** {max_imbalance:.0f}x")

            except Exception as e:
                st.warning(f"⚠️ Complexity analysis failed: {str(e)[:50]}")

        sampling_default = file_size_mb > 5 or (complexity_score and complexity_score > 5.0)

        config['enable_smart_sampling'] = st.toggle(
            "Enable Smart Sampling",
            value=sampling_default,
            help="Uses advanced algorithms to sample data while preserving patterns"
        )

        if config['enable_smart_sampling']:
            with st.container(border=True):
                st.markdown("**Sampling Configuration**")
                col_thresh1, col_thresh2 = st.columns(2)

                with col_thresh1:
                    config['size_threshold'] = st.number_input(
                        "Size Threshold (rows)",
                        min_value=1000,
                        max_value=500000,
                        value=100000,
                        step=1000,
                        help="Datasets larger than this will trigger sampling"
                    )

                with col_thresh2:
                    config['complexity_threshold'] = st.slider(
                        "Complexity Threshold",
                        min_value=1.0,
                        max_value=10.0,
                        value=5.0,
                        step=0.5,
                        help="Higher complexity = more aggressive sampling"
                    )

                if preview_df is not None and len(preview_df) > 0:
                    preview_rows = len(preview_df)
                    if uploaded_file.size > 0:
                        bytes_per_row = len(str(preview_df).encode()) / preview_rows
                        estimated_total = int(uploaded_file.size / bytes_per_row) if bytes_per_row > 0 else 0
                        if estimated_total > 0:
                            col_est1, col_est2 = st.columns(2)
                            with col_est1:
                                st.caption(f"**Estimated:** {estimated_total:,} rows")
                            with col_est2:
                                if estimated_total > config['size_threshold']:
                                    st.caption("🔔 **Will sample**")
                                else:
                                    st.caption("✅ **Within threshold**")
        else:
            config['max_rows'] = st.number_input(
                "Maximum Rows",
                min_value=1000,
                max_value=200000,
                value=50000,
                step=1000,
                help="Maximum rows to load when smart sampling is off"
            )

        return config

    @staticmethod
    def _render_advanced_settings(file_ext: str, file_size_mb: float,
                                 preview_df: Optional[pd.DataFrame] = None) -> Dict:
        """Advanced settings with smart sampling options."""
        config = {}

        st.markdown("#### Advanced Options")
        st.caption("Most users can leave these at default values")

        with st.container(border=True):
            st.markdown("**🎯 Sampling Configuration**")
            config['random_state'] = st.number_input(
                "Random Seed",
                min_value=0,
                max_value=1000,
                value=42,
                help="Seed for reproducible sampling (42 = standard)"
            )

            if preview_df is not None and not preview_df.empty:
                categorical_cols = preview_df.select_dtypes(include=['object', 'category']).columns.tolist()
                suitable_strat_cols = []
                for col in categorical_cols:
                    unique_count = preview_df[col].nunique()
                    if 2 <= unique_count <= 20:
                        suitable_strat_cols.append(col)

                if suitable_strat_cols:
                    strat_options = ["None (Random sampling)"] + suitable_strat_cols
                    selected = st.selectbox(
                        "Preserve Distribution (Stratify)",
                        options=strat_options,
                        index=0,
                        help="Maintain original distribution of selected column"
                    )
                    if selected != "None (Random sampling)":
                        config['stratify_col'] = selected
                        st.success(f"✅ Will preserve distribution of '{selected}'")
                else:
                    st.caption("No suitable categorical columns for stratification")

        with st.container(border=True):
            st.markdown("**🧹 Data Cleaning**")
            config['na_values'] = st.text_input(
                "Treat as Missing Values",
                value="NA, N/A, null, NULL, NaN, nan, -, ..",
                help="Comma-separated values to treat as empty/NaN"
            )

            col_clean1, col_clean2 = st.columns(2)
            with col_clean1:
                config['remove_duplicates'] = st.toggle(
                    "Remove Duplicates",
                    value=True,
                    help="Automatically remove duplicate rows"
                )
            with col_clean2:
                config['fix_column_names'] = st.toggle(
                    "Clean Column Names",
                    value=True,
                    help="Standardize column names (lowercase, underscores)"
                )

            config['skip_rows'] = st.number_input(
                "Skip Initial Rows",
                min_value=0,
                max_value=100,
                value=0,
                help="Skip metadata or header rows"
            )

        with st.container(border=True):
            st.markdown("**🔍 Data Type Detection**")
            col_type1, col_type2 = st.columns(2)
            with col_type1:
                config['parse_dates'] = st.toggle(
                    "Auto-Detect Dates",
                    value=True,
                    help="Automatically identify and convert date columns"
                )
            with col_type2:
                config['infer_types'] = st.toggle(
                    "Infer Column Types",
                    value=True,
                    help="Automatically detect optimal data types"
                )

        config['optimize_memory'] = st.toggle(
            "Optimize Memory Usage",
            value=True,
            help="Reduce memory footprint using efficient data types"
        )

        if file_ext in ['csv', 'tsv', 'txt']:
            with st.container(border=True):
                st.markdown("**📄 CSV Options**")
                config['decimal'] = st.selectbox(
                    "Decimal Separator",
                    options=[".", ","],
                    index=0,
                    help="Character used for decimal points in numbers"
                )

        if file_size_mb > 100:
            st.warning("""
            ⚠️ **Large File Detected**
            **Recommendations:**
            1. Enable Smart Sampling
            2. Consider reducing maximum rows
            3. Close other browser tabs
            4. Use 64-bit Python if available
            """)

        return config

    @staticmethod
    def create_file_preview(uploaded_file, config: Dict) -> Optional[pd.DataFrame]:
        """Create a preview with smart analysis."""
        try:
            uploaded_file.seek(0)
            file_ext = uploaded_file.name.split('.')[-1].lower() if '.' in uploaded_file.name else ''

            na_values = None
            if config.get('na_values'):
                na_values = [v.strip() for v in config['na_values'].split(',')]

            preview_rows = 10

            if file_ext in ['csv', 'tsv', 'txt']:
                df = pd.read_csv(
                    uploaded_file,
                    sep=config.get('separator', ','),
                    encoding=config.get('encoding', 'utf-8'),
                    nrows=preview_rows + config.get('skip_rows', 0),
                    na_values=na_values,
                    keep_default_na=config.get('keep_default_na', True),
                    decimal=config.get('decimal', '.'),
                    encoding_errors='replace'
                )
                if config.get('skip_rows', 0) > 0:
                    df = df.iloc[config['skip_rows']:]

            elif file_ext in ['xlsx', 'xls']:
                df = pd.read_excel(
                    uploaded_file,
                    sheet_name=config.get('sheet', 0),
                    nrows=preview_rows + config.get('skip_rows', 0),
                    na_values=na_values,
                    keep_default_na=config.get('keep_default_na', True),
                    engine='openpyxl'
                )
                if config.get('skip_rows', 0) > 0:
                    df = df.iloc[config['skip_rows']:]

            elif file_ext == 'json':
                df = pd.read_json(uploaded_file, nrows=preview_rows)
            elif file_ext == 'parquet':
                df = pd.read_parquet(uploaded_file)
            else:
                st.error(f"❌ Unsupported file type: .{file_ext}")
                return None

            uploaded_file.seek(0)

            if df is not None and not df.empty:
                st.session_state.preview_df = df

                try:
                    if enhanced_smart_sampling_score is not None and analyze_data_characteristics is not None:
                        complexity_score = enhanced_smart_sampling_score(df)
                        data_analysis = analyze_data_characteristics(df)
                        st.session_state.complexity_score = complexity_score
                        st.session_state.data_analysis = data_analysis
                except ImportError:
                    pass

            return df

        except pd.errors.EmptyDataError:
            st.error("❌ File appears to be empty")
            return None
        except pd.errors.ParserError as e:
            st.error(f"❌ Could not parse file: {str(e)[:100]}")
            st.info("💡 Try adjusting field separator or encoding")
            return None
        except UnicodeDecodeError as e:
            st.error(f"❌ Encoding error: {str(e)[:100]}")
            st.info("💡 Try changing the encoding in Basic Settings")
            return None
        except Exception as e:
            st.error(f"❌ Preview failed: {str(e)[:100]}")
            return None


# ─── DATASET MANAGER ──────────────────────────────────────────────────────

class DatasetManager:
    """Professional dataset management with enterprise-grade UX."""

    @staticmethod
    def upload_widget():
        """Render professional data upload interface."""
        st.markdown("<h5>Load data from files, sample datasets, or external sources</h5>", unsafe_allow_html=True)

        tab1, tab2, tab3 = st.tabs([
            "**📁 File Upload**",
            "**🌟 Sample Data**",
            "**🔗 External Sources**"
        ])

        with tab1:
            DatasetManager._render_file_upload()

        with tab2:
            DatasetManager._render_sample_data()

        with tab3:
            DatasetManager._render_external_sources()

    @staticmethod
    def _render_file_upload():
        """Professional file upload interface."""
        st.markdown("### 📁 Upload Your Data")

        uploaded_file = st.file_uploader(
            "Drag & drop or click to browse",
            type=SUPPORTED_FILE_TYPES,
            help=f"""
            **Supported formats:** {', '.join(SUPPORTED_FILE_TYPES).upper()}
            **Maximum size:** {MAX_UPLOAD_SIZE_MB}MB
            **Best practices:** Clean column names, UTF-8 encoding
            """,
            label_visibility="collapsed"
        )

        if uploaded_file:
            file_size_mb = uploaded_file.size / (1024 * 1024)
            file_ext = uploaded_file.name.split('.')[-1].upper() if '.' in uploaded_file.name else "UNK"

            with st.container(border=True):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("File", uploaded_file.name[:20] + "..." if len(uploaded_file.name) > 20 else uploaded_file.name,
                             help=uploaded_file.name)
                with col2:
                    st.metric("Type", file_ext)
                with col3:
                    st.metric("Size", f"{file_size_mb:.1f} MB")
                with col4:
                    if file_size_mb > MAX_UPLOAD_SIZE_MB:
                        status = "❌ Too large"
                        delta_color = "off"
                    else:
                        status = "✅ Ready"
                        delta_color = "normal"
                    st.metric("Status", status, delta_color=delta_color)

            if file_size_mb > MAX_UPLOAD_SIZE_MB:
                st.error(f"""
                ❌ **File exceeds size limit**
                • Your file: {file_size_mb:.1f}MB
                • Maximum allowed: {MAX_UPLOAD_SIZE_MB}MB
                **Solutions:**
                1. Compress or split your file
                2. Use sample data for testing
                3. Export to CSV/Parquet for better compression
                """)
                return

            with st.container(border=True):
                st.markdown("#### ⚙️ Import Configuration")
                import_config = ImportConfigManager.render_import_config(uploaded_file)
                st.session_state.import_config = import_config

                col_preview, col_load, col_reset = st.columns([2, 2, 1])

                with col_preview:
                    if st.button("👁️ **Preview Data**",
                                use_container_width=True,
                                type="secondary",
                                help="Preview first 10 rows with current settings"):
                        with st.spinner("Generating preview..."):
                            preview_df = ImportConfigManager.create_file_preview(
                                uploaded_file, import_config
                            )
                            if preview_df is not None:
                                with st.expander("📋 Data Preview", expanded=True):
                                    st.dataframe(preview_df, use_container_width=True)
                                    col_stat1, col_stat2, col_stat3 = st.columns(3)
                                    with col_stat1:
                                        st.caption(f"**Rows:** {len(preview_df)}")
                                    with col_stat2:
                                        st.caption(f"**Columns:** {len(preview_df.columns)}")
                                    with col_stat3:
                                        missing = preview_df.isna().sum().sum()
                                        missing_pct = missing / (len(preview_df) * len(preview_df.columns)) if len(preview_df) > 0 else 0
                                        if missing_pct > 0.1:
                                            st.error(f"**Missing:** {missing} ({missing_pct:.1%})")
                                        else:
                                            st.caption(f"**Missing:** {missing}")

                with col_load:
                    if st.button("🚀 **Load Dataset**",
                                use_container_width=True,
                                type="primary",
                                help="Load dataset with current settings"):
                        DatasetManager._load_dataset(uploaded_file)

                with col_reset:
                    if st.button("🔄 **Reset**",
                                use_container_width=True,
                                help="Reset all settings to defaults"):
                        keys_to_clear = ['import_config', 'preview_df', 'complexity_score', 'data_analysis']
                        for key in keys_to_clear:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.rerun()

    @staticmethod
    def _render_sample_data():
        """Professional sample data interface."""
        st.markdown("### 🎯 Sample Datasets")
        st.caption("Explore platform features with ready-to-use datasets")

        col1, col2 = st.columns(2)

        with col1:
            with st.container(border=True, height=200):
                st.markdown("#### 📈 **Sales Analytics**")
                st.caption("5,000+ sales records with regional performance, product categories, and profit analysis")
                if st.button(
                    "📥 Load Sales Data",
                    use_container_width=True,
                    key="load_sales_sample_main",
                    help="Load sales analytics sample dataset"
                ):
                    DatasetManager._load_sample_dataset('sales')

        with col2:
            with st.container(border=True, height=200):
                st.markdown("#### 🏠 **Real Estate**")
                st.caption("3,000+ property listings with price distribution, location analysis, and market trends")
                if st.button(
                    "📥 Load Housing Data",
                    use_container_width=True,
                    key="load_housing_sample_main",
                    help="Load real estate sample dataset"
                ):
                    DatasetManager._load_sample_dataset('housing')

        with st.expander("🚀 Quick Start Guide", expanded=False):
            st.markdown("""
            **Get started in minutes:**
            1. **Choose a sample dataset** above
            2. **Explore the data** in the Data Exploration tab
            3. **Try AI Copilot** for automated insights
            4. **Create visualizations** in Chart Studio
            5. **Build a report** with your findings
            **Sample data is perfect for:**
            • Testing platform features
            • Learning data analysis workflows
            • Demonstrating capabilities to stakeholders
            • Prototyping before using your own data
            """)

    @staticmethod
    def _render_external_sources():
        """Professional external sources interface."""
        st.markdown("### 🔗 External Data Sources")
        st.caption("Connect to databases, APIs, or cloud storage")

        try:
            if DataSourceConnector:
                DataSourceConnector.render_connection_selector()
            else:
                st.info("""
                🔌 **External Connectors**
                *This feature requires additional setup.*
                **Available options:**
                1. Upload files directly (recommended)
                2. Use sample data for testing
                3. Contact support for enterprise connectors
                """)
        except Exception:
            st.error("🔌 Connection interface unavailable")
            st.info("Please use file upload or sample data for now.")

    @staticmethod
    def _load_dataset(uploaded_file):
        """Production-grade dataset loading using DataService."""
        try:
            progress_bar = st.progress(0, text="🔄 Initializing smart import...")
            status_container = st.empty()

            status_container.markdown("**📦 Loading import configuration...**")
            progress_bar.progress(10)

            import_config = st.session_state.get('import_config', {})

            defaults = {
                'separator': ',',
                'encoding': 'utf-8',
                'sheet': 0,
                'enable_smart_sampling': True,
                'size_threshold': 100000,
                'complexity_threshold': 5.0,
                'random_state': 42,
                'stratify_col': None,
                'optimize_memory': True,
                'remove_duplicates': True,
                'fix_column_names': True,
                'parse_dates': True,
                'infer_types': True,
                'skip_rows': 0,
                'keep_default_na': True,
                'decimal': '.',
                'na_values': "NA, N/A, null, NULL, NaN, nan, -, .."
            }

            for key, default_value in defaults.items():
                if key not in import_config:
                    import_config[key] = default_value

            status_container.markdown("**🔧 Loading dataset with smart settings...**")
            progress_bar.progress(25)

            data_service = _get_data_service()
            df, metadata = data_service.load_dataset_from_file(uploaded_file, import_config)

            if df is None:
                st.error(f"❌ Failed to load: {metadata.get('error', 'Unknown error')}")
                progress_bar.empty()
                status_container.empty()
                return

            status_container.markdown("**💾 Saving to workspace...**")
            progress_bar.progress(90)

            st.session_state.original_dataset = df.copy()
            st.session_state.base_dataset = df.copy()
            st.session_state.dataset = df.copy()
            st.session_state.dataset_metadata = metadata

            # Store sampling info if available
            if metadata.get('sampling_info'):
                st.session_state.sampling_metadata = metadata.get('sampling_info', {})
            if metadata.get('sampling_report'):
                st.session_state.smart_sampling_report = metadata.get('sampling_report')

            st.session_state.filter_state = {
                'filters': {},
                'null_handling': {},
                'logic_mode': "AND",
                'logic_groups': [],
                'applied': True,
                'last_update': time.time(),
                'version': 1.0
            }

            for key in ['preview_df', 'complexity_score', 'data_analysis', 'import_config']:
                if key in st.session_state:
                    del st.session_state[key]

            progress_bar.progress(100)
            status_container.markdown("**✅ Import complete!**")
            time.sleep(0.3)
            progress_bar.empty()
            status_container.empty()

            with st.container(border=True):
                col_s1, col_s2, col_s3 = st.columns(3)
                with col_s1:
                    st.metric("Rows", f"{len(df):,}")
                with col_s2:
                    st.metric("Columns", f"{len(df.columns)}")
                with col_s3:
                    sampling_info = metadata.get('sampling_info', {})
                    if sampling_info.get('was_sampled'):
                        original_rows = sampling_info.get('original_shape', (0, 0))[0]
                        sampled_rows = sampling_info.get('sampled_shape', (0, 0))[0]
                        if original_rows > 0:
                            reduction_pct = (1 - sampled_rows/original_rows) * 100
                            st.metric("Reduction", f"{reduction_pct:.1f}%")
                    else:
                        st.metric("Status", "✅ Complete")

            if metadata.get('sampling_info', {}).get('was_sampled'):
                st.info(f"""
                🎯 **Smart Sampling Applied**
                **Method:** {sampling_info.get('method', 'Unknown')}
                **Reason:** {sampling_info.get('reason', 'N/A')}
                **Complexity Score:** {sampling_info.get('sampling_score', 0):.1f}/10
                • **Original:** {sampling_info.get('original_shape', (0, 0))[0]:,} rows
                • **Sampled:** {sampling_info.get('sampled_shape', (0, 0))[0]:,} rows
                """)

            time.sleep(0.5)
            st.rerun()

        except Exception as e:
            st.error(f"❌ **Import Failed**\n**Error:** {str(e)[:150]}")
            with st.expander("🔍 Technical Details"):
                st.code(traceback.format_exc())
            if 'progress_bar' in locals():
                progress_bar.empty()
            if 'status_container' in locals():
                status_container.empty()

    @staticmethod
    def _load_sample_dataset(dataset_type: str):
        """Load sample dataset using DataService."""
        try:
            with st.spinner(f"🎯 Loading {dataset_type} dataset..."):
                data_service = _get_data_service()
                df, metadata = data_service.load_sample_dataset(dataset_type)

                st.session_state.original_dataset = df.copy()
                st.session_state.base_dataset = df.copy()
                st.session_state.dataset = df.copy()
                st.session_state.dataset_metadata = metadata

                st.session_state.filter_state = {
                    'filters': {},
                    'null_handling': {},
                    'logic_mode': "AND",
                    'logic_groups': [],
                    'applied': True
                }

                if 'import_config' in st.session_state:
                    del st.session_state.import_config

                st.success(f"""
                {metadata.get('dataset_name', 'Dataset')} loaded successfully!
                • **Rows:** {len(df):,}
                • **Columns:** {len(df.columns)}
                • **Ready for analysis** in Data Exploration tab
                """)

                time.sleep(0.5)
                st.rerun()

        except Exception as e:
            st.error(f"❌ Failed to load sample dataset: {str(e)[:80]}")
            st.info("Try reloading the page or contact support if the issue persists.")


# ─── FILTER PANEL ENTRY POINT ────────────────────────────────────────────

class ProfessionalFilterUI:
    """
    Enhanced unified filter system with better UX and error handling.
    All filtering logic is delegated to DataService.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.filter_id = f"filter_id"
        self._initialize_filter_state()

    def _initialize_filter_state(self):
        """Initialize filter state with defaults."""
        if 'filter_state' not in st.session_state:
            st.session_state.filter_state = {
                'filters': {},
                'null_handling': {},
                'logic_mode': "AND",
                'logic_groups': [],
                'applied': True,
                'last_update': time.time(),
                'version': 1.0
            }

        if 'live_update_mode' not in st.session_state:
            st.session_state.live_update_mode = True

        if 'filter_history' not in st.session_state:
            st.session_state.filter_history = []

    def render(self) -> Optional[pd.DataFrame]:
        """Main render method with error boundary."""
        try:
            if self.df is None or self.df.empty:
                st.info("📭 No data available for filtering")
                return self.df

            validation = quick_validate_dataframe(self.df)
            if not validation['valid']:
                st.error("❌ Cannot filter invalid dataset")
                for issue in validation.get('issues', []):
                    st.error(f"• {issue}")
                return self.df

            self._render_header()

            col_filters, col_summary = st.columns([2, 1])

            with col_filters:
                self._render_filter_builder()

            with col_summary:
                self._render_filter_summary()

            self._render_actions()

            filtered_data = self._apply_filters_to_data()

            if st.session_state.live_update_mode:
                self._auto_apply_filters(filtered_data)

            return filtered_data

        except Exception as e:
            st.error(f"❌ Filter system error: {str(e)[:80]}")
            st.info("Resetting filters to default...")
            self._reset_to_default()
            return self.df

    def _render_header(self):
        """Render enhanced filter header."""
        col1, col4 = st.columns([3, 1])

        with col1:
            st.markdown("### 🎛️ Dataset Filters")
            active_count = len(st.session_state.filter_state['filters'])
            if active_count > 0:
                st.caption(f"🟢 **{active_count} active filter(s)**")
            else:
                st.caption("⚪ No filters applied")

        with col4:
            live_mode = st.toggle(
                "Live Update",
                value=st.session_state.live_update_mode,
                help="Apply filters automatically when changed",
                key=f"live_toggle_{self.filter_id}"
            )
            if live_mode != st.session_state.live_update_mode:
                st.session_state.live_update_mode = live_mode
                st.rerun()

        st.markdown("---")

    def _render_filter_builder(self):
        """Render enhanced filter creation interface."""
        st.markdown("#### 🔍 Filter Builder")

        if not st.session_state.filter_state['filters']:
            self._render_filter_suggestions()

        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist() if not self.df.empty else []
        categorical_cols = self.df.select_dtypes(include=['object', 'category']).columns.tolist() if not self.df.empty else []
        date_cols = [c for c in self.df.columns if pd.api.types.is_datetime64_any_dtype(self.df[c])] if not self.df.empty else []
        other_cols = [c for c in self.df.columns if c not in numeric_cols + categorical_cols + date_cols] if not self.df.empty else []

        tab_names = [
            f"📊 Numeric ({len(numeric_cols)})",
            f"🏷️ Categorical ({len(categorical_cols)})",
            f"📅 Date ({len(date_cols)})",
            f"📝 Other ({len(other_cols)})"
        ]

        filter_tabs = st.tabs(tab_names)

        with filter_tabs[0]:
            if numeric_cols:
                selected_col = st.selectbox(
                    "Select numeric column",
                    numeric_cols,
                    key=f"num_select_{self.filter_id}",
                    label_visibility="collapsed"
                )
                if selected_col:
                    self._render_numeric_filter(selected_col)
            else:
                st.info("🎯 No numeric columns available")

        with filter_tabs[1]:
            if categorical_cols:
                selected_col = st.selectbox(
                    "Select categorical column",
                    categorical_cols,
                    key=f"cat_select_{self.filter_id}",
                    label_visibility="collapsed"
                )
                if selected_col:
                    self._render_categorical_filter(selected_col)
            else:
                st.info("🎯 No categorical columns available")

        with filter_tabs[2]:
            if date_cols:
                selected_col = st.selectbox(
                    "Select date column",
                    date_cols,
                    key=f"date_select_{self.filter_id}",
                    label_visibility="collapsed"
                )
                if selected_col:
                    self._render_date_filter(selected_col)
            else:
                st.info("🎯 No date columns available")

        with filter_tabs[3]:
            if other_cols:
                selected_col = st.selectbox(
                    "Select other column",
                    other_cols,
                    key=f"other_select_{self.filter_id}",
                    label_visibility="collapsed"
                )
                if selected_col:
                    self._render_text_filter(selected_col)
            else:
                st.info("🎯 No other columns available")

        if len(st.session_state.filter_state['filters']) > 1:
            st.markdown("---")
            self._render_logic_mode()

        self._render_active_filters()

    def _render_filter_suggestions(self):
        """Show intelligent filter suggestions."""
        with st.container(border=True):
            st.markdown("💡 **Quick Filter Suggestions**")
            suggestions = []

            numeric_cols = self.df.select_dtypes(include=[np.number]).columns
            for col in list(numeric_cols)[:3]:
                try:
                    col_range = self.df[col].max() - self.df[col].min()
                    if col_range > 0:
                        suggestions.append(f"Filter **{col}** by range")
                except:
                    pass

            cat_cols = self.df.select_dtypes(include=['object', 'category']).columns
            for col in list(cat_cols)[:2]:
                try:
                    unique_count = self.df[col].nunique()
                    if 2 <= unique_count <= 10:
                        suggestions.append(f"Select values for **{col}**")
                except:
                    pass

            if suggestions:
                for suggestion in suggestions[:3]:
                    st.caption(f"• {suggestion}")
            else:
                st.caption("Add filters using the controls above")

    def _render_logic_mode(self):
        """Render logic mode selector for multiple filters."""
        st.markdown("**Filter Logic**")
        col1, col2 = st.columns([2, 1])

        with col1:
            logic_mode = st.radio(
                "Combine filters using:",
                ["AND (all filters must match)", "OR (any filter can match)"],
                index=0,
                horizontal=True,
                key=f"logic_mode_{self.filter_id}"
            )
            st.session_state.filter_state['logic_mode'] = "AND" if "AND" in logic_mode else "OR"

        with col2:
            if st.button("🔀 Group Filters", key=f"group_{self.filter_id}", use_container_width=True):
                self._create_logic_group()

    def _create_logic_group(self):
        """Create logic group for complex filtering."""
        active_filters = list(st.session_state.filter_state['filters'].keys())
        if len(active_filters) >= 2:
            with st.popover("📦 Create Filter Group"):
                selected = st.multiselect(
                    "Select filters to group:",
                    active_filters,
                    default=active_filters[:2],
                    key=f"group_select_{self.filter_id}"
                )
                if selected and st.button("✅ Create Group", key=f"create_group_{self.filter_id}"):
                    if 'logic_groups' not in st.session_state.filter_state:
                        st.session_state.filter_state['logic_groups'] = []
                    st.session_state.filter_state['logic_groups'].append(selected)
                    st.success(f"Created group with {len(selected)} filters")
                    st.rerun()

    def _render_numeric_filter(self, column: str):
        """Render enhanced numeric filter controls."""
        try:
            col_min, col_max = float(self.df[column].min()), float(self.df[column].max())
            col_mean = float(self.df[column].mean())

            with st.container(border=True):
                st.markdown(f"##### 📊 {column}")
                col_stat1, col_stat2, col_stat3 = st.columns(3)
                with col_stat1:
                    st.caption(f"Min: {col_min:.2f}")
                with col_stat2:
                    st.caption(f"Max: {col_max:.2f}")
                with col_stat3:
                    st.caption(f"Mean: {col_mean:.2f}")

                filter_type = st.radio(
                    "Filter type:",
                    ["Range", "Greater than", "Less than", "Outliers"],
                    horizontal=True,
                    key=f"num_type_{column}_{self.filter_id}"
                )

                if filter_type == "Range":
                    current_min, current_max = st.slider(
                        f"Select range for {column}",
                        col_min,
                        col_max,
                        (col_min, col_max),
                        key=f"range_{column}_{self.filter_id}"
                    )
                    if current_min > col_min or current_max < col_max:
                        st.session_state.filter_state['filters'][column] = {
                            'type': 'range',
                            'min': current_min,
                            'max': current_max
                        }
                    elif column in st.session_state.filter_state['filters']:
                        del st.session_state.filter_state['filters'][column]

                elif filter_type == "Greater than":
                    threshold = st.number_input(
                        "Greater than:",
                        col_min,
                        col_max,
                        col_mean,
                        key=f"gt_{column}_{self.filter_id}"
                    )
                    if threshold > col_min:
                        st.session_state.filter_state['filters'][column] = {
                            'type': 'gt',
                            'value': threshold
                        }
                    elif column in st.session_state.filter_state['filters']:
                        del st.session_state.filter_state['filters'][column]

                elif filter_type == "Less than":
                    threshold = st.number_input(
                        "Less than:",
                        col_min,
                        col_max,
                        col_mean,
                        key=f"lt_{column}_{self.filter_id}"
                    )
                    if threshold < col_max:
                        st.session_state.filter_state['filters'][column] = {
                            'type': 'lt',
                            'value': threshold
                        }
                    elif column in st.session_state.filter_state['filters']:
                        del st.session_state.filter_state['filters'][column]

                elif filter_type == "Outliers":
                    Q1 = self.df[column].quantile(0.25)
                    Q3 = self.df[column].quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR

                    st.info(f"Outlier bounds: [{lower_bound:.2f}, {upper_bound:.2f}]")
                    action = st.radio(
                        "Handle outliers:",
                        ["Exclude outliers", "Keep outliers only", "No action"],
                        key=f"outlier_{column}_{self.filter_id}"
                    )
                    if action == "Exclude outliers":
                        st.session_state.filter_state['filters'][column] = {
                            'type': 'range',
                            'min': float(lower_bound),
                            'max': float(upper_bound)
                        }
                    elif action == "Keep outliers only":
                        st.session_state.filter_state['filters'][column] = {
                            'type': 'or',
                            'conditions': [
                                {'type': 'lt', 'value': float(lower_bound)},
                                {'type': 'gt', 'value': float(upper_bound)}
                            ]
                        }
                    elif column in st.session_state.filter_state['filters']:
                        del st.session_state.filter_state['filters'][column]

                self._render_null_handling(column)
        except Exception as e:
            st.error(f"❌ Could not create filter for '{column}': {str(e)[:50]}")

    def _render_categorical_filter(self, column: str):
        """Render enhanced categorical filter controls."""
        try:
            unique_vals = self.df[column].dropna().unique()
            value_counts = self.df[column].value_counts()

            with st.container(border=True):
                st.markdown(f"##### 🏷️ {column}")
                col_stat1, col_stat2 = st.columns(2)
                with col_stat1:
                    st.caption(f"Unique: {len(unique_vals)}")
                with col_stat2:
                    top_value = value_counts.index[0] if len(value_counts) > 0 else "N/A"
                    st.caption(f"Top: {str(top_value)[:20]}")

                search_term = st.text_input(
                    "Search values:",
                    placeholder="Type to filter...",
                    key=f"search_{column}_{self.filter_id}"
                )

                display_vals = unique_vals
                if search_term:
                    display_vals = [val for val in unique_vals if search_term.lower() in str(val).lower()]

                if len(display_vals) > 50:
                    st.warning(f"Showing first 50 of {len(display_vals)} matching values")
                    display_vals = display_vals[:50]

                col_sel1, col_sel2 = st.columns([4, 1])
                with col_sel1:
                    selected_vals = st.multiselect(
                        "Select values to include:",
                        sorted(display_vals),
                        key=f"cat_{column}_{self.filter_id}"
                    )
                with col_sel2:
                    st.write("")
                    st.write("")
                    if st.button("✓ All", key=f"select_all_{column}_{self.filter_id}", use_container_width=True):
                        selected_vals = list(display_vals)
                        st.rerun()

                if selected_vals:
                    st.session_state.filter_state['filters'][column] = {
                        'type': 'categorical',
                        'values': selected_vals
                    }
                    st.caption(f"Selected: {len(selected_vals)} value(s)")
                elif column in st.session_state.filter_state['filters']:
                    del st.session_state.filter_state['filters'][column]

                self._render_null_handling(column)
        except Exception as e:
            st.error(f"❌ Could not create filter for '{column}': {str(e)[:50]}")

    def _render_date_filter(self, column: str):
        """Render enhanced date filter controls."""
        try:
            min_date = self.df[column].min().date()
            max_date = self.df[column].max().date()

            with st.container(border=True):
                st.markdown(f"##### 📅 {column}")
                st.caption(f"Range: {min_date} to {max_date}")

                date_range = st.date_input(
                    "Select date range:",
                    [min_date, max_date],
                    min_date,
                    max_date,
                    key=f"date_{column}_{self.filter_id}"
                )

                if len(date_range) == 2:
                    start_date, end_date = date_range

                    preset = st.selectbox(
                        "Quick presets:",
                        ["Custom", "Last 7 days", "Last 30 days", "Last 90 days", "Year to date", "Last year"],
                        key=f"date_preset_{column}_{self.filter_id}"
                    )

                    if preset != "Custom":
                        today = datetime.now().date()
                        if preset == "Last 7 days":
                            start_date = today - timedelta(days=7)
                        elif preset == "Last 30 days":
                            start_date = today - timedelta(days=30)
                        elif preset == "Last 90 days":
                            start_date = today - timedelta(days=90)
                        elif preset == "Year to date":
                            start_date = datetime(today.year, 1, 1).date()
                        elif preset == "Last year":
                            start_date = datetime(today.year - 1, 1, 1).date()
                            end_date = datetime(today.year - 1, 12, 31).date()

                    if start_date != min_date or end_date != max_date:
                        st.session_state.filter_state['filters'][column] = {
                            'type': 'date_range',
                            'start': pd.to_datetime(start_date),
                            'end': pd.to_datetime(end_date)
                        }
                        st.caption(f"Selected: {start_date} to {end_date}")
                    elif column in st.session_state.filter_state['filters']:
                        del st.session_state.filter_state['filters'][column]

                self._render_null_handling(column)
        except Exception as e:
            st.error(f"❌ Could not create filter for '{column}': {str(e)[:50]}")

    def _render_text_filter(self, column: str):
        """Render enhanced text filter controls."""
        try:
            with st.container(border=True):
                st.markdown(f"##### 📝 {column}")

                search_type = st.radio(
                    "Search type:",
                    ["Contains", "Starts with", "Ends with", "Exact match", "Regex"],
                    horizontal=True,
                    key=f"text_type_{column}_{self.filter_id}"
                )

                search_text = st.text_input(
                    "Search text:",
                    placeholder="Enter search text...",
                    key=f"text_{column}_{self.filter_id}"
                )

                case_sensitive = st.checkbox(
                    "Case sensitive",
                    value=False,
                    key=f"case_{column}_{self.filter_id}"
                )

                if search_text.strip():
                    if search_type == "Starts with":
                        pattern = f"^{re.escape(search_text)}"
                        use_regex = True
                    elif search_type == "Ends with":
                        pattern = f"{re.escape(search_text)}$"
                        use_regex = True
                    elif search_type == "Exact match":
                        pattern = f"^{re.escape(search_text)}$"
                        use_regex = True
                    elif search_type == "Regex":
                        pattern = search_text
                        use_regex = True
                    else:  # Contains
                        pattern = re.escape(search_text)
                        use_regex = False

                    st.session_state.filter_state['filters'][column] = {
                        'type': 'text',
                        'search': search_text.strip(),
                        'pattern': pattern,
                        'search_type': search_type,
                        'case_sensitive': case_sensitive,
                        'use_regex': use_regex
                    }

                    try:
                        if use_regex:
                            matches = self.df[column].astype(str).str.contains(pattern, case=case_sensitive, regex=True).sum()
                        else:
                            matches = self.df[column].astype(str).str.contains(search_text, case=case_sensitive).sum()
                        st.caption(f"Matches: {matches:,} rows")
                    except:
                        pass
                elif column in st.session_state.filter_state['filters']:
                    del st.session_state.filter_state['filters'][column]

                self._render_null_handling(column)
        except Exception as e:
            st.error(f"❌ Could not create filter for '{column}': {str(e)[:50]}")

    def _render_null_handling(self, column: str):
        """Render enhanced null handling options."""
        try:
            null_count = self.df[column].isna().sum()
            if null_count > 0:
                with st.expander(f"⚡ Null Values ({null_count:,} rows)", expanded=False):
                    option = st.radio(
                        f"How to handle null values in {column}?",
                        ["❌ Exclude nulls", "✅ Include nulls", "📊 Treat as separate category"],
                        key=f"null_{column}_{self.filter_id}"
                    )
                    if "Exclude" in option:
                        st.session_state.filter_state['null_handling'][column] = 'exclude'
                    elif "Include" in option:
                        st.session_state.filter_state['null_handling'][column] = 'include'
                    else:
                        st.session_state.filter_state['null_handling'][column] = 'separate'
                    st.caption(f"{null_count:,} null values will be {option.split()[-1].lower()}")
        except:
            pass

    def _render_active_filters(self):
        """Display enhanced active filters panel."""
        active_filters = st.session_state.filter_state.get('filters', {})
        if not active_filters:
            return

        st.markdown("---")
        st.markdown("#### ✅ Active Filters")

        for i, (col, filter_def) in enumerate(active_filters.items()):
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 2, 1])

                with col1:
                    icon = "📊" if filter_def.get('type') in ['range', 'gt', 'lt'] else \
                           "🏷️" if filter_def.get('type') == 'categorical' else \
                           "📅" if filter_def.get('type') == 'date_range' else \
                           "📝"
                    st.markdown(f"{icon} **{col}**")
                    desc = self._get_filter_description(col, filter_def)
                    st.caption(desc)

                    null_handling = st.session_state.filter_state['null_handling'].get(col, 'exclude')
                    null_count = self.df[col].isna().sum() if col in self.df.columns else 0
                    if null_count > 0:
                        null_text = "excluded" if null_handling == 'exclude' else \
                                   "included" if null_handling == 'include' else \
                                   "separate category"
                        st.caption(f"Nulls: {null_count:,} {null_text}")

                with col2:
                    filtered_count = self._count_filtered_rows(col, filter_def)
                    total_count = len(self.df)
                    impact_pct = (filtered_count / total_count * 100) if total_count > 0 else 0
                    st.metric(
                        "Impact",
                        f"{impact_pct:.0f}%",
                        delta=f"{filtered_count:,} rows",
                        delta_color="normal" if impact_pct > 50 else "off"
                    )

                with col3:
                    remove_key = f"remove_{col}_{self.filter_id}_{i}"
                    if st.button("🗑️", key=remove_key, help="Remove this filter"):
                        if st.session_state.get(f"confirm_{remove_key}", False):
                            del st.session_state.filter_state['filters'][col]
                            if col in st.session_state.filter_state['null_handling']:
                                del st.session_state.filter_state['null_handling'][col]
                            st.rerun()
                        else:
                            st.session_state[f"confirm_{remove_key}"] = True
                            st.rerun()
                    if st.session_state.get(f"confirm_{remove_key}", False):
                        st.caption("Click again to confirm")

    def _get_filter_description(self, column: str, filter_def: Dict) -> str:
        """Get human-readable filter description."""
        if filter_def.get('type') == 'range':
            return f"Range: {filter_def.get('min', ''):.2f} to {filter_def.get('max', ''):.2f}"
        elif filter_def.get('type') == 'gt':
            return f"Greater than: {filter_def.get('value', ''):.2f}"
        elif filter_def.get('type') == 'lt':
            return f"Less than: {filter_def.get('value', ''):.2f}"
        elif filter_def.get('type') == 'categorical':
            values = filter_def.get('values', [])
            if len(values) <= 3:
                return f"Values: {', '.join(map(str, values))}"
            else:
                return f"{len(values)} values selected"
        elif filter_def.get('type') == 'date_range':
            start = filter_def.get('start', '')
            end = filter_def.get('end', '')
            if hasattr(start, 'strftime'):
                start = start.strftime('%Y-%m-%d')
            if hasattr(end, 'strftime'):
                end = end.strftime('%Y-%m-%d')
            return f"Date range: {start} to {end}"
        elif filter_def.get('type') == 'text':
            search_type = filter_def.get('search_type', 'Contains')
            return f"{search_type}: '{filter_def.get('search', '')}'"
        return "Custom filter"

    def _count_filtered_rows(self, column: str, filter_def: Dict) -> int:
        """Count rows affected by a specific filter."""
        try:
            if column not in self.df.columns:
                return 0

            # Use DataService's filter mask logic but we need to compute count
            # We'll just call the service with the filter state for this single filter
            # but that's inefficient; we can compute mask directly here.
            # For simplicity, we'll use a direct implementation similar to _get_filter_mask.
            # We'll copy the logic from DataService but we can't call it directly because it expects full filter_state.
            # To avoid duplication, we'll compute mask manually.
            filter_def_copy = filter_def.copy()
            mask = self._get_filter_mask_for_count(column, filter_def_copy)
            return mask.sum()
        except:
            return 0

    def _get_filter_mask_for_count(self, col: str, filter_def: Dict) -> pd.Series:
        """Simplified mask for counting (copied from DataService)."""
        filter_type = filter_def.get('type')
        if filter_type == 'range':
            return (self.df[col] >= filter_def['min']) & (self.df[col] <= filter_def['max'])
        elif filter_type == 'gt':
            return self.df[col] > filter_def['value']
        elif filter_type == 'lt':
            return self.df[col] < filter_def['value']
        elif filter_type == 'categorical':
            return self.df[col].isin(filter_def['values'])
        elif filter_type == 'date_range':
            return (self.df[col] >= filter_def['start']) & (self.df[col] <= filter_def['end'])
        elif filter_type == 'text':
            search = filter_def.get('search', '')
            case_sensitive = filter_def.get('case_sensitive', False)
            use_regex = filter_def.get('use_regex', False)
            if use_regex:
                pattern = filter_def.get('pattern', search)
                return self.df[col].astype(str).str.contains(pattern, case=case_sensitive, regex=True, na=False)
            else:
                return self.df[col].astype(str).str.contains(search, case=case_sensitive, na=False)
        elif filter_type == 'or':
            conditions = filter_def.get('conditions', [])
            mask = pd.Series(False, index=self.df.index)
            for cond in conditions:
                if cond.get('type') == 'gt':
                    mask = mask | (self.df[col] > cond['value'])
                elif cond.get('type') == 'lt':
                    mask = mask | (self.df[col] < cond['value'])
            return mask
        return pd.Series(True, index=self.df.index)

    def _render_filter_summary(self):
        """Render enhanced filter impact summary panel."""
        st.markdown("#### 📊 Filter Impact Summary")

        filtered_df = self._apply_filters_to_data()

        if filtered_df is None:
            st.info("No data available")
            return

        original_rows = len(self.df)
        filtered_rows = len(filtered_df)

        if original_rows == 0:
            st.warning("Empty dataset")
            return

        removed_rows = original_rows - filtered_rows
        remaining_pct = (filtered_rows / original_rows * 100)

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Original", f"{original_rows:,}", delta="Total rows", delta_color="off")
        with col2:
            delta_color = "inverse" if removed_rows > 0 else "off"
            st.metric("Filtered", f"{filtered_rows:,}", delta=f"-{removed_rows:,} rows", delta_color=delta_color)

        progress_value = remaining_pct / 100
        if remaining_pct < 10:
            progress_color = "#ef4444"
            message = "⚠️ **Heavy filtering** - only 10% of data remains"
        elif remaining_pct < 30:
            progress_color = "#f59e0b"
            message = "⚠️ **Significant filtering** - 30% of data remains"
        elif remaining_pct < 70:
            progress_color = "#3b82f6"
            message = "ℹ️ **Moderate filtering**"
        else:
            progress_color = "#10b981"
            message = "✅ **Light filtering**"

        st.markdown(f"""
        <div style="background-color: #f3f4f6; border-radius: 8px; padding: 2px; margin: 8px 0;">
            <div style="background-color: {progress_color}; width: {progress_value*100}%;
                     height: 20px; border-radius: 6px; transition: width 0.3s;">
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_pct1, col_pct2, col_pct3 = st.columns(3)
        with col_pct1:
            st.caption(f"**{remaining_pct:.1f}%** remaining")
        with col_pct2:
            st.caption(f"**{(100-remaining_pct):.1f}%** removed")
        with col_pct3:
            st.caption(f"**{removed_rows:,}** rows")

        with st.container(border=True):
            st.markdown(message)
            if remaining_pct < 5:
                st.caption("💡 Consider relaxing filters to preserve more data")
            elif remaining_pct > 95:
                st.caption("💡 Filters have minimal impact on dataset size")

        try:
            original_memory = self.df.memory_usage(deep=True).sum() / (1024 ** 2)
            filtered_memory = filtered_df.memory_usage(deep=True).sum() / (1024 ** 2)
            memory_saved = original_memory - filtered_memory
            memory_pct = (memory_saved / original_memory * 100) if original_memory > 0 else 0
            if memory_saved > 1:
                st.caption(f"💾 Memory saved: {memory_saved:.1f} MB ({memory_pct:.0f}%)")
        except:
            pass

    def _render_actions(self):
        """Render enhanced action buttons."""
        st.markdown("---")

        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

        with col1:
            apply_disabled = st.session_state.live_update_mode
            apply_label = "✅ Applied (Live Mode)" if apply_disabled else "✅ Apply Filters"
            if st.button(
                apply_label,
                use_container_width=True,
                type="primary",
                disabled=apply_disabled,
                key=f"apply_main_{self.filter_id}"
            ):
                self._save_and_apply()
                st.balloons()

        # Export is inside popover
        with col2:
            if st.button("📥 Export", use_container_width=True, type="secondary"):
                filtered_df = self._apply_filters_to_data()
                if filtered_df is not None:
                    self._render_export_menu(filtered_df)

    def _render_export_menu(self, filtered_df: pd.DataFrame):
        """Render enhanced export menu."""
        with st.popover("📥 Export Options", use_container_width=True):
            csv_data = filtered_df.to_csv(index=False)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            st.download_button(
                "💾 Download CSV",
                csv_data,
                f"filtered_data_{timestamp}.csv",
                "text/csv",
                use_container_width=True,
                key=f"download_csv_{self.filter_id}"
            )

            json_data = filtered_df.to_json(orient='records', indent=2)
            st.download_button(
                "📄 Download JSON",
                json_data,
                f"filtered_data_{timestamp}.json",
                "application/json",
                use_container_width=True,
                key=f"download_json_{self.filter_id}"
            )

            st.markdown("---")
            if st.button("📋 Copy Preview", use_container_width=True, key=f"copy_preview_{self.filter_id}"):
                preview_text = filtered_df.head(10).to_string()
                st.code(preview_text[:500] + "..." if len(preview_text) > 500 else preview_text)
                st.success("Preview ready for copying")

    def _apply_filters_to_data(self) -> Optional[pd.DataFrame]:
        """Apply current filters using DataService."""
        if not st.session_state.filter_state.get('filters', {}):
            return self.df.copy()

        data_service = _get_data_service()
        try:
            return data_service.apply_filters(
                self.df,
                st.session_state.filter_state
            )
        except Exception as e:
            st.error(f"❌ Error applying filters: {str(e)[:80]}")
            return self.df

    def _auto_apply_filters(self, filtered_df: pd.DataFrame):
        """Auto-apply filters in live update mode."""
        if filtered_df is not None and st.session_state.live_update_mode:
            try:
                if st.session_state.dataset is not None and not filtered_df.equals(st.session_state.dataset):
                    st.session_state.dataset = filtered_df.copy()
                    st.rerun()
            except:
                st.session_state.dataset = filtered_df.copy()
                st.rerun()

    def _save_and_apply(self):
        """Save current filters and apply them."""
        if st.session_state.filter_state['filters']:
            if 'filter_history' not in st.session_state:
                st.session_state.filter_history = []
            if len(st.session_state.filter_history) > 10:
                st.session_state.filter_history = st.session_state.filter_history[-10:]
            st.session_state.filter_history.append(deepcopy(st.session_state.filter_state))

        st.session_state.filter_state['last_update'] = time.time()
        st.session_state.filter_state['applied'] = True

        filtered_df = self._apply_filters_to_data()
        if filtered_df is not None:
            st.session_state.dataset = filtered_df.copy()
            original_rows = len(self.df)
            filtered_rows = len(filtered_df)
            removed_pct = ((original_rows - filtered_rows) / original_rows * 100) if original_rows > 0 else 0
            if removed_pct > 0:
                st.success(f"✅ Filters applied - {filtered_rows:,} rows ({removed_pct:.1f}% removed)")
            else:
                st.success("✅ Filters applied")
            st.rerun()

    def _reset_to_default(self):
        """Reset filter state to default."""
        st.session_state.filter_state = {
            'filters': {},
            'null_handling': {},
            'logic_mode': "AND",
            'logic_groups': [],
            'applied': True,
            'last_update': time.time(),
            'version': 1.0
        }


# ─── MAIN ENTRY POINT ────────────────────────────────────────────────────

def render_filter_panel() -> Optional[pd.DataFrame]:
    """
    Enhanced single entry point for all filtering.
    Returns filtered DataFrame or None.
    """
    try:
        if ('dataset' not in st.session_state or
            st.session_state.dataset is None or
            st.session_state.dataset.empty):
            st.info("📭 No dataset loaded. Please load data first.")
            return None

        if (st.session_state.base_dataset is None and
            st.session_state.original_dataset is not None):
            st.session_state.base_dataset = st.session_state.original_dataset.copy()

        base_df = st.session_state.base_dataset

        if base_df is None or base_df.empty:
            st.warning("⚠️ The dataset is empty. No filtering available.")
            return base_df

        if 'filter_state' not in st.session_state:
            st.session_state.filter_state = {
                'filters': {},
                'null_handling': {},
                'logic_mode': "AND",
                'logic_groups': [],
                'applied': True,
                'last_update': time.time(),
                'version': 1.0
            }

        if 'live_update_mode' not in st.session_state:
            st.session_state.live_update_mode = True

        filter_ui = ProfessionalFilterUI(base_df)
        filtered_data = filter_ui.render()

        if (st.session_state.live_update_mode and
            filtered_data is not None and
            not filtered_data.empty and
            'dataset' in st.session_state):
            try:
                if st.session_state.dataset is not None:
                    current_hash = hash(str(st.session_state.dataset.head(10).to_dict()))
                    filtered_hash = hash(str(filtered_data.head(10).to_dict()))
                    if current_hash != filtered_hash:
                        st.session_state.dataset = filtered_data.copy()
                        st.rerun()
            except:
                pass

        return filtered_data

    except Exception as e:
        st.error(f"❌ Filter panel error: {str(e)[:80]}")
        return st.session_state.base_dataset if 'base_dataset' in st.session_state else None


# ─── INITIALIZATION HELPERS ──────────────────────────────────────────────

def initialize_data_state():
    """Enhanced data-related session state initialization."""
    defaults = {
        'dataset': None,
        'original_dataset': None,
        'base_dataset': None,
        'dataset_metadata': None,
        'filter_state': {
            'filters': {},
            'null_handling': {},
            'logic_mode': "AND",
            'logic_groups': [],
            'applied': True,
            'last_update': time.time(),
            'version': 1.0
        },
        'live_update_mode': True,
        'filter_history': [],
        'import_config': {},
        'sampling_metadata': {},
        'sampling_report': None,
        'data_quality_report': None,
        'last_data_refresh': None,
        'dataset_signature': None,
        'dataset_loading_time': None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = deepcopy(value)
        elif key == 'filter_state':
            current = st.session_state[key]
            for subkey, subvalue in defaults[key].items():
                if subkey not in current:
                    current[subkey] = subvalue


# ─── EXPORTS ──────────────────────────────────────────────────────────────

__all__ = [
    'DatasetManager',
    'ProfessionalFilterUI',
    'ImportConfigManager',
    'render_filter_panel',
    'initialize_data_state',
    'get_data_summary',
    'render_data_status',
    'quick_data_actions',
    'get_column_types',
    'validate_dataset',
    'safe_render',
    'quick_validate_dataframe'
]