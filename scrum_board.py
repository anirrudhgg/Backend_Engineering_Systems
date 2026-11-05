"""Scrum board: sprints with a capacity, item states, velocity and a daily burndown."""
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

STATES = ("todo", "in-progress", "done")


@dataclass
class BacklogItem:
    id: str
    title: str
    description: str
    story_points: int
    state: str = "todo"
    sprint_id: Optional[str] = None
    done_on: Optional[date] = None  # set when the item moves to "done"


@dataclass
class Sprint:
    id: str
    goal: str
    start_date: date
    end_date: date
    capacity: int
    items: list[BacklogItem] = field(default_factory=list)
    velocity: int = 0  # story points completed, set when the sprint is completed

    @property
    def committed_points(self) -> int:
        return sum(item.story_points for item in self.items)

    def completion_percentage(self) -> float:
        if not self.items:
            return 0.0
        done_count = sum(1 for item in self.items if item.state == "done")
        return done_count / len(self.items) * 100


class Board:
    def __init__(self):
        self._sprints: dict[str, Sprint] = {}
        self._completed_sprints: list[Sprint] = []

    def start_sprint(self, goal: str, capacity: int, items: list[BacklogItem],
                     start: Optional[date] = None, length_days: int = 14) -> Sprint:
        points = sum(item.story_points for item in items)
        if points > capacity:
            raise ValueError(f"{points} story points exceed the sprint capacity of {capacity}.")

        start = start or date.today()
        sprint = Sprint(
            id=f"S{len(self._sprints) + 1}",
            goal=goal,
            start_date=start,
            end_date=start + timedelta(days=length_days - 1),
            capacity=capacity,
            items=items,
        )
        for item in items:
            item.sprint_id = sprint.id
        self._sprints[sprint.id] = sprint
        return sprint

    def move_item(self, item_id: str, new_state: str, on: Optional[date] = None) -> None:
        if new_state not in STATES:
            raise ValueError(f"Unknown state '{new_state}'. Use one of {STATES}.")
        for sprint in self._sprints.values():
            for item in sprint.items:
                if item.id == item_id:
                    item.state = new_state
                    item.done_on = (on or date.today()) if new_state == "done" else None
                    return
        raise KeyError(f"No item with id '{item_id}' in any sprint.")

    def complete_sprint(self, sprint_id: str) -> Sprint:
        """Records the sprint's velocity (completed points) and closes it."""
        sprint = self._sprints[sprint_id]
        sprint.velocity = sum(i.story_points for i in sprint.items if i.state == "done")
        self._completed_sprints.append(sprint)
        return sprint

    def current_velocity(self, last_n: int = 3) -> float:
        """Rolling average velocity over the last `last_n` completed sprints."""
        recent = self._completed_sprints[-last_n:]
        if not recent:
            return 0.0
        return sum(s.velocity for s in recent) / len(recent)

    def burndown(self, sprint_id: str, until: Optional[date] = None) -> list[tuple[date, int]]:
        """Remaining story points at the end of each sprint day, up to `until` (default today)."""
        sprint = self._sprints.get(sprint_id)
        if not sprint:
            return []
        last_day = min(until or date.today(), sprint.end_date)
        result = []
        day = sprint.start_date
        while day <= last_day:
            done = sum(i.story_points for i in sprint.items
                       if i.state == "done" and i.done_on and i.done_on <= day)
            result.append((day, sprint.committed_points - done))
            day += timedelta(days=1)
        return result


if __name__ == "__main__":
    board = Board()
    start = date(2026, 11, 2)
    items = [BacklogItem("US-1", "Login", "", 5), BacklogItem("US-2", "Profile page", "", 3)]
    sprint = board.start_sprint("Accounts", capacity=10, items=items, start=start, length_days=5)
    board.move_item("US-1", "done", on=start + timedelta(days=1))
    board.move_item("US-2", "done", on=start + timedelta(days=3))
    for day, remaining in board.burndown(sprint.id, until=sprint.end_date):
        print(day, remaining)
    board.complete_sprint(sprint.id)
    print("Velocity:", board.current_velocity())
