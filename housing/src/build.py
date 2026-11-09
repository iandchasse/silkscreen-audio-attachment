"""Audio attachment housing: build, export, check, render, report. Exit 1 when a check fails.

    <enclosure venv python> build.py [--no-render]

Checks: seated interference vs the stock case, PCBA fit, roof clearance, lid/base seam (rabbet),
-Y insertion sweep, J6 engagement, screws, SW10 keep-out, plug opening (coaxial + plug envelope), base identity vs rev C,
printability. Solids are tessellated at 0.01 mm and compared with manifold3d (exact mesh booleans, min_gap).
"""
import json
import math
import sys
import time

import cadquery as cq
import numpy as np
import trimesh
from scipy.spatial import cKDTree

import params as P
import parts
import util as U

OUT = P.OUT
T0 = time.time()


def log(*a):
    print(f'[{time.time() - T0:6.1f}s]', *a, flush=True)


def mf(shape):
    return U.manifold_of(U.to_mesh(shape))


def ivol(a, b):
    return U.mvolume(a ^ b)


def r3(v):
    return None if v is None else round(float(v), 3)


# ---------------------------------------------------------------- print orientation
def to_print(shape, part, top):
    if part == 'lid':      # top-down: X' = x, Y' = z, Z' = top - y
        return shape.rotate(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), -90).translate(cq.Vector(0, 0, top))
    return shape.translate(cq.Vector(0, -P.Y_BOT, -P.ZOB))    # base on its back face: Z' = z + 7.95


def print_to_E(pts, part, top):
    if part == 'lid':
        return np.c_[pts[:, 0], top - pts[:, 2], pts[:, 1]]
    return np.c_[pts[:, 0], pts[:, 1] + P.Y_BOT, pts[:, 2] + P.ZOB]


def overhangs(mesh):
    """Downward faces steeper than OVERHANG_DEG from vertical, grouped into patches (from rev A)."""
    n = mesh.face_normals
    lim = math.sin(math.radians(P.OVERHANG_DEG))
    zmin = mesh.triangles[:, :, 2].min(1)
    flag = (n[:, 2] < -lim) & (zmin > 0.05)
    idx = np.where(flag)[0]
    patches = []
    if len(idx):
        adj = mesh.face_adjacency
        keep = flag[adj[:, 0]] & flag[adj[:, 1]]
        for c in trimesh.graph.connected_components(adj[keep], nodes=idx, min_len=1):
            c = np.asarray(c)
            area = float(mesh.area_faces[c].sum())
            sub = mesh.submesh([c], append=True)
            per = float(sum(np.linalg.norm(sub.vertices[e[0]] - sub.vertices[e[1]])
                            for e in sub.edges[trimesh.grouping.group_rows(sub.edges_sorted, require_count=1)]))
            width = 2 * area / per if per > 0 else 0
            lo, hi = sub.bounds
            patches.append({'area': round(area, 2), 'width': round(width, 2), 'z': [round(float(lo[2]), 2), round(float(hi[2]), 2)],
                            'bbox_xy': [round(float(v), 1) for v in (lo[0], lo[1], hi[0], hi[1])],
                            'ok': width <= P.BRIDGE_OK_W or area <= 1.0, 'bed_edge': float(hi[2]) <= 1.6})
    return patches


def thin_walls(mesh, s=0.35, rmax=P.MIN_WALL + 0.1):
    pts, fi, nrm = U.sample_triangles(mesh.triangles, s)
    pts = np.round(pts, 6)
    pairs = cKDTree(pts).query_pairs(rmax, output_type='ndarray')
    thick = np.full(len(pts), np.inf)
    for a in range(0, len(pairs), 2_000_000):
        pr = pairs[a:a + 2_000_000]
        for i, j in ((pr[:, 0], pr[:, 1]), (pr[:, 1], pr[:, 0])):
            anti = np.einsum('ij,ij->i', nrm[i], nrm[j]) < -0.95
            d = pts[i] - pts[j]
            t = np.einsum('ij,ij->i', d, nrm[i])
            lat = np.linalg.norm(d - t[:, None] * nrm[i], axis=1)
            ok = anti & (t > 0.05) & (lat < 0.75 * s + 0.02)
            np.minimum.at(thick, i[ok], t[ok])
    return pts, thick


def declared_thin(M):
    """E-frame boxes where walls under 1.2 are intended (x0, x1, y0, y1, z0, z1)."""
    top, cb = M['top'], M['cb_floor']
    ay, az = parts.jack_axis(M['g'])
    uh = cb - P.RECESS_TOP
    d = {'base': {'floor 1.0 (contract) and its run-out into the corners': (-9, 69, 115.2, 116.75, -9, 9)},
         'lid': {f'seam skirt {P.RAB - P.RAB_CL:.1f} (rides over the base rabbet)': (-9, 69, P.CASE_TOP + P.RAB_CL_V - 0.05, P.LID_BOT + 0.6, -9, P.BROW_Z + 0.05),
                 'wall above the plug opening and the end pad': (-5.5, -2.7, ay + P.OPEN_D / 2 - 0.2, top + 0.1, az - 5.2, az + 5.2),
                 'end wall at the pad (pad 0.3 deep)': (-5.5, -2.7, P.LID_BOT - 0.05, top + 0.1, az - 5.2, az + 5.2)}}
    for x, z in P.HOLES:
        d['base'][f'blind-pilot skin {P.PILOT_SKIN} at x {x}'] = (x - 1.0, x + 1.0, P.CASE_TOP - 0.1, P.PILOT_BOT + 0.1, z - 1.0, z + 1.0)
        d['lid'][f'under-head layer {uh:.1f} at x {x}'] = (x - 2.6, x + 2.6, P.RECESS_TOP - 0.1, cb + 0.1, z - 2.6, z + 2.6)
        d['lid'][f'screw column wall {P.COL_R - P.CB_D / 2:.1f} at x {x}'] = (x - 3.4, x + 3.4, P.PCB_Y1 - 0.1, top + 0.1, z - 3.4, z + 3.4)
    return d


def check_print(M):
    res, ok = {}, True
    dec_all = declared_thin(M)
    for part in ('base', 'lid'):
        pm = U.to_mesh(to_print(M[part], part, M['top']))
        ov = overhangs(pm)
        pts, th = thin_walls(pm)
        E = print_to_E(pts, part, M['top'])
        dec = np.zeros(len(pts), bool)
        dmin = {}
        boxes = dec_all.get(part, {})
        sels = {lab: (E[:, 0] >= x0) & (E[:, 0] <= x1) & (E[:, 1] >= y0) & (E[:, 1] <= y1) & (E[:, 2] >= z0) & (E[:, 2] <= z1)
                for lab, (x0, x1, y0, y1, z0, z1) in boxes.items()}
        vol = {lab: (b[1] - b[0]) * (b[3] - b[2]) * (b[5] - b[4]) for lab, b in boxes.items()}
        for lab, sel in sels.items():
            dec |= sel
            own = sel.copy()          # a big box reports its own minimum, not that of a smaller box inside it
            for o, so in sels.items():
                if o != lab and vol[o] < vol[lab]:
                    own &= ~so
            if (own & np.isfinite(th)).any():
                dmin[lab] = round(float(th[own].min()), 3)
        thin = (th < P.MIN_WALL - 0.05) & ~dec      # 0.05: grid-sampling noise at s 0.35 reads a 1.2 wall as ~1.17
        clusters = []
        if thin.any():
            q = E[thin]
            for c in trimesh.graph.connected_components(cKDTree(q).query_pairs(0.6, output_type='ndarray'),
                                                        nodes=np.arange(len(q)), min_len=1)[:12]:
                c = np.asarray(c)
                clusters.append({'n': int(len(c)), 'min_t': round(float(th[thin][c].min()), 3),
                                 'E_bbox': np.round(np.r_[q[c].min(0), q[c].max(0)], 2).tolist()})
        bad = [p for p in ov if not (p['ok'] or p['bed_edge'])]
        r = {'orientation': 'top-down (roof on the bed)' if part == 'lid' else 'on its back face (back jaw on the bed)',
             'print_height': round(float(pm.bounds[1][2]), 2), 'watertight': bool(pm.is_watertight),
             'overhang_patches': len(ov), 'bed_edge_rounds': [p for p in ov if p['bed_edge']][:6],
             'overhang_failing': bad[:8], 'bridges_accepted': [p for p in ov if p['ok'] and not p['bed_edge']][:8],
             'thin_min_undeclared': r3(th[~dec].min()) if (~dec).any() and np.isfinite(th[~dec]).any() else None,
             'thin_clusters_undeclared': clusters, 'declared_thin_min': dmin}
        r['pass'] = (not bad) and (not clusters) and r['watertight']
        ok &= r['pass']
        res[part] = r
    return {'pass': bool(ok), 'parts': res,
            'rule': f'overhang > {P.OVERHANG_DEG} deg from vertical fails unless narrower than {P.BRIDGE_OK_W} mm (bridge) '
                    f'or a bed-edge round (patch top <= 1.6 mm above the bed; cosmetic droop); walls >= {P.MIN_WALL} except declared'}


# ---------------------------------------------------------------- checks against the case / PCBA
def load_case():
    return {n: U.manifold_of(U.load_stl(P.STOCK_OUT / f'{n}.stl')) for n in ('tub', 'lid')}


def case_vol(m, case):
    return sum(ivol(m, c) for c in case.values())


def check_seated(K, case):
    rows = {}
    for n in ('base_nb', 'lid', 'pcb', 'smd', 'jack', 'header_bodies', 'pins'):
        v = case_vol(K[n], case)
        g = min(K[n].min_gap(c, 3.0) for c in case.values())
        rows[n] = {'vol_mm3': r3(v), 'min_gap': r3(g)}
    bi = [K['bumps'] ^ c for c in case.values()]
    vb = sum(U.mvolume(i) for i in bi)
    depth = max([np.subtract(*U.mbbox(i)[::-1])[2] for i in bi if U.mvolume(i) > 1e-7] or [0])
    rows['bumps (designed)'] = {'vol_mm3': r3(vb), 'depth_z': r3(depth)}
    ok = all(r['vol_mm3'] < P.EPS_VOL for k, r in rows.items() if 'bumps' not in k) and 0.05 < depth < 0.15
    return {'pass': bool(ok), 'rows': rows,
            'note': 'designed contacts: floor on the top face (gap 0), bump ridges 0.10 into the back face; '
                    'everything else must not intersect'}


def check_fit(K, M):
    pairs = [('base_nb', 'lid'), ('base_nb', 'pcb'), ('lid', 'pcb'), ('base_nb', 'smd'), ('lid', 'smd'), ('base_nb', 'jack'),
             ('lid', 'jack'), ('base_nb', 'header_bodies'), ('lid', 'pins'), ('base_nb', 'pins')]
    rows, ok = {}, True
    for a, b in pairs:
        v = ivol(K[a], K[b])
        g = K[a].min_gap(K[b], 3.0)
        rows[f'{a} / {b}'] = {'vol_mm3': r3(v), 'min_gap': r3(g)}
        ok &= v < P.EPS_VOL
        if (a, b) == ('lid', 'pins'):
            ok &= g >= P.ROOF_CLR - 0.01
        if (a, b) == ('lid', 'smd'):
            ok &= g >= 0.0                                        # the column's r 3.2 equals the spec's keep-out: a part at the limit just touches
        if (a, b) == ('lid', 'jack'):
            ok &= g >= 0.10                                       # the left screw column stands 0.15 off the jack body
        if (a, b) == ('base_nb', 'lid'):                          # seam clearance (rabbet: 0.10 lateral, 0.10-0.15 vertical)
            ok &= g >= P.RAB_CL - 0.005
    import manifold3d as m3
    # the lid below the board top keeps >= PCB_GAP from the board edge (the columns clamp from above: gap 0)
    below_roof = K['lid'] ^ m3.Manifold.cube([80.0, P.PCB_Y1 - 0.05 - 100.0, 40.0]).translate([-10.0, 100.0, -20.0])
    g = below_roof.min_gap(K['pcb'], 3.0)
    rows['lid below the board top / pcb'] = {'vol_mm3': r3(ivol(below_roof, K['pcb'])), 'min_gap': r3(g)}
    ok &= g >= P.PCB_GAP - 0.01
    # roof: every lid point above the jack top plane keeps >= ROOF_CLR over the jack, the tails and the SMD parts
    ytop = max(M['g']['jack']['body_box']['y'][1], parts.tail_tip(M['g']))
    roof = K['lid'] ^ m3.Manifold.cube([80.0, 40.0, 40.0]).translate([-10.0, ytop - 0.001, -20.0])
    for hx, hz in P.HOLES:                                        # the screw columns are covered by the keep-out/float checks above
        roof = roof - mf(U.cyl_y(hx, hz, P.COL_R + 0.05, ytop - 1, ytop + 20))
    rg = min(roof.min_gap(K[n], 3.0) for n in ('jack', 'pins', 'smd'))
    rows['lid above y %.2f / jack, tails, smd' % ytop] = {'min_gap': r3(rg), 'roof_underside_y': M['roof_under'],
                                                           'jack_top_y': M['g']['jack']['body_box']['y'][1],
                                                           'tail_tip_y': parts.tail_tip(M['g'])}
    ok &= rg >= P.ROOF_CLR - 0.01
    fl = {}
    for dx, dz in ((0.19, 0), (-0.19, 0), (0, 0.19), (0, -0.19)):
        v = 0.0
        for n in ('pcb', 'smd', 'jack', 'header_bodies', 'pins'):
            m = K[n].translate([dx, 0, dz])
            v += ivol(m, K['base_nb']) + ivol(m, K['lid'])
        fl[f'dx {dx} dz {dz}'] = r3(v)
        ok &= v < P.EPS_VOL
    return {'pass': bool(ok), 'rows': rows, 'pcba_float_0.19': fl,
            'note': 'PCB lies on the floor (y 116.6) and under the two screw columns (117.6): gap 0 is the clamp. Float: boss dia 4.40 '
                    f'in the dia {P.HOLE_D} holes; lid wall {P.PCB_GAP} off the PCB edge; roof >= {P.ROOF_CLR} over the jack and tails.'}


def check_base_identity(M):
    """The base must equal the printed rev C base except for the left boss/pilot moving from x 10 to x 12."""
    f = P.A.parent / 'silkscreen-light-attachment' / 'housing' / 'out' / 'E' / 'base.stl'
    if not f.exists():
        return {'pass': True, 'note': 'rev C base.stl not found; skipped', 'file': str(f)}
    ref = U.manifold_of(U.load_stl(f))
    new = mf(M['base'])
    d = (new - ref) + (ref - new)
    vol = U.mvolume(d)
    lo, hi = U.mbbox(d) if vol > 1e-6 else ([0] * 3, [0] * 3)
    x0, x1 = 7.6, 14.5                      # old boss 10 +- 2.4 (recess), new boss 12 +- 2.2
    inside = lo[0] >= x0 - 0.05 and hi[0] <= x1 + 0.05 and lo[2] >= -3.5 and hi[2] <= 1.5 and lo[1] >= P.CASE_TOP - 0.1
    return {'pass': bool(inside), 'vol_diff_mm3': r3(vol), 'diff_bbox_lo': [r3(v) for v in lo], 'diff_bbox_hi': [r3(v) for v in hi],
            'ref': 'silkscreen-light-attachment/housing/out/E/base.stl (rev C)',
            'rule': 'symmetric difference lies inside x 7.6..14.5, z -3.5..1.5 (the two boss/pilot sites) and above the case top'}


def check_plug(M, K, case):
    """Opening coaxial with the jack barrel (measured on the lid mesh) and a dia 9 x 20 plug seated against the nose tip."""
    g = M['g']
    ay, az = parts.jack_axis(g)
    n = g['jack']['nose']
    lm = U.to_mesh(M['lid'])
    tr = lm.triangles[(lm.triangles[:, :, 0].max(1) < n['x'][1] + 0.5) & (lm.triangles[:, :, 1].min(1) > ay - 0.5)]
    pts, _, _ = U.sample_triangles(tr, 0.05)
    sel = pts[(pts[:, 0] > P.XO0 + 0.5) & (pts[:, 0] < n['x'][1] + 0.2) & (pts[:, 1] > ay + 1.0)]
    r = np.hypot(sel[:, 1] - ay, sel[:, 2] - az)
    sel = sel[(r > P.OPEN_D / 2 - 0.3) & (r < P.OPEN_D / 2 + 0.3)]
    A = np.c_[2 * sel[:, 1], 2 * sel[:, 2], np.ones(len(sel))]       # least-squares circle through the opening's upper arc
    bvec = sel[:, 1] ** 2 + sel[:, 2] ** 2
    sol = np.linalg.lstsq(A, bvec, rcond=None)[0]
    cy, cz = float(sol[0]), float(sol[1])
    rad = math.sqrt(sol[2] + cy * cy + cz * cz)
    off = math.hypot(cy - ay, cz - az)
    pl, x_tip = P.PLUG, n['x'][0]
    body = U.cyl_x(ay, az, pl['body_d'] / 2, x_tip - pl['body_l'], x_tip)
    tip = U.cyl_x(ay, az, pl['tip_d'] / 2, x_tip, g['jack']['body_box']['x'][1])
    env = {'body': mf(body), 'tip': mf(tip)}
    rows = {}
    ok = off <= 0.2
    for nm, m in env.items():
        for tgt, mm_ in (('lid', K['lid']), ('base', K['base_nb'])):
            v = ivol(m, mm_)
            rows[f'plug {nm} / {tgt}'] = {'vol_mm3': r3(v), 'min_gap': r3(m.min_gap(mm_, 3.0))}
            ok &= v < P.EPS_VOL
        v = case_vol(m, case)
        gp = min(m.min_gap(c, 3.0) for c in case.values())
        rows[f'plug {nm} / case'] = {'vol_mm3': r3(v), 'min_gap': r3(gp)}
        ok &= v < P.EPS_VOL
    ok &= rows['plug body / lid']['min_gap'] >= P.PAD_DEPTH - 0.05
    ok &= rows['plug body / case']['min_gap'] > 0.5
    return {'pass': bool(ok), 'opening_centre_measured': {'y': r3(cy), 'z': r3(cz)}, 'opening_dia_measured': r3(2 * rad),
            'jack_axis': {'y': ay, 'z': az}, 'offset_mm': r3(off), 'opening_dia_design': P.OPEN_D,
            'radial_gap_nose_to_opening': r3(P.OPEN_D / 2 - n['dia'] / 2), 'end_pad_behind_nose_tip': P.PAD_DEPTH, 'rows': rows,
            'rule': 'opening centre within 0.2 of the jack axis; plug body dia 9 x 20 and tip dia 3.5 (seated at the nose tip) '
                    'do not intersect the lid, base or case; body-to-lid gap >= the end pad depth'}


def check_seam(K):
    """Rabbet seam: lid skirt over the base's stepped-in top edge. Lateral clearance RAB_CL all round (the lid shifted by
    0.095 in any direction must still clear the base), vertical 0.10 at the floor top / RAB_CL_V at the shoulder."""
    rows, ok = {}, True
    s = P.RAB_CL - 0.005
    d = s / math.sqrt(2)                                # diagonal: 0.095 along the diagonal (the clearance is radial)
    for dx, dz in ((s, 0), (-s, 0), (0, s), (0, -s), (d, d), (-d, -d), (d, -d), (-d, d)):
        v = ivol(K['lid'].translate([dx, 0, dz]), K['base_nb'])
        rows[f'lid shifted dx {dx:+.3f} dz {dz:+.3f}'] = r3(v)
        ok &= v < P.EPS_VOL
    for dy in (P.LID_BOT - P.FLOOR_TOP - 0.005,):
        v = ivol(K['lid'].translate([0, -dy, 0]), K['base_nb'])
        rows[f'lid lowered {dy:.3f}'] = r3(v)
        ok &= v < P.EPS_VOL
    lat = [r3(K['lid'].min_gap(K['base_nb'], 1.0))]
    return {'pass': bool(ok), 'rows': rows, 'min_gap_lid_base': lat[0],
            'design': {'rabbet_step': P.RAB, 'lid_skirt_wall': round(P.RAB - P.RAB_CL, 2), 'lateral_clearance': P.RAB_CL,
                       'shoulder_y': P.CASE_TOP, 'skirt_lower_edge_y': round(P.CASE_TOP + P.RAB_CL_V, 3),
                       'vertical_clearance_at_shoulder': P.RAB_CL_V, 'lid_underside_over_floor_top': round(P.LID_BOT - P.FLOOR_TOP, 3)},
            'rule': 'the lid stays clear of the base when shifted 0.095 in x/z (0.10 designed) and when lowered 0.095'}


def play(m, case, h, axis, sign, dmax=1.2):
    def hit(d):
        v = [0, h, 0]
        v[0 if axis == 'x' else 2] = sign * d
        return case_vol(m.translate(v), case) > P.EPS_VOL
    if not hit(dmax):
        return None
    lo, hi = 0.0, dmax
    for _ in range(8):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if hit(mid) else (mid, hi)
    return round(lo, 3)


def pmax(a, b):
    return None if a is None or b is None else max(a, b)


def check_sweep(K, case, g):
    tip = min(p['y_post_tip'] for p in g['header']['pins'])
    face = g['header'].get('j6_face_y', list(P.J6_FACE))
    h_tip = [round(face[1] - tip, 2), round(face[0] - tip, 2)]
    body_bot = min(b['body_box']['y'][0] for b in g['header']['bodies'])
    hs = sorted({10.0, 9.0, 8.5, 8.0, 7.5, 7.0, 6.5, 6.0, 5.5, h_tip[0], h_tip[1], 4.0, 3.0, 2.0, 1.5, 1.0, 0.5, 0.0}, reverse=True)
    rows, coll = [], []
    for h in hs:
        v = sum(case_vol(K[n].translate([0, h, 0]), case) for n in ('base_nb', 'lid', 'pcb', 'header_bodies', 'pins', 'smd', 'jack'))
        vb = case_vol(K['bumps'].translate([0, h, 0]), case)
        p = {f'{a}{"+" if s > 0 else "-"}': play(K['base_nb'], case, h, a, s) for a in ('x', 'z') for s in (1, -1)}
        rows.append({'h': h, 'collision_mm3': r3(v), 'bumps_mm3': r3(vb), **p})
        if v > P.EPS_VOL:
            coll.append(h)

    def within(keys, lim):
        """Highest sampled h from which the play stays <= lim all the way down to seated."""
        best = None
        for r in sorted(rows, key=lambda r: r['h']):
            if not all(r[k] is not None and r[k] <= lim for k in keys):
                break
            best = r['h']
        return best
    at_tip = [r for r in rows if r['h'] in h_tip]
    ok_x = all(all(r[k] is not None and r[k] <= P.X_PLAY_OK for k in ('x+', 'x-')) for r in at_tip)
    ok_z = all(all(r[k] is not None and r[k] <= P.PLAY_OK for k in ('z+', 'z-')) for r in at_tip)
    ok = not coll and ok_x and ok_z
    bump_h = max([r['h'] for r in rows if r['bumps_mm3'] > P.EPS_VOL], default=None)
    return {'pass': bool(ok), 'h_post_tips_at_J6_face': h_tip, 'h_header_bodies_enter_opening': round(P.CASE_TOP - body_bot, 2),
            'x_play_at_tips': {str(r['h']): pmax(r['x+'], r['x-']) for r in at_tip},
            'z_play_at_tips': {str(r['h']): pmax(r['z+'], r['z-']) for r in at_tip},
            f'h_x_play_within_{P.X_PLAY_OK}': within(('x+', 'x-'), P.X_PLAY_OK),
            'h_x_play_within': within(('x+', 'x-'), P.PLAY_OK), 'h_z_play_within': within(('z+', 'z-'), P.PLAY_OK),
            'h_bumps_touch_(sampled)': bump_h, 'collisions_at_h': coll, 'rows': rows,
            'rule': f'-Y insertion; play = free lateral travel of the base before it touches the case (None = > 1.2); '
                    f'when the post tips reach the J6 face X play <= {P.X_PLAY_OK} (front-corner X guides) and Z play <= '
                    f'{P.PLAY_OK}; no collision except the bump ridges; "within" = highest sampled h from which the play '
                    f'stays under the limit down to seated'}


def check_pins(g):
    tip = min(p['y_post_tip'] for p in g['header']['pins'])
    face = g['header'].get('j6_face_y', list(P.J6_FACE))
    e = [round(face[0] - tip, 3), round(face[1] - tip, 3)]
    tol = 0.10 + 0.10 + 0.13      # case top, floor, header OAL
    j = P.J6_OPEN
    edge = min(min(p['x'] - p['square'] / 2 - j['x0'], j['x1'] - p['x'] - p['square'] / 2,
                   p['z'] - p['square'] / 2 - j['z0'], j['z1'] - p['z'] - p['square'] / 2) for p in g['header']['pins'])
    ok = P.E_LIM[0] <= e[0] - tol and e[1] + tol <= P.E_LIM[1] and edge > 0.6
    return {'pass': bool(ok), 'engagement_nominal': e, 'worst_case': [round(e[0] - tol, 3), round(e[1] + tol, 3)],
            'limits': list(P.E_LIM), 'stack_tol': tol, 'post_tip_y': tip, 'pin_to_opening_edge_min': round(edge, 3)}


def check_screws(M):
    """Blind pilots: a skin under each pilot, the pilot open above it, and a nominal M2 x 3 seats its head (k max, flush
    with the top) before its tip reaches the pilot bottom. Longer screws bottom in the boss, never on the case."""
    base, top, cb, S = M['base'], M['top'], M['cb_floor'], P.SCREW
    r = P.PILOT_D / 2 - 0.05
    a = math.pi * r * r
    holes = {}
    for x, z in P.HOLES:
        skin = base.intersect(U.cyl_y(x, z, r, P.CASE_TOP - 0.5, P.PILOT_BOT + 0.3)).Volume() / a
        open_v = base.intersect(U.cyl_y(x, z, r, P.PILOT_BOT + 0.01, P.BOSS_TOP + 0.5)).Volume()
        holes[f'x {x}'] = {'skin_measured': r3(skin), 'material_in_pilot_mm3': r3(open_v)}
    tip = cb - S['L']
    margin = tip - P.PILOT_BOT
    res = {'screw': S['name'], 'pilot_d': P.PILOT_D, 'pilot_bottom_y': P.PILOT_BOT, 'skin_design': P.PILOT_SKIN,
           'counterbore_floor_y': cb, 'head_top_y_at_k_max': round(cb + S['head_k'], 3), 'lid_top_y': top,
           'lid_top_above_case': round(top - P.CASE_TOP, 3), 'tip_y_nominal': round(tip, 3),
           'tip_to_pilot_bottom': round(margin, 3), 'tip_above_case_top': round(tip - P.CASE_TOP, 3),
           'longest_screw_that_seats': round(cb - P.PILOT_BOT, 3),
           'thread_engagement_mm': round(P.BOSS_TOP - tip, 3),
           'thread_engagement_pitches': round((P.BOSS_TOP - tip) / S['pitch'], 1),
           'thread_depth_radial_nominal': round((S['d'] - P.PILOT_D) / 2, 3),
           'engagement_split': {'boss above the floor': round(P.BOSS_TOP - P.FLOOR_TOP, 3), 'floor': round(P.FLOOR_TOP - tip, 3)},
           'screw_4mm': {'bottoms_at_y': P.PILOT_BOT, 'head_proud_of_top': round(P.PILOT_BOT + 4.0 + S['head_k'] - top, 3),
                         'tip_above_case_top': P.PILOT_SKIN},
           'holes': holes}
    ok = all(h['skin_measured'] >= P.PILOT_SKIN - 0.01 and h['material_in_pilot_mm3'] < 0.01 for h in holes.values())
    ok &= margin >= P.TIP_MARGIN_MIN and cb + S['head_k'] <= top + 1e-6
    res['pass'] = bool(ok)
    res['rule'] = (f'pilot blind with >= {P.PILOT_SKIN} skin; nominal {S["L"]} mm screw tip >= {P.TIP_MARGIN_MIN} above the '
                   f'pilot bottom with a k-max head on the counterbore floor; head top <= lid top; lid top <= 4.9 above the case')
    return res


def check_keepout(M):
    """Front-corner X guides: below y 107 the base stays at z >= 2.0 on the right (SW10) and above y 91 on the left."""
    m = U.to_mesh(M['base'])
    pts, _, _ = U.sample_triangles(m.triangles, 0.1)
    low = pts[pts[:, 1] < P.RIGHT_KEEP_Y - 0.01]
    right, left = low[low[:, 0] > 30], low[low[:, 0] < 30]
    res = {'lowest_base_y': r3(pts[:, 1].min()),
           'right_min_z_below_107': r3(right[:, 2].min()) if len(right) else None,
           'left_min_z_below_107': r3(left[:, 2].min()) if len(left) else None,
           'right_min_x_below_107': r3(right[:, 0].min()) if len(right) else None,
           'guide_inner_faces': f'x {P.CX0 - P.CL:.2f} / {P.CX1 + P.CL:.2f} ({P.CL} off the case sides) + the wraps round the '
                                f'front vertical corners'}
    ok = (not len(right) or right[:, 2].min() >= P.RIGHT_KEEP_Z - 1e-3) and pts[:, 1].min() >= 91.0
    res['pass'] = bool(ok)
    res['rule'] = f'right side below y {P.RIGHT_KEEP_Y}: z >= {P.RIGHT_KEEP_Z} (SW10 slot y 89.8..106.0, z <= 0.6); left side plain above y 91'
    return res


def check_pcba_stl(K, case):
    """The PCB agent's E-frame PCBA STL (pcb/production/3d/*_pcba_E.stl), body by body, vs the housing and the case."""
    cand = sorted((P.A / 'pcb' / 'production' / '3d').glob('*_pcba_E.stl'))
    f = cand[-1] if cand else P.A / 'pcb' / 'production' / '3d' / 'missing_pcba_E.stl'
    if not f.exists():
        return {'pass': True, 'note': 'no E-frame PCBA STL yet; the geometry.json solids were used'}
    import os
    m = U.load_stl(f)
    bodies = m.split(only_watertight=False)
    rows, ok, bad = {}, True, []
    for tgt in ('base_nb', 'lid', 'case'):
        v, g = 0.0, 9.0
        for b in bodies:
            mb = U.manifold_of(b)
            if tgt == 'case':
                vv = case_vol(mb, case)
                gg = min(mb.min_gap(c, 3.0) for c in case.values())
            else:
                vv, gg = ivol(mb, K[tgt]), mb.min_gap(K[tgt], 3.0)
            v += vv
            g = min(g, gg)
            if vv > P.EPS_VOL:
                bad.append({'target': tgt, 'body_bbox': np.round(b.bounds, 2).tolist(), 'vol': r3(vv)})
        rows[tgt] = {'vol_mm3': r3(v), 'min_gap': r3(g)}
        ok &= v < P.EPS_VOL
    return {'pass': bool(ok), 'file': str(f.relative_to(P.A)), 'mtime': time.ctime(os.path.getmtime(f)),
            'bodies': len(bodies), 'bounds': np.round(m.bounds, 3).tolist(), 'rows': rows, 'intersecting_bodies': bad[:10]}


# ---------------------------------------------------------------- exports / renders
def export(M):
    (OUT / 'E').mkdir(parents=True, exist_ok=True)
    (OUT / 'print').mkdir(parents=True, exist_ok=True)
    E = {}
    for n in ('base', 'lid'):
        U.to_mesh(M[n]).export(OUT / 'E' / f'{n}.stl')
        E[n] = OUT / 'E' / f'{n}.stl'
    for n, s in M['pcba'].items():
        U.to_mesh(s).export(OUT / 'E' / f'pcba_{n}.stl')
        E['pcba_' + n] = OUT / 'E' / f'pcba_{n}.stl'
    meshes = []
    for n in ('base', 'lid'):
        ps = to_print(M[n], n, M['top'])
        cq.exporters.export(ps, str(OUT / 'print' / f'{n}.step'))
        pm = U.to_mesh(ps, 0.01)
        pm.export(OUT / 'print' / f'{n}.stl')
        meshes.append(pm)
    try:
        b, l = meshes[0].copy(), meshes[1].copy()
        b.apply_translation([-b.bounds[0][0] + 5, -b.bounds[0][1] + 5, -b.bounds[0][2]])
        l.apply_translation([-l.bounds[0][0] + 5, -l.bounds[0][1] + 5 + b.bounds[1][1] + 8, -l.bounds[0][2]])
        sc = trimesh.Scene()
        sc.add_geometry(b, node_name='base')
        sc.add_geometry(l, node_name='lid')
        sc.export(str(OUT / 'print' / 'plate.3mf'))
        plate = 'print/plate.3mf'
    except Exception as ex:
        plate = f'3MF export failed: {ex}'
    return E, plate


def renders(E, M):
    import render as R
    import section2d as S
    rd = OUT / 'render'
    rd.mkdir(exist_ok=True)
    C = [(P.STOCK_OUT / 'tub.stl', '#d9d4c7', 1.0), (P.STOCK_OUT / 'lid.stl', '#c9c3b4', 1.0)]
    col = {'base': '#3d424c', 'lid': '#55606e', 'pcba_pcb': '#1f1f1f', 'pcba_smd': '#303030', 'pcba_jack': '#8a8f98',
           'pcba_header_bodies': '#202020', 'pcba_pins': '#d4af37'}
    parts_all = C + [(E[n], col[n], 1.0) for n in col]
    ay, az = parts.jack_axis(M['g'])
    near = (-12, 72, 100, 128, -12, 14)
    out = [R.render(rd / 'assembly_iso.png', parts_all, (0.55, 0.55, 0.75), (0, 1, 0), near, zoom=1.1),
           R.render(rd / 'left_end_jack_opening.png', parts_all, (-1, 0.0, 0.0), (0, 1, 0), (-6, -5, 110, 126, -14, 14), ortho=True, zoom=1.0),
           R.render(rd / 'left_end_iso.png', parts_all, (-0.8, 0.35, 0.45), (0, 1, 0), (-8, 14, 110, 126, -8, 10), zoom=1.2),
           R.render(rd / 'front.png', parts_all, (0, 0, 1), (0, 1, 0), (-10, 70, 102, 128, -12, 16), ortho=True, zoom=1.05),
           R.render(rd / 'exploded_iso.png', C + [(E['base'], col['base'], 1.0)] + [(E[n], col[n], 1.0) for n in col if n.startswith('pcba')],
                    (0.55, 0.65, 0.6), (0, 1, 0), near, zoom=1.1),
           R.render(rd / 'section_jack_axis_z0.png', parts_all, (0, 0, 1), (0, 1, 0), (-12, 24, 108, 128, az, az),
                    clip=('z', az, False), ortho=True, zoom=1.0)]
    items = [(P.STOCK_OUT / 'tub.stl', '#d9d4c7', 'case'), (E['base'], '#3d424c', 'base (dark)'), (E['lid'], '#9fb3c8', 'lid (light)'),
             (E['pcba_pcb'], '#1f7a3a', 'PCB'), (E['pcba_jack'], '#c0c4cc', 'jack'), (E['pcba_smd'], '#f2c200', 'SMD parts')]
    xj = M['g']['jack']['body_box']['x']
    out.append(S.section_png(rd / 'section_jack_x2.3.png', items, round((xj[0] + xj[1]) / 2, 2), (-9, 9, 104, 127),
                             title='Audio lid: section across the jack body (x 2.3); roof 0.3 over the jack'))
    out.append(S.section_png(rd / 'section_boss_x12.png', items, P.HOLES[0][0], (-9, 9, 104, 127),
                             title='Audio lid: section through the left screw column (x 12)'))
    out.append(S.section_png(rd / 'section_plug_opening_x-4.png', items, -4.0, (-9, 9, 104, 127),
                             title='Audio lid: section through the end wall and plug opening (x -4)'))
    return [str(p.relative_to(OUT)) for p in out]


# ---------------------------------------------------------------- report
def report(M, C, files):
    s, f, sw, pn, pr = C['seated'], C['fit'], C['sweep'], C['pins'], C['print']
    sc, ko, sm, pg, bi = C['screws'], C['keepout'], C['seam'], C['plug'], C['base_identity']
    ok = lambda c: 'pass' if c['pass'] else 'FAIL'
    ay, az = parts.jack_axis(M['g'])
    tip = M['cb_floor'] - P.SCREW['L']
    L = ['# Audio attachment housing - check report', '',
         f"Base = rev C base with the left boss at x {P.HOLES[0][0]:.2f}; new audio lid (no hood, closed cap, plug opening in the left end). "
         f"PCBA source: **{M['src']}**. Lid top y {M['top']} ({M['top'] - P.CASE_TOP:.1f} above the case top), roof underside y {M['roof_under']}, "
         f"front face z {P.Z_FRONT_AUDIO}. Overall: **{'PASS' if C['pass'] else 'FAIL'}**.", '',
         '| Check | Result | Key numbers |', '|---|---|---|',
         f"| Base identity vs rev C | {ok(bi)} | symmetric difference {bi.get('vol_diff_mm3')} mm3, inside the two boss sites (bbox {bi.get('diff_bbox_lo')} .. {bi.get('diff_bbox_hi')}) |",
         f"| Seated vs stock case | {ok(s)} | base (no bumps) {s['rows']['base_nb']['vol_mm3']} mm3, lid {s['rows']['lid']['vol_mm3']}, PCBA {s['rows']['pcb']['vol_mm3']}/{s['rows']['jack']['vol_mm3']}; bumps {s['rows']['bumps (designed)']['vol_mm3']} mm3, depth {s['rows']['bumps (designed)']['depth_z']} |",
         f"| PCBA fit | {ok(f)} | lid-jack gap {f['rows']['lid / jack']['min_gap']}, lid-SMD {f['rows']['lid / smd']['min_gap']}, lid-tails {f['rows']['lid / pins']['min_gap']}, "
         f"roof over jack/tails/SMD {[v for k, v in f['rows'].items() if k.startswith('lid above')][0]['min_gap']}, PCB edge to the lid below the board top {f['rows']['lid below the board top / pcb']['min_gap']}; float +-0.19 clean |",
         f"| Seam (rabbet) | {ok(sm)} | min gap lid-base {sm['min_gap_lid_base']}; clean when the lid is shifted 0.095 in x/z or lowered 0.095 |",
         f"| Plug opening | {ok(pg)} | opening dia {pg['opening_dia_measured']} (design {pg['opening_dia_design']}), centre y {pg['opening_centre_measured']['y']} z {pg['opening_centre_measured']['z']} vs jack axis y {ay} z {az}: offset {pg['offset_mm']}; "
         f"plug body dia 9 x 20 to lid gap {pg['rows']['plug body / lid']['min_gap']}, to case {pg['rows']['plug body / case']['min_gap']}; tip dia 3.5 clean |",
         f"| -Y insertion | {ok(sw)} | tips reach the J6 face at h {sw['h_post_tips_at_J6_face']}: X play {' / '.join(str(v) for v in sw['x_play_at_tips'].values())} (target <= {P.X_PLAY_OK}), Z {' / '.join(str(v) for v in sw['z_play_at_tips'].values())}; bumps touch ~h {sw['h_bumps_touch_(sampled)']} |",
         f"| Screws | {ok(sc)} | M2 x 3 pan, blind dia {sc['pilot_d']} pilots (skin {min(h['skin_measured'] for h in sc['holes'].values())}); counterbore dia {P.CB_D} floor y {sc['counterbore_floor_y']}; tip y {sc['tip_y_nominal']} = {sc['tip_to_pilot_bottom']} above the pilot bottom; thread {sc['thread_engagement_mm']} mm |",
         f"| Side keep-out (SW10) | {ok(ko)} | below y {P.RIGHT_KEEP_Y} the base is at z >= {ko['right_min_z_below_107']} (needs >= {P.RIGHT_KEEP_Z}) |",
         f"| J6 engagement | {ok(pn)} | {pn['engagement_nominal']} nominal, {pn['worst_case']} worst (limits {pn['limits']}) |",
         f"| Printability | {ok(pr)} | base {pr['parts']['base']['orientation']}, lid {pr['parts']['lid']['orientation']} |"]
    ps = C.get('pcba_stl', {})
    if 'rows' in ps:
        L += ['', f"Real PCBA STL ({ps['file']}, {ps['bodies']} bodies, {ps['mtime']}): " + ', '.join(
            f"{k} {v['vol_mm3']} mm3 / gap {v['min_gap']}" for k, v in ps['rows'].items()) + f" -> {'pass' if ps['pass'] else 'FAIL'}."]
    elif ps:
        L += ['', f"PCBA STL: {ps.get('note')}"]
    L += ['', '## Insertion sweep (h = height above seated; play in mm, None = free > 1.2)', '',
          '| h | collision mm3 | bumps mm3 | x+ | x- | z+ | z- |', '|---|---|---|---|---|---|---|']
    L += [f"| {r['h']} | {r['collision_mm3']} | {r['bumps_mm3']} | {r['x+']} | {r['x-']} | {r['z+']} | {r['z-']} |" for r in sw['rows']]
    sl = OUT / 'slice' / 'slice-report.json'
    if sl.exists():
        d = json.loads(sl.read_text())
        L += ['', '## OrcaSlicer CLI (Elegoo CC2 0.4, 0.20 Standard, PETG, 3 walls, 30 %, supports OFF, detect thin walls ON)', '']
        L += [f"- {n}: {d[n].get('time')}, {d[n].get('grams')} g, {d[n].get('layers')} layers, support {d[n].get('support_used')}, "
              f"warnings {len(d[n].get('warnings', []))}" for n in ('base', 'lid') if n in d]
        ps_ = d.get('base', {}).get('pilot_skins')
        if ps_:
            L += [f"- base G-code, blind-pilot skins: {'PRINTED' if ps_['printed'] else 'NOT PRINTED'}"]
    L += ['', NOTES.format(top=M['top'], dtop=M['top'] - P.CASE_TOP, ru=M['roof_under'], cb=M['cb_floor'], tip=tip, tip_c=tip - P.CASE_TOP,
                           th=P.BOSS_TOP - tip, pd=P.PILOT_D, pb=P.PILOT_BOT, mg=tip - P.PILOT_BOT, ay=ay, az=az,
                           zf=P.Z_FRONT_AUDIO, od=P.OPEN_D, pad=P.PAD_DEPTH, hx=P.HOLES[0][0], p4=P.PILOT_BOT + 4.0 + P.SCREW['head_k'] - M['cb_floor'],
                           rf=P.R_TOP_FRONT, re=P.R_END, cr=P.COL_R, cd=2 * P.COL_R, cw=P.COL_R - P.CB_D / 2)]
    L += ['', '## Files', ''] + [f'- {x}' for x in files]
    (OUT / 'REPORT.md').write_text('\n'.join(L) + '\n', encoding='utf-8')


NOTES = """## What it is
- **2 printed parts + 2 screws.** BASE: the rev C base, unchanged (1.0 floor on the case top, window over the J6 opening, 1.2 skirt
  with the X guides and snap ridges, rabbeted top edge, blind dia {pd} pilots), except that the left boss and pilot moved from x 10
  to **x {hx:.2f}** (z -1.00) to clear the jack body (x -2.84..8.65) and give the lid's screw column room.
- LID: a closed rounded cap, no hood. One cavity over the whole board (PCB outline + 0.3), roof underside y {ru} (jack top
  122.60 + 0.3, header tails 119.60), top y {top} ({dtop:.1f} above the case top), front face z {zf} (flush with the base's front
  tongue, 2.5 in front of the case face). Rev C seam: the lid's 0.7 skirt rides over the base rabbet. Top-front edge R{rf}, back
  top edge R2.0, back plan corners concentric with the case's, front plan corners R3.75. The X-Y end corners follow the base's R6.25
  arcs up to the seam and then rise straight with only R{re} at the roof ends (the plug opening top is at y {ay:.2f}+{od}/2, no room for more).
- **Plug opening** in the left end wall: dia {od} circle on the jack barrel axis (y {ay:.2f}, z {az:.2f}), plus a straight slot below it to the
  lid's lower edge (the lid prints roof-down, so the opening has no overhang). A 0.3 deep flat pad on the end face (|z| < 4.9) sits
  behind the nose tip (x -5.34) so a dia 9 plug body seated against the nose never touches the lid.
- **Screws.** Two M2 x 3 pan heads from the top, each in a dia 4.4 counterbore (floor y {cb:.2f}) in a dia {cd:.1f} lid column (wall
  {cw:.1f}) whose underside clamps the PCB top (y 117.60). A nominal 3 mm screw ends at y {tip:.2f}: {mg:.2f} above the blind-pilot skin,
  {tip_c:.2f} above the case top, thread {th:.1f} mm. A 4 mm screw bottoms on the pilot skin with its head {p4:.1f} proud of the counterbore floor.
- **Print:** PETG, no supports. Base on its back face; lid top-down (roof on the bed). Turn on Detect thin wall (the 0.2 skins under the pilots).
- **Build:** drop the PCBA on the base, lid on, 2 screws, push the assembly straight down onto the case top.

## Deviations from the spec
1. Roof ends: only R{re} (the opening top at y 123.35 leaves 0.75 above it; a bigger round would break the opening).
2. Plug opening is a keyhole (circle + slot to the lower edge) for printability, plus a 0.3 end pad; the circle is the spec's dia {od}.
3. Screw columns are dia 6.0 (r {cr:.1f}), not the 3.2 keep-out radius: the jack float (0.19) and a 0.3 gap to parts need it, so the PCB-top clamp is a 0.6 wide ring around the dia 4.8 boss recess.
"""


def main():
    OUT.mkdir(exist_ok=True)
    M = parts.build_all()
    log('solids', M['src'], 'lid top', M['top'])
    E, plate = export(M)
    log('exported')
    K = {n: mf(M[n]) for n in ('base_nb', 'lid', 'bumps')}
    K.update({n: mf(sh) for n, sh in M['pcba'].items()})
    case = load_case()
    log('manifolds')
    C = {'base_identity': check_base_identity(M)}
    log('base identity', C['base_identity']['pass'])
    C['seated'] = check_seated(K, case)
    log('seated', C['seated']['pass'])
    C['fit'] = check_fit(K, M)
    log('fit', C['fit']['pass'])
    C['seam'] = check_seam(K)
    log('seam', C['seam']['pass'])
    C['pins'] = check_pins(M['g'])
    C['plug'] = check_plug(M, K, case)
    log('plug', C['plug']['pass'])
    C['pcba_stl'] = check_pcba_stl(K, case)
    log('pcba stl', C['pcba_stl']['pass'])
    C['screws'] = check_screws(M)
    log('screws', C['screws']['pass'])
    C['keepout'] = check_keepout(M)
    log('keepout', C['keepout']['pass'])
    C['sweep'] = check_sweep(K, case, M['g'])
    log('sweep', C['sweep']['pass'])
    C['print'] = check_print(M)
    log('print', C['print']['pass'])
    C['pass'] = all(v['pass'] for v in C.values() if isinstance(v, dict))
    C['meta'] = {'pcba_source': M['src'], 'lid_top_y': M['top'], 'roof_underside_y': M['roof_under'], 'front_z': P.Z_FRONT_AUDIO,
                 'counterbore_floor_y': M['cb_floor'], 'holes': P.HOLES, 'left_boss_moved': {'from': [10.0, -1.0], 'to': list(P.HOLES[0])},
                 'plug_opening': {'dia': P.OPEN_D, 'axis_y': parts.jack_axis(M['g'])[0], 'axis_z': parts.jack_axis(M['g'])[1]},
                 'screw': P.SCREW, 'screw_tip_y': round(M['cb_floor'] - P.SCREW['L'], 2), 'pilot_bottom_y': P.PILOT_BOT,
                 'volumes_mm3': {n: round(M[n].Volume(), 1) for n in ('base', 'lid')}}
    files = [str(p.relative_to(OUT)) for p in list((OUT / 'print').glob('*')) + list((OUT / 'E').glob('*.stl'))]
    if '--no-render' not in sys.argv:
        try:
            files += renders(E, M)
        except Exception as ex:
            import traceback
            traceback.print_exc()
            files.append(f'renders failed: {ex}')
        log('renders')
    (OUT / 'checks.json').write_text(json.dumps(C, indent=1))
    report(M, C, files + [plate])
    log('PASS' if C['pass'] else 'FAIL', {k: v['pass'] for k, v in C.items() if isinstance(v, dict) and 'pass' in v})
    return 0 if C['pass'] else 1


if __name__ == '__main__':
    sys.exit(main())
