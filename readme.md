# Data Explorer Pro

**Professional Data Analysis Platform with AI Copilot**

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-FF4B4B)](https://streamlit.io/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000)](https://github.com/psf/black)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)](CONTRIBUTING.md)
[![GitHub Stars](https://img.shields.io/github/stars/abdallah-bodzz/data-explorer-pro?style=social)](https://github.com/abdallah-bodzz/data-explorer-pro)

---

![Data Explorer Pro Landing Page](assets\screenshots\landing.jpg)

---

## Overview

Data Explorer Pro is a modern, modular data analysis workbench built on Streamlit and Plotly. It combines powerful data transformation tools, an AI-powered assistant, and a professional reporting engine—all within a clean, intuitive interface.

Designed for data scientists, analysts, and business intelligence professionals, it enables you to:

- **Explore** datasets interactively with summary stats, distributions, and correlations
- **Prepare** data via filters, joins, type conversions, and calculated columns
- **Visualise** with 20+ chart types, fully configurable
- **Get AI insights** via Copilot (supports Google Gemini, Anthropic Claude, or local EchoEngine)
- **Build reports** with structured sections and embedded charts
- **Export** professional HTML reports

---

## Key Features

| Feature | Description |
|---------|-------------|
| **📊 Data Exploration** | Instant overview of dataset health, missing values, duplicates, and key metrics |
| **🤖 AI Copilot** | Natural-language analysis with automated chart suggestions; works offline with EchoEngine |
| **📈 Chart Studio** | Create histograms, scatter plots, bar/line charts, treemaps, bubble maps, KPIs, gauges, and more |
| **🧹 Data Preparation** | Filter, remove duplicates, handle missing values, convert data types, and create formula-based columns |
| **🔗 Relationship Modelling** | Join multiple tables, define relationships, and generate SQL/Pandas/Polars code |
| **📄 Report Builder** | Assemble sections, attach charts, and export to clean HTML reports |
| **🔌 Extensible Architecture** | Modular design (Core → Services → UI) makes it easy to add new features or swap backends |

---

## Architecture

The project follows a clean **layered architecture**:

```
┌─────────────────────────────────────────────────────────────────┐
│                        UI Layer                                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │
│  │ Explore  │ │ Copilot  │ │ Studio   │ │ Prep     │         │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘         │
│        │            │            │            │               │
│        ▼            ▼            ▼            ▼               │
│  ┌────────────────────────────────────────────────────────┐   │
│  │                   Services Layer                      │   │
│  │  DataService │ ChartService │ AIService │ ReportService │   │
│  └────────────────────────────────────────────────────────┘   │
│                              │                                │
│                              ▼                                │
│  ┌────────────────────────────────────────────────────────┐   │
│  │                    Core Layer                          │   │
│  │  core/ai/  │  core/data/  │  core/charts/  │ config   │   │
│  └────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

- **Core** – pure business logic, no UI dependencies
- **Services** – orchestrate core components and provide clean interfaces to the UI
- **UI** – Streamlit-specific rendering and user interaction
- **Reporting** – HTML generation and template management

For a detailed breakdown, see [docs/Roadmap to a Modular Architecture.md](docs/Roadmap%20to%20a%20Modular%20Architecture.md).

---

## Installation

### Prerequisites

- Python 3.10 or higher
- pip (or conda)

### Clone the Repository

```bash
git clone https://github.com/abdallah-bodzz/data-explorer-pro.git
cd data-explorer-pro
```

### Create and Activate a Virtual Environment (Recommended)

```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

For optional AI providers (Gemini/Claude), install the respective packages:

```bash
pip install google-generativeai anthropic
```

---

## Usage

Launch the app with:

```bash
streamlit run main.py
```

Your browser will open at `http://localhost:8501`.

### First Steps

1. **Load Data** – use the sidebar to upload a CSV/Excel file, load a sample dataset, or connect to an external data source
2. **Explore** – view summary statistics, distributions, and correlations in the Explore tab
3. **Clean & Prepare** – apply filters, handle missing values, and create new columns in the Data Preparation tab
4. **Create Charts** – use Chart Studio to build custom visualisations
5. **Ask AI** – switch to the AI Copilot tab to get automated analysis and chart suggestions
6. **Build Reports** – use the Report Builder to compile sections and export an HTML report

---

## Configuration

### AI Providers

- **EchoEngine** (default) – local heuristic analysis; works without an API key
- **Google Gemini** – set your API key in the sidebar (requires `google-generativeai` package)
- **Anthropic Claude** – set your API key in the sidebar (requires `anthropic` package)

Keys are stored only in the browser session and are never transmitted to our servers.

### Environment Variables (Optional)

You can also set API keys via environment variables:

```bash
export GEMINI_API_KEY="your-key-here"
export ANTHROPIC_API_KEY="your-key-here"
```

---

## Project Story

Data Explorer Pro started in mid-2025 as a question: *"What does it actually take to build a professional data tool?"*

It evolved through three major iterations:
1. **Tkinter desktop app** – functional but visually limited
2. **CustomTkinter modern UI** – better aesthetics, still desktop-bound
3. **Streamlit web application** – the current, mature version

Before the current refactored structure, there were **34 previous versions**. Each represented a different approach, a different architecture, a different way of solving the same problem. Some were prototypes, some were abandoned halfway, some were complete rewrites that I thought would be "the one."

The project has been through cycles of intense, full-time development and long breaks. It's a testament to persistence, learning, and the pursuit of craftsmanship.

**Why build at all?** Because building teaches you things that using never can. The value isn't just in the finished product—it's in the knowledge gained along the way.

Read the full story in [docs/project.md](docs/project.md).

---

## Development Roadmap

The project is being refactored incrementally toward a clean, service-oriented architecture. Progress so far:

| Stage | Description | Status |
|-------|-------------|--------|
| 1 | File Restructuring | ✅ Complete |
| 2 | Service Layer Extraction | ✅ Complete |
| 3 | Centralise Session State | 🔄 Planned |
| 4 | Dependency Injection | 🔄 Planned |
| 5 | Break Circular Dependencies | 🔄 Planned |
| 6 | Testing & Documentation | 🔄 Planned |

See [docs/Roadmap to a Modular Architecture.md](docs/Roadmap%20to%20a%20Modular%20Architecture.md) for full details.

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| **Frontend** | Streamlit (Python-based web framework) |
| **Visualisation** | Plotly (interactive charts) |
| **Data Manipulation** | Pandas, NumPy |
| **Statistical Analysis** | SciPy, StatsModels |
| **Machine Learning** | Scikit-learn |
| **AI Providers** | Google Gemini, Anthropic Claude, EchoEngine (local) |
| **Reporting** | Jinja2, HTML/CSS |
| **Code Quality** | Black, isort, flake8 |

---

## Project Structure

```
data_explorer_pro/
├── core/                    # Pure business logic
│   ├── ai/                  # AI providers and utilities
│   ├── data/                # Data models and operations
│   ├── charts/              # Chart templates
│   └── config.py            # Global configuration
├── services/                # Orchestration layer
│   ├── data_service.py
│   ├── chart_service.py
│   ├── ai_service.py
│   └── report_service.py
├── ui/                      # Streamlit interface
│   ├── app.py               # Main application
│   ├── state.py             # Session state management
│   ├── components/          # Reusable UI components
│   └── tabs/                # Each tab as a separate module
├── reporting/               # HTML export
├── utils/                   # Helpers
├── docs/                    # Documentation
├── assets/                  # Screenshots, images
├── archive/                 # Previous versions
├── charts/                  # Saved charts
├── main.py                  # Entry point
└── requirements.txt         # Dependencies
```

---

## Contributing

We welcome contributions! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:

- Code style (black, isort)
- Pull request process
- Issue reporting
- Development setup

---

## License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.

---

## Acknowledgements

- Built with [Streamlit](https://streamlit.io/) and [Plotly](https://plotly.com/)
- AI capabilities powered by [Google Gemini](https://ai.google.dev/) and [Anthropic Claude](https://www.anthropic.com/)
- Heuristic engine (EchoEngine) developed in-house for offline insights
- Icons and design inspired by modern data tools
- The open-source Python community for building the incredible libraries this project depends on

---

## Contact & Support

- **GitHub Issues**: [Report a bug or request a feature](https://github.com/abdallah-bodzz/data-explorer-pro/issues)
- **Discussion**: Open an issue for questions or ideas
- **Repository**: [github.com/abdallah-bodzz/data-explorer-pro](https://github.com/abdallah-bodzz/data-explorer-pro)

---

**Developed by Abdallah A Khames · [BODZZ](https://github.com/abdallah-bodzz) · 2026**

*"The value isn't just in the finished product—it's in the knowledge gained along the way."*