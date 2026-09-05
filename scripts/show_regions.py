#!/usr/bin/env python3
"""Draws the regions configured in config/regions.yaml onto a snapshot.

By default captures a fresh frame from the camera (only works if nothing
else, e.g. the monitoring daemon, is holding it open — stop it first with
scripts/stop.sh, or pass --image instead) and saves the annotated result to
regions_preview.jpg (or --output).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

from mimamori.camera import Camera
from mimamori.config import Config
from mimamori.regions import RegionSet

COLORS = {
    "door": (0, 0, 255),
    "bed": (255, 0, 0),
    "sofa": (0, 255, 0),
    "table": (0, 255, 255),
}


def capture_frame(size: tuple[int, int]) -> np.ndarray:
    camera = Camera(size=size)
    try:
        return camera.capture_frame()
    finally:
        camera.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--image", type=Path, help="Use this image instead of capturing a new one")
    parser.add_argument("--output", type=Path, default=Path("regions_preview.jpg"))
    args = parser.parse_args()

    config = Config.load()
    regions = RegionSet.from_yaml(config.regions_file)

    if args.image:
        frame = cv2.imread(str(args.image))
        if frame is None:
            sys.exit(f"Could not read image: {args.image}")
    else:
        try:
            frame = capture_frame(config.camera.size)
        except RuntimeError as exc:
            sys.exit(
                f"Could not capture from camera ({exc}). If mimamori is running, stop it first "
                "(scripts/stop.sh) or pass --image an-existing-snapshot.jpg instead."
            )

    for name in RegionSet.REQUIRED:
        pts = np.array([[int(x), int(y)] for x, y in regions[name].polygon], dtype=np.int32)
        color = COLORS[name]
        cv2.polylines(frame, [pts], True, color, 3)
        cv2.putText(frame, name, tuple(pts[0]), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)

    cv2.imwrite(str(args.output), frame)
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
