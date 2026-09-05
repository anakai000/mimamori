from mimamori.events import EventDetector, RestroomPhase, RestroomTracker, ZoneTracker
from mimamori.regions import BBox, Region, RegionSet


def square_region(name: str, x1: float, y1: float, x2: float, y2: float) -> Region:
    return Region(name=name, polygon=((x1, y1), (x2, y1), (x2, y2), (x1, y2)))


def make_regions() -> RegionSet:
    return RegionSet(
        {
            "door": square_region("door", 0, 0, 50, 50),
            "bed": square_region("bed", 100, 100, 200, 200),
            "sofa": square_region("sofa", 300, 300, 400, 400),
            "table": square_region("table", 500, 500, 600, 600),
        }
    )


def bbox_in(region: Region) -> BBox:
    x, y = region.polygon[0]
    x2, y2 = region.polygon[2]
    return BBox(x1=x + 1, y1=y + 1, x2=x2 - 1, y2=y2 - 1)


def far_away_bbox() -> BBox:
    return BBox(x1=900, y1=900, x2=950, y2=950)


def test_zone_tracker_emits_in_then_out():
    regions = make_regions()
    tracker = ZoneTracker(regions)
    bed_box = bbox_in(regions["bed"])

    assert tracker.update([bed_box]) == ["BED-IN"]
    assert tracker.update([bed_box]) == []
    assert tracker.update([far_away_bbox()]) == ["BED-OUT"]


def test_restroom_tracker_full_entry_exit_cycle():
    regions = make_regions()
    tracker = RestroomTracker(regions["door"])
    at_door = bbox_in(regions["door"])
    away = far_away_bbox()

    assert tracker.update([], "open") == []
    assert tracker.phase is RestroomPhase.OUTSIDE

    assert tracker.update([at_door], "open") == []
    assert tracker.phase is RestroomPhase.AT_DOOR_ENTERING

    assert tracker.update([away], "closed") == ["RESTROOM-IN"]
    assert tracker.phase is RestroomPhase.INSIDE

    assert tracker.update([away], "open") == []
    assert tracker.phase is RestroomPhase.AT_DOOR_EXITING

    assert tracker.update([at_door], "open") == ["RESTROOM-OUT"]
    assert tracker.phase is RestroomPhase.OUTSIDE


def test_restroom_tracker_false_start_resets_to_outside():
    regions = make_regions()
    tracker = RestroomTracker(regions["door"])
    at_door = bbox_in(regions["door"])
    away = far_away_bbox()

    tracker.update([at_door], "open")
    assert tracker.phase is RestroomPhase.AT_DOOR_ENTERING

    # Person steps away from the door without the door ever closing.
    events = tracker.update([away], "open")
    assert events == []
    assert tracker.phase is RestroomPhase.OUTSIDE


def test_event_detector_combines_zone_and_restroom_events():
    regions = make_regions()
    detector = EventDetector(regions)
    bed_box = bbox_in(regions["bed"])

    assert detector.update([bed_box], "open") == ["BED-IN"]


def test_zone_tracker_debounces_single_frame_flicker():
    regions = make_regions()
    tracker = ZoneTracker(regions, debounce_frames=3)
    bed_box = bbox_in(regions["bed"])
    away = far_away_bbox()

    assert tracker.update([bed_box]) == []
    assert tracker.update([bed_box]) == []
    assert tracker.update([bed_box]) == ["BED-IN"]

    # A single missed-detection frame shouldn't be enough to flip it back out.
    assert tracker.update([away]) == []
    assert tracker.update([bed_box]) == []
    assert tracker.update([bed_box]) == []


def test_zone_tracker_confirms_change_that_holds_for_debounce_window():
    regions = make_regions()
    tracker = ZoneTracker(regions, debounce_frames=3)
    bed_box = bbox_in(regions["bed"])
    away = far_away_bbox()

    tracker.update([bed_box])
    tracker.update([bed_box])
    tracker.update([bed_box])  # confirmed BED-IN

    assert tracker.update([away]) == []
    assert tracker.update([away]) == []
    assert tracker.update([away]) == ["BED-OUT"]
