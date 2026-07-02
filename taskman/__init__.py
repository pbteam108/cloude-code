"""taskman: a small task management + notification CLI.

Standard-library-only tool that stores tasks in a JSON file, prints a TODO
list, and computes schedule-based notifications (overdue / upcoming) with an
optional Slack Incoming Webhook integration.
"""

from .models import (
    Task,
    load_tasks,
    save_tasks,
    parse_due,
    next_id,
    default_storage_path,
)

__version__ = "0.1.0"

__all__ = [
    "Task",
    "load_tasks",
    "save_tasks",
    "parse_due",
    "next_id",
    "default_storage_path",
    "__version__",
]
