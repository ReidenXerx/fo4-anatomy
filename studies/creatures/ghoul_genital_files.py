"""The files that put the ghoul genital texture on ghouls only (no engine change, no edit to anyone's plugin):
  meshes/actors/character/characterassets/FemaleBodyGhoul.nif   copy of the deployed FemaleBody.nif whose genital
                                                                  shape names AnatomyGenitalsGhoul.bgsm
  materials/anatomy/AnatomyGenitalsGhoul.bgsm                    AnatomyGenitals.bgsm with Anatomy\\Ghoul\\ textures
  Anatomy Ghoul Genitals.esp (light)                            NakedGhoulTorso (Fallout4.esm 0EAFB9) override: female
                                                                  third-person model -> FemaleBodyGhoul.nif
Nothing else in Ivy overrides 0EAFB9 (list_overlaps.py, 11-09). Output D:\\F4Output\\ghoulskin\\out\\Data.
    python -I ghoul_genital_files.py"""
import pathlib
import re
import struct
import sys

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-refit\tools')
import esl  # noqa: E402
import nif  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
DATA = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data')
OUT = pathlib.Path(r'D:\F4Output\ghoulskin\out\Data')
CA = 'meshes/actors/character/characterassets/'
OLD_MAT = 'Materials\\Anatomy\\AnatomyGenitals.bgsm'
NEW_MAT = 'Materials\\Anatomy\\AnatomyGenitalsGhoul.bgsm'
PLUGIN = 'Anatomy Ghoul Genitals.esp'
ARMA_ID = 0x0EAFB9


def bgsm():
    b = (DATA / 'Materials/Anatomy/AnatomyGenitals.bgsm').read_bytes()
    out, o, n = bytearray(), 0, 0
    # length-prefixed strings (uint32 length incl. the NUL); retarget Anatomy\FemaleBody_* to Anatomy\Ghoul\
    for m in re.finditer(rb'(?i)anatomy[\\/]femalebody_[dns]\.dds\0', b):
        # walk back to the length prefix: the string starts right after it
        s0 = m.start()
        while s0 > 0 and b[s0 - 1] >= 32:
            s0 -= 1
        ln = struct.unpack_from('<I', b, s0 - 4)[0]
        old = b[s0:s0 + ln]
        if not old.endswith(b'\0') or m.end() != s0 + ln:
            raise SystemExit(f'unexpected BGSM layout at {s0}: {old!r}')
        new = re.sub(rb'(?i)(anatomy([\\/]))(femalebody_)', rb'\1Ghoul\2\3', old)
        out += b[o:s0 - 4] + struct.pack('<I', len(new)) + new
        o = s0 + ln
        n += 1
    out += b[o:]
    if n != 3:
        raise SystemExit(f'expected 3 texture strings, found {n}')
    dst = OUT / 'materials/anatomy/AnatomyGenitalsGhoul.bgsm'
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(bytes(out))
    print('bgsm:', [s.decode() for s in re.findall(rb'[\x20-\x7e]{8,}', bytes(out))])


def mesh():
    m = nif.Nif(DATA / CA / 'FemaleBody.nif')
    if OLD_MAT not in m.strings:
        raise SystemExit(f'{OLD_MAT} not in the body string table: {[s for s in m.strings if "bgsm" in s.lower()]}')
    dst = OUT / CA / 'FemaleBodyGhoul.nif'
    dst.parent.mkdir(parents=True, exist_ok=True)
    m.save_renamed(dst, {OLD_MAT: NEW_MAT})
    back = nif.Nif(dst)
    print('nif: strings with bgsm/tri:', [s for s in back.strings if re.search(r'(?i)bgsm|\.tri', s)],
          '| shapes', [s.name for s in back.shapes()])


def plugin():
    fo4 = esl.Plugin(DATA / 'Fallout4.esm')
    rec = next(r for r in fo4.records if r[0] == 'R' and r[2] == 'ARMA' and r[3] == ARMA_ID)
    body = fo4.body(rec)
    raw = bytearray()
    o, hit = 0, 0
    while o < len(body):
        t, n = body[o:o + 4], struct.unpack_from('<H', body, o + 4)[0]
        v = body[o + 6:o + 6 + n]
        if t == b'MOD3':
            v = b'Actors\\Character\\CharacterAssets\\FemaleBodyGhoul.nif\0'
            hit += 1
        raw += t + struct.pack('<H', len(v)) + v
        o += 6 + n
    if hit != 1:
        raise SystemExit('MOD3 not found once')
    # record header: keep the master's flags (uncompressed here), form version 131
    flags = rec[4] & ~0x00040000
    hdr = b'ARMA' + struct.pack('<III', len(raw), flags, ARMA_ID) + struct.pack('<IHH', 0, 131, 0)
    grup = b'GRUP' + struct.pack('<I', 24 + len(hdr) + len(raw)) + b'ARMA' + struct.pack('<I', 0) + \
        struct.pack('<IHH', 0, 0, 0) + hdr + bytes(raw)

    def field(t, v):
        return t + struct.pack('<H', len(v)) + v
    tes4 = field(b'HEDR', struct.pack('<fiI', 1.0, 1, 0x800)) + field(b'CNAM', b'Anatomy\0') + \
        field(b'MAST', b'Fallout4.esm\0') + field(b'DATA', struct.pack('<Q', 0))
    out = b'TES4' + struct.pack('<III', len(tes4), esl.LIGHT, 0) + struct.pack('<IHH', 0, 131, 0) + tes4 + grup
    (OUT / PLUGIN).write_bytes(out)
    back = esl.Plugin(OUT / PLUGIN)
    r = next(r for r in back.records if r[0] == 'R')
    print('plugin:', PLUGIN, r[2], f'{r[3]:08X}', 'flags', hex(r[4]), 'MOD3' in back.body(r).decode('latin1'),
          re.findall(rb'[\x20-\x7e]{10,}', back.body(r)))


if __name__ == '__main__':
    bgsm()
    mesh()
    plugin()
