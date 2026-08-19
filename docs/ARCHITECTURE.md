# System Architecture & Technical Specifications

This document establishes the architectural principles, component specifications, layer responsibilities, data flow, and error-handling behavior for the **AI Code Review Assistant** (Multi-Language Engine).

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
│  Input Handling    │ │ Language-Specific │ │   AI Reviewer    │
│  (input_handling/) │ │ Static Analyzers  │ │      (ai/)       │
│  ├─► validator.py  │ │   (analyzers/)    │ │  ├─► prompts.py   │
│  ├─► language_det. │ │  ├─► Python (5)   │ │  └─► openai_rev.  │
│  └─► preprocessor. │ │  ├─► JS/TS (1)    │ │                  │
│                    │ │  └─► Java (1)     │ │                  │
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
│           Multi-Language Remediation & Test Generator      │
│                      (remediation/)                        │
└─────────────────────────────┬──────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────┐
│                   Report Building Layer                    │
│                        (report/)                           │
└────────────────────────────────────────────────────────────┘
```

---

## 2. Multi-Language Pipeline Routing

1. **Validation**: Accepts `.py`, `.pyw`, `.js`, `.jsx`, `.ts`, `.tsx`, `.java`, and `.txt` files.
2. **Language Detection**: Uses regex weights, file extensions, and manual overrides.
3. **Preprocessing**: Normalizes line endings (CRLF -> LF) and line character offsets. For Python, validates AST syntax; for non-Python, skips Python `ast.parse`.
4. **Static Analyzer Routing**:
   - Python -> `[ASTAnalyzer, PyflakesAnalyzer, BanditAnalyzer, RadonAnalyzer, StyleAnalyzer]`
   - JavaScript / TypeScript -> `[JSAnalyzer]`
   - Java -> `[JavaAnalyzer]`
   - Unsupported -> Skips static analysis cleanly, deferring to AI analysis (PRD Part 5.3).
5. **AI Review Engine**: Prompt formatted with language identifier (`Python`, `JavaScript`, `TypeScript`, `Java`).
6. **Result Fusion & Deduplication**: Produces canonical `Issue` domain objects regardless of language.
7. **Severity & Scoring**: Applies PRD Part 15 exact 7-dimension weights.
8. **Remediation & Test Generation**:
   - Python: Python fixes, diffs, Pytest cases.
   - JavaScript/TypeScript: JS/TS fixes, diffs, Jest cases.
   - Java: Java fixes, diffs, JUnit 5 cases.
