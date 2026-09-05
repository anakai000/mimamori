import numpy as np
import pytest

from mimamori.detector import PERSON_CLASS_ID, parse_detections


def raw_detection(class_id: float, confidence: float, box=(0.1, 0.2, 0.5, 0.6)) -> np.ndarray:
    x1, y1, x2, y2 = box
    return [0.0, class_id, confidence, x1, y1, x2, y2]


def make_raw(rows) -> np.ndarray:
    arr = np.zeros((1, 1, len(rows), 7), dtype=np.float32)
    for i, row in enumerate(rows):
        arr[0, 0, i, :] = row
    return arr


def test_parse_detections_filters_by_class_and_confidence():
    raw = make_raw(
        [
            raw_detection(PERSON_CLASS_ID, 0.9),  # kept
            raw_detection(PERSON_CLASS_ID, 0.2),  # below threshold
            raw_detection(7, 0.99),  # wrong class (car)
        ]
    )

    boxes = parse_detections(raw, width=200, height=100, confidence_threshold=0.5)

    assert len(boxes) == 1
    assert boxes[0].confidence == pytest.approx(0.9)


def test_parse_detections_scales_box_to_frame_size():
    raw = make_raw([raw_detection(PERSON_CLASS_ID, 0.8, box=(0.1, 0.2, 0.5, 0.6))])

    boxes = parse_detections(raw, width=200, height=100, confidence_threshold=0.5)

    box = boxes[0]
    assert box.x1 == pytest.approx(20.0)
    assert box.y1 == pytest.approx(20.0)
    assert box.x2 == pytest.approx(100.0)
    assert box.y2 == pytest.approx(60.0)
