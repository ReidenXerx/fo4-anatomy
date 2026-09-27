"""The genitals' own small textures (A-48): an aligned tile of the skin maps instead of three full-size copies.

Only the genitals' shape samples Textures\\Anatomy\\*, and only on Nahka's island: under 1% of the skin's texels. Yet
the builder wrote a full copy of each map (at 4K: 10.7 + 21.3 + 21.3 MB of VRAM whenever a woman's genitals render).
The owner, 2026-09-28: "Lets try! It would be handy on my steam deck".

So the three maps become the one aligned tile of the skin's UV grid that holds the genitals' UVs (with a margin), and
the genitals' shape samples that tile:
  - the tile is a power-of-two fraction of the texture (1/2, 1/4, 1/8...) at a multiple of its own size. Every mip
    level's crop is then a whole number of 4x4 blocks, copied byte for byte: the same texels as the full copy, no
    re-encode, at any skin size (2K, 4K).
  - the UVs are remapped u' = (u - u0) / t. For a power of two t that is exact in half floats, so each vertex samples
    the very texel it sampled before (checked: remapped back, every UV equals the original).
  - chosen from the genitals' own UVs, so it works for any skin; if no tile smaller than the whole texture holds them,
    nothing changes.
"""
import math
import struct

MARGIN = 1 / 256          # beyond the island's UVs: 16 texels at 4K, for filtering and the first mips
SHAPE = 'AnatomyGenitals'
LAST = (0.0, 0.0, 1.0)    # the tile the last apply() chose


def tile_for(uvs, margin=MARGIN):
    """(u0, v0, t): the smallest aligned power-of-two tile holding every UV plus the margin; t == 1 means none."""
    us, vs = [u for u, _ in uvs], [v for _, v in uvs]
    lo_u, hi_u, lo_v, hi_v = min(us) - margin, max(us) + margin, min(vs) - margin, max(vs) + margin
    if lo_u < 0 or lo_v < 0 or hi_u > 1 or hi_v > 1:
        return 0.0, 0.0, 1.0
    t = 1.0
    best = (0.0, 0.0, 1.0)
    while t >= 1 / 64:
        u0, v0 = math.floor(lo_u / t) * t, math.floor(lo_v / t) * t
        if hi_u <= u0 + t and hi_v <= v0 + t:
            best = (u0, v0, t)
        else:
            break
        t /= 2
    return best


def remap_uvs(nif_path):
    """Point the genitals' shape at the tile; returns the tile (u0, v0, t). Checks every UV maps back exactly."""
    import nif
    n = nif.Nif(nif_path)
    s = n.shape(SHAPE)
    uvs = [s.uv(i) for i in range(s.count)]
    u0, v0, t = tile_for(uvs)
    if t == 1.0:
        return u0, v0, t
    for i, (u, v) in enumerate(uvs):
        struct.pack_into('<2e', n.b, s.data_at + i * s.stride + s.uv_at, (u - u0) / t, (v - v0) / t)
    n.save(nif_path)
    back = nif.Nif(nif_path).shape(SHAPE)
    bad = sum(1 for i, (u, v) in enumerate(uvs) if (lambda a: (a[0] * t + u0, a[1] * t + v0))(back.uv(i)) != (u, v))
    if bad:
        raise SystemExit(f'atlas: {bad} genital UVs do not map back to the texel they sampled')
    return u0, v0, t


def crop(data, u0, v0, t):
    """The tile of a DDS (any format genital_texture.Dds reads), every mip level, as a DDS of the same format."""
    import genital_texture as gt
    d = gt.Dds('tile', data)
    if d.fallback:
        raise SystemExit('atlas: a re-encoded map should already be in a format the builder writes')
    W, H = d.w, d.h
    T = int(W * t)
    if T * 1.0 != W * t or int(H * t) != T:
        raise SystemExit(f'atlas: a {W}x{H} texture has no whole {t} tile')
    x0, y0 = int(W * u0), int(H * v0)
    levels = 0
    body = bytearray()
    for L in range(d.mips):
        w, h, bx, by, off = d.level(L)
        tw = max(1, T >> L)
        if bx == 0 or tw < 1:
            break
        unit = 1 if d.bw == 1 else 4
        cx, cy = (x0 >> L) // unit, (y0 >> L) // unit
        cw = max(1, (tw + unit - 1) // unit)
        for r in range(cw):
            a = off + ((cy + r) * bx + cx) * d.block
            body += d.b[a:a + cw * d.block]
        levels += 1
        if tw == 1:
            break
    head = bytearray(d.b[:d.data_off])
    struct.pack_into('<2I', head, 12, T, T)
    flags = struct.unpack_from('<I', head, 8)[0]
    if d.bw == 1:
        struct.pack_into('<I', head, 20, T * d.block)                                   # pitch
        flags = (flags | 0x8) & ~0x80000
    else:
        struct.pack_into('<I', head, 20, max(1, T // 4) ** 2 * d.block)                  # linear size
        flags = (flags | 0x80000) & ~0x8
    struct.pack_into('<I', head, 8, flags | 0x20000)
    struct.pack_into('<I', head, 28, levels)
    return bytes(head) + bytes(body)


def apply(nif_path, texture_dir, names=('FemaleBody_d.dds', 'FemaleBody_n.dds', 'FemaleBody_s.dds')):
    """The whole step: remap the genitals' UVs in the built Anatomy.nif, crop the three maps; a report line."""
    import io
    from PIL import Image
    global LAST
    u0, v0, t = remap_uvs(nif_path)
    LAST = (u0, v0, t)
    if t == 1.0:
        return 'atlas: the genitals\' UVs fill no smaller tile; the full-size maps stay'
    before = after = 0
    for n in names:
        p = texture_dir / n
        full = p.read_bytes()
        tile = crop(full, u0, v0, t)
        # the tile's top level must be the full map's texels there (decoded, both through Pillow)
        a = Image.open(io.BytesIO(full)).convert('RGBA')
        b = Image.open(io.BytesIO(tile)).convert('RGBA')
        x0, y0 = int(a.size[0] * u0), int(a.size[1] * v0)
        if a.crop((x0, y0, x0 + b.size[0], y0 + b.size[1])).tobytes() != b.tobytes():
            raise SystemExit(f'atlas: {n}\'s tile does not decode to the full map\'s texels')
        p.write_bytes(tile)
        before, after = before + len(full), after + len(tile)
    return (f'atlas: the genitals sample a {t:g} tile at ({u0:g}, {v0:g}); their three maps '
            f'{before / 2**20:.1f} MB -> {after / 2**20:.1f} MB, texel for texel the same (A-48)')
