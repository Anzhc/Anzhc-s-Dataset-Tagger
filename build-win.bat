@echo off

REM Check if venv directory exists
if not exist venv (
    echo Virtual environment does not exist. Exiting...
    exit /b 1
)

REM Activate the virtual environment
call venv\Scripts\activate

nuitka --standalone --onefile --enable-plugin=pyqt5 --follow-imports --output-filename=Anzhc-s-Dataset-Tagger --disable-console .\src\main.py

REM Deactivate the virtual environment
call venv\Scripts\deactivate
