#!/usr/bin/env python3
"""Exercise the four lines together on saved public bytes, without sending anything."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parent.parent


def main():
    if Path.cwd().resolve() != ROOT:
        raise SystemExit('run from repository root')
    scratch = ROOT / 'test/scratch'
    scratch.mkdir(parents=True, exist_ok=True)
    results = []
    with tempfile.TemporaryDirectory(prefix='gathering24-', dir=scratch) as directory:
        work = Path(directory)
        archives = []
        for label, source in [('old', 'shared/api_bundle/imd-openapi.json'),
                              ('new', 'gathering/imd-openapi-current-24.json')]:
            archive_path = work / (label + '.zip')
            with zipfile.ZipFile(archive_path, 'w') as archive:
                archive.writestr('openapi.json', (ROOT / source).read_bytes())
                archive.writestr('inert-note.txt', 'public API description only\n')
            archives.append((str(archive_path.relative_to(ROOT)),
                             hashlib.sha256(archive_path.read_bytes()).hexdigest()))
        old, new = archives
        unpacked = str((work / 'unpacked').relative_to(ROOT))
        report = str((work / 'allocation.json').relative_to(ROOT))
        batch = str((work / 'batch.json').relative_to(ROOT))
        request = 'line-3/tools/rewardsplit/example.json'
        metadata = 'line-3/tools/rewardsplit/zto-mainnet.json'
        jobs = [
            ('exact plan', 'line-1/tools/optplan/optplan.py', ['--demo', '--workers', '2'], 0),
            ('approved ZIP extraction', 'line-2/tools/safezip/safezip.py',
             ['extract', new[0], unpacked, '--sha256', new[1], '--seconds', '10'], 0),
            ('exact ZTO allocation', 'line-3/tools/rewardsplit/rewardsplit.py',
             ['allocate', '--input', request, '--metadata', metadata, '--output', report], 0),
            ('verified receipt', 'line-3/tools/rewardreceipt/rewardreceipt.py',
             ['verify', '--request', request, '--metadata', metadata, '--report', report], 0),
            ('build review batches', 'line-3/tools/rewardbatch/rewardbatch.py',
             ['build', '--request', request, '--report', report, '--metadata', metadata,
              '--batch-size', '2', '--output', batch], 0),
            ('verify review batches', 'line-3/tools/rewardbatch/rewardbatch.py',
             ['verify', '--request', request, '--report', report, '--metadata', metadata,
              '--bundle', batch], 0),
            ('budget paradox warning', 'line-3/tools/rewardcompare/rewardcompare.py', ['demo'], 1),
            ('fresh public API comparison', 'line-4/tools/constcheck/constcheck.py',
             ['compare', 'shared/api_bundle/imd-openapi.json', 'gathering/imd-openapi-current-24.json'], 0),
            ('approved shared ZIP comparison', 'shared/api_bundle/api_bundle.py',
             [old[0], new[0], '--old-sha256', old[1], '--new-sha256', new[1],
              '--seconds', '10', '--nodes', '2'], 0),
            ('reject too-small shared node budget', 'shared/api_bundle/api_bundle.py',
             [old[0], new[0], '--nodes', '1'], 2),
        ]
        for label, script, args, expected in jobs:
            command = [sys.executable, '-B', script, *args]
            completed = subprocess.run(command, cwd=ROOT, capture_output=True,
                                       text=True, timeout=30)
            results.append(dict(label=label, command=command, expected_exit=expected,
                                exit=completed.returncode,
                                passed=completed.returncode == expected,
                                stdout=completed.stdout, stderr=completed.stderr))
        if (work / 'unpacked/openapi.json').read_bytes() != (ROOT / 'gathering/imd-openapi-current-24.json').read_bytes():
            raise AssertionError('extracted public description differs from capture')
        allocation = json.loads((work / 'allocation.json').read_text())
        if sum(int(row['units']) for row in allocation['allocations']) != 10**18:
            raise AssertionError('ZTO allocation failed conservation')
        warning = json.loads(results[6]['stdout'])
        if warning['contributors_moving_against_budget'] != ['d', 'e']:
            raise AssertionError('illustrative budget paradox was not flagged')
        bundle = json.loads(results[8]['stdout'])
        if bundle['operations_compared'] != 5 or bundle['findings']:
            raise AssertionError('unchanged public API comparison differed')
        batches = json.loads((work / 'batch.json').read_text())
        assert batches['batch_count'] == 2
        assert sum(int(b['units']) for b in batches['batches']) == 10**18
        assert [r for b in batches['batches'] for r in b['allocations']] == allocation['allocations']
    (ROOT / 'gathering/integration-results-24.json').write_text(json.dumps(results, indent=2) + '\n')
    for row in results:
        print(('PASS' if row['passed'] else 'FAIL'), row['label'], 'exit', row['exit'])
    return 0 if all(row['passed'] for row in results) else 1


if __name__ == '__main__':
    sys.exit(main())
