# ui/tabs/ai_copilot.py
"""
AI Copilot Tab – Professional chat interface for AI-powered data analysis.
Handles user interaction, chat history, and delegates analysis to AI services.
"""

import streamlit as st
import pandas as pd
import time
import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime
from copy import deepcopy

logger = logging.getLogger(__name__)

# Import AI Service
from services.ai_service import AIService

# Import Chart Service for rendering AI‑suggested charts
from services.chart_service import ChartService

# ============================================================================
# CONSTANTS & CONFIGURATION
# ============================================================================

CHAT_MESSAGE_LIMIT = 50

# Global service instances (singletons)
_ai_service = None
_chart_service = None


def get_ai_service() -> AIService:
    """Lazy initialisation of the AIService singleton."""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service


def get_chart_service() -> ChartService:
    """Lazy initialisation of the ChartService singleton."""
    global _chart_service
    if _chart_service is None:
        _chart_service = ChartService()
    return _chart_service


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def _init_session_state():
    """Initialize or validate session state variables."""
    defaults = {
        'chat_history': [],
        'ai_processing': False,
        'last_analysis_id': None,
        'use_filtered_for_ai': True,
        'chat_expanded_sections': {},
        'show_chart_code': {},
        'current_model_info': None,
        'chat_loaded': False,
        'processing_steps': [],
        'last_interaction_time': time.time(),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = deepcopy(value)


# ============================================================================
# ENHANCED CHAT RENDERING
# ============================================================================

def render_chat_history():
    """Render chat history with professional animations."""
    _init_session_state()
    st.markdown(AI_COPILOT_STYLES, unsafe_allow_html=True)
    chat_history = st.session_state.get('chat_history', [])
    with st.container():
        if len(chat_history) > 10:
            with st.expander(f"📜 Earlier conversations ({len(chat_history)-10} more)", expanded=False):
                for i, message in enumerate(chat_history[:-10]):
                    _render_chat_message(message, i)
        recent_messages = chat_history[-10:] if len(chat_history) > 10 else chat_history
        for i, message in enumerate(recent_messages):
            _render_chat_message(message, len(chat_history) - len(recent_messages) + i)
    st.markdown("""
    <script>
        setTimeout(() => {
            const chatArea = document.querySelector('[data-testid="stVerticalBlock"]');
            if (chatArea) {
                chatArea.scrollTo({
                    top: chatArea.scrollHeight,
                    behavior: 'smooth'
                });
            }
        }, 100);
    </script>
    """, unsafe_allow_html=True)
    st.session_state.chat_loaded = True


def _render_chat_message(message: Dict[str, Any], index: int):
    role = message.get('role', 'user')
    content = message.get('content', '')
    timestamp = message.get('timestamp', time.time())
    if role == 'user':
        _render_user_message(content, timestamp, index)
    else:
        _render_assistant_message(content, timestamp, index)


def _render_user_message(content: str, timestamp: float, index: int):
    message_time = datetime.fromtimestamp(timestamp).strftime('%I:%M %p')
    html = render_user_message_html(content, message_time, index, MESSAGE_STYLES_AI['user'])
    st.markdown(html, unsafe_allow_html=True)


def _render_assistant_message(content: Dict[str, Any], timestamp: float, index: int):
    section_key = f"message_{index}"
    if section_key not in st.session_state.chat_expanded_sections:
        st.session_state.chat_expanded_sections[section_key] = True
    message_time = datetime.fromtimestamp(timestamp).strftime('%I:%M %p')
    col1, col2 = st.columns([6, 1])
    with col1:
        header_html = render_assistant_header_html(message_time, MESSAGE_STYLES_AI['assistant'])
        st.markdown(header_html, unsafe_allow_html=True)
    with col2:
        with st.popover("⋮", help="Message actions"):
            expanded = st.session_state.chat_expanded_sections[section_key]
            toggle_icon = "▼" if expanded else "▶"
            toggle_label = "Collapse" if expanded else "Expand"
            if st.button(f"{toggle_icon} {toggle_label}",
                        key=f"toggle_{section_key}",
                        use_container_width=True,
                        type="secondary"):
                st.session_state.chat_expanded_sections[section_key] = not expanded
                st.rerun()
            st.divider()
            if st.button("📋 Copy Summary",
                        key=f"copy_{section_key}",
                        use_container_width=True,
                        help="Copy analysis to clipboard"):
                _copy_analysis_to_clipboard(content)
                st.toast("Copied to clipboard", icon="📋")
            if st.button("↻ Re-run Analysis",
                        key=f"rerun_{section_key}",
                        use_container_width=True,
                        help="Re-run this analysis"):
                st.session_state.rerun_prompt = content.get('user_prompt', '')
                st.rerun()
    if st.session_state.chat_expanded_sections[section_key]:
        with st.container():
            st.markdown('<div class="expandable-content">', unsafe_allow_html=True)
            try:
                _render_assistant_content(content, index)
            except Exception as e:
                logger.error(f"Failed to render assistant content: {e}")
                st.markdown(get_error_indicator_html("Failed to display analysis"), unsafe_allow_html=True)
                with st.expander("Technical Details", expanded=False):
                    st.code(str(e)[:200], language="text")
            st.markdown('</div>', unsafe_allow_html=True)


def _render_assistant_content(content: Dict[str, Any], message_index: int):
    ai_service = get_ai_service()

    if content.get('ai_generated', False):
        model_name = content.get('model', 'AI Model').replace('gemini-', 'Gemini ').replace('claude-', 'Claude ')
        success_html = get_success_indicator_html(f"Analysis complete • {model_name}")
        st.markdown(success_html, unsafe_allow_html=True)
    else:
        st.info("🔧 **Heuristic Analysis** • Generated using built-in methods")
    if content.get('story'):
        _render_story_section(content['story'], message_index)
    insights = content.get('insights') or ai_service.extract_insights(content.get('story', ''))
    if insights:
        _render_insights_summary(insights, message_index)
    if content.get('charts'):
        _render_charts_section(content['charts'], message_index)
    _render_analysis_metadata(content, message_index)


def _render_story_section(story_text: str, message_index: int):
    if not story_text:
        return
    ai_service = get_ai_service()
    formatted_story = ai_service.format_story(story_text)
    with st.expander("📋 **Analysis Summary**", expanded=True):
        with st.container():
            st.markdown(formatted_story)
        st.divider()


def _render_insights_summary(insights: List, message_index: int):
    if not insights:
        return
    with st.container(border=True):
        st.markdown("### 💡 Key Insights")
        st.caption("Most important findings from the analysis")
        top_insights = insights[:5]
        for i, insight in enumerate(top_insights):
            insight_text = insight if isinstance(insight, str) else insight.get('description', str(insight))
            html = get_insight_item_html(insight_text, i)
            st.markdown(html, unsafe_allow_html=True)


def _render_charts_section(charts: List[Dict[str, Any]], message_index: int):
    if not charts:
        return
    with st.container(border=True):
        st.markdown(f"### 📊 Visualizations")
        st.caption(f"{len(charts)} chart{'s' if len(charts) > 1 else ''} generated")
        if len(charts) == 1:
            _render_single_chart(charts[0], message_index, 0)
        elif len(charts) <= 3:
            cols = st.columns(len(charts))
            for i, (chart, col) in enumerate(zip(charts, cols)):
                with col:
                    _render_single_chart(chart, message_index, i, compact=True)
        else:
            tab_titles = [f"Chart {i+1}" for i in range(len(charts))]
            tabs = st.tabs(tab_titles)
            for i, (chart, tab) in enumerate(zip(charts, tabs)):
                with tab:
                    _render_single_chart(chart, message_index, i)


def _render_single_chart(chart: Dict[str, Any], message_index: int, chart_index: int, compact: bool = False):
    chart_id = chart.get('id', f"chart_{message_index}_{chart_index}")
    with st.container():
        title = chart.get('title', 'Untitled Chart')
        chart_type = chart.get('chart_type', 'unknown').title()
        description = chart.get('description', '')
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"**{title}**")
            if description:
                st.caption(description)
        with col2:
            chart_badge = get_chart_container_html(chart_type)
            st.markdown(chart_badge, unsafe_allow_html=True)
        try:
            df = st.session_state.get('dataset')
            if df is not None and not df.empty:
                # Use ChartService to render the AI‑suggested chart
                fig = get_chart_service().create_chart_from_suggestion(df, chart)
                if fig:
                    with st.container():
                        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                        height = 300 if compact else 400
                        st.plotly_chart(fig, use_container_width=True, height=height)
                        st.markdown('</div>', unsafe_allow_html=True)
                    _render_chart_actions(chart, chart_id, df)
                else:
                    st.info("Chart preview unavailable")
            else:
                st.info("📁 Load dataset to preview")
        except Exception as e:
            st.markdown(get_error_indicator_html("Chart render failed, error: " + str(e) + ""), unsafe_allow_html=True)


def _render_chart_actions(chart: Dict[str, Any], chart_id: str, df: pd.DataFrame):
    col1, col2 = st.columns(2)
    with col1:
        show_code = st.session_state.show_chart_code.get(chart_id, False)
        label = "Hide Code" if show_code else "View Code"
        if st.button(label,
                    key=f"code_{chart_id}",
                    use_container_width=True,
                    type="secondary"):
            st.session_state.show_chart_code[chart_id] = not show_code
            st.rerun()
    with col2:
        if st.button("Refresh",
                    key=f"refresh_{chart_id}",
                    use_container_width=True,
                    type="secondary"):
            st.rerun()
    if st.session_state.show_chart_code.get(chart_id, False):
        with st.expander("Chart Code", expanded=True):
            code = chart.get('code', '# No code available')
            st.code(code, language='python')


def _render_analysis_metadata(content: Dict[str, Any], message_index: int):
    metadata_html = get_analysis_metadata_html(content)
    if metadata_html:
        st.markdown(metadata_html, unsafe_allow_html=True)


# ============================================================================
# ENHANCED CHAT INTERFACE
# ============================================================================

def render_ai_copilot_tab():
    _init_session_state()
    st.session_state.last_interaction_time = time.time()
    st.markdown(AI_COPILOT_STYLES, unsafe_allow_html=True)
    render_chat_history()
    _render_chat_input()
    _render_bottom_controls()


def _render_chat_input():
    if not st.session_state.get('chat_history'):
        render_quick_suggestions()
    if 'rerun_prompt' in st.session_state:
        user_prompt = st.session_state.pop('rerun_prompt')
        _process_user_input(user_prompt)
        return
    if 'quick_suggestion' in st.session_state:
        user_prompt = st.session_state.pop('quick_suggestion')
        _process_user_input(user_prompt)
        return
    user_prompt = st.chat_input(
        "💭 Ask about your data...",
        key="chat_input_main"
    )
    if user_prompt:
        _process_user_input(user_prompt)


def _render_bottom_controls():
    chat_history = st.session_state.get('chat_history', [])
    if not chat_history:
        return
    st.divider()
    render_bottom_controls_ai_streamlit(chat_history, st.session_state.get('use_filtered_for_ai', True))
    session_duration = time.time() - st.session_state.last_interaction_time
    minutes = int(session_duration // 60)
    if minutes > 0:
        st.caption(f"⏱️ Session active for {minutes}m")


# ============================================================================
# ENHANCED PROCESSING & ERROR HANDLING
# ============================================================================

def _process_user_input(user_prompt: str):
    processing_placeholder = st.empty()
    with processing_placeholder.container():
        st.markdown(render_processing_state_html(), unsafe_allow_html=True)

    try:
        is_valid, error_msg = _validate_dataset()
        if not is_valid:
            st.error(f"❌ {error_msg}")
            processing_placeholder.empty()
            time.sleep(1)
            return

        dataset = st.session_state['dataset']
        if st.session_state.get('use_filtered_for_ai', True):
            filtered_df = st.session_state.get('filtered_dataset')
            if filtered_df is not None and not filtered_df.empty:
                dataset = filtered_df

        _add_user_message(user_prompt)

        # Build AI configuration from session state
        config = {
            'model': st.session_state.get('ai_model', 'EchoEngine'),
            'api_key': st.session_state.get('api_key', ''),
            'temperature': st.session_state.get('ai_temperature', 0.3),
            'EchoEngine_mode': st.session_state.get('ai_EchoEngine_mode', True),
            'debug_mode': st.session_state.get('debug_mode', False),
            'max_charts': 6,
            'min_charts': 3,
        }

        # Generate analysis via AIService
        ai_service = get_ai_service()
        result = ai_service.generate_analysis(dataset, user_prompt, config)

        if result.get('error'):
            _add_assistant_message({
                "story": f"## ❌ Analysis Failed\n\n**Error**: {result['error'][:200]}\n\nPlease try a different question or simplify your request.",
                "charts": [],
                "ai_generated": False,
                "analysis_mode": "error"
            })
            st.error(f"❌ Analysis failed")
        else:
            _add_assistant_message(result)
            num_charts = len(result.get('charts', []))
            if num_charts > 0:
                st.success(f"✅ Generated {num_charts} chart{'s' if num_charts > 1 else ''}")
            else:
                st.success("✅ Analysis complete")

    except Exception as e:
        logger.error(f"AI analysis failed: {e}", exc_info=True)
        _add_assistant_message({
            "story": f"## ❌ Unexpected Error\n\nAnalysis failed due to an unexpected error.\n\n```\n{str(e)[:200]}\n```\n\nPlease try again.",
            "charts": [],
            "ai_generated": False,
            "analysis_mode": "error"
        })
        st.error(f"❌ Analysis error")

    finally:
        processing_placeholder.empty()
        time.sleep(0.2)
        st.rerun()


# ============================================================================
# CHAT MANAGEMENT FUNCTIONS
# ============================================================================

def _add_user_message(content: str):
    _init_session_state()
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if not content or not content.strip():
        return
    cleaned_content = content.strip()
    chat_history = st.session_state.chat_history
    if (chat_history and
        chat_history[-1].get('role') == 'user' and
        chat_history[-1].get('content') == cleaned_content):
        st.toast("Message already sent", icon="💬")
        return
    st.session_state.chat_history.append({
        'role': 'user',
        'content': cleaned_content,
        'timestamp': time.time(),
        'user_prompt': cleaned_content
    })
    if len(st.session_state.chat_history) > CHAT_MESSAGE_LIMIT:
        if CHAT_MESSAGE_LIMIT > 10:
            keep_first = 5
            keep_last = CHAT_MESSAGE_LIMIT - keep_first
            st.session_state.chat_history = (
                st.session_state.chat_history[:keep_first] +
                st.session_state.chat_history[-keep_last:]
            )


def _add_assistant_message(content: Dict[str, Any]):
    _init_session_state()
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if st.session_state.chat_history and st.session_state.chat_history[-1].get('role') == 'user':
        user_prompt = st.session_state.chat_history[-1].get('content', '')
        content['user_prompt'] = user_prompt
    st.session_state.chat_history.append({
        'role': 'assistant',
        'content': content,
        'timestamp': time.time()
    })
    st.session_state.last_analysis_id = content.get('id', str(time.time()))


def _validate_dataset() -> Tuple[bool, str]:
    dataset = st.session_state.get('dataset')
    if dataset is None:
        return False, "No dataset loaded"
    if isinstance(dataset, pd.DataFrame) and dataset.empty:
        return False, "Dataset is empty"
    if len(dataset.columns) == 0:
        return False, "Dataset has no columns"
    if len(dataset) < 3:
        return False, f"Dataset has only {len(dataset)} rows (minimum 3)"
    numeric_cols = [col for col in dataset.columns if pd.api.types.is_numeric_dtype(dataset[col])]
    categorical_cols = [col for col in dataset.columns if dataset[col].dtype == "object" or pd.api.types.is_categorical_dtype(dataset[col])]
    if not numeric_cols and not categorical_cols:
        return False, "Dataset needs at least one numeric or categorical column"
    total_cells = len(dataset) * len(dataset.columns)
    if total_cells > 0:
        missing_cells = dataset.isnull().sum().sum()
        missing_pct = missing_cells / total_cells
        if missing_pct > 0.5:
            return False, f"Dataset has {missing_pct:.0%} missing values"
    return True, f"✅ Ready: {len(dataset):,} rows × {len(dataset.columns)} columns"


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def _copy_analysis_to_clipboard(content: Dict[str, Any]):
    try:
        ai_service = get_ai_service()
        story = content.get('story', '')
        insights = ai_service.extract_insights(story)

        clipboard_text = f"AI Data Analysis Summary\n"
        clipboard_text += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        clipboard_text += f"Model: {content.get('model', 'Heuristic Analysis')}\n\n"

        if story:
            paragraphs = story.split('\n\n')
            for para in paragraphs[:3]:
                if len(para.strip()) > 20:
                    clipboard_text += f"{para.strip()}\n\n"

        if insights:
            clipboard_text += "Key Insights:\n"
            for i, insight in enumerate(insights[:5], 1):
                insight_text = insight if isinstance(insight, str) else insight.get('description', str(insight))
                clipboard_text += f"{i}. {insight_text}\n"

        st.code(clipboard_text, language="text")
        st.toast("📋 Analysis ready to copy", icon="📋")
    except Exception as e:
        st.error(f"Failed to prepare copy")


# ============================================================================
# AI UI COMPONENTS - PREMIUM & PROFESSIONAL
# ============================================================================

import streamlit as st
import time
from typing import Dict, Any

# ============================================================================
# AI COPILOT SPECIFIC STYLES - PREMIUM
# ============================================================================

AI_COPILOT_STYLES = """
<style>
/* Premium Animations - Calm & Smooth */
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(12px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes fadeInDown {
    from { opacity: 0; transform: translateY(-12px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes slideInRight {
    from { opacity: 0; transform: translateX(20px); }
    to { opacity: 1; transform: translateX(0); }
}
@keyframes gentleFloat {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-2px); }
}
@keyframes subtlePulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.8; }
}
@keyframes smoothExpand {
    from { max-height: 0; opacity: 0; }
    to { max-height: 1000px; opacity: 1; }
}
@keyframes shimmer {
    0% { background-position: -1000px 0; }
    100% { background-position: 1000px 0; }
}
@keyframes slowSpin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

/* Chat Bubbles */
.chat-bubble {
    animation: fadeIn 0.4s ease;
    backdrop-filter: blur(8px);
    transition: all 0.2s ease;
}
.chat-bubble:hover {
    transform: translateY(-1px);
}
.chat-bubble::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--accent-color, rgba(59, 130, 246, 0.2)), transparent);
    opacity: 0;
    transition: opacity 0.3s ease;
}
.chat-bubble:hover::before {
    opacity: 1;
}

/* Message Avatars */
.message-avatar {
    animation: gentleFloat 6s ease-in-out infinite;
}

/* Quick Analysis Cards */
.quick-analysis-card {
    animation: fadeInUp 0.5s ease;
    animation-delay: calc(var(--index, 0) * 0.05s);
    transition: all 0.25s ease;
    cursor: pointer;
}
.quick-analysis-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

/* Insight Items */
.insight-item {
    animation: fadeInUp 0.5s ease;
    animation-delay: calc(var(--insight-index, 0) * 0.1s);
    transition: all 0.2s ease;
}
.insight-item:hover {
    transform: translateX(4px);
}

/* Chart Container */
.chart-container {
    transition: all 0.3s ease;
    border-radius: 12px;
    overflow: hidden;
}
.chart-container:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.08);
}

/* Expandable Content */
.expandable-content {
    animation: smoothExpand 0.4s ease;
    overflow: hidden;
}

/* Chat Input */
.ai-chat-input-wrapper {
    backdrop-filter: blur(10px);
    background: rgba(255, 255, 255, 0.96);
    border: 1.5px solid rgba(0, 0, 0, 0.08);
    border-radius: 16px;
    transition: all 0.3s ease;
    padding: 1rem 1.25rem;
}
.ai-chat-input-wrapper:hover {
    border-color: rgba(59, 130, 246, 0.2);
    box-shadow: 0 6px 20px rgba(59, 130, 246, 0.08);
}
.ai-chat-input-wrapper:focus-within {
    border-color: rgba(59, 130, 246, 0.3);
    box-shadow: 0 8px 24px rgba(59, 130, 246, 0.12);
}

/* Scrollbar */
.chat-scroll-area::-webkit-scrollbar {
    width: 6px;
}
.chat-scroll-area::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.02);
    border-radius: 3px;
}
.chat-scroll-area::-webkit-scrollbar-thumb {
    background: rgba(99, 102, 241, 0.2);
    border-radius: 3px;
}
.chat-scroll-area::-webkit-scrollbar-thumb:hover {
    background: rgba(99, 102, 241, 0.3);
}

/* Loading States */
.skeleton-loading {
    background: linear-gradient(90deg, #f0f0f0 25%, #e8e8e8 50%, #f0f0f0 75%);
    background-size: 200% 100%;
    animation: shimmer 2s infinite ease-in-out;
    border-radius: 6px;
}

/* Status Indicators */
.status-indicator {
    animation: subtlePulse 3s ease-in-out infinite;
}

/* Typing Indicator */
.typing-dots {
    display: inline-flex;
    gap: 4px;
}
.typing-dots span {
    width: 4px;
    height: 4px;
    background: #6b7280;
    border-radius: 50%;
    animation: typing 1.4s infinite ease-in-out;
}
.typing-dots span:nth-child(2) {
    animation-delay: 0.2s;
}
.typing-dots span:nth-child(3) {
    animation-delay: 0.4s;
}
@keyframes typing {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-4px); }
}

/* Glass Effect */
.glass-effect {
    backdrop-filter: blur(12px);
    background: rgba(255, 255, 255, 0.88);
    border: 1px solid rgba(255, 255, 255, 0.2);
}

/* Success/Error States */
.success-micro {
    animation: fadeInUp 0.5s ease;
}
.error-micro {
    animation: fadeInUp 0.5s ease;
}

/* Hover Effects */
.hover-lift {
    transition: transform 0.2s ease;
}
.hover-lift:hover {
    transform: translateY(-2px);
}

/* Focus Rings */
.focus-ring:focus {
    outline: 2px solid rgba(59, 130, 246, 0.4);
    outline-offset: 2px;
}

/* Find the Message Avatars section in AI_COPILOT_STYLES and update it */
.message-avatar {
    animation: gentleFloat 6s ease-in-out infinite;
    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    cursor: pointer;
    z-index: 10;
}
.message-avatar:hover {
    transform: scale(1.2) rotate(5deg);
    box-shadow: 0 0 15px var(--accent-color, rgba(99, 102, 241, 0.4));
    border-width: 2px !important;
}
</style>
"""

# AI Message styling
MESSAGE_STYLES_AI = {
    'user': {
        'avatar': "👤",
        'gradient': 'linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(37, 99, 235, 0.05) 100%)',
        'border': '1px solid rgba(59, 130, 246, 0.15)',
        'accent': 'rgba(59, 130, 246, 0.3)'
    },
    'assistant': {
        'avatar': "🧠",
        'gradient': 'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.05) 100%)',
        'border': '1px solid rgba(16, 185, 129, 0.15)',
        'accent': 'rgba(16, 185, 129, 0.3)'
    },
    'system': {
        'avatar': "⚙️",
        'gradient': 'linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(124, 58, 237, 0.05) 100%)',
        'border': '1px solid rgba(139, 92, 246, 0.15)',
        'accent': 'rgba(139, 92, 246, 0.3)'
    }
}


def render_user_message_html(content: str, timestamp: str, index: int, style: dict) -> str:
    return f"""
    <div class="chat-bubble" style="--accent-color: {style['accent']};">
        <div style="margin: 1.25rem 0; display: flex; justify-content: flex-end; align-items: flex-start; gap: 0.75rem;">
            <div style="max-width: 80%; min-width: 200px;">
                <div style="background: {style['gradient']}; padding: 1rem 1.25rem; border-radius: 18px; border: {style['border']};">
                    <div style="font-size: 0.95rem; line-height: 1.5;  margin-bottom: 0.5rem; font-weight: 500;">{content}</div>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="font-size: 0.7rem; color: #6b7280; opacity: 0.7;">You</div>
                        <div style="font-size: 0.7rem; color: #6b7280; opacity: 0.5;">{timestamp}</div>
                    </div>
                </div>
            </div>
            <div class="message-avatar" style="background: {style['gradient']}; width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 1px solid {style['accent']}; font-size: 1rem; margin-top: 0.25rem;">
                {style['avatar']}
            </div>
        </div>
    </div>
    """


def render_assistant_header_html(timestamp: str, style: dict) -> str:
    return f"""
    <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.75rem; animation: slideInRight 0.4s ease;">
        <div class="message-avatar" style="background: {style['gradient']}; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 1px solid {style['accent']}; font-size: 0.9rem;">
            {style['avatar']}
        </div>
        <div>
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <div style="font-weight: 600;  font-size: 0.9rem;">AI Assistant</div>
                <div class="status-indicator" style="width: 6px; height: 6px; background: #10b981; border-radius: 50%;"></div>
            </div>
            <div style="font-size: 0.7rem; color: #6b7280;">{timestamp}</div>
        </div>
    </div>
    """


def render_processing_state_html() -> str:
    return """
    <div style="margin: 2rem 0; padding: 2rem; border-radius: 16px; background: linear-gradient(135deg, rgba(99, 102, 241, 0.05), rgba(139, 92, 246, 0.03)); border: 1px solid rgba(99, 102, 241, 0.1); animation: fadeIn 0.4s ease;">
        <div style="display: flex; align-items: center; justify-content: center; gap: 1rem; margin-bottom: 2rem;">
            <div style="animation: gentleFloat 3s ease-in-out infinite;">
                <div style="animation: slowSpin 2s linear infinite;">
                    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="12" cy="12" r="10" stroke="rgba(99, 102, 241, 0.2)" stroke-width="2"/>
                        <path d="M12 2a10 10 0 0 1 10 10" stroke="#6366f1" stroke-width="2" stroke-linecap="round">
                            <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1.5s" repeatCount="indefinite"/>
                        </path>
                    </svg>
                </div>
            </div>
            <div>
                <h3 style="margin: 0 0 0.25rem 0;  font-size: 1.1rem; font-weight: 600;">Processing Request</h3>
                <p style="margin: 0; color: #6b7280; font-size: 0.9rem;">Analyzing data patterns...</p>
            </div>
        </div>
        <div style="display: flex; flex-direction: column; gap: 0.75rem; max-width: 350px; margin: 0 auto;">
            <div class="skeleton-loading" style="height: 12px; width: 80%; border-radius: 6px;"></div>
            <div class="skeleton-loading" style="height: 12px; width: 70%; border-radius: 6px; animation-delay: 0.1s;"></div>
            <div class="skeleton-loading" style="height: 12px; width: 85%; border-radius: 6px; animation-delay: 0.2s;"></div>
        </div>
    </div>
    """


def render_quick_suggestions():
    with st.container():
        st.markdown("""
        <div style="margin-bottom: 2rem; animation: fadeIn 0.5s ease;">
            <div style="text-align: center; margin-bottom: 1.5rem;">
                <div style="display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.5rem 1rem; background: rgba(99, 102, 241, 0.06); border-radius: 10px; border: 1px solid rgba(99, 102, 241, 0.12); margin-bottom: 0.5rem;">
                    <div style="color: #6366f1; font-size: 1rem;">💡</div>
                    <div style="font-weight: 600;  font-size: 0.9rem;">Quick Start</div>
                </div>
                <p style="color: #6b7280; font-size: 0.85rem; max-width: 450px; margin: 0.5rem auto 0;">Select a suggestion or type your own question</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        suggestions = [
            {"icon": "📈", "title": "Trend Analysis", "description": "Analyze patterns over time", "prompt": "Show me trends and patterns in the data"},
            {"icon": "🔍", "title": "Data Overview", "description": "Get comprehensive insights", "prompt": "Give me an overview of the dataset"},
            {"icon": "🎯", "title": "Find Correlations", "description": "Discover relationships", "prompt": "Find correlations between variables"},
            {"icon": "📊", "title": "Summary Statistics", "description": "Key metrics and statistics", "prompt": "Show me summary statistics"}
        ]
        cols = st.columns(2)
        for idx, suggestion in enumerate(suggestions):
            with cols[idx % 2]:
                st.markdown(f"""
                <div class="quick-analysis-card hover-lift" style="--index: {idx}; margin-bottom: 1rem;">
                    <div style="padding: 1rem; background: linear-gradient(135deg, {['rgba(99, 102, 241, 0.06)', 'rgba(16, 185, 129, 0.06)', 'rgba(245, 158, 11, 0.06)', 'rgba(139, 92, 246, 0.06)'][idx]}, transparent); border-radius: 12px; border: 1px solid {['rgba(99, 102, 241, 0.12)', 'rgba(16, 185, 129, 0.12)', 'rgba(245, 158, 11, 0.12)', 'rgba(139, 92, 246, 0.12)'][idx]};">
                        <div style="display: flex; align-items: flex-start; gap: 0.75rem;">
                            <div style="background: {['rgba(99, 102, 241, 0.1)', 'rgba(16, 185, 129, 0.1)', 'rgba(245, 158, 11, 0.1)', 'rgba(139, 92, 246, 0.1)'][idx]}; padding: 0.5rem; border-radius: 10px; color: {['#6366f1', '#10b981', '#f59e0b', '#8b5cf6'][idx]}; font-size: 1rem;">{suggestion['icon']}</div>
                            <div>
                                <div style="font-weight: 600;  font-size: 0.9rem; margin-bottom: 0.25rem;">{suggestion['title']}</div>
                                <div style="font-size: 0.8rem; color: #6b7280; line-height: 1.4;">{suggestion['description']}</div>
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Use this", key=f"quick_suggestion_{idx}", use_container_width=True, type="secondary"):
                    st.session_state.quick_suggestion = suggestion['prompt']
                    st.rerun()


def render_bottom_controls_ai_streamlit(chat_history: list, use_filtered: bool):
    with st.container():
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem; background: rgba(0, 0, 0, 0.02); border-radius: 8px; border: 1px solid rgba(0, 0, 0, 0.05);">
                <div style="font-size: 0.8rem; color: #6366f1;">💬</div>
                <div style="font-size: 0.8rem; color: #4b5563; font-weight: 500;">{len(chat_history)} messages</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            if st.button("🗑️ Clear Chat", key="clear_chat_button", use_container_width=True, type="secondary"):
                st.session_state.chat_history = []
                st.toast("Chat cleared", icon="🗑️")
                st.rerun()


def get_chart_container_html(chart_type: str) -> str:
    return f"""
    <div style="background: linear-gradient(135deg, rgba(79, 70, 229, 0.08), rgba(147, 51, 234, 0.05)); padding: 0.25rem 0.5rem; border-radius: 10px; text-align: center; font-size: 0.75rem; color: #4f46e5; font-weight: 600; border: 1px solid rgba(79, 70, 229, 0.15);">
        {chart_type}
    </div>
    """


def get_insight_item_html(insight: str, index: int) -> str:
    return f"""
    <div class="insight-item hover-lift" style="--insight-index: {index}; margin: 0.75rem 0;">
        <div style="display: flex; align-items: flex-start; gap: 0.75rem; padding: 0.75rem; background: rgba(99, 102, 241, 0.03); border-radius: 10px; border: 1px solid rgba(99, 102, 241, 0.08);">
            <div style="display: flex; align-items: center; justify-content: center; width: 20px; height: 20px; background: rgba(99, 102, 241, 0.1); border-radius: 6px; color: #6366f1; font-size: 0.8rem; font-weight: 600;">
                {index + 1}
            </div>
            <div style="flex: 1; font-size: 0.9rem; line-height: 1.5; font-weight: 500;">
                {insight}
            </div>
        </div>
    </div>
    """


def get_analysis_metadata_html(content: Dict[str, Any]) -> str:
    metadata = []
    if content.get('ai_generated'):
        model = content.get('model', 'Unknown').replace('gemini-', 'Gemini ').replace('claude-', 'Claude ')
        metadata.append(f"""
        <div style="display: flex; align-items: center; gap: 0.5rem; animation: fadeIn 0.5s ease;">
            <div style="width: 4px; height: 4px; background: #6366f1; border-radius: 50%;"></div>
            <div style="font-size: 0.75rem; color: #6b7280;">Model: <span style="color: #6366f1; font-weight: 600;">{model}</span></div>
        </div>
        """)
    if content.get('generation_time'):
        time_sec = content['generation_time']
        time_color = "#10b981" if time_sec < 2 else "#f59e0b" if time_sec < 5 else "#ef4444"
        metadata.append(f"""
        <div style="display: flex; align-items: center; gap: 0.5rem; animation: fadeIn 0.5s ease 0.1s;">
            <div style="width: 4px; height: 4px; background: {time_color}; border-radius: 50%;"></div>
            <div style="font-size: 0.75rem; color: #6b7280;">Time: <span style="color: {time_color}; font-weight: 600;">{time_sec:.1f}s</span></div>
        </div>
        """)
    chart_count = len(content.get('charts', []))
    if chart_count > 0:
        metadata.append(f"""
        <div style="display: flex; align-items: center; gap: 0.5rem; animation: fadeIn 0.5s ease 0.2s;">
            <div style="width: 4px; height: 4px; background: #8b5cf6; border-radius: 50%;"></div>
            <div style="font-size: 0.75rem; color: #6b7280;">Charts: <span style="color: #8b5cf6; font-weight: 600;">{chart_count}</span></div>
        </div>
        """)
    if metadata:
        return f"""
        <div style="display: flex; flex-wrap: wrap; gap: 1rem; margin-top: 1rem; padding: 0.75rem; background: rgba(0, 0, 0, 0.02); border-radius: 10px; border: 1px solid rgba(0, 0, 0, 0.05);">
            {''.join(metadata)}
        </div>
        """
    return ""


def get_success_indicator_html(message: str) -> str:
    return f"""
    <div class="success-micro" style="display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.5rem 1rem; background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.05)); border-radius: 10px; border: 1px solid rgba(16, 185, 129, 0.2); margin-bottom: 1rem;">
        <div style="display: flex; align-items: center; justify-content: center; width: 24px; height: 24px; background: #10b981; border-radius: 8px; color: white; font-size: 0.9rem;">
            ✓
        </div>
        <div style="font-size: 0.9rem; color: #065f46; font-weight: 600;">{message}</div>
    </div>
    """


def get_error_indicator_html(message: str) -> str:
    return f"""
    <div class="error-indicator" style="display:inline-flex;align-items:center;gap:12px;padding:14px 20px;background:rgba(239,68,68,0.08);border-radius:10px;border:1px solid rgba(239,68,68,0.12);margin:0 0 16px 0;transition:all 0.32s cubic-bezier(0.2,0,0,1);cursor:default;">
        <div class="error-icon" style="display:flex;align-items:center;justify-content:center;width:20px;height:20px;background:rgba(239,68,68,0.9);border-radius:6px;color:white;font-size:11px;font-weight:500;flex-shrink:0;font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI','SF Pro Text',system-ui,sans-serif;transition:all 0.28s cubic-bezier(0.2,0,0,1);backdrop-filter:blur(2px);">!</div>
        <div class="error-message" style="font-size:13.5px;color:#fca5a5;font-weight:430;line-height:1.5;letter-spacing:0.02em;font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI','SF Pro Text',system-ui,sans-serif;transition:color 0.24s cubic-bezier(0.2,0,0,1);">{message}</div>
    </div>
    <style>
        .error-indicator:hover{{
            background:rgba(239,68,68,0.10);
            border-color:rgba(239,68,68,0.18);
            transform:translateY(-1px);
        }}
        .error-indicator:hover .error-icon{{
            transform:scale(1.1) translateZ(0);
            background:rgba(239,68,68,0.95);
            box-shadow:0 2px 8px rgba(239,68,68,0.25);
        }}
        .error-indicator:hover .error-message{{
            color:#f87171;
            font-weight:450;
        }}
        .error-indicator:active{{
            transform:translateY(0);
            transition-duration:0.16s;
        }}
        .error-indicator:active .error-icon{{
            transform:scale(0.98);
            transition-duration:0.08s;
        }}
        @media (prefers-reduced-motion: reduce) {{
            .error-indicator, .error-icon, .error-message {{
                transition:none;
            }}
        }}
    </style>
    """


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "render_ai_copilot_tab",
    "render_chat_history",
    "_validate_dataset",
]