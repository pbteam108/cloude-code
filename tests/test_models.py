"""Tests for taskman.models: persistence, id generation, due parsing."""

import os
import tempfile
import unittest
from datetime import datetime

from taskman.models import (
    Task,
    StorageError,
    load_tasks,
    save_tasks,
    next_id,
    parse_due,
)


class TempFileTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self._tmp.name, "tasks.json")

    def tearDown(self) -> None:
        self._tmp.cleanup()


class RoundTripTests(TempFileTestCase):
    def test_save_load_round_trip(self) -> None:
        tasks = [
            Task(id=1, title="A", due="2026-07-05", status="todo", notes="n"),
            Task(id=2, title="B", due=None, status="done"),
        ]
        save_tasks(self.path, tasks)
        loaded = load_tasks(self.path)
        self.assertEqual(loaded, tasks)

    def test_missing_file_returns_empty(self) -> None:
        missing = os.path.join(self._tmp.name, "nope.json")
        self.assertEqual(load_tasks(missing), [])

    def test_malformed_json_raises(self) -> None:
        with open(self.path, "w", encoding="utf-8") as fh:
            fh.write("{ not json ]")
        with self.assertRaises(StorageError):
            load_tasks(self.path)


class NextIdTests(unittest.TestCase):
    def test_empty(self) -> None:
        self.assertEqual(next_id([]), 1)

    def test_max_plus_one(self) -> None:
        tasks = [Task(id=3, title="x"), Task(id=7, title="y")]
        self.assertEqual(next_id(tasks), 8)


class ParseDueTests(unittest.TestCase):
    def test_none_and_empty(self) -> None:
        self.assertIsNone(parse_due(None))
        self.assertIsNone(parse_due(""))

    def test_date_only_is_midnight(self) -> None:
        self.assertEqual(parse_due("2026-07-05"), datetime(2026, 7, 5, 0, 0, 0))

    def test_datetime(self) -> None:
        self.assertEqual(
            parse_due("2026-07-05T09:30:00"), datetime(2026, 7, 5, 9, 30, 0)
        )

    def test_datetime_space_separator(self) -> None:
        self.assertEqual(
            parse_due("2026-07-05 09:30"), datetime(2026, 7, 5, 9, 30)
        )

    def test_invalid_raises(self) -> None:
        with self.assertRaises(ValueError):
            parse_due("not-a-date")


if __name__ == "__main__":
    unittest.main()
