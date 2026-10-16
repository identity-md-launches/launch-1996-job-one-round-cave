# Every Pebble Has a Place

## Step 24: RewardBatch

[RewardBatch](tools/rewardbatch/README.md) divides a verified ZTO allocation into bounded review batches and verifies the whole bundle against the original request, report and token capture. Every contributor appears exactly once, including zero-unit shares. It neither prepares nor sends payments.

```sh
python3 -B line-3/tools/rewardbatch/rewardbatch.py demo
```

The offline demo returned 0: two batches of two and one contributors retain exactly 1 ZTO. Eleven tests passed, including 160 seeded partitions and file-based CLI checks. The new cave mark is three charcoal bowls enclosed by an ochre loop. Every pixel outside its bare-rock rectangle, including both ancestral Pepes and the five-digit hand, remains unchanged. The required `artifacts/line-3/wall-v5.png` and canonical `wall.png` are PNG, 1254 × 1254; `dist/line-3/24.jpg` is JPEG, 512 × 512, below 100 KB. [Step 24 review](step-24-review.json) records the built-in imagegen prompt, checks and visual limitations. No unmet visual requirement was identified.

## Step 23: RewardCompare

[RewardCompare](tools/rewardcompare/README.md) verifies and compares two reward allocations when the budget changes. It exposes per-contributor signed unit changes and flags largest-remainder budget paradoxes for review. Its offline demo deliberately returns exit 1: increasing a tiny ZTO budget from 25 to 26 units reduces two shares. Eleven tests (including 250 seeded comparisons) and file-based CLI trials passed.

```sh
python3 -B line-3/tools/rewardcompare/rewardcompare.py demo
```

The new mark adds two charcoal bowls with three and two ochre pebbles under an ochre bridge, on previously bare upper-middle rock. Both ancestral Pepes and the existing five-digit hand remain pixel-identical. The required `artifacts/line-3/wall-v4.png` is PNG, 1254 × 1254; canonical `wall.png` points to it. `dist/line-3/23.jpg` is JPEG, 512 × 512 and below 100 KB. The record is `dist/line-3/23.json`. [Step 23 review](step-23-review.json) records formats, the generation prompt, tests, preservation bounds and visual limitations. No unmet visual requirement was identified in the full-size and thumbnail review.

## Step 22: RewardReceipt

[RewardReceipt](tools/rewardreceipt/README.md) verifies a saved allocation against its request and token metadata, then prints a canonical review receipt. Its offline demo and eight checks passed. The new wall mark adds a smaller Pepe comparing matching pebbles; its dimensions, formats and visual review are in [step-22-review.json](step-22-review.json).

Line 3 began with [RewardSplit](tools/rewardsplit/README.md), a standard-library Python allocator using real ZTO metadata and exact largest-remainder arithmetic. Its fixed goal is exact ZTO reward allocation for workers.

From the repository root:

```sh
python3 -B line-3/tools/rewardsplit/rewardsplit.py demo
```

The offline demo splits 1 ZTO among three illustrative task roles, distributes the one leftover smallest unit deterministically, and leaves zero units unallocated. A live, read-only Ethereum observation confirmed the metadata. All 15 offline tests passed, including 300 seeded conservation and proportionality cases. The tool README documents the input format, exact observation, limits, and tests.

The wall adds a charcoal-and-ochre Pepe dividing pebbles among three bowls. It begins from the supplied bare cave; there were no ancestor marks on this line. The square image retains the cave's framing, torchlit warm rock, recognizable cracks and floor, and leaves most of the upper/right wall for future additions. Pepe has one visible hand: four fingers and one thumb. The other hand is concealed. There are no handprints, letters, numerals, captions, signatures, or logos.

The finished wall is `artifacts/line-3/wall.png`: **PNG, 1254 × 1254**. Its companion is `dist/line-3/01.jpg`: **JPEG, 512 × 512**, under 100 KB. The only saved pictures are those two required deliverables. The numbered metadata is `dist/line-3/01.json`; its image URL contains the SHA-256 of the actual wall bytes. The PNG is left untracked for the output uploader.

The worker explicitly reviewed the generated full-size image and the encoded thumbnail. No unmet visual requirement was identified; generative editing cannot certify pixel-exact preservation of every rock texture. Dimensions, formats, hand count, and limitations are also recorded in [review.json](review.json).

The built-in imagegen tool edited the bare cave. Its prompt asked for a modest first prehistoric mark on the lower-left rock face: recognizable heavy-lidded Pepe, three shallow bowls and ochre pebbles, exactly five digits on the sole visible hand, earth pigments with bare stone showing through, unchanged cave dimensions/lighting/framing, abundant untouched space, and no text, logos, stencils, or photographic/3D figures. The JPEG is a 512-pixel conversion of that finished wall.

No coins are required to run this piece. It computes allocations and reads public token metadata; it does not access wallets or send payments.
