# Team Development & Collaboration Workflow

This document outlines the four-person parallel development model for building the **AI Code Review Assistant**.

---

## 1. Team Ownership Model

To maximize development velocity and prevent merge conflicts, the codebase is divided into four clear ownership areas:

### 👑 Team Lead (Architecture & Core Infrastructure)
- **Owned Packages**: `core/`, `orchestrator/`, `config/`, `services/`, `IMPLEMENTATION_PLAN.md`
- **Primary Responsibilities**:
  - Maintain core domain schemas (`issue_model.py`) and contracts (`interfaces.py`).
  - Oversee pipeline orchestrator (`orchestrator/pipeline.py`).
  - Perform PR code reviews and approve architectural changes.
  - Coordinate integration across developer modules.

### 🔍 Static Analysis Developer
- **Owned Packages**: `input_handling/`, `analyzers/`
- **Primary Responsibilities**:
  - Implement input validation, language detection, and code normalization.
  - Build static analyzer wrappers for `ast`, `pyflakes`, `bandit`, `radon`, and `pycodestyle`.
  - Ensure all static findings conform to `Issue` model (`detection_source="static"`).

### 🤖 AI Developer
- **Owned Packages**: `ai/`, `prompts/`, co-owns `fusion/`
- **Primary Responsibilities**:
  - Build LangChain model client wrapper (`llm_client.py`).
  - Author versioned prompt templates (`prompts/`).
  - Build reasoning chains for detection, explanation, fix generation, test generation, and summary generation.
  - Co-own fusion and deduplication engine (`fusion/merge.py`).

### 📊 UI & Reporting Developer
- **Owned Packages**: `app/`, `report/`, `remediation/`, `tests/evaluation/`
- **Primary Responsibilities**:
  - Build interactive Streamlit interface (`app/main.py`, `app/ui/components.py`).
  - Implement report builder and Markdown/JSON export serializers (`report/`).
  - Build fix and test AST syntax validators (`remediation/`).
  - Build benchmark evaluation harness (`tests/evaluation/`).

---

## 2. Shared Data Contracts

All team components interact seamlessly because they communicate strictly via the typed domain models defined in `core/issue_model.py`:

```
Static Analyzers ────► List[Issue] (source="static") ──┐
                                                      ├──► Fusion ──► Fused List[Issue] ──► Pipeline ──► ReviewResult
AI Reasoning Chains ─► List[Issue] (source="ai") ──────┘
```

- **Static Analyzer Output**: Returns `List[Issue]` with `detection_source=DetectionSourceEnum.STATIC` and `confidence=1.0`.
- **AI Reviewer Output**: Returns `List[Issue]` with `detection_source=DetectionSourceEnum.AI` and model self-reported confidence.
- **Fusion Output**: Takes both lists and returns a single, unified `List[Issue]` with resolved severities and deduplicated line references.
- **Pipeline Output**: Assembles issues, score, and summary into a `ReviewResult` object passed to the UI layer.

---

## 3. Communication Rules

1. **Contract Changes**: Any change to `core/issue_model.py` or `core/interfaces.py` requires Team Lead approval.
2. **Module Integration**: Test your component against the `CodeReviewPipeline` skeleton in `orchestrator/pipeline.py` using mock interface implementations.
3. **PR Approval**: Every PR must be approved by the designated module owner before merging into `develop`.
