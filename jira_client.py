from __future__ import annotations

import base64
import logging
from typing import Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class JiraClient:
    """
    Minimal Jira client stub. Auth values are placeholders for user input.
    """

    def __init__(
        self,
        base_url: str,
        user_email: Optional[str] = None,
        api_token: Optional[str] = None,
        session: Optional[requests.Session] = None,
        timeout_seconds: int = 30,
    ) -> None:
        self.base_url = base_url.rstrip("/") if base_url else ""
        self.user_email = user_email
        self.api_token = api_token
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

    def _auth_headers(self) -> Dict[str, str]:
        if not (self.user_email and self.api_token):
            raise ValueError("Jira credentials are not set. Update config.")
        token_bytes = f"{self.user_email}:{self.api_token}".encode("utf-8")
        encoded = base64.b64encode(token_bytes).decode("utf-8")
        return {
            "Authorization": f"Basic {encoded}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def create_ticket(
        self,
        project_key: str,
        summary: str,
        description: str,
        issue_type: str = "Task",
        labels: Optional[List[str]] = None,
    ) -> Dict:
        """
        Create a Jira issue.
        """
        if not self.base_url:
            raise ValueError("Jira base_url is not set. Update config.")

        url = f"{self.base_url}/rest/api/3/issue"
        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": issue_type},
                "labels": labels or [],
            }
        }

        headers = self._auth_headers()
        resp = self.session.post(
            url, json=payload, headers=headers, timeout=self.timeout_seconds
        )
        resp.raise_for_status()
        return resp.json()

