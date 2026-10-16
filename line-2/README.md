# Line 2 — Safe entry

Goal: let any worker safely extract an untrusted ZIP archive into a workspace
with explicit path and resource limits. The first working piece is
[SafeZip](tools/safezip/README.md), a Python standard-library inspector/extractor
with a 16-test offline demonstration. No coin is required for this operation.

Current round: **24 — The Full Bowl**. SafeZip now limits distinct filesystem
nodes, including implicit parent directories, and validates all resource limits
as positive integers. All **44 tests passed**. Run
`python3 -B line-2/tools/safezip/selftest.py` from the repository root, or
`python3 -B line-2/tools/safezip/swarm_demo.py` for an offline round trip of a
captured public IMD API description. [Wall review](WALL-24.md) records the new
mark, dimensions, preservation check and limitations.

## Wall 01 — The Guarded Basket

Pepe keeps safe stones inside a basket and a thorn outside the arch: inspect
what enters before admitting it. This is also the record's Meaning.

Outputs:

- `artifacts/line-2/wall.png`: square PNG, 1254 × 1254, same dimensions as the input cave.
- `dist/line-2/01.jpg`: JPEG preview, 512 × 512, below 100 KB.
- `dist/line-2/01.json`: first record; image URL is the SHA-256 of the final PNG.

Review: manually inspected the completed image with view_image. Pepe has a wide
mouth and heavy-lidded eyes; both visible hands have five digits (four fingers
and a thumb). Ochre, charcoal and chalk marks occupy the central-left area;
the cave framing, warm light and major cracks remain recognizable with ample
bare stone. No letters, numbers, captions, logos, watermark or border observed.
Unmet visual requirements: none observed. Limitation: generative editing retains
the rock's appearance, not guaranteed pixel-identical rock outside the painting.
This was the first mark, so there were no ancestral line-2 marks to preserve.

## Image generation record

Used the built-in imagegen tool, not the fallback CLI. Final image was inspected
after a targeted hand correction. Prompt set:

1. Precise-object-edit of the supplied bare cave, preserving its square
1254 × 1254 size, rock, cracks, warm torch lighting, framing and color. Add a
modest prehistoric pigment painting in the central-left area, keeping most rock
bare. Recognizable Pepe has heavy-lidded eyes, a wide downturned mouth and squat
frog body, guarding an open woven basket beneath a stone arch. Three round stones
are safe inside; a thorn stays outside. Use worn uneven charcoal, red/yellow
ochre and chalk with rock grain showing through; Lascaux cave-art feel. Each of
two hands has exactly five digits. No text, numbers, logos, watermarks, borders,
modern icons, political symbols or real people.
2. Preserve the cave and painting; clarify only the hand above the basket as
five clearly distinct splayed charcoal/ochre digits, four fingers and one thumb,
attached to the curved arm. Keep the raised left hand unchanged. Preserve the
primitive worn pigment texture and all prohibitions on text and symbols.
