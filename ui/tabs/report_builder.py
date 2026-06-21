# ui/tabs/report_builder.py
"""
Report Builder Tab – Professional report creation with sections and charts.
Manages report structure, chart library, and export functionality.
Delegates chart creation to ChartService and report operations to ReportService.
"""

import streamlit as st
import pandas as pd
import numpy as np
import uuid
import time
from typing import Dict, Any, List, Optional

from ui.tabs.chart_studio import ChartManager
from services.chart_service import ChartService
from services.report_service import ReportService
from reporting.html_export import export_report_interface

# ===== GLOBAL SERVICES =====
_chart_service = None
_report_service = None


def get_chart_service() -> ChartService:
    """Lazy initialisation of the ChartService singleton."""
    global _chart_service
    if _chart_service is None:
        _chart_service = ChartService()
    return _chart_service


def get_report_service() -> ReportService:
    """Lazy initialisation of the ReportService singleton."""
    global _report_service
    if _report_service is None:
        _report_service = ReportService()
    return _report_service


# ===== POLISHED SESSION STATE =====
def init_report_builder_state():
    """Initialize clean report builder state with performance optimizations"""
    defaults = {
        'report_builder_sections': [
            {
                'id': str(uuid.uuid4()),
                'title': 'Executive Summary',
                'content': 'Write your introduction and key findings here...',
                'chart_ids': []
            }
        ],
        'report_builder_charts': [],
        'report_active_tab': 'content',
        'report_editing_chart': None,
        'report_builder_welcome_shown': False,
        'custom_templates': {},
        'active_chart_section': None,
        'show_save_template': False
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ===== POLISHED UI COMPONENTS =====
def render_polished_template_selection():
    """Professional template selection with enhanced visual design"""
    with st.expander("🚀 **Start with a Professional Template**", 
                   expanded=not st.session_state.report_builder_sections[0]['content'].strip()):
        st.markdown("""
        <div style='text-align: center; margin-bottom: 2rem;'>
            <h3 style='margin-bottom: 0.5rem;'>Choose Your Report Foundation</h3>
            <p style='color: #666; margin-bottom: 0;'>Select a professionally designed template or start with a blank canvas</p>
        </div>
        """, unsafe_allow_html=True)

        # Get templates from service
        report_service = get_report_service()
        templates = report_service.get_templates()
        templates_list = list(templates.items())

        cols = st.columns(3)
        for i, (key, template) in enumerate(templates_list):
            with cols[i % 3]:
                with st.container(border=True):
                    st.markdown(f"<h4 style='margin-bottom: 0.5rem;'>{template.get('icon', '📄')} {template['name']}</h4>", 
                               unsafe_allow_html=True)
                    st.caption(template['description'])
                    section_count = len(template['sections'])
                    st.markdown(f"<div style='display: flex; justify-content: space-between; align-items: center; margin-top: 1rem;'>"
                               f"<span style='padding: 0.2rem 0.5rem; border-radius: 12px; font-size: 0.8rem;'>"
                               f"{section_count} section{'s' if section_count != 1 else ''}</span>"
                               f"</div>", unsafe_allow_html=True)
                    if st.button("Use This Template", 
                                key=f"temp_{key}", 
                                use_container_width=True,
                                type="primary"):
                        load_template(key)
                        st.success(f"✓ {template['name']} template loaded!")
                        st.rerun()

        st.markdown("<hr style='margin: 2rem 0;'>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.container(border=True):
                st.markdown("<div style='text-align: center;'>"
                           "<h4 style='margin-bottom: 0.5rem;'>🎨 Start from Scratch</h4>"
                           "<p style='color: #666; margin-bottom: 1rem;'>Complete creative control with a blank canvas</p>"
                           "</div>", unsafe_allow_html=True)
                if st.button("Create Blank Report", 
                           key="blank_temp", 
                           use_container_width=True,
                           type="secondary"):
                    load_template("custom")
                    st.success("✓ Blank report created!")
                    st.rerun()

        st.markdown("""
        **Build Your Report in 4 Simple Steps:**
        1. **🎯 Choose Foundation** - Select a template that matches your communication goal
        2. **📝 Craft Narrative** - Write compelling content in organized sections  
        3. **📊 Add Evidence** - Create and assign visualizations to support your story
        4. **👁️ Polish & Share** - Preview, refine, and export your professional report
        *💡 Tip: Start with a template for structure, then customize to make it your own.*
        """)


def render_polished_content_editor(df):
    """Polished content editor with professional organization"""
    st.header("📝 Build Your Report")
    render_polished_template_selection()
    st.markdown("---")
    with st.container():
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.subheader("Report Structure")
            st.caption("Organize your content into logical, flowing sections.")
        with col2:
            total_charts = sum(len(section.get('chart_ids', [])) for section in st.session_state.report_builder_sections)
            st.metric("Sections", len(st.session_state.report_builder_sections))
        with col3:
            st.metric("Charts", total_charts)

    if st.button("➕ **Add New Section**", 
                use_container_width=True, 
                type="secondary",
                help="Add a new content section to your report structure"):
        add_new_section()
        st.rerun()

    st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)

    for i, section in enumerate(st.session_state.report_builder_sections):
        render_polished_section_ui(i, section, df)


def render_polished_section_ui(index: int, section: Dict[str, Any], df: pd.DataFrame):
    """Ultra-polished section UI with professional styling"""
    with st.container(border=True):
        header_col1, header_col2, header_col3 = st.columns([4, 1, 1])

        with header_col1:
            section['title'] = st.text_input(
                "Section Title",
                value=section['title'],
                key=f"title_{section['id']}",
                placeholder="Enter a clear, descriptive section title...",
                label_visibility="collapsed"
            )

        with header_col2:
            new_pos = st.number_input(
                "Position",
                min_value=1,
                max_value=len(st.session_state.report_builder_sections),
                value=index+1,
                key=f"order_{section['id']}",
                label_visibility="collapsed",
                help=f"Change section position (1-{len(st.session_state.report_builder_sections)})"
            )
            if new_pos != index+1:
                move_section_to_index(index, new_pos-1)
                st.rerun()

        with header_col3:
            if len(st.session_state.report_builder_sections) > 1:
                if st.button("🗑️", 
                           key=f"del_{section['id']}", 
                           use_container_width=True,
                           help="Delete this section and all its content"):
                    delete_section(index)
                    st.rerun()

        st.markdown("**Content**")
        section['content'] = st.text_area(
            "Write your analysis...",
            value=section['content'],
            height=120,
            key=f"content_{section['id']}",
            placeholder="""Craft your narrative here...

• Use bullet points for clarity and scannability
• **Emphasize** key findings and critical metrics  
• Reference charts that support your data stories
• Keep paragraphs concise and focused""",
            label_visibility="collapsed"
        )

        render_polished_section_charts(section)

        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            available_charts = [c for c in st.session_state.report_builder_charts 
                               if c['id'] not in section.get('chart_ids', [])]
            if available_charts:
                with st.popover("📥 Add Existing Chart", use_container_width=True):
                    st.markdown("**Select from Your Chart Library:**")
                    chart_options = {c['id']: f"{c.get('name', 'Unnamed Chart')} • {c.get('chart_type', 'chart').title()}" 
                                   for c in available_charts}
                    selected_chart = st.selectbox(
                        "Choose chart to add",
                        options=list(chart_options.keys()),
                        format_func=lambda x: chart_options[x],
                        key=f"add_existing_chart_{section['id']}",
                        label_visibility="collapsed"
                    )
                    if st.button("Add to Section", 
                               key=f"add_existing_btn_{section['id']}",
                               use_container_width=True,
                               type="primary"):
                        section['chart_ids'].append(selected_chart)
                        st.success("✓ Chart added to section!")
                        st.rerun()
            else:
                st.button("📥 Add Existing Chart", 
                         disabled=True, 
                         use_container_width=True,
                         help="No available charts in your library. Create charts first.",
                         key=f"add_existing_chart_btn_{section['id']}")

        with col2:
            if st.button("🆕 Create New Chart", 
                        key=f"add_chart_btn_{section['id']}", 
                        use_container_width=True,
                        help="Create and add a new visualization"):
                st.session_state.active_chart_section = section['id']
                st.rerun()

        with col3:
            chart_count = len(section.get('chart_ids', []))
            st.metric("Charts in Section", chart_count, label_visibility="visible")

        if st.session_state.get('active_chart_section') == section['id']:
            render_polished_inline_chart_creator(section, df)


def render_polished_section_charts(section: Dict[str, Any]):
    """Polished chart display with professional visual organization"""
    if section['chart_ids']:
        st.markdown("**📊 Visualizations in This Section**")
        for chart_id in section['chart_ids']:
            chart = get_chart_by_id(chart_id)
            if chart:
                with st.container(border=True):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"**{chart.get('name', 'Unnamed Chart')}**")
                        if chart.get('description'):
                            st.caption(chart['description'])
                        chart_type = chart.get('chart_type', 'chart').title()
                        st.markdown(f"<code style='background: #f0f2f6; padding: 0.2rem 0.5rem; border-radius: 8px; font-size: 0.8rem;'>{chart_type}</code>", 
                                   unsafe_allow_html=True)
                    with col2:
                        if st.button("Remove", 
                                   key=f"remove_{chart_id}_{section['id']}", 
                                   use_container_width=True,
                                   type="secondary"):
                            section['chart_ids'].remove(chart_id)
                            st.rerun()


def get_column_types(df: pd.DataFrame):
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()
    datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
    return numeric_cols, categorical_cols, datetime_cols


def render_polished_inline_chart_creator(section: Dict[str, Any], df: pd.DataFrame):
    """Professional inline chart creator with enhanced UX"""
    with st.container(border=True):
        st.subheader(f"🎨 Create New Chart for: {section['title']}")

        numeric_cols, categorical_cols, datetime_cols = get_column_types(df)
        chart_manager = ChartManager(
            df, numeric_cols, categorical_cols, datetime_cols,
            key_prefix=f"inline_{section['id']}"
        )

        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("**Chart Configuration**")
            chart_types = chart_manager.get_chart_types_display()
            chart_type = st.selectbox(
                "Chart Type",
                options=list(chart_types.keys()),
                format_func=lambda x: chart_types[x],
                key=f"inline_type_{section['id']}",
                help="Choose the visualization type that best tells your data story"
            )
            chart_name = st.text_input(
                "Chart Name", 
                value=f"{section['title']} Visualization",
                key=f"name_{section['id']}",
                placeholder="Enter a descriptive chart name...",
                help="A clear name helps readers understand the chart's purpose"
            )
            chart_description = st.text_input(
                "Chart Description",
                value="",
                key=f"desc_{section['id']}",
                placeholder="Briefly describe the key insight this chart reveals...",
                help="Explain what story this visualization tells and why it matters"
            )

            try:
                config = chart_manager.get_configuration_preserved(chart_type, {})
            except ValueError as e:
                st.error(f"Configuration error: {str(e)}")
                return

        with col2:
            st.markdown("**Live Preview**")
            preview_container = st.container()
            with preview_container:
                if config and any(config.values()):
                    try:
                        preview_fig = get_chart_service().create_chart(df, chart_type, config)
                        if preview_fig:
                            st.plotly_chart(preview_fig, use_container_width=True, height=250)
                            st.caption("Live preview - adjust settings to refine your visualization")
                        else:
                            st.info("👆 Configure chart settings to see a live preview")
                    except Exception as e:
                        st.error(f"Preview unavailable: {str(e)}")
                else:
                    st.info("👆 Configure chart settings to see a live preview")

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("✅ Create & Add to Section", 
                        type="primary", 
                        use_container_width=True,
                        disabled=not chart_name.strip(),
                        help="Create this chart and add it to the current section"):
                new_chart = create_chart_from_config(chart_name, chart_description, chart_type, config, df)
                if new_chart:
                    section['chart_ids'].append(new_chart['id'])
                    st.session_state.active_chart_section = None
                    st.success("✓ Chart created and added to section!")
                    st.rerun()

        with col2:
            if st.button("❌ Cancel Creation", 
                        use_container_width=True,
                        type="secondary",
                        help="Close chart creator without saving"):
                st.session_state.active_chart_section = None
                st.rerun()


def render_polished_visualizations_tab(df):
    """Professional chart gallery with enhanced organization"""
    st.header("📊 Chart Library")

    with st.container(border=True):
        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
        with col1:
            st.subheader("Visualization Management")
            st.caption("Create, organize, and manage all your data visualizations")
        with col2:
            if st.button("📈 New Chart", use_container_width=True, type="primary"):
                add_new_chart()
                st.rerun()
        with col3:
            if st.button("📊 Bar", use_container_width=True):
                add_quick_chart('bar')
                st.rerun()
        with col4:
            if st.button("📈 Line", use_container_width=True):
                add_quick_chart('line')
                st.rerun()
        with col5:
            if st.button("🫧 Scatter", use_container_width=True):
                add_quick_chart('scatter')
                st.rerun()

    if not st.session_state.report_builder_charts:
        st.info("""
        ## 📊 No Charts Yet
        Your chart library is empty. Create your first visualization to start building your report.
        **Quick Start Options:**
        - Use the buttons above to create common chart types
        - Create charts directly within sections in the **Write Content** tab
        - Explore different visualization types for your data stories
        *💡 Tip: Create charts that directly support your key narrative points.*
        """)
    else:
        st.markdown(f"**Your Chart Library ({len(st.session_state.report_builder_charts)} charts)**")
        cols = st.columns(2)
        for i, chart in enumerate(st.session_state.report_builder_charts):
            with cols[i % 2]:
                render_polished_chart_card(chart, i, df)


def render_polished_chart_card(chart, index, df):
    """Professional chart card with enhanced layout"""
    with st.container(border=True):
        col1, col2 = st.columns([4, 1])
        with col1:
            chart['name'] = st.text_input(
                "Chart Name",
                value=chart.get('name', 'Unnamed Chart'),
                key=f"chart_name_{chart['id']}",
                placeholder="Enter chart name...",
                label_visibility="collapsed"
            )
        with col2:
            config_state = st.session_state.get('report_editing_chart') == chart['id']
            if st.button("⚙️" if not config_state else "✏️", 
                       key=f"config_{chart['id']}", 
                       use_container_width=True,
                       help="Configure chart settings" if not config_state else "Close configuration"):
                st.session_state.report_editing_chart = chart['id'] if not config_state else None
                st.rerun()

        if chart.get('figure'):
            st.plotly_chart(chart['figure'], use_container_width=True, height=200)
            st.caption("Current visualization - update configuration to refresh")
        else:
            st.info("🔄 **Chart not configured** - use the configuration panel below to set up your visualization")

        chart['description'] = st.text_input(
            "Description",
            value=chart.get('description', ''),
            key=f"desc_{chart['id']}",
            placeholder="Describe the insight this chart provides...",
            label_visibility="collapsed"
        )

        if st.session_state.get('report_editing_chart') == chart['id']:
            render_polished_chart_configuration(chart, df)

        col_status, col_gen, col_del = st.columns([2, 2, 1])
        with col_status:
            assigned_sections = get_chart_assignment_status(chart['id'])
            if assigned_sections:
                section_list = ", ".join(assigned_sections[:2])
                if len(assigned_sections) > 2:
                    section_list += f" +{len(assigned_sections)-2} more"
                st.caption(f"📑 **Used in:** {section_list}")
            else:
                st.caption("📭 **Not assigned** - add to sections in Write Content tab")

        with col_gen:
            if st.button("Generate", 
                       key=f"gen_{chart['id']}", 
                       use_container_width=True,
                       help="Generate/refresh chart with current configuration"):
                generate_chart(chart, df)
                st.rerun()

        with col_del:
            if st.button("🗑️", 
                       key=f"delete_{chart['id']}", 
                       use_container_width=True, 
                       help="Delete this chart from library"):
                delete_chart(index)
                st.rerun()


def render_polished_chart_configuration(chart: Dict[str, Any], df: pd.DataFrame):
    """Professional chart configuration with enhanced organization"""
    try:
        numeric_cols, categorical_cols, datetime_cols = get_column_types(df)
        chart_manager = ChartManager(
            df, numeric_cols, categorical_cols, datetime_cols, 
            key_prefix=f"chart_{chart['id']}"
        )
        st.markdown("**Chart Configuration**")
        chart_types = chart_manager.get_chart_types_display()
        current_type = chart.get('chart_type', 'histogram')
        chart_type_options = list(chart_types.keys())
        current_index = chart_type_options.index(current_type) if current_type in chart_type_options else 0
        new_chart_type = st.selectbox(
            "Visualization Type",
            options=chart_type_options,
            index=current_index,
            format_func=lambda x: chart_types[x],
            key=f"chart_type_{chart['id']}",
            help="Select the most appropriate chart type for your data story"
        )
        if new_chart_type != chart.get('chart_type'):
            chart['chart_type'] = new_chart_type
            chart['config'] = {}
            chart['figure'] = None

        current_config = chart.get('config', {})
        new_config = chart_manager.get_configuration_preserved(new_chart_type, current_config)
        chart['config'] = new_config

        if st.button("✅ Close Configuration", 
                   key=f"close_config_{chart['id']}", 
                   use_container_width=True,
                   type="secondary"):
            st.session_state.report_editing_chart = None
            st.rerun()

    except Exception as e:
        st.error(f"❌ Configuration error: {str(e)}")


def get_unique_timestamp():
    return str(time.time_ns())


_chart_counter = 0


def get_unique_chart_key(prefix="plotly"):
    global _chart_counter
    _chart_counter += 1
    return f"{prefix}_{_chart_counter}_{get_unique_timestamp()}"


def render_polished_preview_export():
    """Professional preview and export with validation"""
    st.header("👁️ Preview & Export")

    # Get sections and charts for validation
    sections = st.session_state.report_builder_sections
    charts = st.session_state.report_builder_charts

    # Validate report before allowing export
    report_service = get_report_service()
    valid, msg = report_service.validate_report(sections, charts)

    if not valid:
        st.warning(f"⚠️ **Report has issues:** {msg}")
        st.caption("Please fix the issues before exporting.")

    # Display export interface (existing function)
    export_report_interface()

    st.markdown("---")
    st.subheader("Report Preview")

    if not sections:
        st.info("""
        ## 📝 Report Preview
        Your report is empty. Add sections and content in the **Write Content** tab to see your preview here.
        *The preview shows exactly how your final report will appear to readers.*
        """)
        return

    MAX_CHARTS = 12
    total_charts = sum(len(section.get('chart_ids', [])) for section in sections)

    if total_charts > MAX_CHARTS:
        st.warning(f"📊 **Large Report Detected** - Showing first {MAX_CHARTS} of {total_charts} charts for performance. Full export includes all visualizations.")

    chart_count = 0
    for i, section in enumerate(sections):
        with st.container(border=True):
            st.markdown(f"<h3 style='margin-bottom: 1rem;'>{section.get('title', 'Untitled Section')}</h3>", 
                       unsafe_allow_html=True)

            if section.get('content'):
                st.markdown(section['content'])

            for chart_id in section.get('chart_ids', []):
                if chart_count >= MAX_CHARTS:
                    break
                chart = get_chart_by_id(chart_id)
                if chart and chart.get('figure'):
                    with st.container(border=True):
                        st.markdown(f"<h4 style='margin-bottom: 0.5rem;'>{chart.get('name', 'Unnamed Chart')}</h4>", 
                                   unsafe_allow_html=True)
                        if chart.get('description'):
                            st.caption(chart['description'])
                        st.plotly_chart(
                            chart['figure'], 
                            use_container_width=True,
                            key=get_unique_chart_key(f"preview_{chart['id']}")
                        )
                    chart_count += 1

            if chart_count >= MAX_CHARTS:
                remaining = total_charts - MAX_CHARTS
                st.info(f"📊 **Preview Limited** - {remaining} additional chart{'s' if remaining != 1 else ''} included in full export.")
                break

    # Report statistics
    stats = report_service.get_report_stats(sections, charts)
    if stats['total_sections'] > 0:
        with st.expander("📊 Report Statistics", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Sections", stats['total_sections'])
                st.metric("Charts", stats['total_charts'])
            with col2:
                st.metric("Empty Sections", stats['empty_sections'])
                st.metric("Charts Assigned", stats['assigned_charts'])
            with col3:
                st.metric("Content Completeness", f"{stats['content_completeness']:.0f}%")
                st.metric("Unassigned Charts", stats['unassigned_charts'])


# ===== POLISHED UTILITY FUNCTIONS =====
def add_new_section():
    new_section = get_report_service().create_empty_section(
        title=f"Section {len(st.session_state.report_builder_sections) + 1}"
    )
    st.session_state.report_builder_sections.append(new_section)


def delete_section(index: int):
    if len(st.session_state.report_builder_sections) > 1:
        st.session_state.report_builder_sections.pop(index)


def move_section_to_index(old_index: int, new_index: int):
    sections = st.session_state.report_builder_sections
    if 0 <= new_index < len(sections):
        section = sections.pop(old_index)
        sections.insert(new_index, section)


def add_new_chart():
    new_chart = get_report_service().create_chart_stub(
        name=f"Chart {len(st.session_state.report_builder_charts) + 1}",
        chart_type='histogram'
    )
    st.session_state.report_builder_charts.append(new_chart)


def add_quick_chart(chart_type: str):
    type_names = {'bar': 'Bar', 'line': 'Line', 'scatter': 'Scatter'}
    new_chart = get_report_service().create_chart_stub(
        name=f'Quick {type_names.get(chart_type, chart_type.title())}',
        chart_type=chart_type
    )
    new_chart['description'] = f'Quick {chart_type} chart showing key patterns'
    st.session_state.report_builder_charts.append(new_chart)


def delete_chart(index: int):
    chart_id = st.session_state.report_builder_charts[index]['id']
    for section in st.session_state.report_builder_sections:
        if chart_id in section['chart_ids']:
            section['chart_ids'].remove(chart_id)
    st.session_state.report_builder_charts.pop(index)


def create_chart_from_config(name: str, description: str, chart_type: str, config: Dict, df: pd.DataFrame) -> Optional[Dict]:
    """Professional chart creation with enhanced error handling, using ChartService."""
    if not name.strip():
        st.error("Please provide a chart name.")
        return None

    try:
        figure = get_chart_service().create_chart(df, chart_type, config)
        if not figure:
            st.error("No data available for this chart configuration. Please check your column selections and data.")
            return None

        # Use ReportService to create a chart stub (with fresh ID) but we already have a chart object
        # We'll construct manually to preserve the figure
        new_chart = {
            'id': str(uuid.uuid4()),
            'name': name,
            'chart_type': chart_type,
            'config': config,
            'figure': figure,
            'description': description
        }
        st.session_state.report_builder_charts.append(new_chart)
        return new_chart

    except ValueError as e:
        st.error(f"Invalid chart configuration: {str(e)}. Please ensure selected columns match the chart type requirements.")
        return None
    except Exception as e:
        st.error(f"Chart creation failed: {str(e)}. Please try different settings or check your data.")
        return None


def generate_chart(chart: Dict[str, Any], df: pd.DataFrame):
    """Generate AND STORE the actual chart figure using ChartService."""
    try:
        if not chart.get('config'):
            st.error("❌ Please configure the chart settings first")
            return

        fig = get_chart_service().create_chart(df, chart['chart_type'], chart.get('config', {}))
        if fig:
            chart['figure'] = fig
            st.success("✅ Chart generated successfully!")
        else:
            st.error("❌ Chart generation failed")
    except Exception as e:
        st.error(f"❌ Chart generation failed: {str(e)}")


def ensure_all_charts_have_figures():
    """Ensure all charts have actual figure objects generated."""
    df = st.session_state.dataset
    if df is None:
        return False

    any_missing = False
    for chart in st.session_state.report_builder_charts:
        if not chart.get('figure') and chart.get('config'):
            try:
                chart['figure'] = get_chart_service().create_chart(df, chart['chart_type'], chart['config'])
            except Exception as e:
                st.error(f"Failed to generate chart '{chart.get('name')}': {str(e)}")
                any_missing = True

    return not any_missing


def get_chart_by_id(chart_id: str) -> Optional[Dict[str, Any]]:
    for chart in st.session_state.report_builder_charts:
        if chart['id'] == chart_id:
            return chart
    return None


def get_chart_assignment_status(chart_id: str) -> List[str]:
    assigned = []
    for section in st.session_state.report_builder_sections:
        if chart_id in section.get('chart_ids', []):
            assigned.append(section['title'])
    return assigned


def load_template(template_key: str):
    """Load template using ReportService."""
    sections = get_report_service().load_template(template_key)
    st.session_state.report_builder_sections = sections


# ===== MAIN FUNCTION - PRODUCTION GRADE =====
def render_report_builder_tab():
    """Ultra-polished, professional Report Builder"""
    init_report_builder_state()

    if st.session_state.get('active_chart_section'):
        section_ids = {s['id'] for s in st.session_state.report_builder_sections}
        if st.session_state.active_chart_section not in section_ids:
            st.session_state.active_chart_section = None

    df = st.session_state.dataset
    if df is None:
        st.info("""
        <div style='text-align: center; padding: 3rem;'>
            <h3 style='margin-bottom: 1rem;'>📤 Load Your Data to Begin</h3>
            <p style='color: #666; margin-bottom: 2rem;'>Please load a dataset in the <strong>Dataset Overview</strong> tab to start building your professional report.</p>
            <p style='color: #888;'>You can use sample data or upload your own CSV/Excel file to begin your analysis.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    tab1, tab2, tab3 = st.tabs([
        "📝 **Write Content**",
        "📊 **Manage Charts**",
        "👁️ **Preview & Export**"
    ])

    with tab1:
        render_polished_content_editor(df)

    with tab2:
        render_polished_visualizations_tab(df)

    with tab3:
        render_polished_preview_export()