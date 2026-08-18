# Milestone 2 — Copy-Paste GitHub Issues Breakdown

**GitHub Repository:** [https://github.com/Nethravathi-24/AI-CODE-REVIEW-ASSISSTANT](https://github.com/Nethravathi-24/AI-CODE-REVIEW-ASSISSTANT)  
**Milestone:** Milestone 2 (Static-Analysis Pipeline & Prototype UI)  
**Team Allocation:** 4-Person Parallel Development  

---

## 1. Assignment Table

| Issue ID | Title | Assigned Role | Branch Name | Parallel Ready? |
|---|---|---|---|---|
| **#1** | M2.1 Input Validation Implementation | Static Analysis Developer | `feature/static-analysis` | ✅ Yes |
| **#2** | M2.2 Python Language Detection | Static Analysis Developer | `feature/static-analysis` | ⚠️ Needs #1 |
| **#3** | M2.3 Code Preprocessing & Syntax Checking | Static Analysis Developer | `feature/static-analysis` | ⚠️ Needs #1 |
| **#4** | M2.4 Base Static Analyzer Implementation | Static Analysis Developer | `feature/static-analysis` | ✅ Yes |
| **#5** | M2.5 AST Custom Structural Analyzer | Static Analysis Developer | `feature/static-analysis` | ⚠️ Needs #4 |
| **#6** | M2.6 Pyflakes Analyzer Wrapper | Static Analysis Developer | `feature/static-analysis` | ⚠️ Needs #4 |
| **#7** | M2.7 Bandit Security Analyzer Wrapper | Static Analysis Developer | `feature/static-analysis` | ⚠️ Needs #4 |
| **#8** | M2.8 Radon Complexity Analyzer Wrapper | Static Analysis Developer | `feature/static-analysis` | ⚠️ Needs #4 |
| **#9** | M2.9 Style Analyzer Wrapper (PEP 8) | Static Analysis Developer | `feature/static-analysis` | ⚠️ Needs #4 |
| **#10**| M2.10 Static Analyzer Error Isolation | Static Analysis Developer | `feature/static-analysis` | ⚠️ Needs #4-#9 |
| **#11**| M2.11 Static Analysis Unit Test Suite | Static Analysis Developer | `feature/static-analysis` | ⚠️ Needs #1-#10 |
| **#12**| M2.AI Mock AI Reviewer & Boundary Stub | AI Developer | `feature/ai-engine` | ✅ Yes |
| **#13**| M2.12 Streamlit Code Input Interface | UI/Reporting Developer | `feature/ui-reporting` | ✅ Yes |
| **#14**| M2.13 Review Trigger Button & Execution State | UI/Reporting Developer | `feature/ui-reporting` | ⚠️ Needs #13 |
| **#15**| M2.14 Results Dashboard Layout (Mock Data) | UI/Reporting Developer | `feature/ui-reporting` | ✅ Yes |
| **#16**| M2.15 Collapsible Issue Cards Component | UI/Reporting Developer | `feature/ui-reporting` | ⚠️ Needs #15 |
| **#17**| M2.16 Input Validation Pipeline Integration | Team Lead | `feature/m2-integration` | ⚠️ Needs #1-#3 |
| **#18**| M2.17 Static Analyzers Pipeline Wiring | Team Lead | `feature/m2-integration` | ⚠️ Needs #4-#10 |
| **#19**| M2.18 Pipeline Error Handling & Degradation | Team Lead | `feature/m2-integration` | ⚠️ Needs #17, #18 |
| **#20**| M2.19 End-to-End Static Integration Tests | Team Lead | `feature/m2-integration` | ⚠️ Needs #1-#19 |

---

## 2. Branch Table

| Branch Name | Target Branch | Primary Developer | Purpose |
|---|---|---|---|
| `feature/static-analysis` | `develop` | Static Analysis Developer | Input validation, language detection, preprocessing, and 5 static analyzers |
| `feature/ai-engine` | `develop` | AI Developer | Mock AI reviewer stub matching `AIReviewerProtocol` |
| `feature/ui-reporting` | `develop` | UI/Reporting Developer | Streamlit UI input area, results dashboard, and issue card components |
| `feature/m2-integration` | `develop` | Team Lead | Orchestrator pipeline wiring, graceful failure handling, & integration tests |

---

## 3. Dependency Graph

```
[M2.1 Input Validation] ────► [M2.2 Language Detection] ────► [M2.3 Preprocessing]
                                                                     │
[M2.4 Base Analyzer] ──┬──► [M2.5 AST Analyzer]                      │
                       ├──► [M2.6 Pyflakes Wrapper]                  │
                       ├──► [M2.7 Bandit Wrapper]                    │
                       ├──► [M2.8 Radon Wrapper]                     │
                       └──► [M2.9 Style Wrapper]                     │
                                   │                                 │
                                   ▼                                 ▼
                       [M2.10 Error Isolation]               [M2.16 Input Wiring]
                                   │                                 │
                                   ▼                                 ▼
                       [M2.11 Analyzer Tests] ───────────────► [M2.17 Analyzer Wiring]
                                                                     │
                                                                     ▼
                                                         [M2.18 Error Handling]
                                                                     │
                                                                     ▼
                                                         [M2.19 Integration Tests]

[M2.12 UI Input] ──► [M2.13 Review Trigger]
[M2.14 UI Dashboard] ──► [M2.15 Issue Cards]  (UI uses mock data independently)
[M2.12 Mock AI Boundary]                      (AI uses mock stub independently)
```

---

## 4. Copy-Paste GitHub Issues Detail

### 🔍 STATIC ANALYSIS DEVELOPER ISSUES

#### Issue #1
- **Title**: `M2.1 — Input Validation Implementation`
- **Milestone**: `Milestone 2`
- **Assigned Role**: `Static Analysis Developer`
- **Branch Name**: `feature/static-analysis`
- **Files/Directories Allowed to Modify**: `input_handling/validation.py`, `tests/unit/test_validation.py`
- **Dependencies**: `core/issue_model.py`, `services/config_service.py`
- **Description**: Implement raw input text validation in `input_handling/validation.py`. Check for empty strings, character count limits (>50,000 chars), file size limits (>200 KB), and non-UTF8 encoding fallbacks.
- **Acceptance Criteria**:
  - Empty string raises or returns explicit error payload.
  - Payload over 50,000 chars or 200 KB is rejected cleanly.
  - Zero live API calls made.
- **Tests Required**: Unit tests in `tests/unit/test_validation.py` checking empty, oversized, and valid code inputs.
- **Definition of Done**: `pytest tests/unit/test_validation.py` passes 100%.

#### Issue #2
- **Title**: `M2.2 — Python Language Detection`
- **Milestone**: `Milestone 2`
- **Assigned Role**: `Static Analysis Developer`
- **Branch Name**: `feature/static-analysis`
- **Files/Directories Allowed to Modify**: `input_handling/language_detection.py`, `tests/unit/test_language_detection.py`
- **Dependencies**: Issue #1 (`input_handling/validation.py`)
- **Description**: Implement heuristic Python language detection based on file extension (`.py`) and Python keyword signatures (`def `, `import `, `class `, `if __name__ ==`).
- **Acceptance Criteria**:
  - Accurately classifies Python code with high confidence.
  - Returns "unknown" if confidence is low.
- **Tests Required**: Unit tests in `tests/unit/test_language_detection.py` testing Python snippets vs non-Python text.
- **Definition of Done**: `pytest tests/unit/test_language_detection.py` passes 100%.

#### Issue #3
- **Title**: `M2.3 — Code Preprocessing & Syntax Checking`
- **Milestone**: `Milestone 2`
- **Assigned Role**: `Static Analysis Developer`
- **Branch Name**: `feature/static-analysis`
- **Files/Directories Allowed to Modify**: `input_handling/preprocessing.py`, `tests/unit/test_preprocessing.py`
- **Dependencies**: `core/issue_model.py`
- **Description**: Normalize line endings (CRLF ➔ LF), run initial `ast.parse` syntax check, and produce line offset maps.
- **Acceptance Criteria**:
  - Returns unparseable syntax errors as a `category="syntax_error"`, `severity="critical"` `Issue` object.
  - Preserves original 1-indexed line numbers.
- **Tests Required**: Unit tests in `tests/unit/test_preprocessing.py` testing clean vs syntactically broken code.
- **Definition of Done**: `pytest tests/unit/test_preprocessing.py` passes 100%.

#### Issue #4
- **Title**: `M2.4 — Base Static Analyzer Implementation`
- **Milestone**: `Milestone 2`
- **Assigned Role**: `Static Analysis Developer`
- **Branch Name**: `feature/static-analysis`
- **Files/Directories Allowed to Modify**: `analyzers/base.py`
- **Dependencies**: `core/interfaces.py`, `core/issue_model.py`
- **Description**: Implement `BaseAnalyzer` class conforming to `StaticAnalyzerProtocol`.
- **Acceptance Criteria**:
  - Provides standard `analyze(code: str, filename: str) -> List[Issue]` signature.
  - Returns standardized `Issue` objects.
- **Tests Required**: Interface compliance check in `test_analyzers.py`.
- **Definition of Done**: `isinstance(analyzer, StaticAnalyzerProtocol)` returns True.

#### Issue #5
- **Title**: `M2.5 — Custom AST Structural Analyzer`
- **Milestone**: `Milestone 2`
- **Assigned Role**: `Static Analysis Developer`
- **Branch Name**: `feature/static-analysis`
- **Files/Directories Allowed to Modify**: `analyzers/ast_analyzer.py`
- **Dependencies**: Issue #4 (`analyzers/base.py`)
- **Description**: Build AST node walker detecting bare `except:` clauses, unclosed file handles without context managers (`with`), nesting depth > 4, and functions with > 5 parameters.
- **Acceptance Criteria**:
  - Returns `Issue` objects with precise 1-indexed line numbers.
  - Sets `detection_source = DetectionSourceEnum.STATIC` and `confidence = 1.0`.
- **Tests Required**: Unit tests in `test_analyzers.py` targeting AST structural bugs.
- **Definition of Done**: Passes unit tests against AST fixture code.

#### Issue #6
- **Title**: `M2.6 — Pyflakes Analyzer Wrapper`
- **Milestone**: `Milestone 2`
- **Assigned Role**: `Static Analysis Developer`
- **Branch Name**: `feature/static-analysis`
- **Files/Directories Allowed to Modify**: `analyzers/pyflakes_analyzer.py`
- **Dependencies**: Issue #4 (`analyzers/base.py`), `pyflakes`
- **Description**: Programmatically invoke `pyflakes.api` to capture unused imports, unused local variables, undefined names, and shadow variables.
- **Acceptance Criteria**:
  - Converts `pyflakes` reporter messages cleanly into `Issue` objects.
  - Never raises unhandled exceptions.
- **Tests Required**: Unit test in `test_analyzers.py` with unused imports and undefined variables.
- **Definition of Done**: Pyflakes issues mapped correctly to `Issue` model.

#### Issue #7
- **Title**: `M2.7 — Bandit Security Analyzer Wrapper`
- **Milestone**: `Milestone 2`
- **Assigned Role**: `Static Analysis Developer`
- **Branch Name**: `feature/static-analysis`
- **Files/Directories Allowed to Modify**: `analyzers/bandit_analyzer.py`
- **Dependencies**: Issue #4 (`analyzers/base.py`), `bandit`
- **Description**: Programmatically run `bandit` scanner against code string to catch hardcoded secrets, `eval`/`exec` usage, unsafe deserialization (`pickle`), and SQL injection patterns.
- **Acceptance Criteria**:
  - Security findings mapped to `CategoryEnum.SECURITY` and `SeverityEnum.HIGH` or `CRITICAL`.
  - Captures CWE reference IDs in `references` field where available.
- **Tests Required**: Unit test in `test_analyzers.py` with SQL injection and hardcoded passwords.
- **Definition of Done**: Security findings created with correct CWE reference tags.

#### Issue #8
- **Title**: `M2.8 — Radon Cyclomatic Complexity Analyzer Wrapper`
- **Milestone**: `Milestone 2`
- **Assigned Role**: `Static Analysis Developer`
- **Branch Name**: `feature/static-analysis`
- **Files/Directories Allowed to Modify**: `analyzers/radon_analyzer.py`
- **Dependencies**: Issue #4 (`analyzers/base.py`), `radon`
- **Description**: Compute cyclomatic complexity using `radon`. Flag functions with cyclomatic complexity > 10 as `CODE_QUALITY` or `MAINTAINABILITY` issues.
- **Acceptance Criteria**:
  - Converts high-complexity functions into `Issue` objects with line bounds.
- **Tests Required**: Unit test in `test_analyzers.py` with high-complexity nested function.
- **Definition of Done**: Radon complexity findings flagged accurately.

#### Issue #9
- **Title**: `M2.9 — Style Analyzer Wrapper (PEP 8)`
- **Milestone**: `Milestone 2`
- **Assigned Role**: `Static Analysis Developer`
- **Branch Name**: `feature/static-analysis`
- **Files/Directories Allowed to Modify**: `analyzers/style_analyzer.py`
- **Dependencies**: Issue #4 (`analyzers/base.py`), `pycodestyle`
- **Description**: Programmatically wrap `pycodestyle` to detect line length > 79 chars, indentation errors, and trailing whitespace.
- **Acceptance Criteria**:
  - Maps style findings to `CategoryEnum.READABILITY` / `BEST_PRACTICE` and `SeverityEnum.INFORMATIONAL` / `LOW`.
- **Tests Required**: Unit test in `test_analyzers.py` with long lines and trailing whitespace.
- **Definition of Done**: PEP 8 style findings converted to `Issue` objects.

#### Issue #10
- **Title**: `M2.10 — Static Analyzer Error Isolation Wrapper`
- **Milestone**: `Milestone 2`
- **Assigned Role**: `Static Analysis Developer`
- **Branch Name**: `feature/static-analysis`
- **Files/Directories Allowed to Modify**: `analyzers/base.py`, `analyzers/__init__.py`
- **Dependencies**: Issues #4 – #9
- **Acceptance Criteria**:
  - Wraps each analyzer execution in a safe try/except block.
  - If one analyzer crashes (e.g. `bandit` exception), remaining analyzers continue execution.
- **Tests Required**: Unit test with a intentionally throwing mock analyzer.
- **Definition of Done**: Crashing analyzer logs error but pipeline returns valid issues from other tools.

#### Issue #11
- **Title**: `M2.11 — Static Analysis Suite Unit Tests`
- **Milestone**: `Milestone 2`
- **Assigned Role**: `Static Analysis Developer`
- **Branch Name**: `feature/static-analysis`
- **Files/Directories Allowed to Modify**: `tests/unit/test_analyzers.py`
- **Dependencies**: Issues #1 – #10
- **Description**: Full unit test suite covering input validation, language detection, preprocessing, and all 5 static analyzers.
- **Acceptance Criteria**:
  - 100% test pass rate across all static analysis unit tests.
- **Definition of Done**: `pytest tests/unit/test_analyzers.py` passes 100%.

---

### 🤖 AI DEVELOPER ISSUES

#### Issue #12
- **Title**: `M2.AI — Mock AI Reviewer & Protocol Boundary Stub`
- **Milestone**: `Milestone 2`
- **Assigned Role**: `AI Developer`
- **Branch Name**: `feature/ai-engine`
- **Files/Directories Allowed to Modify**: `ai/mock_reviewer.py`, `ai/__init__.py`, `tests/unit/test_ai_mock.py`
- **Dependencies**: `core/interfaces.py`, `core/issue_model.py`
- **Description**: Implement `MockAIReviewer` conforming to `AIReviewerProtocol`. Returns canned candidate AI `Issue` objects (`detection_source="ai"`) for pipeline testing without live OpenAI API calls.
- **Acceptance Criteria**:
  - Fully implements `AIReviewerProtocol`.
  - Zero live API calls made; 0 token cost.
- **Tests Required**: Unit test verifying `MockAIReviewer.review()` returns valid `List[Issue]`.
- **Definition of Done**: `pytest tests/unit/test_ai_mock.py` passes 100%.

---

### 📊 UI / REPORTING DEVELOPER ISSUES

#### Issue #13
- **Title**: `M2.12 — Streamlit Code Input Interface`
- **Milestone**: `Milestone 2`
- **Assigned Role**: `UI/Reporting Developer`
- **Branch Name**: `feature/ui-reporting`
- **Files/Directories Allowed to Modify**: `app/main.py`, `app/ui/components.py`
- **Dependencies**: `streamlit`, `core/issue_model.py`
- **Description**: Build Streamlit code input section featuring a multi-line text area (monospace font), file uploader (`.py`), and language override dropdown.
- **Acceptance Criteria**:
  - Captures pasted text or uploaded `.py` file contents cleanly.
  - Does NOT call analyzers directly.
- **Tests Required**: Manual UI check / Streamlit component render check.
- **Definition of Done**: Input text area and uploader render cleanly in `streamlit run app/main.py`.

#### Issue #14
- **Title**: `M2.13 — Review Trigger Button & Execution State`
- **Milestone**: `Milestone 2`
- **Assigned Role**: `UI/Reporting Developer`
- **Branch Name**: `feature/ui-reporting`
- **Files/Directories Allowed to Modify**: `app/main.py`, `app/ui/state.py`
- **Dependencies**: Issue #13
- **Description**: Implement "Run Review" CTA button with active state management and progress spinner indicator during review execution.
- **Acceptance Criteria**:
  - Button disabled when input text is empty or review is in progress.
  - Displays spinner state while waiting for pipeline result.
- **Definition of Done**: Button state toggles correctly during review trigger.

#### Issue #15
- **Title**: `M2.14 — Results Dashboard Layout (Mock Data)`
- **Milestone**: `Milestone 2`
- **Assigned Role**: `UI/Reporting Developer`
- **Branch Name**: `feature/ui-reporting`
- **Files/Directories Allowed to Modify**: `app/ui/components.py`
- **Dependencies**: `core/issue_model.py`
- **Description**: Render top dashboard summary header, overall code quality score card/gauge, issue count metric tiles, and interactive severity filter chips using a `ReviewResult` object.
- **Acceptance Criteria**:
  - Accepts standard `ReviewResult` model.
  - Renders score, label, total issues, and severity breakdown cleanly.
- **Definition of Done**: Dashboard renders correctly using mock `ReviewResult`.

#### Issue #16
- **Title**: `M2.15 — Collapsible Issue Cards Component`
- **Milestone**: `Milestone 2`
- **Assigned Role**: `UI/Reporting Developer`
- **Branch Name**: `feature/ui-reporting`
- **Files/Directories Allowed to Modify**: `app/ui/components.py`
- **Dependencies**: Issue #15
- **Description**: Build collapsible UI cards for each `Issue` object, showing category badge, severity badge, confidence rating, line range, code snippet, description, and "why it matters" explanation.
- **Acceptance Criteria**:
  - Renders all fields from `Issue` schema.
  - Filters dynamically when user toggles severity filter chips.
- **Definition of Done**: Issue cards expand/collapse and filter cleanly.

---

### 👑 TEAM LEAD ISSUES

#### Issue #17
- **Title**: `M2.16 — Input Validation Pipeline Integration`
- **Milestone**: `Milestone 2`
- **Assigned Role**: `Team Lead`
- **Branch Name**: `feature/m2-integration`
- **Files/Directories Allowed to Modify**: `orchestrator/pipeline.py`
- **Dependencies**: Issues #1, #2, #3
- **Description**: Wire `input_handling` validation, language detection, and preprocessing into `CodeReviewPipeline.review_code()`.
- **Acceptance Criteria**:
  - Rejects empty/oversized input before running analyzers.
  - Populates language field on returned `ReviewResult`.
- **Definition of Done**: Pipeline handles invalid inputs gracefully.

#### Issue #18
- **Title**: `M2.17 — Static Analyzers Pipeline Wiring`
- **Milestone**: `Milestone 2`
- **Assigned Role**: `Team Lead`
- **Branch Name**: `feature/m2-integration`
- **Files/Directories Allowed to Modify**: `orchestrator/pipeline.py`
- **Dependencies**: Issues #4 – #10
- **Description**: Wire static analyzer execution loop into `CodeReviewPipeline` to collect all static findings into `static_issues`.
- **Acceptance Criteria**:
  - Executes registered `StaticAnalyzerProtocol` instances.
  - Aggregates static findings into `ReviewResult.issues`.
- **Definition of Done**: Pipeline collects issues from all 5 static tools.

#### Issue #19
- **Title**: `M2.18 — Pipeline Error Handling & Graceful Degradation`
- **Milestone**: `Milestone 2`
- **Assigned Role**: `Team Lead`
- **Branch Name**: `feature/m2-integration`
- **Files/Directories Allowed to Modify**: `orchestrator/pipeline.py`
- **Dependencies**: Issues #17, #18
- **Description**: Add top-level try/except handling in `CodeReviewPipeline` to record `PipelineError` objects and return partial results if individual analyzers fail.
- **Acceptance Criteria**:
  - Pipeline never raises raw exceptions to callers.
  - Returns `PipelineResult(success=True, is_partial_analysis=True)` if an analyzer fails.
- **Definition of Done**: Pipeline degrades gracefully under tool failure.

#### Issue #20
- **Title**: `M2.19 — End-to-End Static Pipeline Integration Tests`
- **Milestone**: `Milestone 2`
- **Assigned Role**: `Team Lead`
- **Branch Name**: `feature/m2-integration`
- **Files/Directories Allowed to Modify**: `tests/integration/test_static_pipeline.py`
- **Dependencies**: Issues #1 – #19
- **Description**: Implement end-to-end integration test suite running raw Python code strings through full validation, static tool execution, and `ReviewResult` output.
- **Acceptance Criteria**:
  - Clean Python snippets receive 100/100 scores.
  - Buggy Python snippets return exact expected static `Issue` objects.
  - All 18 baseline Milestone 1 tests continue passing.
- **Definition of Done**: `pytest` passes 100% across all unit and integration tests.

---

## 5. Recommended Execution Order

1. **Step 1 (Parallel Start)**:
   - Static Analysis Dev starts on **Issue #1 (Input Validation)** and **Issue #4 (Base Analyzer)**.
   - UI/Reporting Dev starts on **Issue #13 (Streamlit Input UI)** and **Issue #15 (Results Dashboard Layout)**.
   - AI Dev starts on **Issue #12 (Mock AI Reviewer Stub)**.
   - Team Lead prepares **Issue #17 (Pipeline Skeleton Wiring)**.
2. **Step 2 (Static Analyzers Execution)**:
   - Static Analysis Dev completes **Issues #2, #3, #5, #6, #7, #8, #9, #10**.
   - UI Dev completes **Issues #14, #16**.
3. **Step 3 (Static Test Verification)**:
   - Static Analysis Dev completes **Issue #11 (Static Analyzer Unit Tests)**.
4. **Step 4 (Team Lead Integration Checkpoint)**:
   - Team Lead merges `feature/static-analysis`, `feature/ai-engine`, and `feature/ui-reporting` into `feature/m2-integration`.
   - Team Lead executes **Issues #17, #18, #19, #20**.
5. **Step 5 (Milestone 2 Pull Request)**:
   - Team Lead opens PR from `feature/m2-integration` to `develop`.
   - Run full `pytest` suite (unit + integration).
   - Merge to `develop` upon 100% test pass.
