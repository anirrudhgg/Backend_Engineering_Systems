# Backend Engineering Systems

Three small Python domain models, each with a `unittest` suite. Together they practise modelling business rules in code: money handling, state changes and priority scheduling.

| Module | What it models | Key techniques |
|---|---|---|
| `payment_processor.py` | Payments with tiered fees, regional tax and an audit trail | `Decimal` money, frozen dataclasses, input validation |
| `scrum_board.py` | Sprints, item states, velocity and burndown | Dataclasses, date handling, rule enforcement |
| `kanban_scheduler.py` | A work queue with service classes and WIP limits | `heapq` priority queue, CD3 ordering |

Requires Python 3.10+ and no extra packages.

```
python -m unittest discover tests -v    # run all 31 tests
python payment_processor.py             # short demo of each module
python scrum_board.py
python kanban_scheduler.py
```

## Payment processor

- **Exact money:** amounts, fees and taxes are `Decimal` values rounded to cents, never `float`
- **Marginal fee tiers:** 1.5% on the first 1,000, 1.2% up to 5,000 and 1.0% above, applied like tax brackets so a larger payment never pays a smaller fee
- **Regional tax:** looked up from the currency's region (the 15% EU rate is an example value)
- **Tamper-proof records:** receipts and audit events are frozen dataclasses, and the history is returned as a tuple, so callers can read it but not change it
- **Validation:** zero or negative amounts and unsupported currencies raise `ValueError`

## Scrum board

- Sprints have a start and end date and reject items whose story points exceed the capacity
- Items move between `todo`, `in-progress` and `done`; unknown states and IDs raise errors
- Completing a sprint records its velocity (completed points); `current_velocity()` averages the last three sprints
- `burndown()` returns the remaining points for each day of the sprint, based on when each item was finished

## Kanban scheduler

- Items are pulled by **service class** first (Expedite, Fixed Date, Standard, Intangible), then by **CD3** (Cost of Delay ÷ Duration, highest first), then first-in-first-out
- `pull_next()` respects the WIP limit, and `complete()` frees a slot
- Only one Expedite item can be active or queued at a time
- `prioritised_backlog()` shows the queue in exactly the order `pull_next()` will take it

## Tests

`tests/` holds 31 tests, including boundary cases: fees just either side of a tier limit, rejected inputs, attempts to modify stored receipts, rolling velocity over more than three sprints, and pull order matching the displayed backlog.

## Project structure

```
├── payment_processor.py
├── scrum_board.py
├── kanban_scheduler.py
└── tests/
    ├── test_payment_processor.py
    ├── test_scrum_board.py
    └── test_kanban_scheduler.py
```
