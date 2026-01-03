from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence


@dataclass
class Finding:
    group: Dict[str, str]
    count: int
    window: str


def evaluate_counts(
    events: Iterable[Dict],
    threshold_count: int,
    window_minutes: int,
    group_by: Sequence[str],
    search_name: str = "unnamed",
) -> List[Finding]:
    """
    Aggregate events and flag groups whose count meets/exceeds threshold.

    This logic is pure and testable without Splunk connectivity.
    """
    aggregates: defaultdict[tuple, int] = defaultdict(int)
    for event in events:
        key = tuple(str(event.get(field, "unknown")) for field in group_by)
        event_count = event.get("count", 1)
        try:
            event_count = int(event_count)
        except (ValueError, TypeError):
            event_count = 1
        aggregates[key] += event_count

    findings: List[Finding] = []
    window_label = f"last {window_minutes}m"
    for key, total in aggregates.items():
        if total >= threshold_count:
            group_dict = {field: value for field, value in zip(group_by, key)}
            findings.append(
                Finding(group=group_dict, count=total, window=window_label)
            )

    return findings

