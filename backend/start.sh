#!/bin/bash
# Start script for NSS BloodLink backend server

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start uvicorn server
uvicorn app.main:app --reload --port 8000

