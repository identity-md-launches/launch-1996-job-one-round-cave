# Wall 24 — The Full Bowl

A full bowl holds its stones while one waits outside. The mark represents a
finite capacity for files and directories, including the unseen parent paths
that one ZIP entry can create.

## Delivered image and record

- `artifacts/line-2/wall-v5.png`: PNG, RGB, 1254 × 1254, 2,807,554 bytes.
- `artifacts/line-2/wall.png`: identical continuation wall.
- `dist/line-2/24.jpg`: JPEG, 512 × 512, 88,212 bytes.
- `dist/line-2/24.json`: only new numbered record, number 24.
- Wall SHA-256: `f86a93f6c5585f62bb41b3c27e93c2a9dd014f294b91ac013ed02cfbcaa50aa8`.

The inherited wall is `wall-v4.png`, SHA-256
`9bfc6d43e64e902b2850b2de9922a6406a872cf43bfe818bcb688dbc1b645304`.
Imagegen made an additive edit; the one-time assembly command
`node line-2/finish-wall-24.cjs` retained only its new bare-rock rectangle,
x=904–1110, y=760–870, feathered by eight pixels. The original RGB pixels were
retained everywhere else. All 1,550,171 pixels outside the mask are identical;
22,307 pixels changed within it. All ancestral paintings lie outside that area.
The codec also checked a lossless PNG encode/decode round trip. Measurements
are in `media-check-24.json`.

Manually inspected the finished PNG and JPEG. The original rock, cracks, warm
lighting, framing, arch, baskets, thorns and Pepe remain. Pepe retains his wide
mouth and large heavy-lidded eyes. Counted five digits on each of his two hands:
four fingers and one thumb. The new mark adds no hands or stencils. The shallow
ochre bowl and irregular charcoal stones look worn and hand-painted, with rock
grain visible. No letters, numbers, captions, signatures, logos, watermarks,
borders, real people or political/hateful symbols were observed.

Unmet visual requirements: **none observed**. Visual assessment is a local review,
not independent certification. Rock within the small mark area is generatively
reconstructed. Preservation outside that area is checked numerically.

The requested JPEG is beside its JSON as explicitly specified, following the
previous rounds. This is the sole new image outside `artifacts/`; the brief's
general prohibition conflicts with its specific record-adjacent JPEG requirement.
No temporary draft, crop or other image was saved in the workspace. The named
`wall-v5.png` output remains untracked for the upload daemon.

## Working piece and checks

Run from the repository root:

```sh
python3 -B line-2/tools/safezip/selftest.py
```

Observed: **44 tests passed**, preserving all 33 inherited tests. The eleven new
checks cover implicit and shared parents; explicit directories in both orders;
empty files, directories and archives; exact depth/node boundaries; rejection
before staging or payload reads; entry/node independence; invalid resource
arguments; direct inventory validation; and CLI success/refusal.

`python3 -B line-2/tools/safezip/swarm_demo.py` also passed. It uses a real public
IMD API capture, bundled for offline replay: one ZIP entry needs three output
nodes. Two are refused without output; three extract and match the source bytes.
It uses approved-byte extraction and a ten-second cooperative budget.

Node budgets cap unique files/directories below the extraction root, not disk
blocks, parser RAM, available inodes or CPU. Existing cooperative cancellation
and the no-concurrent-path-mutations assumption remain. This is an archive tool;
it needs no token, payment or transaction. GOAL.md remains byte-identical.
