@echo off
setlocal EnableDelayedExpansion
title AI Code Review Assistant - Pipeline Runner

echo ================================================================
echo               AI CODE REVIEW ASSISTANT RUNNER
echo ================================================================
echo.

:: ------------------------------------------------------------------
:: Step 1: Git Synchronization and Rebasing
:: ------------------------------------------------------------------
echo [STEP 1/5] Synchronizing repository and checking upstream...
git rev-parse --is-inside-work-tree >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo Fetching latest updates from origin...
    git fetch origin >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        set HAS_LOCAL_CHANGES=0
        for /f "tokens=*" %%i in ('git status --porcelain 2^>nul') do (
            set HAS_LOCAL_CHANGES=1
        )
        if "!HAS_LOCAL_CHANGES!"=="1" (
            echo [INFO] Uncommitted changes detected in local working tree.
            echo [INFO] Skipping auto-rebase to preserve your working changes.
        ) else (
            echo Rebasing on origin/main...
            git rebase origin/main
            if %ERRORLEVEL% neq 0 (
                echo [WARNING] Git rebase encountered issues or merge conflicts.
                echo [WARNING] Resolve conflicts or run 'git rebase --abort'.
            ) else (
                echo [OK] Git rebase completed cleanly.
            )
        )
    ) else (
        echo [INFO] Remote origin unreachable or offline. Continuing locally.
    )
) else (
    echo [INFO] Git repository not detected. Skipping rebase step.
)
echo.

:: ------------------------------------------------------------------
:: Step 2: Environment Configuration (.env)
:: ------------------------------------------------------------------
echo [STEP 2/5] Checking environment configuration...
if not exist ".env" (
    if exist ".env.example" (
        echo Initializing .env from .env.example...
        copy .env.example .env >nul
        echo [OK] Created .env configuration file.
    ) else (
        echo [WARNING] No .env.example found to initialize .env.
    )
) else (
    echo [OK] .env configuration file found.
)
echo.

:: ------------------------------------------------------------------
:: Step 3: Python Virtual Environment and Dependencies
:: ------------------------------------------------------------------
echo [STEP 3/5] Verifying Python virtual environment and dependencies...
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed or not found in system PATH.
    pause
    exit /b 1
)

if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment: venv...
    python -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Checking and installing dependencies from requirements.txt...
pip install -r requirements.txt --quiet
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Dependency installation returned a non-zero status.
) else (
    echo [OK] Dependencies verified and up to date.
)
echo.

:: ------------------------------------------------------------------
:: Step 4: Backend Pipeline Verification and Unit Tests
:: ------------------------------------------------------------------
echo [STEP 4/5] Running backend static analysis pipeline tests...
python -m pytest -q
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Backend tests failed. Halting before launching frontend.
    pause
    exit /b 1
)
echo [OK] All backend tests passed successfully.
echo.

:: ------------------------------------------------------------------
:: Step 5: Frontend UI Launch (Streamlit)
:: ------------------------------------------------------------------
echo [STEP 5/5] Launching Frontend Interface...
if exist "app\main.py" (
    echo Starting Streamlit application on http://localhost:8501 ...
    streamlit run app\main.py
) else (
    echo [INFO] app\main.py not yet created [Frontend UI scheduled in Issue #13].
    echo [OK] Backend and input-handling pipeline are verified and operational.
)

echo.
echo ================================================================
echo                   EXECUTION COMPLETED
echo ================================================================
pause
