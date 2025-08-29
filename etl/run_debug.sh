#!/bin/bash

# Debug Script for Supabase Upsert Error
# This script runs the debug program to isolate the upsert error

echo "🚀 Starting Supabase Upsert Debug Session"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "debug_workflow_upsert.py" ]; then
    echo "❌ Error: Please run this script from the etl/ directory"
    echo "Current directory: $(pwd)"
    exit 1
fi

# Check if Python virtual environment exists
if [ -d "venv" ]; then
    echo "📦 Activating Python virtual environment..."
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "⚠️  Warning: No virtual environment found. Using system Python."
fi

# Check if required packages are installed
echo "🔍 Checking required packages..."
python3 -c "import supabase" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Error: supabase package not found. Installing..."
    pip install supabase
fi

python3 -c "import dotenv" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Error: python-dotenv package not found. Installing..."
    pip install python-dotenv
fi

echo "✅ Required packages checked"

# Run the debug program
echo "🔍 Running debug program..."
echo "=========================================="

python3 debug_workflow_upsert.py

echo "=========================================="
echo "🏁 Debug session completed"

# Deactivate virtual environment if it was activated
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
    echo "✅ Virtual environment deactivated"
fi
