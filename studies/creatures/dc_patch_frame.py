"""one-off: move dc_geom.py's vent onto the belly-normal frame (s local to the entry)."""
import pathlib
import sys

p = pathlib.Path(sys.argv[1])
s = p.read_text(encoding='utf-8')
REP = [
    ("print('entry', ENTRY.round(2), 'arc', round(S_E, 2), 'belly slope', round(float(np.interp(ENTRY[1], YS, np.gradient(ZS, YS))), 2))",
     "slope = float(np.interp(ENTRY[1], YS, np.gradient(ZS, YS)))\n"
     "print('entry', ENTRY.round(2), 'arc', round(S_E, 2), 'belly slope', round(slope, 2))\n"
     "_n0 = np.array([0.0, slope, -1.0]) / np.hypot(slope, 1.0)\n"
     "_t0 = np.cross(np.array([1.0, 0.0, 0.0]), _n0)\n"
     "_t0 = _t0 if _t0[2] > 0 else -_t0\n"
     "FRAME.update(P0=ray(ENTRY + 10.0 * _n0, -_n0)[0], n0=_n0, t0=_t0, b0=np.array([1.0, 0.0, 0.0]))\n"
     "S_E = 0.0                                         # vent coordinates: s along t0 from the entry\n"
     "print('frame n0', _n0.round(3), 't0', _t0.round(3), 'P0', FRAME['P0'].round(2))"),
    ("tri_isl.append(int(T_ISL[ray_up(cen[0], cen[1])[1]]))",
     "tri_isl.append(int(T_ISL[ray(cen + 6.0 * FRAME['n0'], -FRAME['n0'])[1]]))"),
    ("wts = [body_sample(rest[vi][0], rest[vi][1])[1] for vi in src]",
     "wts = [body_sample_pt(rest[vi])[1] for vi in src]"),
    ("fw = [body_sample(max(abs(p[0]), 0.35) * (1 if half == 'R' else -1), p[1])[1]",
     "fw = [body_sample_pt(np.array([max(abs(p[0]), 0.35) * (1 if half == 'R' else -1), p[1], p[2]]))[1]"),
    ("fw_f = [body_sample(max(abs(p[0]), 0.35) * (1 if half == 'R' else -1), p[1])[1]",
     "fw_f = [body_sample_pt(np.array([max(abs(p[0]), 0.35) * (1 if half == 'R' else -1), p[1], p[2]]))[1]"),
    ("(lambda d: (d.min(), d.max()))(np.array([p[2] - surf_z(p[0], p[1]) for p in rim]) * -1)))",
     "(lambda d: (d.min(), d.max()))(np.array([(p - ray(p + 6.0 * FRAME['n0'], -FRAME['n0'])[0]) @ FRAME['n0']\n"
     "                                         for p in rim]))))"),
    ("NL[i] @ surface(p[0], 0 * p[0] + float(np.interp(p[1], YS, SS)))[1] > 0", "NL[i] @ FRAME['n0'] > 0"),
    ("NF_[i] @ surface(p[0], float(np.interp(p[1], YS, SS)))[1] > 0", "NF_[i] @ FRAME['n0'] > 0"),
]
for a, b in REP:
    if a not in s:
        raise SystemExit('missing: ' + a[:70])
    s = s.replace(a, b)
p.write_text(s, encoding='utf-8')
print('patched', len(REP))
