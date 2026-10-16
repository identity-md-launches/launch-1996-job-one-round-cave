#!/usr/bin/env python3
"""Offline functional and adversarial checks, using only disposable workspace data."""
from pathlib import Path
import stat
import hashlib
import io
import json
from unittest import mock
import struct
import tempfile
import unittest
import warnings
import zipfile

from safezip import process, Rejected


class SafeZipTests(unittest.TestCase):
    def setUp(self):
        scratch = Path('test/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix='safezip-test-', dir=scratch)
        self.root = Path(self.tmp.name)
        self.archive = self.root / 'input.zip'
        self.output = self.root / 'output'

    def tearDown(self):
        self.tmp.cleanup()

    def make(self, members, compression=zipfile.ZIP_STORED):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with zipfile.ZipFile(self.archive, 'w', compression=compression) as archive:
                for name, data in members:
                    archive.writestr(name, data)

    def reject(self, members, **limits):
        self.make(members)
        with self.assertRaises((Rejected, zipfile.BadZipFile)):
            process(self.archive, self.output, **limits)
        self.assertFalse(self.output.exists())
        self.assertFalse(list(self.root.glob('.safezip-*')))

    def test_roundtrip(self):
        self.make([('docs/readme.txt', b'hello\n'), ('empty/', b''), ('zero', b'')])
        before = process(self.archive)
        self.assertFalse(self.output.exists())
        result = process(self.archive, self.output)
        self.assertEqual(result['total_bytes'], 6)
        self.assertEqual(before['entries'], result['entries'])
        self.assertEqual((self.output / 'docs/readme.txt').read_bytes(), b'hello\n')
        self.assertTrue((self.output / 'empty').is_dir())
        self.assertEqual(result['entries'][0]['sha256'],
                         '5891b5b522d5df086d0ff0b110fbd9d21bb4fc7163af34d08286a2e846f6be03')

    def test_deflate(self):
        self.make([('data', b'abc' * 100)], zipfile.ZIP_DEFLATED)
        self.assertEqual(process(self.archive, self.output)['total_bytes'], 300)

    def test_paths(self):
        for name in ['../escape', '/absolute', 'a/../../escape', 'a\\escape',
                     'C:/drive', 'a//b', './a', 'a/./b', 'a/../b', 'NUL.txt',
                     'a.', 'a ', 'cafe\u0301', 'bad:stream', 'a\x01b', 'a/' * 33 + 'deep']:
            with self.subTest(name=name):
                self.reject([(name, b'x')])

    def test_collisions(self):
        for names in [('a', 'a'), ('A', 'a'), ('a', 'a/b'), ('a/b', 'a'),
                      ('A/b', 'a/c'), ('A/', 'a/b')]:
            with self.subTest(names=names):
                self.reject([(name, b'') for name in names])

    def test_explicit_directory_after_implicit(self):
        self.make([('a/b', b'x'), ('a/', b'')])
        process(self.archive, self.output)
        self.assertEqual((self.output / 'a/b').read_bytes(), b'x')

    def test_symlink_and_special_members(self):
        for mode in (stat.S_IFLNK, stat.S_IFIFO, stat.S_IFSOCK, stat.S_IFCHR):
            info = zipfile.ZipInfo('link')
            info.create_system = 3
            info.external_attr = (mode | 0o777) << 16
            self.reject([(info, b'target')])

    def test_byte_and_entry_limits(self):
        self.reject([('big', b'12345')], file_bytes=4)
        self.reject([('a', b'123'), ('b', b'456')], total_bytes=5)
        self.reject([('a', b''), ('b', b'')], entries=1)
        self.make([('big', b'0' * 10000)], zipfile.ZIP_DEFLATED)
        with self.assertRaises(Rejected):
            process(self.archive, self.output, ratio=2)
        with self.assertRaises(Rejected):
            process(self.archive, archive_bytes=1)
        with self.assertRaises(Rejected):
            process(self.archive, entries=0)

    def test_implicit_parents_count_toward_node_limit(self):
        self.make([('a/b/c/file', b'x')])
        # One ZIP entry needs four filesystem objects, before the stage root.
        with self.assertRaisesRegex(Rejected, 'filesystem node limit'):
            process(self.archive, self.output, entries=1, nodes=3)
        self.assert_unpublished()
        result = process(self.archive, self.output, entries=1, nodes=4)
        self.assertTrue(result['ok'])
        self.assertEqual(len(list(self.output.rglob('*'))), 4)
        self.assertEqual((self.output / 'a/b/c/file').read_bytes(), b'x')

    def test_shared_parents_count_once(self):
        self.make([('a/b/first', b'one'), ('a/b/second', b'two'), ('a/c', b'')])
        with self.assertRaisesRegex(Rejected, 'filesystem node limit'):
            process(self.archive, nodes=4)
        process(self.archive, self.output, nodes=5)
        self.assertEqual(len(list(self.output.rglob('*'))), 5)

    def test_explicit_parents_count_once_in_either_order(self):
        members = [('a/b/file', b'x'), ('a/b/', b''), ('a/', b'')]
        for ordered in (members, list(reversed(members))):
            with self.subTest(order=[name for name, _ in ordered]):
                self.make(ordered)
                self.assertTrue(process(self.archive, nodes=3)['ok'])
                with self.assertRaisesRegex(Rejected, 'filesystem node limit'):
                    process(self.archive, self.output, nodes=2)
                self.assert_unpublished()

    def test_empty_directories_and_zero_byte_files_count(self):
        self.make([('empty/', b''), ('zero', b'')])
        with self.assertRaisesRegex(Rejected, 'filesystem node limit'):
            process(self.archive, self.output, nodes=1)
        self.assert_unpublished()
        self.assertEqual(process(self.archive, self.output, nodes=2)['total_bytes'], 0)
        self.assertEqual(len(list(self.output.rglob('*'))), 2)

    def test_empty_archive_does_not_charge_stage_root(self):
        self.make([])
        process(self.archive, self.output, nodes=1)
        self.assertEqual(list(self.output.iterdir()), [])

    def test_node_limit_rejects_before_staging_or_payload_read(self):
        self.make([('a/b/file', b'content')])
        with mock.patch('safezip.tempfile.mkdtemp') as staging:
            with mock.patch('safezip.zipfile.ZipFile.open') as payload:
                for output in (None, self.output):
                    with self.assertRaisesRegex(Rejected, 'filesystem node limit'):
                        process(self.archive, output, nodes=2)
                staging.assert_not_called()
                payload.assert_not_called()
        self.assert_unpublished()

    def test_node_limit_independent_of_entry_limit(self):
        self.make([('a/b', b'x'), ('a/c', b'y')])
        with self.assertRaisesRegex(Rejected, 'entry limit'):
            process(self.archive, entries=1, nodes=100)
        with self.assertRaisesRegex(Rejected, 'filesystem node limit'):
            process(self.archive, entries=100, nodes=2)
        self.assertTrue(process(self.archive, entries=2, nodes=3)['ok'])

    def test_max_depth_and_unicode_node_boundary(self):
        name = '/'.join(['caf\u00e9'] * 31 + ['file'])
        self.make([(name, b'')])
        with self.assertRaisesRegex(Rejected, 'filesystem node limit'):
            process(self.archive, self.output, nodes=31)
        self.assert_unpublished()
        process(self.archive, self.output, nodes=32)
        self.assertEqual(len(list(self.output.rglob('*'))), 32)

    def test_resource_limits_require_positive_integers_before_read(self):
        for name in ('entries', 'file_bytes', 'total_bytes', 'archive_bytes', 'ratio', 'nodes'):
            for value in (0, -1, True, False, 1.0, 1.5, float('nan'),
                          float('inf'), float('-inf'), '2', None):
                with self.subTest(name=name, value=value):
                    with mock.patch.object(Path, 'open') as opened:
                        with self.assertRaisesRegex(Rejected, 'positive integer'):
                            process(self.archive, self.output, **{name: value})
                        opened.assert_not_called()
        self.assert_unpublished()

    def test_inventory_node_limit_validates_direct_calls(self):
        import argparse
        from safezip import inventory
        limits = argparse.Namespace(entries=10, file_bytes=10, total_bytes=100, ratio=200)
        self.make([('a/b', b'x')])
        with zipfile.ZipFile(self.archive) as archive:
            for value in (0, -1, True, 1.0, float('nan'), None):
                with self.subTest(value=value), self.assertRaises(Rejected):
                    inventory(archive, limits, node_limit=value)
            self.assertEqual(len(inventory(archive, limits, node_limit=2)[0]), 1)
            with self.assertRaisesRegex(Rejected, 'filesystem node limit'):
                inventory(archive, limits, node_limit=1)

    def test_nodes_cli(self):
        import subprocess
        self.make([('a/b/file', b'content')])
        script = str(Path(__file__).with_name('safezip.py'))
        for value in ('0', '-1', 'nan', '2', '2.5'):
            result = subprocess.run(['python3', '-B', script, 'extract', str(self.archive),
                                     str(self.output), '--nodes', value],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertNotIn('Traceback', result.stderr)
            self.assert_unpublished()
        result = subprocess.run(['python3', '-B', script, 'extract', str(self.archive),
                                 str(self.output), '--nodes', '3'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)['ok'])
        self.assertEqual((self.output / 'a/b/file').read_bytes(), b'content')

    def test_crc_failure_is_atomic(self):
        self.make([('first', b'good'), ('second', b'broken')])
        raw = bytearray(self.archive.read_bytes())
        offset = raw.index(b'broken')
        raw[offset] ^= 1
        self.archive.write_bytes(raw)
        with self.assertRaises(zipfile.BadZipFile):
            process(self.archive, self.output)
        self.assertFalse(self.output.exists())
        self.assertFalse(list(self.root.glob('.safezip-*')))

    def test_corrupt_deflate_cli_cleans_stage(self):
        import subprocess
        self.make([('first', b'good'), ('bad', b'payload' * 30)], zipfile.ZIP_DEFLATED)
        with zipfile.ZipFile(self.archive) as archive:
            info = archive.getinfo('bad')
            start = info.header_offset + 30 + len(info.filename.encode()) + len(info.extra)
            size = info.compress_size
        raw = bytearray(self.archive.read_bytes())
        raw[start:start + size] = b'\xff' * size
        self.archive.write_bytes(raw)
        result = subprocess.run(['python3', '-B', str(Path(__file__).with_name('safezip.py')),
                                 'extract', str(self.archive), str(self.output)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertNotIn('Traceback', result.stderr)
        self.assertFalse(self.output.exists())
        self.assertFalse(list(self.root.glob('.safezip-*')))

    def test_truncated_archive(self):
        self.archive.write_bytes(b'PK\x03\x04')
        with self.assertRaises(zipfile.BadZipFile):
            process(self.archive, self.output)
        self.assertFalse(self.output.exists())

    def test_output_no_clobber(self):
        self.make([('ok', b'x')])
        self.output.mkdir()
        (self.output / 'keep').write_text('original')
        with self.assertRaises(Rejected):
            process(self.archive, self.output)
        self.assertEqual((self.output / 'keep').read_text(), 'original')

    def test_symlink_paths_refused(self):
        self.make([('ok', b'x')])
        link = self.root / 'alias'
        link.symlink_to('input.zip')
        with self.assertRaises(Rejected):
            process(link)
        link.unlink()
        link.symlink_to('missing-directory', target_is_directory=True)
        with self.assertRaises(Rejected):
            process(self.archive, link / 'output')

    def test_outside_workspace_refused_without_read(self):
        with self.assertRaises(Rejected):
            process('../never-read-this.zip')
        self.make([('ok', b'x')])
        with self.assertRaises(Rejected):
            process(self.archive, '../never-write-this')

    def test_unsupported_compression(self):
        self.make([('ok', b'x')], zipfile.ZIP_BZIP2)
        with self.assertRaises(Rejected):
            process(self.archive)

    def test_encrypted_flag(self):
        self.make([('ok', b'x')])
        raw = bytearray(self.archive.read_bytes())
        central = raw.index(b'PK\x01\x02')
        struct.pack_into('<H', raw, central + 8, 1)
        self.archive.write_bytes(raw)
        with self.assertRaises(Rejected):
            process(self.archive)

    def test_archive_digest_and_approved_extraction(self):
        self.make([('ok', b'reviewed bytes')])
        digest = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        report = process(self.archive)
        self.assertEqual(report['archive_sha256'], digest)
        result = process(self.archive, self.output, expected_sha256=digest.upper())
        self.assertEqual(result['archive_sha256'], digest)
        self.assertEqual((self.output / 'ok').read_bytes(), b'reviewed bytes')

    def test_changed_archive_rejected_before_zip_parsing(self):
        self.make([('ok', b'original')])
        digest = process(self.archive)['archive_sha256']
        self.make([('ok', b'replacement')])
        with mock.patch('safezip.zipfile.ZipFile') as parser:
            with self.assertRaisesRegex(Rejected, 'differs from approved'):
                process(self.archive, self.output, expected_sha256=digest)
            parser.assert_not_called()
        self.assertFalse(self.output.exists())
        self.assertFalse(list(self.root.glob('.safezip-*')))

    def test_invalid_digest(self):
        self.make([('ok', b'original')])
        for digest in ('', '0' * 63, '0' * 65, 'g' * 64, ' ' + 'a' * 64, 42):
            with self.subTest(digest=digest), self.assertRaises(Rejected):
                process(self.archive, self.output, expected_sha256=digest)
        self.assertFalse(self.output.exists())

    def test_snapshot_resists_path_replacement(self):
        self.make([('ok', b'approved')])
        digest = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        original_zip = zipfile.ZipFile
        replacement = io.BytesIO()
        with original_zip(replacement, 'w') as archive:
            archive.writestr('ok', b'changed')

        def replace_path_then_parse(snapshot):
            self.archive.unlink()
            self.archive.write_bytes(replacement.getvalue())
            return original_zip(snapshot)

        with mock.patch('safezip.zipfile.ZipFile', side_effect=replace_path_then_parse):
            result = process(self.archive, self.output, expected_sha256=digest)
        self.assertEqual((self.output / 'ok').read_bytes(), b'approved')
        self.assertEqual(result['archive_sha256'], digest)
        self.assertNotEqual(hashlib.sha256(self.archive.read_bytes()).hexdigest(), digest)

    def test_actual_input_size_checked_after_stat(self):
        self.make([('ok', b'x')])
        original_open = Path.open

        def grow_before_open(path, *args, **kwargs):
            if path == self.archive and args == ('rb',):
                with original_open(path, 'ab') as writer:
                    writer.write(b'X' * 1024)
            return original_open(path, *args, **kwargs)

        size = self.archive.stat().st_size
        with mock.patch.object(Path, 'open', grow_before_open):
            with self.assertRaisesRegex(Rejected, 'while reading'):
                process(self.archive, self.output, archive_bytes=size)
        self.assertFalse(self.output.exists())

    def test_exact_archive_limit(self):
        self.make([('ok', b'x')])
        size = self.archive.stat().st_size
        self.assertTrue(process(self.archive, archive_bytes=size)['ok'])
        with self.assertRaises(Rejected):
            process(self.archive, archive_bytes=size - 1)

    def test_approved_digest_does_not_bypass_payload_checks(self):
        self.make([('ok', b'broken')])
        raw = bytearray(self.archive.read_bytes())
        raw[raw.index(b'broken')] ^= 1
        self.archive.write_bytes(raw)
        digest = hashlib.sha256(raw).hexdigest()
        with self.assertRaises(zipfile.BadZipFile):
            process(self.archive, self.output, expected_sha256=digest)
        self.assertFalse(self.output.exists())
        self.assertFalse(list(self.root.glob('.safezip-*')))

    def test_approval_cli(self):
        import subprocess
        self.make([('ok', b'reviewed')])
        script = str(Path(__file__).with_name('safezip.py'))
        inspected = subprocess.run(['python3', '-B', script, 'inspect', str(self.archive)],
                                   capture_output=True, text=True)
        self.assertEqual(inspected.returncode, 0, inspected.stderr)
        digest = json.loads(inspected.stdout)['archive_sha256']
        for wrong in ('0' * 64, 'not-a-digest'):
            result = subprocess.run(['python3', '-B', script, 'extract', str(self.archive),
                                     str(self.output), '--sha256', wrong],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertFalse(json.loads(result.stdout)['ok'])
            self.assertFalse(self.output.exists())
        result = subprocess.run(['python3', '-B', script, 'extract', str(self.archive),
                                 str(self.output), '--sha256', digest],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['archive_sha256'], digest)
        self.assertEqual((self.output / 'ok').read_bytes(), b'reviewed')

    def assert_unpublished(self):
        self.assertFalse(self.output.exists())
        self.assertFalse(list(self.root.glob('.safezip-*')))

    def test_cancellation_before_read(self):
        with mock.patch.object(Path, 'open') as opened:
            with self.assertRaisesRegex(Rejected, 'cancelled'):
                process(self.archive, self.output, cancelled=lambda: True)
            opened.assert_not_called()
        self.assert_unpublished()

    def test_cancel_during_snapshot(self):
        self.make([('large', b'x' * 150000)])
        calls = 0

        def cancel():
            nonlocal calls
            calls += 1
            return calls == 3  # Entry check, first read, then second read.

        with mock.patch('safezip.zipfile.ZipFile') as parser:
            with self.assertRaisesRegex(Rejected, 'cancelled'):
                process(self.archive, self.output, cancelled=cancel)
            parser.assert_not_called()
        self.assert_unpublished()

    def test_cancel_in_inventory(self):
        self.make([('a', b''), ('b', b'')])
        import safezip
        original = safezip.member_name
        visited = []

        def visit(info):
            visited.append(info.filename)
            return original(info)

        with mock.patch('safezip.member_name', side_effect=visit):
            with self.assertRaisesRegex(Rejected, 'cancelled'):
                process(self.archive, self.output, cancelled=lambda: bool(visited))
        self.assertEqual(visited, ['a'])
        self.assert_unpublished()

    def test_cancel_mid_payload_cleans_stage(self):
        self.make([('large', b'x' * 150000)])

        def cancel_after_chunk():
            return any((stage / 'large').exists()
                       and (stage / 'large').stat().st_size >= 65536
                       for stage in self.root.glob('.safezip-*'))

        with self.assertRaisesRegex(Rejected, 'cancelled'):
            process(self.archive, self.output, cancelled=cancel_after_chunk)
        self.assert_unpublished()

    def test_cancel_before_publish_empty_archive(self):
        self.make([])
        with self.assertRaisesRegex(Rejected, 'cancelled'):
            process(self.archive, self.output,
                    cancelled=lambda: bool(list(self.root.glob('.safezip-*'))))
        self.assert_unpublished()

    def test_time_budget_before_read_and_after_staging(self):
        self.make([('ok', b'content')])
        with mock.patch('safezip.time.monotonic', side_effect=[10, 11]):
            with self.assertRaisesRegex(Rejected, 'time budget'):
                process(self.archive, self.output, seconds=1)
        self.assert_unpublished()

        def clock():
            return 20 if list(self.root.glob('.safezip-*')) else 10

        with mock.patch('safezip.time.monotonic', side_effect=clock):
            with self.assertRaisesRegex(Rejected, 'time budget'):
                process(self.archive, self.output, seconds=5)
        self.assert_unpublished()

    def test_interruption_options_validate(self):
        for seconds in (0, -1, float('inf'), float('-inf'), float('nan'), True, '1', 10 ** 1000):
            with self.subTest(seconds=seconds), self.assertRaises(Rejected):
                process(self.archive, self.output, seconds=seconds)
        with self.assertRaisesRegex(Rejected, 'callable'):
            process(self.archive, cancelled=True)
        self.assert_unpublished()

    def test_generous_budget_and_non_cancelled_roundtrip(self):
        self.make([('ok', b'content')])
        with mock.patch('safezip.time.monotonic', return_value=10):
            result = process(self.archive, self.output, seconds=1,
                             cancelled=lambda: False)
        self.assertTrue(result['content_checked'])
        self.assertEqual((self.output / 'ok').read_bytes(), b'content')

    def test_budget_cli(self):
        import subprocess
        self.make([('ok', b'content')])
        script = str(Path(__file__).with_name('safezip.py'))
        for seconds in ('0', '-1', 'nan', 'inf', '1e-300'):
            result = subprocess.run(['python3', '-B', script, 'extract', str(self.archive),
                                     str(self.output), '--seconds', seconds],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertFalse(json.loads(result.stdout)['ok'])
            self.assert_unpublished()
        result = subprocess.run(['python3', '-B', script, 'extract', str(self.archive),
                                 str(self.output), '--seconds', '60'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)['ok'])

    def test_cli(self):
        import subprocess
        self.make([('ok', b'x')])
        script = Path(__file__).with_name('safezip.py')
        result = subprocess.run(['python3', '-B', str(script), 'inspect', str(self.archive)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"content_checked": true', result.stdout)
        result = subprocess.run(['python3', '-B', str(script), 'extract', str(self.archive),
                                 str(self.output), '--file-bytes', '0'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('"ok": false', result.stdout)


if __name__ == '__main__':
    unittest.main(verbosity=2)
