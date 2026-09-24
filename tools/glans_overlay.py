"""The head of every man's penis a little redder and glossy (A-31, the owner's poll 2026-09-25): "lets make it
more red bc rn its like dead color ... make it more glossy bc in reality penis head is like glossy".

Two LooksMenu overlays on the men's body (BodyTalk4, whose files stay untouched), painted in ITS OWN UV:
  AnatomyGlansFlush  a MULTIPLY pass (src = dest colour, dst = zero): white everywhere, rose on the head.
                     It multiplies the skin already lit, so the skin's own detail and light stay; only
                     the hue deepens. Unlit (lighting influence 0): it is a factor, not a colour.
  AnatomyGlansGloss  an ADDITIVE pass (one, one): a faint sheen on the head plus the game's own glass
                     cubemap (Textures1.ba2 Shared/Cubemaps/ShinyGlass_e.dds), masked to the head, so
                     the reflection moves with the view as a wet surface's does.
The head is where the tip bone Penis_05 carries the vertex (the same bone the shape scales, A-31):
mask = smoothstep(0.35, 0.8) of its weight, so both end at the crown. Painted triangle by triangle
(barycentric), never as a box: the shaft sits next to the head on the same UV island.

Measured, and the stage stops on it: no triangle that carries no head weight may cover a painted texel
(a mirrored or shared UV would redden something else).

The BGEM layout is the one decoded from materials that work in this game (scratchpad bgem_read: the
63-byte base header, five textures, 47 bytes of effect fields; Caliente's pubic hair overlay and a glass
material both read with nothing left over), and every file written is read back through it.

    python tools/glans_overlay.py [--data <Data>] [--out build/overlays]
"""
import argparse
import json
import math
import pathlib
import struct

import nif

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = pathlib.Path(r'D:\GOGGames\Fallout 4 GOTY\Data')
BODY = 'Meshes/Actors/Character/CharacterAssets/MaleBody.nif'
SHAPE, HEAD_BONE = 'BaseMaleBody:0', 'Penis_05'
SIZE = 2048
FLUSH = (1.0, 0.72, 0.75)           # the multiply factor on the head: red kept, green and blue down
SHEEN = 0.06                        # the gloss pass's own faint white on the head
ENV_SCALE = 0.35                    # how strongly the cubemap shows (the glass material: 0.53)
CUBEMAP = r'Shared\Cubemaps\ShinyGlass_e.dds'
NORMAL = r'Actors\Character\BaseHumanMale\BaseMaleBody_n.dds'
PLUGIN = 'Anatomy.esp'
TEX = r'Overlays\Anatomy'
FLUSH_ID, GLOSS_ID = 'AnatomyGlansFlush', 'AnatomyGlansGloss'


def smoothstep(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def paint(data):
    """(mask[SIZE*SIZE], overlap texels, head texels) from the live men's mesh."""
    body = nif.Nif(data / BODY)
    shape = body.shape(SHAPE)
    bones, _ = body.skin(shape)
    if HEAD_BONE not in bones:
        raise SystemExit(f'{BODY}: not weighted to {HEAD_BONE}: not the body this was measured on')
    k = bones.index(HEAD_BONE)
    head = [sum(w for s, w in shape.skin_weights(i) if s == k) for i in range(shape.count)]
    m = [smoothstep(0.35, 0.8, w) for w in head]
    uv = [shape.uv(i) for i in range(shape.count)]
    mask = [0.0] * (SIZE * SIZE)
    other = bytearray(SIZE * SIZE)
    for t in shape.triangles():
        pts = [(uv[i][0] * SIZE - 0.5, uv[i][1] * SIZE - 0.5) for i in t]
        lo_x = max(0, int(math.floor(min(p[0] for p in pts))))
        hi_x = min(SIZE - 1, int(math.ceil(max(p[0] for p in pts))))
        lo_y = max(0, int(math.floor(min(p[1] for p in pts))))
        hi_y = min(SIZE - 1, int(math.ceil(max(p[1] for p in pts))))
        (x0, y0), (x1, y1), (x2, y2) = pts
        den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(den) < 1e-12:
            continue
        carries = max(head[i] for i in t) > 0.05
        for y in range(lo_y, hi_y + 1):
            for x in range(lo_x, hi_x + 1):
                a = ((y1 - y2) * (x - x2) + (x2 - x1) * (y - y2)) / den
                b = ((y2 - y0) * (x - x2) + (x0 - x2) * (y - y2)) / den
                c = 1.0 - a - b
                if a < -1e-6 or b < -1e-6 or c < -1e-6:
                    continue
                o = y * SIZE + x
                if carries:
                    mask[o] = max(mask[o], a * m[t[0]] + b * m[t[1]] + c * m[t[2]])
                else:
                    other[o] = 1
    # grow the painted head two texels into texels NO triangle covers, so filtering has no dark rim
    covered = [v > 0 for v in mask]
    for _ in range(2):
        grown = list(mask)
        for y in range(1, SIZE - 1):
            row = y * SIZE
            for x in range(1, SIZE - 1):
                o = row + x
                if mask[o] > 0 or other[o]:
                    continue
                n = max(mask[o - 1], mask[o + 1], mask[o - SIZE], mask[o + SIZE])
                if n > 0:
                    grown[o] = n
        mask = grown
    overlap = sum(1 for o in range(SIZE * SIZE) if other[o] and covered[o] and mask[o] > 0.1)
    painted = sum(1 for v in mask if v > 0.1)
    return mask, overlap, painted


def dds(path, rgb):
    from PIL import Image
    im = Image.new('RGB', (SIZE, SIZE))
    im.putdata(rgb)
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, 'DDS', pixel_format='DXT1')


def bgem(base, envmap='', normal=NORMAL, envmask='', src=6, dst=7, env=False, lighting=0.0):
    """A version-2 BGEM, field by field in the layout decoded from working materials."""
    head = b'BGEM' + struct.pack('<II4ff', 2, 3, 0.0, 0.0, 1.0, 1.0, 1.0)
    head += struct.pack('<BIIB', 1, src, dst, 0)                           # alpha blend on, src, dst, test ref
    head += bytes([0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0])                         # alpha test off, z write OFF, z test on
    head += struct.pack('<fBfB', 0.0, 1 if env else 0, ENV_SCALE, 0)         # refraction power, envmap, scale, g2p
    assert len(head) == 63, len(head)
    out = head
    for p in (base, '', envmap, normal, envmask):
        raw = p.encode('ascii') + b'\0'
        out += struct.pack('<I', len(raw)) + raw
    out += bytes(6)                                                          # blood, lighting, falloff .. soft: off
    out += struct.pack('<3f', 1.0, 1.0, 1.0)                                 # base colour white
    out += struct.pack('<6f', 1.0, 0.0, 0.0, 0.0, 0.0, lighting)             # colour scale, falloff, lighting infl.
    out += struct.pack('<Bf', 0, 0.0)                                        # envmap min LOD, soft depth
    return out


def read_back(blob):
    """(src, dst, envmap flag, textures, lighting) from a BGEM, by the same decoded layout."""
    src, dst = struct.unpack_from('<II', blob, 33)
    env = blob[57]
    o, tex = 63, []
    for _ in range(5):
        n = struct.unpack_from('<I', blob, o)[0]
        tex.append(blob[o + 4:o + 4 + n - 1].decode('ascii'))
        o += 4 + n
    lighting = struct.unpack_from('<f', blob, o + 6 + 12 + 20)[0]
    if len(blob) != o + 47:
        raise SystemExit(f'BGEM is {len(blob)} bytes, the layout says {o + 47}')
    return src, dst, env, tex, lighting


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--data', type=pathlib.Path, default=DATA)
    ap.add_argument('--out', type=pathlib.Path, default=ROOT / 'build/overlays')
    args = ap.parse_args()
    mask, overlap, painted = paint(args.data)
    print(f'head mask: {painted} texels painted at {SIZE}; texels also covered by a triangle with no head weight: {overlap}')
    if overlap:
        raise SystemExit('another part of the body shares the head\'s UV: it would be tinted too')
    if painted < 500:
        raise SystemExit('almost nothing painted: the UVs or the bone are not what was measured')
    tex = args.out / 'Textures' / TEX.replace('\\', '/')
    dds(tex / 'GlansFlush.dds', [tuple(round(255 * (1 - v * (1 - f))) for f in FLUSH) for v in mask])
    dds(tex / 'GlansSheen.dds', [(round(255 * v * SHEEN),) * 3 for v in mask])
    dds(tex / 'GlansMask.dds', [(round(255 * v),) * 3 for v in mask])
    mats = args.out / 'Materials' / TEX.replace('\\', '/')
    mats.mkdir(parents=True, exist_ok=True)
    flush = bgem(TEX + r'\GlansFlush.dds', src=4, dst=1)                    # dest colour x ours
    gloss = bgem(TEX + r'\GlansSheen.dds', envmap=CUBEMAP, envmask=TEX + r'\GlansMask.dds', src=0, dst=0, env=True,
                 lighting=1.0)                                               # one + one
    for name, blob, want in ((FLUSH_ID, flush, (4, 1, 0)), (GLOSS_ID, gloss, (0, 0, 1))):
        src, dst, env, texs, _ = read_back(blob)
        if (src, dst, env) != want:
            raise SystemExit(f'{name}: read back src {src} dst {dst} envmap {env}, wrote {want}')
        (mats / f'{name}.bgem').write_bytes(blob)
        print(f'{name}.bgem: blend {src}/{dst}, envmap {env}, textures {[t for t in texs if t]}')
    templates = [dict(id=i, name=n, slots=[dict(slot=3, material='Overlays\\Anatomy\\' + i + '.bgem')], playable=False,
                      transformable=False, sort=0, gender=0)
                 for i, n in ((FLUSH_ID, 'Anatomy - glans colour'), (GLOSS_ID, 'Anatomy - glans gloss'))]
    tj = args.out / 'F4SE/Plugins/F4EE/Overlays' / PLUGIN / 'overlays.json'
    tj.parent.mkdir(parents=True, exist_ok=True)
    tj.write_text(json.dumps(templates, indent=4), encoding='utf-8')
    print(f'{tj.relative_to(args.out)}: {len(templates)} templates, gender 0 (men), slot 3 (body)')


if __name__ == '__main__':
    main()
