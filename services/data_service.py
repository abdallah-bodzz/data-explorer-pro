# services/data_service.py
"""
Data Service – Pure business logic for data operations.
No UI, no Streamlit, no session state.
"""

import io
import re
import time
import requests
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

# Core imports
from core.data.sampler import maybe_sample, enhanced_smart_sampling_score
from core.data.operations import FormulaEngine
from core.data.model import RelationshipCanvas
from core.data.sample_data import generate_sample_sales_data, generate_sample_housing_data
from core.data.scripts_library import (
    find_fuzzy_duplicates,
    detect_data_types,
    handle_missing_data,
    fix_date_formats,
    split_columns_smartly,
    build_cohort_analysis,
    decompose_time_series,
    engineer_features,
    segment_customers_rfm,
    analyze_pricing,
    analyze_ab_test,
    normalize_text,
    match_schemas,
    sanitize_pii_data,
)


class DataService:
    """Service for all data operations – loading, filtering, transformations, scripts, joins, validation."""

    def __init__(self):
        """Initialize DataService (stateless)."""
        pass

    # =========================================================================
    # LOADING
    # =========================================================================

    def load_dataset_from_file(self, file, config: Dict[str, Any]) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Load dataset from an uploaded file.

        Args:
            file: Uploaded file object (with .name, .read, .seek)
            config: Import configuration dict (separator, encoding, sheet, etc.)

        Returns:
            Tuple of (DataFrame or None, metadata dict)
        """
        try:
            file_ext = file.name.split('.')[-1].lower() if '.' in file.name else ''
            na_values = None
            if config.get('na_values'):
                na_values = [v.strip() for v in config['na_values'].split(',')]

            df = None

            if file_ext in ['csv', 'tsv', 'txt']:
                df = pd.read_csv(
                    file,
                    sep=config.get('separator', ','),
                    encoding=config.get('encoding', 'utf-8'),
                    na_values=na_values,
                    keep_default_na=config.get('keep_default_na', True),
                    parse_dates=config.get('parse_dates', True),
                    skiprows=config.get('skip_rows', 0),
                    decimal=config.get('decimal', '.'),
                    encoding_errors='replace'
                )
            elif file_ext in ['xlsx', 'xls']:
                df = pd.read_excel(
                    file,
                    sheet_name=config.get('sheet', 0),
                    na_values=na_values,
                    keep_default_na=config.get('keep_default_na', True),
                    parse_dates=config.get('parse_dates', True),
                    skiprows=config.get('skip_rows', 0),
                    engine='openpyxl'
                )
            elif file_ext == 'json':
                df = pd.read_json(file)
            elif file_ext == 'parquet':
                df = pd.read_parquet(file)
            else:
                return None, {'error': f'Unsupported file type: .{file_ext}'}

            if df is None or df.empty:
                return None, {'error': 'File appears empty'}

            # Apply smart sampling if enabled
            if config.get('enable_smart_sampling', False):
                df, sampling_metadata = self.smart_sample(
                    df,
                    size_threshold=config.get('size_threshold', 100000),
                    complexity_threshold=config.get('complexity_threshold', 5.0)
                )
            else:
                max_rows = config.get('max_rows', 50000)
                if len(df) > max_rows:
                    df = df.head(max_rows)

            # Remove duplicates
            if config.get('remove_duplicates', True):
                df = df.drop_duplicates()

            # Fix column names
            if config.get('fix_column_names', True):
                df.columns = [
                    str(col).strip()
                    .replace(' ', '_')
                    .replace('\n', '_')
                    .replace('\r', '_')
                    .replace('\t', '_')
                    .replace('.', '_')
                    .replace('-', '_')
                    .lower()
                    for col in df.columns
                ]

            # Optimize memory
            if config.get('optimize_memory', True):
                df = self._optimize_dataframe(df)

            metadata = {
                'filename': file.name,
                'file_type': file_ext,
                'shape': df.shape,
                'columns': df.columns.tolist(),
                'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
                'loaded_at': datetime.now().isoformat(),
                'source_type': 'file_upload',
                'row_count': len(df),
                'column_count': len(df.columns),
            }

            return df, metadata

        except pd.errors.ParserError as e:
            return None, {'error': f'Parsing error: {str(e)[:100]}'}
        except UnicodeDecodeError as e:
            return None, {'error': f'Encoding error: {str(e)[:100]}'}
        except Exception as e:
            return None, {'error': str(e)}

    def load_sample_dataset(self, dataset_type: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Load a sample dataset.

        Args:
            dataset_type: 'sales' or 'housing'

        Returns:
            Tuple of (DataFrame, metadata dict)
        """
        if dataset_type == 'sales':
            df = generate_sample_sales_data(5000, heavy_fields=False)
            name = 'Sales Analytics'
        elif dataset_type == 'housing':
            df = generate_sample_housing_data(3000, heavy_fields=False)
            name = 'Real Estate'
        else:
            raise ValueError(f'Unknown sample dataset: {dataset_type}')

        metadata = {
            'filename': f'{name} Sample.csv',
            'shape': df.shape,
            'columns': df.columns.tolist(),
            'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
            'loaded_at': datetime.now().isoformat(),
            'source_type': 'sample_data',
            'dataset_name': name,
            'row_count': len(df),
            'column_count': len(df.columns),
        }
        return df, metadata

    def load_from_url(self, url: str, config: Dict[str, Any]) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Load dataset from a URL.

        Args:
            url: Direct download URL
            config: Dict with keys: file_type, encoding, etc.

        Returns:
            Tuple of (DataFrame or None, metadata dict)
        """
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            content = response.content

            file_type = config.get('file_type', 'auto')
            if file_type == 'auto':
                if url.endswith('.csv'):
                    file_type = 'csv'
                elif url.endswith('.json'):
                    file_type = 'json'
                elif url.endswith(('.xlsx', '.xls')):
                    file_type = 'excel'
                else:
                    file_type = 'csv'  # default

            if file_type == 'csv':
                df = pd.read_csv(io.BytesIO(content), encoding=config.get('encoding', 'utf-8'))
            elif file_type == 'json':
                df = pd.read_json(io.BytesIO(content))
            elif file_type == 'excel':
                df = pd.read_excel(io.BytesIO(content))
            else:
                return None, {'error': f'Unsupported file type: {file_type}'}

            if df.empty:
                return None, {'error': 'File appears empty'}

            metadata = {
                'source_url': url,
                'file_type': file_type,
                'shape': df.shape,
                'columns': df.columns.tolist(),
                'loaded_at': datetime.now().isoformat(),
                'source_type': 'web_url',
                'row_count': len(df),
                'column_count': len(df.columns),
            }
            return df, metadata
        except requests.exceptions.Timeout:
            return None, {'error': 'Connection timeout'}
        except requests.exceptions.RequestException as e:
            return None, {'error': f'Request error: {str(e)[:100]}'}
        except Exception as e:
            return None, {'error': str(e)}

    # =========================================================================
    # FILTERING
    # =========================================================================

    def apply_filters(self, df: pd.DataFrame, filter_state: Dict[str, Any]) -> pd.DataFrame:
        """
        Apply filters defined in filter_state.

        Args:
            df: Input DataFrame
            filter_state: {
                'filters': {col: filter_def},
                'null_handling': {col: 'exclude'|'include'|'separate'},
                'logic_mode': 'AND' | 'OR',
                'logic_groups': [[col1, col2], ...]
            }

        Returns:
            Filtered DataFrame
        """
        if not filter_state.get('filters'):
            return df

        filtered_df = df.copy()
        filters = filter_state.get('filters', {})
        null_handling = filter_state.get('null_handling', {})
        logic_mode = filter_state.get('logic_mode', 'AND')

        # AND logic: apply all filters sequentially
        if logic_mode == 'AND':
            for col, filter_def in filters.items():
                if col not in filtered_df.columns:
                    continue

                mask = self._get_filter_mask(filtered_df, col, filter_def)
                null_mask = filtered_df[col].isna()
                null_method = null_handling.get(col, 'exclude')

                # Apply null handling
                if null_method == 'include':
                    mask = mask | null_mask
                elif null_method == 'separate' and filter_def.get('type') == 'categorical':
                    # For categorical, nulls are treated as separate category
                    mask = mask | null_mask
                # 'exclude' – nulls excluded by default

                filtered_df = filtered_df[mask]

            return filtered_df

        # OR logic with groups
        else:
            logic_groups = filter_state.get('logic_groups', [])
            if logic_groups:
                result_indices = set()
                for group in logic_groups:
                    group_mask = pd.Series(True, index=filtered_df.index)
                    for col in group:
                        if col in filters:
                            mask = self._get_filter_mask(filtered_df, col, filters[col])
                            group_mask = group_mask & mask
                    result_indices.update(set(filtered_df.index[group_mask]))
                return filtered_df[filtered_df.index.isin(result_indices)]

            # Simple OR: union of all filters
            final_mask = pd.Series(False, index=filtered_df.index)
            for col, filter_def in filters.items():
                if col in filtered_df.columns:
                    mask = self._get_filter_mask(filtered_df, col, filter_def)
                    final_mask = final_mask | mask
            return filtered_df[final_mask]

    def _get_filter_mask(self, df: pd.DataFrame, col: str, filter_def: Dict[str, Any]) -> pd.Series:
        """Generate a boolean mask for a single filter definition."""
        filter_type = filter_def.get('type')

        if filter_type == 'range':
            return (df[col] >= filter_def['min']) & (df[col] <= filter_def['max'])

        elif filter_type == 'gt':
            return df[col] > filter_def['value']

        elif filter_type == 'lt':
            return df[col] < filter_def['value']

        elif filter_type == 'categorical':
            return df[col].isin(filter_def['values'])

        elif filter_type == 'date_range':
            return (df[col] >= filter_def['start']) & (df[col] <= filter_def['end'])

        elif filter_type == 'text':
            search = filter_def.get('search', '')
            case_sensitive = filter_def.get('case_sensitive', False)
            use_regex = filter_def.get('use_regex', False)

            if use_regex:
                pattern = filter_def.get('pattern', search)
                try:
                    return df[col].astype(str).str.contains(
                        pattern,
                        case=case_sensitive,
                        regex=True,
                        na=False
                    )
                except re.error:
                    # Invalid regex – fallback to literal
                    return df[col].astype(str).str.contains(search, case=case_sensitive, na=False)
            else:
                return df[col].astype(str).str.contains(search, case=case_sensitive, na=False)

        elif filter_type == 'or':
            # For outlier filters: conditions list
            conditions = filter_def.get('conditions', [])
            mask = pd.Series(False, index=df.index)
            for cond in conditions:
                if cond.get('type') == 'gt':
                    mask = mask | (df[col] > cond['value'])
                elif cond.get('type') == 'lt':
                    mask = mask | (df[col] < cond['value'])
            return mask

        # Default: keep all
        return pd.Series(True, index=df.index)

    # =========================================================================
    # DATA OPERATIONS
    # =========================================================================

    def remove_duplicates(self, df: pd.DataFrame, subset: Optional[List[str]] = None,
                         keep: str = 'first') -> pd.DataFrame:
        """Remove duplicate rows."""
        return df.drop_duplicates(subset=subset, keep=keep)

    def handle_missing_values(self, df: pd.DataFrame, strategy: str = 'auto',
                              columns: Optional[List[str]] = None) -> Tuple[pd.DataFrame, Dict]:
        """
        Handle missing values using the specified strategy.
        Returns (cleaned_df, summary_dict).
        """
        result = handle_missing_data(df, strategy=strategy, columns=columns)
        return result.get('imputed_data', df), result.get('summary', {})

    def convert_data_types(self, df: pd.DataFrame, conversions: Dict[str, str]) -> pd.DataFrame:
        """
        Convert columns to specified types.
        conversions: {col_name: target_type}
        """
        result = df.copy()
        for col, new_type in conversions.items():
            if col not in df.columns:
                continue
            try:
                if new_type == 'int64':
                    result[col] = pd.to_numeric(result[col], errors='coerce').astype('Int64')
                elif new_type == 'float64':
                    result[col] = pd.to_numeric(result[col], errors='coerce')
                elif new_type == 'object':
                    result[col] = result[col].astype('string')
                elif new_type == 'bool':
                    result[col] = result[col].astype('boolean')
                elif new_type == 'datetime64[ns]':
                    result[col] = pd.to_datetime(result[col], errors='coerce')
                elif new_type == 'category':
                    result[col] = result[col].astype('category')
            except Exception:
                continue
        return result

    def create_calculated_column(self, df: pd.DataFrame, formula: str, new_column: str) -> pd.DataFrame:
        """
        Create a new column from a formula expression.
        Delegates to FormulaEngine.
        """
        return FormulaEngine.evaluate_formula(df, formula, new_column)

    # =========================================================================
    # SCRIPTS (delegates to scripts_library)
    # =========================================================================

    def run_script(self, df: pd.DataFrame, script_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a data script by ID.
        Returns a dict with result (DataFrame, report, etc.).
        """
        script_map = {
            'duplicates': find_fuzzy_duplicates,
            'types': detect_data_types,
            'missing': handle_missing_data,
            'dates': fix_date_formats,
            'splitter': split_columns_smartly,
            'cohorts': build_cohort_analysis,
            'timeseries': decompose_time_series,
            'features': engineer_features,
            'rfm': segment_customers_rfm,
            'pricing': analyze_pricing,
            'abtest': analyze_ab_test,
            'normalize': normalize_text,
            'schema': match_schemas,
            'privacy': sanitize_pii_data,
        }

        script_func = script_map.get(script_id)
        if not script_func:
            return {'error': f'Unknown script: {script_id}'}

        try:
            result = script_func(df, **config)
            return result
        except Exception as e:
            return {'error': str(e)}

    # =========================================================================
    # JOINS (from data_model)
    # =========================================================================

    def perform_join(self, datasets: Dict[str, pd.DataFrame],
                     links: List[Tuple], start_table: str,
                     join_type: str = 'inner') -> Tuple[pd.DataFrame, List[Dict]]:
        """
        Perform joins on multiple datasets using RelationshipCanvas.
        Returns (joined_df, execution_plan).
        """
        canvas = RelationshipCanvas(datasets)
        # Restore links
        for link in links:
            if len(link) >= 5:
                from_table, from_col, to_table, to_col, op_type = link[:5]
                if op_type == 'join':
                    join_type_from_link = link[6] if len(link) > 6 else join_type
                    alias = link[5] if len(link) > 5 else None
                    canvas.add_join(from_table, from_col, to_table, to_col,
                                   join_type_from_link, alias)
        result = canvas.join(start_table, join_type)
        plan = canvas.plan
        return result, plan

    # =========================================================================
    # ANALYSIS & VALIDATION
    # =========================================================================

    def get_dataset_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get comprehensive dataset summary."""
        if df is None or df.empty:
            return {'error': 'Dataset is empty'}

        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        datetime_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]

        return {
            'row_count': len(df),
            'col_count': len(df.columns),
            'numeric_columns': numeric_cols,
            'categorical_columns': categorical_cols,
            'datetime_columns': datetime_cols,
            'missing_count': int(df.isnull().sum().sum()),
            'missing_percentage': float(df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100),
            'duplicate_count': int(df.duplicated().sum()),
            'duplicate_percentage': float(df.duplicated().sum() / len(df) * 100),
            'memory_mb': float(df.memory_usage(deep=True).sum() / (1024 ** 2)),
            'column_types': {col: str(dtype) for col, dtype in df.dtypes.items()},
        }

    def validate_dataset(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate dataset and return issues and warnings."""
        issues = []
        warnings = []

        if df is None:
            return {'valid': False, 'issues': ['Dataset is None']}

        if df.empty:
            return {'valid': False, 'issues': ['Dataset is empty']}

        # Check column names for control characters
        for col in df.columns:
            if any(char in str(col) for char in ['\n', '\r', '\t', '\0']):
                issues.append(f"Column '{col}' contains control characters")

        # Check duplicates
        dup_count = df.duplicated().sum()
        if dup_count > 0:
            warnings.append(f"Found {dup_count:,} duplicate rows ({dup_count/len(df)*100:.1f}%)")

        # Check missing values
        missing_pct = df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100
        if missing_pct > 30:
            issues.append(f"High missing values: {missing_pct:.1f}%")
        elif missing_pct > 5:
            warnings.append(f"Missing values: {missing_pct:.1f}%")

        # Check for constant columns
        constant_cols = [col for col in df.columns if df[col].nunique() == 1]
        if constant_cols:
            warnings.append(f"Constant columns: {', '.join(constant_cols[:5])}")

        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'row_count': len(df),
            'column_count': len(df.columns),
            'missing_percentage': missing_pct,
            'duplicate_count': dup_count,
            'constant_columns': constant_cols,
        }

    # =========================================================================
    # SAMPLING
    # =========================================================================

    def smart_sample(self, df: pd.DataFrame, size_threshold: int = 100000,
                     complexity_threshold: float = 5.0) -> Tuple[pd.DataFrame, Dict]:
        """
        Apply smart sampling to large datasets.
        Returns (sampled_df, metadata).
        """
        sampled_df, metadata, _ = maybe_sample(
            df,
            size_threshold=size_threshold,
            complexity_threshold=complexity_threshold,
            random_state=42
        )
        return sampled_df, metadata

    # =========================================================================
    # INTERNAL HELPERS
    # =========================================================================

    def _optimize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Optimize memory usage of DataFrame."""
        result = df.copy()

        # Downcast numeric columns
        for col in result.select_dtypes(include=[np.number]).columns:
            try:
                col_min = result[col].min()
                col_max = result[col].max()
                if pd.api.types.is_integer_dtype(result[col]):
                    if col_min >= 0:
                        for dtype in [np.uint8, np.uint16, np.uint32]:
                            if col_max <= np.iinfo(dtype).max:
                                result[col] = result[col].astype(dtype)
                                break
                    else:
                        for dtype in [np.int8, np.int16, np.int32]:
                            if col_min >= np.iinfo(dtype).min and col_max <= np.iinfo(dtype).max:
                                result[col] = result[col].astype(dtype)
                                break
                elif pd.api.types.is_float_dtype(result[col]):
                    if result[col].dtype != np.float32:
                        result[col] = pd.to_numeric(result[col], downcast='float')
            except Exception:
                continue

        # Convert strings to categories when beneficial
        for col in result.select_dtypes(include=['object']).columns:
            try:
                num_unique = result[col].nunique()
                num_total = len(result[col])
                if 1 < num_unique < num_total * 0.5:
                    result[col] = result[col].astype('category')
            except Exception:
                continue

        return result