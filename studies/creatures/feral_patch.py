"""'Anatomy Feral Ghouls - Ivy Patch.esp' (light): every ARMA in Ivy's ENABLED plugins (not Fallout4.esm: the main
plugin has those) whose male model is one of our 12 feral body meshes and whose winning female model is not our _F
mesh gets MOD3 = <body>_F.nif (+ every MO2x copied to MO3x). Overrides the WINNING version of each record; every form
id inside is remapped to this plugin's master list (masters in load order). Replaces '... - UAP Withered.esp'.
    python -I feral_patch.py <out Data>"""
import os
import pathlib
import struct
import sys

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-refit\tools')
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import esl  # noqa: E402
from feral_all import arma_with_female, write_plugin  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
OUT = pathlib.Path(sys.argv[1])
DATA = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data')
NAME = 'Anatomy Feral Ghouls - Ivy Patch.esp'
BODIES = {'feralghoulbase', 'feralghoulbasebubble1a', 'feralghoulbasebubble1b', 'feralghoulbasebubble1c',
          'feralghoulbasebubble2a', 'feralghoulbasebubble2b', 'feralghoulbasewithered', 'feralghoulbaseshadow',
          'glowingone', 'putridglowingonebody', 'putridglowingonebodyb', 'putridglowingonebloatedbody'}
FID_SUBS = {b'RNAM', b'NAM0', b'NAM1', b'NAM2', b'NAM3', b'MODL', b'SNDD', b'ONAM'}   # ARMA form-id fields
SKIP = {'anatomy feral ghouls.esp', NAME.lower(), 'anatomy feral ghouls - uap withered.esp'}
txt = pathlib.Path(os.environ['LOCALAPPDATA']) / 'Fallout4' / 'plugins.txt'
order = ['Fallout4.esm', 'DLCRobot.esm', 'DLCworkshop01.esm', 'DLCCoast.esm', 'DLCworkshop02.esm',
         'DLCworkshop03.esm', 'DLCNukaWorld.esm']
order += [l[1:].strip() for l in txt.read_text(encoding='utf-8', errors='replace').splitlines() if l.startswith('*')]
rank = {n.lower(): i for i, n in enumerate(order)}
cased = {n.lower(): n for n in order}


def subs(d):
    o = 0
    while o + 6 <= len(d):
        t, n = d[o:o + 4], struct.unpack_from('<H', d, o + 4)[0]
        yield t, d[o + 6:o + 6 + n]
        o += 6 + n


win = {}                                    # (owner, local id) -> (plugin name, its masters lowercase, flags, body)
for name in order:
    if name.lower() in SKIP or not (DATA / name).exists():
        continue
    try:
        pl = esl.Plugin(DATA / name)
    except Exception:                                                               # noqa: BLE001
        continue
    masters = [x.lower() for x in pl.masters]
    for r in pl.records:
        if r[0] != 'R' or r[2] != 'ARMA':
            continue
        mi = r[3] >> 24
        owner = masters[mi] if mi < len(masters) else name.lower()
        try:
            body = pl.body(r)
        except Exception:                                                           # noqa: BLE001
            continue
        win[(owner, r[3] & 0xFFFFFF)] = (name, masters, r[4], body)
need = []
for (owner, lid), (name, masters, flags, body) in sorted(win.items()):
    d = dict(subs(body))
    mod2 = d.get(b'MOD2', b'').rstrip(b'\0').decode('latin1')
    mod3 = d.get(b'MOD3', b'').rstrip(b'\0').decode('latin1')
    stem = pathlib.PureWindowsPath(mod2).stem.lower()
    if owner == 'fallout4.esm' or stem not in BODIES or mod3.lower().endswith('_f.nif'):
        continue
    need.append((owner, lid, name, masters, flags, body, stem))
# masters: every plugin any remapped form id points into, in load order
used = set()
for owner, lid, name, masters, flags, body, stem in need:
    used.add(owner)
    srcm = masters + [name.lower()]
    for t, v in subs(body):
        if t in FID_SUBS and len(v) == 4:
            mi = struct.unpack('<I', v)[0] >> 24
            used.add(srcm[min(mi, len(srcm) - 1)])
our_masters = sorted(used, key=lambda n: rank.get(n, 10 ** 6))
idx = {n: i for i, n in enumerate(our_masters)}


def remap(fid, srcm):
    if fid == 0:
        return 0
    mi = fid >> 24
    return (idx[srcm[min(mi, len(srcm) - 1)]] << 24) | (fid & 0xFFFFFF)


records = []
for owner, lid, name, masters, flags, body, stem in need:
    srcm = masters + [name.lower()]
    out = b''
    for t, v in subs(body):
        if t in FID_SUBS and len(v) == 4:
            v = struct.pack('<I', remap(struct.unpack('<I', v)[0], srcm))
        out += t + struct.pack('<H', len(v)) + v
    # the female path keeps the vanilla mesh's own capitalisation
    proper = {'feralghoulbase': 'FeralGhoulBase', 'feralghoulbasebubble1a': 'FeralGhoulBaseBubble1a',
              'feralghoulbasebubble1b': 'FeralGhoulBaseBubble1b', 'feralghoulbasebubble1c': 'FeralGhoulBaseBubble1c',
              'feralghoulbasebubble2a': 'FeralGhoulBaseBubble2a', 'feralghoulbasebubble2b': 'FeralGhoulBaseBubble2b',
              'feralghoulbasewithered': 'FeralGhoulBaseWithered', 'feralghoulbaseshadow': 'FeralGhoulBaseShadow',
              'glowingone': 'GlowingOne', 'putridglowingonebody': 'PutridGlowingOneBody',
              'putridglowingonebodyb': 'PutridGlowingOneBodyB',
              'putridglowingonebloatedbody': 'PutridGlowingOneBloatedBody'}[stem]
    body_f = arma_with_female(out, f'Actors\\FeralGhoul\\CharacterAssets\\{proper}_F.nif')
    records.append(((idx[owner] << 24) | lid, flags, body_f))
    edid = dict(subs(body)).get(b'EDID', b'').rstrip(b'\0').decode('latin1')
    print(f'  {cased.get(owner, owner)}:{lid:06X} {edid:40s} (winner {name}) -> {proper}_F.nif')
write_plugin(OUT / NAME, [cased.get(n, n) for n in our_masters], records)
print(NAME, len(records), 'records, masters', [cased.get(n, n) for n in our_masters])
