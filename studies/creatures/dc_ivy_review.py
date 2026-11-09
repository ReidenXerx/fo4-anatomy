"""Review nifs for the Ivy patch bodies: DEPO's body + our re-fitted male shapes (renders only, never shipped).
    python -I dc_ivy_review.py"""
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif  # noqa: E402
from transplant import transplant  # noqa: E402

D = pathlib.Path(r'D:\F4Output\creatures\dc')
OUT = D / 'ivy_review' / 'Data' / 'meshes' / 'actors' / 'deathclaw'
OUT.mkdir(parents=True, exist_ok=True)
PEN = ('Materials\\actors\\Deathclaw\\PenisRegular.BGSM',
       ['textures\\actors\\deathclaw\\PenisRegular_D.dds', 'textures\\actors\\deathclaw\\PenisRegular_N.dds',
        'textures\\actors\\deathclaw\\PenisRegular_S.dds'])
for key, f in (('Moj', 'MojDeathclaw.nif'), ('Mythic', 'Deathclaw_mythic.nif')):
    van = D / 'ivy_survey' / f
    body = max(nif.Nif(van).shapes(), key=lambda s: s.count).name
    info = transplant(van, D / 'ivy_build' / key / 'male.nif', OUT / f'review_{key}.nif',
                      {'Base': (body, None, None), 'Penis': (body, PEN[0], PEN[1])},
                      bodytri=f'Actors\\Deathclaw\\review_{key}.tri')
    shutil.copyfile(D / 'ivy_build' / key / 'male.tri', OUT / f'review_{key}.tri')
    print(key, info['shapes'][-3:])
