"""Restroom sliding-door open/closed classification.

The lens has no IR-cut filter (see SPEC.md), so color can't be relied on at
night; instead we classify the door's region by how textured/edgy it looks,
via Canny edge density. This needs two reference values calibrated on-device
(config.yaml -> door.closed_edge_density / open_edge_density): capture a frame
with the door closed and one with it open, and record each edge density.
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .regions import Region


def edge_density(roi: np.ndarray) -> float:
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if roi.ndim == 3 else roi
    edges = cv2.Canny(gray, 50, 150)
    return float(edges.mean())


def _roi(frame: np.ndarray, region: Region) -> np.ndarray:
    xs = [p[0] for p in region.polygon]
    ys = [p[1] for p in region.polygon]
    x1, x2 = int(min(xs)), int(max(xs))
    y1, y2 = int(min(ys)), int(max(ys))
    return frame[y1:y2, x1:x2]


@dataclass
class DoorStateDetector:
    region: Region
    closed_edge_density: float
    open_edge_density: float

    def classify(self, frame: np.ndarray) -> str:
        return self.classify_density(edge_density(_roi(frame, self.region)))

    def classify_density(self, density: float) -> str:
        closed_dist = abs(density - self.closed_edge_density)
        open_dist = abs(density - self.open_edge_density)
        return "closed" if closed_dist <= open_dist else "open"
