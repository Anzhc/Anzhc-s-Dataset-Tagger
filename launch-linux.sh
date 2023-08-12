#!/bin/bash

# Check if venv directory exists
if [ ! -d "venv" ]; then
    echo "Virtual environment does not exist. Exiting..."
    exit 1
fi

# Activate the virtual environment
source venv/bin/activate

# Launch main.py
python src/main.py

# Deactivate the virtual environment
deactivate
