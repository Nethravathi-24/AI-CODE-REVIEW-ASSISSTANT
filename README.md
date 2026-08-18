# AI Code Review Assistant

> A hybrid static-analysis and LLM-reasoning web application that reviews source code, classifies and explains issues, proposes and validates fixes, generates tests, and produces a scored review report.

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-Milestone%201%20COMPLETE-green.svg)](#current-project-status)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 1. Project Purpose

The **AI Code Review Assistant** provides fast, explainable, and trustworthy code reviews for developers (students, junior engineers, and senior reviewers). It bridges the gap between traditional linters (which catch known patterns deterministically but lack contextual understanding) and LLMs (which understand developer intent and explain issues well but can hallucinate or produce unstructured results).

---

## 2. Problem Statement

1. **Manual Code Reviews are Slow**: Developers bottleneck on senior engineering availability.
2. **Static Linters are Shallow**: Tools like `pyflakes` or `bandit` output raw rule codes (e.g. `E501`) without plain-language explanations or fix suggestions.
3. **Pure LLM Code Reviews are Unreliable**: Pasting code into generic chat LLMs can produce hallucinated findings, inconsistent severities, and unvalidated code fixes.
4. **Fixes & Tests are Unverified**: Most AI tools suggest code edits without validating whether the new code compiles or resolves the underlying issue.

---

## 3. Key MVP Capabilities

- **Hybrid Detection**: Merges deterministic static analysis (`ast`, `pyflakes`, `bandit`, `radon`, `pycodestyle`) with AI reasoning (OpenAI via LangChain).
- **Typed Issue Model**: Uniform JSON/Pydantic schema (`Issue`) for all findings across static and AI layers.
- **Deterministic Severity & Scoring**: Categorical lookup rules for severities; 7-dimension code quality scoring math (Correctness 25%, Security 25%, Maintainability 15%, Readability 10%, Performance 10%, Best Practices 10%, Testability 5%).
- **Result Fusion & Deduplication**: Reconciliation engine that matches line ranges and categories, ensuring single deduplicated findings.
- **Validation-First Remediation**: AI-generated code fixes and `pytest` test cases are validated via `ast.parse` and static re-scanning before UI display.
- **Privacy & Security**: Zero code execution of user snippets; API keys isolated via environment variables.

---

## 4. High-Level Architecture

```
┌────────────────────────────────────────────────────────────┐
│                      Streamlit UI Layer                     │
└───────────────────────────┬────────────────────────────────┘
                             │
                    ┌────────▼─────────┐
                    │   Orchestrator   │
                    └────────┬─────────┘
        ┌────────────────────┼─────────────────────┐
        ▼                    ▼                      ▼
┌───────────────┐   ┌─────────────────┐   ┌──────────────────┐
│ Input Handling │   │ Static Analysis │   │     AI Layer     │
│ & Validation  │   │ Linters & AST   │   │ LangChain Chains │
└───────────────┘   └─────────────────┘   └──────────────────┘
        │                    │                      │
        └────────────────────┴──────────┬───────────┘
                                         ▼
                             ┌──────────────────────┐
                             │    Result Fusion     │
                             └──────────┬───────────┘
                                        ▼
                             ┌──────────────────────┐
                             │ Remediation & Score  │
                             └──────────┬───────────┘
                                        ▼
                                 ReviewResult UI
```

---

## 5. Technology Stack

- **Core Language**: Python 3.10+
- **Data Modeling & Settings**: Pydantic v2, Pydantic-Settings
- **AI Orchestration**: LangChain, LangChain-OpenAI
- **Static Analyzers**: Python stdlib `ast`, `pyflakes`, `bandit`, `radon`, `pycodestyle`
- **User Interface**: Streamlit
- **Testing & Quality**: pytest, pytest-mock

---

## 6. Project Structure

```
ai_code_review_assistant/
├── app/                  # Streamlit UI layer (components, pages, state)
├── core/                 # Core domain models, interfaces, severity, & scoring
├── orchestrator/         # Pipeline orchestration controller
├── input_handling/       # Input validation, language detection, & preprocessing
├── analyzers/            # Static analysis tool wrappers
├── ai/                   # LangChain wrappers, clients, and chains
├── prompts/              # Versioned prompt templates
├── fusion/               # Result fusion, deduplication, & confidence rules
├── remediation/          # Fix & test syntax validation
├── report/               # Report building & export formatting (Markdown/JSON)
├── services/             # Configuration & environment services
├── config/               # Application constants & settings facade
├── utils/                # Diffing & file utilities
├── docs/                 # Architecture & workflow documentation
└── tests/                # Unit, integration, & evaluation tests
    └── unit/
```

---

## 7. Setup & Installation Instructions

### Prerequisites
- Python 3.10 or higher
- Git

### Installation
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd ai-code-review-assistant
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## 8. Environment Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Configure your environment variables in `.env`:
   ```ini
   OPENAI_API_KEY=your_actual_openai_api_key_here
   OPENAI_MODEL=gpt-4o-mini
   AI_TEMPERATURE=0.2
   MAX_FILE_SIZE_KB=200
   ENVIRONMENT=development
   ```

*Note: The application foundation runs cleanly without an `OPENAI_API_KEY` set (static analysis mode).*

---

## 9. How to Run Tests

Run the complete unit test suite using `pytest`:

```bash
pytest -v
```

To run with coverage or filter specific test files:
```bash
pytest tests/unit/test_issue_model.py -v
```

---

## 10. How to Run the Application (Post-Implementation)

Once the Streamlit UI layer is implemented in Milestone 2+:

```bash
streamlit run app/main.py
```

---

## 11. Team Development Workflow & Branch Strategy

- **Main Branch (`main`)**: Protected. Production-ready, fully tested code only.
- **Develop Branch (`develop`)**: Integration branch for completed feature branches.
- **Feature Branches**: Named `feature/<developer>-<feature-description>` (e.g. `feature/static-bandit-wrapper`).
- **Pull Requests**: All code changes require a PR, passing `pytest` suite, and code owner review.

---

## 12. Current Project Status

- **Milestone 1 — COMPLETE**
  - Project directory skeleton created
  - Centralized settings service (`services/config_service.py`)
  - Typed Pydantic v2 domain schemas (`core/issue_model.py`)
  - Deterministic severity engine (`core/severity.py`)
  - 100% unit test pass rate (14/14 tests passing)
- **Milestone 2** — Pending Team Lead Approval
