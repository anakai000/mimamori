#!/usr/bin/env bash
# Turns the live preview OFF: closes scripts/preview.py and restarts
# whichever mimamori instance preview_on.sh had stopped (systemd service, or
# scripts/start.sh). May need your sudo password if it was the systemd
# service.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -f run/preview.pid ] && kill -0 "$(cat run/preview.pid)" 2>/dev/null; then
  echo "Stopping live preview (PID $(cat run/preview.pid)) ..."
  kill "$(cat run/preview.pid)"
  rm -f run/preview.pid
else
  echo "Live preview doesn't appear to be running."
fi

MARKER="run/preview_stopped_which.txt"
if [ -f "$MARKER" ]; then
  WHICH="$(cat "$MARKER")"
  rm -f "$MARKER"
  case "$WHICH" in
    systemd)
      echo "Restarting systemd-managed mimamori.service ..."
      sudo systemctl start mimamori.service
      ;;
    manual)
      echo "Restarting mimamori (scripts/start.sh) ..."
      ./scripts/start.sh
      ;;
    *)
      echo "Nothing to restart (mimamori wasn't running when preview_on.sh was used)."
      ;;
  esac
else
  echo "No record of what to restart - was scripts/preview_on.sh used to turn preview on?"
fi
