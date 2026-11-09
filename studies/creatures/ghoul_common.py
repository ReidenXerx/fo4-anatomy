"""Shared bits for the ghoul skin job: meshes into one space, UV rasterising to per-texel 3D positions, DDS <-> array
through texconv, 3D noise (gradient fBm, ridged, cellular)."""
import pathlib
import subprocess
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif  # noqa: E402

TEXCONV = r'D:\F4Tools\texconv\texconv.exe'
ROOT = pathlib.Path(r'D:\F4Output\ghoulskin')
MESH = ROOT / 'mesh'


# ---------------------------------------------------------------- meshes
def load_shape(nif_name, shape_name=None):
    m = nif.Nif(MESH / nif_name)
    shapes = m.shapes()
    s = shapes[0] if shape_name is None else next(x for x in shapes if x.name == shape_name)
    pos = np.array(s.positions(), dtype=np.float64)
    uv = np.array([s.uv(i) for i in range(s.count)], dtype=np.float64)
    tri = np.array(s.triangles(), dtype=np.int64)
    bones, xfs = m.skin(s)
    skin = {b.lower(): (np.array(r, dtype=np.float64).reshape(3, 3), np.array(t, dtype=np.float64), sc)
            for b, (r, t, sc) in zip(bones, xfs) if b}
    return dict(name=f'{nif_name}:{s.name}', pos=pos, uv=uv, tri=tri, skin=skin)


def to_bone(skin_entry, p):
    r, t, s = skin_entry
    return s * p @ r.T + t


def from_bone(skin_entry, p):
    r, t, s = skin_entry
    return ((p - t) / s) @ r


def into(shape, ref, bone):
    """shape's vertices expressed in ref's skin space through a bone both are bound to."""
    return from_bone(ref['skin'][bone], to_bone(shape['skin'][bone], shape['pos']))


def openings(shape):
    """Vertex indices on open boundary edges (after welding by position)."""
    key = {}
    weld = np.empty(len(shape['pos']), dtype=np.int64)
    for i, p in enumerate(np.round(shape['pos'], 3)):
        weld[i] = key.setdefault(tuple(p), len(key))
    edges = {}
    for a, b, c in weld[shape['tri']]:
        for e in ((a, b), (b, c), (c, a)):
            k = (min(e), max(e))
            edges[k] = edges.get(k, 0) + 1
    ring = {v for e, n in edges.items() if n == 1 for v in e}
    first = {}
    for i, w in enumerate(weld):
        first.setdefault(w, i)
    return np.array(sorted(first[w] for w in ring), dtype=np.int64)


# ---------------------------------------------------------------- rasterising
def rasterize(size, layers):
    """layers: [(uv (n,2), tri (m,3), world pos (n,3), tag)]. Returns pos (H,W,3) float32, tag (H,W) int8 (-1 = none),
    and how many texels a later layer overwrote."""
    h = w = size
    pos = np.zeros((h, w, 3), np.float32)
    tag = np.full((h, w), -1, np.int8)
    clash = 0
    for uv, tri, world, t in layers:
        px = uv[:, 0] * w - 0.5
        py = uv[:, 1] * h - 0.5
        for a, b, c in tri:
            xa, xb, xc = px[a], px[b], px[c]
            ya, yb, yc = py[a], py[b], py[c]
            x0, x1 = int(np.floor(min(xa, xb, xc))), int(np.ceil(max(xa, xb, xc)))
            y0, y1 = int(np.floor(min(ya, yb, yc))), int(np.ceil(max(ya, yb, yc)))
            x0, y0 = max(x0, 0), max(y0, 0)
            x1, y1 = min(x1, w - 1), min(y1, h - 1)
            if x1 < x0 or y1 < y0:
                continue
            den = (yb - yc) * (xa - xc) + (xc - xb) * (ya - yc)
            if abs(den) < 1e-12:
                continue
            gx, gy = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
            l1 = ((yb - yc) * (gx - xc) + (xc - xb) * (gy - yc)) / den
            l2 = ((yc - ya) * (gx - xc) + (xa - xc) * (gy - yc)) / den
            l3 = 1 - l1 - l2
            inside = (l1 >= -1e-4) & (l2 >= -1e-4) & (l3 >= -1e-4)
            if not inside.any():
                continue
            yy, xx = gy[inside], gx[inside]
            p = l1[inside, None] * world[a] + l2[inside, None] * world[b] + l3[inside, None] * world[c]
            clash += int(((tag[yy, xx] >= 0) & (tag[yy, xx] != t)).sum())
            pos[yy, xx] = p
            tag[yy, xx] = t
    return pos, tag, clash


def fill_gutters(pos, tag):
    """Every uncovered texel takes its nearest covered texel's position, so detail runs into the gutters and the
    mips do not bleed the old texture in."""
    from scipy import ndimage
    _, (iy, ix) = ndimage.distance_transform_edt(tag < 0, return_indices=True)
    return pos[iy, ix]


# ---------------------------------------------------------------- DDS io
def dds_to_array(path, work):
    work = pathlib.Path(work)
    work.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([TEXCONV, '-nologo', '-ft', 'tga', '-f', 'R8G8B8A8_UNORM', '-m', '1', '-y', '-o', str(work),
                        str(path)], capture_output=True, text=True)
    out = work / (pathlib.Path(path).stem + '.tga')
    if r.returncode or not out.exists():
        raise SystemExit(f'texconv decode failed {path}: {r.stdout[-400:]}')
    return np.asarray(Image.open(out).convert('RGBA'), dtype=np.uint8)


def array_to_dds(arr, fmt, dst, work):
    """arr uint8 (H,W,4) -> dst DDS in fmt with full mips."""
    work = pathlib.Path(work)
    work.mkdir(parents=True, exist_ok=True)
    dst = pathlib.Path(dst)
    tmp = work / (dst.stem + '.tga')
    Image.fromarray(arr, 'RGBA').save(tmp)
    args = [TEXCONV, '-nologo', '-f', fmt, '-m', '0', '-y', '-o', str(work), str(tmp)]
    r = subprocess.run(args, capture_output=True, text=True)
    out = work / (dst.stem + '.dds')
    if r.returncode or not out.exists():
        raise SystemExit(f'texconv encode failed {dst}: {r.stdout[-400:]}')
    dst.parent.mkdir(parents=True, exist_ok=True)
    out.replace(dst)
    return dst


# ---------------------------------------------------------------- noise
def _hash3(ix, iy, iz, seed):
    h = (ix.astype(np.int64) * 73856093) ^ (iy.astype(np.int64) * 19349663) ^ (iz.astype(np.int64) * 83492791) ^ \
        (seed * 2654435761)
    h = (h ^ (h >> 13)) * 1274126177
    h = h ^ (h >> 16)
    return h & 0x7FFFFFFF


_GRAD = np.array([[1, 1, 0], [-1, 1, 0], [1, -1, 0], [-1, -1, 0], [1, 0, 1], [-1, 0, 1], [1, 0, -1], [-1, 0, -1],
                  [0, 1, 1], [0, -1, 1], [0, 1, -1], [0, -1, -1], [1, 1, 0], [-1, 1, 0], [0, -1, 1], [0, -1, -1]],
                 np.float32)


def perlin(p, seed=0):
    """3D gradient noise in about [-1, 1]; p (n,3) float32."""
    pi = np.floor(p).astype(np.int64)
    f = (p - pi).astype(np.float32)
    u = f * f * f * (f * (f * 6 - 15) + 10)
    out = np.zeros(len(p), np.float32)
    for dx in (0, 1):
        wx = u[:, 0] if dx else 1 - u[:, 0]
        for dy in (0, 1):
            wy = u[:, 1] if dy else 1 - u[:, 1]
            for dz in (0, 1):
                wz = u[:, 2] if dz else 1 - u[:, 2]
                g = _GRAD[_hash3(pi[:, 0] + dx, pi[:, 1] + dy, pi[:, 2] + dz, seed) & 15]
                d = (f[:, 0] - dx) * g[:, 0] + (f[:, 1] - dy) * g[:, 1] + (f[:, 2] - dz) * g[:, 2]
                out += wx * wy * wz * d
    return out


def fbm(p, octaves, seed=0, lac=2.0, gain=0.5):
    out = np.zeros(len(p), np.float32)
    amp, norm, q = 1.0, 0.0, p.astype(np.float32)
    for o in range(octaves):
        out += amp * perlin(q, seed + o * 101)
        norm += amp
        amp *= gain
        q = q * lac + np.float32(17.17)
    return out / norm


def ridged(p, octaves, seed=0):
    out = np.zeros(len(p), np.float32)
    amp, norm, q = 1.0, 0.0, p.astype(np.float32)
    for o in range(octaves):
        out += amp * (1 - np.abs(perlin(q, seed + o * 131)))
        norm += amp
        amp *= 0.5
        q = q * 2.03 + np.float32(5.3)
    return out / norm


def cellular(p, seed=0, jitter=0.9):
    """F1, F2 distances and the nearest cell's id-hash (0..1) for jittered-grid Worley noise."""
    pi = np.floor(p).astype(np.int64)
    f1 = np.full(len(p), 9.0, np.float32)
    f2 = np.full(len(p), 9.0, np.float32)
    cid = np.zeros(len(p), np.float32)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                cx, cy, cz = pi[:, 0] + dx, pi[:, 1] + dy, pi[:, 2] + dz
                h = _hash3(cx, cy, cz, seed)
                jx = ((h & 1023) / 1023.0 - 0.5) * jitter + 0.5
                jy = (((h >> 10) & 1023) / 1023.0 - 0.5) * jitter + 0.5
                jz = (((h >> 20) & 1023) / 1023.0 - 0.5) * jitter + 0.5
                d = np.sqrt((cx + jx - p[:, 0]) ** 2 + (cy + jy - p[:, 1]) ** 2 + (cz + jz - p[:, 2]) ** 2) \
                    .astype(np.float32)
                closer = d < f1
                f2 = np.where(closer, f1, np.minimum(f2, d))
                cid = np.where(closer, ((h >> 7) & 4095) / 4095.0, cid).astype(np.float32)
                f1 = np.where(closer, d, f1)
    return f1, f2, cid


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)
