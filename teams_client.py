from __future__ import annotations

import logging
from typing import Dict, Optional

import requests

logger = logging.getLogger(__name__)


class TeamsClient:
    """
    Placeholder Teams client using an incoming webhook.
    """

    def __init__(self, webhook_url: Optional[str]) -> None:
        self.webhook_url = webhook_url
        self.session = requests.Session()

    def post_message(self, text: str) -> Dict:
        if not self.webhook_url:
            raise ValueError("Teams webhook_url is not set.")

        payload = {"text": text}
        resp = self.session.post(self.webhook_url, json=payload, timeout=15)
        resp.raise_for_status()
        return resp.json() if resp.text else {"status": "sent"}

