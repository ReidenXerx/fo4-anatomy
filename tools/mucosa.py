"""A procedural wet-mucosa pattern painted into a rect of a DDS, on every mip level, leaving every
other texel byte for byte the same (see genital_texture.py for the Dds reader and encode_blocks()).

Pure: no file IO. Used to fill a rect with a placeholder pattern (colour/normal/specular) instead of
a texture author's paint, e.g. for a preview or a synthetic test fixture.

The rect's v runs down the canal (v0 the entrance), its u around it. folds='along' (the anal canal, A-50):
folds run down the canal. folds='across' (the vaginal canal's rugae, A-54): ridges ring the canal, and at
the entrance row the pattern is exactly base (no folds, specular = base), fading in over ENTRANCE, so a
canal whose first ring sits on a single texel of the vulva shows no line there.
"""
import math

from PIL import Image

from genital_texture import Dds, encode_blocks

RUGAE = 14            # ridges down the vaginal canal (folds='across')
ENTRANCE = 0.15       # of the rect's depth: the rugae, and the specular's step to wet, fade in over it


def _across_pixel(s, t, kind, base, wet):
    """folds='across': (r, g, b, a) for rect coords s (around), t (down, 0 = the entrance row)."""
    tc = max(0.0, min(1.0, t))
    ramp = min(1.0, tc / ENTRANCE)
    phase = 2 * math.pi * RUGAE * tc + 0.6 * math.sin(2 * math.pi * s)     # a little wave, 0 at s = 0 and 1
    if kind == 'colour':
        b = (1.0 + (0.45 - 1.0) * tc) * (1.0 + 0.10 * ramp * math.sin(phase))
        return tuple(max(0, min(255, int(round(base[k] * b)))) for k in range(3)) + (255,)
    if kind == 'normal':
        ny = max(-1.0, min(1.0, 0.35 * ramp * math.cos(phase)))
        nz = math.sqrt(max(0.0, 1.0 - ny * ny))
        return 128, max(0, min(255, int(round(ny * 127.5 + 127.5)))), max(0, min(255, int(round(nz * 127.5 + 127.5)))), 255
    if kind == 'specular':
        w = wet or base
        return (int(round(base[0] + (w[0] - base[0]) * ramp)), int(round(base[1] + (w[1] - base[1]) * ramp)), 0, 255)
    raise ValueError(f'mucosa.paint: unknown kind {kind!r}')


def _pattern_pixel(u, v, kind, base, u0, v0, u1, v1, folds='along', wet=None):
    """(r, g, b, a) 0-255 for one UV sample, per the kind's formula."""
    du, dv = u1 - u0, v1 - v0
    s = (u - u0) / du if du else 0.0
    t = (v - v0) / dv if dv else 0.0
    if folds == 'across':
        return _across_pixel(s, t, kind, base, wet)
    if folds != 'along':
        raise ValueError(f'mucosa.paint: unknown folds {folds!r}')
    tc = max(0.0, min(1.0, t))                          # depth gradient only makes sense inside the rect
    if kind == 'colour':
        depth = 1.0 + (0.45 - 1.0) * tc                 # 1.0 at v0 -> 0.45 at v1
        fold = 1.0 + 0.08 * math.sin(2 * math.pi * 10 * s)
        b = depth * fold
        r = max(0, min(255, int(round(base[0] * b))))
        g = max(0, min(255, int(round(base[1] * b))))
        bl = max(0, min(255, int(round(base[2] * b))))
        return r, g, bl, 255
    if kind == 'normal':
        nx = max(-1.0, min(1.0, 0.35 * math.cos(2 * math.pi * 10 * s)))
        nz = math.sqrt(max(0.0, 1.0 - nx * nx))
        r = max(0, min(255, int(round(nx * 127.5 + 127.5))))
        g = max(0, min(255, int(round(0.0 * 127.5 + 127.5))))
        bl = max(0, min(255, int(round(nz * 127.5 + 127.5))))
        return r, g, bl, 255
    if kind == 'specular':
        return int(base[0]), int(base[1]), 0, 255
    raise ValueError(f'mucosa.paint: unknown kind {kind!r}')


def paint(dds_bytes: bytes, rect: tuple, kind: str, base: tuple, folds: str = 'along', wet: tuple = None) -> bytes:
    """New DDS bytes: identical to dds_bytes everywhere except the texels of rect (0..1 UV, u across, v
    down, v=0 the top row) on every mip level, replaced by a procedural wet-mucosa pattern (kind =
    'colour' | 'normal' | 'specular', base an RGB or (spec_r, spec_g) 0-255 tuple; folds 'along' | 'across', wet the
    specular's (r, g) past the entrance for 'across'). dds_bytes must be a
    format Dds actually reads (not d.fallback): DXT1/DXT3/DXT5/BC5, or uncompressed 24/32-bit."""
    u0, v0, u1, v1 = rect
    d = Dds('mucosa', dds_bytes)
    if d.fallback:
        raise ValueError('mucosa.paint: unsupported DDS format (Dds.fallback)')
    out = bytearray(dds_bytes)
    for L in range(d.mips):
        w, h, bx, by, off = d.level(L)
        x0 = max(0, min(w, math.floor(u0 * w)))
        x1 = max(0, min(w, math.ceil(u1 * w)))
        y0 = max(0, min(h, math.floor(v0 * h)))
        y1 = max(0, min(h, math.ceil(v1 * h)))
        if x1 - x0 < 1 or y1 - y0 < 1:                  # smaller than 1 texel on this level: skip it
            continue
        if d.bw == 1:                                    # uncompressed: texel by texel, no block expansion
            for y in range(y0, y1):
                vy = (y + 0.5) / h
                for x in range(x0, x1):
                    ux = (x + 0.5) / w
                    r, g, b, a = _pattern_pixel(ux, vy, kind, base, u0, v0, u1, v1, folds, wet)
                    at = off + (y * w + x) * d.block
                    out[at + d.raw['R']] = r
                    out[at + d.raw['G']] = g
                    out[at + d.raw['B']] = b
                    if d.block == 4 and 'A' in d.raw:
                        out[at + d.raw['A']] = a
            continue
        # block format: expand to 4-texel block boundaries, re-encode the region, drop its blocks in place.
        # Block INDEX bounds, not pixel bounds: a level under 4 texels wide (the last one or two mips) is
        # still exactly one block (bx==1), so a pixel-multiple-of-4 width would floor to 0 and skip it.
        bx0, bx1 = x0 // 4, min(bx, (x1 + 3) // 4)
        by0, by1 = y0 // 4, min(by, (y1 + 3) // 4)
        px0, py0 = bx0 * 4, by0 * 4
        px1, py1 = min(w, bx1 * 4), min(h, by1 * 4)
        rw, rh = px1 - px0, py1 - py0
        cbx, cby = bx1 - bx0, by1 - by0
        img_mode = 'RGB' if d.pil_format == 'BC5' else 'RGBA'
        region = Image.new(img_mode, (rw, rh))
        pix = region.load()
        for j in range(rh):
            vy = (py0 + j + 0.5) / h
            for i in range(rw):
                ux = (px0 + i + 0.5) / w
                r, g, b, a = _pattern_pixel(ux, vy, kind, base, u0, v0, u1, v1, folds, wet)
                pix[i, j] = (r, g, b) if img_mode == 'RGB' else (r, g, b, a)
        enc = encode_blocks(region, d.pil_format)
        for j in range(cby):
            for i in range(cbx):
                k = j * cbx + i
                dst = off + ((by0 + j) * bx + (bx0 + i)) * d.block
                out[dst:dst + d.block] = enc[k * d.block:(k + 1) * d.block]
    return bytes(out)
