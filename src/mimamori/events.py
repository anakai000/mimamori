"""Derives BED/SOFA/TABLE/RESTROOM *-IN and *-OUT events from per-frame
person detections, region polygons, and (for the restroom) door state."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Sequence

from .regions import BBox, Region, RegionSet

SIMPLE_ZONES = ("bed", "sofa", "table")

ZONE_EVENT_NAMES = {
    "bed": ("BED-IN", "BED-OUT"),
    "sofa": ("SOFA-IN", "SOFA-OUT"),
    "table": ("TABLE-IN", "TABLE-OUT"),
}


class RestroomPhase(str, Enum):
    OUTSIDE = "OUTSIDE"
    AT_DOOR_ENTERING = "AT_DOOR_ENTERING"
    INSIDE = "INSIDE"
    AT_DOOR_EXITING = "AT_DOOR_EXITING"


@dataclass
class RestroomTracker:
    """The camera can't see inside the restroom, so entry/exit is inferred
    from the person reaching the door followed by the door's open/closed
    state changing:

    OUTSIDE --person at door--> AT_DOOR_ENTERING --door closes, person gone--> INSIDE (emits RESTROOM-IN)
    INSIDE --door opens--> AT_DOOR_EXITING --person reappears at door--> OUTSIDE (emits RESTROOM-OUT)
    """

    door_region: Region
    phase: RestroomPhase = RestroomPhase.OUTSIDE

    def update(self, bboxes: Sequence[BBox], door_state: str) -> List[str]:
        person_at_door = any(self.door_region.overlaps(bbox) for bbox in bboxes)
        events: List[str] = []

        if self.phase is RestroomPhase.OUTSIDE:
            if person_at_door:
                self.phase = RestroomPhase.AT_DOOR_ENTERING
        elif self.phase is RestroomPhase.AT_DOOR_ENTERING:
            if door_state == "closed" and not person_at_door:
                self.phase = RestroomPhase.INSIDE
                events.append("RESTROOM-IN")
            elif door_state == "open" and not person_at_door:
                self.phase = RestroomPhase.OUTSIDE
        elif self.phase is RestroomPhase.INSIDE:
            if door_state == "open":
                self.phase = RestroomPhase.AT_DOOR_EXITING
        elif self.phase is RestroomPhase.AT_DOOR_EXITING:
            if person_at_door:
                self.phase = RestroomPhase.OUTSIDE
                events.append("RESTROOM-OUT")

        return events


@dataclass
class ZoneTracker:
    regions: RegionSet
    _occupied: Dict[str, bool] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        self._occupied = {zone: False for zone in SIMPLE_ZONES}

    def update(self, bboxes: Sequence[BBox]) -> List[str]:
        events: List[str] = []
        for zone in SIMPLE_ZONES:
            region = self.regions[zone]
            now_occupied = any(region.overlaps(bbox) for bbox in bboxes)
            was_occupied = self._occupied[zone]
            if now_occupied and not was_occupied:
                events.append(ZONE_EVENT_NAMES[zone][0])
            elif was_occupied and not now_occupied:
                events.append(ZONE_EVENT_NAMES[zone][1])
            self._occupied[zone] = now_occupied
        return events


class EventDetector:
    def __init__(self, regions: RegionSet):
        self.regions = regions
        self._zone_tracker = ZoneTracker(regions)
        self._restroom_tracker = RestroomTracker(regions["door"])

    def update(self, bboxes: Sequence[BBox], door_state: str) -> List[str]:
        events = self._zone_tracker.update(bboxes)
        events += self._restroom_tracker.update(bboxes, door_state)
        return events
