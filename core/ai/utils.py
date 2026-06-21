# core/ai/utils.py - PRODUCTION READY AI UTILITIES
"""
Core AI utilities for Data Explorer Pro.
"""

import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
import streamlit as st
import time
import re
import hashlib
from datetime import datetime
from copy import deepcopy

from core.config import DEFAULT_CONFIG
from core.ai.echo_engine import EchoChartRecommender
from core.ai.call import build_story_and_charts_prompt, request_ai_json, GENAI_AVAILABLE, CLAUDE_AVAILABLE

# Import canonical schema functions
from core.ai.charts_utils import (
    normalize_ai_response,
    validate_canonical_chart,
    CHART_FAMILIES,
)

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION & STATE MANAGEMENT
# ============================================================================

def get_ai_config() -> Dict[str, Any]:
    """
    Get current AI configuration from session state.
    Returns clean config with safe defaults and chart family awareness.
    """
    return {
        'api_key': st.session_state.get('api_key', '').strip(),
        'model': st.session_state.get('ai_model', 'EchoEngine'),
        'temperature': min(0.9, max(0.1, st.session_state.get('ai_temperature', 0.3))),
        'EchoEngine_mode': bool(st.session_state.get('ai_EchoEngine_mode', True)),
        'debug_mode': bool(st.session_state.get('debug_mode', False)),
        'max_charts': 6,
        'min_charts': 3,
        'chart_families': CHART_FAMILIES,  # Include for reference
    }


def should_use_EchoEngine_mode(config: Dict[str, Any]) -> bool:
    """
    Determine if we should use EchoEngine mode based on configuration.
    Intelligent decision making with clear fallback logic.

    Args:
        config: AI configuration dict.

    Returns:
        True if EchoEngine mode should be used.
    """
    # Explicit EchoEngine model
    if config.get('model') == 'EchoEngine':
        logger.info("Using EchoEngine (explicit model selection)")
        return True

    # Force EchoEngine mode
    if config.get('EchoEngine_mode', False):
        logger.info("Using EchoEngine (EchoEngine mode enabled)")
        return True

    # No API key for live models
    if not config.get('api_key'):
        logger.warning("No API key provided, falling back to EchoEngine")
        return True

    # Library availability
    model = config.get('model', '')
    if model.startswith('gemini') and not GENAI_AVAILABLE:
        logger.error("Gemini requested but library not available")
        return True

    if model.startswith('claude') and not CLAUDE_AVAILABLE:
        logger.error("Claude requested but library not available")
        return True

    # Invalid model name
    if model not in ['gemini-2.5-flash-lite', 'claude-3-haiku-20240307', 'EchoEngine']:
        logger.warning(f"Unrecognized model '{model}', defaulting to EchoEngine")
        return True

    return False


# ============================================================================
# ENHANCED VALIDATION FUNCTIONS
# ============================================================================

def validate_chart_with_data(chart_config: Dict, df: pd.DataFrame) -> Tuple[bool, str, str]:
    """
    Validate chart config against actual data with family awareness.
    Returns: (is_valid, message, level) where level is 'success', 'warning', or 'error'
    """
    chart_type = chart_config.get('chart_type')
    if not chart_type:
        return False, "Missing chart_type", "error"

    # Get family from chart or determine it
    family = chart_config.get('_family')
    if not family:
        # Try to determine family
        for fam, info in CHART_FAMILIES.items():
            if chart_type in info['charts']:
                family = fam
                break
        if not family:
            family = 'xy'  # Default to XY family

    # Validate based on family
    if family == 'metric':
        value_col = chart_config.get('value_col')
        if not value_col:
            return False, f"{chart_type} requires 'value_col' field", "error"
        if value_col not in df.columns:
            return False, f"Value column '{value_col}' not found in data", "error"

        # Check target_value is number if provided
        target = chart_config.get('target_value')
        if target and isinstance(target, str) and target in df.columns:
            return True, f"'target_value' should be a number, not column name '{target}'", "warning"

    elif family == 'hierarchical':
        path = chart_config.get('path')
        if not path:
            return False, f"{chart_type} requires 'path' array for hierarchy", "error"
        if not isinstance(path, list):
            return False, "'path' must be an array of column names", "error"
        if len(path) == 0:
            return False, "'path' array cannot be empty", "error"

        for col in path:
            if col not in df.columns:
                return False, f"Path column '{col}' not found in data", "error"

    elif family == 'geospatial':
        lat = chart_config.get('lat_col')
        lon = chart_config.get('lon_col')
        if not lat or not lon:
            return False, f"{chart_type} requires both 'lat_col' and 'lon_col'", "error"
        if lat not in df.columns:
            return False, f"Latitude column '{lat}' not found in data", "error"
        if lon not in df.columns:
            return False, f"Longitude column '{lon}' not found in data", "error"

    else:  # xy family or special
        x = chart_config.get('x')
        if x and x not in df.columns:
            return False, f"X column '{x}' not found in data", "error"

        # Check if y is needed for certain chart types
        if chart_type in ['line', 'scatter', 'bar', 'box', 'violin', 'bubble']:
            y = chart_config.get('y')
            if not y:
                return False, f"{chart_type} requires 'y' column", "error"
            if y not in df.columns:
                return False, f"Y column '{y}' not found in data", "error"

        # Check optional fields if provided
        for field in ['color', 'size']:
            col = chart_config.get(field)
            if col and col not in df.columns:
                return True, f"Optional {field} column '{col}' not found", "warning"

    return True, "✓ Valid chart configuration", "success"


def validate_dataset_for_analysis(df: pd.DataFrame, user_prompt: str) -> Dict[str, Any]:
    """
    Validate dataset and prompt for analysis with comprehensive error messages.
    Returns detailed validation result with suggestions.
    """
    error_details = []
    warnings = []
    suggestions = []

    # Dataset validation
    if df is None:
        error_details.append("No dataset loaded. Please upload or select sample data first.")
        return {
            'valid': False,
            'message': error_details[0],
            'error_type': 'no_dataset',
            'suggestions': ["Upload a CSV, Excel, or JSON file", "Try sample datasets from the sidebar"]
        }

    if df.empty:
        error_details.append("Dataset is empty. Please load a valid dataset.")
        return {
            'valid': False,
            'message': error_details[0],
            'error_type': 'empty_dataset',
            'suggestions': ["Check your file format", "Verify the data has content"]
        }

    if len(df.columns) == 0:
        error_details.append("Dataset has no columns. Please check your data.")
        return {
            'valid': False,
            'message': error_details[0],
            'error_type': 'no_columns',
            'suggestions': ["Check column headers", "Try different file format"]
        }

    if len(df) < 3:
        error_details.append(f"Dataset has only {len(df)} rows (minimum 3 required for analysis).")
        return {
            'valid': False,
            'message': error_details[0],
            'error_type': 'insufficient_data',
            'suggestions': ["Add more data points", "Use a larger dataset"]
        }

    # Prompt validation
    if not user_prompt or not user_prompt.strip():
        error_details.append("Please provide an analysis request.")
        return {
            'valid': False,
            'message': error_details[0],
            'error_type': 'no_prompt',
            'suggestions': ["Ask about trends, patterns, or comparisons", "Use quick suggestions for inspiration"]
        }

    if len(user_prompt) > 1000:
        warnings.append(f"Prompt is long ({len(user_prompt)} chars). For best results, keep under 1000 characters.")

    # Data quality checks
    numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
    categorical_cols = [
        col for col in df.columns
        if df[col].dtype == "object" or pd.api.types.is_categorical_dtype(df[col])
    ]
    datetime_cols = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]

    if not numeric_cols and not categorical_cols:
        error_details.append("Dataset needs at least one numeric or categorical column for analysis.")
        return {
            'valid': False,
            'message': error_details[0],
            'error_type': 'no_analyzable_columns',
            'suggestions': ["Check data types", "Convert text to categorical if appropriate"]
        }

    # Check data quality
    total_cells = len(df) * len(df.columns)
    if total_cells > 0:
        missing_cells = df.isnull().sum().sum()
        missing_pct = (missing_cells / total_cells) * 100

        if missing_pct > 50:
            warnings.append(f"Dataset has {missing_pct:.0%} missing values. Results may be limited.")
            suggestions.append("Consider using data cleaning tools in Data Preparation tab")

        if missing_pct > 75:
            error_details.append(f"Dataset has {missing_pct:.0%} missing values. Please clean your data first.")
            return {
                'valid': False,
                'message': error_details[0],
                'error_type': 'excessive_missing_data',
                'suggestions': ["Use fill missing values tool", "Remove rows/columns with too many missing values"]
            }

    # Generate analysis suggestions based on data shape
    if numeric_cols and datetime_cols:
        suggestions.append("Try asking about trends over time with date columns")
    if categorical_cols and numeric_cols:
        suggestions.append("Try asking to compare categories using bar charts")
    if len(numeric_cols) >= 2:
        suggestions.append("Try asking about correlations between variables")

    # Success response with details
    return {
        'valid': True,
        'message': f"✅ Ready for analysis: {len(df):,} rows × {len(df.columns)} columns",
        'error_type': 'valid',
        'warnings': warnings,
        'suggestions': suggestions,
        'details': {
            'rows': len(df),
            'columns': len(df.columns),
            'numeric_columns': len(numeric_cols),
            'categorical_columns': len(categorical_cols),
            'datetime_columns': len(datetime_cols),
            'missing_percentage': missing_pct if total_cells > 0 else 0.0,
        }
    }


def create_error_response(title: str, message: str, error: str = "") -> Dict[str, Any]:
    """
    Create professional error response with helpful suggestions.
    """
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

    # Common error patterns and suggestions
    error_lower = error.lower() if error else ""
    suggestions = [
        "Try a simpler or more specific question",
        "Check your data quality in the Data Preparation tab",
        "Use manual analysis tools in Chart Studio",
        "Try heuristic analysis (turn on EchoEngine mode)"
    ]

    # Add specific suggestions based on error
    if "api" in error_lower or "key" in error_lower:
        suggestions.append("Check your API key in the sidebar settings")
        suggestions.append("Try EchoEngine mode for free heuristic analysis")

    if "json" in error_lower or "parse" in error_lower:
        suggestions.append("The AI response format was unexpected")
        suggestions.append("Try rephrasing your question more clearly")

    if "column" in error_lower or "field" in error_lower:
        suggestions.append("Verify column names exist in your dataset")
        suggestions.append("Check for typos in column references")

    return {
        "story": f"{title}\n\n{message}\n\n*Error occurred at {timestamp}*",
        "charts": [],
        "ai_generated": False,
        "error": error[:200] if error else "Unknown error",
        "analysis_mode": "error",
        "generated_at": time.time(),
        "id": f"error_{int(time.time())}_{hashlib.md5((error or title).encode()).hexdigest()[:8]}",
        "metadata": {
            "error_type": "analysis_failed",
            "timestamp": timestamp,
            "suggestions": suggestions[:3],
            "severity": "high"
        }
    }


# ============================================================================
# INTELLIGENT ANALYSIS GENERATION - ENHANCED
# ============================================================================

def ai_generate_analysis(
    df: pd.DataFrame,
    user_prompt: str,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Main AI analysis function with enhanced validation and family awareness.

    Features:
    - Comprehensive dataset validation
    - Chart family-aware normalization
    - Intelligent fallback mechanisms
    - Detailed error reporting
    - Performance timing

    Args:
        df: The dataset.
        user_prompt: The user's question/request.
        config: Optional AI configuration dict. If not provided, falls back to
                reading from st.session_state (legacy mode).

    Returns:
        Analysis result dict (story, charts, metadata, etc.).
    """
    # Professional timing
    start_time = time.time()
    logger.info(f"🚀 Starting AI analysis: '{user_prompt[:50]}...'")

    # Use provided config or fall back to session state
    if config is None:
        config = get_ai_config()
    else:
        # Ensure we have all needed keys by merging with defaults
        defaults = get_ai_config()
        # Merge, giving precedence to passed config
        config = {**defaults, **config}

    # Input validation
    validation_result = validate_dataset_for_analysis(df, user_prompt)
    if not validation_result['valid']:
        logger.error(f"Validation failed: {validation_result['message']}")
        return create_error_response(
            "⚠️ Input Validation Failed",
            validation_result['message'],
            validation_result.get('error_type', 'validation_error')
        )

    # Log validation warnings if any
    for warning in validation_result.get('warnings', []):
        logger.warning(f"Dataset warning: {warning}")

    try:
        debug_mode = config.get('debug_mode', False)

        if debug_mode:
            logger.info(f"📊 Dataset: {len(df):,} rows, {len(df.columns)} cols")
            logger.info(f"🤖 Model: {config['model']}")
            logger.info(f"🌡️ Temperature: {config['temperature']}")

        # Generate dataset context (timed)
        context_start = time.time()
        summary = analyze_dataset_summary(df)
        sample_data = get_data_sample(df)
        context_time = time.time() - context_start

        if debug_mode:
            logger.info(f"⏱️ Context generation: {context_time:.2f}s")

        # Choose analysis path based on configuration
        use_echoengine = should_use_EchoEngine_mode(config)

        if use_echoengine:
            if debug_mode:
                logger.info("🔧 Using heuristic analysis (EchoEngine mode)")

            result = generate_heuristic_analysis(df, user_prompt, summary, sample_data, config)
            result['analysis_mode'] = 'heuristic'
            result['ai_generated'] = False
            result['model'] = 'EchoEngine'

        else:
            if debug_mode:
                logger.info(f"🤖 Using live AI: {config['model']}")

            result = call_live_ai(df, user_prompt, summary, sample_data, config)
            result['analysis_mode'] = 'ai'
            result['ai_generated'] = True
            result['model'] = config['model']

        # ENHANCED VALIDATION: Filter and validate charts with family awareness
        if result.get('charts'):
            valid_charts = []
            warnings = []
            skipped = 0

            for chart in result['charts']:
                try:
                    # Normalize with family awareness
                    normalized = normalize_ai_response(chart)

                    # Validate against data
                    is_valid, msg, level = validate_chart_with_data(normalized, df)

                    if is_valid and level == "success":
                        normalized['_validated'] = True
                        normalized['_validation_status'] = 'success'
                        valid_charts.append(normalized)

                    elif is_valid and level == "warning":
                        # Keep with warning
                        normalized['_validated'] = True
                        normalized['_validation_status'] = 'warning'
                        normalized['_warning'] = msg
                        valid_charts.append(normalized)
                        warnings.append(f"Chart '{normalized.get('title', '')}': {msg}")

                    else:
                        # Skip invalid
                        skipped += 1
                        if debug_mode:
                            logger.warning(f"Skipping invalid chart: {msg}")

                except Exception as e:
                    logger.warning(f"Chart processing failed: {str(e)[:100]}")
                    skipped += 1

            result['charts'] = valid_charts

            # Add validation summary to metadata
            result.setdefault('metadata', {})
            result['metadata']['chart_validation'] = {
                'total_suggested': len(result.get('charts', [])) + skipped,
                'validated': len(valid_charts),
                'skipped': skipped,
                'warnings': len(warnings),
                'success_rate': f"{len(valid_charts)}/{len(valid_charts) + skipped}"
            }

            # Add warnings to story if any (but not too many)
            if warnings and 'story' in result:
                warning_count = len(warnings)
                if warning_count <= 2:
                    warning_text = "\n\n**Note**: " + "; ".join(warnings)
                else:
                    warning_text = f"\n\n**Note**: {warning_count} charts had minor issues (e.g., {warnings[0].split(':')[0]})"
                result['story'] += warning_text

        # Ensure we have at least one chart or provide guidance
        if not result.get('charts') and 'story' in result:
            result['story'] += "\n\n*No visualizations were generated. Try asking about specific columns or relationships.*"

        # Add comprehensive metadata
        result['generated_at'] = time.time()
        result['generation_time'] = time.time() - start_time
        result['dataset_info'] = {
            'rows': len(df),
            'columns': len(df.columns),
            'numeric_columns': len(summary.get('numeric_columns', [])),
            'categorical_columns': len(summary.get('categorical_columns', [])),
            'datetime_columns': len(summary.get('datetime_columns', [])),
            'data_quality_score': summary.get('data_quality_score', 0),
        }

        # Add performance timing breakdown
        result['timing'] = {
            'total': result['generation_time'],
            'context': context_time,
            'analysis': result['generation_time'] - context_time,
            'validation': time.time() - start_time - result['generation_time']
        }

        # Ensure story is properly formatted
        if 'story' in result:
            result['story'] = format_story_for_display(result['story'])

        # Extract insights from story for quick reference
        if result.get('story'):
            insights = extract_insights_from_story(result['story'])
            if insights:
                result['insights'] = insights
                result['metadata']['insight_count'] = len(insights)

        # Add unique ID for tracking
        result['id'] = f"analysis_{int(time.time())}_{hashlib.md5(json.dumps(result).encode()).hexdigest()[:8]}"

        # Log completion
        chart_count = len(result.get('charts', []))
        analysis_time = result['generation_time']

        logger.info(f"✅ Analysis complete: {analysis_time:.2f}s, {chart_count} charts, {result.get('analysis_mode', 'unknown')} mode")

        if debug_mode and chart_count > 0:
            for i, chart in enumerate(result['charts'][:3], 1):
                chart_type = chart.get('chart_type', 'unknown')
                title = chart.get('title', 'Untitled')[:30]
                logger.debug(f"  Chart {i}: {chart_type} - '{title}'")

        return result

    except Exception as e:
        logger.error(f"❌ AI analysis failed: {str(e)}", exc_info=True)

        # Create detailed error response
        return create_error_response(
            "## ⚠️ Analysis Failed",
            f"**Error**: {str(e)[:200]}\n\n"
            + f"**Technical Details**:\n"
            + f"• Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            + f"• Dataset: {len(df):,} rows × {len(df.columns)} columns\n"
            + f"• Prompt: '{user_prompt[:50]}...'\n\n"
            + f"**Next Steps**:",
            str(e)
        )


def generate_heuristic_analysis(
    df: pd.DataFrame,
    user_prompt: str,
    summary: Dict[str, Any],
    sample_data: List[Dict],
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate heuristic analysis using EchoEngine with enhanced suggestions.
    """
    try:
        # Use the recommender from EchoEngine
        recommender = EchoChartRecommender(config=DEFAULT_CONFIG)
        raw_charts = recommender.recommend_charts(df, user_prompt, max_suggestions=config.get('max_charts', 6))

        # Process and validate charts
        valid_charts = []
        for chart in raw_charts:
            if isinstance(chart, dict):
                # Normalize using canonical schema with family awareness
                normalized = normalize_ai_response(chart)

                # Basic validation
                is_valid, validation_msg = validate_canonical_chart(normalized, df)
                if is_valid:
                    normalized['heuristic'] = True
                    normalized['source'] = 'EchoEngine'
                    normalized['_validated'] = True
                    valid_charts.append(normalized)

        # Build enhanced story
        story = build_analysis_story(df, user_prompt, summary, valid_charts, is_heuristic=True)

        return {
            "story": story,
            "charts": valid_charts,
            "ai_generated": False,
            "model": "EchoEngine",
            "source": "heuristic",
            "metadata": {
                "heuristic_mode": True,
                "chart_count": len(valid_charts),
                "recommendation": "Provide API key for AI-powered analysis with detailed insights",
                "limitations": "Heuristic analysis uses pattern matching, not AI reasoning",
                "upgrade_suggestion": "Add API key for Gemini or Claude for better results"
            }
        }

    except Exception as e:
        logger.error(f"Heuristic analysis failed: {e}")

        # Clean fallback with guidance
        return {
            "story": build_fallback_story(df, user_prompt, summary, error=str(e)[:100]),
            "charts": [],
            "ai_generated": False,
            "model": "heuristic_error",
            "error": str(e)[:100],
            "metadata": {
                "error": str(e)[:100],
                "fallback_mode": True,
                "suggestions": [
                    "Try simplifying your request",
                    "Check data format and quality",
                    "Consider uploading a different dataset"
                ]
            }
        }


def call_live_ai(
    df: pd.DataFrame,
    user_prompt: str,
    summary: Dict[str, Any],
    sample_data: List[Dict],
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Call live AI API with enhanced error handling and retry logic.
    """
    try:
        # Build optimized prompt with detailed context
        prompt = build_story_and_charts_prompt(
            df_summary=summary,
            user_prompt=user_prompt,
        )

        if config.get('debug_mode'):
            logger.debug(f"📝 Prompt length: {len(prompt):,} chars")
            logger.debug(f"🌡️ Temperature: {config['temperature']}")

        # Call AI with retry logic
        response = request_ai_json(
            prompt=prompt,
            api_key=config['api_key'],
            model=config['model'],
            temperature=config['temperature'],
            df=df,
            max_retries=2
        )

        if not response:
            logger.warning("AI returned no response, falling back to heuristic")
            return generate_heuristic_analysis(df, user_prompt, summary, sample_data, config)

        # Extract components
        story = response.get('story', '')
        raw_charts = response.get('charts', [])

        # Filter and validate charts
        valid_charts = []
        for chart in raw_charts:
            if isinstance(chart, dict):
                is_valid, validation_msg = validate_canonical_chart(chart, df)
                if is_valid:
                    chart['ai_generated'] = True
                    chart['model'] = config['model']
                    chart['_source'] = 'live_ai'
                    valid_charts.append(chart)

        # Ensure we have output
        if not story and not valid_charts:
            logger.warning("AI returned empty response")
            return {
                "story": build_fallback_story(df, user_prompt, summary, error="Empty AI response"),
                "charts": [],
                "ai_generated": True,
                "model": config['model'],
                "error": "Empty AI response",
                "metadata": {
                    "ai_error": "Empty response",
                    "fallback_used": False
                }
            }

        # Build result with AI metadata
        result = {
            "story": story or build_fallback_story(df, user_prompt, summary),
            "charts": valid_charts,
            "ai_generated": True,
            "model": config['model'],
            "source": "live_ai",
            "metadata": {
                **response.get('metadata', {}),
                "api_used": True,
                "model_family": "gemini" if config['model'].startswith('gemini') else "claude",
                "response_quality": "good" if story and valid_charts else "limited"
            }
        }

        return result

    except Exception as e:
        logger.error(f"Live AI call failed: {e}")

        # Graceful fallback to heuristic with explanation
        heuristic_result = generate_heuristic_analysis(df, user_prompt, summary, sample_data, config)
        heuristic_result['metadata']['ai_fallback'] = True
        heuristic_result['metadata']['ai_error'] = str(e)[:100]
        heuristic_result['story'] = f"## ⚠️ AI Service Unavailable\n\n" + \
                                  f"Live AI analysis failed. Using heuristic fallback.\n\n" + \
                                  heuristic_result.get('story', '')

        return heuristic_result


# ============================================================================
# DATA UTILITIES
# ============================================================================

def get_data_sample(df: pd.DataFrame, n_rows: int = 20) -> List[Dict[str, Any]]:
    """
    Get clean data sample for AI context with intelligent sampling.
    """
    if df is None or df.empty:
        return []

    try:
        # Intelligent sampling based on dataset size
        if len(df) > 1000:
            # For large datasets, sample intelligently
            sample_size = min(n_rows * 3, 150, len(df))
            # Try to get diverse samples
            if len(df.columns) > 1:
                # Sample with stratification for categorical columns if available
                categorical_cols = [
                    col for col in df.columns
                    if df[col].dtype == "object" or pd.api.types.is_categorical_dtype(df[col])
                ]
                if categorical_cols and len(categorical_cols) > 0:
                    # Use first categorical column for stratification
                    strat_col = categorical_cols[0]
                    if df[strat_col].nunique() < 20:  # Only if reasonable number of categories
                        try:
                            sample_df = df.groupby(strat_col, group_keys=False).apply(
                                lambda x: x.sample(min(len(x), max(1, sample_size // df[strat_col].nunique())))
                            ).head(n_rows)
                        except:
                            sample_df = df.sample(min(sample_size, len(df))).head(n_rows)
                    else:
                        sample_df = df.sample(min(sample_size, len(df))).head(n_rows)
                else:
                    sample_df = df.sample(min(sample_size, len(df))).head(n_rows)
            else:
                sample_df = df.sample(min(sample_size, len(df))).head(n_rows)
        else:
            sample_df = df.head(n_rows)

        # Convert to JSON-serializable format with type handling
        result = []
        for _, row in sample_df.iterrows():
            row_dict = {}
            for col in sample_df.columns:
                val = row[col]

                if pd.isna(val):
                    row_dict[col] = None
                elif isinstance(val, (np.integer, np.int64, np.int32, int)):
                    row_dict[col] = int(val)
                elif isinstance(val, (np.float64, np.float32, float)):
                    if np.isinf(val) or np.isnan(val):
                        row_dict[col] = None
                    else:
                        # Round for readability
                        row_dict[col] = round(float(val), 4)
                elif isinstance(val, (datetime, pd.Timestamp)):
                    row_dict[col] = val.isoformat() if not pd.isna(val) else None
                elif isinstance(val, (bool, np.bool_)):
                    row_dict[col] = bool(val)
                else:
                    # Stringify with length limit
                    str_val = str(val)
                    if len(str_val) > 100:
                        str_val = str_val[:97] + "..."
                    row_dict[col] = str_val

            result.append(row_dict)

        return result

    except Exception as e:
        logger.error(f"Failed to create data sample: {e}")
        # Fallback to simple head
        try:
            return df.head(min(n_rows, len(df))).to_dict('records')
        except:
            return []


def analyze_dataset_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate comprehensive dataset summary with enhanced statistics.
    """
    if df is None or df.empty:
        return {
            "row_count": 0,
            "col_count": 0,
            "columns": {},
            "numeric_columns": [],
            "categorical_columns": [],
            "datetime_columns": [],
            "missing_data_percentage": 0.0,
            "analysis_timestamp": time.time()
        }

    try:
        columns_info = {}
        numeric_cols = []
        categorical_cols = []
        datetime_cols = []

        # Analyze each column
        for col in df.columns:
            try:
                series = df[col]
                dtype_str = str(series.dtype)

                col_info = {
                    "dtype": dtype_str,
                    "unique_count": int(series.nunique()),
                    "missing_count": int(series.isnull().sum()),
                    "missing_percentage": float((series.isnull().sum() / len(df)) * 100),
                    "sample_values": []
                }

                # Get sample non-null values (up to 3)
                non_null_samples = series.dropna().head(3).tolist()
                for sample in non_null_samples:
                    if isinstance(sample, (datetime, pd.Timestamp)):
                        col_info["sample_values"].append(sample.isoformat())
                    elif isinstance(sample, float):
                        col_info["sample_values"].append(round(sample, 4))
                    else:
                        col_info["sample_values"].append(str(sample))

                # Detect column type and add appropriate statistics
                if pd.api.types.is_numeric_dtype(series):
                    col_info["type"] = "numeric"
                    numeric_cols.append(col)

                    if series.count() > 0:
                        col_info["statistics"] = {
                            "min": float(series.min()),
                            "max": float(series.max()),
                            "mean": float(series.mean()),
                            "std": float(series.std()),
                            "median": float(series.median()),
                            "q25": float(series.quantile(0.25)),
                            "q75": float(series.quantile(0.75)),
                        }

                elif pd.api.types.is_datetime64_any_dtype(series):
                    col_info["type"] = "datetime"
                    datetime_cols.append(col)

                    if series.count() > 0:
                        col_info["statistics"] = {
                            "min": series.min().isoformat(),
                            "max": series.max().isoformat(),
                            "range_days": (series.max() - series.min()).days,
                        }

                elif series.dtype == 'object' or pd.api.types.is_categorical_dtype(series):
                    col_info["type"] = "categorical"
                    categorical_cols.append(col)

                    if series.count() > 0:
                        value_counts = series.value_counts()
                        col_info["statistics"] = {
                            "top_values": value_counts.head(5).to_dict(),
                            "value_distribution": "high_cardinality" if series.nunique() > 50 else "low_cardinality"
                        }

                else:
                    col_info["type"] = "other"

                columns_info[col] = col_info

            except Exception as col_error:
                logger.debug(f"Error analyzing column {col}: {col_error}")
                columns_info[col] = {
                    "dtype": str(df[col].dtype),
                    "type": "unknown",
                    "error": str(col_error)[:100]
                }

        # Calculate data quality metrics
        total_cells = len(df) * len(df.columns)
        missing_cells = df.isnull().sum().sum()
        missing_percentage = (missing_cells / total_cells * 100) if total_cells > 0 else 0

        # Calculate data quality score (0-100)
        completeness_score = 100 - missing_percentage
        diversity_score = sum(1 for col_info in columns_info.values()
                            if col_info.get('unique_count', 0) > 1) / len(columns_info) * 100
        data_quality_score = (completeness_score * 0.7 + diversity_score * 0.3)

        return {
            "row_count": len(df),
            "col_count": len(df.columns),
            "columns": columns_info,
            "numeric_columns": numeric_cols,
            "categorical_columns": categorical_cols,
            "datetime_columns": datetime_cols,
            "missing_data_percentage": missing_percentage,
            "analysis_timestamp": time.time(),
            "data_quality_score": max(0, min(100, data_quality_score)),
            "summary_stats": {
                "total_cells": total_cells,
                "complete_cells": total_cells - missing_cells,
                "completeness_percentage": 100 - missing_percentage,
                "column_type_distribution": {
                    "numeric": len(numeric_cols),
                    "categorical": len(categorical_cols),
                    "datetime": len(datetime_cols),
                    "other": len(df.columns) - len(numeric_cols) - len(categorical_cols) - len(datetime_cols)
                }
            }
        }

    except Exception as e:
        logger.error(f"Dataset analysis failed: {e}")

        # Minimal fallback
        return {
            "row_count": len(df),
            "col_count": len(df.columns),
            "numeric_columns": [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])],
            "categorical_columns": [col for col in df.columns if df[col].dtype == "object" or pd.api.types.is_categorical_dtype(df[col])],
            "datetime_columns": [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])],
            "missing_data_percentage": 0.0,
            "analysis_timestamp": time.time(),
            "data_quality_score": 0,
            "error": str(e)[:100]
        }


# ============================================================================
# STORY AND INSIGHTS GENERATION
# ============================================================================

def build_analysis_story(
    df: pd.DataFrame,
    user_prompt: str,
    summary: Dict[str, Any],
    charts: List[Dict[str, Any]],
    is_heuristic: bool = False
) -> str:
    """
    Build professional analysis story with enhanced insights.
    """
    analysis_method = "Heuristic analysis" if is_heuristic else "AI-powered analysis"
    timestamp = time.strftime('%Y-%m-%d %H:%M')
    data_quality = summary.get('data_quality_score', 0)

    story_parts = [
        f"## 📊 Analysis: {user_prompt}",
        "",
        f"**Dataset**: {len(df):,} records × {len(df.columns)} columns",
        f"**Method**: {analysis_method}",
        f"**Data Quality**: {data_quality:.0f}/100" if data_quality > 0 else "",
        f"**Generated**: {timestamp}",
        "",
    ]

    # Filter out empty lines
    story_parts = [line for line in story_parts if line.strip()]

    # Dataset overview
    numeric_count = len(summary.get('numeric_columns', []))
    categorical_count = len(summary.get('categorical_columns', []))
    datetime_count = len(summary.get('datetime_columns', []))

    story_parts.append("### 📋 Dataset Overview")

    if numeric_count:
        top_numeric = summary.get('numeric_columns', [])[:3]
        story_parts.append(f"• **{numeric_count} numeric columns** for quantitative analysis")
        if top_numeric:
            story_parts.append(f"  Examples: {', '.join(top_numeric)}")

    if categorical_count:
        top_categorical = summary.get('categorical_columns', [])[:3]
        story_parts.append(f"• **{categorical_count} categorical columns** for segmentation")
        if top_categorical:
            story_parts.append(f"  Examples: {', '.join(top_categorical)}")

    if datetime_count:
        story_parts.append(f"• **{datetime_count} date/time columns** for trend analysis")

    # Chart recommendations
    if charts:
        story_parts.append("")
        story_parts.append("### 📈 Recommended Visualizations")

        for i, chart in enumerate(charts, 1):
            title = chart.get('title', f'Chart {i}')
            description = chart.get('description', '')
            chart_type = chart.get('chart_type', 'chart').title().replace('_', ' ')

            story_parts.append(f"**{i}. {title}**")
            story_parts.append(f"  *Type*: {chart_type}")
            if description:
                story_parts.append(f"  *Purpose*: {description}")

            # Add column info for the chart
            if chart.get('x'):
                story_parts.append(f"  *X-axis*: `{chart['x']}`")
            if chart.get('y'):
                story_parts.append(f"  *Y-axis*: `{chart['y']}`")
            if chart.get('value_col'):
                story_parts.append(f"  *Metric*: `{chart['value_col']}`")
            if chart.get('path'):
                path_str = ' → '.join(chart['path'][:3])
                story_parts.append(f"  *Hierarchy*: {path_str}")

    # Key findings based on chart types
    story_parts.append("")
    story_parts.append("### 💡 Key Insights")

    # Analyze chart types to generate insights
    chart_types = [chart.get('chart_type', '') for chart in charts[:3]]

    if 'line' in chart_types or any('trend' in chart.get('title', '').lower() for chart in charts[:2]):
        story_parts.append("• **Time-based patterns** reveal important trends and seasonality")
        story_parts.append("• Consider comparing multiple time periods for deeper insights")

    if 'bar' in chart_types or 'box' in chart_types:
        story_parts.append("• **Category comparisons** highlight performance differences")
        story_parts.append("• Top performers and underperformers are clearly visible")

    if 'scatter' in chart_types or 'correlation_matrix' in chart_types:
        story_parts.append("• **Variable relationships** show how factors influence each other")
        story_parts.append("• Strong correlations may indicate causal relationships")

    if 'histogram' in chart_types or 'density' in chart_types:
        story_parts.append("• **Data distributions** reveal central tendencies and outliers")
        story_parts.append("• Check for normal distribution or skewness in key metrics")

    if 'treemap' in chart_types:
        story_parts.append("• **Hierarchical structures** show part-to-whole relationships")
        story_parts.append("• Largest segments dominate the visualization")

    # Add generic insights if needed
    if len([p for p in story_parts if p.startswith("• ")]) < 4:
        story_parts.append("• **Data patterns** emerge from systematic analysis")
        story_parts.append("• **Actionable insights** can drive business decisions")
        story_parts.append("• **Further segmentation** may reveal additional insights")

    # Next steps
    story_parts.append("")
    story_parts.append("### 🚀 Next Steps")

    if numeric_count >= 2:
        story_parts.append("• **Explore correlations** between numeric variables")

    if categorical_count >= 1 and numeric_count >= 1:
        story_parts.append("• **Compare performance** across different categories")

    if datetime_count >= 1 and numeric_count >= 1:
        story_parts.append("• **Analyze trends** over time for key metrics")

    story_parts.append("• **Use filters** to drill down into specific segments")
    story_parts.append("• **Export visualizations** for reports and presentations")
    story_parts.append("• **Ask follow-up questions** for deeper analysis")

    # Professional footer
    story_parts.append("")
    story_parts.append("---")
    story_parts.append(f"*Analysis completed at {timestamp} using Data Explorer Pro*")

    if is_heuristic:
        story_parts.append("*Using heuristic pattern detection. For AI-powered insights, add an API key.*")

    return "\n".join(story_parts)


def build_fallback_story(
    df: pd.DataFrame,
    user_prompt: str,
    summary: Dict[str, Any],
    error: str = ""
) -> str:
    """Build helpful fallback story when analysis fails."""

    error_note = f"\n\n**Note**: Analysis encountered an issue: {error[:100]}" if error else ""

    # Get column suggestions
    numeric_cols = summary.get('numeric_columns', [])[:5]
    categorical_cols = summary.get('categorical_columns', [])[:5]
    datetime_cols = summary.get('datetime_columns', [])[:3]

    column_suggestions = []
    if numeric_cols and categorical_cols:
        column_suggestions.append(f"Compare `{categorical_cols[0]}` with `{numeric_cols[0]}`")
    if datetime_cols and numeric_cols:
        column_suggestions.append(f"Track `{numeric_cols[0]}` over time using `{datetime_cols[0]}`")
    if len(numeric_cols) >= 2:
        column_suggestions.append(f"Explore relationship between `{numeric_cols[0]}` and `{numeric_cols[1]}`")

    suggestion_text = ""
    if column_suggestions:
        suggestion_text = "\n\n**Try asking about**:\n" + "\n".join([f"• {s}" for s in column_suggestions])

    return f"""## 📋 Basic Dataset Overview

**Query**: "{user_prompt[:100]}{'...' if len(user_prompt) > 100 else ''}"
**Status**: Basic overview (full analysis unavailable)
**Dataset**: {len(df):,} records × {len(df.columns)} columns

**Available Columns**:
• Numeric ({len(numeric_cols)}): {', '.join(numeric_cols) if numeric_cols else 'None'}
• Categorical ({len(categorical_cols)}): {', '.join(categorical_cols) if categorical_cols else 'None'}
• Date/Time ({len(datetime_cols)}): {', '.join(datetime_cols) if datetime_cols else 'None'}

**Analysis Approaches**:
1. **Trend Analysis**: Use date columns with numeric metrics
2. **Comparison**: Compare categories using bar or box plots
3. **Correlation**: Explore relationships between numeric variables
4. **Distribution**: Understand spread and outliers in your data
5. **Composition**: Show parts of a whole with pie or treemap charts

{suggestion_text}

**To get better results**:
• Be specific about which columns to analyze
• Ask about relationships between specific variables
• Use the Chart Studio for manual visualization
• Check data quality in Data Preparation tab

{error_note}

*Generated: {time.strftime('%Y-%m-%d %H:%M')}*"""


# ============================================================================
# UI HELPER FUNCTIONS
# ============================================================================

def format_story_for_display(story: str) -> str:
    """
    Format story for clean display in UI with proper markdown formatting.
    """
    if not story:
        return "No analysis available."

    # Clean up common formatting issues
    story = story.strip()

    # Replace chart references with consistent format
    story = re.sub(r'\$CHART_(\d+)\$', r'**Chart \1**', story)
    story = re.sub(r'\[CHART_(\d+)\]', r'**Chart \1**', story)
    story = re.sub(r'CHART_(\d+)', r'**Chart \1**', story)

    # Fix common markdown issues
    story = re.sub(r'\*\*(.*?)\*\*\s*\*\*(.*?)\*\*', r'**\1 \2**', story)  # Merge adjacent bold
    story = re.sub(r'#\s+#', '# ', story)  # Fix double headers

    # Ensure proper line spacing
    lines = story.split('\n')
    formatted_lines = []

    for i, line in enumerate(lines):
        line = line.rstrip()

        # Skip empty lines at the very beginning
        if i == 0 and not line:
            continue

        # Handle headers with proper spacing
        if line.startswith('##### '):
            if formatted_lines and formatted_lines[-1] != '':
                formatted_lines.append('')
            formatted_lines.append(f"##### {line[6:]}")
        elif line.startswith('#### '):
            if formatted_lines and formatted_lines[-1] != '':
                formatted_lines.append('')
            formatted_lines.append(f"#### {line[5:]}")
            formatted_lines.append('')
        elif line.startswith('### '):
            if formatted_lines and formatted_lines[-1] != '':
                formatted_lines.append('')
            formatted_lines.append(f"### {line[4:]}")
            formatted_lines.append('')
        elif line.startswith('## '):
            if formatted_lines and formatted_lines[-1] != '':
                formatted_lines.append('')
            formatted_lines.append(f"## {line[3:]}")
            formatted_lines.append('')
        elif line.startswith('# '):
            if formatted_lines and formatted_lines[-1] != '':
                formatted_lines.append('')
            formatted_lines.append(f"# {line[2:]}")
            formatted_lines.append('')

        # Handle lists
        elif line.startswith('- ') or line.startswith('* ') or line.startswith('• '):
            if formatted_lines and formatted_lines[-1] != '' and not formatted_lines[-1].startswith('#'):
                formatted_lines.append('')
            formatted_lines.append(f"• {line[2:]}")
        elif re.match(r'^\d+\.\s', line):
            if formatted_lines and formatted_lines[-1] != '' and not formatted_lines[-1].startswith('#'):
                formatted_lines.append('')
            formatted_lines.append(line)

        # Handle regular text
        elif line:
            formatted_lines.append(line)
        else:
            # Empty line - only add if previous line wasn't empty
            if formatted_lines and formatted_lines[-1] != '':
                formatted_lines.append('')

    # Clean up multiple consecutive empty lines
    result = []
    last_empty = False

    for line in formatted_lines:
        if line == '':
            if not last_empty:
                result.append(line)
                last_empty = True
        else:
            result.append(line)
            last_empty = False

    # Ensure we end with content, not empty line
    while result and result[-1] == '':
        result.pop()

    return '\n'.join(result)


def extract_insights_from_story(story: str, max_insights: int = 5) -> List[str]:
    """
    Extract key insights from story text with intelligent pattern matching.
    Returns most important insights for quick reference.
    """
    if not story:
        return []

    insights = []

    # Look for bullet points first (most likely insights)
    lines = story.split('\n')

    for line in lines:
        line = line.strip()

        # Look for bullet points with insight-like content
        if line.startswith(('- ', '• ', '* ', '1. ', '2. ', '3. ', '4. ', '5. ')):
            # Clean the bullet point
            clean_line = re.sub(r'^[•\-\*\d\.\s]+', '', line)

            # Check if it looks like an insight (not too short, not a header)
            if (len(clean_line) > 25 and len(clean_line) < 200 and
                not clean_line.endswith(':') and
                'http' not in clean_line.lower() and
                'chart' not in clean_line.lower()):
                insights.append(clean_line.strip())

        # Look for sentences with insight indicators
        elif len(line) > 40 and len(line) < 250:
            insight_indicators = [
                'shows that', 'indicates that', 'suggests that', 'implies that',
                'demonstrates', 'reveals that', 'highlights', 'confirms that',
                'suggests', 'indicates', 'reveals', 'shows',
                'important to note', 'key finding', 'notable observation',
                'we can see', 'it is clear', 'this suggests'
            ]

            if any(indicator in line.lower() for indicator in insight_indicators):
                # Clean up the line
                clean_line = re.sub(r'\*\*', '', line)
                clean_line = re.sub(r'\[CHART_\d+\]', '', clean_line)
                clean_line = re.sub(r'\*\*Chart \d+\*\*', '', clean_line)
                clean_line = re.sub(r'\s+', ' ', clean_line).strip()

                # Remove trailing punctuation issues
                clean_line = re.sub(r'[\.;,:]\s*$', '', clean_line)

                if len(clean_line) > 30:
                    insights.append(clean_line)

    # Deduplicate and prioritize
    unique_insights = []
    seen = set()

    for insight in insights:
        # Normalize for comparison
        normalized = insight.lower().strip()
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)

        if normalized not in seen and len(insight) > 10:
            unique_insights.append(insight)
            seen.add(normalized)

    # Score insights by importance (simple heuristic)
    scored_insights = []
    for insight in unique_insights:
        score = 0

        # Score based on length (medium length is good)
        if 50 <= len(insight) <= 150:
            score += 2

        # Score based on keywords
        importance_keywords = [
            'significant', 'important', 'key', 'major', 'critical',
            'strong', 'clear', 'notable', 'substantial', 'considerable'
        ]
        for keyword in importance_keywords:
            if keyword in insight.lower():
                score += 1

        # Score based on being a complete sentence
        if insight[0].isupper() and insight[-1] in '.!?':
            score += 1

        scored_insights.append((score, insight))

    # Sort by score and take top insights
    scored_insights.sort(key=lambda x: x[0], reverse=True)
    top_insights = [insight for _, insight in scored_insights[:max_insights]]

    # Clean up insights for display
    final_insights = []
    for insight in top_insights:
        # Trim if too long
        if len(insight) > 120:
            insight = insight[:117] + '...'
        final_insights.append(insight)

    return final_insights


# ============================================================================
# UTILITY FUNCTIONS FOR UI INTEGRATION
# ============================================================================

def get_analysis_quality_score(result: Dict[str, Any]) -> int:
    """
    Calculate a quality score for analysis results (0-100).
    """
    score = 50  # Base score

    # Score based on chart count
    chart_count = len(result.get('charts', []))
    if chart_count >= 3:
        score += 20
    elif chart_count >= 1:
        score += 10

    # Score based on story length
    story = result.get('story', '')
    if len(story) > 500:
        score += 15
    elif len(story) > 200:
        score += 5

    # Score based on validation
    validated = result.get('metadata', {}).get('chart_validation', {}).get('validated', 0)
    suggested = result.get('metadata', {}).get('chart_validation', {}).get('total_suggested', 1)
    if suggested > 0:
        validation_rate = validated / suggested
        score += int(validation_rate * 15)

    # Penalize errors
    if result.get('error'):
        score -= 20

    return min(100, max(0, score))


def format_analysis_metadata(result: Dict[str, Any]) -> str:
    """
    Format analysis metadata for display.
    """
    metadata = []

    # Model info
    model = result.get('model', 'Unknown')
    if model == 'EchoEngine':
        metadata.append(f"**Model**: {model} (Heuristic)")
    else:
        metadata.append(f"**Model**: {model}")

    # Timing
    gen_time = result.get('generation_time', 0)
    if gen_time > 0:
        metadata.append(f"**Time**: {gen_time:.1f}s")

    # Chart count
    chart_count = len(result.get('charts', []))
    if chart_count > 0:
        metadata.append(f"**Charts**: {chart_count}")

    # Validation info
    validation = result.get('metadata', {}).get('chart_validation', {})
    if validation.get('validated', 0) > 0:
        metadata.append(f"**Validated**: {validation['validated']}/{validation.get('total_suggested', 0)}")

    return " • ".join(metadata)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Main analysis function
    "ai_generate_analysis",

    # Configuration
    "get_ai_config",
    "should_use_EchoEngine_mode",

    # Validation functions
    "validate_chart_with_data",
    "validate_dataset_for_analysis",

    # Data utilities
    "get_data_sample",
    "analyze_dataset_summary",

    # Story and formatting
    "format_story_for_display",
    "extract_insights_from_story",
    "build_analysis_story",
    "build_fallback_story",

    # Utility functions
    "create_error_response",
    "get_analysis_quality_score",
    "format_analysis_metadata",
]