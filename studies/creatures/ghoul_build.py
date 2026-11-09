"""Ghoul skin, more disgusting (alasdairn 11-09, via Watcher). Texture-only: every ghoul skin map keeps its path, size
and channel layout; the new detail is a 3D field (necrotic mottling, peeled raw flesh, weeping sores, pustules,
veins, leathery cracks) sampled at each texel's surface position, so head, rear head, body and hands agree across
every seam. The detail fades to nothing at the face edge: NPC faces are baked FaceGen (made from the OLD head
texture), so the neck and rear-head ring stay exactly as the faces expect.
    python -I ghoul_build.py [F|M] [--only d,n,s] [--disgust 1.0]
Output: D:\\F4Output\\ghoulskin\\out\\Data\\textures\\..."""
import argparse
import pathlib
import sys
import time

import numpy as np
from PIL import Image
from scipy.spatial import cKDTree

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import ghoul_common as gc  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
SRC = gc.ROOT / 'src'
OUT = gc.ROOT / 'out' / 'Data'
WORK = gc.ROOT / 'work'
V2 = SRC / 'Fallout4 - Textures2' / 'textures/actors/character'
V3 = SRC / 'Fallout4 - Textures3' / 'textures/actors/character'
HR = SRC / 'loose_CBBE HeadRear Absolute Fix' / 'textures/actors/character'
CB = SRC / "loose_Caliente's Beautiful Bodies Enhancer" / 'textures/actors/character'
BT = SRC / 'loose_BodyTalk' / 'textures/actors/character'

# per texture: maps {kind: (source dds, output path under Data, BC format)}, the shapes painted on it, whether only
# the painted islands change (the rear-head texture's other islands are the unused vanilla body layout)
TEXTURES = {
    'F': [
        dict(name='F body', layers=['body'], islands_only=False, maps={
            'd': (HR / 'custombody/ghoulfemalebody_d.dds', 'textures/actors/character/custombody/ghoulfemalebody_d.dds', 'BC1_UNORM'),
            'n': (HR / 'custombody/ghoulfemalebody_n.dds', 'textures/actors/character/custombody/ghoulfemalebody_n.dds', 'BC5_UNORM'),
            's': (HR / 'custombody/ghoulfemalebody_s.dds', 'textures/actors/character/custombody/ghoulfemalebody_s.dds', 'BC5_UNORM')}),
        dict(name='F rear head', layers=['rear'], islands_only=True, maps={
            'd': (HR / 'ghoulfemale/ghoulfemalebody_d.dds', 'textures/actors/character/ghoulfemale/ghoulfemalebody_d.dds', 'BC1_UNORM'),
            'n': (HR / 'ghoulfemale/ghoulfemalebody_n.dds', 'textures/actors/character/ghoulfemale/ghoulfemalebody_n.dds', 'BC5_UNORM'),
            's': (HR / 'ghoulfemale/ghoulfemalebody_s.dds', 'textures/actors/character/ghoulfemale/ghoulfemalebody_s.dds', 'BC5_UNORM')}),
        dict(name='F hands', layers=['hands'], islands_only=False, maps={
            'd': (CB / 'ghoulfemale/ghoulfemalehands_d.dds', 'textures/actors/character/ghoulfemale/ghoulfemalehands_d.dds', 'BC1_UNORM'),
            'n': (CB / 'ghoulfemale/ghoulfemalehands_n.dds', 'textures/actors/character/ghoulfemale/ghoulfemalehands_n.dds', 'BC5_UNORM'),
            's': (CB / 'ghoulfemale/ghoulfemalehands_s.dds', 'textures/actors/character/ghoulfemale/ghoulfemalehands_s.dds', 'BC5_UNORM')}),
        dict(name='F face', layers=['head'], islands_only=False, maps={
            'd': (V2 / 'ghoulfemale/ghoulfemalehead_d.dds', 'textures/actors/character/ghoulfemale/ghoulfemalehead_d.dds', 'BC7_UNORM'),
            'n': (V2 / 'ghoulfemale/ghoulfemalehead_n.dds', 'textures/actors/character/ghoulfemale/ghoulfemalehead_n.dds', 'BC5_UNORM'),
            's': (V2 / 'ghoulfemale/ghoulfemalehead_s.dds', 'textures/actors/character/ghoulfemale/ghoulfemalehead_s.dds', 'BC5_UNORM')}),
    ],
    'M': [
        dict(name='M body', layers=['body', 'rear'], islands_only=False, maps={
            'd': (BT / 'ghoulmale/ghoulmalebody_d.dds', 'textures/actors/character/ghoulmale/ghoulmalebody_d.dds', 'BC7_UNORM'),
            'n': (BT / 'ghoulmale/ghoulmalebody_n.dds', 'textures/actors/character/ghoulmale/ghoulmalebody_n.dds', 'BC5_UNORM'),
            's': (BT / 'ghoulmale/ghoulmalebody_s.dds', 'textures/actors/character/ghoulmale/ghoulmalebody_s.dds', 'BC5_UNORM')}),
        dict(name='M hands', layers=['hands'], islands_only=False, maps={
            'd': (V3 / 'ghoulmale/ghoulmalehands_d.dds', 'textures/actors/character/ghoulmale/ghoulmalehands_d.dds', 'BC1_UNORM'),
            'n': (V3 / 'ghoulmale/ghoulmalehands_n.dds', 'textures/actors/character/ghoulmale/ghoulmalehands_n.dds', 'BC5_UNORM'),
            's': (V3 / 'ghoulmale/ghoulmalehands_s.dds', 'textures/actors/character/ghoulmale/ghoulmalehands_s.dds', 'BC5_UNORM')}),
        dict(name='M face', layers=['head'], islands_only=False, maps={
            'd': (V2 / 'ghoulmale/ghoulmalehead_d.dds', 'textures/actors/character/ghoulmale/ghoulmalehead_d.dds', 'BC7_UNORM'),
            'n': (V2 / 'ghoulmale/ghoulmalehead_n.dds', 'textures/actors/character/ghoulmale/ghoulmalehead_n.dds', 'BC5_UNORM'),
            's': (V2 / 'ghoulmale/ghoulmalehead_s.dds', 'textures/actors/character/ghoulmale/ghoulmalehead_s.dds', 'BC5_UNORM')}),
    ],
}
MESHES = {'F': dict(body=('femalebody.nif', 'CBBE'), genitals=('femalebody.nif', 'AnatomyGenitals'),
                    hands=('femalehands.nif', None), head=('femaleghoulhead.nif', None),
                    rear=('femaleheadrear.nif', None)),
          'M': dict(body=('malebody.nif', None), hands=('malehands.nif', None), head=('maleghoulhead.nif', None),
                    rear=('maleghoulheadrear.nif', None))}
FADE_IN, FADE_OUT = 0.8, 5.0        # game units from the face edge: untouched inside FADE_IN, full detail past FADE_OUT


def shapes_in_body_space(sex):
    m = MESHES[sex]
    body = gc.load_shape(*m['body'])
    out = {}
    for key, (n, s) in m.items():
        sh = gc.load_shape(n, s)
        if key in ('body', 'genitals'):
            world = sh['pos']
        elif key == 'hands':
            world = gc.into(sh, body, 'larm_hand')
        elif key == 'head':
            world = gc.into(sh, body, 'chest')
        else:                                       # rear head: through the head mesh (HEAD), then into the body
            head = gc.load_shape(*m['head'])
            p = gc.from_bone(head['skin']['head'], gc.to_bone(sh['skin']['head'], sh['pos']))
            world = gc.from_bone(body['skin']['chest'], gc.to_bone(head['skin']['chest'], p))
        out[key] = dict(sh, world=world)
    # the face's edge where it meets the body or the rear head: the detail fades to zero there
    head = out['head']
    ring = head['world'][gc.openings(head)]
    near = np.vstack([out['body']['world'], out['rear']['world']])
    d, _ = cKDTree(near).query(ring)
    out['face_edge'] = ring[d < 0.05]
    return out


# ---------------------------------------------------------------- the look
def material(p, seed, disgust):
    """Per point (n,3) in game units: colour ops, height (units), wetness, face-agnostic. Returns dict of arrays."""
    p = p.astype(np.float32)
    # domain warp: every feature is pushed around by a slow 3D vector field, so nothing reads as a grid or a circle
    wv = np.stack([gc.fbm(p / 4.0 + o, 3, seed + 20 + i) for i, o in enumerate((0.0, 5.2, 9.7))], -1)
    w = p + 1.4 * wv
    big = gc.fbm(w / 9.0, 4, seed + 1)
    mid = gc.fbm(w / 3.0, 4, seed + 2)
    fine = gc.fbm(w / 0.45, 3, seed + 11)
    # rot clusters: some regions badly rotted, others only bruised (11-09 renders read as an even leopard print)
    region = gc.smoothstep(-0.12, 0.22, gc.fbm(p / 16.0 + 50.0, 3, seed + 14))
    necro = gc.smoothstep(0.0, 0.32, big + 0.35 * mid + 0.15 * region)  # bruised, dying skin
    bile = gc.smoothstep(0.08, 0.35, gc.fbm(w / 6.0 + 31.0, 3, seed + 3))  # jaundiced yellow-green blotches
    rawn = gc.fbm(w / 4.5 + 7.0, 5, seed + 4) + 0.18 * mid + 0.04 * fine + 0.22 * (region - 0.55)
    raw = gc.smoothstep(0.20, 0.27, rawn)                                 # skin sloughed off: raw flesh
    margin = gc.smoothstep(0.13, 0.20, rawn) * (1 - raw)                 # blackened, crusted edge round it
    deep = gc.smoothstep(0.30, 0.40, rawn)                                # the deepest, darkest meat
    stri = gc.ridged(w * np.array([1.0, 1.0, 3.5], np.float32) / 0.6, 2, seed + 5)   # muscle fibre
    fat = gc.smoothstep(0.35, 0.55, gc.fbm(w / 0.3 + 2.0, 2, seed + 12)) * raw  # yellow fat specks in the meat

    def sore(q):
        f1, _, cid = gc.cellular(q / 1.9, seed + 6)
        dens = (0.06 + 0.55 * region) * (0.6 + 0.6 * np.clip(big + 0.3, 0, 1))
        has = (cid < dens).astype(np.float32)
        rad = (0.20 + 0.16 * (cid / np.maximum(dens, 1e-3))) * (1 + 0.45 * fine)
        return f1, rad, has
    f1, rad, has = sore(w)
    crater = gc.smoothstep(rad, rad * 0.55, f1) * has
    rim = np.exp(-((f1 - rad) / 0.09) ** 2) * has
    halo = np.exp(-((f1 - rad) / 0.30) ** 2) * has * (1 - crater)       # inflamed skin round each sore
    ooze = np.zeros_like(crater)
    for step in (0.30, 0.60, 0.95):                                       # weeping: trails run down (+z is up)
        g1, grad, ghas = sore(w + np.array([0, 0, step], np.float32))
        ooze = np.maximum(ooze, gc.smoothstep(grad * 1.1, grad * 0.5, g1) * ghas * (1.15 - step))
    ooze = np.clip(ooze, 0, 1) * (1 - crater)
    g1, _, gid = gc.cellular(w / 0.7 + 3.3, seed + 7)                     # pustules, clustered by the sores
    pust = gc.smoothstep(0.26, 0.04, g1) * (gid < 0.015 + 0.30 * halo + 0.04 * necro * region)
    vein = gc.smoothstep(0.93, 0.98, gc.ridged(w / 2.4, 3, seed + 8)) * gc.smoothstep(-0.05, 0.25, mid)
    fis = gc.smoothstep(0.935, 0.985, gc.ridged(w / 1.2 + 4.0, 2, seed + 9)) * \
        gc.smoothstep(0.0, 0.25, gc.fbm(p / 5.0 + 3.0, 2, seed + 13)) * (1 - raw) * (1 - crater)   # skin fissures
    pores = gc.fbm(p / 0.22, 2, seed + 10)
    k = np.float32(disgust)
    height = (0.05 * pores + 0.03 * fine - 0.12 * raw - 0.06 * deep + 0.07 * stri * raw + 0.05 * margin
              - 0.30 * crater + 0.10 * rim + 0.04 * halo + 0.20 * pust + 0.05 * vein - 0.10 * fis + 0.02 * ooze) * k
    wet = np.clip(np.maximum.reduce([0.9 * raw, 0.6 * crater, 0.8 * pust, 0.3 * rim, 0.75 * ooze]), 0, 1) * \
        min(1.0, k)
    return dict(grey=np.full(len(p), min(1.0, float(k)), np.float32), necro=necro * k, bile=bile * k, raw=raw * k, margin=margin * k, deep=deep * k, stri=stri,
                fat=fat * k, fine=fine, crater=crater * k, rim=rim * k, halo=halo * k, ooze=ooze * k,
                pust=pust * k, vein=vein * k, crack=fis * k, height=height, wet=wet)


def paint(base, f):
    """base (n,3) 0..1 -> new colour."""
    lum = (base @ np.array([0.3, 0.55, 0.15], np.float32))[:, None]
    detail = np.clip(lum / max(float(np.median(lum)), 1e-3), 0.4, 1.8)  # the old skin's own light/dark detail

    def mix(c, col, a):
        return c + (col - c) * np.clip(a, 0, 1)[:, None]
    c = base.copy()
    c = mix(c, lum * np.array([0.95, 0.98, 0.85], np.float32), f['grey'] * 0.25)   # deader, greyer overall
    c = mix(c, c * np.array([0.55, 0.42, 0.48], np.float32), f['necro'] * 0.6)          # purple-brown bruising
    c = mix(c, lum * np.array([1.15, 1.08, 0.50], np.float32), f['bile'] * 0.35)        # jaundice
    c = mix(c, c * np.array([1.05, 0.62, 0.58], np.float32), f['halo'] * 0.55)          # inflamed, angry skin
    c = mix(c, np.array([0.13, 0.07, 0.05], np.float32) * detail, f['margin'] * 0.75)   # blackened crust edge
    meat = np.array([0.42, 0.10, 0.085], np.float32) * (0.70 + 0.45 * f['stri'])[:, None] * \
        (0.85 + 0.30 * f['fine'])[:, None] * detail ** 0.5
    meat = mix(meat, np.array([0.20, 0.035, 0.04], np.float32), f['deep'] * 0.8)
    meat = mix(meat, np.array([0.62, 0.50, 0.28], np.float32), f['fat'] * 0.7)
    c = mix(c, meat, f['raw'] * 0.92)
    c = mix(c, np.array([0.40, 0.33, 0.17], np.float32) * detail ** 0.5, f['ooze'] * 0.55)   # yellow-brown weep
    c = mix(c, np.array([0.48, 0.42, 0.26], np.float32) * detail ** 0.5, f['rim'] * 0.40)    # crusted pus rim
    sorec = np.array([0.17, 0.03, 0.03], np.float32) * (0.8 + 0.4 * f['fine'])[:, None]
    c = mix(c, sorec, f['crater'] * 0.95)
    c = mix(c, np.array([0.78, 0.70, 0.44], np.float32), f['pust'] * 0.75)
    c = mix(c, np.array([0.22, 0.15, 0.24], np.float32) * detail ** 0.5, f['vein'] * 0.45)
    c = c * (1 - 0.40 * np.clip(f['crack'], 0, 1))[:, None]
    return np.clip(c, 0, 1)


# ---------------------------------------------------------------- per texture
def evaluate(pos, mask, fade, seed, disgust, chunk=600_000):
    """Fields for the texels in mask; returns full-size arrays (H,W) / (H,W,k)."""
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


def resize(a, size):
    if a.shape[0] == size:
        return a
    im = Image.fromarray(a.astype(np.float32), 'F').resize((size, size), Image.BOX if size < a.shape[0] else
                                                           Image.BILINEAR)
    return np.asarray(im, np.float32)


def slope_normals(height, pos):
    """Tangent-space normal (x, y, z) of the height field, per world unit along each texel axis; DirectX green."""
    def d(axis):
        hp, hm = np.roll(height, -1, axis), np.roll(height, 1, axis)
        pp, pm = np.roll(pos, -1, axis), np.roll(pos, 1, axis)
        dist = np.linalg.norm(pp - pm, axis=-1)
        g = np.where(dist > 1e-4, (hp - hm) / np.maximum(dist, 1e-4), 0)
        return np.clip(g, -3, 3)
    hx, hy = d(1), d(0)
    n = np.stack([-hx, -hy, np.ones_like(hx)], -1)
    return n / np.linalg.norm(n, axis=-1, keepdims=True)


def build(tex, shapes, seed, disgust, only):
    t0 = time.time()
    sizes = {}
    srcs = {}
    for k, (src, _, _) in tex['maps'].items():
        a = gc.dds_to_array(src, WORK / 'dec')
        srcs[k] = a
        sizes[k] = a.shape[0]
    size = max(sizes.values())
    layers = [(shapes[l]['uv'], shapes[l]['tri'], shapes[l]['world'], i) for i, l in enumerate(tex['layers'])]
    pos, tag, clash = gc.rasterize(size, layers)
    covered = tag >= 0
    print(f'{tex["name"]}: {size}px, covered {covered.mean() * 100:.1f}%, layer clash {clash} texels '
          f'({time.time() - t0:.0f}s)', flush=True)
    full = gc.fill_gutters(pos, tag)
    if tex.get('prep'):                               # e.g. the genitals: the human texture recoloured to ghoul first
        tex['prep'](srcs, full, covered)
    if tex['islands_only']:
        from scipy import ndimage
        mask = ndimage.binary_dilation(covered, iterations=max(4, size // 256))
    else:
        mask = np.ones_like(covered)
    dist, _ = cKDTree(shapes['face_edge']).query(full[mask].reshape(-1, 3))
    fade = np.zeros(covered.shape, np.float32)
    fade[mask] = gc.smoothstep(FADE_IN, FADE_OUT, dist)
    f = evaluate(full, mask, fade, seed, disgust)
    print(f'   fields done ({time.time() - t0:.0f}s)', flush=True)
    results = {}
    for k, (src, rel, fmt) in tex['maps'].items():
        if only and k not in only:
            continue
        sz = sizes[k]
        a = srcs[k].astype(np.float32) / 255.0
        m = resize(mask.astype(np.float32), sz) > 0.5
        if k == 'd':
            ff = {n: resize(v, sz) for n, v in f.items() if n != 'height' and n != 'wet'}
            base = a[..., :3].reshape(-1, 3)
            new = paint(base, {n: v.ravel() for n, v in ff.items()}).reshape(sz, sz, 3)
            a[..., :3] = np.where(m[..., None], new, a[..., :3])
        elif k == 'n':
            h = resize(f['height'], sz)
            p = np.stack([resize(full[..., i], sz) for i in range(3)], -1)
            nd = slope_normals(h, p)
            n0 = a[..., :2] * 2 - 1
            z0 = np.sqrt(np.clip(1 - (n0 ** 2).sum(-1), 0, 1))
            n = np.stack([n0[..., 0] + nd[..., 0], n0[..., 1] + nd[..., 1], z0 * nd[..., 2]], -1)
            n /= np.linalg.norm(n, axis=-1, keepdims=True)
            a[..., 0] = np.where(m, n[..., 0] * 0.5 + 0.5, a[..., 0])
            a[..., 1] = np.where(m, n[..., 1] * 0.5 + 0.5, a[..., 1])
            a[..., 2] = 0
            a[..., 3] = 1
        else:                                         # _s: R specular, G glossiness
            w = resize(f['wet'], sz)
            dry = resize(np.clip(f['necro'] + f['crack'], 0, 1), sz)
            r = a[..., 0] + (0.55 - a[..., 0]) * w
            g = a[..., 1] + (0.82 - a[..., 1]) * w
            r = r * (1 - 0.30 * dry * (1 - w))
            a[..., 0] = np.where(m, r, a[..., 0])
            a[..., 1] = np.where(m, g, a[..., 1])
            a[..., 2] = 0
            a[..., 3] = 1
        out = (np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)
        dst = gc.array_to_dds(out, fmt, OUT / rel, WORK / 'enc')
        (WORK / 'png').mkdir(parents=True, exist_ok=True)
        Image.fromarray(out[..., :3]).save(WORK / 'png' / f'{tex["name"].replace(" ", "_")}_{k}.png')
        results[k] = dst
        print(f'   {k}: {sz}px {fmt} -> {dst.relative_to(OUT)}', flush=True)
    np.savez_compressed(WORK / f'{tex["name"].replace(" ", "_")}_space.npz', pos=pos.astype(np.float16), tag=tag)
    print(f'   done ({time.time() - t0:.0f}s)', flush=True)
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('sex', nargs='*', default=['F', 'M'])
    ap.add_argument('--only', default='')
    ap.add_argument('--tex', default='', help='substring of a texture name, e.g. "face"')
    ap.add_argument('--disgust', type=float, default=1.0)
    ap.add_argument('--seed', type=int, default=1109)
    a = ap.parse_args()
    only = set(a.only.split(',')) - {''}
    for sex in a.sex:
        shapes = shapes_in_body_space(sex)
        print(f'{sex}: face edge {len(shapes["face_edge"])} vertices', flush=True)
        for tex in TEXTURES[sex]:
            if a.tex and a.tex.lower() not in tex['name'].lower():
                continue
            build(tex, shapes, a.seed, a.disgust, only)


if __name__ == '__main__':
    main()
