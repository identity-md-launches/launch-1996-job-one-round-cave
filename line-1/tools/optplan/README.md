# Optplan

Prove the shortest schedule for a small offline dependency graph. It complements
Workplan's fast greedy plan: Optplan searches task starts at completion events,
including choices that deliberately leave workers idle. Python 3.9+,
standard library only; it never executes task labels, uses a network, or reads
environment variables.

From the repository root:

```sh
python3 -B line-1/tools/optplan/optplan.py --idle-demo --workers 2
```

Observed result in round 24: the five-task demonstration finishes at minute
**16**, reports `"proven_optimal": true`, and lists its worker schedule. It leaves
worker 2 idle for minute 0–1 so both builds can start at minute 1. The inherited
solver incorrectly reported **21** as optimal for this graph.

| Task | Minutes | Prerequisites | Returned interval |
| --- | ---: | --- | --- |
| prepare | 1 | none | 0–1 |
| build-a | 7 | prepare | 1–8 |
| build-b | 7 | prepare | 1–8 |
| integrate | 8 | both builds | 8–16 |
| background | 6 | none | 8–14 |

Starting background immediately occupies a worker until minute 6, delaying one
build until 6–13 and integration until 13–21. Waiting instead attains the
16-minute dependency-chain lower bound. Background is still completed; no task
is omitted. Durations here are illustrative caller estimates, not measurements.

The original `--demo --workers 2` still finishes in **11** minutes (15 with one
worker). Both demo commands return exit 0.

Use the same `{"tasks": [...]}` JSON shape as Workplan with `--input`. Exact
search accepts at most 14 tasks and integer-minute estimates only; use Workplan
or Replan for larger graphs, fractional estimates, and progress snapshots.
Inputs are limited to an ordinary workspace-local file of 100,000 bytes, read
with a bounded read. Duplicate JSON keys, cycles, unknown fields, missing or
duplicate task ids, and invalid durations are rejected. For the waiting example:

```sh
python3 -B line-1/tools/optplan/optplan.py --input line-1/tools/optplan/idle-example.json --workers 2
```

Search is exponential. `--max-states` defaults to 100,000 unique states and may
be set from 1 to 1,000,000. Exceeding it exits **1**, prints an error to stderr,
and emits **no schedule or optimality claim**. A completed search exits **0**.
The limit bounds search states, not wall-clock seconds or exact memory usage;
some graphs below 14 tasks will exceed it. Use Workplan for a quick heuristic
or explicitly increase the limit. Invalid input also exits 1. Argument syntax
errors use argparse's exit 2. Nothing is written by the planner CLI.

The solver
does not promise a real-world deadline: estimates, worker availability, and the
nonpreemptive model remain caller assumptions.

The original optimality argument was wrong: non-delay schedules need not
include an optimum. The repaired search considers every ready-task subset up
to the number of free workers, including the empty subset while work is active.
It advances to the next completion. With no active work, starting nothing
cannot improve the remaining finish, so that one choice is omitted.

Why completion events suffice: fix the worker assignment and per-worker order
of any optimal feasible schedule. Move each task as early as its prerequisites
and preceding task on that worker allow. This cannot increase its finish and
puts every start at zero or another task's completion. The search includes
these starts and intentional idle intervals. This argument assumes identical,
continuously available workers; positive integer durations; only finish-to-start
dependencies; and nonpreemptive tasks. There are no release dates, calendars,
skills, communication delays, or external resource constraints.

Check the regression and independent oracle with:

```sh
python3 -B line-1/tools/optplan/selftest.py
```

Observed: **10 tests passed**, including the 21→16 regression, 120 seeded graphs
with 1–6 tasks and 1–3 workers, and all 64 forward-edge DAGs on four ordered
tasks. The independent breadth-first oracle advances one minute at a time and
allows starts even without a completion. Each result is checked for task
coverage, durations, dependencies, worker nonoverlap and finish consistency.
Checks also cover deterministic input permutations, unchanged inputs, simultaneous
completions, a 14-task chain, state-limit boundaries, CLI failure without partial
output, bounded input and duplicate keys. All checks use only the standard
library; disposable input files live under `test/scratch/optplan/`.

The lightweight inherited check remains available:

```sh
python3 -B line-1/tools/optplan/optplan.py --self-test
```

It passes the original examples plus the intentional-waiting regression.
These are local observations, not a guarantee about supplied estimates.
The only runtime source dependency is the unchanged sibling
`../workplan/workplan.py`; keep both folders together. No install or network is
needed. The task labels are never executed.
