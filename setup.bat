@echo off
REM Muruthi MVP Setup Script for Windows

echo.
echo ============================================================
echo Muruthi - Life Operating System
echo Setup Script for Windows
echo ============================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

echo [1/3] Checking Python version...
python --version
echo.

REM Install dependencies
echo [2/3] Installing Python dependencies...
echo This may take a few minutes on first run...
echo.

pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install requirements
    pause
    exit /b 1
)
echo.

REM Run verification
echo [3/3] Running verification...
echo.
python verify.py
if errorlevel 1 (
    echo.
    echo WARNING: Some checks failed, but the MVP should still work
    echo Make sure ActivityWatch is running before launching the app
)

echo.
echo ============================================================
echo Setup complete!
echo ============================================================
echo.
echo Next steps:
echo.
echo 1. Download and run ActivityWatch:
echo    https://activitywatch.readthedocs.io/
echo.
echo 2. Test the complete pipeline:
echo    python test_pipeline.py
echo.
echo 3. Launch the dashboard:
echo    python -m app.main
echo.
pause
