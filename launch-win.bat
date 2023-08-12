@echo off

REM Check if venv directory exists
if not exist venv (
    echo Virtual environment does not exist. Exiting...
    exit /b 1
)

REM Activate the virtual environment
call venv\Scripts\activate

REM Launch main.py
python src\main.py

REM Deactivate the virtual environment
call venv\Scripts\deactivate
