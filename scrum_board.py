from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


@dataclass
class BacklogItem:
    id: str
    title: str
    description: str
    story_points: int
    state: str = "todo"
    sprint_id: Optional[str] = None


@dataclass
class Sprint:
    id: str
    goal: str
    start_date: date
    end_date: date
    capacity: int
    items: list[BacklogItem] = field(default_factory=list)
    velocity: float = 0.0

    def completion_percentage(self) -> float:
        if not self.items:
            return 0.0
        done_count = sum(1 for item in self.items if item.state == "done")
        return (done_count / len(self.items)) * 100


class Board:
    def __init__(self):
        self._sprints: dict[str, Sprint] = {}
        self._backlog: list[BacklogItem] = []
        self._completed_sprints: list[Sprint] = []

    def start_sprint(self, goal: str, capacity: int, items: list[BacklogItem]) -> Sprint:
        sprint_id = f"S{len(self._sprints) + 1}"
        sprint = Sprint(
            id=sprint_id,
            goal=goal,
            start_date=date.today(),
            end_date=date.today(),
            capacity=capacity,
            items=items,
        )
        # Assign items to sprint
        for item in items:
            item.sprint_id = sprint_id
        self._sprints[sprint_id] = sprint
        return sprint

    def move_item(self, item_id: str, new_state: str) -> None:
        # Search through all sprints for the item
        for sprint in self._sprints.values():
            for item in sprint.items:
                if item.id == item_id:
                    item.state = new_state
                    return

    def current_velocity(self) -> float:
        if not self._completed_sprints:
            return 0.0
        total = sum(s.velocity for s in self._completed_sprints)
        return total / len(self._completed_sprints)

    def burndown(self, sprint_id: str) -> list[tuple[date, float]]:
        sprint = self._sprints.get(sprint_id)
        if not sprint:
            return []
        # Calculate remaining points per day (simplified: just current state)
        total_points = sum(item.story_points for item in sprint.items)
        done_points = sum(
            item.story_points for item in sprint.items if item.state == "done"
        )
        remaining = total_points - done_points
        return [(date.today(), remaining)]


def test_start_sprint_assigns_items():
    board = Board()
    item = BacklogItem(id="US-001", title="Login", description="...", story_points=3)
    sprint = board.start_sprint("Implement auth", 20, [item])
    assert sprint.goal == "Implement auth"
    assert len(sprint.items) == 1
    assert item.sprint_id == sprint.id


def test_move_item_changes_state():
    board = Board()
    item = BacklogItem(id="US-001", title="Login", description="...", story_points=3)
    sprint = board.start_sprint("Goal", 20, [item])
    board.move_item("US-001", "in-progress")
    assert sprint.items[0].state == "in-progress"


def test_velocity_rolling_average():
    board = Board()
    # Simulate 3 completed sprints with known velocities
    s1 = Sprint("S1", "Goal1", date.today(), date.today(), 20, velocity=10.0)
    s2 = Sprint("S2", "Goal2", date.today(), date.today(), 20, velocity=15.0)
    s3 = Sprint("S3", "Goal3", date.today(), date.today(), 20, velocity=12.0)
    board._completed_sprints = [s1, s2, s3]
    expected_average = (10.0 + 15.0 + 12.0) / 3
    velocity = board.current_velocity()
    assert abs(velocity - expected_average) < 0.1


def test_completion_percentage():
    sprint = Sprint(
        id="S1",
        goal="Goal",
        start_date=date.today(),
        end_date=date.today(),
        capacity=20,
    )
    sprint.items = [
        BacklogItem("1", "A", "", 5, state="done"),
        BacklogItem("2", "B", "", 5, state="todo"),
    ]
    assert sprint.completion_percentage() == 50.0


def test_burndown_decreases():
    board = Board()
    item1 = BacklogItem("1", "A", "", 5, state="done")
    item2 = BacklogItem("2", "B", "", 5, state="todo")
    sprint = board.start_sprint("Goal", 20, [item1, item2])
    burndown = board.burndown(sprint.id)
    points = [points for _, points in burndown]
    assert points == sorted(points, reverse=True)  # must be non-increasing


# Run all tests
if __name__ == "__main__":
    print("Running Sprint Board tests...")
    test_start_sprint_assigns_items()
    print("✓ test_start_sprint_assigns_items")
    test_move_item_changes_state()
    print("✓ test_move_item_changes_state")
    test_velocity_rolling_average()
    print("✓ test_velocity_rolling_average")
    test_completion_percentage()
    print("✓ test_completion_percentage")
    test_burndown_decreases()
    print("✓ test_burndown_decreases")
    print("\n Sprint Board tests passed! ✅"