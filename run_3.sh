#!/bin/bash
# ─────────────────────────────────────────────
#  Run Sensors Only — Gas, Sound, Humiture
# ─────────────────────────────────────────────

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$PROJECT_DIR/logs"
PID_FILE="$PROJECT_DIR/.sensor_pids"

mkdir -p "$LOG_DIR"

# ── Colours ──────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# ── Stop mode ─────────────────────────────────
if [ "$1" == "stop" ]; then
  if [ ! -f "$PID_FILE" ]; then
    echo -e "${YELLOW}No running sensors found.${NC}"
    exit 0
  fi
  echo -e "${YELLOW}Stopping all sensors...${NC}"
  while read -r pid; do
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" && echo "  Stopped PID $pid"
    fi
  done < "$PID_FILE"
  rm -f "$PID_FILE"
  echo -e "${GREEN}All sensors stopped.${NC}"
  exit 0
fi

# ── Activate virtualenv ───────────────────────
if [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
  source "$PROJECT_DIR/venv/bin/activate"
  echo -e "${GREEN}✔ Virtual environment activated${NC}"
else
  echo -e "${YELLOW}⚠ No venv found — using system Python.${NC}"
fi

# ── Check .env ────────────────────────────────
if [ ! -f "$PROJECT_DIR/.env" ]; then
  echo -e "${RED}✘ .env file missing.${NC}"
  exit 1
fi
echo -e "${GREEN}✔ .env found${NC}"

# ── Helper: launch a process in background ────
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

# ── Clear old PIDs ────────────────────────────
if [ -f "$PID_FILE" ]; then
  echo -e "${YELLOW}⚠ Sensors may already be running. Run ./run_sensors.sh stop first.${NC}"
  exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Starting Sensors"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

launch "gas"      "python hardware/drivers/co2_sensor.py"
launch "sound"    "python hardware/drivers/sound_sensor.py"
launch "humiture" "python hardware/drivers/Humiture_Sensor.py"
launch "camera"   "python hardware/drivers/pi_camera_logic.py"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "  ${GREEN}All sensors running!${NC}"
echo ""
echo "  Logs     →  ./logs/"
echo "  Stop all →  ./run_sensors.sh stop"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"