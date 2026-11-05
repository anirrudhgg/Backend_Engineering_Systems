import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kanban_scheduler import KanbanScheduler, WorkItem  # noqa: E402


class TestOrdering(unittest.TestCase):
    def test_service_class_comes_first(self):
        s = KanbanScheduler()
        s.add(WorkItem.standard("Feature", cod=9000, duration=1))
        s.add(WorkItem.expedite("Outage", cod=100))
        self.assertEqual(s.pull_next().title, "Outage")

    def test_highest_cd3_first_within_a_class(self):
        s = KanbanScheduler()
        s.add(WorkItem.standard("Low CD3", cod=500, duration=2))      # 250
        s.add(WorkItem.standard("High CD3", cod=3000, duration=3))    # 1000
        s.add(WorkItem.standard("Medium CD3", cod=1000, duration=2))  # 500
        order = [s.pull_next().title for _ in range(3)]
        self.assertEqual(order, ["High CD3", "Medium CD3", "Low CD3"])

    def test_backlog_matches_pull_order(self):
        s = KanbanScheduler(wip_limit=10)
        s.add(WorkItem.intangible("Debt", cod=50, duration=1))
        s.add(WorkItem.standard("A", cod=100, duration=1))
        s.add(WorkItem.standard("B", cod=900, duration=1))
        expected = [i.title for i in s.prioritised_backlog()]
        pulled = [s.pull_next().title for _ in range(3)]
        self.assertEqual(pulled, expected)

    def test_equal_items_are_fifo(self):
        s = KanbanScheduler()
        s.add(WorkItem.standard("First", cod=100, duration=1))
        s.add(WorkItem.standard("Second", cod=100, duration=1))
        self.assertEqual(s.pull_next().title, "First")


class TestLimits(unittest.TestCase):
    def test_wip_limit_and_completion(self):
        s = KanbanScheduler(wip_limit=1)
        s.add(WorkItem.standard("A", cod=100, duration=1))
        s.add(WorkItem.standard("B", cod=50, duration=1))
        first = s.pull_next()
        self.assertIsNone(s.pull_next())  # WIP limit reached
        s.complete(first)
        self.assertEqual(s.pull_next().title, "B")

    def test_only_one_expedite_at_a_time(self):
        s = KanbanScheduler()
        s.add(WorkItem.expedite("Outage 1", cod=100))
        with self.assertRaises(ValueError):
            s.add(WorkItem.expedite("Outage 2", cod=100))

    def test_new_expedite_allowed_after_previous_is_done(self):
        s = KanbanScheduler()
        s.add(WorkItem.expedite("Outage 1", cod=100))
        s.complete(s.pull_next())
        s.add(WorkItem.expedite("Outage 2", cod=100))  # must not raise
        self.assertEqual(s.pull_next().title, "Outage 2")

    def test_invalid_items_rejected(self):
        with self.assertRaises(ValueError):
            WorkItem.standard("Zero duration", cod=100, duration=0)
        with self.assertRaises(ValueError):
            WorkItem.standard("Negative CoD", cod=-1, duration=1)

    def test_empty_queue(self):
        self.assertIsNone(KanbanScheduler().pull_next())


if __name__ == "__main__":
    unittest.main()
