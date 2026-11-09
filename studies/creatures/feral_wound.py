"""The feral stump's torn end: Textures\\Anatomy\\Creatures\\FeralStumpWound_d/n/s.dds (512, raw torn meat: dark wet
red core, ragged fibres, a crusted rim matching dried feral skin) and Materials\\Anatomy\\Creatures\\
FeralStumpWound.bgsm (vanilla FeralGhoulBody1.BGSM with its three textures retargeted).
    python -I feral_wound.py <out Data dir>"""
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
N = 512


def textures():
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32) / N
    p = np.stack([xx.ravel() * 6, yy.ravel() * 6, np.zeros(N * N, np.float32)], -1)
    r = np.sqrt((xx - 0.5) ** 2 + (yy - 0.5) ** 2).ravel() * 2          # 0 centre, 1 = rim of the disc UVs
    fib = gc.ridged(p * np.array([1, 1, 0], np.float32) * 2.5 + 3, 3, 41)
    blot = gc.fbm(p * 1.3, 4, 42)
    fine = gc.fbm(p * 6, 3, 43)
    rim = gc.smoothstep(0.62, 0.95, r + 0.12 * blot)
    meat = np.stack([0.27 + 0.09 * fib, 0.055 + 0.03 * fib, 0.05 + 0.02 * fib], -1) * (0.75 + 0.35 * fine)[:, None]
    meat = meat * (1 - 0.55 * gc.smoothstep(0.1, 0.5, blot))[:, None] + \
        np.array([0.10, 0.02, 0.02], np.float32) * gc.smoothstep(0.1, 0.5, blot)[:, None] * 0.55
    crust = np.array([0.17, 0.11, 0.075], np.float32) * (0.8 + 0.4 * fine)[:, None]
    col = meat + (crust - meat) * rim[:, None]
    d = (np.clip(col, 0, 1) * 255 + 0.5).astype(np.uint8).reshape(N, N, 3)
    d = np.concatenate([d, np.full((N, N, 1), 255, np.uint8)], -1)
    h = (0.6 * fib + 0.3 * fine - 0.5 * gc.smoothstep(0.0, 0.6, 1 - r) + 0.4 * rim).reshape(N, N)
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 2.0
    gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 2.0
    n = np.stack([-gx, -gy, np.ones_like(gx)], -1)                         # DirectX green (measured on FO4 skin)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    nn = np.zeros((N, N, 4), np.uint8)
    nn[..., 0] = (n[..., 0] * 127.5 + 127.5).astype(np.uint8)
    nn[..., 1] = (n[..., 1] * 127.5 + 127.5).astype(np.uint8)
    nn[..., 3] = 255
    wet = (1 - rim).reshape(N, N)
    ss = np.zeros((N, N, 4), np.uint8)
    ss[..., 0] = ((0.25 + 0.35 * wet) * 255).astype(np.uint8)              # specular
    ss[..., 1] = ((0.35 + 0.50 * wet) * 255).astype(np.uint8)              # gloss: wet meat
    ss[..., 3] = 255
    base = OUT / 'textures/anatomy/creatures'
    for arr, kind, fmt in ((d, 'd', 'BC1_UNORM'), (nn, 'n', 'BC5_UNORM'), (ss, 's', 'BC5_UNORM')):
        gc.array_to_dds(arr, fmt, base / f'FeralStumpWound_{kind}.dds', gc.ROOT / 'work' / 'enc_wound')
        print('texture', kind)


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
        new = f'Anatomy/Creatures/FeralStumpWound_{m.group(1).decode().lower()}.dds'.encode() + b'\0'
        out += b[o:s0 - 4] + struct.pack('<I', len(new)) + new
        o = s0 + ln
        n += 1
    out += b[o:]
    if n != 3:
        raise SystemExit(f'expected 3 textures, found {n}: {re.findall(rb"[ -~]{8,}", b)}')
    dst = OUT / 'materials/anatomy/creatures/FeralStumpWound.bgsm'
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(bytes(out))
    print('bgsm', [s.decode() for s in re.findall(rb'[ -~]{8,}', bytes(out))])


if __name__ == '__main__':
    textures()
    bgsm()
