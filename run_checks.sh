#!/bin/bash
# run_checks.sh — run everything; exit non-zero on any failure.
# Usage: ./run_checks.sh          (backend + frontend)
#        ./run_checks.sh backend  (backend only)
set -e
cd "$(dirname "$0")"

echo "1/3 Backend test suite (unit + API smoke, mock mode)..."
python -m pytest tests/ -q

if [ "$1" != "backend" ]; then
  echo "2/3 Frontend type check..."
  (cd frontend && npx tsc --noEmit)

  echo "3/3 Frontend production build..."
  (cd frontend && npm run build --silent)
else
  echo "2/3 + 3/3 skipped (backend-only mode)"
fi

echo "ALL CHECKS PASSED ✅"
