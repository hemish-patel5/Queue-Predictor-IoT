# ─────────────────────────────────────────────────────────────
#  Queue & Comfort Predictor — Start All Services
#  Team Mandarin · COMP816
#
#  Usage:
#    chmod +x run_all.sh   (first time only)
#    ./run_all.sh          (start everything)
#    ./run_all.sh stop     (kill all background processes)
# ─────────────────────────────────────────────────────────────

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$PROJECT_DIR/logs"
PID_FILE="$PROJECT_DIR/.pids"

mkdir -p "$LOG_DIR"

# ── Colours ──────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# ── Stop mode ────────────────────────────────────────────────
if [ "$1" == "stop" ]; then
  if [ ! -f "$PID_FILE" ]; then
    echo -e "${YELLOW}No running processes found.${NC}"
    exit 0
  fi
  echo -e "${YELLOW}Stopping all Queue Predictor processes...${NC}"
  while read -r pid; do
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" && echo "  Stopped PID $pid"
    fi
  done < "$PID_FILE"
  rm -f "$PID_FILE"
  echo -e "${GREEN}All processes stopped.${NC}"
  exit 0
fi

# ── Activate virtualenv ───────────────────────────────────────
if [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
  source "$PROJECT_DIR/venv/bin/activate"
  echo -e "${GREEN}✔ Virtual environment activated${NC}"
else
  echo -e "${YELLOW}⚠ No venv found — using system Python. Run: python3 -m venv venv && pip install -r backend/requirements.txt${NC}"
fi

# ── Check .env ───────────────────────────────────────────────
if [ ! -f "$PROJECT_DIR/.env" ]; then
  echo -e "${RED}✘ .env file missing. Copy .env.example → .env and add your API key.${NC}"
  exit 1
fi
echo -e "${GREEN}✔ .env found${NC}"

# ── Helper: launch a process in background ───────────────────
launch() {
  local name="$1"
  local cmd="$2"
  local log="$LOG_DIR/${name}.log"

  echo -e "  Starting ${YELLOW}${name}${NC}..."
  cd "$PROJECT_DIR"
  eval "$cmd" >> "$log" 2>&1 &
  local pid=$!
  echo "$pid" >> "$PID_FILE"
  echo -e "  ${GREEN}✔ ${name}${NC} → PID $pid  (log: logs/${name}.log)"
  sleep 0.5
}

# ── Clear old PIDs ───────────────────────────────────────────
rm -f "$PID_FILE"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Queue & Comfort Predictor — Starting"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ── 1. Sensor Drivers ────────────────────────────────────────
echo "[ Sensor Drivers ]"
launch "dht22"    "python hardware/drivers/dht22_driver.py"
launch "co2"      "python hardware/drivers/co2_driver.py"
launch "sound"    "python hardware/drivers/sound_driver.py"
launch "pir"      "python hardware/drivers/pir_counter.py"
launch "vision"   "python hardware/vision/people_counter.py"

echo ""

# ── 2. Sensor Fusion ─────────────────────────────────────────
echo "[ Backend ]"
launch "fusion"   "python backend/logic/sensor_fusion.py"
sleep 1  # give fusion a moment to write fused_state.json first

# ── 3. LLM Advisory ──────────────────────────────────────────
launch "advisory" "python backend/services/llm_advisory.py"

# ── 4. API Server ─────────────────────────────────────────────
launch "api"      "python backend/services/api_server.py"

echo ""

# ── 5. Frontend ───────────────────────────────────────────────
echo "[ Frontend ]"
launch "dashboard" "python3 -m http.server 8080 --directory frontend"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "  ${GREEN}All services running!${NC}"
echo ""
echo "  Dashboard  →  http://localhost:8080"
echo "  API state  →  http://localhost:5000/api/state"
echo "  API advise →  http://localhost:5000/api/advisory"
echo ""
echo "  Logs       →  ./logs/"
echo "  Stop all   →  ./run_all.sh stop"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"