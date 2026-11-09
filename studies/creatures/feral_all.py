"""Feral ghoul genitals, every variant (owner-approved 11-09):
  1 vanilla feral body meshes out of Fallout4 - Meshes.ba2
  2 Blender (feral_build.py): male = our stump on the SAME path (wins over UAP by load rule), female = <name>_F.nif
  3 restore the shape transforms of every original shape byte for byte (PyNifly rewrites some, e.g. SplineHair)
  4 plugins: 'Anatomy Feral Ghouls.esp' (light; the 12 vanilla feral body ARMAs get a female model <name>_F.nif,
    every MO2x field copied to MO3x), 'Anatomy Feral Ghouls - UAP Withered.esp' (light; UAP ErectionFix's 4 withered
    body ARMAs, master ErectionFix_SilverPerv.esp)
    python -I feral_all.py [--only BaseName]"""
import argparse
import json
import pathlib
import struct
import subprocess
import sys

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-refit\tools')
import esl  # noqa: E402
import gamedata  # noqa: E402
import nif  # noqa: E402

DATA = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data')
UAP = pathlib.Path(r'D:\Vortex\fallout4\mods\1387286231_UAPv2.6.64-1+2')
ROOT = pathlib.Path(r'D:\F4Output\creatures\feral')
OUT = ROOT / __import__('os').environ.get('FERAL_OUT', 'out2') / 'Data'    # a fresh dir per rebuild
REL = 'meshes/actors/feralghoul/characterassets/'
BLENDER = r'D:\F4Tools\blender-5.1.2-windows-x64\blender.exe'
HERE = pathlib.Path(__file__).resolve().parent
# vanilla feral body ARMAs (Fallout4.esm) -> mesh name
ARMAS = {0x06B4ED: 'FeralGhoulBase', 0x0B03B1: 'FeralGhoulBaseBubble1a', 0x0B03B0: 'FeralGhoulBaseBubble1b',
         0x0B0393: 'FeralGhoulBaseBubble1c', 0x0B0392: 'FeralGhoulBaseBubble2a', 0x0B039B: 'FeralGhoulBaseBubble2b',
         0x0A073E: 'FeralGhoulBaseWithered', 0x0A0749: 'FeralGhoulBaseShadow', 0x020BCB: 'GlowingOne',
         0x0A96B9: 'PutridGlowingOneBody', 0x0A96B8: 'PutridGlowingOneBodyB', 0x0A96B7: 'PutridGlowingOneBloatedBody'}
UAP_WITHERED = [0x000801, 0x000806, 0x00080B, 0x000810]          # ErectionFix_SilverPerv.esp body ARMAs


def extract():
    a = gamedata.Ba2(DATA / 'Fallout4 - Meshes.ba2')
    van = ROOT / 'vanilla'
    van.mkdir(parents=True, exist_ok=True)
    for name in sorted(set(ARMAS.values())):
        rel = REL + name.lower() + '.nif'
        if rel not in a:
            raise SystemExit(f'{rel} not in Fallout4 - Meshes.ba2')
        (van / f'{name}.nif').write_bytes(a.read(rel))
    return van


def xf_offset(m, shape):
    o, _ = m.offsets[shape.index]
    c = nif.Cursor(m.b, o)
    c.take('i')
    for _ in range(c.take('I')):
        c.take('i')
    c.take('i')
    c.take('I')
    return c.o                                                     # translation (3f), rotation (9f), scale (f)


def restore_transforms(src, dst):
    s, d = nif.Nif(src), nif.Nif(dst)
    want = {sh.name: bytes(s.b[xf_offset(s, sh):xf_offset(s, sh) + 52]) for sh in s.shapes()}
    fixed = []
    for sh in d.shapes():
        if sh.name in want:
            o = xf_offset(d, sh)
            if bytes(d.b[o:o + 52]) != want[sh.name]:
                d.b[o:o + 52] = want[sh.name]
                fixed.append(sh.name)
    d.save(dst)
    return fixed


def arma_with_female(body, female_path):
    """Subrecords of an ARMA with MOD3 (+ every MO2x as MO3x) set to the female model; existing MOD3/MO3x dropped."""
    subs = []
    o = 0
    while o < len(body):
        t, n = body[o:o + 4], struct.unpack_from('<H', body, o + 4)[0]
        subs.append((t, body[o + 6:o + 6 + n]))
        o += 6 + n
    subs = [(t, v) for t, v in subs if not (t == b'MOD3' or t[:3] == b'MO3')]
    last2 = max(i for i, (t, _) in enumerate(subs) if t == b'MOD2' or t[:3] == b'MO2')
    female = [(b'MOD3', female_path.encode() + b'\0')] + [(b'MO3' + t[3:], v) for t, v in subs if t[:3] == b'MO2']
    subs = subs[:last2 + 1] + female + subs[last2 + 1:]
    return b''.join(t + struct.pack('<H', len(v)) + v for t, v in subs)


def write_plugin(path, masters, records):
    def field(t, v):
        return t + struct.pack('<H', len(v)) + v
    grup = b''
    for fid, flags, body in records:
        grup += b'ARMA' + struct.pack('<III', len(body), flags & ~0x00040000, fid) + struct.pack('<IHH', 0, 131, 0) + body
    grup = b'GRUP' + struct.pack('<I', 24 + len(grup)) + b'ARMA' + struct.pack('<I', 0) + struct.pack('<IHH', 0, 0, 0) + grup
    hdr = field(b'HEDR', struct.pack('<fiI', 1.0, len(records), 0x800)) + field(b'CNAM', b'Anatomy\0')
    for m in masters:
        hdr += field(b'MAST', m.encode() + b'\0') + field(b'DATA', struct.pack('<Q', 0))
    path.write_bytes(b'TES4' + struct.pack('<III', len(hdr), esl.LIGHT, 0) + struct.pack('<IHH', 0, 131, 0) + hdr + grup)


def plugins():
    fo4 = esl.Plugin(DATA / 'Fallout4.esm')
    recs = []
    for r in fo4.records:
        if r[0] == 'R' and r[2] == 'ARMA' and r[3] in ARMAS:
            fpath = f'Actors\\FeralGhoul\\CharacterAssets\\{ARMAS[r[3]]}_F.nif'
            recs.append((r[3], r[4], arma_with_female(fo4.body(r), fpath)))
    if len(recs) != len(ARMAS):
        raise SystemExit(f'found {len(recs)} of {len(ARMAS)} feral ARMAs')
    write_plugin(OUT / 'Anatomy Feral Ghouls.esp', ['Fallout4.esm'], recs)
    ef = esl.Plugin(UAP / 'ErectionFix_SilverPerv.esp')
    idx = len(ef.masters) if hasattr(ef, 'masters') else 2           # its own records' master index
    recs = []
    for r in ef.records:
        if r[0] == 'R' and r[2] == 'ARMA' and (r[3] & 0xFFFFFF) in UAP_WITHERED:
            fpath = 'Actors\\FeralGhoul\\CharacterAssets\\FeralGhoulBaseWithered_F.nif'
            # in our plugin ErectionFix is master index 2 (after Fallout4.esm, DLCNukaWorld.esm)
            recs.append(((2 << 24) | (r[3] & 0xFFFFFF), r[4], arma_with_female(ef.body(r), fpath)))
    write_plugin(OUT / 'Anatomy Feral Ghouls - UAP Withered.esp',
                 ['Fallout4.esm', 'DLCNukaWorld.esm', 'ErectionFix_SilverPerv.esp'], recs)
    return len(recs), idx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='')
    a = ap.parse_args()
    van = extract()
    names = sorted(set(ARMAS.values()))
    if a.only:
        names = [n for n in names if n == a.only]
    jobs = []
    for n in names:
        jobs += ['M', str(van / f'{n}.nif'), str(OUT / REL / f'{n}.nif'),
                 'F', str(van / f'{n}.nif'), str(OUT / REL / f'{n}_F.nif')]
    rep = ROOT / 'report.json'
    r = subprocess.run([BLENDER, '-b', '-P', str(HERE / 'feral_build.py'), '--', str(rep)] + jobs,
                       capture_output=True, text=True, timeout=3600)
    built = [l for l in r.stdout.splitlines() if l.startswith('BUILT')]
    errs = [l for l in (r.stdout + r.stderr).splitlines() if 'Traceback' in l or 'Error:' in l and 'freed' not in l]
    print(f'{len(built)} built', errs[:5])
    report = json.loads(rep.read_text())
    for dst, info in report.items():
        src = van / (pathlib.Path(dst).stem.removesuffix('_F') + '.nif')
        fixed = restore_transforms(src, dst)
        print(pathlib.Path(dst).name, info.get('gap'), info.get('nipple_z'), info.get('error', ''), 'xf restored', fixed)
    print('plugins', plugins())


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    main()
