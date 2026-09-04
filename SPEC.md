
# Mimamori Night-Routine Monitoring System Specification

## Objective
Build a Python-based background monitoring daemon for a Raspberry Pi 4/5. 
The system uses a bedside PIR motion sensor and an LDR light sensor to monitor night restroom visits and send alert snapshots via the LINE Messaging API.

## Hardware & Environment
- **Platform:** Raspberry Pi (Raspberry Pi OS 64-bit)
- **Library:** `gpiozero` for handling GPIO interrupts
- **Sensors:**
  - Bedside PIR Sensor: GPIO 17
  - Restroom Door PIR Sensor: GPIO 27
  - Light Sensor (LDR Digital Output): GPIO 22
- **Camera:** Pi NoIR Camera Module v2/v3 (accessed via `picamera2` or `OpenCV`)

## State Machine Logic
1. **IDLE (Night Mode):** Active from 22:00 to 06:00.
2. **BED_EXIT:** Triggered when Bedside PIR detects motion AND LDR reports room is DARK.
   - Start timer `T_exit`.
3. **IN_RESTROOM:** Triggered when Restroom PIR detects motion within 2 minutes of BED_EXIT.
4. **BED_RETURN:** Triggered when Bedside PIR detects motion again after IN_RESTROOM state.
5. **ANOMALY DETECTED (Alert Triggers):**
   - **Fall / Inactivity Timeout:** State remains in `BED_EXIT` or `IN_RESTROOM` for longer than 10 minutes without return motion.
   - **Light Left On:** `BED_RETURN` completed, but LDR detects light remains ON for > 3 minutes.

## Notification Requirements
- Use `line-bot-sdk` (Python) to send alerts.
- **Alert Payload:** Text message describing the anomaly + camera snapshot image saved to `/tmp/alert.jpg` and sent via LINE API push message.

## Task for Claude Code
1. Create a clean Python project structure (`src/`, `config/`, `tests/`).
2. Write `main.py` implementing the state machine and GPIO listeners asynchronously.
3. Write a service module `line_notifier.py` to dispatch LINE push messages.
4. Provide a `systemd` service unit file (`mimamori.service`) so this daemon runs on Pi boot.
