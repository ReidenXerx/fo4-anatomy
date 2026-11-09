"""Canine penis material: Textures\\Anatomy\\Creatures\\CaninePenis_d/n/s.dds (512 x 1024; UV u = around, v = root
(0) -> tip (1); v < 0.04 = the sheath's inner lining) and Materials\\Anatomy\\Creatures\\CaninePenis.bgsm (vanilla
FeralGhoulBody1.BGSM, the same non-tinted creature skin shader the feral wound uses, textures retargeted).
Look: wet, deep red at the root and knot, brighter pink-red along the shaft, a slightly purple pointed tip, a faint
ventral line, branching veins along the length, fine mottling.
    python -I canine_tex.py <out Data dir>"""
import pathlib
import re
import struct
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import gamedata  # noqa: E402
import ghoul_common as gc  # noqa: E402

OUT = pathlib.Path(sys.argv[1])
DATA = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data')
W, H = 512, 1024
STEM = 'MutantGlans'


def textures():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    u, v = xx / W, yy / H
    ang = u * 2 * np.pi
    # tube-space noise coordinates (seamless around u): circle in xy, length in z
    p = np.stack([np.cos(ang).ravel() * 1.2, np.sin(ang).ravel() * 1.2, v.ravel() * 9.0], -1).astype(np.float32)
    vein = gc.ridged(p * np.array([1.6, 1.6, 0.55], np.float32) + 7, 4, 51)            # long branching ridges
    q1, q2 = np.percentile(vein, [91, 98.5])                                    # thresholds from the noise itself
    patch = gc.fbm(p * 0.8 + 3, 2, 54)
    vein = gc.smoothstep(q1, q2, vein) * gc.smoothstep(*np.percentile(patch, [35, 65]), patch)          # sparse
    mott = gc.fbm(p * 2.2, 4, 52)
    fine = gc.fbm(p * 9.0, 3, 53)
    vv = v.ravel()
    knot = np.exp(-((vv - 0.05) / 0.06) ** 2)
    tip = gc.smoothstep(0.80, 1.0, vv)
    base = np.array([0.46, 0.22, 0.20], np.float32)
    deep = np.array([0.34, 0.20, 0.14], np.float32)
    purple = np.array([0.42, 0.16, 0.24], np.float32)
    col = base + (deep - base) * np.clip(knot * 0.8 + gc.smoothstep(0.12, 0.0, vv) * 0.6, 0, 1)[:, None]
    col = col + (purple - col) * tip[:, None] * 0.6
    ventral = np.exp(-((np.cos(ang).ravel() - 1.0) / 0.06) ** 2)          # underside line (u = 0 faces down)
    col = col * (1 - 0.18 * ventral)[:, None]
    col = col * (0.88 + 0.22 * mott)[:, None] * (0.95 + 0.08 * fine)[:, None]
    col = col + (np.array([0.40, 0.09, 0.18], np.float32) - col) * (vein * 0.45)[:, None]
    lining = vv * 0.0                                             # sheath lining: paler
    col = col + (np.array([0.62, 0.36, 0.36], np.float32) - col) * lining[:, None] * 0.7
    d = (np.clip(col, 0, 1) * 255 + 0.5).astype(np.uint8).reshape(H, W, 3)
    d = np.concatenate([d, np.full((H, W, 1), 255, np.uint8)], -1)
    h = (0.9 * vein + 0.15 * mott + 0.08 * fine).reshape(H, W)
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 2.5
    gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 2.5
    n = np.stack([-gx, -gy, np.ones_like(gx)], -1)                                     # DirectX green
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    nn = np.zeros((H, W, 4), np.uint8)
    nn[..., 0] = (n[..., 0] * 127.5 + 127.5).astype(np.uint8)
    nn[..., 1] = (n[..., 1] * 127.5 + 127.5).astype(np.uint8)
    nn[..., 3] = 255
    ss = np.zeros((H, W, 4), np.uint8)
    ss[..., 0] = ((0.40 + 0.15 * fine.reshape(H, W)) * 255).astype(np.uint8)            # specular: wet mucosa
    ss[..., 1] = ((0.78 - 0.20 * vein.reshape(H, W)) * 255).astype(np.uint8)            # gloss
    ss[..., 3] = 255
    base_dir = OUT / 'textures/anatomy/creatures'
    for arr, kind, fmt in ((d, 'd', 'BC7_UNORM'), (nn, 'n', 'BC5_UNORM'), (ss, 's', 'BC5_UNORM')):
        gc.array_to_dds(arr, fmt, base_dir / f'{STEM}_{kind}.dds', gc.ROOT / 'work' / 'enc_sm')
        print('texture', kind)
    from PIL import Image
    Image.fromarray(d[..., :3]).save(gc.ROOT.parent / 'creatures' / 'sm' / f'{STEM}_d_preview.png')


def bgsm():
    mats = gamedata.Ba2(DATA / 'Fallout4 - Materials.ba2')
    b = mats.read('materials/actors/feralghoul/feralghoulbody1.bgsm')
    out, o, n = bytearray(), 0, 0
    for m in re.finditer(rb'(?i)actors[\\/]feralghoul[\\/]feralghoulbody1_([dns])\.dds\0', b):
        s0 = m.start()
        while s0 > 0 and b[s0 - 1] >= 32:
            s0 -= 1
        ln = struct.unpack_from('<I', b, s0 - 4)[0]
        if s0 + ln != m.end():
            raise SystemExit('unexpected BGSM layout')
        new = f'Anatomy/Creatures/{STEM}_{m.group(1).decode().lower()}.dds'.encode() + b'\0'
        out += b[o:s0 - 4] + struct.pack('<I', len(new)) + new
        o = s0 + ln
        n += 1
    out += b[o:]
    if n != 3:
        raise SystemExit(f'expected 3 textures, found {n}')
    dst = OUT / f'materials/anatomy/creatures/{STEM}.bgsm'
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(bytes(out))
    print('bgsm', [s.decode() for s in re.findall(rb'[ -~]{8,}', bytes(out))])


if __name__ == '__main__':
    textures()
    bgsm()
