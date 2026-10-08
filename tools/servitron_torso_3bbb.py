"""Servitron's breast torsos for 3BBB bodies (the owner, 2026-10-08: "not sure that i see boobs jiggle"): Servitron's own
torsos weigh the breasts to CBBE's single LBreast_skin, which a 3BBB physics preset never moves. The Anatomy Tailor's 3BBB
sets ("Servitron Torso <X> Boobs (Anatomy 3BBB)") weigh them to LBreast_01..03_skin; this gives them our suit push
(servitron_torso.trim) and, on the rubber Boobs, the breast socket (servitron_collar.build), with their slider data.
The skeleton must then carry 3BBB's breast bones (out\\Meshes\\Servitron\\skeleton.nif).

    python tools/servitron_torso_3bbb.py <out folder>   -> <out>/ShapeData/<set folder>/..., <out>/SliderSets/*.osp
"""
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import servitron_collar as sc  # noqa: E402
import servitron_torso as st  # noqa: E402

TAILOR = pathlib.Path(r'D:\F4Output\RefitExport\Single\Servitron\build-3BBB\BodySlide')
SETS = (19, 20, 22, 23, 24, 25, 40, 41)


def main():
    out = pathlib.Path(sys.argv[1])
    (out / 'SliderSets').mkdir(parents=True, exist_ok=True)
    for no in SETS:
        folder = f'Anatomy3BBB Servitron #{no}'
        src = TAILOR / 'ShapeData' / folder
        dst = out / 'ShapeData' / folder
        dst.mkdir(parents=True, exist_ok=True)
        for f in sorted(src.glob('Torso*.nif')):
            pushed = dst / f.name
            print(f'{folder}: {st.trim(f, pushed)}')
            osd = f.with_suffix('.osd')
            if 'Robo' not in f.name:                 # the rubber breasts get the socket; Robo-Boobs are metal
                tmp = dst / ('_pushed_' + f.name)
                shutil.move(pushed, tmp)
                print(f'{folder}: {sc.build(tmp, pushed, osd=(osd, dst / osd.name))}')
                tmp.unlink()
            else:
                shutil.copy2(osd, dst / osd.name)
        shutil.copy2(TAILOR / 'SliderSets' / f'{folder}.osp', out / 'SliderSets' / f'{folder}.osp')


if __name__ == '__main__':
    main()
