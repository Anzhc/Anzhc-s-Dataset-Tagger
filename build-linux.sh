#!/bin/bash

# Check if venv directory exists
if [ ! -d "venv" ]; then
    echo "Virtual environment does not exist. Exiting..."
    exit 1
fi

# Activate the virtual environment
source venv/bin/activate

nuitka --standalone --onefile --enable-plugin=pyqt5 --follow-imports --output-filename=Anzhc-s-Dataset-Tagger --disable-console ./src/main.py

# Deactivate the virtual environment
deactivate
