# Gathering 24 — The Seed Carrier

This round checked all four lines, refreshed the shared ZIP-to-OpenAPI bundle
with ConstCheck and explicit inventory node budgets, and added an ochre seed
carrier to the inherited gathering wall. See [REPORT.md](REPORT.md) for each
line's results, limitations and suggested scope. [COINS.md](COINS.md) says
**none**: ZTO already supports the reward tools and the others need no coin.
No line folder or line record was changed.

Run from the repository root, with Python's standard library only:

```sh
python3 -B gathering/check_tools_24.py
python3 -B gathering/try_lines_24.py
python3 -B shared/api_bundle/selftest.py
python3 -B shared/api_bundle/demo.py
python3 -B gathering/check_delivery_24.py
```

Observed: all **28** documented line commands returned their expected exits,
**194** line unittest cases passed, **10** cross-line trials passed, and
**24** shared integration tests passed. RewardCompare's demo exit 1 is its
expected budget-paradox warning; the insufficient node-budget trial's exit 2
is its expected refusal. The shared demo also ran in an isolated disposable
workspace containing only `api_bundle`, with no line folders. Scratch directories
are created when needed and are never a shipped dependency. The shared runtime
and demo are ordinary Python source, fully offline, with no installation needed.

The live check was one read-only GET of the public IMD OpenAPI description,
using `Pepeolithic-Gathering/24.0`. The 23,132-byte capture matched the bundled
baseline and is delivered as `imd-openapi-current-24.json`, so all commands above
work without network. The reward trial uses the line's real historical Ethereum
ZTO metadata, not a new chain observation. No API operation, wallet, key,
environment setting, signature, payment, POST or transaction was used.

## Outputs and review

- `artifacts/gathering/wall-v5.png`: full **1254 × 1254 RGB PNG**,
  SHA-256 `f60e785e5288aba361f9217b5e75e7687ead3d3d92abe8d62a5fda3d7eb84421`.
  It remains untracked for the artifact uploader.
- `artifacts/gathering/wall.png`: relative link to `wall-v5.png`.
- `dist/gathering/24.jpg`: **512 × 512 JPEG**, **86,735 bytes**.
- `dist/gathering/24.json`: numbered content-addressed record in the requested shape.
- `dist/goals.json`: all four unchanged goals.
- `dist/index.html`: one page with all **120** records, newest painted marks
  first per wall, including links to all **100** preserved future slots.

The installed image tool (`mcp__image__generate`) made an isolated pigment mark;
its full prompt and the final format/visual review are in `review-24.json`.
`finish_wall_24.py` documents the build-time assembly: it consumes the generated
mark **once** and replaces that same output path with the complete wall, using
local PNG code and the existing line 1 BSD-licensed JPEG encoder via Node.
Do not rerun that assembly against the finished wall: its input must be the
reviewed 1024-pixel generation, which is intentionally not retained as another
image. No new codec or dependency was installed.

`preservation-24.json` and the delivery check confirm **8,498** changed RGB pixels
within the bare-rock 150 × 145 placement rectangle and **zero** outside it.
The inherited rock, cracks, lighting, framing, earlier marks and Pepe remain.
The finished full wall and JPEG were explicitly inspected: five digits on each
inherited hand; no new hands or stencils; no letters, numbers, logos, frames or
forbidden symbols observed. No unmet visual requirement was found. The small
mark has less detail in the thumbnail. This worker review is not independent
human approval; a curator should inspect the full wall before visual publication.

`delivery-check-24.json` records the final local checks, including the hashes of
all **202** unchanged line files/records/previews, source provenance, gallery
coverage, image dimensions, output hash, placeholder preservation and allowed
paths. Those checks establish the listed structural facts, not general behavior
or artistic quality. Earlier gathering evidence remains as historical records.
