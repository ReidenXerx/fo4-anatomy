import collections, pathlib, sys
import numpy as np
sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif
for p in sys.argv[1:]:
    m = nif.Nif(pathlib.Path(p))
    print(p)
    for s in m.shapes():
        P = np.array(s.positions())
        names, xf = m.skin(s)
        print(f'  {s.name}: {s.count}v {m.types[s.index]} bbox {P.min(0).round(1)} {P.max(0).round(1)} bones {len(names) if names else 0}')
