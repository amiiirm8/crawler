#!/bin/bash

# Navigate to the root directory of the project
cd "$(dirname "$0")/.."

# Activate the virtual environment if exists
if [ -d "venv" ]; then
  source venv/bin/activate
fi

# Navigate to the script directory
cd scripts/

# Run the Python script
python3 web_crawler.py
