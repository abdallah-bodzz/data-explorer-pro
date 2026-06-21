# data_scripts.py
"""
🚀 Professional Data Scripts Runner
One-click solutions for common data problems
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
import time
import traceback
import json

# Import script implementations
try:
    from core.data.scripts_library import (
        # Global flags
        FUZZY_AVAILABLE, PHONETICS_AVAILABLE, STATSMODELS_AVAILABLE, SCIPY_AVAILABLE,
        
        # Detective Scripts
        find_fuzzy_duplicates,
        detect_data_types,
        find_anomaly_patterns,
        
        # Fixer Scripts
        split_columns_smartly,
        handle_missing_data,
        fix_date_formats,
        
        # Transformer Scripts
        build_cohort_analysis,
        decompose_time_series,
        engineer_features,
        
        # Business Intelligence
        segment_customers_rfm,
        analyze_pricing,
        analyze_ab_test,
        
        # Emergency Cleanup
        normalize_text,
        match_schemas,
        sanitize_pii_data
    )
    SCRIPTS_AVAILABLE = True
except ImportError as e:
    SCRIPTS_AVAILABLE = False
    FUZZY_AVAILABLE = False
    PHONETICS_AVAILABLE = False
    STATSMODELS_AVAILABLE = False
    SCIPY_AVAILABLE = False

# ============================================================================
# SCRIPT DEFINITIONS - CLEAN & PROFESSIONAL WITH DETAILED HOW-IT-WORKS
# ============================================================================

if SCRIPTS_AVAILABLE:
    SCRIPTS = {
        "Detective": [
            {
                "id": "duplicates",
                "name": "Find Fuzzy Duplicates",
                "description": "Advanced duplicate detection using fuzzy matching (Levenshtein distance) and phonetic algorithms. Identifies near-identical records despite typos, abbreviations, case variations, or formatting differences. Returns clustered duplicates with suggested canonical values.",
                "icon": "🕵️",
                "function": find_fuzzy_duplicates,
                "requires": ["text_columns"],
                "outputs": ["cleaned_data", "duplicate_report"],
                "category": "Detective",
                "needs_deps": not FUZZY_AVAILABLE,
                "dep_message": "pip install fuzzywuzzy python-Levenshtein",
                "how_it_works": """
                **Algorithm Overview:**
                1. **Text Normalization**: Converts all text to lowercase, removes special characters, standardizes common terms (Inc, Ltd, Street -> St)
                2. **Similarity Scoring**: Uses Levenshtein distance (fuzzywuzzy) for string similarity + Metaphone phonetic algorithm for sound-alike matching
                3. **Clustering**: Groups values with similarity ≥ threshold (default: 85%) into clusters
                4. **Canonical Selection**: Chooses most complete/formal version as reference (longest, proper case)

                **Technical Details:**
                - Processes first 5 text columns for performance
                - Handles datasets up to 10k rows efficiently
                - Returns confidence scores (high/medium) based on cluster size
                - Adds cluster_id columns to original data for traceability

                **Performance Notes:**
                - Complexity: O(n²) for each column (limited to 5 columns)
                - Memory: Creates normalized text cache
                - Time: ~1 second per 1000 rows per column

                **Use Cases:**
                - Customer name deduplication
                - Address standardization
                - Product name cleaning
                """
            },
            {
                "id": "types",
                "name": "Detect Data Types",
                "description": "Intelligent data type inference with 70%+ confidence threshold. Automatically converts messy text to proper types (dates, currencies, booleans, percentages). Handles mixed formats in same column and provides conversion report.",
                "icon": "🔍",
                "function": detect_data_types,
                "requires": ["mixed_types"],
                "outputs": ["converted_data", "type_report"],
                "category": "Detective",
                "needs_deps": False,
                "how_it_works": """
                **Detection Pipeline:**
                1. **Type Testing**: Tests each column against 7 type detectors in priority order:
                   - Datetime (20+ format patterns)
                   - Integer (whole numbers only)
                   - Float (decimal numbers)
                   - Boolean (true/false, yes/no, 1/0)
                   - Categorical (<30% unique values)
                   - Currency ($, €, £ symbols)
                   - Percentage (% signs)

                2. **Confidence Scoring**: Each detector returns 0.0-1.0 confidence based on pattern matches
                3. **Conversion**: Applies conversion if confidence ≥ 0.7 (70%)

                **Technical Details:**
                - Date detection tests: ISO, US, European, and 17 other formats
                - Currency detection: Supports $, €, £, ¥ with/without commas
                - Boolean detection: 10+ true/false variations
                - Preserves null values during conversion

                **Edge Cases Handled:**
                - Mixed date formats in same column
                - Currency symbols with/without spaces
                - Percentage values as strings ("15%")
                - Scientific notation numbers

                **Quality Metrics:**
                - Success rate per conversion
                - Failed rows count
                - Evidence samples for debugging
                """
            },
            {
                "id": "anomalies",
                "name": "Find Anomaly Patterns",
                "description": "Statistical anomaly detection using Z-score analysis (3+ std deviations). Identifies outliers, impossible value combinations, temporal anomalies, and suspicious patterns beyond simple thresholds.",
                "icon": "📊",
                "function": find_anomaly_patterns,
                "requires": ["numeric_columns"],
                "outputs": ["anomaly_report", "flagged_data"],
                "category": "Detective",
                "needs_deps": False,
                "how_it_works": """
                **Multi-Layer Anomaly Detection:**

                1. **Statistical Outliers (Z-score):**
                   - Calculates mean and standard deviation per numeric column
                   - Flags values beyond 3 standard deviations (99.7% threshold)
                   - Temporal analysis if date column exists

                2. **Impossible Value Combinations:**
                   - Logical rule checking (e.g., age < 18 AND income > 100K)
                   - Business rule validation
                   - Cross-column consistency checks

                3. **Temporal Anomalies:**
                   - Future dates (beyond current date + buffer)
                   - Historical outliers (pre-1900 dates)
                   - Unusual time patterns (midnight transactions)

                4. **Pattern-Based Detection:**
                   - Unusual hour distributions
                   - Round number clustering ($100, $500)
                   - Sequence anomalies

                **Technical Implementation:**
                - Z-score with Bessel's correction for sample std dev
                - Temporal analysis uses pandas datetime properties
                - Pattern detection via aggregation and statistical tests

                **Output:**
                - Flagged DataFrame with boolean outlier columns
                - Statistical report with confidence intervals
                - Temporal patterns analysis
                """
            }
        ],
        "Fixer": [
            {
                "id": "splitter",
                "name": "Smart Column Splitter",
                "description": "Intelligently splits combined columns using delimiter detection and pattern recognition. Automatically names new columns based on content analysis (street, city, zip). Handles inconsistent separators within same column.",
                "icon": "✂️",
                "function": split_columns_smartly,
                "requires": ["text_columns"],
                "outputs": ["split_data", "split_report"],
                "category": "Fixer",
                "needs_deps": False,
                "how_it_works": """
                **Smart Splitting Algorithm:**

                1. **Delimiter Detection:**
                   - Tests 9 common delimiters: , ; | \\t - / \\ : space
                   - Scores each delimiter by frequency and consistency
                   - Selects highest scoring delimiter automatically

                2. **Content-Aware Column Naming:**
                   - Analyzes sample data from each split column
                   - Detects patterns: addresses, names, codes
                   - Names columns accordingly: _street, _city, _zip, _state

                3. **Intelligent Cleaning:**
                   - Removes empty/whitespace-only columns
                   - Drops columns with >90% null values
                   - Preserves original data types where possible

                4. **Quality Validation:**
                   - Calculates split success rate
                   - Reports rows with missing parts
                   - Suggests alternative delimiters if low success

                **Technical Features:**
                - Handles variable number of splits per row
                - Smart null handling (empty strings → NaN)
                - Memory efficient (streaming split where possible)

                **Common Use Cases:**
                - Full name → first/last
                - Address → street/city/state/zip
                - Date-time → date/time components
                - CSV-in-a-column parsing
                """
            },
            {
                "id": "missing",
                "name": "Handle Missing Data",
                "description": "Comprehensive missing value analysis with optimal imputation strategy selection. Automatically chooses between mean/median/mode, forward fill, interpolation, or dropping based on data characteristics and missing patterns.",
                "icon": "💡",
                "function": handle_missing_data,
                "requires": ["any_data"],
                "outputs": ["imputed_data", "strategy_report"],
                "category": "Fixer",
                "needs_deps": False,
                "how_it_works": """
                **Intelligent Imputation Strategy Selection:**

                1. **Missing Pattern Analysis:**
                   - MCAR (Missing Completely at Random) detection
                   - MAR (Missing at Random) pattern identification
                   - MNAR (Missing Not at Random) flagging

                2. **Automatic Strategy Assignment:**
                   - **<20% missing**: Mean/Median/Mode based on skewness
                   - **20-50% missing**: Advanced imputation (interpolation, MICE*)
                   - **>50% missing**: Column dropping recommendation
                   - **Temporal data**: Forward/backward fill
                   - **Categorical**: Mode or "Unknown" imputation

                3. **Skew-Aware Imputation:**
                   - Normal distribution: Mean imputation
                   |Skew| > 1: Median imputation
                   - Binary/categorical: Mode imputation

                4. **Temporal Imputation:**
                   - Time series: Linear interpolation
                   - Dates: Forward fill with carryover
                   - Seasonal data: Seasonal decomposition imputation

                **Quality Controls:**
                - Tracks imputed vs original value distribution
                - Validates imputation doesn't create new outliers
                - Provides strategy justification per column

                *MICE: Multiple Imputation by Chained Equations (when scipy available)
                """
            },
            {
                "id": "dates",
                "name": "Fix Date Formats",
                "description": "Standardizes mixed date formats (MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD) to consistent datetime objects. Tests 20+ common formats and applies best match. Handles ambiguous dates with confidence scoring.",
                "icon": "🗓️",
                "function": fix_date_formats,
                "requires": ["date_like_columns"],
                "outputs": ["standardized_dates", "format_report"],
                "category": "Fixer",
                "needs_deps": False,
                "how_it_works": """
                **Multi-Format Date Parsing Engine:**

                1. **Format Testing Pipeline:**
                   - Tests 20+ date formats in priority order
                   - ISO 8601 (YYYY-MM-DD) → US (MM/DD/YYYY) → EU (DD/MM/YYYY)
                   - Month names (Jan, January) and ordinals (1st, 2nd)
                   - Epoch timestamps and Excel serial numbers

                2. **Confidence-Based Selection:**
                   - Scores each format by successful parse rate
                   - Requires ≥70% success for auto-selection
                   - Fallback to pandas intelligent parsing

                3. **Ambiguity Resolution:**
                   - MM/DD vs DD/MM: Uses locale hints and value ranges
                   - Two-digit years: 00-68 → 2000s, 69-99 → 1900s
                   - Invalid dates: February 30th → coerced to NaN

                4. **Output Standardization:**
                   - Converts to pandas datetime64[ns]
                   - Optional formatting: ISO, US, European
                   - Timezone-naive (UTC) for consistency

                **Technical Features:**
                - 100x faster than try-each-format loops
                - Memory efficient via vectorized operations
                - Handles 10,000+ dates per second

                **Supported Formats:**
                - 2023-12-25, 12/25/2023, 25/12/2023
                - Dec 25 2023, 25 December 2023
                - 20231225, 12252023
                - Unix timestamps, Excel serial numbers
                """
            }
        ],
        "Transformer": [
            {
                "id": "cohorts",
                "name": "Build Cohort Analysis",
                "description": "Converts transaction data to retention cohort matrices. Calculates cohort sizes, retention rates, and revenue metrics. Supports daily, weekly, monthly, and quarterly cohorts with time-since-first-purchase indexing.",
                "icon": "👥",
                "function": build_cohort_analysis,
                "requires": ["user_id", "date_column", "value_column"],
                "outputs": ["cohort_matrix", "retention_analysis"],
                "category": "Transformer",
                "needs_deps": False,
                "how_it_works": """
                **Cohort Analysis Engine:**

                1. **Cohort Definition:**
                   - First purchase date per customer = cohort assignment
                   - Flexible periodization: day, week, month, quarter
                   - Time index = periods since first purchase

                2. **Matrix Construction:**
                   - **User Matrix**: # of active customers per period
                   - **Revenue Matrix**: Total revenue per period
                   - **Retention Matrix**: % of cohort still active

                3. **Key Metrics Calculation:**
                   - **Cohort Size**: Initial customers in each cohort
                   - **Retention Rate**: Active % in periods 1, 3, 6, 12
                   - **LTV (Lifetime Value)**: Cumulative revenue per cohort
                   - **Churn Rate**: 1 - Retention rate

                4. **Visualization-Ready Output:**
                   - Heatmap-ready matrices
                   - Time-series retention curves
                   - Cohort comparison metrics

                **Business Insights:**
                - Identify best/worst performing acquisition periods
                - Measure feature impact on retention
                - Calculate customer lifetime value
                - Optimize marketing spend timing

                **Technical Implementation:**
                - Uses pandas Period for efficient time grouping
                - Handles 1M+ transactions efficiently
                - Memory optimized via sparse matrix representation
                """
            },
            {
                "id": "timeseries",
                "description": "Statistical time series decomposition using seasonal_decompose (additive/multiplicative). Separates trend, seasonality, and residual components. Calculates trend/seasonality strength and identifies residual outliers.",
                "name": "Decompose Time Series",
                "icon": "📈",
                "function": decompose_time_series,
                "requires": ["date_column", "numeric_column"],
                "outputs": ["decomposition", "forecast"],
                "category": "Transformer",
                "needs_deps": not STATSMODELS_AVAILABLE,
                "dep_message": "pip install statsmodels",
                "how_it_works": """
                **STL Decomposition Algorithm:**

                1. **Preprocessing:**
                   - Resampling to consistent frequency
                   - Handling missing values via interpolation
                   - Detrending for multiplicative model

                2. **Decomposition Process:**
                   - **Trend**: LOESS smoothing (seasonal-trend decomposition)
                   - **Seasonal**: Periodic component extraction
                   - **Residual**: Remainder = Observed - (Trend + Seasonal)

                3. **Model Selection:**
                   - **Additive**: Y = Trend + Seasonal + Residual
                   - **Multiplicative**: Y = Trend × Seasonal × Residual
                   - Automatic selection based on variance pattern

                4. **Statistical Analysis:**
                   - **Trend Strength**: 1 - Var(Residual)/Var(Trend+Residual)
                   - **Seasonality Strength**: 1 - Var(Residual)/Var(Seasonal+Residual)
                   - **Outliers**: |Residual| > 2σ flagged as anomalies

                **Technical Details:**
                - Uses Statsmodels' seasonal_decompose
                - Automatic period detection via FFT
                - Handles up to 10,000 time points
                - Returns pandas Series for easy plotting

                **Business Applications:**
                - Sales trend analysis
                - Seasonality adjustment for forecasting
                - Anomaly detection in metrics
                - Campaign impact isolation
                """
            },
            {
                "id": "features",
                "name": "Engineer Features",
                "description": "Machine learning feature engineering with train/test safety. Creates temporal features, interactions, lag variables, encoding schemes, and statistical transformations. Maintains data integrity for modeling pipelines.",
                "icon": "🤖",
                "function": engineer_features,
                "requires": ["mixed_data"],
                "outputs": ["enhanced_data", "feature_report"],
                "category": "Transformer",
                "needs_deps": False,
                "how_it_works": """
                **Feature Engineering Pipeline:**

                1. **Temporal Features:**
                   - Cyclical encoding (sin/cos for hours, days, months)
                   - Business day indicators
                   - Holiday/weekend flags
                   - Time since events

                2. **Numeric Transformations:**
                   - Log, square root, polynomial features
                   - Z-score standardization
                   - Quantile binning (5, 10 bins)
                   - Statistical moments (skew, kurtosis)

                3. **Categorical Encoding:**
                   - Frequency encoding (value counts)
                   - Target encoding (mean target per category)*
                   - Leave-one-out encoding for CV safety

                4. **Interaction Features:**
                   - Product interactions (A × B)
                   - Ratio features (A / B)
                   - Conditional combinations

                5. **Lag & Window Features:**
                   - Time-series lags (1, 7, 30 periods)
                   - Rolling statistics (mean, std, min, max)
                   - Expanding window features

                **Technical Safeguards:**
                - Prevents data leakage via group-based encoding
                - Handles NaN in transformations gracefully
                - Limits features to prevent dimensionality explosion
                - Provides feature importance via correlation

                *Target encoding only with target column provided
                """
            }
        ],
        "Business": [
            {
                "id": "rfm",
                "name": "Segment Customers (RFM)",
                "description": "Customer segmentation using Recency-Frequency-Monetary analysis with automatic quartile scoring. Creates 11 strategic segments (Champions, Loyal, At Risk, Lost) with actionable recommendations for each.",
                "icon": "💎",
                "function": segment_customers_rfm,
                "requires": ["customer_id", "date_column", "transaction_value"],
                "outputs": ["segments", "action_plan"],
                "category": "Business",
                "needs_deps": False,
                "how_it_works": """
                **RFM Segmentation Methodology:**

                1. **Metric Calculation:**
                   - **Recency**: Days since last purchase (lower = better)
                   - **Frequency**: Total transactions (higher = better)
                   - **Monetary**: Total spend (higher = better)

                2. **Quartile Scoring (1-4):**
                   - Each metric divided into 4 equal quartiles
                   - R: 4=most recent, 1=least recent
                   - F/M: 4=highest, 1=lowest

                3. **Segment Mapping:**
                   - **Champions (444, 443)**: Recent, frequent, high value
                   - **Loyal (344, 343)**: Regular, high value but less recent
                   - **At Risk (124, 123)**: Once valuable, now inactive
                   - **Lost (111)**: Inactive, low value, not recent

                4. **Action Plan Generation:**
                   - **Champions**: Reward, upsell, ask for reviews
                   - **Loyal**: Loyalty programs, exclusive offers
                   - **At Risk**: Win-back campaigns, surveys
                   - **Lost**: Reactivation campaigns, deep discounts

                **Technical Implementation:**
                - Pandas quantile-based scoring
                - Handles 1M+ customers efficiently
                - Memory optimized via chunk processing

                **Business Applications:**
                - Targeted marketing campaign design
                - Customer lifetime value optimization
                - Churn prediction and prevention
                - Resource allocation optimization
                """
            },
            {
                "id": "pricing",
                "name": "Analyze Pricing",
                "description": "Price elasticity analysis and optimal pricing recommendations. Calculates price-quantity correlations, segments by price tiers, and identifies revenue-optimal price points with statistical validation.",
                "icon": "💰",
                "function": analyze_pricing,
                "requires": ["price_column", "quantity_column"],
                "outputs": ["elasticity_analysis", "price_recommendations"],
                "category": "Business",
                "needs_deps": False,
                "how_it_works": """
                **Pricing Analytics Engine:**

                1. **Elasticity Estimation:**
                   - Correlation analysis: price vs quantity
                   - Elasticity = %ΔQuantity / %ΔPrice
                   - Cross-price elasticity for product groups

                2. **Price Segmentation:**
                   - Quartile-based price tiers (Low, Medium, High)
                   - Performance analysis per tier:
                     * Revenue contribution
                     * Volume contribution
                     * Profit margin estimation

                3. **Optimal Price Detection:**
                   - Revenue = Price × Quantity curve analysis
                   - Marginal revenue calculation
                   - Competitive price positioning

                4. **Statistical Validation:**
                   - Confidence intervals for elasticity estimates
                   - Bootstrap resampling for robustness
                   - Outlier impact assessment

                **Technical Analysis:**
                - Uses log-log regression for elasticity*
                - Monte Carlo simulation for uncertainty
                - Market basket analysis for cross-elasticity

                **Business Recommendations:**
                - **Elastic goods**: Lower prices to increase revenue
                - **Inelastic goods**: Raise prices carefully
                - **Luxury goods**: Premium pricing strategies
                - **Commodities**: Competitive price matching

                *When statsmodels available, otherwise uses correlation
                """
            },
            {
                "id": "abtest",
                "name": "Analyze A/B Test",
                "description": "Statistical A/B test analysis with t-tests, confidence intervals, and power analysis. Calculates lift, statistical significance (p < 0.05), and provides clear implementation recommendations.",
                "icon": "🧪",
                "function": analyze_ab_test,
                "requires": ["test_group_column", "metric_column"],
                "outputs": ["statistical_report", "recommendation"],
                "category": "Business",
                "needs_deps": not SCIPY_AVAILABLE,
                "dep_message": "pip install scipy",
                "how_it_works": """
                **Statistical Test Pipeline:**

                1. **Descriptive Statistics:**
                   - Group means, standard deviations
                   - 95% confidence intervals
                   - Sample size per variant

                2. **Hypothesis Testing:**
                   - **Null hypothesis**: No difference between groups
                   - **Alternative**: Groups are statistically different
                   - **Test**: Welch's t-test (unequal variances)
                   - **Significance**: p < 0.05 threshold

                3. **Effect Size Calculation:**
                   - **Cohen's d**: Standardized mean difference
                   - **Lift**: % improvement over control
                   - **NNT**: Number needed to treat for impact

                4. **Power Analysis:**
                   - **Statistical power**: Probability of detecting true effect
                   - **Required sample size**: For 80% power at α=0.05
                   - **Minimum detectable effect**: Smallest effect detectable

                5. **Business Interpretation:**
                   - **Winner declaration** (if p < 0.05 and positive lift)
                   - **Confidence rating**: High/Medium/Low based on power
                   - **Risk assessment**: Type I/II error probabilities

                **Technical Implementation:**
                - Uses scipy.stats for t-tests
                - Statsmodels for power analysis
                - Bonferroni correction for multiple comparisons

                **Outputs:**
                - Statistical significance (p-value)
                - Practical significance (lift %)
                - Implementation recommendation
                - Sample size recommendation for follow-up
                """
            }
        ],
        "Cleanup": [
            {
                "id": "normalize",
                "name": "Normalize Text",
                "description": "Comprehensive text normalization: fixes encoding issues (UTF-8), standardizes whitespace, corrects common typos, applies smart casing rules, and removes special characters while preserving structure.",
                "icon": "🧹",
                "function": normalize_text,
                "requires": ["text_columns"],
                "outputs": ["cleaned_text", "changes_summary"],
                "category": "Cleanup",
                "needs_deps": False,
                "how_it_works": """
                **Text Normalization Pipeline:**

                1. **Encoding Correction:**
                   - Fixes UTF-8 mojibake (Ã© → é, â€™ → ')
                   - Handles Windows-1252 vs UTF-8 conflicts
                   - Normalizes to UTF-8 encoding

                2. **Whitespace Standardization:**
                   - Removes leading/trailing whitespace
                   - Collapses multiple spaces to single
                   - Normalizes line endings (\\r\\n → \\n)

                3. **Typo Correction:**
                   - 50+ common spelling errors (recieve → receive)
                   - Abbreviation expansion (St. → Street, Inc. → Incorporated)
                   - Date/month abbreviation standardization

                4. **Smart Casing:**
                   - **Names**: Title case (John Smith)
                   - **Emails**: Lowercase (john@example.com)
                   - **Addresses**: Proper case (Main Street)
                   - **Boolean values**: Standardized (True/False)

                5. **Special Character Handling:**
                   - Preserves: . - @ , ; : ' "
                   - Removes: control characters, emoji, non-printable
                   - Standardizes: quotes, dashes, bullets

                **Technical Features:**
                - Regex-based for performance
                - Vectorized pandas operations
                - Memory efficient via in-place modifications

                **Quality Metrics:**
                - Changes per column count
                - Before/after samples
                - Encoding issue detection rate
                """
            },
            {
                "id": "schema",
                "name": "Match Schemas",
                "description": "Fuzzy schema matching for dataset merging. Uses column name similarity, data type compatibility, and value distribution analysis to suggest column mappings between datasets with confidence scores.",
                "icon": "🔗",
                "function": match_schemas,
                "requires": ["multiple_datasets"],
                "outputs": ["merged_data", "mapping_report"],
                "category": "Cleanup",
                "needs_deps": not FUZZY_AVAILABLE,
                "dep_message": "pip install fuzzywuzzy python-Levenshtein",
                "how_it_works": """
                **Schema Matching Algorithm:**

                1. **Schema Analysis:**
                   - Column names, data types, unique value counts
                   - Null percentages, sample value distributions
                   - Data type families (numeric, text, datetime, boolean)

                2. **Similarity Scoring (0-1 scale):**
                   - **Name Similarity (40%)**: Levenshtein distance on normalized names
                   - **Type Compatibility (30%)**: Can types be safely converted?
                   - **Value Distribution (30%)**: Similar unique value ratios

                3. **Confidence Classification:**
                   - **High (>0.7)**: Automatic mapping recommended
                   - **Medium (0.5-0.7)**: Review suggested
                   - **Low (<0.5)**: Manual inspection required

                4. **Mapping Suggestions:**
                   - One-to-one column mappings
                   - Many-to-one consolidation suggestions
                   - Data type conversion recommendations
                   - Null handling strategy alignment

                **Technical Implementation:**
                - Hungarian algorithm for optimal matching
                - Fuzzy string matching with token sort ratio
                - Data type compatibility matrix

                **Use Cases:**
                - Merging datasets from different sources
                - Schema evolution tracking
                - Data warehouse table alignment
                - API response to database mapping
                """
            },
            {
                "id": "privacy",
                "name": "Sanitize PII Data",
                "description": "GDPR/CCPA compliant PII detection and anonymization. Identifies emails, phones, SSNs, credit cards with pattern matching. Applies appropriate masking while preserving data utility.",
                "icon": "🔒",
                "function": sanitize_pii_data,
                "requires": ["text_columns"],
                "outputs": ["sanitized_data", "privacy_report"],
                "category": "Cleanup",
                "needs_deps": False,
                "how_it_works": """
                **PII Detection & Sanitization:**

                1. **Detection Methods:**
                   - **Column Name Patterns**: email, phone, ssn in column names
                   - **Content Patterns**: Regex for emails, phones, SSNs, credit cards
                   - **Statistical Analysis**: Value distribution analysis

                2. **Sensitivity Levels:**
                   - **Conservative**: Only obvious PII (SSN, credit cards)
                   - **Standard**: + emails, phones, IP addresses
                   - **Aggressive**: + names, addresses, partial matching

                3. **Anonymization Techniques:**
                   - **Email**: ***@domain.com (preserves domain)
                   - **Phone**: ***-***-1234 (preserves last 4)
                   - **SSN**: ***-**-1234 (preserves last 4)
                   - **Credit Card**: **** **** **** 1234
                   - **Names**: J*** S*** (preserves initials)
                   - **Addresses**: *** Main Street (removes numbers)

                4. **Compliance Features:**
                   - GDPR Article 17 (right to erasure) compliance
                   - CCPA data subject access request support
                   - Audit trail of all modifications
                   - Reversibility option (with secure key)

                **Technical Implementation:**
                - 20+ regex patterns for global PII formats
                - Performance optimized for large datasets
                - Configurable false positive thresholds

                **Quality Assurance:**
                - Before/after samples for verification
                - False positive/negative reporting
                - Data utility preservation metrics
                """
            }
        ]
    }
else:
    SCRIPTS = {}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def _analyze_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze dataset to determine which scripts are applicable"""
    if df is None or df.empty:
        return {}
    
    analysis = {
        "row_count": len(df),
        "column_count": len(df.columns),
        "numeric_columns": df.select_dtypes(include=[np.number]).columns.tolist(),
        "text_columns": df.select_dtypes(include=['object']).columns.tolist(),
        "date_columns": [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])],
        "missing_count": df.isnull().sum().sum(),
        "duplicate_rows": df.duplicated().sum()
    }
    
    # Additional checks
    analysis["has_user_id"] = any('id' in str(col).lower() or 'user' in str(col).lower() for col in df.columns)
    analysis["has_dates"] = len(analysis["date_columns"]) > 0
    analysis["has_prices"] = any('price' in str(col).lower() or 'amount' in str(col).lower() or 'revenue' in str(col).lower() for col in df.columns)
    analysis["has_groups"] = any('group' in str(col).lower() or 'variant' in str(col).lower() or 'test' in str(col).lower() for col in df.columns)
    analysis["has_email"] = any('email' in str(col).lower() for col in df.columns)
    analysis["has_address"] = any('address' in str(col).lower() or 'city' in str(col).lower() or 'zip' in str(col).lower() for col in df.columns)
    
    return analysis

def _check_script_requirements(script: Dict, analysis: Dict, df: pd.DataFrame) -> Tuple[bool, str]:
    """Check if script can run on current dataset"""
    
    # First check if script needs dependencies
    if script.get('needs_deps', False):
        return False, f"Missing dependencies: {script.get('dep_message', 'Install required packages')}"
    
    requires = script.get("requires", [])
    
    if not requires:
        return True, "Ready"
    
    checks = {
        "any_data": lambda: len(df) > 0,
        "text_columns": lambda: len(analysis.get("text_columns", [])) > 0,
        "numeric_columns": lambda: len(analysis.get("numeric_columns", [])) > 0,
        "date_like_columns": lambda: (len(analysis.get("date_columns", [])) > 0 or 
                                     any('date' in str(col).lower() for col in df.columns)),
        "mixed_types": lambda: (len(analysis.get("text_columns", [])) > 0 and 
                               len(analysis.get("numeric_columns", [])) > 0),
        "mixed_data": lambda: len(df.columns) >= 3,
        "user_id": lambda: analysis.get("has_user_id", False),
        "date_column": lambda: analysis.get("has_dates", False),
        "value_column": lambda: analysis.get("has_prices", False),
        "customer_id": lambda: analysis.get("has_user_id", False),
        "transaction_value": lambda: analysis.get("has_prices", False),
        "price_column": lambda: analysis.get("has_prices", False),
        "quantity_column": lambda: any('qty' in str(col).lower() or 'quantity' in str(col).lower() for col in df.columns),
        "test_group_column": lambda: analysis.get("has_groups", False),
        "metric_column": lambda: len(analysis.get("numeric_columns", [])) > 0,
        "multiple_datasets": lambda: len(st.session_state.get('relationship_datasets', {})) > 1
    }
    
    # Check each requirement
    failed_checks = []
    for req in requires:
        if req in checks:
            try:
                if not checks[req]():
                    failed_checks.append(req.replace("_", " "))
            except:
                failed_checks.append(req.replace("_", " "))
    
    if failed_checks:
        return False, f"Requires: {', '.join(failed_checks)}"
    
    return True, "Ready"

def _run_script_with_progress(df: pd.DataFrame, script_func, script_name: str, **kwargs) -> Dict[str, Any]:
    """Execute script with progress tracking"""
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Initialization
        progress_bar.progress(10)
        status_text.text("Initializing...")
        
        # Step 2: Execution
        progress_bar.progress(40)
        status_text.text(f"Running {script_name}...")
        
        result = script_func(df, **kwargs)
        
        # Step 3: Finalization
        progress_bar.progress(90)
        status_text.text("Finalizing results...")
        
        progress_bar.progress(100)
        status_text.text("Complete!")
        
        time.sleep(0.3)
        progress_bar.empty()
        status_text.empty()
        
        return {
            "success": True,
            "result": result,
            "error": None
        }
        
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        
        return {
            "success": False,
            "result": df,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

# ============================================================================
# UI COMPONENTS
# ============================================================================

def _render_script_card(script: Dict, analysis: Dict, df: pd.DataFrame, container):
    """Render a clean script card"""
    with container.container(border=True):
        # Check if script can run
        can_run, reason = _check_script_requirements(script, analysis, df)
        
        # Header with icon and name
        st.markdown(f"#### {script['icon']} {script['name']}")
        
        # Description
        st.caption(script['description'])
        
        # Status indicator with dependency warning
        if script.get('needs_deps', False):
            status_markdown = f"🔴 Missing dependencies"
            status_color = "red"
            with st.expander("⚠️ Dependency Required", expanded=False):
                st.caption(f"{script.get('dep_message', 'Install required packages')}")
                if st.button("📋 Copy Install Command", key=f"copy_{script['id']}"):
                    st.code(script.get('dep_message', ''))
        elif can_run:
            status_markdown = "🟢 Ready to run"
            status_color = "green"
        else:
            status_markdown = f"🟡 {reason}"
            status_color = "orange"
        
        st.markdown(f"<span style='color: {status_color}; font-size: 0.9em;'>{status_markdown}</span>", 
                   unsafe_allow_html=True)
        
        # Run button
        if st.button(
            "▶️ Run",
            key=f"btn_{script['category']}_{script['id']}",
            disabled=not can_run,
            use_container_width=True,
            type="primary" if can_run else "secondary"
        ):
            st.session_state.selected_script = script
            st.rerun()

def _render_dataset_summary(df: pd.DataFrame):
    """Render dataset summary bar"""
    with st.container(border=True):
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Rows", f"{len(df):,}")
        with col2:
            st.metric("Columns", len(df.columns))
        with col3:
            st.metric("Numeric", len(df.select_dtypes(include=[np.number]).columns))
        with col4:
            st.metric("Text", len(df.select_dtypes(include=['object']).columns))
        with col5:
            missing = df.isnull().sum().sum()
            st.metric("Missing", f"{missing:,}")

def _render_script_configuration(script: Dict, df: pd.DataFrame):
    """Render configuration options for selected script"""
    config = {}
    
    with st.form(key="script_config_form"):
        st.markdown("#### Configuration")
        
        # Performance warning for large datasets
        if len(df) > 10000:
            st.warning(f"⚠️ **Large Dataset Detected** ({len(df):,} rows)")
            if st.checkbox("Force run on large dataset", key="force_large"):
                config['force_large_dataset'] = True
            else:
                st.caption("Consider sampling or filtering for faster processing")
                config['disabled'] = True
        
        # Dynamic configuration based on script type
        if script['id'] == 'duplicates':
            config['similarity_threshold'] = st.slider(
                "Similarity threshold",
                min_value=0.70,
                max_value=0.95,
                value=0.85,
                help="Lower values catch more potential duplicates"
            )
            text_cols = df.select_dtypes(include=['object']).columns.tolist()
            if text_cols:
                config['columns_to_check'] = st.multiselect(
                    "Columns to check",
                    options=text_cols,
                    default=text_cols[:min(3, len(text_cols))]
                )
            else:
                st.info("No text columns available for duplicate detection")
        
        elif script['id'] == 'types':
            text_cols = df.select_dtypes(include=['object']).columns.tolist()
            if text_cols:
                config['columns_to_convert'] = st.multiselect(
                    "Columns to auto-convert",
                    options=text_cols,
                    default=text_cols[:min(5, len(text_cols))],
                    help="Select columns with ambiguous data types"
                )
            else:
                st.info("No text columns available for type detection")
        
        elif script['id'] == 'splitter':
            text_cols = df.select_dtypes(include=['object']).columns.tolist()
            if text_cols:
                config['column_to_split'] = st.selectbox(
                    "Select column to split",
                    options=text_cols,
                    help="Choose a column containing combined data"
                )
                config['delimiter'] = st.text_input(
                    "Delimiter (leave blank for auto-detect)",
                    value="",
                    help="e.g., comma, semicolon, pipe (|)"
                )
            else:
                st.info("No text columns available for splitting")
        
        elif script['id'] == 'dates':
            date_like_cols = [c for c in df.columns if 'date' in c.lower() or 'time' in c.lower()]
            if date_like_cols:
                config['date_columns'] = st.multiselect(
                    "Select date columns",
                    options=date_like_cols,
                    default=date_like_cols[:min(3, len(date_like_cols))],
                    help="Columns that contain date information"
                )
                config['output_format'] = st.selectbox(
                    "Output format",
                    options=["auto", "iso", "us", "europe"],
                    help="ISO: YYYY-MM-DD, US: MM/DD/YYYY, Europe: DD/MM/YYYY"
                )
            else:
                st.info("No obvious date columns found. Try 'Detect Data Types' first.")
        
        elif script['id'] == 'rfm':
            date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
            id_cols = [c for c in df.columns if 'id' in c.lower() or 'user' in c.lower()]
            value_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            
            if date_cols and id_cols and value_cols:
                config['customer_id_col'] = st.selectbox(
                    "Customer ID column",
                    options=id_cols,
                    index=0,
                    help="Column containing unique customer identifiers"
                )
                config['date_col'] = st.selectbox(
                    "Date column",
                    options=date_cols,
                    index=0,
                    help="Column containing transaction dates"
                )
                config['value_col'] = st.selectbox(
                    "Value column",
                    options=value_cols,
                    index=0,
                    help="Column containing transaction amounts"
                )
                config['time_unit'] = st.selectbox(
                    "Time unit for cohorts",
                    options=["month", "week", "quarter", "year"],
                    index=0
                )
            else:
                st.error("Need customer ID, date, and value columns for RFM analysis")
                if not date_cols:
                    st.caption("Missing: Date column")
                if not id_cols:
                    st.caption("Missing: Customer ID column")
                if not value_cols:
                    st.caption("Missing: Value column")
        
        # Submit button
        col1, col2 = st.columns([1, 1])
        with col1:
            submit_button = st.form_submit_button(
                "▶️ Run Script",
                type="primary",
                use_container_width=True,
                disabled=config.get('disabled', False)
            )
        with col2:
            cancel_button = st.form_submit_button(
                "Cancel",
                use_container_width=True
            )
    
    if cancel_button:
        cleanup_script_state()
        st.rerun()
    
    if submit_button:
        # Remove empty config values
        config = {k: v for k, v in config.items() if v is not None and v != ""}
        return config
    
    return None

def _display_script_results(result: Dict, script: Dict, original_df: pd.DataFrame):
    """Display results from script execution - FIXED & DIRECT"""
    
    # Error handling
    if not result.get("success", False):
        st.error(f"❌ Script Failed")
        
        error_msg = result.get('error', 'Unknown error')
        st.code(f"Error: {error_msg}", language="text")
        
        if st.checkbox("Show technical details"):
            st.text_area("Traceback", result.get('traceback', 'No traceback'), height=200)
        
        if st.button("← Back to Scripts"):
            cleanup_script_state()
            st.rerun()
        return
    
    # Get the script result
    script_result = result.get("result", {})
    
    # FIXED: Find the main DataFrame properly
    main_df = None
    
    # Priority order for output keys
    output_key_priority = [
        'enhanced_data', 'cleaned_data', 'converted_data', 'imputed_data',
        'split_data', 'standardized_dates', 'sanitized_data', 'cleaned_text',
        'flagged_data', 'rfm_scores', 'cohort_data', 'decomposition',
        'cohort_matrix', 'user_cohort_matrix', 'retention_matrix'
    ]
    
    if isinstance(script_result, dict):
        # Try priority keys first
        for key in output_key_priority:
            if key in script_result and isinstance(script_result[key], pd.DataFrame):
                main_df = script_result[key]
                break
        
        # Fallback: find any DataFrame
        if main_df is None:
            for key, value in script_result.items():
                if isinstance(value, pd.DataFrame):
                    main_df = value
                    break
    
    elif isinstance(script_result, pd.DataFrame):
        main_df = script_result
    
    # Show results
    if main_df is not None:
        st.markdown(f"### {script['name']} Results")
        
        # Data preview
        with st.expander("📊 Data Preview", expanded=True):
            st.dataframe(main_df.head(100), use_container_width=True)
            st.caption(f"{main_df.shape[0]:,} rows × {main_df.shape[1]} columns")
        
        # Show what changed
        if original_df is not None:
            original_rows = original_df.shape[0]
            original_cols = original_df.shape[1]
            new_rows = main_df.shape[0]
            new_cols = main_df.shape[1]
            
            # Highlight new columns
            new_columns = list(set(main_df.columns) - set(original_df.columns))
            removed_columns = list(set(original_df.columns) - set(main_df.columns))
            
            with st.container(border=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Rows", f"{new_rows:,}", f"{new_rows - original_rows:+}")
                with col2:
                    st.metric("Columns", f"{new_cols:,}", f"{new_cols - original_cols:+}")
                with col3:
                    st.metric("New Columns", len(new_columns))
                
                if new_columns:
                    st.caption(f"**New columns:** {', '.join(new_columns[:8])}")
                    if len(new_columns) > 8:
                        st.caption(f"...and {len(new_columns) - 8} more")
                
                if removed_columns:
                    st.warning(f"**Removed columns:** {', '.join(removed_columns)}")
        
        # # Additional reports if available
        # if isinstance(script_result, dict):
        #     report_keys = [k for k in script_result.keys() 
        #                   if isinstance(script_result[k], pd.DataFrame) and k != main_df.name if hasattr(main_df, 'name')]
        #     report_keys = [k for k in report_keys if k not in output_key_priority[:8]]
            
        #     if report_keys:
        #         with st.expander("📈 Detailed Reports", expanded=False):
        #             for report_key in report_keys[:3]:  # Limit to 3 reports
        #                 st.markdown(f"**{report_key.replace('_', ' ').title()}**")
        #                 st.dataframe(script_result[report_key].head(20), use_container_width=True)
        
        # CRITICAL FIX: SINGLE APPLY BUTTON - Updates BOTH dataset states
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("💾 **Apply to Dataset**", type="primary", use_container_width=True):
                # Update BOTH dataset states
                st.session_state.dataset = main_df.copy()
                st.session_state.base_dataset = main_df.copy()  # THIS WAS MISSING!
                
                # Reset filters (columns changed, filters break)
                st.session_state.filter_state = {
                    'filters': {},
                    'null_handling': {},
                    'logic_mode': "AND",
                    'logic_groups': [],
                    'applied': True
                }
                
                # Clear script state
                cleanup_script_state()
                
                # Show success
                st.success("✅ Dataset updated! All changes applied.")
                time.sleep(0.8)
                st.rerun()
        
        with col2:
            if st.button("← Back to Scripts", use_container_width=True):
                cleanup_script_state()
                st.rerun()
        
        # Export option for reports
        if isinstance(script_result, dict):
            report_dfs = [script_result[k] for k in script_result.keys() 
                         if isinstance(script_result[k], pd.DataFrame)]
            
            if report_dfs:
                with st.expander("📥 Export Reports", expanded=False):
                    for i, report_df in enumerate(report_dfs[:2]):
                        csv = report_df.to_csv(index=False)
                        st.download_button(
                            label=f"Download {list(script_result.keys())[i]}",
                            data=csv,
                            file_name=f"{script['id']}_{list(script_result.keys())[i]}.csv",
                            mime="text/csv"
                        )
    
    else:
        # No DataFrame found - show other outputs
        st.info("This script doesn't produce a modified dataset. Check reports below.")
        
        if isinstance(script_result, dict):
            with st.expander("📋 Script Output", expanded=True):
                for key, value in script_result.items():
                    if isinstance(value, pd.DataFrame):
                        st.markdown(f"**{key}**")
                        st.dataframe(value.head(20), use_container_width=True)
                    elif isinstance(value, dict):
                        st.markdown(f"**{key}**")
                        st.json(value, expanded=False)
                    elif isinstance(value, (str, int, float, bool)):
                        st.metric(key, str(value))
        
        if st.button("← Back to Scripts", use_container_width=True):
            cleanup_script_state()
            st.rerun()

def cleanup_script_state():
    """Clear temporary script results and states"""
    keys_to_remove = ['selected_script', 'script_result', 'temp_config', 'script_progress']
    for key in keys_to_remove:
        if key in st.session_state:
            del st.session_state[key]

# ============================================================================
# MAIN RENDER FUNCTION
# ============================================================================

def render_scripts_tab():
    """Render the Data Scripts tab"""
    
    # Dependency check banner
    if not SCRIPTS_AVAILABLE:
        st.error("""
        ⚠️ **Script Library Required**
        
        Please install required packages:
        ```bash
        pip install fuzzywuzzy python-Levenshtein phonetics
        pip install statsmodels scipy
        ```
        
        Some scripts will be limited without these dependencies.
        """)
        return
    
    # Check if dataset is loaded
    if st.session_state.get('dataset') is None:
        st.info("""
        ## 📊 Load Data First
        
        To use data scripts, please:
        1. Upload a dataset using the upload section
        2. Or load sample data from the main page
        
        **No data currently loaded.**
        """)
        
        # Quick upload button
        if st.button("📤 Go to Upload Page", type="primary", use_container_width=True):
            # Reset to trigger upload view
            from app import SessionStateManager
            SessionStateManager.reset_analysis(preserve_filters=False)
            st.rerun()
        
        return
    
    df = st.session_state.dataset
    
    # Check for empty dataset
    if df is None or df.empty:
        st.warning("""
        ## 📭 Dataset is Empty
        
        Please load a valid dataset with data to use scripts.
        """)
        return
    
    # Dataset summary
    _render_dataset_summary(df)
    
    # Dependency status
    missing_deps = []
    if not FUZZY_AVAILABLE:
        missing_deps.append("fuzzywuzzy")
    if not STATSMODELS_AVAILABLE:
        missing_deps.append("statsmodels")
    if not SCIPY_AVAILABLE:
        missing_deps.append("scipy")
    
    if missing_deps:
        with st.expander("⚠️ Missing Dependencies", expanded=False):
            st.caption(f"Some scripts require additional packages:")
            for dep in missing_deps:
                if dep == "fuzzywuzzy":
                    st.code("pip install fuzzywuzzy python-Levenshtein")
                elif dep == "statsmodels":
                    st.code("pip install statsmodels")
                elif dep == "scipy":
                    st.code("pip install scipy")
    
    # Main content based on state
    if 'selected_script' not in st.session_state:
        _render_script_library(df)
    else:
        _render_script_execution(df)

def _render_script_library(df: pd.DataFrame):
    """Render the main script library view"""
    
    dataset_analysis = _analyze_dataset(df)
    st.markdown("#### Available Scripts")
    st.caption("##### Select a category to view scripts")
    
    # Category tabs
    if not SCRIPTS:
        st.warning("No scripts available. Check dependencies and restart the app.")
        return
    
    # Filter out empty categories
    active_categories = {k: v for k, v in SCRIPTS.items() if v}
    if not active_categories:
        st.warning("No active script categories available.")
        return
    
    category_tabs = st.tabs(list(active_categories.keys()))
    
    for idx, (category_name, category_scripts) in enumerate(active_categories.items()):
        with category_tabs[idx]:
            # Create columns for script cards
            cols = st.columns(2)
            
            for script_idx, script in enumerate(category_scripts):
                col = cols[script_idx % 2]
                with col:
                    _render_script_card(script, dataset_analysis, df, col)
    
    # Quick recommendations
    _render_quick_recommendations(dataset_analysis, df)

def _render_script_execution(df: pd.DataFrame):
    """Render script execution view"""
    
    script = st.session_state.selected_script
    
    # Header with back button
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("← Back", use_container_width=True):
            cleanup_script_state()
            st.rerun()
    
    with col2:
        st.markdown(f"### {script['icon']} {script['name']}")
        st.caption(script['description'])
    
    # How it works explanation - NOW SCRIPT-SPECIFIC
    with st.expander("📖 How This Script Works", expanded=False):
        st.markdown(script.get('how_it_works', """
        **Process Overview:**
        1. **Analyze** your data to understand patterns and structure
        2. **Apply** intelligent transformations based on the analysis
        3. **Return** cleaned data along with a detailed report
        
        **Expected Outputs:**
        - Cleaned/transformed dataset
        - Detailed analysis report
        
        **Data Safety:** Your original data is never modified until you click "Apply to Dataset"
        
        **Performance:** For large datasets (>10k rows), consider filtering first
        """))
    
    # Configuration
    config = _render_script_configuration(script, df)
    
    # Execution
    if config is not None:
        with st.spinner(f"Running {script['name']}..."):
            result = _run_script_with_progress(
                df,
                script['function'],
                script['name'],
                **config
            )
            st.session_state.script_result = result
    
    # Results display
    if 'script_result' in st.session_state:
        _display_script_results(st.session_state.script_result, script, df)

def _render_quick_recommendations(analysis: Dict, df: pd.DataFrame):
    """Show quick recommendations based on data"""
    
    recommendations = []
    
    # Check for duplicates
    if analysis.get('duplicate_rows', 0) > 0:
        recommendations.append({
            "script": "Find Fuzzy Duplicates",
            "reason": f"{analysis['duplicate_rows']} exact duplicates found",
            "category": "Detective"
        })
    
    # Check for missing data
    missing_pct = analysis.get('missing_count', 0) / max(1, (analysis.get('row_count', 1) * analysis.get('column_count', 1)))
    if missing_pct > 0.05:
        recommendations.append({
            "script": "Handle Missing Data",
            "reason": f"{missing_pct:.1%} of data is missing",
            "category": "Fixer"
        })
    
    # Check for transaction data
    if (analysis.get('has_user_id') and analysis.get('has_dates') and analysis.get('has_prices')):
        recommendations.append({
            "script": "Segment Customers (RFM)",
            "reason": "Perfect for customer segmentation analysis",
            "category": "Business"
        })
    
    # Check for text issues
    if analysis.get('text_columns') and len(analysis.get('text_columns', [])) > 3:
        recommendations.append({
            "script": "Normalize Text",
            "reason": f"{len(analysis['text_columns'])} text columns could be standardized",
            "category": "Cleanup"
        })
    
    if recommendations:
        st.markdown("---")
        with st.expander("💡 Suggested Scripts", expanded=False):
            st.markdown("**Based on your data, consider:**")
            for rec in recommendations[:3]:
                st.markdown(f"- **{rec['script']}**: {rec['reason']}")
            
            if len(recommendations) > 3:
                st.caption(f"... and {len(recommendations) - 3} more recommendations")

# ============================================================================
# EXPORT
# ============================================================================

__all__ = ["render_scripts_tab"]