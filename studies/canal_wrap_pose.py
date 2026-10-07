"""A built body with its canal posed as the fork's [Canal] wraps a shaft (studies/canal_wrap_sim.py's step), for cutaway
renders: the canal's vertices moved in place (fixed-size vertex bytes only), every other byte as built.

    python studies/canal_wrap_pose.py <FemaleBody.nif> <out.nif> [tip depth, default 12.5]
"""
import io
import contextlib
import runpy
import shutil
import sys

src, dst = sys.argv[1], sys.argv[2]
depth = float(sys.argv[3]) if len(sys.argv) > 3 else 12.5
shutil.copyfile(src, dst)
sys.argv = ['canal_wrap_sim.py', dst]
with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path(str(__import__('pathlib').Path(__file__).with_name('canal_wrap_sim.py')))
s, nif = g['s'], g['nif']
shaft = g['shaft_to'](depth)
at = g['skinned'](g['wrap'](shaft))
for i, p in at.items():
    s.set_position(i, p)
g['n'].save(dst)
back = nif.Nif(dst).shape(g['cd'].SHAPE)
moved = sum(1 for i in at if back.position(i) != g['pos'][i])
print(f'{dst}: {moved} canal vertices posed around a shaft {depth} deep along VAGINA_PATH (radius {g["pd"].SHAFT_RADIUS}); '
      f'shaft points: {[tuple(round(x, 2) for x in p) for p in shaft]}')
