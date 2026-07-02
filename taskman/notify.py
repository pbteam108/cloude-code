"""Notification logic: categorization, message rendering, and Slack sending.

All scheduling functions accept an explicit ``now`` argument so callers (and
tests) can inject a deterministic reference time. ``datetime.now()`` is only
resolved lazily by the CLI, never at import time.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

from .models import Task

__all__ = [
    "Categorized",
    "categorize",
    "render_message",
    "render_task_list",
    "send_slack",
]

#: Default look-ahead window (hours) for "upcoming" tasks.
DEFAULT_WINDOW_HOURS = 24


@dataclass
class Categorized:
    """Result of categorizing tasks relative to a reference time.

    Attributes:
        overdue: Undone tasks whose due time is at or before ``now``.
        upcoming: Undone tasks due after ``now`` and within the window.
        later: Undone tasks with a due time beyond the window.
        no_due: Undone tasks with no due date.
    """

    overdue: List[Task]
    upcoming: List[Task]
    later: List[Task]
    no_due: List[Task]


def _due_sort_key(task: Task) -> datetime:
    dt = task.due_datetime()
    return dt if dt is not None else datetime.max


def categorize(
    tasks: List[Task],
    now: datetime,
    within_hours: int = DEFAULT_WINDOW_HOURS,
) -> Categorized:
    """Split undone tasks into overdue / upcoming / later / no-due buckets.

    Done tasks are ignored. ``upcoming`` covers ``now < due <= now + window``.
    Each bucket is sorted by due time (no-due tasks by id/insertion order).
    """
    window_end = now + timedelta(hours=within_hours)
    overdue: List[Task] = []
    upcoming: List[Task] = []
    later: List[Task] = []
    no_due: List[Task] = []

    for task in tasks:
        if task.status == "done":
            continue
        due = task.due_datetime()
        if due is None:
            no_due.append(task)
        elif due <= now:
            overdue.append(task)
        elif due <= window_end:
            upcoming.append(task)
        else:
            later.append(task)

    overdue.sort(key=_due_sort_key)
    upcoming.sort(key=_due_sort_key)
    later.sort(key=_due_sort_key)
    return Categorized(overdue=overdue, upcoming=upcoming, later=later, no_due=no_due)


def _format_due(task: Task) -> str:
    return task.due if task.due else "(no due date)"


def _bullet(task: Task) -> str:
    return f"  - [#{task.id}] {task.title} (due {_format_due(task)})"


def render_message(
    tasks: List[Task],
    now: datetime,
    within_hours: int = DEFAULT_WINDOW_HOURS,
) -> str:
    """Render a plaintext notification summarizing schedule alerts + TODOs."""
    cats = categorize(tasks, now, within_hours)
    lines: List[str] = []
    lines.append(f"TODO notification ({now.strftime('%Y-%m-%d %H:%M')})")
    lines.append(f"Look-ahead window: next {within_hours}h")
    lines.append("")

    if cats.overdue:
        lines.append(f"OVERDUE ({len(cats.overdue)}):")
        lines.extend(_bullet(t) for t in cats.overdue)
        lines.append("")

    if cats.upcoming:
        lines.append(f"UPCOMING within {within_hours}h ({len(cats.upcoming)}):")
        lines.extend(_bullet(t) for t in cats.upcoming)
        lines.append("")

    if cats.later:
        lines.append(f"Later ({len(cats.later)}):")
        lines.extend(_bullet(t) for t in cats.later)
        lines.append("")

    if cats.no_due:
        lines.append(f"No due date ({len(cats.no_due)}):")
        lines.extend(_bullet(t) for t in cats.no_due)
        lines.append("")

    if not (cats.overdue or cats.upcoming or cats.later or cats.no_due):
        lines.append("No open tasks. You're all caught up!")

    return "\n".join(lines).rstrip() + "\n"


def render_task_list(
    tasks: List[Task],
    now: Optional[datetime] = None,
) -> str:
    """Render an aligned table of tasks, marking overdue ones with ``!``.

    ``now`` is only used to flag overdue tasks; pass ``None`` to skip flagging.
    """
    if not tasks:
        return "(no tasks)\n"

    header = ("", "ID", "STATUS", "DUE", "TITLE")
    rows = []
    for task in tasks:
        overdue = False
        if now is not None and task.status != "done":
            due = task.due_datetime()
            overdue = due is not None and due <= now
        marker = "!" if overdue else " "
        rows.append(
            (
                marker,
                str(task.id),
                task.status,
                task.due or "-",
                task.title,
            )
        )

    all_rows = [header] + rows
    widths = [max(len(row[i]) for row in all_rows) for i in range(len(header))]

    def fmt(row: tuple) -> str:
        return "  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)).rstrip()

    lines = [fmt(header), fmt(("", "-" * widths[1], "-" * widths[2], "-" * widths[3], "-" * widths[4]))]
    lines.extend(fmt(row) for row in rows)
    return "\n".join(lines) + "\n"


def send_slack(webhook_url: str, text: str, timeout: float = 10.0) -> bool:
    """POST ``{"text": text}`` as JSON to a Slack Incoming Webhook.

    Returns ``True`` on a 2xx response, ``False`` otherwise. Network and HTTP
    errors are caught and reported via the return value (never raised).
    """
    payload = json.dumps({"text": text}).encode("utf-8")
    request = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return 200 <= response.status < 300
    except urllib.error.HTTPError as exc:
        return 200 <= exc.code < 300
    except (urllib.error.URLError, OSError, ValueError):
        return False
