#!/usr/bin/env bash
# Stops the mimamori monitoring daemon started via scripts/start.sh.
set -euo pipefail
cd "$(dirname "$0")/.."

PID_FILE="run/mimamori.pid"

if [ ! -f "$PID_FILE" ]; then
  echo "No PID file at $PID_FILE - is mimamori running (maybe started another way, e.g. systemd)?"
  exit 1
fi

PID="$(cat "$PID_FILE")"

if ! kill -0 "$PID" 2>/dev/null; then
  echo "Process $PID isn't running; removing stale PID file."
  rm -f "$PID_FILE"
  exit 1
fi

kill "$PID"
for _ in $(seq 1 10); do
  if ! kill -0 "$PID" 2>/dev/null; then
    rm -f "$PID_FILE"
    echo "mimamori stopped."
    exit 0
  fi
  sleep 0.5
done

echo "Process $PID did not exit in time; sending SIGKILL."
kill -9 "$PID" 2>/dev/null || true
rm -f "$PID_FILE"
