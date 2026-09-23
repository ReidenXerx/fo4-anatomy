"""The body texture for the genitals: Nahka's painted inside, in the owner's skin, nothing else touched.

Nahka's new triangles sample a corner of the body atlas that CBBE does not use (tools/uv_check.py),
and the owner's skin maps are flat filler there, so the lips and canals render as plain skin. The
body's shader names a material (basehumanFemaleskin.bgsm), and the material decides the textures,
so the only way in is the same texture files, patched, at the same paths: a mod that wins that
conflict (Anatomy-dev, after the skin mod).

  mask     the genital triangles' UVs rasterised at the texture's size, padded 8 texels (filtering
           and mips reach past a triangle's edge); texels any OTHER triangle samples are left out.
  colour   the diffuse is matched in linear light: per-channel gains that carry Nahka's skin tone
           onto the owner's, measured on the ring of crotch skin around the genitals in both
           textures (same UVs: shared vertices keep CBBE's UVs, A-4). Her mucosa keeps its shift
           relative to her skin. The specular map is matched by OFFSET, not gain: the owner's skin
           has almost no specular (red ~0.3 of 255 against Nahka's ~48), so a gain would make her
           wet mucosa as matte as skin. Her skin level lands on the owner's, and only what she
           painted ABOVE her skin level is added. Normals are copied as she drew them (her genital
           vertices keep her tangents, A-4).
  seam     the island's edge meets the crotch skin across a UV seam (116 points). Colour and
           specular are corrected there to match the skin side exactly, the correction fading
           inward over FEATHER texels (Gaussian-weighted from the nearest seam points), so the
           edge carries no line. Normals fade to flat at the edge instead: the two sides of a UV
           seam use different tangent frames, so equal values would not be equal normals, and
           flat is continuous in any frame.
  blocks   DXT1/BC5 are 4x4 blocks. Only blocks the padded mask reaches are re-encoded, on every
           mip level (each level from the patched top level, box-filtered). Every other block of
           every level keeps the owner's bytes, and the check proves it.

Inputs are read, never written: the deployed textures in Data and Nahka's archive. Outputs (they
carry both of theirs, A-2: never in git) go to D:\\F4Output\\AnatomyLab\\textures.

    python tools/genital_texture.py            # build + verify all six maps (clean and dirty)
"""
import io
import json
import math
import pathlib
import struct
import sys

from PIL import Image, ImageDraw, ImageFilter

import align_body as ab
import nif

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKIN = ab.DEFAULT_DATA / 'Textures/Actors/Character/BaseHumanFemale'
NAHKA = ROOT / 'build/nahka_tex/Data/Body Textures/Textures/Actors/Character/BaseHumanFemale'
OUT = pathlib.Path(r'D:\F4Output\AnatomyLab\textures')
CORNER = (0.15, 0.80, 0.55, 1.0)      # u0, v0, u1, v1: where the genital island lies (uv_check.py)
PAD = 8                               # texels of padding around the island, at the top level
RING = 3.0                            # crotch skin within this of the genitals sets the colour match
FEATHER = 32                          # texels over which the seam correction fades out
SIGMA = 10.0                          # Gaussian reach of one seam point's correction, in texels
# Zero-touch (A-21): the genitals are their own shape with their own material. Its textures are the
# player's skin, AS THE BODY'S MATERIAL NAMES IT, with Nahka's island patched in, written to OUR paths.
# (Before A-21 the patch went over Textures/Actors/Character/BaseHumanFemale, but the owner's body
# material, CBBE Holy Fix's, names Actors/Character/custombody/: that patch was never shown.)
SKIN_MATERIAL = 'Materials/actors/Character/BaseHumanFemale/basehumanFemaleskin.bgsm'
ANATOMY_OUT = OUT / 'Anatomy'
# (material slot, our file, Nahka file, kind); the dirty variants are not ours (accepted, A-21)
MAPS = [('diffuse', 'FemaleBody_d.dds', 'femalebody_d.dds', 'colour'),
        ('normal', 'FemaleBody_n.dds', 'femalebody_n.dds', 'normal'),
        ('smoothspec', 'FemaleBody_s.dds', 'femalebody_s.dds', 'specular')]


# --------------------------------------------------------------------------
# DDS: legacy FourCC files (DXT1 = BC1, 8 bytes a block; BC5U/ATI2 = BC5, 16 bytes a block)
# --------------------------------------------------------------------------

class Dds:
    def __init__(self, path, data=None):
        """A file, or (a label, the bytes) for a texture read out of an archive (gamedata)."""
        self.path = pathlib.Path(path)
        self.b = bytearray(data if data is not None else self.path.read_bytes())
        self.h, self.w = struct.unpack_from('<II', self.b, 12)
        self.mips = max(1, struct.unpack_from('<I', self.b, 28)[0])
        self.fourcc = bytes(self.b[84:88])
        if self.fourcc == b'DX10':
            raise SystemExit(f'{path}: DX10 header not handled')
        self.block = 8 if self.fourcc == b'DXT1' else 16 if self.fourcc in (b'BC5U', b'ATI2') else None
        if self.block is None:
            raise SystemExit(f'{path}: unexpected format {self.fourcc}')
        self.pil_format = 'DXT1' if self.block == 8 else 'BC5'

    def level(self, L):
        """(width, height, blocks across, blocks down, byte offset) of mip level L."""
        off = 128
        for k in range(L + 1):
            w, h = max(1, self.w >> k), max(1, self.h >> k)
            bx, by = max(1, (w + 3) // 4), max(1, (h + 3) // 4)
            if k == L:
                return w, h, bx, by, off
            off += bx * by * self.block

    def top(self):
        return Image.open(io.BytesIO(bytes(self.b))).convert('RGB')


def encode_blocks(img, pil_format):
    """Pillow's encoder, stripped of its header: the image's 4x4 blocks in raster order."""
    buf = io.BytesIO()
    img.save(buf, 'DDS', pixel_format=pil_format)
    data = buf.getvalue()
    return data[148:] if pil_format == 'BC5' else data[128:]


# --------------------------------------------------------------------------
# geometry: which texels the genitals sample, which the crotch ring samples
# --------------------------------------------------------------------------

def islands(size):
    body = nif.Nif(ab.OUT / 'ShapeData/AnatomyBodyZeX/AnatomyBodyZeX.nif')
    s = body.shape(ab.SHAPE)
    pos = s.positions()
    uv = [s.uv(j) for j in range(s.count)]
    tris = s.triangles()
    shared = {int(j) for j in json.loads((ab.OUT / 'mapping.json').read_text())['output_to_cbbe']}
    genital = Image.new('L', (size, size), 0)
    other = Image.new('L', (size, size), 0)
    ring = Image.new('L', (size, size), 0)
    dg, do, dr = ImageDraw.Draw(genital), ImageDraw.Draw(other), ImageDraw.Draw(ring)
    centres = [(0.0, 1.55, -55.58), (0.0, -1.58, -54.07)]          # physics_design.OPENINGS
    n_gen = n_ring = 0
    for t in tris:
        cu = sum(uv[v][0] for v in t) / 3
        cv = sum(uv[v][1] for v in t) / 3
        poly = [(uv[v][0] * size, uv[v][1] * size) for v in t]
        in_corner = CORNER[0] <= cu <= CORNER[2] and CORNER[1] <= cv <= CORNER[3]
        if in_corner and any(v not in shared for v in t):       # Nahka's triangles only, never CBBE's
            dg.polygon(poly, fill=255)
            n_gen += 1
            continue
        do.polygon(poly, fill=255)
        near = min(math.dist(pos[v], c) for v in t for c in centres)
        if near <= RING:
            dr.polygon(poly, fill=255)
            n_ring += 1
    padded = genital.filter(ImageFilter.MaxFilter(2 * PAD + 1))
    # texels another triangle samples stay the owner's, however close to the island they are
    clash = sum(1 for a, b in zip(padded.get_flattened_data(), other.get_flattened_data()) if a and b)
    core_clash = sum(1 for a, b in zip(genital.get_flattened_data(), other.get_flattened_data()) if a and b)
    mask = Image.composite(Image.new('L', (size, size), 0), padded, other)
    return mask, genital, ring, dict(genital_triangles=n_gen, ring_triangles=n_ring,
                                     padded_texels_other_samples=clash, island_texels_other_samples=core_clash)


# --------------------------------------------------------------------------
# colour
# --------------------------------------------------------------------------

def to_linear(c):
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def to_srgb(c):
    c = max(0.0, min(1.0, c))
    c = c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
    return int(round(c * 255))


LIN = [to_linear(float(i)) for i in range(256)]


def ring_means(img, ring, linear):
    sums, n = [0.0, 0.0, 0.0], 0
    for px, m in zip(img.get_flattened_data(), ring.get_flattened_data()):
        if m:
            for k in range(3):
                sums[k] += LIN[px[k]] if linear else px[k]
            n += 1
    return [s / max(n, 1) for s in sums], n


def matched(nahka, fit, kind):
    """Nahka's texels carried onto the owner's tone. colour: linear gains (fit = gains);
    specular: her level onto the owner's plus what she painted above it (fit = (owner, hers))."""
    if kind == 'normal':
        return nahka
    if kind == 'colour':
        lut = [[to_srgb(LIN[i] * g) for i in range(256)] for g in fit]
    else:
        own, hers = fit
        lut = [[max(0, min(255, int(round(own[k] + max(0.0, i - hers[k]))))) for i in range(256)] for k in range(3)]
    r, g, b = nahka.split()
    return Image.merge('RGB', (r.point(lut[0]), g.point(lut[1]), b.point(lut[2]) if kind == 'colour' else b))


# --------------------------------------------------------------------------
# build one map
# --------------------------------------------------------------------------

def build(src, nahka_name, kind, geometry):
    mask, island, ring, facts = geometry(src.w)
    own = src.top()
    nah_full = Image.open(NAHKA / nahka_name).convert('RGB')
    nah = nah_full.reduce(nah_full.size[0] // src.w) if nah_full.size[0] != src.w else nah_full
    report = dict(facts)
    fit = None
    if kind != 'normal':
        om, n = ring_means(own, ring, kind == 'colour')
        nm, _ = ring_means(nah, ring, kind == 'colour')
        report.update(ring_texels=n, owner_ring=[round(x, 4) for x in om], nahka_ring=[round(x, 4) for x in nm])
        if kind == 'colour':
            fit = [om[k] / nm[k] if nm[k] > 1e-6 else 1.0 for k in range(3)]
            report['gains'] = [round(g, 3) for g in fit]
        else:
            fit = (om, nm)
    patched = Image.composite(matched(nah, fit, kind), own, mask)
    raw = seam_difference(own, patched, src.w)
    patched = feather_seam(patched, mask, kind, src.w)
    report['seam'] = dict(raw, feathered=seam_difference(own, patched, src.w)['after'])
    out = bytearray(src.b)
    changed = 0
    for L in range(src.mips):
        w, h, bx, by, off = src.level(L)
        f = 1 << L
        m = mask if L == 0 else mask.reduce(f) if src.w % f == 0 else mask.resize((w, h), Image.BOX)
        target = patched if L == 0 else patched.reduce(f) if src.w % f == 0 else patched.resize((w, h), Image.BOX)
        mp = m.load()
        blocks = [(x, y) for y in range(by) for x in range(bx)
                  if any(mp[i, j] for j in range(4 * y, min(h, 4 * y + 4)) for i in range(4 * x, min(w, 4 * x + 4)))]
        if not blocks:
            continue
        x0, x1 = min(b[0] for b in blocks), max(b[0] for b in blocks)
        y0, y1 = min(b[1] for b in blocks), max(b[1] for b in blocks)
        crop = target.crop((4 * x0, 4 * y0, min(w, 4 * x1 + 4), min(h, 4 * y1 + 4)))
        enc = encode_blocks(crop, src.pil_format)
        cw = x1 - x0 + 1
        for x, y in blocks:
            k = (y - y0) * cw + (x - x0)
            dst = off + (y * bx + x) * src.block
            out[dst:dst + src.block] = enc[k * src.block:(k + 1) * src.block]
            changed += 1
    report['blocks_reencoded'] = changed
    return src, out, report, mask


SEAM = {}


def seam_pairs():
    """Copies of one point split by the UV seam where the genital island meets the crotch skin:
    (the genital copy's uv, the skin copy's uv)."""
    if 'pairs' not in SEAM:
        body = nif.Nif(ab.OUT / 'ShapeData/AnatomyBodyZeX/AnatomyBodyZeX.nif')
        s = body.shape(ab.SHAPE)
        pos = s.positions()
        wid = nif.weld(pos)
        groups = {}
        for j, g in enumerate(wid):
            groups.setdefault(g, []).append(j)
        corner = (lambda uv: CORNER[0] <= uv[0] <= CORNER[2] and CORNER[1] <= uv[1] <= CORNER[3])
        pairs = []
        for js in groups.values():
            gen = [s.uv(j) for j in js if corner(s.uv(j))]
            skin = [s.uv(j) for j in js if not corner(s.uv(j))]
            if gen and skin:
                pairs.append((gen[0], skin[0]))
        SEAM['pairs'] = pairs
    return SEAM['pairs']


def seam_difference(before, after, size):
    """Mean |difference| across the seam (0-255 per channel), before and after the patch."""
    pairs = seam_pairs()
    if not pairs:
        return 'no seam pairs'
    pb, pa = before.load(), after.load()
    at = (lambda uv: (min(size - 1, int(uv[0] * size)), min(size - 1, int(uv[1] * size))))
    diff = (lambda img: [sum(abs(img[at(g)][k] - img[at(sk)][k]) for g, sk in pairs) / len(pairs) for k in range(3)])
    return dict(pairs=len(pairs), before=[round(x, 1) for x in diff(pb)], after=[round(x, 1) for x in diff(pa)])


def feather_seam(img, mask, kind, size):
    """Pull the island's edge onto the skin across the seam, fading inward (see the docstring)."""
    pairs = seam_pairs()
    at = (lambda uv: (min(size - 1, int(uv[0] * size)), min(size - 1, int(uv[1] * size))))
    px, mp = img.load(), mask.load()
    lin = kind == 'colour'
    val = (lambda c: [LIN[x] for x in c] if lin else [float(x) for x in c])
    pts = []
    for g, sk in pairs:
        gp, sp = at(g), at(sk)
        if kind == 'normal':
            d = [128 - px[gp][0], 128 - px[gp][1], 0.0]                  # towards flat
        else:
            a, b = val(px[sp]), val(px[gp])
            d = [a[k] - b[k] for k in range(3)]
        pts.append((gp, d))
    cell = FEATHER
    grid = {}
    for i, ((x, y), _) in enumerate(pts):
        grid.setdefault((x // cell, y // cell), []).append(i)
    xs = [p[0][0] for p in pts]
    ys = [p[0][1] for p in pts]
    for y in range(max(0, min(ys) - FEATHER), min(size, max(ys) + FEATHER + 1)):
        for x in range(max(0, min(xs) - FEATHER), min(size, max(xs) + FEATHER + 1)):
            if not mp[x, y]:
                continue
            near = [i for gx in (x // cell - 1, x // cell, x // cell + 1) for gy in (y // cell - 1, y // cell, y // cell + 1)
                    for i in grid.get((gx, gy), ())]
            if not near:
                continue
            dist = [((pts[i][0][0] - x) ** 2 + (pts[i][0][1] - y) ** 2) ** 0.5 for i in near]
            r = min(dist)
            if r > FEATHER:
                continue
            fade = (1 - r / FEATHER) ** 2
            ws = [math.exp(-(d * d) / (2 * SIGMA * SIGMA)) for d in dist]
            tot = sum(ws) or 1.0
            corr = [sum(w * pts[i][1][k] for w, i in zip(ws, near)) / tot * fade for k in range(3)]
            c = px[x, y]
            if lin:
                v = [to_srgb(LIN[c[k]] + corr[k]) for k in range(3)]
            else:
                v = [max(0, min(255, int(round(c[k] + corr[k])))) for k in range(3)]
            if kind != 'colour':
                v[2] = c[2]
            px[x, y] = tuple(v)
    return img


def verify(src, out, mask):
    """Every block the padded mask does not reach, on every level, is the owner's byte for byte."""
    bad = 0
    for L in range(src.mips):
        w, h, bx, by, off = src.level(L)
        f = 1 << L
        m = mask if L == 0 else mask.reduce(f) if src.w % f == 0 else mask.resize((w, h), Image.BOX)
        mp = m.load()
        for y in range(by):
            for x in range(bx):
                hit = any(mp[i, j] for j in range(4 * y, min(h, 4 * y + 4)) for i in range(4 * x, min(w, 4 * x + 4)))
                a = off + (y * bx + x) * src.block
                if not hit and src.b[a:a + src.block] != out[a:a + src.block]:
                    bad += 1
    return bad


def main(data=None):
    """Zero-touch (A-21): read the skin the BODY'S MATERIAL names (loose or in an archive, the copy
    the game would load), patch Nahka's island in, and write our textures plus our material:
        ANATOMY_OUT/FemaleBody_d/n/s.dds   -> Data/Textures/Anatomy/
        ANATOMY_OUT/AnatomyGenitals.bgsm   -> Data/Materials/Anatomy/  (the skin material, our paths)"""
    import bgsm
    import gamedata
    game = gamedata.Game(data or ab.DEFAULT_DATA)
    material = game.read(SKIN_MATERIAL)
    slots, _ = bgsm.textures(material)
    names = dict(zip(bgsm.NAMES, slots))
    print(f'skin material: {game.describe(SKIN_MATERIAL)}; textures {[names[m[0]] for m in MAPS]}')
    ANATOMY_OUT.mkdir(parents=True, exist_ok=True)
    cache = {}

    def geometry(size):
        if size not in cache:
            cache[size] = islands(size)
        return cache[size]
    problems = []
    for slot, ours, nahka_name, kind in MAPS:
        rel = 'Textures/' + names[slot]
        if not names[slot] or game.find(rel) is None:
            problems.append(f'{slot}: the skin material names {names[slot]!r}, which the game does not have')
            continue
        src = Dds(rel, game.read(rel))
        src, out, report, mask = build(src, nahka_name, kind, geometry)
        bad = verify(src, out, mask)
        (ANATOMY_OUT / ours).write_bytes(out)
        print(f'{ours} from {game.describe(rel)} ({src.w}x{src.h} {src.fourcc.decode()} {src.mips} mips, {kind}): '
              f'{report}; blocks outside the patch that differ from the skin\'s: {bad}')
        if bad:
            problems.append(ours)
        if report['island_texels_other_samples']:
            problems.append(f'{ours}: another triangle samples the island itself')
    ours_material = bgsm.with_textures(material, {m[0]: f'Anatomy/{m[1]}' for m in MAPS})
    (ANATOMY_OUT / 'AnatomyGenitals.bgsm').write_bytes(ours_material)
    back, _ = bgsm.textures(ours_material)
    print(f'AnatomyGenitals.bgsm: the skin material with textures {back[:3]}')
    if problems:
        print('\nFAIL - ' + '; '.join(problems))
        sys.exit(1)
    print(f'\nPASS - wrote {ANATOMY_OUT}; outside the genital patch every block of every mip is the skin\'s.')


if __name__ == '__main__':
    main()
