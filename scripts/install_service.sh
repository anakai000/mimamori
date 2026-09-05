#!/usr/bin/env bash
# Installs mimamori as a systemd service that starts automatically on boot,
# using the unit file checked into systemd/mimamori.service.
# Needs sudo — run this yourself, it's not meant to be run non-interactively.
set -euo pipefail
cd "$(dirname "$0")/.."
REPO_ROOT="$(pwd)"

if [ ! -d ".venv" ]; then
  echo "No .venv found in $REPO_ROOT - run the setup steps in README.md first." >&2
  exit 1
fi
if [ ! -f ".env" ]; then
  echo "No .env found in $REPO_ROOT - copy .env.example to .env and fill it in first." >&2
  exit 1
fi

if ! grep -q "WorkingDirectory=$REPO_ROOT$" systemd/mimamori.service; then
  echo "systemd/mimamori.service's WorkingDirectory doesn't match $REPO_ROOT." >&2
  echo "Edit systemd/mimamori.service's User/WorkingDirectory/EnvironmentFile/ExecStart paths to match this checkout, then re-run." >&2
  exit 1
fi

echo "Installing systemd/mimamori.service to /etc/systemd/system/ ..."
sudo cp systemd/mimamori.service /etc/systemd/system/mimamori.service
sudo systemctl daemon-reload
sudo systemctl enable --now mimamori.service

echo
echo "Installed and started. Useful commands:"
echo "  sudo systemctl status mimamori.service   # check it's running"
echo "  journalctl -u mimamori.service -f        # follow logs"
echo "  sudo systemctl disable --now mimamori.service   # stop it and undo autostart"
