# Contributing Guidelines

Welcome to the **AI Code Review Assistant** project. To ensure smooth parallel development across our 4-person team, all contributors must strictly adhere to the rules outlined below.

---

## 1. Branch Strategy & Commit Rules

1. **No Direct Commits to `main`**: The `main` branch contains production-tested releases. Direct pushes are blocked.
2. **No Direct Commits to `develop`**: The `develop` branch is our shared integration branch. All work must arrive via Pull Requests.
3. **Use Feature Branches**: Create feature branches from `develop` using the format:
   `feature/<developer-name>-<short-description>`  
   *(e.g., `feature/static-bandit-wrapper`, `feature/ai-detection-chain`)*.
4. **Pull Requests Required**: Every feature branch must be merged via a Pull Request (PR) with at least one approval from a code owner.

---

## 2. Code & Architecture Integrity Rules

5. **Shared Issue Model Protection**: The domain schemas in `core/issue_model.py` form our **SHARED CONTRACT**. Do NOT modify fields, enums, validators, or serialization methods without explicit Team Lead approval.
6. **Module Isolation**: Respect code ownership bounds (see `.github/CODEOWNERS`). Do not edit another team member's module without coordination.
7. **Keep Business Logic Independent of UI**: Business logic (`core/`, `analyzers/`, `ai/`, `fusion/`, `remediation/`, `orchestrator/`) must NEVER import Streamlit (`import streamlit`). All UI code remains inside `app/`.
8. **Do Not Silently Alter Architecture**: Any proposed architectural change must be discussed and approved before implementation.
9. **Minimal Dependencies**: Do not introduce third-party libraries without justification and Team Lead approval.

---

## 3. Security & Safety Hard Rules

10. **Zero Secrets in Code**: Never commit API keys, tokens, or passwords. All credentials must be loaded via `services/config_service.py` from `.env`.
11. **NEVER Execute User Code**: Submitted user code must be treated strictly as un-executable text data. Never use `exec()`, `eval()`, `compile()` for execution, or subprocess evaluation on submitted user snippets.

---

## 4. Testing & Pull Request Workflow

12. **Tests are Mandatory**: Every implementation change or bug fix must include corresponding unit tests in `tests/unit/`.
13. **Run `pytest` Before Creating a PR**: Verify that all unit tests pass locally before opening a PR:
    ```bash
    pytest -v
    ```
14. **PR Description Requirements**: Every PR must include:
    - **What changed**: Summary of code additions/modifications.
    - **Why it changed**: Technical motivation or task reference.
    - **Tests performed**: Command executed and verification outcome.
    - **Known limitations**: Any remaining edge cases or deferred work.
15. **Prefer Small Changes**: Keep PRs focused, granular, and independently testable.
