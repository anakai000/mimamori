import numpy as np

from mimamori.door import DoorStateDetector, edge_density
from mimamori.regions import Region


def make_door_region() -> Region:
    return Region(name="door", polygon=((0, 0), (50, 0), (50, 50), (0, 50)))


def test_edge_density_higher_for_noisy_than_flat_frame():
    rng = np.random.default_rng(0)
    flat = np.full((50, 50, 3), 128, dtype=np.uint8)
    noisy = rng.integers(0, 255, size=(50, 50, 3), dtype=np.uint8)

    assert edge_density(noisy) > edge_density(flat)


def test_classify_density_picks_nearest_reference():
    detector = DoorStateDetector(make_door_region(), closed_edge_density=5.0, open_edge_density=25.0)

    assert detector.classify_density(6.0) == "closed"
    assert detector.classify_density(24.0) == "open"
    assert detector.classify_density(15.0) == "closed"  # tie-break: equidistant -> closed


def test_classify_reads_frame_roi():
    detector = DoorStateDetector(make_door_region(), closed_edge_density=0.0, open_edge_density=200.0)
    frame = np.full((100, 100, 3), 128, dtype=np.uint8)

    assert detector.classify(frame) == "closed"
