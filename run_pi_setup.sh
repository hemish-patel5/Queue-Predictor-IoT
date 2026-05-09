#!/usr/bin/env bash
# Raspberry Pi setup helper
# Run this on the Raspberry Pi before starting services to install system packages
# and Python dependencies needed for the camera (YOLOv8, OpenCV, MQTT, etc.).

set -euo pipefail

echo "This script will install system packages and Python dependencies for the Queue Predictor on a Raspberry Pi."
echo "Run with: sudo ./run_pi_setup.sh"

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo)."; exit 1
fi

apt update && apt upgrade -y

# Install OS-level packages required by OpenCV/ultralytics and cameras
apt install -y python3-venv python3-pip build-essential libatlas-base-dev libjpeg-dev libopenjp2-7-dev \
  libavcodec-dev libavformat-dev libswscale-dev v4l-utils ffmpeg libssl-dev

# Create venv in project root if missing
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"
pip install --upgrade pip

# Install Python requirements
if [ -f "$PROJECT_DIR/backend/requirements-updated.txt" ]; then
  pip install -r "$PROJECT_DIR/backend/requirements-updated.txt"
else
  pip install -r "$PROJECT_DIR/backend/requirements.txt"
fi

# ultralytics sometimes needs extra dependencies; ensure it's installed
pip install ultralytics

echo "✔ Raspberry Pi setup complete. You can now run ./run_all.sh to start services."
