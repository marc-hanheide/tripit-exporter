#!/bin/bash
# Run the TripIt API integration test with actual credentials

# Setup virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate || { echo "Error: Failed to activate virtual environment"; exit 1; }

# Run the integration test directly
echo "Running TripIt API integration test..."
PYTHONPATH=. python tests/test_tripit_integration.py

# Or alternatively, run with pytest
# echo "Running TripIt API integration test with pytest..."
# python -m pytest tests/test_tripit_integration.py -v
