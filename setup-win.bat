@echo off

REM Check if venv directory exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate the virtual environment
call venv\Scripts\activate

REM Check if requirements need to be installed
pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install requirements. Exiting...
    call venv\Scripts\deactivate
    exit /b 1
)

REM Deactivate the virtual environment
call venv\Scripts\deactivate
