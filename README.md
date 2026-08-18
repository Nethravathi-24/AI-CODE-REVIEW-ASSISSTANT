# AI Code Review Assistant

> A modular static-analysis and code review engine for Python source code that validates inputs, detects languages, preprocesses code, runs deterministic static analyzers, calculates severity deterministically, and produces structured review results.

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-Milestone%202%20COMPLETE-green.svg)](#current-project-status)
[![Tests](https://img.shields.io/badge/tests-83%20passed-brightgreen.svg)](#running-tests)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 1. Project Overview

The **AI Code Review Assistant** provides fast, explainable, and trustworthy code analysis. It bridges the gap between raw linters and higher-level code reviews by orchestrating multiple static analysis tools into a unified, typed domain model with deterministic severity calculation and quality scoring.

### Current Milestone 2 Focus: Static Analysis Pipeline
The current implementation completes **Milestone 2 (Static-Analysis Pipeline & Orchestration)**. It provides a complete, deterministic Python static review pipeline that operates locally with zero external network dependencies or API keys.

---

## 2. Implemented Milestone 2 Pipeline

The static review pipeline follows a strict linear execution sequence with early-stop validation gates and isolated analyzer error handling:

```text
Input (Code String / Bytes / File)
  │
  ▼
1. Validation (input_handling/validator.py)
   ├─► INVALID ──► STOP immediately (no analyzers run; returns failure PipelineResult)
   └─► VALID ──► Continue
  │
  ▼
2. Language Detection (input_handling/language_detector.py)
   ├─► Heuristic keyword pattern signatures & file extension detection (.py, .pyw)
   └─► Manual language override support
  │
  ▼
3. Preprocessing (input_handling/preprocessor.py)
   ├─► Line ending normalization (CRLF/CR ➔ LF) and line offset mapping
   └─► AST syntax parsing check (captures structured SYNTAX_ERROR issue if unparseable)
  │
  ▼
4. Static Analyzers Execution (analyzers/)
   ├─► AST Structural Analyzer (bare excepts, unclosed files, deep nesting, param limits)
   ├─► Pyflakes Analyzer (unused imports, undefined names, unused variables)
   ├─► Bandit Security Analyzer (eval/exec, hardcoded secrets, unsafe calls)
   ├─► Radon Complexity Analyzer (cyclomatic complexity CC > 10)
   └─► Style Analyzer (PEP 8 line length > 79, formatting issues via pycodestyle)
   │  [Error Isolation: Failing analyzers log errors & continue remaining analyzers]
  │
  ▼
5. Issue Collection
   └─► Combines findings from all successfully executed analyzers into a unified List[Issue]
  │
  ▼
6. Severity Processing (core/severity.py)
   └─► Applies deterministic calculate_severity() mapping to all collected issues
  │
  ▼
7. Result Assembly
   ├─► ReviewResult (issues, CodeQualityScore, ReviewSummary, language, submitted_code)
   └─► PipelineResult (success, review_result, errors, warnings, is_partial_analysis, execution_time)
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
- **Testing**: `pytest`, `pytest-mock`

---

## 4. Repository Structure

```text
AI-CODE-REVIEW-ASSISSTANT/
├── analyzers/               # Deterministic static analyzer wrappers
│   ├── ast_analyzer.py      # Custom AST structural walker (bare except, leaks, nesting)
│   ├── bandit_analyzer.py   # Bandit security analyzer wrapper
│   ├── base.py              # BaseAnalyzer abstract base class
│   ├── pyflakes_analyzer.py # Pyflakes linter wrapper
│   ├── radon_analyzer.py    # Radon cyclomatic complexity analyzer wrapper
│   └── style_analyzer.py    # PEP 8 pycodestyle wrapper
├── config/                  # Configuration settings facade
│   └── settings.py          # Settings instance
├── core/                    # Core domain layer (independent of UI and external services)
│   ├── interfaces.py        # Shared protocol contracts (StaticAnalyzerProtocol, etc.)
│   ├── issue_model.py       # Pydantic domain models (Issue, ReviewResult, PipelineResult)
│   └── severity.py          # Deterministic severity calculation engine
├── docs/                    # Architecture and developer workflow documentation
│   ├── ARCHITECTURE.md      # Detailed system architecture and data contracts
│   ├── MILESTONE_2_TASKS.md # Milestone 2 task and issue breakdown
│   └── TEAM_WORKFLOW.md     # Team collaboration and contribution workflow
├── input_handling/          # Input ingestion, validation, and preprocessing
│   ├── language_detector.py # Language detection heuristics & overrides
│   ├── models.py            # Input handling data schemas (ValidationResult, PreprocessedCode)
│   ├── preprocessor.py      # CRLF normalization & AST syntax checking
│   └── validator.py         # Boundary, size, encoding, and file-type validation
├── orchestrator/            # Pipeline coordination layer
│   ├── pipeline.py          # CodeReviewPipeline, run_pipeline, review_code
│   └── __init__.py          # Public entry points
├── services/                # Application support services
│   └── config_service.py    # Pydantic-Settings environment variable loader
├── tests/                   # Test suite
│   ├── integration/         # End-to-end static pipeline integration tests
│   └── unit/                # Unit tests for config, contracts, issues, severity, analyzers, input
├── .env.example             # Example environment variable file
├── requirements.txt         # Project dependencies
└── README.md                # This documentation file
```

---

## 5. Installation & Setup

### Prerequisites
* **Python**: Version 3.10 or higher
* **Git**: Version 2.x+
* **Package Manager**: `pip` or `uv`

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

   # On Windows (Command Prompt):
   .\venv\Scripts\activate.bat
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

   *Alternatively, if using `uv`:*
   ```bash
   uv pip install -r requirements.txt
   ```

---

## 6. Environment & Configuration

Configuration is managed centrally via `pydantic-settings` in [`services/config_service.py`](services/config_service.py).

### Environment File Setup
Copy `.env.example` to create your local `.env`:
```bash
# On Linux/macOS:
cp .env.example .env

# On Windows:
copy .env.example .env
```

### Supported Configuration Variables

| Variable | Default Value | Description |
|---|---|---|
| `MAX_FILE_SIZE_KB` | `200` | Maximum allowable file size in kilobytes |
| `MAX_CODE_CHARS` | `50000` | Maximum character count for submitted snippets |
| `ENVIRONMENT` | `development` | Runtime environment (`development`, `staging`, `production`) |
| `OPENAI_API_KEY` | `""` | *(Optional — not required for Milestone 2 static analysis)* |
| `OPENAI_MODEL` | `gpt-4o-mini` | *(Optional — for future AI milestones)* |
| `AI_TEMPERATURE` | `0.2` | *(Optional — for future AI milestones)* |

> **Note**: No API keys or external services are required to run the Milestone 2 static review pipeline. The pipeline executes 100% locally and offline.

---

## 7. Running the Static Review Pipeline

You can invoke the pipeline programmatically in Python using either `run_pipeline()` (for full execution metadata) or `review_code()` (for direct review results):

### Example 1: Full Pipeline Execution (`run_pipeline`)

```python
from orchestrator import run_pipeline

code_snippet = """
import sys

def execute_payload(user_input: str):
    try:
        return eval(user_input)
    except:
        return None
"""

# Run the complete static pipeline
result = run_pipeline(code_snippet, filename="sample.py")

# Check execution status
if result.success:
    review = result.review_result
    print(f"Language Detected: {review.language}")
    print(f"Quality Score:     {review.score.overall_score}/100 ({review.score.label})")
    print(f"Total Issues:      {review.summary.total_issues}")
    print(f"Execution Time:    {result.execution_time_seconds}s\n")

    for idx, issue in enumerate(review.issues, 1):
        print(f"[{idx}] {issue.severity.value.upper()} | {issue.category.value} (Tool: {issue.detecting_tool})")
        print(f"    Line {issue.line_start}: {issue.description}")
        print(f"    Why it matters: {issue.why_it_matters}\n")
else:
    print("Validation failed:")
    for err in result.errors:
        print(f"  - [{err.stage}] {err.message}")
```

### Example 2: Direct Review Result (`review_code`)

```python
from orchestrator import review_code

review = review_code("def add(a, b):\n    return a + b\n")
print(f"Score: {review.score.overall_score} ({review.score.label})")
print(f"Issues: {len(review.issues)}")
```

---

## 8. Running Tests

Run the complete test suite using `pytest`:

```bash
# Standard pytest execution
pytest -v

# Or using uv:
uv run --with-requirements requirements.txt pytest -v
```

### Running Specific Test Modules

```bash
# Run unit tests only
pytest tests/unit/ -v

# Run static analyzers unit tests
pytest tests/unit/test_analyzers.py -v

# Run input handling unit tests
pytest tests/unit/test_input_handling.py -v

# Run end-to-end integration tests
pytest tests/integration/test_static_pipeline.py -v
```

---

## 9. Current Project Status

- **Milestone 1 — Core Schemas & Contracts**: **COMPLETE**
  - Typed Pydantic v2 schemas (`Issue`, `Fix`, `GeneratedTest`, `ReviewResult`, `PipelineResult`)
  - Protocol contracts (`StaticAnalyzerProtocol`, `AIReviewerProtocol`, `FusionServiceProtocol`, `ReportBuilderProtocol`)
  - Deterministic severity engine (`core/severity.py`)
  - Centralized configuration service (`services/config_service.py`)

- **Milestone 2 — Static Analysis Pipeline & Orchestration**: **COMPLETE**
  - Input validation, boundary checks, and binary safety (`input_handling/validator.py`)
  - Python language detection and signature matching (`input_handling/language_detector.py`)
  - Code preprocessing, CRLF normalization, and syntax checking (`input_handling/preprocessor.py`)
  - 5 deterministic static analyzers (`ast`, `pyflakes`, `bandit`, `radon`, `style`)
  - Orchestrator pipeline integration with per-analyzer error isolation (`orchestrator/pipeline.py`)
  - Comprehensive unit and integration test suite (**83 passing tests**)

- **Milestone 3+ — AI Reasoning, Fusion, Fix/Test Remediation, & UI**: *PLANNED (Future Work)*
  - LLM detection and explanation chains (Milestone 3)
  - Finding fusion & deduplication engine (Milestone 4)
  - Validated fix and test generation (Milestone 5)
  - 7-dimension scoring breakdown and report exporters (Milestone 6)
  - Benchmark evaluation suite (Milestone 7)
  - Streamlit dashboard UI (Milestone 8)
