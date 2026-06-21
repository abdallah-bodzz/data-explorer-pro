# services/report_service.py
"""
Report Service – Orchestrates report generation, template management, and validation.
Wraps the low‑level HTML rendering engine and provides a clean UI interface.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional, Tuple

import plotly.graph_objects as go
import pandas as pd

from reporting.html_export import CleanReportGenerator

logger = logging.getLogger(__name__)


class ReportService:
    """
    Service for report generation, template management, and validation.

    This service provides a clean interface for the UI layer to manage report
    templates, validate sections and charts, and generate HTML reports.
    It delegates low‑level HTML rendering to the CleanReportGenerator.
    """

    # Professional report templates
    REPORT_TEMPLATES = {
        "executive_dashboard": {
            "name": "Executive Dashboard Summary",
            "description": "High-level overview for C-suite: Key metrics, trends, and actionable insights.",
            "icon": "🎯",
            "sections": [
                {
                    "title": "At-a-Glance Metrics",
                    "content": "**Key Performance Indicators**\n\n- **Core Metric 1**: [Insert value from data, e.g., Total Revenue: $X]\n- **Core Metric 2**: [Insert value, e.g., Growth Rate: Y%]\n- **Efficiency Metric**: [Insert, e.g., Conversion Rate: Z%]\n\nUse a pie chart or bar chart here to visualize metric distribution. Keep text concise.",
                    "chart_ids": []
                },
                {
                    "title": "Trend Highlights",
                    "content": "**Quick Trend Overview**\n\n- Positive: [e.g., Upward trend in key metric over last quarter]\n- Watch: [e.g., Slight dip in secondary metric]\n\nUse a line chart to show time-based trends. Limit to 2-3 lines for clarity.",
                    "chart_ids": []
                },
                {
                    "title": "Top Insights",
                    "content": "**Actionable Takeaways**\n\n1. **Insight 1**: [Data-driven finding, e.g., Category A drives 60% of results—double down here]\n2. **Insight 2**: [e.g., Correlation between X and Y suggests optimization opportunity]\n\nUse a bubble chart or heatmap to support insights.",
                    "chart_ids": []
                },
                {
                    "title": "Next Steps & Recommendations",
                    "content": "**Priority Actions**\n\n- Action 1: [Specific, measurable step based on data]\n- Action 2: [Another data-backed recommendation]\n\nEnd with a call to action. Use a simple bar chart if ranking priorities.",
                    "chart_ids": []
                }
            ]
        },
        "trend_analysis": {
            "name": "Trend Analysis Report",
            "description": "Deep dive into patterns over time. Ideal for monitoring changes and forecasting.",
            "icon": "📈",
            "sections": [
                {
                    "title": "Report Overview",
                    "content": "**Purpose & Scope**\n\nThis report analyzes trends in [key variables, e.g., sales, user engagement] from [date range].\n\nAdd a line chart here for overall trend preview.",
                    "chart_ids": []
                },
                {
                    "title": "Historical Trends",
                    "content": "**Timeline Analysis**\n\n- Period 1: [Describe early trends, e.g., Steady growth at X%]\n- Period 2: [e.g., Peak in Q3 due to Y factor]\n\nUse line charts with multiple series.",
                    "chart_ids": []
                },
                {
                    "title": "Key Drivers & Correlations",
                    "content": "**What's Influencing Trends?**\n\n- Driver 1: [e.g., Strong correlation between marketing spend and conversions]\n- Anomaly: [e.g., Dip explained by external factor]\n\nUse scatter or heatmap to show relationships.",
                    "chart_ids": []
                },
                {
                    "title": "Future Outlook & Recommendations",
                    "content": "**Projections & Actions**\n\n- Projected Trend: [Informal forecast based on patterns]\n- Rec 1: [Data-backed suggestion]\n\nEnd with a line chart extending trends.",
                    "chart_ids": []
                }
            ]
        },
        "performance_comparison": {
            "name": "Comparative Performance Report",
            "description": "Side-by-side analysis of categories, groups, or periods.",
            "icon": "📊",
            "sections": [
                {
                    "title": "Comparison Framework",
                    "content": "**What We're Comparing**\n\n- Groups: [e.g., Regions: North vs. South]\n- Metrics: [e.g., Revenue, Efficiency]\n- Timeframe: [e.g., Last 12 months]\n\nStart with a bar chart overview.",
                    "chart_ids": []
                },
                {
                    "title": "Overall Performance Rankings",
                    "content": "**Metric-by-Metric Analysis**\n\n- Metric 1: [Box plot showing distributions]\n- Metric 2: [Violin plot for density insights]\n\nUse box/violin for distributions, bars for averages.",
                    "chart_ids": []
                },
                {
                    "title": "Insights & Optimization",
                    "content": "**What It Means & How to Improve**\n\n- Strength Transfer: [Apply best practices]\n- Opportunity: [Close gaps by addressing root causes]\n\nEnd with prioritized actions.",
                    "chart_ids": []
                }
            ]
        }
    }

    def __init__(self, state_manager=None):
        """
        Initialise the ReportService.

        Args:
            state_manager: Optional state manager for session state access.
                           Not used directly, but kept for future extension.
        """
        self.state = state_manager
        self._templates = self.REPORT_TEMPLATES

    # ===== Template Management =====

    def get_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Return all available report templates.

        Returns:
            Dictionary of template_key -> template_data.
        """
        return self._templates.copy()

    def get_template(self, template_key: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific template by key.

        Args:
            template_key: The template identifier.

        Returns:
            Template data dict, or None if not found.
        """
        return self._templates.get(template_key)

    def load_template(self, template_key: str) -> List[Dict[str, Any]]:
        """
        Load a template and return its sections with fresh IDs.

        Args:
            template_key: Key of the template to load ('executive_dashboard', etc.)
                          or 'custom' for a blank template.

        Returns:
            List of section dicts with fresh UUIDs.

        Raises:
            ValueError: If the template_key is not found.
        """
        if template_key == "custom":
            return [{
                'id': str(uuid.uuid4()),
                'title': 'Executive Summary',
                'content': '',
                'chart_ids': []
            }]

        template = self._templates.get(template_key)
        if not template:
            raise ValueError(f"Template '{template_key}' not found")

        sections = []
        for section_template in template['sections']:
            sections.append({
                'id': str(uuid.uuid4()),
                'title': section_template['title'],
                'content': section_template['content'],
                'chart_ids': []
            })

        return sections

    def get_template_names(self) -> List[str]:
        """Return a list of all available template keys."""
        return list(self._templates.keys())

    def get_template_display_names(self) -> Dict[str, str]:
        """Return mapping of template_key -> display name."""
        return {key: data['name'] for key, data in self._templates.items()}

    # ===== Validation =====

    def validate_sections(self, sections: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """
        Validate that sections have required fields.

        Args:
            sections: List of section dicts.

        Returns:
            (is_valid, error_message)
        """
        if not sections:
            return False, "Sections list is empty"

        for i, section in enumerate(sections):
            if not section.get('title'):
                return False, f"Section {i+1} is missing a title"
            if 'content' not in section:
                return False, f"Section '{section.get('title', 'Untitled')}' is missing content"
            if not isinstance(section.get('chart_ids', []), list):
                return False, f"Section '{section.get('title', 'Untitled')}' has invalid chart_ids (must be a list)"

        return True, "All sections are valid"

    def validate_charts(self, charts: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """
        Validate that charts have required fields.

        Args:
            charts: List of chart dicts.

        Returns:
            (is_valid, error_message)
        """
        if not charts:
            return True, "No charts to validate"

        for i, chart in enumerate(charts):
            if not chart.get('id'):
                return False, f"Chart {i+1} is missing an ID"
            if not chart.get('figure'):
                return False, f"Chart '{chart.get('name', 'Untitled')}' has no figure"

        return True, "All charts are valid"

    def validate_report(self, sections: List[Dict[str, Any]], charts: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """
        Validate both sections and charts for a complete report.

        Args:
            sections: List of section dicts.
            charts: List of chart dicts.

        Returns:
            (is_valid, error_message)
        """
        sections_valid, sections_msg = self.validate_sections(sections)
        if not sections_valid:
            return False, sections_msg

        charts_valid, charts_msg = self.validate_charts(charts)
        if not charts_valid:
            return False, charts_msg

        # Check that all chart_ids in sections reference existing charts
        chart_ids = {chart['id'] for chart in charts if chart.get('id')}
        for i, section in enumerate(sections):
            for chart_id in section.get('chart_ids', []):
                if chart_id not in chart_ids:
                    return False, f"Section '{section.get('title', 'Untitled')}' references chart '{chart_id}' which doesn't exist"

        return True, "Report is valid"

    # ===== Report Generation =====

    def generate_html_report(
        self,
        title: str,
        author: str,
        sections: List[Dict[str, Any]],
        charts: List[Dict[str, Any]],
        include_toc: bool = True
    ) -> str:
        """
        Generate a complete HTML report from sections and charts.

        Args:
            title: Report title.
            author: Author name.
            sections: List of section dicts with 'title', 'content', 'chart_ids'.
            charts: List of chart dicts with 'id', 'name', 'figure', 'description'.
            include_toc: Whether to include a table of contents.

        Returns:
            HTML string of the complete report.

        Raises:
            ValueError: If sections are empty or validation fails.
        """
        if not sections:
            raise ValueError("Cannot generate report with empty sections")

        # Validate first
        valid, msg = self.validate_report(sections, charts)
        if not valid:
            raise ValueError(f"Report validation failed: {msg}")

        # Convert charts to exportable format (HTML snippets)
        export_charts = self._prepare_charts_for_export(charts)

        return CleanReportGenerator.generate_html_report(
            title=title,
            author=author,
            sections=sections,
            charts=export_charts,
            include_toc=include_toc
        )

    def generate_ai_report(
        self,
        title: str,
        analyst: str,
        messages: List[Dict[str, Any]],
        df: Optional[pd.DataFrame] = None
    ) -> str:
        """
        Generate an HTML report from AI conversation history.

        Args:
            title: Report title.
            analyst: Analyst name.
            messages: List of chat messages (user + assistant).
            df: Optional DataFrame for chart generation.

        Returns:
            HTML string of the AI report.
        """
        from services.chart_service import ChartService
        chart_service = ChartService()

        sections = []
        charts = []

        for i, msg in enumerate(messages):
            if msg.get('role') == 'user':
                sections.append({
                    'id': f"question-{i}",
                    'title': f"Question {len([s for s in sections if 'Question' in s.get('title', '')]) + 1}",
                    'content': f"**User Query:** {msg.get('content', '')}",
                    'chart_ids': []
                })
            elif msg.get('role') == 'assistant' and isinstance(msg.get('content'), dict):
                content = msg['content']
                section_charts = []

                if content.get('charts') and df is not None:
                    for j, chart_suggestion in enumerate(content.get('charts', [])):
                        try:
                            chart_fig = chart_service.create_chart_from_suggestion(df, chart_suggestion)
                            if chart_fig:
                                chart_id = f"ai_chart_{i}_{j}"
                                chart_name = chart_suggestion.get('title', f'Chart {j+1}')
                                charts.append({
                                    'id': chart_id,
                                    'name': chart_name,
                                    'chart_type': chart_suggestion.get('chart_type', 'chart'),
                                    'figure': chart_fig,
                                    'description': chart_suggestion.get('description', '')
                                })
                                section_charts.append(chart_id)
                        except Exception as e:
                            logger.warning(f"Failed to generate AI chart: {e}")

                section_content = content.get('story', 'AI analysis completed.')

                if content.get('insights'):
                    section_content += "\n\n### Key Insights\n"
                    for insight in content.get('insights', []):
                        if isinstance(insight, dict):
                            section_content += f"- **{insight.get('title', 'Insight')}**: {insight.get('description', '')}\n"
                        else:
                            section_content += f"- {insight}\n"

                sections.append({
                    'id': f"analysis-{i}",
                    'title': f"Analysis {len([s for s in sections if 'Analysis' in s.get('title', '')]) + 1}",
                    'content': section_content,
                    'chart_ids': section_charts
                })

        include_toc = len(sections) > 1
        return self.generate_html_report(title, analyst, sections, charts, include_toc)

    # ===== Chart Export Helpers =====

    def _prepare_charts_for_export(self, charts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert charts with Plotly figures to exportable HTML snippets.

        Args:
            charts: List of chart dicts with Plotly figures.

        Returns:
            List of chart dicts with HTML snippets.
        """
        export_charts = []
        for chart in charts:
            if chart.get('figure'):
                try:
                    html = self._chart_to_html(chart['figure'])
                    export_charts.append({
                        'id': chart.get('id', str(uuid.uuid4())),
                        'name': chart.get('name', 'Unnamed Chart'),
                        'chart_type': chart.get('chart_type', 'chart'),
                        'html': html,
                        'description': chart.get('description', '')
                    })
                except Exception as e:
                    logger.warning(f"Failed to convert chart '{chart.get('name', '')}' to HTML: {e}")
        return export_charts

    def _chart_to_html(self, fig: go.Figure) -> str:
        """
        Convert a Plotly figure to an HTML snippet.

        Args:
            fig: The Plotly figure.

        Returns:
            HTML snippet.
        """
        import plotly.io as pio
        return pio.to_html(fig, full_html=False, include_plotlyjs=False)

    def export_chart(self, fig: go.Figure, format: str = 'png',
                     width: int = 1200, height: int = 800) -> bytes:
        """
        Export a Plotly figure to image bytes.

        Args:
            fig: The Plotly figure.
            format: Image format ('png', 'jpeg', 'webp', 'svg', 'pdf').
            width: Image width in pixels.
            height: Image height in pixels.

        Returns:
            Image bytes.

        Raises:
            ValueError: If the figure is None or format is unsupported.
        """
        if fig is None:
            raise ValueError("Cannot export None figure")

        try:
            return fig.to_image(format=format, width=width, height=height)
        except Exception as e:
            logger.exception(f"Error exporting chart to {format}: {e}")
            raise ValueError(f"Export failed: {str(e)}")

    # ===== Section Management Helpers =====

    def create_empty_section(self, title: str = "New Section") -> Dict[str, Any]:
        """Create a new empty section with a fresh ID."""
        return {
            'id': str(uuid.uuid4()),
            'title': title,
            'content': '',
            'chart_ids': []
        }

    def create_chart_stub(self, name: str = "New Chart", chart_type: str = "histogram") -> Dict[str, Any]:
        """Create a new chart stub with a fresh ID."""
        return {
            'id': str(uuid.uuid4()),
            'name': name,
            'chart_type': chart_type,
            'config': {},
            'figure': None,
            'description': ''
        }

    # ===== Report Statistics =====

    def get_report_stats(self, sections: List[Dict[str, Any]], charts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get statistics about a report.

        Args:
            sections: List of section dicts.
            charts: List of chart dicts.

        Returns:
            Dictionary with report statistics.
        """
        total_charts = len(charts)
        assigned_charts = sum(1 for chart in charts if self._is_chart_assigned(chart['id'], sections))
        unassigned_charts = total_charts - assigned_charts

        total_sections = len(sections)
        empty_sections = sum(1 for s in sections if not s.get('content', '').strip())
        sections_with_charts = sum(1 for s in sections if s.get('chart_ids'))

        return {
            'total_sections': total_sections,
            'empty_sections': empty_sections,
            'sections_with_charts': sections_with_charts,
            'total_charts': total_charts,
            'assigned_charts': assigned_charts,
            'unassigned_charts': unassigned_charts,
            'content_completeness': round((total_sections - empty_sections) / max(1, total_sections) * 100, 1)
        }

    def _is_chart_assigned(self, chart_id: str, sections: List[Dict[str, Any]]) -> bool:
        """Check if a chart is assigned to any section."""
        for section in sections:
            if chart_id in section.get('chart_ids', []):
                return True
        return False