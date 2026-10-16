"""Offline integration tests; all disposable files live in test/scratch."""
import copy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

import api_bundle as bundle


class BundleTests(unittest.TestCase):
    def setUp(self):
        scratch = Path('test/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=scratch)
        self.root = Path(self.tmp.name)
        self.doc = {'openapi': '3.1.0', 'paths': {'/items': {'get': {
            'responses': {'200': {'description': 'OK'}}}}}}

    def tearDown(self):
        self.tmp.cleanup()

    def archive(self, name, doc=None, extra=(), compression=zipfile.ZIP_STORED):
        path = self.root / name
        with zipfile.ZipFile(path, 'w', compression=compression) as output:
            output.writestr('openapi.json', json.dumps(self.doc if doc is None else doc))
            for filename, data in extra:
                output.writestr(filename, data)
        return path

    def test_unchanged_with_inert_executable(self):
        a = self.archive('a.zip', extra=[('script.py', 'raise RuntimeError("NEVER EXECUTE")')])
        before = sorted(p.name for p in self.root.iterdir())
        report = bundle.compare(a, a)
        self.assertEqual(report['status'], 'no_detected_breakage')
        self.assertEqual(len(report['bundle_inputs']['old']['checked_files']), 2)
        self.assertEqual(before, sorted(p.name for p in self.root.iterdir()))

    def test_break_and_cli_exit(self):
        a = self.archive('a.zip')
        b = self.archive('b.zip', {'openapi': '3.1.0', 'paths': {}})
        self.assertEqual(bundle.compare(a, b)['counts']['breaking'], 1)
        result = subprocess.run([sys.executable, '-B', str(Path(bundle.__file__)), str(a), str(b)],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'breaking')

    def test_review_exit(self):
        a = self.archive('a.zip')
        changed = copy.deepcopy(self.doc)
        changed['info'] = {'title': 'changed', 'version': '2'}
        b = self.archive('b.zip', changed)
        result = subprocess.run([sys.executable, '-B', str(Path(bundle.__file__)), str(a), str(b)],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 3)

    def test_zip_traversal_refused_even_when_unselected(self):
        a = self.archive('a.zip', extra=[('../escape', b'bad')])
        with self.assertRaises(ValueError):
            bundle.read_bundle(a)

    def test_crc_refused_even_when_unselected(self):
        a = self.archive('a.zip', extra=[('other', b'corrupt-me')])
        raw = a.read_bytes().replace(b'corrupt-me', b'CORRUPT-ME')
        a.write_bytes(raw)
        with self.assertRaises(zipfile.BadZipFile):
            bundle.read_bundle(a)

    def test_duplicate_and_case_collision_refused(self):
        a = self.archive('a.zip', extra=[('OPENAPI.JSON', b'{}')])
        with self.assertRaises(ValueError):
            bundle.read_bundle(a)

    def test_ratio_limit(self):
        a = self.archive('a.zip', extra=[('bomb', b'0'*100000)], compression=zipfile.ZIP_DEFLATED)
        with self.assertRaisesRegex(ValueError, 'ratio'):
            bundle.read_bundle(a)

    def test_json_duplicate_and_size_limits(self):
        for data in [b'{"openapi":"3.1.0","paths":{},"paths":{}}',
                     b' ' * (bundle.apidelta.MAX_BYTES + 1)]:
            a = self.root / 'invalid.zip'
            with zipfile.ZipFile(a, 'w') as output:
                output.writestr('openapi.json', data)
            with self.assertRaises(ValueError):
                bundle.read_bundle(a)

    def test_missing_member_and_symlink(self):
        a = self.archive('a.zip')
        with self.assertRaises(ValueError):
            bundle.read_bundle(a, 'absent.json')
        link = self.root / 'alias.zip'
        link.symlink_to('a.zip')
        with self.assertRaises(ValueError):
            bundle.read_bundle(link)

    def test_real_imd_capture(self):
        # Included public data is copied here, so no line directory is required.
        baseline = json.loads(Path(__file__).with_name('imd-openapi.json').read_bytes())
        a = self.archive('real.zip', baseline)
        report = bundle.compare(a, a)
        self.assertEqual(report['operations_compared'], 5)
        self.assertEqual(report['findings'], [])

    def test_approved_archive_digests(self):
        a = self.archive('approved.zip')
        digest = hashlib.sha256(a.read_bytes()).hexdigest()
        report = bundle.compare(a, a, old_sha256=digest.upper(), new_sha256=digest)
        self.assertTrue(report['bundle_inputs']['old']['approved_sha256_checked'])
        self.assertTrue(report['bundle_inputs']['new']['approved_sha256_checked'])
        self.assertFalse(bundle.compare(a, a)['bundle_inputs']['old']['approved_sha256_checked'])

    def test_wrong_digest_rejected_before_parsing(self):
        a = self.archive('wrong.zip')
        digest = hashlib.sha256(a.read_bytes()).hexdigest()
        # An approved pathname is not enough: a later byte replacement must fail.
        self.archive('wrong.zip', extra=[('extra', b'changed')])
        with mock.patch.object(bundle.zipfile, 'ZipFile') as parser:
            with self.assertRaisesRegex(ValueError, 'differs from approved'):
                bundle.read_bundle(a, expected_sha256=digest)
            parser.assert_not_called()

    def test_malformed_digest(self):
        a = self.archive('malformed.zip')
        for value in ('', 'g'*64, '0'*63, '0'*65, True, 12):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, '64 hexadecimal'):
                bundle.read_bundle(a, expected_sha256=value)

    def test_approval_still_checks_other_member_crc(self):
        a = self.archive('crc.zip', extra=[('unselected', b'corrupt-me')])
        a.write_bytes(a.read_bytes().replace(b'corrupt-me', b'CORRUPT-ME'))
        with self.assertRaises(zipfile.BadZipFile):
            bundle.read_bundle(a, expected_sha256=hashlib.sha256(a.read_bytes()).hexdigest())

    def test_comparison_uses_approved_snapshot_after_replacement(self):
        a = self.archive('replace.zip')
        digest = hashlib.sha256(a.read_bytes()).hexdigest()
        zip_type = zipfile.ZipFile
        replacement = io.BytesIO()
        with zip_type(replacement, 'w') as output:
            output.writestr('openapi.json', '{"openapi":"3.1.0","paths":{}}')

        def replace_then_parse(snapshot):
            a.write_bytes(replacement.getvalue())
            return zip_type(snapshot)

        with mock.patch.object(bundle.zipfile, 'ZipFile', side_effect=replace_then_parse):
            document, inventory = bundle.read_bundle(a, expected_sha256=digest)
        self.assertEqual(document, self.doc)
        self.assertEqual(inventory['archive_sha256'], digest)
        self.assertNotEqual(hashlib.sha256(a.read_bytes()).hexdigest(), digest)

    def test_boundcheck_on_real_api_in_zip(self):
        baseline = json.loads(Path(__file__).with_name('imd-openapi.json').read_bytes())
        schema = baseline['paths']['/requests/quote']['post']['requestBody']['content']['application/json']['schema']
        schema.setdefault('properties', {})['clientNote'] = {'type': 'string', 'maxLength': 160}
        proposed = copy.deepcopy(baseline)
        proposed['paths']['/requests/quote']['post']['requestBody']['content']['application/json']['schema']['properties']['clientNote']['maxLength'] = 80
        old, new = self.archive('old.zip', baseline), self.archive('new.zip', proposed)
        report = bundle.compare(old, new)
        self.assertEqual(report['extension'], 'constcheck-v1 (includes multiplecheck-v1 and boundcheck-v1)')
        self.assertEqual(report['counts']['breaking'], 1)
        self.assertEqual(report['counts']['review'], 1)
        self.assertIn('size_bound_incompatible', [f['code'] for f in report['findings']])
        # Relaxation retains the original unresolved review, rather than auto-accepting.
        self.assertEqual(bundle.compare(new, old)['status'], 'review_required')
        self.assertEqual(bundle.compare(old, old)['status'], 'no_detected_breakage')

    def test_cli_approved_bounds_and_wrong_digest(self):
        old_doc = copy.deepcopy(self.doc)
        old_doc['paths']['/items']['get']['responses']['200']['content'] = {
            'application/json': {'schema': {'type': 'number', 'maximum': 10}}}
        new_doc = copy.deepcopy(old_doc)
        new_doc['paths']['/items']['get']['responses']['200']['content']['application/json']['schema']['maximum'] = 20
        a, b = self.archive('a.zip', old_doc), self.archive('b.zip', new_doc)
        argv = [sys.executable, '-B', str(Path(bundle.__file__)), str(a), str(b),
                '--old-sha256', hashlib.sha256(a.read_bytes()).hexdigest(), '--new-sha256']
        result = subprocess.run(argv + [hashlib.sha256(b.read_bytes()).hexdigest()], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(json.loads(result.stdout)['counts']['breaking'], 1)
        result = subprocess.run(argv + ['not-a-digest'], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertFalse(json.loads(result.stdout)['ok'])

    def test_multiple_of_break_and_integer_equivalence_in_zip(self):
        old_doc = copy.deepcopy(self.doc)
        op = old_doc['paths']['/items']['get']
        op['requestBody'] = {'content': {'application/json': {
            'schema': {'type': 'integer', 'multipleOf': 2}}}}
        changed = copy.deepcopy(old_doc)
        changed['paths']['/items']['get']['requestBody']['content']['application/json']['schema']['multipleOf'] = 3
        old, new = self.archive('old.zip', old_doc), self.archive('new.zip', changed)
        report = bundle.compare(old, new)
        self.assertEqual(report['status'], 'breaking')
        self.assertIn('multiple_of_incompatible', [f['code'] for f in report['findings']])
        self.assertEqual(bundle.compare(old, old)['status'], 'no_detected_breakage')
        # On an integer domain, 0.5 and an absent multiple both admit every integer.
        equivalent = copy.deepcopy(old_doc)
        del equivalent['paths']['/items']['get']['requestBody']['content']['application/json']['schema']['multipleOf']
        half = copy.deepcopy(equivalent)
        half['paths']['/items']['get']['requestBody']['content']['application/json']['schema']['multipleOf'] = 0.5
        a, b = self.archive('any.zip', equivalent), self.archive('half.zip', half)
        self.assertFalse(any(f['code'] == 'multiple_of_incompatible'
                             for f in bundle.compare(a, b)['findings']))

    def test_cooperative_cancellation_and_budget(self):
        a = self.archive('a.zip')
        with self.assertRaisesRegex(ValueError, 'cancelled'):
            bundle.compare(a, a, cancelled=lambda: True)
        with self.assertRaisesRegex(ValueError, 'positive'):
            bundle.compare(a, a, seconds=0)
        with self.assertRaisesRegex(ValueError, 'positive'):
            bundle.compare(a, a, seconds=10**1000)
        self.assertEqual(bundle.compare(a, a, seconds=10)['status'], 'no_detected_breakage')
        result = subprocess.run([sys.executable, '-B', str(Path(bundle.__file__)),
                                 str(a), str(a), '--seconds', '0'],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 2)


    def test_const_change_in_approved_public_api_zip(self):
        old = json.loads(Path(__file__).with_name('imd-openapi.json').read_bytes())
        schema = old['paths']['/requests/quote']['post']['requestBody']['content']['application/json']['schema']
        schema.setdefault('properties', {})['clientMode'] = {'type': 'string', 'const': 'standard'}
        new = copy.deepcopy(old)
        new['paths']['/requests/quote']['post']['requestBody']['content']['application/json']['schema']['properties']['clientMode']['const'] = 'express'
        a, b = self.archive('const-old.zip', old), self.archive('const-new.zip', new)
        report = bundle.compare(a, b, old_sha256=hashlib.sha256(a.read_bytes()).hexdigest(),
                                new_sha256=hashlib.sha256(b.read_bytes()).hexdigest())
        self.assertEqual(report['status'], 'breaking')
        self.assertEqual(report['operations_compared'], 5)
        self.assertIn('const_incompatible', [f['code'] for f in report['findings']])
        self.assertEqual(report['counts']['review'], 1)

    def test_response_const_removal_and_openapi30_review(self):
        old = copy.deepcopy(self.doc)
        old['paths']['/items']['get']['responses']['200']['content'] = {
            'application/json': {'schema': {'const': False}}}
        new = copy.deepcopy(old)
        del new['paths']['/items']['get']['responses']['200']['content']['application/json']['schema']['const']
        a, b = self.archive('a.zip', old), self.archive('b.zip', new)
        self.assertIn('const_incompatible', [f['code'] for f in bundle.compare(a, b)['findings']])
        old['openapi'] = new['openapi'] = '3.0.3'
        a, b = self.archive('c.zip', old), self.archive('d.zip', new)
        report = bundle.compare(a, b)
        self.assertEqual(report['status'], 'review_required')
        self.assertNotIn('const_incompatible', [f['code'] for f in report['findings']])

    def test_node_budget_checks_unselected_implicit_parents(self):
        a = self.archive('deep.zip', extra=[('a/b/inert.txt', b'not executed')])
        # openapi.json + a + a/b + a/b/inert.txt = four nodes.
        with mock.patch.object(bundle.zipfile.ZipFile, 'open') as payload:
            with self.assertRaisesRegex(ValueError, 'filesystem node limit'):
                bundle.compare(a, a, nodes=3)
            payload.assert_not_called()
        self.assertEqual(bundle.compare(a, a, nodes=4)['status'], 'no_detected_breakage')

    def test_invalid_node_budget_refused_before_read(self):
        for value in (True, False, 0, -1, 1.0, None, '4'):
            with self.subTest(value=value), mock.patch.object(Path, 'open') as opened:
                with self.assertRaisesRegex(ValueError, 'positive integer'):
                    bundle.compare('nonexistent.zip', 'nonexistent.zip', nodes=value)
                opened.assert_not_called()

    def test_cli_node_budget_and_const_exit(self):
        old = copy.deepcopy(self.doc)
        old['paths']['/items']['get']['requestBody'] = {'content': {
            'application/json': {'schema': {'const': 0}}}}
        new = copy.deepcopy(old)
        new['paths']['/items']['get']['requestBody']['content']['application/json']['schema']['const'] = False
        a, b = self.archive('a.zip', old), self.archive('b.zip', new)
        cmd = [sys.executable, '-B', str(Path(bundle.__file__)), str(a), str(b), '--nodes']
        for value, code in [('0', 2), ('1', 1)]:
            result = subprocess.run(cmd + [value], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, code, result.stderr)
            if code == 1:
                self.assertIn('const_incompatible', [f['code'] for f in json.loads(result.stdout)['findings']])


if __name__ == '__main__':
    unittest.main(verbosity=2)
