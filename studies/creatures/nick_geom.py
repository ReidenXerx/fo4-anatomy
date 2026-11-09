"""Our synth penis for SynthGen2Body.nif (Nick Valentine and every gen2 synth; replaces UAP's Synt_Gen2_Penis on the
same path, same bones, same morph names). Built in numpy, in the SHAPE SPACE of UAP's penis:
  Synt_Gen2_Penis       rigid polymer plates (one per penis bone, telescoping: in erection the plates keep their length
                        and the rubber between them shows), a domed glans with a flared rim, a seamed pod; the synth
                        BODY material (skin swaps apply), UVs in a plain window of the skin texture
  Synt_Gen2_PenisJoints dark rubber: the joint sleeve between plates, a socket collar at the root, the tip port;
                        Gen2a.BGSM (the endoskeleton texture), UVs in a dark even window
The centreline of each state (rest + each UAP morph) is a Catmull-Rom spline through the means of UAP's per-bone
vertex regions (root, Penis_01..05, tip) - the same vertex sets carried by the morph, so our plates follow UAP's
measured bend. Shaft Width = radial; Sack Size and the pod's share of every morph = nearest UAP sack deltas.
    python -I nick_geom.py <out.json>"""
import json
import math
import sys

import numpy as np

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif  # noqa: E402
import tri_sync  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
UAP_NIF = r'D:\F4Output\creatures\nick\src\uap\SynthGen2Body.nif'
UAP_TRI = r'D:\Vortex\fallout4\mods\1387286231_UAPv2.6.64-1+2\Meshes\Actors\Synths\SynthGen2Body.tri'
VAN_NIF = r'D:\F4Output\creatures\nick\src\Fallout4 - Meshes\meshes\actors\synths\synthgen2body.nif'
SKIN_UV = (0.836, 0.905, 0.695, 0.825)          # plain synth skin window (u0, u1, v0, v1)
RUBBER_UV = (0.555, 0.589, 0.016, 0.115)        # dark even endoskeleton window
SHAFT_MORPHS = ['Erection', 'Erection Up', 'Erection Down', 'Penis Adjust']
SEG = 24

m = nif.Nif(UAP_NIF)
sh = m.shape('Synt_Gen2_Penis')
P = np.array(sh.positions())
bones, _ = m.skin(sh)
W = np.zeros((len(P), len(bones)))
for i in range(len(P)):
    for slot, w in sh.skin_weights(i):
        W[i, slot] += w
bi = {b: k for k, b in enumerate(bones)}
dom = W.argmax(1)
region = {k: np.where(dom == bi[f'Penis_0{k}'])[0] for k in range(1, 6)}
sack = np.where(dom == bi['Penis_Balls_01'])[0]
tri = {s: {n: (mult, d) for n, mult, d in ms} for s, ms in tri_sync.read(UAP_TRI)}['Synt_Gen2_Penis']


def morphed(name):
    Q = P.copy()
    if name:
        mult, d = tri[name]
        for i, v in d.items():
            Q[i] += np.array(v, float) * mult
    return Q


# tip = the 12 glans vertices farthest along the last segment, chosen once (rest) and carried by index
d45 = P[region[5]].mean(0) - P[region[4]].mean(0)
tip_set = region[5][np.argsort(P[region[5]] @ d45)[-12:]]


def nodes(Q):
    n = [Q[region[k]].mean(0) for k in range(1, 6)]
    root = n[0] - (n[1] - n[0]) * 0.9
    return np.array([root] + n + [Q[tip_set].mean(0)])         # node index s: 0 root, 1..5 bones, 6 tip


class Curve:
    """Catmull-Rom through the nodes, sampled densely; position/frame by node parameter s or by arclength."""

    def __init__(self, Q):
        n = nodes(Q)
        ext = np.vstack([2 * n[0] - n[1], n, 2 * n[-1] - n[-2]])
        self.s = np.linspace(0, 6, 601)
        pts = []
        for s in self.s:
            k = min(int(s), 5)
            t = s - k
            p0, p1, p2, p3 = ext[k], ext[k + 1], ext[k + 2], ext[k + 3]
            pts.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
        self.p = np.array(pts)
        self.L = np.concatenate([[0], np.cumsum(np.linalg.norm(self.p[1:] - self.p[:-1], axis=1))])

    def ell(self, s):
        return float(np.interp(s, self.s, self.L))

    def at_ell(self, ell):
        """centre, T, X, N at arclength ell (extrapolated linearly past either end)."""
        e = min(max(ell, 0.0), self.L[-1])
        k = min(np.searchsorted(self.L, e, side='right') - 1, len(self.L) - 2)
        f = (e - self.L[k]) / (self.L[k + 1] - self.L[k] + 1e-12)
        c = self.p[k] * (1 - f) + self.p[k + 1] * f
        T = self.p[min(k + 2, len(self.p) - 1)] - self.p[max(k - 1, 0)]
        T /= np.linalg.norm(T)
        c = c + T * (ell - e)
        X = np.array([1.0, 0, 0])
        N = np.cross(T, X)
        N /= np.linalg.norm(N)
        X = np.cross(N, T)
        return c, T, X, N

    def at_s(self, s):
        return self.at_ell(self.ell(s) + (s - min(max(s, 0), 6)) * (self.L[-1] / 6))


curves = {'': Curve(P)}
for name in SHAFT_MORPHS:
    curves[name] = Curve(morphed(name))
rest = curves['']
half_w = [np.percentile(np.abs(P[region[k]][:, 0]), 95) for k in range(1, 6)]
R0 = 0.95 * float(np.median(half_w[:4]))
print('rest length', round(rest.L[-1], 2), 'erect length', round(curves['Erection'].L[-1], 2), 'R0', round(R0, 2),
      'half widths', np.round(half_w, 2))
print('rest nodes', nodes(P).round(2).tolist())
print('erect nodes', nodes(morphed('Erection')).round(2).tolist())


# ---------------------------------------------------------------- design: each vertex = (anchor, theta, rho, axial)
# anchor ('s', s) = rides the curve at node parameter s (stretchy rubber);
# anchor ('ell', s0, a) = rides at arclength(s0) + a (a rigid plate centred at s0 keeps its length)
class Part:
    def __init__(self):
        self.anchor, self.th, self.rho, self.ax, self.uv, self.w = [], [], [], [], [], []
        self.pod = []
        self.faces = []

    def add(self, anchor, th, rho, uv, w, ax=0.0):
        for lst, v in ((self.anchor, anchor), (self.th, th), (self.rho, rho), (self.ax, ax), (self.uv, uv),
                       (self.w, w), (self.pod, None)):
            lst.append(v)
        return len(self.anchor) - 1

    def add_pod(self, p, uv, w):
        k = self.add(None, 0, 0, uv, w)
        self.pod[k] = p
        return k


def ring_strip(part, rings, uvwin):
    """rings: [(anchor, rho, w, axial, vfrac)] -> quads; UV wraps theta across the window, vfrac runs along it."""
    u0, u1, v0, v1 = uvwin
    rows = []
    for anchor, rho, w, ax, vf in rings:
        row = []
        for s in range(SEG + 1):                       # +1: duplicated seam column (seam on the underside)
            th = 2 * math.pi * s / SEG + math.pi / 2
            row.append(part.add(anchor, th, rho, (u0 + (u1 - u0) * s / SEG, v0 + (v1 - v0) * vf), w, ax))
        rows.append(row)
    for r in range(len(rows) - 1):
        for s in range(SEG):
            part.faces.append((rows[r][s], rows[r][s + 1], rows[r + 1][s + 1], rows[r + 1][s]))
    return rows


def taper(s):
    return R0 * (1.0 - 0.025 * max(s - 1, 0.0))


plates, joints = Part(), Part()
ere = curves['Erection']
SLEEVE = 0.84                   # rubber sleeve radius (x R0)
INNER = 0.865                   # plate end rings close down to here, just above the sleeve
COVER = 0.88                    # plate length = this share of its ERECT span (telescoping: they nest at rest)


def plate_radius(k):            # nested sleeves: each plate slides inside the one nearer the root
    return R0 * (1.10 - 0.055 * (k - 1))


def closed_plate(k, a0, a1, Rk, w, v0, v1):
    """A rigid sleeve: outer shell with a small bevel at each end + flat end rings down to INNER (separate strips,
    so the edges stay hard)."""
    span = a1 - a0
    offs = [a0, a0 + 0.06, a0 + 0.16] + list(np.linspace(a0 + 0.16, a1 - 0.10, 5)[1:-1]) + [a1 - 0.10, a1 - 0.03, a1]
    rad = [0.95, 0.99, 1.0, 1.0, 1.0, 1.0, 1.0, 0.995, 0.97]
    vf = lambda a: v0 + (v1 - v0) * (a - a0) / span                                  # noqa: E731
    ring_strip(plates, [(('ell', k, a), Rk * r, w, 0.0, vf(a)) for a, r in zip(offs, rad)], SKIN_UV)
    # end rings: winding (ring order) sets the facing - outer->inner faces +T, so the root-side end goes inner->outer
    ring_strip(plates, [(('ell', k, a0), R0 * INNER, w, 0.0, vf(a0) + 0.01), (('ell', k, a0), Rk * 0.95, w, 0.0,
                                                                              vf(a0))], SKIN_UV)
    ring_strip(plates, [(('ell', k, a1), Rk * 0.97, w, 0.0, vf(a1)), (('ell', k, a1), R0 * INNER, w, 0.0,
                                                                      vf(a1) + 0.01)], SKIN_UV)


# plates for Penis_01..04, centred on node k
plate_len = {}
for k in range(1, 5):
    L = COVER * (ere.ell(k + 0.5) - ere.ell(k - 0.5))
    plate_len[k] = L
    a0 = -L / 2 - (0.15 if k == 1 else 0.0)                      # the first plate starts just inside the collar
    closed_plate(k, a0, L / 2, plate_radius(k), {f'Penis_0{k}': 1.0},
                 (rest.ell(k) + a0) / rest.L[-1], (rest.ell(k) + L / 2) / rest.L[-1])
# glans (Penis_05), centred on node 5, rigid: a base sleeve that nests in plate 4, a flared rim beyond plate 4's
# reach even at rest, then an elliptical dome down to a small port
back = COVER * (ere.ell(5) - ere.ell(4.5))
front = rest.ell(6) - rest.ell(5)
rest_reach4 = rest.ell(4) + plate_len[4] / 2 - rest.ell(5)       # where plate 4 ends at rest, relative to node 5
rim_a = max(rest_reach4 + 0.15, -back + 0.3)
Rb = plate_radius(5)
prof = [(-back, 0.95), (-back + 0.06, 0.99), (rim_a - 0.25, 1.0), (rim_a - 0.08, 1.10), (rim_a, 1.16),
        (rim_a + 0.12, 1.12), (rim_a + 0.30, 1.05)]
dome0 = rim_a + 0.30
for e in np.linspace(0.08, 1.0, 9):
    prof.append((dome0 + (front - dome0) * e, max(1.05 * math.sqrt(max(1 - e ** 2.4, 0.0)), 0.20 * R0 / Rb)))
w5 = {'Penis_05': 1.0}
rings = [(('ell', 5, a), Rb * r, w5, 0.0, (rest.ell(5) + a) / rest.L[-1]) for a, r in prof]
ring_strip(plates, rings, SKIN_UV)
ring_strip(plates, [(('ell', 5, -back), R0 * INNER, w5, 0.0, 0.01), (('ell', 5, -back), Rb * 0.95, w5, 0.0, 0.0)],
           SKIN_UV)
glans_tip_a = prof[-1][0]
glans_k = 5


def sleeve_w(s):
    """Rubber sleeve: rigid with the plate it lies under; blended across each joint (k + 0.5)."""
    for j in range(1, 5):
        if abs(s - (j + 0.5)) < 0.12:
            f = (s - (j + 0.5 - 0.12)) / 0.24
            return {f'Penis_0{j}': 1 - f, f'Penis_0{j + 1}': f}
    k = int(min(max(round(s), 1), 5))
    return {f'Penis_0{k}': 1.0}


ss = sorted(set([0.55, 0.8, 1.0] + [x for j in range(1, 5) for x in (j + 0.5 - 0.2, j + 0.5 - 0.1, j + 0.5,
                                                                       j + 0.5 + 0.1, j + 0.5 + 0.2)] + [4.9]))
rings = [(('s', s), R0 * SLEEVE, sleeve_w(s), 0.0, (s - ss[0]) / (ss[-1] - ss[0])) for s in ss]
ring_strip(joints, rings, RUBBER_UV)
# root collar: a rubber socket flange lying on the body (axis = forward, slightly down; not the hanging tangent),
# the shaft leaving through its opening
COLLAR_C = rest.at_s(0.15)[0]
COLLAR_T = np.array([0.0, 1.0, -0.30]) / np.linalg.norm([0.0, 1.0, -0.30])
ca = [-0.70, -0.25, 0.00, 0.18, 0.34, 0.45]
cr = [1.30, 1.50, 1.52, 1.38, 1.12, 0.94]
# 100% Pelvis_skin: a socket fixed to the body. Penis_00 weights here (up to 0.6) let AAF's root swings drag the flange
# into long dark wedges (Fo4-mcp 11-09, BP70 cowgirl); the shaft's first plate reaches back inside the socket instead
rings = [(('fix', a), R0 * r, {'Pelvis_skin': 1.0}, 0.0, k / 5) for k, (a, r) in enumerate(zip(ca, cr))]
collar_first = len(joints.anchor)
ring_strip(joints, rings, RUBBER_UV)
collar = range(collar_first, len(joints.anchor))                 # sits on the body: no morph moves it
# tip port: from the dome's last ring, a small cup sunk into the glans
port = [(('ell', glans_k, glans_tip_a), 0.20 * R0, {'Penis_05': 1.0}, 0.0, 0.0),
        (('ell', glans_k, glans_tip_a), 0.12 * R0, {'Penis_05': 1.0}, -0.10, 0.5),
        (('ell', glans_k, glans_tip_a), 0.02, {'Penis_05': 1.0}, -0.22, 1.0)]
ring_strip(joints, port, RUBBER_UV)

# pod: an ellipsoid at UAP's sack, with a seam crease down the middle (x = 0)
S = P[sack]
lo, hi = np.percentile(S, 4, axis=0), np.percentile(S, 96, axis=0)
ax = (hi - lo) / 2 * 1.05
cb = (hi + lo) / 2
top_z = cb[2] + ax[2]
LAT, LON = 14, 28
grid = []
for i in range(LAT + 1):
    phi = math.pi * i / LAT
    row = []
    for j in range(LON + 1):
        lam = 2 * math.pi * j / LON
        d = np.array([math.sin(phi) * math.cos(lam), math.sin(phi) * math.sin(lam), math.cos(phi)])
        crease = 1.0 - 0.16 * math.exp(-(d[0] / 0.09) ** 2) * math.sin(phi)
        p = cb + d * ax * crease
        # rigid on the balls bone (a Pelvis_skin blend stretched into a pale sheet when AAF moved the bone), and a
        # PLANAR UV (side view: y, z) - the spherical wrap pinched into a swirl at its poles
        w = {'Penis_Balls_01': 1.0}
        u0, u1, v0, v1 = SKIN_UV
        uu = 0.5 + 0.5 * (p[1] - cb[1]) / (ax[1] * 1.1)
        vv = 0.5 - 0.5 * (p[2] - cb[2]) / (ax[2] * 1.1)
        row.append(plates.add_pod(p, (u0 + (u1 - u0) * uu, v0 + (v1 - v0) * vv), w))
    grid.append(row)
for i in range(LAT):
    for j in range(LON):
        plates.faces.append((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))


# ---------------------------------------------------------------- positions per state
def place(part, curve, width=0.0):
    out = []
    for k, anchor in enumerate(part.anchor):
        if anchor is None:
            out.append(part.pod[k])
            continue
        if anchor[0] == 'fix':
            T = COLLAR_T
            X = np.array([1.0, 0, 0])
            N = np.cross(T, X)
            c = COLLAR_C + T * anchor[1]
        elif anchor[0] == 's':
            c, T, X, N = curve.at_s(anchor[1])
        else:
            c, T, X, N = curve.at_ell(curve.ell(anchor[1]) + anchor[2])
        r = part.rho[k] * (1.0 + width)
        th = part.th[k]
        out.append(c + T * part.ax[k] + r * (math.cos(th) * X + math.sin(th) * N))
    return np.array(out)


def pod_delta(part, name):
    out = np.zeros((len(part.anchor), 3))
    D = morphed(name)[sack] - S
    for k, p in enumerate(part.pod):
        if p is not None:
            near = np.argsort(np.linalg.norm(S - p, axis=1))[:4]
            out[k] = D[near].mean(0)
    return out


result = {}
for nm, part in (('Synt_Gen2_Penis', plates), ('Synt_Gen2_PenisJoints', joints)):
    restP = place(part, rest)
    is_pod = np.array([a is None for a in part.anchor])
    morphs = {}
    for name in SHAFT_MORPHS:
        d = place(part, curves[name]) - restP
        d[is_pod] = pod_delta(part, name)[is_pod]
        if part is joints:
            d[list(collar)] = 0
        morphs[name] = d.tolist()
    sw = place(part, rest, width=0.35) - restP
    sw[is_pod] = 0
    morphs['Shaft Width'] = sw.tolist()
    morphs['Sack Size'] = pod_delta(part, 'Sack Size').tolist()
    tris = []
    for a, b, c, d in part.faces:
        tris += [(a, b, c), (a, c, d)]
    result[nm] = dict(verts=restP.tolist(), uv=part.uv, weights=part.w, tris=tris, morphs=morphs)
    E = restP + np.array(morphs['Erection'])
    print(nm, len(restP), 'verts', len(tris), 'tris', 'rest bbox', restP.min(0).round(2), restP.max(0).round(2),
          'erect bbox', E.min(0).round(2), E.max(0).round(2))
v = nif.Nif(VAN_NIF)
vb = v.shape('Body:0')
vbones, _ = v.skin(vb)
result['_body_weights'] = [[(vbones[s], w) for s, w in vb.skin_weights(i)] for i in range(vb.count)]
result['_body_positions'] = np.array(vb.positions()).tolist()
result['_uap_penis_bbox'] = [P.min(0).tolist(), P.max(0).tolist()]
json.dump(result, open(sys.argv[1], 'w'))
print('uap bbox', P.min(0).round(2), P.max(0).round(2), 'uap erect bbox', morphed('Erection').min(0).round(2),
      morphed('Erection').max(0).round(2))
