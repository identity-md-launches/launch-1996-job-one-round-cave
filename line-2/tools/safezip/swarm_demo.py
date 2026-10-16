#!/usr/bin/env python3
"""Offline node-budget demonstration using a captured public IMD description."""
import hashlib
import json
from pathlib import Path
import tempfile
import zipfile

from safezip import Rejected, local_path, process


def main():
    sample = local_path(Path(__file__).with_name('imd-openapi.json'))
    with sample.open('rb') as source:
        data = source.read(65537)
    expected = 'be142840c010710cb2a5b9e5c73e71d8e79ec4054c15661699d60bfa627be96a'
    digest = hashlib.sha256(data).hexdigest()
    if digest != expected:
        raise ValueError('public sample differs from the recorded capture')
    scratch = local_path('test/scratch')
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='safezip-swarm-', dir=scratch) as temp:
        root = Path(temp)
        source = root / 'public-description.zip'
        target = root / 'unpacked'
        name = 'docs/imd/openapi.json'
        with zipfile.ZipFile(source, 'w') as archive:
            # Stable metadata makes this offline demonstration reproducible.
            info = zipfile.ZipInfo(name)
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED)
        inspected = process(source, nodes=3, seconds=10)
        rejection = None
        try:
            process(source, target, nodes=2, seconds=10,
                    expected_sha256=inspected['archive_sha256'])
        except Rejected as error:
            rejection = str(error)
        if rejection != 'filesystem node limit exceeded':
            raise AssertionError('two-node budget did not reject this three-node archive')
        if target.exists() or list(root.glob('.safezip-*')):
            raise AssertionError('rejection left output behind')
        extracted = process(source, target, nodes=3, seconds=10,
                            expected_sha256=inspected['archive_sha256'])
        count = len(list(target.rglob('*')))
        if (target / name).read_bytes() != data or count != 3:
            raise AssertionError('extraction differs from the public capture')
        print(json.dumps({
            'ok': True, 'network_used': False,
            'sample_source': 'https://api.imd.fun/openapi.json',
            'sample_sha256': digest, 'sample_bytes': len(data),
            'archive_sha256': extracted['archive_sha256'],
            'zip_entries': len(extracted['entries']),
            'filesystem_nodes_excluding_destination_root': count,
            'nodes_2': rejection, 'nodes_3': 'extracted; bytes match capture',
            'failed_stage_removed': True,
        }, indent=2))


if __name__ == '__main__':
    main()
