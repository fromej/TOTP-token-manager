#!/bin/bash

# Ensure we're in the right directory
PROJECT_DIR="$(dirname "$0")"
cd "$PROJECT_DIR"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
uv pip install -r backend/requirements.txt

# Run the application
echo "Starting TOTP Manager..."
cd backend
uvicorn main:app --reload
