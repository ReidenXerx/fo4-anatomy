"""Review-only nifs (never shipped): the vanilla deathclaw body + our male / female shapes, so one render shows the
genitals on the body. Penis/inner take our texture paths, lips the body's.
    python -I dc_review.py <out dir>"""
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from transplant import transplant  # noqa: E402

out = pathlib.Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
D = pathlib.Path(r'D:\F4Output\creatures\dc')
VAN = D / 'vanilla' / 'deathclaw.nif'
PEN = ('Materials\\actors\\Deathclaw\\PenisRegular.BGSM',
       ['textures\\actors\\deathclaw\\PenisRegular_D.dds', 'textures\\actors\\deathclaw\\PenisRegular_N.dds',
        'textures\\actors\\deathclaw\\PenisRegular_S.dds'])
for g, lips, inner in (('male', 'Base', 'Penis'), ('female', 'VulvaLips', 'VulvaInner')):
    info = transplant(VAN, D / 'build' / f'{g}.nif', out / f'review_{g}.nif',
                      {lips: ('DeathclawFX:0', None, None), inner: ('DeathclawFX:0', PEN[0], PEN[1])},
                      bodytri=f'Actors\\Deathclaw\\review_{g}.tri')
    shutil.copyfile(D / 'build' / f'{g}.tri', out / f'review_{g}.tri')
    print(g, info['shapes'])
