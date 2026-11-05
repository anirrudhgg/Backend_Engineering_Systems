"""Kanban scheduler: a priority queue ordered by service class, then by CD3, with WIP limits."""
import heapq
import itertools
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from typing import Optional


class ServiceClass(IntEnum):
    """Lower number = pulled first."""
    EXPEDITE = 0      # production down: skip the queue
    FIXED_DATE = 1    # deadline-driven work
    STANDARD = 2      # normal feature work
    INTANGIBLE = 3    # tech debt: done when nothing else is waiting


@dataclass
class WorkItem:
    service_class: ServiceClass
    cost_of_delay_per_week: float  # value lost per week of waiting
    duration_weeks: float
    title: str
    deadline: Optional[datetime] = field(default=None)

    def __post_init__(self):
        if self.cost_of_delay_per_week < 0:
            raise ValueError("Cost of delay cannot be negative.")
        if self.duration_weeks <= 0:
            raise ValueError("Duration must be positive.")

    @property
    def cd3_score(self) -> float:
        """CD3 = Cost of Delay / Duration. Higher = do first."""
        return self.cost_of_delay_per_week / self.duration_weeks

    @classmethod
    def expedite(cls, title: str, cod: float, duration: float = 0.5) -> "WorkItem":
        return cls(ServiceClass.EXPEDITE, cod, duration, title)

    @classmethod
    def fixed_date(cls, title: str, cod: float, deadline: datetime, duration: float) -> "WorkItem":
        return cls(ServiceClass.FIXED_DATE, cod, duration, title, deadline)

    @classmethod
    def standard(cls, title: str, cod: float, duration: float) -> "WorkItem":
        return cls(ServiceClass.STANDARD, cod, duration, title)

    @classmethod
    def intangible(cls, title: str, cod: float, duration: float) -> "WorkItem":
        return cls(ServiceClass.INTANGIBLE, cod, duration, title)


class KanbanScheduler:
    EXPEDITE_LIMIT = 1  # more than one expedite item at a time means the system is on fire

    def __init__(self, wip_limit: int = 4):
        if wip_limit < 1:
            raise ValueError("WIP limit must be at least 1.")
        self.wip_limit = wip_limit
        # Heap entries: (service class, -CD3, insertion order, item).
        # The insertion counter keeps equal items in FIFO order.
        self._queue: list[tuple[int, float, int, WorkItem]] = []
        self._in_progress: list[WorkItem] = []
        self._counter = itertools.count()

    def _expedite_count(self) -> int:
        queued = sum(1 for *_, item in self._queue if item.service_class == ServiceClass.EXPEDITE)
        active = sum(1 for item in self._in_progress if item.service_class == ServiceClass.EXPEDITE)
        return queued + active

    def add(self, item: WorkItem) -> None:
        if item.service_class == ServiceClass.EXPEDITE and self._expedite_count() >= self.EXPEDITE_LIMIT:
            raise ValueError("Only one expedite item is allowed at a time.")
        heapq.heappush(self._queue, (item.service_class, -item.cd3_score, next(self._counter), item))

    def pull_next(self) -> Optional[WorkItem]:
        """Starts the highest-priority item, unless the WIP limit is reached."""
        if len(self._in_progress) >= self.wip_limit or not self._queue:
            return None
        *_, item = heapq.heappop(self._queue)
        self._in_progress.append(item)
        return item

    def complete(self, item: WorkItem) -> None:
        """Finishes an in-progress item, freeing a WIP slot."""
        self._in_progress.remove(item)  # raises ValueError if it was not in progress

    def in_progress(self) -> list[WorkItem]:
        return list(self._in_progress)

    def prioritised_backlog(self) -> list[WorkItem]:
        """The queue in the exact order pull_next() will take it."""
        return [item for *_, item in sorted(self._queue)]


if __name__ == "__main__":
    scheduler = KanbanScheduler(wip_limit=2)
    scheduler.add(WorkItem.standard("Update UI CSS", cod=500, duration=2))
    scheduler.add(WorkItem.standard("Checkout redesign", cod=3000, duration=3))
    scheduler.add(WorkItem.intangible("Refactor logging", cod=200, duration=1))
    scheduler.add(WorkItem.expedite("Fix production database", cod=10000))

    print("Prioritised backlog:")
    for item in scheduler.prioritised_backlog():
        print(f"- {item.title} ({item.service_class.name}, CD3 {item.cd3_score:.0f})")
