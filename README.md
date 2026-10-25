# Backend Engineering Systems & Algorithms

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A high-performance collection of production-grade backend systems and data structures built in Python. This repository demonstrates core principles in **Test-Driven Development (TDD)**, **advanced object-oriented architecture**, and **algorithmic efficiency** for distributed and concurrent service workloads.

---

## 🛠️ Included Modules & Architecture

### 1. FinTech Payment Processor (`payment_processor.py`)
A secure, audit-compliant financial transaction engine designed to handle multi-currency payments, tiered fee calculations, and regional taxation rules.
* **Tiered Fee Engine:** Dynamically calculates processing fees based on tiered volume thresholds (e.g., 1.5% down to 1.0%).
* **Regional Tax Compliance:** Automated tax rate application based on currency and origin jurisdiction (e.g., EU VAT handling).
* **Immutable Audit Trail:** Uses Python `dataclasses` and UUID generation to log immutable transaction events.
* **Defensive Copying:** Implements secure internal state management (`get_transaction_history` returns a deep copy) to protect against external collection mutation and data leaks.

### 2. Agile Scrum Board Engine (`scrum_board.py`)
A robust domain model simulating enterprise project management systems, sprint lifecycles, and velocity tracking.
* **Sprint & Backlog Modeling:** Manages item states (`todo`, `in-progress`, `done`) mapped to discrete sprint capacities.
* **Rolling Velocity Metrics:** Computes historical team velocity rolling averages across completed sprints.
* **Burndown Tracking:** Generates programmatic remaining-effort arrays for burndown chart rendering.

### 3. Kanban Priority-Queue Scheduler (`kanban_scheduler.py`)
An advanced scheduling framework leveraging Python’s `heapq` priority queue to optimize workflow efficiency under restrictive **Work-In-Progress (WIP)** limits.
* **Service Class Prioritization:** Implements strict priority inversion handling for `EXPEDITE` (production outages) versus `STANDARD` and `INTANGIBLE` technical debt tasks.
* **CD3 Optimization:** Automatically calculates and sorts items using the **Cost of Delay Divided by Duration (CD3)** lean economic metric to maximize throughput.
* **WIP Enforcement:** Programmatically blocks queue overloading with strict threshold checks.

---

## 🧪 Test-Driven Development (TDD) & Quality Assurance
All modules are backed by comprehensive, self-contained unit test suites utilizing Python’s native `assert` syntax. Tests cover state isolation, boundary limits, and edge cases.

To execute the verification test suites locally:
```bash
python payment_processor.py
python scrum_board.py
python kanban_scheduler.py
