# System Architecture & Technical Specifications

This document establishes the architectural principles, component specifications, layer responsibilities, data flow, and error-handling behavior for the **AI Code Review Assistant**.

---

## 1. High-Level Architecture

The system follows a modular, decoupled layered architecture. Data moves strictly top-to-bottom through defined interfaces without circular dependencies.

```text
┌────────────────────────────────────────────────────────────┐
│                    Streamlit Web UI                        │
│                     (app/main.py)                          │
└─────────────────────────────┬──────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────┐
│                    Orchestration Layer                     │
│               (orchestrator/pipeline.py)                   │
└─────────────────────────────┬──────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
┌────────▼───────────┐ ┌──────▼────────────┐ ┌─────▼──────────────┐
│  Input Handling    │ │  Static Analysis  │ │   AI Reviewer    │
│  (input_handling/) │ │   (analyzers/)    │ │      (ai/)       │
└────────┬───────────┘ └──────┬────────────┘ └─────┬──────────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────┐
│                   Result Fusion Engine                     │
│                    (fusion/service.py)                     │
└─────────────────────────────┬──────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────┐
│            Severity & 7-Dimension Scoring Engine           │
│             (core/severity.py & core/scoring.py)           │
└─────────────────────────────┬──────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────┐
│               Remediation & Test Generator                 │
│                      (remediation/)                        │
└─────────────────────────────┬──────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────┐
│                   Report Building Layer                    │
│                        (report/)                           │
└────────────────────────────────────────────────────────────┘
```

---

## 2. End-to-End Pipeline Flow

The orchestrator executes the code review through 10 sequential stages:

```text
Input (Code string / Bytes / Filename)
   │
   ▼
[Stage 1: Validation] (input_handling/validator.py)
   ├─► Checks: Null/empty, 200 KB size limit, 50,000 char limit, binary null-bytes, UTF-8/BOM, .py/.pyw extension
   ├─► On Failure ──► HALT immediately; return PipelineResult(success=False)
   └─► On Success ──► Proceed
   │
   ▼
[Stage 2: Language Detection] (input_handling/language_detector.py)
   └─► Heuristics & manual override support
   │
   ▼
[Stage 3: Preprocessing] (input_handling/preprocessor.py)
   ├─► CRLF/CR ➔ LF line ending normalization & character offset mapping
   └─► AST syntax parsing check (captures structured SYNTAX_ERROR issue if unparseable)
   │
   ▼
[Stage 4: Static Analyzers Execution] (analyzers/)
   ├─► Runs ASTAnalyzer, PyflakesAnalyzer, BanditAnalyzer, RadonAnalyzer, StyleAnalyzer
   └─► Error Isolation: Exceptions logged, non-fatal errors recorded, execution continues
   │
   ▼
[Stage 5: AI Review Execution (Optional)] (ai/)
   ├─► LLM reasoning chain for logic flaws, runtime risks, edge cases, maintainability
   └─► Graceful fallback: returns empty list if OPENAI_API_KEY is missing or fails
   │
   ▼
[Stage 6: Result Fusion & Deduplication] (fusion/)
   ├─► Line & category deduplication matching
   └─► Corroborated findings receive confidence boost and DetectionSourceEnum.BOTH
   │
   ▼
[Stage 7: Severity Recalculation] (core/severity.py)
   └─► Enforces deterministic severity rules (Syntax error is CRITICAL; confidence capping)
   │
   ▼
[Stage 8: Remediation & Test Generation] (remediation/)
   ├─► FixGenerator: produces suggested fix, corrected code snippet, unified diff, AST syntax check
   └─► TestGenerator: produces executable pytest test case
   │
   ▼
[Stage 9: 7-Dimension Quality Scoring & Summary] (core/scoring.py)
   ├─► PRD Part 15 weights: Correctness (25%), Security (25%), Maintainability (15%), Readability (10%), Performance (10%), Best Practices (10%), Testability (5%)
   └─► Severity point deductions: CRITICAL (-25), HIGH (-15), MEDIUM (-8), LOW (-3), INFORMATIONAL (-1)
   │
   ▼
[Stage 10: Result Assembly & Reporting] (report/ & app/main.py)
   └─► ReviewResult & PipelineResult assembled for Streamlit UI rendering and JSON/MD/PDF export
```

---

## 3. Core Component Layers

### 3.1 Domain Models (`core/issue_model.py`)
- `Issue`: Core finding model with stable ID, category, severity, confidence, line range, snippet, description, why-it-matters, fix, generated test, detection source, and tool.
- `CodeQualityScore`: Overall score (0-100), qualitative label, 7 dimension scores, summary notes.
- `ReviewSummary`: Severity counters (critical, high, medium, low, info), executive summary.
- `ReviewResult`: Complete review payload.
- `PipelineResult`: Full execution result with errors, warnings, partial analysis flags, execution time.

### 3.2 7-Dimension Quality Scoring (`core/scoring.py`)
Deterministic scoring engine implementing PRD Part 15 exact weights and severity deduction rules.

### 3.3 Static Analysis Layer (`analyzers/`)
- `ASTAnalyzer`: Custom AST structural walker.
- `PyflakesAnalyzer`: Pyflakes linter wrapper.
- `BanditAnalyzer`: Bandit security scanner wrapper.
- `RadonAnalyzer`: Cyclomatic complexity calculator.
- `StyleAnalyzer`: PEP 8 pycodestyle wrapper.

### 3.4 AI Review Layer (`ai/`)
- Implements `AIReviewerProtocol`.
- Uses OpenAI LLM structured outputs with LangChain.
- Degrades gracefully to static-only mode when API key is unavailable.

### 3.5 Result Fusion Engine (`fusion/`)
- Implements `FusionServiceProtocol`.
- Reconciles static findings and AI findings using fuzzy line and category matching.
- Increases confidence when independent tools corroborate a finding.

### 3.6 Remediation & Test Generation Layer (`remediation/`)
- `FixGenerator`: Generates suggested fixes, corrected snippets, and unified diffs.
- `TestGenerator`: Generates pytest regression test cases.
- `validator.py`: Safe static AST syntax check (`ast.parse()`). Zero execution of user code.

### 3.7 Report Exporter Layer (`report/`)
- `MarkdownReportExporter`: Human-readable Markdown executive report.
- `JSONReportExporter`: Machine-readable pretty-printed JSON payload.
- `PDFReportExporter`: PDF report generation with fallback explanation.

### 3.8 User Interface Layer (`app/main.py` & `app/ui/components.py`)
- Streamlit application entry point.
- Score dashboard, severity summary cards, multi-select category/severity filters, expandable finding cards, and one-click export downloads.

---

## 4. Security & Safety Rules

1. **Zero Code Execution**: Submitted user code, generated fixes, and generated tests are treated strictly as plain text data. The system **NEVER** executes code via `eval()`, `exec()`, or subprocess.
2. **Secret Management**: Environment variables are managed centrally via `pydantic-settings`. Secrets are gitignored and never logged or rendered in UI outputs.
