
# Mimamori Night-Routine Monitoring System Specification

## Objective
Build a Python-based background monitoring daemon for a Raspberry Pi 4.
The system uses a camera to monitor restroom visits and other night-routine activity, detecting
anomalies (e.g. a fall, or an unusually long stay in a room) and sending alert snapshots via the
LINE Messaging API. This will later be extended with a bedside PIR motion sensor.

## Decisions log (clarified with user on 2026-09-04)
- **Detection approach:** lightweight ML person detector (COCO "person" class) run per-frame,
  region membership determined by bounding-box overlap with configured region polygons.
  Implementation choice: OpenCV DNN with a MobileNet-SSD model — no PyTorch/ultralytics
  dependency, modest memory footprint, and fast enough on Pi 4 CPU for a slow-changing state
  machine like this one. Configurable so the model path/backend can be swapped later.
- **Camera:** actual hardware confirmed via `rpicam-hello --list-cameras` as an OV5647 sensor
  (Raspberry Pi Camera Module v1.3, 5MP, CSI-connected), with the IR-cut filter physically
  removed from the lens by the user — making it NoIR-equivalent (IR-sensitive) for night use.
  Implications for software:
  - An IR illuminator (e.g. 850/940nm IR LEDs) is required for night-time visibility; not in
    scope to build, assumed to be present in the room.
  - Night frames will be near-monochrome/off-color; daytime frames will look washed/pink since
    there's no IR-cut filter. Person detection should tolerate this — the MobileNet-SSD model
    is grayscale-tolerant, but if accuracy suffers under IR lighting, converting frames to
    grayscale before inference is the fallback.
  - Auto white balance should be set to a fixed/manual mode rather than an outdoor/indoor AWB
    preset, since libcamera's color-based AWB algorithms assume a normal IR-cut-filtered sensor.
  Accessed via `picamera2` (libcamera backend). Detection will run against the
  `1296x972 @ 46.34fps` mode (best balance of field-of-view vs. frame rate for a CPU-bound
  detector; the `640x480 @ 62.5fps` mode is the fallback if that's still too slow).
- **Regions & door state:** defined in a static, hand-authored YAML config
  (`config/regions.yaml`) as pixel-coordinate polygons, calibrated by eye against a saved
  snapshot. No interactive calibration tool for v1. Door open/closed is inferred from
  pixel-difference/edge-change within the door's own region.
- **Operating hours:** monitoring runs 24/7 (no night-only window). This may be revisited later.
- **Anomaly rule:** each state gets its own configurable max-duration threshold; exceeding it
  raises ANOMALY. Defaults: `OTHER` 3 min, `RESTROOM` 10 min, `SOFA`/`TABLE` 60 min, `BED` no
  timeout (sleep is expected to be long). Thresholds live in config, not hardcoded.
- **Credentials:** LINE channel access token and target user ID are read from environment
  variables (e.g. `LINE_CHANNEL_ACCESS_TOKEN`, `LINE_TO_USER_ID`), never committed to the repo.
- **Testing (this dev environment has no Pi/camera attached):** unit tests exercise the state
  machine and region-overlap logic against synthetic frames / fabricated bounding boxes; the
  `line_notifier` module is tested with the LINE client mocked. Camera capture itself
  (`picamera2`) is not exercised here and must be verified on-device.

## Hardware & Environment
- **Platform:** Raspberry Pi 4 (Raspberry Pi OS 64-bit)
- **Library:** `gpiozero` for handling GPIO interrupts (for the PIR sensor, added later)
- **Sensors (not wired up yet, reserved GPIO pins):**
  - Bedside PIR Sensor: GPIO 17 (later)
  - Restroom Door PIR Sensor: GPIO 27 (later)
  - Light Sensor (LDR Digital Output): GPIO 22 (later)
- **Camera:** OV5647-based Camera Module (v1.3), CSI-connected, accessed via `picamera2`

## Camera event detection
Prerequisite — four regions are defined ahead of time as polygons in `config/regions.yaml`:
1. The sliding door to the restroom
2. The bed
3. The sofa
4. The table

Events, derived once per processed frame from the current person bounding box(es) and region
polygons:
- **RESTROOM-IN**: person bounding box overlaps the restroom door region, and the door region
  is subsequently detected as closed with the person no longer visible outside it.
- **RESTROOM-OUT**: the door region is detected as open, followed by a person bounding box
  appearing overlapping the door region from the inside.
- **BED-IN** / **BED-OUT**: person bounding box starts/stops overlapping the bed region.
- **SOFA-IN** / **SOFA-OUT**: person bounding box starts/stops overlapping the sofa region.
- **TABLE-IN** / **TABLE-OUT**: person bounding box starts/stops overlapping the table region.
- **ALERT**: internal event raised whenever ANOMALY is entered; triggers a LINE push
  notification with a snapshot.

## State Machine Logic
States: `BED`, `SOFA`, `TABLE`, `RESTROOM`, `OTHER`, `ANOMALY`.

1. `BED` — entered on `BED-IN`.
2. `SOFA` — entered on `SOFA-IN`.
3. `TABLE` — entered on `TABLE-IN`.
4. `RESTROOM` — entered on `RESTROOM-IN`.
5. `OTHER` — entered on any `*-OUT` event (person is in transit, not in a tracked zone).
6. `ANOMALY` — entered when the current state's max-duration threshold is exceeded
   (per-state thresholds; see Decisions log). Raises an `ALERT` event. Cleared back to `OTHER`
   once a person is next seen in any known zone.

## Platform
Reference `konnyaku256/mimamori` as prior art for on-Pi camera capture/streaming plumbing
(WebRTC via Momo, v4l2loopback multiplexing). It has no person-detection or state-machine
logic of its own — this project builds that layer from scratch and only borrows capture
conventions where useful.

## Notification Requirements
- Use `line-bot-sdk` (Python) to send alerts via the LINE Messaging API (push message), not the
  deprecated LINE Notify service.
- **Alert Payload:** text message describing the anomaly (state + duration) + a camera snapshot
  saved to `/tmp/alert.jpg` and sent as part of the LINE push message.
- Credentials via environment variables (see Decisions log).

## Task for Claude Code
1. Create a clean Python project structure (`src/`, `config/`, `tests/`).
2. Write `main.py` implementing the state machine and camera handling asynchronously.
3. Write a detection module for person detection + region-overlap event derivation.
4. Write a service module `line_notifier.py` to dispatch LINE push messages.
5. Provide a `systemd` service unit file (`mimamori.service`) so this daemon runs on Pi boot.
6. Write unit tests per the Testing decision above.
