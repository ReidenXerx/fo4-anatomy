"""Fallout 4 material files (.bgsm, version 2): read the texture paths, write a copy with some replaced.

The layout up to the textures (BaseMaterialFile, then BGSM), measured on the owner's skin material
(CBBE Holy Fix's basehumanFemaleskin.bgsm: diffuse at byte 63):

    char[4] "BGSM", uint32 version (2), uint32 tile flags, float U offset, V offset, U scale, V scale,
    float alpha, bool alpha blend + uint32 source blend + uint32 destination blend,
    uint8 alpha test ref, 11 bools (alpha test, z-write, z-test, SSR, wetness SSR, decal, two-sided,
    decal no fade, non-occluder, refraction, refraction falloff), float refraction power,
    bool environment mapping, float environment mask scale, bool grayscale-to-palette colour
    = 63 bytes; then 9 textures, each uint32 length (with the NUL) + chars + NUL:
    diffuse, normal, smooth/spec, greyscale, envmap, glow, inner layer, wrinkles, displacement.
Everything after the textures is copied as it is. Paths are relative to Data/Textures.

    python tools/bgsm.py <file.bgsm>       # print the texture paths
"""
import pathlib
import struct
import sys

HEAD = 63
NAMES = ('diffuse', 'normal', 'smoothspec', 'greyscale', 'envmap', 'glow', 'innerlayer', 'wrinkles',
         'displacement')


def textures(data):
    """The 9 texture paths and the byte offset where the textures end."""
    if data[:4] != b'BGSM':
        raise ValueError('not a BGSM file')
    version = struct.unpack_from('<I', data, 4)[0]
    if version != 2:
        raise ValueError(f'BGSM version {version}: only version 2 (Fallout 4) is read here')
    o, out = HEAD, []
    for _ in NAMES:
        (n,) = struct.unpack_from('<I', data, o)
        if n < 1 or o + 4 + n > len(data) or data[o + 4 + n - 1] != 0:
            raise ValueError(f'texture string at {o} is not a NUL-terminated string')
        out.append(data[o + 4:o + 4 + n - 1].decode('latin1'))
        o += 4 + n
    return out, o


def with_textures(data, replace):
    """A copy with textures replaced ({slot index or name: path}); every other byte is kept."""
    paths, end = textures(data)
    for key, value in replace.items():
        paths[NAMES.index(key) if isinstance(key, str) else key] = value
    body = b''.join(struct.pack('<I', len(p) + 1) + p.encode('latin1') + b'\0' for p in paths)
    return data[:HEAD] + body + data[end:]


if __name__ == '__main__':
    paths, _ = textures(pathlib.Path(sys.argv[1]).read_bytes())
    for name, path in zip(NAMES, paths):
        print(f'{name:13} {path!r}')
