from pathlib import Path

from mimamori.config import Config
from mimamori.state_machine import State


def test_load_reads_yaml_and_applies_defaults_for_missing_keys(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("LINE_CHANNEL_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("LINE_TO_USER_ID", raising=False)
    monkeypatch.delenv("SNAPSHOT_PUBLIC_URL_BASE", raising=False)

    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
        regions_file: config/regions.yaml
        camera:
          size: [640, 480]
        state_timeouts_seconds:
          RESTROOM: 300
          BED: null
        """
    )

    config = Config.load(config_path)

    assert config.camera.size == (640, 480)
    assert config.state_timeouts_seconds[State.RESTROOM] == 300.0
    assert config.state_timeouts_seconds[State.BED] is None
    # Untouched defaults still present.
    assert config.state_timeouts_seconds[State.OTHER] == 180.0
    assert config.detection.confidence_threshold == 0.5
    assert config.line_channel_access_token is None
    assert config.debug.event_capture_dir is None


def test_load_reads_debug_event_capture_dir(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("LINE_CHANNEL_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("LINE_TO_USER_ID", raising=False)

    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
        regions_file: config/regions.yaml
        debug:
          event_capture_dir: event_captures
        """
    )

    config = Config.load(config_path)

    assert config.debug.event_capture_dir == "event_captures"


def test_load_reads_line_credentials_from_env(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("LINE_CHANNEL_ACCESS_TOKEN", "secret-token")
    monkeypatch.setenv("LINE_TO_USER_ID", "U999")

    config_path = tmp_path / "config.yaml"
    config_path.write_text("regions_file: config/regions.yaml\n")

    config = Config.load(config_path)

    assert config.line_channel_access_token == "secret-token"
    assert config.line_to_user_id == "U999"
