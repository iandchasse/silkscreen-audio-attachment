"""Audio attachment solids (E frame): BASE (rev C, left boss at x 12), new audio LID, PCBA from geometry.json (proxy if missing)."""
import json
import math

import numpy as np

import params as P
import util as U

N = 36  # polygon segments per 90 deg of arc


def arc_pts(c0, c1, r, a0, a1, n=N):
    """(c0 + r cos a, c1 + r sin a) for a from a0 to a1 (deg)."""
    k = max(2, int(abs(a1 - a0) / 90 * n))
    return [(c0 + r * math.cos(math.radians(a0 + (a1 - a0) * i / k)),
             c1 + r * math.sin(math.radians(a0 + (a1 - a0) * i / k))) for i in range(k + 1)]


def round_poly(pts, radii, n=N):
    """Closed polygon with a tangent arc of radius radii[i] at vertex i (0 = sharp corner)."""
    out, m = [], len(pts)
    for i in range(m):
        p0, p1, p2 = (np.array(pts[(i - 1) % m], float), np.array(pts[i], float), np.array(pts[(i + 1) % m], float))
        r = radii[i]
        if r <= 0:
            out.append(tuple(p1))
            continue
        vin, vout = (p1 - p0) / np.linalg.norm(p1 - p0), (p2 - p1) / np.linalg.norm(p2 - p1)
        cr = vin[0] * vout[1] - vin[1] * vout[0]
        phi = math.acos(max(-1.0, min(1.0, float(vin @ vout))))
        t = r * math.tan(phi / 2)
        t1, t2 = p1 - vin * t, p1 + vout * t
        c = t1 + np.array([-vin[1], vin[0]]) * r * (1 if cr > 0 else -1)
        a1, a2 = math.atan2(*(t1 - c)[::-1]), math.atan2(*(t2 - c)[::-1])
        da = (a2 - a1) % (2 * math.pi) if cr > 0 else -((a1 - a2) % (2 * math.pi))
        k = max(2, int(abs(da) / (math.pi / 2) * n))
        out += [(c[0] + r * math.cos(a1 + da * j / k), c[1] + r * math.sin(a1 + da * j / k)) for j in range(k + 1)]
    return out


# ------------------------------------------------------------------ PCBA data
def proxy_geometry():
    """Proxy PCBA from the spec numbers (used until pcb/build/geometry.json exists)."""
    jb, jn = P.JACK_BODY, P.JACK_NOSE
    pins = []
    bodies = []
    pos = {'J1': [(44.502, -3.810), (47.042, -3.810), (49.582, -3.810), (52.122, -3.810)], 'J2': [(49.582, -1.270)],
           'J3': [(57.202, -1.270)]}
    for ref, pp in pos.items():
        for x, z in pp:
            pins.append({'ref': ref, 'x': x, 'z': z, 'square': 0.64, 'y_post_tip': 108.1, 'y_tail_tip': 119.6})
            bodies.append({'ref': ref, 'body_box': {'x': [x - 1.27, x + 1.27], 'z': [z - 1.27, z + 1.27], 'y': [114.1, 116.6]}})
    smd = [(9.8, 15.5, 2.5, 5.2), (16.5, 24.0, 1.5, 5.4), (25.0, 31.5, -5.4, -2.0), (25.0, 29.0, 1.0, 3.0), (30.0, 35.0, 1.0, 5.0),
           (41.0, 46.0, 0.5, 5.0), (47.0, 52.0, 2.0, 5.0), (53.0, 61.0, 1.5, 5.4), (15.6, 22.0, -5.4, -3.0)]
    parts = [{'ref': f'P{i}', 'body_box': {'x': [x0, x1], 'z': [z0, z1], 'y': [117.6, 117.6 + P.SMD_H]}}
             for i, (x0, x1, z0, z1) in enumerate(smd)]
    return {'pcb': {'outline_xz': None, 'bbox_xz': [[-2.5, 62.5], [-6.0, 6.0]]},
            'holes': [{'x': x, 'z': z, 'dia': P.HOLE_D} for x, z in P.HOLES], 'parts': parts,
            'jack': {'body_box': {'x': list(jb['x']), 'y': list(jb['y']), 'z': list(jb['z'])},
                     'nose': {'x': list(jn['x']), 'dia': jn['dia'], 'axis_y': jn['axis_y'], 'axis_z': jn['axis_z']}},
            'header': {'bodies': bodies, 'pins': pins, 'j6_face_y': list(P.J6_FACE)}}


def pcba_data():
    """Returns (data, source): the PCB agent's geometry.json when present and usable, else the proxy."""
    try:
        import os
        import time
        g = json.loads(P.PCB_GEOM.read_text())
        miss = [k for k in ('pcb', 'holes', 'parts', 'header', 'jack') if k not in g]
        if not miss:
            return g, f"geometry.json rev {g.get('rev')} ({g.get('date')}, file mtime {time.ctime(os.path.getmtime(P.PCB_GEOM))})"
        print('geometry.json present but missing', miss, '- using the proxy')
    except FileNotFoundError:
        pass
    except Exception as ex:
        print('geometry.json unreadable:', ex)
    return proxy_geometry(), 'PROXY from the spec numbers'


def outline_xz(g):
    o = g['pcb'].get('outline_xz')
    if o:
        return [tuple(p) for p in o]
    (x0, x1), (z0, z1) = g['pcb']['bbox_xz']
    r = 2.0
    return arc_pts(x1 - r, z0 + r, r, -90, 0) + arc_pts(x1 - r, z1 - r, r, 0, 90) + \
        arc_pts(x0 + r, z1 - r, r, 90, 180) + arc_pts(x0 + r, z0 + r, r, 180, 270)


def tail_tip(g):
    return max(p['y_tail_tip'] for p in g['header']['pins'])


def jack_axis(g):
    n = g['jack']['nose']
    return n['axis_y'], n['axis_z']


def roof_under(g):
    top_parts = max([p['body_box']['y'][1] for p in g['parts']] + [g['jack']['body_box']['y'][1], tail_tip(g)])
    return round(top_parts + P.ROOF_CLR, 2)


def lid_top(g):
    return round(roof_under(g) + P.ROOF_T, 2)


def bbox_solid(b, grow=0.0):
    return U.box(b['x'][0] - grow, b['x'][1] + grow, b['y'][0] - grow, b['y'][1] + grow, b['z'][0] - grow, b['z'][1] + grow)


def build_pcba(g):
    y0 = g['pcb'].get('underside_y_seated', P.PCB_Y0)
    t = g['pcb'].get('thickness', P.PCB_T)
    pcb = U.prism_y(outline_xz(g), y0, y0 + t)
    pcb = U.cut(pcb, *[U.cyl_y(h['x'], h['z'], h['dia'] / 2, y0 - 1, y0 + t + 1) for h in g['holes']])
    smd = U.fuse(*[bbox_solid(p['body_box']) for p in g['parts']])
    bodies = U.fuse(*[bbox_solid(b['body_box']) for b in g['header']['bodies']])
    pins = U.fuse(*[U.box(p['x'] - p['square'] / 2, p['x'] + p['square'] / 2, p['y_post_tip'], p['y_tail_tip'],
                          p['z'] - p['square'] / 2, p['z'] + p['square'] / 2) for p in g['header']['pins']])
    j = g['jack']
    ay, az = jack_axis(g)
    n = j['nose']
    jack = U.fuse(bbox_solid(j['body_box']), U.cyl_x(ay, az, n['dia'] / 2, n['x'][0], n['x'][1] + 0.01))
    return {'pcb': pcb, 'smd': smd, 'header_bodies': bodies, 'pins': pins, 'jack': jack}


# ------------------------------------------------------------------ outlines
def cap_xy(ybot, top, inset=0.0):
    """Cap outline in the X-Y (front) view: sides at XO0/XO1, R6.25 corners, flat top. inset > 0 offsets it inward
    (concentric arcs): the rabbet / lid-skirt boundaries."""
    cy = top - P.XY_R
    ybot = min(ybot, cy - 0.5)          # the arcs start at cy; callers clip the bottom themselves
    r = P.XY_R - inset
    return [(P.XO0 + inset, ybot), (P.XO1 - inset, ybot)] + arc_pts(P.CORNER_X[1], cy, r, 0, 90) + \
        arc_pts(P.CORNER_X[0], cy, r, 90, 180)


def case_cavity():
    """Stock case top region grown by CL on the sides/front/back (top face kept at 115.60)."""
    c, top = P.CL, P.CASE_TOP
    x0, x1, zb, zf = P.CX0 - c, P.CX1 + c, P.CZB - c, P.CZF + c
    r5 = P.CORNER_R + c
    cy = top - r5
    xy = [(x0, 90.0), (x1, 90.0)] + arc_pts(P.CORNER_X[1], cy, r5, 0, 90) + arc_pts(P.CORNER_X[0], cy, r5, 90, 180)
    rb, rf = P.BACK_R + c, P.FRONT_R + c
    yz = [(90.0, zb)] + arc_pts(top - rb, P.BACK_C[1], rb, -90, 0) + arc_pts(top - rf, P.FRONT_C[1], rf, 0, 90) + [(90.0, zf)]
    vb, vf = P.VBACK_R + c, P.VFRONT_R + c
    xz = arc_pts(-2.09, -4.7, vb, 180, 270) + arc_pts(62.09, -4.7, vb, 270, 360) + \
        arc_pts(62.29, 4.2, vf, 0, 90) + arc_pts(-2.29, 4.2, vf, 90, 180)
    s1 = U.prism_z(xy, -12, 14)
    s2 = U.prism_x(yz, -8, 68)
    s3 = U.prism_y(xz, 90.0, top + 0.5)
    return s1.intersect(s2).intersect(s3).clean()


def slope():
    return (P.EMIT_Z[0] - P.WIN_EDGE[1]) / (P.EMIT_Y - P.WIN_EDGE[0])


def graze_z(y, margin=P.LIGHT_MARGIN):
    """z of the grazing ray (kept from rev C: it shapes the base's front tongue cut; the base is unchanged)."""
    s = slope()
    return P.WIN_EDGE[1] + s * (y - P.WIN_EDGE[0]) - margin * math.sqrt(1 + s * s)


def light_cut():
    """Everything the base may not occupy in front of the case face over the window width."""
    y0 = P.JAW_Y0
    s = slope()
    yl = P.WIN_EDGE[0] + (P.LED_CLR_Z - P.WIN_EDGE[1] + P.LIGHT_MARGIN * math.sqrt(1 + s * s)) / s
    yz = [(100.0, P.CZF + P.CL), (y0, P.CZF + P.CL), (y0, graze_z(y0)), (yl, P.LED_CLR_Z), (118.0, P.LED_CLR_Z),
          (118.0, 20.0), (100.0, 20.0)]
    return U.prism_x(yz, -2.29, 62.29)


def fin_yz():
    """Side-view (Y-Z) region of the skirt incl. the front-corner X guides: everything at y >= Y_BOT, plus z above the
    45 deg line through (Y_BOT, FIN_Z) down to FIN_Y; concave corner filleted FIN_RC, convex tip rounded FIN_RV."""
    from shapely.geometry import Polygon
    y0, z0 = P.Y_BOT, P.FIN_Z
    zt = z0 + (y0 - P.FIN_Y)
    s = Polygon([(y0 + 12, -20), (y0 + 12, 30), (P.FIN_Y, 30), (P.FIN_Y, zt), (y0, z0), (y0, -20)])
    s = s.buffer(P.FIN_RC, quad_segs=16).buffer(-P.FIN_RC, quad_segs=16)
    s = s.buffer(-P.FIN_RV, quad_segs=16).buffer(P.FIN_RV, quad_segs=16)
    return list(s.exterior.coords)[:-1]


def base_xz():
    """Plan (X-Z) outline of the base: back corners, sides, the wraps round the case's front vertical corners and the
    central tongue (z up to 9, trimmed by light_cut) between them."""
    wr = P.WRAP_R
    return arc_pts(-2.09, -4.7, P.XZ_R_BACK, 180, 270) + arc_pts(62.09, -4.7, P.XZ_R_BACK, 270, 360) + \
        arc_pts(62.29, 4.2, wr, 0, 90) + [(62.29, 9.0), (-2.29, 9.0)] + arc_pts(-2.29, 4.2, wr, 90, 180)


def tongue_rect():
    """The base's central front tongue (x between the wraps, z 4..9): never rabbeted, never skirted."""
    from shapely.geometry import box as sbox
    return sbox(-2.29, 4.0, 62.29, 9.0)


def rabbet_cut(top):
    """Base: everything on the floor's rim (y CASE_TOP .. above the floor) outside the outline inset by RAB, except the
    tongue. Leaves a shoulder at y = CASE_TOP, RAB wide, all round the sides, back and corner wraps."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    keep = unary_union([Polygon(base_xz()).buffer(-P.RAB, join_style='round', quad_segs=16), tongue_rect()])
    keep = max(keep.geoms, key=lambda p: p.area) if hasattr(keep, 'geoms') else keep
    band = U.box(-10, 70, P.CASE_TOP, P.LID_BOT + 1.0, -10, 14)
    inside = U.prism_y(list(keep.exterior.coords)[:-1], P.CASE_TOP - 1, P.LID_BOT + 2).intersect(
        U.prism_z(cap_xy(100, top, P.RAB), -10, 14))
    return band.cut(inside)


# ------------------------------------------------------------------ parts
def build_base(g, top, with_bumps=True):
    xz = base_xz()
    env = U.prism_z(cap_xy(P.FIN_Y, top), P.ZOB - 1, 10).intersect(U.prism_y(xz, P.FIN_Y, P.FLOOR_TOP)).intersect(
        U.prism_x(fin_yz(), -8, 68)).clean()
    j = P.J6_OPEN
    window = U.box(j['x0'], j['x1'], 110.0, 118.0, j['z0'], j['z1'])
    bosses = [U.cyl_y(x, z, P.BOSS_D / 2, P.FLOOR_TOP - 0.5, P.BOSS_TOP) for x, z in P.HOLES]
    b = P.BUMP
    zc = P.CZB - P.CL + b['proud'] - b['r']
    bumps = [U.cyl_x(b['y'], zc, b['r'], xa, xb) for xa, xb in b['xs']] if with_bumps else []
    base = U.cut(env, case_cavity(), light_cut(), window, rabbet_cut(top))
    base = U.fuse(base, *bosses, *bumps)
    base = U.cut(base, *[U.cyl_y(x, z, P.PILOT_D / 2, P.PILOT_BOT, P.BOSS_TOP + 1) for x, z in P.HOLES])   # blind
    return U.one_solid(base), {'bumps': U.fuse(*bumps) if bumps else None}


# ------------------------------------------------------------------ lid (audio)
def lid_xy(top):
    """X-Y (front view) outline of the lid, y from 100 up to the roof: follows the base's rev C corner arcs (R6.25, centre y
    BASE_TOP_REF - 6.25) up to the rim at LID_BOT so the seam is flush, then goes straight up and rounds the roof's end edges
    with R_END (the jack opening top is at y 123.35, so only a small round fits at the ends)."""
    r, cy0 = P.XY_R, P.BASE_TOP_REF - P.XY_R
    th = math.degrees(math.asin((P.LID_BOT - cy0) / r))
    right = arc_pts(P.CORNER_X[1], cy0, r, 0, th)
    xe = right[-1][0]
    re = P.R_END
    right_top = arc_pts(xe - re, top - re, re, 0, 90)
    left = [(60.0 - x, y) for x, y in reversed(right)]
    left_top = [(60.0 - x, y) for x, y in reversed(right_top)]
    return [(P.XO0, 100.0), (P.XO1, 100.0)] + right + right_top + left_top + left


def lid_yz(top):
    """Side view (Y-Z): flat roof, R_TOP_FRONT top-front edge, back top edge R2 like rev C; front face at Z_FRONT_AUDIO."""
    zf, zb = P.Z_FRONT_AUDIO, P.ZOB
    return round_poly([(100.0, zb), (100.0, zf), (top, zf), (top, zb)], [0, 0, P.R_TOP_FRONT, P.TOP_R_BACK])


def lid_xz():
    """Plan: back corners like rev C (concentric with the case's back vertical corners), front corners R XZ_R_FRONT_LID."""
    zf, rl = P.Z_FRONT_AUDIO, P.XZ_R_FRONT_LID
    return arc_pts(-2.09, -4.7, P.XZ_R_BACK, 180, 270) + arc_pts(62.09, -4.7, P.XZ_R_BACK, 270, 360) + \
        arc_pts(P.XO1 - rl, zf - rl, rl, 0, 90) + arc_pts(P.XO0 + rl, zf - rl, rl, 90, 180)


def build_lid(g, top):
    zf = P.Z_FRONT_AUDIO
    env = U.prism_z(lid_xy(top), P.ZOB - 1, zf + 1).intersect(U.prism_x(lid_yz(top), -8, 68)).intersect(
        U.prism_y(lid_xz(), 100.0, top + 1)).clean()
    from shapely.geometry import Polygon, box as sbox
    from shapely.ops import unary_union
    cav_poly = Polygon(outline_xz(g)).buffer(P.PCB_GAP, join_style='round', quad_segs=16)
    xc0, _, xc1, _ = cav_poly.bounds
    ru = roof_under(g)
    # skirt over the base's rabbet (rev C): below the rim (z < BROW_Z) only a skirt rides over the stepped-in edge; in front of
    # BROW_Z (the base's front tongue is never rabbeted) the lid simply stops at LID_BOT.
    inner = unary_union([Polygon(base_xz()).buffer(-(P.RAB - P.RAB_CL), join_style='round', quad_segs=16),
                         sbox(xc0, 0.0, xc1, P.BROW_Z + 1.0)])
    inner = max(inner.geoms, key=lambda p: p.area) if hasattr(inner, 'geoms') else inner
    below = U.box(-10, 70, 100, P.CASE_TOP + P.RAB_CL_V, -10, P.BROW_Z)
    ins = U.prism_y(list(inner.exterior.coords)[:-1], 100, P.LID_BOT).intersect(
        U.prism_z(cap_xy(100, P.BASE_TOP_REF, P.RAB - P.RAB_CL), -10, P.BROW_Z)).intersect(
        U.box(-10, 70, 99, P.LID_BOT + 1, -10, P.BROW_Z))
    front_rim = U.box(-10, 70, 100, P.LID_BOT, P.BROW_Z - 0.01, zf + 2)
    under = U.fuse(below, ins, front_rim)
    # one open cavity over the board: PCB outline + PCB_GAP all round, up to the roof underside
    cavity = U.prism_y(list(cav_poly.exterior.coords)[:-1], P.PCB_Y0, ru)
    # the jack body (x -2.84..) and its nose stand past the board's left edge (x -2.5): a local pocket keeps PCB_GAP around them
    jb = g['jack']['body_box']
    cavity = cavity.fuse(U.box(jb['x'][0] - P.PCB_GAP, xc0 + 0.5, P.PCB_Y0, ru, jb['z'][0] - P.PCB_GAP, jb['z'][1] + P.PCB_GAP)).clean()
    xc0 = min(xc0, jb['x'][0] - P.PCB_GAP)
    # round the cavity's top-back edge (R0.6) so the roof/back wall keeps >= 1.2 round the outer R2 edge
    zb_in = cav_poly.bounds[1]
    cavity = cavity.intersect(U.prism_x(round_poly([(P.PCB_Y0 - 1, zb_in), (P.PCB_Y0 - 1, 20.0), (ru, 20.0), (ru, zb_in)],
                                                   [0, 0, 0, 0.6]), -10, 70)).clean()
    # round the cavity's top-front edge concentric with the outer R_TOP_FRONT round, so the front wall / roof keep their
    # thickness round the corner (the board's front edge moved to z 7.0 on 2026-11-09, which put the cavity front at 7.3)
    zf_in = cav_poly.bounds[3]
    r_in = max(0.2, P.R_TOP_FRONT - (zf - zf_in))
    cavity = cavity.intersect(U.prism_x(round_poly([(P.PCB_Y0 - 1, -20.0), (P.PCB_Y0 - 1, zf_in), (ru, zf_in), (ru, -20.0)],
                                                   [0, 0, r_in, 0]), -10, 70)).clean()
    # screw columns (clamp on the PCB top, y 117.60) with the deep counterbore
    cb_floor = round(P.PILOT_BOT + P.TIP_ABOVE_SKIN + P.SCREW['L'], 3)
    cols = [U.cyl_y(x, z, P.COL_R, P.PCB_Y1, ru + 0.5) for x, z in P.HOLES]
    holes = []
    for x, z in P.HOLES:
        holes += [U.cyl_y(x, z, P.RECESS_D / 2, 116.0, P.RECESS_TOP), U.cyl_y(x, z, P.CLR_D / 2, 116.0, cb_floor + 0.01),
                  U.cyl_y(x, z, P.CB_D / 2, cb_floor, top + 1)]
    # plug opening: circle OPEN_D coaxial with the jack barrel + a straight slot down to the lid's lower edge (no overhang when
    # the lid prints top-down), and the flat pad behind the nose tip
    ay, az = jack_axis(g)
    nx0 = g['jack']['nose']['x'][0]
    ro = P.OPEN_D / 2
    opening = [U.cyl_x(ay, az, ro, P.XO0 - 1, xc0 + 0.02),
               U.box(P.XO0 - 1, xc0 + 0.02, 115.0, ay, az - ro, az + ro),
               U.box(P.XO0 - 1, P.XO0 + P.PAD_DEPTH, P.LID_BOT - 0.01, top + 1, az - P.PAD_HALF_Z, az + P.PAD_HALF_Z)]
    lid = env.cut(under, cavity).fuse(*cols).clean()
    lid = U.cut(lid, *holes, *opening)
    return U.one_solid(lid), {'cb_floor': cb_floor, 'roof_under': ru, 'cav_x': (round(xc0, 3), round(xc1, 3))}


def build_all():
    g, src = pcba_data()
    top = lid_top(g)
    base, bf = build_base(g, P.BASE_TOP_REF)
    base_nb, _ = build_base(g, P.BASE_TOP_REF, with_bumps=False)
    lid, lf = build_lid(g, top)
    return dict(g=g, src=src, top=top, base=base, base_nb=base_nb, lid=lid, pcba=build_pcba(g), bumps=bf['bumps'],
                cb_floor=lf['cb_floor'], roof_under=lf['roof_under'], cav_x=lf['cav_x'])


if __name__ == '__main__':
    import time
    t = time.time()
    M = build_all()
    for n in ('base', 'lid'):
        bb = M[n].BoundingBox()
        print(n, M[n].isValid(), len(M[n].Solids()), round(M[n].Volume(), 1),
              [round(v, 2) for v in (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax)])
    print('lid top', M['top'], 'roof under', M['roof_under'], 'cb floor', M['cb_floor'], 'src', M['src'], f'{time.time() - t:.1f}s')
