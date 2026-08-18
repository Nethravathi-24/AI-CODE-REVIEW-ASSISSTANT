# AI Code Review Assistant

> A production-ready modular static-analysis and AI-powered code review engine for Python source code that validates inputs, detects languages, preprocesses code, runs deterministic static analyzers and AI reasoning chains, fuses findings, calculates 7-dimension quality scores, generates remediations and tests, and exports structured reports.

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-PRODUCTION%20READY-green.svg)](#current-project-status)
[![Tests](https://img.shields.io/badge/tests-148%20passed-brightgreen.svg)](#running-tests)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 1. Project Overview

The **AI Code Review Assistant** provides fast, explainable, and trustworthy code analysis. It bridges the gap between raw linters and higher-level code reviews by orchestrating multiple static analysis tools and optional AI reasoning chains into a unified, typed domain model with deterministic 7-dimension quality scoring and actionable fix recommendations.

---

## 2. Complete End-to-End Architecture & Flow

The review pipeline follows a strict linear execution sequence with early-stop validation gates, isolated analyzer error handling, and graceful AI fallback:

```text
Input Code / Bytes / File Upload
  │
  ▼
1. Validation (input_handling/validator.py)
   ├─► INVALID ──► STOP immediately (returns failure PipelineResult)
   └─► VALID ──► Continue
  │
  ▼
2. Language Detection (input_handling/language_detector.py)
   ├─► Signature matching & extension heuristics (.py, .pyw)
   └─► Manual language override support
  │
  ▼
3. Preprocessing (input_handling/preprocessor.py)
   ├─► Line ending normalization (CRLF/CR ➔ LF) and line offset mapping
   └─► AST syntax parsing check (captures structured SYNTAX_ERROR issue if unparseable)
  │
  ▼
4. Static Analysis Execution (analyzers/)
   ├─► AST Structural Analyzer (bare excepts, unclosed files, deep nesting, param limits)
   ├─► Pyflakes Analyzer (unused imports, undefined names, unused variables)
   ├─► Bandit Security Analyzer (eval/exec, hardcoded secrets, unsafe calls)
   ├─► Radon Complexity Analyzer (cyclomatic complexity CC > 10)
   └─► Style Analyzer (PEP 8 line length > 79, formatting issues via pycodestyle)
   │  [Error Isolation: Failing analyzers log errors & continue remaining analyzers]
  │
  ▼
5. AI Review Engine (ai/) [Optional / Graceful Degradation]
   ├─► LLM reasoning for logic flaws, runtime risks, edge cases, and maintainability
   └─► Automatically falls back to static-only mode if OPENAI_API_KEY is missing
  │
  ▼
6. Result Fusion Engine (fusion/)
   ├─► Normalizes and deduplicates static and AI findings
   └─► Boosts confidence when independent static and AI sources corroborate
  │
  ▼
7. Severity Engine (core/severity.py)
   └─► Computes final deterministic severity levels (CRITICAL, HIGH, MEDIUM, LOW, INFORMATIONAL)
  │
  ▼
8. 7-Dimension Quality Scoring (core/scoring.py)
   └─► Deducts points across Correctness (25%), Security (25%), Maintainability (15%), Readability (10%), Performance (10%), Best Practices (10%), Testability (5%)
  │
  ▼
9. Remediation & Test Generation (remediation/)
   ├─► Generates suggested fixes, unified diffs, and AST syntax validation
   └─► Generates executable pytest regression test cases
  │
  ▼
10. Report Building & Streamlit UI (report/ & app/main.py)
    ├─► Interactive Streamlit dashboard with quality gauges, filters, and cards
    └─► Report Exporters for Markdown, JSON, and PDF
```

---

## 3. Technology Stack

- **Core Runtime**: Python 3.10+ (compatible with Python 3.10 – 3.14)
- **Data Modeling & Schemas**: Pydantic v2
- **Configuration Management**: Pydantic-Settings
- **Static Analysis Tools**:
  - Python Standard Library `ast` (AST structural analyzer & syntax parser)
  - `pyflakes` (logical errors, undefined names, unused imports)
  - `bandit` (security vulnerability and unsafe pattern scanner)
  - `radon` (cyclomatic complexity metrics)
  - `pycodestyle` (PEP 8 style and readability linter)
- **AI Engine**: LangChain & OpenAI API (`gpt-4o`, `gpt-4o-mini`)
- **User Interface**: Streamlit web application (`app/main.py`)
- **Testing**: `pytest`, `pytest-mock`

---

## 4. Repository Structure

```text
AI-CODE-REVIEW-ASSISSTANT/
├── ai/                      # AI LLM reasoning engine & fallback handlers
│   ├── mock_reviewer.py     # Deterministic mock reviewer for offline tests
│   ├── models.py            # Structured LLM reasoning schemas
│   ├── openai_reviewer.py   # OpenAI & LangChain integration
│   ├── prompts.py           # Review prompts and system instructions
│   └── reviewer.py          # AI reviewer factory function
├── analyzers/               # Deterministic static analyzer wrappers
│   ├── ast_analyzer.py      # Custom AST structural walker
│   ├── bandit_analyzer.py   # Bandit security analyzer wrapper
│   ├── base.py              # BaseAnalyzer abstract base class
│   ├── pyflakes_analyzer.py # Pyflakes linter wrapper
│   ├── radon_analyzer.py    # Radon cyclomatic complexity analyzer
│   └── style_analyzer.py    # PEP 8 pycodestyle wrapper
├── app/                     # Streamlit web application (Canonical UI)
│   ├── main.py              # Official Streamlit entry point
│   └── ui/                  # UI components and view layouts
│       └── components.py    # Streamlit dashboard & card components
├── config/                  # Configuration settings facade
├── core/                    # Core domain layer
│   ├── interfaces.py        # Shared protocol contracts
│   ├── issue_model.py       # Pydantic domain models (Issue, ReviewResult, PipelineResult)
│   ├── scoring.py           # 7-Dimension Quality Scoring engine
│   └── severity.py          # Deterministic severity calculation engine
├── docs/                    # Architecture and developer documentation
├── fusion/                  # Finding reconciliation & deduplication engine
│   ├── deduplication.py     # Fuzzy line and category deduplication rules
│   ├── fusion_service.py    # Merges static and AI findings into canonical issues
│   └── models.py            # Fusion configuration models
├── input_handling/          # Input ingestion, validation, and preprocessing
│   ├── language_detector.py # Language detection heuristics & overrides
│   ├── models.py            # Input handling data schemas
│   ├── preprocessor.py      # CRLF normalization & AST syntax checking
│   └── validator.py         # Boundary, size, encoding, and file-type validation
├── orchestrator/            # Pipeline coordination layer
│   └── pipeline.py          # CodeReviewPipeline, run_pipeline, review_code
├── remediation/             # Fix and test generation layer
│   ├── fix_generator.py     # Automated fix & diff generator
│   ├── test_generator.py    # Automated pytest unit test generator
│   └── validator.py         # Safe AST syntax check validator
├── report/                  # Structured report export engine
│   ├── json_report.py       # Pretty JSON exporter
│   ├── markdown_report.py   # Structured Markdown exporter
│   ├── pdf_report.py        # PDF exporter with safe fallback
│   └── report_builder.py    # ReportBuilder facade
├── services/                # Application support services
├── tests/                   # Comprehensive unit and integration test suite
├── .env.example             # Example environment variable file
├── requirements.txt         # Project dependencies
└── README.md                # Project documentation
```

---

## 5. Installation & Setup

### Prerequisites
* **Python**: Version 3.10 or higher
* **Git**: Version 2.x+

### Step-by-Step Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd AI-CODE-REVIEW-ASSISSTANT
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # On macOS/Linux:
   python3 -m venv venv
   source venv/bin/activate

   # On Windows (PowerShell):
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 6. Environment & Configuration

Copy `.env.example` to create your local `.env`:
```bash
cp .env.example .env
```

### Supported Configuration Variables

| Variable | Default Value | Description |
|---|---|---|
| `MAX_FILE_SIZE_KB` | `200` | Maximum allowable file size in kilobytes |
| `MAX_CODE_CHARS` | `50000` | Maximum character count for submitted snippets |
| `ENVIRONMENT` | `development` | Runtime environment (`development`, `production`) |
| `OPENAI_API_KEY` | `""` | Optional OpenAI API Key for AI review mode |
| `OPENAI_MODEL` | `gpt-4o` | Model name for OpenAI reviewer |

> **Static-Only Mode**: If `OPENAI_API_KEY` is missing or invalid, the application automatically operates in static-only mode without crashing or failing.

---

## 7. Running the Web Application

Launch the Streamlit web interface:

```bash
python -m streamlit run app/main.py
```

Open your browser to `http://localhost:8501`.

Features available in the web UI:
- Code snippet text area & `.py` file drag-and-drop uploader.
- Toggle between AI Reasoning and Static-Only mode.
- OpenAI connection status indicator.
- 7-Dimension Score Dashboard & Severity Counter Summary.
- Interactive multi-select category and severity filters.
- Expandable finding cards with why-it-matters explanations, unified diff fixes, and generated pytest cases.
- One-click report downloads in Markdown, JSON, and PDF formats.

---

## 8. Programmatic Pipeline Execution

```python
from orchestrator import run_pipeline

code_snippet = """
def execute_payload(user_input: str):
    try:
        return eval(user_input)
    except:
        return None
"""

result = run_pipeline(code_snippet, filename="sample.py")

if result.success:
    review = result.review_result
    print(f"Overall Score: {review.score.overall_score}/100 ({review.score.label})")
    print(f"Total Issues:  {review.summary.total_issues}")
    for issue in review.issues:
        print(f" - [{issue.severity.value.upper()}] Line {issue.line_start}: {issue.description}")
```

---

## 9. Running Tests

Run the full test suite with `pytest`:

```bash
pytest -v
```

All **148 tests** are passing.

---

## 10. Security Boundaries & Critical Rules

- **Zero Code Execution Guarantee**: Submitted user code, generated fixes, and generated test cases are treated strictly as plain text data. The system **NEVER** executes submitted code via `exec()`, `eval()`, or subprocess invocation.
- **AST Syntax Checking**: Syntax validation is performed purely via `ast.parse()`.
- **Secret Protection**: API keys and environment credentials are loaded from environment variables and `.env` files (gitignored). API keys are never exposed in UI outputs or log logs.
