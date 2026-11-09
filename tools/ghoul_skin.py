"""Rotten ghoul skin, made on the player's PC from the ghoul textures THEY have installed (owner + alasdairn
2026-11-09, option 1: nothing third-party ships with us; CBBE / HeadRear Fix / BodyTalk ghoul textures are read, never
copied). numpy + Pillow only (the builder ships no scipy and no texconv).

Method (approved on Ivy, 11-09): every texel of a ghoul skin map is rasterised to its 3D point on the mesh that wears
it, all meshes brought into the BODY's skin space through shared bones (hands via LArm_Hand, head via Chest, rear head
via HEAD then Chest), so head, rear head, body and hands sample ONE 3D procedural field: necrotic bruising, jaundice,
sloughed raw flesh with crusted edges, weeping sores, pustules, veins, fissures. Seams agree by construction. The
detail fades to nothing at the face's edge (NPC faces are baked FaceGen made from the old head texture).

    build(job, shapes, read, size_cap) -> {kind: DDS bytes}
"""
import io
import time

import numpy as np
from PIL import Image

import genital_texture as gt
import nif

FADE_IN, FADE_OUT = 0.8, 5.0          # game units from the face edge: untouched inside FADE_IN, full detail past FADE_OUT
FIELD_MAX = 1024                      # the procedural field's own resolution cap (maps can be larger)
LW = np.array([0.3, 0.55, 0.15], np.float32)


# ---------------------------------------------------------------- meshes in the body's skin space
def load_shape(path, shape_name=None):
    m = nif.Nif(path)
    shapes = m.shapes()
    s = max(shapes, key=lambda x: x.count) if shape_name is None else next(x for x in shapes if x.name == shape_name)
    bones, xfs = m.skin(s)
    return dict(name=f'{path}:{s.name}', pos=np.array(s.positions(), np.float64),
                uv=np.array([s.uv(i) for i in range(s.count)], np.float64),
                tri=np.array(s.triangles(), np.int64),
                skin={b.lower(): (np.array(r, np.float64).reshape(3, 3), np.array(t, np.float64), sc)
                      for b, (r, t, sc) in zip(bones, xfs) if b})


def to_bone(e, p):
    r, t, s = e
    return s * p @ r.T + t


def from_bone(e, p):
    r, t, s = e
    return ((p - t) / s) @ r


def into(shape, ref, bone):
    return from_bone(ref['skin'][bone], to_bone(shape['skin'][bone], shape['pos']))


def openings(shape):
    """first vertex index of every welded vertex on an open boundary edge"""
    key, weld = {}, np.empty(len(shape['pos']), np.int64)
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
    return np.array(sorted(first[w] for w in ring), np.int64)


def nearest_dist(q, pts, chunk=4096):
    """distance from each q to its nearest pt (brute force, chunked: pts are a few hundred to a few thousand)"""
    out = np.empty(len(q), np.float64)
    for s in range(0, len(q), chunk):
        d = ((q[s:s + chunk, None, :] - pts[None, :, :]) ** 2).sum(-1)
        out[s:s + chunk] = np.sqrt(d.min(1))
    return out


def body_space(sex, meshes):
    """meshes: {'body','hands','head','rear'[, 'genitals']: shape dict}. Adds 'world' (body skin space) and each
    vertex's distance to the face edge ('edge'); returns the dict."""
    body = meshes['body']
    for key, sh in meshes.items():
        if key in ('body', 'genitals'):
            sh['world'] = sh['pos']
        elif key == 'hands':
            sh['world'] = into(sh, body, 'larm_hand')
        elif key == 'head':
            sh['world'] = into(sh, body, 'chest')
        else:
            head = meshes['head']
            p = from_bone(head['skin']['head'], to_bone(sh['skin']['head'], sh['pos']))
            sh['world'] = from_bone(body['skin']['chest'], to_bone(head['skin']['chest'], p))
    head = meshes['head']
    ring = head['world'][openings(head)]
    near = np.vstack([meshes['body']['world'], meshes['rear']['world']])
    edge = ring[nearest_dist(ring, near) < 0.05]
    if len(edge) < 8:
        raise SystemExit(f'{sex}: the face edge was not found where head meets body ({len(edge)} points)')
    for sh in meshes.values():
        sh['edge'] = nearest_dist(sh['world'], edge)
    return meshes


# ---------------------------------------------------------------- texels -> 3D
def rasterize(size, layers):
    """layers [(uv, tri, attrs (n,k))] -> attrs per texel (size,size,k) float32 and coverage (bool)"""
    k = layers[0][2].shape[1]
    out = np.zeros((size, size, k), np.float32)
    cov = np.zeros((size, size), bool)
    for uv, tri, att in layers:
        px, py = uv[:, 0] * size - 0.5, uv[:, 1] * size - 0.5
        for a, b, c in tri:
            xa, xb, xc, ya, yb, yc = px[a], px[b], px[c], py[a], py[b], py[c]
            x0, x1 = max(int(np.floor(min(xa, xb, xc))), 0), min(int(np.ceil(max(xa, xb, xc))), size - 1)
            y0, y1 = max(int(np.floor(min(ya, yb, yc))), 0), min(int(np.ceil(max(ya, yb, yc))), size - 1)
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
            if ins.any():
                yy, xx = gy[ins], gx[ins]
                out[yy, xx] = l1[ins, None] * att[a] + l2[ins, None] * att[b] + l3[ins, None] * att[c]
                cov[yy, xx] = True
    return out, cov


def _shift_fill(val, have):
    """one step: every empty texel next to a filled one takes the mean of its filled 4-neighbours"""
    acc = np.zeros_like(val)
    n = np.zeros(have.shape, np.float32)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        hv = np.roll(np.roll(have, dy, 0), dx, 1)
        acc += np.roll(np.roll(val, dy, 0), dx, 1) * hv[..., None]
        n += hv
    new = (~have) & (n > 0)
    val = np.where(new[..., None], acc / np.maximum(n, 1)[..., None], val)
    return val, have | new


def fill_gutters(val, cov, near=24):
    """gutters: grow the islands out `near` texels (what mips and filtering sample), then the rest from a coarse
    push-pull (never seen, only keeps the field continuous)"""
    have = cov.copy()
    for _ in range(near):
        if have.all():
            break
        val, have = _shift_fill(val, have)
    if not have.all():
        small, sh = val, have
        levels = []
        while sh.shape[0] > 4 and not sh.all():
            levels.append((small, sh))
            h = sh.shape[0] // 2
            w4 = sh.reshape(h, 2, h, 2).sum((1, 3)).astype(np.float32)
            v4 = (small * sh[..., None]).reshape(h, 2, h, 2, -1).sum((1, 3))
            small = v4 / np.maximum(w4, 1)[..., None]
            sh = w4 > 0
        if not sh.all():
            small = np.where(sh[..., None], small, small[sh].mean(0) if sh.any() else 0)
        for big, bh in reversed(levels):
            up = np.repeat(np.repeat(small, 2, 0), 2, 1)
            small = np.where(bh[..., None], big, up)
        val = np.where(have[..., None], val, small)
    return val


def dilate(mask, it):
    m = mask.copy()
    for _ in range(it):
        m = m | np.roll(m, 1, 0) | np.roll(m, -1, 0) | np.roll(m, 1, 1) | np.roll(m, -1, 1)
    return m


# ---------------------------------------------------------------- noise (numpy, seeded hashes)
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


# ---------------------------------------------------------------- the look (as approved on Ivy, 11-09)
def material(p, seed, disgust):
    p = p.astype(np.float32)
    wv = np.stack([fbm(p / 4.0 + o, 3, seed + 20 + i) for i, o in enumerate((0.0, 5.2, 9.7))], -1)
    w = p + 1.4 * wv
    big = fbm(w / 9.0, 4, seed + 1)
    mid = fbm(w / 3.0, 4, seed + 2)
    fine = fbm(w / 0.45, 3, seed + 11)
    region = smoothstep(-0.12, 0.22, fbm(p / 16.0 + 50.0, 3, seed + 14))
    necro = smoothstep(0.0, 0.32, big + 0.35 * mid + 0.15 * region)
    bile = smoothstep(0.08, 0.35, fbm(w / 6.0 + 31.0, 3, seed + 3))
    rawn = fbm(w / 4.5 + 7.0, 5, seed + 4) + 0.18 * mid + 0.04 * fine + 0.22 * (region - 0.55)
    raw = smoothstep(0.20, 0.27, rawn)
    margin = smoothstep(0.13, 0.20, rawn) * (1 - raw)
    deep = smoothstep(0.30, 0.40, rawn)
    stri = ridged(w * np.array([1.0, 1.0, 3.5], np.float32) / 0.6, 2, seed + 5)
    fat = smoothstep(0.35, 0.55, fbm(w / 0.3 + 2.0, 2, seed + 12)) * raw

    def sore(q):
        f1, _, cid = cellular(q / 1.9, seed + 6)
        dens = (0.06 + 0.55 * region) * (0.6 + 0.6 * np.clip(big + 0.3, 0, 1))
        has = (cid < dens).astype(np.float32)
        rad = (0.20 + 0.16 * (cid / np.maximum(dens, 1e-3))) * (1 + 0.45 * fine)
        return f1, rad, has
    f1, rad, has = sore(w)
    crater = smoothstep(rad, rad * 0.55, f1) * has
    rim = np.exp(-((f1 - rad) / 0.09) ** 2) * has
    halo = np.exp(-((f1 - rad) / 0.30) ** 2) * has * (1 - crater)
    ooze = np.zeros_like(crater)
    for step in (0.30, 0.60, 0.95):
        g1, grad, ghas = sore(w + np.array([0, 0, step], np.float32))
        ooze = np.maximum(ooze, smoothstep(grad * 1.1, grad * 0.5, g1) * ghas * (1.15 - step))
    ooze = np.clip(ooze, 0, 1) * (1 - crater)
    g1, _, gid = cellular(w / 0.7 + 3.3, seed + 7)
    pust = smoothstep(0.26, 0.04, g1) * (gid < 0.015 + 0.30 * halo + 0.04 * necro * region)
    vein = smoothstep(0.93, 0.98, ridged(w / 2.4, 3, seed + 8)) * smoothstep(-0.05, 0.25, mid)
    fis = smoothstep(0.935, 0.985, ridged(w / 1.2 + 4.0, 2, seed + 9)) * \
        smoothstep(0.0, 0.25, fbm(p / 5.0 + 3.0, 2, seed + 13)) * (1 - raw) * (1 - crater)
    pores = fbm(p / 0.22, 2, seed + 10)
    k = np.float32(disgust)
    height = (0.05 * pores + 0.03 * fine - 0.12 * raw - 0.06 * deep + 0.07 * stri * raw + 0.05 * margin
              - 0.30 * crater + 0.10 * rim + 0.04 * halo + 0.20 * pust + 0.05 * vein - 0.10 * fis + 0.02 * ooze) * k
    wet = np.clip(np.maximum.reduce([0.9 * raw, 0.6 * crater, 0.8 * pust, 0.3 * rim, 0.75 * ooze]), 0, 1) * min(1.0, k)
    return dict(grey=np.full(len(p), min(1.0, float(k)), np.float32), necro=necro * k, bile=bile * k, raw=raw * k,
                margin=margin * k, deep=deep * k, stri=stri, fat=fat * k, fine=fine, crater=crater * k, rim=rim * k,
                halo=halo * k, ooze=ooze * k, pust=pust * k, vein=vein * k, crack=fis * k, height=height, wet=wet)


def paint(base, f):
    lum = (base @ LW)[:, None]
    detail = np.clip(lum / max(float(np.median(lum)), 1e-3), 0.4, 1.8)

    def mix(c, col, a):
        return c + (col - c) * np.clip(a, 0, 1)[:, None]
    c = base.copy()
    c = mix(c, lum * np.array([0.95, 0.98, 0.85], np.float32), f['grey'] * 0.25)
    c = mix(c, c * np.array([0.55, 0.42, 0.48], np.float32), f['necro'] * 0.6)
    c = mix(c, lum * np.array([1.15, 1.08, 0.50], np.float32), f['bile'] * 0.35)
    c = mix(c, c * np.array([1.05, 0.62, 0.58], np.float32), f['halo'] * 0.55)
    c = mix(c, np.array([0.13, 0.07, 0.05], np.float32) * detail, f['margin'] * 0.75)
    meat = np.array([0.42, 0.10, 0.085], np.float32) * (0.70 + 0.45 * f['stri'])[:, None] * \
        (0.85 + 0.30 * f['fine'])[:, None] * detail ** 0.5
    meat = mix(meat, np.array([0.20, 0.035, 0.04], np.float32), f['deep'] * 0.8)
    meat = mix(meat, np.array([0.62, 0.50, 0.28], np.float32), f['fat'] * 0.7)
    c = mix(c, meat, f['raw'] * 0.92)
    c = mix(c, np.array([0.40, 0.33, 0.17], np.float32) * detail ** 0.5, f['ooze'] * 0.55)
    c = mix(c, np.array([0.48, 0.42, 0.26], np.float32) * detail ** 0.5, f['rim'] * 0.40)
    sorec = np.array([0.17, 0.03, 0.03], np.float32) * (0.8 + 0.4 * f['fine'])[:, None]
    c = mix(c, sorec, f['crater'] * 0.95)
    c = mix(c, np.array([0.78, 0.70, 0.44], np.float32), f['pust'] * 0.75)
    c = mix(c, np.array([0.22, 0.15, 0.24], np.float32) * detail ** 0.5, f['vein'] * 0.45)
    c = c * (1 - 0.40 * np.clip(f['crack'], 0, 1))[:, None]
    return np.clip(c, 0, 1)


def evaluate(pos, mask, fade, seed, disgust, chunk=400_000):
    idx = np.flatnonzero(mask.ravel())
    P = pos.reshape(-1, 3)
    out = {}
    for s in range(0, len(idx), chunk):
        sl = idx[s:s + chunk]
        f = material(P[sl], seed, disgust)
        fd = fade.ravel()[sl]
        for k, v in f.items():
            if k not in out:
                out[k] = np.zeros(P.shape[0], np.float32)
            out[k][sl] = v * (fd if k not in ('stri', 'fine') else 1)
    return {k: v.reshape(mask.shape) for k, v in out.items()}


def slope_normals(height, pos):
    def d(axis):
        hp, hm = np.roll(height, -1, axis), np.roll(height, 1, axis)
        pp, pm = np.roll(pos, -1, axis), np.roll(pos, 1, axis)
        dist = np.linalg.norm(pp - pm, axis=-1)
        return np.clip(np.where(dist > 1e-4, (hp - hm) / np.maximum(dist, 1e-4), 0), -3, 3)
    hx, hy = d(1), d(0)
    n = np.stack([-hx, -hy, np.ones_like(hx)], -1)
    return n / np.linalg.norm(n, axis=-1, keepdims=True)


# ---------------------------------------------------------------- DDS in / out (Pillow, the builder's own encoders)
def read_dds(label, data, size):
    """bytes -> (size,size,4) uint8 RGBA, resized to size (BOX down, bilinear up)"""
    d = gt.Dds(label, data)
    rgb, a = d.top(), d.top_alpha()
    im = Image.merge('RGBA', (*rgb.split(), a))
    if im.size != (size, size):
        im = im.resize((size, size), Image.BOX if im.size[0] > size else Image.BILINEAR)
    return np.asarray(im, np.uint8)


def write_dds(arr, kind):
    """(H,W,4) uint8 -> DDS bytes with every mip: colour DXT5 (keeps alpha), normal and specular BC5"""
    im = Image.fromarray(arr, 'RGBA')
    levels = [im]
    while levels[-1].size[0] > 4:
        w = levels[-1].size[0] // 2
        levels.append(levels[-1].resize((w, w), Image.BOX))
    return gt.reencoded(levels, 'DXT5' if kind == 'd' else 'BC5')


def resize(a, size):
    if a.shape[0] == size:
        return a
    im = Image.fromarray(a.astype(np.float32), 'F').resize((size, size), Image.BOX if size < a.shape[0] else
                                                           Image.BILINEAR)
    return np.asarray(im, np.float32)


# ---------------------------------------------------------------- one texture
def build(name, layers, shapes, sources, islands_only, size, seed=1109, disgust=1.0, prep=None):
    """layers: shape keys painted on this texture; sources: {kind: (label, bytes)}; returns {kind: DDS bytes}.
    Every map is written at `size` (the builder's cap: 2K by default)."""
    t0 = time.time()
    srcs = {k: read_dds(lbl, data, size) for k, (lbl, data) in sources.items()}
    att = [(shapes[l]['uv'], shapes[l]['tri'], np.hstack([shapes[l]['world'], shapes[l]['edge'][:, None]]))
           for l in layers]
    # the 3D field is evaluated at most at FIELD_MAX and upsampled: its finest features (pores, pustules) still span
    # several texels there, and a 2K map costs a quarter of the time (a player's PC, 2026-11-09: ~1 min per map)
    fsize = min(size, FIELD_MAX)
    val, cov = rasterize(fsize, att)
    full = fill_gutters(val, cov)
    # only the islands and a ring round them (what filtering and mips reach): the gutters keep the old texels, and
    # the field, most of the time spent here, is not evaluated where nothing is drawn (a third of a body sheet)
    mask = dilate(cov, max(8, fsize // 128))
    fade = np.where(mask, smoothstep(FADE_IN, FADE_OUT, full[..., 3]), 0).astype(np.float32)
    f = evaluate(full[..., :3], mask, fade, seed, disgust)
    if fsize != size:
        f = {k: resize(v, size) for k, v in f.items()}
        full = np.stack([resize(full[..., i], size) for i in range(4)], -1)
        mask = resize(mask.astype(np.float32), size) > 0.5
        cov = resize(cov.astype(np.float32), size) > 0.5
    pos = full[..., :3]
    if prep:
        prep(srcs, pos, cov)
    out = {}
    for k, a8 in srcs.items():
        a = a8.astype(np.float32) / 255.0
        if k == 'd':
            ff = {n: v.ravel() for n, v in f.items() if n not in ('height', 'wet')}
            new = paint(a[..., :3].reshape(-1, 3), ff).reshape(size, size, 3)
            a[..., :3] = np.where(mask[..., None], new, a[..., :3])
        elif k == 'n':
            nd = slope_normals(f['height'], pos)
            n0 = a[..., :2] * 2 - 1
            z0 = np.sqrt(np.clip(1 - (n0 ** 2).sum(-1), 0, 1))
            n = np.stack([n0[..., 0] + nd[..., 0], n0[..., 1] + nd[..., 1], z0 * nd[..., 2]], -1)
            n /= np.linalg.norm(n, axis=-1, keepdims=True)
            a[..., 0] = np.where(mask, n[..., 0] * 0.5 + 0.5, a[..., 0])
            a[..., 1] = np.where(mask, n[..., 1] * 0.5 + 0.5, a[..., 1])
            a[..., 2], a[..., 3] = 0, 1
        else:                                         # _s: R specular, G glossiness
            w = f['wet']
            dry = np.clip(f['necro'] + f['crack'], 0, 1)
            r = (a[..., 0] + (0.55 - a[..., 0]) * w) * (1 - 0.30 * dry * (1 - w))
            g = a[..., 1] + (0.82 - a[..., 1]) * w
            a[..., 0] = np.where(mask, r, a[..., 0])
            a[..., 1] = np.where(mask, g, a[..., 1])
            a[..., 2], a[..., 3] = 0, 1
        out[k] = write_dds((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8), k)
    print(f'   {name}: {size}px, covered {cov.mean() * 100:.0f}%, {time.time() - t0:.0f} s')
    return out


def genital_prep(body, genitals, human_d, ghoul_d, tone=512):
    """the ghoul women's genital texture: the human genital texture's light/dark detail carried on the ghoul body's
    colour at the nearest BODY VERTEX (found once per genital vertex, then interpolated across its triangles: no
    KD-tree and no per-texel search), mucosa turned necrotic maroon. human_d / ghoul_d: (label, bytes) of the body
    textures the genitals sit on."""
    hum = read_dds(*human_d, tone)[..., :3].astype(np.float32) / 255
    gho = read_dds(*ghoul_d, tone)[..., :3].astype(np.float32) / 255
    from PIL import ImageFilter

    def blur(a):
        return np.asarray(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3)),
                          np.float32) / 255
    hum, gho = blur(hum), blur(gho)
    buv = body['uv']
    bx = np.clip((buv[:, 0] * tone).astype(int), 0, tone - 1)
    by = np.clip((buv[:, 1] * tone).astype(int), 0, tone - 1)
    b_h, b_g = hum[by, bx], gho[by, bx]
    gw, bw = genitals['world'], body['world']
    near = np.empty(len(gw), np.int64)
    for s in range(0, len(gw), 512):
        near[s:s + 512] = ((gw[s:s + 512, None, :] - bw[None, :, :]) ** 2).sum(-1).argmin(1)
    tones = np.hstack([b_h[near], b_g[near]]).astype(np.float32)          # per genital vertex: human, ghoul

    def prep(srcs, pos, cov):
        g8 = srcs['d']
        size = g8.shape[0]
        val, have = rasterize(size, [(genitals['uv'], genitals['tri'], tones)])
        val = fill_gutters(val, have, near=8).reshape(-1, 6)
        g = g8[..., :3].reshape(-1, 3).astype(np.float32) / 255
        detail = np.clip((g @ LW) / np.maximum(val[:, :3] @ LW, 0.03), 0.3, 1.15)[:, None]
        rgb = val[:, 3:] * detail * 0.88
        mucosa = np.clip((g[:, 0] - g[:, 1] - 0.07) / 0.14, 0, 1)[:, None]
        rgb = rgb + (np.array([0.36, 0.13, 0.15], np.float32) * detail ** 0.7 - rgb) * (0.8 * mucosa)
        srcs['d'] = np.concatenate([(np.clip(rgb, 0, 1).reshape(size, size, 3) * 255 + 0.5).astype(np.uint8),
                                    g8[..., 3:]], -1)
    return prep


def dds_bytes_preview(data):
    """first mip of a DDS we wrote, as a PIL image (tests / previews)"""
    return Image.open(io.BytesIO(data)).convert('RGB')
