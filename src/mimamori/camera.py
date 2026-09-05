"""picamera2 wrapper. Only importable/usable on the Raspberry Pi itself."""

from __future__ import annotations

from typing import Tuple

import cv2
import numpy as np

try:
    from picamera2 import Picamera2
except ImportError:  # pragma: no cover - picamera2 only exists on the Pi
    Picamera2 = None


class Camera:
    def __init__(self, size: Tuple[int, int] = (1296, 972), fps: float = 1.0):
        if Picamera2 is None:
            raise RuntimeError(
                "picamera2 is not available in this environment; Camera only runs on the Pi "
                "(install it via apt: python3-picamera2)."
            )
        self._picam2 = Picamera2()
        # Counterintuitively, picamera2/libcamera's "RGB888" format actually delivers
        # bytes in B,G,R memory order (i.e. what OpenCV/cv2 calls BGR) - "BGR888" gives
        # the reverse. Confirmed empirically 2026-09-05: requesting "BGR888" produced
        # visibly swapped R/B channels (e.g. skin rendered blue).
        #
        # FrameDurationLimits caps the sensor/ISP's own capture rate to `fps` - without
        # this, the sensor keeps running at its mode's native rate (e.g. ~46fps) even if
        # we only pull a frame occasionally, wasting power on frames we throw away.
        frame_duration_us = int(1_000_000 / fps)
        config = self._picam2.create_video_configuration(
            main={"size": size, "format": "RGB888"},
            controls={"FrameDurationLimits": (frame_duration_us, frame_duration_us)},
        )
        self._picam2.configure(config)
        self._picam2.start()

    def capture_frame(self) -> np.ndarray:
        return self._picam2.capture_array()

    def save_snapshot(self, frame: np.ndarray, path: str) -> None:
        cv2.imwrite(str(path), frame)

    def close(self) -> None:
        self._picam2.stop()
