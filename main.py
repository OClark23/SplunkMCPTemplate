from __future__ import annotations

import argparse
import logging
import uuid
from pathlib import Path
from typing import Any, Dict

from .analyzer import evaluate_counts
from .config import AppConfig, load_config
from .report_builder import build_markdown_report
from .splunk_client import SplunkClient
from .jira_client import JiraClient
from .teams_client import TeamsClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Splunk MCP template runner")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.yaml"),
        help="Path to config.yaml (defaults to config.yaml)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write the markdown report.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config_path = args.config
    if not config_path.exists():
        fallback = Path("config.example.yaml")
        if fallback.exists():
            config_path = fallback
        else:
            raise FileNotFoundError(f"Config not found: {args.config}")

    config: AppConfig = load_config(config_path)

    run_cfg = config.run
    log_level = run_cfg.log_level.upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    logger = logging.getLogger("splunk_mcp")
    run_id = str(uuid.uuid4())[:8]
    logger.info("Starting MCP run id=%s config=%s", run_id, config_path)

    if args.output:
        run_cfg.output_path = args.output

    search_cfg = config.search
    splunk_cfg = config.splunk
    threshold_cfg = config.threshold
    jira_cfg = config.jira
    teams_cfg = config.teams

    search_name = search_cfg.name
    spl_query = search_cfg.spl
    earliest = search_cfg.earliest
    latest = search_cfg.latest
    group_by = threshold_cfg.group_by
    threshold_count = threshold_cfg.count
    window_minutes = threshold_cfg.window_minutes

    client = SplunkClient(
        host=splunk_cfg.host,
        token=splunk_cfg.token,
        username=splunk_cfg.username,
        password=splunk_cfg.password,
        verify_ssl=bool(splunk_cfg.verify_ssl),
    )

    events = client.run_search(
        spl=spl_query,
        earliest=earliest,
        latest=latest,
    )

    findings = evaluate_counts(
        events=events,
        threshold_count=threshold_count,
        window_minutes=window_minutes,
        group_by=group_by,
        search_name=search_name,
    )

    report = build_markdown_report(
        search_name=search_name,
        threshold_count=threshold_count,
        window_minutes=window_minutes,
        findings=findings,
    )
    print(report)
    if run_cfg.output_path:
        Path(run_cfg.output_path).write_text(report, encoding="utf-8")
        logger.info("Report written to %s", run_cfg.output_path)

    if not findings:
        logger.info("No findings above threshold; Jira step skipped.")
        return

    if jira_cfg.enabled:
        jira_client = JiraClient(
            base_url=jira_cfg.base_url,
            user_email=jira_cfg.user_email,
            api_token=jira_cfg.api_token,
        )

        summary_template = jira_cfg.summary_template
        summary = summary_template.replace("{{search_name}}", search_name)
        labels = jira_cfg.labels
        issue_type = jira_cfg.issue_type

        result = jira_client.create_ticket(
            project_key=jira_cfg.project_key,
            summary=summary,
            description=report,
            issue_type=issue_type,
            labels=labels,
        )
        logger.info("Jira result: %s", result)
    else:
        logger.info("Jira disabled; skipping ticket creation.")

    if teams_cfg.enabled:
        teams_client = TeamsClient(webhook_url=teams_cfg.webhook_url)
        teams_result = teams_client.post_message(report)
        logger.info("Teams result: %s", teams_result)
    else:
        logger.info("Teams disabled; skipping Teams notification.")


if __name__ == "__main__":
    main()

