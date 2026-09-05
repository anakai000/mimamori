#!/usr/bin/env bash
# Stops the systemd-managed mimamori daemon (installed via install_service.sh).
# Needs sudo — run this yourself.
#
# Note: this only stops it for now. It stays *enabled*, so it will start
# again on the next boot. To also stop it from auto-starting on boot, run:
#   sudo systemctl disable --now mimamori.service
set -euo pipefail

sudo systemctl stop mimamori.service
echo "mimamori.service stopped."
echo "(it's still enabled and will start again on next boot — run"
echo " 'sudo systemctl disable --now mimamori.service' instead to also stop that)"
