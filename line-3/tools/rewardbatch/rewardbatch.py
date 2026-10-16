#!/usr/bin/env python3
"""Divide a verified ZTO/IMD allocation into complete offline review batches."""

import argparse
import importlib.util
import json
from pathlib import Path
import sys

SPEC = importlib.util.spec_from_file_location(
    "rewardreceipt", Path(__file__).resolve().parents[1] / "rewardreceipt" / "rewardreceipt.py")
rr = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rr)
rs = rr.rs


def build(request, report, metadata, batch_size):
    """Verify first, then partition every canonical row exactly once, including zeros."""
    rs.require(type(batch_size) is int and 1 <= batch_size <= rs.MAX_CONTRIBUTORS,
               "batch_size must be an integer between 1 and 1000")
    receipt = rr.verify(request, report, metadata)
    rows = report["allocations"]
    batches = []
    for start in range(0, len(rows), batch_size):
        # Own the returned JSON objects: later edits cannot mutate the source report.
        chunk = json.loads(rr.canonical_bytes(rows[start:start + batch_size]))
        batches.append({
            "number": len(batches) + 1,
            "start_row": start,
            "row_count": len(chunk),
            "units": str(sum(int(row["units"]) for row in chunk)),
            "rows_sha256": rr.digest(chunk),
            "allocations": chunk,
        })
    result = {
        "schema": "rewardbatch-v1",
        "scope": "offline review batches only; no transaction, payment, entitlement or authorization",
        "receipt": receipt,
        "batch_size": batch_size,
        "batch_count": len(batches),
        "contributor_count": len(rows),
        "budget_units": report["budget_units"],
        "batched_units": str(sum(int(batch["units"]) for batch in batches)),
        "allocation_rows_sha256": rr.digest(rows),
        "order": "ASCII contributor id; zero allocations retained; no recipient inferred",
        "batches": batches,
    }
    # Match the bounded inherited reader so every written bundle is readable again.
    rs.require(len((json.dumps(result, indent=2, ensure_ascii=True) + "\n").encode("utf-8"))
               <= rs.MAX_BYTES, "bundle exceeds 256-KiB limit; use fewer contributors or a larger batch_size")
    return result


def verify(request, report, metadata, bundle):
    """Rebuild from trusted-by-caller inputs; internal bundle hashes alone never suffice."""
    rs.require(isinstance(bundle, dict), "bundle must be an object")
    expected = build(request, report, metadata, bundle.get("batch_size"))
    rs.require(rr.canonical_bytes(bundle) == rr.canonical_bytes(expected),
               "bundle differs from the complete canonical partition of the verified allocation")
    return {
        "schema": "rewardbatch-verification-v1",
        "result": "verified complete exact partition",
        "bundle_sha256": rr.digest(bundle),
        "report_sha256": expected["receipt"]["report_sha256"],
        "batch_count": expected["batch_count"],
        "contributor_count": expected["contributor_count"],
        "budget_units": expected["budget_units"],
        "batched_units": expected["batched_units"],
        "scope": expected["scope"],
    }


def demo():
    metadata = rs.read_json(rr.ROOT / "zto-mainnet.json")
    request = rs.read_json(rr.ROOT / "example.json")
    report = rs.allocate(request, metadata)
    bundle = build(request, report, metadata, 2)
    return {"demo": "Included illustrative roles; real captured ZTO metadata; no payees or payments",
            "bundle": bundle, "verification": verify(request, report, metadata, bundle)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("demo", help="split the included 1-ZTO allocation into two review batches")
    for command in ("build", "verify"):
        check = sub.add_parser(command)
        check.add_argument("--request", required=True)
        check.add_argument("--report", required=True)
        check.add_argument("--metadata", default=str(rr.ROOT / "zto-mainnet.json"))
        check.add_argument("--output", help="new workspace JSON file; never overwrite")
        if command == "build":
            check.add_argument("--batch-size", type=int, required=True)
        else:
            check.add_argument("--bundle", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "demo":
            result = demo()
        else:
            request = rs.read_json(args.request)
            report = rs.read_json(args.report)
            metadata = rs.read_json(args.metadata)
            if args.command == "build":
                result = build(request, report, metadata, args.batch_size)
            else:
                result = verify(request, report, metadata, rs.read_json(args.bundle))
        rs.write_json(result, getattr(args, "output", None))
    except (rs.Invalid, OSError, ValueError, OverflowError) as exc:
        message = str(exc) if isinstance(exc, rs.Invalid) else type(exc).__name__
        print("rewardbatch: " + message, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
