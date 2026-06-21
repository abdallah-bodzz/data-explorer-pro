# scripts_library.py
"""
📚 Data Scripts Implementation Library
Production-ready solutions for common data problems
"""

import pandas as pd
import numpy as np
import re
from typing import Dict, Any, List, Tuple, Optional, Union
from datetime import datetime, timedelta
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# DEPENDENCY HANDLING (GRACEFUL FALLBACKS)
# ============================================================================

# Initialize all as False with graceful fallbacks
FUZZY_AVAILABLE = False
PHONETICS_AVAILABLE = False
STATSMODELS_AVAILABLE = False
SCIPY_AVAILABLE = False

# Try to import optional dependencies
try:
    from fuzzywuzzy import fuzz, process
    FUZZY_AVAILABLE = True
except ImportError:
    pass  # Handled in UI

try:
    import phonetics
    PHONETICS_AVAILABLE = True
except ImportError:
    pass

try:
    import statsmodels
    STATSMODELS_AVAILABLE = True
except ImportError:
    pass

try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    pass

# Handle missing streamlit for match_schemas function
try:
    import streamlit as st
except ImportError:
    # Create dummy st for match_schemas function
    class DummySt:
        session_state = {}
    st = DummySt()

# ============================================================================
# DETECTIVE SCRIPTS
# ============================================================================

def find_fuzzy_duplicates(df: pd.DataFrame, similarity_threshold: float = 0.85, 
                         columns_to_check: List[str] = None, **kwargs) -> Dict[str, Any]:
    """
    Find duplicates with typos, abbreviations, and formatting differences.
    
    Args:
        df: Input DataFrame
        similarity_threshold: Minimum similarity score (0.0 to 1.0)
        columns_to_check: Specific columns to analyze (default: all text columns)
    
    Returns:
        Dictionary with cleaned data, duplicate report, and summary
    """
    
    # Empty dataset handling
    if df is None or df.empty:
        return {"error": "Dataset is empty", "cleaned_data": df}
    
    # Performance guard for large datasets
    if len(df) > 10000:
        return {
            "warning": "Large dataset detected (>10k rows). Consider sampling for faster results.",
            "suggestion": "Filter dataset or use smaller sample first",
            "cleaned_data": df,
            "duplicate_report": pd.DataFrame(),
            "summary": {"large_dataset": True}
        }
    
    # Dependency check
    if not FUZZY_AVAILABLE:
        return {
            "warning": "Fuzzy matching unavailable. Install: pip install fuzzywuzzy python-Levenshtein",
            "error": "Missing fuzzywuzzy dependency",
            "cleaned_data": df,
            "duplicate_report": pd.DataFrame()
        }
    
    # Default to all text columns
    if columns_to_check is None:
        columns_to_check = df.select_dtypes(include=['object']).columns.tolist()
    
    if not columns_to_check:
        return {"error": "No text columns to check", "cleaned_data": df}
    
    results = {}
    all_duplicates = pd.DataFrame()
    cleaned_df = df.copy()
    
    # Limit to first 5 columns for performance
    for col in columns_to_check[:5]:
        if col not in df.columns:
            continue
        
        # Get unique non-null values
        values = df[col].dropna().astype(str).unique()
        if len(values) < 2:
            continue
        
        # Normalize values for comparison
        normalized = {val: _normalize_text(val) for val in values}
        
        # Find clusters using similarity
        clusters = []
        processed = set()
        
        for i, (val1, norm1) in enumerate(normalized.items()):
            if val1 in processed:
                continue
            
            cluster = [val1]
            processed.add(val1)
            
            for val2, norm2 in list(normalized.items())[i+1:]:
                if val2 in processed:
                    continue
                
                # Calculate multiple similarity measures
                similarities = []
                
                # 1. Normalized text similarity
                if FUZZY_AVAILABLE:
                    text_sim = fuzz.ratio(norm1, norm2) / 100
                else:
                    # Simple token-based similarity
                    tokens1 = set(re.findall(r'\w+', norm1))
                    tokens2 = set(re.findall(r'\w+', norm2))
                    if tokens1 and tokens2:
                        text_sim = len(tokens1.intersection(tokens2)) / len(tokens1.union(tokens2))
                    else:
                        text_sim = 0
                similarities.append(text_sim)
                
                # 2. Phonetic similarity (if available)
                if PHONETICS_AVAILABLE and len(norm1) > 2 and len(norm2) > 2:
                    try:
                        phonetic1 = phonetics.metaphone(norm1)
                        phonetic2 = phonetics.metaphone(norm2)
                        if phonetic1 and phonetic2:
                            phonetic_sim = 1.0 if phonetic1 == phonetic2 else 0.0
                            similarities.append(phonetic_sim)
                    except:
                        pass
                
                # Use maximum similarity
                max_similarity = max(similarities) if similarities else 0
                
                if max_similarity >= similarity_threshold:
                    cluster.append(val2)
                    processed.add(val2)
            
            if len(cluster) > 1:
                clusters.append(cluster)
        
        if clusters:
            # Create report for this column
            report_data = []
            for cluster_id, cluster in enumerate(clusters):
                canonical = _choose_canonical_value(cluster)
                for value in cluster:
                    report_data.append({
                        "column": col,
                        "original_value": value,
                        "cluster_id": f"cluster_{cluster_id}",
                        "canonical_value": canonical,
                        "confidence": "high" if len(cluster) > 2 else "medium"
                    })
            
            col_report = pd.DataFrame(report_data)
            all_duplicates = pd.concat([all_duplicates, col_report], ignore_index=True)
            
            # Add cluster information to cleaned data
            cluster_map = dict(zip(col_report["original_value"], col_report["cluster_id"]))
            cleaned_df[f"{col}_duplicate_cluster"] = cleaned_df[col].map(cluster_map)
            
            results[col] = {
                "clusters": len(clusters),
                "duplicate_values": sum(len(c) - 1 for c in clusters),
                "suggested_merges": col_report
            }
    
    summary = {
        "columns_analyzed": len(results),
        "total_clusters": sum(info["clusters"] for info in results.values()),
        "total_duplicate_values": sum(info["duplicate_values"] for info in results.values()),
        "similarity_threshold": similarity_threshold,
        "algorithm": "fuzzy_matching"
    }
    
    if not results:
        summary["message"] = "No fuzzy duplicates found at current threshold"
    
    return {
        "cleaned_data": cleaned_df,
        "duplicate_report": all_duplicates,
        "summary": summary
    }

def detect_data_types(df: pd.DataFrame, columns_to_convert: List[str] = None, **kwargs) -> Dict[str, Any]:
    """
    Auto-detect and convert messy data types.
    
    Args:
        df: Input DataFrame
        columns_to_convert: Specific columns to analyze (default: all columns)
    
    Returns:
        Dictionary with converted data, type report, and summary
    """
    
    # Empty dataset handling
    if df is None or df.empty:
        return {"error": "Dataset is empty", "converted_data": df}
    
    # Default to all columns
    if columns_to_convert is None:
        columns_to_convert = df.columns.tolist()
    
    # Safe dtype extraction
    original_dtypes = {}
    for col in columns_to_convert:
        try:
            original_dtypes[col] = str(df[col].dtype)
        except:
            original_dtypes[col] = 'unknown'
    
    converted_df = df.copy()
    conversion_log = []
    
    for col in columns_to_convert:
        if col not in df.columns:
            continue
        
        col_data = df[col].dropna()
        if len(col_data) == 0:
            # All null column
            conversion_log.append({
                "column": col,
                "original_type": original_dtypes.get(col, 'unknown'),
                "detected_type": "null_only",
                "confidence": 1.0,
                "new_type": "object",
                "converted_rows": 0,
                "failed_rows": 0,
                "notes": "Column contains only null values"
            })
            continue
        
        # Test for different data types
        tests = [
            ("datetime", _detect_datetime_type, "datetime64[ns]"),
            ("integer", _detect_integer_type, "Int64"),
            ("float", _detect_float_type, "float64"),
            ("boolean", _detect_boolean_type, "boolean"),
            ("categorical", _detect_categorical_type, "category"),
            ("currency", _detect_currency_type, "float64"),
            ("percentage", _detect_percentage_type, "float64")
        ]
        
        best_match = None
        best_confidence = 0
        
        for type_name, detector, target_dtype in tests:
            try:
                confidence, evidence = detector(col_data)
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = (type_name, target_dtype, evidence)
            except Exception as e:
                continue
        
        # Apply conversion if confident enough
        if best_match and best_confidence >= 0.7:  # 70% confidence threshold
            type_name, target_dtype, evidence = best_match
            
            try:
                if type_name == "datetime":
                    converted_df[col] = pd.to_datetime(df[col], errors='coerce')
                elif type_name == "integer":
                    converted_df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
                elif type_name == "float":
                    converted_df[col] = pd.to_numeric(df[col], errors='coerce')
                elif type_name == "boolean":
                    converted_df[col] = _convert_to_boolean(df[col])
                elif type_name == "categorical":
                    converted_df[col] = df[col].astype('category')
                elif type_name == "currency":
                    converted_df[col] = _convert_currency_to_numeric(df[col])
                elif type_name == "percentage":
                    converted_df[col] = _convert_percentage_to_numeric(df[col])
                
                success_count = converted_df[col].notna().sum()
                failed_count = converted_df[col].isna().sum() - df[col].isna().sum()
                
                conversion_log.append({
                    "column": col,
                    "original_type": original_dtypes.get(col, 'unknown'),
                    "detected_type": type_name,
                    "confidence": round(best_confidence, 2),
                    "new_type": target_dtype,
                    "converted_rows": int(success_count),
                    "failed_rows": int(failed_count),
                    "evidence": evidence[:3] if evidence else []
                })
                
            except Exception as e:
                conversion_log.append({
                    "column": col,
                    "original_type": original_dtypes.get(col, 'unknown'),
                    "detected_type": type_name,
                    "confidence": round(best_confidence, 2),
                    "error": str(e)[:100],
                    "evidence": evidence[:3] if evidence else []
                })
        else:
            # No confident type detected
            conversion_log.append({
                "column": col,
                "original_type": original_dtypes.get(col, 'unknown'),
                "detected_type": "unknown",
                "confidence": round(best_confidence, 2) if best_match else 0,
                "new_type": original_dtypes.get(col, 'unknown'),
                "converted_rows": 0,
                "failed_rows": 0,
                "notes": "No confident type detected"
            })
    
    # Calculate statistics
    successful_conversions = len([l for l in conversion_log 
                                 if l.get("converted_rows", 0) > 0 and "error" not in l])
    failed_conversions = len([l for l in conversion_log if "error" in l])
    
    type_distribution = {}
    for log in conversion_log:
        dtype = log.get("detected_type", "unknown")
        type_distribution[dtype] = type_distribution.get(dtype, 0) + 1
    
    return {
        "converted_data": converted_df,
        "type_report": pd.DataFrame(conversion_log),
        "summary": {
            "total_columns": len(columns_to_convert),
            "successful_conversions": successful_conversions,
            "failed_conversions": failed_conversions,
            "type_distribution": type_distribution,
            "confidence_threshold": 0.7
        }
    }

def find_anomaly_patterns(df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
    """
    Find statistical anomalies and suspicious patterns.
    
    Args:
        df: Input DataFrame
    
    Returns:
        Dictionary with anomaly report and summary
    """
    
    # Empty dataset handling
    if df is None or df.empty:
        return {"error": "Dataset is empty", "flagged_data": df}
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    anomaly_report = []
    flagged_df = df.copy()
    
    # 1. Statistical Outliers (Z-score method)
    for col in numeric_cols:
        col_data = df[col].dropna()
        if len(col_data) < 10:
            continue
        
        # Calculate Z-scores
        mean = col_data.mean()
        std = col_data.std()
        
        if std == 0:  # Constant column
            continue
        
        z_scores = np.abs((col_data - mean) / std)
        outliers = col_data[z_scores > 3]  # 3 standard deviations
        
        if len(outliers) > 0:
            # Check for temporal patterns if date column exists
            date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
            temporal_info = {}
            
            if date_cols:
                date_col = date_cols[0]
                outlier_indices = outliers.index
                outlier_dates = df.loc[outlier_indices, date_col]
                
                temporal_info = {
                    "date_range": f"{outlier_dates.min().date()} to {outlier_dates.max().date()}",
                    "day_of_week_dist": outlier_dates.dt.dayofweek.value_counts().to_dict(),
                    "month_dist": outlier_dates.dt.month.value_counts().to_dict()
                }
            
            anomaly_report.append({
                "column": col,
                "anomaly_type": "statistical_outlier",
                "count": len(outliers),
                "percentage": len(outliers) / len(col_data) * 100,
                "method": "z_score_3std",
                "min_value": outliers.min(),
                "max_value": outliers.max(),
                "data_mean": mean,
                "data_std": std,
                "temporal_patterns": temporal_info
            })
            
            # Flag outliers in data
            flagged_df[f"{col}_is_outlier"] = df.index.isin(outliers.index)
    
    # 2. Impossible Value Combinations
    impossible_combos = []
    if len(numeric_cols) >= 2:
        for i, col1 in enumerate(numeric_cols):
            for col2 in numeric_cols[i+1:]:
                # Simple logical checks
                if "age" in col1.lower() and "income" in col2.lower():
                    # Check for unrealistic age-income combinations
                    mask = (df[col1] < 18) & (df[col2] > 100000)
                    if mask.any():
                        impossible_combos.append({
                            "columns": f"{col1} ↔ {col2}",
                            "rule": "age < 18 AND income > 100,000",
                            "violations": mask.sum(),
                            "percentage": mask.sum() / len(df) * 100
                        })
    
    # 3. Temporal Anomalies
    temporal_anomalies = []
    date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
    
    for date_col in date_cols[:1]:  # Check first date column only
        date_data = df[date_col].dropna()
        if len(date_data) < 10:
            continue
        
        # Check for future dates
        now = pd.Timestamp.now()
        future_dates = date_data[date_data > now + timedelta(days=1)]
        
        if len(future_dates) > 0:
            temporal_anomalies.append({
                "column": date_col,
                "anomaly_type": "future_date",
                "count": len(future_dates),
                "percentage": len(future_dates) / len(date_data) * 100,
                "max_future_date": future_dates.max().date()
            })
        
        # Check for dates too far in past (e.g., before 1900)
        old_dates = date_data[date_data < pd.Timestamp('1900-01-01')]
        if len(old_dates) > 0:
            temporal_anomalies.append({
                "column": date_col,
                "anomaly_type": "historical_date",
                "count": len(old_dates),
                "percentage": len(old_dates) / len(date_data) * 100,
                "min_date": old_dates.min().date()
            })
    
    # 4. Pattern-based anomalies (e.g., all transactions at midnight)
    pattern_anomalies = []
    if date_cols and len(numeric_cols) > 0:
        date_col = date_cols[0]
        numeric_col = numeric_cols[0]
        
        # Check for transactions at unusual hours
        if hasattr(df[date_col].dt, 'hour'):
            midnight_transactions = df[date_col].dt.hour == 0
            if midnight_transactions.any():
                pattern_anomalies.append({
                    "pattern": "midnight_transactions",
                    "count": midnight_transactions.sum(),
                    "percentage": midnight_transactions.sum() / len(df) * 100,
                    "avg_value": df.loc[midnight_transactions, numeric_col].mean() if numeric_col in df.columns else None
                })
    
    summary = {
        "columns_analyzed": len(numeric_cols) + len(date_cols),
        "statistical_outliers": len([a for a in anomaly_report if a["anomaly_type"] == "statistical_outlier"]),
        "impossible_combinations": len(impossible_combos),
        "temporal_anomalies": len(temporal_anomalies),
        "pattern_anomalies": len(pattern_anomalies)
    }
    
    return {
        "statistical_report": pd.DataFrame(anomaly_report) if anomaly_report else pd.DataFrame(),
        "impossible_combinations": pd.DataFrame(impossible_combos) if impossible_combos else pd.DataFrame(),
        "temporal_report": pd.DataFrame(temporal_anomalies) if temporal_anomalies else pd.DataFrame(),
        "pattern_report": pd.DataFrame(pattern_anomalies) if pattern_anomalies else pd.DataFrame(),
        "flagged_data": flagged_df,
        "summary": summary
    }

# ============================================================================
# FIXER SCRIPTS
# ============================================================================

def split_columns_smartly(df: pd.DataFrame, column_to_split: str = None, 
                         delimiter: str = None, **kwargs) -> Dict[str, Any]:
    """
    Split columns with inconsistent delimiters intelligently.
    
    Args:
        df: Input DataFrame
        column_to_split: Column to split (auto-detected if None)
        delimiter: Specific delimiter to use (auto-detected if None)
    
    Returns:
        Dictionary with split data and report
    """
    
    # Empty dataset handling
    if df is None or df.empty:
        return {"error": "Dataset is empty", "split_data": df}
    
    # Auto-select column if not specified
    if column_to_split is None:
        text_cols = df.select_dtypes(include=['object']).columns.tolist()
        if text_cols:
            # Choose column with highest potential for splitting
            best_col = None
            best_score = 0
            
            for col in text_cols[:5]:  # Check first 5 columns
                sample = df[col].dropna().astype(str).head(100)
                if len(sample) == 0:
                    continue
                
                # Score based on delimiter variety
                delimiters = [',', ';', '|', '\t', ' - ', '/', '\\', ':', ' ']
                score = sum(sample.str.count(d).sum() for d in delimiters) / len(sample)
                
                if score > best_score:
                    best_score = score
                    best_col = col
            
            column_to_split = best_col if best_col else text_cols[0]
        else:
            return {"error": "No text columns found", "split_data": df}
    
    if column_to_split not in df.columns:
        return {"error": f"Column '{column_to_split}' not found", "split_data": df}
    
    col_data = df[column_to_split].dropna().astype(str)
    if len(col_data) == 0:
        return {"error": f"Column '{column_to_split}' has no data", "split_data": df}
    
    # Auto-detect delimiter if not specified
    if delimiter is None:
        delimiter = _detect_delimiter(col_data)
        if delimiter is None:
            return {"error": "Could not detect a consistent delimiter", "split_data": df}
    
    # Split the column
    try:
        split_result = col_data.str.split(delimiter, expand=True)
        
        # Clean empty columns and rows
        split_result = split_result.replace('', np.nan)
        split_result = split_result.dropna(how='all', axis=1)
        
        # Remove columns that are mostly empty
        split_result = split_result.loc[:, split_result.notna().mean() > 0.1]
        
        # Name new columns based on content analysis
        n_cols = split_result.shape[1]
        column_names = _suggest_column_names(split_result, column_to_split)
        
        split_result.columns = column_names
        
        # Combine with original data
        result_df = pd.concat([df.drop(columns=[column_to_split]), split_result], axis=1)
        
        # Generate split statistics
        split_stats = {
            "original_column": column_to_split,
            "delimiter_used": repr(delimiter),
            "new_columns": column_names,
            "rows_processed": len(col_data),
            "max_parts": split_result.shape[1],
            "rows_with_missing_parts": split_result.isna().any(axis=1).sum(),
            "success_rate": (split_result.notna().any(axis=1).sum() / len(col_data)) * 100
        }
        
        return {
            "split_data": result_df,
            "split_report": split_stats,
            "summary": {
                "original_column": column_to_split,
                "new_columns_created": len(column_names),
                "delimiter_detected": delimiter,
                "split_success_rate": f"{split_stats['success_rate']:.1f}%"
            }
        }
        
    except Exception as e:
        return {"error": f"Failed to split column: {str(e)}", "split_data": df}

def handle_missing_data(df: pd.DataFrame, strategy: str = "auto", **kwargs) -> Dict[str, Any]:
    """
    Analyze missing patterns and apply optimal imputation strategy.
    
    Args:
        df: Input DataFrame
        strategy: Imputation strategy ('auto', 'drop', 'mean', 'median', 'mode', 'forward', 'interpolate')
    
    Returns:
        Dictionary with imputed data and strategy report
    """
    
    # Empty dataset handling
    if df is None or df.empty:
        return {"error": "Dataset is empty", "imputed_data": df}
    
    # Analyze missing patterns
    missing_summary = df.isnull().sum()
    missing_pct = (missing_summary / len(df)) * 100
    
    missing_analysis = pd.DataFrame({
        "column": missing_summary.index,
        "missing_count": missing_summary.values,
        "missing_percentage": missing_pct.values,
        "dtype": [str(df[col].dtype) for col in df.columns]
    })
    
    # Determine strategy for each column
    if strategy == "auto":
        strategies = _determine_auto_strategies(df, missing_pct)
    else:
        strategies = {col: strategy for col in df.columns}
    
    # Apply strategies
    cleaned_df = df.copy()
    imputation_log = []
    
    for col in df.columns:
        if missing_pct[col] == 0:
            imputation_log.append({
                "column": col,
                "missing_count": 0,
                "strategy": "none",
                "impute_value": None,
                "reason": "No missing values"
            })
            continue
        
        col_strategy = strategies.get(col, "mean")
        
        try:
            if col_strategy == "drop_column":
                cleaned_df = cleaned_df.drop(columns=[col])
                imputation_log.append({
                    "column": col,
                    "missing_count": int(missing_summary[col]),
                    "strategy": "drop_column",
                    "impute_value": None,
                    "reason": f"High missing rate ({missing_pct[col]:.1f}%)"
                })
                continue
            
            elif col_strategy == "drop_rows":
                # Will be handled at the end
                pass
            
            elif col_strategy == "mean":
                if pd.api.types.is_numeric_dtype(cleaned_df[col]):
                    impute_val = cleaned_df[col].mean()
                    cleaned_df[col] = cleaned_df[col].fillna(impute_val)
                    imputation_log.append({
                        "column": col,
                        "missing_count": int(missing_summary[col]),
                        "strategy": "mean",
                        "impute_value": float(impute_val),
                        "reason": "Numeric column with random missing"
                    })
            
            elif col_strategy == "median":
                if pd.api.types.is_numeric_dtype(cleaned_df[col]):
                    impute_val = cleaned_df[col].median()
                    cleaned_df[col] = cleaned_df[col].fillna(impute_val)
                    imputation_log.append({
                        "column": col,
                        "missing_count": int(missing_summary[col]),
                        "strategy": "median",
                        "impute_value": float(impute_val),
                        "reason": "Numeric column with skewed distribution"
                    })
            
            elif col_strategy == "mode":
                impute_val = cleaned_df[col].mode().iloc[0] if not cleaned_df[col].mode().empty else "Unknown"
                cleaned_df[col] = cleaned_df[col].fillna(impute_val)
                imputation_log.append({
                    "column": col,
                    "missing_count": int(missing_summary[col]),
                    "strategy": "mode",
                    "impute_value": str(impute_val)[:50],
                    "reason": "Categorical column"
                })
            
            elif col_strategy == "forward":
                if pd.api.types.is_datetime64_any_dtype(cleaned_df[col]) or 'date' in col.lower():
                    cleaned_df[col] = cleaned_df[col].ffill()
                    imputation_log.append({
                        "column": col,
                        "missing_count": int(missing_summary[col]),
                        "strategy": "forward_fill",
                        "impute_value": None,
                        "reason": "Temporal column"
                    })
            
            elif col_strategy == "interpolate":
                if pd.api.types.is_numeric_dtype(cleaned_df[col]):
                    cleaned_df[col] = cleaned_df[col].interpolate()
                    imputation_log.append({
                        "column": col,
                        "missing_count": int(missing_summary[col]),
                        "strategy": "interpolate",
                        "impute_value": None,
                        "reason": "Numeric time series"
                    })
            
            elif col_strategy == "constant":
                if pd.api.types.is_numeric_dtype(cleaned_df[col]):
                    impute_val = 0
                else:
                    impute_val = "Unknown"
                cleaned_df[col] = cleaned_df[col].fillna(impute_val)
                imputation_log.append({
                    "column": col,
                    "missing_count": int(missing_summary[col]),
                    "strategy": "constant",
                    "impute_value": impute_val,
                    "reason": "Fill with constant value"
                })
        
        except Exception as e:
            imputation_log.append({
                "column": col,
                "missing_count": int(missing_summary[col]),
                "strategy": "failed",
                "error": str(e)[:100],
                "reason": "Imputation failed"
            })
    
    # Handle row dropping if specified
    if any(s == "drop_rows" for s in strategies.values()):
        before_rows = len(cleaned_df)
        cleaned_df = cleaned_df.dropna()
        after_rows = len(cleaned_df)
        
        imputation_log.append({
            "column": "ALL",
            "missing_count": before_rows - after_rows,
            "strategy": "drop_rows",
            "impute_value": None,
            "reason": f"Dropped rows with any missing values ({before_rows - after_rows} rows)"
        })
    
    # Calculate summary statistics
    original_missing = missing_summary.sum()
    final_missing = cleaned_df.isnull().sum().sum()
    
    columns_dropped = len([l for l in imputation_log if l["strategy"] == "drop_column"])
    successful_imputations = len([l for l in imputation_log if l["strategy"] not in ["none", "failed", "drop_column", "drop_rows"]])
    
    return {
        "imputed_data": cleaned_df,
        "missing_analysis": missing_analysis,
        "strategy_report": pd.DataFrame(imputation_log),
        "summary": {
            "original_rows": len(df),
            "final_rows": len(cleaned_df),
            "original_missing": int(original_missing),
            "final_missing": int(final_missing),
            "missing_reduction": f"{((original_missing - final_missing) / original_missing * 100):.1f}%" if original_missing > 0 else "0%",
            "columns_dropped": columns_dropped,
            "successful_imputations": successful_imputations,
            "overall_strategy": strategy
        }
    }

def fix_date_formats(df: pd.DataFrame, date_columns: List[str] = None, 
                    output_format: str = "auto", **kwargs) -> Dict[str, Any]:
    """
    Handle mixed date formats and standardize to consistent format.
    
    Args:
        df: Input DataFrame
        date_columns: Columns to process (auto-detected if None)
        output_format: Desired output format ('auto', 'iso', 'us', 'europe')
    
    Returns:
        Dictionary with standardized dates and format report
    """
    
    # Empty dataset handling
    if df is None or df.empty:
        return {"error": "Dataset is empty", "standardized_dates": df}
    
    # Auto-detect date columns
    if date_columns is None:
        date_columns = _detect_date_columns(df)
    
    if not date_columns:
        return {"error": "No date-like columns found", "standardized_dates": df}
    
    # Define format mapping for output
    format_map = {
        "iso": "%Y-%m-%d",
        "us": "%m/%d/%Y",
        "europe": "%d/%m/%Y",
        "standard": "%Y-%m-%d %H:%M:%S"
    }
    
    output_fmt = format_map.get(output_format, None)
    
    cleaned_df = df.copy()
    conversion_log = []
    
    for col in date_columns:
        if col not in df.columns:
            continue
        
        original_data = df[col].copy()
        original_dtype = str(df[col].dtype)
        
        # Track conversion attempts
        attempts = []
        
        # Already datetime
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            cleaned_df[col] = pd.to_datetime(df[col])
            attempts.append({
                "method": "already_datetime",
                "success_rate": 1.0,
                "format": "datetime64"
            })
        
        else:
            # Try common date formats
            common_formats = [
                '%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d',
                '%d-%m-%Y', '%d/%m/%Y', '%d.%m.%Y',
                '%m-%d-%Y', '%m/%d/%Y', '%m.%d.%Y',
                '%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S',
                '%d-%b-%Y', '%d %b %Y', '%b %d, %Y',
                '%d-%B-%Y', '%d %B %Y', '%B %d, %Y',
                '%Y%m%d', '%d%m%Y', '%m%d%Y'
            ]
            
            best_format = None
            best_success = 0
            
            for fmt in common_formats:
                try:
                    parsed = pd.to_datetime(df[col], format=fmt, errors='coerce')
                    success_rate = parsed.notna().mean()
                    attempts.append({
                        "method": "format_specific",
                        "format": fmt,
                        "success_rate": float(success_rate)
                    })
                    
                    if success_rate > best_success:
                        best_success = success_rate
                        best_format = fmt
                except:
                    continue
            
            # Try generic parsing
            generic_parsed = pd.to_datetime(df[col], errors='coerce')
            generic_success = generic_parsed.notna().mean()
            attempts.append({
                "method": "generic_parsing",
                "format": "infer",
                "success_rate": float(generic_success)
            })
            
            # Choose best method
            if best_format and best_success >= generic_success:
                cleaned_df[col] = pd.to_datetime(df[col], format=best_format, errors='coerce')
                used_method = "format_specific"
                used_format = best_format
                success_rate = best_success
            else:
                cleaned_df[col] = generic_parsed
                used_method = "generic_parsing"
                used_format = "infer"
                success_rate = generic_success
        
        # Format output if requested
        if output_fmt and pd.api.types.is_datetime64_any_dtype(cleaned_df[col]):
            cleaned_df[f"{col}_formatted"] = cleaned_df[col].dt.strftime(output_fmt)
        
        # Calculate conversion statistics
        converted_count = cleaned_df[col].notna().sum()
        failed_count = cleaned_df[col].isna().sum() - original_data.isna().sum()
        
        conversion_log.append({
            "column": col,
            "original_type": original_dtype,
            "conversion_method": used_method if 'used_method' in locals() else "already_datetime",
            "format_used": used_format if 'used_format' in locals() else original_dtype,
            "success_rate": float(success_rate) if 'success_rate' in locals() else 1.0,
            "converted_rows": int(converted_count),
            "failed_rows": int(failed_count),
            "output_format": output_fmt if output_fmt else "keep_datetime"
        })
    
    summary = {
        "columns_processed": len(date_columns),
        "successful_conversions": len([l for l in conversion_log if l["success_rate"] > 0.7]),
        "average_success_rate": np.mean([l["success_rate"] for l in conversion_log]),
        "output_format": output_format
    }
    
    return {
        "standardized_dates": cleaned_df,
        "format_report": pd.DataFrame(conversion_log),
        "summary": summary
    }

# ============================================================================
# TRANSFORMER SCRIPTS
# ============================================================================

def build_cohort_analysis(df: pd.DataFrame, customer_id_col: str = None,
                         date_col: str = None, value_col: str = None,
                         time_unit: str = "month", **kwargs) -> Dict[str, Any]:
    """
    Build cohort retention analysis from transaction data.
    
    Args:
        df: Input DataFrame with transaction data
        customer_id_col: Column containing customer IDs
        date_col: Column containing transaction dates
        value_col: Column containing transaction values
        time_unit: Time unit for cohorts ('day', 'week', 'month', 'quarter')
    
    Returns:
        Dictionary with cohort matrices and analysis
    """
    
    # Empty dataset handling
    if df is None or df.empty:
        return {"error": "Dataset is empty"}
    
    # Auto-detect columns
    auto_detected = _auto_detect_cohort_columns(df)
    
    if customer_id_col is None:
        customer_id_col = auto_detected.get("customer_id")
    if date_col is None:
        date_col = auto_detected.get("date")
    if value_col is None:
        value_col = auto_detected.get("value")
    
    # Validate required columns
    missing_cols = []
    if customer_id_col is None:
        missing_cols.append("customer_id")
    if date_col is None:
        missing_cols.append("date")
    
    if missing_cols:
        return {"error": f"Missing required columns: {', '.join(missing_cols)}"}
    
    # Prepare data
    cohort_df = df.copy()
    
    # Convert date to datetime
    cohort_df['cohort_date'] = pd.to_datetime(cohort_df[date_col], errors='coerce')
    cohort_df = cohort_df.dropna(subset=['cohort_date', customer_id_col])
    
    if len(cohort_df) == 0:
        return {"error": "No valid data for cohort analysis"}
    
    # Determine time unit frequency
    freq_map = {
        "day": "D",
        "week": "W",
        "month": "M",
        "quarter": "Q"
    }
    freq = freq_map.get(time_unit, "M")
    
    # Calculate cohort periods
    cohort_df['cohort_period'] = cohort_df.groupby(customer_id_col)['cohort_date'].transform('min').dt.to_period(freq)
    cohort_df['order_period'] = cohort_df['cohort_date'].dt.to_period(freq)
    
    # Calculate cohort index (periods since first purchase)
    cohort_df['cohort_index'] = (cohort_df['order_period'] - cohort_df['cohort_period']).apply(lambda x: x.n)
    
    # Create cohort matrices
    # 1. User cohort matrix (retention)
    user_cohort_data = cohort_df.groupby(['cohort_period', 'cohort_index'])[customer_id_col].nunique()
    user_cohort_matrix = user_cohort_data.unstack(level=0)
    
    # 2. Revenue cohort matrix (if value column provided)
    if value_col and value_col in cohort_df.columns:
        revenue_cohort_data = cohort_df.groupby(['cohort_period', 'cohort_index'])[value_col].sum()
        revenue_cohort_matrix = revenue_cohort_data.unstack(level=0)
    else:
        revenue_cohort_matrix = pd.DataFrame()
        value_col = None
    
    # Calculate retention percentages
    cohort_sizes = user_cohort_matrix.iloc[0]
    retention_matrix = user_cohort_matrix.divide(cohort_sizes, axis=1) * 100
    
    # Create cohort summary
    cohort_summary = pd.DataFrame({
        'cohort': cohort_sizes.index.astype(str),
        'cohort_size': cohort_sizes.values,
        'avg_retention_1': retention_matrix.loc[1] if 1 in retention_matrix.index else 0,
        'avg_retention_3': retention_matrix.loc[3] if 3 in retention_matrix.index else 0,
        'avg_retention_6': retention_matrix.loc[6] if 6 in retention_matrix.index else 0
    })
    
    if value_col:
        cohort_summary['avg_order_value'] = revenue_cohort_matrix.loc[0] / cohort_sizes if 0 in revenue_cohort_matrix.index else 0
        cohort_summary['total_revenue'] = revenue_cohort_matrix.loc[0] if 0 in revenue_cohort_matrix.index else 0
    
    # Calculate key metrics
    total_cohorts = len(cohort_sizes)
    avg_cohort_size = cohort_sizes.mean()
    avg_retention = retention_matrix.mean().mean()
    
    if value_col:
        total_revenue = revenue_cohort_matrix.sum().sum()
        avg_revenue_per_user = total_revenue / cohort_sizes.sum() if cohort_sizes.sum() > 0 else 0
    else:
        total_revenue = None
        avg_revenue_per_user = None
    
    return {
        "cohort_data": cohort_df,
        "user_cohort_matrix": user_cohort_matrix,
        "revenue_cohort_matrix": revenue_cohort_matrix if value_col else pd.DataFrame(),
        "retention_matrix": retention_matrix,
        "cohort_summary": cohort_summary,
        "summary": {
            "total_cohorts": total_cohorts,
            "total_users": int(cohort_sizes.sum()),
            "average_cohort_size": float(avg_cohort_size),
            "average_retention_rate": float(avg_retention),
            "total_revenue": float(total_revenue) if total_revenue else None,
            "average_revenue_per_user": float(avg_revenue_per_user) if avg_revenue_per_user else None,
            "time_unit": time_unit,
            "date_range": f"{cohort_df['cohort_date'].min().date()} to {cohort_df['cohort_date'].max().date()}",
            "columns_used": {
                "customer_id": customer_id_col,
                "date": date_col,
                "value": value_col
            }
        }
    }

def decompose_time_series(df: pd.DataFrame, date_col: str = None,
                         value_col: str = None, frequency: str = "auto",
                         model: str = "additive", **kwargs) -> Dict[str, Any]:
    """
    Decompose time series into trend, seasonality, and residual components.
    
    Args:
        df: Input DataFrame
        date_col: Column containing dates
        value_col: Column containing values to decompose
        frequency: Time series frequency ('auto', 'D', 'W', 'M', 'Q', 'Y')
        model: Decomposition model ('additive' or 'multiplicative')
    
    Returns:
        Dictionary with decomposition components and analysis
    """
    
    # Empty dataset handling
    if df is None or df.empty:
        return {"error": "Dataset is empty"}
    
    # Dependency check
    if not STATSMODELS_AVAILABLE:
        return {
            "warning": "Time series decomposition requires statsmodels",
            "error": "Missing dependency: pip install statsmodels",
            "decomposition": pd.DataFrame()
        }
    
    # Auto-detect columns
    if date_col is None:
        date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
        date_col = date_cols[0] if date_cols else None
    
    if value_col is None:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        value_col = numeric_cols[0] if numeric_cols else None
    
    if date_col is None or value_col is None:
        return {"error": "Need both date and numeric columns for time series decomposition"}
    
    # Prepare time series
    ts_df = df.copy()
    ts_df['date'] = pd.to_datetime(ts_df[date_col], errors='coerce')
    ts_df = ts_df.dropna(subset=['date', value_col])
    
    if len(ts_df) < 10:
        return {"error": "Insufficient data for time series decomposition (need at least 10 points)"}
    
    # Set date as index and sort
    ts_df = ts_df.set_index('date').sort_index()
    time_series = ts_df[value_col]
    
    # Determine frequency if auto
    if frequency == "auto":
        frequency = _detect_time_series_frequency(time_series)
    
    # Resample to consistent frequency if needed
    if frequency:
        try:
            # Map frequency strings to pandas offset aliases
            freq_map = {
                'D': 'D', 'daily': 'D',
                'W': 'W', 'weekly': 'W',
                'M': 'MS', 'monthly': 'MS',
                'Q': 'QS', 'quarterly': 'QS',
                'Y': 'YS', 'yearly': 'YS'
            }
            
            resample_freq = freq_map.get(frequency, frequency)
            time_series = time_series.resample(resample_freq).mean().ffill()
        except Exception as e:
            return {"error": f"Failed to resample time series: {str(e)}"}
    
    # Perform decomposition
    try:
        from statsmodels.tsa.seasonal import seasonal_decompose
        
        # Determine period based on frequency
        if frequency in ['D', 'daily']:
            period = 7  # Weekly seasonality
        elif frequency in ['W', 'weekly']:
            period = 52  # Yearly seasonality
        elif frequency in ['M', 'MS', 'monthly']:
            period = 12  # Yearly seasonality
        elif frequency in ['Q', 'QS', 'quarterly']:
            period = 4  # Yearly seasonality
        elif frequency in ['Y', 'YS', 'yearly']:
            period = None  # No seasonality for yearly data
        else:
            period = len(time_series) // 2  # Default heuristic
        
        if period is not None and len(time_series) < period * 2:
            period = len(time_series) // 2
        
        decomposition = seasonal_decompose(
            time_series.dropna(),
            model=model,
            period=period,
            extrapolate_trend='freq'
        )
        
        # Create decomposition DataFrame
        decomp_df = pd.DataFrame({
            'observed': decomposition.observed,
            'trend': decomposition.trend,
            'seasonal': decomposition.seasonal,
            'residual': decomposition.resid
        })
        
        # Calculate statistics
        trend_strength = 1 - (decomposition.resid.var() / (decomposition.trend + decomposition.resid).var())
        seasonality_strength = 1 - (decomposition.resid.var() / (decomposition.seasonal + decomposition.resid).var())
        
        # Identify outliers in residuals
        resid_mean = decomposition.resid.mean()
        resid_std = decomposition.resid.std()
        outliers = decomposition.resid[
            (decomposition.resid < resid_mean - 2*resid_std) | 
            (decomposition.resid > resid_mean + 2*resid_std)
        ]
        
        summary = {
            "time_series_length": len(time_series),
            "frequency": frequency,
            "model": model,
            "period": period,
            "trend_strength": float(trend_strength),
            "seasonality_strength": float(seasonality_strength),
            "outliers_count": len(outliers),
            "variance_explained": float(1 - (decomposition.resid.var() / decomposition.observed.var())),
            "columns_used": {
                "date": date_col,
                "value": value_col
            }
        }
        
        return {
            "decomposition": decomp_df,
            "statistics": summary,
            "outliers": outliers,
            "components": {
                "observed": decomposition.observed,
                "trend": decomposition.trend,
                "seasonal": decomposition.seasonal,
                "residual": decomposition.resid
            }
        }
        
    except ImportError:
        return {"error": "statsmodels library required for time series decomposition"}
    except Exception as e:
        return {"error": f"Decomposition failed: {str(e)}"}

def engineer_features(df: pd.DataFrame, target_column: str = None,
                     exclude_columns: List[str] = None, **kwargs) -> Dict[str, Any]:
    """
    Generate machine learning features from raw data.
    
    Args:
        df: Input DataFrame
        target_column: Target variable for supervised feature engineering
        exclude_columns: Columns to exclude from feature engineering
    
    Returns:
        Dictionary with engineered features and feature report
    """
    
    # Empty dataset handling
    if df is None or df.empty:
        return {"error": "Dataset is empty", "enhanced_data": df}
    
    if exclude_columns is None:
        exclude_columns = []
    
    # Create copy for feature engineering
    feature_df = df.copy()
    feature_report = []
    
    # Track original columns
    original_columns = set(feature_df.columns)
    
    # 1. Date Feature Engineering
    date_cols = [c for c in feature_df.columns if pd.api.types.is_datetime64_any_dtype(feature_df[c])]
    
    for col in date_cols:
        if col in exclude_columns:
            continue
        
        try:
            # Extract temporal features
            feature_df[f'{col}_year'] = feature_df[col].dt.year
            feature_df[f'{col}_month'] = feature_df[col].dt.month
            feature_df[f'{col}_day'] = feature_df[col].dt.day
            feature_df[f'{col}_dayofweek'] = feature_df[col].dt.dayofweek
            feature_df[f'{col}_dayofyear'] = feature_df[col].dt.dayofyear
            feature_df[f'{col}_week'] = feature_df[col].dt.isocalendar().week
            feature_df[f'{col}_quarter'] = feature_df[col].dt.quarter
            
            # Boolean features
            feature_df[f'{col}_is_weekend'] = feature_df[col].dt.dayofweek.isin([5, 6]).astype(int)
            feature_df[f'{col}_is_month_end'] = feature_df[col].dt.is_month_end.astype(int)
            feature_df[f'{col}_is_month_start'] = feature_df[col].dt.is_month_start.astype(int)
            feature_df[f'{col}_is_quarter_end'] = feature_df[col].dt.is_quarter_end.astype(int)
            feature_df[f'{col}_is_quarter_start'] = feature_df[col].dt.is_quarter_start.astype(int)
            feature_df[f'{col}_is_year_end'] = feature_df[col].dt.is_year_end.astype(int)
            feature_df[f'{col}_is_year_start'] = feature_df[col].dt.is_year_start.astype(int)
            
            # Cyclical features
            feature_df[f'{col}_month_sin'] = np.sin(2 * np.pi * feature_df[col].dt.month / 12)
            feature_df[f'{col}_month_cos'] = np.cos(2 * np.pi * feature_df[col].dt.month / 12)
            feature_df[f'{col}_dayofweek_sin'] = np.sin(2 * np.pi * feature_df[col].dt.dayofweek / 7)
            feature_df[f'{col}_dayofweek_cos'] = np.cos(2 * np.pi * feature_df[col].dt.dayofweek / 7)
            
            feature_report.append({
                "feature_type": "date",
                "original_column": col,
                "features_created": 15,
                "notes": "Temporal features extracted"
            })
            
        except Exception as e:
            feature_report.append({
                "feature_type": "date",
                "original_column": col,
                "error": str(e)[:100]
            })
    
    # 2. Numeric Feature Engineering
    numeric_cols = feature_df.select_dtypes(include=[np.number]).columns.tolist()
    numeric_cols = [c for c in numeric_cols if c not in exclude_columns and c not in date_cols]
    
    for col in numeric_cols[:10]:  # Limit to first 10 numeric columns
        try:
            # Basic transformations
            feature_df[f'{col}_log'] = np.log1p(np.abs(feature_df[col]))
            feature_df[f'{col}_sqrt'] = np.sqrt(np.abs(feature_df[col]))
            feature_df[f'{col}_squared'] = feature_df[col] ** 2
            feature_df[f'{col}_cubed'] = feature_df[col] ** 3
            
            # Statistical features
            feature_df[f'{col}_zscore'] = (feature_df[col] - feature_df[col].mean()) / feature_df[col].std()
            
            # Binning
            feature_df[f'{col}_bin_5'] = pd.qcut(feature_df[col], 5, labels=False, duplicates='drop')
            feature_df[f'{col}_bin_10'] = pd.qcut(feature_df[col], 10, labels=False, duplicates='drop')
            
            feature_report.append({
                "feature_type": "numeric",
                "original_column": col,
                "features_created": 7,
                "notes": "Transformations and binnings"
            })
            
        except Exception as e:
            feature_report.append({
                "feature_type": "numeric",
                "original_column": col,
                "error": str(e)[:100]
            })
    
    # 3. Categorical Feature Engineering
    categorical_cols = feature_df.select_dtypes(include=['object', 'category']).columns.tolist()
    categorical_cols = [c for c in categorical_cols if c not in exclude_columns]
    
    for col in categorical_cols[:5]:  # Limit to first 5 categorical columns
        try:
            # Only process if reasonable number of categories
            n_unique = feature_df[col].nunique()
            if 2 <= n_unique <= 20:
                # Frequency encoding
                freq_encoding = feature_df[col].value_counts(normalize=True)
                feature_df[f'{col}_freq'] = feature_df[col].map(freq_encoding)
                
                # Target encoding (if target provided)
                if target_column and target_column in feature_df.columns:
                    if pd.api.types.is_numeric_dtype(feature_df[target_column]):
                        target_mean = feature_df.groupby(col)[target_column].mean()
                        feature_df[f'{col}_target_mean'] = feature_df[col].map(target_mean)
                
                feature_report.append({
                    "feature_type": "categorical",
                    "original_column": col,
                    "features_created": 2 if target_column else 1,
                    "unique_values": n_unique,
                    "notes": "Encoding features"
                })
            
        except Exception as e:
            feature_report.append({
                "feature_type": "categorical",
                "original_column": col,
                "error": str(e)[:100]
            })
    
    # 4. Interaction Features
    if len(numeric_cols) >= 2:
        try:
            # Create some meaningful interactions
            for i in range(min(3, len(numeric_cols))):
                for j in range(i + 1, min(4, len(numeric_cols))):
                    col1, col2 = numeric_cols[i], numeric_cols[j]
                    feature_df[f'{col1}_x_{col2}'] = feature_df[col1] * feature_df[col2]
                    feature_df[f'{col1}_div_{col2}'] = feature_df[col1] / (feature_df[col2] + 1e-10)
            
            feature_report.append({
                "feature_type": "interaction",
                "features_created": 6,  # 3 choose 2 * 2
                "notes": "Numeric interaction features"
            })
            
        except Exception as e:
            feature_report.append({
                "feature_type": "interaction",
                "error": str(e)[:100]
            })
    
    # 5. Lag Features (for time series)
    if date_cols and len(numeric_cols) > 0:
        date_col = date_cols[0]
        numeric_col = numeric_cols[0]
        
        try:
            # Sort by date
            temp_df = feature_df.sort_values(date_col).copy()
            
            # Create lag features
            for lag in [1, 7, 30]:  # 1 day, 1 week, 1 month lags
                if len(temp_df) > lag:
                    temp_df[f'{numeric_col}_lag_{lag}'] = temp_df[numeric_col].shift(lag)
            
            feature_df = temp_df
            
            feature_report.append({
                "feature_type": "lag",
                "original_column": numeric_col,
                "features_created": 3,
                "notes": "Time series lag features"
            })
            
        except Exception as e:
            feature_report.append({
                "feature_type": "lag",
                "error": str(e)[:100]
            })
    
    # Calculate feature statistics
    new_columns = set(feature_df.columns) - original_columns
    total_features = len(new_columns)
    
    # Feature importance estimation (if target provided)
    if target_column and target_column in feature_df.columns:
        try:
            # Simple correlation-based importance
            numeric_features = feature_df.select_dtypes(include=[np.number]).columns.tolist()
            numeric_features = [f for f in numeric_features if f != target_column]
            
            correlations = feature_df[numeric_features].corrwith(feature_df[target_column]).abs()
            top_features = correlations.nlargest(10)
            
            feature_importance = pd.DataFrame({
                'feature': top_features.index,
                'correlation_with_target': top_features.values
            })
        except:
            feature_importance = pd.DataFrame()
    else:
        feature_importance = pd.DataFrame()
    
    summary = {
        "original_features": len(original_columns),
        "new_features_created": total_features,
        "total_features": len(feature_df.columns),
        "feature_types_created": len(set(item.get("feature_type", "") for item in feature_report)),
        "target_column": target_column,
        "has_feature_importance": not feature_importance.empty
    }
    
    return {
        "enhanced_data": feature_df,
        "feature_report": pd.DataFrame(feature_report),
        "feature_importance": feature_importance,
        "summary": summary
    }

# ============================================================================
# BUSINESS INTELLIGENCE SCRIPTS
# ============================================================================

def segment_customers_rfm(df: pd.DataFrame, customer_id_col: str = None,
                         date_col: str = None, value_col: str = None,
                         **kwargs) -> Dict[str, Any]:
    """
    Segment customers using RFM (Recency, Frequency, Monetary) analysis.
    
    Args:
        df: Input DataFrame with transaction data
        customer_id_col: Column containing customer IDs
        date_col: Column containing transaction dates
        value_col: Column containing transaction values
    
    Returns:
        Dictionary with RFM segments and analysis
    """
    
    # Empty dataset handling
    if df is None or df.empty:
        return {"error": "Dataset is empty"}
    
    # Auto-detect columns
    auto_detected = _auto_detect_cohort_columns(df)
    
    if customer_id_col is None:
        customer_id_col = auto_detected.get("customer_id")
    if date_col is None:
        date_col = auto_detected.get("date")
    if value_col is None:
        value_col = auto_detected.get("value")
    
    # Validate required columns
    missing_cols = []
    if customer_id_col is None:
        missing_cols.append("customer_id")
    if date_col is None:
        missing_cols.append("date")
    if value_col is None:
        missing_cols.append("value")
    
    if missing_cols:
        return {"error": f"Missing required columns: {', '.join(missing_cols)}"}
    
    # Prepare data
    rfm_df = df.copy()
    
    # Convert date to datetime
    rfm_df['transaction_date'] = pd.to_datetime(rfm_df[date_col], errors='coerce')
    rfm_df = rfm_df.dropna(subset=['transaction_date', customer_id_col, value_col])
    
    if len(rfm_df) == 0:
        return {"error": "No valid data for RFM analysis"}
    
    # Calculate RFM metrics
    max_date = rfm_df['transaction_date'].max()
    
    rfm_metrics = rfm_df.groupby(customer_id_col).agg({
        'transaction_date': lambda x: (max_date - x.max()).days,  # Recency (days since last purchase)
        customer_id_col: 'count',  # Frequency (number of purchases)
        value_col: 'sum'  # Monetary (total spending)
    }).rename(columns={
        'transaction_date': 'recency',
        customer_id_col: 'frequency',
        value_col: 'monetary'
    })
    
    # Create RFM scores (1-4, where 4 is best)
    rfm_metrics['R_score'] = pd.qcut(rfm_metrics['recency'], 4, labels=[4, 3, 2, 1])
    rfm_metrics['F_score'] = pd.qcut(rfm_metrics['frequency'], 4, labels=[1, 2, 3, 4])
    rfm_metrics['M_score'] = pd.qcut(rfm_metrics['monetary'], 4, labels=[1, 2, 3, 4])
    
    # Combine scores
    rfm_metrics['RFM_Score'] = (
        rfm_metrics['R_score'].astype(str) + 
        rfm_metrics['F_score'].astype(str) + 
        rfm_metrics['M_score'].astype(str)
    )
    
    # Define RFM segments
    segment_map = {
        '444': 'Champions', '443': 'Champions', '434': 'Champions', '433': 'Champions',
        '344': 'Loyal Customers', '343': 'Loyal Customers', '334': 'Loyal Customers', '333': 'Loyal Customers',
        '244': 'Potential Loyalists', '243': 'Potential Loyalists', '234': 'Potential Loyalists', '233': 'Potential Loyalists',
        '144': 'Recent Customers', '143': 'Recent Customers', '134': 'Recent Customers', '133': 'Recent Customers',
        '424': 'Promising', '423': 'Promising', '414': 'Promising', '413': 'Promising',
        '324': 'Need Attention', '323': 'Need Attention', '314': 'Need Attention', '313': 'Need Attention',
        '224': 'About To Sleep', '223': 'About To Sleep', '214': 'About To Sleep', '213': 'About To Sleep',
        '124': 'At Risk', '123': 'At Risk', '114': 'At Risk', '113': 'At Risk',
        '422': 'Cannot Lose Them', '421': 'Cannot Lose Them', '412': 'Cannot Lose Them', '411': 'Cannot Lose Them',
        '322': 'Hibernating', '321': 'Hibernating', '312': 'Hibernating', '311': 'Hibernating',
        '222': 'Lost', '221': 'Lost', '212': 'Lost', '211': 'Lost', '111': 'Lost'
    }
    
    rfm_metrics['segment'] = rfm_metrics['RFM_Score'].map(segment_map).fillna('Unclassified')
    
    # Define action recommendations
    action_map = {
        'Champions': 'Reward them. Can be early adopters for new products.',
        'Loyal Customers': 'Upsell higher value products. Ask for reviews.',
        'Potential Loyalists': 'Offer membership or loyalty program.',
        'Recent Customers': 'Provide onboarding support. Encourage first purchase.',
        'Promising': 'Create brand awareness. Offer free trials.',
        'Need Attention': 'Share success stories. Recommend based on purchase history.',
        'About To Sleep': 'Share valuable resources. Re-engage with promotions.',
        'At Risk': 'Send personalized emails to reconnect. Offer renewals.',
        'Cannot Lose Them': 'Win them back via renewals or new products.',
        'Hibernating': 'Re-activate with reach out campaign. Offer discounts.',
        'Lost': 'Revive interest with reach out campaign.'
    }
    
    rfm_metrics['action'] = rfm_metrics['segment'].map(action_map).fillna('Monitor and engage')
    
    # Calculate segment statistics
    segment_stats = rfm_metrics.groupby('segment').agg({
        'recency': 'mean',
        'frequency': 'mean',
        'monetary': 'mean',
        customer_id_col: 'count'
    }).rename(columns={customer_id_col: 'customer_count'}).round(2)
    
    segment_stats['percentage'] = (segment_stats['customer_count'] / len(rfm_metrics) * 100).round(1)
    segment_stats = segment_stats.sort_values('customer_count', ascending=False)
    
    # Calculate overall statistics
    total_customers = len(rfm_metrics)
    champions = segment_stats.loc['Champions', 'customer_count'] if 'Champions' in segment_stats.index else 0
    at_risk = segment_stats.loc['At Risk', 'customer_count'] if 'At Risk' in segment_stats.index else 0
    lost = segment_stats.loc['Lost', 'customer_count'] if 'Lost' in segment_stats.index else 0
    
    summary = {
        "total_customers": total_customers,
        "total_segments": len(segment_stats),
        "champions_percentage": round(champions / total_customers * 100, 1) if total_customers > 0 else 0,
        "at_risk_percentage": round(at_risk / total_customers * 100, 1) if total_customers > 0 else 0,
        "lost_percentage": round(lost / total_customers * 100, 1) if total_customers > 0 else 0,
        "average_recency": round(rfm_metrics['recency'].mean(), 1),
        "average_frequency": round(rfm_metrics['frequency'].mean(), 2),
        "average_monetary": round(rfm_metrics['monetary'].mean(), 2),
        "total_monetary": round(rfm_metrics['monetary'].sum(), 2),
        "date_range": f"{rfm_df['transaction_date'].min().date()} to {rfm_df['transaction_date'].max().date()}",
        "columns_used": {
            "customer_id": customer_id_col,
            "date": date_col,
            "value": value_col
        }
    }
    
    return {
        "rfm_scores": rfm_metrics,
        "segment_statistics": segment_stats,
        "action_plan": rfm_metrics[['segment', 'action']].drop_duplicates().set_index('segment')['action'].to_dict(),
        "summary": summary
    }

def analyze_pricing(df: pd.DataFrame, price_col: str = None,
                   quantity_col: str = None, product_col: str = None,
                   **kwargs) -> Dict[str, Any]:
    """
    Analyze pricing data for elasticity and optimal pricing.
    
    Args:
        df: Input DataFrame with pricing data
        price_col: Column containing prices
        quantity_col: Column containing quantities sold
        product_col: Column containing product identifiers
    
    Returns:
        Dictionary with pricing analysis and recommendations
    """
    
    # Empty dataset handling
    if df is None or df.empty:
        return {"error": "Dataset is empty"}
    
    # Auto-detect columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    text_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    if price_col is None:
        # Look for price-like columns
        price_candidates = [c for c in df.columns if 'price' in c.lower() or 'cost' in c.lower() or 'amount' in c.lower()]
        price_col = price_candidates[0] if price_candidates else (numeric_cols[0] if numeric_cols else None)
    
    if quantity_col is None:
        # Look for quantity-like columns
        qty_candidates = [c for c in df.columns if 'qty' in c.lower() or 'quantity' in c.lower() or 'volume' in c.lower()]
        quantity_col = qty_candidates[0] if qty_candidates else (numeric_cols[1] if len(numeric_cols) > 1 else None)
    
    if product_col is None and text_cols:
        product_col = text_cols[0]
    
    # Validate required columns
    if price_col is None or quantity_col is None:
        return {"error": "Need both price and quantity columns for pricing analysis"}
    
    # Prepare data
    pricing_df = df.copy()
    pricing_df = pricing_df.dropna(subset=[price_col, quantity_col])
    
    if len(pricing_df) == 0:
        return {"error": "No valid data for pricing analysis"}
    
    # Calculate basic metrics
    pricing_df['revenue'] = pricing_df[price_col] * pricing_df[quantity_col]
    
    # Product-level analysis (if product column provided)
    if product_col and product_col in pricing_df.columns:
        product_analysis = pricing_df.groupby(product_col).agg({
            price_col: ['mean', 'std', 'min', 'max'],
            quantity_col: ['sum', 'mean', 'std'],
            'revenue': 'sum'
        }).round(2)
        
        # Flatten column names
        product_analysis.columns = ['_'.join(col).strip() for col in product_analysis.columns.values]
        product_analysis = product_analysis.reset_index()
        
        # Calculate price elasticity approximation
        product_analysis['price_elasticity'] = _estimate_price_elasticity(pricing_df, product_col, price_col, quantity_col)
        
        # Identify optimal price points (simplified)
        product_analysis['suggested_price'] = product_analysis.apply(
            lambda row: row[f'{price_col}_mean'] * 1.1 if row['price_elasticity'] < 1 else row[f'{price_col}_mean'] * 0.9,
            axis=1
        )
    else:
        product_analysis = pd.DataFrame()
    
    # Overall pricing analysis
    price_stats = {
        "average_price": float(pricing_df[price_col].mean()),
        "price_std": float(pricing_df[price_col].std()),
        "price_range": f"{pricing_df[price_col].min()} - {pricing_df[price_col].max()}",
        "median_price": float(pricing_df[price_col].median()),
        "price_skewness": float(pricing_df[price_col].skew())
    }
    
    quantity_stats = {
        "total_quantity": int(pricing_df[quantity_col].sum()),
        "average_quantity": float(pricing_df[quantity_col].mean()),
        "quantity_std": float(pricing_df[quantity_col].std())
    }
    
    revenue_stats = {
        "total_revenue": float(pricing_df['revenue'].sum()),
        "average_revenue_per_transaction": float(pricing_df['revenue'].mean()),
        "revenue_std": float(pricing_df['revenue'].std())
    }
    
    # Price-quantity relationship
    correlation = pricing_df[[price_col, quantity_col]].corr().iloc[0, 1]
    
    # Price segments analysis
    price_bins = pd.qcut(pricing_df[price_col], 4, labels=['Low', 'Medium-Low', 'Medium-High', 'High'])
    segment_analysis = pricing_df.groupby(price_bins).agg({
        quantity_col: 'sum',
        'revenue': 'sum',
        price_col: 'count'
    }).rename(columns={price_col: 'transaction_count'})
    
    segment_analysis['avg_price'] = pricing_df.groupby(price_bins)[price_col].mean()
    segment_analysis['avg_quantity'] = pricing_df.groupby(price_bins)[quantity_col].mean()
    segment_analysis = segment_analysis.round(2)
    
    # Recommendations
    recommendations = []
    
    if correlation < -0.3:
        recommendations.append({
            "type": "elastic_demand",
            "message": "Demand appears price-elastic (quantity decreases with price increases)",
            "suggestion": "Consider lowering prices to increase total revenue"
        })
    elif correlation > 0.3:
        recommendations.append({
            "type": "inelastic_demand",
            "message": "Demand appears price-inelastic (quantity increases with price)",
            "suggestion": "Consider testing price increases"
        })
    
    # Identify best-performing price segment
    best_segment = segment_analysis['revenue'].idxmax() if not segment_analysis.empty else None
    
    if best_segment:
        recommendations.append({
            "type": "best_segment",
            "message": f"Best revenue from '{best_segment}' price segment",
            "suggestion": f"Focus marketing on {best_segment.lower()} price points"
        })
    
    summary = {
        "total_transactions": len(pricing_df),
        "price_quantity_correlation": float(correlation),
        "products_analyzed": len(product_analysis) if not product_analysis.empty else 0,
        "price_segments": len(segment_analysis),
        "columns_used": {
            "price": price_col,
            "quantity": quantity_col,
            "product": product_col
        },
        "recommendations_count": len(recommendations)
    }
    
    return {
        "product_analysis": product_analysis,
        "price_statistics": price_stats,
        "quantity_statistics": quantity_stats,
        "revenue_statistics": revenue_stats,
        "segment_analysis": segment_analysis,
        "recommendations": pd.DataFrame(recommendations) if recommendations else pd.DataFrame(),
        "summary": summary
    }

def analyze_ab_test(df: pd.DataFrame, group_col: str = None,
                   metric_col: str = None, **kwargs) -> Dict[str, Any]:
    """
    Analyze A/B test results with statistical significance.
    
    Args:
        df: Input DataFrame with test data
        group_col: Column containing test groups (A/B variants)
        metric_col: Column containing performance metric
    
    Returns:
        Dictionary with A/B test analysis and statistical results
    """
    
    # Empty dataset handling
    if df is None or df.empty:
        return {"error": "Dataset is empty"}
    
    # Dependency check
    if not SCIPY_AVAILABLE:
        return {
            "warning": "A/B test analysis requires scipy",
            "error": "Missing dependency: pip install scipy",
            "group_statistics": pd.DataFrame()
        }
    
    # Auto-detect columns
    if group_col is None:
        # Look for group-like columns
        group_candidates = [c for c in df.columns if 'group' in c.lower() or 'variant' in c.lower() or 'test' in c.lower()]
        if group_candidates:
            group_col = group_candidates[0]
        else:
            # Look for columns with few unique values (potential groups)
            for col in df.columns:
                if df[col].nunique() <= 5 and df[col].nunique() >= 2:
                    group_col = col
                    break
    
    if metric_col is None:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        metric_col = numeric_cols[0] if numeric_cols else None
    
    if group_col is None or metric_col is None:
        return {"error": "Need both group and metric columns for A/B test analysis"}
    
    # Prepare data
    ab_df = df.copy()
    ab_df = ab_df.dropna(subset=[group_col, metric_col])
    
    if len(ab_df) == 0:
        return {"error": "No valid data for A/B test analysis"}
    
    # Get unique groups
    groups = ab_df[group_col].unique()
    if len(groups) < 2:
        return {"error": "Need at least 2 groups for A/B test analysis"}
    
    # Limit to top 5 groups for clarity
    groups = groups[:5]
    ab_df = ab_df[ab_df[group_col].isin(groups)]
    
    # Calculate group statistics
    group_stats = []
    
    for group in groups:
        group_data = ab_df[ab_df[group_col] == group][metric_col]
        
        stats = {
            "group": group,
            "sample_size": len(group_data),
            "mean": float(group_data.mean()),
            "std": float(group_data.std()),
            "min": float(group_data.min()),
            "max": float(group_data.max()),
            "median": float(group_data.median())
        }
        
        if len(group_data) > 0:
            stats["confidence_interval_95"] = (
                float(group_data.mean() - 1.96 * group_data.std() / np.sqrt(len(group_data))),
                float(group_data.mean() + 1.96 * group_data.std() / np.sqrt(len(group_data)))
            )
        
        group_stats.append(stats)
    
    group_stats_df = pd.DataFrame(group_stats)
    
    # Statistical tests
    statistical_tests = []
    
    if len(groups) == 2:
        # T-test for two groups
        from scipy import stats
        
        group_a = ab_df[ab_df[group_col] == groups[0]][metric_col]
        group_b = ab_df[ab_df[group_col] == groups[1]][metric_col]
        
        try:
            t_stat, p_value = stats.ttest_ind(group_a, group_b, equal_var=False)
            
            statistical_tests.append({
                "test": "t_test_independent",
                "groups": f"{groups[0]} vs {groups[1]}",
                "t_statistic": float(t_stat),
                "p_value": float(p_value),
                "significant": p_value < 0.05,
                "effect_size": float((group_b.mean() - group_a.mean()) / np.sqrt((group_a.std()**2 + group_b.std()**2) / 2))
            })
        except Exception as e:
            statistical_tests.append({
                "test": "t_test_independent",
                "error": str(e)[:100]
            })
    
    # Calculate lift compared to first group (control)
    if len(group_stats_df) > 1:
        control_mean = group_stats_df.iloc[0]["mean"]
        
        lifts = []
        for idx, row in group_stats_df.iterrows():
            if idx == 0:
                lifts.append(0.0)  # Control group
            else:
                lift = ((row["mean"] - control_mean) / control_mean) * 100
                lifts.append(float(lift))
        
        group_stats_df["lift_vs_control"] = lifts
    
    # Power analysis
    power_analysis = {}
    if len(groups) == 2:
        try:
            from statsmodels.stats.power import TTestIndPower
            
            effect_size = abs(group_stats_df.iloc[1]["mean"] - group_stats_df.iloc[0]["mean"]) / np.sqrt(
                (group_stats_df.iloc[0]["std"]**2 + group_stats_df.iloc[1]["std"]**2) / 2
            )
            
            power_analysis = {
                "effect_size": float(effect_size),
                "sample_size_per_group": int(min(group_stats_df.iloc[0]["sample_size"], group_stats_df.iloc[1]["sample_size"])),
                "alpha": 0.05,
                "power": float(TTestIndPower().power(effect_size, 
                                                    group_stats_df.iloc[0]["sample_size"], 
                                                    0.05, 
                                                    ratio=group_stats_df.iloc[1]["sample_size"]/group_stats_df.iloc[0]["sample_size"]))
            }
        except ImportError:
            power_analysis = {"error": "statsmodels required for power analysis"}
        except Exception as e:
            power_analysis = {"error": str(e)[:100]}
    
    # Recommendations
    recommendations = []
    
    if statistical_tests and "p_value" in statistical_tests[0]:
        p_value = statistical_tests[0]["p_value"]
        
        if p_value < 0.05:
            winner_idx = 1 if group_stats_df.iloc[1]["mean"] > group_stats_df.iloc[0]["mean"] else 0
            winner = group_stats_df.iloc[winner_idx]["group"]
            lift = group_stats_df.iloc[winner_idx]["lift_vs_control"]
            
            recommendations.append({
                "type": "statistically_significant",
                "message": f"Test is statistically significant (p = {p_value:.4f})",
                "recommendation": f"Implement variant '{winner}' with {lift:.1f}% lift"
            })
        else:
            recommendations.append({
                "type": "not_significant",
                "message": f"Test is not statistically significant (p = {p_value:.4f})",
                "recommendation": "Continue testing or consider other variants"
            })
    
    if power_analysis and "power" in power_analysis:
        power = power_analysis["power"]
        if power < 0.8:
            recommendations.append({
                "type": "underpowered",
                "message": f"Test may be underpowered (power = {power:.2f})",
                "recommendation": "Increase sample size for more reliable results"
            })
    
    summary = {
        "total_groups": len(groups),
        "total_samples": len(ab_df),
        "control_group": groups[0] if len(groups) > 0 else None,
        "test_groups": list(groups[1:]) if len(groups) > 1 else [],
        "metric": metric_col,
        "has_statistical_tests": len(statistical_tests) > 0,
        "columns_used": {
            "group": group_col,
            "metric": metric_col
        }
    }
    
    return {
        "group_statistics": group_stats_df,
        "statistical_tests": pd.DataFrame(statistical_tests) if statistical_tests else pd.DataFrame(),
        "power_analysis": power_analysis,
        "recommendations": pd.DataFrame(recommendations) if recommendations else pd.DataFrame(),
        "summary": summary
    }

# ============================================================================
# EMERGENCY CLEANUP SCRIPTS
# ============================================================================

def normalize_text(df: pd.DataFrame, columns_to_clean: List[str] = None, 
                  **kwargs) -> Dict[str, Any]:
    """
    Normalize text data: fix encoding, whitespace, casing, and common typos.
    
    Args:
        df: Input DataFrame
        columns_to_clean: Specific columns to normalize (default: all text columns)
    
    Returns:
        Dictionary with cleaned text and changes summary
    """
    
    # Empty dataset handling
    if df is None or df.empty:
        return {"error": "Dataset is empty", "cleaned_text": df}
    
    # Default to all text columns
    if columns_to_clean is None:
        columns_to_clean = df.select_dtypes(include=['object']).columns.tolist()
    
    if not columns_to_clean:
        return {"error": "No text columns to clean", "cleaned_text": df}
    
    cleaned_df = df.copy()
    changes_log = []
    
    # Common encoding fixes
    encoding_fixes = {
        'Ã©': 'é', 'Ã¨': 'è', 'Ãª': 'ê', 'Ã«': 'ë',
        'Ã¡': 'á', 'Ã ': 'à', 'Ã¢': 'â', 'Ã£': 'ã',
        'Ã±': 'ñ', 'Ãº': 'ú', 'Ã¼': 'ü', 'Ã§': 'ç',
        'â€™': "'", 'â€œ': '"', 'â€': '"', 'â€"': '-',
        'â€"': '-', 'â€"': '-', 'â€"': '-',
        'â€¢': '•', 'â€"': '-', 'â€"': '-',
        'â€"': '-', 'â€"': '-', 'â€"': '-'
    }
    
    # Common typos
    typo_corrections = {
        r'\brecieve\b': 'receive',
        r'\bseperate\b': 'separate',
        r'\boccured\b': 'occurred',
        r'\bdefinately\b': 'definitely',
        r'\bacheive\b': 'achieve',
        r'\bwierd\b': 'weird',
        r'\btomm?orow\b': 'tomorrow',
        r'\bembarass\b': 'embarrass',
        r'\bmaintance\b': 'maintenance',
        r'\bpronounciation\b': 'pronunciation',
        r'\brhythm\b': 'rhythm',
        r'\boccassion\b': 'occasion',
        r'\bcommited\b': 'committed',
        r'\bgoverment\b': 'government',
        r'\blabratory\b': 'laboratory',
        r'\bneccessary\b': 'necessary',
        r'\bpublically\b': 'publicly'
    }
    
    # Standard abbreviations
    abbreviation_map = {
        r'\bSt\.\b': 'Street',
        r'\bAve\.\b': 'Avenue',
        r'\bBlvd\.\b': 'Boulevard',
        r'\bDr\.\b': 'Drive',
        r'\bLn\.\b': 'Lane',
        r'\bRd\.\b': 'Road',
        r'\bInc\.\b': 'Inc',
        r'\bCorp\.\b': 'Corp',
        r'\bLtd\.\b': 'Ltd',
        r'\bCo\.\b': 'Co',
        r'\bDept\.\b': 'Department',
        r'\bJan\.\b': 'January',
        r'\bFeb\.\b': 'February',
        r'\bMar\.\b': 'March',
        r'\bApr\.\b': 'April',
        r'\bJun\.\b': 'June',
        r'\bJul\.\b': 'July',
        r'\bAug\.\b': 'August',
        r'\bSep\.\b': 'September',
        r'\bOct\.\b': 'October',
        r'\bNov\.\b': 'November',
        r'\bDec\.\b': 'December'
    }
    
    for col in columns_to_clean:
        if col not in cleaned_df.columns:
            continue
        
        original_sample = cleaned_df[col].dropna().astype(str).head(3).tolist()
        changes_made = 0
        
        # Convert to string type
        cleaned_df[col] = cleaned_df[col].astype(str)
        
        # 1. Fix encoding issues
        for bad, good in encoding_fixes.items():
            before = cleaned_df[col].str.contains(bad, regex=False).sum()
            cleaned_df[col] = cleaned_df[col].str.replace(bad, good, regex=False)
            after = cleaned_df[col].str.contains(bad, regex=False).sum()
            changes_made += (before - after)
        
        # 2. Remove extra whitespace
        cleaned_df[col] = cleaned_df[col].str.strip()
        cleaned_df[col] = cleaned_df[col].str.replace(r'\s+', ' ', regex=True)
        changes_made += len(cleaned_df[col])  # All rows potentially affected
        
        # 3. Fix common typos
        for typo, correction in typo_corrections.items():
            before = cleaned_df[col].str.contains(typo, regex=True).sum()
            cleaned_df[col] = cleaned_df[col].str.replace(typo, correction, regex=True)
            after = cleaned_df[col].str.contains(typo, regex=True).sum()
            changes_made += (before - after)
        
        # 4. Standardize abbreviations
        for abbrev, full in abbreviation_map.items():
            before = cleaned_df[col].str.contains(abbrev, regex=True).sum()
            cleaned_df[col] = cleaned_df[col].str.replace(abbrev, full, regex=True)
            after = cleaned_df[col].str.contains(abbrev, regex=True).sum()
            changes_made += (before - after)
        
        # 5. Smart casing based on column name
        col_lower = col.lower()
        
        if any(name_word in col_lower for name_word in ['name', 'first', 'last', 'person', 'customer']):
            # Title case for names
            cleaned_df[col] = cleaned_df[col].str.title()
            changes_made += len(cleaned_df[col])
        
        elif any(address_word in col_lower for address_word in ['address', 'city', 'state', 'country']):
            # Proper case for addresses
            cleaned_df[col] = cleaned_df[col].str.title()
            changes_made += len(cleaned_df[col])
        
        elif any(email_word in col_lower for email_word in ['email', 'mail']):
            # Lowercase for emails
            cleaned_df[col] = cleaned_df[col].str.lower()
            changes_made += len(cleaned_df[col])
        
        # 6. Remove special characters (keep alphanumeric and basic punctuation)
        cleaned_df[col] = cleaned_df[col].str.replace(r'[^\w\s\.\-@,;:\'"]', '', regex=True)
        
        # 7. Standardize boolean-like values
        bool_patterns = {
            r'^(true|yes|1|t|y)$': 'True',
            r'^(false|no|0|f|n)$': 'False',
            r'^(enabled|active|on)$': 'Enabled',
            r'^(disabled|inactive|off)$': 'Disabled'
        }
        
        for pattern, replacement in bool_patterns.items():
            mask = cleaned_df[col].str.match(pattern, case=False, na=False)
            if mask.any():
                cleaned_df.loc[mask, col] = replacement
                changes_made += mask.sum()
        
        # Calculate statistics
        cleaned_sample = cleaned_df[col].dropna().astype(str).head(3).tolist()
        
        changes_log.append({
            "column": col,
            "changes_made": changes_made,
            "percentage_changed": f"{(changes_made / len(cleaned_df) * 100):.1f}%" if len(cleaned_df) > 0 else "0%",
            "example_before": original_sample[0] if original_sample else "",
            "example_after": cleaned_sample[0] if cleaned_sample else ""
        })
    
    # Summary statistics
    total_changes = sum(item["changes_made"] for item in changes_log)
    avg_change_pct = np.mean([float(item["percentage_changed"].rstrip('%')) for item in changes_log])
    
    summary = {
        "columns_cleaned": len(columns_to_clean),
        "total_changes": total_changes,
        "average_change_percentage": f"{avg_change_pct:.1f}%",
        "operations_applied": [
            "encoding_fixes",
            "whitespace_normalization",
            "typo_correction",
            "casing_normalization",
            "special_character_removal"
        ]
    }
    
    return {
        "cleaned_text": cleaned_df,
        "changes_summary": pd.DataFrame(changes_log),
        "summary": summary
    }

def match_schemas(df1: pd.DataFrame, df2: pd.DataFrame = None, 
                 **kwargs) -> Dict[str, Any]:
    """
    Match schemas between datasets using fuzzy column name matching.
    
    Args:
        df1: First DataFrame
        df2: Second DataFrame (optional, uses session state if None)
    
    Returns:
        Dictionary with schema matching results and mapping
    """
    
    if df1 is None or df1.empty:
        return {"error": "First dataset is empty"}
    
    # Get second dataset from session state if not provided
    if df2 is None:
        if 'relationship_datasets' in st.session_state:
            datasets = st.session_state.relationship_datasets
            if len(datasets) > 1:
                # Get the first non-main dataset
                for key, dataset in datasets.items():
                    if key != 'main' and dataset is not None:
                        df2 = dataset
                        break
        
        if df2 is None:
            return {"error": "Second dataset not provided or not found in session state"}
    
    if df2 is None or df2.empty:
        return {"error": "Second dataset is empty"}
    
    # Dependency check
    if not FUZZY_AVAILABLE:
        return {
            "warning": "Schema matching requires fuzzywuzzy",
            "error": "Missing dependency: pip install fuzzywuzzy python-Levenshtein",
            "schema_mapping": pd.DataFrame()
        }
    
    # Analyze both schemas
    schema1 = _analyze_schema(df1)
    schema2 = _analyze_schema(df2)
    
    # Find potential matches
    matches = []
    
    for col1, info1 in schema1.items():
        best_match = None
        best_score = 0
        
        for col2, info2 in schema2.items():
            # Calculate matching score
            score = _calculate_column_similarity(col1, col2, info1, info2)
            
            if score > best_score:
                best_score = score
                best_match = (col2, info2, score)
        
        if best_match and best_score > 0.3:  # Threshold for matching
            col2, info2, score = best_match
            
            matches.append({
                "dataset1_column": col1,
                "dataset2_column": col2,
                "similarity_score": round(score, 3),
                "dataset1_type": info1["dtype"],
                "dataset2_type": info2["dtype"],
                "dataset1_unique": info1["unique_values"],
                "dataset2_unique": info2["unique_values"],
                "match_confidence": "high" if score > 0.7 else "medium" if score > 0.5 else "low",
                "suggested_action": "exact_match" if score > 0.9 else "fuzzy_match" if score > 0.7 else "review_needed"
            })
    
    # Create mapping DataFrame
    mapping_df = pd.DataFrame(matches) if matches else pd.DataFrame()
    
    # Find unmatched columns
    matched_cols1 = set(m["dataset1_column"] for m in matches)
    matched_cols2 = set(m["dataset2_column"] for m in matches)
    
    unmatched1 = [col for col in schema1.keys() if col not in matched_cols1]
    unmatched2 = [col for col in schema2.keys() if col not in matched_cols2]
    
    # Summary
    summary = {
        "dataset1_columns": len(schema1),
        "dataset2_columns": len(schema2),
        "matches_found": len(matches),
        "unmatched_in_dataset1": len(unmatched1),
        "unmatched_in_dataset2": len(unmatched2),
        "high_confidence_matches": len([m for m in matches if m["match_confidence"] == "high"]),
        "average_similarity": round(np.mean([m["similarity_score"] for m in matches]), 3) if matches else 0
    }
    
    return {
        "schema_mapping": mapping_df,
        "unmatched_columns": {
            "dataset1": unmatched1,
            "dataset2": unmatched2
        },
        "schema_analysis": {
            "dataset1": schema1,
            "dataset2": schema2
        },
        "summary": summary
    }

def sanitize_pii_data(df: pd.DataFrame, detection_level: str = "standard",
                     **kwargs) -> Dict[str, Any]:
    """
    Detect and sanitize Personally Identifiable Information (PII).
    
    Args:
        df: Input DataFrame
        detection_level: Detection sensitivity ('conservative', 'standard', 'aggressive')
    
    Returns:
        Dictionary with sanitized data and PII report
    """
    
    # Empty dataset handling
    if df is None or df.empty:
        return {"error": "Dataset is empty", "sanitized_data": df}
    
    text_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    if not text_cols:
        return {"error": "No text columns found for PII detection", "sanitized_data": df}
    
    # PII patterns with varying sensitivity
    pii_patterns = {
        "email": {
            "pattern": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "conservative": True,
            "standard": True,
            "aggressive": True
        },
        "phone": {
            "pattern": r'(\+\d{1,3}[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b',
            "conservative": True,
            "standard": True,
            "aggressive": True
        },
        "ssn": {
            "pattern": r'\b\d{3}-\d{2}-\d{4}\b',
            "conservative": True,
            "standard": True,
            "aggressive": True
        },
        "credit_card": {
            "pattern": r'\b\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?\d{4}\b',
            "conservative": True,
            "standard": True,
            "aggressive": True
        },
        "ip_address": {
            "pattern": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
            "conservative": False,
            "standard": True,
            "aggressive": True
        },
        "name": {
            "pattern": r'\b([A-Z][a-z]+ [A-Z][a-z]+)\b',  # Simple name pattern
            "conservative": False,
            "standard": True,
            "aggressive": True
        },
        "address": {
            "pattern": r'\b\d+\s+([A-Z][a-z]+\s)+([A-Z][a-z]+)\b',  # Simple address pattern
            "conservative": False,
            "standard": False,
            "aggressive": True
        }
    }
    
    # Column name hints for PII
    pii_keywords = {
        "email": ["email", "mail", "e-mail"],
        "phone": ["phone", "mobile", "tel", "telephone"],
        "name": ["name", "firstname", "lastname", "fullname", "username"],
        "address": ["address", "street", "city", "zip", "postal", "location"],
        "id": ["ssn", "social", "id", "passport", "driver", "license", "national"],
        "financial": ["credit", "card", "account", "bank", "routing"]
    }
    
    sanitized_df = df.copy()
    pii_report = []
    
    for col in text_cols:
        col_lower = col.lower()
        col_data = sanitized_df[col].dropna().astype(str)
        
        if len(col_data) == 0:
            continue
        
        detected_types = []
        changes_made = 0
        
        # Check by column name
        for pii_type, keywords in pii_keywords.items():
            if any(keyword in col_lower for keyword in keywords):
                if pii_type not in detected_types:
                    detected_types.append(pii_type)
        
        # Check by pattern matching
        sample_data = col_data.head(100)
        
        for pii_type, pattern_info in pii_patterns.items():
            if not pattern_info.get(detection_level, False):
                continue
            
            pattern = pattern_info["pattern"]
            matches = sample_data.str.contains(pattern, regex=True).sum()
            
            if matches > 0:
                # Adjust threshold based on detection level
                threshold = {
                    "conservative": 0.05,  # 5% match
                    "standard": 0.03,      # 3% match
                    "aggressive": 0.01      # 1% match
                }.get(detection_level, 0.03)
                
                if matches / len(sample_data) >= threshold:
                    if pii_type not in detected_types:
                        detected_types.append(pii_type)
        
        # Apply sanitization
        if detected_types:
            for pii_type in detected_types:
                if pii_type == "email":
                    # Keep domain, mask local part
                    sanitized_df[col] = sanitized_df[col].astype(str).apply(
                        lambda x: re.sub(r'([A-Za-z0-9._%+-]+)@', '***@', x)
                    )
                    changes_made += sanitized_df[col].str.contains('***@').sum()
                
                elif pii_type == "phone":
                    # Keep last 4 digits
                    sanitized_df[col] = sanitized_df[col].astype(str).apply(
                        lambda x: re.sub(r'(\d{3})[-.]?\d{3}[-.]?(\d{4})', r'***-***-\2', x)
                    )
                    changes_made += sanitized_df[col].str.contains(r'\*\*\*-\*\*\*-\d{4}').sum()
                
                elif pii_type == "ssn":
                    # Keep last 4 digits
                    sanitized_df[col] = sanitized_df[col].astype(str).apply(
                        lambda x: re.sub(r'(\d{3})-(\d{2})-(\d{4})', r'***-**-\3', x)
                    )
                    changes_made += sanitized_df[col].str.contains(r'\*\*\*-\*\*-\d{4}').sum()
                
                elif pii_type == "credit_card":
                    # Keep last 4 digits
                    sanitized_df[col] = sanitized_df[col].astype(str).apply(
                        lambda x: re.sub(r'\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?(\d{4})', r'**** **** **** \1', x)
                    )
                    changes_made += sanitized_df[col].str.contains(r'\*\*\*\* \*\*\*\* \*\*\*\* \d{4}').sum()
                
                elif pii_type == "ip_address":
                    # Partially mask
                    sanitized_df[col] = sanitized_df[col].astype(str).apply(
                        lambda x: re.sub(r'\b(\d{1,3})\.(\d{1,3})\.\d{1,3}\.\d{1,3}\b', r'\1.\2.***.***', x)
                    )
                
                elif pii_type == "name":
                    # Mask all but first letter
                    sanitized_df[col] = sanitized_df[col].astype(str).apply(
                        lambda x: re.sub(r'\b(\w)\w+\b', r'\1***', x)
                    )
                
                elif pii_type == "address":
                    # General masking
                    sanitized_df[col] = sanitized_df[col].astype(str).apply(
                        lambda x: re.sub(r'\b\d+\s+', '*** ', x)
                    )
            
            pii_report.append({
                "column": col,
                "detected_pii_types": ", ".join(detected_types),
                "detection_method": f"column_name_and_patterns ({detection_level})",
                "changes_made": changes_made,
                "percentage_affected": f"{(changes_made / len(sanitized_df) * 100):.1f}%" if len(sanitized_df) > 0 else "0%",
                "sample_before": sample_data.iloc[0] if len(sample_data) > 0 else "",
                "sample_after": sanitized_df[col].iloc[0] if len(sanitized_df[col]) > 0 else ""
            })
    
    # Calculate summary statistics
    columns_with_pii = len(pii_report)
    total_changes = sum(item["changes_made"] for item in pii_report)
    
    # Get unique PII types detected
    all_pii_types = []
    for report in pii_report:
        types = report["detected_pii_types"].split(", ")
        all_pii_types.extend(types)
    
    unique_pii_types = list(set(all_pii_types))
    
    summary = {
        "columns_checked": len(text_cols),
        "columns_with_pii": columns_with_pii,
        "total_changes": total_changes,
        "detection_level": detection_level,
        "pii_types_detected": unique_pii_types,
        "compliance_level": "GDPR/CCPA compliant" if columns_with_pii > 0 else "No PII detected"
    }
    
    return {
        "sanitized_data": sanitized_df,
        "pii_report": pd.DataFrame(pii_report) if pii_report else pd.DataFrame(),
        "summary": summary
    }

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _normalize_text(text: str) -> str:
    """Normalize text for comparison"""
    if not isinstance(text, str):
        text = str(text)
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove special characters (keep letters, numbers, and spaces)
    text = re.sub(r'[^\w\s]', '', text)
    
    # Standardize common terms
    replacements = {
        'inc': '', 'llc': '', 'ltd': '', 'corp': '', 'company': '',
        'street': 'st', 'avenue': 'ave', 'road': 'rd', 'boulevard': 'blvd',
        'mister': 'mr', 'mrs': '', 'miss': 'ms', 'doctor': 'dr',
        'incorporated': '', 'limited': ''
    }
    
    for old, new in replacements.items():
        text = re.sub(rf'\b{old}\b', new, text)
    
    return text.strip()

def _choose_canonical_value(values: List[str]) -> str:
    """Choose the best canonical value from a list of duplicates"""
    if not values:
        return ""
    
    # Prefer values that are not empty
    non_empty = [v for v in values if v and str(v).strip()]
    if not non_empty:
        return values[0]
    
    # Prefer longer values (more complete)
    non_empty.sort(key=lambda x: len(str(x)), reverse=True)
    
    # Prefer values with proper casing
    proper_case = [v for v in non_empty if v == v.title() or v == v.upper()]
    if proper_case:
        return proper_case[0]
    
    return non_empty[0]

def _detect_datetime_type(data) -> Tuple[float, List]:
    """Detect if data is datetime type"""
    try:
        parsed = pd.to_datetime(data, errors='coerce')
        success_rate = parsed.notna().mean()
        sample = data.head(3).tolist()
        return float(success_rate), sample
    except:
        return 0.0, []

def _detect_integer_type(data) -> Tuple[float, List]:
    """Detect if data is integer type"""
    try:
        parsed = pd.to_numeric(data, errors='coerce')
        success_rate = parsed.notna().mean()
        if success_rate > 0:
            # Check if all successful values are integers
            int_mask = parsed.dropna().apply(lambda x: float(x).is_integer())
            if int_mask.all():
                sample = parsed.dropna().astype(int).head(3).tolist()
                return float(success_rate), sample
    except:
        pass
    return 0.0, []

def _detect_float_type(data) -> Tuple[float, List]:
    """Detect if data is float type"""
    try:
        parsed = pd.to_numeric(data, errors='coerce')
        success_rate = parsed.notna().mean()
        if success_rate > 0:
            sample = parsed.dropna().head(3).tolist()
            return float(success_rate), sample
    except:
        pass
    return 0.0, []

def _detect_boolean_type(data) -> Tuple[float, List]:
    """Detect if data is boolean type"""
    str_data = data.astype(str).str.lower().str.strip()
    bool_patterns = ['true', 'false', 'yes', 'no', '1', '0', 't', 'f', 'y', 'n']
    matches = str_data.isin(bool_patterns).mean()
    if matches > 0.8:  # At least 80% match boolean patterns
        sample = data.head(3).tolist()
        return float(matches), sample
    return 0.0, []

def _detect_categorical_type(data) -> Tuple[float, List]:
    """Detect if data is categorical type"""
    unique_ratio = data.nunique() / len(data)
    if 0.01 <= unique_ratio <= 0.3:  # Between 1% and 30% unique values
        sample = data.value_counts().head(3).index.tolist()
        return 1.0, sample
    return 0.0, []

def _detect_currency_type(data) -> Tuple[float, List]:
    """Detect if data is currency type"""
    str_data = data.astype(str)
    currency_patterns = [r'^\$', r'USD', r'EUR', r'£', r'¥']
    matches = sum(str_data.str.contains(pattern).sum() for pattern in currency_patterns)
    match_rate = matches / len(str_data)
    if match_rate > 0.3:  # At least 30% match currency patterns
        sample = data.head(3).tolist()
        return float(match_rate), sample
    return 0.0, []

def _detect_percentage_type(data) -> Tuple[float, List]:
    """Detect if data is percentage type"""
    str_data = data.astype(str)
    percent_matches = str_data.str.contains('%').sum()
    match_rate = percent_matches / len(str_data)
    if match_rate > 0.3:  # At least 30% have percent signs
        sample = data.head(3).tolist()
        return float(match_rate), sample
    return 0.0, []

def _convert_to_boolean(series):
    """Convert series to boolean type"""
    str_series = series.astype(str).str.lower().str.strip()
    
    true_values = ['true', 'yes', '1', 't', 'y']
    false_values = ['false', 'no', '0', 'f', 'n']
    
    result = pd.Series(np.nan, index=series.index)
    result[str_series.isin(true_values)] = True
    result[str_series.isin(false_values)] = False
    
    return result.astype('boolean')

def _convert_currency_to_numeric(series):
    """Convert currency strings to numeric"""
    str_series = series.astype(str)
    
    # Remove currency symbols and commas
    cleaned = str_series.str.replace(r'[$,£€¥]', '', regex=True)
    cleaned = cleaned.str.replace(',', '', regex=False)
    
    return pd.to_numeric(cleaned, errors='coerce')

def _convert_percentage_to_numeric(series):
    """Convert percentage strings to numeric"""
    str_series = series.astype(str)
    
    # Remove percent signs and convert to decimal
    cleaned = str_series.str.replace('%', '', regex=False)
    numeric = pd.to_numeric(cleaned, errors='coerce')
    
    # Convert to decimal (divide by 100)
    return numeric / 100

def _detect_delimiter(data):
    """Detect the most likely delimiter in text data"""
    delimiters = [',', ';', '|', '\t', ' - ', '/', '\\', ':', ' ']
    delimiter_scores = {}
    
    for delim in delimiters:
        split_counts = data.str.count(delim)
        total_count = split_counts.sum()
        
        if total_count > 0:
            avg_splits = split_counts.mean()
            consistency = 1 - (split_counts.std() / (avg_splits + 1e-10))
            score = total_count * consistency
            
            delimiter_scores[delim] = {
                "count": total_count,
                "consistency": consistency,
                "score": score
            }
    
    if not delimiter_scores:
        return None
    
    return max(delimiter_scores.keys(), key=lambda d: delimiter_scores[d]["score"])

def _suggest_column_names(split_df, original_col):
    """Suggest meaningful names for split columns"""
    n_cols = split_df.shape[1]
    suggestions = []
    
    # Common patterns for different numbers of columns
    if n_cols == 2:
        suggestions = [f"{original_col}_part1", f"{original_col}_part2"]
    elif n_cols == 3:
        suggestions = [f"{original_col}_part1", f"{original_col}_part2", f"{original_col}_part3"]
    elif n_cols > 3:
        suggestions = [f"{original_col}_{i+1}" for i in range(n_cols)]
    
    # Analyze content to improve suggestions
    for i in range(min(n_cols, 3)):
        col_data = split_df.iloc[:, i].dropna().astype(str)
        
        if len(col_data) > 0:
            # Check for common patterns
            sample = col_data.head(10).str.lower()
            
            if sample.str.contains(r'\b(st|street|ave|avenue|rd|road)\b').any():
                suggestions[i] = f"{original_col}_street"
            elif sample.str.contains(r'\b(city|town)\b').any():
                suggestions[i] = f"{original_col}_city"
            elif sample.str.contains(r'\b(state|province|region)\b').any():
                suggestions[i] = f"{original_col}_state"
            elif sample.str.contains(r'\b(zip|postal|code)\b').any():
                suggestions[i] = f"{original_col}_zip"
            elif sample.str.match(r'\d{5}').any() or sample.str.match(r'\d{5}-\d{4}').any():
                suggestions[i] = f"{original_col}_zip"
            elif sample.str.match(r'^[A-Z]{2}$').any():
                suggestions[i] = f"{original_col}_state"
    
    return suggestions

def _determine_auto_strategies(df, missing_pct):
    """Determine optimal imputation strategies automatically"""
    strategies = {}
    
    for col in df.columns:
        pct = missing_pct[col]
        
        if pct == 0:
            strategies[col] = "none"
        elif pct > 50:
            strategies[col] = "drop_column"
        elif pct > 20:
            # Significant missing data
            if pd.api.types.is_numeric_dtype(df[col]):
                # Check skewness
                skewness = df[col].skew()
                if abs(skewness) > 1:
                    strategies[col] = "median"
                else:
                    strategies[col] = "mean"
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                strategies[col] = "forward"
            else:
                strategies[col] = "mode"
        else:
            # Small amount of missing data
            if pd.api.types.is_numeric_dtype(df[col]):
                strategies[col] = "mean"
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                strategies[col] = "forward"
            else:
                strategies[col] = "mode"
    
    return strategies

def _detect_date_columns(df):
    """Detect columns that contain date-like data"""
    date_cols = []
    
    for col in df.columns:
        # Already datetime
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            date_cols.append(col)
            continue
        
        # String columns that might contain dates
        if df[col].dtype == 'object':
            sample = df[col].dropna().astype(str).head(100)
            if len(sample) == 0:
                continue
            
            # Check for common date patterns
            date_patterns = [
                r'\d{4}-\d{2}-\d{2}',
                r'\d{2}/\d{2}/\d{4}',
                r'\d{2}-\d{2}-\d{4}',
                r'\d{1,2}\s+\w+\s+\d{4}',
                r'\w+\s+\d{1,2},\s+\d{4}',
                r'\d{8}',  # YYYYMMDD
                r'\d{6}'   # YYMMDD
            ]
            
            pattern_matches = sum(sample.str.match(pattern).sum() for pattern in date_patterns)
            
            if pattern_matches > len(sample) * 0.3:  # 30% match
                date_cols.append(col)
    
    return date_cols

def _detect_time_series_frequency(series):
    """Detect the frequency of a time series"""
    if len(series) < 3:
        return None
    
    # Calculate time differences
    time_diff = series.index.to_series().diff().dropna()
    
    if len(time_diff) == 0:
        return None
    
    # Most common difference
    mode_diff = time_diff.mode()
    if len(mode_diff) > 0:
        mode_diff = mode_diff.iloc[0]
        
        # Map to frequency string
        if mode_diff.days == 1:
            return 'D'
        elif mode_diff.days == 7:
            return 'W'
        elif 28 <= mode_diff.days <= 31:
            return 'M'
        elif 89 <= mode_diff.days <= 92:
            return 'Q'
        elif 365 <= mode_diff.days <= 366:
            return 'Y'
    
    return None

def _auto_detect_cohort_columns(df):
    """Auto-detect columns suitable for cohort/RFM analysis"""
    result = {}
    
    # Look for customer/user ID columns
    id_patterns = ['id', 'user', 'customer', 'client', 'account']
    for col in df.columns:
        col_lower = col.lower()
        if any(pattern in col_lower for pattern in id_patterns):
            result['customer_id'] = col
            break
    
    # Look for date columns
    date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
    if date_cols:
        result['date'] = date_cols[0]
    
    # Look for value columns
    value_patterns = ['price', 'amount', 'value', 'revenue', 'sales', 'cost']
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    for col in numeric_cols:
        col_lower = col.lower()
        if any(pattern in col_lower for pattern in value_patterns):
            result['value'] = col
            break
    
    # Fallback to first numeric column for value
    if 'value' not in result and len(numeric_cols) > 0:
        result['value'] = numeric_cols[0]
    
    return result

def _estimate_price_elasticity(df, product_col, price_col, quantity_col):
    """Estimate price elasticity for products"""
    try:
        # Group by product and calculate log changes
        product_stats = df.groupby(product_col).agg({
            price_col: ['mean', 'std'],
            quantity_col: ['mean', 'std']
        })
        
        # Flatten columns
        product_stats.columns = ['_'.join(col).strip() for col in product_stats.columns.values]
        
        # Calculate elasticity as % change in quantity / % change in price
        # Simplified version using coefficient of variation
        price_cv = product_stats[f'{price_col}_std'] / product_stats[f'{price_col}_mean']
        quantity_cv = product_stats[f'{quantity_col}_std'] / product_stats[f'{quantity_col}_mean']
        
        # Avoid division by zero
        mask = price_cv > 0
        elasticity = -quantity_cv[mask] / price_cv[mask]
        
        return elasticity.mean() if not elasticity.empty else 0
    except:
        return 0

def _analyze_schema(df):
    """Analyze schema of a DataFrame"""
    schema = {}
    
    for col in df.columns:
        try:
            dtype = str(df[col].dtype)
        except:
            dtype = 'unknown'
        
        try:
            unique_count = df[col].nunique()
        except:
            unique_count = 0
        
        try:
            null_count = df[col].isna().sum()
        except:
            null_count = 0
        
        schema[col] = {
            "dtype": dtype,
            "unique_values": int(unique_count),
            "null_count": int(null_count),
            "null_percentage": float(null_count / len(df) * 100) if len(df) > 0 else 0,
            "sample_values": df[col].dropna().head(3).tolist() if not df[col].empty else []
        }
    
    return schema

def _calculate_column_similarity(col1, col2, info1, info2):
    """Calculate similarity score between two columns"""
    score = 0
    
    # 1. Name similarity
    if FUZZY_AVAILABLE:
        name_similarity = fuzz.ratio(col1.lower(), col2.lower()) / 100
    else:
        # Simple token-based similarity
        tokens1 = set(col1.lower().split('_'))
        tokens2 = set(col2.lower().split('_'))
        if tokens1 and tokens2:
            name_similarity = len(tokens1.intersection(tokens2)) / len(tokens1.union(tokens2))
        else:
            name_similarity = 0
    
    score += name_similarity * 0.4  # 40% weight
    
    # 2. Data type compatibility
    dtype1 = info1["dtype"]
    dtype2 = info2["dtype"]
    
    dtype_groups = {
        "numeric": ["int", "float", "int64", "float64"],
        "text": ["object", "string"],
        "datetime": ["datetime", "timestamp"],
        "boolean": ["bool", "boolean"]
    }
    
    dtype_match = 0
    for group, types in dtype_groups.items():
        if any(t in dtype1 for t in types) and any(t in dtype2 for t in types):
            dtype_match = 1
            break
    
    score += dtype_match * 0.3  # 30% weight
    
    # 3. Value distribution similarity (simplified)
    try:
        unique_ratio1 = info1["unique_values"] / info1.get("sample_count", 100)
        unique_ratio2 = info2["unique_values"] / info2.get("sample_count", 100)
        
        unique_similarity = 1 - abs(unique_ratio1 - unique_ratio2)
        score += unique_similarity * 0.3  # 30% weight
    except:
        pass
    
    return min(score, 1.0)

# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    # Global flags for dependency checking
    'FUZZY_AVAILABLE', 'PHONETICS_AVAILABLE', 'STATSMODELS_AVAILABLE', 'SCIPY_AVAILABLE',
    
    # Detective Scripts
    'find_fuzzy_duplicates',
    'detect_data_types',
    'find_anomaly_patterns',
    
    # Fixer Scripts
    'split_columns_smartly',
    'handle_missing_data',
    'fix_date_formats',
    
    # Transformer Scripts
    'build_cohort_analysis',
    'decompose_time_series',
    'engineer_features',
    
    # Business Intelligence
    'segment_customers_rfm',
    'analyze_pricing',
    'analyze_ab_test',
    
    # Emergency Cleanup
    'normalize_text',
    'match_schemas',
    'sanitize_pii_data'
]