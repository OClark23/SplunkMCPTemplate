from __future__ import annotations

import json
import logging
import os
from typing import Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

SEARCH_EXPORT_ENDPOINT = "/services/search/jobs/export"


class SplunkClient:
    """
    Minimal Splunk client. Auth placeholders are left for the user to fill in.
    """

    def __init__(
        self,
        host: str,
        token: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        verify_ssl: bool = True,
        session: Optional[requests.Session] = None,
        timeout_seconds: int = 30,
    ) -> None:
        self.host = host.rstrip("/") if host else ""
        self.token = token or os.getenv("SPLUNK_TOKEN")
        self.username = username or os.getenv("SPLUNK_USERNAME")
        self.password = password or os.getenv("SPLUNK_PASSWORD")
        self.verify_ssl = verify_ssl
        self.timeout_seconds = timeout_seconds
        self.session = session or self._build_session()

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST", "GET"],
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def run_search(
        self,
        spl: str,
        earliest: str = "-60m",
        latest: str = "now",
    ) -> List[Dict]:
        """
        Run an SPL search. Returns a list of event dicts.
        """
        if not self.host:
            raise ValueError("Splunk host is not set. Update config.example.yaml.")

        # TODO: Insert your preferred auth method (token or basic).
        headers: Dict[str, str] = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        elif self.username and self.password:
            self.session.auth = (self.username, self.password)
        else:
            raise ValueError("No Splunk auth provided. Set token or username/password.")

        payload = {
            "search": spl if spl.startswith("search") else f"search {spl}",
            "earliest_time": earliest,
            "latest_time": latest,
            "output_mode": "json",
        }

        url = f"{self.host}{SEARCH_EXPORT_ENDPOINT}"
        logger.debug("Submitting Splunk search to %s", url)
        resp = self.session.post(
            url,
            data=payload,
            headers=headers,
            verify=self.verify_ssl,
            stream=True,
            timeout=self.timeout_seconds,
        )
        resp.raise_for_status()

        events: List[Dict] = []
        for line in resp.iter_lines():
            if not line:
                continue
            try:
                decoded = json.loads(line.decode("utf-8"))
            except json.JSONDecodeError:
                continue
            result = decoded.get("result")
            if result:
                events.append(result)
        logger.info("Retrieved %d events from Splunk.", len(events))
        return events

