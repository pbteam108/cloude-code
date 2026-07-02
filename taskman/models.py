"""Data model and persistence for tasks.

Defines the :class:`Task` dataclass, storage-path resolution, load/save
helpers, due-date parsing, and next-id generation.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional

from .storage import read_json, write_json, StorageError

__all__ = [
    "Task",
    "StorageError",
    "default_storage_path",
    "load_tasks",
    "save_tasks",
    "parse_due",
    "next_id",
]

#: Environment variable that overrides the default storage location.
ENV_FILE = "TASKMAN_FILE"

#: Allowed task status values.
VALID_STATUSES = ("todo", "done")


@dataclass
class Task:
    """A single task.

    Attributes:
        id: Unique positive integer identifier.
        title: Human-readable task title.
        due: Optional ISO-8601 date ("2026-07-05") or datetime
            ("2026-07-05T09:00:00") string. ``None`` means the task has no
            schedule.
        status: Either ``"todo"`` or ``"done"``.
        notes: Optional free-form notes.
    """

    id: int
    title: str
    due: Optional[str] = None
    status: str = "todo"
    notes: str = ""

    def to_dict(self) -> dict:
        """Return a JSON-serializable dict representation."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Build a :class:`Task` from a raw dict, tolerating missing fields."""
        return cls(
            id=int(data["id"]),
            title=str(data["title"]),
            due=data.get("due"),
            status=str(data.get("status", "todo")),
            notes=str(data.get("notes", "")),
        )

    def due_datetime(self) -> Optional[datetime]:
        """Return the parsed ``due`` as a :class:`datetime`, or ``None``."""
        return parse_due(self.due)


def default_storage_path() -> str:
    """Resolve the storage file path.

    Uses the ``TASKMAN_FILE`` environment variable if set, otherwise
    ``tasks.json`` in the current working directory.
    """
    return os.environ.get(ENV_FILE) or "tasks.json"


def parse_due(due: Optional[str]) -> Optional[datetime]:
    """Parse a due string into a :class:`datetime`.

    Date-only strings (``"2026-07-05"``) are parsed to midnight. Full
    datetime strings (``"2026-07-05T09:00:00"``) are parsed as-is. Returns
    ``None`` for empty/``None`` input. Raises :class:`ValueError` for strings
    that cannot be parsed.
    """
    if due is None or due == "":
        return None
    text = due.strip()
    # Accept a space separator as well as the ISO "T".
    normalized = text.replace(" ", "T", 1) if " " in text and "T" not in text else text
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        # Fall back to a small set of common explicit formats.
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(normalized, fmt)
            except ValueError:
                continue
    raise ValueError(f"Unrecognized due date/time: {due!r}")


def next_id(tasks: List[Task]) -> int:
    """Return the next available id (max existing id + 1, or 1 if empty)."""
    if not tasks:
        return 1
    return max(task.id for task in tasks) + 1


def load_tasks(path: Optional[str] = None) -> List[Task]:
    """Load tasks from ``path`` (or the default storage path).

    Returns an empty list if the file does not exist. Raises
    :class:`StorageError` on malformed JSON.
    """
    path = path or default_storage_path()
    data = read_json(path)
    return [Task.from_dict(item) for item in data.get("tasks", [])]


def save_tasks(path: Optional[str], tasks: List[Task]) -> None:
    """Persist ``tasks`` to ``path`` (or the default storage path)."""
    path = path or default_storage_path()
    write_json(path, {"tasks": [task.to_dict() for task in tasks]})
