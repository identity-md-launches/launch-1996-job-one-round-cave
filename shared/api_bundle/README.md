# API Bundle

Compare OpenAPI descriptions inside untrusted ZIPs without extracting or executing any member. Python 3.9+ and the standard library only. No installation, line folders, network or accounts are needed.

Run from a workspace root:

```sh
python3 -B shared/api_bundle/selftest.py
```

Gathering 24 result: **24 integration tests passed**. Checks include fixed-value `const` changes, request/response variance, OpenAPI 3.0 review, node-budget rejection before payload reads, invalid node limits, the previous approval and bound cases, `multipleOf` changes inside ZIPs, integer-domain equivalence, cooperative cancellation, a positive time budget, real public IMD API data, breaking/review/error CLI exits, CRC checks of every payload and inert executable content. Scratch lives under `test/scratch/` and is never a runtime dependency.

For two archives you received:

```sh
python3 -B shared/api_bundle/api_bundle.py old.zip new.zip --member openapi.json
```

Use caller-reviewed archive hashes to require the exact approved bytes:

```sh
python3 -B shared/api_bundle/api_bundle.py old.zip new.zip --old-sha256 OLD_APPROVED_SHA256 --new-sha256 NEW_APPROVED_SHA256
```

For a cooperative archive-processing budget, add `--seconds 10`. The limit covers both archive snapshots, their inventories and payload reads, with checkpoints before and after comparison. It does not interrupt a single long schema-analysis call or impose an operating-system CPU limit. Python callers can pass a `cancelled` callback to `compare(...)`; no thread or signal handler is started.

Replace the uppercase argument labels with the real 64-character hex digests from your review process. They are not shipped example hashes. Obtain a snapshot's archive hash with SafeZip's inspect command or your own trusted hashing tool; the previous bundle report also includes it. A hash establishes byte identity, not publisher identity or safety. Approval is optional for backward compatibility; each input report says whether it was checked. An incorrect or malformed approval returns exit 2 before that archive's ZIP parsing. Comparison uses exactly the in-memory bytes that passed approval, so replacing the path after capture cannot swap the description.

Paths must be in the current workspace with no symlink components, and the exact selected member must exist in both ZIPs. JSON goes to stdout. Exit **0** means no detected breakage, **1** potential breaking change, **2** invalid input/error, **3** unresolved review. Only exit 0 passes this static check; it does not prove runtime compatibility.

The shared snapshot joins SafeZip (line 2) with ApiDelta, BoundCheck, MultipleCheck and ConstCheck (line 4). `vendor/` contains ordinary source files; `SOURCES.json` records original/delivered hashes. SafeZip and ApiDelta are byte-identical snapshots. BoundCheck, MultipleCheck and ConstCheck only adapt sibling module and demo capture paths to the shared layout. No line source was modified. Refresh these copies deliberately and rerun tests when upstream changes.

Each archive is read once, at most 32 MiB. Every member is validated for paths, types, compression, collisions and declared limits. Every file is streamed to check CRC, actual byte counts and SHA-256, including files not selected for comparison. Only the selected JSON is retained, at most 1 MiB. Nothing is extracted or imported from an archive. Inventories identify all checked files and selected-member/archive hashes.

BoundCheck adds numeric and size-bound findings: narrowing requests or widening responses can break clients. A hypothetical reduction of `clientNote.maxLength` from 160 to 80 in the captured real IMD API yields one breaking and one review finding through the ZIP flow. It is a synthetic upgrade, not an observed service change. Bound relaxations retain the base review findings. No comparison discards an unresolved review just because it recognizes a bound.

MultipleCheck adds rational `multipleOf` findings. It detects when a revised request rejects formerly accepted multiples or a revised response permits multiples that violate the old contract. In the included ZIP test, integer request `multipleOf` changing from 2 to 3 produces a breaking finding. The integer-only `multipleOf: 0.5` case is treated as equivalent to an unrestricted integer domain. Existing review findings remain visible.

ConstCheck adds fixed-value findings for OpenAPI 3.1: adding/changing a request
`const` or removing/changing a response `const` may break callers. It distinguishes
JSON booleans, null, strings and numbers, and preserves inherited review findings.
For OpenAPI 3.0 and cross-version changes, `const` remains an unresolved review.

Add `--nodes 200` (Python `compare(..., nodes=200)`) to bound distinct member
paths plus implicit parent directories in each archive. For example,
`docs/openapi.json` consumes two nodes even when the ZIP has one entry. Default:
32,000. Every member counts, including unselected files and empty directories.
The check runs during inventory before payload decompression. This limits the
inventory structure; no filesystem objects are extracted. Positive integers only;
invalid values fail before reading. Archive parsing still occurs before inventory.

See the complete offline flow with one command:

```sh
python3 -B shared/api_bundle/demo.py
```

Observed: a hypothetical `clientMode` fixed-value change in the captured public
IMD API produces one breaking and one retained review finding over five operations.
The descriptions are packaged into reproducible ZIPs with approved SHA-256 hashes.
A two-node budget accepts `docs/openapi.json`; a one-node budget refuses it.
No member is extracted, executed, or called. The demo exits 0 after checking its
expected outcomes, creates only disposable data in `test/scratch/`, and cleans up.
Its simulated change does not claim the live API changed.

Limits: stored/deflated ZIPs, 1,000 entries, 16 MiB per file, 64 MiB total uncompressed, ratio 200, normalized portable names. Memory/CPU are not hard sandboxed; initial path access requires a cooperative local workspace. API analysis covers a bounded OpenAPI 3.0/3.1 subset and local object-member references. It does not fetch external references, fully validate schemas, model every constraint interaction or prove compatibility. MultipleCheck normalizes integer domains only when both sides are explicitly integer-only; other numeric precision follows ApiDelta's JSON float parser. Regexes, compositions and other unsupported semantics still need review. Description hashes cannot detect undocumented runtime changes.

A fresh read-only GET of `https://api.imd.fun/openapi.json` on 2026-10-16 matched the bundled capture: 23,132 bytes, SHA-256 `be142840c010710cb2a5b9e5c73e71d8e79ec4054c15661699d60bfa627be96a`. Comparing approved ZIP snapshots with `--seconds 10` returned five operations and no findings. Only the public description GET was used; no payment or mutation endpoint or transaction was called. The bundled public capture is test/demo data, not required by the comparison CLI.
