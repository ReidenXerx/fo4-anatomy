"""Control / fallback variant of 'Anatomy Feral Ghouls.esp' WITHOUT the Bloated Glowing One ARMA (0A96B7): a female
Bloated then wears the male (vanilla-geometry) mesh, which tells whether the dismember crash is our _F mesh or the
engine's female cut path. Same file name (drop-in swap).  python -I feral_noblo.py <out dir>"""
import pathlib
import sys

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-refit\tools')
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import esl  # noqa: E402
from feral_all import ARMAS, DATA, arma_with_female, write_plugin  # noqa: E402

out = pathlib.Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
fo4 = esl.Plugin(DATA / 'Fallout4.esm')
recs = []
for r in fo4.records:
    if r[0] == 'R' and r[2] == 'ARMA' and r[3] in ARMAS and r[3] != 0x0A96B7:
        fpath = f'Actors\\FeralGhoul\\CharacterAssets\\{ARMAS[r[3]]}_F.nif'
        recs.append((r[3], r[4], arma_with_female(fo4.body(r), fpath)))
write_plugin(out / 'Anatomy Feral Ghouls.esp', ['Fallout4.esm'], recs)
print(len(recs), 'records ->', out / 'Anatomy Feral Ghouls.esp')
