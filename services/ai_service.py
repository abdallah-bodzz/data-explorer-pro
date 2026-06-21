# services/ai_service.py
"""
AI Service – Orchestrates AI-powered analysis and insights.
Wraps core.ai.utils and core.ai.call functions for UI consumption.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd

from core.ai import utils as ai_utils
from core.ai.call import (
    get_available_models,
    validate_api_key,
    get_api_provider_status,
)

logger = logging.getLogger(__name__)


class AIService:
    """Service for AI analysis, insight extraction, and model management."""

    def __init__(self):
        """Initialise the AI service."""
        pass

    def generate_analysis(
        self,
        df: pd.DataFrame,
        user_prompt: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate AI analysis for the dataset.

        Args:
            df: The dataset.
            user_prompt: The user's question/request.
            config: AI configuration dict with keys:
                - model: str (e.g., 'EchoEngine', 'gemini-2.5-flash-lite')
                - api_key: str
                - temperature: float (0.1-0.9)
                - EchoEngine_mode: bool
                - debug_mode: bool
                - max_charts: int (optional)
                - min_charts: int (optional)
                If None, the function falls back to session state.

        Returns:
            Analysis result dict (story, charts, metadata, etc.)

        Raises:
            ValueError: If the dataset is invalid or the prompt is empty.
        """
        if df is None or df.empty:
            raise ValueError("Dataset is empty or None")
        if not user_prompt or not user_prompt.strip():
            raise ValueError("User prompt is empty")

        # Delegate to the core function, which now accepts an optional config
        # Note: core.ai.utils.ai_generate_analysis has been updated to accept
        # a config parameter; if not provided, it falls back to session state.
        return ai_utils.ai_generate_analysis(df, user_prompt, config)

    def extract_insights(self, story: str, max_insights: int = 5) -> List[str]:
        """
        Extract key insights from a story text.

        Args:
            story: The narrative text.
            max_insights: Maximum number of insights to return.

        Returns:
            List of insight strings.
        """
        if not story:
            return []
        return ai_utils.extract_insights_from_story(story, max_insights)

    def format_story(self, story: str) -> str:
        """
        Format a story for clean display with proper markdown.

        Args:
            story: The raw story text.

        Returns:
            Formatted story string.
        """
        if not story:
            return ""
        return ai_utils.format_story_for_display(story)

    def get_available_models(self) -> List[str]:
        """Return list of available AI models (including EchoEngine)."""
        return get_available_models()

    def validate_api_key(self, api_key: str, model: str) -> Tuple[bool, str]:
        """
        Validate API key for a specific model.

        Args:
            api_key: The API key to validate.
            model: The model name.

        Returns:
            (is_valid, message)
        """
        return validate_api_key(api_key, model)

    def get_provider_status(self) -> Dict[str, bool]:
        """Get availability status of all AI providers."""
        return get_api_provider_status()

    def should_use_echoengine(self, config: Dict[str, Any]) -> bool:
        """
        Determine if EchoEngine mode should be used based on configuration.

        Args:
            config: AI configuration dict.

        Returns:
            True if EchoEngine should be used, False otherwise.
        """
        return ai_utils.should_use_EchoEngine_mode(config)

    def get_default_config(self) -> Dict[str, Any]:
        """
        Get default AI configuration (useful for UI initialisation).

        Returns:
            Dictionary with default values for all AI settings.
        """
        return ai_utils.get_ai_config()

    # ===== Additional helpers for UI convenience =====

    def build_config_from_session(self) -> Dict[str, Any]:
        """
        Build AI configuration from the current Streamlit session state.
        This is a convenience method for UI modules that still use session state.

        Returns:
            Configuration dictionary.
        """
        import streamlit as st

        return {
            'model': st.session_state.get('ai_model', 'EchoEngine'),
            'api_key': st.session_state.get('api_key', ''),
            'temperature': st.session_state.get('ai_temperature', 0.3),
            'EchoEngine_mode': st.session_state.get('ai_EchoEngine_mode', True),
            'debug_mode': st.session_state.get('debug_mode', False),
            'max_charts': 6,
            'min_charts': 3,
        }

    def is_model_available(self, model: str) -> bool:
        """
        Check if a specific model is available (library installed and API key valid).

        Args:
            model: Model name.

        Returns:
            True if the model can be used.
        """
        available_models = self.get_available_models()
        if model not in available_models:
            return False
        if model == 'EchoEngine':
            return True
        # For live models, we need an API key and library
        status = self.get_provider_status()
        if model.startswith('gemini'):
            return status.get('gemini_available', False)
        if model.startswith('claude'):
            return status.get('claude_available', False)
        return False