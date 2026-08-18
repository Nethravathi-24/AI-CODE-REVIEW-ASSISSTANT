# Team Development & Collaboration Workflow

This document establishes the collaboration practices, module ownership, feature development workflow, testing standards, and static analyzer contribution guidelines for the **AI Code Review Assistant**.

---

## 1. Module Ownership Matrix

| Developer Role | Owned Packages & Files | Responsibilities |
|---|---|---|
| **Team Lead** | `core/`, `orchestrator/`, `config/`, `services/`, `IMPLEMENTATION_PLAN.md` | Architecture contracts (`interfaces.py`), domain schemas (`issue_model.py`), pipeline orchestration (`orchestrator/pipeline.py`), configuration management, code reviews, PR approvals. |
| **Static Analysis Developer** | `input_handling/`, `analyzers/`, `tests/unit/test_analyzers.py`, `tests/unit/test_input_handling.py` | Input validation, encoding & size boundaries, language detection heuristics, preprocessing & AST syntax checking, static analyzer tool wrappers (`ast`, `pyflakes`, `bandit`, `radon`, `pycodestyle`). |
| **AI Developer** *(Upcoming)* | `ai/`, `prompts/`, co-owns `fusion/` | LangChain client wrappers, versioned prompt templates, LLM reasoning chains (detection, explanation, summary), mock reviewer boundaries. |
| **UI & Reporting Developer** *(Upcoming)* | `app/`, `report/`, `remediation/`, `tests/evaluation/` | Streamlit dashboard UI, report formatters (Markdown/JSON), remediation fix & test validators, benchmark evaluation harness. |

---

## 2. Shared Data Contracts & Rules

All components communicate strictly through the Pydantic v2 schemas defined in `core/issue_model.py` and the protocol contracts in `core/interfaces.py`:

```text
Static Analyzers ────► List[Issue] (source="static") ──┐
                                                       ├──► Orchestrator ──► ReviewResult / PipelineResult
AI Reasoning Chains ─► List[Issue] (source="ai") ──────┘
```

### Contract Integrity Rules
1. **Immutable Core Schemas**: Modifications to `core/issue_model.py` or `core/interfaces.py` require Team Lead review and approval.
2. **Standardized Issue Objects**: Every finding returned by any static tool must be an instance of `Issue` with:
   - `detection_source = DetectionSourceEnum.STATIC`
   - `confidence = 1.0` (or tool-specific normalized float between 0.0 and 1.0)
   - 1-indexed `line_start` and `line_end` (with `line_end >= line_start`)
   - Verbatim `code_snippet` excerpt
3. **No Direct UI Dependencies in Core Logic**: Analyzers, validators, and orchestrators must NEVER import Streamlit or web presentation modules.

---

## 3. Git Branching & PR Workflow

```text
main (Protected, Production-Ready)
  ▲
  │ (Pull Request after full test suite pass)
feature/<module-or-ticket-name> (e.g. feature/static-analyzers, feature/m2-integration)
```

### 3.1 Branch Naming Conventions
- Feature branches: `feature/<developer-or-task-description>` (e.g., `feature/static-analysis`, `feature/m2-integration`)
- Bugfix branches: `fix/<bug-description>` (e.g., `fix/language-detection-patterns`)
- Documentation: `docs/<topic>` (e.g., `docs/m2-architecture-update`)

### 3.2 Pull Request Guidelines
1. **Self-Review**: Run the test suite locally before pushing:
   ```bash
   pytest -v
   ```
2. **Branch Hygiene**: Rebase on `origin/main` before opening PRs to ensure clean history.
3. **PR Description**: Include:
   - Summary of changes
   - Components integrated or modified
   - Verification commands and test results
   - Closed issue references (e.g., `Closes #18`)

---

## 4. How to Add or Modify a Static Analyzer

Follow this 4-step workflow when adding a new static analysis tool or modifying existing analyzer rules:

### Step 1: Inherit from `BaseAnalyzer`
Create a new file in `analyzers/` (e.g. `analyzers/my_tool_analyzer.py`) inheriting from `BaseAnalyzer`:

```python
from typing import List
from analyzers.base import BaseAnalyzer
from core.issue_model import CategoryEnum, DetectionSourceEnum, Issue, SeverityEnum

class MyToolAnalyzer(BaseAnalyzer):
    @property
    def name(self) -> str:
        return "my_tool"

    def analyze(self, code: str, filename: str = "submitted_snippet") -> List[Issue]:
        issues: List[Issue] = []
        # Implement deterministic inspection logic
        # Convert tool findings to Issue objects using self._generate_issue_id()
        # and self._get_code_snippet()
        return issues
```

### Step 2: Register in `analyzers/__init__.py`
Export the new analyzer class and add it to `get_default_analyzers()`:

```python
from analyzers.my_tool_analyzer import MyToolAnalyzer

def get_default_analyzers() -> List[BaseAnalyzer]:
    return [
        ASTAnalyzer(),
        PyflakesAnalyzer(),
        BanditAnalyzer(),
        RadonAnalyzer(),
        StyleAnalyzer(),
        MyToolAnalyzer(),  # <-- Added
    ]
```

### Step 3: Write Unit Tests in `tests/unit/test_analyzers.py`
Add isolated unit test cases testing that the analyzer correctly flags target patterns and returns valid `Issue` instances.

### Step 4: Run Test Suite
```bash
pytest tests/unit/test_analyzers.py -v
pytest tests/integration/test_static_pipeline.py -v
```

---

## 5. Testing & Verification Standards

All code contributions must include tests and maintain 100% pass rates.

### Test Structure
```text
tests/
├── unit/
│   ├── test_config.py          # Settings and environment variable loading
│   ├── test_contracts.py       # Interface protocol runtime checks and imports
│   ├── test_issue_model.py     # Pydantic schema validation & serialization
│   ├── test_severity.py        # Severity engine lookup & confidence capping
│   ├── test_input_handling.py  # Validation, language detection, & preprocessing
│   └── test_analyzers.py       # Unit tests for all static analyzer tool wrappers
└── integration/
    └── test_static_pipeline.py # End-to-end static pipeline integration tests
```

### Executing Tests
```bash
# Run all tests
pytest -v

# Run with uv
uv run --with-requirements requirements.txt pytest -v
```
