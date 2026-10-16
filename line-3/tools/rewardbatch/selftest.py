#!/usr/bin/env python3
"""Offline integrity and conservation checks for review batching."""
import copy
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

import rewardbatch as rb


class BatchTests(unittest.TestCase):
    def setUp(self):
        self.metadata = rb.rs.read_json(rb.rr.ROOT / "zto-mainnet.json")
        self.request = rb.rs.read_json(rb.rr.ROOT / "example.json")
        self.report = rb.rs.allocate(self.request, self.metadata)

    def build(self, size=2):
        return rb.build(self.request, self.report, self.metadata, size)

    def verify(self, bundle):
        return rb.verify(self.request, self.report, self.metadata, bundle)

    def test_example(self):
        bundle = self.build()
        self.assertEqual([x["row_count"] for x in bundle["batches"]], [2, 1])
        self.assertEqual(bundle["batched_units"], "1000000000000000000")
        self.assertEqual(self.verify(bundle)["result"], "verified complete exact partition")

    def test_boundaries(self):
        for size, count in ((1, 3), (3, 1), (1000, 1)):
            self.assertEqual(self.build(size)["batch_count"], count)
        for size in (0, -1, 1001, True, False, "2", 2.0, None):
            with self.subTest(size=size), self.assertRaises(rb.rs.Invalid):
                self.build(size)

    def test_tampered_source_report(self):
        self.report["allocations"][0]["units"] = "0"
        with self.assertRaises(rb.rs.Invalid):
            self.build()

    def test_missing_duplicate_reordered_rows(self):
        for mutate in (
            lambda x: x["batches"].pop(),
            lambda x: x["batches"].append(copy.deepcopy(x["batches"][0])),
            lambda x: x["batches"].reverse(),
            lambda x: x["batches"][0]["allocations"].reverse(),
        ):
            bundle = self.build()
            mutate(bundle)
            with self.assertRaises(rb.rs.Invalid):
                self.verify(bundle)

    def test_rehashed_tampering_rejected(self):
        bundle = self.build()
        batch = bundle["batches"][0]
        batch["allocations"][0]["units"] = "1"
        batch["rows_sha256"] = rb.rr.digest(batch["allocations"])
        batch["units"] = str(sum(int(r["units"]) for r in batch["allocations"]))
        with self.assertRaises(rb.rs.Invalid):
            self.verify(bundle)

    def test_wrong_metadata_receipt_or_extra_fields(self):
        for key, value in (("receipt", {}), ("batched_units", "1"),
                           ("contributor_count", True), ("extra", None)):
            bundle = self.build()
            bundle[key] = value
            with self.subTest(key=key), self.assertRaises(rb.rs.Invalid):
                self.verify(bundle)
        metadata = dict(self.metadata, block_number=self.metadata["block_number"] + 1)
        with self.assertRaises(rb.rs.Invalid):
            rb.verify(self.request, self.report, metadata, self.build())

    def test_zeros_retained_and_input_order_canonical(self):
        self.request = {"budget": "0.000000000000000001", "contributors": [
            {"id": "z", "weight": "0"}, {"id": "b", "weight": "1"},
            {"id": "a", "weight": "1"}]}
        self.report = rb.rs.allocate(self.request, self.metadata)
        bundle = self.build(1)
        rows = [b["allocations"][0] for b in bundle["batches"]]
        self.assertEqual([(r["id"], r["units"]) for r in rows], [("a", "1"), ("b", "0"), ("z", "0")])
        self.request["contributors"].reverse()
        report = rb.rs.allocate(self.request, self.metadata)
        other = rb.build(self.request, report, self.metadata, 1)
        self.assertEqual(other["batches"], bundle["batches"])
        self.assertNotEqual(other["receipt"]["request_sha256"], bundle["receipt"]["request_sha256"])

    def test_returned_rows_do_not_alias_report(self):
        bundle = self.build()
        bundle["batches"][0]["allocations"][0]["units"] = "123"
        self.assertNotEqual(self.report["allocations"][0]["units"], "123")

    def test_oversized_bundle_rejected_before_output(self):
        request = {"budget": "1", "contributors": [
            {"id": "role%04d" % i + "x" * 50, "weight": "1"}
            for i in range(1000)]}
        report = rb.rs.allocate(request, self.metadata)
        with self.assertRaisesRegex(rb.rs.Invalid, "bundle exceeds"):
            rb.build(request, report, self.metadata, 1)

    def test_seeded_conservation_and_uint256(self):
        rng = random.Random(24)
        for index in range(160):
            count = rng.randint(1, 60)
            units = rb.rs.UINT256_MAX if index == 0 else rng.randint(1, 10**30)
            request = {"budget": rb.rs.display_units(units, self.metadata["decimals"]),
                       "contributors": [{"id": "role%03d" % i, "weight": str(rng.randint(1, 100))}
                                        for i in range(count)]}
            report = rb.rs.allocate(request, self.metadata)
            bundle = rb.build(request, report, self.metadata, rng.randint(1, 70))
            self.assertEqual(sum(int(b["units"]) for b in bundle["batches"]), units)
            self.assertEqual([r for b in bundle["batches"] for r in b["allocations"]], report["allocations"])
            rb.verify(request, report, self.metadata, bundle)

    def test_cli_roundtrip_overwrite_and_duplicate_keys(self):
        scratch = Path.cwd() / "test" / "scratch"
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temp:
            root = Path(temp)
            for name, obj in (("request", self.request), ("report", self.report)):
                (root / (name + ".json")).write_text(json.dumps(obj))
            command = [sys.executable, "-B", str(Path(rb.__file__)), "build",
                       "--request", str(root / "request.json"), "--report", str(root / "report.json"),
                       "--batch-size", "2", "--output", str(root / "bundle.json")]
            run = lambda args: subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(run(command).returncode, 0)
            self.assertEqual(run(command).returncode, 2)
            verify = command[:3] + ["verify"] + command[4:8] + ["--bundle", str(root / "bundle.json")]
            result = run(verify)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["batched_units"], self.report["budget_units"])
            (root / "bundle.json").write_text('{"batch_size":2,"batch_size":1}')
            self.assertEqual(run(verify).returncode, 2)


if __name__ == "__main__":
    unittest.main()
