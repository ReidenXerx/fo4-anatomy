"""Servitron's breasts in rubber with robotic areolae, to match its rubber abdomen (the owner, 2026-10-08: "we need make
appropriate rubber designed tits like robotic", then "lets also design robotic areola and nipples", poll: "Chrome ring +
metal nipple cap").

Its "Boobs" torsos draw the breasts with Materials/Servitron/default/PlasticBoobs.bgsm; every paint style uses that one
file, and nothing else does. This writes a loose override of it and its three maps:
  - PlasticBoobs.bgsm: the rubber abdomen's own material (default/GITS_plastic.bgsm: gloss, environment map) on the maps
    below;
  - RubberBoobs_d.dds: Servitron's breast texture turned to dark rubber, and on each breast a brushed-chrome areola
    plate (eight rivets, a dark groove at its rim and round the nipple) with a polished metal cap on the nipple;
  - RubberBoobs_n.dds: our own normal map: smooth rubber (no skin pores), the plate, rivets, grooves and the domed cap in
    relief (nothing of a skin mod's normal map is shipped);
  - RubberBoobs_s.dds: the rubber's gloss (as the abdomen: specular 127, gloss 64), the metal brighter and glossier.
The areolae sit where the breast mesh's nipples are (Torso 2 GITS Boobs' "Boobs": the most forward vertex of each
breast), measured in UV space with the local UV-to-surface scale, so the design is round on the body.

    python tools/servitron_rubber.py <out folder (Data-relative tree)>
"""
import io
import math
import pathlib
import struct
import sys

import numpy as np
from PIL import Image, ImageOps

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import gamedata  # noqa: E402
import genital_texture as gt  # noqa: E402
import nif  # noqa: E402

ARCHIVES = pathlib.Path(r'D:\F4Output\servitron\x\main\Data')
BREAST_MESH = pathlib.Path(r'D:\F4Output\servitron\x\bs\Data\tools\BodySlide\ShapeData\Servitron\Torso 2 GITS Boobs.nif')
SRC_TEX = 'textures\\servitron\\plasticfemalebody_d.dds'
SRC_MAT = 'materials\\servitron\\default\\gits_plastic.bgsm'
OUT_MAT = 'Materials/Servitron/default/PlasticBoobs.bgsm'
OUT_D = 'Textures/Anatomy/Servitron/RubberBoobs_d.dds'
OUT_N = 'Textures/Anatomy/Servitron/RubberBoobs_n.dds'
OUT_S = 'Textures/Anatomy/Servitron/RubberBoobs_s.dds'
RUBBER = (24, 24, 28)        # the abdomen's rubber reads near-black with a cool cast
SPREAD = 0.55                # how much of the source's shading survives (0 flat, 1 all)
RUBBER_SPEC = (127, 64)      # the abdomen's own: flat_r127-g064_s
# the design (the owner's second look, 2026-10-08: "areola should be more elegant", "lets make areola + nipple also
# latex but slightly different material kind of latex"): a softly raised satin-latex areola in a deep plum graphite,
# less glossy than the body's rubber so it reads by its sheen, one fine seam at its rim (the only robotic line), and a
# glossy latex dome on the nipple. Sizes are fractions of the areola's radius as Servitron's own texture paints it.
AREOLA_TINT = (58, 36, 50)       # plum graphite
NIPPLE_TINT = (72, 44, 62)
SATIN = (110, 80)                # areola: softer sheen than the body (127, 64 spec but more spread)
GLOSS = (235, 210)               # nipple: glossy latex
NIPPLE = 0.30                    # nipple dome radius / areola radius
SEAM = (0.93, 0.98)              # the seam's band / areola radius
RELIEF = 2.2                     # normal strength (height units -> slope)
AREOLAE = []                     # what the last build drew: (uv centre, radius on the body)


def nipples(lum):
    """[(uv centre, 2x2 matrix uv offset -> surface offset in units, areola radius in units)] per breast: the centre
    and size of the areola Servitron's own texture paints (its dark disc near the breast's tip), the surface scale from
    the breast mesh around it"""
    n = nif.Nif(BREAST_MESH)
    s = n.shape('Boobs')
    pos = s.positions()
    L = np.asarray(lum, np.float32)
    size = L.shape[0]
    out = []
    for side in (-1, 1):
        vs = [i for i, p in enumerate(pos) if p[0] * side > 0.5]
        tip = max(vs, key=lambda i: pos[i][1])
        guess = s.uv(tip)
        # the painted areola: the darkest disc within 0.04 uv of the breast's tip
        r = int(0.04 * size)
        cx, cy = int(guess[0] * size), int(guess[1] * size)
        win = L[cy - r:cy + r, cx - r:cx + r]
        thr = win.min() + 0.5 * (np.median(win) - win.min())
        ys, xs = np.nonzero(win < thr)
        uv0 = ((cx - r + xs.mean() + 0.5) / size, (cy - r + ys.mean() + 0.5) / size)
        area_uv = len(xs) / size ** 2
        # the surface scale there: least squares uv -> (x, z) from the vertices around the painted centre
        cen = min(vs, key=lambda i: math.dist(s.uv(i), uv0))
        near = [i for i in vs if math.dist(pos[i], pos[cen]) < 1.8 and i != cen]
        A = np.array([[s.uv(i)[0] - s.uv(cen)[0], s.uv(i)[1] - s.uv(cen)[1]] for i in near])
        B = np.array([[pos[i][0] - pos[cen][0], pos[i][2] - pos[cen][2]] for i in near])
        M, *_ = np.linalg.lstsq(A, B, rcond=None)
        M = M.T
        radius = math.sqrt(area_uv * abs(np.linalg.det(M)) / math.pi)   # the disc's area, on the body
        out.append((uv0, M, radius))
    return out


def design(size, lum):
    """per texel: (height, colour rgb, spec, gloss, mask) arrays over the whole map, the design drawn at each areola"""
    h = np.zeros((size, size), np.float32)
    col = np.zeros((size, size, 3), np.float32)
    spec = np.zeros((size, size, 2), np.float32)
    mask = np.zeros((size, size), np.float32)
    AREOLAE.clear()
    for uv0, M, R in nipples(lum):
        AREOLAE.append((tuple(round(x, 4) for x in uv0), round(R, 2)))
        inv = np.linalg.inv(M)
        reach = np.abs(inv).sum(axis=1) * R * 1.4
        u0, u1 = int((uv0[0] - reach[0]) * size), int((uv0[0] + reach[0]) * size) + 2
        v0, v1 = int((uv0[1] - reach[1]) * size), int((uv0[1] + reach[1]) * size) + 2
        us, vs = np.meshgrid((np.arange(u0, u1) + 0.5) / size - uv0[0], (np.arange(v0, v1) + 0.5) / size - uv0[1])
        x = M[0, 0] * us + M[0, 1] * vs
        z = M[1, 0] * us + M[1, 1] * vs
        t = np.hypot(x, z) / R                                  # 0 at the centre, 1 at the areola's rim
        hh = np.zeros_like(t)
        cc = np.zeros(t.shape + (3,))
        ss = np.zeros(t.shape + (2,))
        mm = np.zeros_like(t)
        ar = t < 1.0
        hh[ar] = 0.04 * np.clip((1.0 - t[ar]) / 0.12, 0, 1)        # a soft rise over its last eighth
        cc[ar] = AREOLA_TINT
        ss[ar] = SATIN
        nip = t < NIPPLE
        hh[nip] = 0.04 + 0.26 * np.sqrt(np.clip(1 - (t[nip] / NIPPLE) ** 2, 0, 1))
        shade = 0.85 + 0.15 * (1 - t[nip] / NIPPLE)
        cc[nip] = np.array(NIPPLE_TINT)[None, :] * shade[:, None]
        ss[nip] = GLOSS
        seam = (t >= SEAM[0]) & (t < SEAM[1])
        hh[seam] -= 0.03
        cc[seam] = np.array(AREOLA_TINT) * 0.55
        # the rim blends into the body's rubber over a short band, so the disc has no hard edge in colour
        mm[ar] = 1.0
        edge = (t >= 1.0) & (t < 1.08)
        mm[edge] = 1.0 - (t[edge] - 1.0) / 0.08
        cc[edge] = AREOLA_TINT
        ss[edge] = SATIN
        sl = (slice(v0, v1), slice(u0, u1))
        h[sl] = np.where(mm > 0, hh, h[sl])
        col[sl] = np.where(mm[..., None] > 0, cc, col[sl])
        spec[sl] = np.where(mm[..., None] > 0, ss, spec[sl])
        mask[sl] = np.maximum(mask[sl], mm)
    return h, col, spec, mask


# the socket collar's gasket (tools/servitron_collar.py: its rings map down these strips, rim first): rubber at the rim,
# a satin bead with a glossy crest, a dark groove, a satin graphite flange with very fine ribs onto the suit
GASKET = dict(bead=(0.10, 0.50), groove=(0.50, 0.62), bead_tint=(44, 44, 50), groove_tint=(14, 14, 16),
              flange_tint=(32, 32, 37), bead_spec=(210, 185), groove_spec=(40, 30), flange_spec=(125, 95))


def gasket(size, h, col, spec, mask):
    import servitron_collar as sc
    ring_s = [p[0] for p in sc.PROFILE]
    for u0, u1, v0, v1 in sc.STRIPS:
        x0, x1 = int(u0 * size), int(u1 * size) + 1
        y0, y1 = int(v0 * size), int(v1 * size) + 1
        f = (np.arange(y0, y1) + 0.5) / size
        f = np.clip((f - v0) / (v1 - v0), 0, 1) * (len(ring_s) - 1)
        s = np.interp(f, np.arange(len(ring_s)), ring_s)[:, None] * np.ones((1, x1 - x0))
        u = ((np.arange(x0, x1) + 0.5) / size)[None, :] * np.ones((y1 - y0, 1))
        hh = np.zeros_like(s)
        cc = np.zeros(s.shape + (3,))
        ss = np.zeros(s.shape + (2,))
        cc[:] = RUBBER
        ss[:] = RUBBER_SPEC
        b0, b1 = GASKET['bead']
        bead = (s >= b0) & (s < b1)
        crest = np.sin(np.pi * (s - b0) / (b1 - b0))
        cc[bead] = np.array(GASKET['bead_tint'])[None, :] * (0.85 + 0.35 * crest[bead])[:, None]
        ss[bead] = GASKET['bead_spec']
        hh[bead] = 0.05 * crest[bead]
        g0, g1 = GASKET['groove']
        groove = (s >= g0) & (s < g1)
        cc[groove] = GASKET['groove_tint']
        ss[groove] = GASKET['groove_spec']
        hh[groove] = -0.03
        flange = s >= g1
        cc[flange] = GASKET['flange_tint']
        ss[flange] = GASKET['flange_spec']
        hh[flange] = 0.008 * np.sin(u[flange] * 2 * np.pi * 900)      # fine ribs round the socket
        sl = (slice(y0, y1), slice(x0, x1))
        h[sl], col[sl], spec[sl], mask[sl] = hh, cc, ss, 1.0


def mips(img):
    levels = [img]
    while min(levels[-1].size) > 1:
        w, hh = levels[-1].size
        levels.append(levels[-1].resize((max(1, w // 2), max(1, hh // 2)), Image.LANCZOS))
    return levels


def maps(src_dds):
    img = Image.open(io.BytesIO(src_dds))
    img.load()
    rgba = img.convert('RGBA')
    size = rgba.width
    lum = ImageOps.grayscale(rgba)
    mean = sum(i * n for i, n in enumerate(lum.histogram())) / max(1, lum.width * lum.height)
    lut = np.array([max(0.0, min(2.5, 1.0 + SPREAD * (v - mean) / max(1.0, mean))) for v in range(256)], np.float32)
    base = lut[np.asarray(lum)][..., None] * np.array(RUBBER, np.float32)[None, None, :]
    h, col, spec, mask = design(size, lum)
    gasket(size, h, col, spec, mask)
    rgb = mask[..., None] * col + (1 - mask[..., None]) * base          # the rim blends into the rubber
    d_img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), 'RGB')
    d_img.putalpha(rgba.getchannel('A'))
    # normals from the height field: one texel is about 1/size of the uv span; on the body ~ |M| units
    gy, gx = np.gradient(h)
    scale = RELIEF * size / 60.0
    nx, ny = -gx * scale, -gy * scale
    nz = np.ones_like(nx)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    n_rgb = np.stack([(nx / ln + 1) * 127.5, (ny / ln + 1) * 127.5, (nz / ln + 1) * 127.5], axis=-1)
    n_img = Image.fromarray(np.clip(n_rgb, 0, 255).astype(np.uint8), 'RGB')
    s_rg = mask[..., None] * spec + (1 - mask[..., None]) * np.array(RUBBER_SPEC, np.float32)[None, None, :]
    s_img = Image.fromarray(np.clip(np.concatenate([s_rg, np.zeros_like(s_rg[..., :1])], axis=-1), 0, 255).astype(np.uint8), 'RGB')
    return (gt.reencoded(mips(d_img), 'DXT5'), gt.reencoded(mips(n_img), 'BC5'), gt.reencoded(mips(s_img), 'BC5'), size)


def swap_string(blob, old, new):
    """a BGSM's length-prefixed string (u32 length counting the NUL, then the bytes) replaced"""
    o = old.encode('latin1') + b'\0'
    at = blob.find(struct.pack('<I', len(o)) + o)
    if at < 0:
        raise ValueError(f'{old} is not in the material')
    n = new.encode('latin1') + b'\0'
    return blob[:at] + struct.pack('<I', len(n)) + n + blob[at + 4 + len(o):]


def main():
    out = pathlib.Path(sys.argv[1])
    main_ba2 = gamedata.Ba2(ARCHIVES / 'Servitron - Main.ba2')
    tex_ba2 = gamedata.Ba2(ARCHIVES / 'Servitron - Textures.ba2')
    d, n_, s, size = maps(tex_ba2.read(SRC_TEX))
    mat = main_ba2.read(SRC_MAT)
    mat = swap_string(mat, 'Servitron/GITS_plastic_d.dds', OUT_D[len('Textures/'):])
    mat = swap_string(mat, 'Shared/FlatFlat_n.dds', OUT_N[len('Textures/'):])
    mat = swap_string(mat, 'Servitron/flat_r127-g064_s.dds', OUT_S[len('Textures/'):])
    for rel, data in ((OUT_D, d), (OUT_N, n_), (OUT_S, s), (OUT_MAT, mat)):
        (out / rel).parent.mkdir(parents=True, exist_ok=True)
        (out / rel).write_bytes(data)
    print(f'{OUT_MAT} ({len(mat)} bytes, from {SRC_MAT}); maps {size}x{size}: _d DXT5 {len(d)}, _n BC5 {len(n_)}, '
          f'_s BC5 {len(s)} bytes; areolae {AREOLAE}')


if __name__ == '__main__':
    main()
