"""Region polygons and person/region overlap testing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Union

import cv2
import numpy as np
import yaml

Point = Tuple[float, float]


@dataclass(frozen=True)
class BBox:
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float = 1.0

    @property
    def center(self) -> Point:
        return ((self.x1 + self.x2) / 2.0, (self.y1 + self.y2) / 2.0)


@dataclass(frozen=True)
class Region:
    name: str
    polygon: Tuple[Point, ...]

    def contains_point(self, point: Point) -> bool:
        contour = np.array(self.polygon, dtype=np.float32).reshape((-1, 1, 2))
        return cv2.pointPolygonTest(contour, point, False) >= 0

    def overlaps(self, bbox: BBox) -> bool:
        return self.contains_point(bbox.center)


class RegionSet:
    """The four named regions the state machine and event detector rely on."""

    REQUIRED = ("door", "bed", "sofa", "table")

    def __init__(self, regions: Dict[str, Region]):
        missing = [name for name in self.REQUIRED if name not in regions]
        if missing:
            raise ValueError(f"Missing required region(s): {', '.join(missing)}")
        self._regions = regions

    @classmethod
    def from_yaml(cls, path: Union[str, Path]) -> "RegionSet":
        with open(path, "r") as f:
            raw = yaml.safe_load(f) or {}
        regions = {
            name: Region(name=name, polygon=tuple((float(x), float(y)) for x, y in points))
            for name, points in raw.items()
        }
        return cls(regions)

    def __getitem__(self, name: str) -> Region:
        return self._regions[name]

    def overlapping(self, bbox: BBox) -> List[str]:
        return [name for name, region in self._regions.items() if region.overlaps(bbox)]
