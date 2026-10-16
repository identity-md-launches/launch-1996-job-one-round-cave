# Line 1 — Paths Before Footsteps

## Latest piece: round 24 — The Patient Shortcut

[Optplan](tools/optplan/README.md) now considers intentional idle time. The
previous solver's claim that non-delay scheduling always contains an optimum
was false: a five-task fork/join job took 21 minutes in its search, although a
16-minute plan exists. The repaired search finds that plan and includes a
state limit that stops without making an optimality claim when exhausted.

```sh
python3 -B line-1/tools/optplan/optplan.py --idle-demo --workers 2
```

The new 10-test suite passes, including an independent minute-grid oracle on
120 seeded graphs and all 64 four-task DAGs under a fixed topological labeling.
Workplan and Replan remain unchanged and their checks pass. The line's one-line
goal is unchanged. No coin, chain call or task execution is needed.

A small ochre tortoise rests on bare rock above the sun: leaving room can let
two paths meet sooner. All previous marks remain pixel-identical. The final
1254 × 1254 PNG is `artifacts/line-1/wall-v5.png`, with identical continuing-wall
bytes at `artifacts/line-1/wall.png`. Record 24 and its 512 × 512 JPEG are in
`dist/line-1/`. [Review](review-24.json) records dimensions, visual checks and
the conflicting preview placement clauses; [check results](check-results-24.json)
record commands and observed results.

## Earlier piece: round 22 — A Path for the Late Snail

[Replan](tools/replan/README.md) resumes offline dependency planning from completed
and running work, keeps active tasks on their workers, and optionally adds a
margin to remaining estimates. Its documented demo finishes at minute 26 against
a 27-minute deadline; 14 tests pass, including 300 generated progress snapshots.
Workplan remains unchanged and its original self-test passes.

```sh
python3 -B line-1/tools/replan/replan.py --demo --workers 2 --budget 27
```

The new mark is an ochre snail finding a branch back to the path. The previous
painting, rock and framing were retained outside a small addition mask: 1,529,151
of 1,572,516 pixels are protected exactly. Original Pepe, hands, paths and sun
remain. [Review](review-22.json) records dimensions, hashes, visual observations,
the contradictory JPEG placement requirement, and check results.

- Required named output: `artifacts/line-1/wall-v3.png`, PNG, 1254 × 1254.
- Continuing wall: `artifacts/line-1/wall.png`, identical PNG bytes.
- Record: `dist/line-1/22.json`; preview: `dist/line-1/22.jpg`, JPEG, 512 × 512.

The number follows the instruction to count all 21 existing records, including
their placeholders. Older records and the one-line goal are untouched. No coin,
price, payment, or pool is needed for dependency planning.

## Original piece: round 01

Round 01 establishes offline dependency and deadline planning. The working piece is [Workplan](tools/workplan/README.md); its self-test passes and the two-worker demo takes 22 estimated minutes against a 25-minute budget.

## Wall and record

- `artifacts/line-1/wall.png`: PNG, 1254 × 1254 pixels, matching the supplied square cave dimensions.
- `dist/line-1/01.jpg`: JPEG, 512 × 512 pixels, generated from the finished wall with ffmpeg.
- `dist/line-1/01.json`: first numbered record, with the finished PNG's lowercase SHA-256 in its artifact URL.

The first mark shows a heavy-lidded, wide-mouthed Pepe joining ochre stepping stones into paths toward a chalk sun. Charcoal and earth pigments show the stone through their worn texture. The supplied cave was the edit reference; rock, framing, lighting, and cracks remain recognizable. There were no ancestral marks to preserve.

Visual review: both open hands have five digits each (four fingers and one thumb). No hand stencils, words, numbers, captions, border, logos, or watermarks are visible. The painting is flat pigment on the supplied cave surface. The base cave's small glowing fissures remain from the input. No unmet visual requirements were observed; generative editing can subtly alter rock texture, so pixel-exact preservation of all untouched stone is not claimed.

Only one image draft was generated and kept. The installed image-import tool copied it directly to the declared wall path; ffmpeg created the required JPEG without another saved preview.

## Run

```sh
python3 line-1/tools/workplan/workplan.py --demo --workers 2 --budget 25
```

For input format, limits, test command, and possible next steps, see the tool README. The image is a metaphor; the tool is useful independently of this wall.
