"""
Echo Narratives v1.0 - Production-Grade Business Intelligence Storytelling
Transform data into compelling business narratives with actionable insights.
Consultant-grade reports that drive decision-making.
"""

import re
import time
import textwrap
import logging
import random
from typing import Dict, Any, List, Optional, Tuple, Union, Set
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass, field

import pandas as pd
import numpy as np

# ============================================================================
# CONSTANTS & ENUMS
# ============================================================================

class InsightCategory(Enum):
    """Categories of business insights."""
    RISK = "risk"
    OPPORTUNITY = "opportunity"
    PERFORMANCE = "performance"
    DATA_QUALITY = "data_quality"
    TREND = "trend"
    DISTRIBUTION = "distribution"

class NarrativeSection(Enum):
    """Narrative sections."""
    HEADER = "header"
    EXECUTIVE_HIGHLIGHT = "executive_highlight"
    PRIORITY_INSIGHTS = "priority_insights"
    ANALYSIS_CONTEXT = "analysis_context"
    VISUAL_ANALYSIS = "visual_analysis"
    STRATEGIC_RECOMMENDATIONS = "strategic_recommendations"
    NEXT_STEPS = "next_steps"
    TECHNICAL_APPENDIX = "technical_appendix"

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

logger = logging.getLogger(__name__)

def setup_narrative_logging(level: str = "INFO"):
    """Configure logging for narrative generation."""
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, level.upper()))
        logger.propagate = False

setup_narrative_logging()

# ============================================================================
# TEMPLATES & CONFIGURATION
# ============================================================================

INSIGHT_TEMPLATES = {
    'dependency_risk': {
        'title': "🚨 CRITICAL DEPENDENCY",
        'template': "**{title}**: '{top_item}' drives {concentration:.0%} of {metric}. This concentration represents significant business risk and requires immediate attention.",
        'action': "Develop contingency plans and diversify away from '{top_item}' within 30 days.",
        'category': InsightCategory.RISK.value,
        'priority': 10,
        'icon': '🚨',
        'color': '#ff4444'
    },
    'strong_pareto': {
        'title': "🎯 80/20 EFFICIENCY",
        'template': "**{title}**: Top {top_n} {dimension}s drive {concentration:.0%} of {metric}. Classic Pareto distribution detected - focus resources for maximum ROI.",
        'action': "Prioritize resources on top {top_n} {dimension}s and establish monitoring.",
        'category': InsightCategory.OPPORTUNITY.value,
        'priority': 8,
        'icon': '🎯',
        'color': '#00aa00'
    },
    'business_relationship': {
        'title': "🔗 TOP PERFORMER",
        'template': "**{title}**: '{top_segment}' segment delivers {share_of_total:.0%} of {metric} with {performance_multiplier:.1f}x average performance. High-value segment identified.",
        'action': "Reverse-engineer '{top_segment}' success factors and replicate across segments.",
        'category': InsightCategory.PERFORMANCE.value,
        'priority': 7,
        'icon': '🔗',
        'color': '#0066cc'
    },
    'golden_period': {
        'title': "⭐ PEAK PERFORMANCE",
        'template': "**{title}**: {period} delivers {performance_ratio:.1f}x average {metric}. This represents peak performance worth investigating.",
        'action': "Analyze success factors in {period} and embed in quarterly planning.",
        'category': InsightCategory.PERFORMANCE.value,
        'priority': 8,
        'icon': '⭐',
        'color': '#ffaa00'
    },
    'missing_data_opportunity': {
        'title': "💡 DATA OPPORTUNITY",
        'template': "**{title}**: Missing '{missing_column}' ({missing_pct:.0%}) correlates with {difference_pct:.0%} higher {impact_metric}. Investigate this counter-intuitive pattern.",
        'action': "Investigate data collection for '{missing_column}' and validate correlation.",
        'category': InsightCategory.OPPORTUNITY.value,
        'priority': 7,
        'icon': '💡',
        'color': '#aa00ff'
    },
    'significant_trend': {
        'title': "📈 STRONG TREND",
        'template': "**{title}**: {metric} is {direction} at {trend:.1%} per period. Consistent {direction} momentum detected.",
        'action': "Develop initiatives to {'accelerate' if direction == 'growing' else 'reverse'} this trend.",
        'category': InsightCategory.TREND.value,
        'priority': 6,
        'icon': '📈',
        'color': '#008888'
    },
    'high_volatility': {
        'title': "⚡ HIGH VOLATILITY",
        'template': "**{title}**: {metric} shows high volatility (CV={cv:.2f}). This indicates significant fluctuations requiring attention.",
        'action': "Implement smoothing or forecasting models for better predictability.",
        'category': InsightCategory.RISK.value,
        'priority': 5,
        'icon': '⚡',
        'color': '#ff6600'
    },
    'moderate_concentration': {
        'title': "📊 CONCENTRATION",
        'template': "**{title}**: Top {top_n} {dimension}s deliver {concentration:.0%} of {metric}. Moderate concentration requiring monitoring.",
        'action': "Monitor concentration levels monthly and consider gradual diversification.",
        'category': InsightCategory.DISTRIBUTION.value,
        'priority': 5,
        'icon': '📊',
        'color': '#555555'
    },
    'healthy_distribution': {
        'title': "✅ HEALTHY DISTRIBUTION",
        'template': "**{title}**: {metric} is well-distributed across {dimension}s (diversity score: {diversity_score:.1f}). Low concentration risk identified.",
        'action': "Maintain current distribution strategy and document best practices.",
        'category': InsightCategory.DISTRIBUTION.value,
        'priority': 4,
        'icon': '✅',
        'color': '#00aa44'
    },
    'data_quality_issue': {
        'title': "⚠️ DATA QUALITY",
        'template': "**{title}**: {missing_pct:.0%} missing values in '{missing_column}'. Data completeness affects analysis reliability.",
        'action': "Improve data collection process for '{missing_column}' within 60 days.",
        'category': InsightCategory.DATA_QUALITY.value,
        'priority': 3,
        'icon': '⚠️',
        'color': '#ff8800'
    }
}

CHART_ICONS = {
    'histogram': '📊',
    'bar': '📈',
    'line': '📉',
    'scatter': '🔗',
    'pie': '🥧',
    'box': '📦',
    'violin': '🎻',
    'heatmap': '🧊',
    'area': '🏞️',
    'waterfall': '💧',
    'funnel': '🪫',
    'treemap': '🌳',
}

BUSINESS_TERM_SYNONYMS = {
    'revenue': ['revenue', 'sales', 'income', 'turnover', 'gmv', 'top line'],
    'profit': ['profit', 'margin', 'earnings', 'bottom line', 'net income'],
    'cost': ['cost', 'expense', 'spend', 'expenditure', 'outlay'],
    'growth': ['growth', 'increase', 'expansion', 'rise', 'upswing'],
    'customer': ['customer', 'client', 'consumer', 'user', 'subscriber'],
    'conversion': ['conversion', 'rate', 'ratio', 'percentage', 'yield'],
    'efficiency': ['efficiency', 'productivity', 'utilization', 'performance'],
    'quality': ['quality', 'satisfaction', 'score', 'rating', 'feedback']
}

# Priority indicators for numbered lists
PRIORITY_INDICATORS = ["❶", "❷", "❸", "❹", "❺", "❻", "❼", "❽", "❾", "❿"]

# Confidence level mappings
CONFIDENCE_LEVELS = {
    'high': {'threshold': 0.75, 'icon': '🔬', 'label': 'High Confidence'},
    'medium': {'threshold': 0.5, 'icon': '🔍', 'label': 'Medium Confidence'},
    'low': {'threshold': 0.0, 'icon': '⚠️', 'label': 'Low Confidence'}
}

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class NarrativeConfig:
    """Configuration for narrative generation."""
    max_insights: int = 4
    max_charts: int = 6
    max_recommendations: int = 4
    max_narrative_length: int = 20000
    enable_icons: bool = True
    enable_technical_appendix: bool = True
    language_style: str = "professional"  # "professional", "executive", "technical"
    include_actions: bool = True
    timestamp_format: str = "%Y-%m-%d %H:%M"
    
    def __post_init__(self):
        """Validate configuration."""
        if self.max_insights > 10:
            logger.warning(f"max_insights reduced from {self.max_insights} to 10")
            self.max_insights = 10
        if self.max_charts > 10:
            logger.warning(f"max_charts reduced from {self.max_charts} to 10")
            self.max_charts = 10

@dataclass
class ChartInfo:
    """Information about a chart for narrative generation."""
    chart_type: str
    title: str
    description: str
    confidence: float
    columns: List[str]
    insight_context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate and clean chart info."""
        self.confidence = max(0.0, min(1.0, self.confidence))
        if not self.columns:
            self.columns = []

# ============================================================================
# CORE NARRATIVE GENERATION
# ============================================================================

class NarrativeGenerator:
    """Production-grade narrative generator for business intelligence."""
    
    def __init__(self, config: Optional[NarrativeConfig] = None):
        self.config = config or NarrativeConfig()
        self._quality_metrics = {
            'generated': 0,
            'failed': 0,
            'avg_length': 0,
            'avg_insights': 0
        }
    
    def generate_consultant_narrative(self, df: pd.DataFrame, user_prompt: str,
                                     metadata: Dict[str, Any],
                                     charts: List[Dict[str, Any]]) -> str:
        """
        Generate professional business intelligence narrative.
        
        Args:
            df: DataFrame being analyzed
            user_prompt: User's original query
            metadata: Enhanced metadata from engine.py with insights
            charts: List of recommended charts with metadata
            
        Returns:
            Formatted markdown narrative ready for display
        """
        start_time = time.time()
        
        try:
            # Validate inputs
            self._validate_inputs(df, user_prompt, metadata, charts)
            
            # Convert charts to ChartInfo objects
            chart_infos = self._process_charts(charts)
            
            # Generate narrative sections
            sections = self._generate_narrative_sections(
                df, user_prompt, metadata, chart_infos
            )
            
            # Assemble final narrative
            narrative = self._assemble_narrative(sections)
            
            # Validate quality
            quality_check = self.validate_narrative(narrative)
            if not quality_check[0]:
                logger.warning(f"Narrative quality issues: {quality_check[1]}")
                # Apply fixes if possible
                narrative = self._enhance_narrative_quality(narrative)
            
            # Update metrics
            self._update_metrics(len(narrative), len(metadata.get('prioritized_insights', [])))
            
            logger.info(f"Narrative generated in {time.time() - start_time:.2f}s")
            return narrative
            
        except Exception as e:
            logger.error(f"Narrative generation failed: {e}", exc_info=True)
            return self._generate_fallback_narrative(df, user_prompt, metadata, charts)
    
    def _validate_inputs(self, df: pd.DataFrame, user_prompt: str,
                        metadata: Dict[str, Any], charts: List[Dict[str, Any]]) -> None:
        """Validate inputs for narrative generation."""
        if df is None or df.empty:
            raise ValueError("DataFrame is empty or None")
        
        if not isinstance(user_prompt, str):
            raise ValueError("User prompt must be a string")
        
        if not isinstance(metadata, dict):
            raise ValueError("Metadata must be a dictionary")
        
        if not isinstance(charts, list):
            raise ValueError("Charts must be a list")
    
    def _process_charts(self, charts: List[Dict[str, Any]]) -> List[ChartInfo]:
        """Convert raw chart dictionaries to ChartInfo objects."""
        chart_infos = []
        
        for i, chart in enumerate(charts[:self.config.max_charts]):
            try:
                chart_info = ChartInfo(
                    chart_type=chart.get('chart_type', 'unknown'),
                    title=chart.get('title', f'Chart {i+1}'),
                    description=chart.get('description', ''),
                    confidence=float(chart.get('confidence', 0.5)),
                    columns=chart.get('columns', []),
                    insight_context=chart.get('insight_context', {}),
                    metadata={
                        'id': chart.get('id', f'chart_{i}'),
                        'generated_at': chart.get('generated_at', time.time()),
                        'business_impact': chart.get('business_impact', 1.0)
                    }
                )
                chart_infos.append(chart_info)
            except Exception as e:
                logger.warning(f"Failed to process chart {i}: {e}")
                continue
        
        return chart_infos
    
    def _generate_narrative_sections(self, df: pd.DataFrame, user_prompt: str,
                                    metadata: Dict[str, Any],
                                    chart_infos: List[ChartInfo]) -> Dict[NarrativeSection, List[str]]:
        """Generate all narrative sections."""
        sections = {}
        
        # 1. Header
        sections[NarrativeSection.HEADER] = self._generate_header(user_prompt)
        
        # 2. Executive Highlight
        sections[NarrativeSection.EXECUTIVE_HIGHLIGHT] = self._generate_executive_highlight(
            metadata
        )
        
        # 3. Priority Insights
        sections[NarrativeSection.PRIORITY_INSIGHTS] = self._generate_priority_insights(
            metadata
        )
        
        # 4. Analysis Context
        sections[NarrativeSection.ANALYSIS_CONTEXT] = self._generate_analysis_context(
            df, metadata
        )
        
        # 5. Visual Analysis
        sections[NarrativeSection.VISUAL_ANALYSIS] = self._generate_visual_analysis(
            chart_infos
        )
        
        # 6. Strategic Recommendations
        sections[NarrativeSection.STRATEGIC_RECOMMENDATIONS] = self._generate_strategic_recommendations(
            metadata, chart_infos
        )
        
        # 7. Next Steps
        sections[NarrativeSection.NEXT_STEPS] = self._generate_next_steps(
            metadata, chart_infos
        )
        
        # 8. Technical Appendix (optional)
        if self.config.enable_technical_appendix:
            sections[NarrativeSection.TECHNICAL_APPENDIX] = self._generate_technical_appendix(
                df, metadata, chart_infos
            )
        
        return sections
    
    def _generate_header(self, user_prompt: str) -> List[str]:
        """Generate narrative header."""
        prompt_truncated = self._truncate_text(user_prompt, 120)
        
        return [
            "# 📋 BUSINESS INTELLIGENCE REPORT",
            "",
            f"**Analysis Context**: \"{prompt_truncated}\"",
            f"**Report Date**: {datetime.now().strftime(self.config.timestamp_format)}",
            f"**Analysis Engine**: Echo Intelligence v1.0",
            ""
        ]
    
    def _generate_executive_highlight(self, metadata: Dict[str, Any]) -> List[str]:
        """Generate executive highlight section."""
        lines = []
        
        # Quick stats box
        lines.extend(self._generate_quick_stats_box(metadata))
        lines.append("")
        
        # Hero insight
        hero_insight = metadata.get('hero_insight')
        if hero_insight:
            lines.append("## 🎯 EXECUTIVE HIGHLIGHT")
            lines.append("")
            lines.append(self._format_hero_insight(hero_insight))
            lines.append("")
        
        return lines
    
    def _generate_quick_stats_box(self, metadata: Dict[str, Any]) -> List[str]:
        """Generate quick stats overview box."""
        stats = []
        
        # Row count
        row_count = metadata.get('row_count', 0)
        if row_count > 1000000:
            stats.append(f"📊 **{row_count/1000000:.1f}M records**")
        elif row_count > 1000:
            stats.append(f"📊 **{row_count/1000:.1f}K records**")
        else:
            stats.append(f"📊 **{row_count:,} records**")
        
        # Column count
        col_count = metadata.get('col_count', 0)
        stats.append(f"📋 **{col_count} columns**")
        
        # Business metrics
        business_cols = metadata.get('business_priority_columns', [])
        if business_cols:
            stats.append(f"💰 **{len(business_cols)} business metrics**")
        
        # Insights count
        insights = metadata.get('prioritized_insights', [])
        if insights:
            high_impact = sum(1 for i in insights if i.get('priority', 0) >= 7)
            stats.append(f"🎯 **{high_impact} high-impact insights**")
        
        return [" | ".join(stats)]
    
    def _format_hero_insight(self, insight: Dict[str, Any]) -> str:
        """Format hero insight for executive highlight."""
        template = INSIGHT_TEMPLATES.get(insight.get('type', ''), {})
        
        try:
            # Format the insight text
            insight_text = template.get('template', '{body}').format(**insight)
        except KeyError as e:
            logger.warning(f"Missing key in insight formatting: {e}")
            insight_text = insight.get('body', '')
        
        # Clean up the text
        insight_text = re.sub(r'\*\*', '', insight_text)
        
        # Format with icon and color
        icon = template.get('icon', '🎯') if self.config.enable_icons else ''
        action = insight.get('action', template.get('action', 'Review this insight'))
        
        formatted = [
            f"{icon} **{insight.get('title', 'Key Finding')}**",
            "",
            insight_text,
            "",
            f"**→ Recommended Action**: {action}"
        ]
        
        return "\n".join(formatted)
    
    def _generate_priority_insights(self, metadata: Dict[str, Any]) -> List[str]:
        """Generate priority insights section."""
        lines = []
        
        prioritized_insights = metadata.get('prioritized_insights', [])
        if not prioritized_insights:
            return lines
        
        lines.append("## 🔍 PRIORITY BUSINESS INSIGHTS")
        lines.append("")
        lines.append("*Ranked by business impact and analytical confidence*")
        lines.append("")
        
        for i, insight in enumerate(prioritized_insights[:self.config.max_insights], 1):
            try:
                lines.append(self._format_insight_for_narrative(insight, i))
                lines.append("")
            except Exception as e:
                logger.warning(f"Failed to format insight {i}: {e}")
                continue
        
        return lines
    
    def _format_insight_for_narrative(self, insight: Dict[str, Any], index: int) -> str:
        """Format a single insight for the narrative."""
        insight_type = insight.get('type', 'statistical_insight')
        template = INSIGHT_TEMPLATES.get(insight_type, {
            'title': 'Insight',
            'template': '{body}',
            'icon': '📊'
        })
        
        # Priority indicator
        if index <= len(PRIORITY_INDICATORS):
            priority_icon = PRIORITY_INDICATORS[index-1]
        else:
            priority_icon = f"{index}."
        
        # Get formatted body
        try:
            body = template['template'].format(**insight)
        except KeyError:
            body = insight.get('body', '')
        
        # Clean markdown from body for cleaner display
        body = re.sub(r'\*\*', '', body)
        
        # Confidence indicator
        confidence = insight.get('confidence', 0)
        confidence_info = self._get_confidence_info(confidence)
        
        # Action text
        action = insight.get('action', template.get('action', 'Review this insight for opportunities'))
        
        formatted = [
            f"{priority_icon} **{template['icon'] if self.config.enable_icons else ''} {template['title']}**",
            f"   {body}",
            f"   → **Action**: {action}",
            f"   {confidence_info['icon']} **{confidence_info['label']}** ({confidence:.0%})"
        ]
        
        return "\n".join(formatted)
    
    def _get_confidence_info(self, confidence: float) -> Dict[str, str]:
        """Get confidence level information."""
        if confidence >= CONFIDENCE_LEVELS['high']['threshold']:
            return CONFIDENCE_LEVELS['high']
        elif confidence >= CONFIDENCE_LEVELS['medium']['threshold']:
            return CONFIDENCE_LEVELS['medium']
        else:
            return CONFIDENCE_LEVELS['low']
    
    def _generate_analysis_context(self, df: pd.DataFrame, 
                                  metadata: Dict[str, Any]) -> List[str]:
        """Generate analysis context section."""
        lines = [
            "## 📊 ANALYSIS CONTEXT",
            ""
        ]
        
        # Dataset summary
        row_count = metadata.get('row_count', 0)
        col_count = metadata.get('col_count', 0)
        lines.append(f"**Dataset**: {row_count:,} records × {col_count} columns")
        
        # Business metrics
        business_cols = metadata.get('business_priority_columns', [])
        if business_cols:
            lines.append(f"**Key Business Metrics**: {', '.join(business_cols[:3])}")
        
        # Data quality
        missing_pct = metadata.get('global_missing_pct', 0)
        if missing_pct > 0.1:
            lines.append(f"⚠️ **Data Quality Alert**: {missing_pct:.1%} missing values overall")
        elif missing_pct > 0.05:
            lines.append(f"📝 **Data Quality Note**: {missing_pct:.1%} missing values")
        else:
            lines.append(f"✅ **Data Quality**: Excellent ({missing_pct:.1%} missing)")
        
        # Time analysis
        if metadata.get('datetime_columns'):
            dt_cols = metadata['datetime_columns']
            lines.append(f"📅 **Time Analysis**: {len(dt_cols)} date/time column{'s' if len(dt_cols) > 1 else ''} available")
        
        # Correlations
        strong_corrs = [c for c in metadata.get('top_correlations', []) 
                       if abs(c.get('corr', 0)) > 0.7]
        if strong_corrs:
            lines.append(f"🔗 **Strong Relationships**: {len(strong_corrs)} significant correlation{'s' if len(strong_corrs) > 1 else ''}")
        
        # Analysis method
        if metadata.get('analysis_mode') == 'heuristic':
            lines.append(f"⚙️ **Analysis Method**: Heuristic analysis with business rule engine")
        else:
            lines.append(f"⚙️ **Analysis Method**: AI-enhanced with heuristic validation")
        
        return lines
    
    def _generate_visual_analysis(self, chart_infos: List[ChartInfo]) -> List[str]:
        """Generate visual analysis section."""
        lines = [
            "## 📈 VISUAL ANALYSIS",
            ""
        ]
        
        if not chart_infos:
            lines.append("*No visualizations generated. Consider refining your analysis request or checking data quality.*")
            lines.append("")
            return lines
        
        lines.append("*Visualizations prioritized to highlight key business insights*")
        lines.append("")
        
        for i, chart in enumerate(chart_infos, 1):
            try:
                lines.append(self._format_chart_for_narrative(chart, i))
                lines.append("")
            except Exception as e:
                logger.warning(f"Failed to format chart {i}: {e}")
                continue
        
        return lines
    
    def _format_chart_for_narrative(self, chart: ChartInfo, index: int) -> str:
        """Format a chart for the narrative."""
        # Chart icon and confidence indicator
        icon = CHART_ICONS.get(chart.chart_type, '📊') if self.config.enable_icons else ''
        confidence_info = self._get_confidence_info(chart.confidence)
        
        # Insight context
        has_insight = chart.insight_context.get('has_insight', False)
        insight_title = chart.insight_context.get('primary_insight', '')
        
        # Format the entry
        lines = []
        
        # Header with optional insight badge
        if has_insight and insight_title:
            lines.append(f"{index}. **{icon} {chart.title}** - {confidence_info['icon']} {confidence_info['label']} **🔍 Insight Visualization**")
            lines.append(f"   *Visualizes: {insight_title}*")
        else:
            lines.append(f"{index}. **{icon} {chart.title}** - {confidence_info['icon']} {confidence_info['label']}")
        
        # Clean description
        clean_desc = re.sub(r'\*\*[^*]+\*\*:\s*', '', chart.description)
        if clean_desc:
            clean_desc = self._truncate_text(clean_desc, 200)
            lines.append(f"   {clean_desc}")
        
        # One-liner if available
        if 'one_liner' in chart.metadata:
            one_liner = chart.metadata['one_liner']
            if one_liner:
                lines.append(f"   *{one_liner}*")
        
        return "\n".join(lines)
    
    def _generate_strategic_recommendations(self, metadata: Dict[str, Any],
                                           chart_infos: List[ChartInfo]) -> List[str]:
        """Generate strategic recommendations based on insights."""
        lines = [
            "## 🚀 STRATEGIC RECOMMENDATIONS",
            "",
            "*Prioritized by business impact and implementation feasibility*",
            ""
        ]
        
        recommendations = self._create_strategic_recommendations(metadata, chart_infos)
        
        if not recommendations:
            lines.append("*No specific recommendations available. Review insights for opportunities.*")
            return lines
        
        for i, rec in enumerate(recommendations[:self.config.max_recommendations], 1):
            try:
                lines.append(self._format_recommendation(rec, i))
                lines.append("")
            except Exception as e:
                logger.warning(f"Failed to format recommendation {i}: {e}")
                continue
        
        return lines
    
    def _create_strategic_recommendations(self, metadata: Dict[str, Any],
                                         chart_infos: List[ChartInfo]) -> List[Dict[str, Any]]:
        """Create strategic recommendations based on insights."""
        recommendations = []
        insights = metadata.get('prioritized_insights', [])
        
        # 1. RISK MITIGATION
        risk_insights = [i for i in insights if i.get('type') in ['dependency_risk', 'critical_risk']]
        if risk_insights:
            top_risk = risk_insights[0]
            recommendations.append({
                'title': '🚨 Risk Mitigation Initiative',
                'description': f"Address dependency on '{top_risk.get('top_item', 'key segment')}' driving {top_risk.get('concentration', 0):.0%} of {top_risk.get('metric', 'key metric')}",
                'timeline': 'Immediate (1-4 weeks)',
                'owner': 'Leadership Team',
                'priority': 10
            })
        
        # 2. EFFICIENCY OPTIMIZATION
        pareto_insights = [i for i in insights if i.get('type') in ['strong_pareto', 'moderate_concentration']]
        if pareto_insights:
            top_pareto = pareto_insights[0]
            recommendations.append({
                'title': '🎯 Focus Optimization Program',
                'description': f"Concentrate resources on top {top_pareto.get('top_n', 3)} {top_pareto.get('dimension', 'segments')} driving {top_pareto.get('concentration', 0):.0%} of impact",
                'timeline': 'Short-term (1-3 months)',
                'owner': 'Operations Team',
                'priority': 8
            })
        
        # 3. PERFORMANCE REPLICATION
        relationship_insights = [i for i in insights if i.get('type') == 'business_relationship']
        if relationship_insights:
            top_rel = relationship_insights[0]
            recommendations.append({
                'title': '🔗 Best Practice Replication',
                'description': f"Reverse-engineer and replicate success factors from '{top_rel.get('top_segment', 'top performer')}' segment across organization",
                'timeline': 'Medium-term (3-6 months)',
                'owner': 'Strategy Team',
                'priority': 7
            })
        
        # 4. DATA QUALITY IMPROVEMENT
        missing_insights = [i for i in insights if i.get('type') in ['missing_data_opportunity', 'missing_data_impact', 'data_quality_issue']]
        if missing_insights:
            top_missing = missing_insights[0]
            recommendations.append({
                'title': '🔍 Data Quality Initiative',
                'description': f"Improve data collection and validation for '{top_missing.get('missing_column', 'key column')}' ({top_missing.get('missing_pct', 0):.0%} missing)",
                'timeline': 'Ongoing',
                'owner': 'Data Team',
                'priority': 6
            })
        
        # 5. DASHBOARD DEVELOPMENT
        insight_charts = [c for c in chart_infos if c.insight_context.get('has_insight', False)]
        if insight_charts:
            recommendations.append({
                'title': '📊 Executive Dashboard',
                'description': f"Build executive dashboard with {len(insight_charts)} key visualizations to monitor priority insights",
                'timeline': 'Medium-term (3-6 months)',
                'owner': 'BI Team',
                'priority': 5
            })
        
        # Sort by priority
        recommendations.sort(key=lambda x: x['priority'], reverse=True)
        return recommendations
    
    def _format_recommendation(self, rec: Dict[str, Any], index: int) -> str:
        """Format a single recommendation."""
        return f"{index}. **{rec['title']}**\n" \
               f"   {rec['description']}\n" \
               f"   👤 **Owner**: {rec['owner']} | 📅 **Timeline**: {rec['timeline']}"
    
    def _generate_next_steps(self, metadata: Dict[str, Any],
                            chart_infos: List[ChartInfo]) -> List[str]:
        """Generate immediate next steps."""
        lines = [
            "## 📅 IMMEDIATE NEXT STEPS",
            ""
        ]
        
        steps = [
            "1. **Review Priority Insights**: Start with insights marked with 🚨 or 🎯",
            "2. **Validate with Business Context**: Apply domain expertise to each finding",
            "3. **Schedule Review Meeting**: Present findings to key stakeholders within 7 days",
            "4. **Develop Action Plan**: Convert top 3 recommendations into specific initiatives",
            "5. **Assign Ownership**: Designate owners for each recommended action",
            "6. **Establish Monitoring**: Set up regular review cadence for key metrics",
            "7. **Document Learnings**: Update playbook with insights and successful interventions"
        ]
        
        lines.extend(steps)
        return lines
    
    def _generate_technical_appendix(self, df: pd.DataFrame,
                                    metadata: Dict[str, Any],
                                    chart_infos: List[ChartInfo]) -> List[str]:
        """Generate technical appendix."""
        lines = [
            "## 🔧 TECHNICAL APPENDIX",
            ""
        ]
        
        # Basic info
        lines.append(f"**Dataset Characteristics**: {metadata.get('row_count', 0):,} rows × {metadata.get('col_count', 0)} columns")
        
        # Analysis info
        if metadata.get('analysis_time_ms'):
            lines.append(f"**Analysis Duration**: {metadata['analysis_time_ms']}ms")
        
        if metadata.get('data_hash'):
            lines.append(f"**Dataset Fingerprint**: {metadata['data_hash'][:16]}...")
        
        # Chart statistics
        if chart_infos:
            high_conf = sum(1 for c in chart_infos if c.confidence > 0.7)
            medium_conf = sum(1 for c in chart_infos if 0.5 <= c.confidence <= 0.7)
            insight_driven = sum(1 for c in chart_infos if c.insight_context.get('has_insight', False))
            
            lines.append(f"**Chart Quality**: {high_conf} high-confidence, {medium_conf} medium-confidence, {insight_driven} insight-driven")
        
        # Additional metadata
        if metadata.get('generated_at'):
            gen_time = datetime.fromtimestamp(metadata['generated_at'])
            lines.append(f"**Generation Timestamp**: {gen_time.strftime(self.config.timestamp_format)}")
        
        lines.append(f"**Narrative Engine**: Echo Narratives v1.0")
        
        return lines
    
    def _assemble_narrative(self, sections: Dict[NarrativeSection, List[str]]) -> str:
        """Assemble all narrative sections into final output."""
        lines = []
        
        # Add all sections in order
        section_order = [
            NarrativeSection.HEADER,
            NarrativeSection.EXECUTIVE_HIGHLIGHT,
            NarrativeSection.PRIORITY_INSIGHTS,
            NarrativeSection.ANALYSIS_CONTEXT,
            NarrativeSection.VISUAL_ANALYSIS,
            NarrativeSection.STRATEGIC_RECOMMENDATIONS,
            NarrativeSection.NEXT_STEPS,
            NarrativeSection.TECHNICAL_APPENDIX
        ]
        
        for section in section_order:
            if section in sections and sections[section]:
                lines.extend(sections[section])
                # Add spacing between sections
                if sections[section][-1] != '':
                    lines.append('')
        
        # Add footer
        lines.append("---")
        lines.append(f"*Generated by Echo Intelligence v1.0 • Professional Business Analytics • {datetime.now().strftime('%Y-%m-%d')}*")
        
        return "\n".join(lines)
    
    def _generate_fallback_narrative(self, df: pd.DataFrame, user_prompt: str,
                                    metadata: Dict[str, Any],
                                    charts: List[Dict[str, Any]]) -> str:
        """Generate fallback narrative when primary generation fails."""
        lines = [
            "# 📋 ANALYSIS REPORT",
            "",
            f"**Analysis Request**: \"{self._truncate_text(user_prompt, 100)}\"",
            f"**Report Date**: {datetime.now().strftime(self.config.timestamp_format)}",
            "",
            "## 📊 Dataset Overview",
            f"- **Records**: {len(df):,}",
            f"- **Columns**: {len(df.columns)}",
        ]
        
        # Add memory usage if available
        try:
            memory_mb = df.memory_usage(deep=True).sum() / (1024 ** 2)
            lines.append(f"- **Memory**: {memory_mb:.1f} MB")
        except:
            pass
        
        # Add column types
        numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
        categorical_cols = [col for col in df.columns if df[col].dtype == 'object' or pd.api.types.is_categorical_dtype(df[col])]
        datetime_cols = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
        
        if numeric_cols:
            lines.append(f"- **Numeric Metrics**: {', '.join(numeric_cols[:3])}{'...' if len(numeric_cols) > 3 else ''}")
        if categorical_cols:
            lines.append(f"- **Categories**: {', '.join(categorical_cols[:3])}{'...' if len(categorical_cols) > 3 else ''}")
        if datetime_cols:
            lines.append(f"- **Time Dimensions**: {', '.join(datetime_cols[:2])}")
        
        # Add chart recommendations
        if charts:
            lines.append("")
            lines.append("## 📈 Recommended Visualizations")
            for i, chart in enumerate(charts[:3], 1):
                title = chart.get('title', f'Chart {i}')
                lines.append(f"{i}. {title}")
        
        lines.append("")
        lines.append("## 💡 Next Steps")
        lines.append("1. Ask specific questions about relationships between columns")
        lines.append("2. Use manual analysis tools for custom visualizations")
        lines.append("3. Check data quality and column types")
        
        lines.append("")
        lines.append("---")
        lines.append(f"*Generated: {datetime.now().strftime(self.config.timestamp_format)} (Fallback Mode)*")
        
        return "\n".join(lines)
    
    def _update_metrics(self, narrative_length: int, insight_count: int) -> None:
        """Update quality metrics."""
        self._quality_metrics['generated'] += 1
        self._quality_metrics['avg_length'] = (
            (self._quality_metrics['avg_length'] * (self._quality_metrics['generated'] - 1) + narrative_length)
            / self._quality_metrics['generated']
        )
        self._quality_metrics['avg_insights'] = (
            (self._quality_metrics['avg_insights'] * (self._quality_metrics['generated'] - 1) + insight_count)
            / self._quality_metrics['generated']
        )
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text with ellipsis."""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."
    
    def _enhance_narrative_quality(self, narrative: str) -> str:
        """Enhance narrative quality with business context and formatting."""
        # Clean up excessive whitespace
        lines = [line.rstrip() for line in narrative.split('\n')]
        cleaned_lines = []
        
        for i, line in enumerate(lines):
            if line.strip() == '' and i > 0 and lines[i-1].strip() == '':
                continue  # Skip consecutive empty lines
            cleaned_lines.append(line)
        
        narrative = '\n'.join(cleaned_lines)
        
        # Add business context if missing
        business_terms = ['business', 'strategy', 'performance', 'growth', 
                         'efficiency', 'optimization', 'impact', 'value', 'roi']
        
        has_business_context = any(term in narrative.lower() for term in business_terms)
        if not has_business_context and len(narrative) > 100:
            # Add business context paragraph
            context_phrases = [
                "\n\n*This analysis supports data-driven business decision-making and strategic planning.*",
                "\n\n*These findings enable evidence-based strategy development and operational excellence.*",
                "\n\n*Results contribute to performance improvement and resource optimization initiatives.*"
            ]
            narrative += random.choice(context_phrases)
        
        return narrative

# ============================================================================
# CHART TITLE & DESCRIPTION GENERATION
# ============================================================================

class ChartNarrativeGenerator:
    """Generator for chart titles and descriptions."""
    
    def __init__(self):
        self._cache = {}
        self._cache_size = 100
        self._cache_hits = 0
        self._cache_misses = 0
    
    def generate_chart_title(self, chart_type: str, columns: List[str],
                            metadata: Dict[str, Any], df: pd.DataFrame) -> str:
        """
        Generate professional chart titles with business context.
        
        Args:
            chart_type: Type of chart
            columns: Columns used in the chart
            metadata: Dataset metadata
            df: DataFrame
            
        Returns:
            Professional chart title
        """
        cache_key = f"{chart_type}_{'_'.join(sorted(columns))}_{len(df)}"
        
        # Check cache
        if cache_key in self._cache:
            self._cache_hits += 1
            return self._cache[cache_key]
        
        self._cache_misses += 1
        
        if not columns:
            title = f"{CHART_ICONS.get(chart_type, '📊')} {chart_type.replace('_', ' ').title()} Analysis"
        else:
            # Check for insight context
            insights = metadata.get('prioritized_insights', [])
            for insight in insights:
                insight_cols = insight.get('columns', [])
                if set(insight_cols).issubset(set(columns)):
                    title = self._generate_insight_based_title(chart_type, columns, insight)
                    break
            else:
                # Business metric titles
                for col in columns:
                    col_lower = col.lower()
                    if any(term in col_lower for term in BUSINESS_TERM_SYNONYMS['revenue']):
                        title = self._generate_business_metric_title(chart_type, columns, 'Revenue')
                        break
                    elif any(term in col_lower for term in BUSINESS_TERM_SYNONYMS['profit']):
                        title = self._generate_business_metric_title(chart_type, columns, 'Profit')
                        break
                    elif any(term in col_lower for term in BUSINESS_TERM_SYNONYMS['cost']):
                        title = self._generate_business_metric_title(chart_type, columns, 'Cost')
                        break
                else:
                    # Template-based titles
                    title = self._generate_template_based_title(chart_type, columns, metadata, df)
        
        # Cache result
        self._cache[cache_key] = title
        if len(self._cache) > self._cache_size:
            self._cache.pop(next(iter(self._cache)))
        
        return title
    
    def _generate_insight_based_title(self, chart_type: str, columns: List[str],
                                     insight: Dict[str, Any]) -> str:
        """Generate title based on insight type."""
        insight_type = insight.get('type', '')
        
        x_col = columns[0] if len(columns) > 0 else None
        y_col = columns[1] if len(columns) > 1 else None
        
        if insight_type == 'dependency_risk':
            return f"🚨 Dependency Analysis: {insight.get('metric', 'Key Metric')} Concentration"
        elif insight_type == 'strong_pareto':
            return f"🎯 80/20 Analysis: {insight.get('metric', 'Metric')} Distribution"
        elif insight_type == 'business_relationship':
            return f"🔗 Performance Analysis: {insight.get('category', 'Segment')} × {insight.get('metric', 'Metric')}"
        elif insight_type == 'golden_period':
            return f"⭐ Peak Performance Analysis: {insight.get('metric', 'Metric')}"
        elif chart_type == 'histogram' and x_col:
            return f"📊 Distribution of {x_col}"
        elif chart_type == 'bar' and x_col and y_col:
            return f"📈 {y_col} by {x_col}"
        elif chart_type == 'line' and x_col and y_col:
            return f"📉 {y_col} Trend"
        
        return f"{CHART_ICONS.get(chart_type, '📊')} {chart_type.replace('_', ' ').title()} Analysis"
    
    def _generate_business_metric_title(self, chart_type: str, columns: List[str],
                                       metric_name: str) -> str:
        """Generate title for business metrics."""
        icon = CHART_ICONS.get(chart_type, '📊')
        
        title_templates = {
            'histogram': f"{icon} {metric_name} Distribution Analysis",
            'bar': f"{icon} {metric_name} by {columns[0] if columns else 'Category'}",
            'line': f"{icon} {metric_name} Trend Analysis",
            'pie': f"{icon} {metric_name} Composition",
            'scatter': f"{icon} {metric_name} Relationships",
        }
        
        return title_templates.get(chart_type, f"{icon} {metric_name} Analysis")
    
    def _generate_template_based_title(self, chart_type: str, columns: List[str],
                                      metadata: Dict[str, Any], df: pd.DataFrame) -> str:
        """Generate title using templates."""
        x_col = columns[0] if len(columns) > 0 else None
        y_col = columns[1] if len(columns) > 1 else None
        
        # Get semantic types
        x_type = None
        y_type = None
        if x_col and x_col in metadata.get('columns', {}):
            x_type = metadata['columns'][x_col].get('semantic_type')
        if y_col and y_col in metadata.get('columns', {}):
            y_type = metadata['columns'][y_col].get('semantic_type')
        
        # Title templates
        templates = {
            ('line', 'datetime', 'numeric'): "{y} Trend Analysis",
            ('bar', 'categorical', 'numeric'): "{y} Performance by {x}",
            ('histogram', 'numeric', None): "Distribution of {x}",
            ('scatter', 'numeric', 'numeric'): "{y} vs {x} Relationship",
            ('pie', 'categorical', None): "{x} Composition",
            ('pie', 'categorical', 'numeric'): "{x} Value Distribution",
            ('box', 'categorical', 'numeric'): "{y} Distribution by {x}"
        }
        
        key = (chart_type, x_type, y_type)
        if key in templates:
            return f"{CHART_ICONS.get(chart_type, '📊')} " + \
                   templates[key].format(x=x_col or "", y=y_col or "")
        
        # Fallback
        icon = CHART_ICONS.get(chart_type, '📊')
        if x_col and y_col:
            return f"{icon} {y_col} by {x_col}"
        elif x_col:
            return f"{icon} {x_col} Analysis"
        else:
            return f"{icon} {chart_type.replace('_', ' ').title()} Analysis"
    
    def generate_insightful_title(self, chart_type: str, columns: List[str],
                                 df: pd.DataFrame, metadata: Dict[str, Any]) -> str:
        """
        Generate data-driven, insightful chart titles.
        Falls back gracefully to standard titles.
        """
        if not columns or len(df) < 3:
            return self.generate_chart_title(chart_type, columns, metadata, df)
        
        try:
            x_col = columns[0] if len(columns) > 0 else None
            y_col = columns[1] if len(columns) > 1 else None
            
            # Try data-driven insights
            if chart_type == 'line' and x_col and y_col:
                title = self._generate_line_chart_insight_title(df, x_col, y_col)
                if title:
                    return title
            elif chart_type == 'bar' and x_col and y_col:
                title = self._generate_bar_chart_insight_title(df, x_col, y_col)
                if title:
                    return title
            elif chart_type == 'scatter' and x_col and y_col:
                title = self._generate_scatter_chart_insight_title(df, x_col, y_col)
                if title:
                    return title
            elif chart_type == 'histogram' and x_col:
                title = self._generate_histogram_insight_title(df, x_col, metadata)
                if title:
                    return title
                    
        except Exception as e:
            logger.debug(f"Insightful title generation failed: {e}")
        
        # Fall back to standard title
        return self.generate_chart_title(chart_type, columns, metadata, df)
    
    def _generate_line_chart_insight_title(self, df: pd.DataFrame,
                                          x_col: str, y_col: str) -> Optional[str]:
        """Generate insightful title for line charts."""
        try:
            valid_data = df[[x_col, y_col]].dropna()
            if len(valid_data) < 4:
                return None
            
            sorted_data = valid_data.sort_values(x_col)
            y_vals = sorted_data[y_col].values
            
            # Calculate trend
            n = len(y_vals)
            first_q = np.mean(y_vals[:max(3, n//4)])
            last_q = np.mean(y_vals[-max(3, n//4):])
            
            if abs(first_q) > 1e-9:
                change_pct = (last_q - first_q) / abs(first_q)
                
                if change_pct > 0.25:
                    return f"📈 {y_col} Up {change_pct:.0%} (Strong Growth Trend)"
                elif change_pct > 0.1:
                    return f"📈 {y_col} Growing {change_pct:.0%}"
                elif change_pct < -0.25:
                    return f"📉 {y_col} Down {abs(change_pct):.0%} (Significant Decline)"
                elif change_pct < -0.1:
                    return f"📉 {y_col} Declining {abs(change_pct):.0%}"
        except Exception:
            pass
        return None
    
    def _generate_bar_chart_insight_title(self, df: pd.DataFrame,
                                         x_col: str, y_col: str) -> Optional[str]:
        """Generate insightful title for bar charts."""
        try:
            grouped = df.groupby(x_col)[y_col].mean().sort_values(ascending=False)
            if len(grouped) < 3:
                return None
            
            top_val = grouped.iloc[0]
            second_val = grouped.iloc[1]
            top_cat = str(grouped.index[0])
            
            if abs(second_val) > 1e-9:
                lead_ratio = top_val / second_val
                
                if lead_ratio > 3.0:
                    return f"🥇 {y_col}: {top_cat} Leads by {lead_ratio:.1f}x"
                elif lead_ratio > 2.0:
                    return f"🥇 {y_col}: {top_cat} Dominates"
        except Exception:
            pass
        return None
    
    def _generate_scatter_chart_insight_title(self, df: pd.DataFrame,
                                             x_col: str, y_col: str) -> Optional[str]:
        """Generate insightful title for scatter plots."""
        try:
            valid_data = df[[x_col, y_col]].dropna()
            if len(valid_data) < 5:
                return None
            
            corr = valid_data[x_col].corr(valid_data[y_col])
            if not pd.isna(corr):
                if abs(corr) > 0.75:
                    direction = "Positive" if corr > 0 else "Negative"
                    return f"🔗 Strong {direction} Link ({corr:.2f})"
                elif abs(corr) > 0.5:
                    return f"📈 Moderate Correlation ({corr:.2f})"
        except Exception:
            pass
        return None
    
    def _generate_histogram_insight_title(self, df: pd.DataFrame, x_col: str,
                                         metadata: Dict[str, Any]) -> Optional[str]:
        """Generate insightful title for histograms."""
        try:
            if x_col in metadata.get('columns', {}):
                col_meta = metadata['columns'][x_col]
                stats = col_meta.get('numeric_stats', {})
                
                if stats:
                    skew = stats.get('skew', 0)
                    if skew > 1.5:
                        return f"⚖️ {x_col}: Right-Skewed Distribution"
                    elif skew < -1.5:
                        return f"⚖️ {x_col}: Left-Skewed Distribution"
                    
                    outlier_pct = col_meta.get('outlier_score', 0)
                    if outlier_pct > 0.05:
                        return f"⚠️ {x_col} with {outlier_pct:.0%} Outliers"
        except Exception:
            pass
        return None
    
    def generate_chart_description(self, chart_type: str, columns: List[str],
                                  df: pd.DataFrame, metadata: Dict[str, Any]) -> str:
        """
        Generate professional chart descriptions with business context.
        """
        if not columns:
            return "Professional data visualization for analytical insights."
        
        # Start with base description
        base_desc = self._get_base_chart_description(chart_type, columns)
        
        # Add data-driven insights
        data_insight = self._get_data_insight_for_chart(chart_type, columns, df, metadata)
        if data_insight:
            base_desc += f" **Data Insight**: {data_insight}"
        
        # Add business context
        business_context = self._get_business_context_for_columns(columns, metadata)
        if business_context:
            base_desc += f" **Business Context**: {business_context}"
        
        # Add analytical guidance
        guidance = self._get_analytical_guidance(chart_type, columns)
        if guidance:
            base_desc += f" **Analytical Guidance**: {guidance}"
        
        return base_desc
    
    def _get_base_chart_description(self, chart_type: str, columns: List[str]) -> str:
        """Get base chart description."""
        descriptions = {
            'histogram': "Visualizes frequency distribution, showing central tendency, spread, and potential outliers.",
            'bar': "Compares performance across segments for benchmarking and gap analysis.",
            'line': "Tracks metrics over time to identify trends, seasonality, and inflection points.",
            'scatter': "Explores relationships and correlations to identify potential causal links.",
            'pie': "Shows proportional composition and relative contributions of different segments.",
            'box': "Compares distributions across groups, revealing central tendency, spread, and outliers.",
            'violin': "Combines box plot with density estimation for detailed distribution analysis.",
            'heatmap': "Visualizes matrix data to identify patterns and correlations.",
        }
        
        x_col = columns[0] if len(columns) > 0 else None
        y_col = columns[1] if len(columns) > 1 else None
        
        if chart_type == 'histogram' and x_col:
            return f"Distribution analysis of {x_col}, showing frequency and spread."
        elif chart_type == 'bar' and x_col and y_col:
            return f"Comparative analysis of {y_col} across {x_col} segments."
        elif chart_type == 'line' and x_col and y_col:
            return f"Trend analysis of {y_col} over {x_col}, tracking performance changes."
        elif chart_type == 'scatter' and x_col and y_col:
            return f"Relationship analysis between {x_col} and {y_col}."
        elif chart_type == 'pie' and x_col:
            return f"Composition analysis of {x_col}, showing segment proportions."
        
        return descriptions.get(chart_type, "Professional data visualization for business analysis.")
    
    def _get_data_insight_for_chart(self, chart_type: str, columns: List[str],
                                   df: pd.DataFrame, metadata: Dict[str, Any]) -> str:
        """Get data-driven insight for chart."""
        if not columns or len(df) < 3:
            return ""
        
        try:
            if chart_type == 'line' and len(columns) >= 2:
                x_col, y_col = columns[0], columns[1]
                if y_col in df.columns:
                    y_vals = df[y_col].dropna().values
                    if len(y_vals) >= 4:
                        cv = np.std(y_vals) / np.mean(y_vals) if np.mean(y_vals) != 0 else 0
                        if cv > 0.5:
                            return "High variability detected, suggesting multiple performance regimes."
            
            elif chart_type == 'bar' and len(columns) >= 2:
                x_col, y_col = columns[0], columns[1]
                if x_col in df.columns and y_col in df.columns:
                    grouped = df.groupby(x_col)[y_col].mean()
                    if len(grouped) >= 3:
                        spread = grouped.max() - grouped.min()
                        if spread > 0:
                            relative_spread = spread / grouped.mean() if grouped.mean() != 0 else 0
                            if relative_spread > 1.0:
                                return "Wide performance spread indicates significant segment differences."
            
            elif chart_type == 'scatter' and len(columns) >= 2:
                x_col, y_col = columns[0], columns[1]
                corr = df[[x_col, y_col]].corr().iloc[0, 1] if x_col in df.columns and y_col in df.columns else 0
                if not pd.isna(corr) and abs(corr) > 0.6:
                    return f"Shows {'strong positive' if corr > 0 else 'strong negative'} correlation (r={corr:.2f})."
        except Exception:
            pass
        
        return ""
    
    def _get_business_context_for_columns(self, columns: List[str],
                                         metadata: Dict[str, Any]) -> str:
        """Get business context for columns."""
        business_terms = []
        
        for col in columns:
            if col in metadata.get('columns', {}):
                col_meta = metadata['columns'][col]
                
                # Check for business priority
                if col_meta.get('business_priority') == 'high':
                    business_terms.append(f"'{col}' is a key business metric")
                
                # Check for business terms in name
                col_lower = col.lower()
                if any(term in col_lower for term in BUSINESS_TERM_SYNONYMS['revenue']):
                    business_terms.append(f"'{col}' relates to commercial performance")
                elif any(term in col_lower for term in BUSINESS_TERM_SYNONYMS['profit']):
                    business_terms.append(f"'{col}' relates to profitability")
                elif any(term in col_lower for term in BUSINESS_TERM_SYNONYMS['cost']):
                    business_terms.append(f"'{col}' relates to cost management")
        
        if business_terms:
            return f"Focuses on {', '.join(business_terms[:2])}."
        
        return ""
    
    def _get_analytical_guidance(self, chart_type: str, columns: List[str]) -> str:
        """Provide analytical guidance for interpreting the chart."""
        guidance_map = {
            'histogram': "Look for distribution shape (normal, skewed, bimodal) and outlier presence.",
            'bar': "Compare segment heights to identify leaders and laggards. Note performance gaps.",
            'line': "Observe trend direction, seasonality patterns, and inflection points.",
            'scatter': "Assess correlation strength and direction. Look for clusters or outliers.",
            'pie': "Evaluate segment proportions and relative contributions to the whole.",
            'box': "Compare median lines, IQR ranges, and outlier patterns across segments.",
        }
        
        return guidance_map.get(chart_type, "Analyze patterns, trends, and relationships revealed.")
    
    def generate_one_liner(self, chart_type: str, columns: List[str],
                          df: pd.DataFrame, metadata: Dict[str, Any]) -> str:
        """
        Generate concise one-line insights for chart previews.
        """
        if not columns:
            return "Professional data visualization"
        
        icon = CHART_ICONS.get(chart_type, '📊')
        x_col = columns[0] if len(columns) > 0 else None
        y_col = columns[1] if len(columns) > 1 else None
        
        # Check for insight context
        insights = metadata.get('prioritized_insights', [])
        for insight in insights:
            insight_cols = insight.get('columns', [])
            if set(insight_cols).issubset(set(columns)):
                insight_type = insight.get('type', '')
                if insight_type == 'dependency_risk':
                    return f"{icon} Critical dependency visualization"
                elif insight_type == 'strong_pareto':
                    return f"{icon} 80/20 concentration analysis"
                elif insight_type == 'business_relationship':
                    return f"{icon} Top performer analysis"
        
        # Chart-specific one-liners
        if chart_type == 'histogram' and x_col:
            return f"{icon} Distribution analysis of {x_col}"
        elif chart_type == 'bar' and x_col and y_col:
            return f"{icon} {y_col} comparison across {x_col}"
        elif chart_type == 'line' and x_col and y_col:
            return f"{icon} {y_col} trend over {x_col}"
        elif chart_type == 'scatter' and x_col and y_col:
            return f"{icon} {y_col} vs {x_col} relationship"
        elif chart_type == 'pie' and x_col:
            return f"{icon} {x_col} composition analysis"
        
        return f"{icon} Professional {chart_type.replace('_', ' ')} analysis"

# ============================================================================
# PUBLIC API FUNCTIONS
# ============================================================================

# Create default instances
_default_narrative_generator = NarrativeGenerator()
_default_chart_narrative_generator = ChartNarrativeGenerator()

def generate_consultant_narrative(df: pd.DataFrame, user_prompt: str,
                                 metadata: Dict[str, Any],
                                 charts: List[Dict[str, Any]],
                                 config: Optional[NarrativeConfig] = None) -> str:
    """
    Generate professional business intelligence narrative.
    
    Args:
        df: DataFrame being analyzed
        user_prompt: User's original query
        metadata: Enhanced metadata from engine.py with insights
        charts: List of recommended charts with metadata
        config: Narrative configuration
        
    Returns:
        Formatted markdown narrative ready for display
    """
    if config:
        generator = NarrativeGenerator(config)
    else:
        generator = _default_narrative_generator
    
    return generator.generate_consultant_narrative(df, user_prompt, metadata, charts)

def generate_chart_title(chart_type: str, columns: List[str],
                        metadata: Dict[str, Any], df: pd.DataFrame) -> str:
    """
    Generate professional chart titles with business context.
    
    Args:
        chart_type: Type of chart
        columns: Columns used in the chart
        metadata: Dataset metadata
        df: DataFrame
        
    Returns:
        Professional chart title
    """
    return _default_chart_narrative_generator.generate_chart_title(
        chart_type, columns, metadata, df
    )

def generate_insightful_title(chart_type: str, columns: List[str],
                             df: pd.DataFrame, metadata: Dict[str, Any]) -> str:
    """
    Generate data-driven, insightful chart titles.
    Falls back gracefully to standard titles.
    
    Args:
        chart_type: Type of chart
        columns: Columns used in the chart
        df: DataFrame
        metadata: Dataset metadata
        
    Returns:
        Insightful chart title
    """
    return _default_chart_narrative_generator.generate_insightful_title(
        chart_type, columns, df, metadata
    )

def generate_chart_description(chart_type: str, columns: List[str],
                              df: pd.DataFrame, metadata: Dict[str, Any]) -> str:
    """
    Generate professional chart descriptions with business context.
    
    Args:
        chart_type: Type of chart
        columns: Columns used in the chart
        df: DataFrame
        metadata: Dataset metadata
        
    Returns:
        Professional chart description
    """
    return _default_chart_narrative_generator.generate_chart_description(
        chart_type, columns, df, metadata
    )

def generate_one_liner(chart_type: str, columns: List[str],
                      df: pd.DataFrame, metadata: Dict[str, Any]) -> str:
    """
    Generate concise one-line insights for chart previews.
    
    Args:
        chart_type: Type of chart
        columns: Columns used in the chart
        df: DataFrame
        metadata: Dataset metadata
        
    Returns:
        One-line chart description
    """
    return _default_chart_narrative_generator.generate_one_liner(
        chart_type, columns, df, metadata
    )

def format_story_for_display(story: str, max_length: int = 10000) -> str:
    """
    Format story for clean UI display with proper spacing.
    Preserves key sections while ensuring reasonable length.
    
    Args:
        story: The narrative story to format
        max_length: Maximum character length
        
    Returns:
        Formatted story
    """
    if not story:
        return ""
    
    # Early return for short stories
    if len(story) < 1000:
        return story
    
    # Clean up markdown formatting
    lines = story.split('\n')
    formatted_lines = []
    in_list = False
    
    for line in lines:
        line = line.rstrip()
        if not line:
            in_list = False
            if formatted_lines and formatted_lines[-1] != '':
                formatted_lines.append('')
            continue
        
        # Handle headers
        if line.startswith('# '):
            if formatted_lines and formatted_lines[-1] != '':
                formatted_lines.append('')
            formatted_lines.append(line)
            formatted_lines.append('')
            in_list = False
        elif line.startswith('## '):
            if formatted_lines and formatted_lines[-1] != '':
                formatted_lines.append('')
            formatted_lines.append(line)
            in_list = False
        elif line.startswith('### '):
            if formatted_lines and formatted_lines[-1] != '':
                formatted_lines.append('')
            formatted_lines.append(line)
            in_list = False
        
        # Handle lists
        elif line.startswith('• ') or line.startswith('- ') or line.startswith('* '):
            if not in_list and formatted_lines and formatted_lines[-1] != '':
                formatted_lines.append('')
            formatted_lines.append(f"  {line}")
            in_list = True
        elif re.match(r'^\d+\.\s', line):
            if not in_list and formatted_lines and formatted_lines[-1] != '':
                formatted_lines.append('')
            formatted_lines.append(f"  {line}")
            in_list = True
        
        # Handle indented content
        elif line.startswith('  ') and in_list:
            formatted_lines.append(f"    {line.strip()}")
        
        else:
            formatted_lines.append(line)
            in_list = False
    
    # Join with proper spacing
    result = '\n'.join(formatted_lines)
    
    # Ensure reasonable length
    if len(result) > max_length:
        # Try to preserve key sections
        sections = re.split(r'\n## ', result)
        
        if len(sections) > 3:
            # Keep key sections
            preserved_sections = []
            section_titles = ['EXECUTIVE HIGHLIGHT', 'PRIORITY BUSINESS INSIGHTS', 
                             'STRATEGIC RECOMMENDATIONS', 'IMMEDIATE NEXT STEPS']
            
            for section in sections[:4]:  # Keep first 4 sections
                if any(title in section.upper() for title in section_titles):
                    preserved_sections.append(section)
            
            if preserved_sections:
                result = '## '.join(preserved_sections[:3])
                result += "\n\n... *[Report truncated. Full analysis available in detailed view]*"
    
    return result

def extract_insights_from_story(story: str, max_insights: int = 4) -> List[str]:
    """
    Extract key insights from story text for quick consumption.
    
    Args:
        story: The narrative story
        max_insights: Maximum number of insights to extract
        
    Returns:
        List of extracted insights
    """
    if not story:
        return []
    
    insights = []
    
    # Look for insight patterns
    insight_patterns = [
        r'\d+\.\d+x',  # Multipliers like 2.3x
        r'\d+%',  # Percentages
        r'drives\s+\d+%',  # Drives X%
        r'top\s+\d+',  # Top 3
        r'critical\s+dependency',
        r'80/20',
        r'pareto',
        r'correlates',
        r'trend',
        r'growth',
        r'decline',
        r'volatility',
        r'opportunity',
        r'risk',
    ]
    
    # Split into sentences
    sentences = re.split(r'[.!?]+', story)
    
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 30 or len(sentence) > 200:
            continue
        
        # Check for insight indicators
        sentence_lower = sentence.lower()
        if any(re.search(pattern, sentence_lower) for pattern in insight_patterns):
            # Clean the sentence
            clean_sentence = re.sub(r'[#\-•*]\s*', '', sentence)
            clean_sentence = re.sub(r'\*\*', '', clean_sentence)
            clean_sentence = re.sub(r'\*', '', clean_sentence)
            clean_sentence = re.sub(r'\[.*?\]', '', clean_sentence)
            
            if 30 < len(clean_sentence) < 150:
                insights.append(clean_sentence + '.')
        
        if len(insights) >= max_insights * 2:
            break
    
    # Deduplicate
    seen = set()
    unique_insights = []
    for insight in insights:
        key = re.sub(r'[^\w\s]', '', insight.lower())[:50]
        if key not in seen:
            unique_insights.append(insight)
            seen.add(key)
    
    return unique_insights[:max_insights]

def enhance_with_business_context(text: str) -> str:
    """
    Enhance text with business context and professional phrasing.
    
    Args:
        text: Text to enhance
        
    Returns:
        Enhanced text
    """
    if not text or len(text) < 50:
        return text or ""
    
    # Check if already has business context
    business_terms = ['business', 'strategy', 'performance', 'growth', 
                     'efficiency', 'optimization', 'impact', 'value', 'roi']
    
    has_context = any(term in text.lower() for term in business_terms)
    
    if not has_context:
        context_phrases = [
            " This analysis supports data-driven business decision-making.",
            " These findings enable evidence-based strategy development.",
            " Results contribute to operational excellence and performance improvement.",
            " Insights support strategic planning and resource optimization.",
        ]
        text += random.choice(context_phrases)
    
    return text

def validate_narrative_length(narrative: str, max_chars: int = 20000) -> Tuple[bool, str]:
    """
    Validate narrative length and content quality.
    
    Args:
        narrative: Narrative to validate
        max_chars: Maximum allowed characters
        
    Returns:
        (is_valid, message)
    """
    if not narrative:
        return False, "Narrative is empty"
    
    if len(narrative) > max_chars:
        return False, f"Narrative exceeds maximum length ({len(narrative)} > {max_chars} chars)"
    
    # Check for professional structure
    has_headers = any(line.startswith('#') for line in narrative.split('\n'))
    has_insights = any(icon in narrative for icon in ['🚨', '🎯', '💡', '⭐', '🔗'])
    
    if not has_headers:
        return False, "Narrative lacks professional structure (no headers)"
    
    if not has_insights:
        return False, "Narrative lacks business insights"
    
    return True, "Narrative validated successfully"

def sanitize_for_display(text: str) -> str:
    """
    Sanitize text for safe display (remove PII, format consistently).
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove potential PII patterns
    patterns = [
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Phone
        r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14})\b',  # Credit card
    ]
    
    sanitized = text
    for pattern in patterns:
        sanitized = re.sub(pattern, '[REDACTED]', sanitized, flags=re.IGNORECASE)
    
    # Normalize whitespace
    sanitized = re.sub(r'\s+', ' ', sanitized)
    sanitized = sanitized.strip()
    
    return sanitized

def calculate_narrative_quality(narrative: str) -> Dict[str, float]:
    """
    Calculate narrative quality metrics.
    
    Args:
        narrative: Narrative to evaluate
        
    Returns:
        Dictionary of quality metrics
    """
    if not narrative:
        return {'overall': 0, 'structure': 0, 'insights': 0, 'actionability': 0, 'clarity': 0}
    
    metrics = {
        'structure': 0.0,
        'insights': 0.0,
        'actionability': 0.0,
        'clarity': 0.0
    }
    
    # Structure score
    lines = narrative.split('\n')
    header_count = sum(1 for line in lines if line.startswith('#'))
    list_count = sum(1 for line in lines if re.match(r'^\s*[•\-*]\s', line) or re.match(r'^\s*\d+\.\s', line))
    
    metrics['structure'] = min(1.0, (header_count * 0.3) + (list_count * 0.02))
    
    # Insights score
    insight_icons = ['🚨', '🎯', '💡', '⭐', '🔗', '📈', '⚡', '📊', '✅', '⚠️']
    icon_count = sum(1 for icon in insight_icons if icon in narrative)
    metrics['insights'] = min(1.0, icon_count * 0.2)
    
    # Actionability score
    action_terms = ['action', 'recommend', 'suggest', 'next step', 'plan', 'initiative']
    action_count = sum(1 for term in action_terms if term.lower() in narrative.lower())
    metrics['actionability'] = min(1.0, action_count * 0.15)
    
    # Clarity score (simple proxy)
    avg_line_length = sum(len(line) for line in lines) / max(1, len(lines))
    metrics['clarity'] = 1.0 if 40 <= avg_line_length <= 120 else 0.5
    
    # Overall score
    weights = {'structure': 0.3, 'insights': 0.4, 'actionability': 0.2, 'clarity': 0.1}
    metrics['overall'] = sum(metrics[k] * weights[k] for k in weights)
    
    return {k: round(v, 2) for k, v in metrics.items()}

# Legacy function for backward compatibility
def generate_executive_summary(df: pd.DataFrame, metadata: Dict[str, Any],
                              top_insights: List[Dict[str, Any]]) -> str:
    """Legacy function for backward compatibility."""
    return generate_consultant_narrative(df, "", metadata, [])

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "generate_chart_title",
    "generate_insightful_title",
    "generate_chart_description",
    "generate_one_liner",
    ]

# Version and metadata
__version__ = "1.0.0"
__author__ = "Data Explorer Pro"
__description__ = "Production-grade business intelligence storytelling engine"