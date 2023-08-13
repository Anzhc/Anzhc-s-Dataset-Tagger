#!/bin/bash

# Check if venv directory exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate the virtual environment
source venv/bin/activate

# Check if requirements need to be installed
if ! pip install -r requirements.txt; then
    echo "Failed to install requirements. Exiting..."
    deactivate
    exit 1
fi

# Deactivate the virtual environment
deactivate
