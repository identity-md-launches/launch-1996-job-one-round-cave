"""Regression checks for fixed-value variance and inherited findings."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import constcheck as c


def document(schema, response=False):
    media = {'application/json': {'schema': schema}}
    op = {'responses': {'200': {'description': 'ok', 'content': media if response else {}}}}
    if not response:
        op['requestBody'] = {'content': media}
    return {'openapi': '3.1.0', 'paths': {'/items': {'post': op}}}


def hits(old, new, response=False):
    report = c.compare(document(old, response), document(new, response))
    return [finding for finding in report['findings'] if finding['code'] == 'const_incompatible']


class Tests(unittest.TestCase):
    def test_request_added_removed_and_changed(self):
        self.assertTrue(hits({}, {'const': 'fixed'}))
        self.assertFalse(hits({'const': 'fixed'}, {}))
        self.assertTrue(hits({'const': 'old'}, {'const': 'new'}))

    def test_response_added_removed_and_changed(self):
        self.assertFalse(hits({}, {'const': 'fixed'}, True))
        self.assertTrue(hits({'const': 'fixed'}, {}, True))
        self.assertTrue(hits({'const': 'old'}, {'const': 'new'}, True))

    def test_zero_false_and_null_are_distinct(self):
        for left, right in ((0, False), (False, 0), (None, False), ('0', 0)):
            with self.subTest(left=left, right=right):
                self.assertTrue(hits({'const': left}, {'const': right}))

    def test_numeric_json_equality(self):
        self.assertFalse(hits({'const': 1}, {'const': 1.0}))
        self.assertFalse(hits({'const': -0.0}, {'const': 0}))
        self.assertFalse(hits({'const': 0.5}, {'const': 0.50}))
        self.assertFalse(hits({'const': [1, {'x': 2.0}]}, {'const': [1.0, {'x': 2}]}))

    def test_object_order_and_array_order(self):
        self.assertFalse(hits({'const': {'b': 2, 'a': 1}}, {'const': {'a': 1.0, 'b': 2.0}}))
        self.assertTrue(hits({'const': [1, 2]}, {'const': [2, 1]}))

    def test_reference_recursion_and_location(self):
        old = document({'$ref': '#/components/schemas/N'})
        old['components'] = {'schemas': {'N': {'properties': {
            'next': {'$ref': '#/components/schemas/N'}, 'mode/~': {'const': 'first'}}}}}
        new = copy.deepcopy(old)
        new['components']['schemas']['N']['properties']['mode/~']['const'] = 'second'
        result = c.compare(old, new)
        found = [f for f in result['findings'] if f['code'] == 'const_incompatible']
        self.assertEqual(len(found), 1)
        self.assertIn('mode~1~0', found[0]['location'])

    def test_inherited_rules_remain(self):
        old = {'const': 'old', 'multipleOf': 2, 'maximum': 10}
        new = {'const': 'new', 'multipleOf': 3, 'maximum': 5}
        codes = {f['code'] for f in c.compare(document(old), document(new))['findings']}
        self.assertTrue({'const_incompatible', 'multiple_of_incompatible',
                         'numeric_bound_incompatible', 'schema_constraint_changed'} <= codes)

    def test_relaxation_still_requires_review(self):
        self.assertEqual(c.compare(document({'const': 'fixed'}), document({}))['status'],
                         'review_required')

    def test_openapi_30_const_remains_review(self):
        old, new = document({'const': 'old'}), document({'const': 'new'})
        old['openapi'] = new['openapi'] = '3.0.3'
        report = c.compare(old, new)
        self.assertEqual(report['status'], 'review_required')
        self.assertFalse(any(f['code'] == 'const_incompatible' for f in report['findings']))

    def test_capture_and_demo(self):
        obj, _ = c.api.load(c.multiple.bound.BASE.with_name('imd-openapi.json'))
        self.assertEqual(c.compare(obj, obj)['operations_compared'], 5)
        self.assertEqual(c.compare(obj, obj)['findings'], [])
        self.assertEqual(c.demo()['counts']['breaking'], 1)

    def test_cli_exit_codes(self):
        root = Path('test/scratch')
        root.mkdir(parents=True, exist_ok=True)
        script = str(Path(__file__).with_name('constcheck.py'))
        with tempfile.TemporaryDirectory(dir=root) as folder:
            old, new = Path(folder) / 'old.json', Path(folder) / 'new.json'
            old.write_text(json.dumps(document({'const': 'a'})))
            for schema, code in (({'const': 'a'}, 0), ({'const': 'b'}, 1),
                                 ({}, 3)):
                new.write_text(json.dumps(document(schema)))
                result = subprocess.run([sys.executable, '-B', script, 'compare', str(old), str(new)],
                                        capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, code, result.stderr)
                json.loads(result.stdout)
            new.write_text('{"openapi":"3.1.0","paths":{},"paths":{}}')
            result = subprocess.run([sys.executable, '-B', script, 'compare', str(old), str(new)],
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 2)


if __name__ == '__main__':
    unittest.main()
