#!/usr/bin/env python3
"""Place the image tool's isolated pigment on bare rock, preserving all other pixels.

Build-time only: run once after generation into wall-v5.png. The generated image
is consumed in memory and replaced by the complete wall. No intermediate image
is saved. JPEG uses the existing local line-1 BSD-licensed encoder through Node.
"""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import zlib

from check_delivery import png


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(width, height, pixels):
    def chunk(kind, payload):
        return (struct.pack('>I', len(payload)) + kind + payload
                + struct.pack('>I', zlib.crc32(kind + payload) & 0xffffffff))
    stride = width * 3
    raw = bytearray()
    for y in range(height):
        row = pixels[y*stride:(y+1)*stride]
        raw.append(1)
        raw.extend((value - (row[i-3] if i >= 3 else 0)) & 255
                   for i, value in enumerate(row))
    return (b'\x89PNG\r\n\x1a\n'
            + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


def main():
    previous = Path('artifacts/gathering/wall-v4.png').read_bytes()
    output_path = Path('artifacts/gathering/wall-v5.png')
    generated = output_path.read_bytes()
    (width, height), original = png(previous)
    (gw, gh), pigment = png(generated)
    assert (width, height) == (1254, 1254)
    assert (gw, gh) == (1024, 1024), 'requires the reviewed isolated mark'
    result = bytearray(original)
    # Bare rock beyond the inherited red trail; no ancestor pigment is inside.
    x, y, w, h = 1000, 850, 150, 145
    sx, sy, sw, sh = 340, 380, 335, 325
    changed = 0
    for row in range(h):
        for column in range(w):
            red_coverage = yellow_coverage = 0
            # Nine samples keep the worn generated edges at this smaller scale.
            for dy in range(3):
                for dx in range(3):
                    px = int(sx + (column + (dx+.5)/3) * sw / w)
                    py = int(sy + (row + (dy+.5)/3) * sh / h)
                    r, g, b = pigment[(py*gw+px)*3:(py*gw+px)*3+3]
                    if r > g and r - b > 45:
                        coverage = min(1, (r-b)/180)
                        if g > r*.65:
                            yellow_coverage += coverage/9
                        else:
                            red_coverage += coverage/9
            coverage = red_coverage + yellow_coverage
            if coverage < .07:
                continue
            offset = ((y+row)*width+x+column)*3
            rock = original[offset:offset+3]
            # Flatten the generated colors into earth pigment. The original
            # stone supplies every shadow and crack; no generated shading survives.
            mix = yellow_coverage / coverage
            color = [187*(1-mix)+206*mix, 89*(1-mix)+158*mix, 42*(1-mix)+83*mix]
            grain = .7 + .3 * ((column*73 + row*37) % 29)/28
            alpha = .76 * coverage * grain
            result[offset:offset+3] = bytes(round(c*(1-alpha)+p*alpha) for c,p in zip(rock,color))
            changed += result[offset:offset+3] != rock
    encoded = encode(width, height, result)
    assert png(encoded)[1] == result
    output_path.write_bytes(encoded)
    canonical = Path('artifacts/gathering/wall.png')
    assert canonical.is_symlink()
    canonical.unlink()
    canonical.symlink_to('wall-v5.png')
    subprocess.run(['node', '-e', "const fs=require('node:fs'); const c=require('./line-1/media/finish-wall.cjs'); const p=c.thumbnail(c.decode(fs.readFileSync('artifacts/gathering/wall-v5.png'))); if(p.length>100000)throw Error('preview too large'); fs.writeFileSync('dist/gathering/24.jpg',p);"], check=True)
    protected_old, protected_new = hashlib.sha256(), hashlib.sha256()
    outside = 0
    for row in range(height):
        for column in range(width):
            if not (x <= column < x+w and y <= row < y+h):
                pos=(row*width+column)*3
                a,b=original[pos:pos+3],result[pos:pos+3]
                outside += a != b
                protected_old.update(a); protected_new.update(b)
    assert outside == 0 and protected_old.digest() == protected_new.digest()
    report = {'inherited_wall_sha256':sha(previous), 'generated_mark_sha256':sha(generated),
              'output_sha256':sha(encoded), 'mark_rectangle':[x,y,w,h],
              'source_crop':[sx,sy,sw,sh], 'changed_pixels_inside':changed,
              'pixels_changed_outside':outside, 'protected_rgb_sha256':protected_new.hexdigest(),
              'method':'Image-tool pigment crop flattened to ochre and alpha-composited on bare stone; unchanged RGB everywhere else.'}
    Path('gathering/preservation-24.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
