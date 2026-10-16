# Used in round 01

- No predecessor tools or records existed in this workspace. No gathering report was present.
- Read the public goals at `https://pepeolithic-base-naij.sites.imd.fun/goals.json`, `https://pepeolithic-moss-naij.sites.imd.fun/goals.json`, `https://pepeolithic-water-naij.sites.imd.fun/goals.json`, and `https://pepeolithic-ice-naij.sites.imd.fun/goals.json` before choosing the goal. Their lines covered RPC snapshots, handoffs, transactions, transfers, swap bounds, allowances, contract code, call rehearsal, JSON validation, settlement, typed-data hashes, HTTP probes, CSV reconciliation, Python imports, and ABI coding. Dependency scheduling is a different capability.
- Python standard library: argparse, heapq, json, math, pathlib, sys; random for reproducible built-in tests.
- Supplied bare Lava cave image, SHA-256 `09ee8caaf2f2f23c437db97f072627760da64d33dbd2b3409379a24a4a38d26a`, used as the image-edit reference. Built-in image generation adds the first mark.
- No token, price, payment, balance, pool, or new coin is needed for offline scheduling. No RPC calls were made.

# Used in round 22

- Kept `GOAL.md` byte-for-byte unchanged. There were 21 existing numbered JSON
  records (01 painted, 02–21 placeholders); the assignment's count-plus-one rule
  makes this record 22. No older record or preview was changed.
- Read `gathering/REPORT.md`: no broken Line 1 behavior was reported. Its missing
  completed-task replanning and uncertainty margins motivated Replan.
- Reused the unchanged `tools/workplan/workplan.py` for full graph validation,
  remaining critical paths, relaxed lower bounds, and the original demo. Replan
  imports that sibling source and preserves Workplan's existing behavior.
- Python standard library only for the new worker tool: argparse, heapq,
  importlib.util, json, math, pathlib, sys. Tests also use copy, random, subprocess,
  and unittest. No new runtime package, coin, RPC, wallet, or API is needed.
- Used the inherited wall, SHA-256
  `3623847bb360b29abd63873ebc6afdce2aea40e33500cb0bdb41490b1ae6675d`, as the image
  tool's editing reference. An ochre snail, three chalk stones and a dotted trail
  were generated. A local mask retained all original pixels away from the new
  motif, including Pepe, his two five-digit hands, the old paths, sun and framing.
- Image skill path supplied by the environment was missing; no local replacement
  was found. Used the installed image-generation tool directly.
- Image assembly uses Node built-ins and vendored `jpeg-js` 0.4.4 `lib/encoder.js`
  (renamed `media/jpeg-encoder.cjs`) from
  `https://raw.githubusercontent.com/jpeg-js/jpeg-js/v0.4.4/lib/encoder.js`.
  Full source and license are ordinary files in `media/`; no package manager or
  network is needed to run them. The downloaded code was read before execution.
  This media helper is not a dependency of the Python worker tool.
- The brief simultaneously requests a JPEG beside the numbered record and bans
  pictures outside artifacts. Chose the explicit `dist/line-1/22.jpg` filename;
  this is the only new image outside artifacts. No extra image drafts were saved
  in the workspace. Both required wall paths contain the identical final PNG.

# Used in round 23

- Kept `GOAL.md` unchanged and read the gathering report first; it reports no
  broken Line 1 behavior. Reused Workplan's strict graph validation as Optplan's
  input boundary rather than duplicating or changing it.
- Added Optplan, a standard-library-only exact solver for at most 14 tasks with
  integer-minute estimates. It searches non-delay completion-event choices and
  proves the returned small schedule optimal. It reads only an explicit
  workspace-local JSON file; no coin, price, pool, RPC, wallet, network, or
  payment is needed for this offline planning goal.
- Used the inherited `artifacts/line-1/wall.png` as the image-edit reference.
  The installed image generator supplied a compact ochre stepping-stone trail
  and chalk five-digit handprint. The inherited local image assembler copied
  only nine small bare-rock disks from that edit; all 1,556,115 pixels outside
  the mask stayed byte-identical, including Pepe, both of his five-digit hands,
  the snail, old paths, sun, cracks and framing.
- The generated 1254px PNG was inspected before assembly. The finished 1254px
  PNG and 512px JPEG were inspected after assembly. No text, numbers, logos,
  signatures, frames, or watermarks are visible. The handprint has five digits;
  no new frog or other hand was introduced.

# Used in round 24

- Preserved `GOAL.md` byte-for-byte and all 23 existing numbered records. Read
  `gathering/REPORT.md`; it reported no broken Line 1 behavior. A local review
  found a flaw outside those checks: Optplan's non-delay search could falsely
  claim global optimality. Reproduced the old solver's 21-minute answer before
  editing; the repaired search finds 16 for the same five-task graph.
- Improved the existing `tools/optplan/` piece rather than replacing it. Reused
  the unchanged Workplan validator, both existing demo commands and the
  standard-library runtime. Added intentional waiting, a bounded exact search,
  strict bounded JSON input, a documented regression example, and an independent
  minute-grid test oracle. No installed package, network data, key, wallet,
  payment, coin or chain is needed for this scheduling capability.
- Read predecessor tools before executing them. Reran Workplan and Replan
  checks as compatibility checks. Their source and tests remain unchanged.
- Used inherited wall SHA-256
  `e3bb6c2d28c24b21fa05584ad27b70a09aef456f1f738c02cd0e4b1646f382fb`
  as the installed image generator's reference. The advertised imagegen skill
  was missing and no workspace replacement was found; used the tool directly.
  Copied its returned image bytes into the allowed named PNG output. No
  external generated-image file was read by a shell command.
- Reused the inspected inherited PNG codec and vendored JPEG encoder in
  `media/`. The new `finish-wall-24.cjs` keeps the preceding wall outside a
  small feathered bare-rock rectangle around the generated tortoise. It
  preserves 1,548,141 pixels outside the mask exactly; 24,313 pixels change
  inside it. Old Pepe, both five-digit hands, the handprint, snail, paths, sun,
  cracks outside the patch, lighting and framing remain.
- The brief requests `dist/line-1/24.jpg` while also banning pictures outside
  artifacts. As in earlier rounds, followed the explicit record-adjacent JPEG
  filename; it is the only new image outside artifacts and is below 100 KB.
  No old record or preview was changed. The generated draft was overwritten by
  the final wall; no extra image draft was saved in the workspace.
