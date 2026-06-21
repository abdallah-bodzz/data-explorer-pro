#**************************************************************************
#                    SMART SAMPLING MODULE (Production-Grade)
#**************************************************************************

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

def generate_sampling_metadata(
    df: pd.DataFrame,
    sampled_df: pd.DataFrame,
    was_sampled: bool,
    sampling_reason: str,
    sample_frac: Optional[float],
    random_state: Optional[int],
    stratified_col: Optional[str],
    sampling_score: float
) -> Dict[str, Any]:
    """Generates metadata for AI prompt while preserving original format"""
    return {
        'was_sampled': was_sampled,
        'original_shape': df.shape,
        'sampled_shape': sampled_df.shape if was_sampled else df.shape,
        'sample_fraction': sample_frac,
        'sampling_score': sampling_score,
        'random_state': random_state,
        'stratified': stratified_col is not None,
        'stratified_column': stratified_col,
        'reason': sampling_reason
    }

def generate_sampling_report(
    df: pd.DataFrame,
    metadata: Dict[str, Any],
    data_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """Generates comprehensive report for UI display"""
    return {
        "metadata": metadata,
        "analysis": data_analysis,
        "visual_summary": {
            "skew_summary": data_analysis.get("numerical", {}).get("skewness", {}),
            "top_imbalanced_cats": sorted(
                data_analysis.get("categorical", {}).get("imbalance", {}).items(),
                key=lambda x: x[1].get("imbalance_ratio", 0),
                reverse=True
            )[:3]
        }
    }

def safe_skew_calc(series: pd.Series, sample_size: int = 10_000) -> float:
    """Optimized skew calculation with sampling for large series"""
    if len(series) > sample_size:
        return series.sample(sample_size, random_state=42).skew()
    return series.skew()

def analyze_data_characteristics(df: pd.DataFrame) -> Dict[str, Any]:
    """Comprehensive analysis of DataFrame characteristics"""
    analysis: Dict[str, Any] = {
        "size": len(df),
        "dimensions": len(df.columns),
        "missing_data": {},
        "numerical": {},
        "categorical": {},
        "temporal_columns": [],
        "recommendations": []
    }

    # Missing data analysis
    null_pct = df.isnull().mean().sort_values(ascending=False)
    analysis["missing_data"]["total_null_percentage"] = float(null_pct.mean())
    analysis["missing_data"]["high_null_columns"] = [col for col, pct in null_pct.items() if pct > 0.3]

    # Numerical analysis
    num_cols = df.select_dtypes(include=np.number).columns
    if len(num_cols) > 0:
        skewness = {col: safe_skew_calc(df[col]) for col in num_cols}
        analysis["numerical"]["columns"] = list(skewness.keys())
        analysis["numerical"]["skewness"] = {k: round(v, 2) for k, v in skewness.items()}
        avg_abs_skew = float(np.mean(np.abs(list(skewness.values()))))
        analysis["numerical"]["average_abs_skewness"] = round(avg_abs_skew, 2)
        if avg_abs_skew > 1.0:
            analysis["recommendations"].append(
                "Numerical data shows significant skewness – consider transformations or stratified sampling."
            )

    # Categorical analysis
    cat_cols = df.select_dtypes(include=['object', 'category']).columns
    if len(cat_cols) > 0:
        imbalance_info: Dict[str, Any] = {}
        high_card_cols: list = []
        for col in cat_cols:
            counts = df[col].value_counts(normalize=True)
            dominant_pct = float(counts.iloc[0])
            min_pct = float(counts.min())
            imbalance_ratio = round(dominant_pct / (min_pct if min_pct > 0 else 0.01), 2)
            imbalance_info[col] = {
                "unique_values": int(counts.size),
                "dominant_class": counts.index[0],
                "dominant_percentage": round(dominant_pct, 2),
                "imbalance_ratio": imbalance_ratio
            }
            if counts.size > 50:
                high_card_cols.append(col)
        analysis["categorical"]["imbalance"] = imbalance_info
        analysis["categorical"]["high_cardinality_cols"] = high_card_cols
        if any(v["imbalance_ratio"] > 10 for v in imbalance_info.values()):
            analysis["recommendations"].append(
                "Significant categorical imbalance detected – recommend stratified sampling."
            )

    # Temporal detection
    temporal_cols = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
    if temporal_cols:
        analysis["temporal_columns"] = temporal_cols
        analysis["recommendations"].append(
            "Temporal data detected – ensure sampling preserves time dependencies."
        )

    return analysis

def smart_sampling_score(df: pd.DataFrame) -> float:
    """Calculates a normalized complexity score (0–10) based on data characteristics"""
    if df.empty:
        return 0.0

    analysis = analyze_data_characteristics(df)
    score = 0.0

    # Size factor (0–2)
    size_factor = min(2.0, np.log10(max(1, analysis["size"]/1000)) * 0.5)
    score += size_factor

    # Dimensionality factor (0–2)
    dim_factor = min(2.0, analysis["dimensions"] * 0.1)
    score += dim_factor

    # Null data factor (0–2)
    null_factor = min(2.0, len(analysis["missing_data"]["high_null_columns"]) * 0.5)
    score += null_factor

    # Numerical skew factor (0–2)
    num_skew = analysis["numerical"].get("average_abs_skewness", 0.0)
    num_factor = min(2.0, num_skew * 0.5)
    score += num_factor

    # Categorical imbalance factor (0–2)
    cat_factor = min(2.0, sum(1 for v in analysis["categorical"].get("imbalance", {}).values() if v["imbalance_ratio"] > 10))
    score += cat_factor

    # Temporal factor (0–1)
    temp_factor = 1.0 if analysis["temporal_columns"] else 0.0
    score += temp_factor

    # High cardinality factor (0–1)
    card_factor = min(1.0, len(analysis["categorical"].get("high_cardinality_cols", [])) * 0.2)
    score += card_factor

    # Normalize to 0–10
    normalized = round((score / 10.0) * 10.0, 1)
    return normalized

def analyze_memory_usage(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze memory usage by column and data type"""
    memory_usage = df.memory_usage(deep=True)
    total_memory_mb = memory_usage.sum() / (1024 ** 2)
    
    column_memory = {}
    for col in df.columns:
        col_memory = df[col].memory_usage(deep=True) / (1024 ** 2)
        column_memory[col] = {
            'memory_mb': col_memory,
            'dtype': str(df[col].dtype),
            'efficiency': 'high' if col_memory < 1.0 else 'medium' if col_memory < 10.0 else 'low'
        }
    
    return {
        'total_memory_mb': total_memory_mb,
        'column_breakdown': column_memory,
        'memory_intensive_columns': [col for col, info in column_memory.items() if info['efficiency'] == 'low']
    }

def enhanced_smart_sampling_score(df: pd.DataFrame) -> float:
    """Enhanced scoring that includes memory usage"""
    base_score = smart_sampling_score(df)
    memory_info = analyze_memory_usage(df)
    
    # Add memory factor (0-2 points)
    memory_factor = min(2.0, memory_info['total_memory_mb'] / 100)  # 100MB = 1 point, 200MB = 2 points
    
    return min(10.0, base_score + memory_factor)

def maybe_sample(
    df: pd.DataFrame,
    size_threshold: int = 100_000,
    complexity_threshold: float = 5.0,
    random_state: int = 42,
    stratify_col: Optional[str] = None
) -> Tuple[pd.DataFrame, Dict[str, Any], Dict[str, Any]]:
    """
    Intelligently sample a DataFrame and return:
      - sampled_df
      - prompt_metadata (for AI prompt)
      - full_report (for UI)
    """
    # Empty DataFrame case
    if df.empty:
        metadata = generate_sampling_metadata(
            df, df, False,
            "Empty DataFrame – no sampling performed",
            None, None, None, 0.0
        )
        return df.copy(), metadata, {"error": "Empty DataFrame"}

    # Analyze & score
    data_analysis = analyze_data_characteristics(df)
    current_score = enhanced_smart_sampling_score(df)
    n_rows = len(df)

    # Decide if sampling is needed
    needs_sampling = (n_rows > size_threshold) or (current_score > complexity_threshold)
    if not needs_sampling:
        reason = (
            f"Dataset size ({n_rows:,} rows) below threshold ({size_threshold:,}) "
            f"and complexity score ({current_score:.1f}) acceptable."
        )
        metadata = generate_sampling_metadata(
            df, df, False, reason, 1.0, None, None, current_score
        )
        report = generate_sampling_report(df, metadata, data_analysis)
        return df.copy(), metadata, report

    # Adaptive fraction
    base_frac = min(0.9, max(0.3, 1.0 - current_score*0.08))
    if data_analysis["temporal_columns"]:
        base_frac = min(0.8, base_frac)

    # Determine stratification column
    strat_col = stratify_col
    if strat_col and strat_col not in df.columns:
        logger.warning(f"Stratify column '{strat_col}' not in DataFrame; ignoring.")
        strat_col = None

    if not strat_col:
        # Auto-select most imbalanced categorical col
        imbalances = [
            (col, info["imbalance_ratio"])
            for col, info in data_analysis["categorical"].get("imbalance", {}).items()
            if info["unique_values"] <= 50 and info["imbalance_ratio"] > 5
        ]
        if imbalances:
            strat_col = max(imbalances, key=lambda x: x[1])[0]
            logger.info(f"Auto-stratifying by '{strat_col}'.")

    # Sample - FIXED: Use train_size instead of test_size to get the correct fraction
    sampled_df: pd.DataFrame
    stratified = False
    if strat_col and df[strat_col].nunique() > 1:
        try:
            sampled_df, _ = train_test_split(  # FIXED: swapped assignment
                df,
                train_size=base_frac,  # FIXED: use train_size to specify fraction to keep
                stratify=df[strat_col],
                random_state=random_state
            )
            stratified = True
        except Exception as e:
            logger.warning(f"Stratified sampling failed ({e}); falling back to random.")

    if not stratified:
        sampled_df = df.sample(frac=base_frac, random_state=random_state)

    reason = (
        f"Dataset sampled: size {n_rows:,} rows -> {len(sampled_df):,} rows "
        f"({base_frac:.2f} fraction), score={current_score:.1f}."
    )

    # Build outputs
    metadata = generate_sampling_metadata(
        df, sampled_df, True, reason, base_frac,
        random_state, strat_col if stratified else None,
        current_score
    )
    report = generate_sampling_report(df, metadata, data_analysis)

    return sampled_df, metadata, report