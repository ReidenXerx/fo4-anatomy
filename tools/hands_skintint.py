"""BodyTalk men's hands -> skin-tint shader, so LooksMenu's lit overlays draw on them (Complexion, measured in Ivy
2026-11-14: BodyTalk 3.8's MaleHands.nif / 1stPersonMaleHands.nif carry BSLightingShaderProperty type 0 (Default),
flags1 0x80400203 (no Skin_Tint) and flags2 Vertex_Colors; LooksMenu clones the hands WITH that shader and a skin
.bgsm over it never draws or blinks off. Vanilla hands, the CBBE hands and our Anatomy bodies use type 5.)
Only the shader block changes: type 5, the VANILLA file's flags1/flags2 (Vertex_Colors off: the colours stay in the
vertex data, the shader no longer reads them), and the vanilla block's 16 skin-tint bytes appended (type 5's own
fields; every BodyTalk byte before them keeps its place). Geometry, segments, skin and wrist shape are BodyTalk's
byte for byte. The vanilla file is read from the game's Meshes BA2 for its flags/tail only.
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


def lsp(n):
    """(block index, bytes, flags offset) of the file's single BSLightingShaderProperty"""
    hits = [i for i, t in enumerate(n.types) if t == 'BSLightingShaderProperty']
    assert len(hits) == 1, hits
    o, s = n.offsets[hits[0]]
    b = bytes(n.b[o:o + s])
    nextra = struct.unpack_from('<I', b, 8)[0]
    return hits[0], b, 12 + 4 * nextra + 4


for name in ('MaleHands.nif', '1stPersonMaleHands.nif'):
    src = next(p for p in SRC.iterdir() if p.name.lower() == name.lower())
    arc = next(a for a in ARCS if REL + name.lower() in a)
    van_path = OUT.parent / f'_vanilla_{name}'
    van_path.parent.mkdir(parents=True, exist_ok=True)
    van_path.write_bytes(arc.read(REL + name.lower()))
    bt, van = nif.Nif(src), nif.Nif(van_path)
    bi, bb, bfo = lsp(bt)
    vi, vb, vfo = lsp(van)
    btype = struct.unpack_from('<I', bb, 0)[0]
    vtype = struct.unpack_from('<I', vb, 0)[0]
    assert btype == 0 and vtype == 5, (btype, vtype)
    assert len(vb) - len(bb) == 16 and vb[-16:] == bytes(16) or len(vb) - len(bb) == 16, (len(bb), len(vb))
    assert bfo == vfo
    f1, f2 = struct.unpack_from('<II', vb, vfo)
    new = bytearray(bb)
    struct.pack_into('<I', new, 0, 5)
    struct.pack_into('<II', new, bfo, f1, f2)
    new += vb[len(bb):]
    dst = OUT / 'Meshes/Actors/Character/CharacterAssets' / name
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(bt.with_blocks({bi: bytes(new)}))
    chk = nif.Nif(dst)
    ci, cb, cfo = lsp(chk)
    same_geo = all(chk.shape(s.name).positions() == s.positions() and chk.shape(s.name).triangles() == s.triangles()
                   for s in bt.shapes())
    print(f'{name}: type {struct.unpack_from("<I", cb, 0)[0]}, flags1 {struct.unpack_from("<I", cb, cfo)[0]:#010x}, '
          f'flags2 {struct.unpack_from("<I", cb, cfo + 4)[0]:#06x}, block {len(bb)} -> {len(cb)} B, geometry '
          f'{"identical" if same_geo else "CHANGED"} -> {dst} ({dst.stat().st_size:,} B)')
    van_path.unlink()
