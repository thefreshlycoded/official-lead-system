#!/usr/bin/env bash
set -euo pipefail

# Usage: bash script/run_upwork_scraper.sh [--hours=24] [--pages=3] [--require-login]

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="$ROOT_DIR/log/upwork_scraper.log"

# Load env files if present (ignored by git per .gitignore)
if [[ -f "$ROOT_DIR/.env" ]]; then
  set -a
  source "$ROOT_DIR/.env"
  set +a
fi
if [[ -f "$ROOT_DIR/.env.local" ]]; then
  set -a
  source "$ROOT_DIR/.env.local"
  set +a
fi

HOURS=24
PAGES=3
REQUIRE_LOGIN=true
for arg in "$@"; do
  case "$arg" in
    --hours=*) HOURS="${arg#*=}" ;;
    --pages=*) PAGES="${arg#*=}" ;;
    --require-login) REQUIRE_LOGIN=true ;;
    --no-login) REQUIRE_LOGIN=false ;;
  esac
done

cd "$ROOT_DIR"

{
  echo "=== RUN START $(date)"
  echo "[Runner] DATABASE_URL=${DATABASE_URL:-}"
  echo "[Runner] SCRAPER_ID=${SCRAPER_ID:-}"
  echo "[Runner] CHROME_BIN=${CHROME_BIN:-}"
} >"$LOG_FILE"

# Find a Python interpreter with pip
PY_CMD=""
CANDIDATES=(
  "$ROOT_DIR/upwork_ai/upwork_scraper_env/bin/python"
  "$(command -v python3 || true)"
  "/opt/homebrew/bin/python3"
  "/usr/local/bin/python3"
)
for C in "${CANDIDATES[@]}"; do
  if [[ -n "$C" && -x "$C" ]]; then
    if "$C" -m pip --version >/dev/null 2>&1; then
      PY_CMD="$C"
      break
    fi
  fi
done
if [[ -z "$PY_CMD" ]]; then
  echo "[Runner] ERROR: No suitable python3 with pip found" | tee -a "$LOG_FILE"
  exit 1
fi

{
  echo "[Runner] Using PY_CMD=$PY_CMD"
  "$PY_CMD" --version | sed 's/^/[Runner] /'
} | tee -a "$LOG_FILE"

# Ensure Python deps are installed (upgrade quietly but log)
"$PY_CMD" -m pip install -U -r "$ROOT_DIR/upwork_ai/requirements.txt" 2>&1 | tee -a "$LOG_FILE"

# Launch the scraper (unbuffered output for immediate logging)
echo "[Runner] Launching scraper with args: --hours=${HOURS} --pages=${PAGES}" | tee -a "$LOG_FILE"
export PYTHONUNBUFFERED=1
# NOTE: REQUIRE_CONTINUE=false allows auto-detection of login instead of waiting for Rails UI
export REQUIRE_CONTINUE="false"

# Anti-detection & stealth settings
export UNDETECTED_CHROMEDRIVER=1
export DISABLE_BLINK_FEATURES=AutomationControlled
export CHROMEDRIVER_DISABLE_DEV_SHM_USAGE=1
export RANDOM_DELAY_MIN=2
export RANDOM_DELAY_MAX=8

# Prefer Google Chrome app if CHROME_BIN not set
if [[ -z "${CHROME_BIN:-}" ]]; then
  for CAND in \
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    "/Applications/Google Chrome 2.app/Contents/MacOS/Google Chrome" \
    "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary" \
    "/Applications/Chromium.app/Contents/MacOS/Chromium"; do
    if [[ -x "$CAND" ]]; then
      export CHROME_BIN="$CAND"
      echo "[Runner] Auto-detected CHROME_BIN=$CHROME_BIN" | tee -a "$LOG_FILE"
      break
    fi
  done
fi

# Show user what will happen
if [[ "$REQUIRE_LOGIN" == "true" ]]; then
  echo "[Runner] 🔐 LOGIN REQUIRED: Browser will open - you must login to Upwork first!" | tee -a "$LOG_FILE"
  echo "[Runner] ⚠️  STEALTH MODE ENABLED: Using undetected-chromedriver" | tee -a "$LOG_FILE"
  echo "[Runner] ✓ After login, scraper will AUTO-CONTINUE automatically." | tee -a "$LOG_FILE"
  echo "[Runner] ℹ️  Just login in the browser - no buttons to click!" | tee -a "$LOG_FILE"
fi

"$PY_CMD" -u "$ROOT_DIR/upwork_ai/run_upwork_latest.py" "--hours=${HOURS}" "--pages=${PAGES}" 2>&1 | tee -a "$LOG_FILE"
