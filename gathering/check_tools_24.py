#!/usr/bin/env python3
"""Run every documented line check/demo from disposable workspace copies."""
import concurrent.futures
import json
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent
SCRATCH = ROOT / 'test/scratch/gathering24'
JOBS = [
    (1, 'workplan/workplan.py', ['--self-test'], 0),
    (1, 'workplan/workplan.py', ['--demo', '--workers', '2', '--budget', '25'], 0),
    (1, 'replan/selftest.py', [], 0),
    (1, 'replan/replan.py', ['--demo', '--workers', '2', '--budget', '27'], 0),
    (1, 'optplan/optplan.py', ['--self-test'], 0),
    (1, 'optplan/optplan.py', ['--demo', '--workers', '2'], 0),
    (1, 'optplan/selftest.py', [], 0),
    (1, 'optplan/optplan.py', ['--idle-demo', '--workers', '2'], 0),
    (1, 'optplan/optplan.py', ['--input', 'line-1/tools/optplan/idle-example.json', '--workers', '2'], 0),
    (2, 'safezip/selftest.py', [], 0),
    (2, 'safezip/swarm_demo.py', [], 0),
    (3, 'rewardsplit/selftest.py', [], 0),
    (3, 'rewardsplit/rewardsplit.py', ['demo'], 0),
    (3, 'rewardreceipt/selftest.py', [], 0),
    (3, 'rewardreceipt/rewardreceipt.py', ['demo'], 0),
    (3, 'rewardcompare/selftest.py', [], 0),
    (3, 'rewardcompare/rewardcompare.py', ['demo'], 1),
    (3, 'rewardbatch/selftest.py', [], 0),
    (3, 'rewardbatch/rewardbatch.py', ['demo'], 0),
    (4, 'constcheck/selftest.py', [], 0),
    (4, 'constcheck/constcheck.py', ['demo'], 0),
    (4, 'apidelta/selftest.py', [], 0),
    (4, 'apidelta/apidelta.py', ['demo'], 0),
    (4, 'boundcheck/selftest.py', [], 0),
    (4, 'boundcheck/boundcheck.py', ['demo'], 0),
    (4, 'multiplecheck/selftest.py', [], 0),
    (4, 'multiplecheck/multiplecheck.py', ['demo'], 0),
    (4, 'multiplecheck/multiplecheck.py', ['compare',
        'line-4/tools/apidelta/imd-openapi.json',
        'line-4/tools/apidelta/imd-openapi.json'], 0),
]


def main():
    if Path.cwd().resolve() != ROOT:
        raise SystemExit('run from repository root')
    SCRATCH.mkdir(parents=True, exist_ok=True)
    for n in range(1, 5):
        shutil.copytree(ROOT / f'line-{n}/tools', SCRATCH / f'line-{n}/tools',
                        dirs_exist_ok=True)

    def run(job):
        n, script, args, expected = job
        command = [sys.executable, '-B',
                   str((SCRATCH / f'line-{n}/tools' / script).relative_to(ROOT)), *args]
        completed = subprocess.run(command, cwd=ROOT, capture_output=True,
                                   text=True, timeout=90)
        return dict(line=n, command=command, expected_exit=expected,
                    exit=completed.returncode, passed=completed.returncode == expected,
                    stdout=completed.stdout, stderr=completed.stderr)

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(run, JOBS))
    (ROOT / 'gathering/check-results-24.json').write_text(json.dumps(results, indent=2) + '\n')
    for row in results:
        print(('PASS' if row['passed'] else 'FAIL'), ' '.join(row['command']),
              'exit', row['exit'])
    return 0 if all(row['passed'] for row in results) else 1


if __name__ == '__main__':
    sys.exit(main())
