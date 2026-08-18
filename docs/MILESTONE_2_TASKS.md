# Milestone 2 Task Breakdown & GitHub Issues Schedule

**Target Release:** Milestone 2 — Static-Analysis Pipeline & Prototype UI  
**Lead Architect:** Team Lead  
**Team Model:** 4-Person Parallel Development  

---

## 1. Branch Allocation & Team Assignment

| Developer Role | Assigned Branch Name | Owned Modules | Assigned Issues |
|---|---|---|---|
| **Static Analysis Developer** | `feature/static-analysis` | `input_handling/`, `analyzers/` | Issue #1 – #11 |
| **AI Developer** | `feature/ai-engine` | `ai/`, `prompts/` | Issue #12 |
| **UI / Reporting Developer** | `feature/ui-reporting` | `app/`, `report/`, `tests/evaluation/` | Issue #13 – #16 |
| **Team Lead** | `feature/m2-integration` | `core/`, `orchestrator/` | Issue #17 – #20 |

---

## 2. GitHub Issues Task Breakdown

### 🔍 Static Analysis Developer (`feature/static-analysis`)

#### [ISSUE #1] M2.1: Input Validation Implementation
- **File**: `input_handling/validation.py`
- **Objective**: Validate submitted raw code for empty state, character limits (>50,000 chars), file size limits (>200 KB), and non-UTF8 encoding fallbacks.
- **Dependencies**: `core/issue_model.py`, `services/config_service.py`
- **Acceptance Criteria**: Raises/returns clear error messages on empty/oversized inputs; never calls API for invalid inputs.

#### [ISSUE #2] M2.2: Python Language Detection
- **File**: `input_handling/language_detection.py`
- **Objective**: Implement heuristic detection based on file extension (`.py`) and Python keyword signatures (`def `, `import `, `class `, indentation).
- **Dependencies**: `input_handling/validation.py`
- **Acceptance Criteria**: Accurately classifies Python snippets with high confidence; returns "unknown" if confidence is low.

#### [ISSUE #3] M2.3: Code Preprocessing & Normalization
- **File**: `input_handling/preprocessing.py`
- **Objective**: Normalize line endings (CRLF ➔ LF), run initial `ast.parse` syntax check, and produce line offset maps.
- **Dependencies**: `core/issue_model.py`
- **Acceptance Criteria**: Produces syntax error `Issue` (`category="syntax_error"`, `severity="critical"`) if code is unparseable.

#### [ISSUE #4] M2.4: Base Analyzer Implementation
- **File**: `analyzers/base.py`
- **Objective**: Create `BaseAnalyzer` class implementing `StaticAnalyzerProtocol`.
- **Dependencies**: `core/interfaces.py`, `core/issue_model.py`
- **Acceptance Criteria**: Establishes standard `analyze(code, filename) -> List[Issue]` method for all linters.

#### [ISSUE #5] M2.5: AST Custom Structural Analyzer
- **File**: `analyzers/ast_analyzer.py`
- **Objective**: Custom AST node walker detecting bare `except:`, unclosed file handles without `with`, deep nesting (>4 levels), and functions with >5 parameters.
- **Dependencies**: `analyzers/base.py`, `core/issue_model.py`
- **Acceptance Criteria**: Returns properly populated `Issue` objects with precise 1-indexed line numbers.

#### [ISSUE #6] M2.6: Pyflakes Analyzer Wrapper
- **File**: `analyzers/pyflakes_analyzer.py`
- **Objective**: Wrap `pyflakes.api` programmatically to capture unused imports, unused local variables, undefined names, and shadow variables.
- **Dependencies**: `analyzers/base.py`, `pyflakes`
- **Acceptance Criteria**: Converts `pyflakes` messages to `Issue` objects (`detection_source="static"`, `confidence=1.0`).

#### [ISSUE #7] M2.7: Bandit Security Analyzer Wrapper
- **File**: `analyzers/bandit_analyzer.py`
- **Objective**: Programmatically run `bandit` scanner to flag hardcoded secrets, `eval`/`exec` calls, unsafe `pickle` usage, and SQL injection patterns.
- **Dependencies**: `analyzers/base.py`, `bandit`
- **Acceptance Criteria**: Maps security findings to `CategoryEnum.SECURITY` and `SeverityEnum.HIGH` or `CRITICAL`.

#### [ISSUE #8] M2.8: Radon Complexity Analyzer Wrapper
- **File**: `analyzers/radon_analyzer.py`
- **Objective**: Compute cyclomatic complexity using `radon`. Flag functions with cyclomatic complexity > 10 as `CODE_QUALITY` or `MAINTAINABILITY` issues.
- **Dependencies**: `analyzers/base.py`, `radon`
- **Acceptance Criteria**: Converts high-complexity functions to `Issue` objects with line range information.

#### [ISSUE #9] M2.9: Style Analyzer Wrapper (PEP 8)
- **File**: `analyzers/style_analyzer.py`
- **Objective**: Wrap `pycodestyle` programmatically to detect line length (>79 chars), indentation errors, and trailing whitespace.
- **Dependencies**: `analyzers/base.py`, `pycodestyle`
- **Acceptance Criteria**: Returns `Issue` objects categorized as `CategoryEnum.READABILITY` or `BEST_PRACTICE` with `INFORMATIONAL` / `LOW` severity.

#### [ISSUE #10] M2.10: Analyzer Error Isolation
- **File**: `analyzers/base.py` / `analyzers/__init__.py`
- **Objective**: Implement exception handling wrapper around individual analyzer executions so that if one analyzer (e.g. `bandit`) crashes, other analyzers continue running.
- **Dependencies**: `analyzers/base.py`
- **Acceptance Criteria**: Analyzer execution failures log errors but do not crash the pipeline.

#### [ISSUE #11] M2.11: Static Analyzer Unit Tests
- **File**: `tests/unit/test_analyzers.py`
- **Objective**: Comprehensive unit test suite for all static analyzers (`ast`, `pyflakes`, `bandit`, `radon`, `style`).
- **Dependencies**: Issues #1 – #10
- **Acceptance Criteria**: 100% test pass rate on fixture snippets containing known bugs.

---

### 🤖 AI Developer (`feature/ai-engine`)

#### [ISSUE #12] M2 AI Integration Boundary & Mock Reviewer
- **File**: `ai/mock_reviewer.py`
- **Objective**: Implement a lightweight `MockAIReviewer` conforming to `AIReviewerProtocol` that returns canned candidate `Issue` objects without making live OpenAI API calls.
- **Dependencies**: `core/interfaces.py`, `core/issue_model.py`
- **Acceptance Criteria**: Allows pipeline integration and testing without incurring network calls or token costs during Milestone 2.

---

### 📊 UI / Reporting Developer (`feature/ui-reporting`)

#### [ISSUE #13] M2.12: Streamlit Code Input Interface
- **File**: `app/main.py`, `app/ui/components.py`
- **Objective**: Build code input section featuring a multi-line text area, file uploader (`.py`), and language override dropdown.
- **Dependencies**: `streamlit`, `core/issue_model.py`
- **Acceptance Criteria**: Captures user input text or uploaded `.py` file content cleanly.

#### [ISSUE #14] M2.13: Review Trigger & Progress Spinner
- **File**: `app/main.py`, `app/ui/components.py`
- **Objective**: Build "Run Review" button with active state management and progress indicator.
- **Dependencies**: `app/main.py`
- **Acceptance Criteria**: Button is disabled during execution or when input is empty; shows active progress spinner.

#### [ISSUE #15] M2.14: Results Dashboard Layout (Mock Data)
- **File**: `app/ui/components.py`
- **Objective**: Render dashboard summary header, overall quality score gauge/card, total issue counters, and severity filter chips using a `ReviewResult` object.
- **Dependencies**: `core/issue_model.py`
- **Acceptance Criteria**: Displays mock `ReviewResult` score and summary statistics cleanly.

#### [ISSUE #16] M2.15: Collapsible Issue Cards Component
- **File**: `app/ui/components.py`
- **Objective**: Render expandable UI cards for each `Issue`, displaying category badge, severity badge, confidence rating, line numbers, code snippet, description, and "why it matters".
- **Dependencies**: `core/issue_model.py`
- **Acceptance Criteria**: Renders all required `Issue` fields; filters dynamically based on selected severity filter chips.

---

### 👑 Team Lead (`feature/m2-integration`)

#### [ISSUE #17] M2.16: Input Validation Pipeline Integration
- **File**: `orchestrator/pipeline.py`
- **Objective**: Wire `input_handling` validation, language detection, and preprocessing into `CodeReviewPipeline`.
- **Dependencies**: Issues #1, #2, #3
- **Acceptance Criteria**: Rejects invalid inputs gracefully before running analyzers; sets language on `ReviewResult`.

#### [ISSUE #18] M2.17: Static Analyzers Pipeline Wiring
- **File**: `orchestrator/pipeline.py`
- **Objective**: Wire all static analyzers into `CodeReviewPipeline.review_code()` to collect static findings into `static_issues`.
- **Dependencies**: Issues #4 – #10
- **Acceptance Criteria**: Pipeline runs all registered static analyzers concurrently or sequentially and gathers `List[Issue]`.

#### [ISSUE #19] M2.18: Pipeline Error Handling & Graceful Degradation
- **File**: `orchestrator/pipeline.py`
- **Objective**: Implement top-level error handling in `CodeReviewPipeline` to capture pipeline warnings, static analyzer failures, and syntax error fallbacks without raising raw exceptions.
- **Dependencies**: Issue #17, #18
- **Acceptance Criteria**: Pipeline returns `PipelineResult` with `success=True` and warnings if individual analyzers fail.

#### [ISSUE #20] M2.19: Milestone 2 End-to-End Integration Tests
- **File**: `tests/integration/test_static_pipeline.py`
- **Objective**: Build integration test suite testing the full static pipeline from raw Python code string input through input validation, static tool execution, to final `ReviewResult`.
- **Dependencies**: Issues #1 – #19
- **Acceptance Criteria**: Tests verify clean snippets receive high scores and buggy snippets return correct static `Issue` objects.

---

## 3. Team Start Plan & Immediate Assignments

- **Immediate Starters**:
  - **Static Analysis Developer**: Can start immediately on **Issue #1 (Input Validation)** and **Issue #4 (Base Analyzer Interface)** on branch `feature/static-analysis`.
  - **UI / Reporting Developer**: Can start immediately on **Issue #13 (Streamlit Input UI)** and **Issue #15 (Results Dashboard Layout with Mock Data)** on branch `feature/ui-reporting`.
  - **AI Developer**: Can start immediately on **Issue #12 (Mock AI Reviewer Boundary)** on branch `feature/ai-engine`.
  - **Team Lead**: Can start on **Issue #17 (Input Validation Pipeline Integration Skeleton)** on branch `feature/m2-integration`.

- **Blockers**: None. All 4 developers have zero blocking dependencies for initial task starts.
