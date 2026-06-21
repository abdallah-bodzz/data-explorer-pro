"""
Echo Engine Core v1.0.0 - Production-Grade Business Intelligence Agent
Professional analytics with insight mining, relationship detection, and actionable intelligence.
Transformed from chart generator to business consultant in a box.

Features:
- Business relationship mining
- Time series intelligence  
- Pareto concentration analysis
- Missing data impact detection
- Insight-driven chart prioritization
- Professional executive summaries
"""

import json
import re
import logging
import math
import time
import copy
import uuid
import hashlib
import sys
from typing import Optional, Dict, Any, List, Tuple, Generator, Set, Union
from dataclasses import dataclass, field, asdict
from collections import defaultdict, Counter
from datetime import datetime
from enum import Enum
import concurrent.futures
from functools import lru_cache

import pandas as pd
import numpy as np
from pandas.api.types import (
    is_numeric_dtype,
    is_datetime64_any_dtype,
    is_categorical_dtype,
    is_string_dtype,
    is_bool_dtype
)

# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

class BusinessPriority(Enum):
    HIGH = "high"
    MEDIUM = "medium" 
    LOW = "low"

class InsightType(Enum):
    DEPENDENCY_RISK = "dependency_risk"
    STRONG_PARETO = "strong_pareto"
    BUSINESS_RELATIONSHIP = "business_relationship"
    GOLDEN_PERIOD = "golden_period"
    MISSING_DATA_OPPORTUNITY = "missing_data_opportunity"
    SIGNIFICANT_TREND = "significant_trend"
    HIGH_VOLATILITY = "high_volatility"
    SEASONAL_PATTERN = "seasonal_pattern"
    MODERATE_CONCENTRATION = "moderate_concentration"
    HEALTHY_DISTRIBUTION = "healthy_distribution"
    DATA_QUALITY_ISSUE = "data_quality_issue"
    CRITICAL_RISK = "critical_risk"

class SemanticType(Enum):
    NUMERIC = "numeric"
    CURRENCY = "currency"
    PERCENTAGE = "percentage"
    DATETIME = "datetime"
    CATEGORICAL = "categorical"
    BOOLEAN = "boolean"
    STAGE = "stage"
    ID = "id"
    UNKNOWN = "unknown"

class ChartType(Enum):
    HISTOGRAM = "histogram"
    BAR = "bar"
    LINE = "line"
    SCATTER = "scatter"
    PIE = "pie"
    BOX = "box"
    VIOLIN = "violin"
    HEATMAP = "heatmap"
    AREA = "area"
    WATERFALL = "waterfall"
    FUNNEL = "funnel"
    TREEMAP = "treemap"

# Business priority terms with weights
BUSINESS_PRIORITY_TERMS = {
    BusinessPriority.HIGH: {
        'revenue': 3.0, 'sales': 3.0, 'profit': 3.0, 'gmv': 3.0, 'arr': 3.0,
        'margin': 3.0, 'growth': 2.5, 'income': 2.5, 'earnings': 2.5,
        'gross': 2.5, 'net': 2.5, 'turnover': 2.5, 'value': 2.5, 'worth': 2.5,
        'conversion': 2.5, 'roi': 2.5, 'lifetime': 2.5, 'clv': 2.5,
        'arpu': 2.5, 'transaction': 2.5
    },
    BusinessPriority.MEDIUM: {
        'cost': 2.0, 'expense': 2.0, 'spend': 2.0, 'rate': 2.0,
        'performance': 2.0, 'efficiency': 2.0, 'productivity': 2.0,
        'utilization': 2.0, 'satisfaction': 2.0, 'retention': 2.0,
        'churn': 2.0, 'engagement': 2.0, 'frequency': 2.0, 'duration': 2.0,
        'quality': 2.0, 'score': 2.0, 'metric': 2.0
    },
    BusinessPriority.LOW: {
        'id': 0.1, 'index': 0.1, 'uuid': 0.1, 'timestamp': 0.5,
        'created_at': 0.5, 'updated_at': 0.5, 'row_id': 0.1,
        'record_id': 0.1, 'primary_key': 0.1, 'foreign_key': 0.1,
        'sequence': 0.1, 'hash': 0.1, 'token': 0.1, 'version': 0.3,
        'flag': 0.3, 'status_code': 0.3, 'guid': 0.1
    }
}

CHART_PREFERENCE_MULTIPLIERS = {
    'business_charts': {
        ChartType.BAR.value: 1.4,
        ChartType.LINE.value: 1.4,
        ChartType.HISTOGRAM.value: 1.3,
        ChartType.PIE.value: 1.2,
        ChartType.WATERFALL.value: 1.2,
        ChartType.FUNNEL.value: 1.1,
    },
    'analytical_charts': {
        ChartType.SCATTER.value: 1.0,
        ChartType.BOX.value: 0.9,
        ChartType.VIOLIN.value: 0.7,
        # ChartType.BUBBLE.value: 0.8,
        # ChartType.HEATMAP.value: 0.8,
    }
}

DEFAULT_CONFIG = {
    # Performance & Memory Limits
    'sample_limit': 10000,
    'min_rows': 3,
    'max_columns_for_flood': 80,
    'max_chart_candidates': 120,
    'max_rows_for_chart': 5000,
    'cache_size': 50,
    
    # Insight Mining Thresholds
    'relationship_min_ratio': 1.5,
    'relationship_min_share': 0.02,
    'relationship_min_sample_pct': 0.05,
    'pareto_threshold': 0.8,
    'dependency_risk_threshold': 0.5,
    'trend_threshold': 0.1,
    'volatility_threshold': 1.0,
    'golden_period_ratio': 1.5,
    'missing_impact_threshold': 0.2,
    'missing_importance_threshold': 0.1,
    
    # Scoring Weights
    'weights': {
        'type_match': 0.20,
        'data_quality': 0.15,
        'variation': 0.25,
        'business_impact': 0.25,
        'actionability': 0.10,
        'unique_penalty': 0.05,
    },
    
    # Chart Preferences
    'chart_preference_multipliers': CHART_PREFERENCE_MULTIPLIERS,
    
    # Confidence Thresholds
    'confidence_emit': 0.25,
    'confidence_high': 0.7,
    'confidence_medium': 0.5,
    
    # Analysis Thresholds
    'correlation_threshold': 0.7,
    'variation_threshold': 0.3,
    'skew_threshold': 1.0,
    'outlier_threshold': 0.05,
    'missing_data_threshold': 0.3,
    'seasonality_cv_threshold': 0.3,
    
    # Feature Flags
    'feature_flags': {
        'relationship_mining': True,
        'time_intelligence': True,
        'pareto_detection': True,
        'missing_data_analysis': True,
        'insight_boosting': True,
        'dynamic_limits': True,
        'anomaly_detection': True,
        'corr_bonus': True,
    },
    
    # Display Limits
    'top_k': 10,
    'max_categories_pie': 8,
    'max_bins_histogram': 50,
    'max_insights': 5,
    
    # Business Context
    'business_priority_terms': {
        BusinessPriority.HIGH.value: list(BUSINESS_PRIORITY_TERMS[BusinessPriority.HIGH].keys()),
        BusinessPriority.MEDIUM.value: list(BUSINESS_PRIORITY_TERMS[BusinessPriority.MEDIUM].keys()),
        BusinessPriority.LOW.value: list(BUSINESS_PRIORITY_TERMS[BusinessPriority.LOW].keys()),
    },
    
    # Performance Optimizations
    'performance': {
        'enable_column_caching': True,
        'semantic_type_cache_size': 100,
        'enable_sampling_for_analysis': True,
        'analysis_sample_size': 5000,
        'max_workers': 2
    }
}

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

logger = logging.getLogger(__name__)

def setup_logging(level: str = "INFO"):
    """Configure logging for the engine."""
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, level.upper()))
        logger.propagate = False

# Initialize logging
setup_logging()

# ============================================================================
# BUSINESS INTELLIGENCE DATA STRUCTURES
# ============================================================================

@dataclass
class BusinessInsight:
    """Professional business insight with prioritization and actionability."""
    insight_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    priority: float = 5.0  # 1-10 scale
    title: str = ""
    body: str = ""
    insight_type: str = "insight"
    related_columns: List[str] = field(default_factory=list)
    confidence: float = 0.8
    source_algorithm: str = ""
    actionable: bool = True
    suggested_action: str = ""
    impact_score: float = 0.0
    generated_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dictionary."""
        return {
            'id': self.insight_id,
            'priority': round(self.priority, 2),
            'title': self.title,
            'body': self.body,
            'type': self.insight_type,
            'columns': self.related_columns,
            'confidence': round(self.confidence, 2),
            'actionable': self.actionable,
            'action': self.suggested_action,
            'source': self.source_algorithm,
            'impact_score': round(self.impact_score, 2),
            'generated_at': self.generated_at
        }

class InsightStore:
    """Central repository for business insights with prioritization and deduplication."""
    
    PRIORITY_WEIGHTS = {
        InsightType.DEPENDENCY_RISK.value: 10.0,
        InsightType.CRITICAL_RISK.value: 9.0,
        InsightType.MISSING_DATA_OPPORTUNITY.value: 8.5,
        InsightType.GOLDEN_PERIOD.value: 8.0,
        InsightType.STRONG_PARETO.value: 7.0,
        InsightType.BUSINESS_RELATIONSHIP.value: 6.5,
        InsightType.SIGNIFICANT_TREND.value: 6.0,
        InsightType.MODERATE_CONCENTRATION.value: 5.0,
        InsightType.HIGH_VOLATILITY.value: 4.0,
        InsightType.SEASONAL_PATTERN.value: 3.5,
        InsightType.HEALTHY_DISTRIBUTION.value: 3.0,
        InsightType.DATA_QUALITY_ISSUE.value: 2.0,
    }
    
    def __init__(self, metadata: Dict[str, Any]):
        self.metadata = metadata
        self.insights: List[BusinessInsight] = []
        self._seen_patterns: Set[str] = set()
        
    def add_insights(self, raw_insights: List[Dict], source: str) -> None:
        """Convert raw insights to BusinessInsight objects with deduplication."""
        if not raw_insights:
            return
            
        for raw in raw_insights:
            # Create unique pattern key for deduplication
            pattern_key = self._create_pattern_key(raw)
            if pattern_key in self._seen_patterns:
                continue
                
            self._seen_patterns.add(pattern_key)
            
            insight_type = raw.get('type', 'statistical_insight')
            
            # Create the insight
            insight = BusinessInsight(
                priority=self.PRIORITY_WEIGHTS.get(insight_type, 5.0) * raw.get('priority_multiplier', 1.0),
                title=self._generate_title(raw, insight_type),
                body=raw.get('insight', raw.get('story', raw.get('body', ''))),
                insight_type=insight_type,
                related_columns=self._extract_columns(raw),
                confidence=raw.get('confidence', 0.8),
                source_algorithm=source,
                actionable=raw.get('actionable', True),
                suggested_action=self._suggest_action(raw, insight_type),
                impact_score=self._calculate_impact_score(raw, insight_type)
            )
            
            self.insights.append(insight)
    
    def _create_pattern_key(self, raw: Dict) -> str:
        """Create unique key for insight deduplication."""
        columns = sorted(self._extract_columns(raw))
        metric = str(raw.get('metric', ''))
        return f"{raw.get('type', 'unknown')}_{'_'.join(columns)}_{metric}"
    
    def _extract_columns(self, raw: Dict) -> List[str]:
        """Extract all column references from insight."""
        columns = []
        
        # Check common field names
        for field_name in ['metric', 'category', 'dimension', 'missing_column', 
                          'impact_metric', 'date_column', 'x', 'y']:
            if field_name in raw and raw[field_name]:
                value = raw[field_name]
                if isinstance(value, str):
                    columns.append(value)
        
        # Check for explicit columns list
        if 'columns' in raw and isinstance(raw['columns'], list):
            columns.extend([c for c in raw['columns'] if isinstance(c, str)])
        
        return list(set(columns))
    
    def _generate_title(self, raw: Dict, insight_type: str) -> str:
        """Generate concise, action-oriented title."""
        title_templates = {
            InsightType.DEPENDENCY_RISK.value: f"🚨 Critical Dependency: {raw.get('metric', 'Key Metric')}",
            InsightType.STRONG_PARETO.value: f"🎯 80/20 Rule: {raw.get('metric', 'Metric')} Concentration",
            InsightType.BUSINESS_RELATIONSHIP.value: f"🔗 Top Performer: {raw.get('category', 'Category')} × {raw.get('metric', 'Metric')}",
            InsightType.GOLDEN_PERIOD.value: f"⭐ Peak Performance: {raw.get('period', 'Period')}",
            InsightType.MISSING_DATA_OPPORTUNITY.value: f"💡 Data Opportunity: Missing {raw.get('missing_column', 'Data')}",
            InsightType.SIGNIFICANT_TREND.value: f"📈 Strong Trend: {raw.get('metric', 'Metric')}",
            InsightType.HIGH_VOLATILITY.value: f"⚡ High Volatility: {raw.get('metric', 'Metric')}",
            InsightType.SEASONAL_PATTERN.value: f"🔄 Seasonal Pattern: {raw.get('metric', 'Metric')}",
            InsightType.MODERATE_CONCENTRATION.value: f"📊 Concentration: {raw.get('metric', 'Metric')}",
            InsightType.HEALTHY_DISTRIBUTION.value: f"✅ Healthy Spread: {raw.get('metric', 'Metric')}",
            InsightType.CRITICAL_RISK.value: f"🚨 Critical Risk: {raw.get('metric', 'Metric')}"
        }
        
        return title_templates.get(insight_type, f"Insight: {insight_type.replace('_', ' ').title()}")
    
    def _suggest_action(self, raw: Dict, insight_type: str) -> str:
        """Generate specific, actionable next steps."""
        action_templates = {
            InsightType.DEPENDENCY_RISK.value: f"Diversify from over-reliance on '{raw.get('top_item', 'key segment')}'",
            InsightType.STRONG_PARETO.value: f"Focus on top {raw.get('top_n', 3)} {raw.get('dimension', 'segments')}",
            InsightType.BUSINESS_RELATIONSHIP.value: f"Replicate '{raw.get('top_segment', 'top performer')}' success across segments",
            InsightType.GOLDEN_PERIOD.value: f"Analyze why {raw.get('period', 'this period')} outperforms and replicate",
            InsightType.MISSING_DATA_OPPORTUNITY.value: f"Investigate why missing '{raw.get('missing_column')}' correlates with better performance",
            InsightType.SIGNIFICANT_TREND.value: f"Capitalize on this {'growth' if raw.get('trend', 0) > 0 else 'decline'} trend",
            InsightType.HIGH_VOLATILITY.value: f"Implement smoothing or forecasting for better planning",
            InsightType.SEASONAL_PATTERN.value: f"Align resource allocation with seasonal peaks",
            InsightType.MODERATE_CONCENTRATION.value: f"Monitor concentration levels and consider diversification",
            InsightType.HEALTHY_DISTRIBUTION.value: f"Maintain this healthy distribution across segments",
            InsightType.CRITICAL_RISK.value: f"Immediate action required to mitigate this risk"
        }
        
        default_action = "Review this insight for strategic opportunities"
        return action_templates.get(insight_type, default_action)
    
    def _calculate_impact_score(self, raw: Dict, insight_type: str) -> float:
        """Calculate business impact score (0-1)."""
        base_score = 0.5
        
        # Impact based on type
        type_impact = {
            InsightType.DEPENDENCY_RISK.value: 0.9,
            InsightType.CRITICAL_RISK.value: 0.9,
            InsightType.MISSING_DATA_OPPORTUNITY.value: 0.8,
            InsightType.GOLDEN_PERIOD.value: 0.8,
            InsightType.STRONG_PARETO.value: 0.7,
            InsightType.BUSINESS_RELATIONSHIP.value: 0.7,
            InsightType.SIGNIFICANT_TREND.value: 0.6,
            InsightType.HIGH_VOLATILITY.value: 0.6,
            InsightType.SEASONAL_PATTERN.value: 0.5,
            InsightType.MODERATE_CONCENTRATION.value: 0.5,
            InsightType.HEALTHY_DISTRIBUTION.value: 0.4,
            InsightType.DATA_QUALITY_ISSUE.value: 0.4
        }
        
        base_score = type_impact.get(insight_type, 0.5)
        
        # Adjust based on data
        if 'share_of_total' in raw:
            base_score *= min(1.0, raw['share_of_total'] * 2)
        elif 'concentration' in raw:
            base_score *= min(1.0, raw['concentration'] * 2)
        elif 'difference_pct' in raw:
            base_score *= min(1.0, raw['difference_pct'])
        
        return min(1.0, max(0.1, base_score))
    
    def get_prioritized_insights(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top insights sorted by priority and impact."""
        self.insights.sort(key=lambda x: (x.priority, x.impact_score), reverse=True)
        return [insight.to_dict() for insight in self.insights[:limit]]
    
    def get_hero_insight(self) -> Optional[Dict[str, Any]]:
        """Get the single most important insight (hero insight)."""
        insights = self.get_prioritized_insights(limit=1)
        return insights[0] if insights else None

@dataclass
class ColumnSummary:
    """Professional column metadata with caching and performance tracking."""
    name: str
    dtype: str
    semantic_type: str
    null_count: int
    null_pct: float
    unique_count: int
    top_values: Dict[Any, int] = field(default_factory=dict)
    sample_values: List[Any] = field(default_factory=list)
    numeric_stats: Dict[str, Optional[float]] = field(default_factory=dict)
    outlier_score: Optional[float] = None
    anomaly_flag: bool = False
    anomaly_reason: Optional[str] = None
    business_priority: str = "medium"
    is_junk: bool = False
    semantic_inferred_at: float = field(default_factory=time.time)
    analysis_time_ms: int = 0
    _hash: str = field(default="")
    
    def __post_init__(self):
        """Compute stable hash for caching and performance."""
        if not self._hash:
            content = f"{self.name}|{self.semantic_type}|{self.null_pct:.3f}|{self.unique_count}"
            self._hash = hashlib.md5(content.encode()).hexdigest()[:10]
    
    def to_dict(self) -> Dict[str, Any]:
        """Safe serialization for caching and metadata."""
        return {
            'name': self.name,
            'dtype': self.dtype,
            'semantic_type': self.semantic_type,
            'null_pct': self.null_pct,
            'unique_count': self.unique_count,
            'business_priority': self.business_priority,
            'is_junk': self.is_junk,
            'anomaly_flag': self.anomaly_flag,
            'outlier_score': self.outlier_score,
            '_hash': self._hash,
        }

# ============================================================================
# BUSINESS INTELLIGENCE MINING ENGINES
# ============================================================================

class InsightMiner:
    """Core engine for mining business insights from data."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    def mine_insights(self, df: pd.DataFrame, metadata: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """Run all insight mining algorithms."""
        insights = {}
        
        try:
            # 1. Business Relationships
            if self._get_feature_flag('relationship_mining'):
                relationships = self._find_key_relationships(df, metadata)
                insights['relationships'] = relationships
            
            # 2. Time Patterns
            if self._get_feature_flag('time_intelligence') and metadata.get('datetime_columns'):
                time_patterns = self._analyze_time_patterns(df, metadata)
                insights['time_patterns'] = time_patterns
            
            # 3. Pareto Patterns
            if self._get_feature_flag('pareto_detection'):
                pareto_patterns = self._detect_pareto_patterns(df, metadata)
                insights['pareto_patterns'] = pareto_patterns
            
            # 4. Missing Data Impact
            if self._get_feature_flag('missing_data_analysis'):
                missing_impact = self._analyze_missing_impact(df, metadata)
                insights['missing_data_impact'] = missing_impact
                
        except Exception as e:
            logger.error(f"Insight mining failed: {e}", exc_info=True)
            # Return empty insights rather than failing completely
        
        return insights
    
    def _get_feature_flag(self, flag_name: str) -> bool:
        """Safely get feature flag with default."""
        return self.config.get('feature_flags', {}).get(flag_name, False)
    
    def _find_key_relationships(self, df: pd.DataFrame, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find SIGNIFICANT business relationships."""
        insights = []
        
        # Get thresholds from config with defaults
        min_ratio = self.config.get('relationship_min_ratio', 1.5)
        min_share = self.config.get('relationship_min_share', 0.02)
        min_sample_pct = self.config.get('relationship_min_sample_pct', 0.05)
        
        # Get business priority columns
        business_high = self.config.get('business_priority_terms', {}).get(BusinessPriority.HIGH.value, [])
        business_medium = self.config.get('business_priority_terms', {}).get(BusinessPriority.MEDIUM.value, [])
        
        # Prioritize business columns
        business_categoricals = [
            col for col in metadata.get('categorical_columns', [])
            if not metadata['columns'][col].get('is_junk', False) and
            (any(term in col.lower() for term in business_high + business_medium) or
             metadata['columns'][col].get('business_priority') == BusinessPriority.HIGH.value)
        ][:10]
        
        business_numerics = [
            col for col in metadata.get('numeric_columns', [])
            if not metadata['columns'][col].get('is_junk', False) and
            (any(term in col.lower() for term in business_high + business_medium) or
             metadata['columns'][col].get('business_priority') in [BusinessPriority.HIGH.value, BusinessPriority.MEDIUM.value])
        ][:8]
        
        if not business_categoricals or not business_numerics:
            return insights
        
        total_rows = metadata.get('row_count', 0)
        
        for cat_col in business_categoricals:
            for num_col in business_numerics:
                if cat_col == num_col:
                    continue
                
                try:
                    # Group by SUM (business impact)
                    grouped = df.groupby(cat_col)[num_col].agg(['sum', 'mean', 'count'])
                    if len(grouped) < 3:
                        continue
                    
                    total_value = grouped['sum'].sum()
                    if total_value == 0:
                        continue
                    
                    # Calculate share AND performance
                    grouped['share_of_total'] = grouped['sum'] / total_value
                    grouped['performance_ratio'] = grouped['mean'] / df[num_col].mean()
                    
                    # Apply significance filters
                    significant = grouped[
                        (grouped['count'] >= total_rows * min_sample_pct) &
                        (grouped['share_of_total'] >= min_share) &
                        (grouped['performance_ratio'] >= min_ratio)
                    ]
                    
                    if not significant.empty:
                        # Get top performer
                        top_row = significant.nlargest(1, 'share_of_total').iloc[0]
                        top_category = significant.nlargest(1, 'share_of_total').index[0]
                        
                        # Determine insight type
                        insight_type = InsightType.BUSINESS_RELATIONSHIP.value
                        priority_multiplier = 1.5
                        
                        if top_row['share_of_total'] > self.config.get('dependency_risk_threshold', 0.5):
                            insight_type = InsightType.DEPENDENCY_RISK.value
                            priority_multiplier = 2.5
                        
                        # Create insight
                        insight = {
                            'type': insight_type,
                            'category': cat_col,
                            'metric': num_col,
                            'top_segment': str(top_category),
                            'share_of_total': float(top_row['share_of_total']),
                            'performance_multiplier': float(top_row['performance_ratio']),
                            'row_count': int(top_row['count']),
                            'confidence': min(0.95, 0.7 + (top_row['performance_ratio'] * 0.1)),
                            'actionable': True,
                            'priority_multiplier': priority_multiplier,
                            'insight': self._format_relationship_insight(
                                insight_type, top_category, top_row, num_col
                            )
                        }
                        
                        insights.append(insight)
                        
                except Exception as e:
                    logger.debug(f"Relationship mining failed for {cat_col}×{num_col}: {e}")
                    continue
        
        # Sort by impact (share × performance)
        insights.sort(key=lambda x: x['share_of_total'] * x['performance_multiplier'], reverse=True)
        return insights[:self.config.get('max_insights', 5)]
    
    def _format_relationship_insight(self, insight_type: str, top_category: str, 
                                    top_row: pd.Series, num_col: str) -> str:
        """Format relationship insight text."""
        if insight_type == InsightType.DEPENDENCY_RISK.value:
            return (
                f"🚨 DEPENDENCY RISK: '{top_category}' drives "
                f"{top_row['share_of_total']:.0%} of {num_col} with "
                f"{top_row['performance_ratio']:.1f}x average performance"
            )
        else:
            return (
                f"'{top_category}' segment delivers "
                f"{top_row['share_of_total']:.0%} of {num_col} with "
                f"{top_row['performance_ratio']:.1f}x average performance"
            )
    
    def _analyze_time_patterns(self, df: pd.DataFrame, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Intelligent time analysis with business context."""
        time_insights = []
        
        if not self._get_feature_flag('time_intelligence'):
            return time_insights
        
        # Get datetime columns
        datetime_cols = metadata.get('datetime_columns', [])
        if not datetime_cols:
            return time_insights
        
        # Get business metrics to analyze
        business_metrics = []
        for num_col in metadata.get('numeric_columns', []):
            if metadata['columns'][num_col].get('is_junk', False):
                continue
            
            # Score business importance
            col_lower = num_col.lower()
            if any(term in col_lower for term in self.config.get('business_priority_terms', {}).get(BusinessPriority.HIGH.value, [])):
                business_metrics.append((num_col, 3.0))
            elif any(term in col_lower for term in self.config.get('business_priority_terms', {}).get(BusinessPriority.MEDIUM.value, [])):
                business_metrics.append((num_col, 1.0))
        
        # Sort by business importance
        business_metrics.sort(key=lambda x: x[1], reverse=True)
        
        # Analyze top datetime column with top business metrics
        dt_col = datetime_cols[0]
        for num_col, importance_score in business_metrics[:3]:
            try:
                # Prepare time series
                time_df = df[[dt_col, num_col]].dropna()
                if len(time_df) < 6:
                    continue
                
                # Sort by time
                time_df = time_df.sort_values(dt_col)
                
                # Convert to numeric for analysis
                time_series = pd.to_numeric(time_df[num_col], errors='coerce').dropna()
                if len(time_series) < 6:
                    continue
                
                insights = self._analyze_time_series(time_series, dt_col, num_col)
                time_insights.extend(insights)
                    
            except Exception as e:
                logger.debug(f"Time analysis failed for {dt_col}×{num_col}: {e}")
                continue
        
        return time_insights[:3]
    
    def _analyze_time_series(self, time_series: pd.Series, dt_col: str, 
                            num_col: str) -> List[Dict[str, Any]]:
        """Analyze a single time series for patterns."""
        insights = []
        y = time_series.values
        
        # 1. TREND ANALYSIS
        x = np.arange(len(time_series))
        slope, intercept = np.polyfit(x, y, 1)
        y_mean = np.mean(y)
        
        if abs(y_mean) > 1e-9:
            normalized_slope = slope / abs(y_mean)
            trend_threshold = self.config.get('trend_threshold', 0.1)
            
            if abs(normalized_slope) > trend_threshold:
                direction = "growing" if slope > 0 else "declining"
                insights.append({
                    'type': InsightType.SIGNIFICANT_TREND.value,
                    'date_column': dt_col,
                    'metric': num_col,
                    'trend': float(normalized_slope),
                    'direction': direction,
                    'confidence': min(0.9, 0.7 + min(0.2, abs(normalized_slope))),
                    'priority_multiplier': 1.8 if abs(normalized_slope) > 0.2 else 1.2,
                    'insight': f"{num_col} is {direction} at {abs(normalized_slope):.1%} per period"
                })
        
        # 2. VOLATILITY ANALYSIS
        if len(time_series) >= 12:
            try:
                monthly = pd.to_datetime(time_series.index).to_period('M')
                monthly_df = pd.DataFrame({'value': y, 'month': monthly})
                monthly_agg = monthly_df.groupby('month')['value'].mean()
                
                if len(monthly_agg) >= 3:
                    cv = monthly_agg.std() / monthly_agg.mean() if monthly_agg.mean() != 0 else 0
                    volatility_threshold = self.config.get('volatility_threshold', 1.0)
                    
                    if cv > volatility_threshold:
                        insights.append({
                            'type': InsightType.HIGH_VOLATILITY.value,
                            'date_column': dt_col,
                            'metric': num_col,
                            'cv': float(cv),
                            'confidence': 0.8,
                            'priority_multiplier': 1.3,
                            'insight': f"⚠️ {num_col} is HIGHLY VOLATILE (CV={cv:.2f})"
                        })
            except Exception as e:
                logger.debug(f"Volatility analysis failed: {e}")
        
        # 3. GOLDEN PERIOD DETECTION
        if len(time_series) >= 8:
            window_size = max(3, len(time_series) // 4)
            max_avg = -np.inf
            best_start = 0
            
            for i in range(len(time_series) - window_size + 1):
                window_avg = np.mean(y[i:i+window_size])
                if window_avg > max_avg:
                    max_avg = window_avg
                    best_start = i
            
            overall_avg = np.mean(y)
            golden_period_ratio = self.config.get('golden_period_ratio', 1.5)
            
            if overall_avg > 0 and max_avg / overall_avg > golden_period_ratio:
                insights.append({
                    'type': InsightType.GOLDEN_PERIOD.value,
                    'date_column': dt_col,
                    'metric': num_col,
                    'performance_ratio': float(max_avg / overall_avg),
                    'confidence': 0.75,
                    'priority_multiplier': 1.8,
                    'insight': f"⭐ GOLDEN PERIOD: Best {window_size} periods deliver {max_avg/overall_avg:.1f}x average"
                })
        
        return insights
    
    def _detect_pareto_patterns(self, df: pd.DataFrame, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find concentration patterns (80/20 rule)."""
        pareto_insights = []
        
        if not self._get_feature_flag('pareto_detection'):
            return pareto_insights
        
        pareto_threshold = self.config.get('pareto_threshold', 0.8)
        dependency_threshold = self.config.get('dependency_risk_threshold', 0.5)
        
        # Get business combinations only
        business_categories = [
            col for col in metadata.get('categorical_columns', [])
            if not metadata['columns'][col].get('is_junk', False) and
            metadata['columns'][col].get('unique_count', 0) >= 3
        ][:12]
        
        business_metrics = [
            col for col in metadata.get('numeric_columns', [])
            if not metadata['columns'][col].get('is_junk', False) and
            metadata['columns'][col].get('business_priority') in [BusinessPriority.HIGH.value, BusinessPriority.MEDIUM.value]
        ][:8]
        
        for cat_col in business_categories:
            for num_col in business_metrics:
                if cat_col == num_col:
                    continue
                
                try:
                    # Group by SUM (business impact)
                    grouped = df.groupby(cat_col)[num_col].sum()
                    if len(grouped) < 5:
                        continue
                    
                    total = grouped.sum()
                    if total == 0:
                        continue
                    
                    # Sort descending
                    grouped_sorted = grouped.sort_values(ascending=False)
                    cumulative = grouped_sorted.cumsum() / total
                    
                    # Find Pareto point
                    pareto_point = (cumulative <= pareto_threshold).sum() + 1
                    concentration = cumulative.iloc[pareto_point - 1] if pareto_point > 0 else 0
                    
                    insight = self._create_pareto_insight(
                        cat_col, num_col, pareto_point, concentration, dependency_threshold, grouped_sorted
                    )
                    
                    if insight:
                        pareto_insights.append(insight)
                        
                except Exception as e:
                    logger.debug(f"Pareto analysis failed for {cat_col}×{num_col}: {e}")
                    continue
        
        # Deduplicate by metric
        return self._deduplicate_insights(pareto_insights)
    
    def _create_pareto_insight(self, cat_col: str, num_col: str, pareto_point: int,
                              concentration: float, dependency_threshold: float,
                              grouped_sorted: pd.Series) -> Optional[Dict[str, Any]]:
        """Create Pareto insight based on concentration level."""
        # 1. EXTREME CONCENTRATION (DEPENDENCY RISK)
        if pareto_point == 1 and concentration >= dependency_threshold:
            top_item = str(grouped_sorted.index[0])
            return {
                'type': InsightType.DEPENDENCY_RISK.value,
                'dimension': cat_col,
                'metric': num_col,
                'top_item': top_item,
                'concentration': float(concentration),
                'top_n': int(pareto_point),
                'confidence': 0.9,
                'priority_multiplier': 2.5,
                'insight': f"🚨 CRITICAL DEPENDENCY: '{top_item}' drives {concentration:.0%} of {num_col} - HIGH RISK"
            }
        
        # 2. STRONG PARETO (EFFICIENCY OPPORTUNITY)
        elif pareto_point <= 3 and concentration >= 0.8:
            return {
                'type': InsightType.STRONG_PARETO.value,
                'dimension': cat_col,
                'metric': num_col,
                'concentration': float(concentration),
                'top_n': int(pareto_point),
                'confidence': 0.85,
                'priority_multiplier': 2.0,
                'insight': f"🎯 80/20 RULE: Top {pareto_point} {cat_col}s drive {concentration:.0%} of {num_col}"
            }
        
        # 3. MODERATE CONCENTRATION
        elif pareto_point <= 5 and concentration >= 0.6:
            return {
                'type': InsightType.MODERATE_CONCENTRATION.value,
                'dimension': cat_col,
                'metric': num_col,
                'concentration': float(concentration),
                'top_n': int(pareto_point),
                'confidence': 0.75,
                'priority_multiplier': 1.5,
                'insight': f"📊 CONCENTRATION: Top {pareto_point} {cat_col}s deliver {concentration:.0%} of {num_col}"
            }
        
        # 4. HEALTHY DISTRIBUTION
        elif pareto_point >= 10:
            diversity_score = len(grouped_sorted) / pareto_point
            return {
                'type': InsightType.HEALTHY_DISTRIBUTION.value,
                'dimension': cat_col,
                'metric': num_col,
                'diversity_score': float(diversity_score),
                'confidence': 0.7,
                'priority_multiplier': 1.0,
                'insight': f"✅ HEALTHY DISTRIBUTION: {num_col} is well-distributed across {cat_col}s"
            }
        
        return None
    
    def _analyze_missing_impact(self, df: pd.DataFrame, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze impact of missing data on business outcomes."""
        missing_insights = []
        
        if not self._get_feature_flag('missing_data_analysis'):
            return missing_insights
        
        importance_threshold = self.config.get('missing_importance_threshold', 0.1)
        impact_threshold = self.config.get('missing_impact_threshold', 0.2)
        
        # Find important columns with high missingness
        important_missing = []
        for col, info in metadata.get('columns', {}).items():
            if info.get('is_junk', False):
                continue
                
            null_pct = info.get('null_pct', 0)
            
            # Check if column is business important
            is_important = self._is_business_important_column(col, info, metadata)
            
            if is_important and null_pct > importance_threshold:
                important_missing.append((col, null_pct, info.get('business_priority', BusinessPriority.LOW.value)))
        
        # Sort by importance and missingness
        important_missing.sort(key=lambda x: (x[2] == BusinessPriority.HIGH.value, x[1]), reverse=True)
        
        # Analyze impact on key business metrics
        key_metrics = [
            col for col in metadata.get('numeric_columns', [])
            if not metadata['columns'][col].get('is_junk', False) and
            any(term in col.lower() for term in ['revenue', 'sales', 'profit', 'margin', 'growth', 'conversion', 'value'])
        ][:5]
        
        for missing_col, null_pct, priority in important_missing[:3]:
            for metric in key_metrics:
                if missing_col == metric:
                    continue
                    
                try:
                    insight = self._analyze_missing_column_impact(
                        df, missing_col, null_pct, metric, impact_threshold
                    )
                    if insight:
                        missing_insights.append(insight)
                        break  # Move to next missing column
                        
                except Exception as e:
                    logger.debug(f"Missing impact analysis failed for {missing_col}×{metric}: {e}")
                    continue
        
        return missing_insights[:2]
    
    def _is_business_important_column(self, col: str, info: Dict[str, Any], metadata: Dict[str, Any]) -> bool:
        """Check if column is business important."""
        col_lower = col.lower()
        
        # Business term in name
        business_terms = ['customer', 'revenue', 'profit', 'cost', 'price', 'discount',
                         'segment', 'region', 'category', 'product', 'client', 'user']
        
        if any(term in col_lower for term in business_terms):
            return True
        
        # High business priority
        if info.get('business_priority') == BusinessPriority.HIGH.value:
            return True
        
        # Hero metric
        if metadata.get('hero_metric') == col:
            return True
        
        return False
    
    def _analyze_missing_column_impact(self, df: pd.DataFrame, missing_col: str, 
                                      null_pct: float, metric: str, 
                                      impact_threshold: float) -> Optional[Dict[str, Any]]:
        """Analyze impact of a specific missing column on a metric."""
        # Compare metric when column is null vs not null
        not_null_mask = df[missing_col].notnull()
        null_mask = df[missing_col].isnull()
        
        # Need sufficient samples
        if not_null_mask.sum() < 5 or null_mask.sum() < 5:
            return None
        
        metric_when_present = df.loc[not_null_mask, metric].mean()
        metric_when_missing = df.loc[null_mask, metric].mean()
        
        if pd.isna(metric_when_present) or pd.isna(metric_when_missing):
            return None
        
        if abs(metric_when_present) > 1e-9:
            difference = (metric_when_missing - metric_when_present) / abs(metric_when_present)
            
            # SIGNIFICANT DIFFERENCE
            if abs(difference) > impact_threshold:
                direction = "higher" if difference > 0 else "lower"
                
                # Determine insight type
                insight_type = 'missing_data_impact'
                priority_multiplier = 1.5
                
                if difference > 0.3:  # Missing = 30% BETTER
                    insight_type = InsightType.MISSING_DATA_OPPORTUNITY.value
                    priority_multiplier = 2.0
                
                insight = {
                    'type': insight_type,
                    'missing_column': missing_col,
                    'missing_pct': float(null_pct),
                    'impact_metric': metric,
                    'difference_pct': float(abs(difference)),
                    'direction': direction,
                    'confidence': 0.8 if abs(difference) > 0.3 else 0.7,
                    'priority_multiplier': priority_multiplier,
                    'actionable': True
                }
                
                # Generate insight text
                if insight_type == InsightType.MISSING_DATA_OPPORTUNITY.value:
                    insight['insight'] = (
                        f"💡 OPPORTUNITY: Missing '{missing_col}' ({null_pct:.0%}) correlates with "
                        f"{abs(difference):.0%} HIGHER {metric}"
                    )
                else:
                    insight['insight'] = (
                        f"🔍 DATA IMPACT: When '{missing_col}' is missing ({null_pct:.0%}), "
                        f"'{metric}' is {abs(difference):.0%} {direction}"
                    )
                
                return insight
        
        return None
    
    def _deduplicate_insights(self, insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate insights by metric (keep highest priority)."""
        metric_insights = {}
        for insight in insights:
            metric = insight.get('metric', '')
            if not metric:
                continue
                
            if (metric not in metric_insights or 
                insight.get('priority_multiplier', 0) > metric_insights[metric].get('priority_multiplier', 0)):
                metric_insights[metric] = insight
        
        return list(metric_insights.values())[:3]

# ============================================================================
# CORE DATASET ANALYSIS
# ============================================================================

class DatasetAnalyzer:
    """Production-grade dataset analysis with business insight mining."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or DEFAULT_CONFIG
        self.insight_miner = InsightMiner(self.config)
    
    def analyze(self, df: pd.DataFrame, max_top_values: int = 10) -> Dict[str, Any]:
        """Analyze dataset and mine insights."""
        start_time = time.time()
        
        # Memory guard: limit columns
        if len(df.columns) > self.config.get('max_columns_for_flood', 80):
            logger.warning(f"Dataset too wide: {len(df.columns)} columns, limiting")
            columns_to_keep = self._select_columns_for_analysis(df)
            df = df[columns_to_keep].copy()
        
        # Initialize summary structure
        summary = self._initialize_summary(df)
        
        try:
            # Analyze each column
            self._analyze_columns(df, summary, max_top_values)
            
            # Calculate correlations if enough numeric columns
            if len(summary["numeric_columns"]) >= 2:
                summary["top_correlations"] = self._calculate_top_correlations(df, summary["numeric_columns"])
            
            # Detect hero metric
            summary["hero_metric"] = self._detect_hero_metric(summary)
            
            # BUSINESS INSIGHT MINING
            insight_start_time = time.time()
            insights = self.insight_miner.mine_insights(df, summary)
            
            # Store insights in summary
            for key, value in insights.items():
                summary[key] = value
            
            # Create insight store and add insights
            insight_store = InsightStore(summary)
            for source, insight_list in insights.items():
                insight_store.add_insights(insight_list, source)
            
            # Store prioritized insights
            summary['prioritized_insights'] = insight_store.get_prioritized_insights(
                self.config.get('max_insights', 5)
            )
            summary['hero_insight'] = insight_store.get_hero_insight()
            
            # Generate executive summary
            summary["executive_summary"] = self._generate_enhanced_executive_summary(summary)
            
            # Performance metrics
            summary["analysis_time_ms"] = int((time.time() - start_time) * 1000)
            summary["insight_generation_time_ms"] = int((time.time() - insight_start_time) * 1000)
            
            logger.info(f"Dataset analyzed: {summary['row_count']:,} rows × {summary['col_count']} cols in {summary['analysis_time_ms']}ms")
            logger.info(f"Insights generated: {len(summary['prioritized_insights'])} business insights")
            
            return summary
            
        except Exception as e:
            logger.error(f"Dataset analysis failed: {e}", exc_info=True)
            # Return basic summary even if analysis fails
            summary['error'] = str(e)
            return summary
    
    def _initialize_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Initialize the summary dictionary."""
        return {
            "shape": df.shape,
            "row_count": int(df.shape[0]),
            "col_count": int(df.shape[1]),
            "columns": {},
            "numeric_columns": [],
            "categorical_columns": [],
            "datetime_columns": [],
            "global_missing_pct": 0.0,
            "top_correlations": [],
            "analysis_timestamp": time.time(),
            "data_hash": self._compute_dataset_hash(df),
            "business_priority_columns": [],
            "hero_metric": None,
            "executive_summary": "",
            "analysis_time_ms": 0,
            "insight_generation_time_ms": 0,
            "performance_metrics": {
                "cache_hits": 0,
                "cache_misses": 0,
                "cached_columns": 0
            }
        }
    
    def _analyze_columns(self, df: pd.DataFrame, summary: Dict[str, Any], max_top_values: int) -> None:
        """Analyze each column in the dataset."""
        for col in df.columns:
            col_start_time = time.time()
            try:
                col_summary = self._analyze_single_column(df, col, summary['row_count'], max_top_values)
                summary["columns"][col] = col_summary.to_dict()
                
                # Categorize by semantic type
                if col_summary.semantic_type in [SemanticType.NUMERIC.value, SemanticType.CURRENCY.value, SemanticType.PERCENTAGE.value]:
                    summary["numeric_columns"].append(col)
                elif col_summary.semantic_type == SemanticType.DATETIME.value:
                    summary["datetime_columns"].append(col)
                elif col_summary.semantic_type in [SemanticType.CATEGORICAL.value, SemanticType.BOOLEAN.value, SemanticType.STAGE.value]:
                    summary["categorical_columns"].append(col)
                
                # Track business priority
                if col_summary.business_priority == BusinessPriority.HIGH.value:
                    summary["business_priority_columns"].append(col)
                    
            except Exception as e:
                logger.warning(f"Error analyzing column {col}: {e}")
                summary["columns"][col] = {
                    'name': col,
                    'dtype': str(df[col].dtype),
                    'semantic_type': SemanticType.UNKNOWN.value,
                    'null_count': int(df[col].isnull().sum()),
                    'null_pct': float(df[col].isnull().mean()),
                    'unique_count': int(df[col].nunique()),
                    'business_priority': BusinessPriority.LOW.value,
                    'is_junk': True,
                    'analysis_time_ms': int((time.time() - col_start_time) * 1000)
                }
        
        # Calculate global missing data
        total_cells = summary['row_count'] * summary['col_count']
        if total_cells > 0:
            summary["global_missing_pct"] = float(df.isnull().sum().sum() / total_cells)
    
    def _analyze_single_column(self, df: pd.DataFrame, col: str, total_rows: int,
                              max_top_values: int) -> ColumnSummary:
        """Analyze a single column with professional metrics."""
        series = df[col]
        
        # Basic stats
        null_count = int(series.isnull().sum())
        null_pct = float(null_count / max(1, total_rows))
        non_null = series.dropna()
        unique_count = int(series.nunique(dropna=True))
        
        # Top values
        try:
            if len(non_null) > 0:
                if is_datetime64_any_dtype(series):
                    top_vals = non_null.astype(str).value_counts().head(max_top_values).to_dict()
                    sample_vals = non_null.astype(str).head(5).tolist()
                else:
                    top_vals = non_null.value_counts().head(max_top_values).to_dict()
                    sample_vals = non_null.head(5).tolist()
            else:
                top_vals = {}
                sample_vals = []
        except Exception:
            top_vals = {}
            sample_vals = non_null.head(5).tolist() if len(non_null) > 0 else []
        
        # Infer semantic type
        semantic_type = self._infer_semantic_type(df, col)
        
        # Determine business priority
        business_priority = self._calculate_business_priority(col, semantic_type, null_pct)
        
        # Check if junk column
        is_junk = self._is_junk_column(col, semantic_type, unique_count, total_rows)
        
        # Create summary
        col_summary = ColumnSummary(
            name=col,
            dtype=str(series.dtype),
            semantic_type=semantic_type,
            null_count=null_count,
            null_pct=null_pct,
            unique_count=unique_count,
            top_values=top_vals,
            sample_values=sample_vals,
            business_priority=business_priority,
            is_junk=is_junk,
        )
        
        # Add numeric stats if applicable
        if semantic_type in [SemanticType.NUMERIC.value, SemanticType.CURRENCY.value, SemanticType.PERCENTAGE.value]:
            self._add_numeric_analysis(col_summary, non_null)
        
        # Detect anomalies
        if self.config.get('feature_flags', {}).get('anomaly_detection', True):
            self._detect_anomalies(col_summary, non_null)
        
        return col_summary
    
    def _infer_semantic_type(self, df: pd.DataFrame, col: str) -> str:
        """Professional semantic type inference with caching."""
        # Use caching for performance
        cache_key = f"{col}_{df[col].dtype}_{len(df)}"
        
        # Check cache
        if hasattr(self, '_semantic_type_cache') and cache_key in self._semantic_type_cache:
            return self._semantic_type_cache[cache_key]
        
        series = df[col]
        semantic_type = self._infer_semantic_type_impl(series, col)
        
        # Update cache
        if not hasattr(self, '_semantic_type_cache'):
            self._semantic_type_cache = {}
        
        # Limit cache size
        if len(self._semantic_type_cache) > 100:
            self._semantic_type_cache.pop(next(iter(self._semantic_type_cache)))
        
        self._semantic_type_cache[cache_key] = semantic_type
        return semantic_type
    
    def _infer_semantic_type_impl(self, series: pd.Series, col_name: str) -> str:
        """Implementation of semantic type inference."""
        col_lower = col_name.lower()
        
        # Check dtype first
        if is_datetime64_any_dtype(series):
            return SemanticType.DATETIME.value
        
        if is_numeric_dtype(series):
            non_null = series.dropna()
            if len(non_null) == 0:
                return SemanticType.NUMERIC.value
            
            numeric_vals = pd.to_numeric(non_null, errors='coerce').dropna()
            if len(numeric_vals) == 0:
                return SemanticType.NUMERIC.value
            
            # Check for percentage patterns
            in_0_100 = ((numeric_vals >= 0) & (numeric_vals <= 100)).mean()
            in_0_1 = ((numeric_vals >= 0) & (numeric_vals <= 1)).mean()
            
            percent_indicators = ['pct', 'percent', 'percentage', 'rate', 'ratio']
            
            if (in_0_100 > 0.8 and in_0_100 > in_0_1) or any(indicator in col_lower for indicator in percent_indicators):
                return SemanticType.PERCENTAGE.value
            
            # Currency detection
            if numeric_vals.mean() > 10:
                str_vals = numeric_vals.astype(str)
                decimal_parts = str_vals.str.split('.').str[-1]
                if len(decimal_parts) > 0:
                    two_decimals = decimal_parts[decimal_parts.str.len() == 2]
                    if len(two_decimals) / len(decimal_parts) > 0.5:
                        return SemanticType.CURRENCY.value
            
            return SemanticType.NUMERIC.value
        
        if is_string_dtype(series) or is_categorical_dtype(series):
            non_null = series.dropna().astype(str)
            if len(non_null) == 0:
                return SemanticType.CATEGORICAL.value
            
            # Check for stage/funnel columns
            stage_indicators = ['stage', 'step', 'funnel', 'status', 'phase', 'level', 'progress', 'state']
            if any(indicator in col_lower for indicator in stage_indicators):
                return SemanticType.STAGE.value
            
            # Boolean detection
            unique_vals = non_null.unique()
            if len(unique_vals) <= 4:
                bool_patterns = [
                    r'^(true|false|yes|no|1|0|t|f|y|n)$',
                    r'^(active|inactive|enabled|disabled|on|off)$',
                    r'^(success|failure|pass|fail|complete|incomplete)$',
                    r'^(win|loss|won|lost|approved|rejected)$'
                ]
                
                for pattern in bool_patterns:
                    pattern_re = re.compile(pattern, re.IGNORECASE)
                    if all(pattern_re.match(str(v).strip()) for v in unique_vals):
                        return SemanticType.BOOLEAN.value
            
            # Check for datetime strings
            if len(non_null) > 0:
                sample = non_null.head(100)
                date_patterns = [
                    r'\d{4}-\d{2}-\d{2}',
                    r'\d{2}/\d{2}/\d{4}',
                    r'\d{4}/\d{2}/\d{2}',
                    r'\d{2}-\d{2}-\d{4}',
                ]
                
                date_count = 0
                for val in sample:
                    if any(re.search(pattern, str(val)) for pattern in date_patterns):
                        date_count += 1
                
                if date_count / len(sample) > 0.7:
                    return SemanticType.DATETIME.value
            
            return SemanticType.CATEGORICAL.value
        
        if is_bool_dtype(series):
            return SemanticType.BOOLEAN.value
        
        # ID detection
        if 'id' in col_lower:# and unique_count / len(series) > 0.9:
            return SemanticType.ID.value
        
        return SemanticType.UNKNOWN.value
    
    def _calculate_business_priority(self, col_name: str, semantic_type: str, null_pct: float) -> str:
        """Calculate business priority with enhanced scoring."""
        col_lower = col_name.lower()
        score = 0
        
        # Name-based scoring
        for priority_level, terms in BUSINESS_PRIORITY_TERMS.items():
            for term, weight in terms.items():
                if term == col_lower or f"_{term}" in col_lower or f"{term}_" in col_lower:
                    if priority_level == BusinessPriority.HIGH:
                        score += weight
                    elif priority_level == BusinessPriority.MEDIUM:
                        score += weight
        
        # Semantic type bonus
        if semantic_type in [SemanticType.CURRENCY.value, SemanticType.PERCENTAGE.value, SemanticType.NUMERIC.value]:
            score += 1
        elif semantic_type == SemanticType.DATETIME.value:
            score += 1
        
        # Data quality penalty
        if null_pct > 0.3:
            score -= 2
        elif null_pct > 0.1:
            score -= 1
        
        # Determine priority
        if score >= 3:
            return BusinessPriority.HIGH.value
        elif score >= 1:
            return BusinessPriority.MEDIUM.value
        else:
            return BusinessPriority.LOW.value
    
    def _is_junk_column(self, col_name: str, semantic_type: str, unique_count: int, total_rows: int) -> bool:
        """Identify junk columns (IDs, metadata, etc.)."""
        col_lower = col_name.lower()
        
        # Explicit junk patterns
        junk_patterns = [
            r'^id$', r'_id$', r'^uuid$', r'^guid$', r'^pk_', r'^fk_',
            r'^rowid$', r'^index$', r'^key$', r'^hash$', r'^md5$',
            r'^token$', r'^secret$', r'^password$', r'^ssn$', r'^pin$',
            r'^version$', r'^created$', r'^updated$', r'^deleted$',
        ]
        
        for pattern in junk_patterns:
            if re.search(pattern, col_lower):
                return True
        
        # High unique ratio + non-business name
        unique_ratio = unique_count / max(1, total_rows)
        if unique_ratio > 0.9 and semantic_type != SemanticType.DATETIME.value:
            # Check if it's actually a business column
            business_terms = list(BUSINESS_PRIORITY_TERMS[BusinessPriority.HIGH].keys()) + \
                           list(BUSINESS_PRIORITY_TERMS[BusinessPriority.MEDIUM].keys())
            if not any(term in col_lower for term in business_terms):
                return True
        
        return False
    
    def _add_numeric_analysis(self, col_summary: ColumnSummary, non_null_series: pd.Series) -> None:
        """Add professional numeric analysis with robust error handling."""
        try:
            numeric_series = pd.to_numeric(non_null_series, errors='coerce').dropna()
            
            # Set default outlier score first
            col_summary.outlier_score = 0.0
            
            if len(numeric_series) < 2:
                return
            
            # Basic statistics
            stats = {
                "count": int(numeric_series.count()),
                "mean": float(numeric_series.mean()),
                "std": float(numeric_series.std()),
                "min": float(numeric_series.min()),
                "25%": float(numeric_series.quantile(0.25)),
                "50%": float(numeric_series.quantile(0.5)),
                "75%": float(numeric_series.quantile(0.75)),
                "max": float(numeric_series.max()),
            }
            
            # Advanced statistics
            if len(numeric_series) > 2:
                stats["skew"] = float(numeric_series.skew())
            if len(numeric_series) > 3:
                stats["kurtosis"] = float(numeric_series.kurtosis())
            
            # Clean NaN values
            cleaned_stats = {}
            for k, v in stats.items():
                if pd.isna(v):
                    cleaned_stats[k] = None
                else:
                    cleaned_stats[k] = v
            
            col_summary.numeric_stats = cleaned_stats
            
            # Outlier detection
            q1 = cleaned_stats.get('25%')
            q3 = cleaned_stats.get('75%')
            
            if q1 is None or q3 is None:
                return
                
            iqr = max(1e-12, q3 - q1)
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            outliers = numeric_series[(numeric_series < lower_bound) | (numeric_series > upper_bound)]
            outlier_pct = len(outliers) / len(numeric_series)
            
            col_summary.outlier_score = float(outlier_pct)
            
            # Flag significant anomalies
            if 0.01 < outlier_pct < self.config.get('outlier_threshold', 0.05):
                col_summary.anomaly_flag = True
                col_summary.anomaly_reason = f"{len(outliers)} outliers detected ({outlier_pct:.1%})"
                
        except Exception as e:
            logger.debug(f"Error in numeric analysis for {col_summary.name}: {e}")
            col_summary.outlier_score = 0.0
            col_summary.numeric_stats = {}
    
    def _detect_anomalies(self, col_summary: ColumnSummary, non_null_series: pd.Series) -> None:
        """Detect data anomalies with business context."""
        if col_summary.semantic_type == SemanticType.NUMERIC.value and col_summary.numeric_stats:
            # Check for zero or negative values in positive metrics
            col_lower = col_summary.name.lower()
            positive_metrics = ['revenue', 'sales', 'profit', 'income', 'gmv', 'margin']
            
            if any(term in col_lower for term in positive_metrics):
                numeric_series = pd.to_numeric(non_null_series, errors='coerce').dropna()
                negative_pct = (numeric_series < 0).mean()
                if negative_pct > 0.1:
                    col_summary.anomaly_flag = True
                    if not col_summary.anomaly_reason:
                        col_summary.anomaly_reason = f"Unexpected negative values ({negative_pct:.1%})"
                    else:
                        col_summary.anomaly_reason += f"; Negative values ({negative_pct:.1%})"
    
    def _calculate_top_correlations(self, df: pd.DataFrame, numeric_cols: List[str],
                                   max_pairs: int = 8) -> List[Dict]:
        """Calculate top correlations with error handling and business context."""
        if len(numeric_cols) < 2:
            return []
        
        try:
            numeric_df = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
            corr_matrix = numeric_df.corr(method='pearson')
            
            pairs = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i + 1, len(corr_matrix.columns)):
                    col1 = corr_matrix.columns[i]
                    col2 = corr_matrix.columns[j]
                    corr = corr_matrix.iloc[i, j]
                    
                    if pd.isna(corr):
                        continue
                    
                    # Check if either column has business importance
                    col1_lower = col1.lower()
                    col2_lower = col2.lower()
                    
                    business_score = 0
                    business_high = self.config.get('business_priority_terms', {}).get(BusinessPriority.HIGH.value, [])
                    
                    if any(term in col1_lower for term in business_high):
                        business_score += 1
                    if any(term in col2_lower for term in business_high):
                        business_score += 1
                    
                    pairs.append({
                        "x": col1,
                        "y": col2,
                        "corr": float(corr),
                        "abs_corr": abs(float(corr)),
                        "business_relevance": business_score
                    })
            
            # Sort by business relevance and correlation strength
            pairs.sort(key=lambda x: (x["business_relevance"], x["abs_corr"]), reverse=True)
            
            return pairs[:max_pairs]
            
        except Exception as e:
            logger.warning(f"Error calculating correlations: {e}")
            return []
    
    def _detect_hero_metric(self, metadata: Dict[str, Any]) -> Optional[str]:
        """Detect the most important business metric (hero metric)."""
        candidates = []
        
        for col, info in metadata['columns'].items():
            # Skip junk columns
            if info.get('is_junk', False):
                continue
            
            score = 0
            
            # Business priority
            if info.get('business_priority') == BusinessPriority.HIGH.value:
                score += 3
            elif info.get('business_priority') == BusinessPriority.MEDIUM.value:
                score += 1
            
            # Semantic type suitability
            if info.get('semantic_type') in [SemanticType.NUMERIC.value, SemanticType.CURRENCY.value, SemanticType.PERCENTAGE.value]:
                score += 2
            
            # Data quality
            if info.get('null_pct', 1.0) < 0.05:
                score += 1
            
            # Good variation (not constant, not all unique)
            unique_ratio = info.get('unique_count', 0) / max(1, metadata['row_count'])
            if 0.01 < unique_ratio < 0.8:
                score += 1
            
            # Business term in name
            col_lower = col.lower()
            if any(term in col_lower for term in self.config.get('business_priority_terms', {}).get(BusinessPriority.HIGH.value, [])):
                score += 2
            
            if score >= 5:
                candidates.append((score, col))
        
        if not candidates:
            return None
        
        # Return highest scoring
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]
    
    def _select_columns_for_analysis(self, df: pd.DataFrame) -> List[str]:
        """Intelligently select columns for analysis when dataset is too wide."""
        columns = list(df.columns)
        
        if len(columns) <= self.config.get('max_columns_for_flood', 80):
            return columns
        
        # Score columns for selection
        scored_columns = []
        business_terms = self.config.get('business_priority_terms', {})
        
        for col in columns:
            score = 0
            
            # Business priority scoring
            col_lower = col.lower()
            if any(term in col_lower for term in business_terms.get(BusinessPriority.HIGH.value, [])):
                score += 3
            elif any(term in col_lower for term in business_terms.get(BusinessPriority.MEDIUM.value, [])):
                score += 1
            
            # Data type scoring (prefer analyzable types)
            if is_numeric_dtype(df[col]):
                score += 2
            elif is_datetime64_any_dtype(df[col]):
                score += 2
            elif df[col].dtype == 'object' or is_categorical_dtype(df[col]):
                score += 1
            
            # Avoid ID columns
            if re.search(r'^id$|_id$|^uuid$|^guid$', col_lower):
                score -= 3
            
            # Prefer shorter column names (often more meaningful)
            if len(col) < 30:
                score += 1
            
            scored_columns.append((score, col))
        
        # Sort by score (descending) and select top
        scored_columns.sort(key=lambda x: x[0], reverse=True)
        selected = [col for _, col in scored_columns[:self.config.get('max_columns_for_flood', 80)]]
        
        logger.info(f"Selected {len(selected)} out of {len(columns)} columns for analysis")
        return selected
    
    def _compute_dataset_hash(self, df: pd.DataFrame, sample_size: int = 2000) -> str:
        """Compute stable hash of dataset for caching with intelligent sampling."""
        if df.empty:
            return "empty"
        
        # Sample data intelligently
        if len(df) > sample_size:
            try:
                # Try to find a categorical column for stratification
                cat_cols = [col for col in df.columns 
                           if is_string_dtype(df[col]) or is_categorical_dtype(df[col])]
                if cat_cols and df[cat_cols[0]].nunique() < 50:
                    sample = df.groupby(cat_cols[0], group_keys=False).apply(
                        lambda x: x.sample(n=min(len(x), sample_size // df[cat_cols[0]].nunique()), 
                                         random_state=42)
                    ).sample(n=min(sample_size, len(df)), random_state=42)
                else:
                    sample = df.sample(n=min(sample_size, len(df)), random_state=42)
            except Exception:
                sample = df.sample(n=min(sample_size, len(df)), random_state=42)
        else:
            sample = df
        
        # Compute hash from structure and sample
        structure = f"{df.shape}|{','.join(sorted(df.columns))}"
        content = str(sample.values.tobytes())
        combined = f"{structure}|{content}"
        
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    def _generate_enhanced_executive_summary(self, metadata: Dict[str, Any]) -> str:
        """Generate executive summary with hero insight."""
        lines = []
        
        # Basic dataset info
        lines.append(f"**Dataset**: {metadata['row_count']:,} records × {metadata['col_count']} columns")
        
        # Add hero insight if available
        hero = metadata.get('hero_insight')
        if hero:
            insight_text = hero.get('body', '').replace('🚨', '').replace('🎯', '').replace('💡', '')
            lines.append(f"**Key Insight**: {insight_text[:200]}")
        
        # Add data quality note
        missing_pct = metadata.get('global_missing_pct', 0)
        if missing_pct > 0.05:
            lines.append(f"⚠️ **Data Quality**: {missing_pct:.1%} missing values")
        
        # Add business metrics count
        business_cols = metadata.get('business_priority_columns', [])
        if business_cols:
            lines.append(f"**Business Metrics**: {len(business_cols)} identified")
        
        # Add insight count
        insights = metadata.get('prioritized_insights', [])
        if insights:
            critical_insights = sum(1 for i in insights if i.get('type') in [InsightType.DEPENDENCY_RISK.value, InsightType.CRITICAL_RISK.value])
            if critical_insights > 0:
                lines.append(f"🚨 **Critical Findings**: {critical_insights} requiring immediate attention")
        
        return " | ".join(lines)

# ============================================================================
# ENHANCED CHART RECOMMENDER
# ============================================================================

class EchoChartRecommender:
    """Production-grade chart recommender with insight-driven prioritization."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # Deep copy default config
        self.config = copy.deepcopy(DEFAULT_CONFIG)
        if config:
            # Safely merge configs
            self._safe_merge_config(config)
        
        # Performance cache
        self._chart_cache = {}
        self._insight_cache = {}
        self._last_cache_clean = time.time()
        
        # Performance metrics
        self.metrics = {
            'candidates_generated': 0,
            'candidates_filtered': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'generation_time_ms': 0,
            'insight_boosts_applied': 0,
            'dynamic_limits_applied': 0,
        }
    
    def _safe_merge_config(self, config: Dict[str, Any]) -> None:
        """Safely merge configuration with defaults."""
        for key, value in config.items():
            if key == 'feature_flags' and isinstance(value, dict):
                # Merge feature flags
                self.config.setdefault('feature_flags', {}).update(value)
            elif isinstance(value, dict) and key in self.config and isinstance(self.config[key], dict):
                # Merge nested dictionaries
                self.config[key].update(value)
            else:
                # Replace or add top-level key
                self.config[key] = value
    
    def recommend_charts(self, df: pd.DataFrame, prompt: Optional[str] = None, 
                        max_suggestions: int = 8) -> List[Dict[str, Any]]:
        """Generate professional chart recommendations with insight-driven prioritization."""
        start_time = time.time()
        
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(df, prompt, max_suggestions)
            
            # Check cache (with TTL)
            if self._check_cache(cache_key):
                self.metrics['cache_hits'] += 1
                logger.info(f"Cache hit for {cache_key}")
                return self._chart_cache[cache_key]['result']
            
            self.metrics['cache_misses'] += 1
            
            # Sample data for analysis
            sample_df = self._sample_data(df)
            
            # Get metadata WITH insights
            analyzer = DatasetAnalyzer(self.config)
            metadata = analyzer.analyze(sample_df)
            
            # Generate candidate stream with early cutoff
            candidates = []
            candidate_count = 0
            
            for candidate in self._generate_candidate_stream(sample_df, metadata, prompt):
                candidate_count += 1
                
                # Score candidate with insight boosting
                scored_candidate = self._score_candidate_with_insights(candidate, sample_df, metadata, prompt)
                
                # Filter by confidence threshold
                if scored_candidate['confidence'] >= self.config.get('confidence_emit', 0.25):
                    candidates.append(scored_candidate)
                
                # Early cutoff to prevent memory explosion
                if candidate_count >= self.config.get('max_chart_candidates', 120):
                    logger.info(f"Early cutoff at {candidate_count} candidates")
                    break
            
            self.metrics['candidates_generated'] = candidate_count
            self.metrics['candidates_filtered'] = len(candidates)
            
            # Rank and select top candidates with insight priority
            ranked_candidates = self._rank_candidates_with_insights(candidates, metadata, max_suggestions)
            
            # Enhance with professional narratives and insights
            suggestions = []
            for candidate in ranked_candidates:
                suggestion = self._build_final_suggestion_with_insights(candidate, sample_df, metadata)
                suggestions.append(suggestion)
            
            # Cache result
            self._cache_result(cache_key, suggestions, metadata)
            
            # Update metrics
            self.metrics['generation_time_ms'] = int((time.time() - start_time) * 1000)
            
            logger.info(f"Generated {len(suggestions)} suggestions from {candidate_count} candidates in {self.metrics['generation_time_ms']}ms")
            logger.info(f"Insight boosts applied: {self.metrics['insight_boosts_applied']}")
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error in recommend_charts: {e}", exc_info=True)
            return []
    
    def _score_candidate_with_insights(self, candidate: Dict[str, Any], df: pd.DataFrame, 
                                      metadata: Dict[str, Any], prompt: Optional[str]) -> Dict[str, Any]:
        """Score candidate with insight-based boosting."""
        # Get base score
        base_score = self._calculate_base_score(candidate, df, metadata, prompt)
        
        # Calculate insight boost
        insight_boost = 0.0
        if self.config.get('feature_flags', {}).get('insight_boosting', False):
            insight_boost = self._calculate_insight_boost(candidate, metadata)
            if insight_boost > 0:
                self.metrics['insight_boosts_applied'] += 1
        
        # Apply boost
        final_confidence = min(0.99, base_score['confidence'] + insight_boost)
        
        return {
            **candidate,
            'confidence': final_confidence,
            'base_confidence': base_score['confidence'],
            'insight_boost': insight_boost,
            'scoring_breakdown': {
                **base_score.get('scoring_breakdown', {}),
                'insight_boost': round(insight_boost, 3)
            }
        }
    
    def _calculate_insight_boost(self, candidate: Dict[str, Any], metadata: Dict[str, Any]) -> float:
        """Boost charts that visualize key insights."""
        boost = 0.0
        columns = candidate.get('columns', [])
        chart_type = candidate.get('chart_type', '')
        
        # Get prioritized insights
        insights = metadata.get('prioritized_insights', [])
        
        for insight in insights:
            insight_cols = insight.get('columns', [])
            if not insight_cols:
                continue
            
            # EXACT MATCH: Chart visualizes THE insight
            if set(insight_cols).issubset(set(columns)):
                insight_type = insight.get('type', '')
                insight_priority = insight.get('priority', 5.0)
                
                # High boost for risk insights
                if insight_type in [InsightType.DEPENDENCY_RISK.value, InsightType.CRITICAL_RISK.value]:
                    boost += 0.35
                elif insight_type in [InsightType.STRONG_PARETO.value, InsightType.GOLDEN_PERIOD.value, InsightType.MISSING_DATA_OPPORTUNITY.value]:
                    boost += 0.25
                elif insight_priority >= 7.0:
                    boost += 0.20
                else:
                    boost += 0.15
            
            # PARTIAL MATCH: Chart shows part of insight
            elif any(col in columns for col in insight_cols):
                if insight.get('priority', 0) >= 7.0:
                    boost += 0.12
                else:
                    boost += 0.08
        
        # SPECIAL BOOSTS BY CHART TYPE
        if chart_type == ChartType.LINE.value:
            # Boost for time insights
            for insight in metadata.get('time_patterns', []):
                if insight.get('metric') in columns:
                    boost += 0.15
                    break
        
        elif chart_type in [ChartType.BAR.value, ChartType.PIE.value]:
            # Boost for Pareto insights
            for insight in metadata.get('pareto_patterns', []):
                if (insight.get('metric') in columns and 
                    insight.get('dimension') in columns):
                    boost += 0.18
                    break
        
        elif chart_type == ChartType.SCATTER.value:
            # Boost for relationship insights
            for insight in metadata.get('relationship_insights', []):
                if (insight.get('metric') in columns and 
                    insight.get('category') in columns):
                    boost += 0.15
                    break
        
        return min(0.4, boost)  # Cap at 40% boost
    
    def _rank_candidates_with_insights(self, candidates: List[Dict], metadata: Dict[str, Any], 
                                      max_count: int) -> List[Dict]:
        """Rank candidates with insight priority and diversity."""
        if not candidates:
            return []
        
        # Sort by confidence (with insight boost)
        candidates.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Ensure insight visualization diversity
        selected = []
        chart_type_counts = defaultdict(int)
        used_insights = set()
        
        max_per_type = {
            ChartType.BAR.value: 3,
            ChartType.LINE.value: 2,
            ChartType.HISTOGRAM.value: 2,
            ChartType.PIE.value: 1,
            ChartType.SCATTER.value: 2,
            ChartType.BOX.value: 1,
        }
        
        for candidate in candidates:
            if len(selected) >= max_count:
                break
            
            chart_type = candidate['chart_type']
            
            # Check chart type limit
            if chart_type_counts.get(chart_type, 0) >= max_per_type.get(chart_type, 1):
                continue
            
            # Check if this chart visualizes a new insight
            columns = set(candidate.get('columns', []))
            new_insight = False
            
            for insight in metadata.get('prioritized_insights', []):
                insight_cols = set(insight.get('columns', []))
                insight_id = insight.get('id', '')
                
                if insight_cols.issubset(columns) and insight_id not in used_insights:
                    new_insight = True
                    used_insights.add(insight_id)
                    break
            
            # If we already have enough charts and this doesn't show a new insight, skip
            if len(selected) > 3 and not new_insight:
                continue
            
            selected.append(candidate)
            chart_type_counts[chart_type] = chart_type_counts.get(chart_type, 0) + 1
        
        # Fill remaining slots with high-confidence candidates
        if len(selected) < max_count:
            remaining = [c for c in candidates if c not in selected]
            remaining.sort(key=lambda x: x['confidence'], reverse=True)
            selected.extend(remaining[:max_count - len(selected)])
        
        return selected
    
    def _build_final_suggestion_with_insights(self, candidate: Dict[str, Any], df: pd.DataFrame, 
                                             metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Build final chart suggestion with insight context."""
        # Import narratives module
        try:
            from .narratives import (
                generate_chart_title, 
                generate_chart_description, 
                generate_one_liner,
                generate_insightful_title
            )
            
            columns = candidate['columns']
            chart_type = candidate['chart_type']
            
            # Use enhanced title generation
            try:
                title = generate_insightful_title(chart_type, columns, df, metadata)
            except Exception as e:
                logger.debug(f"Insightful title generation failed: {e}, using standard title")
                title = generate_chart_title(chart_type, columns, metadata, df)
            
            description = generate_chart_description(chart_type, columns, df, metadata)
            one_liner = generate_one_liner(chart_type, columns, df, metadata)
            
        except ImportError:
            # Fallback if narratives module is not available
            logger.warning("Narratives module not available, using fallback titles")
            columns = candidate['columns']
            chart_type = candidate['chart_type']
            
            title = f"{chart_type.title()} Chart"
            if columns:
                title = f"{chart_type.title()} of {', '.join(columns[:2])}"
            
            description = f"Professional {chart_type} visualization"
            one_liner = f"{chart_type.replace('_', ' ').title()} analysis"
        
        # Generate safe Plotly code
        code = self._generate_safe_plotly_code(df, chart_type, columns, title)
        
        # Build base suggestion
        suggestion = {
            'chart_type': chart_type,
            'title': title,
            'description': description,
            'one_liner': one_liner,
            'confidence': candidate['confidence'],
            'code': code,
            'id': f"chart_{uuid.uuid4().hex[:8]}",
            'ai_generated': False,
            'consultant_grade': True,
            'business_impact': candidate.get('business_impact', 1.0),
            'insight_boost': candidate.get('insight_boost', 0.0),
            'generated_at': time.time(),
            'scoring_breakdown': candidate.get('scoring_breakdown', {}),
        }
        
        # Add insight context
        matching_insights = []
        for insight in metadata.get('prioritized_insights', []):
            insight_cols = insight.get('columns', [])
            if set(insight_cols).issubset(set(columns)):
                matching_insights.append(insight)
            elif any(col in columns for col in insight_cols):
                matching_insights.append(insight)
        
        if matching_insights:
            top_insight = matching_insights[0]
            suggestion['insight_context'] = {
                'has_insight': True,
                'primary_insight': top_insight.get('title'),
                'insight_body': top_insight.get('body'),
                'insight_type': top_insight.get('type'),
                'action': top_insight.get('action', '')
            }
            
            # Enhance title for insight charts
            if top_insight.get('type') in [InsightType.DEPENDENCY_RISK.value, InsightType.CRITICAL_RISK.value]:
                suggestion['title'] = f"🚨 {suggestion['title']}"
            elif top_insight.get('type') == InsightType.STRONG_PARETO.value:
                suggestion['title'] = f"🎯 {suggestion['title']} (80/20 Rule)"
            elif top_insight.get('type') == InsightType.GOLDEN_PERIOD.value:
                suggestion['title'] = f"⭐ {suggestion['title']} (Peak Performance)"
            elif top_insight.get('type') == InsightType.MISSING_DATA_OPPORTUNITY.value:
                suggestion['title'] = f"💡 {suggestion['title']} (Data Opportunity)"
        else:
            suggestion['insight_context'] = {
                'has_insight': False,
                'primary_insight': None
            }
        
        # Add chart-specific metadata
        if chart_type == ChartType.PIE.value:
            suggestion['names_col'] = columns[0] if len(columns) > 0 else None
            suggestion['values_col'] = columns[1] if len(columns) > 1 else None
        elif chart_type == ChartType.LINE.value:
            suggestion['date_col'] = columns[0] if len(columns) > 0 else None
            suggestion['value_col'] = columns[1] if len(columns) > 1 else None
        else:
            suggestion['x'] = columns[0] if len(columns) > 0 else None
            suggestion['y'] = columns[1] if len(columns) > 1 else None
        
        return suggestion
    
    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    
    def _generate_cache_key(self, df: pd.DataFrame, prompt: Optional[str], max_suggestions: int) -> str:
        """Generate stable cache key."""
        analyzer = DatasetAnalyzer(self.config)
        data_hash = analyzer._compute_dataset_hash(df)
        prompt_hash = hashlib.md5(str(prompt or "").encode()).hexdigest()[:8]
        return f"{data_hash}_{prompt_hash}_{max_suggestions}"
    
    def _check_cache(self, cache_key: str, ttl_seconds: int = 300) -> bool:
        """Check cache with TTL."""
        if time.time() - self._last_cache_clean > 60:
            self._clean_cache()
            self._last_cache_clean = time.time()
        
        if cache_key in self._chart_cache:
            entry = self._chart_cache[cache_key]
            if time.time() - entry['timestamp'] < ttl_seconds:
                return True
            else:
                del self._chart_cache[cache_key]
        
        return False
    
    def _clean_cache(self):
        """Clean cache to prevent memory issues."""
        current_time = time.time()
        max_age = 600
        
        keys_to_remove = []
        for key, entry in self._chart_cache.items():
            if current_time - entry['timestamp'] > max_age:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._chart_cache[key]
        
        cache_size = self.config.get('cache_size', 50)
        if len(self._chart_cache) > cache_size:
            entries = sorted(self._chart_cache.items(), key=lambda x: x[1]['timestamp'])
            for key, _ in entries[:len(entries) - cache_size]:
                del self._chart_cache[key]
    
    def _cache_result(self, cache_key: str, result: List[Dict], metadata: Dict[str, Any]):
        """Cache result with metadata."""
        self._chart_cache[cache_key] = {
            'result': result,
            'metadata': metadata,
            'timestamp': time.time(),
            'size': len(result),
        }
    
    def _sample_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Intelligently sample data for analysis."""
        sample_limit = self.config.get('sample_limit', 10000)
        
        if len(df) <= sample_limit:
            return df.copy()
        
        # For large datasets, use stratified sampling if possible
        categorical_cols = [
            col for col in df.columns
            if is_string_dtype(df[col]) or is_categorical_dtype(df[col])
        ]
        
        if categorical_cols:
            strat_col = categorical_cols[0]
            if df[strat_col].nunique() <= 50:
                try:
                    return df.groupby(strat_col, group_keys=False).apply(
                        lambda x: x.sample(n=min(len(x), sample_limit // df[strat_col].nunique()), 
                                         random_state=42)
                    ).sample(n=min(sample_limit, len(df)), random_state=42)
                except Exception:
                    pass
        
        return df.sample(n=min(sample_limit, len(df)), random_state=42)
    
    def _generate_candidate_stream(self, df: pd.DataFrame, metadata: Dict[str, Any], 
                                  prompt: Optional[str]) -> Generator[Dict[str, Any], None, None]:
        """Generate chart candidates with dynamic limits."""
        # Filter out junk columns
        valid_cols = [
            col for col in df.columns
            if not metadata['columns'][col].get('is_junk', False)
        ]
        
        if not valid_cols:
            return
        
        # Categorize columns by type and business priority
        numeric_cols = self._prioritize_columns([
            col for col in valid_cols
            if metadata['columns'][col]['semantic_type'] in [SemanticType.NUMERIC.value, SemanticType.CURRENCY.value, SemanticType.PERCENTAGE.value]
        ])
        
        categorical_cols = self._prioritize_columns([
            col for col in valid_cols
            if metadata['columns'][col]['semantic_type'] in [SemanticType.CATEGORICAL.value, SemanticType.BOOLEAN.value, SemanticType.STAGE.value]
        ])
        
        datetime_cols = [
            col for col in valid_cols
            if metadata['columns'][col]['semantic_type'] == SemanticType.DATETIME.value
        ]
        
        # Get flood limits
        flood_limits = {
            ChartType.HISTOGRAM.value: {'columns': 12, 'pairs': 1},
            ChartType.BAR.value: {'columns': 8, 'pairs': 6},
            ChartType.LINE.value: {'columns': 6, 'pairs': 8},
            ChartType.SCATTER.value: {'columns': 4, 'pairs': 4},
            ChartType.PIE.value: {'columns': 8, 'pairs': 1},
            ChartType.BOX.value: {'columns': 3, 'pairs': 3},
        }
        
        # Histograms
        for num_col in numeric_cols[:flood_limits[ChartType.HISTOGRAM.value]['columns']]:
            yield {
                'type': 'single',
                'chart_type': ChartType.HISTOGRAM.value,
                'columns': [num_col],
                'business_impact': self._calculate_business_impact(num_col, metadata),
            }
        
        # Bar charts
        for cat_col in categorical_cols[:flood_limits[ChartType.BAR.value]['columns']]:
            pair_limit = self._get_dynamic_pair_limit(ChartType.BAR.value, cat_col, df, metadata)
            for num_col in numeric_cols[:pair_limit]:
                yield {
                    'type': 'pair',
                    'chart_type': ChartType.BAR.value,
                    'columns': [cat_col, num_col],
                    'business_impact': self._calculate_business_impact(cat_col, metadata) * 
                                     self._calculate_business_impact(num_col, metadata),
                }
        
        # Line charts
        for dt_col in datetime_cols[:flood_limits[ChartType.LINE.value]['columns']]:
            for num_col in numeric_cols[:flood_limits[ChartType.LINE.value]['pairs']]:
                yield {
                    'type': 'pair',
                    'chart_type': ChartType.LINE.value,
                    'columns': [dt_col, num_col],
                    'business_impact': self._calculate_business_impact(num_col, metadata),
                }
        
        # Scatter plots
        scatter_count = 0
        for i, col1 in enumerate(numeric_cols[:flood_limits[ChartType.SCATTER.value]['columns']]):
            for col2 in numeric_cols[i+1:i+flood_limits[ChartType.SCATTER.value]['pairs']]:
                if scatter_count < 3:
                    yield {
                        'type': 'pair',
                        'chart_type': ChartType.SCATTER.value,
                        'columns': [col1, col2],
                        'business_impact': self._calculate_business_impact(col1, metadata) * 
                                         self._calculate_business_impact(col2, metadata),
                    }
                    scatter_count += 1
        
        # Pie charts
        for cat_col in categorical_cols[:flood_limits[ChartType.PIE.value]['columns']]:
            unique_count = metadata['columns'][cat_col]['unique_count']
            if unique_count <= self.config.get('max_categories_pie', 8):
                yield {
                    'type': 'single',
                    'chart_type': ChartType.PIE.value,
                    'columns': [cat_col],
                    'business_impact': self._calculate_business_impact(cat_col, metadata),
                }
    
    def _calculate_base_score(self, candidate: Dict[str, Any], df: pd.DataFrame, 
                             metadata: Dict[str, Any], prompt: Optional[str]) -> Dict[str, Any]:
        """Calculate base score without insight boost."""
        columns = candidate['columns']
        chart_type = candidate['chart_type']
        
        if candidate['type'] == 'single':
            base_score = self._score_single_column(df, columns[0], chart_type, metadata)
        else:
            base_score = self._score_column_pair(df, columns[0], columns[1], chart_type, metadata)
        
        # Business impact multiplier
        business_impact = candidate.get('business_impact', 1.0)
        
        # Chart type preference multiplier
        chart_multiplier = self._get_chart_multiplier(chart_type)
        
        # Intent boost from user prompt
        intent_boost = self._calculate_intent_boost(prompt, chart_type, columns, df)
        
        # Calculate weighted score
        weighted_score = base_score * business_impact * chart_multiplier
        confidence = min(0.99, max(0.1, weighted_score + intent_boost))
        
        scoring_breakdown = {
            'base_score': round(base_score, 3),
            'business_impact': round(business_impact, 3),
            'chart_multiplier': round(chart_multiplier, 3),
            'intent_boost': round(intent_boost, 3),
            'weighted_score': round(weighted_score, 3),
        }
        
        return {
            'confidence': confidence,
            'scoring_breakdown': scoring_breakdown
        }
    
    def _calculate_business_impact(self, column_name: str, metadata: Dict[str, Any]) -> float:
        """Calculate business impact with data-driven scoring."""
        col_lower = column_name.lower()
        base_score = 1.0
        
        # String matching base
        business_terms = self.config.get('business_priority_terms', {})
        
        for term in business_terms.get(BusinessPriority.HIGH.value, []):
            if term == col_lower or f"_{term}" in col_lower or f"{term}_" in col_lower:
                base_score = 1.5
                break
        
        if base_score == 1.0:
            for term in business_terms.get(BusinessPriority.HIGH.value, []):
                if term in col_lower:
                    base_score = 1.3
                    break
        
        if base_score == 1.0:
            for term in business_terms.get(BusinessPriority.MEDIUM.value, []):
                if term in col_lower:
                    base_score = 1.2
                    break
        
        # Data-driven adjustments
        if column_name in metadata['columns']:
            col_meta = metadata['columns'][column_name]
            
            # Constant data penalty
            unique_count = col_meta.get('unique_count', 0)
            if unique_count <= 1:
                return 0.3
            
            # High missing data penalty
            null_pct = col_meta.get('null_pct', 0)
            if null_pct is not None:
                if null_pct > 0.3:
                    base_score *= 0.7
                elif null_pct > 0.1:
                    base_score *= 0.9
            
            # Data variation bonus
            if col_meta.get('semantic_type') in [SemanticType.NUMERIC.value, SemanticType.CURRENCY.value, SemanticType.PERCENTAGE.value]:
                stats = col_meta.get('numeric_stats', {})
                if stats and 'mean' in stats and 'std' in stats:
                    mean = stats['mean']
                    std = stats['std']
                    
                    if mean is not None and std is not None and abs(mean) > 1e-9:
                        cv = std / abs(mean)
                        
                        if cv > 0.5:
                            base_score *= 1.3
                        elif cv > 0.2:
                            base_score *= 1.1
                        elif cv < 0.05:
                            base_score *= 0.7
            
            # Unique values adjustment
            unique_ratio = unique_count / max(1, metadata['row_count'])
            if unique_ratio > 0.95 and 'id' in col_lower:
                base_score *= 0.5
        
        return max(0.3, min(2.0, base_score))
    
    def _get_chart_multiplier(self, chart_type: str) -> float:
        """Get chart preference multiplier."""
        business_charts = self.config.get('chart_preference_multipliers', {}).get('business_charts', {})
        analytical_charts = self.config.get('chart_preference_multipliers', {}).get('analytical_charts', {})
        
        if chart_type in business_charts:
            return business_charts[chart_type]
        elif chart_type in analytical_charts:
            return analytical_charts[chart_type]
        return 1.0
    
    def _calculate_intent_boost(self, prompt: Optional[str], chart_type: str, 
                               columns: List[str], df: pd.DataFrame) -> float:
        """Boost score based on user intent from prompt."""
        if not prompt:
            return 0.0
        
        prompt_lower = prompt.lower()
        boost = 0.0
        
        intent_patterns = {
            ChartType.HISTOGRAM.value: [
                (r'\b(distribution|spread|frequency|histogram|range|variation)\b', 0.15),
            ],
            ChartType.BAR.value: [
                (r'\b(compare|comparison|difference|versus|vs\.?|ranking|rank|highest|lowest)\b', 0.15),
            ],
            ChartType.LINE.value: [
                (r'\b(trend|over time|time series|history|timeline|forecast|prediction)\b', 0.15),
            ],
            ChartType.SCATTER.value: [
                (r'\b(relationship|correlation|associated with|related to|impact of|effect of)\b', 0.15),
            ],
            ChartType.PIE.value: [
                (r'\b(composition|breakdown|percentage|share|proportion|part of|makeup)\b', 0.15),
            ],
        }
        
        if chart_type in intent_patterns:
            for pattern, boost_value in intent_patterns[chart_type]:
                if re.search(pattern, prompt_lower):
                    boost += boost_value
                    break
        
        business_terms = {
            'revenue': 0.1, 'sales': 0.1, 'profit': 0.1,
            'cost': 0.08, 'expense': 0.08, 'growth': 0.08,
        }
        
        for term, boost_value in business_terms.items():
            if term in prompt_lower:
                for col in columns:
                    if col and term in col.lower():
                        boost += boost_value
                        break
        
        return min(boost, 0.3)
    
    def _score_single_column(self, df: pd.DataFrame, col: str, chart_type: str, 
                            metadata: Dict[str, Any]) -> float:
        """Score single column for chart type."""
        if col not in metadata['columns']:
            return 0.1
        
        col_meta = metadata['columns'][col]
        
        # Type match
        type_match = self._calculate_type_match(col_meta['semantic_type'], chart_type)
        
        # Data quality
        null_pct = col_meta.get('null_pct', 0)
        data_quality = 1.0 - (null_pct if null_pct is not None else 0)
        
        # Variation
        variation = self._calculate_variation_score(col_meta)
        
        # Apply weights
        weights = self.config.get('weights', DEFAULT_CONFIG['weights'])
        score = (
            weights['type_match'] * type_match +
            weights['data_quality'] * data_quality +
            weights['variation'] * variation
        )
        
        # Penalize too many unique values
        unique_count = col_meta.get('unique_count', 0)
        if unique_count is not None:
            unique_ratio = unique_count / max(1, metadata['row_count'])
            if unique_ratio > 0.9 and chart_type in [ChartType.BAR.value, ChartType.PIE.value]:
                score -= weights['unique_penalty']
        
        return max(0.0, min(1.0, score))
    
    def _score_column_pair(self, df: pd.DataFrame, col1: str, col2: str, 
                          chart_type: str, metadata: Dict[str, Any]) -> float:
        """Score column pair for chart type."""
        score1 = self._score_single_column(df, col1, chart_type, metadata)
        score2 = self._score_single_column(df, col2, chart_type, metadata)
        
        avg_score = (score1 + score2) / 2
        
        # Pair-specific bonuses
        pair_bonus = 0
        
        if chart_type == ChartType.SCATTER.value and self.config.get('feature_flags', {}).get('corr_bonus', True):
            try:
                corr = df[[col1, col2]].corr().iloc[0, 1]
                if not pd.isna(corr):
                    abs_corr = abs(corr)
                    if abs_corr > 0.5:
                        pair_bonus += 0.1 * min(1.0, abs_corr)
            except Exception:
                pass
        
        return max(0.0, min(1.0, avg_score + pair_bonus))
    
    def _calculate_type_match(self, semantic_type: str, chart_type: str) -> float:
        """Calculate how well semantic type matches chart type."""
        type_map = {
            ChartType.HISTOGRAM.value: {
                SemanticType.NUMERIC.value: 1.0,
                SemanticType.CURRENCY.value: 1.0,
                SemanticType.PERCENTAGE.value: 1.0,
                SemanticType.DATETIME.value: 0.6,
                SemanticType.CATEGORICAL.value: 0.2,
                SemanticType.UNKNOWN.value: 0.3
            },
            ChartType.BAR.value: {
                SemanticType.CATEGORICAL.value: 1.0,
                SemanticType.BOOLEAN.value: 1.0,
                SemanticType.STAGE.value: 0.9,
                SemanticType.DATETIME.value: 0.8,
                SemanticType.NUMERIC.value: 0.4,
                SemanticType.UNKNOWN.value: 0.3
            },
            ChartType.LINE.value: {
                SemanticType.DATETIME.value: 1.0,
                SemanticType.NUMERIC.value: 0.9,
                SemanticType.CURRENCY.value: 0.9,
                SemanticType.PERCENTAGE.value: 0.9,
                SemanticType.CATEGORICAL.value: 0.2,
                SemanticType.UNKNOWN.value: 0.3
            },
            ChartType.SCATTER.value: {
                SemanticType.NUMERIC.value: 0.8,
                SemanticType.CURRENCY.value: 0.8,
                SemanticType.PERCENTAGE.value: 0.8,
                SemanticType.DATETIME.value: 0.3,
                SemanticType.CATEGORICAL.value: 0.1,
                SemanticType.UNKNOWN.value: 0.2
            },
            ChartType.PIE.value: {
                SemanticType.CATEGORICAL.value: 1.0,
                SemanticType.BOOLEAN.value: 1.0,
                SemanticType.STAGE.value: 0.9,
                SemanticType.DATETIME.value: 0.3,
                SemanticType.NUMERIC.value: 0.1,
                SemanticType.UNKNOWN.value: 0.2
            },
            ChartType.BOX.value: {
                SemanticType.NUMERIC.value: 0.7,
                SemanticType.CURRENCY.value: 0.7,
                SemanticType.PERCENTAGE.value: 0.7,
                SemanticType.CATEGORICAL.value: 0.2,
                SemanticType.UNKNOWN.value: 0.3
            },
        }
        
        return type_map.get(chart_type, {}).get(semantic_type, 0.3)
    
    def _calculate_variation_score(self, col_meta: Dict[str, Any]) -> float:
        """Calculate variation score."""
        if col_meta['semantic_type'] in [SemanticType.NUMERIC.value, SemanticType.CURRENCY.value, SemanticType.PERCENTAGE.value]:
            stats = col_meta.get('numeric_stats', {})
            if stats:
                q1 = stats.get('25%')
                q3 = stats.get('75%')
                median = stats.get('50%')
                
                if q1 is not None and q3 is not None and median is not None:
                    iqr = q3 - q1
                    if abs(median) > 1e-9:
                        return min(1.0, iqr / abs(median))
        
        elif col_meta['semantic_type'] in [SemanticType.CATEGORICAL.value, SemanticType.BOOLEAN.value, SemanticType.STAGE.value]:
            unique_count = col_meta['unique_count']
            if unique_count <= 1:
                return 0.0
            
            if col_meta.get('top_values'):
                counts = np.array(list(col_meta['top_values'].values()))
                total = counts.sum()
                if total > 0:
                    probs = counts / total
                    entropy = -np.sum(probs * np.log2(probs + 1e-9))
                    max_entropy = np.log2(unique_count + 1e-9)
                    if max_entropy > 0:
                        return entropy / max_entropy
        
        return 0.5
    
    def _prioritize_columns(self, columns: List[str]) -> List[str]:
        """Prioritize columns by business importance and variation."""
        if not columns:
            return []
        
        scored = []
        business_terms = self.config.get('business_priority_terms', {})
        
        for col in columns:
            score = 0
            
            if any(term in col.lower() for term in business_terms.get(BusinessPriority.HIGH.value, [])):
                score += 3
            elif any(term in col.lower() for term in business_terms.get(BusinessPriority.MEDIUM.value, [])):
                score += 1
            
            if len(col) <= 30 and re.match(r'^[a-zA-Z0-9_ ]+$', col):
                score += 1
            
            scored.append((score, col))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [col for _, col in scored]
    
    def _get_dynamic_pair_limit(self, chart_type: str, column: str, 
                               df: pd.DataFrame, metadata: Dict[str, Any]) -> int:
        """Get dynamic pair limit based on column characteristics."""
        default = 6  # Default for bar charts
        
        if not self.config.get('feature_flags', {}).get('dynamic_limits', True):
            return default
        
        if chart_type == ChartType.BAR.value and column in metadata['columns']:
            unique_count = metadata['columns'][column].get('unique_count', 0)
            
            if unique_count is None:
                return default
            
            # Fewer pairs for high-cardinality categorical columns
            if unique_count > 20:
                return min(default, 4)
            elif unique_count > 10:
                return min(default, 6)
            elif unique_count > 5:
                return min(default, 8)
        
        return default
    
    def _generate_safe_plotly_code(self, df: pd.DataFrame, chart_type: str, 
                                  columns: List[str], title: str) -> str:
        """Generate safe Plotly code with dynamic adjustments."""
        if not columns:
            return "# No columns specified for chart"
        
        # Safe column names (properly quoted)
        safe_cols = [repr(col) for col in columns]
        
        # Chart-specific code generation
        if chart_type == ChartType.HISTOGRAM.value and len(columns) >= 1:
            return f"""import plotly.express as px
fig = px.histogram(df, x={safe_cols[0]}, title={repr(title)})
fig.update_layout(
    plot_bgcolor='white',
    xaxis=dict(showgrid=False),
    yaxis=dict(showgrid=True, gridcolor='lightgray', gridwidth=0.5),
    font=dict(family='Arial, sans-serif', size=12)
)"""
        
        elif chart_type == ChartType.BAR.value and len(columns) >= 2:
            # Dynamic category limit for bar charts
            cat_col = columns[0]
            unique_count = df[cat_col].nunique() if cat_col in df.columns else 0
            limit = 12  # Default
            
            if unique_count > 20:
                limit = 10
            elif unique_count > 15:
                limit = 8
            
            return f"""import plotly.express as px
# Aggregate for cleaner visualization (top {limit} categories)
agg_df = df.groupby({safe_cols[0]})[{safe_cols[1]}].mean().reset_index()
agg_df = agg_df.sort_values({safe_cols[1]}, ascending=False).head({limit})
fig = px.bar(agg_df, x={safe_cols[0]}, y={safe_cols[1]}, title={repr(title)})
fig.update_layout(
    plot_bgcolor='white',
    xaxis=dict(tickangle=-45, categoryorder='total descending'),
    yaxis=dict(showgrid=True, gridcolor='lightgray', gridwidth=0.5),
    font=dict(family='Arial, sans-serif', size=12)
)"""
        
        elif chart_type == ChartType.LINE.value and len(columns) >= 2:
            return f"""import plotly.express as px
# Ensure chronological order
df_sorted = df.sort_values({safe_cols[0]})
fig = px.line(df_sorted, x={safe_cols[0]}, y={safe_cols[1]}, title={repr(title)})
fig.update_traces(line=dict(width=2.5, color='#1f77b4'))
fig.update_layout(
    plot_bgcolor='white',
    xaxis=dict(showgrid=True, gridcolor='lightgray', gridwidth=0.5),
    yaxis=dict(showgrid=True, gridcolor='lightgray', gridwidth=0.5),
    hovermode='x unified',
    font=dict(family='Arial, sans-serif', size=12)
)"""
        
        elif chart_type == ChartType.SCATTER.value and len(columns) >= 2:
            return f"""import plotly.express as px
fig = px.scatter(df, x={safe_cols[0]}, y={safe_cols[1]}, title={repr(title)})
fig.update_traces(
    marker=dict(size=8, opacity=0.7, line=dict(width=1, color='DarkSlateGrey'))
)
fig.update_layout(
    plot_bgcolor='white',
    xaxis=dict(showgrid=True, gridcolor='lightgray', gridwidth=0.5),
    yaxis=dict(showgrid=True, gridcolor='lightgray', gridwidth=0.5),
    font=dict(family='Arial, sans-serif', size=12)
)"""
        
        elif chart_type == ChartType.PIE.value and len(columns) >= 1:
            if len(columns) >= 2:
                return f"""import plotly.express as px
fig = px.pie(df, names={safe_cols[0]}, values={safe_cols[1]}, title={repr(title)})
fig.update_traces(textposition='inside', textinfo='percent+label')
fig.update_layout(
    font=dict(family='Arial, sans-serif', size=12),
    showlegend=True,
    legend=dict(orientation='v', yanchor='middle', y=0.5)
)"""
            else:
                return f"""import plotly.express as px
value_counts = df[{safe_cols[0]}].value_counts().reset_index()
value_counts.columns = [{safe_cols[0]}, 'count']
fig = px.pie(value_counts, names={safe_cols[0]}, values='count', title={repr(title)})
fig.update_traces(textposition='inside', textinfo='percent+label')
fig.update_layout(
    font=dict(family='Arial, sans-serif', size=12),
    showlegend=True,
    legend=dict(orientation='v', yanchor='middle', y=0.5)
)"""
        
        # Fallback for other chart types
        return f"""# {chart_type.title()} Chart Code
import plotly.express as px
# Customize this code for your specific visualization needs
# Columns: {', '.join(columns)}
# Documentation: https://plotly.com/python/
"""

# ============================================================================
# PUBLIC API FUNCTIONS
# ============================================================================

def analyze_dataset(df: pd.DataFrame, config: Optional[Dict[str, Any]] = None,
                   max_top_values: int = 10) -> Dict[str, Any]:
    """Analyze dataset and mine business insights."""
    analyzer = DatasetAnalyzer(config)
    return analyzer.analyze(df, max_top_values)

def infer_semantic_type(df: pd.DataFrame, col: str) -> str:
    """Infer semantic type of a column."""
    analyzer = DatasetAnalyzer()
    return analyzer._infer_semantic_type(df, col)

def get_echo_config() -> Dict[str, Any]:
    """Get Echo Engine configuration for integration."""
    return copy.deepcopy(DEFAULT_CONFIG)

def update_echo_config(**updates) -> Dict[str, Any]:
    """Update Echo Engine configuration."""
    config = get_echo_config()
    config.update(updates)
    return config

def validate_dataset_for_echo(df: pd.DataFrame) -> Tuple[bool, str]:
    """Validate dataset for Echo Engine analysis."""
    if df is None or df.empty:
        return False, "Dataset is empty"
    
    if len(df.columns) == 0:
        return False, "Dataset has no columns"
    
    if len(df) < DEFAULT_CONFIG.get('min_rows', 3):
        return False, f"Dataset needs at least {DEFAULT_CONFIG.get('min_rows', 3)} rows"
    
    # Check for at least one analyzable column
    has_analyzable = False
    for col in df.columns:
        if not re.match(r'^id$|_id$|^uuid$|^guid$', col.lower()):
            has_analyzable = True
            break
    
    if not has_analyzable:
        return False, "Dataset appears to contain only ID columns"
    
    return True, "Dataset validated successfully"

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "EchoChartRecommender",
]

# Version and metadata
__version__ = "1.0.0"
__author__ = "BODZZ Analytics"
__description__ = "Production-grade Business Intelligence Agent with insight mining"