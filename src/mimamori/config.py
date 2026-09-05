"""Loads config.yaml plus environment-variable secrets into a Config object."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Tuple

import yaml

from .state_machine import State

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "config.yaml"


@dataclass
class CameraConfig:
    size: Tuple[int, int] = (1296, 972)
    # Caps the sensor/ISP's own capture rate (see camera.py) - lower means less
    # power draw. 1fps is plenty for a slow-moving night-routine use case.
    fps: float = 1.0


@dataclass
class DetectionConfig:
    model_prototxt: str = "models/MobileNetSSD_deploy.prototxt"
    model_weights: str = "models/MobileNetSSD_deploy.caffemodel"
    confidence_threshold: float = 0.5
    process_interval_seconds: float = 1.0
    # How many consecutive frames a bed/sofa/table occupancy change must hold
    # before it's confirmed as a real *-IN/*-OUT event, to filter out
    # single-frame detector flicker (e.g. a bbox jittering across the region
    # edge). At process_interval_seconds=1.0 this default (4) means ~4s.
    zone_debounce_frames: int = 4


@dataclass
class DoorConfig:
    closed_edge_density: float = 5.0
    open_edge_density: float = 25.0


@dataclass
class NotifierConfig:
    snapshot_path: str = "/tmp/alert.jpg"
    snapshot_public_url_base: Optional[str] = None


@dataclass
class DebugConfig:
    # When set, a snapshot is saved here every time a *-IN/*-OUT event fires,
    # named "<YYMMDDHHMMSS>_<EVENT>.jpg" (e.g. 260905143005_TABLE-IN.jpg).
    # For testing/tuning region calibration, not needed in normal operation.
    event_capture_dir: Optional[str] = None


DEFAULT_STATE_TIMEOUTS_SECONDS: Dict[State, Optional[float]] = {
    State.OTHER: 180.0,
    State.RESTROOM: 600.0,
    State.SOFA: 3600.0,
    State.TABLE: 3600.0,
    State.BED: None,
}


@dataclass
class Config:
    regions_file: str = "config/regions.yaml"
    camera: CameraConfig = field(default_factory=CameraConfig)
    detection: DetectionConfig = field(default_factory=DetectionConfig)
    door: DoorConfig = field(default_factory=DoorConfig)
    notifier: NotifierConfig = field(default_factory=NotifierConfig)
    debug: DebugConfig = field(default_factory=DebugConfig)
    state_timeouts_seconds: Dict[State, Optional[float]] = field(
        default_factory=lambda: dict(DEFAULT_STATE_TIMEOUTS_SECONDS)
    )
    line_channel_access_token: Optional[str] = None
    line_to_user_id: Optional[str] = None

    @classmethod
    def load(cls, path: "Path | str" = DEFAULT_CONFIG_PATH) -> "Config":
        with open(path, "r") as f:
            raw = yaml.safe_load(f) or {}

        camera_raw = raw.get("camera", {})
        detection_raw = raw.get("detection", {})
        door_raw = raw.get("door", {})
        notifier_raw = raw.get("notifier", {})
        debug_raw = raw.get("debug", {})
        timeouts_raw = raw.get("state_timeouts_seconds", {})

        state_timeouts_seconds = dict(DEFAULT_STATE_TIMEOUTS_SECONDS)
        for name, seconds in timeouts_raw.items():
            state_timeouts_seconds[State(name)] = float(seconds) if seconds is not None else None

        defaults = cls()
        return cls(
            regions_file=raw.get("regions_file", defaults.regions_file),
            camera=CameraConfig(
                size=tuple(camera_raw.get("size", defaults.camera.size)),
                fps=camera_raw.get("fps", defaults.camera.fps),
            ),
            detection=DetectionConfig(
                model_prototxt=detection_raw.get("model_prototxt", defaults.detection.model_prototxt),
                model_weights=detection_raw.get("model_weights", defaults.detection.model_weights),
                confidence_threshold=detection_raw.get(
                    "confidence_threshold", defaults.detection.confidence_threshold
                ),
                process_interval_seconds=detection_raw.get(
                    "process_interval_seconds", defaults.detection.process_interval_seconds
                ),
                zone_debounce_frames=detection_raw.get(
                    "zone_debounce_frames", defaults.detection.zone_debounce_frames
                ),
            ),
            door=DoorConfig(
                closed_edge_density=door_raw.get("closed_edge_density", defaults.door.closed_edge_density),
                open_edge_density=door_raw.get("open_edge_density", defaults.door.open_edge_density),
            ),
            notifier=NotifierConfig(
                snapshot_path=notifier_raw.get("snapshot_path", defaults.notifier.snapshot_path),
                snapshot_public_url_base=notifier_raw.get(
                    "snapshot_public_url_base", os.environ.get("SNAPSHOT_PUBLIC_URL_BASE")
                ),
            ),
            debug=DebugConfig(
                event_capture_dir=debug_raw.get("event_capture_dir", defaults.debug.event_capture_dir),
            ),
            state_timeouts_seconds=state_timeouts_seconds,
            line_channel_access_token=os.environ.get("LINE_CHANNEL_ACCESS_TOKEN"),
            line_to_user_id=os.environ.get("LINE_TO_USER_ID"),
        )
