# AI Code Review Assistant

> A production-ready multi-language static-analysis and AI-powered code review engine for Python, JavaScript, TypeScript, and Java source code that validates inputs, detects languages, preprocesses code, runs language-specific static analyzers and AI reasoning chains, fuses findings, calculates 7-dimension quality scores, generates remediations and tests, and exports structured reports.

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-PRODUCTION%20READY-green.svg)](#current-project-status)
[![Multi-Language](https://img.shields.io/badge/languages-Python%20%7C%20JS%20%7C%20TS%20%7C%20Java-blue.svg)](#language-support-matrix)
[![Tests](https://img.shields.io/badge/tests-157%20passed-brightgreen.svg)](#running-tests)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 1. Project Overview

The **AI Code Review Assistant** provides fast, explainable, and trustworthy code analysis across multiple programming languages. It bridges the gap between raw linters and higher-level code reviews by orchestrating language-specific static analysis tools and optional AI reasoning chains into a unified, typed domain model with deterministic 7-dimension quality scoring and actionable fix recommendations.

---

## 2. Language Support Matrix

| Language | Extensions | Static Analyzers | AI Reasoning | Fix & Diff | Unit Test Generation | Status |
|---|---|---|---|---|---|---|
| **Python** | `.py`, `.pyw` | AST Structural, Pyflakes, Bandit, Radon, Style | Full LLM Reasoning | Python Fix + Unified Diff | Pytest Case | **Full (Static + AI)** |
| **JavaScript** | `.js`, `.jsx` | JS Pattern Analyzer (`eval`, `var`, `==`, `console.log`, XSS) | Full LLM Reasoning | JS Fix + Unified Diff | Jest / Mocha Case | **Full (Hybrid Static + AI)** |
| **TypeScript** | `.ts`, `.tsx` | TS Pattern Analyzer (`any` type, `eval`, `var`, `==`, XSS) | Full LLM Reasoning | TS Fix + Unified Diff | Jest / Vitest Case | **Full (Hybrid Static + AI)** |
| **Java** | `.java` | Java Pattern Analyzer (`Runtime.exec`, string `==`, `System.out`, catch) | Full LLM Reasoning | Java Fix + Unified Diff | JUnit 5 Case | **Full (Hybrid Static + AI)** |
| **Unsupported** | Other | Static analysis skipped (PRD Part 5.3) | AI Reasoning (Labeled low confidence) | Plain fix description | Generic test outline | **AI Fallback Only** |

---

## 3. End-to-End Pipeline Architecture

```text
Source Code (Python, JS, TS, Java)
  │
  ▼
1. Validation (input_handling/validator.py)
   ├─► Checks: Null/empty, 200 KB limit, 50,000 chars, null-bytes, UTF-8/BOM, extensions (.py, .js, .ts, .java)
   └─► INVALID ──► STOP immediately (returns failure PipelineResult)
  │
  ▼
2. Language Detection & Manual Override (input_handling/language_detector.py)
   ├─► Signature heuristics, regex weights, and extension mapping
   └─► Manual language override support
  │
  ▼
3. Preprocessing (input_handling/preprocessor.py)
   ├─► Line ending normalization (CRLF/CR ➔ LF) and line character offset mapping
   └─► Language-aware syntax checking (Python `ast.parse` for Python; delimiter validation for JS/TS/Java)
  │
  ▼
4. Language-Specific Static Analyzers (analyzers/)
   ├─► Python: AST Structural, Pyflakes, Bandit, Radon, Style Analyzers
   ├─► JavaScript / TypeScript: JS/TS Static Pattern Analyzer
   └─► Java: Java Static Pattern Analyzer
  │
  ▼
5. AI Review Engine (ai/) [Optional / Graceful Fallback]
   ├─► LLM reasoning for logic bugs, runtime risks, edge cases, maintainability
   └─► Automatically falls back to static-only mode if OPENAI_API_KEY is missing
  │
  ▼
6. Result Fusion Engine (fusion/)
   ├─► Normalizes and deduplicates static and AI findings into unified Issue objects
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
   ├─► FixGenerator: language-specific fixes, unified diffs, and static syntax check
   └─► TestGenerator: language-specific test cases (Pytest, Jest, JUnit)
  │
  ▼
10. Report Building & Streamlit UI (report/ & app/main.py)
    ├─► Interactive Streamlit dashboard with quality gauges, filters, and cards
    └─► Report Exporters for Markdown, JSON, and PDF
```

---

## 4. Technology Stack

- **Core Runtime**: Python 3.10+ (compatible with Python 3.10 – 3.14)
- **Data Modeling & Schemas**: Pydantic v2
- **Configuration Management**: Pydantic-Settings
- **Static Analysis Tools**:
  - Python Standard Library `ast` (AST structural analyzer & syntax parser)
  - `pyflakes` (logical errors, undefined names, unused imports)
  - `bandit` (security vulnerability and unsafe pattern scanner)
  - `radon` (cyclomatic complexity metrics)
  - `pycodestyle` (PEP 8 style and readability linter)
  - `JSAnalyzer` (custom JavaScript/TypeScript static pattern analyzer)
  - `JavaAnalyzer` (custom Java static pattern analyzer)
- **AI Engine**: LangChain & OpenAI API (`gpt-4o`, `gpt-4o-mini`)
- **User Interface**: Streamlit web application (`app/main.py`)
- **Testing**: `pytest`, `pytest-mock`

---

## 5. Repository Structure

```text
AI-CODE-REVIEW-ASSISSTANT/
├── ai/                      # AI LLM reasoning engine & fallback handlers
│   ├── mock_reviewer.py     # Deterministic mock reviewer for offline tests
│   ├── models.py            # Structured LLM reasoning schemas
│   ├── openai_reviewer.py   # OpenAI & LangChain integration
│   ├── prompts.py           # Multi-language review prompts and instructions
│   └── reviewer.py          # AI reviewer factory function
├── analyzers/               # Language-specific static analyzer wrappers
│   ├── ast_analyzer.py      # Custom AST structural walker (Python)
│   ├── bandit_analyzer.py   # Bandit security analyzer wrapper (Python)
│   ├── base.py              # BaseAnalyzer abstract base class
│   ├── java_analyzer.py     # Java static pattern analyzer
│   ├── js_analyzer.py       # JavaScript / TypeScript static pattern analyzer
│   ├── pyflakes_analyzer.py # Pyflakes linter wrapper (Python)
│   ├── radon_analyzer.py    # Radon cyclomatic complexity analyzer (Python)
│   └── style_analyzer.py    # PEP 8 pycodestyle wrapper (Python)
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
├── input_handling/          # Multi-language input validation & preprocessing
│   ├── language_detector.py # Language detection heuristics & overrides
│   ├── models.py            # Input handling data schemas
│   ├── preprocessor.py      # CRLF normalization & language-aware syntax checking
│   └── validator.py         # Boundary, size, encoding, and multi-language extension validation
├── orchestrator/            # Pipeline coordination layer
│   └── pipeline.py          # CodeReviewPipeline, run_pipeline, review_code
├── remediation/             # Fix and test generation layer
│   ├── fix_generator.py     # Multi-language fix & diff generator
│   ├── test_generator.py    # Multi-language test generator (Pytest, Jest, JUnit)
│   └── validator.py         # Multi-language safe static syntax check validator
├── report/                  # Structured report export engine
├── services/                # Application support services
├── tests/                   # Comprehensive unit and integration test suite
│   ├── fixtures/            # Benchmark test fixtures for Python, JS, TS, Java
│   └── unit/                # Multi-language unit and integration tests
├── .env.example             # Example environment variable file
├── requirements.txt         # Project dependencies
└── README.md                # Project documentation
```

---

## 6. Installation & Setup

```bash
git clone <repository-url>
cd AI-CODE-REVIEW-ASSISSTANT
python -m venv venv
.\venv\Scripts\Activate.ps1   # On Windows
pip install -r requirements.txt
```

---

## 7. Running the Web Application

Launch the Streamlit web interface:

```bash
python -m streamlit run app/main.py
```

Open your browser to `http://localhost:8501`.

Features available in the multi-language UI:
- **Code Upload**: Accepts `.py`, `.pyw`, `.js`, `.jsx`, `.ts`, `.tsx`, `.java`, and `.txt` files.
- **Code Editor**: Paste source code for any language.
- **Language Detection & Override**: Auto-detects language and allows manual override selection (Python, JavaScript, TypeScript, Java, Unknown).
- **Quality Gauges & Filters**: 7-dimension score breakdown, severity cards, category/severity multi-select filters.
- **Exporting**: One-click downloads in Markdown, JSON, and PDF formats.

---

## 8. Running Tests

Run the complete test suite with `pytest`:

```bash
pytest -q
```

All **157 tests** are passing.

---

## 9. Security Boundaries & Safety Rules

- **Zero Code Execution Guarantee**: Submitted user code, generated fixes, and generated test cases are treated strictly as plain text data. The system **NEVER** executes code via `eval()`, `exec()`, or subprocess.
- **Static Syntax Checking**: Python code is checked via `ast.parse()`; non-Python code is checked via static delimiter analysis.
- **Secret Protection**: API keys are loaded from environment variables and `.env` files (gitignored). API keys are never exposed in UI outputs or logs.
