#!/bin/bash
### COMMON SETUP; DO NOT MODIFY ###
set -e

# --- CONFIGURE THIS SECTION ---
run_all_tests() {
  echo "Running all tests..."

  if [ -d "/eval_assets/tests" ]; then
    cd /eval_assets
    PROJECT_ROOT="/app"
    PARSE_SCRIPT="/eval_assets/parse_results"

    # Hidden validation tests resolve repository files relative to /eval_assets.
    # Bridge expected paths to injected code under /app.
    if [ -f "$PROJECT_ROOT/app.py" ] && [ ! -e "/eval_assets/app.py" ]; then
      ln -s "$PROJECT_ROOT/app.py" /eval_assets/app.py
    fi
    if [ -f "$PROJECT_ROOT/tracker.py" ] && [ ! -e "/eval_assets/tracker.py" ]; then
      ln -s "$PROJECT_ROOT/tracker.py" /eval_assets/tracker.py
    fi
    if [ -d "$PROJECT_ROOT/src" ] && [ ! -e "/eval_assets/src" ]; then
      ln -s "$PROJECT_ROOT/src" /eval_assets/src
    fi
    if [ -d "$PROJECT_ROOT/sample_data" ] && [ ! -e "/eval_assets/sample_data" ]; then
      ln -s "$PROJECT_ROOT/sample_data" /eval_assets/sample_data
    fi
  else
    cd /app 2>/dev/null || cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(pwd)"
    PARSE_SCRIPT="$PROJECT_ROOT/parsing.py"
  fi

  PYTHONPATH="$PROJECT_ROOT:$PROJECT_ROOT/src" python3 -m pytest -o addopts='' tests/ -v --tb=short --no-header \
    > /tmp/stdout.txt 2> /tmp/stderr.txt || true

  cat /tmp/stdout.txt
  cat /tmp/stderr.txt >&2

  python3 "$PARSE_SCRIPT" /tmp/stdout.txt /tmp/stderr.txt "$PROJECT_ROOT/results.json" || true
}
# --- END CONFIGURATION SECTION ---

### COMMON EXECUTION; DO NOT MODIFY ###
run_all_tests
