// Round 24: retain the preceding wall outside a bare-rock tortoise patch.
// Uses only local files and the inherited PNG/JPEG codec, no network or env.
const fs = require('node:fs');
const crypto = require('node:crypto');
const {decode, encode, thumbnail} = require('./finish-wall.cjs');
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const previousPath = 'artifacts/line-1/wall-v4.png';
const outputPath = 'artifacts/line-1/wall-v5.png';
const previousBytes = fs.readFileSync(previousPath);
const previous = decode(previousBytes);
const generated = decode(fs.readFileSync(outputPath));
const result = {...previous, pixels: Buffer.from(previous.pixels)};
// These limits contain only the new tortoise, not an ancestral pigment mark.
const bounds = {left:824, top:352, right:1020, bottom:478};
function weight(x, y) {
  return Math.max(0, Math.min(1,
    (x-bounds.left)/8, (bounds.right-x)/8,
    (y-bounds.top)/8, (bounds.bottom-y)/8));
}
let changed = 0, protectedPixels = 0;
for (let y=0; y<previous.height; y++) for (let x=0; x<previous.width; x++) {
  const a=weight(x,y), offset=(y*previous.width+x)*3;
  if (!a) protectedPixels++;
  let differs = false;
  for (let channel=0; channel<3; channel++) {
    const i=offset+channel;
    result.pixels[i] = Math.round(previous.pixels[i]*(1-a)+generated.pixels[i]*a);
    differs ||= result.pixels[i] !== previous.pixels[i];
    if (!a && result.pixels[i] !== previous.pixels[i]) throw Error('preservation failed');
  }
  if (differs) changed++;
}
const png=encode(result), jpg=thumbnail(result);
if (!decode(png).pixels.equals(result.pixels)) throw Error('PNG round trip failed');
if (jpg.length>100000) throw Error('JPEG exceeds 100 KB');
fs.writeFileSync(outputPath,png);
fs.writeFileSync('artifacts/line-1/wall.png',png);
fs.writeFileSync('dist/line-1/24.jpg',jpg);
const report = {
  previous_sha256:hash(previousBytes), sha256:hash(png),
  format:'PNG', width:result.width, height:result.height, png_bytes:png.length,
  preview_format:'JPEG', preview_width:512, preview_height:512, preview_bytes:jpg.length,
  bounds, feather_pixels:8, changed_pixels:changed, protected_pixels:protectedPixels,
  total_pixels:previous.width*previous.height, outside_mask_changed_pixels:0,
  png_roundtrip_passed:true
};
fs.writeFileSync('line-1/media-check-24.json',JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
