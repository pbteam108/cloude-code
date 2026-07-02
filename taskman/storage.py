"""Low-level JSON read/write helpers for the task storage file.

Kept separate from :mod:`taskman.models` so the data-model code stays focused
on the :class:`~taskman.models.Task` structure rather than file I/O details.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict


class StorageError(RuntimeError):
    """Raised when the storage file exists but cannot be parsed."""


def read_json(path: str) -> Dict[str, Any]:
    """Read and parse the JSON storage file at ``path``.

    Returns an empty ``{"tasks": []}`` structure if the file does not exist.
    Raises :class:`StorageError` if the file exists but contains malformed JSON.
    """
    if not os.path.exists(path):
        return {"tasks": []}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        raise StorageError(
            f"Task file {path!r} contains malformed JSON: {exc}"
        ) from exc
    if not isinstance(data, dict) or not isinstance(data.get("tasks", []), list):
        raise StorageError(
            f"Task file {path!r} has an unexpected structure; "
            'expected {"tasks": [ ... ]}.'
        )
    data.setdefault("tasks", [])
    return data


def write_json(path: str, data: Dict[str, Any]) -> None:
    """Write ``data`` to ``path`` as pretty-printed UTF-8 JSON."""
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
