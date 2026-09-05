#!/usr/bin/env bash
# Starts the mimamori monitoring daemon in the background.
set -euo pipefail
cd "$(dirname "$0")/.."

PID_FILE="run/mimamori.pid"
LOG_FILE="run/mimamori.log"
mkdir -p run

if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "mimamori is already running (PID $(cat "$PID_FILE")). Use scripts/stop.sh first."
  exit 1
fi

source .venv/bin/activate
set -a
source .env
set +a

nohup python main.py > "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"
disown

echo "mimamori started (PID $(cat "$PID_FILE")), logging to $LOG_FILE"
echo "Tail logs with: tail -f $LOG_FILE"
