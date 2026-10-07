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
# the design, in units on the body from the nipple's centre
CAP, GROOVE, PLATE, BEVEL = 0.42, 0.50, 1.15, 1.27
RIVETS, RIVET_AT, RIVET_R = 8, 0.85, 0.09
RELIEF = 2.2                 # normal strength (height units -> slope)


def nipples():
    """[(uv centre, 2x2 matrix uv offset -> surface offset in units)] for each breast"""
    n = nif.Nif(BREAST_MESH)
    s = n.shape('Boobs')
    pos = s.positions()
    out = []
    for side in (-1, 1):
        vs = [i for i, p in enumerate(pos) if p[0] * side > 0.5]
        tip = max(vs, key=lambda i: pos[i][1])
        near = [i for i in vs if math.dist(pos[i], pos[tip]) < 1.6 and i != tip]
        c, uv0 = pos[tip], s.uv(tip)
        # the surface there: x across, z up (the breast faces +y); least squares uv -> (x, z)
        A = np.array([[s.uv(i)[0] - uv0[0], s.uv(i)[1] - uv0[1]] for i in near])
        B = np.array([[pos[i][0] - c[0], pos[i][2] - c[2]] for i in near])
        M, *_ = np.linalg.lstsq(A, B, rcond=None)
        out.append((uv0, M.T))
    return out


def design(size):
    """per texel: (height, colour rgb, spec, gloss, mask) arrays over the whole map, the design drawn at each nipple"""
    h = np.zeros((size, size), np.float32)
    col = np.zeros((size, size, 3), np.float32)
    spec = np.zeros((size, size, 2), np.float32)
    mask = np.zeros((size, size), np.float32)
    for uv0, M in nipples():
        # a texel window around the nipple, big enough for the bevel
        inv = np.linalg.inv(M)
        reach = np.abs(inv).sum(axis=1) * BEVEL * 1.3
        u0, u1 = int((uv0[0] - reach[0]) * size), int((uv0[0] + reach[0]) * size) + 2
        v0, v1 = int((uv0[1] - reach[1]) * size), int((uv0[1] + reach[1]) * size) + 2
        us, vs = np.meshgrid((np.arange(u0, u1) + 0.5) / size - uv0[0], (np.arange(v0, v1) + 0.5) / size - uv0[1])
        x = M[0, 0] * us + M[0, 1] * vs
        z = M[1, 0] * us + M[1, 1] * vs
        d = np.hypot(x, z)
        a = np.arctan2(z, x)
        hh = np.zeros_like(d)
        cc = np.zeros(d.shape + (3,))
        ss = np.zeros(d.shape + (2,))
        mm = np.zeros_like(d)
        brushed = 1.0 + 0.06 * np.sin(a * 90.0) + 0.04 * np.sin(d * 140.0)
        cap = d < CAP
        hh[cap] = 0.35 * np.sqrt(np.clip(1 - (d[cap] / CAP) ** 2, 0, 1)) + 0.06
        cc[cap] = np.array([178, 181, 188])[None, :] * (0.92 + 0.08 * (1 - d[cap] / CAP))[:, None]
        ss[cap] = (255, 230)
        groove = (d >= CAP) & (d < GROOVE)
        hh[groove] = -0.06
        cc[groove] = (38, 38, 42)
        ss[groove] = (60, 40)
        plate = (d >= GROOVE) & (d < PLATE)
        hh[plate] = 0.06
        cc[plate] = np.array([138, 140, 146])[None, :] * brushed[plate][:, None]
        ss[plate] = (205, 175)
        for k in range(RIVETS):
            ang = 2 * math.pi * k / RIVETS
            rd = np.hypot(x - RIVET_AT * math.cos(ang), z - RIVET_AT * math.sin(ang))
            r = rd < RIVET_R
            hh[r] = 0.06 + 0.07 * np.sqrt(np.clip(1 - (rd[r] / RIVET_R) ** 2, 0, 1))
            cc[r] = (196, 198, 204)
            ss[r] = (245, 215)
        bevel = (d >= PLATE) & (d < BEVEL)
        t = (d[bevel] - PLATE) / (BEVEL - PLATE)
        hh[bevel] = 0.06 * (1 - t)
        cc[bevel] = np.array([96, 97, 102])[None, :] * (1 - 0.3 * t)[:, None]
        ss[bevel] = (170, 140)
        mm[d < BEVEL] = 1.0
        sl = (slice(v0, v1), slice(u0, u1))
        h[sl] = np.where(mm > 0, hh, h[sl])
        col[sl] = np.where(mm[..., None] > 0, cc, col[sl])
        spec[sl] = np.where(mm[..., None] > 0, ss, spec[sl])
        mask[sl] = np.maximum(mask[sl], mm)
    return h, col, spec, mask


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
    h, col, spec, mask = design(size)
    rgb = np.where(mask[..., None] > 0, col, base)
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
    s_rg = np.where(mask[..., None] > 0, spec, np.array(RUBBER_SPEC, np.float32)[None, None, :])
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
          f'_s BC5 {len(s)} bytes; areolae at {[tuple(round(x, 4) for x in uv) for uv, _ in nipples()]}')


if __name__ == '__main__':
    main()
