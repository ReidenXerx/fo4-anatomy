"""The 3BBB (Anatomy Tailor) versions of Servitron's rigged rubber abdomens, women's and men's (a Sonnet audit, 2026-10-08:
the 3BBB copy predated the rig's ring-edge weights and no tool made it). The Tailor's sets "Servitron Abdomen <X> Rubber
(Anatomy 3BBB)" are rigged by servitron.build, then made male by servitron_male.build, each with its slider set.

    python tools/servitron_3bbb.py <out folder>   -> <out>/ShapeData/..., <out>/SliderSets/AnatomyServitron3BBB*.osp
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import servitron as srv  # noqa: E402
import servitron_male as sm  # noqa: E402

TAILOR = pathlib.Path(r'D:\F4Output\RefitExport\Single\Servitron\build-3BBB\BodySlide')
SETS = ((3, 'Abdomen GITS Rubber', 'GITS'), (6, 'Abdomen Wetsuit Rubber', 'Wetsuit'))


def male_set(text, stem, kind, folder, male_folder):
    s = text
    s = s.replace(f'<SliderSet name="Servitron {stem} (Anatomy 3BBB)"', f'<SliderSet name="Servitron {stem} Male (Anatomy 3BBB)"')
    s = s.replace(f'<DataFolder>{folder}</DataFolder>', f'<DataFolder>{male_folder}</DataFolder>')
    s = s.replace(f'<SourceFile>{stem}.nif</SourceFile>', f'<SourceFile>{stem} Male.nif</SourceFile>')
    s = re.sub(rf'>{re.escape(stem)}</OutputFile>', f'>{stem} Male</OutputFile>', s)
    s = s.replace(f'{stem}.osd\\', f'{stem} Male.osd\\')
    s = s.replace(f'Abdomen_{kind}_Rubber_VRing2', sm.PENIS)
    return s


def main():
    out = pathlib.Path(sys.argv[1])
    for no, stem, kind in SETS:
        folder = f'Anatomy3BBB Servitron #{no}'
        male_folder = f'Anatomy3BBB Servitron Male #{no}'
        src = TAILOR / 'ShapeData' / folder
        rig = out / 'ShapeData' / folder
        male = out / 'ShapeData' / male_folder
        rig.mkdir(parents=True, exist_ok=True)
        male.mkdir(parents=True, exist_ok=True)
        for line in srv.build(src / f'{stem}.nif', rig / f'{stem}.nif', (src / f'{stem}.osd', rig / f'{stem}.osd')):
            print(f'{folder}: {line}')
        for line in sm.build(rig / f'{stem}.nif', male / f'{stem} Male.nif', rig / f'{stem}.osd', male / f'{stem} Male.osd'):
            print(f'{male_folder}: {line}')
        osp = (TAILOR / 'SliderSets' / f'{folder}.osp').read_text(encoding='utf-8', errors='replace')
        (out / 'SliderSets').mkdir(parents=True, exist_ok=True)
        (out / 'SliderSets' / f'{folder}.osp').write_text(osp, encoding='utf-8')
        (out / 'SliderSets' / f'{male_folder}.osp').write_text(male_set(osp, stem, kind, folder, male_folder),
                                                                encoding='utf-8')
        print(f'{folder}: slider sets written (the women\'s as the Tailor has it, the men\'s beside it)')


if __name__ == '__main__':
    main()
