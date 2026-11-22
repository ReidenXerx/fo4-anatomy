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
# Head Ilham.nif, a clone of Servitron_Head_Assaultron 02000BBD / its recipe 020008F2). Only with --ilham: the public esp
# stays as it is until her licensing answer. Appended, so the ids above never move: 0x804/0x806 abdomens (Arousal.psc
# reads them as men), 0x808 head; each recipe at the module's id + 1.
ILHAM = [
    (0x02000B89, 0x02000813, 'AnatSrv_Abdomen_GITS_Rubber_Male_Ilham', 'Abdomen - GITS Rubber (Male, Ilham)',
     'Servitron\\Abdomen GITS Rubber Male Ilham.nif'),
    (0x02000B8C, 0x02000816, 'AnatSrv_Abdomen_Wetsuit_Rubber_Male_Ilham', 'Abdomen - Wetsuit Rubber (Male, Ilham)',
     'Servitron\\Abdomen Wetsuit Rubber Male Ilham.nif'),
    (0x02000BBD, 0x020008F2, 'AnatSrv_Head_Ilham', 'Head - Ilham', 'Servitron\\Head Ilham.nif'),
]


def sub(t, v):
    return t.encode() + struct.pack('<H', len(v)) + v


def fields(pl, fid):
    rec = next(r for r in pl.records if r[3] == fid)
    return list(esl_dist.subrecords(pl.body(rec)))


def main():
    out = pathlib.Path(sys.argv[1])
    modules = MODULES + (ILHAM if '--ilham' in sys.argv[2:] else [])
    pl = esl.Plugin(SERVITRON)
    records = []
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
    esl_dist.write_plugin(out / 'AnatomyServitron.esp', MASTERS, records)
    for k, (_, _, edid, *_r) in enumerate(modules):
        print(f'  {edid}: OMOD {0x800 + 2 * k:06X}, COBJ {0x801 + 2 * k:06X}')
    print(f'{out / "AnatomyServitron.esp"}: {len(records)} records ({len(modules)} modules + recipes), light')


if __name__ == '__main__':
    main()
