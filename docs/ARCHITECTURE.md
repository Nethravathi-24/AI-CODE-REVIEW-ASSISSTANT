# System Architecture & Technical Specifications

This document establishes the architectural principles, component specifications, layer responsibilities, data flow, and error-handling behavior for the **AI Code Review Assistant** (Milestone 2 implementation).

---

## 1. High-Level Architecture

The system follows a modular, decoupled layered architecture. Data moves strictly top-to-bottom through defined interfaces.

```text
┌────────────────────────────────────────────────────────────┐
│                    Orchestration Layer                     │
│               (orchestrator/pipeline.py)                   │
└─────────────────────────────┬──────────────────────────────┘
                              │
         ┌────────────────────┴────────────────────┐
         │                                         │
┌────────▼──────────────────┐             ┌────────▼──────────────────┐
│   Input Handling Layer    │             │   Static Analysis Layer   │
│ (input_handling/models.py)│             │     (analyzers/base.py)   │
│  ├─► validator.py         │             │  ├─► ast_analyzer.py      │
│  ├─► language_detector.py │             │  ├─► pyflakes_analyzer.py │
│  └─► preprocessor.py      │             │  ├─► bandit_analyzer.py   │
│                           │             │  ├─► radon_analyzer.py    │
│                           │             │  └─► style_analyzer.py    │
└────────┬──────────────────┘             └────────┬──────────────────┘
         │                                         │
         └────────────────────┬────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────┐
│                    Core Domain Layer                       │
│    (core/issue_model.py, core/interfaces, core/severity)   │
└────────────────────────────────────────────────────────────┘
```

---

## 2. End-to-End Pipeline Flow

The orchestrator executes the static code review through six sequential stages:

```text
Input (Code string / Bytes / Filename)
   │
   ▼
[Stage 1: Validation]
   ├─► Checks: None/empty check, size limit (200 KB), char limit (50,000), binary null-bytes, UTF-8/BOM, file extension (.py, .pyw)
   ├─► On Failure ──► HALT immediately; return PipelineResult(success=False, errors=[PipelineError(stage='validation')])
   └─► On Success ──► Proceed with decoded raw_code
   │
   ▼
[Stage 2: Language Detection]
   ├─► Analyzes file extension (.py, .pyw), keyword signatures (def, class, import, pass, etc.), and manual overrides
   └─► Produces LanguageDetectionResult(language='python', confidence=..., is_python=True/False)
   │
   ▼
[Stage 3: Preprocessing]
   ├─► Normalizes line endings (CRLF and CR to standard LF) and computes 0-indexed line character offsets
   ├─► Validates Python syntax using ast.parse() (without executing code)
   └─► If Syntax Error: captures structured Issue (category='syntax_error', severity='critical') and bypasses downstream AST tools
   │
   ▼
[Stage 4: Static Analysis Execution]
   ├─► Iterates over all registered analyzers: ASTAnalyzer, PyflakesAnalyzer, BanditAnalyzer, RadonAnalyzer, StyleAnalyzer
   ├─► Isolated Execution: Each analyzer runs in an individual try/except block
   ├─► On Exception: logs error, records non-fatal PipelineError, adds warning, marks is_partial_analysis=True, and CONTINUES remaining analyzers
   └─► Gathers List[Issue] findings from all successfully executed analyzers
   │
   ▼
[Stage 5: Severity Processing]
   ├─► Passes every collected Issue through calculate_severity()
   └─► Enforces deterministic severity rules (e.g. syntax errors are always CRITICAL; confidence capping)
   │
   ▼
[Stage 6: Scoring & Result Assembly]
   ├─► Computes CodeQualityScore (deductions per severity, 0-100 overall score, dimension breakdowns)
   ├─► Computes ReviewSummary (exact counts for critical, high, medium, low, and informational issues)
   ├─► Assembles ReviewResult
   └─► Returns PipelineResult(success=True, review_result=..., errors=..., warnings=..., execution_time_seconds=...)
```

---

## 3. Input Handling Layer

The input handling layer is responsible for ingesting, validating, classifying, and normalizing raw code before any static analysis tool is invoked.

### 3.1 Input Representation
The pipeline accepts code as `str`, `bytes`, or `None`, along with an optional `filename` and an optional `manual_override`.

### 3.2 Validation Rules (`input_handling/validator.py`)
1. **Empty / Null Input**: Rejects `None`, empty strings, and whitespace-only submissions (`ValidationErrorType.EMPTY_INPUT`).
2. **Byte Size Limit**: Rejects inputs exceeding `MAX_FILE_SIZE_KB` (default: 200 KB) (`ValidationErrorType.OVERSIZED_BYTES`).
3. **Character Limit**: Rejects inputs exceeding `MAX_CODE_CHARS` (default: 50,000 characters) (`ValidationErrorType.OVERSIZED_CHARS`).
4. **Binary Safety**: Rejects inputs containing null bytes (`\x00`) to prevent non-text or binary file processing (`ValidationErrorType.BINARY_INPUT`).
5. **UTF-8 Decoding & BOM Handling**: Automatically strips UTF-8 Byte Order Marks (BOM `\ufeff` / `\xef\xbb\xbf`) and rejects invalid encodings (`ValidationErrorType.DECODING_ERROR`).
6. **File Extension Check**: If a filename is supplied, validates that it has a valid Python extension (`.py`, `.pyw`) (`ValidationErrorType.INVALID_FILE_TYPE`).

### 3.3 Language Detection (`input_handling/language_detector.py`)
- **Precedence 1**: Manual language override (e.g., `manual_override="python"`).
- **Precedence 2**: File extension (`.py`, `.pyw` yields `0.60` base confidence).
- **Precedence 3**: Regex pattern signature weights (`def `, `class `, `import `, `pass`, `return`, `with `, decorators, etc.).
- **Conflict Handling**: Checks for non-Python signatures (JavaScript, Java, C/C++, Go, Rust, HTML) and penalizes Python confidence if conflicts exist.

### 3.4 Preprocessing & Syntax Validation (`input_handling/preprocessor.py`)
- Normalizes all line endings (CRLF `\r\n` and CR `\r` ➔ standard LF `\n`).
- Preserves the original unmodified code string in `PreprocessedCode.original_code`.
- Generates 0-indexed character line offset arrays for accurate line mapping.
- Runs `ast.parse()` to verify syntax. If a `SyntaxError` or `IndentationError` occurs:
  - Generates a structured `Issue` with `category=CategoryEnum.SYNTAX_ERROR` and `severity=SeverityEnum.CRITICAL`.
  - Sets `is_valid_syntax=False`.
  - The pipeline skips downstream AST static analyzers and includes this syntax error in the final report.

---

## 4. Static Analyzers Layer

All static analyzers inherit from the abstract base class `BaseAnalyzer` (`analyzers/base.py`) and satisfy `StaticAnalyzerProtocol` (`core/interfaces.py`).

```python
class BaseAnalyzer(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def analyze(self, code: str, filename: str = "submitted_snippet") -> List[Issue]: ...
```

### 4.1 Implemented Analyzers

| Analyzer Name | Module | Tool / Underlying Library | Checks Performed | Primary Issue Categories | Severities Produced |
|---|---|---|---|---|---|
| **ASTAnalyzer** | `analyzers/ast_analyzer.py` | Python stdlib `ast` | • Bare `except:` clauses<br>• Unclosed `open()` calls without `with`<br>• Excessive function parameters (> 5)<br>• Deep control-flow nesting (> 4 levels) | `ERROR_HANDLING`<br>`RESOURCE_MANAGEMENT`<br>`CODE_QUALITY`<br>`MAINTAINABILITY` | `HIGH`<br>`MEDIUM`<br>`LOW` |
| **PyflakesAnalyzer** | `analyzers/pyflakes_analyzer.py` | `pyflakes.checker.Checker` | • Undefined variable references<br>• Unused imports<br>• Unused local variables<br>• Duplicate argument names | `LOGICAL_BUG`<br>`BEST_PRACTICE`<br>`CODE_QUALITY` | `HIGH`<br>`LOW` |
| **BanditAnalyzer** | `analyzers/bandit_analyzer.py` | `bandit.core.manager.BanditManager` | • Unsafe `eval()` / `exec()` calls<br>• Hardcoded passwords / secrets<br>• SQL injection vulnerabilities<br>• Insecure deserialization | `SECURITY` | `HIGH`<br>`MEDIUM`<br>`LOW` |
| **RadonAnalyzer** | `analyzers/radon_analyzer.py` | `radon.complexity.cc_visit` | • Functions with cyclomatic complexity > 10 | `MAINTAINABILITY` | `HIGH` (CC ≥ 20)<br>`MEDIUM` (CC > 10) |
| **StyleAnalyzer** | `analyzers/style_analyzer.py` | `pycodestyle.Checker` (in-memory) | • Line length > 79 characters (E501)<br>• Indentation and whitespace formatting | `READABILITY`<br>`BEST_PRACTICE` | `LOW`<br>`INFORMATIONAL` |

---

## 5. Issue Flow & Severity Processing

Findings follow a strictly typed lifecycle from detection to reporting:

```text
┌────────────────────────────────────────────────────────────┐
│ 1. Detection: BaseAnalyzer.analyze() produces List[Issue]   │
│    - detection_source = DetectionSourceEnum.STATIC         │
│    - confidence = 1.0                                      │
│    - 1-indexed line_start and line_end                     │
│    - verbatim code_snippet extracted                       │
└─────────────────────────────┬──────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────┐
│ 2. Issue Collection: Orchestrator merges all tool outputs  │
└─────────────────────────────┬──────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────┐
│ 3. Severity Engine: core.severity.calculate_severity()     │
│    - Base lookup: CATEGORY_BASE_SEVERITY_MAP                │
│    - Hard rule: SYNTAX_ERROR is always CRITICAL            │
│    - Confidence capping: confidence < 0.6 capped at MEDIUM │
└─────────────────────────────┬──────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────┐
│ 4. Score & Summary Engine:                                 │
│    - Deductions: Critical: 25, High: 15, Med: 8, Low: 3    │
│    - CodeQualityScore: 0.0 - 100.0 with qualitative label  │
│    - ReviewSummary: counts per severity level              │
└─────────────────────────────┬──────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────┐
│ 5. Result Models: ReviewResult & PipelineResult assembled  │
└────────────────────────────────────────────────────────────┘
```

---

## 6. Error Handling & Fault Isolation

The pipeline separates fatal validation failures from non-fatal analyzer runtime exceptions.

### 6.1 Invalid Input Handling (Fatal / Early Exit)
When submitted input fails validation (empty, oversized, binary, invalid extension):
1. Execution halts **before** invoking any static analyzers.
2. Zero analyzers are executed.
3. Returns `PipelineResult`:
   - `success = False`
   - `review_result = None`
   - `errors = [PipelineError(stage="validation", is_fatal=True, message=...)]`
   - `is_partial_analysis = False`

### 6.2 Analyzer Failure Isolation (Non-Fatal / Graceful Degradation)
If an individual static analyzer raises an unexpected exception (e.g. out of memory, unexpected AST construct):
1. The exception is caught in the analyzer's isolated execution loop.
2. The failure is logged via `logging.getLogger(__name__).error(..., exc_info=True)`.
3. A non-fatal error is appended to `PipelineResult.errors` (`stage="static_analysis"`, `is_fatal=False`).
4. A warning string is added to `PipelineResult.warnings`.
5. `PipelineResult.is_partial_analysis` is flagged as `True`.
6. **Remaining analyzers continue executing normally.**
7. Findings from successful analyzers are gathered, processed for severity, and returned in `review_result`.

---

## 7. Dependency Rules & Architecture Boundaries

To prevent coupling, the codebase follows strict architectural boundary rules:

1. **Top-Down Dependencies Only**:
   - `orchestrator/` depends on `input_handling/`, `analyzers/`, and `core/`.
   - `analyzers/` and `input_handling/` depend on `core/`.
   - `core/` has **zero** dependencies on higher-level packages.
2. **Framework Independence**:
   - `core/`, `input_handling/`, `analyzers/`, and `orchestrator/` have zero dependencies on web frameworks (Streamlit).
3. **No Network / Zero Execution Guarantee**:
   - The static pipeline performs purely textual and AST-level inspections.
   - User-submitted code is **never** executed (`eval`/`exec`/`import`).
   - No external network calls are made during static analysis.
