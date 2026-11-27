"""AnatomyServitron.esp (light): the male rubber abdomens as Robot Workbench modules (the owner's poll, 2026-10-08).
Each module is Servitron's own Rubber abdomen module (Servitron.esm, Nexus 32801) with our name and mesh; each recipe is
its recipe pointing at ours. The masters repeat Servitron.esm's own (Fallout4.esm, DLCRobot.esm) so its ids keep their
index byte; ours take the next one, in the light range.

    python tools/servitron_male_plugin.py <out folder>   -> <out>/AnatomyServitron.esp
"""
import pathlib
import struct
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / 'fo4-refit' / 'tools'))
import esl  # noqa: E402
import esl_dist  # noqa: E402

SERVITRON = esl.DATA / 'Servitron.esm'
MASTERS = ['Fallout4.esm', 'DLCRobot.esm', 'Servitron.esm']
OURS = len(MASTERS) << 24
MODULES = [  # Servitron's module, its recipe, our editor id, name, mesh
    (0x02000B89, 0x02000813, 'AnatSrv_Abdomen_GITS_Rubber_Male', 'Abdomen - GITS Rubber (Male)',
     'Servitron\\Abdomen GITS Rubber Male.nif'),
    (0x02000B8C, 0x02000816, 'AnatSrv_Abdomen_Wetsuit_Rubber_Male', 'Abdomen - Wetsuit Rubber (Male)',
     'Servitron\\Abdomen Wetsuit Rubber Male.nif'),
]
# 2026-11-22 (Dudu's approval via Watcher): Ilham's penis (servitron_male.py --mesh --tag Ilham) and head (General-mods'
# Head Ilham.nif, a clone of Servitron_Head_Assaultron 02000BBD / its recipe 020008F2). Credit: ilhamitaa24 / kassarawi.
# Appended, so the ids above never move: 0x804/0x806 abdomens (Arousal.psc reads them as men), 0x808.. heads; each
# recipe at the module's id + 1.
ILHAM = [
    (0x02000B89, 0x02000813, 'AnatSrv_Abdomen_GITS_Rubber_Male_Ilham', 'Abdomen - GITS Rubber (Male, Ilham)',
     'Servitron\\Abdomen GITS Rubber Male Ilham.nif'),
    (0x02000B8C, 0x02000816, 'AnatSrv_Abdomen_Wetsuit_Rubber_Male_Ilham', 'Abdomen - Wetsuit Rubber (Male, Ilham)',
     'Servitron\\Abdomen Wetsuit Rubber Male Ilham.nif'),
    (0x02000BBD, 0x020008F2, 'AnatSrv_Head_Ilham', 'Head - Ilham', 'Servitron\\Head Ilham.nif'),
    # 11-28 (Dudu approved the release; her licensing answer: the rest is her friend's, the other half of kassarawi):
    # her paint jobs are separate geometries (General-mods measured her blend), so each is a head module of its own
    (0x02000BBD, 0x020008F2, 'AnatSrv_Head_Ilham_Ada', 'Head - Ilham (Ada)', 'Servitron\\Head Ilham Ada.nif'),
    (0x02000BBD, 0x020008F2, 'AnatSrv_Head_Ilham_Vex', 'Head - Ilham (Vex)', 'Servitron\\Head Ilham Vex.nif'),
    (0x02000BBD, 0x020008F2, 'AnatSrv_Head_Ilham_Nuke', 'Head - Ilham (Nuke)', 'Servitron\\Head Ilham Nuke.nif'),
]
# her face laser (General-mods' AnatomyServitron:IlhamLaserEffect): a constant self enchantment that each of her heads
# adds to the robot wearing it, so it runs exactly while one is worn and Servitron's race stays untouched. Cloned from
# DLCRobot's own head-laser enchantment (DLC01EnchBot_Unstable_AssaultronHeadLaser 01002967 / its effect 01002965)
LASER_MGEF, LASER_ENCH = 0x810, 0x811
LASER_SCRIPT = 'AnatomyServitron:IlhamLaserEffect'
LASER_PROPS = [('LaserWeapon', 0x000DD4B1), ('XMarker', 0x0000003B)]   # vanilla AssaultronLaser, XMarker
NPC_ENCHANTMENTS, ADD, FORM_ID = 3, 2, 4   # an actor OMOD's Enchantments property, function Add, a form value (DLCRobot's)


def sub(t, v):
    return t.encode() + struct.pack('<H', len(v)) + v


def fields(pl, fid):
    rec = next(r for r in pl.records if r[3] == fid)
    return list(esl_dist.subrecords(pl.body(rec)))


def wstr(s):
    b = s.encode()
    return struct.pack('<H', len(b)) + b


def laser_records():
    """the laser's effect and enchantment, cloned from DLCRobot's head laser (FULL/DNAM are lstring ids there: our esp is
    not localized, so they become plain strings)"""
    robot = esl.Plugin(esl.DATA / 'DLCRobot.esm')
    vmad = struct.pack('<hhH', 6, 2, 1) + wstr(LASER_SCRIPT) + struct.pack('<BH', 0, len(LASER_PROPS))
    for name, fid in LASER_PROPS:
        vmad += wstr(name) + struct.pack('<BBHhI', 1, 1, 0, -1, fid)   # an object: unused, alias -1, form
    swap = {'EDID': b'AnatSrv_IlhamLaserEffect\0', 'VMAD': vmad, 'FULL': b'Ilham laser\0', 'DNAM': b'\0'}
    mgef = b''.join(sub(t.decode(), swap.get(t.decode(), v)) for t, v in fields(robot, 0x01002965))
    swap = {'EDID': b'AnatSrv_IlhamLaser\0', 'FULL': b'Ilham laser\0', 'EFID': struct.pack('<I', OURS | LASER_MGEF)}
    ench = b''.join(sub(t.decode(), swap.get(t.decode(), v)) for t, v in fields(robot, 0x01002967))
    return [('MGEF', OURS | LASER_MGEF, mgef), ('ENCH', OURS | LASER_ENCH, ench)]


def add_laser(data):
    """an actor OMOD's DATA with one more property, Enchantments += the laser (properties sit at the tail)"""
    count = struct.unpack_from('<I', data, 4)[0]
    return (data[:4] + struct.pack('<I', count + 1) + data[8:]
            + struct.pack('<B3xB3xH2xIIf', FORM_ID, ADD, NPC_ENCHANTMENTS, OURS | LASER_ENCH, 562, 0.0))   # 24 bytes, as
    # DLCRobot's own Enchantments adds: value type, function, property, the form, 0x232, step 0


def main():
    out = pathlib.Path(sys.argv[1])
    # since 11-28 (her licensing answer) her parts are in the public esp; --plain builds the old two-module esp
    modules = MODULES + ([] if '--plain' in sys.argv[2:] else ILHAM)
    pl = esl.Plugin(SERVITRON)
    records = []
    heads = any(m[2].startswith('AnatSrv_Head_Ilham') for m in modules)
    for k, (mod, cobj, edid, name, mesh) in enumerate(modules):
        mine = OURS | (0x800 + 2 * k)
        body = b''
        for t, v in fields(pl, mod):
            tt = t.decode()
            if tt == 'EDID':
                v = edid.encode() + b'\0'
            elif tt == 'FULL':
                v = name.encode() + b'\0'
            elif tt == 'MODL':
                v = mesh.encode() + b'\0'
            elif tt == 'MODT':
                continue                                  # texture hashes of Servitron's mesh, not ours
            elif tt == 'DATA' and edid.startswith('AnatSrv_Head_Ilham'):
                v = add_laser(v)
            body += sub(tt, v)
        records.append(('OMOD', mine, body))
        body = b''
        for t, v in fields(pl, cobj):
            tt = t.decode()
            if tt == 'EDID':
                v = ('co_' + edid).encode() + b'\0'
            elif tt == 'CNAM':
                v = struct.pack('<I', mine)
            body += sub(tt, v)
        records.append(('COBJ', OURS | (0x801 + 2 * k), body))
    if heads:
        records += laser_records()
    esl_dist.write_plugin(out / 'AnatomyServitron.esp', MASTERS, records)
    for k, (_, _, edid, *_r) in enumerate(modules):
        print(f'  {edid}: OMOD {0x800 + 2 * k:06X}, COBJ {0x801 + 2 * k:06X}')
    print(f'{out / "AnatomyServitron.esp"}: {len(records)} records ({len(modules)} modules + recipes), light')


if __name__ == '__main__':
    main()
