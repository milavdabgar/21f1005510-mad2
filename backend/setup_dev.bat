@echo off
echo Setting up development environment...

REM Check for Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is required but not installed.
    echo Please install Python from:
    echo https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    exit /b 1
)

REM Remove existing virtual environment if it exists
if exist .venv (
    echo Removing existing virtual environment...
    rmdir /s /q .venv
)

REM Create new virtual environment
echo Creating virtual environment...
python -m venv .venv

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install development requirements
echo Installing development requirements...
pip install -r requirements.txt

REM Install pre-commit hooks if .pre-commit-config.yaml exists
if exist .pre-commit-config.yaml (
    echo Installing pre-commit hooks...
    pip install pre-commit
    pre-commit install
)

echo Development environment setup complete!
echo To activate the virtual environment in the future, run:
echo .venv\Scripts\activate.bat
