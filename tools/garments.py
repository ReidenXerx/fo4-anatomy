"""Garments (A-36): every CBBE garment on the hip band gets the body's hip handover (A-30), and BodySlide
rebuilds them unattended.

The hip fold (A-30, tools/hip_fold.py) softened CBBE's pelvis -> thigh handover on OUR body, so her groin no
longer tears 11x when her legs go up. Every garment still carries CBBE's handover. So a garment on the naked
body parts from the skin in deep bends, up to 3.8 units at the hip. An outfit tears the way the body did.
And an armour piece over an outfit parts from it the moment only one of them is fixed. The owner's poll
(2026-09-26): "I agree with recommendation", every CBBE garment, "and we need full auto script that will do
all machinery for bodyslides regeneration assuming it will work with our silhouette and other our mods".

What moves, per garment vertex:
  - only the core bones' SPLIT (Pelvis, Pelvis_Rear, Spine1, both thighs);
  - only where the nearest body vertex is one the hip fold changed;
  - fully within NEAR of the body, fading out by FAR (so a loose skirt's hem keeps its author's weights).
The vertex's core total, and every other bone's weight, stay as the author made them. A core bone the
garment lacks is added to its skin, with the body's own bind data.

Nothing another mod ships is written. Everything goes to a private BodySlide workspace, holding:
  - a copy of the program;
  - the original slider set files;
  - our patched ShapeData;
  - one group, "Anatomy Garments".
BodySlide builds that group headless with a zero preset and --trimorphs, so LooksMenu BodyGen and
Silhouette find every morph they did before. Only then does anything reach the game, and only through
`install`.

    python tools/garments.py plan                       # which sets, and why the rest are left
    python tools/garments.py build [--work <dir>]       # patch + check every set into the workspace
    python tools/garments.py regen --target <dir>       # BodySlide builds them there (headless)
    python tools/garments.py all --target <dir>         # plan, build, regen, verify
"""
import argparse
import collections
import json
import math
import pathlib
import re
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

import hip_fold
import nif

DATA = pathlib.Path(r'D:\GOGGames\Fallout 4 GOTY\Data')
WORK = pathlib.Path(r'D:\F4Output\AnatomyGarments')
GROUP = 'Anatomy Garments'
PRESET = 'CBBE Zeroed Sliders'
CORE, THIGHS = hip_fold.CORE, hip_fold.THIGHS
MAX_BONES = hip_fold.MAX_BONES
NEAR, FAR = 1.0, 2.5          # fully the body's within NEAR, the author's again at FAR
CHANGED = 0.02                # a body vertex whose core split moved more than this (L1) is the fold's
CELL = 2.0
OTHER_BODY = re.compile(r'body ?talk|\bbt ?[34]?\b|fusion ?girl|\bfg\b', re.I)
BODY_OUTPUTS = {'actors\\character\\characterassets\\femalebody'}


# ---- geometry ----
class Grid:
    def __init__(self, points):
        self.p = points
        self.g = collections.defaultdict(list)
        for i, q in enumerate(points):
            self.g[self.key(q)].append(i)

    @staticmethod
    def key(q):
        return (math.floor(q[0] / CELL), math.floor(q[1] / CELL), math.floor(q[2] / CELL))

    def within(self, q, r):
        """[(distance, index)] of points within r, nearest first."""
        cx, cy, cz = self.key(q)
        reach = int(math.ceil(r / CELL))
        out = []
        for dx in range(-reach, reach + 1):
            for dy in range(-reach, reach + 1):
                for dz in range(-reach, reach + 1):
                    for i in self.g.get((cx + dx, cy + dy, cz + dz), ()):
                        d = math.dist(self.p[i], q)
                        if d <= r:
                            out.append((d, i))
        out.sort()
        return out


MERGE = {'Pelvis_Rear_skin': ('Pelvis_skin', 'Spine1_skin'), 'Pelvis_skin': ('Pelvis_Rear_skin', 'Spine1_skin'),
         'Spine1_skin': ('Pelvis_skin', 'Pelvis_Rear_skin')}


def fit(share, slots):
    """A core split into at most `slots` bones, dropping the smallest TORSO share into its nearest torso
    neighbour (rear pelvis -> pelvis -> spine). hip_fold.fit merges every torso share into the largest,
    right for the body's legs-up bends; on a garment vertex that also carries Spine1_Rear it put a pelvis
    share on Spine1, and a spine bend parted the Vault 111 suit 4.7 where it had parted 1.2 (measured).
    The thighs keep their shares: dropping one is the tear this exists to remove. {} if nothing fits."""
    if slots <= 0:
        return {}
    share = dict(share)
    while len(share) > slots:
        # the SMALLEST share goes, whatever bone it is: a midline vertex (rear pelvis 0.9, two thighs at
        # 0.05 and 0.03) once lost its rear pelvis, the last torso bone, and parted 8.2 in doggy (measured)
        b = min(share, key=lambda k: (share[k], k))
        x = share.pop(b)
        to = next((m for m in MERGE.get(b, ()) if m in share), None) or max(share, key=lambda k: (share[k], k))
        share[to] += x
    s = sum(share.values())
    return {b: x / s for b, x in share.items()} if s > 0 else {}


def split_of(w):
    t = sum(w.get(b, 0.0) for b in CORE)
    return t, ({b: w[b] / t for b in CORE if w.get(b, 0.0) > 0} if t > 0 else {})


def l1(a, b):
    return sum(abs(a.get(k, 0.0) - b.get(k, 0.0)) for k in set(a) | set(b))


def identity(n, shape):
    o, _ = n.offsets[shape.index]
    _, t, r, s = n._av(nif.Cursor(n.b, o))
    return all(abs(x) < 1e-4 for x in t) and abs(s - 1) < 1e-4 and \
        all(abs(r[k] - (1.0 if k in (0, 4, 8) else 0.0)) < 1e-4 for k in range(9))


# ---- BodySlide files ----
def slider_sets(bs):
    """[(osp path, SliderSet element)] as BodySlide reads them: recursive, *.osp and *.xml."""
    out = []
    folder = bs / 'SliderSets'
    for f in sorted(list(folder.rglob('*.osp')) + list(folder.rglob('*.xml'))):
        try:
            root = ET.fromstring(f.read_bytes().decode('utf-8-sig', 'replace'))
        except ET.ParseError:
            continue
        for s in root.iter('SliderSet'):
            out.append((f, s))
    return out


def groups(bs):
    member = collections.defaultdict(set)
    for f in sorted((bs / 'SliderGroups').rglob('*.xml')):
        try:
            root = ET.fromstring(f.read_bytes().decode('utf-8-sig', 'replace'))
        except ET.ParseError:
            continue
        for g in root.iter('Group'):
            for m in g.iter('Member'):
                member[m.get('name')].add(g.get('name'))
    return member


def norm(p):
    p = p.replace('/', '\\').lower().strip('\\')
    if p.startswith('meshes\\'):
        p = p[7:]
    return p[:-4] if p.endswith('.nif') else p


def output_of(s):
    of = s.find('OutputFile')
    return norm((s.findtext('OutputPath') or '') + '\\' + (of.text if of is not None and of.text else ''))


def worn_female(data):
    """{female model: [slots]} from every active plugin's ARMA (MOD3 + BOD2)."""
    sys.path.insert(0, str(pathlib.Path(__file__).parent))
    import gamedata
    import struct
    import zlib
    g = gamedata.Game(data)
    out = collections.defaultdict(list)
    for pl in g.plugins:
        f = data / pl
        if not f.exists():
            continue
        b = f.read_bytes()
        o = 24 + struct.unpack_from('<I', b, 4)[0]
        while o + 24 <= len(b) and b[o:o + 4] == b'GRUP':
            size = struct.unpack_from('<I', b, o + 4)[0]
            if b[o + 8:o + 12] == b'ARMA':
                p, end = o + 24, o + size
                while p + 24 <= end:
                    rt = b[p:p + 4]
                    rs, rf = struct.unpack_from('<II', b, p + 4)
                    rec = b[p + 24:p + 24 + rs]
                    p += 24 + rs
                    if rt != b'ARMA':
                        continue
                    if rf & 0x40000:
                        try:
                            rec = zlib.decompress(rec[4:])
                        except zlib.error:
                            continue
                    slots, female, q, big = None, None, 0, None
                    while q + 6 <= len(rec):
                        t = rec[q:q + 4]
                        n = struct.unpack_from('<H', rec, q + 4)[0]
                        q += 6
                        if t == b'XXXX':
                            big = struct.unpack_from('<I', rec, q)[0]
                            q += n
                            continue
                        if big is not None:
                            n, big = big, None
                        d = rec[q:q + n]
                        q += n
                        if t == b'BOD2' and len(d) >= 4:
                            slots = struct.unpack_from('<I', d, 0)[0]
                        elif t == b'MOD3':
                            female = d.rstrip(b'\0').decode('cp1252', 'replace')
                    if female and slots is not None:
                        out[norm(female)].append(slots)
            o += size
    return out


# ---- the body ----
class Body:
    """Our body (Anatomy.nif) and where its hip fold changed CBBE's split."""

    def __init__(self, bs):
        n = nif.Nif(bs / 'ShapeData/Anatomy/Anatomy.nif')
        s = n.shape('CBBE')
        self.nif, self.shape = n, s
        self.bones, self.xf = n.skin(s)
        self.pos = s.positions()
        self.w = [{self.bones[sl]: w for sl, w in s.skin_weights(i)} for i in range(s.count)]
        cb = nif.Nif(bs / 'ShapeData/CBBE/CBBEBodyPhysics.nif')
        cs = cb.shape('CBBE')
        cbones, _ = cb.skin(cs)
        cpos = cs.positions()
        cw = [{cbones[sl]: w for sl, w in cs.skin_weights(i)} for i in range(cs.count)]
        cg = Grid(cpos)
        self.band = set()
        for i, p in enumerate(self.pos):
            hit = cg.within(p, 0.05)
            if not hit:
                continue
            _, a = split_of(self.w[i])
            _, b = split_of(cw[hit[0][1]])
            if a and l1(a, b) > CHANGED:
                self.band.add(i)
        self.grid = Grid(self.pos)
        self.bind = {}                              # bone -> (node rot, node t, skin rot, skin t, scale, sphere)
        o, _ = n.offsets[s.skin]
        c = nif.Cursor(n.b, o)
        c.take('i')
        data = c.take('i')
        refs = [c.take('i') for _ in range(c.take('I'))]
        o, _ = n.offsets[data]
        c = nif.Cursor(n.b, o)
        for k in range(c.take('I')):
            sphere = c.take('4f')
            rot9, t3, sc = c.take('9f'), c.take('3f'), c.take('f')
            node = n.nodes.get(refs[k])
            if node:
                self.bind[node['name']] = dict(name=node['name'], node_rot=node['r'], node_t=node['t'],
                                               sphere=sphere, skin_rot=rot9, skin_t=t3, scale=sc)

    def target(self, q):
        """(blend 0..1, the body's core split here) for a garment vertex at q, or None."""
        hits = self.grid.within(q, FAR)
        if not hits or hits[0][1] not in self.band:
            return None
        d0 = hits[0][0]
        f = 1.0 if d0 <= NEAR else (FAR - d0) / (FAR - NEAR)
        acc, tot = collections.defaultdict(float), 0.0
        for d, i in hits[:6]:
            _, sp = split_of(self.w[i])
            if not sp:
                continue
            k = 1.0 / max(d, 1e-3)
            tot += k
            for b, x in sp.items():
                acc[b] += k * x
        if tot <= 0:
            return None
        return f, {b: x / tot for b, x in acc.items()}


# ---- one garment shape ----
def transfer(body, positions, weights):
    """{vertex: new weights} for one shape (weights: [{bone: w}])."""
    wid = nif.weld(positions)
    first = {}
    out = {}
    for i, (q, w) in enumerate(zip(positions, weights)):
        g = wid[i]
        if g in first:                               # welded copies take the same weights: no seam crack
            if first[g] in out:
                out[i] = out[first[g]]
            continue
        first[g] = i
        total, own = split_of(w)
        if total < 0.05:
            continue
        t = body.target(q)
        if t is None:
            continue
        f, want = t
        side = q[0]
        # never hand a vertex the other side's thigh (the hip fold's own rule: LLeg is x < 0). The first
        # trial had the sides swapped: it stripped a thigh vertex of its own thigh and a combat-armour leg
        # parted 7.8 from the skin in doggy where it had parted 0.25 (scratchpad garments/worst.py)
        if side > 0.5:
            want.pop('LLeg_Thigh_skin', None)
        elif side < -0.5:
            want.pop('RLeg_Thigh_skin', None)
        mixed = {b: (1 - f) * own.get(b, 0.0) + f * want.get(b, 0.0) for b in set(own) | set(want)}
        s = sum(mixed.values())
        if s <= 0:
            continue
        mixed = {b: x / s for b, x in mixed.items() if x / s > 1e-3}
        if l1(mixed, own) < 0.01:
            continue
        new = {b: x for b, x in w.items() if b not in CORE and x >= 0.005}
        core = fit(mixed, MAX_BONES - len(new))
        if not core:
            continue
        for b, x in core.items():
            new[b] = x * total
        s = sum(new.values())
        out[i] = {b: x / s for b, x in new.items()}
    return out


def check(positions, before, after):
    """The stage's proof, per shape, or stop (hip_fold.check's rules)."""
    wid = nif.weld(positions)
    for i, w in after.items():
        if abs(sum(w.values()) - 1.0) > 1e-4 or len(w) > MAX_BONES:
            raise SystemExit(f'garments: vertex {i} weights {w} are not four or fewer summing to 1')
        own = sum(before[i].values()) or 1.0          # checked as shares: the author's sum is kept on write
        for b, x in before[i].items():
            x /= own
            if b not in CORE and x > 0.01 and abs(w.get(b, 0.0) - x) > 0.02 + 0.3 * x:
                raise SystemExit(f'garments: vertex {i} lost its {b} weight ({x:.3f} -> {w.get(b, 0.0):.3f})')
        t0 = split_of(before[i])[0] / own
        t1, _ = split_of(w)
        if abs(t0 - t1) > 0.02 + 0.3 * t0:
            raise SystemExit(f'garments: vertex {i} core total {t0:.3f} -> {t1:.3f}')
    seen = {}
    for i in after:
        g = wid[i]
        if g in seen and after[i] != after[seen[g]]:
            raise SystemExit(f'garments: welded copies {seen[g]} and {i} differ: the seam would crack')
        seen.setdefault(g, i)


def placed_bind(bind, m):
    """A body bone's bind data for a shape whose vertex space is m (body space <- shape space; None = the body's).
    FO4 places a vertex by bone world @ skin-to-bone @ v, so the new skin-to-bone is the body's @ m: the bone then
    puts the shape's vertices where the shape's own bones do (fo4-refit R-11). m is rigid: its scale is kept apart."""
    if m is None:
        return bind
    r, t, sc = bind['skin_rot'], bind['skin_t'], bind['scale']
    a = [[sum(r[3 * i + k] * sc * m[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    det = (a[0][0] * (a[1][1] * a[2][2] - a[1][2] * a[2][1]) - a[0][1] * (a[1][0] * a[2][2] - a[1][2] * a[2][0])
           + a[0][2] * (a[1][0] * a[2][1] - a[1][1] * a[2][0]))
    s2 = abs(det) ** (1 / 3)
    t2 = tuple(sum(r[3 * i + k] * sc * m[k][3] for k in range(3)) + t[i] for i in range(3))
    return dict(bind, skin_rot=tuple(a[i][j] / s2 for i in range(3) for j in range(3)), skin_t=t2, scale=s2)


def patch_nif(body, src, dst, xfer=None, chk=None, to_body=None):
    """Patch every skinned shape of one ShapeData .nif into dst. Returns {shape: changed vertices or why not}.
    xfer/chk: another weight transfer and its proof (fo4-refit tools/refit.py, A-58); the hip fold's by default.
    to_body(n, shape) -> 4x4 or None: carries EVERY skinned shape into the body's vertex space (fo4-refit R-10/R-11:
    skinned vertices are placed by their bones, not the node transform, and a shape with no node transform can
    still be authored in another space); None skips the shape. Bones added to such a shape take the body's
    skin-to-bone composed with that matrix, so they place its vertices where its own bones do. Without to_body a
    shape with its own node transform is skipped and the rest are taken as in the body's space, as before."""
    xfer, chk = xfer or transfer, chk or check
    n = nif.Nif(src)
    report, plans = {}, {}
    for s in n.shapes():
        bones, _ = n.skin(s)
        if not bones:
            continue
        m = None
        if to_body:
            m = to_body(n, s)
            if m is None:
                report[s.name] = 'skipped: cannot be placed (the skeleton knows none of its bones)'
                continue
            if all(abs(m[i][j] - (i == j)) < 1e-6 for i in range(4) for j in range(4)):
                m = None                                 # already in the body's space
        elif not identity(n, s):
            report[s.name] = 'skipped: its shape has its own transform'
            continue
        pos = s.positions()
        if m is not None:
            pos = [tuple(float(x) for x in m[:3, :3] @ p + m[:3, 3]) for p in pos]
        before = [{bones[sl]: w for sl, w in s.skin_weights(i)} for i in range(s.count)]
        after = xfer(body, pos, before)
        if not after:
            report[s.name] = 'unchanged: nothing to move'
            continue
        chk(pos, before, after)
        need = sorted({b for w in after.values() for b in w} - set(bones))
        missing = [b for b in need if b not in body.bind]
        if missing:
            raise SystemExit(f'{src.name}/{s.name}: the body has no bind data for {missing}')
        plans[s.index] = (s.name, need, after, {i: sum(before[i].values()) for i in after}, m)
    for index, (name, need, _, _, m) in plans.items():  # blocks are appended: every index stays valid
        if need:
            shape = next(x for x in n.shapes() if x.index == index)
            n = reparse(n.with_bones(shape, [placed_bind(body.bind[b], m) for b in need]))
    for s in n.shapes():
        if s.index not in plans:
            continue
        name, _, after, sums, _ = plans[s.index]
        bones, _ = n.skin(s)
        slot = {b: k for k, b in enumerate(bones)}
        for i, w in after.items():
            s.set_skin_weights(i, [(slot[b], x) for b, x in w.items()], total=sums[i])
        report[name] = len(after)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()                                 # a workspace may HARDLINK the original: writing through
                                                     # the link would rewrite another mod's ShapeData
    n.save(dst)
    return report


def reparse(raw):
    """A Nif over new bytes (with_bones returns bytes; the class reads from a path)."""
    tmp = WORK / '_reparse.nif'
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_bytes(bytes(raw))
    return nif.Nif(tmp)


# ---- which sets ----
def build_choices(bs):
    f = bs / 'BuildSelection.xml'
    if not f.exists():
        return {}
    root = ET.fromstring(f.read_bytes().decode('utf-8-sig', 'replace'))
    return {norm(oc.get('path') or ''): oc.get('choice') for oc in root.iter('OutputChoice')}


def plan(bs, data):
    """(targets, left): targets = [dict(name, osp, folder, src, output, data)]; left = {reason: [names]}."""
    member, worn, choice = groups(bs), worn_female(data), build_choices(bs)
    by_output = collections.defaultdict(list)
    left = collections.defaultdict(list)
    for osp, s in slider_sets(bs):
        name = s.get('name')
        out = output_of(s)
        gs = member.get(name, set())
        # a woman wears it (below) and it was not made on another body: 399 CBBE garments here sit in no
        # group at all, so the CBBE group alone missed most of them (measured 2026-09-26)
        if any(OTHER_BODY.search(x) for x in gs | {name}):
            left['made on another body (BodyTalk, Fusion Girl)'].append(name)
            continue
        if 'CBBE Bodies' in gs or out in BODY_OUTPUTS or name == 'Anatomy Body':
            left['a body, not a garment'].append(name)
            continue
        if out not in worn:
            left["no active plugin wears it as a woman's model"].append(name)
            continue
        folder = (s.findtext('DataFolder') or '').strip()
        src = (s.findtext('SourceFile') or '').strip()
        if not (bs / 'ShapeData' / folder / src).exists():
            left['its ShapeData is missing'].append(name)
            continue
        # every morph file the set reads, in the folder it reads it from: a <Shape DataFolder=...> reads its
        # sliders from ANOTHER folder (an outfit's body copy from CBBE's own). Copying only the set's folder
        # built 144 outfits whose body copy had no morphs at all, and BodySlide said nothing (verify caught it)
        where = {x.get('target') or (x.text or ''): (x.get('DataFolder') or folder) for x in s.findall('Shape')}
        datas = sorted({(where.get(d.get('target'), folder), (d.text or '').split('\\')[0])
                        for d in s.iter('Data') if d.text and '\\' in d.text})
        by_output[out].append(dict(name=name, osp=str(osp.relative_to(bs / 'SliderSets')), folder=folder, src=src,
                                   output=out, data=datas))
    targets = []
    for out, cands in by_output.items():
        if len(cands) == 1:
            targets.append(cands[0])
            continue
        pick = [c for c in cands if c['name'] == choice.get(out)]
        if pick:
            targets.append(pick[0])
            left['another set builds the same mesh (BuildSelection picked the other)'] += [
                c['name'] for c in cands if c is not pick[0]]
        else:
            left['several sets build the same mesh and BuildSelection names none'] += [c['name'] for c in cands]
    return sorted(targets, key=lambda t: t['name']), left


# ---- the workspace ----
def run_bodyslide(cmd, cwd, timeout):
    """Run a private BodySlide headless: minimised without taking focus, and a watchdog presses OK on its
    "No read/write permission for game data path!" warning should one still appear (the owner, 2026-09-30: no
    clicking hundreds of times). Returns (CompletedProcess-like, [what the watchdog answered])."""
    import ctypes
    import threading
    from ctypes import wintypes
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = 7                                    # SW_SHOWMINNOACTIVE
    proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, startupinfo=si)
    user32 = ctypes.windll.user32
    proto = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    stop, answered = threading.Event(), []

    def text(h):
        buf = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(h, buf, 512)
        return buf.value

    def watch():
        while not stop.is_set():
            tops = []
            user32.EnumWindows(proto(lambda h, l: tops.append(h) or True), 0)
            for h in tops:
                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(h, ctypes.byref(pid))
                title = text(h) if pid.value == proc.pid and user32.IsWindowVisible(h) else ''
                if title not in ('Warning', 'Failed'):   # the game data path check; a group build's failed-sets list
                    continue
                buf = ctypes.create_unicode_buffer(64)
                user32.GetClassNameW(h, buf, 64)
                if buf.value != '#32770':
                    continue
                # a Windows task dialog (its text lives in a DirectUIHWND: no child to read or click), so the
                # dialog itself gets IDOK; the build's own log still decides whether the build succeeded
                user32.PostMessageW(h, 0x0111, 1, 0)                   # WM_COMMAND IDOK, no focus taken
                answered.append(f'closed a BodySlide "{title}" dialog' + (' (the game data path check)' if
                                title == 'Warning' else ' (its failed sets are in Log_BS.txt)'))
            stop.wait(0.3)
    t = threading.Thread(target=watch, daemon=True)
    t.start()
    try:
        out, err = proc.communicate(timeout=timeout)
    finally:
        stop.set()
    return subprocess.CompletedProcess(cmd, proc.returncode, out, err), answered


def own_game_path(text, folder):
    """A private BodySlide's Config.xml text with EVERY game data path pointed at `folder` (writable, ours) and the
    missing-path warning off. BodySlide checks write access at start and waits on "No read/write permission for game
    data path!" even in a headless build; GameDataPath alone was not enough (2026-09-30: the per-game
    <GameDataPaths><Fallout4> still named the game's Data and the dialog came back on every launch)."""
    path = str(folder).rstrip('\\') + '\\'
    text = re.sub(r'<GameDataPath>[^<]*</GameDataPath>|<GameDataPath/>',
                  lambda m: f'<GameDataPath>{path}</GameDataPath>', text)
    text = re.sub(r'(<GameDataPaths>.*?<Fallout4>)[^<]*(</Fallout4>)', lambda m: m.group(1) + path + m.group(2),
                  text, count=1, flags=re.S)
    text = re.sub(r'<WarnMissingGamePath>[^<]*</WarnMissingGamePath>',
                  '<WarnMissingGamePath>false</WarnMissingGamePath>', text)
    return text


def workspace(bs, work, target):
    """A private BodySlide: the program, presets and config (OutputDataPath -> target); no sets yet."""
    import re
    home = work / 'BodySlide'
    if home.exists():
        shutil.rmtree(home)
    home.mkdir(parents=True)
    for item in bs.iterdir():
        if item.name in ('ShapeData', 'SliderSets', 'SliderGroups', 'Log_BS.txt', '__folder_managed_by_vortex'):
            continue
        if item.is_dir():
            shutil.copytree(item, home / item.name)
        else:
            shutil.copy2(item, home / item.name)
    cfg = home / 'Config.xml'
    text = cfg.read_text(encoding='utf-8-sig')
    want = '<OutputDataPath>' + str(target).rstrip('\\') + '\\</OutputDataPath>'
    text, k = re.subn(r'<OutputDataPath>[^<]*</OutputDataPath>', lambda m: want, text)
    if k != 1:
        raise SystemExit('BodySlide Config.xml: no single OutputDataPath to point at the target')
    # BodySlide checks it may write the game's Data at start and, when it may not, waits on a dialog even in
    # a headless group build (2026-09-26: both builds sat behind "No read/write permission for game data
    # path!"). A headless build reads nothing there, so the workspace itself is its game data path.
    text = own_game_path(text, work)
    cfg.write_text(text, encoding='utf-8')
    for sub in ('ShapeData', 'SliderSets', 'SliderGroups'):
        (home / sub).mkdir()
    return home


_PW = {}


def _patch_init(body, xfer, chk, to_body):
    import tempfile
    global WORK
    WORK = pathlib.Path(tempfile.mkdtemp(prefix='garments-'))   # reparse's scratch file: one per process
    _PW.update(body=body, xfer=xfer, chk=chk, to_body=to_body)


def _patch_one(job):
    src, dst = job
    return dst, patch_nif(_PW['body'], src, dst, _PW['xfer'], _PW['chk'], _PW['to_body'])


def build(bs, data, work, target, only=None, body=None, xfer=None, chk=None, to_body=None, workers=1, skip=None):
    """body/xfer/chk: another transfer (fo4-refit tools/refit.py, A-58); the hip fold's by default.
    workers > 1: the ShapeData files are patched by that many processes (fo4-refit: 943 sets, 36 min on one core).
    Sets that share one source file are patched once. Reports and output are the same as the serial loop's."""
    targets, left = plan(bs, data)
    if only:
        targets = [t for t in targets if any(o.lower() in t['name'].lower() for o in only)]
    if skip:                                 # skip(target) -> why it is not built, or None (fo4-refit R-15)
        for t in list(targets):
            why = skip(t)
            if why:
                targets.remove(t)
                left[why].append(t['name'])
    home = workspace(bs, work, target)
    body = body or Body(bs)
    print(f"body: {len(body.band)} vertices where our body's weights differ from CBBE's")
    reports = {}
    if workers > 1:
        import multiprocessing as mp
        jobs = {}
        for t in targets:
            jobs.setdefault(home / 'ShapeData' / t['folder'] / t['src'], bs / 'ShapeData' / t['folder'] / t['src'])
        with mp.Pool(workers, initializer=_patch_init, initargs=(body, xfer, chk, to_body)) as pool:
            for dst, report in pool.imap_unordered(_patch_one, [(s, d) for d, s in jobs.items()]):
                reports[dst] = report
    built, off = [], []
    for t in targets:
        src = bs / 'ShapeData' / t['folder'] / t['src']
        dst = home / 'ShapeData' / t['folder'] / t['src']
        report = reports[dst] if dst in reports else patch_nif(body, src, dst, xfer, chk, to_body)
        moved = {k: v for k, v in report.items() if isinstance(v, int)}
        if not moved:
            if dst.exists():                              # a source file two sets share goes once
                dst.unlink()
            off.append(t['name'])
            continue
        for where, f in t['data']:
            src_data, dst_data = bs / 'ShapeData' / where / f, home / 'ShapeData' / where / f
            if src_data.exists() and not dst_data.exists():   # a file missing here is missing from the
                                                               # build it replaces too: verify compares .tri
                dst_data.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_data, dst_data)
        osp = home / 'SliderSets' / t['osp']
        if not osp.exists():
            osp.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(bs / 'SliderSets' / t['osp'], osp)
        t['moved'] = moved
        built.append(t)
        print(f"  {t['name'][:56]:56} {sum(moved.values()):5} vertices  {report}")
    left['off the hip band (nothing to move)'] = off
    root = ET.Element('SliderGroups')
    g = ET.SubElement(root, 'Group', name=GROUP)
    for t in built:
        ET.SubElement(g, 'Member', name=t['name'])
    ET.indent(root)
    ET.ElementTree(root).write(home / 'SliderGroups' / f'{GROUP}.xml', encoding='UTF-8', xml_declaration=True)
    (work / 'plan.json').write_text(json.dumps(dict(built=built, left=left), indent=1), encoding='utf-8')
    print(f'{len(built)} sets patched into {home}')
    for reason, names in sorted(left.items(), key=lambda kv: -len(kv[1])):
        print(f'  left {len(names):4}: {reason}')
    return home, built


def regen(home, target, preset):
    """BodySlide builds the group headless: (exit code, all built, error lines). 'All built' is proven, not read: every
    member set of the group must have written its .nif during this run. BodySlide once skipped 9 sets and still logged
    that all were built (fo4-refit R-7); a set that wrote nothing is named in the error lines as 'not built: <set>'."""
    target.mkdir(parents=True, exist_ok=True)
    started = time.time() - 2
    log = home / 'Log_BS.txt'
    if log.exists():
        log.unlink()
    cmd = [str(home / 'BodySlide.exe'), '--groupbuild', GROUP, '--targetdir', str(target), '--preset', preset,
           '--trimorphs']
    run, answered = run_bodyslide(cmd, home, 7200)
    for a in answered:
        print('   watchdog:', a)
    text = log.read_text(encoding='utf-8', errors='replace') if log.exists() else ''
    ok = 'All group build sets processed successfully!' in text
    errors = [line for line in text.splitlines() if '[1]' in line or 'rror' in line or 'ailed' in line]
    members = {name for name, gs in groups(home).items() if GROUP in gs}
    wrote = {norm(p.relative_to(target).as_posix()) for p in target.rglob('*.nif') if p.stat().st_mtime >= started}
    lost = sorted(s.get('name') for _, s in slider_sets(home) if s.get('name') in members and output_of(s) not in wrote)
    errors += [f'not built: {name}' for name in lost]
    return run.returncode, ok and not lost, errors


def verify(target, into, core_only=True):
    """Every rebuilt garment against the build it will replace: the same vertices to 1e-3, the same morphs
    (.tri, byte for byte), and no weight but the core bones' changed (core_only; a refit, A-58, changes more).
    (bad, checked, missing) lists."""
    bad, checked, missing = [], 0, []
    for new in sorted(target.rglob('*.nif')):
        rel = new.relative_to(target)
        old = into / rel
        if not old.exists():
            missing.append(str(rel))
            continue
        a, b = nif.Nif(old), nif.Nif(new)
        ot, nt = old.with_suffix('.tri'), new.with_suffix('.tri')
        if ot.exists() != nt.exists() or (ot.exists() and ot.read_bytes() != nt.read_bytes()):
            bad.append(f'{rel}: its morphs (.tri) differ from the build it replaces')
        sa_list, sb_list = a.shapes(), b.shapes()
        if [s.name for s in sa_list] != [s.name for s in sb_list]:
            bad.append(f'{rel}: shapes {[s.name for s in sa_list]} -> {[s.name for s in sb_list]}')
            continue
        for sa, sb in zip(sa_list, sb_list):
            if sa.count != sb.count:
                bad.append(f'{rel}/{sb.name}: {sa.count} -> {sb.count} vertices')
                continue
            ba, _ = a.skin(sa)
            bb, _ = b.skin(sb)
            for i, (p, q) in enumerate(zip(sa.positions(), sb.positions())):
                if max(abs(x - y) for x, y in zip(p, q)) > 1e-3:
                    bad.append(f'{rel}/{sb.name}: vertex {i} moved (the preset is not the one the old build used)')
                    break
            for i in range(sa.count if core_only else 0):
                wa = {ba[s]: w for s, w in sa.skin_weights(i)}
                wb = {bb[s]: w for s, w in sb.skin_weights(i)}
                if any(abs(wa.get(k, 0) - wb.get(k, 0)) > 0.03 + 0.3 * wa.get(k, 0) for k in set(wa) | set(wb)
                       if k not in CORE):
                    bad.append(f'{rel}/{sb.name}: vertex {i} changed a non-core weight {wa} -> {wb}')
                    break
        checked += 1
    return bad, checked, missing


def install(target, into, work):
    """Write every verified rebuild over the build it replaces, IN PLACE (a Vortex staging folder is
    hardlinked into Data, so the game's copy changes with it). Refuses while Fallout 4 runs; the files
    it replaces are kept under <work>/backup first."""
    running = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq Fallout4.exe'], capture_output=True, text=True).stdout
    if 'fallout4.exe' in running.lower():
        raise SystemExit('Fallout4.exe is running: nothing written')
    done = 0
    for new in sorted(target.rglob('*')):
        if not new.is_file():
            continue
        rel = new.relative_to(target)
        dest = into / rel
        if not dest.exists():
            continue                                  # verify reported it; a new file needs a Vortex deploy
        if dest.read_bytes() == new.read_bytes():
            continue
        keep = work / 'backup' / rel
        if not keep.exists():
            keep.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dest, keep)
        with open(dest, 'r+b') as f:                  # the same file (and inode): the hardlink holds
            f.write(new.read_bytes())
            f.truncate()
        done += 1
    return done


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('what', choices=('plan', 'build', 'regen', 'all', 'verify', 'install'))
    ap.add_argument('--into', type=pathlib.Path, default=pathlib.Path(r'D:\Vortex\fallout4\mods\bodyslides_f4_sd'),
                    help='where the builds being replaced live (verify, install)')
    ap.add_argument('--data', type=pathlib.Path, default=DATA)
    ap.add_argument('--work', type=pathlib.Path, default=WORK)
    ap.add_argument('--target', type=pathlib.Path, default=pathlib.Path(r'D:\F4Output\Bodyslides\woman'))
    ap.add_argument('--preset', default=PRESET)
    ap.add_argument('--only', nargs='*', help='only the sets whose names contain one of these (a trial run)')
    args = ap.parse_args()
    bs = args.data / 'Tools/BodySlide'
    if args.what == 'plan':
        targets, left = plan(bs, args.data)
        print(f'{len(targets)} CBBE garments worn in game')
        for reason, names in sorted(left.items(), key=lambda kv: -len(kv[1])):
            print(f'  left {len(names):4}: {reason}')
        return
    home = args.work / 'BodySlide'
    if args.what in ('build', 'all'):
        home, built = build(bs, args.data, args.work, args.target, args.only)
    if args.what in ('regen', 'all'):
        code, ok, errors = regen(home, args.target, args.preset)
        print(f"BodySlide exit {code}; {'all sets built' if ok else 'NOT all sets built'}; {len(errors)} error lines")
        for e in errors[:30]:
            print('   ', e)
        if not ok:
            sys.exit(1)
    if args.what in ('verify', 'all', 'install'):
        bad, checked, missing = verify(args.target, args.into)
        print(f'verify: {checked} rebuilt meshes against {args.into}: {len(bad)} bad, {len(missing)} with no build '
              f'there to replace')
        for b in bad[:40]:
            print('   BAD', b)
        for m in missing[:10]:
            print('   not there:', m)
        if bad:
            sys.exit(1)
    if args.what == 'install':
        print(f'install: {install(args.target, args.into, args.work)} files written in place into {args.into}')


if __name__ == '__main__':
    main()
