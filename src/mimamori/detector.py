"""Person detection via a Caffe MobileNet-SSD model (OpenCV DNN backend).

The model is the classic MobileNet-SSD trained on Pascal VOC (21 classes);
see models/README.md for how to obtain the weight files. Class id 15 is
"person" in that label set.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Union

import cv2
import numpy as np

from .regions import BBox

PERSON_CLASS_ID = 15


def parse_detections(
    raw: np.ndarray, width: int, height: int, confidence_threshold: float
) -> List[BBox]:
    """Pure post-processing step, kept separate from the DNN call so it can be
    unit-tested with a synthetic `raw` array (no model file needed)."""
    boxes: List[BBox] = []
    for i in range(raw.shape[2]):
        confidence = float(raw[0, 0, i, 2])
        class_id = int(raw[0, 0, i, 1])
        if class_id != PERSON_CLASS_ID or confidence < confidence_threshold:
            continue
        x1, y1, x2, y2 = raw[0, 0, i, 3:7] * np.array([width, height, width, height])
        boxes.append(BBox(x1=float(x1), y1=float(y1), x2=float(x2), y2=float(y2), confidence=confidence))
    return boxes


class PersonDetector:
    def __init__(
        self,
        prototxt_path: Union[str, Path],
        weights_path: Union[str, Path],
        confidence_threshold: float = 0.5,
        input_size: int = 300,
    ):
        self.confidence_threshold = confidence_threshold
        self.input_size = input_size
        self._net = cv2.dnn.readNetFromCaffe(str(prototxt_path), str(weights_path))

    def detect(self, frame: np.ndarray) -> List[BBox]:
        height, width = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(
            frame, scalefactor=0.007843, size=(self.input_size, self.input_size), mean=127.5
        )
        self._net.setInput(blob)
        raw = self._net.forward()
        return parse_detections(raw, width, height, self.confidence_threshold)
