"""The head of every man's penis a little redder and glossy (A-31, the owner's poll 2026-09-25): "lets make it
more red bc rn its like dead color ... make it more glossy bc in reality penis head is like glossy".

Two LooksMenu overlays on the men's body (BodyTalk4, whose files stay untouched), painted in ITS OWN UV:
  AnatomyGlansFlush  a MULTIPLY pass (src = dest colour, dst = zero): white everywhere, rose on the head.
                     It multiplies the skin already lit, so the skin's own detail and light stay; only
                     the hue deepens. Unlit (lighting influence 0): it is a factor, not a colour.
  AnatomyGlansGloss  a LIT pass: the men's own skin material (basehumanskin.bgsm, read as the game
                     loads it) with its colour black, blended ADDITIVELY (one + one), so all it adds is
                     its specular: ours, strong and very smooth on the head
                     only, over the skin's own normal map. Real highlights from real lights, as a wet
                     surface shows them. Rim, subsurface, skin tint and shadow casting are off (a black
                     diffuse must add nothing else).
                     The first gloss (2026-09-25) was an unlit effect pass with the game's glass cubemap;
                     the owner: "its not gloss its like condom of top of head". A reflection with no
                     lighting reads as a clear shell. LMNSOverlays' nail polish (lit BGSM overlays)
                     showed LooksMenu takes lit materials.
                     Blended (one, inverse source alpha) first, it turned the whole man near black at
                     some angles (the owner, 2026-09-25): the lit shader does not carry the texture's
                     alpha 0 through, so the black covered him. One + one needs no alpha: black adds 0.
The head is where the tip bone Penis_05 carries the vertex (the same bone the shape scales, A-31):
mask = smoothstep(0.35, 0.8) of its weight, so both end at the crown. Painted triangle by triangle
(barycentric), never as a box: the shaft sits next to the head on the same UV island.

Measured, and the stage stops on it: no triangle that carries no head weight may cover a painted texel
(a mirrored or shared UV would redden something else).

The BGEM layout is the one decoded from materials that work in this game (scratchpad bgem_read: the
63-byte base header, five textures, 47 bytes of effect fields; Caliente's pubic hair overlay and a glass
material both read with nothing left over), and every file written is read back through it. The BGSM's
lighting fields were decoded the same way on the men's skin and LMNS's nail material (scratchpad
bgsm_read: both parse to 25 identical trailing bytes); only those fields are changed here.

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
SPEC, GLOSS = 1.0, 0.85            # the head's specular map: red = strength, green = smoothness (wet)
SPEC_MULT = 1.6                     # the material's specular multiplier (the skin's own: 1.0)
SKIN = 'Materials/actors/Character/BaseHumanMale/basehumanskin.bgsm'
ENV_SCALE = 1.0
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


def gloss_bgsm(skin):
    """The men's skin material as the gloss pass: black, transparent colour; our specular map; one + inverse
    source alpha; rim, subsurface, skin tint and shadow casting off; specular multiplier SPEC_MULT."""
    o = 63
    tex = []
    for _ in range(9):
        n = struct.unpack_from('<I', skin, o)[0]
        tex.append(skin[o + 4:o + 4 + n - 1].decode('latin1'))
        o += 4 + n
    tail = bytearray(skin[o:])
    # the lighting fields, at their offsets from the end of the textures (decoded on two real files)
    if tail[1] not in (0, 1) or tail[10] not in (0, 1) or tail[15] != 1:
        raise SystemExit(f'{SKIN}: rim/subsurface/specular flags are not where the layout says: not a v2 skin BGSM')
    n = struct.unpack_from('<I', tail, 64)[0]
    after_root = 68 + n
    emit = tail[after_root + 1]
    flags = after_root + 2 + (12 if emit else 0) + 4          # model-space normals, then the bools
    cast, skin_tint = flags + 5, flags + 12 + 12 + 2
    tail[1] = 0                                               # rim lighting
    tail[10] = 0                                              # subsurface lighting
    struct.pack_into('<f', tail, 28, SPEC_MULT)
    tail[cast] = 0
    tail[skin_tint] = 0
    head = bytearray(skin[:63])
    head[32] = 1                                              # alpha blend
    struct.pack_into('<II', head, 33, 0, 0)                   # one + one: adds its specular and nothing else
    head[41] = 0                                              # alpha test ref
    head[42] = 0                                              # alpha test off
    head[43] = 0                                              # z write off: a coat, not a surface
    out = bytes(head)
    ours = [TEX + r'\GlansGlossBase.dds', tex[1], TEX + r'\GlansSpec.dds'] + [''] * 6
    for t in ours:
        raw = t.encode('ascii') + b'\0'
        out += struct.pack('<I', len(raw)) + raw
    return out + bytes(tail), tex


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
    dds(tex / 'GlansSpec.dds', [(round(255 * v * SPEC), round(255 * v * GLOSS), 0) for v in mask])
    from PIL import Image
    Image.new('RGBA', (4, 4), (0, 0, 0, 0)).save(tex / 'GlansGlossBase.dds', 'DDS', pixel_format='DXT5')
    mats = args.out / 'Materials' / TEX.replace('\\', '/')
    mats.mkdir(parents=True, exist_ok=True)
    flush = bgem(TEX + r'\GlansFlush.dds', src=4, dst=1)                    # dest colour x ours
    src, dst, env, texs, _ = read_back(flush)
    if (src, dst, env) != (4, 1, 0):
        raise SystemExit(f'{FLUSH_ID}: read back src {src} dst {dst} envmap {env}')
    (mats / f'{FLUSH_ID}.bgem').write_bytes(flush)
    print(f'{FLUSH_ID}.bgem: blend {src}/{dst}, textures {[t for t in texs if t]}')
    import gamedata
    skin = gamedata.Game(args.data).read(SKIN)
    gloss, skin_tex = gloss_bgsm(skin)
    if len(gloss) - len(skin) != sum(len(t) for t in (TEX + r'\GlansGlossBase.dds', TEX + r'\GlansSpec.dds')) - \
            sum(len(t) for t in (skin_tex[0], skin_tex[2])):
        raise SystemExit(f'{GLOSS_ID}: the lighting fields did not carry over whole')
    (mats / f'{GLOSS_ID}.bgsm').write_bytes(gloss)
    old = mats / f'{GLOSS_ID}.bgem'
    if old.exists():
        old.unlink()
    print(f'{GLOSS_ID}.bgsm: the men\'s skin material ({len(skin)} B), normal {skin_tex[1]}, specular map ours, '
          f'one + one, specular x{SPEC_MULT}')
    templates = [dict(id=i, name=n, slots=[dict(slot=3, material='Overlays\\Anatomy\\' + i + ext)], playable=False,
                      transformable=False, sort=0, gender=0)
                 for i, n, ext in ((FLUSH_ID, 'Anatomy - glans colour', '.bgem'), (GLOSS_ID, 'Anatomy - glans gloss', '.bgsm'))]
    tj = args.out / 'F4SE/Plugins/F4EE/Overlays' / PLUGIN / 'overlays.json'
    tj.parent.mkdir(parents=True, exist_ok=True)
    tj.write_text(json.dumps(templates, indent=4), encoding='utf-8')
    print(f'{tj.relative_to(args.out)}: {len(templates)} templates, gender 0 (men), slot 3 (body)')


if __name__ == '__main__':
    main()
