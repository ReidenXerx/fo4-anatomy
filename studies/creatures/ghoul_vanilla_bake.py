"""Vanilla-only base textures for the ghoul skin (Dudu 11-09: no CBBE HeadRear Absolute Fix / CBBE / BodyTalk texels).
For each mesh we paint whose UV layout is not vanilla's, the VANILLA ghoul texture is baked onto that mesh's UVs in
3D: every texel's surface point -> nearest point on the vanilla mesh -> its UV -> vanilla colour / specular; normals
go tangent(vanilla) -> object -> tangent(ours) through each triangle's frame. Texels our mesh does not cover keep the
vanilla texture (the rear-head islands on the body sheets are vanilla UVs). Output: uncompressed DDS at the size the
old source had, in D:\\F4Output\\ghoulskin\\src\\vanilla_baked\\textures\\actors\\character\\..., which ghoul_build.py
then uses as its source.  python -I ghoul_vanilla_bake.py [name]"""
import pathlib
import struct
import sys
import time

import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import gamedata  # noqa: E402
import ghoul_common as gc  # noqa: E402
import nif  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
SRC = gc.ROOT / 'src'
V2 = SRC / 'Fallout4 - Textures2' / 'textures/actors/character'
V3 = SRC / 'Fallout4 - Textures3' / 'textures/actors/character'
HR = SRC / 'loose_CBBE HeadRear Absolute Fix' / 'textures/actors/character'
CB = SRC / "loose_Caliente's Beautiful Bodies Enhancer" / 'textures/actors/character'
BT = SRC / 'loose_BodyTalk' / 'textures/actors/character'
OUT = SRC / 'vanilla_baked' / 'textures/actors/character'
VMESH = gc.ROOT / 'vanilla_mesh'
WORK = gc.ROOT / 'work' / 'bake'
CA = 'meshes\\actors\\character\\characterassets\\'
JOBS = [  # name, our mesh, shape, vanilla mesh, vanilla maps, size-from (old source), output stem
    ('F body', 'femalebody.nif', 'CBBE', 'femalebody.nif',
     {'d': V2 / 'ghoulfemale/ghoulfemalebody_d.dds', 'n': V2 / 'ghoulfemale/ghoulfemalebody_n.dds',
      's': V3 / 'ghoulfemale/ghoulfemalebody_s.dds'}, HR / 'custombody/ghoulfemalebody_{}.dds',
     'custombody/ghoulfemalebody'),
    ('F hands', 'femalehands.nif', None, 'femalehands.nif',
     {'d': V3 / 'ghoulfemale/ghoulfemalehands_d.dds', 'n': V3 / 'ghoulfemale/ghoulfemalehands_n.dds',
      's': V3 / 'ghoulfemale/ghoulfemalehands_s.dds'}, CB / 'ghoulfemale/ghoulfemalehands_{}.dds',
     'ghoulfemale/ghoulfemalehands'),
    ('M body', 'malebody.nif', None, 'malebody.nif',
     {'d': V2 / 'ghoulmale/ghoulmalebody_d.dds', 'n': V2 / 'ghoulmale/ghoulmalebody_n.dds',
      's': V2 / 'ghoulmale/ghoulmalebody_s.dds'}, BT / 'ghoulmale/ghoulmalebody_{}.dds',
     'ghoulmale/ghoulmalebody'),
]


def dds_size(p):
    b = pathlib.Path(p).read_bytes()[:20]
    return struct.unpack_from('<I', b, 16)[0], struct.unpack_from('<I', b, 12)[0]      # w, h


def mesh(path, shape=None):
    m = nif.Nif(path)
    s = max(m.shapes(), key=lambda x: x.count) if shape is None else next(x for x in m.shapes() if x.name == shape)
    P = np.array(s.positions(), np.float64)
    U = np.array([s.uv(i) for i in range(s.count)], np.float64)
    T = np.array(s.triangles(), np.int64)
    return P, U, T, s.name


def frames(P, U, T):
    """per triangle: T, B (dP/du, dP/dv, orthonormalised against N, handedness kept), N (winding)"""
    p0, p1, p2 = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]
    u0, u1, u2 = U[T[:, 0]], U[T[:, 1]], U[T[:, 2]]
    e1, e2 = p1 - p0, p2 - p0
    d1, d2 = u1 - u0, u2 - u0
    N = np.cross(e1, e2)
    N /= np.maximum(np.linalg.norm(N, axis=1), 1e-12)[:, None]
    det = d1[:, 0] * d2[:, 1] - d2[:, 0] * d1[:, 1]
    det = np.where(np.abs(det) < 1e-12, 1e-12, det)
    Tg = (e1 * d2[:, 1:2] - e2 * d1[:, 1:2]) / det[:, None]
    Bg = (e2 * d1[:, 0:1] - e1 * d2[:, 0:1]) / det[:, None]
    Tg -= (Tg * N).sum(1)[:, None] * N
    Tg /= np.maximum(np.linalg.norm(Tg, axis=1), 1e-12)[:, None]
    hand = np.sign((np.cross(N, Tg) * Bg).sum(1))
    hand[hand == 0] = 1
    Bn = np.cross(N, Tg) * hand[:, None]
    return Tg, Bn, N


def raster_ids(size, U, T):
    """texel -> (triangle, barycentrics); -1 where uncovered"""
    w, h = size
    tid = np.full((h, w), -1, np.int64)
    bar = np.zeros((h, w, 3), np.float32)
    px, py = U[:, 0] * w - 0.5, U[:, 1] * h - 0.5
    for k, (a, b, c) in enumerate(T):
        xa, xb, xc, ya, yb, yc = px[a], px[b], px[c], py[a], py[b], py[c]
        x0, x1 = max(int(np.floor(min(xa, xb, xc))), 0), min(int(np.ceil(max(xa, xb, xc))), w - 1)
        y0, y1 = max(int(np.floor(min(ya, yb, yc))), 0), min(int(np.ceil(max(ya, yb, yc))), h - 1)
        if x1 < x0 or y1 < y0:
            continue
        den = (yb - yc) * (xa - xc) + (xc - xb) * (ya - yc)
        if abs(den) < 1e-12:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        l1 = ((yb - yc) * (gx - xc) + (xc - xb) * (gy - yc)) / den
        l2 = ((yc - ya) * (gx - xc) + (xa - xc) * (gy - yc)) / den
        l3 = 1 - l1 - l2
        ins = (l1 >= -1e-4) & (l2 >= -1e-4) & (l3 >= -1e-4)
        tid[gy[ins], gx[ins]] = k
        bar[gy[ins], gx[ins]] = np.stack([l1[ins], l2[ins], l3[ins]], -1)
    return tid, bar


def sample(img, uv):
    """bilinear, uv in [0,1] (nif convention: v = row / height), img (H,W,C) float"""
    h, w = img.shape[:2]
    x = np.clip(uv[:, 0] * w - 0.5, 0, w - 1.001)
    y = np.clip(uv[:, 1] * h - 0.5, 0, h - 1.001)
    x0, y0 = np.floor(x).astype(np.int64), np.floor(y).astype(np.int64)
    fx, fy = (x - x0)[:, None], (y - y0)[:, None]
    return (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x0 + 1] * fx * (1 - fy)
            + img[y0 + 1, x0] * (1 - fx) * fy + img[y0 + 1, x0 + 1] * fx * fy)


def resize(img, size):
    from PIL import Image
    w, h = size
    if img.shape[1] == w and img.shape[0] == h:
        return img.astype(np.float32)
    ch = [np.asarray(Image.fromarray(img[..., c].astype(np.float32), 'F').resize((w, h), Image.BILINEAR))
          for c in range(img.shape[2])]
    return np.stack(ch, -1)


def bake(job):
    name, ours_n, shape, van_n, vmaps, size_from, stem = job
    t0 = time.time()
    P, U, T, sname = mesh(gc.MESH / ours_n, shape)
    Q, UQ, TQ, vname = mesh(VMESH / van_n)
    Tt, Bt, Nt = frames(P, U, T)
    Tv, Bv, Nv = frames(Q, UQ, TQ)
    # dense samples of the vanilla surface: (point, triangle, barycentrics)
    n = 10
    bs = np.array([(i / n, j / n, 1 - i / n - j / n) for i in range(n + 1) for j in range(n + 1 - i)])
    pts = (bs[None, :, 0, None] * Q[TQ[:, 0]][:, None] + bs[None, :, 1, None] * Q[TQ[:, 1]][:, None]
           + bs[None, :, 2, None] * Q[TQ[:, 2]][:, None]).reshape(-1, 3)
    pt_tri = np.repeat(np.arange(len(TQ)), len(bs))
    pt_bar = np.tile(bs, (len(TQ), 1))
    tree = cKDTree(pts)
    van = {k: gc.dds_to_array(p, WORK / 'dec').astype(np.float32) / 255.0 for k, p in vmaps.items()}
    for k in vmaps:
        size = dds_size(str(size_from).format(k))
        tid, bar = raster_ids(size, U, T)
        cov = tid >= 0
        ys, xs = np.nonzero(cov)
        tk, bk = tid[ys, xs], bar[ys, xs]
        p = (bk[:, 0, None] * P[T[tk, 0]] + bk[:, 1, None] * P[T[tk, 1]] + bk[:, 2, None] * P[T[tk, 2]])
        dist, j = tree.query(p)
        vt, vb = pt_tri[j], pt_bar[j]
        uv = (vb[:, 0, None] * UQ[TQ[vt, 0]] + vb[:, 1, None] * UQ[TQ[vt, 1]] + vb[:, 2, None] * UQ[TQ[vt, 2]])
        out = resize(van[k], size)                                   # uncovered texels: vanilla as is
        s = sample(van[k], uv)
        if k == 'n':
            x, y = s[:, 0] * 2 - 1, s[:, 1] * 2 - 1
            z = np.sqrt(np.clip(1 - x * x - y * y, 0, 1))
            o = x[:, None] * Tv[vt] + y[:, None] * Bv[vt] + z[:, None] * Nv[vt]
            nx, ny, nz = (o * Tt[tk]).sum(1), (o * Bt[tk]).sum(1), (o * Nt[tk]).sum(1)
            ln = np.maximum(np.sqrt(nx * nx + ny * ny + nz * nz), 1e-6)
            s = s.copy()
            s[:, 0], s[:, 1] = (nx / ln + 1) / 2, (ny / ln + 1) / 2
            if s.shape[1] > 2:
                s[:, 2] = (np.clip(nz / ln, 0, 1) + 1) / 2 if False else np.clip(nz / ln, 0, 1) * 0.5 + 0.5
        out[ys, xs] = s
        # gutters round our islands: nearest covered texel (mips must not bleed vanilla's other layout in)
        ring = ndimage.binary_dilation(cov, iterations=8) & ~cov
        _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
        out[ring] = out[iy[ring], ix[ring]]
        arr = (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)
        if arr.shape[2] == 3:
            arr = np.concatenate([arr, np.full(arr.shape[:2] + (1,), 255, np.uint8)], -1)
        dst = OUT / f'{stem}_{k}.dds'
        gc.array_to_dds(arr, 'R8G8B8A8_UNORM', dst, WORK)
        print(f'{name} {k}: {size[0]}x{size[1]}, ours {sname} {len(P)}v on vanilla {vname} {len(Q)}v, covered '
              f'{cov.mean():.0%}, nearest dist median {np.median(dist):.2f} p95 {np.percentile(dist, 95):.2f} '
              f'({time.time() - t0:.0f}s)', flush=True)


if __name__ == '__main__':
    VMESH.mkdir(parents=True, exist_ok=True)
    b = gamedata.Ba2(pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data\Fallout4 - Meshes.ba2'))
    for n in ('femalebody.nif', 'femalehands.nif', 'malebody.nif'):
        (VMESH / n).write_bytes(b.read(CA + n))
    for job in JOBS:
        if len(sys.argv) > 1 and job[0] != sys.argv[1]:
            continue
        bake(job)
