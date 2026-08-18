# System Architecture & Dependency Rules

This document establishes the architectural principles, layer responsibilities, and strict dependency flow rules for the **AI Code Review Assistant**.

---

## 1. Architectural Layers & Flow

The codebase follows a clean, modular layer hierarchy. Data moves strictly top-to-bottom through defined interfaces.

```
┌─────────────────────────────────────────────────────────┐
│ User Interface Layer (app/, app/ui/)                    │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│ Pipeline Orchestration Layer (orchestrator/)             │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│ Application & Component Services                        │
│ (input_handling/, analyzers/, ai/, fusion/, report/)    │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│ Core Domain Layer (core/issue_model.py, core/interfaces)│
└─────────────────────────────────────────────────────────┘
```

---

## 2. Dependency Direction Rules

1. **Top-Down Dependencies Only**: Higher-level modules (e.g. `app/`, `orchestrator/`) depend on lower-level modules (`core/`, `interfaces.py`). Lower-level modules NEVER import higher-level modules.
2. **Independent Core Domain**: `core/issue_model.py` and `core/interfaces.py` sit at the base of the architecture. They depend ONLY on standard Python libraries (`pydantic`, `enum`, `typing`).
3. **Infrastructure Isolation**: Concrete static tools (`bandit`, `pyflakes`) and AI clients (`ChatOpenAI`) are wrapped behind standardized interfaces (`StaticAnalyzerProtocol`, `AIReviewerProtocol`).
4. **UI Isolation**: The UI layer (`app/`) is a consumer of `orchestrator/pipeline.py`. Core business logic has zero awareness of Streamlit.

---

## 3. Explicitly FORBIDDEN Dependencies

To prevent coupling and enable independent testing, the following import directions are strictly **PROHIBITED**:

| Forbidden Import Direction | Reason for Prohibition |
|---|---|
| `core` ➔ `streamlit` | **NOT ALLOWED**: Core domain must remain usable in headless CLI, testing, or API environments without Streamlit. |
| `core` ➔ `openai` / `langchain` | **NOT ALLOWED**: Domain schemas must not bind to external AI SDK vendor models. |
| `core` ➔ `app` / `app.ui` | **NOT ALLOWED**: Strict circular dependency prohibition. |
| `analyzers` ➔ `app` / `streamlit` | **NOT ALLOWED**: Static analyzers must return pure Pydantic models. |
| `ai` ➔ `streamlit` | **NOT ALLOWED**: AI reasoning chains must execute independently of UI rendering. |

---

## 4. Shared Domain Data Contracts

All components communicate using standard Pydantic models defined in `core/issue_model.py`:

- Static Analyzers return `List[Issue]` (`detection_source="static"`).
- AI Reasoning Chains return `List[Issue]` (`detection_source="ai"`).
- Fusion Service returns `List[Issue]` (unified & deduplicated).
- Orchestrator returns `ReviewResult` containing `issues`, `score`, and `summary`.
