#!/usr/bin/env python3
"""Live preview window: camera feed with region/detection overlay, updating
continuously. For visual testing/calibration only - runs the same
detect -> door -> events -> state pipeline as the daemon, but with no side
effects (no LINE alerts, no event_captures files).

Usage:
    python3 scripts/preview.py

Needs the camera free - stop the daemon first (scripts/stop.sh or
scripts/stop_service.sh) - and a display (the Pi's desktop, or `ssh -X`).
Close the window to quit.
"""

from __future__ import annotations

import time
import tkinter as tk

import cv2
import numpy as np
from PIL import Image, ImageTk

from mimamori.camera import Camera
from mimamori.config import Config
from mimamori.detector import PersonDetector
from mimamori.door import DoorStateDetector
from mimamori.events import EventDetector
from mimamori.regions import RegionSet
from mimamori.state_machine import StateMachine

REGION_COLORS_BGR = {
    "door": (0, 0, 255),
    "bed": (255, 0, 0),
    "sofa": (0, 255, 0),
    "table": (0, 255, 255),
}


def draw_overlay(frame: np.ndarray, regions: RegionSet, bboxes, door_state: str, state_label: str) -> np.ndarray:
    for name in RegionSet.REQUIRED:
        pts = np.array([[int(x), int(y)] for x, y in regions[name].polygon], dtype=np.int32)
        color = REGION_COLORS_BGR[name]
        cv2.polylines(frame, [pts], True, color, 2)
        cv2.putText(frame, name, tuple(pts[0]), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    for bbox in bboxes:
        top_left = (int(bbox.x1), int(bbox.y1))
        bottom_right = (int(bbox.x2), int(bbox.y2))
        cv2.rectangle(frame, top_left, bottom_right, (255, 255, 255), 2)
        cv2.putText(
            frame,
            f"{bbox.confidence:.2f}",
            (top_left[0], max(0, top_left[1] - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )

    banner = f"door={door_state}  state={state_label}"
    cv2.putText(frame, banner, (10, frame.shape[0] - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 4)
    cv2.putText(frame, banner, (10, frame.shape[0] - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    return frame


class PreviewApp:
    def __init__(self, root: tk.Tk, config: Config):
        self.root = root
        self.config = config
        self.regions = RegionSet.from_yaml(config.regions_file)
        self.detector = PersonDetector(
            config.detection.model_prototxt,
            config.detection.model_weights,
            config.detection.confidence_threshold,
        )
        self.door_detector = DoorStateDetector(
            self.regions["door"], config.door.closed_edge_density, config.door.open_edge_density
        )
        self.event_detector = EventDetector(self.regions, zone_debounce_frames=config.detection.zone_debounce_frames)
        self.state_machine = StateMachine(config.state_timeouts_seconds, now=time.monotonic())
        self.camera = Camera(size=config.camera.size, fps=config.camera.fps)

        width, height = config.camera.size
        self.canvas = tk.Canvas(root, width=width, height=height)
        self.canvas.pack()
        self.image_id: int | None = None
        self.photo_image: ImageTk.PhotoImage | None = None

        self.interval_ms = max(50, int(config.detection.process_interval_seconds * 1000))
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.tick()

    def tick(self) -> None:
        now = time.monotonic()
        frame = self.camera.capture_frame()
        bboxes = self.detector.detect(frame)
        door_state = self.door_detector.classify(frame)

        for event in self.event_detector.update(bboxes, door_state):
            self.state_machine.handle_event(event, now)
        self.state_machine.check_timeout(now)

        annotated = draw_overlay(frame.copy(), self.regions, bboxes, door_state, self.state_machine.state.value)
        rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
        self.photo_image = ImageTk.PhotoImage(Image.fromarray(rgb))
        if self.image_id is None:
            self.image_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_image)
        else:
            self.canvas.itemconfig(self.image_id, image=self.photo_image)

        self.root.after(self.interval_ms, self.tick)

    def on_close(self) -> None:
        self.camera.close()
        self.root.destroy()


def main() -> None:
    config = Config.load()
    root = tk.Tk()
    root.title("mimamori live preview")
    PreviewApp(root, config)
    root.mainloop()


if __name__ == "__main__":
    main()
