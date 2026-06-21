# ai_call.py - PRODUCTION GRADE AI INTERFACE
"""
AI provider interfaces for Data Explorer Pro.
"""

import json
import re
import logging
import time
from typing import Optional, Dict, Any, List, Tuple
import pandas as pd
import streamlit as st
from datetime import datetime

logger = logging.getLogger(__name__)

# Import canonical schema and normalization
from core.ai.charts_utils import (
    normalize_ai_response, 
    SUPPORTED_CHART_TYPES,
    validate_chart_possibility,
    CHART_FAMILIES,
)

# ============================================================================
# PROVIDER AVAILABILITY CHECKS
# ============================================================================

# Google Generative AI (Gemini)
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except (ImportError, AttributeError):
    genai = None
    GENAI_AVAILABLE = False

# Anthropic (Claude)
try:
    import anthropic
    CLAUDE_AVAILABLE = True
except (ImportError, AttributeError):
    anthropic = None
    CLAUDE_AVAILABLE = False

# ============================================================================
# AI PROVIDER CLASSES
# ============================================================================

class GeminiProvider:
    """Google Gemini AI provider with exponential backoff and retries."""
    
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash-lite"):
        if not api_key or not isinstance(api_key, str):
            raise ValueError("Valid API key required for Gemini")
        
        if not GENAI_AVAILABLE:
            raise RuntimeError("Google Generative AI library not available")
        
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model)
            self.model_name = model
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            raise RuntimeError(f"Gemini initialization failed: {str(e)}")
    
    def generate_content(self, prompt: str, temperature: float = 0.3, max_retries: int = 2) -> str:
        """Generate content from Gemini with exponential backoff."""
        last_error = None
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    wait_time = 2 ** attempt
                    logger.info(f"Retry attempt {attempt + 1}/{max_retries}, waiting {wait_time}s")
                    time.sleep(wait_time)
                
                response = self.model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": max(0.1, min(0.9, temperature)),
                        "max_output_tokens": 2048,
                        "top_p": 0.95,
                        "top_k": 40
                    }
                )
                
                if not response or not hasattr(response, 'text'):
                    raise ValueError("Empty response from Gemini")
                
                return response.text
                
            except Exception as e:
                last_error = e
                logger.warning(f"Gemini API attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"All {max_retries} Gemini attempts failed")
                    raise RuntimeError(f"Gemini generation failed after {max_retries} attempts: {str(e)}")
        
        raise RuntimeError(f"Unexpected error in Gemini generation: {last_error}")

class ClaudeProvider:
    """Anthropic Claude AI provider with robust error handling."""
    
    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307"):
        if not api_key or not isinstance(api_key, str):
            raise ValueError("Valid API key required for Claude")
        
        if not CLAUDE_AVAILABLE:
            raise RuntimeError("Anthropic Claude library not available")
        
        try:
            self.client = anthropic.Anthropic(api_key=api_key)
            self.model_name = model
        except Exception as e:
            logger.error(f"Failed to initialize Claude: {e}")
            raise RuntimeError(f"Claude initialization failed: {str(e)}")
    
    def generate_content(self, prompt: str, temperature: float = 0.3, max_retries: int = 2) -> str:
        """Generate content from Claude with retries."""
        last_error = None
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    wait_time = 2 ** attempt
                    logger.info(f"Retry attempt {attempt + 1}/{max_retries}, waiting {wait_time}s")
                    time.sleep(wait_time)
                
                response = self.client.messages.create(
                    model=self.model_name,
                    max_tokens=2048,
                    temperature=max(0.1, min(0.9, temperature)),
                    messages=[{"role": "user", "content": prompt}]
                )
                
                if not response or not response.content:
                    raise ValueError("Empty response from Claude")
                
                return response.content[0].text
                
            except Exception as e:
                last_error = e
                logger.warning(f"Claude API attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"All {max_retries} Claude attempts failed")
                    raise RuntimeError(f"Claude generation failed after {max_retries} attempts: {str(e)}")
        
        raise RuntimeError(f"Unexpected error in Claude generation: {last_error}")

# ============================================================================
# ENHANCED PROMPT ENGINEERING WITH DATA INTELLIGENCE
# ============================================================================

def build_detailed_column_info(df: pd.DataFrame, max_columns: int = 12) -> str:
    """Build comprehensive column information for AI context."""
    if df is None or df.empty:
        return "No dataset available for analysis."
    
    column_info = []
    
    # Limit columns for token efficiency
    columns = list(df.columns)[:max_columns]
    
    for col in columns:
        try:
            series = df[col]
            dtype = str(series.dtype)
            non_null = series.count()
            total = len(df)
            null_pct = (series.isnull().sum() / total) * 100
            unique = series.nunique()
            
            # Get sample value
            sample = None
            if not series.empty:
                first_non_null = series.dropna().iloc[0] if not series.dropna().empty else None
                if first_non_null is not None:
                    sample_str = str(first_non_null)
                    if len(sample_str) > 40:
                        sample = sample_str[:37] + "..."
                    else:
                        sample = sample_str
            
            info = f"**{col}** ({dtype})\n"
            info += f"• Complete: {non_null:,}/{total:,} ({100 - null_pct:.1f}%)\n"
            info += f"• Unique: {unique:,} values\n"
            
            # if sample:
            #     info += f"• Sample: `{sample}`\n"
            
            if pd.api.types.is_numeric_dtype(series) and non_null > 0:
                try:
                    info += f"• Range: {series.min():.2f} to {series.max():.2f}\n"
                    info += f"• Average: {series.mean():.2f}\n"
                except:
                    pass
            
            elif pd.api.types.is_datetime64_any_dtype(series) and non_null > 0:
                try:
                    info += f"• Dates: {series.min().date()} to {series.max().date()}\n"
                except:
                    pass
            
            elif series.dtype == 'object' and unique < 15 and unique > 0:
                try:
                    top_vals = series.dropna().value_counts().head(3)
                    if not top_vals.empty:
                        top_list = [f"'{k}' ({v})" for k, v in top_vals.items()]
                        info += f"• Top: {', '.join(top_list)}\n"
                except:
                    pass
            
            column_info.append(info)
        except Exception as e:
            logger.debug(f"Could not analyze column {col}: {e}")
            column_info.append(f"**{col}** (error)\n• Could not analyze this column")
    
    return "\n\n".join(column_info)

def build_story_and_charts_prompt(
    df_summary: Dict[str, Any],
    user_prompt: str,
) -> str:
    """Enhanced prompt with detailed column info and clear schema families."""
    # Get df from session state for column details
    df = None
    if 'dataset' in st.session_state:
        df = st.session_state.dataset
    
    # Build detailed column info if df is available
    column_details = ""
    if df is not None:
        column_details = build_detailed_column_info(df)
    
    # Extract basic column info from summary
    numeric_cols = df_summary.get('numeric_columns', [])[:6]
    categorical_cols = df_summary.get('categorical_columns', [])[:6]
    datetime_cols = df_summary.get('datetime_columns', [])[:3]
    
    row_count = df_summary.get('row_count', 0)
    col_count = df_summary.get('col_count', 0)
    missing_pct = df_summary.get('missing_data_percentage', 0)
    
    # Schema families explanation
    schema_families = """
## 📐 CHART SCHEMA FAMILIES (USE CORRECT FIELDS):

### 1. XY CHARTS (bar, line, scatter, histogram, box, violin, bubble, heatmap)
   - **Required**: 'x' (always)
   - **Optional**: 'y', 'color', 'size'
   - **Example**: {"chart_type": "bar", "x": "Category", "y": "Sales", "color": "Region"}

### 2. METRIC CHARTS (card, kpi, gauge)
   - **Required**: 'value_col'
   - **Optional**: 'agg_func' (sum/mean/count/last), 'target_value' (NUMBER only)
   - **Example**: {"chart_type": "kpi", "value_col": "Revenue", "target_value": 1000000}

### 3. HIERARCHICAL CHARTS (treemap)
   - **Required**: 'path' (ARRAY of columns for hierarchy)
   - **Optional**: 'values', 'color', 'agg_func'
   - **Example**: {"chart_type": "treemap", "path": ["Region", "Country"], "values": "Sales"}

### 4. GEOSPATIAL CHARTS (bubble_map)
   - **Required**: 'lat_col', 'lon_col'
   - **Optional**: 'size_col', 'color_col'
   - **Example**: {"chart_type": "bubble_map", "lat_col": "latitude", "lon_col": "longitude"}

### 5. SPECIAL CHARTS
   - **correlation_matrix**: Auto-calculates (no fields needed)
   - **pie**: Uses 'x' for categories, 'y' for values
"""
    
    # Build prompt
    prompt = f"""# 📊 AI Data Analysis Request
You are a senior data analyst at a top consulting firm. Your client has asked: "{user_prompt}"

## 📋 DATASET OVERVIEW
• **Size**: {row_count:,} records × {col_count} columns
• **Data Quality**: {100 - missing_pct:.1f}% complete
• **Numeric Columns**: {len(numeric_cols)} (e.g., {', '.join(numeric_cols[:3]) if numeric_cols else 'none'})
• **Categorical Columns**: {len(categorical_cols)} (e.g., {', '.join(categorical_cols[:3]) if categorical_cols else 'none'})
• **Date/Time Columns**: {len(datetime_cols)} (e.g., {', '.join(datetime_cols[:2]) if datetime_cols else 'none'})

## 🔍 DETAILED COLUMN INFORMATION
{column_details if column_details else "*No detailed column info available*"}

{schema_families}

## 🎯 YOUR TASK
1. **Analyze** the data in context of the user's request
2. **Suggest 3-5** relevant, actionable visualizations (quality over quantity)
3. For **EACH chart**, use **EXACT** column names from the data above
4. Ensure charts are **actually possible** with available data and column types
5. Tell a **compelling data story** that answers the user's question

## 📝 RESPONSE FORMAT (STRICT JSON ONLY):
{{
  "story": "2-3 paragraph narrative analysis with clear insights... Reference charts as [CHART_1], [CHART_2], etc.",
  "charts": [
    {{
      "chart_type": "bar",
      "x": "exact_column_name",
      "y": "exact_column_name",
      "color": "exact_column_name_if_applicable",
      "title": "Clear, business-focused title",
      "description": "What this chart shows and why it matters (1 sentence)"
    }}
  ]
}}

## 🚨 CRITICAL RULES:
1. ✅ Use **ONLY** column names that exist in the data above
2. ✅ For **metric charts**, use 'value_col' NOT 'y'
3. ✅ For **treemap**, use 'path' array NOT single 'x'
4. ✅ For **bubble_map**, use 'lat_col' and 'lon_col' NOT 'x' and 'y'
5. ✅ 'target_value' must be a **NUMBER** (not column name)
6. ✅ Return **ONLY** the JSON object, no other text or markdown
7. ✅ Validate each chart is possible with the given columns and data types

## 💡 PRO TIPS:
• Match chart types to data types (dates → line charts, categories → bar charts)
• Start simple - ensure basic charts work before adding complexity
• Consider the business context when suggesting visualizations
• Focus on insights that answer the user's specific question"""
    
    return prompt

# ============================================================================
# CLEAN JSON PARSING
# ============================================================================

def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract JSON from AI response with intelligent cleanup.
    Focused on common AI response patterns.
    """
    if not text or not isinstance(text, str):
        return None
    
    text = text.strip()
    
    # Remove common JSON wrappers and code blocks
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(r'\s*```$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^json\s*\n', '', text, flags=re.IGNORECASE)
    
    # Find JSON boundaries - look for { at start or after some text
    start = text.find('{')
    end = text.rfind('}')
    
    if start == -1 or end == -1 or end < start:
        # Try to find array format
        start = text.find('[')
        end = text.rfind(']')
        if start == -1 or end == -1 or end < start:
            logger.warning("No JSON structure found in response")
            return None
    
    json_str = text[start:end + 1]
    
    # Try direct parse first
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.debug(f"Initial JSON parse failed: {e}")
        
        # Common AI JSON issues fix
        try:
            # Fix 1: Remove trailing commas
            json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
            
            # Fix 2: Quote unquoted keys (simple cases)
            lines = json_str.split('\n')
            fixed_lines = []
            
            for line in lines:
                # Match unquoted keys at start of object
                if ':' in line and '"' not in line.split(':')[0].strip():
                    parts = line.split(':', 1)
                    key = parts[0].strip()
                    # Only quote if it looks like a valid identifier
                    if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
                        line = f'"{key}":{parts[1]}'
                fixed_lines.append(line)
            
            json_str = '\n'.join(fixed_lines)
            
            # Fix 3: Replace Python None/True/False with JSON null/true/false
            json_str = json_str.replace('None', 'null')
            json_str = json_str.replace('True', 'true')
            json_str = json_str.replace('False', 'false')
            
            return json.loads(json_str)
            
        except json.JSONDecodeError as e2:
            logger.warning(f"JSON parsing failed after fixes: {e2}")
            logger.debug(f"Failed JSON snippet: {json_str[:200]}...")
            return None

# ============================================================================
# MAIN AI REQUEST FUNCTION WITH ENHANCED VALIDATION
# ============================================================================

def request_ai_json(
    prompt: str,
    api_key: str,
    model: str = "gemini-2.5-flash-lite",
    temperature: float = 0.3,
    df: Optional[pd.DataFrame] = None,
    max_retries: int = 2
) -> Optional[Dict[str, Any]]:
    """
    Request JSON response from AI with enhanced validation.
    Returns response with canonical normalization applied.
    """
    # Validate inputs
    if not prompt or not isinstance(prompt, str):
        logger.error("Invalid prompt provided")
        return None
    
    # EchoEngine mode if no API key or explicitly requested
    if not api_key or not api_key.strip() or model == "EchoEngine":
        logger.info("Using EchoEngine (no API key or EchoEngine requested)")
        if df is not None:
            return _generate_EchoEngine_response(df, prompt)
        return None
    
    # Check provider availability
    if model.startswith("gemini") and not GENAI_AVAILABLE:
        logger.error("Gemini requested but library not available")
        if df is not None:
            return _generate_EchoEngine_response(df, prompt)
        return None
    
    if model.startswith("claude") and not CLAUDE_AVAILABLE:
        logger.error("Claude requested but library not available")
        if df is not None:
            return _generate_EchoEngine_response(df, prompt)
        return None
    
    # Try AI request with retries
    last_error = None
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                wait_time = 2 ** attempt
                logger.info(f"Retry attempt {attempt + 1}/{max_retries}, waiting {wait_time}s")
                time.sleep(wait_time)
            
            # Log request
            if st.session_state.get('debug_mode', False):
                logger.info(f"🤖 AI Request Attempt {attempt + 1}")
                logger.debug(f"Prompt length: {len(prompt):,} chars")

            print("╔══════════════════════════════════════════════════════════════════════════════╗")
            print("║                            🤖 PROMPT TO AI                                   ║")
            print("╚══════════════════════════════════════════════════════════════════════════════╝")
            print(prompt)
            print("════════════════════════════════════════════════════════════════════════════════")
            
            # ===== DEVELOPMENT MODE: MANUAL INPUT =====
            DEV_MODE = False  # Set to False for production
            
            if DEV_MODE:
                print("\n" + "═" * 80)
                print("🧪 DEVELOPMENT MODE: MANUAL INPUT REQUIRED")
                print("═" * 80)
                print(f"📊 Dataset: {len(df):,} rows × {len(df.columns) if df is not None else 0} columns")
                print(f"🤖 Model: {model}")
                print(f"🌡️  Temperature: {temperature}")
                print("\nPlease paste the AI response below (JSON format):")
                print("(Type 'END' on a new line when finished)")
                print("-" * 80)
                
                # Read multi-line input from user
                response_lines = []
                try:
                    while True:
                        line = input()
                        if line.strip() == 'END':
                            break
                        response_lines.append(line)
                except (EOFError, KeyboardInterrupt):
                    print("\n⚠️  Input interrupted, using empty response")
                
                response_text = "\n".join(response_lines)
                
                print(f"\n✅ Manual response received: {len(response_text):,} characters")
                
            else:
                # Production AI call
                if model.startswith("gemini"):
                    provider = GeminiProvider(api_key, model)
                    response_text = provider.generate_content(prompt, temperature, max_retries=1)
                elif model.startswith("claude"):
                    provider = ClaudeProvider(api_key, model)
                    response_text = provider.generate_content(prompt, temperature, max_retries=1)
                else:
                    raise ValueError(f"Unsupported model: {model}")
            
            print("\n╔══════════════════════════════════════════════════════════════════════════════╗")
            print("║                            📝 RAW AI RESPONSE                                 ║")
            print("╚══════════════════════════════════════════════════════════════════════════════╝")
            print(response_text)
            print("════════════════════════════════════════════════════════════════════════════════")
            
            # Parse response
            parsed = extract_json_from_text(response_text)
            
            if not parsed:
                logger.warning(f"Failed to parse JSON response (attempt {attempt + 1})")
                
                # In dev mode, offer manual fix
                if DEV_MODE and attempt == max_retries - 1:
                    print("\n⚠️  JSON parsing failed. Enter corrected JSON (type 'END' when done):")
                    fixed_lines = []
                    while True:
                        line = input()
                        if line.strip() == 'END':
                            break
                        fixed_lines.append(line)
                    
                    fixed_json = "\n".join(fixed_lines)
                    try:
                        parsed = json.loads(fixed_json)
                        print("✅ Manual JSON accepted")
                    except:
                        print("❌ Invalid JSON, continuing with EchoEngine")
                        break
                continue
            
            # Validate basic structure
            if not isinstance(parsed, dict):
                logger.warning(f"Response is not a dictionary (attempt {attempt + 1})")
                continue
            
            # Ensure charts array exists
            if 'charts' not in parsed:
                parsed['charts'] = []
            
            # ENHANCED VALIDATION: Normalize and validate all charts
            validated_charts = []
            validation_warnings = []
            validation_errors = []
            
            for i, chart in enumerate(parsed.get('charts', [])):
                if isinstance(chart, dict):
                    # Normalize with family awareness
                    normalized = normalize_ai_response(chart)
                    
                    # Validate against data if available
                    if df is not None:
                        validation_result = validate_chart_possibility(normalized, df)
                        is_valid, msg, level = validation_result.is_valid, validation_result.message, validation_result.level

                        
                        if is_valid and level == "success":
                            # Add index for reference
                            normalized['_index'] = i + 1
                            normalized['_validated'] = True
                            normalized['_validation_status'] = 'valid'
                            validated_charts.append(normalized)
                            
                        elif is_valid and level == "warning":
                            # Keep with warning
                            normalized['_index'] = i + 1
                            normalized['_validated'] = True
                            normalized['_validation_status'] = 'warning'
                            normalized['_warning'] = msg
                            validated_charts.append(normalized)
                            validation_warnings.append(f"Chart {i+1}: {msg}")
                            
                        else:
                            # Skip invalid chart
                            validation_errors.append(f"Chart {i+1}: {msg}")
                            logger.warning(f"Skipping invalid chart {i+1}: {msg}")
                    else:
                        # No data for validation, just normalize
                        normalized['_index'] = i + 1
                        normalized['_validation_status'] = 'unvalidated'
                        validated_charts.append(normalized)
            
            parsed['charts'] = validated_charts
            
            # Add validation summary to story if any issues
            if (validation_warnings or validation_errors) and 'story' in parsed:
                validation_note = "\n\n## 📋 Validation Summary"
                
                if validation_warnings:
                    validation_note += f"\n\n⚠️  **Warnings** ({len(validation_warnings)}):"
                    for i, warning in enumerate(validation_warnings[:3], 1):
                        validation_note += f"\n{i}. {warning}"
                
                if validation_errors:
                    validation_note += f"\n\n❌ **Skipped Charts** ({len(validation_errors)}):"
                    for i, error in enumerate(validation_errors[:3], 1):
                        validation_note += f"\n{i}. {error}"
                    
                    if len(validation_errors) > 3:
                        validation_note += f"\n... and {len(validation_errors) - 3} more"
                
                parsed['story'] += validation_note
            
            # Ensure story exists
            if 'story' not in parsed or not parsed['story']:
                parsed['story'] = f"## 📊 Analysis\n\nAnalysis generated successfully from {len(validated_charts)} validated chart(s)."
            
            # Add comprehensive metadata
            parsed['metadata'] = {
                **parsed.get('metadata', {}),
                'model': model,
                'temperature': temperature,
                'attempt': attempt + 1,
                'normalized': True,
                'validation_enabled': df is not None,
                'chart_count': len(validated_charts),
                'validated_count': len([c for c in validated_charts if c.get('_validated', False)]),
                'warning_count': len(validation_warnings),
                'error_count': len(validation_errors),
                'generated_at': time.time(),
                'generated_at_human': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'prompt_length': len(prompt),
                'response_length': len(response_text) if 'response_text' in locals() else 0,
            }
            
            # Log success
            chart_count = len(validated_charts)
            valid_count = len([c for c in validated_charts if c.get('_validated', False)])
            
            if chart_count > 0:
                status_icon = "✅" if validation_errors == 0 else "⚠️"
                print(f"\n{status_icon} AI response processed: {valid_count}/{chart_count} charts validated")
                if validation_warnings:
                    print(f"   ⚠️  {len(validation_warnings)} warning(s)")
                if validation_errors:
                    print(f"   ❌ {len(validation_errors)} chart(s) skipped")
                
                logger.info(f"AI response: {valid_count}/{chart_count} charts validated, {len(validation_warnings)} warnings")
            else:
                print(f"\n⚠️  AI response successful but generated 0 valid charts")
                logger.warning(f"AI response successful but generated 0 valid charts")
            
            return parsed
                
        except Exception as e:
            print(f"\n❌ AI request attempt {attempt + 1} failed: {e}")
            logger.warning(f"AI request attempt {attempt + 1} failed: {e}")
            
            last_error = e
            
            if attempt == max_retries - 1:
                print(f"\n💥 All {max_retries} attempts failed, falling back to EchoEngine")
                logger.error(f"All {max_retries} AI attempts failed: {last_error}")
                break
    
    # All attempts failed, fall back to EchoEngine
    if df is not None:
        logger.info("Falling back to EchoEngine response")
        return _generate_EchoEngine_response(df, prompt)
    
    return None

# ============================================================================
# ECHO ENGINE FALLBACK
# ============================================================================

def _generate_EchoEngine_response(df: pd.DataFrame, prompt: str) -> Dict[str, Any]:
    """
    Generate intelligent EchoEngine fallback response.
    Uses canonical normalization for consistency.
    """
    try:
        from core.ai.echo_engine import EchoChartRecommender
        
        recommender = EchoChartRecommender()
        
        # Extract user request from prompt
        user_match = re.search(r'asked:\s*"([^"]+)"', prompt) or re.search(r'request:\s*"([^"]+)"', prompt)
        user_request = user_match.group(1) if user_match else prompt[:100]
        
        # Get recommendations
        raw_charts = recommender.recommend_charts(df, user_request, max_suggestions=5)
        
        # NORMALIZE all charts using canonical schema
        normalized_charts = []
        for i, chart in enumerate(raw_charts):
            if isinstance(chart, dict):
                normalized = normalize_ai_response(chart)
                normalized['_index'] = i + 1
                normalized['heuristic'] = True
                normalized['_validation_status'] = 'heuristic'
                normalized_charts.append(normalized)
        
        # Build professional story
        story = f"""## 📊 Analysis: {user_request}

**Dataset**: {len(df):,} records × {len(df.columns)} columns
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Mode**: Heuristic analysis (EchoEngine)

### 🎯 Overview
Analyzing your data using intelligent pattern detection and rule-based recommendations.

### 📈 Recommended Visualizations"""

        for i, chart in enumerate(normalized_charts):
            chart_ref = f"[CHART_{i+1}]"
            title = chart.get('title', f'Chart {i+1}')
            description = chart.get('description', '')
            chart_type = chart.get('chart_type', 'chart').title()
            story += f"\n\n**{i+1}. {title}** {chart_ref}\n*Type*: {chart_type}\n*Description*: {description}"
        
        story += f"""

### 💡 Insights
• Based on {len(df):,} data points across {len(df.columns)} variables
• Using heuristic pattern detection optimized for clarity
• Recommendations prioritize actionable business insights

### 🔧 Next Steps
• Review the suggested visualizations above
• Click on any chart to view details and customize
• For AI-powered insights with deeper analysis, provide an API key

---
*Generated by EchoEngine heuristic analysis at {datetime.now().strftime('%H:%M')}*"""
        
        return {
            "story": story,
            "charts": normalized_charts,
            "ai_generated": False,
            "model": "EchoEngine",
            "metadata": {
                "source": "EchoEngine",
                "generated_at": time.time(),
                "fallback_mode": True,
                "heuristic_analysis": True,
                "normalized_charts": len(normalized_charts),
                "generated_at_human": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "prompt": prompt[:200] + "..." if len(prompt) > 200 else prompt
            }
        }
        
    except Exception as e:
        logger.error(f"EchoEngine fallback failed: {e}")
        
        # Ultimate minimal fallback with canonical empty chart
        empty_chart = normalize_ai_response({
            "chart_type": "histogram",
            "title": "Dataset Overview",
            "description": "Basic data distribution",
            "_validation_status": "emergency"
        })
        
        return {
            "story": f"""## ⚠️ Analysis Limited

**Dataset**: {len(df):,} records × {len(df.columns)} columns  
**Status**: Basic overview (full analysis unavailable)  
**Error**: {str(e)[:100]}

### 📋 Basic Statistics
- Records: {len(df):,}
- Columns: {len(df.columns)}
- Data quality: {100 - (df.isnull().sum().sum()/(len(df)*len(df.columns))*100):.1f}% complete

### 🔧 Suggested Actions
1. Try a simpler or more specific question
2. Check your data quality and completeness
3. Use the manual analysis tools in Chart Studio
4. For AI-powered insights, provide a valid API key

---
*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*""",
            "charts": [empty_chart] if df is not None and not df.empty else [],
            "ai_generated": False,
            "model": "fallback",
            "metadata": {
                "error": str(e)[:100],
                "fallback_mode": True,
                "emergency_mode": True,
                "generated_at": time.time(),
                "generated_at_human": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }

# ============================================================================
# PROFESSIONAL UTILITY FUNCTIONS
# ============================================================================

def get_available_models() -> List[str]:
    """Get list of available AI models with status."""
    models = ["EchoEngine"]
    
    if GENAI_AVAILABLE:
        models.append("gemini-2.5-flash-lite")
        models.append("gemini-pro")
        models.append("gemini-1.5-pro")
    
    if CLAUDE_AVAILABLE:
        models.append("claude-3-haiku-20240307")
        models.append("claude-3-sonnet-20240229")
        models.append("claude-3-opus-20240229")
    
    return models

def validate_api_key(api_key: str, model: str) -> Tuple[bool, str]:
    """
    Validate API key and model compatibility professionally.
    """
    if model == "EchoEngine":
        return True, "✅ EchoEngine mode enabled"
    
    if not api_key or not api_key.strip():
        return False, "❌ API key is required for live AI models"
    
    if len(api_key) < 20:
        return False, "❌ API key appears too short (minimum 20 characters)"
    
    if model.startswith("gemini") and not GENAI_AVAILABLE:
        return False, "❌ Gemini library not installed. Run: pip install google-generativeai"
    
    if model.startswith("claude") and not CLAUDE_AVAILABLE:
        return False, "❌ Claude library not installed. Run: pip install anthropic"
    
    # Check for common API key patterns
    if model.startswith("gemini") and not api_key.startswith("AIza"):
        return False, "⚠️ Gemini API keys usually start with 'AIza'. Please verify your key."
    
    if model.startswith("claude") and not (api_key.startswith("sk-ant-") or len(api_key) > 40):
        return False, "⚠️ Claude API keys usually start with 'sk-ant-'. Please verify your key."
    
    return True, "✅ Valid API key"

def get_api_provider_status() -> Dict[str, bool]:
    """Get professional status report of all API providers."""
    return {
        "gemini_available": GENAI_AVAILABLE,
        "claude_available": CLAUDE_AVAILABLE,
        "echo_engine_available": True,
        "normalization_available": True,
        "detailed_prompts_enabled": True,
        "chart_families_enabled": True,
        "validation_enabled": True,
    }

def get_ai_system_status() -> Dict[str, Any]:
    """Get comprehensive AI system status report."""
    return {
        "providers": get_api_provider_status(),
        "available_models": get_available_models(),
        "chart_families": list(CHART_FAMILIES.keys()),
        "supported_charts": list(SUPPORTED_CHART_TYPES),
        "enhancements": {
            "detailed_column_info": True,
            "family_aware_normalization": True,
            "chart_validation": True,
            "warning_system": True,
            "fallback_mechanisms": True
        },
        "timestamp": time.time(),
        "version": "2.0.0-enhanced"
    }

# ============================================================================
# QUICK ANALYSIS HELPERS
# ============================================================================

def suggest_quick_analyses(df: pd.DataFrame) -> List[Dict[str, str]]:
    """Suggest quick analyses based on data characteristics."""
    suggestions = []
    
    if df is None or df.empty:
        return suggestions
    
    # Check for date columns for trend analysis
    date_cols = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
    numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
    categorical_cols = [col for col in df.columns if df[col].dtype == "object" or pd.api.types.is_categorical_dtype(df[col])]
    
    if date_cols and numeric_cols:
        suggestions.append({
            "icon": "📈",
            "title": "Trend Analysis",
            "description": "Analyze patterns over time",
            "prompt": f"Show me trends in {numeric_cols[0]} over {date_cols[0]}"
        })
    
    if categorical_cols and numeric_cols:
        suggestions.append({
            "icon": "📊",
            "title": "Comparison",
            "description": "Compare values across categories",
            "prompt": f"Compare {numeric_cols[0]} across different {categorical_cols[0]} categories"
        })
    
    if len(numeric_cols) >= 2:
        suggestions.append({
            "icon": "🔍",
            "title": "Correlation",
            "description": "Find relationships between variables",
            "prompt": f"Find correlations between {numeric_cols[0]} and {numeric_cols[1]}"
        })
    
    if numeric_cols:
        suggestions.append({
            "icon": "📋",
            "title": "Distribution",
            "description": "Analyze data spread and outliers",
            "prompt": f"Show me the distribution of {numeric_cols[0]}"
        })
    
    suggestions.append({
        "icon": "🎯",
        "title": "Comprehensive Overview",
        "description": "Get a complete analysis of the dataset",
        "prompt": "Give me a comprehensive overview of this dataset with key insights and visualizations"
    })
    
    return suggestions

# ============================================================================
# EXPORTS (CLEAN & PROFESSIONAL)
# ============================================================================

__all__ = [
    # Provider availability
    "GENAI_AVAILABLE",
    "CLAUDE_AVAILABLE",
    
    # Core functions
    "build_story_and_charts_prompt",
    "request_ai_json",
    "extract_json_from_text",
    
    # Provider classes
    "GeminiProvider",
    "ClaudeProvider",
    
    # Utility functions
    "get_available_models",
    "validate_api_key",
    "get_api_provider_status",
    "get_ai_system_status",
    "suggest_quick_analyses",
    
    # Helper functions
    "build_detailed_column_info",
]