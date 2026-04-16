#!/bin/bash
### COMMON SETUP; DO NOT MODIFY ###
set -e

# --- CONFIGURE THIS SECTION ---
# Replace this with your command to run all tests
run_all_tests() {
  # Keep cargo's exit code visible through the sed pipe below so `set -e`
  # still aborts on test-binary failure the same way a bare `cargo test`
  # would.
  set -o pipefail

  # Pick a working directory. If /app already holds a real project
  # (Cargo.toml + non-empty src/lib.rs), run tests there. Otherwise the
  # BEFORE phase is active and /app is bare — build a stub project in a
  # scratch dir so we never touch /app and keep it clean for the later
  # codebase.zip extraction performed by the validator.
  workdir=/app
  if [ ! -f /app/Cargo.toml ] || [ ! -s /app/src/lib.rs ]; then
    workdir=/tmp/text_diff_stub
    mkdir -p "$workdir/src"
    cat > "$workdir/Cargo.toml" <<'CARGO_TOML_EOF'
[package]
name = "text_diff"
version = "0.1.0"
edition = "2021"

[lib]
path = "src/lib.rs"

[dependencies]
CARGO_TOML_EOF
    cat > "$workdir/src/lib.rs" <<'LIB_RS_EOF'
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Change {
    Equal { old_line: usize, new_line: usize, content: String },
    Delete { old_line: usize, content: String },
    Insert { new_line: usize, content: String },
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum WordChange {
    Equal(String),
    Delete(String),
    Insert(String),
}

pub fn diff(_: &str, _: &str) -> Vec<Change> { unimplemented!() }
pub fn unified_diff(_: &str, _: &str, _: usize) -> String { unimplemented!() }
pub fn side_by_side(_: &str, _: &str, _: usize) -> String { unimplemented!() }
pub fn word_diff(_: &str, _: &str) -> Vec<WordChange> { unimplemented!() }
pub fn similarity(_: &str, _: &str) -> f64 { unimplemented!() }
pub fn diff_reader(
    _: &mut dyn std::io::BufRead,
    _: &mut dyn std::io::BufRead,
) -> std::io::Result<Vec<Change>> { unimplemented!() }
LIB_RS_EOF
  fi

  mkdir -p "$workdir/tests"
  if [ -d /eval_assets/tests ]; then
    find /eval_assets/tests -maxdepth 4 -name "*.rs" -exec cp {} "$workdir/tests/" \; 2>/dev/null || true
  fi

  cd "$workdir"
  # Rewrite libtest's hardcoded "ok" to "passed" for human-readable output.
  # parsing.py accepts both spellings, so the captured stdout still parses.
  cargo test --no-fail-fast --color=never 2>&1 \
    | sed -E 's/(\.\.\. )ok$/\1passed/; s/^(test result: )ok\./\1passed./'
}
# --- END CONFIGURATION SECTION ---

### COMMON EXECUTION; DO NOT MODIFY ###
run_all_tests
