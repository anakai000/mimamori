#!/usr/bin/env python3
"""Interactive tool to (re)draw the door/bed/sofa/table regions and save
them to config/regions.yaml.

Usage:
    python3 scripts/edit_regions.py [--image path/to/snapshot.jpg]

If --image is omitted, it tries to capture a fresh frame from the camera —
which only works if nothing else (e.g. the monitoring daemon) is holding it
open. Stop it first with scripts/stop.sh, or pass --image instead.

Controls:
    Radio buttons   choose which region you're editing (door/bed/sofa/table)
    Left click      add a point to the selected region, at the click location
    Undo point      remove the last point added to the selected region
    Clear region    remove all points from the selected region
    Recapture       grab a fresh frame from the camera (replaces the preview)
    Save            write all four regions to config/regions.yaml

Each region needs at least 3 points before it can be saved.
"""

from __future__ import annotations

import argparse
import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox

import cv2
import numpy as np
from PIL import Image, ImageTk

from mimamori.camera import Camera
from mimamori.config import Config
from mimamori.regions import RegionSet

REGION_NAMES = RegionSet.REQUIRED  # ("door", "bed", "sofa", "table")
COLORS = {"door": "#ff4040", "bed": "#4080ff", "sofa": "#40c040", "table": "#e0c000"}

Point = list[float]
Regions = dict[str, list[Point]]


def capture_frame(size: tuple[int, int]) -> np.ndarray:
    camera = Camera(size=size)
    try:
        return camera.capture_frame()
    finally:
        camera.close()


def load_initial_regions(regions_file: str) -> Regions:
    try:
        regions = RegionSet.from_yaml(regions_file)
        return {name: [list(p) for p in regions[name].polygon] for name in REGION_NAMES}
    except (FileNotFoundError, ValueError):
        return {name: [] for name in REGION_NAMES}


def write_regions_yaml(path: str, regions: Regions, camera_size: tuple[int, int]) -> None:
    lines = [
        "# Region polygons in pixel coordinates, matching camera.size in config.yaml",
        f"# (currently {camera_size[0]}x{camera_size[1]}).",
        f"# Last edited via scripts/edit_regions.py on {datetime.now():%Y-%m-%d %H:%M}.",
        "",
    ]
    for name in REGION_NAMES:
        lines.append(f"{name}:")
        for x, y in regions[name]:
            lines.append(f"  - [{int(x)}, {int(y)}]")
        lines.append("")
    Path(path).write_text("\n".join(lines))


class RegionEditor:
    def __init__(
        self,
        root: tk.Tk,
        frame_bgr: np.ndarray,
        regions_file: str,
        camera_size: tuple[int, int],
        regions: Regions,
    ):
        self.root = root
        self.regions_file = regions_file
        self.camera_size = camera_size
        self.regions = regions
        self.active = tk.StringVar(value=REGION_NAMES[0])

        height, width = frame_bgr.shape[:2]
        self.photo_image = self._to_photo_image(frame_bgr)

        controls = tk.Frame(root)
        controls.pack(side=tk.TOP, fill=tk.X)
        for name in REGION_NAMES:
            tk.Radiobutton(
                controls,
                text=name,
                variable=self.active,
                value=name,
                fg=COLORS[name],
            ).pack(side=tk.LEFT, padx=4)
        tk.Button(controls, text="Undo point", command=self.undo).pack(side=tk.LEFT, padx=4)
        tk.Button(controls, text="Clear region", command=self.clear).pack(side=tk.LEFT, padx=4)
        tk.Button(controls, text="Recapture", command=self.recapture).pack(side=tk.LEFT, padx=4)
        tk.Button(controls, text="Save", command=self.save).pack(side=tk.LEFT, padx=4)
        tk.Label(controls, text="  click the image to add a point to the selected region").pack(side=tk.LEFT)

        self.canvas = tk.Canvas(root, width=width, height=height)
        self.canvas.pack()
        self.canvas_image_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_image)
        self.canvas.bind("<Button-1>", self.on_click)

        self.redraw()

    @staticmethod
    def _to_photo_image(frame_bgr: np.ndarray) -> ImageTk.PhotoImage:
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        return ImageTk.PhotoImage(Image.fromarray(rgb))

    def on_click(self, event: tk.Event) -> None:
        self.regions[self.active.get()].append([event.x, event.y])
        self.redraw()

    def undo(self) -> None:
        points = self.regions[self.active.get()]
        if points:
            points.pop()
            self.redraw()

    def clear(self) -> None:
        self.regions[self.active.get()] = []
        self.redraw()

    def recapture(self) -> None:
        try:
            frame_bgr = capture_frame(self.camera_size)
        except RuntimeError as exc:
            messagebox.showerror("Capture failed", str(exc))
            return
        self.photo_image = self._to_photo_image(frame_bgr)
        self.canvas.itemconfig(self.canvas_image_id, image=self.photo_image)
        self.redraw()

    def save(self) -> None:
        incomplete = [name for name, pts in self.regions.items() if len(pts) < 3]
        if incomplete:
            messagebox.showwarning("Not saved", f"These regions need >= 3 points: {', '.join(incomplete)}")
            return
        write_regions_yaml(self.regions_file, self.regions, self.camera_size)
        messagebox.showinfo("Saved", f"Saved {self.regions_file}")

    def redraw(self) -> None:
        self.canvas.delete("overlay")
        for name, points in self.regions.items():
            color = COLORS[name]
            for x, y in points:
                self.canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill=color, outline="", tags="overlay")
            if len(points) >= 3:
                flat = [c for point in points for c in point]
                self.canvas.create_polygon(flat, outline=color, fill="", width=2, tags="overlay")
            elif len(points) == 2:
                (x1, y1), (x2, y2) = points
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=2, tags="overlay")
            if points:
                self.canvas.create_text(
                    points[0][0],
                    points[0][1] - 10,
                    text=name,
                    fill=color,
                    anchor=tk.SW,
                    font=("TkDefaultFont", 12, "bold"),
                    tags="overlay",
                )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--image", type=Path, help="Use this image instead of capturing a new one")
    args = parser.parse_args()

    config = Config.load()

    if args.image:
        frame_bgr = cv2.imread(str(args.image))
        if frame_bgr is None:
            sys.exit(f"Could not read image: {args.image}")
    else:
        try:
            frame_bgr = capture_frame(config.camera.size)
        except RuntimeError as exc:
            sys.exit(
                f"Could not capture from camera ({exc}). If mimamori is running, stop it first "
                "(scripts/stop.sh) or pass --image an-existing-snapshot.jpg instead."
            )

    regions = load_initial_regions(config.regions_file)

    root = tk.Tk()
    root.title("mimamori region editor")
    RegionEditor(root, frame_bgr, config.regions_file, config.camera.size, regions)
    root.mainloop()


if __name__ == "__main__":
    main()
