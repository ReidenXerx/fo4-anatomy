"""Servitron's breasts in rubber, to match its rubber abdomen (the owner, 2026-10-08: "we need make appropriate rubber
designed tits like robotic", on a photo of the "Boobs" torso's beige plastic against the black rubber abdomen).

Its "Boobs" torsos draw the breasts with Materials/Servitron/default/PlasticBoobs.bgsm (Servitron's beige
PlasticFemaleBody_d on CBBE's own normal and specular maps); every paint style uses that one file, and nothing else does
(its crotch piece has PlasticCrotch.bgsm). This writes, for a loose override of that file:
  - Materials/Servitron/default/PlasticBoobs.bgsm: the rubber abdomen's own material (default/GITS_plastic.bgsm: its
    gloss, its environment map) pointed at the texture below and at CBBE's body normal map, so nipples and shape keep
    their relief under the shine;
  - Textures/Anatomy/Servitron/RubberBoobs_d.dds: Servitron's breast texture turned to dark rubber (its shading kept as
    a faint variation, nipples a shade darker), every mip, DXT5.

    python tools/servitron_rubber.py <out folder (Data-relative tree)>
"""
import io
import pathlib
import struct
import sys

from PIL import Image, ImageOps

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import gamedata  # noqa: E402
import genital_texture as gt  # noqa: E402

ARCHIVES = pathlib.Path(r'D:\F4Output\servitron\x\main\Data')
SRC_TEX = 'textures\\servitron\\plasticfemalebody_d.dds'
SRC_MAT = 'materials\\servitron\\default\\gits_plastic.bgsm'
OUT_MAT = 'Materials/Servitron/default/PlasticBoobs.bgsm'
OUT_TEX = 'Textures/Anatomy/Servitron/RubberBoobs_d.dds'
RUBBER = (24, 24, 28)        # the abdomen's rubber reads near-black with a cool cast
SPREAD = 0.55                # how much of the source's shading survives (0 flat, 1 all)


def rubber_texture(src_dds):
    img = Image.open(io.BytesIO(src_dds))
    img.load()
    rgba = img.convert('RGBA')
    lum = ImageOps.grayscale(rgba)
    mean = sum(i * n for i, n in enumerate(lum.histogram())) / max(1, lum.width * lum.height)
    lut = [max(0.0, min(2.5, 1.0 + SPREAD * (v - mean) / max(1.0, mean))) for v in range(256)]
    chans = [lum.point(lambda v, c=c: int(max(0, min(255, round(c * lut[v]))))) for c in RUBBER]
    out = Image.merge('RGBA', chans + [rgba.getchannel('A')])
    levels = [out]
    while min(levels[-1].size) > 1:
        w, h = levels[-1].size
        levels.append(levels[-1].resize((max(1, w // 2), max(1, h // 2)), Image.LANCZOS))
    return gt.reencoded(levels, 'DXT5'), out.size


def swap_string(blob, old, new):
    """a BGSM's length-prefixed string (u32 length counting the NUL, then the bytes) replaced"""
    o = old.encode('latin1') + b'\0'
    at = blob.find(struct.pack('<I', len(o)) + o)
    if at < 0:
        raise ValueError(f'{old} is not in the material')
    n = new.encode('latin1') + b'\0'
    return blob[:at] + struct.pack('<I', len(n)) + n + blob[at + 4 + len(o):]


def main():
    out = pathlib.Path(sys.argv[1])
    main_ba2 = gamedata.Ba2(ARCHIVES / 'Servitron - Main.ba2')
    tex_ba2 = gamedata.Ba2(ARCHIVES / 'Servitron - Textures.ba2')
    dds, size = rubber_texture(tex_ba2.read(SRC_TEX))
    mat = main_ba2.read(SRC_MAT)
    mat = swap_string(mat, 'Servitron/GITS_plastic_d.dds', OUT_TEX[len('Textures/'):])
    mat = swap_string(mat, 'Shared/FlatFlat_n.dds', 'Actors/character/basehumanfemale/femalebody_n.dds')
    for rel, data in ((OUT_TEX, dds), (OUT_MAT, mat)):
        (out / rel).parent.mkdir(parents=True, exist_ok=True)
        (out / rel).write_bytes(data)
    print(f'{OUT_MAT} ({len(mat)} bytes, from {SRC_MAT}); {OUT_TEX} {size[0]}x{size[1]} DXT5 ({len(dds)} bytes)')


if __name__ == '__main__':
    main()
