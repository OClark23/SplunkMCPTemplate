from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator


class SplunkSettings(BaseModel):
    host: str = Field(..., description="Splunk management/REST URL")
    token: Optional[str] = Field(default=None, description="Splunk token")
    username: Optional[str] = None
    password: Optional[str] = None
    verify_ssl: bool = True

    @field_validator("host")
    def host_not_empty(cls, v: str) -> str:
        if not v or v == "https://your-splunk-host:8089":
            raise ValueError("Set splunk.host to your Splunk URL.")
        return v


class SearchSettings(BaseModel):
    name: str
    spl: str
    earliest: str = "-60m"
    latest: str = "now"


class ThresholdSettings(BaseModel):
    count: int = 100
    window_minutes: int = 60
    group_by: List[str] = Field(default_factory=lambda: ["host"])


class ReportingSettings(BaseModel):
    include_top_fields: List[str] = Field(default_factory=list)
    max_top_values: int = 5


class JiraSettings(BaseModel):
    enabled: bool = False
    base_url: str = "https://your-domain.atlassian.net"
    project_key: str = "ABC"
    user_email: Optional[str] = None
    api_token: Optional[str] = None
    issue_type: str = "Task"
    summary_template: str = "Splunk alert: {{search_name}}"
    labels: List[str] = Field(default_factory=lambda: ["splunk", "auto"])

    @field_validator("base_url")
    def base_url_set(cls, v: str, info):
        if info.data.get("enabled") and (not v or "your-domain" in v):
            raise ValueError("Set jira.base_url to your Jira site.")
        return v

    @field_validator("project_key")
    def project_key_set(cls, v: str, info):
        if info.data.get("enabled") and v in ("ABC", "", None):
            raise ValueError("Set jira.project_key to your target project.")
        return v


class TeamsSettings(BaseModel):
    enabled: bool = False
    webhook_url: Optional[str] = None

    @field_validator("webhook_url")
    def webhook_required(cls, v: Optional[str], info):
        if info.data.get("enabled") and not v:
            raise ValueError("Set teams.webhook_url for Teams posting.")
        return v


class RunSettings(BaseModel):
    log_level: str = "INFO"
    output_path: Optional[Path] = None


class AppConfig(BaseModel):
    splunk: SplunkSettings
    search: SearchSettings
    threshold: ThresholdSettings = ThresholdSettings()
    reporting: ReportingSettings = ReportingSettings()
    jira: JiraSettings = JiraSettings()
    teams: TeamsSettings = TeamsSettings()
    run: RunSettings = RunSettings()


def load_config(path: Path) -> AppConfig:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    try:
        return AppConfig(**data)
    except ValidationError as exc:
        raise ValueError(f"Invalid configuration: {exc}") from exc

