#!/usr/bin/env python3
"""Offline OpenAPI const compatibility checks, retaining earlier line 4 rules."""

import argparse
import copy
from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import sys


MULTIPLE_PATH = Path(__file__).resolve().parents[1] / 'multiplecheck' / 'multiplecheck.py'
spec = importlib.util.spec_from_file_location('constcheck_multiple', MULTIPLE_PATH)
multiple = importlib.util.module_from_spec(spec)
spec.loader.exec_module(multiple)
api = multiple.api


def json_equal(left, right):
    """JSON Schema equality: numeric values compare mathematically, not by spelling."""
    if type(left) in (int, float) and type(right) in (int, float):
        try:
            return Fraction(str(left)) == Fraction(str(right))
        except (ValueError, OverflowError, ZeroDivisionError) as exc:
            raise api.Invalid('const must contain finite JSON numbers') from exc
    if type(left) is not type(right):
        return False
    if isinstance(left, list):
        return len(left) == len(right) and all(json_equal(a, b) for a, b in zip(left, right))
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(json_equal(left[key], right[key]) for key in left)
    return left == right


class Analyzer(multiple.Analyzer):
    def _schema(self, old, new, loc, direction):
        super()._schema(old, new, loc, direction)
        # `const` is a JSON Schema keyword in OpenAPI 3.1, not an OpenAPI 3.0
        # Schema Object keyword. Leave 3.0 and cross-version changes for review.
        if not (self.old.obj['openapi'].startswith('3.1.') and
                self.new.obj['openapi'].startswith('3.1.')):
            return
        before, after = 'const' in old, 'const' in new
        incompatible = (after and not before) if direction == 'request' else (before and not after)
        if before and after and not json_equal(old['const'], new['const']):
            incompatible = True
        if incompatible:
            self.emit('breaking', 'const_incompatible', loc + '/const',
                      'New request const excludes a formerly allowed value.'
                      if direction == 'request' else
                      'New response const can violate the old fixed value.')


def compare(old, new):
    report = Analyzer(old, new).run()
    report['extension'] = 'constcheck-v1 (includes multiplecheck-v1 and boundcheck-v1)'
    return report


def demo():
    old, digest = api.load(multiple.bound.BASE.with_name('imd-openapi.json'))
    old = copy.deepcopy(old)
    schema = old['paths']['/requests/quote']['post']['requestBody']['content']['application/json']['schema']
    schema.setdefault('properties', {})['clientMode24'] = {'type': 'string', 'const': 'standard'}
    new = copy.deepcopy(old)
    new['paths']['/requests/quote']['post']['requestBody']['content']['application/json']['schema']['properties']['clientMode24']['const'] = 'express'
    report = compare(old, new)
    report.update(capture_sha256=digest,
                  demo='Hypothetical fixed clientMode24 change in the captured public IMD API. No operation called.')
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('demo')
    diff = commands.add_parser('compare')
    diff.add_argument('old')
    diff.add_argument('new')
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            report = demo()
        else:
            old, old_hash = api.load(args.old)
            new, new_hash = api.load(args.new)
            report = compare(old, new)
            report.update(old_sha256=old_hash, new_sha256=new_hash)
        print(json.dumps(report, indent=2, allow_nan=False))
        return 0 if args.command == 'demo' else {
            'breaking': 1, 'review_required': 3, 'no_detected_breakage': 0}[report['status']]
    except (api.Invalid, OSError, ValueError, TypeError, KeyError, RecursionError) as exc:
        print('constcheck: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
