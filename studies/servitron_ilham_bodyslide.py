"""Build the male abdomens with Ilham's penis in the LAB BodySlide at Servitron's preset, with their .tri (2026-11-22).
servitron.bodyslide() swaps Servitron's own set files in; this adds our AnatomyServitronMale<tag>.osp beside them for the
run and takes it out after.

    python studies/servitron_ilham_bodyslide.py <out ShapeData/Servitron> <out SliderSets/AnatomyServitronMale<tag>.osp> <target>
"""
import pathlib
import re
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'tools'))
import prebuilt_bodies as pb  # noqa: E402
import servitron as srv  # noqa: E402

shapedata, osp, target = (pathlib.Path(a) for a in sys.argv[1:4])
sets = tuple(re.findall(r'<SliderSet name="([^"]+)"', osp.read_text(encoding='utf-8')))
dst = pb.LAB / 'SliderSets' / osp.name
if dst.exists():
    raise SystemExit(f'{dst} is already in the LAB: not overwriting it')
shutil.copy2(osp, dst)
try:
    print(srv.bodyslide(shapedata, target, sets=sets))
finally:
    dst.unlink()
for p in sorted(target.rglob('*')):
    if p.is_file():
        print(p.relative_to(target), p.stat().st_size)
