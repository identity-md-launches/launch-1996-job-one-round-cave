# RewardBatch

RewardBatch partitions a verified ZTO reward allocation into bounded review batches. A worker can hand each batch to a reviewer and then check that the assembled bundle contains every contributor exactly once, in canonical order, with the original units. Zero allocations remain visible. It imports RewardReceipt and RewardSplit from the sibling folders; keep the `tools/` tree together. Python 3.9+ and the standard library are the entire runtime dependency set. No installation or network is needed.

Run from the repository root:

```sh
python3 -B line-3/tools/rewardbatch/rewardbatch.py demo
```

Expected exit: **0**. The demo uses the existing illustrative three-role request and real historical Ethereum ZTO metadata capture. It builds batches of two and one contributors, totaling exactly **1000000000000000000 atomic ZTO units (1 ZTO)**, and independently rebuilds and verifies the bundle. It prints the bundle and verification receipt. The roles are illustrative, with no invented recipient addresses.

For your own RewardSplit request and saved allocation:

```sh
python3 -B line-3/tools/rewardbatch/rewardbatch.py build \
  --request REQUEST.json --report REPORT.json --batch-size 50 \
  --metadata line-3/tools/rewardsplit/zto-mainnet.json --output BUNDLE.json
python3 -B line-3/tools/rewardbatch/rewardbatch.py verify \
  --request REQUEST.json --report REPORT.json --bundle BUNDLE.json \
  --metadata line-3/tools/rewardsplit/zto-mainnet.json
```

First produce `REPORT.json` with RewardSplit's `allocate` command. Use the same metadata capture for every step. Batch size is an integer from 1 to 1000 and limits rows, not transaction gas or monetary value. The final batch may be shorter. Input order does not affect row ordering, but the receipt deliberately hashes the original request, including its order. All report rows and any supplied addresses are preserved verbatim; address-free allocations work too. No address is inferred or required.

Verification recomputes the original allocation with RewardReceipt, rebuilds all batches, and compares canonical JSON including value types and every field. It rejects missing, duplicated, reordered, edited or extra data even if an editor updates the internal row hashes. Checksums are unsigned links to caller-supplied inputs; someone replacing both the request and all reports can produce a different valid allocation. Keep the original receipt and inputs through your own trusted handoff process.

Both commands print JSON unless `--output` names a new workspace file. Existing files are never overwritten. Exit **0** means success; **2** means invalid input or an I/O error. JSON inputs reject duplicate keys and are bounded to 256 KiB by the inherited reader. Bundle output is bounded to the same size, so it remains readable. An oversized bundle is rejected before output; larger batches can reduce overhead, but a sufficiently large roster still needs a smaller independently specified allocation. The tool never silently drops rows or splits the original reward budget again.

What happened here: the offline demo returned 0 and verified two batches summing to 1 ZTO. Eleven tests passed, including 160 seeded partitions, uint256 maximum precision, zero-weight/zero-unit rows, source-report tampering, bundle tampering with recomputed hashes, missing/duplicated/reordered rows, strict field/type checking, metadata mismatch, input alias isolation, and file-based CLI build/verify, overwrite refusal and duplicate JSON keys.

```sh
python3 -B line-3/tools/rewardbatch/selftest.py
```

These are review batches only. They carry no payment progress state and do not prevent double payment. They do not establish identity, work quality, authorization, balance, current chain state or actual payment. Nothing reads keys, signs, sends, pays, or accesses network or environment settings. ZTO is the default real token; existing RewardSplit metadata validation also allows IMD.
