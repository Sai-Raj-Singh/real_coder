#!/bin/bash
### COMMON SETUP; DO NOT MODIFY ###
set -e

# --- CONFIGURE THIS SECTION ---
# Replace this with your command to run all tests
run_all_tests() {
  echo "Running all tests..."

  SCRIPT_PATH="$(readlink -f "$0" 2>/dev/null || echo "$0")"
  SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"

  # Detect the directory that contains the tests. In the Docker
  # validation harness this is /eval_assets; for local runs it's the
  # directory containing this script.
  if [ -d /eval_assets/tests ]; then
    TESTS_ROOT=/eval_assets
  else
    TESTS_ROOT="$SCRIPT_DIR"
  fi

  # Detect the directory that contains the solution code.
  # In the validation harness this is /app; for local runs it's the
  # directory containing this script.
  if [ -f /app/package.json ]; then
    CODE_DIR=/app
  else
    CODE_DIR="$SCRIPT_DIR"
  fi

  cd "$TESTS_ROOT"
  POLL_PROJECT_DIR="$CODE_DIR" python3 -m pytest tests/ -v --tb=short -rN 2>&1 || true
}
# --- END CONFIGURATION SECTION ---

### COMMON EXECUTION; DO NOT MODIFY ###
run_all_tests
