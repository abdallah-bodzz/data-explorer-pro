# data_connectors.py
"""
Enhanced Data Source Connector for Data Explorer Pro
Professional dataset discovery with instant loading
Now with REAL database connectors (not fake data)
"""

import streamlit as st
import pandas as pd
import numpy as np
import time
import json
import re
import requests
import traceback
from typing import Tuple, Optional, Dict, List, Any
from urllib.parse import urlparse, urljoin
import warnings
from datetime import datetime, timedelta
import io
import base64
import tempfile
import os
import sys

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

# Connection timeout settings
DEFAULT_TIMEOUT = 30
MAX_ROWS_LIMIT = 50000

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def safe_execute(func, error_message="Operation failed", *args, **kwargs):
    """Execute function safely with error handling"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        st.error(f"❌ {error_message}: {str(e)[:150]}")
        if st.session_state.get('debug_mode', False):
            with st.expander("🔧 Technical Details"):
                st.code(traceback.format_exc())
        return None

def format_bytes(size_bytes):
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def validate_url(url: str) -> Tuple[bool, str]:
    """Validate URL format"""
    if not url.startswith(('http://', 'https://')):
        return False, "URL must start with http:// or https://"
    
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            return False, "Invalid URL format"
        return True, "Valid URL"
    except:
        return False, "Invalid URL format"

# ============================================================================
# DEPENDENCY CHECKER & GRACEFUL FALLBACKS
# ============================================================================

class DependencyManager:
    """Manage optional dependencies with graceful fallbacks"""
    
    @staticmethod
    def check_dependency(name: str, package_name: str = None, install_cmd: str = None) -> Dict:
        """Check if a dependency is available"""
        package_name = package_name or name
        
        result = {
            'name': name,
            'available': False,
            'package': package_name,
            'install_cmd': install_cmd or f"pip install {package_name}",
            'error': None,
            'version': None
        }
        
        try:
            if name == 'sqlalchemy':
                import sqlalchemy
                result['available'] = True
                result['version'] = sqlalchemy.__version__
            elif name == 'pymongo':
                import pymongo
                result['available'] = True
                result['version'] = pymongo.__version__
            elif name == 'snowflake':
                import snowflake.connector
                result['available'] = True
                result['version'] = snowflake.connector.__version__
            elif name == 'bigquery':
                from google.cloud import bigquery
                result['available'] = True
                result['version'] = bigquery.__version__
            elif name == 'mysql':
                import mysql.connector
                result['available'] = True
                result['version'] = mysql.connector.__version__
            elif name == 'postgresql':
                import psycopg2
                result['available'] = True
                result['version'] = psycopg2.__version__.split()[0]
            elif name == 'sqlserver':
                import pyodbc
                result['available'] = True
                result['version'] = pyodbc.version
            elif name == 'gspread':
                import gspread
                result['available'] = True
                result['version'] = gspread.__version__
            else:
                # Try generic import
                __import__(name)
                result['available'] = True
        except ImportError as e:
            result['error'] = str(e)
        except Exception as e:
            result['error'] = f"Import error: {str(e)}"
        
        return result
    
    @staticmethod
    def render_dependency_status(dep: Dict, compact: bool = False):
        """Render dependency status badge"""
        if dep['available']:
            if compact:
                return f"✅ {dep['name']}"
            else:
                st.success(f"✅ {dep['name']} {dep.get('version', '')}".strip())
                return 'real'
        else:
            if compact:
                return f"⚠️ {dep['name']}"
            else:
                with st.container(border=True):
                    st.warning(f"⚠️ {dep['name']} not installed")
                    st.code(dep['install_cmd'], language="bash")
                    
                    # Show use sample button
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        if st.button(f"Use sample data", 
                                    key=f"sample_{dep['name']}",
                                    use_container_width=True):
                            return 'sample'
                    with col2:
                        if st.button("Try anyway", key=f"try_{dep['name']}",
                                    use_container_width=True, type="secondary"):
                            return 'try_anyway'
                return 'missing'
    
    @staticmethod
    def get_available_connectors() -> Dict[str, List[str]]:
        """Get list of available and unavailable connectors"""
        connectors = {
            'sqlite': {'package': None, 'builtin': True},
            'postgresql': {'package': 'psycopg2-binary'},
            'mysql': {'package': 'mysql-connector-python'},
            'sqlserver': {'package': 'pyodbc'},
            'mongodb': {'package': 'pymongo'},
            'snowflake': {'package': 'snowflake-connector-python'},
            'bigquery': {'package': 'google-cloud-bigquery'},
            'google_sheets': {'package': 'gspread'},
        }
        
        available = []
        unavailable = []
        
        for name, info in connectors.items():
            if info.get('builtin'):
                available.append(name)
            else:
                dep = DependencyManager.check_dependency(name, info['package'])
                if dep['available']:
                    available.append(name)
                else:
                    unavailable.append(name)
        
        return {'available': available, 'unavailable': unavailable}

# ============================================================================
# CONNECTION TESTER
# ============================================================================

class ConnectionTester:
    """Test database connections before full execution"""
    
    @staticmethod
    def test_mysql(params: Dict) -> Tuple[bool, str]:
        """Test MySQL connection"""
        try:
            import mysql.connector
            conn = mysql.connector.connect(
                host=params['host'],
                port=params['port'],
                user=params['username'],
                password=params['password'],
                database=params['database'],
                connection_timeout=5
            )
            conn.close()
            return True, "✅ Connection successful"
        except mysql.connector.Error as e:
            return False, f"❌ Connection failed: {e}"
        except Exception as e:
            return False, f"❌ Error: {str(e)[:100]}"
    
    @staticmethod
    def test_postgresql(params: Dict) -> Tuple[bool, str]:
        """Test PostgreSQL connection"""
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=params['host'],
                port=params['port'],
                user=params['username'],
                password=params['password'],
                database=params['database'],
                connect_timeout=5
            )
            conn.close()
            return True, "✅ Connection successful"
        except psycopg2.Error as e:
            return False, f"❌ Connection failed: {e}"
        except Exception as e:
            return False, f"❌ Error: {str(e)[:100]}"
    
    @staticmethod
    def test_sqlite(uploaded_file) -> Tuple[bool, str]:
        """Test SQLite file"""
        try:
            import sqlite3
            with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            
            conn = sqlite3.connect(tmp_path)
            tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn)
            conn.close()
            os.unlink(tmp_path)
            
            if tables.empty:
                return True, "✅ File opened (no tables found)"
            else:
                return True, f"✅ File opened ({len(tables)} tables found)"
        except Exception as e:
            return False, f"❌ Invalid SQLite file: {str(e)[:100]}"
    
    @staticmethod
    def render_test_button(db_type: str, params: Dict = None):
        """Render test connection button"""
        if st.button("🔍 Test Connection", key=f"test_{db_type}_{int(time.time())}", use_container_width=True, type="secondary"):
            with st.spinner("Testing connection..."):
                if db_type == 'mysql':
                    success, message = ConnectionTester.test_mysql(params)
                elif db_type == 'postgresql':
                    success, message = ConnectionTester.test_postgresql(params)
                elif db_type == 'sqlite':
                    success, message = ConnectionTester.test_sqlite(params['file'])
                else:
                    success, message = False, "Test not implemented for this database"
                
                if success:
                    st.success(message)
                else:
                    st.error(message)

# ============================================================================
# PROGRESS INDICATOR
# ============================================================================

class ProgressIndicator:
    """Show loading progress for long operations"""
    
    def __init__(self, message="Processing..."):
        self.message = message
        self.progress_bar = None
        self.status_text = None
    
    def __enter__(self):
        self.progress_bar = st.progress(0)
        self.status_text = st.empty()
        self.update(0, "Starting...")
        return self
    
    def update(self, progress: float, status: str = None):
        """Update progress bar and status"""
        if self.progress_bar:
            self.progress_bar.progress(min(1.0, max(0.0, progress)))
        if status and self.status_text:
            self.status_text.text(f"{self.message} - {status}")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.progress_bar:
            self.progress_bar.empty()
        if self.status_text:
            self.status_text.empty()

# ============================================================================
# SUCCESS MESSAGE HANDLER (GLOBAL)
# ============================================================================

class SuccessHandler:
    """Handle success messages across the application"""
    
    @staticmethod
    def show(message: str, icon: str = "✅"):
        """Show a success message and store it for display"""
        st.session_state.last_success = f"{icon} {message}"
        st.rerun()
    
    @staticmethod
    def render():
        """Render any pending success messages"""
        if 'last_success' in st.session_state and st.session_state.last_success:
            st.success(st.session_state.last_success)
            del st.session_state.last_success
    
    @staticmethod
    def show_toast(message: str, icon: str = "✅"):
        """Show a toast notification (if supported)"""
        try:
            st.toast(f"{icon} {message}", icon=icon)
        except:
            # Fallback to regular success message
            st.success(f"{icon} {message}")

# ============================================================================
# POPULAR PUBLIC DATASETS (Real-world, professionally curated)
# ============================================================================

class PopularDatasets:
    """Real-world popular datasets from GitHub and public sources"""
    
    POPULAR_DATASETS = {
        # Quick Start (Small)
        "iris": {
            "name": "🌸 Iris Flower Dataset",
            "description": "Classic dataset for classification with flower measurements",
            "source": "UCI Machine Learning",
            "url": "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv",
            "size": "150 flowers",
            "features": ["sepal_length", "sepal_width", "petal_length", "petal_width", "species"],
            "use_case": "Classification, clustering, visualization, teaching",
            "category": "Quick Start",
            "difficulty": "Beginner",
            "load_time": "< 1 second",
            "tags": ["small", "classic", "ml"]
        },
        "titanic": {
            "name": "🚢 Titanic Passengers",
            "description": "Classic ML dataset with passenger details and survival",
            "source": "Kaggle/Public",
            "url": "https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv",
            "size": "891 passengers",
            "features": ["Pclass", "Sex", "Age", "SibSp", "Parch", "Fare", "Embarked", "Survived"],
            "use_case": "Predictive modeling, survival analysis, feature engineering",
            "category": "Quick Start",
            "difficulty": "Beginner",
            "load_time": "< 1 second",
            "tags": ["small", "classic", "ml"]
        },
        
        # Business & Sales
        "superstore": {
            "name": "📦 Superstore Sales",
            "description": "Classic business dataset with orders, profits, categories",
            "source": "Curran GitHub",
            "url": "https://raw.githubusercontent.com/curran/data/master/superstore/Superstore.csv",
            "size": "9,900+ orders",
            "features": ["Order Date", "Region", "Category", "Sub-Category", "Sales", "Quantity", "Discount", "Profit"],
            "use_case": "Sales dashboards, customer segmentation, profit analysis",
            "category": "Business",
            "difficulty": "Beginner",
            "load_time": "~2 seconds",
            "tags": ["business", "sales", "profit"]
        },
        
        # Entertainment
        "netflix": {
            "name": "🎬 Netflix Movies & TV Shows",
            "description": "Netflix catalog with titles, genres, directors, and ratings",
            "source": "TidyTuesday GitHub",
            "url": "https://raw.githubusercontent.com/rfordatascience/tidytuesday/main/data/2021/2021-04-20/netflix_titles.csv",
            "size": "8,800+ titles",
            "features": ["type", "title", "director", "cast", "country", "release_year", "rating", "duration", "genre"],
            "use_case": "Content analysis, genre trends, rating distribution",
            "category": "Entertainment",
            "difficulty": "Beginner",
            "load_time": "~3 seconds",
            "tags": ["entertainment", "movies", "tv"]
        },
        
        # Real Estate
        "airbnb": {
            "name": "🏠 Airbnb Listings (NYC)",
            "description": "NYC Airbnb listings with prices, reviews, neighborhoods",
            "source": "Airbnb NYC GitHub",
            "url": "https://raw.githubusercontent.com/toronto0/airbnb/master/listings.csv",
            "size": "40,000+ listings",
            "features": ["neighbourhood", "room_type", "price", "minimum_nights", "number_of_reviews", "availability"],
            "use_case": "Pricing analysis, location optimization, review analysis",
            "category": "Real Estate",
            "difficulty": "Intermediate",
            "load_time": "~4 seconds",
            "tags": ["real estate", "pricing", "reviews"]
        },
        
        # Social Science
        "happiness": {
            "name": "😊 World Happiness Report",
            "description": "Global happiness scores with economic and social indicators",
            "source": "Our World in Data",
            "url": "https://raw.githubusercontent.com/owid/owid-datasets/master/datasets/World%20Happiness%20Report%20(2021)/World%20Happiness%20Report%20(2021).csv",
            "size": "2,000+ entries",
            "features": ["country", "year", "life_ladder", "gdp_per_capita", "social_support", "life_expectancy"],
            "use_case": "Correlation analysis, policy impact, quality of life studies",
            "category": "Social Science",
            "difficulty": "Beginner",
            "load_time": "~1 second",
            "tags": ["social", "economics", "global"]
        },
        
        # Advanced
        "imdb": {
            "name": "🎥 IMDB Movies Dataset",
            "description": "Extensive movie metadata with ratings, budgets, revenues",
            "source": "IMDB Extensive Dataset",
            "url": "https://raw.githubusercontent.com/stefanoleone992/imdb-extensive-dataset/master/IMDb%20movies.csv",
            "size": "85,000+ movies",
            "features": ["title", "year", "genre", "duration", "country", "director", "actors", "avg_vote", "budget"],
            "use_case": "Movie analysis, recommendation systems, box office prediction",
            "category": "Advanced",
            "difficulty": "Intermediate",
            "load_time": "~5 seconds",
            "tags": ["large", "entertainment", "advanced"]
        }
    }
    
    @staticmethod
    def render_interface():
        """Render popular datasets interface"""
        st.subheader("🌟 Popular Public Datasets")
        st.caption("Instant access to real-world datasets for analysis")
        
        # Quick filter chips
        col_filters = st.columns([2, 1, 1, 1])
        with col_filters[0]:
            search_term = st.text_input("🔍 Search datasets", 
                                       placeholder="movies, sales, housing...", 
                                       key="popular_search",
                                       label_visibility="collapsed")
        
        with col_filters[1]:
            if st.button("Quick Start", key="chip_quick", use_container_width=True):
                st.session_state.popular_category = "Quick Start"
        
        with col_filters[2]:
            if st.button("Business", key="chip_business", use_container_width=True):
                st.session_state.popular_category = "Business"
        
        with col_filters[3]:
            if st.button("Entertainment", key="chip_entertainment", use_container_width=True):
                st.session_state.popular_category = "Entertainment"
        
        # Category filter (sticky)
        selected_category = st.selectbox(
            "Category",
            ["All Categories", "Quick Start", "Business", "Entertainment", "Real Estate", "Social Science", "Advanced"],
            key="popular_category",
            label_visibility="collapsed"
        )
        
        # Filter datasets
        filtered_datasets = {}
        for key, dataset in PopularDatasets.POPULAR_DATASETS.items():
            category_match = (selected_category == "All Categories" or dataset['category'] == selected_category)
            search_match = not search_term or any(
                search_term.lower() in str(value).lower() 
                for value in [dataset['name'], dataset['description'], dataset['use_case']] + dataset.get('tags', [])
            )
            
            if category_match and search_match:
                filtered_datasets[key] = dataset
        
        if not filtered_datasets:
            st.info("✨ No datasets match your filters. Try different criteria.")
            return
        
        # Sort by category then name
        sorted_datasets = sorted(
            filtered_datasets.items(),
            key=lambda x: (x[1]['category'], x[1]['name'])
        )
        
        # Group by category
        categories = {}
        for key, dataset in sorted_datasets:
            cat = dataset['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append((key, dataset))
        
        # Display by category
        for category, datasets in categories.items():
            st.markdown(f"### {category}")
            
            cols = st.columns(min(2, len(datasets)))
            for idx, (dataset_key, dataset_info) in enumerate(datasets):
                with cols[idx % len(cols)]:
                    PopularDatasets._render_dataset_card(dataset_key, dataset_info)
    
    @staticmethod
    def _render_dataset_card(dataset_key: str, dataset_info: Dict):
        """Render a single dataset card"""
        with st.container(border=True):
            # Header with loading time
            col_title, col_time = st.columns([3, 1])
            with col_title:
                st.markdown(f"**{dataset_info['name']}**")
            with col_time:
                st.caption(f"⏱️ {dataset_info.get('load_time', '~2s')}")
            
            # Description
            st.caption(dataset_info['description'])
            
            # Stats row
            col_stats1, col_stats2 = st.columns(2)
            with col_stats1:
                st.caption(f"📊 {dataset_info['size']}")
            with col_stats2:
                st.caption(f"🏷️ {dataset_info['difficulty']}")
            
            # Tags
            tags = dataset_info.get('tags', [])
            if tags:
                tag_text = " ".join([f"`{tag}`" for tag in tags[:3]])
                st.caption(tag_text)
            
            # Action buttons
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("📥 Load", 
                            key=f"load_{dataset_key}",
                            use_container_width=True,
                            type="primary",
                            help=f"Load {dataset_info['name']}"):
                    PopularDatasets._load_dataset(dataset_key, dataset_info)
            
            with col_btn2:
                if st.button("👁️ Preview", 
                            key=f"preview_{dataset_key}_{int(time.time())}",
                            use_container_width=True,
                            type="secondary",
                            help=f"Preview {dataset_info['name']}"):
                    PopularDatasets._preview_dataset(dataset_info)
    
    @staticmethod
    def _load_dataset(dataset_key: str, dataset_info: Dict):
        """Load dataset immediately"""
        try:
            # Show loading state
            progress_placeholder = st.empty()
            status_placeholder = st.empty()
            
            progress_placeholder.progress(0.2)
            status_placeholder.text(f"📥 Downloading {dataset_info['name']}...")
            
            # Download with retry
            max_retries = 2
            response = None
            for attempt in range(max_retries):
                try:
                    response = requests.get(dataset_info['url'], timeout=15)
                    response.raise_for_status()
                    break
                except requests.exceptions.Timeout:
                    if attempt == max_retries - 1:
                        raise
                    status_placeholder.text(f"⏳ Retrying ({attempt + 1}/{max_retries})...")
                    time.sleep(1)
                except requests.exceptions.RequestException as e:
                    if attempt == max_retries - 1:
                        raise
                    status_placeholder.text(f"⚠️ Retrying ({attempt + 1}/{max_retries})...")
                    time.sleep(1)
            
            progress_placeholder.progress(0.6)
            status_placeholder.text("🔧 Processing...")
            
            # Parse
            if dataset_info['url'].endswith('.csv'):
                df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))
            else:
                # Try CSV as fallback
                df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))
            
            progress_placeholder.progress(0.9)
            status_placeholder.text("💾 Finalizing...")
            
            # Store in session
            st.session_state.dataset = df
            st.session_state.dataset_metadata = {
                'filename': f"{dataset_info['name'].replace(' ', '_')}.csv",
                'shape': df.shape,
                'columns': df.columns.tolist(),
                'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
                'loaded_at': time.time(),
                'source_type': 'Popular Dataset',
                'source_name': dataset_info['name'],
                'source_url': dataset_info['url']
            }
            st.session_state.original_dataset = df.copy()
            st.session_state.base_dataset = df.copy()
            
            # Reset analysis
            st.session_state.filter_state = {
                'filters': {},
                'null_handling': {},
                'logic_mode': "AND",
                'logic_groups': [],
                'applied': True,
            }
            st.session_state.filter_history = []
            st.session_state.current_chart = None
            st.session_state.chart_history = []
            
            progress_placeholder.progress(1.0)
            status_placeholder.text("✅ Complete!")
            time.sleep(0.3)
            
            progress_placeholder.empty()
            status_placeholder.empty()
            
            # Show success
            SuccessHandler.show(f"Loaded {dataset_info['name']} ({len(df):,} rows)", "📊")
            
        except requests.exceptions.Timeout:
            st.error("⏱️ Connection timeout. The dataset server might be slow.")
        except requests.exceptions.ConnectionError:
            st.error("🔌 Connection error. Check your internet connection.")
        except Exception as e:
            st.error(f"❌ Failed to load: {str(e)[:150]}")
    
    @staticmethod
    def _preview_dataset(dataset_info: Dict):
        """Show dataset preview in a modal-like expander"""
        with st.expander(f"👁️ Preview: {dataset_info['name']}", expanded=True):
            try:
                with st.spinner("Fetching preview..."):
                    response = requests.get(dataset_info['url'], timeout=10)
                    response.raise_for_status()
                    
                    if dataset_info['url'].endswith('.csv'):
                        df = pd.read_csv(io.StringIO(response.text), nrows=10)
                    else:
                        df = pd.read_csv(io.StringIO(response.text), nrows=10)
                    
                    st.markdown(f"**{dataset_info['name']}** - Preview")
                    
                    # Quick stats
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Rows", f"{dataset_info['size'].split()[0]}+")
                    with col2:
                        st.metric("Preview", "10 rows")
                    
                    st.dataframe(df, use_container_width=True)
                    
                    # Load from preview button
                    if st.button("📥 Load Full Dataset", use_container_width=True, type="primary"):
                        PopularDatasets._load_dataset(dataset_info.get('key', ''), dataset_info)
            except Exception as e:
                st.error(f"Preview failed: {str(e)[:100]}")

# ============================================================================
# WEB SOURCES (GitHub, URL, Kaggle) - FIXED VERSION
# ============================================================================

class WebSources:
    """Connect to web-based data sources - FIXED VERSION"""
    
    @staticmethod
    def render_interface():
        """Render web sources interface"""
        st.subheader("🌐 Web Data Sources")
        
        # Connection method tabs
        source_tabs = st.tabs(["🔗 Direct URL", "📂 GitHub", "📊 Kaggle"])
        
        with source_tabs[0]:
            WebSources._render_url_interface()
        
        with source_tabs[1]:
            WebSources._render_github_interface()
        
        with source_tabs[2]:
            WebSources._render_kaggle_interface()
    
    @staticmethod
    def _render_url_interface():
        """Load from direct URLs - FIXED: No buttons in forms"""
        st.caption("Load data from CSV, JSON, Excel, or TSV files via URL")
        
        # Initialize session state for URL input if not exists
        if 'url_input' not in st.session_state:
            st.session_state.url_input = ''
        
        # Quick examples section - COMPLETELY SEPARATE from the form
        st.markdown("**💡 Quick Examples**")
        example_col1, example_col2, example_col3 = st.columns(3)
        
        examples = {
            "Iris": "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv",
            "Titanic": "https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv",
            "Happiness": "https://raw.githubusercontent.com/owid/owid-datasets/master/datasets/World%20Happiness%20Report%20(2021)/World%20Happiness%20Report%20(2021).csv"
        }
        
        with example_col1:
            if st.button("🌸 Iris Dataset", 
                        use_container_width=True, 
                        key="example_iris_url",
                        help="Load Iris flower dataset"):
                st.session_state.url_input = examples["Iris"]
                st.rerun()
        
        with example_col2:
            if st.button("🚢 Titanic Dataset", 
                        use_container_width=True, 
                        key="example_titanic_url",
                        help="Load Titanic passenger dataset"):
                st.session_state.url_input = examples["Titanic"]
                st.rerun()
        
        with example_col3:
            if st.button("😊 Happiness Data", 
                        use_container_width=True, 
                        key="example_happiness_url",
                        help="Load World Happiness Report"):
                st.session_state.url_input = examples["Happiness"]
                st.rerun()
        
        st.markdown("---")
        
        # Main URL form - NO BUTTONS EXCEPT SUBMIT
        with st.form("url_form", border=True, clear_on_submit=False):
            # URL input with validation
            url = st.text_input(
                "Dataset URL *",
                value=st.session_state.get('url_input', ''),
                placeholder="https://example.com/data.csv",
                help="Must be a direct download link (not a webpage)",
                key="url_input_form_field"
            )
            
            # Store the current URL input in session state
            if url:
                st.session_state.url_input = url
            
            # URL validation (immediate feedback)
            if url:
                is_valid, message = validate_url(url)
                if not is_valid:
                    st.warning(f"⚠️ {message}")
                else:
                    st.success("✅ URL format looks good")
            
            # Advanced options in expander
            with st.expander("⚙️ Advanced Options", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    file_type = st.selectbox("File format", 
                                           ["Auto-detect", "CSV", "JSON", "Excel", "TSV", "Text"],
                                           key="url_file_type_select",
                                           help="File format (auto-detect usually works)")
                with col2:
                    encoding = st.selectbox("Encoding", 
                                          ["utf-8", "latin-1", "cp1252", "utf-16", "ascii"],
                                          key="url_encoding_select",
                                          help="Character encoding")
                
                # Headers option
                add_headers = st.checkbox("Add custom headers", value=False, key="url_add_headers_check")
                if add_headers:
                    st.markdown("**Custom Headers**")
                    hcol1, hcol2 = st.columns(2)
                    with hcol1:
                        header_key = st.text_input("Header Key", 
                                                  placeholder="Authorization",
                                                  key="url_header_key_input",
                                                  help="Header name (e.g., Authorization)")
                    with hcol2:
                        header_value = st.text_input("Header Value", 
                                                    placeholder="Bearer token", 
                                                    type="password",
                                                    key="url_header_value_input",
                                                    help="Header value")
            
            # Form submit button - THE ONLY BUTTON IN THE FORM
            submit_col1, submit_col2 = st.columns([3, 1])
            with submit_col1:
                submitted = st.form_submit_button("🌐 Fetch & Load", 
                                                 type="primary", 
                                                 use_container_width=True,
                                                 help="Load data from the provided URL")
            with submit_col2:
                if st.form_submit_button("🔄 Clear", 
                                        type="secondary", 
                                        use_container_width=True,
                                        help="Clear form"):
                    st.session_state.url_input = ''
                    st.rerun()
        
        # Handle form submission OUTSIDE the form context
        if submitted and url:
            if validate_url(url)[0]:
                # Use a spinner to show loading state
                with st.spinner("🌐 Fetching data from URL..."):
                    WebSources._load_from_url(url, 
                                            st.session_state.get('url_file_type_select', 'Auto-detect'),
                                            st.session_state.get('url_encoding_select', 'utf-8'))
            elif not url:
                st.error("❌ Please enter a URL")
            else:
                st.error("❌ Please enter a valid URL starting with http:// or https://")
    
    @staticmethod
    def _render_github_interface():
        """Load from GitHub - FIXED version"""
        st.caption("Load CSV/JSON files from GitHub repositories")
        
        # Initialize session state
        if 'github_url' not in st.session_state:
            st.session_state.github_url = ''
        if 'github_branch' not in st.session_state:
            st.session_state.github_branch = 'main'
        
        # GitHub example URLs
        st.markdown("**💡 Examples**")
        example_col1, example_col2 = st.columns(2)
        
        with example_col1:
            if st.button("📊 Sample CSV", 
                        use_container_width=True,
                        key="github_example_csv"):
                st.session_state.github_url = "https://github.com/mwaskom/seaborn-data/blob/master/iris.csv"
                st.rerun()
        
        with example_col2:
            if st.button("📈 Sample JSON", 
                        use_container_width=True,
                        key="github_example_json"):
                st.session_state.github_url = "https://github.com/vega/vega-datasets/blob/main/data/cars.json"
                st.rerun()
        
        st.markdown("---")
        
        # GitHub form - NO BUTTONS EXCEPT SUBMIT
        with st.form("github_form", border=True, clear_on_submit=False):
            repo_url = st.text_input(
                "GitHub URL *",
                value=st.session_state.get('github_url', ''),
                placeholder="https://github.com/user/repo/blob/main/data.csv",
                help="Link to the file in GitHub (not the raw link)",
                key="github_url_input"
            )
            
            # Store in session state
            if repo_url:
                st.session_state.github_url = repo_url
            
            # Auto-convert and preview
            if repo_url and 'github.com' in repo_url and '/blob/' in repo_url:
                raw_url = repo_url.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                st.success(f"✅ Will fetch from raw URL")
                with st.expander("🔗 Raw URL Preview"):
                    st.code(raw_url[:150] + "..." if len(raw_url) > 150 else raw_url)
            
            # Branch selection
            branch = st.text_input("Branch (optional)", 
                                  placeholder="main", 
                                  value=st.session_state.get('github_branch', 'main'),
                                  key="github_branch_input")
            
            st.session_state.github_branch = branch
            
            # File type hint
            if repo_url and not any(repo_url.endswith(ext) for ext in ['.csv', '.json', '.xlsx', '.xls']):
                st.warning("⚠️ Make sure the URL points to a CSV, JSON, or Excel file")
            
            # Form submit button
            submitted = st.form_submit_button("🔍 Fetch from GitHub", 
                                             type="primary", 
                                             use_container_width=True,
                                             help="Load data from GitHub")
        
        # Handle form submission
        if submitted and repo_url:
            if 'github.com' not in repo_url:
                st.error("❌ Please enter a valid GitHub URL")
            else:
                with st.spinner("🔍 Fetching from GitHub..."):
                    WebSources._load_from_github(repo_url, branch)
    
    @staticmethod
    def _render_kaggle_interface():
        """Kaggle integration - FIXED version"""
        st.caption("Access Kaggle datasets using the Kaggle API")
        
        # Setup instructions
        with st.expander("📋 Setup Instructions (First Time)", expanded=False):
            st.markdown("""
            1. **Create Kaggle account** at [kaggle.com](https://www.kaggle.com)
            2. **Go to Account Settings** → API → Create New API Token
            3. **Download `kaggle.json`** and upload it below
            4. **Search for datasets** using the search box
            """)
        
        # Kaggle JSON upload - NO FORM NEEDED HERE
        kaggle_json = st.file_uploader("Upload kaggle.json", 
                                       type=['json'], 
                                       key="kaggle_json_uploader",
                                       help="Your Kaggle API credentials")
        
        if kaggle_json:
            try:
                # Read and validate JSON
                kaggle_json.seek(0)
                credentials = json.load(kaggle_json)
                username = credentials.get('username', 'Unknown')
                
                # Store credentials in session state
                st.session_state.kaggle_credentials = credentials
                
                st.success(f"✅ Connected as: **{username}**")
                
                # Dataset search interface
                st.markdown("---")
                st.markdown("#### 🔍 Search Kaggle Datasets")
                
                # Quick search examples
                example_cols = st.columns(4)
                example_datasets = ["titanic", "housing prices", "covid-19", "sales data"]
                
                for idx, dataset in enumerate(example_datasets):
                    with example_cols[idx]:
                        if st.button(f"🔎 {dataset.title()}", 
                                    use_container_width=True,
                                    key=f"kaggle_example_{dataset}"):
                            st.session_state.kaggle_search_term = dataset
                            st.rerun()
                
                # Search input
                if 'kaggle_search_term' not in st.session_state:
                    st.session_state.kaggle_search_term = ''
                
                search_term = st.text_input("Search datasets",
                                           value=st.session_state.kaggle_search_term,
                                           placeholder="titanic, housing, covid-19, sales",
                                           key="kaggle_search_input",
                                           help="Search Kaggle dataset titles and descriptions")
                
                # Direct dataset URL input
                st.markdown("---")
                st.markdown("#### 📥 Direct Dataset Download")
                
                kaggle_url = st.text_input(
                    "Kaggle Dataset URL",
                    placeholder="https://www.kaggle.com/datasets/username/dataset-name",
                    key="kaggle_direct_url_input",
                    help="Paste the Kaggle dataset URL directly"
                )
                
                # Load button
                if kaggle_url and st.button("Try to Load from URL", 
                                           use_container_width=True, 
                                           type="primary",
                                           key="kaggle_load_url_btn"):
                    st.warning("""
                    ⚠️ Direct Kaggle downloads require API authentication. 
                    
                    **Alternative methods:**
                    1. Use the Kaggle CLI: `kaggle datasets download -d username/dataset-name`
                    2. Convert to direct CSV link (if available)
                    3. Use the sample datasets above
                    """)
                    
                    # Try to extract dataset identifier
                    if "kaggle.com/datasets/" in kaggle_url:
                        dataset_id = kaggle_url.split("datasets/")[-1].strip("/")
                        st.info(f"Dataset identifier: `{dataset_id}`")
                        
                        # Show command to download
                        st.code(f"kaggle datasets download -d {dataset_id}", language="bash")
                        
            except json.JSONDecodeError:
                st.error("❌ Invalid JSON file. Please upload a valid kaggle.json")
            except Exception as e:
                st.error(f"❌ Error processing credentials: {str(e)[:100]}")
        else:
            st.info("📁 Upload your kaggle.json file to enable Kaggle integration")
            
            # Fallback: Direct CSV from Kaggle (public datasets)
            st.markdown("---")
            st.markdown("#### 🎯 Quick Alternative: Use Public CSV")
            st.caption("Many Kaggle datasets are available as direct CSV links from GitHub")
            
            example_urls = {
                "Titanic CSV": "https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv",
                "Iris Dataset": "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv",
                "Boston Housing": "https://raw.githubusercontent.com/selva86/datasets/master/BostonHousing.csv"
            }
            
            example_cols = st.columns(3)
            for idx, (name, url) in enumerate(example_urls.items()):
                with example_cols[idx]:
                    if st.button(f"📥 {name}", 
                                use_container_width=True,
                                key=f"kaggle_fallback_{name}"):
                        st.session_state.url_input = url
                        st.rerun()
    
    @staticmethod
    def _load_from_url(url: str, file_type: str = "Auto-detect", encoding: str = "utf-8"):
        """Load dataset from URL - ENHANCED with better error handling"""
        try:
            # Show loading state with progress
            progress_placeholder = st.empty()
            status_placeholder = st.empty()
            error_placeholder = st.empty()
            
            progress_placeholder.progress(10)
            status_placeholder.text("🔍 Validating URL...")
            
            # Validate URL first
            is_valid, message = validate_url(url)
            if not is_valid:
                error_placeholder.error(f"❌ {message}")
                return
            
            progress_placeholder.progress(30)
            status_placeholder.text("🌐 Connecting to server...")
            
            # Prepare headers if specified
            headers = {}
            if st.session_state.get('url_add_headers_check'):
                header_key = st.session_state.get('url_header_key_input')
                header_value = st.session_state.get('url_header_value_input')
                if header_key and header_value:
                    headers[header_key] = header_value
            
            # Add user-agent header to avoid blocking
            if 'User-Agent' not in headers:
                headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            
            # Make request with timeout and streaming for large files
            try:
                response = requests.get(url, headers=headers, timeout=30, stream=True)
                response.raise_for_status()
            except requests.exceptions.Timeout:
                error_placeholder.error("⏱️ Connection timeout after 30 seconds. The server might be slow or unavailable.")
                return
            except requests.exceptions.ConnectionError:
                error_placeholder.error("🔌 Connection error. Please check your internet connection.")
                return
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code
                if status_code == 404:
                    error_placeholder.error("❌ File not found (404). Check the URL.")
                elif status_code == 403:
                    error_placeholder.error("❌ Access forbidden (403). The file may require authentication.")
                elif status_code == 429:
                    error_placeholder.error("❌ Too many requests (429). Please try again later.")
                else:
                    error_placeholder.error(f"❌ HTTP Error {status_code}: {e.response.reason}")
                return
            
            # Check file size
            content_length = response.headers.get('content-length')
            if content_length:
                size_bytes = int(content_length)
                if size_bytes > 100 * 1024 * 1024:  # 100MB limit
                    error_placeholder.error(f"❌ File too large ({format_bytes(size_bytes)}). Maximum size is 100MB.")
                    return
                else:
                    status_placeholder.text(f"📦 Downloading {format_bytes(size_bytes)}...")
            
            progress_placeholder.progress(60)
            status_placeholder.text("📥 Reading content...")
            
            # Read content in chunks for large files
            content = b''
            if content_length and int(content_length) > 10 * 1024 * 1024:  # > 10MB
                chunk_size = 1024 * 1024  # 1MB chunks
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        content += chunk
                        # Update progress
                        downloaded = len(content)
                        total = int(content_length)
                        progress = 60 + (downloaded / total * 30)  # 60-90%
                        progress_placeholder.progress(min(90, progress))
            else:
                content = response.content
            
            progress_placeholder.progress(90)
            status_placeholder.text("🔧 Processing data...")
            
            # Auto-detect file type if needed
            if file_type == "Auto-detect":
                file_type = WebSources._detect_file_type(url, response)
            
            # Parse content
            try:
                df = WebSources._parse_content(content, file_type, encoding)
            except pd.errors.EmptyDataError:
                error_placeholder.error("❌ The file appears to be empty or contains no data.")
                return
            except Exception as e:
                error_placeholder.error(f"❌ Failed to parse file: {str(e)[:100]}")
                return
            
            if df.empty:
                error_placeholder.error("❌ The file contains no data.")
                return
            
            progress_placeholder.progress(100)
            status_placeholder.text("✅ Success! Showing preview...")
            time.sleep(0.5)
            
            # Clear progress indicators
            progress_placeholder.empty()
            status_placeholder.empty()
            error_placeholder.empty()
            
            # Show preview and load options
            WebSources._confirm_load(df, "URL Dataset", url, source_type="web_url")
            
        except Exception as e:
            # Clean up placeholders
            if 'progress_placeholder' in locals():
                progress_placeholder.empty()
            if 'status_placeholder' in locals():
                status_placeholder.empty()
            if 'error_placeholder' in locals():
                error_placeholder.empty()
            
            st.error(f"❌ Failed to load: {str(e)[:150]}")
            
            # Show debug info if in debug mode
            if st.session_state.get('debug_mode', False):
                with st.expander("🔧 Technical Details"):
                    st.code(traceback.format_exc())
    
    @staticmethod
    def _load_from_github(repo_url: str, branch: str = "main"):
        """Load dataset from GitHub - ENHANCED"""
        try:
            # Show loading state
            with st.spinner(f"🔍 Processing GitHub URL..."):
                # Convert GitHub URL to raw URL
                if 'github.com' in repo_url and '/blob/' in repo_url:
                    raw_url = repo_url.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                    # Add branch if not in URL
                    if f"/{branch}/" not in raw_url:
                        # Insert branch after the repo name
                        parts = raw_url.split('/')
                        if len(parts) > 5:
                            parts.insert(5, branch)
                            raw_url = '/'.join(parts)
                elif 'raw.githubusercontent.com' in repo_url:
                    raw_url = repo_url
                else:
                    st.error("❌ Not a valid GitHub URL. Should be like: https://github.com/user/repo/blob/main/data.csv")
                    return
                
                # Show what we're fetching
                st.info(f"🌐 Fetching from: `{raw_url[:80]}...`")
                
                # Use the URL loading method
                WebSources._load_from_url(raw_url, source_name=f"GitHub: {repo_url.split('/')[-1]}")
                
        except Exception as e:
            st.error(f"❌ Failed to load from GitHub: {str(e)[:150]}")
    
    @staticmethod
    def _detect_file_type(url: str, response) -> str:
        """Detect file type from URL and headers - ENHANCED"""
        content_type = response.headers.get('content-type', '').lower()
        filename = url.split('/')[-1].lower() if '/' in url else ''
        
        # Check by filename extension first
        if filename.endswith('.csv'):
            return 'CSV'
        elif filename.endswith('.json'):
            return 'JSON'
        elif filename.endswith(('.xlsx', '.xls')):
            return 'Excel'
        elif filename.endswith('.tsv'):
            return 'TSV'
        elif filename.endswith('.txt'):
            return 'Text'
        elif filename.endswith('.parquet'):
            return 'Parquet'
        
        # Check by content-type header
        if 'csv' in content_type or 'text/csv' in content_type:
            return 'CSV'
        elif 'json' in content_type or 'application/json' in content_type:
            return 'JSON'
        elif 'excel' in content_type or 'spreadsheet' in content_type:
            return 'Excel'
        elif 'text/plain' in content_type:
            return 'Text'
        
        # Try to guess from content sample
        try:
            sample = response.text[:1000]
            # Check for JSON
            if sample.strip().startswith('{') or sample.strip().startswith('['):
                return 'JSON'
            # Check for CSV (comma-separated with consistent columns)
            lines = sample.split('\n')
            if len(lines) > 2:
                first_line_commas = lines[0].count(',')
                second_line_commas = lines[1].count(',')
                if first_line_commas > 0 and first_line_commas == second_line_commas:
                    return 'CSV'
            # Check for TSV
            if len(lines) > 2:
                first_line_tabs = lines[0].count('\t')
                second_line_tabs = lines[1].count('\t')
                if first_line_tabs > 0 and first_line_tabs == second_line_tabs:
                    return 'TSV'
        except:
            pass
        
        # Default fallback
        return 'CSV'
    
    @staticmethod
    def _parse_content(content: bytes, file_type: str, encoding: str) -> pd.DataFrame:
        """Parse content based on file type - FIXED with proper io module handling"""
        try:
            if file_type == 'CSV':
                # Try multiple encodings if the first fails
                try:
                    return pd.read_csv(io.StringIO(content.decode(encoding, errors='replace')))
                except UnicodeDecodeError:
                    # Try other common encodings
                    for alt_encoding in ['latin-1', 'cp1252', 'utf-16']:
                        try:
                            return pd.read_csv(io.StringIO(content.decode(alt_encoding, errors='replace')))
                        except:
                            continue
                    raise
            elif file_type == 'JSON':
                return pd.read_json(io.StringIO(content.decode(encoding, errors='replace')))
            elif file_type == 'Excel':
                return pd.read_excel(io.BytesIO(content))
            elif file_type == 'TSV':
                return pd.read_csv(io.StringIO(content.decode(encoding, errors='replace')), sep='\t')
            elif file_type == 'Text':
                # Try to parse as CSV with common delimiters
                text = content.decode(encoding, errors='replace')
                for delimiter in [',', ';', '\t', '|']:
                    try:
                        return pd.read_csv(io.StringIO(text), sep=delimiter)
                    except:
                        continue
                # If all fail, return as single column
                return pd.DataFrame({'text': text.splitlines()})
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            # Provide more helpful error message
            error_msg = f"Failed to parse {file_type} file: {str(e)[:100]}"
            if "UnicodeDecodeError" in str(e):
                error_msg += "\n💡 Try changing the encoding setting"
            elif "EmptyDataError" in str(e):
                error_msg += "\n💡 The file might be empty or have wrong format"
            raise Exception(error_msg)
    
    @staticmethod
    def _confirm_load(df: pd.DataFrame, source_name: str, source_url: str = "", source_type: str = "web"):
        """Enhanced preview and confirm loading - FIXED with proper button handling"""
        st.markdown("---")
        st.markdown(f"#### 👁️ Preview: {source_name}")
        
        # Quick stats in columns
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Rows", f"{len(df):,}")
        with col2:
            st.metric("Columns", len(df.columns))
        with col3:
            missing = df.isnull().sum().sum()
            st.metric("Missing", f"{missing:,}")
        with col4:
            try:
                memory_mb = df.memory_usage(deep=True).sum() / (1024 ** 2)
                st.metric("Memory", f"{memory_mb:.1f} MB")
            except:
                st.metric("Memory", "N/A")
        
        # Data preview with tabs
        preview_tabs = st.tabs(["📋 Data", "📊 Summary", "🔍 Details"])
        
        with preview_tabs[0]:
            st.dataframe(df.head(10), use_container_width=True)
            st.caption(f"Showing 10 of {len(df):,} rows")
        
        with preview_tabs[1]:
            # Column types summary
            num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
            
            col_type1, col_type2, col_type3 = st.columns(3)
            with col_type1:
                st.metric("Numeric", len(num_cols))
            with col_type2:
                st.metric("Categorical", len(cat_cols))
            with col_type3:
                st.metric("Date/Time", len(date_cols))
            
            # Show first few column names
            if len(df.columns) > 0:
                st.markdown("**Columns:**")
                cols_per_row = 4
                for i in range(0, min(12, len(df.columns)), cols_per_row):
                    cols = st.columns(cols_per_row)
                    for j in range(cols_per_row):
                        idx = i + j
                        if idx < len(df.columns):
                            with cols[j]:
                                col_name = df.columns[idx]
                                dtype = str(df[col_name].dtype)
                                st.caption(f"`{col_name[:15]}{'...' if len(col_name) > 15 else ''}`")
                                st.caption(f"_{dtype}_")
        
        with preview_tabs[2]:
            # Data quality quick check
            issues = []
            if df.isnull().any().any():
                null_cols = df.columns[df.isnull().any()].tolist()
                issues.append(f"Missing values in {len(null_cols)} columns")
            if df.duplicated().any():
                duplicate_count = df.duplicated().sum()
                issues.append(f"{duplicate_count:,} duplicate rows")
            if any(df[col].nunique() == 1 for col in df.columns):
                const_cols = [col for col in df.columns if df[col].nunique() == 1]
                issues.append(f"{len(const_cols)} constant columns")
            
            if issues:
                st.warning("**Potential Issues:**")
                for issue in issues:
                    st.write(f"• {issue}")
            else:
                st.success("✅ Data looks clean")
            
            # Show source info
            st.markdown("**Source Information:**")
            st.write(f"• **Type:** {source_type}")
            if source_url:
                st.write(f"• **URL:** `{source_url[:80]}{'...' if len(source_url) > 80 else ''}`")
        
        # Load button with options - STANDALONE BUTTONS (not in form)
        st.markdown("---")
        st.markdown("#### 🚀 Load into Data Explorer")
        
        col_opt1, col_opt2, col_opt3 = st.columns([2, 1, 1])
        
        # Use a unique key for each button to avoid conflicts
        button_timestamp = '1234567890'
        
        # Button 1: Load Full Dataset
        with col_opt1:
            if st.button("✅ Load Full Dataset", 
                        type="primary", 
                        use_container_width=True,
                        key=f"load_full_{button_timestamp}",
                        help=f"Load all {len(df):,} rows"):
                WebSources._finalize_load(df, source_name, source_url, source_type)
        
        # Button 2: Load Sample
        with col_opt2:
            sample_size = min(1000, len(df))
            if st.button(f"📋 Sample ({sample_size} rows)", 
                        use_container_width=True,
                        type="secondary",
                        key=f"load_sample_{button_timestamp}",
                        help=f"Load {sample_size} rows for quick testing"):
                sample_df = df.head(sample_size) if len(df) > sample_size else df
                WebSources._finalize_load(sample_df, f"{source_name} (Sample)", source_url, source_type)
        
        # Button 3: More Preview
        with col_opt3:
            if st.button("🔄 More Preview", 
                        use_container_width=True,
                        type="secondary",
                        key=f"more_preview_{button_timestamp}",
                        help="Show extended preview"):
                with st.expander("📊 Extended Preview (50 rows)", expanded=True):
                    st.dataframe(df.head(50), use_container_width=True)
                    st.caption(f"Showing 50 of {len(df):,} rows")
    
    @staticmethod
    def _finalize_load(df: pd.DataFrame, source_name: str, source_url: str, source_type: str):
        """Finalize loading data into session state - ENHANCED"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{source_name.replace(' ', '_').replace(':', '')}_{timestamp}.csv"
            
            # Store dataset in session state
            st.session_state.dataset = df
            st.session_state.dataset_metadata = {
                'filename': filename,
                'shape': df.shape,
                'columns': df.columns.tolist(),
                'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
                'loaded_at': time.time(),
                'source_type': source_type,
                'source_url': source_url,
                'source_name': source_name
            }
            st.session_state.original_dataset = df.copy()
            st.session_state.base_dataset = df.copy()
            
            # Reset analysis state
            st.session_state.filter_state = {
                'filters': {},
                'null_handling': {},
                'logic_mode': "AND",
                'logic_groups': [],
                'applied': True,
            }
            st.session_state.filter_history = []
            st.session_state.current_chart = None
            st.session_state.chart_history = []
            
            # Clear any previous success messages
            if 'last_success' in st.session_state:
                del st.session_state.last_success
            
            # Show success message with auto-dismiss
            success_msg = f"✅ Loaded {len(df):,} rows from {source_name}"
            
            # Use toast if available
            try:
                st.toast(success_msg, icon="✅")
            except:
                # Fallback to success container that will be cleared on next run
                st.success(success_msg)
            
            # Small delay to show success message
            time.sleep(0.3)
            
            # Trigger rerun to update UI
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Failed to load data: {str(e)[:150]}")

# ============================================================================
# REAL DATABASE CONNECTORS (Enhanced with testing and feedback)
# ============================================================================

class DatabaseConnectors:
    """Real database connection interfaces with enhanced UX"""
    
    @staticmethod
    def render_interface():
        """Render database connectors interface"""
        st.subheader("🗄️ Database Connections")
        
        # Show available connectors status
        connectors = DependencyManager.get_available_connectors()
        
        col_status = st.columns(4)
        status_items = [
            ("SQLite", "✅ Built-in"),
            ("PostgreSQL", "✅" if 'postgresql' in connectors['available'] else "⚠️"),
            ("MySQL", "✅" if 'mysql' in connectors['available'] else "⚠️"),
            ("SQL Server", "✅" if 'sqlserver' in connectors['available'] else "⚠️")
        ]
        
        for idx, (name, status) in enumerate(status_items):
            with col_status[idx]:
                st.caption(f"{name}: {status}")
        
        # Database type selection
        db_type = st.selectbox(
            "Select database type:",
            ["SQLite", "PostgreSQL", "MySQL", "SQL Server", "MongoDB", "Snowflake", "BigQuery"],
            key="db_type_select"
        )
        
        st.markdown("---")
        
        # Render selected connector
        if db_type == "SQLite":
            DatabaseConnectors._render_sqlite()
        elif db_type == "PostgreSQL":
            DatabaseConnectors._render_postgresql()
        elif db_type == "MySQL":
            DatabaseConnectors._render_mysql()
        elif db_type == "SQL Server":
            DatabaseConnectors._render_sql_server()
        elif db_type == "MongoDB":
            DatabaseConnectors._render_mongodb()
        elif db_type == "Snowflake":
            DatabaseConnectors._render_snowflake()
        elif db_type == "BigQuery":
            DatabaseConnectors._render_bigquery()
    
    @staticmethod
    def _render_sqlite():
        """SQLite connection - REAL"""
        st.markdown("##### 📁 SQLite Database")
        st.caption("Upload a SQLite database file (.db, .sqlite, .sqlite3)")
        
        with st.form("sqlite_form", border=True):
            uploaded_db = st.file_uploader(
                "Choose SQLite file", 
                type=['db', 'sqlite', 'sqlite3'], 
                key="sqlite_file",
                help="Upload a SQLite database file"
            )
            
            if uploaded_db:
                file_size = format_bytes(uploaded_db.size)
                st.info(f"📄 **File:** {uploaded_db.name} ({file_size})")
                
                # Quick test button
                if st.button("🔍 Test File", key="test_sqlite", type="secondary", use_container_width=True):
                    success, message = ConnectionTester.test_sqlite(uploaded_db)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
            
            query = st.text_area(
                "SQL Query *", 
                placeholder="SELECT * FROM table_name LIMIT 1000", 
                height=100,
                help="Write your SQL query here",
                key="sqlite_query"
            )
            
            # Query helper
            with st.expander("💡 Query Help", expanded=False):
                st.markdown("""
                **Common queries:**
                - `SELECT * FROM table_name` - Get all data
                - `SELECT name, value FROM table_name WHERE value > 100` - Filtered data
                - `PRAGMA table_info(table_name)` - Show table structure
                
                **Find tables:** `SELECT name FROM sqlite_master WHERE type='table';`
                """)
            
            col1, col2 = st.columns([3, 1])
            with col1:
                submitted = st.form_submit_button("🔌 Execute Query", type="primary", use_container_width=True)
            
            with col2:
                limit = st.number_input("Limit", value=1000, min_value=1, max_value=100000, 
                                       key="sqlite_limit", help="Maximum rows to fetch")
            
            if submitted and uploaded_db and query:
                if limit:
                    query = query.rstrip(';') + f" LIMIT {limit}"
                DatabaseConnectors._execute_sqlite_query({'file': uploaded_db, 'query': query})
    
    @staticmethod
    def _render_mysql():
        """MySQL connection - REAL"""
        # Check dependency
        dep = DependencyManager.check_dependency('mysql', 'mysql-connector-python')
        
        if not dep['available']:
            status = DependencyManager.render_dependency_status(dep)
            if status == 'sample':
                DatabaseConnectors._execute_mysql_sample()
            return
        
        st.markdown("##### 🐬 MySQL Connection")
        st.caption(f"Using mysql-connector-python v{dep['version']}")
        
        with st.form("mysql_form", border=True):
            # Connection details
            col1, col2 = st.columns(2)
            with col1:
                host = st.text_input("Host *", value="localhost", key="mysql_host")
                database = st.text_input("Database *", placeholder="mydatabase", key="mysql_db")
            with col2:
                port = st.number_input("Port", value=3306, min_value=1, max_value=65535, key="mysql_port")
                username = st.text_input("Username *", placeholder="root", key="mysql_user")
            
            password = st.text_input("Password *", type="password", key="mysql_pass")
            
            # Test connection button
            ConnectionTester.render_test_button('mysql', {
                'host': host, 'port': port, 'username': username, 
                'password': password, 'database': database
            })
            
            query = st.text_area(
                "SQL Query *", 
                placeholder="SELECT * FROM mytable LIMIT 1000", 
                height=100,
                key="mysql_query"
            )
            
            submitted = st.form_submit_button("🔌 Connect & Query", type="primary", use_container_width=True)
            
            if submitted and host and database and query:
                DatabaseConnectors._execute_mysql_query({
                    'host': host,
                    'database': database,
                    'username': username,
                    'password': password,
                    'port': port,
                    'query': query
                })
    
    @staticmethod
    def _render_postgresql():
        """PostgreSQL connection - REAL"""
        # Check dependency
        dep = DependencyManager.check_dependency('postgresql', 'psycopg2-binary')
        
        if not dep['available']:
            status = DependencyManager.render_dependency_status(dep)
            if status == 'sample':
                DatabaseConnectors._execute_postgresql_sample()
            return
        
        st.markdown("##### 🐘 PostgreSQL Connection")
        st.caption(f"Using psycopg2 v{dep['version']}")
        
        with st.form("postgresql_form", border=True):
            col1, col2 = st.columns(2)
            with col1:
                host = st.text_input("Host *", value="localhost", key="pg_host")
                database = st.text_input("Database *", value="postgres", key="pg_db")
            with col2:
                port = st.number_input("Port", value=5432, key="pg_port")
                username = st.text_input("Username *", value="postgres", key="pg_user")
            
            password = st.text_input("Password *", type="password", key="pg_pass")
            
            # SSL option
            ssl_mode = st.selectbox("SSL Mode", ["disable", "allow", "prefer", "require"], key="pg_ssl")
            
            # Test connection
            ConnectionTester.render_test_button('postgresql', {
                'host': host, 'port': port, 'username': username,
                'password': password, 'database': database
            })
            
            query = st.text_area(
                "SQL Query *", 
                placeholder="SELECT * FROM my_table LIMIT 1000", 
                height=100,
                key="pg_query"
            )
            
            submitted = st.form_submit_button("🔌 Connect & Query", type="primary", use_container_width=True)
            
            if submitted and host and database and query:
                DatabaseConnectors._execute_postgresql_query({
                    'host': host,
                    'database': database,
                    'username': username,
                    'password': password,
                    'port': port,
                    'query': query,
                    'ssl_mode': ssl_mode
                })
    
    @staticmethod
    def _render_sql_server():
        """SQL Server connection - REAL"""
        # Check dependency
        dep = DependencyManager.check_dependency('sqlserver', 'pyodbc')
        
        if not dep['available']:
            status = DependencyManager.render_dependency_status(dep)
            if status == 'sample':
                DatabaseConnectors._execute_sql_server_sample()
            return
        
        st.markdown("##### 🗄️ SQL Server Connection")
        st.caption(f"Using pyodbc v{dep['version']}")
        
        with st.form("sql_server_form", border=True):
            col1, col2 = st.columns(2)
            with col1:
                server = st.text_input("Server *", placeholder="localhost\\SQLEXPRESS", key="sqlsrv_server")
                database = st.text_input("Database *", placeholder="MyDatabase", key="sqlsrv_db")
            with col2:
                port = st.number_input("Port", value=1433, key="sqlsrv_port")
                username = st.text_input("Username *", placeholder="sa", key="sqlsrv_user")
            
            password = st.text_input("Password *", type="password", key="sqlsrv_pass")
            
            # Trust certificate option
            trust_cert = st.checkbox("Trust Server Certificate", value=True, key="sqlsrv_trust")
            
            query = st.text_area(
                "SQL Query *", 
                placeholder="SELECT TOP 1000 * FROM MyTable", 
                height=100,
                key="sqlsrv_query"
            )
            
            submitted = st.form_submit_button("🔌 Connect & Query", type="primary", use_container_width=True)
            
            if submitted and server and database and query:
                DatabaseConnectors._execute_sql_server_query({
                    'server': server,
                    'database': database,
                    'username': username,
                    'password': password,
                    'port': port,
                    'query': query,
                    'trust_cert': trust_cert
                })
    
    @staticmethod
    def _render_mongodb():
        """MongoDB connection - REAL"""
        # Check dependency
        dep = DependencyManager.check_dependency('pymongo')
        
        if not dep['available']:
            status = DependencyManager.render_dependency_status(dep)
            if status == 'sample':
                DatabaseConnectors._execute_mongodb_sample()
            return
        
        st.markdown("##### 🍃 MongoDB Connection")
        st.caption(f"Using pymongo v{dep['version']}")
        
        with st.form("mongodb_form", border=True):
            # Connection details
            col1, col2 = st.columns(2)
            with col1:
                host = st.text_input("Host *", value="localhost", key="mongo_host")
                database = st.text_input("Database *", placeholder="mydatabase", key="mongo_db")
            with col2:
                port = st.number_input("Port", value=27017, key="mongo_port")
                collection = st.text_input("Collection *", placeholder="mycollection", key="mongo_coll")
            
            # Authentication (optional)
            with st.expander("🔑 Authentication (optional)", expanded=False):
                username = st.text_input("Username", key="mongo_user")
                password = st.text_input("Password", type="password", key="mongo_pass")
            
            # Query options
            query_filter = st.text_area(
                "Query Filter (JSON, optional)", 
                placeholder='{"status": "active", "age": {"$gt": 18}}',
                height=80,
                help="MongoDB query filter in JSON format",
                key="mongo_filter"
            )
            
            col_limit, col_skip = st.columns(2)
            with col_limit:
                limit = st.number_input("Limit", value=1000, min_value=1, max_value=MAX_ROWS_LIMIT, key="mongo_limit")
            with col_skip:
                skip = st.number_input("Skip", value=0, min_value=0, key="mongo_skip")
            
            submitted = st.form_submit_button("🍃 Connect & Query", type="primary", use_container_width=True)
            
            if submitted and host and database and collection:
                DatabaseConnectors._execute_mongodb_query({
                    'host': host,
                    'port': port,
                    'database': database,
                    'collection': collection,
                    'username': username if username else None,
                    'password': password if password else None,
                    'query_filter': query_filter,
                    'limit': limit,
                    'skip': skip
                })
    
    @staticmethod
    def _render_snowflake():
        """Snowflake connection - REAL"""
        # Check dependency
        dep = DependencyManager.check_dependency('snowflake')
        
        if not dep['available']:
            status = DependencyManager.render_dependency_status(dep)
            if status == 'sample':
                DatabaseConnectors._execute_snowflake_sample()
            return
        
        st.markdown("##### ❄️ Snowflake Connection")
        st.caption(f"Using snowflake-connector-python v{dep.get('version', '')}")
        
        with st.form("snowflake_form", border=True):
            # Account details
            account = st.text_input(
                "Account *", 
                placeholder="myaccount.snowflakecomputing.com",
                help="Your Snowflake account identifier",
                key="sf_account"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                username = st.text_input("Username *", key="sf_user")
                database = st.text_input("Database", placeholder="MYDATABASE", key="sf_db")
            with col2:
                password = st.text_input("Password *", type="password", key="sf_pass")
                schema = st.text_input("Schema", placeholder="PUBLIC", key="sf_schema")
            
            warehouse = st.text_input("Warehouse (optional)", placeholder="COMPUTE_WH", key="sf_warehouse")
            
            query = st.text_area(
                "SQL Query *", 
                placeholder="SELECT * FROM MY_TABLE LIMIT 1000", 
                height=100,
                key="sf_query"
            )
            
            submitted = st.form_submit_button("❄️ Connect & Query", type="primary", use_container_width=True)
            
            if submitted and account and username and password and query:
                DatabaseConnectors._execute_snowflake_query({
                    'account': account,
                    'username': username,
                    'password': password,
                    'database': database,
                    'schema': schema,
                    'warehouse': warehouse,
                    'query': query
                })
    
    @staticmethod
    def _render_bigquery():
        """BigQuery connection - REAL"""
        # Check dependency
        dep = DependencyManager.check_dependency('bigquery')
        
        if not dep['available']:
            status = DependencyManager.render_dependency_status(dep)
            if status == 'sample':
                DatabaseConnectors._execute_bigquery_sample()
            return
        
        st.markdown("##### ☁️ BigQuery Connection")
        st.caption(f"Using google-cloud-bigquery v{dep.get('version', '')}")
        
        with st.form("bigquery_form", border=True):
            st.info("Upload your Google Cloud Service Account JSON file")
            
            credentials_file = st.file_uploader(
                "Service Account JSON *", 
                type=['json'], 
                key="bq_creds",
                help="Download from Google Cloud Console"
            )
            
            project_id = st.text_input(
                "Project ID *", 
                placeholder="my-project-id", 
                key="bq_project",
                help="Your Google Cloud project ID"
            )
            
            if credentials_file:
                try:
                    credentials = json.load(credentials_file)
                    client_email = credentials.get('client_email', 'Unknown')
                    st.success(f"✅ Credentials valid for: {client_email}")
                except json.JSONDecodeError:
                    st.error("❌ Invalid JSON file")
            
            query = st.text_area(
                "SQL Query *", 
                placeholder="SELECT * FROM `project.dataset.table` LIMIT 1000", 
                height=100,
                key="bq_query"
            )
            
            # Query cost estimation
            if query and 'SELECT' in query.upper():
                st.caption("💡 BigQuery queries incur costs based on data processed")
            
            submitted = st.form_submit_button("☁️ Connect & Query", type="primary", use_container_width=True)
            
            if submitted and credentials_file and project_id and query:
                DatabaseConnectors._execute_bigquery_query({
                    'credentials': credentials_file,
                    'project_id': project_id,
                    'query': query
                })
    
    # ============================================================================
    # REAL CONNECTION IMPLEMENTATIONS (Enhanced)
    # ============================================================================
    
    @staticmethod
    def _execute_sqlite_query(params: Dict):
        """Execute SQLite query - REAL"""
        try:
            with ProgressIndicator("Querying SQLite database...") as progress:
                uploaded_file = params['file']
                query = params.get('query', '')
                
                progress.update(0.2, "Creating temporary file...")
                
                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name
                
                try:
                    import sqlite3
                    
                    progress.update(0.4, "Connecting to database...")
                    conn = sqlite3.connect(tmp_path)
                    
                    progress.update(0.6, "Executing query...")
                    df = pd.read_sql_query(query, conn)
                    
                    progress.update(0.8, "Closing connection...")
                    conn.close()
                    
                    progress.update(0.9, "Cleaning up...")
                    os.unlink(tmp_path)
                    
                    if df.empty:
                        st.warning("⚠️ Query returned no data.")
                    else:
                        WebSources._confirm_load(df, "SQLite Query", "", source_type="sqlite")
                        
                except sqlite3.Error as e:
                    st.error(f"❌ SQLite error: {str(e)}")
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                except pd.io.sql.DatabaseError as e:
                    st.error(f"❌ Query error: {str(e)}")
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                    
        except Exception as e:
            st.error(f"❌ Connection failed: {str(e)[:200]}")
    
    @staticmethod
    def _execute_mysql_query(params: Dict):
        """Execute MySQL query - REAL"""
        try:
            with ProgressIndicator("Connecting to MySQL...") as progress:
                import mysql.connector
                
                progress.update(0.3, "Establishing connection...")
                conn = mysql.connector.connect(
                    host=params['host'],
                    port=params['port'],
                    user=params['username'],
                    password=params['password'],
                    database=params['database'],
                    connection_timeout=10
                )
                
                progress.update(0.6, "Executing query...")
                df = pd.read_sql_query(params['query'], conn)
                
                progress.update(0.8, "Closing connection...")
                conn.close()
                
                if df.empty:
                    st.warning("⚠️ Query returned no data.")
                else:
                    WebSources._confirm_load(df, "MySQL Query", "", source_type="mysql")
                    
        except mysql.connector.Error as e:
            if e.errno == 2003:
                st.error("❌ Cannot connect to MySQL server. Check host/port.")
            elif e.errno == 1045:
                st.error("❌ Access denied. Check username/password.")
            else:
                st.error(f"❌ MySQL error: {str(e)}")
        except Exception as e:
            st.error(f"❌ Connection failed: {str(e)[:200]}")
    
    @staticmethod
    def _execute_postgresql_query(params: Dict):
        """Execute PostgreSQL query - REAL"""
        try:
            with ProgressIndicator("Connecting to PostgreSQL...") as progress:
                import psycopg2
                
                progress.update(0.3, "Establishing connection...")
                conn = psycopg2.connect(
                    host=params['host'],
                    port=params['port'],
                    user=params['username'],
                    password=params['password'],
                    database=params['database'],
                    connect_timeout=10,
                    sslmode=params.get('ssl_mode', 'prefer')
                )
                
                progress.update(0.6, "Executing query...")
                df = pd.read_sql_query(params['query'], conn)
                
                progress.update(0.8, "Closing connection...")
                conn.close()
                
                if df.empty:
                    st.warning("⚠️ Query returned no data.")
                else:
                    WebSources._confirm_load(df, "PostgreSQL Query", "", source_type="postgresql")
                    
        except psycopg2.OperationalError as e:
            if "could not connect" in str(e):
                st.error("❌ Cannot connect to PostgreSQL server. Check host/port.")
            elif "password authentication" in str(e):
                st.error("❌ Authentication failed. Check username/password.")
            else:
                st.error(f"❌ PostgreSQL error: {str(e)}")
        except Exception as e:
            st.error(f"❌ Connection failed: {str(e)[:200]}")
    
    @staticmethod
    def _execute_sql_server_query(params: Dict):
        """Execute SQL Server query - REAL"""
        try:
            with ProgressIndicator("Connecting to SQL Server...") as progress:
                import pyodbc
                
                # Build connection string
                conn_str = f"""
                    DRIVER={{ODBC Driver 17 for SQL Server}};
                    SERVER={params['server']},{params['port']};
                    DATABASE={params['database']};
                    UID={params['username']};
                    PWD={params['password']};
                    TrustServerCertificate={'yes' if params.get('trust_cert', True) else 'no'};
                """
                
                progress.update(0.3, "Establishing connection...")
                conn = pyodbc.connect(conn_str)
                
                progress.update(0.6, "Executing query...")
                df = pd.read_sql_query(params['query'], conn)
                
                progress.update(0.8, "Closing connection...")
                conn.close()
                
                if df.empty:
                    st.warning("⚠️ Query returned no data.")
                else:
                    WebSources._confirm_load(df, "SQL Server Query", "", source_type="sqlserver")
                    
        except pyodbc.Error as e:
            if "login failed" in str(e).lower():
                st.error("❌ Login failed. Check username/password.")
            elif "cannot open database" in str(e).lower():
                st.error("❌ Cannot open database. Check database name.")
            else:
                st.error(f"❌ SQL Server error: {str(e)}")
        except Exception as e:
            st.error(f"❌ Connection failed: {str(e)[:200]}")
    
    @staticmethod
    def _execute_mongodb_query(params: Dict):
        """Execute MongoDB query - REAL"""
        try:
            with ProgressIndicator("Connecting to MongoDB...") as progress:
                import pymongo
                
                progress.update(0.3, "Establishing connection...")
                
                # Build connection string
                if params.get('username') and params.get('password'):
                    conn_str = f"mongodb://{params['username']}:{params['password']}@{params['host']}:{params['port']}/"
                else:
                    conn_str = f"mongodb://{params['host']}:{params['port']}/"
                
                client = pymongo.MongoClient(conn_str, serverSelectionTimeoutMS=5000)
                
                # Test connection
                client.server_info()
                
                progress.update(0.5, "Accessing database...")
                db = client[params['database']]
                collection = db[params['collection']]
                
                progress.update(0.7, "Querying data...")
                
                # Parse query filter if provided
                query_filter = {}
                if params.get('query_filter'):
                    try:
                        query_filter = json.loads(params['query_filter'])
                    except json.JSONDecodeError:
                        st.warning("⚠️ Invalid JSON filter. Using empty filter.")
                
                # Execute query
                cursor = collection.find(query_filter).skip(params.get('skip', 0)).limit(params.get('limit', 1000))
                
                # Convert to DataFrame
                df = pd.DataFrame(list(cursor))
                
                progress.update(0.9, "Closing connection...")
                client.close()
                
                if df.empty:
                    st.warning("⚠️ Query returned no data.")
                else:
                    # Remove MongoDB _id column
                    if '_id' in df.columns:
                        df = df.drop('_id', axis=1)
                    
                    WebSources._confirm_load(df, "MongoDB Query", "", source_type="mongodb")
                    
        except pymongo.errors.ConnectionFailure:
            st.error("❌ Cannot connect to MongoDB server. Check host/port.")
        except pymongo.errors.OperationFailure as e:
            if "authentication" in str(e).lower():
                st.error("❌ Authentication failed. Check username/password.")
            else:
                st.error(f"❌ MongoDB error: {str(e)}")
        except Exception as e:
            st.error(f"❌ Connection failed: {str(e)[:200]}")
    
    @staticmethod
    def _execute_snowflake_query(params: Dict):
        """Execute Snowflake query - REAL"""
        try:
            with ProgressIndicator("Connecting to Snowflake...") as progress:
                import snowflake.connector
                
                progress.update(0.3, "Establishing connection...")
                
                conn = snowflake.connector.connect(
                    user=params['username'],
                    password=params['password'],
                    account=params['account'],
                    warehouse=params.get('warehouse'),
                    database=params.get('database'),
                    schema=params.get('schema'),
                    timeout=10
                )
                
                progress.update(0.6, "Executing query...")
                df = pd.read_sql_query(params['query'], conn)
                
                progress.update(0.8, "Closing connection...")
                conn.close()
                
                if df.empty:
                    st.warning("⚠️ Query returned no data.")
                else:
                    WebSources._confirm_load(df, "Snowflake Query", "", source_type="snowflake")
                    
        except snowflake.connector.errors.DatabaseError as e:
            if "incorrect username or password" in str(e).lower():
                st.error("❌ Incorrect username or password.")
            elif "account not found" in str(e).lower():
                st.error("❌ Account not found. Check account identifier.")
            else:
                st.error(f"❌ Snowflake error: {str(e)}")
        except Exception as e:
            st.error(f"❌ Connection failed: {str(e)[:200]}")
    
    @staticmethod
    def _execute_bigquery_query(params: Dict):
        """Execute BigQuery query - REAL"""
        try:
            with ProgressIndicator("Connecting to BigQuery...") as progress:
                from google.cloud import bigquery
                from google.oauth2 import service_account
                
                progress.update(0.3, "Loading credentials...")
                
                # Load credentials
                credentials_info = json.load(params['credentials'])
                credentials = service_account.Credentials.from_service_account_info(credentials_info)
                
                progress.update(0.5, "Connecting to BigQuery...")
                client = bigquery.Client(credentials=credentials, project=params['project_id'])
                
                progress.update(0.7, "Executing query...")
                query_job = client.query(params['query'])
                df = query_job.to_dataframe()
                
                progress.update(0.9, "Closing connection...")
                client.close()
                
                if df.empty:
                    st.warning("⚠️ Query returned no data.")
                else:
                    WebSources._confirm_load(df, "BigQuery Query", "", source_type="bigquery")
                    
        except Exception as e:
            if "quota exceeded" in str(e).lower():
                st.error("❌ BigQuery quota exceeded. Try again later.")
            elif "permission denied" in str(e).lower():
                st.error("❌ Permission denied. Check service account permissions.")
            else:
                st.error(f"❌ BigQuery error: {str(e)[:200]}")
    
    # ============================================================================
    # SAMPLE METHODS FOR MISSING DEPENDENCIES
    # ============================================================================
    
    @staticmethod
    def _execute_mysql_sample():
        """Provide sample data for MySQL"""
        st.info("📦 Loading sample data for MySQL demonstration")
        time.sleep(0.5)
        # Load Iris dataset as sample
        dataset_info = PopularDatasets.POPULAR_DATASETS.get('iris')
        if dataset_info:
            PopularDatasets._load_dataset('iris', dataset_info)
    
    @staticmethod 
    def _execute_postgresql_sample():
        """Provide sample data for PostgreSQL"""
        st.info("📦 Loading sample data for PostgreSQL demonstration")
        time.sleep(0.5)
        dataset_info = PopularDatasets.POPULAR_DATASETS.get('titanic')
        if dataset_info:
            PopularDatasets._load_dataset('titanic', dataset_info)
    
    @staticmethod
    def _execute_sql_server_sample():
        """Provide sample data for SQL Server"""
        st.info("📦 Loading sample data for SQL Server demonstration")
        time.sleep(0.5)
        dataset_info = PopularDatasets.POPULAR_DATASETS.get('superstore')
        if dataset_info:
            PopularDatasets._load_dataset('superstore', dataset_info)
    
    @staticmethod
    def _execute_mongodb_sample():
        """Provide sample data for MongoDB"""
        st.info("📦 Loading sample data for MongoDB demonstration")
        time.sleep(0.5)
        dataset_info = PopularDatasets.POPULAR_DATASETS.get('netflix')
        if dataset_info:
            PopularDatasets._load_dataset('netflix', dataset_info)
    
    @staticmethod
    def _execute_snowflake_sample():
        """Provide sample data for Snowflake"""
        st.info("📦 Loading sample data for Snowflake demonstration")
        time.sleep(0.5)
        dataset_info = PopularDatasets.POPULAR_DATASETS.get('happiness')
        if dataset_info:
            PopularDatasets._load_dataset('happiness', dataset_info)
    
    @staticmethod
    def _execute_bigquery_sample():
        """Provide sample data for BigQuery"""
        st.info("📦 Loading sample data for BigQuery demonstration")
        time.sleep(0.5)
        dataset_info = PopularDatasets.POPULAR_DATASETS.get('airbnb')
        if dataset_info:
            PopularDatasets._load_dataset('airbnb', dataset_info)

# ============================================================================
# MAIN CONNECTOR INTERFACE (Enhanced)
# ============================================================================

class DataSourceConnector:
    """Main data source connector interface with enhanced UX"""
    
    @staticmethod
    def render_connection_selector():
        """Render the main connection selector with better organization"""
        # Main connector interface
        default_tab = st.session_state.get('connector_tab', 'Popular Datasets')
        
        # If show_popular is set, force that tab
        if st.session_state.get('show_popular'):
            default_tab = 'Popular Datasets'
            st.session_state.show_popular = False
        
        tab_names = ["🌟 Popular Datasets", "🌐 Web Sources", "🗄️ Databases", "🌐 APIs & Services"]
        tab_index = tab_names.index(default_tab) if default_tab in tab_names else 0
        
        source_tabs = st.tabs(tab_names)
        
        with source_tabs[0]:
            PopularDatasets.render_interface()
            
        with source_tabs[1]:
            WebSources.render_interface()
            
        with source_tabs[2]:
            DatabaseConnectors.render_interface()
            
        with source_tabs[3]:
            # Simple API interface
            st.subheader("🌐 API & Service Connections")
            st.caption("Connect to external services and APIs")
            
            api_cols = st.columns(2)
            
            with api_cols[0]:
                st.markdown("#### 📊 Google Sheets")
                st.caption("Connect to Google Sheets")
                if st.button("Connect to Sheets", use_container_width=True):
                    st.info("Google Sheets integration requires gspread package")
                    st.code("pip install gspread", language="bash")
            
            with api_cols[1]:
                st.markdown("#### 🌐 REST API")
                st.caption("Call REST APIs")
                if st.button("Call REST API", use_container_width=True):
                    st.info("REST API connector - enter your API endpoint:")
                    api_url = st.text_input("API URL", placeholder="https://api.example.com/data")
                    if api_url and st.button("Fetch Data"):
                        try:
                            response = requests.get(api_url, timeout=10)
                            if response.status_code == 200:
                                data = response.json()
                                if isinstance(data, list):
                                    df = pd.DataFrame(data)
                                    WebSources._confirm_load(df, "API Data", api_url, source_type="api")
                                else:
                                    st.error("API returned non-list data")
                            else:
                                st.error(f"API error: {response.status_code}")
                        except Exception as e:
                            st.error(f"API call failed: {str(e)[:100]}")
    
    @staticmethod
    def get_quick_stats():
        """Get quick stats about available data sources"""
        return {
            'popular_datasets': len(PopularDatasets.POPULAR_DATASETS),
            'available_connectors': len(DependencyManager.get_available_connectors()['available']) + 1,
            'last_loaded': st.session_state.get('dataset_metadata', {}).get('loaded_at'),
            'current_dataset': st.session_state.get('dataset_metadata', {}).get('source_name')
        }
    
    @staticmethod
    def render_data_source_status():
        """Render current data source status for sidebar"""
        if 'dataset_metadata' in st.session_state and st.session_state.dataset_metadata:
            meta = st.session_state.dataset_metadata
            source_type = meta.get('source_type', 'unknown')
            source_name = meta.get('source_name', 'Dataset')
            
            # Map source type to icon
            icons = {
                'Popular Dataset': '🌟',
                'web_url': '🌐',
                'github': '📂',
                'sqlite': '📁',
                'mysql': '🐬',
                'postgresql': '🐘',
                'sqlserver': '🗄️',
                'mongodb': '🍃',
                'snowflake': '❄️',
                'bigquery': '☁️',
                'upload': '📁',
                'api': '🔌'
            }
            
            icon = icons.get(source_type, '📊')
            
            # Format time
            loaded_at = meta.get('loaded_at')
            if loaded_at:
                time_str = time.strftime('%H:%M', time.localtime(loaded_at))
            else:
                time_str = "Unknown"
            
            return {
                'icon': icon,
                'name': source_name,
                'type': source_type.replace('_', ' ').title(),
                'time': time_str,
                'rows': meta.get('shape', (0, 0))[0],
                'cols': meta.get('shape', (0, 0))[1]
            }
        return None

# ============================================================================
# INTEGRATION HELPERS
# ============================================================================

def init_connector_session_state():
    """Initialize session state for connectors"""
    if 'connector_tab' not in st.session_state:
        st.session_state.connector_tab = "Popular Datasets"
    if 'data_source_mode' not in st.session_state:
        st.session_state.data_source_mode = None
    if 'show_popular' not in st.session_state:
        st.session_state.show_popular = False

def render_data_source_quick_access():
    """Render quick access to data sources in main app"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📁 Upload", use_container_width=True, type="primary"):
            st.session_state.data_source_mode = "upload"
    
    with col2:
        if st.button("🌟 Samples", use_container_width=True, type="secondary"):
            st.session_state.show_popular = True
            st.session_state.connector_tab = "Popular Datasets"
    
    with col3:
        if st.button("🌐 Web", use_container_width=True, type="secondary"):
            st.session_state.connector_tab = "Web Sources"
    
    with col4:
        if st.button("🗄️ Database", use_container_width=True, type="secondary"):
            st.session_state.connector_tab = "Databases"
    
    # If any data source mode is active, show the connector
    if st.session_state.get('data_source_mode') == 'upload':
        # File upload would be handled by data_handlers.py
        pass
    elif (st.session_state.get('show_popular') or 
          st.session_state.get('connector_tab') in ["Popular Datasets", "Web Sources", "Databases", "APIs & Services"]):
        st.markdown("---")
        DataSourceConnector.render_connection_selector()

# ============================================================================
# EXPORT FOR USE IN OTHER MODULES
# ============================================================================

# Make sure WebSources._confirm_load is available for database connectors
WebSources._confirm_load = WebSources._confirm_load
WebSources._finalize_load = WebSources._finalize_load

# Export main classes and functions
__all__ = [
    'DataSourceConnector',
    'PopularDatasets',
    'WebSources',
    'DatabaseConnectors',
    'DependencyManager',
    'ConnectionTester',
    'ProgressIndicator',
    'SuccessHandler',
    'init_connector_session_state',
    'render_data_source_quick_access',
    'safe_execute',
    'format_bytes',
    'validate_url'
]