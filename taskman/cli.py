"""Argparse-based command-line interface for taskman."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from typing import List, Optional

from . import __version__
from .models import (
    Task,
    StorageError,
    default_storage_path,
    load_tasks,
    save_tasks,
    next_id,
    parse_due,
)
from .notify import (
    DEFAULT_WINDOW_HOURS,
    render_message,
    render_task_list,
    send_slack,
)

SLACK_ENV = "SLACK_WEBHOOK_URL"


def _find_task(tasks: List[Task], task_id: int) -> Optional[Task]:
    for task in tasks:
        if task.id == task_id:
            return task
    return None


def _validate_due(value: Optional[str]) -> Optional[str]:
    """Validate a --due string, raising argparse-friendly errors."""
    if value is None:
        return None
    try:
        parse_due(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    return value


def cmd_add(args: argparse.Namespace) -> int:
    """Handle ``add``."""
    tasks = load_tasks(args.file)
    task = Task(
        id=next_id(tasks),
        title=args.title,
        due=args.due,
        status="todo",
        notes=args.notes or "",
    )
    tasks.append(task)
    save_tasks(args.file, tasks)
    print("Added task:")
    print(render_task_list([task], now=None), end="")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """Handle ``list``."""
    tasks = load_tasks(args.file)
    if args.status:
        tasks = [t for t in tasks if t.status == args.status]
    elif not args.all:
        tasks = [t for t in tasks if t.status == "todo"]
    print(render_task_list(tasks, now=datetime.now()), end="")
    return 0


def cmd_done(args: argparse.Namespace) -> int:
    """Handle ``done``."""
    tasks = load_tasks(args.file)
    task = _find_task(tasks, args.id)
    if task is None:
        print(f"No task with id {args.id}.", file=sys.stderr)
        return 1
    if task.status == "done":
        print(f"Task #{task.id} is already done.")
        return 0
    task.status = "done"
    save_tasks(args.file, tasks)
    print(f"Marked task #{task.id} done: {task.title}")
    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    """Handle ``remove``."""
    tasks = load_tasks(args.file)
    task = _find_task(tasks, args.id)
    if task is None:
        print(f"No task with id {args.id}.", file=sys.stderr)
        return 1
    tasks = [t for t in tasks if t.id != args.id]
    save_tasks(args.file, tasks)
    print(f"Removed task #{task.id}: {task.title}")
    return 0


def cmd_notify(args: argparse.Namespace) -> int:
    """Handle ``notify``."""
    tasks = load_tasks(args.file)
    now = datetime.now()
    message = render_message(tasks, now=now, within_hours=args.within)
    print(message, end="")

    webhook = args.slack_webhook or os.environ.get(SLACK_ENV)
    if not webhook:
        return 0
    if args.dry_run:
        print("\n[dry-run] Slack webhook configured; not sending.")
        return 0

    ok = send_slack(webhook, message)
    if ok:
        print("\nSlack notification sent.")
        return 0
    print(
        "\nWarning: failed to send Slack notification (continuing).",
        file=sys.stderr,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Construct the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="taskman",
        description="Manage tasks and send schedule-based notifications.",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "--file",
        default=default_storage_path(),
        help="Path to the tasks JSON file "
        "(default: $TASKMAN_FILE or ./tasks.json).",
    )

    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    p_add = sub.add_parser("add", help="Add a new task.")
    p_add.add_argument("title", help="Task title.")
    p_add.add_argument(
        "--due",
        type=_validate_due,
        help="Due date (YYYY-MM-DD) or datetime (YYYY-MM-DDTHH:MM).",
    )
    p_add.add_argument("--notes", default="", help="Optional notes.")
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="List tasks (todo by default).")
    p_list.add_argument(
        "--all", action="store_true", help="Show tasks of every status."
    )
    p_list.add_argument(
        "--status",
        choices=("todo", "done"),
        help="Show only tasks with this status.",
    )
    p_list.set_defaults(func=cmd_list)

    p_done = sub.add_parser("done", help="Mark a task as done.")
    p_done.add_argument("id", type=int, help="Task id.")
    p_done.set_defaults(func=cmd_done)

    p_remove = sub.add_parser("remove", help="Remove a task.")
    p_remove.add_argument("id", type=int, help="Task id.")
    p_remove.set_defaults(func=cmd_remove)

    p_notify = sub.add_parser(
        "notify", help="Report overdue/upcoming tasks; optionally post to Slack."
    )
    p_notify.add_argument(
        "--within",
        type=int,
        default=DEFAULT_WINDOW_HOURS,
        metavar="HOURS",
        help=f"Look-ahead window in hours (default: {DEFAULT_WINDOW_HOURS}).",
    )
    p_notify.add_argument(
        "--slack-webhook",
        help=f"Slack Incoming Webhook URL (or set ${SLACK_ENV}).",
    )
    p_notify.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the message but never POST to Slack.",
    )
    p_notify.set_defaults(func=cmd_notify)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point. Returns a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except StorageError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
