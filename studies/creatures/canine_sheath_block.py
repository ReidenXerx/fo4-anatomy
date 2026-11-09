# ---------------------------------------------------------------- sheath (fur) + its opening lining (penis material)
# The sheath RIDES OUR PENIS: sheath param ts (0 rear cap .. 1 opening) maps to the penis' t; at rest it covers
# root..just past the tip, in Erection it pulls back behind the knot. Its radius = the penis' local radius in that
# state (an envelope over a short stretch) x 1.18 + a margin, so nothing pokes through in any state. Closed rear cap,
# a rolled lip snug on the penis at the opening, and a pink lining hugging the penis just inside it.
# UV: each sheath vertex carries a SAMPLE point on the belly: its own y, x = 0.4 + its arc distance from the
# underside line, so Blender projects belly fur unrolled around the tube (no stretched streaks).
TS0 = -0.12
T_OPEN = 1.02
T_OPEN_E = 0.10


def pen_radius(t, state):
    tt = min(max(t, 0.0), 1.0)
    _, R = PS[state]
    ratio = np.clip(interp(smooth(R), tt) / max(interp(smooth(Rr), tt), 1e-3), 0.7, 2.6)
    return pen_profile(tt) * R_mid * 0.95 * ratio * (1 + (0.50 * knot(tt) if state == 'Erection' else 0.0))


def sheath_t(ts, state):
    top = T_OPEN_E if state == 'Erection' else T_OPEN
    return TS0 + (top - TS0) * ts


def env(t, state, span=0.05):
    return max(pen_radius(t + d, state) for d in np.linspace(-span, span, 5))


def sh_radius(ts, state):
    r = env(sheath_t(ts, state), state) * 1.18 + 0.35 * R_mid
    if ts < 0.14:
        r *= 0.30 + 0.70 * (ts / 0.14) ** 0.5
    return r


def lip_radius(state):
    return env(sheath_t(1.0, state), state, 0.03) * 1.06 + 0.04


def on_pen(t, th, r, state, axial=0.0):
    C, _ = PS[state]
    c, T, X, N = frame_at(C, t, pen.tc)
    return c + T * axial + r * (math.cos(th) * X + math.sin(th) * N)


def angdist(th):
    return abs(((th - math.pi / 2 + math.pi) % (2 * math.pi)) - math.pi)


# rows: (ts, radius(state) fn, axial)
SH_ROWS = [(ts, (lambda st, ts=ts: sh_radius(ts, st)), 0.0) for ts in
           [0.0, 0.03, 0.07, 0.14] + list(np.linspace(0.2, 0.92, 10)) + [0.97, 1.0]]
SH_ROWS += [(1.0, (lambda st: 0.5 * (sh_radius(1.0, st) + lip_radius(st))), 0.07),
            (1.0, lip_radius, 0.03)]
sverts, suvs, stris, smor, ssample = [], [], [], {n: [] for n in mor}, []
sh_rows = []
for ts, rfn, axial in SH_ROWS:
    row = []
    for s in range(SEG + 1):
        th = 2 * math.pi * s / SEG + math.pi / 2
        p0 = on_pen(sheath_t(ts, ''), th, rfn(''), '', axial)
        sverts.append(p0)
        suvs.append((s / SEG, ts))
        ssample.append((0.4 + rfn('') * angdist(th), float(p0[1])))
        for n in smor:
            smor[n].append(on_pen(sheath_t(ts, n), th, rfn(n), n, axial) - p0)
        row.append(len(sverts) - 1)
    sh_rows.append(row)
for r in range(len(sh_rows) - 1):
    for s in range(SEG):
        a, b, c, d = sh_rows[r][s], sh_rows[r][s + 1], sh_rows[r + 1][s + 1], sh_rows[r + 1][s]
        stris += [(a, b, c), (a, c, d)]
cpt = on_pen(sheath_t(0.0, ''), 0, 0, '')                                 # rear cap point
sverts.append(cpt)
suvs.append((0.5, 0.0))
ssample.append((0.4, float(cpt[1])))
for n in smor:
    smor[n].append(on_pen(sheath_t(0.0, n), 0, 0, n) - cpt)
for s in range(SEG):
    stris.append((sh_rows[0][s], len(sverts) - 1, sh_rows[0][s + 1]))

# lining (penis material, in the penis shape): from the lip's inner edge back inside, hugging the penis
lin_rows = []
for k, (ts, axial) in enumerate(((1.0, 0.03), (0.96, 0.0), (0.88, 0.0))):
    row = []
    for s in range(SEG + 1):
        th = 2 * math.pi * s / SEG + math.pi / 2
        rf = (lambda st: lip_radius(st)) if k == 0 else (lambda st, ts=ts: env(sheath_t(ts, st), st, 0.03) * 1.06 + 0.04)
        p0 = on_pen(sheath_t(ts, ''), th, rf(''), '', axial)
        verts.append(p0)
        uvs.append((s / SEG, 0.02 + 0.01 * k))
        for n in mor:
            mor[n].append(on_pen(sheath_t(ts, n), th, rf(n), n, axial) - p0)
        row.append(len(verts) - 1)
    lin_rows.append(row)
quads(lin_rows, tris_p, flip=True)                                      # faces inward (seen through the opening)
