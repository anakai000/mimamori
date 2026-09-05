"""Dispatches LINE push messages for anomaly alerts.

Note: the LINE Messaging API (unlike the deprecated LINE Notify service) does
not accept a raw file upload for images — an image message needs a public
HTTPS URL that LINE's servers can fetch. If `snapshot_public_url_base` isn't
configured, alerts fall back to text-only (the snapshot still gets saved
on-device at notifier.snapshot_path).
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    ImageMessage,
    MessagingApi,
    PushMessageRequest,
    TextMessage,
)


def build_messages(
    text: str, image_path: Optional[str], snapshot_public_url_base: Optional[str]
) -> List[object]:
    messages: List[object] = [TextMessage(text=text)]
    if image_path and snapshot_public_url_base:
        url = f"{snapshot_public_url_base.rstrip('/')}/{Path(image_path).name}"
        messages.append(ImageMessage(original_content_url=url, preview_image_url=url))
    return messages


class LineNotifier:
    def __init__(
        self,
        channel_access_token: str,
        to_user_id: str,
        snapshot_public_url_base: Optional[str] = None,
    ):
        self._configuration = Configuration(access_token=channel_access_token)
        self._to_user_id = to_user_id
        self._snapshot_public_url_base = snapshot_public_url_base

    def send_alert(self, text: str, image_path: Optional[str] = None) -> None:
        if image_path and not self._snapshot_public_url_base:
            text += "\n(snapshot saved on-device only; no public URL configured to attach it)"
        messages = build_messages(text, image_path, self._snapshot_public_url_base)
        with ApiClient(self._configuration) as api_client:
            MessagingApi(api_client).push_message(
                PushMessageRequest(to=self._to_user_id, messages=messages)
            )
