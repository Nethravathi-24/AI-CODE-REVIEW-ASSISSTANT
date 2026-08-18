# AI Code Review Assistant — Product Requirements Document (PRD)

**Version:** 1.0
**Date:** August 18, 2026
**Status:** Draft — Ready for Implementation Planning
**Authors / Team:** AI Code Review Assistant Team (Hackathon Build)
**Prepared for:** Development team + Antigravity AI coding agent

## Revision History

| Version | Date | Author(s) | Changes |
|---|---|---|---|
| 0.1 | Aug 18, 2026 | Team Lead | Initial draft skeleton |
| 1.0 | Aug 18, 2026 | Team Lead | Complete PRD for implementation |

---

# PART 1 — DOCUMENT & PROJECT FOUNDATION

## 1.1 Executive Summary

The **AI Code Review Assistant** is a tool that a developer can use to submit a piece of code and receive back a structured, trustworthy review of that code: what's wrong with it, how serious each problem is, why it's a problem, how to fix it, and a set of automatically generated tests to prove the fix works. It combines two very different kinds of technology — **deterministic static analysis** (rule-based tools that check code the same way every time) and **AI reasoning** (a large language model that can understand intent, explain things in plain English, and propose fixes) — so that the strengths of each cover the weaknesses of the other.

This is explicitly **not** "paste code into a chatbox and let ChatGPT talk about it." That pattern is unreliable (the AI can miss things or invent things), unstructured (no consistent severity, no consistent format), and not verifiable. Instead, this system treats static analysis as the *source of ground truth* for anything a machine can check with certainty (syntax errors, known insecure function calls, unused variables, missing exception handling, etc.), and treats the AI layer as the *source of judgment and communication* for anything that requires understanding what the code is trying to do (logic errors, naming quality, architectural smells, generating human-readable explanations, proposing fixes, and writing tests).

## 1.2 Project Overview

### One-line product definition
A hybrid static-analysis-plus-AI web application that reviews source code, classifies and explains the problems it finds, proposes and validates fixes, generates tests, and produces a scored review report — all through a Streamlit interface.

### Product Vision
Every developer, regardless of experience level, should be able to get a **fast, explainable, trustworthy** second opinion on their code — the kind of feedback a senior engineer would give in a code review — without waiting for a human reviewer to be available.

### Product Mission
Combine the reliability of deterministic program analysis with the reasoning and communication ability of large language models to produce code reviews that are both **accurate** (grounded in real analysis, not guesses) and **useful** (explained in plain language, with actionable fixes and tests).

## 1.3 Problem Statement

### The existing problem
1. **Manual code review is slow and inconsistent.** Human reviewers are busy, reviews get delayed, and review quality depends on who happens to review the code.
2. **Beginners don't know what "good code" looks like.** Students and junior developers can write code that runs but is insecure, unmaintainable, or subtly buggy, and they have no fast way to learn why.
3. **Pure static-analysis tools (linters) are shallow.** They catch style and known-pattern issues but cannot explain *why* something matters or reason about intent, and their output ("E501 line too long") is not beginner-friendly.
4. **Pure "ask an LLM to review my code" tools are unreliable.** LLMs can hallucinate issues that don't exist, miss issues a simple rule-check would catch, and give inconsistent severity judgments between runs.
5. **Nobody validates AI-suggested fixes.** Many AI coding tools suggest a fix and stop — they don't verify the fix is syntactically valid, doesn't break existing behavior, or is actually different from the original bug.

### Why the problem matters
Bugs and vulnerabilities that reach production are dramatically more expensive to fix than ones caught during development. Developers — especially students and juniors — need fast feedback loops to learn, and teams need consistent, explainable review standards that don't bottleneck on human availability.

### Proposed solution
A hybrid system where static analyzers do the deterministic detection work, an LLM (via OpenAI, optionally supplemented by Hugging Face models) does the reasoning, explanation, fix generation, and test generation, and a result-fusion layer merges and validates both outputs before anything is shown to the user. LangChain orchestrates the AI reasoning pipeline (prompt templates, structured output, chaining steps together), and Streamlit provides the interactive UI.

## 1.4 Product Value Proposition

- **Trustworthy**: findings are grounded in real static analysis wherever possible; AI is not the sole source of truth.
- **Explainable**: every issue comes with a plain-language "why this matters," not just a rule ID.
- **Actionable**: every issue comes with a concrete suggested fix and, where relevant, a generated test.
- **Beginner-friendly**: written to be understandable by someone who has never heard of an AST or an LLM.
- **Cost-aware**: the architecture avoids unnecessary LLM calls, chunking, and re-analysis.

## 1.5 Key Differentiators

1. Hybrid detection (static + AI) instead of "LLM-only" review.
2. A defined, versioned **Issue Schema** so results are structured and predictable, not free-text.
3. A **result-fusion and validation layer** that deduplicates and reconciles static vs. AI findings instead of showing both blindly.
4. **Fix validation** — generated fixes are checked for syntactic validity and, where possible, tested — before being shown as trustworthy.
5. **Automated test generation** tied directly to the specific bug found, not generic boilerplate tests.
6. A defined **code quality score** with transparent, documented weighting rather than an arbitrary number.

## 1.6 Project Objectives

- Deliver a working end-to-end pipeline: code in → structured, explained, scored review out.
- Support Python as the primary/fully-supported language for MVP (see Part 4 for scope details on other languages).
- Demonstrate measurable AI evaluation (precision/recall against known-issue test code), not just a demo that "looks like it works."
- Produce a codebase clean and modular enough for an AI coding agent (Antigravity) to implement directly from this PRD.

## 1.7 Success Definition

The project is successful if:
1. A user can submit code and receive a complete review report (static + AI findings, severities, explanations, fixes, tests, score) in under the target response time (see Part 24).
2. On a benchmark set of intentionally buggy/vulnerable code samples, the system achieves defined minimum precision/recall thresholds (see Part 27).
3. No user API keys or source code are persisted beyond the session unless the user explicitly opts in.
4. The system degrades gracefully (never crashes) on invalid input, oversized input, or API failure.

## 1.8 Assumptions

- Users have an OpenAI API key available (their own, or a shared project key managed via environment variables) — the system does not include billing infrastructure.
- Primary demonstration and grading environment is local / single-instance (hackathon), not multi-tenant production infrastructure.
- Users are reviewing single files or small snippets, not entire multi-file repositories, for MVP.
- Python is the primary language; broader language support is stretch/future scope.

## 1.9 Constraints

- Must be built only from: Python, OpenAI API/models, Hugging Face models/libraries, LangChain, Streamlit, plus justified supporting libraries (see Part 19).
- No custom model training — only inference against pretrained/hosted models (see Part 8).
- Must run within reasonable hackathon time, cost, and compute constraints (no GPU training jobs, no large local model hosting requirements beyond optional lightweight Hugging Face inference).

## 1.10 Dependencies

- OpenAI API availability and an API key.
- Public/pretrained Hugging Face models (e.g., for classification or embeddings) if used — no custom fine-tuning required.
- Python static analysis libraries (see Part 7).
- Internet access for API calls; the app should clearly degrade if offline (see Part 23).

---

# PART 2 — USERS

## 2.1 Target Users

**Primary users:** Individual developers who want fast feedback on a piece of code — students, junior developers, hobbyists, hackathon participants.
**Secondary users:** Team leads or senior developers who want an automated first-pass review before spending human review time; instructors reviewing student code.

## 2.2 User Personas

### Persona A — Beginner Developer ("Ravi, CS Student")
- **Goals:** Learn what "good code" looks like; understand *why* something is wrong, not just that it is.
- **Problems:** Doesn't know static analysis tools exist or how to read their output; doesn't understand terms like "SQL injection" or "race condition."
- **Expectations:** Plain-language explanations, no jargon without definitions, a clear "here's the fixed version."
- **How the product helps:** Every issue includes a beginner-friendly explanation and a corrected code sample with the fix highlighted.

### Persona B — Student Developer preparing for interviews/projects ("Ananya")
- **Goals:** Make sure a project submission or portfolio piece doesn't embarrass her; learn best practices.
- **Problems:** Limited time, wants a quick "is this OK?" pass.
- **Expectations:** A score she can trust, and a short list of the most important things to fix first.
- **How the product helps:** Severity-sorted issue list + an overall quality score with a clear breakdown.

### Persona C — Junior Developer at a company ("Kevin")
- **Goals:** Catch issues before code review so he doesn't look bad in front of senior engineers.
- **Problems:** Doesn't always know which of his own patterns are risky (e.g., unsafe deserialization, missing input validation).
- **Expectations:** Actionable, specific fixes; confidence that flagged security issues are real, not noise.
- **How the product helps:** Hybrid detection reduces false positives; security findings are backed by static detection wherever possible.

### Persona D — Professional Developer / Small Team ("Meera's team")
- **Goals:** A fast automated pre-review pass to reduce the burden on human reviewers.
- **Problems:** Existing linters are shallow; full AI-only tools are unreliable and slow to trust.
- **Expectations:** Structured, exportable reports; consistent severity criteria across runs.
- **How the product helps:** Deterministic severity rules + exportable review report (Part 16, Part 17).

### Persona E — Developer/Team Lead ("Arjun")
- **Goals:** Establish a consistent review bar across a team; use the tool to teach.
- **Problems:** Hard to standardize what "good code" means across different reviewers.
- **Expectations:** Transparent scoring methodology, category breakdowns (security vs. maintainability vs. performance).
- **How the product helps:** Documented, non-arbitrary scoring model (Part 15) usable as a shared standard.

---

# PART 3 — USER JOURNEY & USE CASES

## 3.1 End-to-End User Journey

1. **Open application** — user opens the Streamlit app in a browser.
2. **Understand interface** — sees a clear header explaining what the tool does, an input area, and a sidebar with options.
3. **Submit code** — pastes code into a text area or uploads a source file.
4. **Select/detect language** — the system auto-detects the language; the user can override via a dropdown.
5. **Start review** — user clicks "Review Code."
6. **Wait for analysis** — a progress indicator shows discrete stages (Validating → Static Analysis → AI Analysis → Fusing Results → Generating Fixes → Generating Tests → Scoring).
7. **View summary** — a dashboard shows overall score, issue counts by severity, and a short executive summary.
8. **Inspect individual issues** — user expands each issue to see detail.
9. **Understand explanations** — each issue has a "why this matters" section in plain language.
10. **View suggested fixes** — each issue with a fix shows a diff/before-after view.
11. **Compare original and corrected code** — side-by-side or unified diff view.
12. **Generate tests** — user can request test cases for a specific issue or for the whole file.
13. **Review score** — user sees the quality score breakdown by dimension.
14. **Export results** — user downloads a report (Markdown/JSON/PDF — see Part 16) or copies corrected code.

## 3.2 Use Case Format

Each use case below uses: **User story → Preconditions → User action → System behavior → Expected result → Error cases → Acceptance criteria.**

### UC-1: Submit code by pasting
- **User story:** As a developer, I want to paste code directly so I don't need to save a file first.
- **Preconditions:** App is loaded.
- **User action:** User pastes code into the text area and clicks "Review Code."
- **System behavior:** System validates input is non-empty and under the size limit, then proceeds to language detection.
- **Expected result:** Review pipeline starts.
- **Error cases:** Empty input → inline error message, no API calls made. Oversized input → error message stating the limit and suggesting file upload with chunking (if supported) or trimming.
- **Acceptance criteria:** Given empty input, when "Review Code" is clicked, the system must display "Please paste or upload code before starting a review" and must not call any API.

### UC-2: Upload a source file
- **User story:** As a developer, I want to upload a `.py` file instead of copy-pasting.
- **Preconditions:** App is loaded.
- **User action:** User uploads a file via the file uploader.
- **System behavior:** System validates extension and size, reads and decodes content, populates the code input area.
- **Expected result:** File content is shown and ready for review.
- **Error cases:** Unsupported extension → rejection message listing supported types. File too large → rejection message with the size limit. Non-UTF-8 encoding → attempt fallback decoding, or reject with a clear message.
- **Acceptance criteria:** Given a `.exe` file is uploaded, when upload completes, the system must reject it with "Unsupported file type. Supported: .py, .js, .ts, .java, .txt" (exact supported list defined in Part 5).

### UC-3: Automatic language detection with override
- **User story:** As a developer, I want the system to detect my code's language automatically but let me correct it if wrong.
- **User action:** User submits code without specifying language.
- **System behavior:** System runs detection heuristics (see Part 5.3) and pre-selects a language in the dropdown; user may change it before starting the review.
- **Expected result:** Correct language is used for analysis.
- **Error cases:** Detection confidence too low → system defaults to "Unknown" and requires manual selection before allowing review to start.
- **Acceptance criteria:** Given valid Python code with no language specified, when detection runs, the system must select "Python" with ≥90% detection accuracy on the benchmark set (Part 25).

### UC-4: Run full review
- **User story:** As a developer, I want a single button to trigger the complete review pipeline.
- **User action:** User clicks "Review Code" with valid input and language selected.
- **System behavior:** Pipeline executes each stage in order (Part 10), showing progress.
- **Expected result:** A complete Review Report is displayed (Part 16).
- **Error cases:** Any stage failure triggers graceful degradation (Part 23) — e.g., if AI analysis fails, static-only results are still shown with a warning banner.
- **Acceptance criteria:** Given the OpenAI API is unreachable, when review runs, the system must still return static-analysis findings and display "AI analysis unavailable — showing static analysis results only."

### UC-5: View an individual issue
- **Preconditions:** A review has completed with at least one issue found.
- **User action:** User clicks/expands an issue card.
- **System behavior:** Displays full issue detail per the Issue Model (Part 11).
- **Acceptance criteria:** Every displayed issue must include, at minimum: category, severity, line number, description, "why it matters," and detection source (static/AI/both).

### UC-6: View and accept a suggested fix
- **Preconditions:** An issue has a generated fix.
- **User action:** User views the diff and may copy the corrected snippet or apply it to the full corrected file.
- **System behavior:** Fix is shown as a diff; system never auto-modifies the user's original submitted code without an explicit action.
- **Acceptance criteria:** The system must never replace the user's original input in the UI unless the user explicitly clicks "Apply fix" or "Copy corrected code."

### UC-7: Generate tests for an issue
- **User action:** User clicks "Generate tests" on an issue or on the whole file.
- **System behavior:** System generates test code (pytest by default for Python) targeting the reported bug, and validates the generated test is syntactically valid Python before displaying it.
- **Acceptance criteria:** Generated test code must pass a syntax-validity check (e.g., `ast.parse`) before being shown; if it fails, the system regenerates once, then shows an error if it still fails.

### UC-8: Export report
- **User action:** User clicks "Export" and selects a format.
- **System behavior:** System serializes the full review into the chosen format and offers a download.
- **Acceptance criteria:** Exported Markdown/JSON must contain all issues, the score breakdown, and be well-formed (valid JSON where JSON is chosen).

---

# PART 4 — PRODUCT SCOPE

## 4.1 MVP (Must Implement) — Priority P0/P1

- Code input via paste and file upload (Python only, fully supported).
- Input validation (empty, size, encoding, extension).
- Language detection with manual override.
- Static analysis using AST parsing + at least one established linter/security scanner (Part 7).
- AI analysis layer using OpenAI via LangChain for: logic-issue reasoning, explanations, fix generation.
- Result fusion (merge static + AI findings, dedupe, assign confidence).
- Issue classification with the defined schema (Part 11).
- Deterministic severity assignment (Part 12).
- Fix suggestions with before/after diff (Part 13), with basic validation (syntax check).
- Test generation for at least the most critical issues (Part 14).
- Code quality score (Part 15).
- Full review report rendered in Streamlit (Part 16/17).
- Graceful error handling for all failure modes in Part 23.
- Export to Markdown and JSON.

## 4.2 Advanced Features (If Time Allows) — Priority P2

- Support for JavaScript/TypeScript and Java via additional static analyzers.
- Hugging Face model used for auxiliary classification (e.g., issue-category classification or embedding-based duplicate detection) to reduce LLM calls.
- PDF export of the report.
- Caching of repeated analyses (same code hash → reuse prior static results).
- Side-by-side full-file diff viewer with syntax highlighting.
- Confidence-based filtering ("show only high-confidence issues").

## 4.3 Future Scope (Explicitly Out of MVP) — Priority P3

- GitHub/GitLab integration and PR review bots.
- Multi-file / whole-repository dependency-aware analysis.
- IDE extensions.
- CI/CD pipeline integration.
- Local/offline LLM support.
- Team dashboards and historical quality tracking.
- User accounts, persistent storage of past reviews.

## 4.4 Non-Goals

- This is **not** a replacement for a professional security audit or a human code reviewer.
- This is **not** a code-generation tool (it corrects existing code; it does not build new features from a spec).
- This is **not** a general-purpose chatbot — the AI layer is scoped strictly to the review pipeline.
- This will **not** train or fine-tune any model.

## 4.5 Feature Priority Legend

| Priority | Meaning |
|---|---|
| P0 | Critical — MVP cannot ship without this |
| P1 | High — expected in MVP, minor slip acceptable |
| P2 | Medium — advanced scope, implement if time allows |
| P3 | Future — explicitly deferred |

---

# PART 5 — FUNCTIONAL REQUIREMENTS

## 5.1 Application

- **Startup:** App loads with a clear title ("AI Code Review Assistant"), a one-sentence description, and an empty input state.
- **Configuration:** API keys and settings are loaded from environment variables via a config module (Part 21); app must fail with a clear message (not a stack trace) if a required key is missing, shown only when an AI-dependent action is attempted (the app should still load and allow static-analysis-only usage without a key).
- **Health/status:** A small sidebar status indicator shows whether the OpenAI connection is configured/reachable.

## 5.2 Code Input

- **Paste code:** A multi-line text area, monospace font, minimum visible height for ~20 lines.
- **Upload source files:** Supported extensions for MVP: `.py`. Advanced scope adds `.js`, `.ts`, `.java`. Max file size: 200 KB (configurable, see Part 21).
- **File type validation:** Reject unsupported extensions with an explicit message listing supported types.
- **File size validation:** Reject files over the configured limit; message states the limit and actual size.
- **Empty input:** Reject with an inline message; do not proceed to analysis.
- **Invalid input (e.g., binary data pasted):** Detect non-text content and reject with "This does not appear to be readable source code."
- **Unsupported language:** If detection confidence is low and the user doesn't override, block review start with a prompt to select a language manually.
- **Encoding issues:** Attempt UTF-8 decode; on failure, attempt a fallback (e.g., latin-1) and warn the user that encoding was inferred; if all decoding fails, reject with a clear message.
- **Malformed files:** If a file cannot be parsed at all (e.g., not valid text), reject before entering the pipeline — do not send malformed content to the AI layer.

## 5.3 Language Detection

**What "language detection" means (plain language):** the system looks at the code's syntax patterns (keywords, file extension, structural cues) to guess which programming language it is, the same way a person could tell Python from Java by noticing `def` vs `public static void`.

- **Automatic detection:** Combine (a) file extension if uploaded, (b) keyword/pattern heuristics (e.g., `def`/`import`/indentation-based blocks → Python signal; `function`/`const`/`;`-terminated lines → JS signal), and, if available, a lightweight Hugging Face language-classification model as a tertiary signal.
- **Manual override:** A dropdown always available; user selection always takes precedence over detection.
- **Unsupported languages:** If the detected/selected language isn't supported, static analysis is skipped for that language and the system relies on AI-only analysis, clearly labeled as lower-confidence in the UI.

## 5.4 Preprocessing

**What "preprocessing" means (plain language):** cleaning and organizing the code before analyzing it — like tidying a room before searching it, so nothing gets missed and everything stays where you can find it (i.e., line numbers stay accurate).

- **Code normalization:** Normalize line endings (CRLF → LF), strip trailing whitespace only for analysis purposes (never alters what's shown to the user as "original").
- **Parsing:** For Python, parse into an Abstract Syntax Tree (AST) — see glossary — to enable structural analysis. If parsing fails, capture the syntax error itself as a P0 issue and skip AST-dependent checks (do not crash the pipeline).
- **Chunking:** For MVP, files are expected to be single-snippet/single-file and are not chunked. If a file exceeds the token budget for AI analysis (Part 24), the system chunks by top-level function/class boundaries (never mid-function) and preserves original line numbers via an offset map.
- **Context preservation:** Every chunk sent to the AI includes surrounding context (e.g., imports, enclosing class signature) so reasoning isn't done blind.
- **Handling large files:** Files near the size limit trigger the chunking path above; files over the hard limit are rejected outright (Part 5.2).
- **Maintaining line numbers:** All internal representations track original line numbers so every issue can be pinpointed to the exact submitted line, even after normalization/chunking.

---

# PART 6 — CODE ANALYSIS CATEGORIES

For each category: what it means, why it matters, detection method, example, expected output, limitations.

## 6.1 Syntax Errors
- **Meaning:** Code that does not follow the language's grammar rules and cannot run at all.
- **Why it matters:** Nothing else can be analyzed until this is fixed; it's a hard blocker.
- **Detection:** Static — Python's built-in `ast.parse` / `compile`.
- **Example:** `def foo(:` (missing parameter name / malformed signature).
- **Expected output:** Critical severity issue with exact line/column, pointing at the parser's own error message translated into plain language.
- **Limitations:** Only pinpoints the first syntax error reliably; subsequent errors may be masked until the first is fixed.

## 6.2 Logical Bugs
- **Meaning:** Code that runs but produces the wrong result (e.g., off-by-one errors, incorrect conditionals, wrong operator).
- **Why it matters:** These are the hardest bugs to catch and the most damaging in production.
- **Detection:** AI (reasoning about intent) — static tools cannot know "what the code was supposed to do."
- **Example:** Using `=` instead of `==` in a context where it's legal but wrong (in Python, `if x = 5` is invalid syntax, but analogous logic bugs like an inverted condition `if not is_valid:` where `is_valid()` should have been called are real examples).
- **Expected output:** High/Medium severity, with AI's reasoning trace summarized as "why AI believes this is a bug."
- **Limitations:** AI can misjudge intent from a snippet without full context; flagged as "AI-detected, unconfirmed" unless corroborated.

## 6.3 Runtime Problems
- **Meaning:** Errors that only appear when the code executes (e.g., `IndexError`, `NoneType has no attribute`, division by zero).
- **Why it matters:** These crash programs in production, often on inputs not tested during development.
- **Detection:** Hybrid — static analysis flags likely patterns (e.g., unguarded list indexing, unguarded division); AI reasons about which specific inputs would trigger them.
- **Example:** `value = data[0]` with no length check.
- **Expected output:** Medium/High severity with a concrete example input that would trigger the crash.
- **Limitations:** Static detection is pattern-based and can over-flag defensively-written code; AI corroboration reduces false positives.

## 6.4 Security Vulnerabilities
- **Meaning:** Code patterns that could be exploited by an attacker (e.g., SQL injection, command injection, hardcoded secrets, insecure deserialization).
- **Why it matters:** Directly causes real-world harm — data breaches, system compromise.
- **Detection:** Static-first (via a security-focused scanner — see Part 7) because these are well-known, well-cataloged patterns; AI adds contextual explanation and exploit scenario description.
- **Example:** `cursor.execute("SELECT * FROM users WHERE id = " + user_input)`.
- **Expected output:** Critical/High severity, plain-language exploit scenario, and a safe rewrite (parameterized query).
- **Limitations:** Static scanners can miss vulnerabilities that require broader context (e.g., a "safe" function used unsafely elsewhere); scanner coverage is limited to known rule sets.

## 6.5 Performance Issues
- **Meaning:** Code that works correctly but is unnecessarily slow or resource-heavy (e.g., nested loops causing O(n²) where O(n) is possible, repeated re-computation).
- **Why it matters:** Impacts user experience and infrastructure cost at scale.
- **Detection:** AI-primary (requires understanding algorithmic intent), with static heuristics flagging obvious anti-patterns (e.g., string concatenation in a loop).
- **Example:** Rebuilding a list inside a loop with `+=` on a string instead of using a list and `.join()`.
- **Expected output:** Medium/Low severity, with a Big-O style explanation in plain language plus a rewritten example.
- **Limitations:** True performance impact depends on data scale, which the tool cannot know from a snippet alone — framed as "likely to matter at scale," not a guarantee.

## 6.6 Code Quality
- **Meaning:** General health of the code beyond correctness — structure, complexity, redundancy.
- **Why it matters:** Affects long-term maintainability and bug risk.
- **Detection:** Static (cyclomatic complexity, function length) + AI (holistic judgment).
- **Example:** A single function 300 lines long doing five unrelated things.
- **Expected output:** Low/Medium severity, "consider splitting into smaller functions," with a suggested decomposition.
- **Limitations:** Subjective at the margins; thresholds are configurable, not absolute truth.

## 6.7 Maintainability
- **Meaning:** How easy the code will be to modify safely in the future.
- **Why it matters:** Most cost of software is in maintenance, not initial writing.
- **Detection:** AI-primary, informed by static complexity metrics.
- **Example:** Deeply nested conditionals (5+ levels) making logic hard to follow.
- **Expected output:** Low/Medium severity with a refactor suggestion (e.g., early returns / guard clauses).
- **Limitations:** Judgment-based; presented as a recommendation, not a rule violation.

## 6.8 Readability
- **Meaning:** How easily a human can understand the code at a glance (naming, formatting, comments).
- **Why it matters:** Poor readability slows every future change and increases bug risk during edits.
- **Detection:** Static (formatting/linting rules) + AI (naming quality judgment).
- **Example:** Variable named `x1` holding a user's bank balance.
- **Expected output:** Informational/Low severity with a naming suggestion.
- **Limitations:** Naming taste is subjective; suggestions are framed as optional.

## 6.9 Best-Practice Violations
- **Meaning:** Deviations from widely accepted conventions for the language (e.g., PEP 8 for Python, using `==` vs `is` incorrectly for `None` checks).
- **Why it matters:** Consistency reduces cognitive load and bugs across a team.
- **Detection:** Static (linter rule sets).
- **Example:** `if x == None:` instead of `if x is None:`.
- **Expected output:** Low/Informational severity, rule ID + plain-language explanation.
- **Limitations:** Some "best practices" are style preferences, not universal law; kept low severity.

## 6.10 Error Handling
- **Meaning:** Whether the code anticipates and handles things that can go wrong (missing files, bad input, network failures).
- **Why it matters:** Missing error handling causes crashes and poor user experience.
- **Detection:** Static (bare `except:`, unguarded I/O calls) + AI (judging whether handling is adequate for the operation's risk).
- **Example:** `open(filename)` with no try/except and no existence check.
- **Expected output:** Medium severity with a suggested try/except block.
- **Limitations:** Cannot know the full deployment context (e.g., whether the file is guaranteed to exist upstream).

## 6.11 Resource Management
- **Meaning:** Whether resources (files, network connections, memory) are properly released.
- **Why it matters:** Leaks cause slow degradation and crashes over time.
- **Detection:** Static (unclosed file handles / missing context managers) primarily.
- **Example:** `f = open(path)` without `with` and without `f.close()`.
- **Expected output:** Medium severity, suggests `with open(...) as f:`.
- **Limitations:** Static detection can miss resource leaks routed through custom wrapper functions.

## 6.12 Duplicate/Redundant Logic
- **Meaning:** The same logic repeated in multiple places instead of factored into one place.
- **Why it matters:** Duplication means bugs must be fixed in multiple places, and they often aren't.
- **Detection:** Static (structural/AST similarity comparison) primarily; AI explains a suggested consolidation.
- **Example:** The same three-line validation block copy-pasted in four functions.
- **Expected output:** Low/Medium severity with a suggested shared function.
- **Limitations:** Only detects duplication within the submitted snippet/file, not across a whole codebase (out of MVP scope).

## 6.13 Potential Edge Cases
- **Meaning:** Inputs or conditions the code doesn't appear to consider (empty lists, negative numbers, concurrent access, Unicode).
- **Why it matters:** Edge cases are the most common source of production incidents.
- **Detection:** AI-primary (requires reasoning about the input domain), informed by static signals (e.g., functions accepting parameters with no visible validation).
- **Example:** A function computing an average that doesn't handle an empty list (`ZeroDivisionError`).
- **Expected output:** Medium severity, paired directly with a generated test case reproducing the edge case (Part 14).
- **Limitations:** AI can only reason about edge cases visible from the code and any provided context; cannot know business-specific constraints not present in the code.

---

# PART 7 — STATIC ANALYSIS

## 7.1 What static analysis is (plain language)

Static analysis means checking code **without running it** — the same way a proofreader can catch a spelling mistake in an essay without needing to read it out loud. The tool looks at the text and structure of the code and compares it against known rules and patterns.

## 7.2 Why we need it

- It is **deterministic**: the same code always produces the same finding, every time, with no "creativity" or randomness.
- It is **fast and free** (no external API calls, no per-run cost).
- It is **reliable for well-defined problems**: syntax errors, known-insecure function calls, unused variables, style violations.

## 7.3 What it can reliably detect
Syntax errors, unused imports/variables, undefined names, missing exception handling around risky calls, known dangerous function usage (`eval`, `exec`, unsafe deserialization), unclosed resources, cyclomatic complexity, PEP 8 style violations, structural duplication.

## 7.4 What it cannot reliably detect
Whether the code does what the *developer intended* (requires understanding intent), performance issues that depend on runtime data scale, naming quality/readability judgment, and business-logic-specific edge cases.

## 7.5 Recommended Python libraries/tools (and why)

| Tool | Purpose | Why chosen |
|---|---|---|
| `ast` (standard library) | Parse Python into an Abstract Syntax Tree; detect syntax errors, structural patterns, unused code, complexity | Built-in, zero dependency risk, full control over what's inspected |
| `pyflakes` | Fast detection of unused imports/variables, undefined names | Lightweight, no config overhead, fast enough for interactive use |
| `bandit` | Security-focused static analysis for Python (hardcoded secrets, `eval`/`exec`, SQL injection patterns, insecure deserialization) | Purpose-built security scanner with a well-known, well-maintained rule set — directly covers Part 6.4 |
| `radon` | Cyclomatic complexity and maintainability index calculation | Gives an objective, numeric basis for Part 6.6/6.7 scoring instead of AI guessing a complexity judgment |
| `pycodestyle` (or `pyflakes`+`pycodestyle` combined via a thin wrapper) | PEP 8 style checking | Covers Part 6.9 deterministically |

*Rationale for not using a single heavyweight tool (e.g., full `pylint`) for MVP:* `pylint` is comprehensive but slower to run and noisier by default, which adds latency and requires significant tuning to avoid overwhelming beginner users with low-value findings. The combination above is lighter, faster, and each tool has one clear job — better matching the "one clear purpose per section/module" principle used throughout this architecture. `pylint` may be added in Advanced Scope if time allows.

## 7.6 How AST-based analysis is used

The system parses submitted Python code into an AST and walks it to detect structural patterns not covered by the above libraries — for example: functions with more than N parameters, deeply nested blocks (readability), bare `except:` clauses (error handling), missing `with` statements around `open()` calls (resource management), and duplicate function bodies (structural hashing for Part 6.12).

## 7.7 How linters are integrated

Each static tool is wrapped by a dedicated **Analyzer** module (Part 20) that runs the tool programmatically (not by shelling out where an importable API exists), catches tool-specific exceptions, and converts native tool output into the shared **Issue Model** (Part 11) — so every static finding, regardless of which underlying tool produced it, looks identical in shape to every other finding by the time it reaches the fusion layer.

## 7.8 How static findings are represented

Every static finding is immediately converted into an Issue object (Part 11) with `detection_source = "static"`, a `confidence` of 1.0 (deterministic tools are treated as ground truth for what they detect), and the originating tool name stored for traceability.

## 7.9 How static findings are passed to the AI layer

Static findings are serialized into a compact structured summary (category, line, short description) and included in the AI prompt context (Part 8) so the AI: (a) does not need to re-discover issues static tools already found with certainty, (b) can add reasoning/explanation on top of them, and (c) can be explicitly told "do not re-report these as new findings" to reduce duplication before the fusion step even runs.

## 7.10 How false positives are handled

- Style/complexity thresholds are configurable, not hardcoded absolutes (Part 21).
- The fusion layer (Part 10) can lower confidence or suppress a static finding if the AI layer, given full context, determines it's a false positive (e.g., a "duplicate logic" flag on two functions that are only superficially similar) — but this downgrade is itself logged and shown to advanced users, never silently dropped.
- Users can mark an issue "not relevant" in the UI (local session only, MVP) to declutter the report without needing to trust the tool blindly.

---

# PART 8 — AI/LLM LAYER

## 8.1 What an LLM is (plain language)

A Large Language Model (LLM) is a program trained on huge amounts of text (including code) that can read text you give it and generate a relevant, coherent response — similar to a very well-read assistant who can explain, summarize, or rewrite something you show it. It doesn't "run" the code; it reasons about the code as text, using patterns learned during training.

## 8.2 Why an LLM is useful for code review

Static tools can tell you *what pattern* exists in code, but not *whether that pattern matches what the code was supposed to do*. An LLM can read the code the way a human reviewer would — considering naming, structure, and apparent intent — and produce a plain-language explanation, which static tools cannot do.

## 8.3 What AI should do
- Reason about logical bugs, edge cases, and intent-dependent issues (Part 6.2, 6.13).
- Write plain-language explanations for both static and AI-found issues.
- Propose fixes and corrected code.
- Generate test cases.
- Produce the executive summary of the report.

## 8.4 What AI should NOT do
- AI must **not** be the sole detector for security vulnerabilities or syntax errors — those are static-first (Part 6.1, 6.4).
- AI must **not** silently overwrite the user's submitted code.
- AI must **not** invent findings without being asked to justify them against the actual submitted code (see hallucination mitigation, 8.10).
- AI must **not** be used for anything outside the code-review pipeline (no general chit-chat mode).

## 8.5 Model selection

- **Primary reasoning model:** an OpenAI chat-completion model, accessed via the OpenAI API, used for logic-bug reasoning, explanation generation, fix generation, test generation, and summary generation. The exact model name is a configuration value (Part 21), not hardcoded, so it can be upgraded without code changes.
- **Hugging Face usage:** Hugging Face is used for narrowly-scoped, lighter-weight auxiliary tasks that don't require full LLM reasoning — for example, a pretrained text-classification or embedding model to (a) assist language detection (Part 5.3) as a tertiary signal, and/or (b) compute embedding similarity between findings during fusion to detect duplicate issues (Part 10) cheaply, without an OpenAI call. This keeps expensive reasoning calls reserved for tasks that actually need them.

## 8.6 OpenAI integration

Called exclusively through LangChain (Part 9) using structured prompt templates. Every AI call in the pipeline is scoped to a single, specific task (e.g., "find logic bugs in this function," "explain this specific static finding," "generate a fix for this specific issue") rather than one giant "review this entire file" prompt — this keeps outputs structured, keeps token usage predictable, and makes failures isolated (one failing sub-task doesn't lose the whole review).

## 8.7 Hugging Face integration

Accessed via the `transformers` library (or the Hugging Face Inference API for lighter deployment) using existing pretrained models — no training or fine-tuning. Used only where it reduces cost/latency versus an LLM call, per 8.5.

## 8.8 Model fallback strategy

If the primary OpenAI model call fails (timeout, rate limit, error), the system retries with backoff (Part 21 configuration) up to a configured limit; if it still fails, the system falls back to returning static-analysis-only results for that section, clearly labeled, rather than blocking the entire report (Part 23).

## 8.9 Context handling

**What "context" means here:** everything the AI is shown before being asked to respond — the code itself, relevant surrounding lines, and the static findings already discovered, so the AI isn't guessing blind. Each AI call includes: the relevant code chunk, its static findings summary (8.9 via Part 7.9), the specific task instruction, and the required output format.

## 8.10 Prompt design principles

- Every prompt is a versioned template (stored in a `prompts/` module, Part 20), not an inline string, so prompts can be reviewed, tested, and improved independently of code logic.
- Every prompt explicitly instructs the model to only report issues it can point to specific line(s) for, and to say "no additional issues found" rather than inventing something when nothing is found — directly targeting hallucination reduction.
- Every prompt requests structured output (8.11), never free-form prose, for anything downstream code needs to parse.

## 8.11 Structured output

All AI responses that feed into the Issue Model are requested in a strict JSON schema, using OpenAI structured output / function-calling capabilities where available. LangChain's output parsers validate the returned JSON against a Pydantic schema (Part 11.2) before it is accepted into the pipeline.

## 8.12 Confidence

Every AI-generated finding includes a self-reported confidence value (low/medium/high) that the model is instructed to set conservatively; this confidence, combined with whether a static tool corroborates the same finding, determines the finding's final confidence after fusion (Part 10.6).

## 8.13 Hallucination mitigation

1. **Line-grounding requirement:** every AI finding must reference an actual line number range from the submitted code; findings referencing lines outside the code's range are discarded automatically by validation code (not trusted from the model).
2. **Schema validation:** any AI response that fails to parse against the expected structured schema is rejected and the call is retried once before falling back to "no AI findings for this chunk."
3. **Static corroboration boost, not requirement:** findings corroborated by static analysis get a confidence boost, but AI-only findings are still shown — just labeled "AI-identified, not independently confirmed" — so genuine logic-bug catches aren't suppressed, while still being honest about certainty.
4. **Scoped prompts:** narrowly-scoped prompts (8.6) reduce the chance of the model wandering into speculative territory.
5. **No fabricated fixes without a diff:** every suggested fix is validated (Part 13) before being labeled as ready to use.

## 8.14 Validation of AI output

Handled by the Result Fusion & Validation layer — see Part 10.

## 8.15 Training vs. Inference

**Training** means teaching a model new patterns using large datasets and significant compute (this project does **not** do this). **Inference** means using an already-trained model to process new input and produce output (this project **only** does this). Every model used in this system — the OpenAI model and any Hugging Face model — is used purely at inference time against its existing pretrained knowledge. No fine-tuning, no custom training runs, and no training data pipeline are required for this project to function.

---

# PART 9 — LANGCHAIN

## 9.1 What LangChain is (plain language)

LangChain is a Python framework for building pipelines around LLM calls — it helps you define reusable prompt templates, chain multiple AI steps together in order, and reliably parse the model's response into structured data, instead of writing raw API-call plumbing by hand for every step.

## 9.2 Why we are using it here

The pipeline in this project has multiple distinct AI sub-tasks (logic-bug detection, explanation, fix generation, test generation, summary generation) that need to run in a defined order, sometimes using the output of one step as input to the next (e.g., the fix-generation step needs the logic-bug-detection step's output). LangChain's chain abstraction is a natural fit for orchestrating exactly this kind of multi-step, structured pipeline.

## 9.3 Where LangChain is used

- **Prompt templates:** every AI task (Part 8.10) is defined as a LangChain `PromptTemplate`, parameterized with the code chunk, static findings summary, and task instruction.
- **Structured output parsing:** LangChain's structured-output / Pydantic-backed output parsers validate and coerce model responses into the Issue Model and Fix Model schemas (Part 11).
- **Model interaction:** all OpenAI calls go through LangChain's model wrapper, centralizing configuration (temperature, max tokens, timeouts — Part 21) in one place instead of scattering raw API calls through the codebase.
- **Pipeline orchestration:** the sequence *Static Summary → AI Detection → Explanation → Fix Generation → Test Generation → Summary* is implemented as a LangChain chain (or sequence of chains) so each stage's output flows into the next with defined interfaces.
- **Retry handling:** LangChain's retry wrapper (or a thin custom wrapper around it) handles transient API failures per the retry policy in Part 21.
- **Validation:** output parser validation failures trigger a single automatic re-prompt asking the model to correct its output format, per Part 8.13.

## 9.4 Where LangChain is deliberately NOT used

Static analysis (Part 7) does not touch LangChain at all — it's plain Python calling analyzer libraries directly, because introducing an LLM framework into a deterministic, non-AI code path would add complexity and risk (e.g., unnecessary abstraction, harder-to-predict behavior) with zero benefit. Similarly, simple non-AI utility logic (file validation, severity calculation, scoring math) is plain Python — LangChain is reserved strictly for the AI reasoning pipeline, not used as a general-purpose framework throughout the app.

---

# PART 10 — HYBRID ANALYSIS ARCHITECTURE

## 10.1 What static analysis produces
A list of Issue objects with `detection_source="static"`, confidence 1.0, precise line references, and category tags — produced deterministically and quickly, with zero LLM cost.

## 10.2 What AI produces
A list of Issue objects with `detection_source="ai"`, a self-reported confidence, category tags, plain-language explanations, and (in later pipeline stages) fix suggestions and tests — produced via the LangChain pipeline (Part 9).

## 10.3 How the results are combined (Result Fusion)

1. Static findings are generated first (fast, free) and are always included as a baseline.
2. Static findings' summaries are given to the AI layer as context (Part 7.9) so AI doesn't waste effort re-finding the same issues from scratch.
3. AI is asked to find issues in categories static tools *cannot* reliably detect (logic bugs, edge cases, performance reasoning, naming/readability judgment — see Part 6 category table) plus to **explain** the static findings and **corroborate or challenge** them if it has strong evidence either way.
4. The fusion module merges both lists into one unified list of Issue objects.

## 10.4 How duplicate findings are merged

Two findings are considered duplicates if they reference overlapping line ranges **and** the same or closely related category. When both a static and an AI finding cover the same underlying issue, they are merged into a single Issue object: the static finding's precise line/category data is kept as authoritative, and the AI finding's explanation text is attached to it — the user sees one issue, not two. Near-duplicate AI findings across separate AI calls (e.g., the same issue mentioned twice in different chunks) are deduplicated using either an exact-match check on line range/category or (in Advanced Scope) embedding similarity via the Hugging Face model from Part 8.5.

## 10.5 How conflicting findings are handled

If AI explicitly disputes a static finding (e.g., "this `except:` clause is actually intentional and documented"), the finding is **not deleted** — its confidence is lowered and the AI's counter-reasoning is attached as a note, so the user sees both the original static rule and the AI's context-aware caveat, and can judge for themselves. The system never lets an AI-only claim silently override a deterministic static finding.

## 10.6 How severity is determined
See Part 12 — severity is computed by fixed rule based on category + a deterministic set of contributing factors, not left to the AI to assign freely.

## 10.7 How confidence is calculated

| Scenario | Confidence |
|---|---|
| Static-only finding | High (deterministic tool, category-dependent baseline defined in tool config) |
| Static + AI agree | Highest |
| AI-only finding, self-reported high confidence, grounded in valid line reference | Medium-High |
| AI-only finding, self-reported low confidence | Low |
| AI disputes a static finding | Static finding's confidence is reduced one tier; dispute note attached |

## 10.8 How the final result is produced

The fused, deduplicated, severity-scored, confidence-scored issue list is passed forward to Issue Classification display grouping (Part 11), then to Fix Generation (Part 13) and Test Generation (Part 14) for the subset of issues that warrant them (see 10.9), then to Scoring (Part 15), and finally assembled into the Review Report (Part 16).

## 10.9 Cost-control principle

Not every issue automatically gets a fix and a test generated — by default, fix generation runs for Medium severity and above (configurable), and test generation runs for issues in the Runtime Problems, Logical Bugs, and Potential Edge Cases categories plus any Critical/High issue, since these are the categories where a test genuinely adds verification value. This avoids firing an LLM call for every single Informational/Low style nit, keeping cost and latency proportional to what matters (see Part 24).

---

# PART 11 — ISSUE MODEL

## 11.1 Purpose

A single, predictable schema that every issue in the system — whether from static analysis or AI — conforms to by the time it reaches the UI or report layer. This is what makes "hybrid" actually work: both halves of the system speak the same structured language.

## 11.2 Schema (conceptual; implemented as a Pydantic model)

```json
{
  "issue_id": "string (unique, stable within a review session)",
  "category": "one of: syntax_error | logical_bug | runtime_problem | security | performance | code_quality | maintainability | readability | best_practice | error_handling | resource_management | duplicate_logic | edge_case",
  "severity": "critical | high | medium | low | informational",
  "confidence": "0.0–1.0 float",
  "file": "string (filename or 'submitted_snippet')",
  "line_start": "integer",
  "line_end": "integer",
  "column": "integer | null",
  "code_snippet": "string — exact excerpt from submitted code",
  "description": "string — short, specific statement of the problem",
  "why_it_matters": "string — plain-language explanation of impact",
  "root_cause": "string | null — underlying reason this happened",
  "suggested_fix": "string | null — human-readable fix description",
  "corrected_code": "string | null — the fixed code snippet",
  "test_recommendation": "string | null — reference to a generated test, if any",
  "detection_source": "static | ai | both",
  "detecting_tool": "string | null — e.g. 'bandit', 'ast_walker', 'openai_logic_review'",
  "references": "list[string] | null — e.g. CWE ID for security issues"
}
```

## 11.3 Notes on design
- `issue_id` is deterministic per session (e.g., hash of category+line+description) so re-renders and exports stay stable.
- `corrected_code` is always a *snippet-level* fix, never a full-file rewrite baked silently into `code_snippet` — preserving user control (Part 13).
- `references` gives senior users something concrete to verify against (e.g., linking a SQL injection finding to CWE-89) without the tool claiming false authority.

---

# PART 12 — SEVERITY SYSTEM

## 12.1 Levels

| Severity | Meaning | Criteria | Example |
|---|---|---|---|
| **Critical** | Code will not run, or is actively, easily exploitable | Syntax errors; unauthenticated injection vulnerabilities; hardcoded production secrets | `eval(user_input)`; SQL built via string concatenation with user input |
| **High** | Code runs but has a serious correctness or security risk under realistic conditions | Confirmed logic bugs affecting core behavior; security issues requiring specific but plausible conditions | Off-by-one in a billing calculation; insecure deserialization of untrusted data |
| **Medium** | Real problem, but limited blast radius or requires uncommon conditions | Missing error handling on I/O; resource leaks; edge cases (empty input, None) | Unclosed file handle; unguarded division |
| **Low** | Code quality/maintainability concern, not a functional risk | Long functions; naming issues; minor duplication | 150-line function doing 3 things |
| **Informational** | Style/best-practice note, no functional impact | PEP 8 spacing; docstring missing | Line exceeds 79 characters |

## 12.2 Deterministic assignment rule

Severity is computed as: **base severity for the category (fixed lookup table, e.g., all confirmed security findings start at High, all syntax errors are Critical) → adjusted by confidence (low-confidence AI-only findings are capped at Medium even if the category's base is High) → adjusted by corroboration (static+AI agreement can raise Medium to High within the category's allowed range, never above the category's ceiling).** The AI is explicitly instructed never to assign severity itself — it may argue for/against corroboration, but the numeric/label severity is always computed by this deterministic function in application code.

## 12.3 User-facing behavior
- Issues sorted Critical → Informational by default.
- Severity filter chips in the UI (Part 17) let users show/hide by level.
- The Review Report summary always leads with Critical/High counts first (Part 16).

---

# PART 13 — CODE FIX / REMEDIATION

## 13.1 Fix recommendations
Every issue eligible for a fix (Part 10.9) receives a `suggested_fix` (plain-language description) and, where feasible, `corrected_code` (an actual corrected snippet scoped to the affected lines).

## 13.2 Minimal changes principle
The AI is explicitly prompted to produce the **smallest possible change** that resolves the issue — not a rewrite of the whole function/file — so the fix is easy to review and trust, and so the user's original structure/style is preserved wherever possible.

## 13.3 Preservation of intended behavior
The fix-generation prompt includes the surrounding function/context and an explicit instruction not to change behavior beyond what's necessary to resolve the specific reported issue.

## 13.4 Before/after comparison
The UI (Part 17) renders every fix as a diff: original snippet vs. corrected snippet, with changed lines highlighted.

## 13.5 Patch/diff representation
Internally, fixes are stored as the corrected snippet plus line range metadata; a unified-diff string is generated on demand for display/export using Python's `difflib`.

## 13.6 Fix validation
Before a fix is shown as "ready," the system:
1. Parses `corrected_code` with `ast.parse` (Python) to confirm it is syntactically valid.
2. Re-runs the relevant static checks (e.g., the specific `bandit`/`ast` rule that originally flagged the issue) against the corrected snippet to confirm the original finding no longer triggers.
3. If either check fails, the fix is **not** shown as validated — it is either regenerated once automatically, or shown with a "Suggested fix — not automatically verified" label so the user isn't misled about confidence.

## 13.7 Risks of AI-generated fixes
Documented explicitly to the user in-app (a small info note near each fix): AI-generated fixes may not account for context outside the shown snippet (e.g., other code that depends on the exact original behavior). Users are responsible for reviewing before applying.

## 13.8 User control
The system **never** modifies the user's original submitted code automatically. The user must explicitly click "Copy corrected code" or "Apply fix" (which updates only the in-session working copy shown in the app, never anything outside the session) to use a fix.

---

# PART 14 — TEST GENERATION

## 14.1 Purpose
Turn a reported bug into a concrete, runnable test that demonstrates the problem (and, once fixed, proves the fix works) — this is what separates this tool from one that just talks about bugs.

## 14.2 Unit test generation
For a given issue (primarily Logical Bugs, Runtime Problems, and Edge Cases — Part 10.9), the AI generates a `pytest`-style test function that calls the relevant function/unit with an input that would trigger the reported problem.

## 14.3 Edge-case tests
For Edge Case findings specifically, the generated test targets exactly the boundary condition identified (empty list, zero, negative number, `None`, unicode input, etc.) rather than a generic happy-path test.

## 14.4 Regression tests
Where a fix has been generated (Part 13), the system can generate a paired test asserting the *fixed* behavior, so the user has a regression test to keep going forward, not just a bug-reproduction test.

## 14.5 Tests for reported bugs
Each generated test includes a comment linking it back to the `issue_id` it targets, so the connection between "this is the bug" and "this is the proof" is explicit and traceable.

## 14.6 Test explanation
Each generated test is accompanied by one sentence explaining what it verifies, in plain language, above the code block.

## 14.7 Supported testing frameworks
MVP: `pytest` for Python (most widely used, minimal boilerplate). Advanced scope: `unittest`-style output as an alternative, selectable in the UI.

## 14.8 Validation considerations
Generated tests are validated the same way as fixes (Part 13.6): must pass `ast.parse` before being shown; on failure, one automatic regeneration attempt, then an explicit "test generation failed for this issue" message rather than showing broken code.

---

# PART 15 — CODE QUALITY SCORING

## 15.1 Dimensions
Correctness, Security, Performance, Maintainability, Readability, Best Practices, Testability.

## 15.2 Calculation approach

Each dimension starts at 100 and is deducted from based on the issues found that map to that dimension, weighted by severity:

| Severity | Deduction per issue (dimension-specific) |
|---|---|
| Critical | -25 |
| High | -15 |
| Medium | -8 |
| Low | -3 |
| Informational | -1 |

Each dimension score is floored at 0. The **overall score** is a weighted average of the seven dimension scores:

| Dimension | Weight |
|---|---|
| Correctness | 25% |
| Security | 25% |
| Maintainability | 15% |
| Readability | 10% |
| Performance | 10% |
| Best Practices | 10% |
| Testability | 5% |

*(Testability score reflects whether the code has clear, testable units — e.g., pure functions vs. deeply side-effecting code — assessed by the AI layer against a short, defined rubric, not free judgment.)*

## 15.3 Weighting rationale
Correctness and Security are weighted highest because they represent the most costly failures (broken/exploitable software). Testability is weighted lowest because it's a secondary quality signal, not a direct functional risk, in a single-snippet review context.

## 15.4 Score interpretation

| Score range | Label |
|---|---|
| 90–100 | Excellent |
| 75–89 | Good |
| 60–74 | Needs Improvement |
| 40–59 | Poor |
| 0–39 | Critical Issues Present |

## 15.5 Limitations
The score reflects issues **detectable from the submitted snippet alone** — it cannot assess architecture-wide concerns, team conventions not visible in the code, or business-logic correctness beyond what's inferable. This limitation is stated directly in the report (Part 16), not hidden.

---

# PART 16 — REVIEW REPORT

## 16.1 Contents
- Overall score (with label, Part 15.4) and a one-paragraph executive summary (AI-generated, grounded strictly in the actual issue list — never generic filler).
- Issue count (total, and by severity).
- Severity distribution (visual, e.g., bar or donut chart).
- Security summary (count + list of Security-category issues, called out separately given their importance).
- Performance summary.
- Quality summary (Code Quality + Maintainability + Readability combined view).
- Critical findings (Critical + High severity, shown first, always expanded by default).
- Detailed findings (full issue list, collapsible, filterable — Part 17).
- Suggested fixes (aggregated view/download of all corrected snippets).
- Tests (aggregated view/download of all generated tests as one importable test file).
- Overall recommendations (a short AI-generated "top 3 things to fix first" list, deterministically derived from the highest-severity/highest-confidence issues, not a freeform AI opinion).

## 16.2 Export formats
- **Markdown**: full human-readable report, matching the in-app structure.
- **JSON**: the full structured issue list plus score breakdown, for programmatic use.
- **PDF** (Advanced Scope): rendered from the Markdown version.

---

# PART 17 — STREAMLIT UI/UX

## 17.1 Page structure
Single-page app with a header, a two-column layout below it (input on the left / sidebar controls on the right, or a top input section followed by a full-width results section — final layout decision left to the implementing engineer, but must follow this component list).

## 17.2 Components

- **Header:** App name + one-line description.
- **Sidebar:** Language override dropdown, static-analysis toggle, AI-analysis toggle (allows a "static only, fast, free" mode), OpenAI connection status indicator, export buttons (once a review exists).
- **Code input area:** Large text area with monospace font and line-count indicator.
- **File upload:** Drag-and-drop/browse uploader, shows filename and size once uploaded.
- **Language selector:** Dropdown, auto-populated by detection, always user-editable.
- **Review button:** Primary call-to-action, disabled while input is empty or a review is already in progress.
- **Loading state:** Non-blocking spinner with the current pipeline stage name (Part 10.8 stage list) so the user knows what's happening, not just that something is happening.
- **Progress/status:** A small stepper or progress bar reflecting pipeline stage (Validating → Static Analysis → AI Analysis → Fusion → Fix Generation → Test Generation → Scoring → Done).
- **Summary dashboard:** Score, severity counts, executive summary — always at the top of results.
- **Issue list:** Card-per-issue, collapsed by default except Critical/High, each showing category badge, severity badge, line reference, and one-line description; expands to full Issue Model detail.
- **Severity filters:** Toggle chips (Critical/High/Medium/Low/Informational) that filter the issue list client-side.
- **Category filters:** Multi-select filter by category (Part 6 list).
- **Code viewer:** Line-numbered, syntax-highlighted view of the submitted code, with issue markers on affected lines.
- **Explanation panel:** Inline within each issue card — the `why_it_matters` text.
- **Suggested fix:** Inline diff view within each issue card.
- **Before/after comparison:** Same diff component reused; an aggregated full-file view is also available (Advanced Scope).
- **Test generation:** A button per eligible issue ("Generate test for this issue") plus a "Generate all tests" bulk action.
- **Score visualization:** Radial/bar chart of the seven dimensions (Part 15.1).
- **Export/download:** Buttons for Markdown/JSON (PDF in advanced scope).
- **Error messages:** Consistent, non-technical, actionable (see Part 23 for exact behaviors per failure).
- **Empty states:** Before any review: friendly placeholder explaining how to get started. After a review with zero issues found: a positive "No issues detected" state that still shows the score breakdown (a clean file still gets a full report, not a blank screen).

---

# PART 18 — TECHNICAL ARCHITECTURE

## 18.1 High-level architecture

```
┌────────────────────────────────────────────────────────────┐
│                      Streamlit UI Layer                     │
│   (input, progress, results rendering, export, filters)     │
└───────────────────────────┬──────────────────────────────────┘
                             │
                    ┌────────▼─────────┐
                    │  Orchestrator /    │
                    │  Pipeline Service  │
                    └────────┬─────────┘
        ┌────────────────────┼─────────────────────┐
        ▼                    ▼                      ▼
┌───────────────┐   ┌─────────────────┐   ┌──────────────────┐
│ Input Handling │   │ Static Analysis  │   │  AI Layer          │
│ & Validation   │   │ (ast, pyflakes,  │   │ (LangChain chains   │
│ & Language     │   │ bandit, radon)   │   │  → OpenAI, optional │
│ Detection      │   │                  │   │  Hugging Face)      │
└───────────────┘   └─────────────────┘   └──────────────────┘
        │                    │                      │
        └────────────────────┴──────────┬───────────┘
                                         ▼
                             ┌──────────────────────┐
                             │ Result Fusion &        │
                             │ Validation Layer       │
                             └──────────┬────────────┘
                                        ▼
                             ┌──────────────────────┐
                             │ Issue Classification & │
                             │ Severity Assignment     │
                             └──────────┬────────────┘
                                        ▼
                     ┌──────────────────┴───────────────────┐
                     ▼                                        ▼
         ┌────────────────────┐                  ┌────────────────────┐
         │ Fix Generation &     │                  │ Test Generation &    │
         │ Validation           │                  │ Validation            │
         └──────────┬──────────┘                  └──────────┬───────────┘
                     └───────────────────┬────────────────────┘
                                          ▼
                               ┌────────────────────┐
                               │ Scoring Engine        │
                               └──────────┬───────────┘
                                          ▼
                               ┌────────────────────┐
                               │ Review Report Builder │
                               └──────────┬───────────┘
                                          ▼
                                  Back to Streamlit UI
```

## 18.2 Module responsibilities
- **Input Handling:** validation, decoding, language detection (Part 5).
- **Static Analysis:** each tool wrapped as an independent Analyzer producing Issue objects (Part 7).
- **AI Layer:** LangChain chains for detection/explanation/fix/test/summary (Part 8, 9).
- **Result Fusion & Validation:** dedupe, merge, confidence/severity computation (Part 10, 12).
- **Fix Generation & Validation:** generate + syntax/re-scan validate (Part 13).
- **Test Generation & Validation:** generate + syntax validate (Part 14).
- **Scoring Engine:** deterministic scoring math (Part 15).
- **Review Report Builder:** assembles final structured report + export serialization (Part 16).

## 18.3 Data flow
Raw code → validated/normalized code → (parallel) static findings + AI findings (AI findings generated using static findings as context) → fused issue list → severity/confidence finalized → fixes generated for eligible issues → tests generated for eligible issues → scores computed → report assembled → rendered in UI.

## 18.4 Request flow
User action in Streamlit triggers the Orchestrator synchronously (Streamlit's execution model); the Orchestrator calls each layer in sequence, updating a shared progress state object that the UI polls/reads to render the stepper (Part 17).

---

# PART 19 — TECHNOLOGY STACK

| Technology | Used for | Why chosen | Alternatives considered |
|---|---|---|---|
| **Python** | Entire application | Required by project constraints; also the natural fit given static analysis, AI orchestration, and Streamlit all have first-class Python support | N/A — required |
| **OpenAI API** | Core AI reasoning (logic bugs, explanations, fixes, tests, summary) | Strong general code-reasoning capability, reliable structured-output support needed for Part 8.11 | Hugging Face-hosted LLMs alone — weaker structured-output guarantees for this use case, reserved instead for lightweight auxiliary tasks |
| **Hugging Face (`transformers`)** | Auxiliary language detection signal; optional embedding-based duplicate detection | Avoids spending OpenAI calls on tasks a small pretrained model can do cheaply/locally | Skipping entirely — rejected because it demonstrates broader stack usage and reduces cost/latency for those sub-tasks |
| **LangChain** | Prompt templating, structured output parsing, chain orchestration, retries | Directly matches the multi-step, structured AI pipeline this project needs (Part 9) | Raw OpenAI SDK calls — rejected as the primary approach because it would mean re-implementing templating/parsing/retry logic by hand across many call sites |
| **Streamlit** | UI | Required by project constraints; also fastest way to build an interactive data/report UI in pure Python | N/A — required |
| **`ast` (stdlib)** | Python parsing, structural static checks | Zero dependency risk, precise control | Third-party parsers — unnecessary given stdlib coverage |
| **`pyflakes`** | Unused imports/vars, undefined names | Lightweight, fast, no config burden | `pylint` — heavier, more setup, deferred to Advanced Scope |
| **`bandit`** | Security static analysis | Purpose-built, well-known rule set for Python security issues | Hand-rolled regex security checks — far less reliable |
| **`radon`** | Complexity/maintainability metrics | Gives objective numeric input to scoring instead of AI guessing | AI-only complexity judgment — less consistent |
| **`pycodestyle`** | PEP 8 style checks | Deterministic, standard | AI-only style judgment — inconsistent, wastes AI calls on solved problems |
| **Pydantic** | Issue Model / schema validation | Enforces the structured Issue schema (Part 11) at runtime, integrates with LangChain output parsing | Plain dicts — rejected, no validation guarantees |
| **`difflib` (stdlib)** | Diff/patch generation for fixes | Built-in, sufficient for snippet-level diffs | Third-party diff libs — unnecessary |

---

# PART 20 — PROJECT STRUCTURE

```
ai-code-review-assistant/
├── app/
│   ├── main.py                 # Streamlit entrypoint
│   └── ui/
│       ├── components.py       # Reusable UI widgets (issue card, diff view, score chart)
│       └── state.py            # Streamlit session-state management
├── core/
│   ├── orchestrator.py         # Pipeline coordinator (Part 18.1)
│   ├── issue_model.py          # Pydantic Issue/Fix/Test schemas (Part 11)
│   ├── severity.py             # Deterministic severity rules (Part 12)
│   └── scoring.py              # Scoring engine (Part 15)
├── input_handling/
│   ├── validation.py           # Size/type/empty/encoding checks (Part 5.2)
│   ├── language_detection.py   # Detection heuristics + HF signal (Part 5.3)
│   └── preprocessing.py        # Normalization, AST parse, chunking (Part 5.4)
├── analyzers/
│   ├── base.py                 # Analyzer interface all static tools implement
│   ├── ast_analyzer.py         # Custom AST-walk checks (Part 7.6)
│   ├── pyflakes_analyzer.py
│   ├── bandit_analyzer.py
│   ├── radon_analyzer.py
│   └── style_analyzer.py       # pycodestyle wrapper
├── ai/
│   ├── chains/
│   │   ├── detection_chain.py  # Logic-bug / edge-case detection
│   │   ├── explanation_chain.py
│   │   ├── fix_chain.py
│   │   ├── test_chain.py
│   │   └── summary_chain.py
│   ├── llm_client.py            # LangChain OpenAI model wrapper/config
│   └── hf_client.py             # Hugging Face auxiliary model wrapper
├── prompts/
│   ├── detection_prompt.py
│   ├── explanation_prompt.py
│   ├── fix_prompt.py
│   ├── test_prompt.py
│   └── summary_prompt.py
├── fusion/
│   ├── merge.py                 # Dedup/merge logic (Part 10.3-10.6)
│   └── confidence.py            # Confidence computation (Part 10.7)
├── remediation/
│   ├── fix_validator.py         # Syntax + re-scan validation (Part 13.6)
│   └── test_validator.py        # Syntax validation for generated tests (Part 14.8)
├── report/
│   ├── builder.py                # Assembles final Review Report (Part 16)
│   └── exporters.py              # Markdown / JSON (/ PDF) export
├── services/
│   └── config_service.py         # Centralized config loading (Part 21)
├── utils/
│   ├── diffing.py                 # difflib wrappers
│   └── file_utils.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/                  # Benchmark buggy/vulnerable code samples (Part 25)
├── docs/
│   └── this PRD, architecture notes
├── config/
│   └── settings.py / .env.example
├── requirements.txt
└── README.md
```

**Responsibility notes:** `core/` holds pipeline-agnostic domain logic (schemas, severity, scoring) with no I/O dependencies, making it independently unit-testable. `analyzers/` and `ai/chains/` are deliberately parallel, swappable structures — each analyzer/chain implements a common interface so new ones can be added without touching the orchestrator. `fusion/` is isolated because it's the most architecturally important piece of the hybrid design (Part 10) and deserves its own tested module rather than being buried inside the orchestrator.

---

# PART 21 — CONFIGURATION

## 21.1 Environment variables (`.env`, never committed)

| Variable | Purpose | Default |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI authentication | — (required for AI features) |
| `OPENAI_MODEL` | Model name for reasoning calls | configurable, e.g. `gpt-4.1-mini`-class model |
| `HF_MODEL_NAME` | Hugging Face model identifier for auxiliary tasks | configurable pretrained model |
| `AI_TEMPERATURE` | Model creativity/randomness setting | `0.2` (low, for consistency) |
| `AI_MAX_TOKENS` | Max tokens per AI call | `1500` |
| `AI_TIMEOUT_SECONDS` | Per-call timeout | `30` |
| `AI_MAX_RETRIES` | Retry attempts on transient failure | `2` |
| `MAX_FILE_SIZE_KB` | Upload size limit | `200` |
| `MAX_CODE_CHARS` | Paste-input character limit | `50000` |
| `ENVIRONMENT` | `development` / `production` flag | `development` |

## 21.2 Notes
- Secrets are never hardcoded or logged (Part 22).
- Development mode may enable verbose logging of pipeline stage timings; production mode suppresses this.
- All thresholds referenced elsewhere in this PRD (complexity limits, severity deduction values, chunking size) are defined as named constants in `config/settings.py`, not scattered magic numbers, so they can be tuned in one place.

---

# PART 22 — SECURITY & PRIVACY

## 22.1 Source code privacy
Submitted code may contain proprietary logic or secrets. The application must:
- Not persist submitted code to disk or a database by default (in-memory/session-only for MVP).
- Clearly state in the UI that code sent for AI analysis is transmitted to OpenAI's API (and optionally Hugging Face, if using their hosted inference rather than local models) subject to those providers' terms — this must be visible before the first AI call, not buried in documentation.
- Offer a "static analysis only" mode (Part 17 sidebar toggle) so a user with sensitive code can get value without any code leaving the local process.

## 22.2 API key protection
Keys are loaded only from environment variables, never from user-facing input fields, and never logged or included in exported reports.

## 22.3 Secret detection
The `bandit` analyzer (Part 7.5) flags hardcoded secrets/credentials found in submitted code itself, as a Critical security finding — protecting the *user* from their own mistake, distinct from protecting the app's own keys.

## 22.4 Prompt injection
Because submitted code is untrusted text passed into LLM prompts, the system must treat code content as **data, not instructions**: prompt templates (Part 9.3) place the code in a clearly delimited, quoted section and explicitly instruct the model that content within that section is data to analyze, not commands to follow — mitigating attempts to embed instructions like "ignore previous instructions" inside a code comment or string literal.

## 22.5 Malicious/unsafe input
The system never executes submitted code (no `exec`/`eval` of user input anywhere in the pipeline — analysis is static/textual and AI-based only). This is a hard architectural rule, not a configuration option.

## 22.6 Large payload attacks
Enforced by the size limits in Part 21; requests exceeding limits are rejected before any processing, static or AI.

## 22.7 Data retention
No long-term retention for MVP. If export/download is used, that file exists only on the user's own machine — the application itself does not retain a copy after the session ends.

## 22.8 Logging
Logs may include pipeline stage timings, error types, and non-sensitive metadata (language, file size, issue counts) for debugging — logs must never include full submitted source code or API keys in production mode.

## 22.9 Third-party API transmission
Explicitly disclosed to the user (22.1). No code is sent to any third party beyond the configured OpenAI/Hugging Face endpoints the app itself calls.

## 22.10 User consent
The "static only" toggle (22.1) functions as the practical consent mechanism for MVP — using AI analysis is an explicit, visible choice, not a silent default the user can't see.

---

# PART 23 — ERROR HANDLING

| Scenario | Behavior |
|---|---|
| Invalid code (unparseable) | Captured as a Critical syntax-error Issue; static analysis for AST-dependent checks skipped; AI is still invoked for whatever it can usefully say about the parse error location, using raw text context |
| Unsupported language | Block review start with a message unless user manually selects a supported language; if none apply, offer "AI-only best-effort review" as an explicit opt-in |
| Empty input | Inline validation error; no pipeline execution, no API calls |
| Large files | Rejected outright if over hard limit; chunked if within the "large but chunkable" range (Part 5.4) |
| Parser failure | Logged; treated as a syntax-error finding, pipeline continues in degraded mode |
| Static analyzer failure (e.g., `bandit` throws) | That analyzer's failure is caught individually; other analyzers still run; a small "some static checks unavailable" note is shown, review still completes |
| OpenAI API failure | Retry per policy (Part 21); on exhausted retries, fall back to static-only results with a visible warning banner; pipeline does not crash |
| Hugging Face failure | Non-critical (auxiliary use only) — silently falls back to the next detection signal (e.g., extension/heuristic-only language detection) with no user-facing error |
| Network timeout | Treated identically to API failure above |
| Rate limiting | Treated as a retryable transient failure; if retries exhausted, same fallback as API failure, with a specific "rate limited, try again shortly" message |
| Malformed AI response | Rejected by schema validation (Part 8.11); triggers one re-prompt; if still malformed, that specific finding/fix/test is dropped with a logged warning, not shown to the user as if it were valid |
| AI hallucination (line out of range, etc.) | Discarded per Part 8.13 grounding rule before ever reaching the UI |
| Partial analysis | Always allowed and clearly labeled — a report with only static results, or missing fixes/tests for some issues, is a valid, honestly-labeled output, never presented as if it were complete |
| Unexpected exceptions | Caught at the Orchestrator level; user sees a friendly "Something went wrong during review — please try again" message; full stack trace goes to logs only, never to the UI |

---

# PART 24 — PERFORMANCE & COST

## 24.1 Response-time expectations
Target end-to-end review time for a typical snippet (under ~150 lines): **under 20 seconds**, dominated by AI call latency. Static analysis alone should complete in under 2 seconds.

## 24.2 File size limitations
See Part 21 (`MAX_FILE_SIZE_KB`, `MAX_CODE_CHARS`).

## 24.3 Token limitations
`AI_MAX_TOKENS` per call bounds cost per request; prompts are scoped per-task (Part 8.6) rather than one large prompt, keeping each individual call's token usage predictable and small.

## 24.4 Chunking strategy
See Part 5.4 — function/class-boundary chunking only when a file exceeds the token budget for a single AI call.

## 24.5 API call minimization
- Static findings are computed once and reused as context across all AI sub-tasks (no redundant re-analysis).
- Fix/test generation is scoped only to issues that warrant it (Part 10.9), not run for every single finding.
- Hugging Face used for auxiliary tasks specifically to avoid spending OpenAI calls where unnecessary (Part 8.5).

## 24.6 Caching
Advanced Scope: cache static-analysis results keyed by a hash of the submitted code, so re-running a review on unchanged code skips redundant static tool execution (AI results are not cached by default, since a user may want fresh reasoning, but this is configurable).

## 24.7 Retry strategy
See Part 21 (`AI_MAX_RETRIES`) with exponential backoff.

## 24.8 Concurrent processing
Where the pipeline allows (e.g., independent static analyzers, or independent AI sub-tasks that don't depend on each other's output), calls are issued concurrently (e.g., via `asyncio` or a thread pool) to reduce total wall-clock time, as long as this doesn't compromise the ordering dependencies noted in Part 9.2.

## 24.9 Cost-awareness
Every architectural decision that reduces LLM calls (Parts 7.9, 8.5, 10.9, 24.5) exists specifically to keep this system affordable to run repeatedly during development, testing, and demoing — not just as an afterthought.

---

# PART 25 — DATA & BENCHMARKING

## 25.1 What we need
- **Training data:** **Not needed.** No model in this system is trained or fine-tuned (Part 8.15).
- **Evaluation data:** **Needed.** A curated set of Python code samples with known, labeled issues, used to measure detection accuracy (Part 27).
- **Test data (software testing sense):** **Needed.** Standard unit/integration test fixtures for the application's own code (Part 26), separate from the AI-evaluation dataset above.

## 25.2 Sources for evaluation data
- Hand-authored synthetic samples: small Python snippets deliberately containing exactly one or two known issues each (e.g., one file with a SQL injection, one with an off-by-one, one with a resource leak) — gives precise ground truth.
- Publicly available vulnerable-code example sets (e.g., well-known open-source security-training repositories) — used only as read-only reference material to author/validate the team's own labeled fixtures, respecting each source's license; the project does not redistribute third-party code verbatim as part of the shipped product.
- Real-world open-source snippets with known, documented bugs (from public bug trackers/changelogs) — used sparingly, for realism, alongside the synthetic set.

## 25.3 Ground-truth labels
Each benchmark fixture is stored with an accompanying expected-issues file (category, approximate line, severity) in `tests/fixtures/`, used by the evaluation harness (Part 27) to compute precision/recall automatically.

---

# PART 26 — TESTING STRATEGY

| Test type | Scope |
|---|---|
| **Unit testing** | `core/`, `fusion/`, `remediation/`, `report/` modules — pure logic, no external API calls, fully mockable |
| **Integration testing** | Full pipeline run against fixture code, with AI calls mocked to return canned structured responses, verifying data flows correctly end-to-end |
| **UI testing** | Manual + Streamlit's testing utilities for key interactions (submit, filter, export) |
| **Static-analysis testing** | Each analyzer tested against fixtures with known findings to confirm correct Issue objects are produced |
| **AI testing** | See Part 27 (separate evaluation discipline) |
| **End-to-end testing** | At least one real (non-mocked) full run against a known benchmark fixture before each milestone demo, to catch integration drift |
| **Regression testing** | Benchmark fixture suite (Part 25) re-run whenever prompts, severity rules, or fusion logic change |
| **Security testing** | Confirm the app itself never executes submitted code; confirm no secrets appear in logs/exports |
| **Performance testing** | Timing assertions against the targets in Part 24.1 on the benchmark set |

Edge cases to explicitly test: empty input, single-line input, syntactically invalid input, extremely long single line, non-UTF-8 file, file at exactly the size limit, code with zero issues, code with only Informational issues, API-key-missing state, simulated API timeout/failure.

---

# PART 27 — AI EVALUATION

## 27.1 Why this is separate from normal testing
Normal software tests check "does the code do what it's supposed to do." AI evaluation checks "is the AI's *judgment* actually good" — a fundamentally probabilistic question that needs its own methodology and metrics, run against the labeled benchmark set from Part 25.

## 27.2 Metrics

- **Precision:** of all issues the system reported, what fraction were real (matched a ground-truth label)?
- **Recall:** of all real issues in the ground-truth set, what fraction did the system find?
- **F1:** harmonic mean of precision and recall — a single balanced score.
- **False positives:** issues reported that don't correspond to any real ground-truth issue.
- **False negatives:** ground-truth issues the system missed entirely.
- **Severity accuracy:** for correctly-detected issues, does the assigned severity match the expected label (exact match or within one level)?
- **Explanation usefulness:** rated on a simple rubric (e.g., 1–5) by human reviewers on a sample — does the explanation correctly describe *why* the issue matters?
- **Fix correctness:** does the validated fix (Part 13.6) actually resolve the issue without introducing a new one, checked against the fixture's expected corrected behavior where available?
- **Test generation usefulness:** does the generated test actually fail against the original buggy code and pass against the fixed code (where both are available in the fixture)?
- **Hallucination rate:** fraction of AI findings discarded by the grounding/validation checks in Part 8.13 relative to total AI findings generated — tracked as a health metric of the AI layer itself.

## 27.3 Human evaluation
Automated metrics above are necessary but not sufficient — a small human review pass (team members rating a sample of explanations/fixes on the 1–5 rubric) is used to sanity-check that "matches ground truth" also means "is actually clear and helpful to a human reader," which automated string/line matching alone cannot confirm.

## 27.4 Minimum bar for demo readiness
Recommended targets before considering the AI layer "demo ready" (tunable by the team based on time available): Precision ≥ 0.7, Recall ≥ 0.6 on the labeled benchmark set, hallucination rate (post-validation) effectively 0% (since grounding validation should already remove ungrounded findings before they're counted).

---

# PART 28 — ACCEPTANCE CRITERIA

Representative testable criteria (additional criteria are embedded throughout Part 3's use cases and should be treated as part of this section collectively):

- Given valid Python code containing a known SQL-injection pattern, when a review is run, the system must report a Security-category Critical or High issue referencing the exact line, with `detection_source` including `static`.
- Given code with a bare `except:` clause, when reviewed, the system must report an Error Handling issue at Medium severity or the category's defined base severity.
- Given code that parses successfully with no issues in any category, when reviewed, the system must still return a complete report with an overall score in the "Excellent" or "Good" range and an explicit "No issues detected" summary state.
- Given the OpenAI API key is missing, when a user attempts a review, the system must still complete a static-only review and must not throw an unhandled exception.
- Given a generated fix, when fix validation runs, the corrected code must parse without syntax errors before being displayed as validated.
- Given a generated test, when test validation runs, the test code must parse without syntax errors before being displayed.
- Given code longer than `MAX_CODE_CHARS`, when submitted, the system must reject it with a message stating the character limit and the actual length submitted.
- Given two issues (one static, one AI) referencing the same line range and same category, when fusion runs, the resulting report must show exactly one merged issue, not two.

---

# PART 29 — NON-FUNCTIONAL REQUIREMENTS

- **Reliability:** The app must never crash the Streamlit process on any single bad input or API failure (Part 23 governs every failure path).
- **Performance:** Meets targets in Part 24.1.
- **Security:** Meets requirements in Part 22; code is never executed by the app itself.
- **Maintainability:** Modular structure (Part 20) with one clear responsibility per module; no duplicated business logic between static/AI paths.
- **Scalability:** Not a primary MVP concern (single-user/local hackathon deployment), but the modular architecture (independent analyzers/chains, stateless orchestrator logic) does not preclude future multi-user deployment.
- **Usability:** Beginner-friendly language throughout the UI (Part 17), consistent with the audience defined in Part 2.
- **Accessibility:** Sufficient color contrast for severity badges (not color-alone indicators — use icons/labels alongside color); readable default font sizes.
- **Observability:** Stage-level timing and error logging (Part 21, Part 22.8) sufficient to debug pipeline issues without exposing sensitive data.
- **Portability:** Runs from a standard `requirements.txt`-based Python environment with no OS-specific dependencies.

---

# PART 30 — TEAM STRUCTURE

Suggested for a small (4–5 person) student/hackathon team:

| Role | Responsibilities | Key dependencies |
|---|---|---|
| **Team Lead / PM** | Owns this PRD, tracks scope (Part 4), coordinates milestones (Part 31), prepares the demo narrative (Part 35) | Depends on all other roles for status |
| **AI/LLM Engineer** | Owns `ai/`, `prompts/`, `fusion/` — prompt design, LangChain chains, hallucination mitigation, fusion logic | Needs the Issue Model (Part 11) finalized early by Backend/Core |
| **Backend/Core Engineer** | Owns `core/`, `input_handling/`, `analyzers/`, `remediation/`, `report/` — the deterministic backbone of the system | Needs to define the Issue Model first, since AI and UI both depend on it |
| **UI Engineer** | Owns `app/` — Streamlit layout, components, state management, UX polish | Needs stable Issue Model + Orchestrator interface to build against, can build with mocked data in parallel early on |
| **Testing/Evaluation Engineer** | Owns `tests/`, benchmark fixture curation (Part 25), evaluation harness (Part 27), regression runs before milestones | Needs fixtures early; can start curating benchmark data before the pipeline is complete |

---

# PART 31 — DEVELOPMENT WORKFLOW

## 31.1 Development phases
See Part 34 for the detailed phase breakdown.

## 31.2 Milestones
1. Issue Model + project skeleton agreed and merged.
2. Static-analysis-only pipeline working end-to-end (no AI yet) with a basic UI.
3. AI layer integrated for detection + explanation.
4. Fusion layer working, deduped and severity-scored.
5. Fix + test generation with validation working.
6. Scoring + full report + export working.
7. Benchmark evaluation run (Part 27) meeting the minimum bar (Part 27.4).
8. Demo rehearsal and polish.

## 31.3 Definition of Done (per feature)
A feature is "done" when: it matches its Part 5/6/etc. specification, it has at least one passing unit or integration test, it degrades gracefully per Part 23 for its relevant failure modes, and it has been reviewed by at least one other team member.

## 31.4 Integration process
Feature branches merge into a shared `develop` branch only after their module's tests pass; `develop` merges into `main` at each milestone.

## 31.5 Testing gates
No merge to `develop` without the relevant unit tests for that module passing; no milestone considered complete without the corresponding integration test/benchmark run passing.

---

# PART 32 — GIT/GITHUB WORKFLOW

- **Branch strategy:** `main` (stable/demo-ready) ← `develop` (integration) ← `feature/<short-description>` branches per task.
- **Commit conventions:** Conventional-commit style prefixes recommended: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`.
- **Pull requests:** Every feature branch merges via PR into `develop`, even on a small team — keeps a reviewable history and catches issues before integration.
- **Code review:** At least one other team member approves before merge; for a 4–5 person team this can be lightweight (a quick read-through), but not skipped.
- **Merge rules:** No direct commits to `main`; `main` only receives merges from `develop` at milestones.
- **Issue tracking:** GitHub Issues used to track each PRD requirement as a task, labeled by Part number/module for traceability back to this document.

---

# PART 33 — ANTIGRAVITY AGENT WORKFLOW

## 33.1 PRD as Source of Truth
This PRD is the authoritative specification for the AI Code Review Assistant. The Antigravity coding agent implementing this project must treat it as the single source of truth for scope, architecture, and behavior.

## 33.2 Required agent workflow
1. **Read the PRD** in full before writing any code.
2. **Understand requirements** — map each PRD Part to concrete implementation tasks.
3. **Identify ambiguities** — where this PRD is underspecified (e.g., exact Streamlit layout pixel details, exact prompt wording), the agent should make a reasonable, documented decision rather than stalling, but must flag it.
4. **Propose architecture** — confirm or refine the module breakdown in Part 18/20 before large-scale implementation.
5. **Create an implementation plan** — a task list mapped to the phases in Part 34.
6. **Break the work into tasks** — one task per module/function group, each independently testable.
7. **Implement incrementally** — following the phase order in Part 34, not building the AI layer before the Issue Model exists, for example.
8. **Run tests** after each meaningful increment (Part 26).
9. **Verify acceptance criteria** (Part 28) for each completed feature before marking it done.
10. **Report deviations from requirements** — if implementation reveals a PRD requirement is impractical, the agent must explicitly report the deviation and rationale, not silently do something different.
11. **Never silently change core requirements** — the Issue Model schema (Part 11), the severity system (Part 12), the hybrid fusion approach (Part 10), and the non-goals (Part 4.4) are considered core and must not be altered without explicit flagging and approval.

## 33.3 What the agent should NOT do without approval
- Introduce technologies outside the permitted stack (Part 19) without justification and flagging.
- Add model training/fine-tuning of any kind (violates Part 8.15/25.1).
- Remove or weaken any security/privacy behavior in Part 22.
- Change the Issue Model schema in a breaking way once other modules depend on it.
- Silently reduce MVP scope (Part 4.1) — if something in MVP proves infeasible in the available time, it must be explicitly reported, not quietly dropped.
- Auto-execute user-submitted code under any circumstance (Part 22.5 — this is an absolute rule, not a suggestion).

---

# PART 34 — IMPLEMENTATION PHASES

- **Phase 0 — Requirements:** Finalize this PRD, resolve ambiguities, confirm module ownership (Part 30).
- **Phase 1 — Project setup:** Repository, folder structure (Part 20), config scaffolding (Part 21), dependency installation.
- **Phase 2 — Issue Model & Core:** Implement Pydantic schemas (Part 11), severity rules (Part 12), scoring math (Part 15) — pure logic, no I/O.
- **Phase 3 — Input handling:** Validation, language detection, preprocessing (Part 5).
- **Phase 4 — Static analysis:** Implement each analyzer (Part 7) producing Issue objects; unit test each against fixtures.
- **Phase 5 — Minimal UI (static-only):** Streamlit input → static analysis → basic issue list, to have an early working demo skeleton.
- **Phase 6 — AI integration:** LangChain chains + prompts (Part 8, 9) for detection and explanation.
- **Phase 7 — Result fusion:** Merge/dedupe/confidence logic (Part 10).
- **Phase 8 — Fix generation:** Fix chain + validation (Part 13).
- **Phase 9 — Test generation:** Test chain + validation (Part 14).
- **Phase 10 — Full report & export:** Report builder, Markdown/JSON export (Part 16).
- **Phase 11 — Full UI:** All components from Part 17, wired to the complete pipeline.
- **Phase 12 — Error handling pass:** Explicitly implement and test every scenario in Part 23.
- **Phase 13 — Benchmark evaluation:** Curate fixtures (Part 25), run the evaluation harness (Part 27), tune prompts/thresholds against the minimum bar.
- **Phase 14 — Demo preparation:** Rehearse the demo script (Part 35), polish UI copy and edge-case handling.

---

# PART 35 — DEMO STRATEGY

## 35.1 Demo code sample
Prepare one deliberately problematic Python file containing, in a single coherent small program (e.g., a simple user-registration function), at least one example each of: a syntax error variant (shown first, then corrected to proceed), a SQL-injection-style security issue, a logic bug, a resource leak, a missing edge-case handling (e.g., empty input), and a readability/naming issue — chosen so the full breadth of categories in Part 6 is visible in one pass.

## 35.2 Demo flow
1. **Input:** Paste the sample code live.
2. **Analysis:** Click "Review Code," narrate the visible progress stepper (Part 17) so judges see the hybrid pipeline actually happening, not a black box.
3. **Static findings:** Point out that the security and syntax findings appeared instantly, before any AI call — demonstrating the deterministic layer.
4. **AI findings:** Show the logic-bug and edge-case findings that only the AI layer could have found, with their explanations.
5. **Severity:** Show the deterministic severity assignment, not an arbitrary AI label.
6. **Explanation:** Expand one issue's plain-language "why it matters."
7. **Suggested fix:** Show the before/after diff for the SQL injection issue specifically — highest impact.
8. **Corrected code:** Copy the corrected snippet, show it's minimal and targeted.
9. **Generated tests:** Show the generated `pytest` test for the edge-case bug, and note it was validated (Part 13.6/14.8), not just generated blindly.
10. **Score:** Show the dimension breakdown and explain the weighting rationale (Part 15.3) briefly.
11. **Final report:** Export to Markdown/JSON live to show the structured output is real and usable outside the app.

## 35.3 What makes this compelling to judges
Judges see: a real architectural decision (hybrid, not "LLM does everything"), visible determinism (static results appearing before AI), a fix that's actually validated rather than just plausible-looking text, a generated test tied directly to a specific bug, and a transparent, non-arbitrary scoring model — each of these directly counters the most common criticism of AI-hackathon-project demos ("it's just a ChatGPT wrapper").

---

# PART 36 — HACKATHON DIFFERENTIATION

## 36.1 Strengths of this design
- **Technical depth:** a real multi-stage pipeline (static + AI + fusion + validation), not a single API call.
- **AI usage:** LLM is used for what it's actually good at (reasoning, explanation, generation) and not used where it's unreliable (deterministic detection, severity assignment).
- **Engineering depth:** validated fixes, validated tests, structured schemas, deterministic scoring — shows software-engineering discipline, not just prompt-writing.
- **Practical usefulness:** solves a real, everyday developer pain point.
- **Novelty:** the fusion/validation layer and fix/test validation loop are less commonly demonstrated in hackathon "AI code reviewer" submissions, which typically stop at "AI explains the code."
- **Evaluation:** an actual precision/recall benchmark (Part 27) is a meaningfully more rigorous claim than "we tested it and it works."
- **Security:** dedicated static security scanning plus prompt-injection-aware design (Part 22.4).
- **Scalability:** modular architecture doesn't paint the team into a corner even though multi-user scaling is out of MVP scope.

## 36.2 Weaknesses of a basic AI code reviewer, and how this design addresses them
| Weakness of "paste code, ask ChatGPT" | How this design addresses it |
|---|---|
| Inconsistent output between runs | Structured schema + deterministic severity/scoring |
| No way to verify AI-suggested fixes | Fix validation loop (Part 13.6) |
| Hallucinated issues | Line-grounding + schema validation (Part 8.13) |
| No security-specific rigor | Dedicated `bandit`-based static security layer |
| No proof the code actually improved | Generated, validated tests tied to specific issues |
| Expensive/slow at scale | Cost-control principles throughout (Part 10.9, 24) |

## 36.3 Honest framing
This project is **not** automatically "winning" — its competitiveness depends on execution quality (does the fusion logic actually reduce noise in practice? are the generated fixes actually good?), demo polish, and how clearly the team can explain the architectural reasoning above under questioning.

---

# PART 37 — RISKS & MITIGATION

| Risk | Probability | Impact | Mitigation | Contingency |
|---|---|---|---|---|
| LLM hallucination | Medium | Medium | Grounding + schema validation (Part 8.13) | Fall back to static-only display for that finding |
| False positives (static or AI) | Medium | Low-Medium | Confidence system, corroboration logic, user "not relevant" dismissal | Document known noisy rules; tune thresholds pre-demo |
| False negatives | Medium | Medium | Hybrid coverage across categories (Part 6) | Explicitly document limitations (Part 38) rather than overclaiming |
| API dependency (OpenAI outage) | Low-Medium | High | Retry + static-only fallback (Part 23) | Rehearse demo with a "static-only mode" backup path |
| API cost overruns | Low | Medium | Scoped prompts, HF for auxiliary tasks, selective fix/test generation (Part 24) | Set a hard per-session/day budget alert during dev |
| Latency | Medium | Medium | Concurrent independent calls where possible (Part 24.8) | Show the progress stepper so perceived wait is acceptable |
| Unsupported languages | High (for non-Python) | Low (MVP is Python-first) | Clear scoping in Part 4.1/4.2 | AI-only best-effort mode with clear labeling |
| Incorrect AI-generated fixes | Medium | Medium-High | Fix validation loop (Part 13.6), user must explicitly apply | "Not automatically verified" labeling as a safety net |
| Security risks in the app itself | Low | High | Never execute submitted code (Part 22.5); no hardcoded secrets | Security review pass before demo |
| Prompt injection via code comments | Low-Medium | Medium | Data/instruction separation in prompts (Part 22.4) | Add adversarial fixture to benchmark set (Part 25) |
| Scope creep | High (common in hackathons) | Medium | Strict MVP/Advanced/Future split (Part 4) | Team Lead enforces phase gate (Part 31) before adding features |
| Integration problems between modules | Medium | Medium | Stable Issue Model contract defined early (Phase 2, Part 34) | Integration tests at each milestone (Part 31.5) |

---

# PART 38 — LIMITATIONS

Stated plainly, both internally and in the product's own UI copy where relevant:

- The AI cannot guarantee bug-free code — it identifies likely issues based on patterns and reasoning, not formal proof.
- Static analysis cannot understand business-specific rules that aren't expressed in the code itself.
- Generated fixes require human review before being trusted in production — validation (Part 13.6) confirms syntactic correctness and that the original static trigger no longer fires, not full behavioral equivalence in all cases.
- Security analysis in this tool is not a substitute for a professional security audit or penetration test — it catches known patterns, not novel or context-dependent vulnerabilities.
- The quality score (Part 15) reflects what's detectable from the submitted snippet alone, not the full system it's part of.
- Multi-file, cross-file, and whole-repository reasoning is out of scope for this version (Part 4.3) — findings are limited to what's visible within the submitted file/snippet.

---

# PART 39 — FUTURE SCOPE

Beyond MVP and Advanced Scope (Part 4), the following are documented as intentional future directions, not commitments for this build:

- GitHub / GitLab integration, including automated pull-request review comments.
- IDE extension (VS Code) for inline review as-you-type.
- CI/CD pipeline integration (fail a build on Critical findings).
- Repository-level, multi-file, dependency-aware analysis.
- Broader language support beyond Python/JS/TS/Java.
- Local/offline LLM support for fully private deployments.
- Team dashboards and historical code-quality tracking over time.
- Organization-level analytics (trends across many developers/repos).

---

# PART 40 — GLOSSARY

| Term | Simple explanation | Why it matters in this project |
|---|---|---|
| **AI (Artificial Intelligence)** | Software that can perform tasks — like understanding language or recognizing patterns — that normally require human-like judgment. | The whole "reasoning" half of this project is AI. |
| **Machine Learning** | A way of building AI systems by learning patterns from data rather than being explicitly programmed with rules for every case. | The models used here (OpenAI's, Hugging Face's) were built this way, even though this project doesn't train any itself. |
| **LLM (Large Language Model)** | A machine-learning model trained on huge amounts of text, able to read and generate human-like text, including code. | This is the core AI technology used for explanations, fixes, and tests (Part 8). |
| **Inference** | Using an already-trained model to process new input and get an output. | Everything this project does with AI models is inference — no training happens (Part 8.15). |
| **Training** | The process of teaching a model by showing it large amounts of data and adjusting it over time. | Explicitly **not** done in this project. |
| **Static Analysis** | Checking code for problems without running it, by examining its text/structure. | The deterministic half of the hybrid architecture (Part 7). |
| **AST (Abstract Syntax Tree)** | A tree-shaped representation of code's structure, used by tools to understand code the way a grammar diagram represents a sentence. | Used for parsing and structural checks (Part 7.6). |
| **Linter** | A tool that checks code against a set of style/quality rules. | Several static analyzers in this project are linters (`pyflakes`, `pycodestyle`). |
| **Vulnerability** | A weakness in code that could be exploited by an attacker. | Central to the Security category (Part 6.4) and `bandit` scanner (Part 7.5). |
| **False positive** | A tool reporting a problem that isn't actually a real problem. | A key quality metric for both static and AI findings (Part 27). |
| **False negative** | A real problem the tool fails to detect. | The other key quality metric (Part 27). |
| **Hallucination** | When an AI model generates something that sounds plausible but isn't actually true or grounded in the real input. | A major risk for the AI layer; specifically mitigated in Part 8.13. |
| **Prompt** | The text instructions given to an LLM to tell it what to do. | Every AI task in this system is driven by a carefully designed prompt (Part 8.10, 9.3). |
| **Prompt Engineering** | The practice of carefully designing prompts to get reliable, high-quality output from an LLM. | Applied throughout the `prompts/` module. |
| **RAG (Retrieval-Augmented Generation)** | A technique where a model is given retrieved external information (e.g., from a database) alongside the prompt to improve accuracy. Not used in this project's core pipeline, since the "external information" here is simply the static findings passed as context — a lighter form of context injection rather than full RAG. | Mentioned for completeness since it's a commonly confused adjacent term. |
| **Embeddings** | Numeric representations of text that capture meaning, allowing similarity comparisons. | Optionally used for duplicate-finding detection (Part 10.4, Advanced Scope). |
| **LangChain** | A framework for building pipelines of LLM calls, prompt templates, and structured output. | The orchestration backbone of the AI layer (Part 9). |
| **Hugging Face** | A platform/library providing access to many pretrained machine-learning models. | Used here for lightweight auxiliary tasks (Part 8.5, 8.7). |
| **Streamlit** | A Python framework for building interactive web apps quickly, without needing separate frontend code. | Powers the entire UI (Part 17). |
| **Severity** | How serious a given issue is. | Governed by a deterministic system, not free AI judgment (Part 12). |
| **Confidence** | How certain the system is that a given finding is correct. | Distinct from severity; affects fusion and display (Part 10.7). |
| **Fusion** | Combining static and AI findings into one unified, deduplicated result set. | The architectural core of the "hybrid" approach (Part 10). |
| **Diff / Patch** | A representation showing exactly what changed between two versions of text/code. | Used to display suggested fixes (Part 13.4-13.5). |
| **Cyclomatic Complexity** | A numeric measure of how many independent paths exist through a piece of code — higher means harder to understand and test. | Used by `radon` to inform Code Quality/Maintainability findings (Part 6.6-6.7, Part 7.5). |
| **CWE (Common Weakness Enumeration)** | A standardized catalog/ID system for known types of software security weaknesses. | Referenced in the Issue Model's `references` field for security findings (Part 11.2). |

---

*End of Product Requirements Document. This document is intended to be read in full by the implementing team and the Antigravity coding agent before implementation begins, per Part 33.*
