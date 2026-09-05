# mimamori

Night-routine monitoring daemon for a Raspberry Pi 4. Watches a camera feed
for a person moving between the bed, sofa, table, and restroom, and pushes a
LINE alert (with a snapshot) if someone stays somewhere unexpectedly long —
e.g. a fall in the restroom.

Full requirements and design decisions are in [SPEC.md](SPEC.md). For a
step-by-step configuration walkthrough in Japanese, see
[docs/設定ガイド.md](docs/設定ガイド.md).

## Project layout

- `src/mimamori/` — the package: region/overlap logic, person detection,
  door state, event derivation, the state machine, camera + LINE I/O, and
  the app that wires it all together.
- `config/config.yaml`, `config/regions.yaml` — runtime configuration and
  region polygons (placeholders — see "Calibration" below).
- `main.py` — daemon entrypoint.
- `systemd/mimamori.service` — unit file to run this on boot.
- `models/` — where the detection model weights go (not committed).
- `scripts/` — operational helper scripts (see "Helper scripts" below).
- `tests/` — unit tests (state machine, region overlap, event derivation,
  door classification, detection post-processing, LINE payload building).

## Setup (on the Pi)

```bash
sudo apt install python3-picamera2 python3-gpiozero   # if not already present
python3 -m venv --system-site-packages .venv           # inherits picamera2/gpiozero
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .                                       # so `import mimamori` works
```

Then follow [models/README.md](models/README.md) to obtain the detection
model weights and to calibrate `config/regions.yaml` and the door edge-density
thresholds in `config/config.yaml`.

Copy `.env.example` to `.env` and fill in `LINE_CHANNEL_ACCESS_TOKEN` and
`LINE_TO_USER_ID` (from your LINE Messaging API channel). `SNAPSHOT_PUBLIC_URL_BASE`
is optional — without it, alerts are text-only (see SPEC.md's Notification
Requirements for why).

## Running

```bash
source .venv/bin/activate
set -a; source .env; set +a
python main.py
```

Or install as a systemd service, so it starts automatically on boot:

```bash
scripts/install_service.sh
```

(equivalent to `sudo cp systemd/mimamori.service /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable --now mimamori.service`)

## Helper scripts

- `scripts/install_service.sh` — installs `systemd/mimamori.service` so the
  daemon starts automatically on boot (needs sudo; run it yourself, see
  "Running" above).
- `scripts/start.sh` — starts the daemon in the background (`run/mimamori.pid`,
  logs to `run/mimamori.log`). Fails if it thinks it's already running.
  For ad-hoc/manual runs — once `install_service.sh` is set up, systemd starts
  it on boot instead and this isn't needed day-to-day.
- `scripts/stop.sh` — stops it via the PID file (only for instances started
  with `scripts/start.sh` — for the systemd-managed one, use
  `scripts/stop_service.sh` instead).
- `scripts/stop_service.sh` — stops the systemd-managed daemon (needs sudo;
  run it yourself). Leaves it enabled, so it starts again on next boot — pass
  that off to `sudo systemctl disable --now mimamori.service` if you want to
  stop that too.
- `scripts/show_regions.py [--image PATH] [--output PATH]` — draws the
  configured door/bed/sofa/table regions onto a snapshot (captures a fresh
  one from the camera by default — stop the daemon first, or pass `--image`)
  and saves it (default `regions_preview.jpg`) so you can eyeball whether the
  regions still line up.
- `scripts/edit_regions.py [--image PATH]` — a small Tkinter GUI (needs a
  display: run it on the Pi's desktop, or over `ssh -X`) to click out new
  door/bed/sofa/table polygons on a live or still snapshot and save them
  straight to `config/regions.yaml`. Needs `python3-pil.imagetk`
  (`sudo apt install python3-pil.imagetk`) in addition to the base setup.

Both region tools need the camera free, so stop the daemon first (or pass
`--image` an existing snapshot) — only one process can hold `picamera2` open
at a time.

## Testing

This dev environment has no Pi camera attached, so tests exercise the state
machine, region/detection/door logic, and LINE payload building against
synthetic inputs — not the actual `picamera2` capture path. Run them with:

```bash
source .venv/bin/activate
python -m pytest
```
