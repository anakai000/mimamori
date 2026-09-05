import pytest

from mimamori.regions import BBox, Region, RegionSet


def square_region(name: str, x1: float, y1: float, x2: float, y2: float) -> Region:
    return Region(name=name, polygon=((x1, y1), (x2, y1), (x2, y2), (x1, y2)))


def test_region_overlaps_when_center_inside():
    region = square_region("bed", 0, 0, 100, 100)
    inside = BBox(x1=10, y1=10, x2=30, y2=30)
    outside = BBox(x1=200, y1=200, x2=230, y2=230)

    assert region.overlaps(inside)
    assert not region.overlaps(outside)


def test_region_set_requires_all_four_regions():
    with pytest.raises(ValueError):
        RegionSet({"bed": square_region("bed", 0, 0, 10, 10)})


def test_region_set_overlapping_returns_matching_names():
    regions = RegionSet(
        {
            "door": square_region("door", 0, 0, 10, 10),
            "bed": square_region("bed", 100, 100, 200, 200),
            "sofa": square_region("sofa", 300, 300, 400, 400),
            "table": square_region("table", 500, 500, 600, 600),
        }
    )
    bbox = BBox(x1=110, y1=110, x2=130, y2=130)

    assert regions.overlapping(bbox) == ["bed"]
