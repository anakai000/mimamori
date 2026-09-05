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
    def __init__(self, size: Tuple[int, int] = (1296, 972)):
        if Picamera2 is None:
            raise RuntimeError(
                "picamera2 is not available in this environment; Camera only runs on the Pi "
                "(install it via apt: python3-picamera2)."
            )
        self._picam2 = Picamera2()
        config = self._picam2.create_video_configuration(main={"size": size, "format": "BGR888"})
        self._picam2.configure(config)
        self._picam2.start()

    def capture_frame(self) -> np.ndarray:
        return self._picam2.capture_array()

    def save_snapshot(self, frame: np.ndarray, path: str) -> None:
        cv2.imwrite(str(path), frame)

    def close(self) -> None:
        self._picam2.stop()
