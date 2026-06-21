# Data Explorer Pro

**Professional Data Analysis Platform with AI Copilot**

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-FF4B4B)](https://streamlit.io/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000)](https://github.com/psf/black)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)](CONTRIBUTING.md)

**Data Explorer Pro** is a modern, modular data analysis workbench built on Streamlit and Plotly. It combines powerful data transformation tools, an AI‑powered assistant (Gemini, Claude, or local heuristics), and a professional reporting engine—all within a clean, intuitive interface.

Designed for data scientists, analysts, and business intelligence professionals, it enables you to:

- **Explore** datasets interactively with summary stats, distributions, and correlations.
- **Prepare** data via filters, joins, type conversions, and calculated columns.
- **Visualise** with 20+ chart types, fully configurable.
- **Get AI insights** via our Copilot (supports Google Gemini, Anthropic Claude, or local EchoEngine).
- **Build reports** with structured sections and embedded charts.
- **Export** professional HTML reports.

---

## Key Features

- **📊 Data Exploration** – instant overview of dataset health, missing values, duplicates, and key metrics.
- **🤖 AI Copilot** – natural‑language analysis with automated chart suggestions; works offline with EchoEngine.
- **📈 Chart Studio** – create histograms, scatter plots, bar/line charts, treemaps, bubble maps, KPIs, gauges, and more.
- **🧹 Data Preparation** – filter, remove duplicates, handle missing values, convert data types, and create formula‑based columns.
- **🔗 Relationship Modelling** – join multiple tables, define relationships, and generate SQL/Pandas/Polars code.
- **📄 Report Builder** – assemble sections, attach charts, and export to clean HTML reports.
- **🔌 Extensible** – modular architecture (Core → Services → UI) makes it easy to add new features or swap backends.

---

## Architecture

The project follows a clean **layered architecture**:

```
┌──────────────────────────────────────────────────────────┐
│                      UI Layer                           │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │
│  │ Explore │ │ Copilot │ │ Studio  │ │ Prep    │      │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘      │
│         │         │         │         │                 │
│         ▼         ▼         ▼         ▼                 │
│  ┌──────────────────────────────────────────────────┐  │
│  │            Services Layer                        │  │
│  │  DataService │ ChartService │ AIService │ Report │  │
│  └──────────────────────────────────────────────────┘  │
│                          │                             │
│                          ▼                             │
│  ┌──────────────────────────────────────────────────┐  │
│  │               Core Layer                         │  │
│  │  core/ai/  │  core/data/  │  core/charts/       │  │
│  └──────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

- **Core** – pure business logic, no UI dependencies.
- **Services** – orchestrate core components and provide clean interfaces to UI.
- **UI** – Streamlit‑specific rendering and user interaction.
- **Reporting** – HTML generation and template management.

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

1. **Load Data** – use the sidebar to upload a CSV/Excel file, load a sample dataset, or connect to an external data source.
2. **Explore** – view summary statistics, distributions, and correlations in the Explore tab.
3. **Clean & Prepare** – apply filters, handle missing values, and create new columns in the Data Preparation tab.
4. **Create Charts** – use Chart Studio to build custom visualisations.
5. **Ask AI** – switch to the AI Copilot tab to get automated analysis and chart suggestions.
6. **Build Reports** – use the Report Builder to compile sections and export an HTML report.

---

## Configuration

### AI Providers

- **EchoEngine** (default) – local heuristic analysis; works without an API key.
- **Google Gemini** – set your API key in the sidebar (requires `google-generativeai` package).
- **Anthropic Claude** – set your API key in the sidebar (requires `anthropic` package).

Keys are stored only in the browser session and are never transmitted to our servers.

### Environment Variables (Optional)

You can also set API keys via environment variables:

```bash
export GEMINI_API_KEY="your-key-here"
export ANTHROPIC_API_KEY="your-key-here"
```

---

## Contributing

We welcome contributions! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

### Development Setup

1. Fork the repository and clone your fork.
2. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt  # (if provided)
   ```
3. Install pre‑commit hooks (optional):
   ```bash
   pre-commit install
   ```
4. Make your changes, add tests, and ensure the code passes linting.
5. Submit a pull request.

---

## License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.

---

## Acknowledgements

- Built with [Streamlit](https://streamlit.io/) and [Plotly](https://plotly.com/).
- AI capabilities powered by [Google Gemini](https://ai.google.dev/) and [Anthropic Claude](https://www.anthropic.com/).
- Heuristic engine (EchoEngine) developed in‑house for offline insights.
- Icons and design inspired by modern data tools.

---

**Developed by Abdallah A Khames · [BODZZ](https://github.com/abdallah-bodzz) · 2026**