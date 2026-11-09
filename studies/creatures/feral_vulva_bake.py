"""Per feral variant: the vulva patch's own texture (512) baked from the body texture under it, so the rim matches the
skin exactly, then the slit and inner labia darkened to wet, purple-red flesh; plus its BGSM (the variant's body BGSM
with its textures retargeted).
Reads D:\\F4Output\\creatures\\feral\\report.json (feral_build.py 'vulva.bake': own UV, body UV per vertex, polygons).
    python -I feral_vulva_bake.py"""
import json
import pathlib
import re
import struct
import sys

import numpy as np
from scipy import ndimage

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import gamedata  # noqa: E402
import ghoul_common as gc  # noqa: E402

ROOT = pathlib.Path(r'D:\F4Output\creatures\feral')
OUT = ROOT / 'out' / 'Data'
DATA = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data')
N = 512
HALF_W = 1.9                                                     # feral_build.vulva_patch half width (game units)
MATS = gamedata.Ba2(DATA / 'Fallout4 - Materials.ba2')
TEXS = [gamedata.Ba2(p) for p in sorted(DATA.glob('Fallout4 - Textures*.ba2'))]


def strings(b):
    return [m.group(0).rstrip(b'\0').decode('latin1') for m in re.finditer(rb'[ -~]{5,}\0', b)]


def read_bgsm(name):
    rel = name.lower().replace('\\', '/')
    rel = rel if rel.startswith('materials/') else 'materials/' + rel
    loose = DATA / rel
    if loose.exists():
        return loose.read_bytes()
    if rel in MATS:
        return MATS.read(rel)
    raise SystemExit(f'BGSM not found: {name}')


def texture(path, work):
    rel = path.lower().replace('\\', '/')
    rel = rel if rel.startswith('textures/') else 'textures/' + rel
    loose = DATA / rel
    if not loose.exists():
        for a in TEXS:
            if rel in a:
                work.mkdir(parents=True, exist_ok=True)
                loose = work / pathlib.Path(rel).name
                loose.write_bytes(a.read(rel))
                break
        else:
            raise SystemExit(f'texture not found: {path}')
    return gc.dds_to_array(loose, work / 'tga').astype(np.float32) / 255.0


def raster(own, body_uv, polys):
    """For each texel of the own layout: the body UV it shows (H,W,2) and coverage."""
    buv = np.zeros((N, N, 2), np.float32)
    cov = np.zeros((N, N), bool)
    own = np.array(own, np.float64)
    body = np.array([b if b is not None else (0.0, 0.0) for b in body_uv], np.float64)   # loose verts: no face
    for poly in polys:
        for a, b, c in ((poly[0], poly[i], poly[i + 1]) for i in range(1, len(poly) - 1)):
            P = own[[a, b, c]] * (N - 1)
            x0, y0 = np.floor(P.min(0)).astype(int)
            x1, y1 = np.ceil(P.max(0)).astype(int)
            gx, gy = np.meshgrid(np.arange(max(x0, 0), min(x1, N - 1) + 1), np.arange(max(y0, 0), min(y1, N - 1) + 1))
            den = (P[1, 1] - P[2, 1]) * (P[0, 0] - P[2, 0]) + (P[2, 0] - P[1, 0]) * (P[0, 1] - P[2, 1])
            if abs(den) < 1e-12:
                continue
            l1 = ((P[1, 1] - P[2, 1]) * (gx - P[2, 0]) + (P[2, 0] - P[1, 0]) * (gy - P[2, 1])) / den
            l2 = ((P[2, 1] - P[0, 1]) * (gx - P[2, 0]) + (P[0, 0] - P[2, 0]) * (gy - P[2, 1])) / den
            l3 = 1 - l1 - l2
            ins = (l1 >= -1e-3) & (l2 >= -1e-3) & (l3 >= -1e-3)
            yy, xx = gy[ins], gx[ins]
            buv[yy, xx] = (l1[ins, None] * body[a] + l2[ins, None] * body[b] + l3[ins, None] * body[c])
            cov[yy, xx] = True
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    return buv[iy, ix], cov


def sample(img, uv):
    h, w = img.shape[:2]
    x = np.clip(uv[..., 0] * w - 0.5, 0, w - 1)
    y = np.clip(uv[..., 1] * h - 0.5, 0, h - 1)
    return np.stack([ndimage.map_coordinates(img[..., c], [y, x], order=1) for c in range(img.shape[2])], -1)


def bgsm_retarget(src, mapping):
    out, o = bytearray(), 0
    for m in re.finditer(rb'[ -~]{5,}\0', src):
        s = m.group(0).rstrip(b'\0').decode('latin1')
        key = s.lower().replace('/', '\\').removeprefix('textures\\')
        if key in mapping and m.start() >= 4 and struct.unpack_from('<I', src, m.start() - 4)[0] == len(m.group(0)):
            new = mapping[key].encode() + b'\0'
            out += src[o:m.start() - 4] + struct.pack('<I', len(new)) + new
            o = m.end()
    out += src[o:]
    return bytes(out)


def main():
    rep = json.loads((ROOT / 'report.json').read_text())
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32) / (N - 1)
    x = (xx - 0.5) * 2 * HALF_W                                   # game units across
    s = yy                                                         # 0 perineum -> 1 pubis
    env = np.clip(np.sin(np.pi * np.clip((s - 0.12) / 0.78, 0, 1)), 0, 1) ** 0.7
    slit = np.exp(-(x / 0.12) ** 2) * env
    inner = np.exp(-((np.abs(x) - 0.30) / 0.18) ** 2) * env
    p3 = np.stack([xx.ravel() * 9, yy.ravel() * 9, np.zeros(N * N, np.float32)], -1)
    wr = gc.fbm(p3, 3, 77).reshape(N, N)                         # wrinkles
    for dst, info in rep.items():
        v = info.get('vulva')
        if not isinstance(v, dict) or 'bake' not in v:
            continue
        variant = pathlib.Path(dst).stem.removesuffix('_F')
        work = ROOT / 'work_vulva' / variant
        bgsm = read_bgsm(v['body_bgsm'])
        tex = [t for t in strings(bgsm) if t.lower().endswith('.dds')]
        d_path = next(t for t in tex if '_d.' in t.lower())
        n_path = next((t for t in tex if '_n.' in t.lower()), None)
        s_path = next((t for t in tex if '_s.' in t.lower()), None)
        buv, cov = raster(v['bake']['own'], v['bake']['body_uv'], v['bake']['polys'])
        D = sample(texture(d_path, work), buv)[..., :3]
        S = sample(texture(s_path, work), buv) if s_path else np.zeros((N, N, 4), np.float32)
        # colour: the skin as it is, darkening into dusky inner labia and a wet, purple-red slit
        col = D * (1 - 0.35 * inner[..., None]) + np.array([0.34, 0.16, 0.17]) * 0.35 * inner[..., None]
        col = col * (1 - 0.75 * slit[..., None]) + np.array([0.20, 0.05, 0.07]) * 0.75 * slit[..., None]
        d = np.concatenate([(np.clip(col, 0, 1) * 255 + 0.5).astype(np.uint8), np.full((N, N, 1), 255, np.uint8)], -1)
        # normal (DirectX green): folds of the labia + fine wrinkles, in the patch's own layout
        h = 0.5 * np.exp(-((np.abs(x) - 0.72) / 0.40) ** 2) * env - 0.6 * slit + 0.04 * wr
        sx = 1.0 / (2 * HALF_W / N)
        sy = 1.0 / (1.0 / N * 6.0)
        gxh = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5 * sx * 0.08
        gyh = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5 * sy * 0.08
        nrm = np.stack([-gxh, -gyh, np.ones_like(h)], -1)
        nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
        nn = np.zeros((N, N, 4), np.uint8)
        nn[..., 0] = (nrm[..., 0] * 127.5 + 127.5).astype(np.uint8)
        nn[..., 1] = (nrm[..., 1] * 127.5 + 127.5).astype(np.uint8)
        nn[..., 3] = 255
        ss = np.zeros((N, N, 4), np.uint8)
        ss[..., 0] = (np.clip(S[..., 0] + (0.50 - S[..., 0]) * np.maximum(slit, 0.5 * inner), 0, 1) * 255).astype(np.uint8)
        ss[..., 1] = (np.clip(S[..., 1] + (0.80 - S[..., 1]) * np.maximum(slit, 0.5 * inner), 0, 1) * 255).astype(np.uint8)
        ss[..., 3] = 255
        base = OUT / 'textures/anatomy/creatures'
        for arr, kind, fmt in ((d, 'd', 'BC1_UNORM'), (nn, 'n', 'BC5_UNORM'), (ss, 's', 'BC5_UNORM')):
            gc.array_to_dds(arr, fmt, base / f'FeralVulva_{variant}_{kind}.dds', work / 'enc')
        mapping = {p.lower().replace('/', '\\').removeprefix('textures\\'): f'Anatomy\\Creatures\\FeralVulva_{variant}_{k}.dds'
                   for p, k in ((d_path, 'd'), (n_path, 'n'), (s_path, 's')) if p}
        new = bgsm_retarget(bgsm, mapping)
        mdst = OUT / f'materials/anatomy/creatures/FeralVulva_{variant}.bgsm'
        mdst.parent.mkdir(parents=True, exist_ok=True)
        mdst.write_bytes(new)
        print(f'{variant}: body {v["body_bgsm"]} -> d {d_path}; coverage {cov.mean() * 100:.0f}%; bgsm textures '
              f'{[t for t in strings(new) if t.lower().endswith(".dds")][:3]}')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    main()
