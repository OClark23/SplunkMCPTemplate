from __future__ import annotations

from typing import Iterable, List

from .analyzer import Finding


def build_markdown_report(
    search_name: str,
    threshold_count: int,
    window_minutes: int,
    findings: Iterable[Finding],
) -> str:
    findings_list: List[Finding] = list(findings)
    if not findings_list:
        return (
            f"# Splunk MCP Report\n\n"
            f"- Search: {search_name}\n"
            f"- Window: last {window_minutes}m\n"
            f"- Threshold: {threshold_count}\n"
            f"- Result: No threshold breaches detected.\n"
        )

    lines: List[str] = [
        "# Splunk MCP Report",
        f"- Search: {search_name}",
        f"- Window: last {window_minutes}m",
        f"- Threshold: {threshold_count}",
        "",
        "## Findings",
    ]

    for finding in findings_list:
        group_parts = ", ".join(f"{k}={v}" for k, v in finding.group.items())
        lines.append(f"- {group_parts}: count={finding.count} (window {finding.window})")

    return "\n".join(lines) + "\n"

