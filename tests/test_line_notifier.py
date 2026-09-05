from unittest.mock import MagicMock, patch

from mimamori.line_notifier import LineNotifier, build_messages


def test_build_messages_text_only_without_public_url():
    messages = build_messages("hello", image_path="/tmp/alert.jpg", snapshot_public_url_base=None)

    assert len(messages) == 1
    assert messages[0].text == "hello"


def test_build_messages_adds_image_when_public_url_configured():
    messages = build_messages(
        "hello", image_path="/tmp/alert.jpg", snapshot_public_url_base="https://example.com/snaps/"
    )

    assert len(messages) == 2
    assert messages[1].original_content_url == "https://example.com/snaps/alert.jpg"
    assert messages[1].preview_image_url == "https://example.com/snaps/alert.jpg"


@patch("mimamori.line_notifier.MessagingApi")
@patch("mimamori.line_notifier.ApiClient")
def test_send_alert_pushes_message_to_configured_user(mock_api_client_cls, mock_messaging_api_cls):
    mock_api_client_cls.return_value.__enter__.return_value = MagicMock()
    mock_messaging_api = MagicMock()
    mock_messaging_api_cls.return_value = mock_messaging_api

    notifier = LineNotifier("token", "U123", snapshot_public_url_base=None)
    notifier.send_alert("anomaly happened")

    mock_messaging_api.push_message.assert_called_once()
    request = mock_messaging_api.push_message.call_args.args[0]
    assert request.to == "U123"
