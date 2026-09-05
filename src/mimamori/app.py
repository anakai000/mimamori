"""Wires camera -> detector -> events -> state machine -> notifier together."""

from __future__ import annotations

import asyncio
import logging
import time

from .camera import Camera
from .config import Config
from .detector import PersonDetector
from .door import DoorStateDetector
from .events import EventDetector
from .line_notifier import LineNotifier
from .regions import RegionSet
from .state_machine import StateMachine

logger = logging.getLogger("mimamori")


class MimamoriApp:
    def __init__(self, config: Config):
        self.config = config
        self.regions = RegionSet.from_yaml(config.regions_file)
        self.detector = PersonDetector(
            config.detection.model_prototxt,
            config.detection.model_weights,
            config.detection.confidence_threshold,
        )
        self.door_detector = DoorStateDetector(
            self.regions["door"],
            config.door.closed_edge_density,
            config.door.open_edge_density,
        )
        self.event_detector = EventDetector(self.regions)
        self.state_machine = StateMachine(config.state_timeouts_seconds, now=time.monotonic())
        self.camera = Camera(size=config.camera.size)

        self.notifier: LineNotifier | None = None
        if config.line_channel_access_token and config.line_to_user_id:
            self.notifier = LineNotifier(
                config.line_channel_access_token,
                config.line_to_user_id,
                config.notifier.snapshot_public_url_base,
            )
        else:
            logger.warning("LINE_CHANNEL_ACCESS_TOKEN/LINE_TO_USER_ID not set; alerts will only be logged.")

    async def run(self) -> None:
        interval = self.config.detection.process_interval_seconds
        try:
            while True:
                self._tick()
                await asyncio.sleep(interval)
        finally:
            self.camera.close()

    def _tick(self) -> None:
        now = time.monotonic()
        frame = self.camera.capture_frame()
        bboxes = self.detector.detect(frame)
        door_state = self.door_detector.classify(frame)

        for event in self.event_detector.update(bboxes, door_state):
            self.state_machine.handle_event(event, now)
            logger.info("event=%s state=%s", event, self.state_machine.state.value)

        alert = self.state_machine.check_timeout(now)
        if alert is not None:
            self._handle_alert(alert, frame)

    def _handle_alert(self, alert, frame) -> None:
        logger.warning(alert.message)
        self.camera.save_snapshot(frame, self.config.notifier.snapshot_path)
        if self.notifier is not None:
            self.notifier.send_alert(alert.message, self.config.notifier.snapshot_path)
