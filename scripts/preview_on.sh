#!/usr/bin/env bash
# Turns the live preview ON: frees the camera by stopping whichever mimamori
# instance is currently running (systemd service, or the scripts/start.sh
# one), remembers which so preview_off.sh can restore it, then launches
# scripts/preview.py in the background. May need your sudo password if the
# systemd service is running.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -f run/preview.pid ] && kill -0 "$(cat run/preview.pid)" 2>/dev/null; then
  echo "Live preview is already running (PID $(cat run/preview.pid))."
  exit 1
fi

mkdir -p run
MARKER="run/preview_stopped_which.txt"
STOPPED="none"

if systemctl is-active --quiet mimamori.service 2>/dev/null; then
  echo "Stopping systemd-managed mimamori.service ..."
  sudo systemctl stop mimamori.service
  STOPPED="systemd"
elif [ -f run/mimamori.pid ] && kill -0 "$(cat run/mimamori.pid)" 2>/dev/null; then
  echo "Stopping manually-started mimamori (scripts/start.sh) ..."
  ./scripts/stop.sh
  STOPPED="manual"
else
  echo "mimamori doesn't appear to be running; nothing to stop."
fi
echo "$STOPPED" > "$MARKER"

source .venv/bin/activate
nohup python3 scripts/preview.py > run/preview.log 2>&1 &
echo $! > run/preview.pid
disown

echo "Live preview started (PID $(cat run/preview.pid)) - a window should appear on your display."
echo "Run scripts/preview_off.sh when done to close it and resume monitoring."
