#!/bin/bash
# Database migration runner script
# Usage: ./scripts/migrate.sh [command]
#   Commands: run, status, create <name>

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Use the project's venv Python directly (not system Python)
if [ -f ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
elif [ -f ".venv/bin/python3" ]; then
    PYTHON=".venv/bin/python3"
else
    echo "Error: No .venv found. Create one with: python3 -m venv .venv && .venv/bin/pip install -e ."
    exit 1
fi

# Load environment (optional, ignore errors)
if [ -f ".env" ] && [ -r ".env" ]; then
    set -a
    source .env 2>/dev/null || true
    set +a
fi

# Run migration command
"$PYTHON" -m db.migrate "${@:-run}"
