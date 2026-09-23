"""Our genital bones, in a copy of the skeleton women actually load (decision A-14).

Which skeleton: DiscreteFemaleSkeleton.esp is active in the owner's game, so women load
Meshes/Actors/Character/CharacterAssets/female/skeleton.nif and female/skeleton.hkx. The .nif is
deployed from Skeletal Adjustments for CBBE, the .hkx from More Flexible Ragdoll (measured
2026-09-23: 208 nodes, not one genital bone; the .hkx animates 74 of them, none genital). Men load
ZeX's skeleton.nif/.hkx.

This copies that .nif and adds physics_design.REST's bones as children of physics_design.PARENT
(Pelvis_skin), with identity rotation, so each turns and moves with the pelvis. Nothing else
changes, and every step is proven:
  1. the base is the owning mod's staging copy (Data's copy becomes ours once deployed);
  2. every original block is byte-identical except the parent's, which only gains child refs, and
     every original node's world transform is unchanged;
  3. each new bone lands at its design position (skin space, via SKIN_OFFSET) to 1e-4;
  4. no .hkx in the game names a new bone, so no animation can move one.

    python tools/skeleton.py               -> build/skeleton/female/skeleton.nif
    python tools/skeleton.py --deployed    also check the game: the skeleton women load in Data,
                                           against every bone the deployed body uses
"""
import math
import pathlib
import re
import sys

import nif
import physics_design as pd
import zex_bones as zb

ROOT = pathlib.Path(__file__).resolve().parent.parent
MODS = pathlib.Path(r'D:\Vortex\fallout4\mods')
DATA = zb.ab.DEFAULT_DATA
FEMALE_REL = 'Meshes/Actors/Character/CharacterAssets/female/skeleton.nif'
BASE = MODS / 'Skeletal Adjustments for CBBE-39006-3-0-1652112684' / FEMALE_REL.lower()
HKX = [MODS / 'More Flexible Ragdoll-101073-1-0-1770184939/meshes/actors/character/characterassets/female/skeleton.hkx',
       MODS / 'More Flexible Ragdoll-101073-1-0-1770184939/meshes/actors/character/characterassets/skeleton.hkx',
       MODS / 'ZeX - ZaZ Extended Skeleton-36702-6-0-1687293851/Meshes/Actors/Character/CharacterAssets/skeleton.hkx']
OUT = ROOT / 'build/skeleton/female/skeleton.nif'
PLUGINS_TXT = pathlib.Path.home() / 'AppData/Local/Fallout4/plugins.txt'


def women_skeleton():
    """The skeleton.nif women load in the owner's game: DFS's female path when its plugin is active."""
    active = PLUGINS_TXT.exists() and any(l.strip().lower() == '*discretefemaleskeleton.esp'
                                          for l in PLUGINS_TXT.read_text(encoding='utf-8', errors='replace').splitlines())
    return DATA / (FEMALE_REL if active else 'Meshes/Actors/Character/CharacterAssets/skeleton.nif'), active


def body_bones(path):
    """The body's skin bones that carry weight (a weightless bone moves nothing, missing or not)."""
    n = nif.Nif(path)
    shape = n.shape(zb.ab.SHAPE)
    bones = n.skin(shape)[0]
    used = {sl for j in range(shape.count) for sl, w in shape.skin_weights(j) if w > 0}
    return [b for sl, b in enumerate(bones) if sl in used]


def missing_from(skeleton_path, bones):
    names = {n['name'] for n in nif.Nif(skeleton_path).nodes.values()}
    return [b for b in bones if b not in names]


def build():
    base = nif.Nif(BASE)
    world = zb.skeleton_world(BASE)
    parent = next(i for i, n in base.nodes.items() if n['name'] == pd.PARENT)
    pr, pt, ps = world[pd.PARENT]
    nodes = []
    for name, skin in pd.REST.items():
        w = [skin[i] - pd.SKIN_OFFSET[i] for i in range(3)]
        local = [v / ps for v in zb.apply(zb.transpose(pr), [w[i] - pt[i] for i in range(3)])]
        nodes.append(dict(name=name, t=tuple(local), r=(1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(base.with_nodes(parent, nodes))
    # each opening bone's stretch child (A-17), sitting on it: the fo4-ocbpc fork moves it out only
    # when something bigger than a penis is in the opening
    identity = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
    for bone, child in pd.STRETCH_BONES.items():
        cur = nif.Nif(OUT)
        at = next(i for i, n in cur.nodes.items() if n['name'] == bone)
        OUT.write_bytes(cur.with_nodes(at, [dict(name=child, t=(0.0, 0.0, 0.0), r=identity)]))

    # ---- proofs
    problems = []
    out = nif.Nif(OUT)
    n_old = len(base.offsets)
    changed = [i for i in range(n_old) if bytes(base.b[slice(base.offsets[i][0], sum(base.offsets[i]))])
               != bytes(out.b[slice(out.offsets[i][0], sum(out.offsets[i]))])]
    if changed != [parent]:
        problems.append(f'blocks changed besides {pd.PARENT}: {[base.nodes.get(i, {}).get("name", i) for i in changed]}')
    old_kids, new_kids = base.nodes[parent]['kids'], out.nodes[parent]['kids']
    if new_kids[:len(old_kids)] != old_kids or len(new_kids) != len(old_kids) + len(nodes):
        problems.append(f'{pd.PARENT} children not the old list plus ours')
    by_name = {n['name']: i for i, n in out.nodes.items()}
    for bone, child in pd.STRETCH_BONES.items():
        if by_name.get(child) not in out.nodes.get(by_name.get(bone), {}).get('kids', []):
            problems.append(f'{child} is not a child of {bone}')
    if out.strings[:len(base.strings)] != base.strings:
        problems.append('the string table changed before our names')
    new_world = zb.skeleton_world(OUT)
    drift = max(max(math.dist(world[n][1], new_world[n][1]),
                    max(abs(a - b) for a, b in zip(zb.flat(world[n][0]), zb.flat(new_world[n][0]))))
                for n in world)
    if drift > 0:
        problems.append(f'an original node moved ({drift})')
    worst = 0.0
    for name, skin in pd.REST.items():
        r, t, s = new_world[name]
        at = [t[i] + pd.SKIN_OFFSET[i] for i in range(3)]
        worst = max(worst, math.dist(at, skin))
        rot = max(abs(a - b) for a, b in zip(zb.flat(r), zb.flat(pr)))
        if rot > 1e-6:
            problems.append(f'{name} does not turn with {pd.PARENT} ({rot})')
    if worst > 1e-4:
        problems.append(f'a new bone is {worst} from its design position')
    for bone, child in pd.STRETCH_BONES.items():
        gap = max(math.dist(new_world[bone][1], new_world[child][1]),
                  max(abs(a - b) for a, b in zip(zb.flat(new_world[bone][0]), zb.flat(new_world[child][0]))))
        if gap > 1e-6:
            problems.append(f'{child} does not sit on {bone} ({gap})')
    keyed = {}
    for h in HKX:
        raw = h.read_bytes() if h.exists() else b''
        hits = [n for n in list(pd.REST) + list(pd.STRETCH_BONES.values())
                if re.search(re.escape(n.encode()) + b'\x00', raw)]
        if hits:
            keyed[h.name] = hits
    if keyed:
        problems.append(f'an animation skeleton names our bones: {keyed}')
    print(f'1. base {BASE.name} from {BASE.parent.parent.parent.parent.parent.parent.name}: {n_old} blocks, '
          f'{len(base.nodes)} nodes')
    print(f'2. wrote {OUT}: {len(out.offsets)} blocks; changed original blocks {[out.nodes[i]["name"] for i in changed]}; '
          f'original nodes moved {drift}')
    print(f'3. {len(nodes)} bones under {pd.PARENT}: worst distance from design {worst:.2e}')
    for name, skin in pd.REST.items():
        print(f'     {name:15} skin ({skin[0]:6.2f},{skin[1]:6.2f},{skin[2]:7.2f})')
    print(f'4. .hkx files checked {len([h for h in HKX if h.exists()])}/{len(HKX)}; naming our bones: {keyed or "none"}')
    if problems:
        raise SystemExit('FAIL - ' + '; '.join(problems))
    return OUT


def deployed():
    path, dfs = women_skeleton()
    body = DATA / 'Meshes/Actors/Character/CharacterAssets/FemaleBody.nif'
    bones = body_bones(body)
    miss = missing_from(path, bones)
    cloth = [b for b in miss if b.startswith('CLOTH_')]        # Havok cloth bones: the cloth data makes them
    real = [b for b in miss if b not in cloth]
    ours = OUT.exists() and path.read_bytes() == OUT.read_bytes()
    print(f'game: DiscreteFemaleSkeleton.esp {"active" if dfs else "NOT active"} -> women load {path.relative_to(DATA)}'
          f' ({"OUR build" if ours else "not our build"}); deployed body uses {len(bones)} bones, '
          f'{len(real)} missing from that skeleton {real or ""}; Havok cloth bones {len(cloth)}')
    return real


def main():
    build()
    if '--deployed' in sys.argv[1:] and deployed():
        raise SystemExit('the skeleton women load lacks bones the body is weighted to: those vertices will stretch')


if __name__ == '__main__':
    main()
