"""Female creature plugins (Dudu 11-10), one light ESP + RobCo ini per Immersive mod:
  - ARMA overrides: MOD3 (the female model) -> our <Name>_F.nif on every skin whose male model we built
    (MO2S copied to MO3S where the vanilla addon had no female model, so glowing swaps still apply)
  - female twins of every NPC_ of the mod's races that sits in a leveled actor list: the twin is a copy with the
    female flag; when the actor takes its traits (= sex) from a template, the twin points at a female twin of that
    template (an NPC_ twin, or a NEW LVLN whose entries are twins)
  - RobCo leveledList ini: each twin added to every list holding its male, same level + count (= half the spawns
    female). Lists flagged "use all" are skipped (they would spawn both).
  - Broodmother (EncMolerat04 + legendaries): the queen is always female - a female-flag override of those records.
    python -I fem_plugin.py <out dir> [mod ...]"""
import pathlib
import struct
import sys

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-refit\tools')
import esl  # noqa: E402

DATA = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data')
F = 'Actors\\'
MODS = {  # plugin stem: (masters, races (master-relative ids in the LAST master's load), female models, overrides)
    'Dogs': (['Fallout4.esm'], [0x187AF9, 0x03578A, 0x090C33],
             {'actors\\dogmeat\\characterassets\\raiderdog.nif': F + 'Dogmeat\\CharacterAssets\\RaiderDog_F.nif',
              'actors\\viciousdog\\viciousdog.nif': F + 'ViciousDog\\ViciousDog_F.nif',
              'actors\\viciousdog\\viciousdogpackleader.nif': F + 'ViciousDog\\ViciousDogPackLeader_F.nif',
              'actors\\fevhound\\characterassets\\fevhound.nif': F + 'FEVHound\\CharacterAssets\\FEVHound_F.nif'},
             []),
    'Wolves': (['Fallout4.esm', 'DLCCoast.esm'], [(1, 0x03D077)],
               {'actors\\dlc03\\mutatedwolf\\wolfalpha.nif': F + 'DLC03\\MutatedWolf\\WolfAlpha_F.nif',
                'actors\\dlc03\\mutatedwolf\\wolffuzzy.nif': F + 'DLC03\\MutatedWolf\\WolfFuzzy_F.nif'}, []),
    'Yao Guai': (['Fallout4.esm'], [0x0A0F2F],
                 {'actors\\yaoguai\\characterassets\\yaoguai.nif': F + 'YaoGuai\\CharacterAssets\\YaoGuai_F.nif',
                  'actors\\yaoguai\\characterassets\\yaoguaishaggy.nif':
                      F + 'YaoGuai\\CharacterAssets\\YaoGuaiShaggy_F.nif'}, []),
    'Radstags': (['Fallout4.esm'], [],      # vanilla already spawns does; only their model changes
                 {'actors\\radstag\\characterassets\\radstagdoe.nif@female':
                      F + 'RadStag\\CharacterAssets\\RadStagDoe_F.nif'}, []),
    'Mole Rats': (['Fallout4.esm'], [0x01D810],
                  {'actors\\molerat\\characterassets\\molerat.nif': F + 'Molerat\\CharacterAssets\\Molerat_F.nif',
                   'actors\\molerat\\characterassets\\molerat01.nif': F + 'Molerat\\CharacterAssets\\Molerat01_F.nif',
                   'actors\\molerat\\characterassets\\molerat02.nif': F + 'Molerat\\CharacterAssets\\Molerat02_F.nif',
                   'actors\\molerat\\characterassets\\broodmother.nif':
                       F + 'Molerat\\CharacterAssets\\Broodmother_F.nif'},
                  [0x1832F8, 0x1846D9, 0x2499FB]),      # Broodmother: always female
}
MO_T = bytes([4] + [0] * 19)                            # model info header, no texture hashes


def subs(d):
    o, res = 0, []
    while o + 6 <= len(d):
        t, n = d[o:o + 4], struct.unpack_from('<H', d, o + 4)[0]
        res.append([t, d[o + 6:o + 6 + n]])
        o += 6 + n
    return res


def pack(sl):
    return b''.join(t + struct.pack('<H', len(v)) + v for t, v in sl)


def get(sl, t):
    return next((v for k, v in sl if k == t), None)


def zs(s):
    return s.encode('latin1') + b'\0'


class Load:
    """the masters in order; every form id kept in THIS plugin's numbering (master index = position here)"""

    def __init__(self, masters):
        self.masters = masters
        self.rec = {}                                   # fid -> (type, flags, subrecords)  (last master wins)
        for i, m in enumerate(masters):
            p = esl.Plugin(DATA / m)
            remap = {j: masters.index(pm) for j, pm in enumerate(p.masters)}
            remap[p.own] = i
            for r in p.records:
                if r[0] != 'R' or r[2] not in ('NPC_', 'LVLN', 'ARMA', 'ARMO'):
                    continue
                fid = (remap[r[3] >> 24] << 24) | (r[3] & 0xFFFFFF)
                self.rec[fid] = (r[2], r[4] & ~0x40000, self.fix(subs(p.body(r)), remap, r[2]))

    @staticmethod
    def fix(sl, remap, typ):
        """re-number the form ids we follow (templates, races, list entries) into this load's numbering"""
        def f(x):
            return (remap.get(x >> 24, x >> 24) << 24) | (x & 0xFFFFFF) if x else 0
        for s in sl:
            t, v = s
            if t in (b'TPLT', b'RNAM', b'WNAM') and len(v) == 4:
                s[1] = struct.pack('<I', f(struct.unpack('<I', v)[0]))
            elif t == b'TPTA':
                s[1] = struct.pack(f'<{len(v) // 4}I', *(f(x) for x in struct.unpack(f'<{len(v) // 4}I', v)))
            elif t == b'LVLO':
                lv, u, fid, cnt, cn, u2 = struct.unpack_from('<HHIHBB', v, 0)
                s[1] = struct.pack('<HHIHBB', lv, u, f(fid), cnt, cn, u2) + v[12:]
            elif t == b'MODL' and typ == 'ARMO':
                s[1] = struct.pack('<I', f(struct.unpack('<I', v)[0]))
        return sl


def u32(v):
    return struct.unpack('<I', v)[0]


def build(stem, masters, races, models, always_f):
    L = Load(masters)
    own = len(masters)
    races = {r if isinstance(r, int) else (r[0] << 24) | r[1] for r in races}
    nid = [0x800]
    out = {'NPC_': [], 'LVLN': [], 'ARMA': []}
    twin = {}
    report = []

    def new_id():
        x = (own << 24) | nid[0]
        nid[0] += 1
        return x

    def traits_src(sl):
        acbs = get(sl, b'ACBS')
        if not struct.unpack_from('<H', acbs, 14)[0] & 1:
            return None
        tpta = get(sl, b'TPTA')
        return u32(tpta[:4]) if tpta and u32(tpta[:4]) else u32(get(sl, b'TPLT'))

    def female(fid, depth=0):
        """the female twin of an NPC_ or LVLN (None when it is already female / unknown)"""
        if fid in twin:
            return twin[fid]
        if fid not in L.rec or depth > 12:
            return None
        typ, flags, sl = L.rec[fid]
        if typ == 'NPC_':
            acbs = get(sl, b'ACBS')
            src = traits_src(sl)
            if src is None and struct.unpack_from('<I', acbs, 0)[0] & 1:
                return None                                  # already female
            new = [list(s) for s in sl]
            for s in new:
                if s[0] == b'EDID':
                    s[1] = zs(s[1].rstrip(b'\0').decode('latin1') + '_AnatomyF')
            if src is None:
                for s in new:
                    if s[0] == b'ACBS':
                        s[1] = struct.pack('<I', u32(s[1][:4]) | 1) + s[1][4:]
            else:
                ft = female(src, depth + 1)
                if ft is None:
                    return None
                for s in new:
                    if s[0] == b'TPLT' and u32(s[1]) == src:
                        s[1] = struct.pack('<I', ft)
                    elif s[0] == b'TPTA' and u32(s[1][:4]) == src:
                        s[1] = struct.pack('<I', ft) + s[1][4:]
            x = new_id()
            twin[fid] = x
            out['NPC_'].append((x, flags, pack(new)))
            return x
        if typ == 'LVLN':
            x = new_id()
            twin[fid] = x                                    # (set first: lists can nest)
            new = [list(s) for s in sl]
            n = 0
            for s in new:
                if s[0] == b'EDID':
                    s[1] = zs(s[1].rstrip(b'\0').decode('latin1') + '_AnatomyF')
                elif s[0] == b'LVLO':
                    lv, u, e, cnt, cn, u2 = struct.unpack_from('<HHIHBB', s[1], 0)
                    fe = female(e, depth + 1)
                    if fe:
                        s[1] = struct.pack('<HHIHBB', lv, u, fe, cnt, cn, u2) + s[1][12:]
                        n += 1
            if not n:
                del twin[fid]
                nid[0] -= 1
                return None
            out['LVLN'].append((x, flags, pack(new)))
            return x
        return None

    # ---- female twins + RobCo lines
    lists = {f: r for f, r in L.rec.items() if r[0] == 'LVLN'}
    lines = []
    for lid, (_, _, sl) in sorted(lists.items()):
        edid = get(sl, b'EDID').rstrip(b'\0').decode('latin1')
        use_all = (get(sl, b'LVLF') or b'\0')[0] & 0x04
        for s in sl:
            if s[0] != b'LVLO':
                continue
            lv, _, e, cnt, cn, _ = struct.unpack_from('<HHIHBB', s[1], 0)
            if e not in L.rec or L.rec[e][0] != 'NPC_':
                continue
            if u32(get(L.rec[e][2], b'RNAM') or b'\0\0\0\0') not in races or e in always_f:
                continue
            if use_all:
                report.append(f'skip use-all list {edid}')
                continue
            fe = female(e)
            if fe is None:
                continue
            m = masters[lid >> 24]
            lines.append(f'// {edid}\nfilterByLLs={m}|{lid & 0xFFFFFF:06X}:addToLLs={stem_plugin(stem)}|'
                         f'{fe & 0xFFF:03X}~{lv}~{cnt}~{cn}')
    # ---- the Broodmother: always female (override)
    for fid in always_f:
        typ, flags, sl = L.rec[fid]
        new = [list(s) for s in sl]
        for s in new:
            if s[0] == b'ACBS':
                s[1] = struct.pack('<I', u32(s[1][:4]) | 1) + s[1][4:]
        out['NPC_'].append((fid, flags, pack(new)))
    # ---- female models on the skin addons
    for fid, (typ, flags, sl) in sorted(L.rec.items()):
        if typ != 'ARMA' or fid >> 24 >= own:
            continue
        m2 = (get(sl, b'MOD2') or b'').rstrip(b'\0').decode('latin1').lower()
        m3 = (get(sl, b'MOD3') or b'').rstrip(b'\0').decode('latin1').lower()
        to = models.get(m2)
        if m3 == 'actors\\radstag\\characterassets\\radstagdoe.nif' and m2 != m3:     # adult stag skins; the fawn
            to = models.get(m3 + '@female', to)                                     # (doe nif as male) stays
        if not to:
            continue
        new = [list(s) for s in sl if s[0] not in (b'MOD3', b'MO3T', b'MO3C', b'MO3F') or False]
        mo3s = get(sl, b'MO3S') or get(sl, b'MO2S')
        new = [s for s in new if s[0] != b'MO3S']
        at = max(i for i, s in enumerate(new) if s[0] in (b'MOD2', b'MO2T', b'MO2C', b'MO2F', b'MO2S')) + 1
        ins = [[b'MOD3', zs(to)], [b'MO3T', MO_T]] + ([[b'MO3S', mo3s]] if mo3s else [])
        new = new[:at] + ins + new[at:]
        out['ARMA'].append((fid, flags, pack(new)))
        report.append(f'ARMA {get(sl, b"EDID").rstrip(bytes(1)).decode()}: {m2} -> {to}')
    return out, nid[0], lines, report


def stem_plugin(stem):
    return f'Anatomy Female {stem}.esp'


def write_plugin(path, masters, groups, next_id):
    def field(t, v):
        return t + struct.pack('<H', len(v)) + v
    body, count = b'', 0
    for typ in ('NPC_', 'LVLN', 'ARMA'):                         # FO4 top-group order
        if not groups[typ]:
            continue
        g = b''
        for fid, flags, rb in groups[typ]:
            g += typ.encode() + struct.pack('<III', len(rb), flags, fid) + struct.pack('<IHH', 0, 131, 0) + rb
            count += 1
        body += b'GRUP' + struct.pack('<I', 24 + len(g)) + typ.encode() + struct.pack('<I', 0) \
            + struct.pack('<IHH', 0, 0, 0) + g
    hdr = field(b'HEDR', struct.pack('<fiI', 1.0, count, next_id)) + field(b'CNAM', b'Anatomy\0')
    for m in masters:
        hdr += field(b'MAST', m.encode() + b'\0') + field(b'DATA', struct.pack('<Q', 0))
    path.write_bytes(b'TES4' + struct.pack('<III', len(hdr), esl.LIGHT, 0) + struct.pack('<IHH', 0, 131, 0)
                     + hdr + body)


if __name__ == '__main__':
    out = pathlib.Path(sys.argv[1])
    for stem in (sys.argv[2:] or list(MODS)):
        masters, races, models, always_f = MODS[stem]
        groups, nxt, lines, report = build(stem, masters, races, models, always_f)
        d = out / stem
        (d / 'F4SE/Plugins/RobCo_Patcher/leveledList').mkdir(parents=True, exist_ok=True)
        write_plugin(d / stem_plugin(stem), masters, groups, nxt)
        if lines:
            (d / f'F4SE/Plugins/RobCo_Patcher/leveledList/Anatomy Female {stem}.ini').write_text(
                f'; Anatomy Female {stem}: female twins added next to the males (same level and count)\n'
                + '\n'.join(lines) + '\n', encoding='utf-8')
        p = esl.Plugin(d / stem_plugin(stem))
        print(f'{stem}: NPC_ {len(groups["NPC_"])} LVLN {len(groups["LVLN"])} ARMA {len(groups["ARMA"])} '
              f'robco lines {len(lines)} next id {nxt:03X} (read back {len(p.records)} entries)')
        for r in report:
            print('  ', r)
