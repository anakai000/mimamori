from mimamori.state_machine import State, StateMachine


def make_machine(**overrides):
    timeouts = {
        State.OTHER: 180.0,
        State.RESTROOM: 600.0,
        State.SOFA: 3600.0,
        State.TABLE: 3600.0,
        State.BED: None,
    }
    timeouts.update(overrides)
    return StateMachine(timeouts, now=0.0)


def test_in_event_transitions_to_zone_state():
    sm = make_machine()
    sm.handle_event("BED-IN", now=1.0)
    assert sm.state is State.BED


def test_out_event_transitions_to_other():
    sm = make_machine()
    sm.handle_event("BED-IN", now=1.0)
    sm.handle_event("BED-OUT", now=2.0)
    assert sm.state is State.OTHER


def test_no_timeout_state_never_alerts():
    sm = make_machine()
    sm.handle_event("BED-IN", now=0.0)
    assert sm.check_timeout(now=10_000.0) is None
    assert sm.state is State.BED


def test_exceeding_threshold_raises_anomaly():
    sm = make_machine(**{State.RESTROOM: 600.0})
    sm.handle_event("RESTROOM-IN", now=0.0)

    assert sm.check_timeout(now=500.0) is None
    assert sm.state is State.RESTROOM

    alert = sm.check_timeout(now=700.0)
    assert alert is not None
    assert alert.previous_state is State.RESTROOM
    assert alert.duration_seconds == 700.0
    assert sm.state is State.ANOMALY


def test_anomaly_only_fires_once_until_cleared():
    sm = make_machine(**{State.RESTROOM: 600.0})
    sm.handle_event("RESTROOM-IN", now=0.0)
    sm.check_timeout(now=700.0)
    assert sm.state is State.ANOMALY

    # Still in ANOMALY: no repeated alert.
    assert sm.check_timeout(now=800.0) is None


def test_next_event_clears_anomaly():
    sm = make_machine(**{State.RESTROOM: 600.0})
    sm.handle_event("RESTROOM-IN", now=0.0)
    sm.check_timeout(now=700.0)
    assert sm.state is State.ANOMALY

    sm.handle_event("RESTROOM-OUT", now=710.0)
    assert sm.state is State.OTHER
