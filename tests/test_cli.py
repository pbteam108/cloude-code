"""Tests for notify categorization/rendering and the CLI, with injected time."""

import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime

from taskman.cli import main
from taskman.models import Task, load_tasks, save_tasks
from taskman.notify import categorize, render_message


NOW = datetime(2026, 7, 2, 12, 0, 0)


def sample_tasks():
    return [
        Task(id=1, title="Overdue report", due="2026-06-30", status="todo"),
        Task(id=2, title="Prep meeting", due="2026-07-02T15:00:00", status="todo"),
        Task(id=3, title="Design review", due="2026-07-20T10:00:00", status="todo"),
        Task(id=4, title="Read list", due=None, status="todo"),
        Task(id=5, title="Already handled", due="2026-06-01", status="done"),
    ]


class CategorizeTests(unittest.TestCase):
    def test_buckets(self) -> None:
        cats = categorize(sample_tasks(), now=NOW, within_hours=24)
        self.assertEqual([t.id for t in cats.overdue], [1])
        self.assertEqual([t.id for t in cats.upcoming], [2])
        self.assertEqual([t.id for t in cats.later], [3])
        self.assertEqual([t.id for t in cats.no_due], [4])

    def test_done_tasks_excluded(self) -> None:
        cats = categorize(sample_tasks(), now=NOW, within_hours=24)
        all_ids = [
            t.id
            for group in (cats.overdue, cats.upcoming, cats.later, cats.no_due)
            for t in group
        ]
        self.assertNotIn(5, all_ids)

    def test_wider_window_promotes_later(self) -> None:
        cats = categorize(sample_tasks(), now=NOW, within_hours=24 * 30)
        self.assertIn(3, [t.id for t in cats.upcoming])
        self.assertEqual(cats.later, [])


class RenderMessageTests(unittest.TestCase):
    def test_contains_titles(self) -> None:
        msg = render_message(sample_tasks(), now=NOW, within_hours=24)
        self.assertIn("Overdue report", msg)
        self.assertIn("Prep meeting", msg)
        self.assertIn("OVERDUE", msg)
        self.assertIn("UPCOMING", msg)
        self.assertNotIn("Already handled", msg)


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self._tmp.name, "tasks.json")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run(self, *argv) -> str:
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["--file", self.path, *argv])
        self.assertEqual(code, 0)
        return buf.getvalue()

    def test_add_then_list(self) -> None:
        self._run("add", "Write docs", "--due", "2026-07-10")
        tasks = load_tasks(self.path)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].title, "Write docs")
        out = self._run("list")
        self.assertIn("Write docs", out)

    def test_done_and_default_list_hides_done(self) -> None:
        self._run("add", "Task A")
        self._run("done", "1")
        self.assertEqual(load_tasks(self.path)[0].status, "done")
        out = self._run("list")
        self.assertNotIn("Task A", out)
        out_all = self._run("list", "--all")
        self.assertIn("Task A", out_all)

    def test_remove(self) -> None:
        self._run("add", "Task A")
        self._run("remove", "1")
        self.assertEqual(load_tasks(self.path), [])

    def test_notify_dry_run(self) -> None:
        save_tasks(self.path, sample_tasks())
        out = self._run(
            "notify", "--within", "48", "--slack-webhook", "http://example.invalid",
            "--dry-run",
        )
        self.assertIn("Overdue report", out)
        self.assertIn("dry-run", out)


if __name__ == "__main__":
    unittest.main()
