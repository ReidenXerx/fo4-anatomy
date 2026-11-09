"""Nick / gen2 synth body by transplant: vanilla SynthGen2Body.nif bytes + our two shapes (seg_fix'ed export) +
penis bone nodes + BODYTRI; our .tri copied alongside.  python -I nick_transplant.py <export Data> <out Data>"""
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from transplant import transplant  # noqa: E402

src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
REL = 'meshes/actors/synths'
VAN = r'D:\F4Output\creatures\nick\src\Fallout4 - Meshes\meshes\actors\synths\synthgen2body.nif'
(out / REL).mkdir(parents=True, exist_ok=True)
info = transplant(VAN, src / REL / 'SynthGen2Body.nif', out / REL / 'SynthGen2Body.nif',
                  {'Synt_Gen2_Penis': ('Body:0', None, None),
                   'Synt_Gen2_PenisJoints': ('MeatCapHead:1', None, None)},
                  bodytri='Actors\\Synths\\SynthGen2Body.tri')
shutil.copyfile(src / REL / 'SynthGen2Body.tri', out / REL / 'SynthGen2Body.tri')
print(info)
