"""Handedness + placement gate (DESIGN-SPEC sec 1).

    "C:\\Program Files\\KiCad\\9.0\\bin\\python.exe" tools\\check_handedness.py

Reads the saved board (read-only) and checks, in the ENCLOSURE frame E:
  1. the K -> E map x_K = X + 100, y_K = Z + 100 is a proper rotation (the F.Cu face seen from +Y is unmirrored: E's X
     runs right and +Z runs down the screen) and equals the kicad-cli STEP chain (x_s, y_s, z_s) = (x_K, -y_K, z) ->
     (X, Y, Z) = (x_s - 100, Y0 + z, -y_s - 100), det +1;
  2. every header pad (J1 1-4, J2 9, J3 12) lands on its J6 pin within 0.02 with the right net, on B.Cu footprints;
  3. the jack J4: 6 pads at x -1.05 / 2.17 / 5.67 (+-0.63), z +-3.60 with 1 = GND, 2 = HP_R, 3 = HP_L; nose tip at x -5.34;
  4. no pad and no hole within 1.0 of J6 5, 6, 7, 8, 10, 11;
  5. the 4 NPTH (2 x 4.80 screw columns, 2 x 1.30 jack pegs) where params says; copper keeps 0.40 / tracks 0.50 off the columns;
  6. every non-jack SMD part on F.Cu inside x 9..62, z -5.5..5.5, height <= 1.3, courtyard >= 3.2 from the column
     centres, pads >= 0.5 from the header pads;
  7. every NPTH-to-board-edge web >= 0.50;
  8. silk minimums (stroke >= 0.15, visible text >= 1.0).
Writes build/gate_handedness.json and exits 1 on any failure.
"""
from __future__ import annotations

import json
import math
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import params as P  # noqa: E402
from kigeom import arc_points  # noqa: E402

ROOT = os.path.dirname(HERE)
mm = pcbnew.ToMM
PART_H = {"SOT-23-5": 1.25, "SOT-23": 1.15, "TSSOP-20_4.4x6.5mm_P0.65mm": 1.20, "TSSOP-14_4.4x5mm_P0.65mm": 1.20, "R_0603_1608Metric": 0.55,
          "C_0603_1608Metric": 0.95}


def seg_dist(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
    return math.hypot(p[0] - (ax + t * dx), p[1] - (ay + t * dy))


def xy(v):
    return (mm(v.x), mm(v.y))


def k_to_step_to_e(xk, yk, z_above_b=0.0):
    """K -> kicad-cli STEP (x_K, -y_K, z) -> E."""
    xs, ys, zs = xk, -yk, z_above_b
    return (xs - 100.0, P.STACK["underside_y"] + zs, -ys - 100.0)


def pad_dist_fn(pad):
    c = xy(pad.GetPosition())
    bb = pad.GetBoundingBox()
    hx, hy = mm(bb.GetWidth()) / 2, mm(bb.GetHeight()) / 2
    if pad.GetShape(pcbnew.F_Cu) == pcbnew.PAD_SHAPE_CIRCLE:
        return lambda p, c=c, r=hx: max(math.hypot(p[0] - c[0], p[1] - c[1]) - r, 0.0)
    return lambda p, c=c, hx=hx, hy=hy: math.hypot(max(abs(p[0] - c[0]) - hx, 0), max(abs(p[1] - c[1]) - hy, 0))


def copper_items(board):
    items = []
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            c, r = xy(t.GetPosition()), mm(t.GetWidth(pcbnew.F_Cu)) / 2
            items.append(("via", "via", t.GetNetname(), lambda p, c=c, r=r: math.hypot(p[0] - c[0], p[1] - c[1]) - r))
        else:
            w = mm(t.GetWidth()) / 2
            a, b = xy(t.GetStart()), xy(t.GetEnd())
            items.append(("track", "track", t.GetNetname(), lambda p, a=a, b=b, w=w: seg_dist(p, a, b) - w))
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                continue
            items.append(("pad", f"{fp.GetReference()}.{pad.GetNumber()}", pad.GetNetname(), pad_dist_fn(pad)))
    return items


def edge_dist_fn(board):
    prims = []
    for d in board.GetDrawings():
        if d.GetLayer() != pcbnew.Edge_Cuts:
            continue
        if d.GetShape() == pcbnew.SHAPE_T_SEGMENT:
            prims.append(("seg", xy(d.GetStart()), xy(d.GetEnd())))
        elif d.GetShape() == pcbnew.SHAPE_T_ARC:
            prims.append(("arc", arc_points(xy(d.GetStart()), xy(d.GetArcMid()), xy(d.GetEnd()), 256)))
        else:
            raise SystemExit(f"unexpected Edge.Cuts shape {d.GetShapeStr()}")

    def dist(p):
        best = 1e9
        for pr in prims:
            if pr[0] == "seg":
                best = min(best, seg_dist(p, pr[1], pr[2]))
            else:
                pts = pr[1]
                best = min(best, min(seg_dist(p, pts[i], pts[i + 1]) for i in range(len(pts) - 1)))
        return best
    return dist, len(prims)


def silk_items(board):
    silk = (pcbnew.F_SilkS, pcbnew.B_SilkS)
    out = []

    def add_shape(g, owner):
        if g.GetLayer() in silk:
            out.append((f"{owner} {g.GetShapeStr()} on {board.GetLayerName(g.GetLayer())}", "stroke",
                        mm(g.GetWidth()), False))

    def add_text(t, owner):
        if t.GetLayer() in silk and t.IsVisible():
            out.append((f"{owner} text '{t.GetText()}' on {board.GetLayerName(t.GetLayer())}", "text",
                        (mm(t.GetTextHeight()), mm(t.GetTextThickness())), t.GetText()))
    for d in board.GetDrawings():
        if d.GetClass() in ("PCB_TEXT", "PCB_TEXTBOX"):
            add_text(d, "board")
        elif d.GetClass() == "PCB_SHAPE":
            add_shape(d, "board")
    for fp in board.GetFootprints():
        for g in fp.GraphicalItems():
            if g.GetClass() in ("PCB_TEXT", "PCB_TEXTBOX"):
                add_text(g, fp.GetReference())
            elif g.GetClass() == "PCB_SHAPE":
                add_shape(g, fp.GetReference())
        for fld in fp.GetFields():
            add_text(fld, fp.GetReference())
    return out


def courtyard_box(fp):
    xs, ys = [], []
    for g in fp.GraphicalItems():
        if g.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
            bb = g.GetBoundingBox()
            xs += [mm(bb.GetLeft()), mm(bb.GetRight())]
            ys += [mm(bb.GetTop()), mm(bb.GetBottom())]
    if not xs:
        return None
    w = 0.025
    return (min(xs) + w, max(xs) - w, min(ys) + w, max(ys) - w)


def main():
    board = pcbnew.LoadBoard(os.path.join(ROOT, P.PROJECT + ".kicad_pcb"))
    lines, fails = [], []

    def ok(cond, msg):
        lines.append(("PASS " if cond else "FAIL ") + msg)
        if not cond:
            fails.append(msg)

    # ---- 1: the frame map is a proper rotation
    M = [[1, 0, 0], [0, 0, 1], [0, -1, 0]]           # STEP -> E linear part: X = x_s, Y = z_s, Z = -y_s
    det = (M[0][0] * (M[1][1] * M[2][2] - M[1][2] * M[2][1]) - M[0][1] * (M[1][0] * M[2][2] - M[1][2] * M[2][0])
           + M[0][2] * (M[1][0] * M[2][1] - M[1][1] * M[2][0]))
    ok(det == 1, f"STEP->E rotation determinant {det} (proper rotation, not a mirror)")
    # K (x right, y down) on the F.Cu face seen from +Y (eye at +Y looking down -Y): screen right = E +X, toward the
    # viewer = E +Y, so screen up = toward x right = (+Y) x (+X) = -Z and screen down = +Z = K's +y.  Hence
    # x_K = X + 100, y_K = Z + 100 is unmirrored.
    def cross(u, v):
        return (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
    right, toward = (1, 0, 0), (0, 1, 0)
    up = cross(toward, right)
    down = tuple(-c for c in up)
    ok(down == (0, 0, 1), f"F.Cu face seen from +Y: right = +X, down = {down} = +Z, so x_K = X + 100, y_K = Z + 100 is unmirrored")
    # ---- 2: header pads
    tol = P.HANDEDNESS_TOL
    want = {(ref, nm): (xz, P.HEADERS[ref]["nets"][nm]) for ref, h in P.HEADERS.items() for nm, xz in h["pads"].items()}
    pth = [(fp.GetReference(), pad) for fp in board.GetFootprints() for pad in fp.Pads()
           if pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
    ok(len(pth) == len(want) and all(r in P.HEADERS for r, _ in pth),
       f"exactly {len(want)} plated through-holes, all on J1/J2/J3 (found {len(pth)})")
    for ref, pad in pth:
        xk, yk = xy(pad.GetPosition())
        X, Z = P.to_e(xk, yk)
        Xs, Ys, Zs = k_to_step_to_e(xk, yk)
        nm = pad.GetNumber()
        w = want.get((ref, nm))
        if w is None:
            ok(False, f"{ref} pad '{nm}' is not a J6 header pad of this board")
            continue
        (wx, wz), wnet = w
        d = math.hypot(X - wx, Z - wz)
        ok(d <= tol, f"{ref} '{nm}' at E ({X:.3f}, {Z:.3f}) vs J6-{nm} ({wx:.3f}, {wz:.3f}): {d:.4f} <= {tol}")
        ok(abs(Xs - X) < 1e-9 and abs(Zs - Z) < 1e-9 and abs(Ys - P.STACK["underside_y"]) < 1e-9,
           f"{ref} '{nm}' via the STEP chain: E ({Xs:.3f}, Y {Ys:.2f}, {Zs:.3f}) agrees")
        ok(pad.GetNetname().lstrip("/") == wnet, f"{ref} '{nm}' net {pad.GetNetname().lstrip('/')} == {wnet}")
    for ref in P.HEADERS:
        fp = [f for f in board.GetFootprints() if f.GetReference() == ref][0]
        ok(fp.GetLayer() == pcbnew.B_Cu, f"{ref} footprint on B.Cu (body under the board)")

    # ---- 3: jack
    J = P.JACK
    jfp = [f for f in board.GetFootprints() if f.GetReference() == "J4"][0]
    ok(jfp.GetLayer() == pcbnew.F_Cu, "J4 on F.Cu (top side)")
    jx0, jz0 = P.to_e(*xy(jfp.GetPosition()))
    ok(abs(jx0 - J["X"]) < tol and abs(jz0 - J["Z"]) < tol, f"J4 origin at E ({jx0:.3f}, {jz0:.3f})")
    ok(abs(jx0 + J["nose_y"][0] - J["nose_tip_x"]) < tol and round(jfp.GetOrientationDegrees()) % 360 == 90,
       f"J4 nose tip at x {jx0 + J['nose_y'][0]:.3f} (spec {J['nose_tip_x']}), rotation 90 (nose toward -X)")
    pads4 = [p for p in jfp.Pads() if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD]
    ok(len(pads4) == 6, f"J4 has 6 SMD pads (found {len(pads4)})")
    for p in pads4:
        X, Z = P.to_e(*xy(p.GetPosition()))
        nm = p.GetNumber()
        ex = J["X"] + J["pad_y"][nm]
        okpos = any(abs(X - ex) < tol and abs(Z - s * J["pad_x"]) < tol for s in (-1, 1))
        ok(okpos, f"J4 pad {nm} at E ({X:.3f}, {Z:.3f}) (want x {ex:.3f}, z +-3.60)")
        ok(p.GetNetname().lstrip("/") == J["nets"][nm], f"J4 pad {nm} net {p.GetNetname().lstrip('/')} == {J['nets'][nm]}")

    # ---- 4: forbidden J6 positions (pads and holes of any kind)
    holes = []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetDrillSize().x > 0:
                holes.append((fp.GetReference(), pad, xy(pad.GetPosition()), mm(pad.GetDrillSize().x) / 2))
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            holes.append(("via", t, xy(t.GetPosition()), mm(t.GetDrillValue()) / 2))
    pad_fns = [(f"{fp.GetReference()}.{pad.GetNumber()}", pad_dist_fn(pad)) for fp in board.GetFootprints()
               for pad in fp.Pads() if pad.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH]
    vias = [(xy(t.GetPosition()), mm(t.GetWidth(pcbnew.F_Cu)) / 2) for t in board.GetTracks() if t.GetClass() == "PCB_VIA"]
    for pin, why in P.FORBIDDEN.items():
        X, Z = P.J6["pins"][pin]
        p = P.to_k(X, Z)
        dp = min(f(p) for _, f in pad_fns)
        dv = min([math.hypot(p[0] - c[0], p[1] - c[1]) - r for c, r in vias] or [9.0])
        dh = min(math.hypot(p[0] - c[0], p[1] - c[1]) - r for _, _, c, r in holes)
        ok(min(dp, dv, dh) >= P.FORBID_R, f"J6-{pin} ({why}) at E ({X}, {Z}): nearest pad {dp:.3f}, via {dv:.3f}, hole {dh:.3f} (>= {P.FORBID_R})")

    # ---- 5: NPTH
    items = copper_items(board)
    npth = [(r, pad, c, rr) for r, pad, c, rr in holes if r != "via" and pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH]
    peg_e = [(J["X"] + py, J["Z"], J["peg_d"]) for px, py in J["pegs"]]       # footprint (0, y) at rot 90 -> E (X0 + y, Z0)
    want_h = [(X, Z, dia, nm) for nm, dia, X, Z, _ in P.HOLES] + [(x, z, d, "peg") for x, z, d in peg_e]
    ok(len(npth) == len(want_h), f"{len(npth)} NPTH holes (params: {len(want_h)} = 2 screw columns + 2 jack pegs)")
    for X, Z, dia, nm in want_h:
        p = P.to_k(X, Z)
        m = [h for h in npth if math.hypot(h[2][0] - p[0], h[2][1] - p[1]) < 0.02 and abs(2 * h[3] - dia) < 0.001]
        ok(len(m) == 1, f"NPTH {nm} dia {dia} at E ({X:.3f}, {Z:.3f})")
    cols = [(P.to_k(X, Z), dia / 2) for nm, dia, X, Z, _ in P.HOLES]
    min_cu = min(f(c) - r for c, r in cols for _, _, _, f in items)
    min_tr = min(f(c) - r for c, r in cols for kind, _, _, f in items if kind == "track")
    ok(min_cu >= P.HOLE_COPPER_CLEAR - 1e-6, f"copper (pads/tracks/vias) to the screw-column hole edges min {min_cu:.3f} >= {P.HOLE_COPPER_CLEAR}")
    ok(min_tr >= P.HOLE_TRACE_CLEAR - 1e-6, f"tracks to the screw-column hole edges min {min_tr:.3f} >= {P.HOLE_TRACE_CLEAR}")

    # ---- 6: placement
    rx0, rx1, rz0, rz1 = P.PART_REGION
    hdr_pads = [(xy(pad.GetPosition()), mm(pad.GetBoundingBox().GetWidth()) / 2)
                for fp in board.GetFootprints() if fp.GetReference() in P.HEADERS for pad in fp.Pads()]
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref.startswith("H") or ref in P.HEADERS:
            continue
        ok(fp.GetLayer() == pcbnew.F_Cu, f"{ref} on F.Cu")
        if ref == "J4":
            continue
        box = courtyard_box(fp)
        X0, Z0 = P.to_e(box[0], box[2])
        X1, Z1 = P.to_e(box[1], box[3])
        padbox = [pad.GetBoundingBox() for pad in fp.Pads()]
        px0 = min(mm(b.GetLeft()) for b in padbox) - 100
        px1 = max(mm(b.GetRight()) for b in padbox) - 100
        pz0 = min(mm(b.GetTop()) for b in padbox) - 100
        pz1 = max(mm(b.GetBottom()) for b in padbox) - 100
        hits = []
        if not (px0 >= rx0 - 1e-6 and px1 <= rx1 + 1e-6 and pz0 >= rz0 - 1e-6 and pz1 <= rz1 + 1e-6):
            hits.append(f"pads x {px0:.2f}..{px1:.2f} z {pz0:.2f}..{pz1:.2f} outside region {P.PART_REGION}")
        h = PART_H[fp.GetFPIDAsString().split(":")[-1]]
        if h > P.PART_MAX_H:
            hits.append(f"height {h} > {P.PART_MAX_H}")
        for nm, dia, hx, hz, purpose in P.HOLES:
            cx, cz = min(max(hx, X0), X1), min(max(hz, Z0), Z1)
            if math.hypot(cx - hx, cz - hz) < P.COLUMN_KEEPOUT - 1e-6:
                hits.append(f"within {P.COLUMN_KEEPOUT} of {nm} ({math.hypot(cx - hx, cz - hz):.2f})")
        dmin = 9.0
        for pad in fp.Pads():
            f = pad_dist_fn(pad)
            for c, r in hdr_pads:
                dmin = min(dmin, f(c) - r)
        if dmin < P.HDR_CLEAR - 1e-6:
            hits.append(f"pad {dmin:.2f} from a header pad (< {P.HDR_CLEAR})")
        ok(not hits, f"{ref} pads E x {px0:.2f}..{px1:.2f} z {pz0:.2f}..{pz1:.2f}, h {h}: " + (", ".join(hits) or "inside the region, clear of the columns and header pads"))

    # ---- 7: NPTH-to-edge webs
    edist, nprim = edge_dist_fn(board)
    webs = [(edist(c) - r, nm) for (nm, c, r) in
            [(f"{ref}@E({P.to_e(*c)[0]:.2f},{P.to_e(*c)[1]:.2f})", c, rr) for ref, pad, c, rr in npth]]
    for w, nm in sorted(webs):
        ok(w >= P.EDGE_WEB_MIN - 1e-6, f"NPTH {nm}: web to board edge {w:.3f} >= {P.EDGE_WEB_MIN}")
    lines.append(f"INFO outline {nprim} Edge.Cuts primitives; min NPTH web {min(webs)[0]:.3f}")

    # ---- 8: silk legend minimums
    sw, th = P.RULES["silk_line_w"], P.RULES["silk_text_h"]
    strokes, texts = [], []
    for what, kind, val, extra in silk_items(board):
        if kind == "stroke":
            strokes.append((val, what))
            if val < sw - 1e-6:
                ok(False, f"silk stroke {what} width {val:.3f} < {sw}")
        else:
            h, t = val
            texts.append((h, t, what))
            if h < th - 1e-6 or t < sw - 1e-6:
                ok(False, f"silk {what} height {h:.3f} / stroke {t:.3f} (need >= {th} / {sw})")
    wmin = min(v for v, _ in strokes if v > 0)
    ok(wmin >= sw - 1e-6, f"silk: {len(strokes)} strokes, min width {wmin:.3f} >= {sw}")
    ok(min(h for h, _, _ in texts) >= th - 1e-6 and min(t for _, t, _ in texts) >= sw - 1e-6,
       f"silk: {len(texts)} visible texts, min height {min(h for h, _, _ in texts):.3f}, min stroke "
       f"{min(t for _, t, _ in texts):.3f}")

    rep = {"pass": not fails, "fails": fails, "lines": lines}
    os.makedirs(os.path.join(ROOT, "build"), exist_ok=True)
    with open(os.path.join(ROOT, "build", "gate_handedness.json"), "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=2)
    for l in lines:
        print(l)
    print(f"HANDEDNESS/PLACEMENT GATE: {'PASS' if not fails else 'FAIL'} ({len(fails)} failures)")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
