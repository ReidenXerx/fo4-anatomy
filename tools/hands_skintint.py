"""BodyTalk men's hands -> the vanilla hands' skin material setup, so LooksMenu's lit overlays draw on them
(Complexion, measured in Ivy 2026-11-14; v2 after the shader-type-only v1 was not enough).
BodyTalk 3.8's MaleHands.nif / 1stPersonMaleHands.nif differ from vanilla in what an overlay clone inherits:
  - BSLightingShaderProperty: type 0 (Default), flags1 without Skin_Tint, flags2 Vertex_Colors, ROOT MATERIAL
    "template/OutfitTemplate_Wet.bgsm" (vanilla: SkinTemplate_Wet - only outfit-root overlays ever drew on them),
    other floats (rim/backlight/subsurface)
  - BSShaderTextureSet: empty (vanilla lists basemalehands _d/_n/_s)
  - vertex colours in the vertex format (36 B per vertex; vanilla 32)
v2 takes the VANILLA shader block whole (its string indices and texture-set reference remapped into this file) and
the vanilla texture set, and drops the colour bytes from every vertex record (desc: stride 9->8 words, colour slot
cleared, skin data one word earlier, VA_COLORS off; the data-size field shrinks with it). Positions, normals,
tangents, UVs, skin weights, triangles, segments and the wrist are BodyTalk's byte for byte.
    python -I hands_skintint.py <BodyTalk Characterassets dir> <out Data dir>"""
import pathlib
import struct
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-refit\tools')
import gamedata  # noqa: E402
import nif  # noqa: E402

SRC, OUT = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
DATA = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data')
REL = 'meshes/actors/character/characterassets/'
ARCS = [gamedata.Ba2(a) for a in sorted(DATA.glob('Fallout4 - Meshes*.ba2'))]
VA_COLORS = 1 << 5


def one(n, kind):
    hits = [i for i, t in enumerate(n.types) if t == kind]
    assert len(hits) == 1, (kind, hits)
    o, s = n.offsets[hits[0]]
    return hits[0], bytearray(n.b[o:o + s])


def shader_fields(b):
    """offsets of the references inside a FO4 BSLightingShaderProperty: name, flags, texture set, root material"""
    nextra = struct.unpack_from('<I', b, 8)[0]
    fo = 12 + 4 * nextra + 4                     # after the controller ref: flags1, flags2
    return {'name': 4, 'flags': fo, 'texset': fo + 8 + 16, 'root': fo + 8 + 16 + 4 + 12 + 4}


def drop_colors(n, s):
    """the shape block with the colour bytes removed from every vertex record"""
    o, size = n.offsets[s.index]
    blk = bytearray(n.b[o:o + size])
    d = s.data_at - o
    desc = struct.unpack_from('<Q', blk, d - 18)[0]
    assert desc == s.desc and (desc >> 44) & VA_COLORS
    stride = (desc & 0xF) * 4
    coff = ((desc >> 24) & 0xF) * 4
    nv, nt = s.count, s.triangle_count
    assert struct.unpack_from('<I', blk, d - 4)[0] == nv * stride + nt * 6
    recs = bytearray()
    for i in range(nv):
        r = blk[d + i * stride:d + (i + 1) * stride]
        recs += r[:coff] + r[coff + 4:]
    new_desc = desc
    new_desc = (new_desc & ~0xF) | (stride // 4 - 1)
    new_desc &= ~(0xF << 24)                     # colour slot cleared
    for sh in (28, 32):                          # skin data, eye data: one word earlier when they sat after the colours
        v = (desc >> sh) & 0xF
        if v and v * 4 > coff:
            new_desc = (new_desc & ~(0xF << sh)) | ((v - 1) << sh)
    new_desc &= ~(VA_COLORS << 44)
    head = blk[:d]
    struct.pack_into('<Q', head, d - 18, new_desc)
    struct.pack_into('<I', head, d - 4, nv * (stride - 4) + nt * 6)
    return bytes(head + recs + blk[d + nv * stride:]), new_desc


for name in ('MaleHands.nif', '1stPersonMaleHands.nif'):
    src = next(p for p in SRC.iterdir() if p.name.lower() == name.lower())
    arc = next(a for a in ARCS if REL + name.lower() in a)
    van_path = OUT.parent / f'_vanilla_{name}'
    van_path.parent.mkdir(parents=True, exist_ok=True)
    van_path.write_bytes(arc.read(REL + name.lower()))
    bt, van = nif.Nif(src), nif.Nif(van_path)
    bi, bsh = one(bt, 'BSLightingShaderProperty')
    vi, vsh = one(van, 'BSLightingShaderProperty')
    ti, _ = one(bt, 'BSShaderTextureSet')
    _, vtex = one(van, 'BSShaderTextureSet')
    F = shader_fields(vsh)
    assert struct.unpack_from('<i', bsh, shader_fields(bsh)['texset'])[0] == ti
    strings, add = list(bt.strings), []

    def sidx(text):
        if text in strings:
            return strings.index(text)
        if text in add:
            return len(strings) + add.index(text)
        add.append(text)
        return len(strings) + len(add) - 1

    new_sh = bytearray(vsh)
    for k in ('name', 'root'):
        vidx = struct.unpack_from('<i', vsh, F[k])[0]
        struct.pack_into('<i', new_sh, F[k], sidx(van.string(vidx)) if vidx >= 0 else -1)
    struct.pack_into('<i', new_sh, F['texset'], ti)
    assert struct.unpack_from('<i', vsh, 12 + 4 * struct.unpack_from('<I', vsh, 8)[0])[0] == -1   # no controller
    shape = bt.shapes()[0]
    new_shape, new_desc = drop_colors(bt, shape)
    dst = OUT / 'Meshes/Actors/Character/CharacterAssets' / name
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(bt.with_blocks({bi: bytes(new_sh), ti: bytes(vtex), shape.index: new_shape}, add_strings=add))
    # checks: the vertex data minus colours is BodyTalk's, the shader + textures are vanilla's
    chk = nif.Nif(dst)
    cs = chk.shapes()[0]
    same = (cs.count == shape.count and cs.positions() == shape.positions() and cs.triangles() == shape.triangles()
            and all(cs.uv(i) == shape.uv(i) and cs.skin_weights(i) == shape.skin_weights(i) for i in range(cs.count)))
    _, csh = one(chk, 'BSLightingShaderProperty')
    root = chk.string(struct.unpack_from('<i', csh, F['root'])[0])
    print(f'{name}: desc {shape.desc:#x} -> {new_desc:#x} (vanilla {van.shapes()[0].desc:#x}), stride {cs.stride}, '
          f'root material {root!r}, type {struct.unpack_from("<I", csh, 0)[0]}, textures {bytes(vtex)[4:60]!r}..., '
          f'geometry/uv/weights {"IDENTICAL" if same else "CHANGED"} -> {dst.stat().st_size:,} B')
    van_path.unlink()
