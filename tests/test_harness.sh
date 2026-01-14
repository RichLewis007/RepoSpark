#!/usr/bin/env bash
# ============================================================================
# Test harness for quick-create-github-repo.sh
# Simulates and verifies behavior under different conditions
# Author: Rich Lewis - GitHub: @RichLewis007
# ============================================================================

set -euo pipefail

SCRIPT_PATH="/Users/rich/dev/python/repospark/repospark.sh"
TEST_DIR="/Users/rich/dev/python/repospark/tests/test-dir"
LOG_DIR="/Users/rich/dev/python/repospark/tests/log-dir"

# Ensure directories exist before any logging
mkdir -p "$LOG_DIR"
: > "$LOG_DIR/test.log"  # Clear or create main log file

log() {
  echo "[$(date +%T)] $1" | tee -a "$LOG_DIR/test.log"
}

run_test() {
  local test_name="$1"
  shift
  mkdir -p "$LOG_DIR"
  log "🧪 Running test: $test_name"
  "$@" | tee "$LOG_DIR/$test_name.log"
}

cleanup() {
  rm -rf "$TEST_DIR" > /dev/null 2>&1
  mkdir -p "$TEST_DIR"
}

# === Test 1: Empty directory triggers scaffold ===
cleanup
cd "$TEST_DIR"
run_test "empty_directory_scaffold" bash "$SCRIPT_PATH" <<< $'name1\ndesc1\n1\n1\n1\ntopic1\n1\nY\nY\nn\nn\n'
cd ..

# # === Test 2: Directory with files – no overwrite ===
# cleanup
# mkdir -p "$TEST_DIR"
# echo "Existing README" > "$TEST_DIR/README.md"
# cd "$TEST_DIR"
# run_test "nonempty_directory_no_overwrite" bash "$SCRIPT_PATH" <<< $'\ntest-repo-2\n\n2\n\n2\n\n\n2\nn\nn\n'
# cd ..

# === Finalize ===
log "✅ All tests completed. Check logs in $LOG_DIR"
