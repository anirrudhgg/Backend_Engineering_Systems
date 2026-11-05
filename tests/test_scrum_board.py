import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scrum_board import Board, BacklogItem, Sprint  # noqa: E402

START = date(2026, 11, 2)


def item(item_id, points, state="todo"):
    return BacklogItem(item_id, f"Item {item_id}", "", points, state=state)


class TestSprints(unittest.TestCase):
    def setUp(self):
        self.board = Board()

    def test_start_sprint_assigns_items_and_dates(self):
        it = item("US-1", 3)
        sprint = self.board.start_sprint("Auth", 20, [it], start=START, length_days=14)
        self.assertEqual(it.sprint_id, sprint.id)
        self.assertEqual(sprint.end_date, START + timedelta(days=13))

    def test_capacity_enforced(self):
        with self.assertRaises(ValueError):
            self.board.start_sprint("Too much", 5, [item("1", 3), item("2", 3)])

    def test_move_item(self):
        sprint = self.board.start_sprint("Goal", 20, [item("US-1", 3)])
        self.board.move_item("US-1", "in-progress")
        self.assertEqual(sprint.items[0].state, "in-progress")

    def test_invalid_state_and_unknown_item(self):
        self.board.start_sprint("Goal", 20, [item("US-1", 3)])
        with self.assertRaises(ValueError):
            self.board.move_item("US-1", "finished")
        with self.assertRaises(KeyError):
            self.board.move_item("US-999", "done")

    def test_completion_percentage(self):
        sprint = Sprint("S1", "Goal", START, START, 20, items=[item("1", 5, "done"), item("2", 5)])
        self.assertEqual(sprint.completion_percentage(), 50.0)


class TestMetrics(unittest.TestCase):
    def setUp(self):
        self.board = Board()

    def run_sprint(self, done_points, open_points):
        items = [item(f"d{done_points}", done_points), item(f"o{open_points}", open_points)]
        sprint = self.board.start_sprint("Goal", 100, items, start=START)
        self.board.move_item(items[0].id, "done", on=START)
        return self.board.complete_sprint(sprint.id)

    def test_velocity_is_completed_points(self):
        self.assertEqual(self.run_sprint(8, 5).velocity, 8)

    def test_rolling_average_uses_last_three(self):
        for points in (2, 10, 15, 12):
            self.run_sprint(points, 1)
        self.assertAlmostEqual(self.board.current_velocity(), (10 + 15 + 12) / 3)

    def test_no_completed_sprints(self):
        self.assertEqual(self.board.current_velocity(), 0.0)

    def test_burndown_per_day(self):
        items = [item("A", 5), item("B", 3)]
        sprint = self.board.start_sprint("Goal", 10, items, start=START, length_days=4)
        self.board.move_item("A", "done", on=START + timedelta(days=1))
        self.board.move_item("B", "done", on=START + timedelta(days=3))
        remaining = [points for _, points in self.board.burndown(sprint.id, until=sprint.end_date)]
        self.assertEqual(remaining, [8, 3, 3, 0])


if __name__ == "__main__":
    unittest.main()
