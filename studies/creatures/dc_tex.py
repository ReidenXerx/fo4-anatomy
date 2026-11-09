"""Our deathclaw penis textures, written at UAP's paths so UAP's materials + its variant swaps keep working:
  Textures\\Actors\\Deathclaw\\PenisRegular_d/_n/_s.dds, PenisAlbino_D.dds, 'penis glowing_G.dds'
UV (dc_geom.py): u = around (0 = dorsal, 0.5 = ventral groove), v 0.12 -> 0.995 = root -> tip, v < 0.10 = the vent's
flesh lining (male floor + the female's inner).
Look: deathclaw skin on the shaft - beige-grey scales with dark grout, darker on the back - fading over the distal
half into wet maroon flesh, deep purple-red spade head, ivory keratin tips on the two dorsal nub rows (geometry from
dc_geom: every 2.3 units, theta = +-0.6), a dark-red ventral groove. Albino: cream scales, pink flesh.
    python -I dc_tex.py <out Data dir> <erect length>"""
import pathlib
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import ghoul_common as gc  # noqa: E402

OUT = pathlib.Path(sys.argv[1])
LEN = float(sys.argv[2])
W, H = 1024, 2048
V0, V1 = 0.12, 0.995
WORK = pathlib.Path(r'D:\F4Output\creatures\dc\tex\work')


def build():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    u, v = (xx + 0.5) / W, (yy + 0.5) / H
    ang = u * 2 * np.pi
    t = np.clip((v - V0) / (V1 - V0), 0, 1)
    ln = t * LEN
    circ = 2 * np.pi * 3.4                                     # circumference of the shaft in mesh units
    p = np.stack([np.cos(ang).ravel() * circ / (2 * np.pi), np.sin(ang).ravel() * circ / (2 * np.pi),
                  ln.ravel()], -1).astype(np.float32)
    tv, vv, av = t.ravel(), v.ravel(), ang.ravel()
    # scales: ~1.3 units at the root, shrinking toward the tip
    sc = (1.0 / (1.25 - 0.55 * tv))[:, None]
    f1, f2, cid = gc.cellular(p * sc * np.array([1.0, 1.0, 0.8], np.float32), 61)
    edge = f2 - f1
    grout = gc.smoothstep(0.16, 0.03, edge)                   # dark lines between scales
    dome = gc.smoothstep(0.0, 0.55, edge)                      # scale centres raised
    mott = gc.fbm(p * 0.35 + 5, 4, 62)
    fine = gc.fbm(p * 3.0, 3, 63)
    dorsal = 0.5 + 0.5 * np.cos(av)                            # 1 on the back (u = 0), 0 on the groove side
    flesh = gc.smoothstep(0.45, 0.80, tv)                      # skin -> flesh over the distal half
    head = np.exp(-((tv - 0.87) / 0.06) ** 2)
    tip = gc.smoothstep(0.93, 1.0, tv)
    groove = np.exp(-(((av - np.pi) / 0.32) ** 2)) * gc.smoothstep(0.10, 0.18, tv)
    # nub tips (dc_geom: rows at theta = +-0.6, every 2.3 from phase 1.15, t 0.2..0.78)
    ph = ((ln.ravel() + 1.15) % 2.3) - 1.15
    nub = np.zeros_like(tv)
    for side in (-0.6, 0.6):
        dth = (av - side + np.pi) % (2 * np.pi) - np.pi
        nub = np.maximum(nub, np.exp(-(ph / 0.30) ** 2 - (dth * 3.4 / 0.38) ** 2))
    nub *= gc.smoothstep(0.18, 0.22, tv) * gc.smoothstep(0.80, 0.76, tv)
    lining = (vv < 0.105).astype(np.float32)

    def colour(pal):
        skin = pal['belly'] + (pal['back'] - pal['belly']) * (dorsal ** 1.5)[:, None]
        skin = skin * (0.86 + 0.28 * (cid - 0.5) * 0.6 + 0.12 * mott)[:, None]
        skin = skin * (1 - 0.55 * grout)[:, None]
        fl = pal['flesh'] * (0.85 + 0.25 * mott + 0.06 * fine)[:, None]
        fl = fl * (1 - 0.22 * grout * (1 - flesh))[:, None]
        fl = fl + (pal['head'] - fl) * head[:, None] * 0.75
        fl = fl + (pal['tip'] - fl) * tip[:, None] * 0.6
        col = skin + (fl - skin) * flesh[:, None]
        col = col + (pal['groove'] - col) * (groove * 0.8)[:, None]
        col = col + (pal['nub'] - col) * (nub * 0.9)[:, None]
        lin = pal['flesh'] * (0.8 + 0.3 * mott)[:, None]
        col = col * (1 - lining)[:, None] + lin * lining[:, None]
        rgb = (np.clip(col, 0, 1) * 255 + 0.5).astype(np.uint8).reshape(H, W, 3)
        return np.concatenate([rgb, np.full((H, W, 1), 255, np.uint8)], -1)

    regular = colour(dict(belly=np.array([0.56, 0.50, 0.42], np.float32), back=np.array([0.24, 0.21, 0.17], np.float32),
                          flesh=np.array([0.46, 0.12, 0.13], np.float32), head=np.array([0.40, 0.09, 0.17], np.float32),
                          tip=np.array([0.62, 0.24, 0.27], np.float32), groove=np.array([0.30, 0.05, 0.07], np.float32),
                          nub=np.array([0.80, 0.73, 0.58], np.float32)))
    albino = colour(dict(belly=np.array([0.88, 0.85, 0.79], np.float32), back=np.array([0.74, 0.70, 0.64], np.float32),
                         flesh=np.array([0.86, 0.46, 0.49], np.float32), head=np.array([0.80, 0.36, 0.45], np.float32),
                         tip=np.array([0.93, 0.60, 0.62], np.float32), groove=np.array([0.66, 0.24, 0.28], np.float32),
                         nub=np.array([0.95, 0.93, 0.86], np.float32)))
    # normal: scale domes + grout grooves on the skin part, soft mottling on the flesh
    hgt = ((0.55 * dome - 0.5 * grout) * (1 - 0.7 * flesh) + 0.12 * mott + 0.05 * fine
           + 0.6 * nub).reshape(H, W)
    hgt = hgt * (1 - lining.reshape(H, W)) + 0.15 * mott.reshape(H, W) * lining.reshape(H, W)
    gx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) * 3.0
    gy = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)) * 3.0
    n = np.stack([-gx, -gy, np.ones_like(gx)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    nn = np.zeros((H, W, 4), np.uint8)
    nn[..., 0] = (n[..., 0] * 127.5 + 127.5).astype(np.uint8)
    nn[..., 1] = (n[..., 1] * 127.5 + 127.5).astype(np.uint8)
    nn[..., 2] = (n[..., 2] * 127.5 + 127.5).astype(np.uint8)
    nn[..., 3] = 255
    wet = np.clip(flesh + lining + groove, 0, 1)
    ss = np.zeros((H, W, 4), np.uint8)
    ss[..., 0] = ((0.22 + 0.25 * wet - 0.10 * grout).reshape(H, W) * 255).clip(0, 255).astype(np.uint8)
    ss[..., 1] = ((0.42 + 0.40 * wet - 0.15 * grout).reshape(H, W) * 255).clip(0, 255).astype(np.uint8)
    ss[..., 3] = 255
    gl = np.clip(0.55 * grout * (1 - flesh) + 0.8 * groove + 0.25 * flesh * (0.6 + 0.4 * mott) + 0.3 * lining, 0, 1)
    gg = np.zeros((H, W, 4), np.uint8)
    gg[..., 0] = gg[..., 1] = gg[..., 2] = (gl.reshape(H, W) * 255).astype(np.uint8)
    gg[..., 3] = 255
    return regular, albino, nn, ss, gg


if __name__ == '__main__':
    regular, albino, nn, ss, gg = build()
    if len(sys.argv) > 3 and sys.argv[3] == 'anatomy':      # standalone (11-09 Dudu: own paths, no UAP files)
        d = OUT / 'textures/anatomy/creatures'
        names = ('DeathclawPenis_d', 'DeathclawPenisAlbino_d', 'DeathclawPenis_n', 'DeathclawPenis_s',
                 'DeathclawPenis_g')
    else:
        d = OUT / 'textures/actors/deathclaw'
        names = ('PenisRegular_D', 'PenisAlbino_D', 'PenisRegular_N', 'PenisRegular_S', 'penis glowing_G')
    for arr, name, fmt in zip((regular, albino, nn, ss, gg), names,
                              ('BC7_UNORM', 'BC7_UNORM', 'BC5_UNORM', 'BC5_UNORM', 'BC7_UNORM')):
        gc.array_to_dds(arr, fmt, d / f'{name}.dds', WORK)
        print('texture', name)
    prev = pathlib.Path(r'D:\F4Output\creatures\dc\tex')
    Image.fromarray(regular[..., :3]).resize((256, 512)).save(prev / 'penis_regular_preview.png')
    Image.fromarray(albino[..., :3]).resize((256, 512)).save(prev / 'penis_albino_preview.png')
