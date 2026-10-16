#!/usr/bin/env python3
"""Independent tiny time-grid oracle and Optplan regression checks."""
from collections import deque
import copy
import itertools
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

import optplan


def minute_oracle(data, workers):
    """Breadth-first search at EVERY integer minute, not completion events.

    Durations in these tests are small. A state is the set of completed tasks
    and a full vector of remaining times. Every available subset, including no
    starts, advances exactly one minute. Repeated states are reached no earlier
    by a later path, so a visited set is safe. The first all-done state wins.
    """
    rows = data['tasks']
    names = {row['id']: i for i, row in enumerate(rows)}
    prerequisites = [sum(1 << names[d] for d in row.get('after', [])) for row in rows]
    target = (1 << len(rows)) - 1
    initial = (0, (0,) * len(rows))
    queue = deque([(initial, 0)])
    visited = {initial}
    while queue:
        (done, remaining), now = queue.popleft()
        if done == target:
            return now
        ready = [i for i in range(len(rows)) if not (done >> i) & 1
                 and remaining[i] == 0 and prerequisites[i] & ~done == 0]
        slots = workers - sum(t > 0 for t in remaining)
        for count in range(min(slots, len(ready)) + 1):
            for chosen in itertools.combinations(ready, count):
                next_times = list(remaining)
                for task in chosen:
                    next_times[task] = rows[task]['minutes']
                next_done = done
                for task, time in enumerate(next_times):
                    if time == 1:
                        next_done |= 1 << task
                    next_times[task] = max(0, time - 1)
                state = (next_done, tuple(next_times))
                if state not in visited:
                    visited.add(state)
                    queue.append((state, now + 1))
    raise AssertionError('oracle found no schedule')


class OptplanTests(unittest.TestCase):
    def assert_schedule(self, data, workers, result):
        indexed = {entry['task']: entry for entry in result['schedule']}
        self.assertEqual(len(indexed), len(result['schedule']))
        self.assertEqual(set(indexed), {row['id'] for row in data['tasks']})
        self.assertTrue(result['proven_optimal'])
        self.assertLessEqual(result['states_examined'], result['state_limit'])
        for row in data['tasks']:
            entry = indexed[row['id']]
            self.assertGreaterEqual(entry['start'], 0)
            self.assertEqual(entry['finish'] - entry['start'], row['minutes'])
            self.assertIn(entry['worker'], range(1, workers + 1))
            for dep in row.get('after', []):
                self.assertLessEqual(indexed[dep]['finish'], entry['start'])
        for worker in range(1, workers + 1):
            entries = sorted((entry for entry in indexed.values() if entry['worker'] == worker),
                             key=lambda entry: entry['start'])
            for left, right in zip(entries, entries[1:]):
                self.assertLessEqual(left['finish'], right['start'])
        self.assertEqual(result['finish'], max(entry['finish'] for entry in indexed.values()))

    def test_idle_regression(self):
        data = optplan.idle_demo()
        result = optplan.exact(data, 2)
        self.assertEqual(result['finish'], 16)
        self.assertEqual(minute_oracle(data, 2), 16)
        self.assert_schedule(data, 2, result)
        self.assertEqual(sum(entry['start'] == 0 for entry in result['schedule']), 1)
        # The original greedy plan starts background immediately and takes 21.
        self.assertEqual(optplan._workplan.plan(data, 2)['finish'], 21)

    def test_seeded_oracle(self):
        rng = random.Random(73724)
        for case in range(120):
            rows = [{'id': str(i), 'minutes': rng.randint(1, 4),
                     'after': [str(j) for j in range(i) if rng.random() < .35]}
                    for i in range(rng.randint(1, 6))]
            data = {'tasks': rows}
            original = copy.deepcopy(data)
            workers = rng.randint(1, 3)
            with self.subTest(case=case):
                result = optplan.exact(data, workers)
                self.assertEqual(result['finish'], minute_oracle(data, workers))
                self.assert_schedule(data, workers, result)
                self.assertEqual(data, original)
                reversed_data = {'tasks': [{**row, 'after': list(reversed(row['after']))}
                                           for row in reversed(rows)]}
                self.assertEqual(result, optplan.exact(reversed_data, workers))

    def test_all_four_task_dags(self):
        edges = list(itertools.combinations(range(4), 2))
        for mask in range(1 << len(edges)):
            rows = [{'id': str(i), 'minutes': [1, 3, 2, 4][i], 'after': []} for i in range(4)]
            for bit, (parent, child) in enumerate(edges):
                if mask & (1 << bit):
                    rows[child]['after'].append(str(parent))
            data = {'tasks': rows}
            with self.subTest(mask=mask):
                result = optplan.exact(data, 2)
                self.assertEqual(result['finish'], minute_oracle(data, 2))
                self.assert_schedule(data, 2, result)

    def test_serial_and_unlimited_workers(self):
        data = optplan.idle_demo()
        self.assertEqual(optplan.exact(data, 1)['finish'], 29)
        self.assertEqual(optplan.exact(data, 64)['finish'], 16)
        self.assert_schedule(data, 64, optplan.exact(data, 64))

    def test_simultaneous_completions(self):
        data = {'tasks': [{'id': 'a', 'minutes': 2}, {'id': 'b', 'minutes': 2},
                          {'id': 'c', 'minutes': 3, 'after': ['a', 'b']}]}
        self.assertEqual(optplan.exact(data, 2)['finish'], 5)
        self.assert_schedule(data, 2, optplan.exact(data, 2))

    def test_fourteen_task_chain(self):
        data = {'tasks': [{'id': str(i), 'minutes': i+1,
                           'after': [str(i-1)] if i else []} for i in range(14)]}
        result = optplan.exact(data, 2)
        self.assertEqual(result['finish'], 105)
        self.assert_schedule(data, 2, result)

    def test_state_limit(self):
        with self.assertRaisesRegex(ValueError, 'optimality not established'):
            optplan.exact(optplan.idle_demo(), 2, max_states=1)
        count = optplan.exact(optplan.idle_demo(), 2)['states_examined']
        self.assertEqual(optplan.exact(optplan.idle_demo(), 2, count)['finish'], 16)
        with self.assertRaisesRegex(ValueError, 'state limit'):
            optplan.exact(optplan.idle_demo(), 2, count-1)
        for bad in (0, -1, True, 1.5, 1000001):
            with self.assertRaisesRegex(ValueError, 'max_states'):
                optplan.exact(optplan.demo(), 2, bad)

    def test_invalid_graphs(self):
        for bad in ({'tasks': []}, {'tasks': [{'id': 'a', 'minutes': True}]},
                    {'tasks': [{'id': 'a', 'minutes': 1.5}]},
                    {'tasks': [{'id': 'a', 'minutes': 0}]},
                    {'tasks': [{'id': 'a', 'minutes': 1, 'after': ['a']}]},
                    {'tasks': [{'id': 'a', 'minutes': 1, 'after': ['missing']}]},
                    {'tasks': [{'id': 'a', 'minutes': 1}, {'id': 'a', 'minutes': 2}]},
                    {'tasks': [{'id': str(i), 'minutes': 1} for i in range(15)]}):
            with self.subTest(data=bad), self.assertRaises(ValueError):
                optplan.exact(bad)
        for workers in (0, 65, True, 2.0):
            with self.assertRaises(ValueError):
                optplan.exact(optplan.demo(), workers)

    def test_bounded_strict_json(self):
        scratch = Path('test/scratch/optplan')
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as tmp:
            path = Path(tmp) / 'input.json'
            path.write_text(json.dumps(optplan.idle_demo()))
            self.assertEqual(optplan.read_input(str(path)), optplan.idle_demo())
            for raw in ('{"tasks":[],"tasks":[]}',
                        '{"tasks":[{"id":"a","minutes":1,"minutes":2}]}',
                        'x' * 100001, '{'):
                path.write_text(raw)
                with self.assertRaises(ValueError):
                    optplan.read_input(str(path))
            with self.assertRaises(ValueError):
                optplan.read_input(tmp)
            # Rejection must occur before reading an outside-workspace target.
            with self.assertRaises(ValueError):
                optplan.read_input(str(Path.cwd().parent / 'not-an-input.json'))

    def test_cli_success_and_limit_failure(self):
        command = [sys.executable, '-B', str(Path(optplan.__file__)), '--idle-demo']
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['finish'], 16)
        result = subprocess.run(command + ['--max-states', '1'], capture_output=True,
                                text=True, timeout=30)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, '')
        self.assertIn('optimality not established', result.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
