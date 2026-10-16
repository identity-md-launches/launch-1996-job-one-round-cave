#!/usr/bin/env python3
"""Offline structural, source-integrity and pixel-preservation checks for gathering 24."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

from check_delivery import jpeg_dimensions, png


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    root = Path(__file__).resolve().parent.parent
    assert Path.cwd().resolve() == root, 'run from repository root'
    expected = json.loads(Path('gathering/line-integrity-24.json').read_text())
    actual = {str(p): sha(p.read_bytes()) for n in range(1,5)
              for folder in (Path(f'line-{n}'), Path(f'dist/line-{n}'))
              for p in folder.rglob('*') if p.is_file()}
    assert actual == expected, 'line sources, records or previews changed'
    old_bytes = Path('artifacts/gathering/wall-v4.png').read_bytes()
    wall_bytes = Path('artifacts/gathering/wall-v5.png').read_bytes()
    canonical = Path('artifacts/gathering/wall.png')
    assert canonical.is_symlink() and canonical.readlink() == Path('wall-v5.png')
    assert canonical.read_bytes() == wall_bytes
    assert not Path('artifacts/gathering/wall-v5.png').is_symlink()
    old_size, old = png(old_bytes)
    size, wall = png(wall_bytes)
    assert old_size == size == (1254,1254)
    preservation = json.loads(Path('gathering/preservation-24.json').read_text())
    assert preservation['inherited_wall_sha256'] == sha(old_bytes)
    assert preservation['output_sha256'] == sha(wall_bytes)
    x,y,w,h = preservation['mark_rectangle']
    assert (x,y,w,h) == (1000,850,150,145)
    old_digest,new_digest = hashlib.sha256(),hashlib.sha256()
    changed = outside = 0
    for row in range(1254):
        a = old[row*1254*3:(row+1)*1254*3]
        b = wall[row*1254*3:(row+1)*1254*3]
        if y <= row < y+h:
            protected_a = a[:x*3]+a[(x+w)*3:]
            protected_b = b[:x*3]+b[(x+w)*3:]
            old_digest.update(protected_a); new_digest.update(protected_b)
            outside += sum(protected_a[i:i+3]!=protected_b[i:i+3] for i in range(0,len(protected_a),3))
            changed += sum(a[i:i+3]!=b[i:i+3] for i in range(x*3,(x+w)*3,3))
        else:
            old_digest.update(a); new_digest.update(b)
            outside += sum(a[i:i+3]!=b[i:i+3] for i in range(0,len(a),3))
    assert old_digest.digest() == new_digest.digest()
    assert outside == preservation['pixels_changed_outside'] == 0
    assert changed == preservation['changed_pixels_inside'] == 8498
    assert new_digest.hexdigest() == preservation['protected_rgb_sha256']
    jpg = Path('dist/gathering/24.jpg').read_bytes()
    assert jpeg_dimensions(jpg) == (512,512) and len(jpg) < 100000
    review = json.loads(Path('gathering/review-24.json').read_text())
    assert review['wall_dimensions'] == [1254,1254]
    assert review['wall_format'] == 'PNG' and review['preview_format'] == 'JPEG'
    assert review['preview_dimensions'] == [512,512]
    assert review['wall_sha256'] == sha(wall_bytes)
    assert review['preview_sha256'] == sha(jpg)
    assert review['visual_requirements_unmet'] == []
    assert review['visual_review']['digits_per_hand'] == [5,5]
    record = json.loads(Path('dist/gathering/24.json').read_text())
    assert set(record) == {'name','image','attributes'}
    assert record['image'] == 'https://api.imd.fun/artifacts/'+sha(wall_bytes)
    traits = {a['trait_type']:a['value'] for a in record['attributes']}
    assert len(record['attributes']) == len(traits) == 6
    assert set(traits) == {'Cave','Wall','Number','Left behind','Meaning','One thing'}
    assert traits['Cave'] == 'Lava' and traits['Wall'] == traits['One thing'] == 'Gathering'
    assert type(traits['Number']) is int and traits['Number'] == 24
    goals = [{'line':n,'goal':Path(f'line-{n}/GOAL.md').read_text().strip()} for n in range(1,5)]
    assert json.loads(Path('dist/goals.json').read_text()) == goals
    page = Path('dist/index.html').read_text()
    assert '<script' not in page and '<style>' in page
    count = placeholders = painted = 0
    bare = 'https://api.imd.fun/artifacts/09ee8caaf2f2f23c437db97f072627760da64d33dbd2b3409379a24a4a38d26a'
    for folder in [f'line-{n}' for n in range(1,5)]+['gathering']:
        for path in Path('dist',folder).glob('*.json'):
            assert re.fullmatch(r'\d{2}\.json',path.name)
            assert f'href="{folder}/{path.name}"' in page
            data = json.loads(path.read_text())
            assert re.fullmatch(r'https://api\.imd\.fun/artifacts/[0-9a-f]{64}',data['image'])
            count += 1
            if data['name'] == 'Not painted yet':
                assert data == {'name':'Not painted yet','image':bare,'attributes':[{'trait_type':'Cave','value':'Lava'}]}
                assert not path.with_suffix('.jpg').exists()
                placeholders += 1
            else:
                assert jpeg_dimensions(path.with_suffix('.jpg').read_bytes()) == (512,512)
                painted += 1
        for number in range(2,22):
            assert json.loads(Path('dist',folder,f'{number:02}.json').read_text())['name'] == 'Not painted yet'
        positions = [page.index(f'href="{folder}/{n:02}.json"') for n in (24,23,22,1)]
        assert positions == sorted(positions)
    assert (count,placeholders,painted) == (120,100,20)
    sources = json.loads(Path('shared/api_bundle/SOURCES.json').read_text())
    assert len(sources) == 5
    for destination,entry in sources.items():
        assert sha(Path(entry['source']).read_bytes()) == entry['source_sha256']
        assert sha(Path('shared/api_bundle',destination).read_bytes()) == entry['sha256']
    checks = json.loads(Path('gathering/check-results-24.json').read_text())
    trials = json.loads(Path('gathering/integration-results-24.json').read_text())
    assert len(checks) == 28 and len(trials) == 10
    for row in checks+trials:
        assert row['passed'] and row['exit'] == row['expected_exit']
    shared = json.loads(Path('gathering/shared-check-results-24.json').read_text())
    assert shared['tests_exit'] == shared['demo_exit'] == 0
    capture = Path('gathering/imd-openapi-current-24.json').read_bytes()
    live = json.loads(Path('gathering/live-check-24.json').read_text())
    assert live['sha256'] == sha(capture) and live['bytes'] == len(capture)
    assert live['method'] == 'GET' and live['status'] == 200
    assert Path('gathering/COINS.md').read_text().startswith('none\n')
    assert not Path('gathering/coin-order.json').exists()
    assert not Path('gathering/deploy-order.json').exists()
    status = subprocess.run(['git','status','--porcelain','--untracked-files=all'],
                            capture_output=True,text=True,check=True).stdout
    for line in status.splitlines():
        path = line[3:]
        assert path.startswith(('gathering/','shared/','artifacts/gathering/','dist/','test/scratch/')), path
        assert not path.startswith(tuple(f'dist/line-{n}/' for n in range(1,5))), path
        p = Path(path)
        if p.is_file() and not path.startswith(('artifacts/','test/scratch/')):
            assert p.stat().st_size <= 100000, path
    # The daemon, not this worker, uploads the named PNG; it is not staged/tracked.
    tracked = subprocess.run(['git','ls-files','--error-unmatch','artifacts/gathering/wall-v5.png'],
                             capture_output=True,text=True)
    assert tracked.returncode == 1
    result = {'passed':True,'line_files_unchanged':len(actual),'gallery_records':count,
              'painted_records':painted,'placeholders_preserved':placeholders,
              'line_commands_passed':len(checks),'line_unittest_cases':sum(int(m.group(1)) for row in checks if (m:=re.search(r'Ran (\d+) tests?',row['stderr']))),
              'cross_line_trials_passed':len(trials),'shared_tests':24,
              'png_dimensions':list(size),'jpeg_dimensions':[512,512],
              'wall_sha256':sha(wall_bytes),'jpeg_bytes':len(jpg),
              'pixels_changed_inside':changed,'pixels_changed_outside':outside,
              'source_hashes_checked':True,'changed_paths_in_scope':True,
              'named_png_untracked':True,
              'limitation':'Local structural/byte checks do not certify behavior or artistic quality.'}
    Path('gathering/delivery-check-24.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
