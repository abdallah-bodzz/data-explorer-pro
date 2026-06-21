# Data Explorer Pro – Staged Refactoring Roadmap to a Modular, Service‑Oriented Architecture

## Executive Summary

The current codebase, while functional, has grown organically into a tightly coupled “big ball of mud”. **The main issues are:**

- **UI logic and business logic are interwoven** — many modules directly read/write `st.session_state` and contain Streamlit‑specific code.
- **`app.py` is a god module** — it imports a dozen other modules and orchestrates the entire UI, making it fragile.
- **Circular dependency** between `app.py` and `relationships_tab.py` (via `SessionStateManager`).
- **High change impact** — a modification in a core module like `ai_charts_utils.py` affects many downstream files.
- **No clear separation of concerns** — AI, data, charting, and reporting are mixed.

**The vision** is a clean, layered architecture with clear boundaries:

- **Core Layer** – pure business logic, no UI dependencies, independent of Streamlit.
- **Service Layer** – orchestrates core components, exposes clean interfaces to the UI.
- **UI Layer** – only concerned with rendering, user input, and delegating to services.
- **Reporting Layer** – uses services and core to generate reports.
- **Centralised State Management** – a single module responsible for all `st.session_state` access.

This refactoring will be carried out in **stages**, each with a clear goal, deliverable, and verification step (the app must work after each stage). This incremental approach minimises risk and allows continuous delivery.

---

## Proposed Final Architecture (The “Sexy” Structure)

We aim for a project layout like this:

```
data_explorer_pro/
├── core/
│   ├── __init__.py
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── call.py               # from ai_call.py
│   │   ├── charts_utils.py       # from ai_charts_utils.py
│   │   ├── utils.py              # from ai_utils.py
│   │   ├── config.py             # (optional, or keep in core/)
│   │   └── echo_engine/          # unchanged
│   │       ├── __init__.py
│   │       ├── engine.py
│   │       └── narratives.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── model.py              # from data_model.py
│   │   ├── operations.py         # from data_operations.py
│   │   ├── scripts_library.py    # from scripts_library.py
│   │   ├── sampler.py            # from smart_sampler.py
│   │   └── connectors.py         # from data_connectors.py (but stripped of UI)
│   └── config.py                 # global config
├── services/
│   ├── __init__.py
│   ├── ai_service.py             # orchestrates AI analysis, insight extraction
│   ├── data_service.py           # loading, filtering, sampling, transformations, joins
│   ├── chart_service.py          # chart creation, export, recommendation
│   └── report_service.py         # report generation (HTML, PDF)
├── ui/
│   ├── __init__.py
│   ├── app.py                    # thin orchestrator, tab routing
│   ├── state.py                  # StateManager (centralised session state access)
│   ├── components/               # reusable widgets (metric cards, chart containers, etc.)
│   │   ├── __init__.py
│   │   ├── cards.py
│   │   ├── charts.py
│   │   └── layout.py
│   ├── tabs/                     # each tab as a separate module
│   │   ├── __init__.py
│   │   ├── explore.py            # from data_dashboard.py
│   │   ├── ai_copilot.py         # from ai_handlers.py
│   │   ├── chart_studio.py       # from chart_handlers.py
│   │   ├── data_prep.py          # combines filtering, operations, scripts
│   │   ├── relationships.py      # from relationships_tab.py
│   │   └── report_builder.py     # from report_builder.py
│   └── styles.py                 # CSS/HTML templates (from ui_components.py)
├── reporting/
│   ├── __init__.py
│   └── html_export.py            # from export_HTML_report.py (logic only, UI removed)
├── utils/                        # general helpers
│   ├── __init__.py
│   └── helpers.py                # (e.g., safe_truncate, format_bytes)
└── main.py                       # Streamlit entry point (renamed from app.py)
```

**Key principles:**

- **Core** has no imports from `streamlit` or `st.session_state`.
- **Services** import only from `core` and standard libraries; they may accept a state manager as a dependency.
- **UI** imports from `services` and `ui.state`; it handles rendering and user events.
- **StateManager** is a single class that all UI modules use to read/write session state. It can be initialised with a default state.

---

## Staged Refactoring Plan

We will break the transformation into **6 stages**. Each stage ends with a working application.

### Stage 0: Preparation (Before Starting)

**Goal:** Set up the foundation for safe refactoring.

- Write a comprehensive set of **smoke tests** (or at least manual test scripts) that cover the main user flows: loading data, filtering, creating charts, running AI analysis, building a report.
- Establish a **feature flag** system (e.g., environment variable `USE_LEGACY_IMPORTS`) to allow gradual switching between old and new modules during the transition.
- Ensure the current codebase is committed to a separate branch (e.g., `refactor/stage-1`).

**Deliverables:** A test suite and a fallback mechanism.

---

### Stage 1: Directory Restructuring (Move Files, Update Imports)

**Goal:** Reorganise the physical files into the new package structure without altering any logic. The app must still work exactly as before.

**Steps:**

1. Create the new directory tree (`core/ai/`, `core/data/`, `services/`, `ui/tabs/`, etc.).
2. Move each existing file to its new location, **keeping the original filename** (e.g., `ai_call.py` → `core/ai/call.py`).
3. Update all import statements **within the project** to reflect the new paths. Use relative or absolute imports as appropriate.
4. Keep `app.py` as the entry point but place it at the root (or rename to `main.py`). For now, keep it as is.
5. Ensure that `__init__.py` files are added to expose the needed components (e.g., `core/ai/__init__.py` can import `call`, `charts_utils`, `utils`).
6. Update any hard‑coded file paths (e.g., to `charts/` directory) if necessary.
7. Verify the app runs with the new structure. Use the feature flag to optionally fall back to old imports if something breaks.

**Deliverables:** A working app with a new directory layout. No behaviour changes.

**Example change (before → after):**

*Before:*
```python
# in ai_handlers.py
from ai_utils import ai_generate_analysis
```

*After:*
```python
# in ui/tabs/ai_copilot.py (formerly ai_handlers.py)
from core.ai.utils import ai_generate_analysis
```

We also need to update `app.py` imports accordingly.

---

### Stage 2: Introduce Service Layer – Extract Business Logic from UI

**Goal:** Create service classes that encapsulate all business logic, and start moving logic out of UI modules. The UI modules will then call these services instead of directly invoking core functions.

**Steps:**

1. Identify the main “orchestration” functions that are currently called from UI:
   - `ai_generate_analysis` (in `ai_utils.py`) – should become a method of `AIService`.
   - Data loading/filtering/sampling (in `data_handlers.py`) – should become `DataService`.
   - Chart creation and recommendation (in `chart_handlers.py` and `echo_engine`) – should become `ChartService`.
   - Report generation (in `export_HTML_report.py` and `report_builder.py`) – should become `ReportService`.

2. Create a new package `services/` with modules:
   - `ai_service.py`
   - `data_service.py`
   - `chart_service.py`
   - `report_service.py`

3. For each service, define a class with methods that accept **explicit parameters** (no `st.session_state`). The service can optionally accept a `state_manager` to persist/retrieve data, but it should not directly use `st.session_state`.

4. Move the core logic from the original modules into these services. Keep the original modules as thin wrappers that call the service (during the transition).

5. Update UI modules to instantiate the services (or use a global service instance) and call them. For now, we can keep the old code and add the new service calls alongside, then gradually remove the old code.

6. **Crucially**, the `StateManager` (from Stage 3) is not yet fully implemented; for now, services can still read/write `st.session_state` directly **but only through a centralised object** to be introduced later. At this stage, we will pass the current `df` and other parameters explicitly, so services are still relatively pure.

**Example: `AIService`**

```python
# services/ai_service.py
from core.ai import utils as ai_utils
from core.ai.call import request_ai_json
from core.ai.charts_utils import create_ai_plot_from_suggestion

class AIService:
    def __init__(self, config=None):
        self.config = config or {}

    def generate_analysis(self, df, user_prompt, model_config):
        # Calls ai_utils.ai_generate_analysis but with explicit parameters
        return ai_utils.ai_generate_analysis(df, user_prompt, model_config)

    def extract_insights(self, story):
        return ai_utils.extract_insights_from_story(story)

    def create_chart_from_suggestion(self, df, suggestion):
        return create_ai_plot_from_suggestion(df, suggestion)
```

**UI changes (in `ai_copilot.py`):**

```python
# ui/tabs/ai_copilot.py
from services.ai_service import AIService
ai_service = AIService()

def _process_user_input(user_prompt):
    # ... get df from state (or from DataService)
    result = ai_service.generate_analysis(df, user_prompt, config)
    # ... update chat history via state manager
```

**Deliverables:** A working app where UI modules delegate to service classes for major operations. The old code inside UI modules is gradually replaced.

---

### Stage 3: Centralise Session State Management

**Goal:** Create a single `StateManager` class that encapsulates all `st.session_state` read/write operations. UI modules will no longer access `st.session_state` directly; they will use the state manager.

**Steps:**

1. Create `ui/state.py` with a `StateManager` class.
2. The `StateManager` should provide getters and setters for all global state variables:
   - `dataset`, `original_dataset`, `base_dataset`
   - `filter_state`, `filter_history`
   - `chat_history`
   - `current_chart`, `chart_history`
   - `report_builder_sections`, `report_builder_charts`
   - `ai_model`, `api_key`, `ai_EchoEngine_mode`
   - etc.
3. The `StateManager` can be a simple wrapper around `st.session_state` but it centralises the keys and provides default values.
4. Update **all** UI modules to import the `StateManager` and use its methods instead of directly accessing `st.session_state`.
5. The services should also receive the `StateManager` (or a subset of it) as a dependency, but for now they can keep using the direct access until we refactor them to accept state via parameters.

**Example `StateManager`:**

```python
# ui/state.py
import streamlit as st
from typing import Optional, Dict, Any, List
import pandas as pd

class StateManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self._init_defaults()

    def _init_defaults(self):
        defaults = {
            'dataset': None,
            'original_dataset': None,
            'base_dataset': None,
            'filter_state': {...},
            'chat_history': [],
            'current_chart': None,
            'chart_history': [],
            'report_builder_sections': [...],
            'report_builder_charts': [],
            'ai_model': 'EchoEngine',
            'api_key': '',
            'ai_EchoEngine_mode': True,
            # ... all other keys
        }
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    def get_dataset(self) -> Optional[pd.DataFrame]:
        return st.session_state.get('dataset')

    def set_dataset(self, df: pd.DataFrame):
        st.session_state['dataset'] = df

    def get_chat_history(self) -> List[Dict]:
        return st.session_state.get('chat_history', [])

    def add_chat_message(self, role: str, content: Any):
        st.session_state['chat_history'].append({'role': role, 'content': content, 'timestamp': time.time()})

    # ... similar for other state variables
```

**UI modules then use:**

```python
from ui.state import StateManager
state = StateManager()
df = state.get_dataset()
state.add_chat_message('user', user_prompt)
```

**Deliverables:** All UI modules now use a central state manager. The app works identically.

---

### Stage 4: Decouple UI from Direct Service Calls – Use Dependency Injection

**Goal:** Remove hard‑coded imports of services from UI modules; instead, inject services into UI components (e.g., via constructors or factory functions). This makes UI components easier to test and swap out.

**Steps:**

1. Modify each UI module (tab) to accept its dependencies (services) as parameters (e.g., in a `__init__` method or as function arguments).
2. In `app.py` (or a central UI factory), instantiate the services and pass them to the tabs.
3. This can be done incrementally; start with the `AIService` and `DataService` and gradually apply to all tabs.
4. For components that are not classes (e.g., functions), we can use closures or global service instances that are set during app initialisation.

**Example:**

*Before (in ai_copilot.py):*

```python
from services.ai_service import AIService
ai_service = AIService()
```

*After:*

```python
# ui/tabs/ai_copilot.py
def render_ai_copilot_tab(ai_service, data_service, state_manager):
    # use the injected services
    ...
```

And in `app.py`:

```python
from services.ai_service import AIService
from services.data_service import DataService
from ui.tabs.ai_copilot import render_ai_copilot_tab
from ui.state import StateManager

state = StateManager()
ai_service = AIService(state)
data_service = DataService(state)

# In the tab rendering:
with tab2:
    render_ai_copilot_tab(ai_service, data_service, state)
```

This improves testability and makes the dependency graph explicit.

**Deliverables:** UI modules are now pure presentation layers; all dependencies are injected.

---

### Stage 5: Break Circular Dependency and Final Cleanup

**Goal:** Remove the circular import between `app.py` and `relationships_tab.py`.

**Solution:** The reset logic that was in `app.SessionStateManager` should be moved to a service, e.g., `DataService.reset_analysis()`. Then `relationships_tab` can call `data_service.reset_analysis()` without importing `app`.

**Steps:**

1. In `services/data_service.py`, add a method `reset_analysis()` that resets all relevant state (via the state manager).
2. Update `relationships_tab.py` to import and use `DataService` instead of `app`.
3. Remove the `SessionStateManager` class from `app.py` (if it only contained reset logic) and ensure all references are updated.
4. Similarly, identify any other cross‑imports and resolve them.

**Additional Cleanup:**

- Remove any remaining direct `st.session_state` references in the core/services layers (they should now use the state manager or receive parameters).
- Ensure all modules respect the layered architecture:
  - Core ↔ no UI dependencies.
  - Services ↔ may depend on Core and StateManager.
  - UI ↔ depends on Services and StateManager.

**Deliverables:** No circular dependencies. The architecture is clean.

---

### Stage 6: (Optional) Enhance with Testing and Documentation

**Goal:** Add unit tests for core services and state manager, and document the new architecture.

**Steps:**

1. Write unit tests for `core/ai/`, `core/data/`, and services using mock objects.
2. Add docstrings and type hints to all public interfaces.
3. Update the project README with the new architecture diagram and contribution guidelines.

---

## Conclusion

This staged refactoring plan provides a clear, low‑risk path to transform the current monolithic codebase into a modular, maintainable, and testable architecture. By following these steps, you will achieve:

- **Separation of concerns** – UI, business logic, and data management are isolated.
- **Improved testability** – core logic can be unit‑tested without Streamlit.
- **Easier collaboration** – teams can work on different layers independently.
- **Future‑proofing** – new features (e.g., REST API, desktop app) can reuse the core/services.

The final structure is both professional and “sexy”, with clear package boundaries and a modern service‑oriented design.