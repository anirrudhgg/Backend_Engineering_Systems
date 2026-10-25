import heapq
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum

class ServiceClass(IntEnum):
    """Lower number = higher priority in the queue."""
    EXPEDITE = 0      # Production down — skip the queue
    FIXED_DATE = 1    # Regulatory deadline — time-critical
    STANDARD = 2      # Normal feature work — FIFO
    INTANGIBLE = 3    # Tech debt — do when nothing else waits

@dataclass(order=True)
class WorkItem:
    priority: int                    # ServiceClass value
    cost_of_delay_per_week: float   # £ per week if not done
    duration_weeks: float           # estimated duration
    title: str = field(compare=False)
    deadline: datetime | None = field(default=None, compare=False)
    
    @property
    def cd3_score(self) -> float:
        """CD3 = Cost of Delay / Duration. Higher = do first."""
        if self.duration_weeks == 0:
            return float('inf')
        return self.cost_of_delay_per_week / self.duration_weeks
    
    @classmethod
    def expedite(cls, title: str, cod: float) -> "WorkItem":
        return cls(ServiceClass.EXPEDITE, cod, 0.5, title)
    
    @classmethod
    def fixed_date(cls, title: str, cod: float, 
                   deadline: datetime, duration: float) -> "WorkItem":
        return cls(ServiceClass.FIXED_DATE, cod, duration, title, deadline)
    
    @classmethod
    def standard(cls, title: str, cod: float, duration: float) -> "WorkItem":
        return cls(ServiceClass.STANDARD, cod, duration, title)

class KanbanScheduler:
    def __init__(self, wip_limit: int = 4):
        self._queue: list[WorkItem] = []
        self._in_progress: list[WorkItem] = []
        self.wip_limit = wip_limit
        self._expedite_count = 0
    
    def add(self, item: WorkItem) -> None:
        if item.priority == ServiceClass.EXPEDITE:
            self._expedite_count += 1
            if self._expedite_count > 1:
                raise ValueError(
                    "WIP limit for Expedite is 1. "
                    "Multiple expedite items = system on fire."
                )
        heapq.heappush(self._queue, item)
    
    def pull_next(self) -> WorkItem | None:
        """Pull highest-priority item if WIP limit allows."""
        if len(self._in_progress) >= self.wip_limit:
            return None  # WIP limit enforced
        if not self._queue:
            return None
        item = heapq.heappop(self._queue)
        self._in_progress.append(item)
        return item
    
    def prioritised_backlog(self) -> list[WorkItem]:
        """Show backlog sorted by CD3 within each service class."""
        by_class: dict[int, list[WorkItem]] = {}
        for item in self._queue:
            by_class.setdefault(item.priority, []).append(item)
        result = []
        for cls in sorted(by_class.keys()):
            # Within each class, sort by CD3 score (highest first)
            result.extend(sorted(by_class[cls], 
                                key=lambda x: -x.cd3_score))
        return result

if __name__ == "__main__":
    scheduler = KanbanScheduler(wip_limit=2)
    scheduler.add(WorkItem.expedite("Fix Production Database", 10000))
    scheduler.add(WorkItem.standard("Update UI CSS", 500, 2))
    
    print("Prioritized Backlog:")
    for item in scheduler.prioritised_backlog():
        print(f"- {item.title} (Priority: {item.priority.name}, CD3: {item.cd3_score})")