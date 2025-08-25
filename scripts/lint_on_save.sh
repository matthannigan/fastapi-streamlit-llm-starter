#!/bin/bash
# scripts/lint_on_save.sh
FILE="$1"

echo "🔍 Linting $FILE..."

# Run flake8
if ! python -m flake8 "$FILE"; then
    echo "❌ Flake8 found issues in $FILE"
fi

# Run mypy if it's a backend file
if [[ "$FILE" == backend/* ]]; then
    cd backend
    if ! python -m mypy "${FILE#backend/}" --ignore-missing-imports; then
        echo "❌ MyPy found type issues in $FILE"
    fi
fi

echo "✅ Linting complete for $FILE"