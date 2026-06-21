# data_operations.py
"""
Data Operations Module - Professional Edition
Clean, transform, and enhance your datasets with powerful operations
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import List, Tuple, Optional, Dict, Any, Callable
import re
from datetime import datetime, timedelta
from copy import deepcopy
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# PREVIEW SETTINGS
# ============================================================================
PREVIEW_ROW_COUNT = 10

# ============================================================================
# PROFESSIONAL UI COMPONENTS
# ============================================================================

def _render_section_header(title: str, description: str = ""):
    """Render a clean section header"""
    st.markdown(f"""
    <div style="margin-bottom: .5rem;">
        <h4>
            {title}
        </h4>
        <h6>
            {description}
        </h6>
    </div>
    """, unsafe_allow_html=True)

def _render_info_box(message: str, type: str = "info"):
    """Render a styled information box"""
    colors = {
        "info": ("#2196F3", "ℹ️"),
        "success": ("#4CAF50", "✅"),
        "warning": ("#FF9800", "⚠️"),
        "error": ("#F44336", "❌")
    }
    
    color, icon = colors.get(type, ("#2196F3", "ℹ️"))
    
    st.markdown(f"""
    <div style="background-color: {color}10; border-left: 4px solid {color}; 
                padding: 0.75rem; margin: 1rem 0; border-radius: 4px;">
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <span style="font-size: 1.1rem;">{icon}</span>
            <span style="font-size: 0.95rem;">{message}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def _render_metric_card(label: str, value: str, delta: str = "", 
                       delta_color: str = "normal"):
    """Render a clean metric card"""
    delta_color_map = {
        "normal": "#4CAF50",
        "inverse": "#F44336",
        "off": "#666"
    }
    
    delta_color_hex = delta_color_map.get(delta_color, delta_color)
    delta_html = ""
    
    if delta:
        if delta.startswith(("+", "-")):
            delta_html = f'<span style="color: {delta_color_hex}; font-size: 0.9rem;">{delta}</span>'
        else:
            delta_html = f'<span style="color: #666; font-size: 0.9rem;">{delta}</span>'
    
    st.markdown(f"""
    <div style="background: white; padding: 1rem; border-radius: 8px; 
                border: 1px solid #E0E0E0; text-align: center;">
        <div style="color: #666; font-size: 0.9rem; margin-bottom: 0.25rem;">
            {label}
        </div>
        <div style="font-size: 1.5rem; font-weight: 600; color: #333;">
            {value}
        </div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

def _render_preview_table(df: pd.DataFrame, title: str = "Preview"):
    """Render a clean preview table"""
    if df is None or df.empty:
        return
    
    max_rows = min(len(df), PREVIEW_ROW_COUNT)
    st.markdown(f"**{title}** (showing {max_rows} of {len(df):,} rows)")
    
    styled_df = df.head(max_rows).style.set_properties(**{
        'font-size': '0.9rem',
        'border': '1px solid #E0E0E0',
        'padding': '4px 8px'
    }).set_table_styles([{
        'selector': 'thead th',
        'props': [('background-color', '#F8F9FA'),
                 ('font-weight', 'bold'),
                 ('border-bottom', '2px solid #1E88E5')]
    }])
    
    st.dataframe(styled_df, use_container_width=True)

# ============================================================================
# FORMULA ENGINE WITH ADVANCED EXAMPLES - FIXED VERSION
# ============================================================================

class FormulaEngine:
    """Secure formula evaluation with advanced business calculations"""
    
    @staticmethod
    def validate_formula(formula: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate formula syntax and security using ACTUAL dataset"""
        issues = []
        warnings = []
        
        if not formula.strip():
            return {"valid": False, "issues": ["Formula is empty"], "warnings": warnings}
        
        # Security checks
        dangerous_patterns = [
            ("__", "double underscore"),
            ("import ", "import statement"),
            ("exec(", "exec function"),
            ("eval(", "eval function"),
            ("open(", "file operation"),
            ("os.", "os module"),
            ("subprocess", "subprocess"),
            ("system(", "system call")
        ]
        
        for pattern, desc in dangerous_patterns:
            if pattern in formula.lower():
                issues.append(f"Security issue: {desc}")
        
        # Check for column references (df['col'] or df["col"])
        col_pattern = r'df\[["\']([^"\']+)["\']\]'
        referenced_cols = re.findall(col_pattern, formula)
        
        # Check if referenced columns exist
        for col in referenced_cols:
            if col not in df.columns:
                issues.append(f"Column '{col}' not found in dataset")
        
        # Check for .dt accessor on non-datetime columns
        dt_pattern = r'df\[["\']([^"\']+)["\']\]\.dt\.'
        dt_cols = re.findall(dt_pattern, formula)
        for col in dt_cols:
            if col in df.columns and not pd.api.types.is_datetime64_any_dtype(df[col]):
                issues.append(f"Column '{col}' used with .dt accessor is not a datetime column (type: {df[col].dtype})")
        
        # Check for .str accessor on non-string columns
        str_pattern = r'df\[["\']([^"\']+)["\']\]\.str\.'
        str_cols = re.findall(str_pattern, formula)
        for col in str_cols:
            if col in df.columns and not pd.api.types.is_string_dtype(df[col]):
                warnings.append(f"Column '{col}' used with .str accessor may not be string (type: {df[col].dtype})")
        
        # Check for basic syntax issues without actually evaluating
        # We'll just check for common mistakes
        if '..' in formula:
            issues.append("Syntax error: Double dot (..) found")
        
        if formula.count('(') != formula.count(')'):
            issues.append("Syntax error: Mismatched parentheses")
        
        # If no critical issues, try a small evaluation test with a subset of data
        if len(issues) == 0:
            try:
                # Use a small subset of actual data (first 3 rows)
                test_df = df.head(3).copy()
                
                # Create safe environment for test
                safe_dict = FormulaEngine._create_safe_environment(test_df)
                
                # Test evaluation
                result = eval(formula, {"__builtins__": {}}, safe_dict)
                
                # Check if result makes sense
                if result is not None:
                    # For scalar operations, we expect a scalar
                    # For vector operations, we expect a Series/array of same length
                    if isinstance(result, (pd.Series, np.ndarray, list)):
                        if len(result) != len(test_df):
                            warnings.append(f"Result length ({len(result)}) doesn't match dataset length ({len(test_df)})")
                
            except AttributeError as e:
                if "dt" in str(e):
                    # We already checked for this above, but double-check
                    issues.append(f"Date accessor error: {str(e)[:100]}")
                else:
                    issues.append(f"Attribute error: {str(e)[:100]}")
            except Exception as e:
                # Don't fail validation on complex operations that might need full data
                # Just log as warning
                warnings.append(f"Evaluation note: {str(e)[:80]}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "referenced_columns": referenced_cols
        }
    
    @staticmethod
    def _create_safe_environment(df: pd.DataFrame) -> Dict:
        """Create safe evaluation environment"""
        return {
            'df': df,
            'np': np,
            'pd': pd,
            'abs': abs,
            'min': min,
            'max': max,
            'sum': sum,
            'round': round,
            'len': len,
            'sqrt': np.sqrt,
            'log': np.log,
            'exp': np.exp,
            'sin': np.sin,
            'cos': np.cos,
            'tan': np.tan,
            'mean': np.mean,
            'std': np.std,
            'var': np.var,
            'median': np.median,
            'where': np.where,
            'clip': np.clip,
            'percentile': np.percentile,
            'log10': np.log10,
            'cumsum': lambda x: pd.Series(x).cumsum(),
            'diff': lambda x: pd.Series(x).diff(),
            'shift': lambda x, n=1: pd.Series(x).shift(n),
            'pct_change': lambda x: pd.Series(x).pct_change(),
            'rank': lambda x, **kwargs: pd.Series(x).rank(**kwargs),
            'quantile': lambda x, q: pd.Series(x).quantile(q),
            'isna': pd.isna,
            'notna': pd.notna,
            'any': any,
            'all': all,
            'sum': sum,
            'max': max,
            'min': min
        }
    
    @staticmethod
    def evaluate_formula(df: pd.DataFrame, formula: str, new_column: str) -> pd.DataFrame:
        """Evaluate formula with proper error handling"""
        try:
            result_df = df.copy()
            
            # Create safe environment
            safe_dict = FormulaEngine._create_safe_environment(result_df)
            
            # Evaluate
            result = eval(formula, {"__builtins__": {}}, safe_dict)
            
            # Handle different result types
            if isinstance(result, (pd.Series, np.ndarray, list)):
                if len(result) == len(result_df):
                    result_df[new_column] = result
                elif len(result) == 1:
                    # Broadcast scalar
                    result_df[new_column] = result[0]
                else:
                    raise ValueError(
                        f"Result length ({len(result)}) doesn't match dataset length ({len(result_df)})"
                    )
            elif pd.api.types.is_scalar(result):
                # Broadcast scalar to all rows
                result_df[new_column] = result
            else:
                # Try to convert
                try:
                    result_series = pd.Series(result)
                    if len(result_series) == len(result_df):
                        result_df[new_column] = result_series
                    else:
                        raise ValueError(f"Cannot convert result of type {type(result)}")
                except:
                    raise ValueError(f"Cannot assign result of type {type(result)}")
            
            return result_df
            
        except Exception as e:
            # Provide more helpful error messages
            error_msg = str(e)
            
            if "Can only use .dt accessor" in error_msg:
                # Find which column caused the issue
                for col in df.columns:
                    if f"df['{col}']" in formula and '.dt.' in formula:
                        if not pd.api.types.is_datetime64_any_dtype(df[col]):
                            raise ValueError(
                                f"Column '{col}' used with .dt accessor is not datetime. "
                                f"Convert it first using Data Types tab."
                            )
                raise ValueError(f"Date accessor error: {error_msg[:100]}")
            
            elif "Can only use .str accessor" in error_msg:
                for col in df.columns:
                    if f"df['{col}']" in formula and '.str.' in formula:
                        if not pd.api.types.is_string_dtype(df[col]):
                            raise ValueError(
                                f"Column '{col}' used with .str accessor is not string. "
                                f"Convert it first using Data Types tab."
                            )
                raise ValueError(f"String accessor error: {error_msg[:100]}")
            
            elif "'numpy' is not defined" in error_msg or "'np' is not defined" in error_msg:
                raise ValueError(
                    "Use np.function() for numpy functions. Example: np.sqrt(df['value'])"
                )
            
            elif "is not defined" in error_msg:
                # Try to extract undefined name
                match = re.search(r"'([^']+)'", error_msg)
                if match:
                    undefined = match.group(1)
                    if undefined in df.columns:
                        raise ValueError(
                            f"Column '{undefined}' must be referenced as df['{undefined}']"
                        )
                    else:
                        raise ValueError(f"'{undefined}' is not defined. Check spelling or use np.{undefined}()")
                else:
                    raise ValueError(f"Reference error: {error_msg[:100]}")
            
            else:
                raise ValueError(f"Evaluation failed: {error_msg[:150]}")
        
    @staticmethod
    def get_advanced_examples() -> Dict[str, str]:
        """Get advanced formula examples with detailed, actionable explanations"""
        return {
            "📈 Time Series Analysis": """
# ──────────────────────────────────────────────────────────────
# 3-Period Moving Average - Smooths fluctuations for trend analysis
# Use: Identifying underlying trends in noisy data
df['sales'].rolling(window=3, min_periods=1).mean()

# Exponential Moving Average - Weights recent data more heavily
# Use: Technical analysis, responsive trend following
df['sales'].ewm(span=7, adjust=False).mean()

# Year-over-Year Growth - Compare performance to same period last year
# Use: Eliminates seasonality, shows true business growth
((df['current_sales'] - df['last_year_sales']) / df['last_year_sales']) * 100

# Month-over-Month Change - Quick performance indicator
# Use: Monthly performance tracking, KPI reporting
df['sales'] - df['sales'].shift(1)

# Cumulative Sum - Running total over time
# Use: Track YTD totals, progressive metrics
df['sales'].cumsum()

# Percentage Contribution - Each row's share of total
# Use: Pareto analysis, contribution analysis
(df['sales'] / df['sales'].sum()) * 100

# Daily Returns - Percentage change day-to-day
# Use: Stock analysis, volatility measurement
df['price'].pct_change() * 100

# 7-Day Rolling Sum - Weekly aggregates with daily updates
# Use: Weekly reporting with daily frequency
df['sales'].rolling(window=7, min_periods=1).sum()

# Seasonality Index - Compare to historical average for same period
# Use: Identify seasonal patterns, adjust forecasts
(df['current_sales'] / df.groupby(df['date'].dt.month)['last_year_sales'].transform('mean') - 1) * 100

# Days Since Last Activity - Measure customer/product engagement
# Use: Customer retention, inventory aging
(pd.Timestamp.now() - df['last_purchase_date']).dt.days
    """,
            
            "💰 Financial & Business Metrics": """
# ──────────────────────────────────────────────────────────────
# Profit Margin - Core profitability metric
# Use: Product profitability, business health
((df['revenue'] - df['cost']) / df['revenue'] * 100).round(2)

# ROI - Return on investment percentage
# Use: Investment decisions, project evaluation
((df['ending_value'] - df['investment']) / df['investment'] * 100).round(2)

# CAGR - Annualized growth rate over multiple years
# Use: Compare investments with different timeframes
((df['ending_value'] / df['starting_value']) ** (1 / df['years']) - 1) * 100

# Markup - Price increase over cost
# Use: Pricing strategy, margin management
((df['selling_price'] - df['cost']) / df['cost'] * 100).round(2)

# Discount Percentage - Price reduction calculation
# Use: Sales promotions, clearance pricing
((df['original_price'] - df['sale_price']) / df['original_price'] * 100).round(2)

# Customer Lifetime Value - Total expected revenue per customer
# Use: Customer segmentation, marketing budget allocation
df['avg_order_value'] * df['purchase_frequency'] * df['customer_lifespan']

# Customer Acquisition Cost - Cost to acquire each new customer
# Use: Marketing ROI, budget optimization
df['marketing_spend'] / df['new_customers'].replace(0, np.nan)

# LTV:CAC Ratio - Efficiency of customer acquisition
# Use: Business sustainability, investor metrics
(df['avg_order_value'] * df['purchase_frequency'] * df['customer_lifespan']) / (df['marketing_spend'] / df['new_customers'].replace(0, np.nan))

# Unit Contribution Margin - Profit per unit sold
# Use: Break-even analysis, product mix decisions
df['price'] - df['variable_cost']

# Break-Even Units - Quantity needed to cover fixed costs
# Use: Business planning, target setting
df['fixed_costs'] / (df['price'] - df['variable_cost'])

# Conversion Rate - Percentage of visitors who convert
# Use: Website optimization, funnel analysis
(df['conversions'] / df['visitors'] * 100).fillna(0).round(2)

# Average Order Value - Revenue per transaction
# Use: Sales strategy, upselling opportunities
df['total_revenue'] / df['number_of_orders']
    """,
            
            "📊 Statistical & Data Science": """
# ──────────────────────────────────────────────────────────────
# Z-Score - Standardizes values for comparison across datasets
# Use: Anomaly detection, data normalization for ML models
(df['value'] - df['value'].mean()) / df['value'].std()

# Min-Max Normalization - Scales values to 0-1 range
# Use: Feature scaling for neural networks, distance-based algorithms
(df['value'] - df['value'].min()) / (df['value'].max() - df['value'].min())

# Percentile Rank - Position within distribution
# Use: Performance ranking, competitive analysis
df['value'].rank(pct=True) * 100

# Outlier Flag - Identifies extreme values
# Use: Data quality, fraud detection, anomaly investigation
abs(df['value'] - df['value'].mean()) > (3 * df['value'].std())

# Robust Z-Score - Uses median and MAD for outlier-resistant scaling
# Use: Statistics with outlier-prone data
(df['value'] - df['value'].median()) / (df['value'].mad() if df['value'].mad() != 0 else 1)

# Log Transformation - Reduces skewness, stabilizes variance
# Use: Financial data, size measures, right-skewed distributions
np.log(df['value'] + 1)

# Square Root Transformation - Mild variance stabilization
# Use: Count data, Poisson-like distributions
np.sqrt(df['value'])

# Top Performer Flag - Identifies best 20%
# Use: Segmentation, incentive programs
df['value'] >= df['value'].quantile(0.8)

# Bottom Performer Flag - Identifies lowest 10%
# Use: Improvement targeting, risk identification
df['value'] <= df['value'].quantile(0.1)

# Percent Change from Baseline - Relative performance metric
# Use: A/B testing, experiment results
((df['value'] - df['baseline']) / df['baseline'] * 100).round(2)

# Rolling Volatility - Measures variability over time
# Use: Risk assessment, quality control
df['price'].rolling(window=20, min_periods=1).std()
    """,
            
            "📅 Date & Time Intelligence": """
# ──────────────────────────────────────────────────────────────
# Age Calculation - Precise age in years (accounts for leap years)
# Use: Demographics, eligibility checks
(pd.Timestamp.now() - df['birth_date']).dt.days / 365.25

# Days Between Dates - Simple duration calculation
# Use: Service level agreements, project timelines
(df['end_date'] - df['start_date']).dt.days

# Business Days - Excludes weekends for work-related calculations
# Use: Project planning, SLA calculations
np.busday_count(df['start_date'].dt.date, df['end_date'].dt.date)

# Year-Month Format - Standardized period identifier
# Use: Time-based grouping, reporting periods
df['date'].dt.strftime('%Y-%m')

# Day of Week - Numeric representation (Monday=0)
# Use: Weekend vs weekday analysis, staffing patterns
df['date'].dt.weekday

# Weekend Flag - Quick indicator for non-business days
# Use: Operations planning, anomaly detection
df['date'].dt.weekday >= 5

# Days Until Month End - Remaining time in current period
# Use: Sales targets, monthly closing processes
(df['date'].dt.days_in_month - df['date'].dt.day)

# Calendar Quarter - Standard fiscal periods
# Use: Financial reporting, quarterly reviews
df['date'].dt.quarter

# Fiscal Quarter - Custom fiscal calendar (April start)
# Use: Companies with non-calendar fiscal years
((df['date'].dt.month - 4) % 12 // 3) + 1

# Hours Worked - Decimal hours for payroll/time tracking
# Use: Timesheet calculations, labor cost analysis
(df['end_time'] - df['start_time']).dt.total_seconds() / 3600

# Days Since Event - Recency scoring
# Use: Customer engagement, equipment maintenance
(pd.Timestamp.now() - df['event_date']).dt.days

# Week Number - ISO standard week numbering
# Use: International reporting, week-based planning
df['date'].dt.isocalendar().week

# Month End Flag - Identifies period boundaries
# Use: Month-end processing, reporting cycles
df['date'].dt.day == df['date'].dt.days_in_month
    """,
            
            "🔤 Text & String Manipulation": """
# ──────────────────────────────────────────────────────────────
# First Name Extraction - Parses full names
# Use: Personalization, name-based segmentation
df['full_name'].str.split().str[0]

# Email Domain Extraction - Extracts company/organization
# Use: Company analysis, B2B marketing
df['email'].str.split('@').str[-1]

# Phone Number Normalization - Standardizes format
# Use: Data cleaning, CRM standardization
df['phone'].str.replace(r'\\D', '', regex=True)

# Keyword Detection - Finds specific terms
# Use: Content analysis, customer support categorization
df['description'].str.contains('urgent', case=False, na=False)

# Word Count - Measures content length
# Use: SEO optimization, content analysis
df['text'].str.split().str.len()

# Number Extraction - Pulls numeric values from text
# Use: Data parsing, mixed-format cleanup
df['mixed_string'].str.extract(r'(\\d+)').astype(float)

# Title Case - Proper capitalization
# Use: Name formatting, professional documents
df['name'].str.title()

# Whitespace Cleanup - Removes extra spaces
# Use: Data quality, string matching preparation
df['text'].str.strip()

# Full Name Construction - Combines separate name fields
# Use: Report generation, formal communications
df['first_name'] + ' ' + df['last_name']

# Email Obfuscation - Privacy protection
# Use: Display without exposing full addresses
df['email'].apply(lambda x: x[:3] + '***' + x[x.find('@'):] if isinstance(x, str) else x)

# URL Domain Extraction - Website analysis
# Use: Web analytics, source tracking
df['url'].str.replace(r'https?://(www\\.)?([^/]+).*', r'\\2', regex=True)

# String Length Validation - Data quality check
# Use: Form validation, database constraints
df['text'].str.len()
    """,
            
            "🎯 Group & Aggregate Intelligence": """
# ──────────────────────────────────────────────────────────────
# Within-Group Percentage - Contribution to subgroup total
# Use: Market share within segments, departmental budgets
(df['value'] / df.groupby('category')['value'].transform('sum') * 100).round(2)

# Group Ranking - Position within each category
# Use: Salesperson rankings by region, product rankings by category
df.groupby('group')['value'].rank(ascending=False, method='dense')

# Deviation from Group Mean - Performance relative to peers
# Use: Competitive benchmarking, anomaly detection
df['value'] - df.groupby('category')['value'].transform('mean')

# Group Normalization - Scales within each subgroup
# Use: Fair comparisons across different-sized groups
(df['value'] - df.groupby('group')['value'].transform('min')) / (df.groupby('group')['value'].transform('max') - df.groupby('group')['value'].transform('min'))

# Cumulative Sum by Group - Running totals per category
# Use: YTD by department, progressive totals by product line
df.groupby('category')['sales'].cumsum()

# Sequential Index by Group - Numbering within categories
# Use: Order tracking, sequence analysis
df.groupby('group').cumcount() + 1

# Previous Value in Group - Lagged comparison
# Use: Time series within categories, sequential analysis
df.groupby('category')['value'].shift(1)

# Next Value in Group - Lead comparison
# Use: Forecasting within groups, forward-looking metrics
df.groupby('category')['value'].shift(-1)

# Group Percentage Change - Relative movement within categories
# Use: Trend analysis by segment
df.groupby('category')['value'].pct_change() * 100

# Group Average Column - Peer comparison baseline
# Use: Performance vs group average, standardization
df.groupby('group')['value'].transform('mean')

# Top N in Group - Flag best performers per category
# Use: Award qualifications, selective targeting
df.groupby('group')['value'].rank(ascending=False) <= 3
    """,
            
            "⚙️ Conditional Logic & Business Rules": """
# ──────────────────────────────────────────────────────────────
# Simple Condition - Binary classification
# Use: Pass/fail, yes/no decisions
np.where(df['score'] > 50, 'Pass', 'Fail')

# Multiple Conditions - Tiered classification
# Use: Grading systems, risk categories, priority levels
np.select(
    [df['score'] >= 90, df['score'] >= 80, df['score'] >= 70],
    ['A', 'B', 'C'],
    default='F'
)

# Any Condition Met - Logical OR across columns
# Use: Risk flags, multi-criteria eligibility
(df[['condition1', 'condition2', 'condition3']] == True).any(axis=1)

# All Conditions Met - Logical AND across columns
# Use: Quality gates, compliance checks
(df[['test1', 'test2', 'test3']] == 'Pass').all(axis=1)

# Recent Activity Flag - Time-based filtering
# Use: Active user identification, retention campaigns
(pd.Timestamp.now() - df['last_active']).dt.days <= 30

# Range Check - Value within acceptable bounds
# Use: Data validation, quality control
df['value'].between(df['min_range'], df['max_range'])

# Weighted Score - Multi-factor evaluation
# Use: Priority scoring, risk assessment, performance metrics
(df['metric1'] * 0.4 + df['metric2'] * 0.3 + df['metric3'] * 0.3).round(2)

# Urgency Score - Time-sensitive prioritization
# Use: Ticket triage, workflow management
(df['days_overdue'] * 0.5 + df['severity_score'] * 0.3 + df['customer_impact'] * 0.2).round(2)

# Tier Assignment - Binned categorization
# Use: Customer segmentation, pricing tiers
pd.cut(df['score'], bins=[0, 60, 80, 90, 100], labels=['D', 'C', 'B', 'A'])

# Boolean Inversion - Reverse logic
# Use: Eligibility checks, exclusion criteria
~df['boolean_column']

# Condition Count - Sum of true conditions
# Use: Checklist completion, multi-criteria scoring
(df['status'] == 'Completed').astype(int)
    """,
            
            "📐 Mathematical & Calculation Essentials": """
# ──────────────────────────────────────────────────────────────
# Percentage Change - Relative difference calculation
# Use: Performance tracking, growth measurement
((df['new_value'] - df['old_value']) / df['old_value'] * 100).fillna(0).round(2)

# Ratio Calculation - Relationship between two metrics
# Use: Financial ratios, operational metrics
df['numerator'] / df['denominator'].replace(0, np.nan)

# Weighted Average - Account for different weights
# Use: Course grades, composite indices
(df['value'] * df['weight']).sum() / df['weight'].sum()

# Geometric Mean - Appropriate for rates of change
# Use: Average growth rates, investment returns
np.exp(np.log(df['growth_rate'] + 1).mean()) - 1

# Compound Interest - Future value calculation
# Use: Investment planning, loan calculations
df['principal'] * (1 + df['annual_rate']/df['compounds_per_year']) ** (df['compounds_per_year'] * df['years'])

# Euclidean Distance - Straight-line distance
# Use: Location analysis, clustering algorithms
np.sqrt((df['x2'] - df['x1'])**2 + (df['y2'] - df['y1'])**2)

# Round to Multiple - Nearest 5, 10, etc.
# Use: Pricing psychology, discrete measurement
np.round(df['value'] / 5) * 5

# Ceiling to Multiple - Round up to nearest increment
# Use: Packaging requirements, resource allocation
np.ceil(df['value'] / 10) * 10

# Floor to Multiple - Round down to nearest increment
# Use: Inventory management, conservative estimates
np.floor(df['value'] / 100) * 100

# Absolute Difference - Magnitude of difference
# Use: Error measurement, variance analysis
abs(df['value1'] - df['value2'])

# Sign Function - Direction indicator
# Use: Change direction, positive/negative classification
np.sign(df['value'])

# Logit Transformation - For probability analysis
# Use: Logistic regression features, odds ratio calculations
np.log(df['probability'] / (1 - df['probability']))
    """,
            
            "📈 Advanced Analytics & Trading Indicators": """
# ──────────────────────────────────────────────────────────────
# Exponentially Weighted Volatility - Time-sensitive risk measure
# Use: Options pricing, risk management
df['price'].ewm(span=20, adjust=False).std()

# Sharpe Ratio - Risk-adjusted return (annualized)
# Use: Investment performance comparison
(df['returns'].mean() / df['returns'].std()) * np.sqrt(252)

# Beta Coefficient - Stock vs market sensitivity
# Use: Portfolio risk assessment, CAPM calculations
df['stock_returns'].rolling(window=60).cov(df['market_returns']) / df['market_returns'].rolling(window=60).var()

# MACD - Moving Average Convergence Divergence
# Use: Technical analysis, trend reversal signals
df['price'].ewm(span=12).mean() - df['price'].ewm(span=26).mean()

# RSI - Relative Strength Index (momentum oscillator)
# Use: Overbought/oversold signals, momentum trading
delta = df['price'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
100 - (100 / (1 + rs))

# Bollinger Bands Position - Relative price position
# Use: Volatility-based trading, mean reversion strategies
(df['price'] - df['price'].rolling(20).mean()) / (df['price'].rolling(20).std() * 2)

# Purchase Frequency - Time between transactions
# Use: Customer behavior analysis, loyalty programs
df.groupby('customer_id')['purchase_date'].diff().dt.days

# Recency Score - Inverse relationship to time since last activity
# Use: RFM analysis, engagement scoring
1 / ((pd.Timestamp.now() - df['last_purchase']).dt.days + 1)

# RFM Score - Composite customer value metric
# Use: Customer segmentation, targeted marketing
(df['recency_score'] * 0.4 + df['frequency_score'] * 0.3 + df['monetary_score'] * 0.3).round(2)

# Churn Risk Score - Probability of customer leaving
# Use: Retention campaigns, proactive intervention
(df['days_inactive'] * 0.5 + df['complaint_count'] * 0.3 + (1 - df['satisfaction_score']) * 0.2).round(2)

# Cohort Retention - Percentage remaining over time
# Use: Product adoption analysis, subscription business metrics
(df['active_in_month'] / df['cohort_size']) * 100
    """,
            
            "🧹 Data Cleaning & Validation": """
# ──────────────────────────────────────────────────────────────
# Missing Value Imputation - Fill gaps with median (robust to outliers)
# Use: Data preparation for ML models, statistical analysis
df['value'].fillna(df['value'].median())

# Winsorization - Cap extreme values at specified percentiles
# Use: Outlier treatment, data normalization
np.clip(df['value'], df['value'].quantile(0.05), df['value'].quantile(0.95))

# Standardization - Z-score for multiple columns
# Use: Feature scaling, comparison across different units
((df['value'] - df['value'].mean()) / df['value'].std()).round(3)

# Age Group Creation - Demographic categorization
# Use: Market segmentation, targeted messaging
pd.cut(df['age'], bins=[0, 18, 35, 50, 65, 100], labels=['<18', '18-35', '36-50', '51-65', '65+'])

# Time of Day Categories - Temporal segmentation
# Use: Operational planning, customer behavior patterns
pd.cut(df['hour'], bins=[0, 6, 12, 18, 24], labels=['Night', 'Morning', 'Afternoon', 'Evening'], right=False)

# Data Validation Flag - Identifies invalid entries
# Use: Data quality monitoring, input validation
(df['value'] < df['min_valid']) | (df['value'] > df['max_valid'])

# Duplicate Detection - Flags duplicate records
# Use: Data deduplication, record consolidation
~df.duplicated(subset=['id', 'date'], keep='first')

# Boolean Encoding - Convert text to numeric flags
# Use: Machine learning feature engineering
df['yes_no_column'].map({'Yes': 1, 'No': 0}).fillna(0)

# One-Hot Encoding - Single category expansion
# Use: Categorical variable preparation for algorithms
(df['category'] == 'A').astype(int)

# Max Normalization - Scale relative to maximum
# Use: Index creation, relative performance metrics
df['value'] / df['value'].max()

# Temporal Consistency Check - Validates time sequences
# Use: Data integrity, logical validation
df['end_date'] >= df['start_date']

# Data Type Consistency - Ensures consistent formatting
# Use: Data pipeline quality, integration checks
df['date'].dt.strftime('%Y-%m-%d') == df['date_string']
    """
        }
    
# ============================================================================
# OPERATIONS ENGINE
# ============================================================================

class OperationsEngine:
    """Core operations engine with history tracking"""
    
    _history = []
    _max_history = 10
    
    @classmethod
    def log_operation(cls, name: str, details: Dict, 
                     before: Tuple[int, int], after: Tuple[int, int]):
        """Log operation to history"""
        log_entry = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "operation": name,
            "details": details,
            "before": {"rows": before[0], "columns": before[1]},
            "after": {"rows": after[0], "columns": after[1]},
            "impact": {
                "rows": after[0] - before[0],
                "columns": after[1] - before[1]
            }
        }
        
        cls._history.append(log_entry)
        
        # Keep history size limited
        if len(cls._history) > cls._max_history:
            cls._history.pop(0)
    
    @classmethod
    def get_history(cls) -> List[Dict]:
        """Get operation history"""
        return cls._history
    
    @classmethod
    def clear_history(cls):
        """Clear history"""
        cls._history = []
    
    @staticmethod
    def execute(operation_func: Callable, name: str, *args, **kwargs) -> Dict[str, Any]:
        """Execute operation with error handling"""
        try:
            df = st.session_state.get('dataset')
            
            if df is None or df.empty:
                return {"success": False, "message": "No dataset available", 
                        "df": None, "error": "Dataset not loaded"}
            
            before_shape = df.shape
            details = kwargs.pop('operation_details', {})
            
            # Execute
            result = operation_func(df, *args, **kwargs)
            
            if result is None:
                return {"success": False, "message": "Operation produced no result", 
                        "df": None, "error": "Result is None"}
            
            if not isinstance(result, pd.DataFrame):
                return {"success": False, "message": "Invalid result type", 
                        "df": None, "error": f"Expected DataFrame, got {type(result)}"}
            
            if result.empty:
                return {"success": False, "message": "Operation produced empty dataset", 
                        "df": None, "error": "Result is empty"}
            
            # Check for actual changes
            if df.shape == result.shape:
                try:
                    if df.equals(result):
                        return {"success": True, "message": "No changes made", 
                                "df": None, "error": None}
                except:
                    pass
            
            # Log and return success
            after_shape = result.shape
            OperationsEngine.log_operation(name, details, before_shape, after_shape)
            
            return {
                "success": True,
                "message": f"✅ {name} completed",
                "df": result,
                "error": None,
                "metrics": {
                    "before": before_shape,
                    "after": after_shape
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ {name} failed",
                "df": None,
                "error": str(e)[:150]
            }
    
    @staticmethod
    def apply_to_dataset(new_df: pd.DataFrame, operation_name: str) -> bool:
        """Apply operation result to dataset"""
        try:
            if new_df is None or new_df.empty:
                return False
            
            # Update session state
            st.session_state.dataset = new_df.copy()
            st.session_state.original_dataset = new_df.copy()
            st.session_state.base_dataset = new_df.copy()
            
            # Update metadata
            if 'dataset_metadata' not in st.session_state:
                st.session_state.dataset_metadata = {}
            
            st.session_state.dataset_metadata.update({
                'last_operation': operation_name,
                'last_operation_time': datetime.now().isoformat(),
                'shape': new_df.shape
            })
            
            # Reset analysis state
            for key in ['current_chart', 'chart_history', 'chat_history']:
                if key in st.session_state:
                    st.session_state[key] = None if key == 'current_chart' else []
            
            return True
            
        except Exception as e:
            st.error(f"Failed to update dataset: {str(e)[:100]}")
            return False

# ============================================================================
# OPERATION COMPONENTS - ORGANIZED
# ============================================================================

def _render_duplicates_ui(df: pd.DataFrame) -> None:
    """Remove duplicate rows"""
    _render_section_header(
        "Remove Duplicate Rows",
        "Identify and remove duplicate entries from your dataset"
    )
    
    if df.empty:
        _render_info_box("Dataset is empty", "info")
        return
    
    duplicates = df.duplicated().sum()
    
    if duplicates == 0:
        _render_info_box("✅ No duplicate rows found", "success")
        return
    
    # Configuration
    with st.container():
        col1, col2 = st.columns(2)
        
        with col1:
            keep = st.selectbox(
                "Keep which occurrence?",
                ["First (recommended)", "Last", "None (remove all duplicates)"],
                help="First: Keep first occurrence of duplicates\nLast: Keep last occurrence\nNone: Remove all duplicates"
            )
            keep_map = {"First (recommended)": "first", "Last": "last", "None (remove all duplicates)": False}
        
        with col2:
            all_cols = st.checkbox("Check all columns", value=True, 
                                  help="Uncheck to select specific columns for comparison")
            if not all_cols:
                subset = st.multiselect("Columns to check:", df.columns.tolist())
            else:
                subset = None
    
    # Impact analysis
    st.markdown("### 📊 Impact Analysis")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Rows", f"{len(df):,}")
    with col2:
        st.metric("Duplicates", f"{duplicates:,}")
    with col3:
        remaining = len(df) - duplicates if keep == "None (remove all duplicates)" else len(df) - duplicates
        st.metric("After Operation", f"{remaining:,}")
    
    # Preview
    if duplicates > 0:
        with st.expander("🔍 Preview Duplicates"):
            dup_df = df[df.duplicated(subset=subset, keep=False)].head(10)
            st.dataframe(dup_df, use_container_width=True)
    
    # Action
    st.markdown("---")
    
    if st.button("✅ Remove Duplicates", type="primary", use_container_width=True):
        def operation(d, subset=None, keep='first'):
            return d.drop_duplicates(subset=subset, keep=keep)
        
        result = OperationsEngine.execute(
            operation, "Remove Duplicates",
            subset=subset, keep=keep_map[keep],
            operation_details={"subset": subset, "keep": keep}
        )
        
        if result["success"] and result["df"] is not None:
            if OperationsEngine.apply_to_dataset(result["df"], "Remove Duplicates"):
                st.success(result["message"])
                st.rerun()
        else:
            st.error(result.get("message", "Operation failed"))

def _render_columns_ui(df: pd.DataFrame) -> None:
    """Manage columns (drop/rename)"""
    _render_section_header(
        "Manage Columns",
        "Drop unnecessary columns or rename them for clarity"
    )
    
    if df.empty:
        _render_info_box("Dataset is empty", "info")
        return
    
    # Tab interface for drop vs rename
    tab1, tab2 = st.tabs(["🗑️ Drop Columns", "🏷️ Rename Columns"])
    
    with tab1:
        # Drop columns
        st.markdown("#### Select columns to remove:")
        
        columns_to_drop = st.multiselect(
            "Select columns to drop",
            df.columns.tolist(),
            help="Selected columns will be permanently removed"
        )
        
        if columns_to_drop:
            # Impact preview
            remaining = [c for c in df.columns if c not in columns_to_drop]
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Current Columns", len(df.columns))
            with col2:
                st.metric("After Removal", len(remaining))
            
            st.markdown("**Columns to be removed:**")
            for col in columns_to_drop[:5]:
                st.caption(f"• {col}")
            if len(columns_to_drop) > 5:
                st.caption(f"... and {len(columns_to_drop) - 5} more")
            
            if st.button("🗑️ Drop Selected Columns", type="primary", use_container_width=True):
                def operation(d, columns):
                    return d.drop(columns=columns, errors='ignore')
                
                result = OperationsEngine.execute(
                    operation, "Drop Columns",
                    columns=columns_to_drop,
                    operation_details={"columns": columns_to_drop}
                )
                
                if result["success"] and result["df"] is not None:
                    if OperationsEngine.apply_to_dataset(result["df"], "Drop Columns"):
                        st.success(f"Removed {len(columns_to_drop)} columns")
                        st.rerun()
    
    with tab2:
        # Rename columns
        st.markdown("#### Rename columns:")
        
        rename_data = []
        for col in df.columns:
            rename_data.append({
                "Current": col,
                "New Name": col,
                "Type": str(df[col].dtype)
            })
        
        edited = st.data_editor(
            pd.DataFrame(rename_data),
            column_config={
                "Current": st.column_config.TextColumn(disabled=True),
                "New Name": st.column_config.TextColumn(),
                "Type": st.column_config.TextColumn(disabled=True)
            },
            hide_index=True,
            use_container_width=True,
            key="rename_editor"
        )
        
        # Collect renames
        renames = {}
        for _, row in edited.iterrows():
            old = row["Current"]
            new = str(row["New Name"]).strip()
            if old != new and new:
                renames[old] = new
        
        if renames:
            st.markdown("**Changes to apply:**")
            for old, new in list(renames.items())[:5]:
                st.caption(f"• {old} → {new}")
            
            if st.button("🏷️ Apply Renames", type="primary", use_container_width=True):
                def operation(d, renames):
                    return d.rename(columns=renames)
                
                result = OperationsEngine.execute(
                    operation, "Rename Columns",
                    renames=renames,
                    operation_details={"renames": renames}
                )
                
                if result["success"] and result["df"] is not None:
                    if OperationsEngine.apply_to_dataset(result["df"], "Rename Columns"):
                        st.success(f"Renamed {len(renames)} columns")
                        st.rerun()

def _render_missing_ui(df: pd.DataFrame) -> None:
    """Handle missing values - FIXED VERSION"""
    _render_section_header(
        "Handle Missing Values",
        "Detect and treat missing values in your dataset"
    )
    
    if df.empty:
        _render_info_box("Dataset is empty", "info")
        return
    
    # Missing analysis - FIX: Convert to list to avoid subscriptable error
    missing_summary = df.isnull().sum()
    columns_with_missing = missing_summary[missing_summary > 0]
    
    # Convert to list of tuples for iteration
    missing_items = list(columns_with_missing.items())
    
    if len(missing_items) == 0:
        _render_info_box("✅ No missing values found", "success")
        return
    
    # Summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Missing", f"{missing_summary.sum():,}")
    with col2:
        missing_pct = (missing_summary.sum() / (len(df) * len(df.columns))) * 100
        st.metric("Percentage", f"{missing_pct:.1f}%")
    with col3:
        st.metric("Affected Columns", len(missing_items))
    
    # Treatment options
    st.markdown("### 🛠️ Treatment Options")
    
    method = st.selectbox(
        "Select treatment method:",
        [
            "Fill with specific value",
            "Fill with mean (numeric only)",
            "Fill with median (numeric only)",
            "Fill with mode (most common)",
            "Remove rows with missing values",
            "Remove columns with missing values"
        ]
    )
    
    # Method-specific options
    fill_value = ""
    if "Fill with specific value" in method:
        fill_value = st.text_input("Value to use:", value="0")
    
    # Affected columns - FIXED: Use list slicing instead of Series slicing
    st.markdown("**Affected columns:**")
    for col, count in missing_items[:5]:
        pct = (count / len(df)) * 100
        st.caption(f"• {col}: {count:,} missing ({pct:.1f}%)")
    if len(missing_items) > 5:
        st.caption(f"... and {len(missing_items) - 5} more")
    
    # Action
    st.markdown("---")
    
    if st.button("✅ Apply Treatment", type="primary", use_container_width=True):
        def operation(d, method, fill_value="", columns=None):
            if columns is None:
                columns = []
                
            if method == "Fill with specific value":
                return d.fillna(fill_value)
            elif method == "Fill with mean (numeric only)":
                new_d = d.copy()
                for col in columns:
                    if pd.api.types.is_numeric_dtype(new_d[col]):
                        new_d[col] = new_d[col].fillna(new_d[col].mean())
                return new_d
            elif method == "Fill with median (numeric only)":
                new_d = d.copy()
                for col in columns:
                    if pd.api.types.is_numeric_dtype(new_d[col]):
                        new_d[col] = new_d[col].fillna(new_d[col].median())
                return new_d
            elif method == "Fill with mode (most common)":
                new_d = d.copy()
                for col in columns:
                    mode_val = new_d[col].mode()
                    if not mode_val.empty:
                        new_d[col] = new_d[col].fillna(mode_val[0])
                return new_d
            elif method == "Remove rows with missing values":
                return d.dropna()
            elif method == "Remove columns with missing values":
                return d.drop(columns=columns)
            return d
        
        # Get column names from the missing items list
        column_names = [col for col, _ in missing_items]
        
        result = OperationsEngine.execute(
            operation, "Handle Missing Values",
            method=method,
            fill_value=fill_value,
            columns=column_names,
            operation_details={"method": method, "affected_columns": len(missing_items)}
        )
        
        if result["success"] and result["df"] is not None:
            if OperationsEngine.apply_to_dataset(result["df"], "Handle Missing Values"):
                st.success(result["message"])
                st.rerun()

def _render_types_ui(df: pd.DataFrame) -> None:
    """Convert data types"""
    _render_section_header(
        "Convert Data Types",
        "Change column data types for better analysis"
    )
    
    if df.empty:
        _render_info_box("Dataset is empty", "info")
        return
    
    # Type analysis
    type_data = []
    for col in df.columns:
        type_data.append({
            "Column": col,
            "Current Type": str(df[col].dtype),
            "Unique Values": df[col].nunique(),
            "Convert To": "Keep current"
        })
    
    # Editor
    st.markdown("Select new data types:")
    
    edited = st.data_editor(
        pd.DataFrame(type_data),
        column_config={
            "Column": st.column_config.TextColumn(disabled=True),
            "Current Type": st.column_config.TextColumn(disabled=True),
            "Unique Values": st.column_config.NumberColumn(disabled=True),
            "Convert To": st.column_config.SelectboxColumn(
                options=["Keep current", "Integer", "Float", "Text", "Boolean", "Date/Time", "Category"]
            )
        },
        hide_index=True,
        use_container_width=True,
        key="type_editor"
    )
    
    # Collect conversions
    conversions = {}
    for _, row in edited.iterrows():
        col = row["Column"]
        new_type = row["Convert To"]
        
        if new_type != "Keep current":
            type_map = {
                "Integer": "int64",
                "Float": "float64",
                "Text": "object",
                "Boolean": "bool",
                "Date/Time": "datetime64[ns]",
                "Category": "category"
            }
            conversions[col] = type_map[new_type]
    
    if conversions:
        st.markdown("**Changes to apply:**")
        for col, new_type in list(conversions.items())[:5]:
            st.caption(f"• {col}: {str(df[col].dtype)} → {new_type}")
        
        if st.button("✅ Apply Type Conversions", type="primary", use_container_width=True):
            def operation(d, conversions):
                new_d = d.copy()
                for col, new_type in conversions.items():
                    try:
                        if new_type == "int64":
                            new_d[col] = pd.to_numeric(new_d[col], errors='coerce').astype('Int64')
                        elif new_type == "float64":
                            new_d[col] = pd.to_numeric(new_d[col], errors='coerce').astype('float64')
                        elif new_type == "object":
                            new_d[col] = new_d[col].astype('string')
                        elif new_type == "bool":
                            new_d[col] = new_d[col].astype('boolean')
                        elif new_type == "datetime64[ns]":
                            new_d[col] = pd.to_datetime(new_d[col], errors='coerce')
                        elif new_type == "category":
                            new_d[col] = new_d[col].astype('category')
                    except Exception as e:
                        st.warning(f"Could not convert {col}: {str(e)[:50]}")
                return new_d
            
            result = OperationsEngine.execute(
                operation, "Convert Data Types",
                conversions=conversions,
                operation_details={"conversions": conversions}
            )
            
            if result["success"] and result["df"] is not None:
                if OperationsEngine.apply_to_dataset(result["df"], "Convert Data Types"):
                    st.success(f"Converted {len(conversions)} columns")
                    st.rerun()

def _render_calculations_ui(df: pd.DataFrame) -> None:
    """Create calculated columns - FIXED validation"""
    _render_section_header(
        "Create Calculated Columns",
        "Build new columns using formulas with df['column'] references"
    )
    
    if df.empty:
        _render_info_box("Dataset is empty", "info")
        return
    
    # Simple layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # FORMULA INPUT
        st.markdown("### 📝 Formula Builder")
        
        new_column = st.text_input(
            "**New Column Name:**",
            placeholder="profit_margin",
            help="Name for the calculated column"
        )
        
        # Formula input with better help
        formula = st.text_area(
            "**Formula Expression:**",
            height=120,
            placeholder="(df['revenue'] - df['cost']) / df['revenue'] * 100",
            help="Use df['column_name'] to reference columns. Example: df['sales'] * df['price']",
            key="formula_input"
        )
        
        # Quick create button
        if st.button(
            "✅ Create Calculated Column",
            type="primary",
            disabled=not (formula and new_column),
            use_container_width=True
        ):
            if new_column in df.columns:
                st.error(f"Column '{new_column}' already exists")
            else:
                # Validate using ACTUAL dataset
                validation = FormulaEngine.validate_formula(formula, df)
                
                if validation["valid"]:
                    try:
                        result_df = FormulaEngine.evaluate_formula(df, formula, new_column)
                        
                        if OperationsEngine.apply_to_dataset(result_df, "Create Calculated Column"):
                            st.success(f"✅ Created column '{new_column}'")
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        
                        # Show helpful hints for common errors
                        error_msg = str(e).lower()
                        if "dt accessor" in error_msg:
                            st.info("💡 **Tip:** Convert your date column to datetime type first using the '🔄 Convert Types' tab.")
                        elif "str accessor" in error_msg:
                            st.info("💡 **Tip:** Convert your text column to string type first using the '🔄 Convert Types' tab.")
                        elif "not defined" in error_msg:
                            st.info("💡 **Tip:** Make sure to use `np.` prefix for numpy functions: `np.sqrt()`, `np.log()`, etc.")
                else:
                    st.error("❌ Formula has issues:")
                    for issue in validation["issues"][:3]:
                        st.caption(f"• {issue}")
                    
                    if validation["warnings"]:
                        st.warning("⚠️ Warnings:")
                        for warning in validation["warnings"][:2]:
                            st.caption(f"• {warning}")
        
        # QUICK PREVIEW - Using actual data
        if formula and new_column:
            st.markdown("---")
            st.markdown("#### 🔍 Quick Preview")
            
            try:
                # Use first 5 rows for preview
                preview_sample = df.head(5).copy()
                preview_df = FormulaEngine.evaluate_formula(
                    preview_sample,
                    formula,
                    "preview_result"
                )
                
                # Find which columns were referenced
                referenced = []
                for col in df.columns:
                    if f"df['{col}']" in formula or f'df["{col}"]' in formula:
                        referenced.append(col)
                
                # Show relevant columns
                if referenced:
                    show_cols = referenced[:3] + ["preview_result"]
                    preview_display = preview_df[show_cols]
                    
                    # Format nicely
                    def format_cell(val):
                        if pd.isna(val):
                            return "—"
                        if isinstance(val, (int, np.integer)):
                            return f"{val:,}"
                        if isinstance(val, (float, np.floating)):
                            return f"{val:,.2f}"
                        if isinstance(val, pd.Timestamp):
                            return val.strftime("%Y-%m-%d")
                        return str(val)[:20]
                    
                    formatted = preview_display.map(format_cell)
                    st.dataframe(formatted, use_container_width=True)
                    
                    # Show data types
                    st.caption("**Data types:**")
                    type_cols = st.columns(len(show_cols))
                    for idx, col in enumerate(show_cols):
                        with type_cols[idx]:
                            dtype = preview_df[col].dtype
                            st.caption(f"`{col}`: {dtype}")
                
            except Exception as e:
                st.warning(f"⚠️ Preview unavailable: {str(e)[:80]}")
                
                # Show quick validation
                try:
                    validation = FormulaEngine.validate_formula(formula, df.head(1))
                    if validation["valid"]:
                        st.info("✅ Formula syntax is valid (full evaluation may need data adjustments)")
                except:
                    pass
    
    with col2:
        # TOOLS & EXAMPLES
        st.markdown("### 🛠️ Tools & Examples")
        
        # Dataset Reference
        with st.expander("📊 Dataset Reference", expanded=False):
            # Quick column browser
            st.markdown("**Quick column reference:**")
            
            # Search/filter
            search_term = st.text_input(
                "Search columns:",
                placeholder="Type to filter...",
                key="col_search",
                label_visibility="collapsed"
            )
            
            # Filter columns
            if search_term:
                filtered_cols = [c for c in df.columns if search_term.lower() in c.lower()]
            else:
                filtered_cols = df.columns.tolist()[:15]  # Limit to 15 by default
            
            # Display with insert buttons
            for col in filtered_cols:
                col1, col2 = st.columns([3, 2])
                
                with col1:
                    st.code(f"df['{col}']")
                
                with col2:
                    dtype = df[col].dtype
                    st.caption(str(dtype))
                
            if len(df.columns) > 15 and not search_term:
                st.caption(f"... and {len(df.columns) - 15} more columns. Use search to find.")
        
        # Advanced Examples
        with st.expander("🚀 Advanced Formula Examples", expanded=False):
            examples = FormulaEngine.get_advanced_examples()
            
            # Category selector
            category = st.selectbox(
                "Select category:",
                list(examples.keys()),
                label_visibility="collapsed"
            )
            
            if category:
                st.code(examples[category], language="python")
                
                # Category-specific tips
                tips = {
                    "📈 Time Series": "For date operations, ensure date columns are datetime type.",
                    "💰 Financial": "Multiply by 100 for percentages. Use parentheses for correct order.",
                    "📊 Analytics": "Normalize data before analysis. Handle missing values first.",
                    "📅 Date Operations": "Convert columns to datetime first. Use .dt accessor for date properties.",
                    "🔬 Advanced": "Group operations require categorical columns. Use .transform() for group-wise operations."
                }
                
                if category in tips:
                    st.info(f"💡 **Note:** {tips[category]}")
        
        # Quick Tips
        with st.expander("💡 Tips & Troubleshooting", expanded=False):
            st.markdown("""
            **Common Issues:**
            
            **1. Date operations fail:**
            • Error: "Can only use .dt accessor with datetimelike values"
            • Fix: Convert column to datetime in "🔄 Convert Types" tab first
            
            **2. String operations fail:**
            • Error: "Can only use .str accessor with string values"
            • Fix: Convert column to string in "🔄 Convert Types" tab
            
            **3. "np is not defined":**
            • Use `np.sqrt()` not `sqrt()`
            • Use `np.log()` not `log()`
            
            **4. Column not found:**
            • Use exact column name: `df['Sales']` vs `df['sales']`
            • Check for typos
            
            **5. Group operations:**
            • Ensure grouping column is categorical
            • Use `.transform()` for group-wise calculations
            """)

# ============================================================================
# MAIN TAB INTERFACE
# ============================================================================

def render_data_operations_tab():
    """Main interface for data operations"""
    # Dataset status
    df = st.session_state.get('dataset')
    
    if df is None or df.empty:
        _render_info_box("📭 No dataset loaded. Please upload data first.", "info")
        return
    
    # Quick stats
    with st.container():
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Rows", f"{len(df):,}")
        with col2:
            st.metric("Columns", len(df.columns))
        with col3:
            nulls = df.isnull().sum().sum()
            st.metric("Missing", f"{nulls:,}")
        with col4:
            dups = df.duplicated().sum()
            st.metric("Duplicates", f"{dups:,}")
        with col5:
            try:
                mem = df.memory_usage(deep=True).sum() / (1024 ** 2)
                st.metric("Memory", f"{mem:.1f} MB")
            except:
                st.metric("Memory", "N/A")
    
    st.markdown("---")
    
    # Operations tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🧹 Clean Data",
        "📊 Manage Columns", 
        "⚡ Handle Missing",
        "🔄 Convert Types",
        "✨ Calculations"
    ])
    
    with tab1:
        _render_duplicates_ui(df)
    
    with tab2:
        _render_columns_ui(df)
    
    with tab3:
        _render_missing_ui(df)
    
    with tab4:
        _render_types_ui(df)
    
    with tab5:
        _render_calculations_ui(df)
    
    # Operation history
    history = OperationsEngine.get_history()
    if history:
        st.markdown("---")
        
        with st.expander("📜 Operation History", expanded=False):
            for op in reversed(history[-5:]):
                with st.container(border=True):
                    col1, col2, col3 = st.columns([1, 2, 1])
                    
                    with col1:
                        st.caption(f"**{op['time']}**")
                    
                    with col2:
                        st.markdown(f"**{op['operation']}**")
                        if 'details' in op and op['details']:
                            details = list(op['details'].items())[:2]
                            for key, value in details:
                                st.caption(f"• {key}: {value}")
                    
                    with col3:
                        rows_before = op['before']['rows']
                        rows_after = op['after']['rows']
                        cols_before = op['before']['columns']
                        cols_after = op['after']['columns']
                        
                        st.caption(f"{rows_before:,}×{cols_before:,} → {rows_after:,}×{cols_after:,}")
            
            if st.button("Clear History", use_container_width=True):
                OperationsEngine.clear_history()
                st.rerun()
    
    # Dataset preview
    st.markdown("---")
    
    with st.expander("🔍 Dataset Preview", expanded=False):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("**Current Dataset**")
            st.markdown(f"**Shape:** {len(df):,} rows × {len(df.columns)} columns")
            
            # Column types summary
            numeric = len(df.select_dtypes(include=[np.number]).columns)
            text = len(df.select_dtypes(include=['object', 'string']).columns)
            dates = len([c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])])
            
            st.markdown(f"**Types:** {numeric} numeric, {text} text, {dates} date")
        
        with col2:
            st.markdown("**Quick Actions**")
            if st.button("📋 Show Summary", use_container_width=True):
                st.dataframe(df.describe(include='all'), use_container_width=True)
            
            if st.button("📤 Export", use_container_width=True):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                csv = df.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv,
                    f"dataset_{timestamp}.csv",
                    "text/csv",
                    use_container_width=True
                )
        
        # Data preview
        st.markdown("**First 5 rows:**")
        _render_preview_table(df.head(5))

# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    'OperationsEngine',
    'FormulaEngine',
    'render_data_operations_tab'
]