"""The BED/SOFA/TABLE/RESTROOM/OTHER/ANOMALY state machine (see SPEC.md)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


class State(str, Enum):
    BED = "BED"
    SOFA = "SOFA"
    TABLE = "TABLE"
    RESTROOM = "RESTROOM"
    OTHER = "OTHER"
    ANOMALY = "ANOMALY"


IN_EVENT_TO_STATE = {
    "BED-IN": State.BED,
    "SOFA-IN": State.SOFA,
    "TABLE-IN": State.TABLE,
    "RESTROOM-IN": State.RESTROOM,
}
OUT_EVENTS = {"BED-OUT", "SOFA-OUT", "TABLE-OUT", "RESTROOM-OUT"}


@dataclass(frozen=True)
class Alert:
    previous_state: State
    duration_seconds: float
    threshold_seconds: float

    @property
    def message(self) -> str:
        return (
            f"Anomaly: stayed in {self.previous_state.value} for "
            f"{self.duration_seconds:.0f}s (threshold {self.threshold_seconds:.0f}s)"
        )


class StateMachine:
    def __init__(self, timeouts_seconds: Dict[State, Optional[float]], now: float = 0.0):
        self.timeouts_seconds = timeouts_seconds
        self.state = State.OTHER
        self._state_entered_at = now

    def handle_event(self, event: str, now: float) -> None:
        """Any event clears a prior ANOMALY too: an *-IN event moves straight
        into that zone, an *-OUT event moves to OTHER."""
        if event in IN_EVENT_TO_STATE:
            self._transition(IN_EVENT_TO_STATE[event], now)
        elif event in OUT_EVENTS:
            self._transition(State.OTHER, now)

    def check_timeout(self, now: float) -> Optional[Alert]:
        if self.state is State.ANOMALY:
            return None
        threshold = self.timeouts_seconds.get(self.state)
        if threshold is None:
            return None
        elapsed = now - self._state_entered_at
        if elapsed <= threshold:
            return None
        alert = Alert(previous_state=self.state, duration_seconds=elapsed, threshold_seconds=threshold)
        self._transition(State.ANOMALY, now)
        return alert

    def _transition(self, new_state: State, now: float) -> None:
        if new_state == self.state:
            return
        self.state = new_state
        self._state_entered_at = now
