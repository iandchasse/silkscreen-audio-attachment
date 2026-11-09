"""STEP models and the enclosure-frame PCBA, built with CadQuery.

Run with the CadQuery python (the enclosure project's venv); generate.py and make_outputs.py call it
through CQ_PYTHON:

    <cq-python> tools/make_step_models.py models <out_dir>
    <cq-python> tools/make_step_models.py eframe <board.step> <board_only.step> <out.step> <out.stl> <report.json>

Model frame (KiCad 3D-model convention): origin = footprint origin, +z away from the board on the component side,
model +y = footprint -y.  The headers are footprints on B.Cu, so KiCad flips their models: body UNDER the board,
pins through it.  Output STEP headers get a fixed timestamp so the files are byte-stable between runs.
"""
from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import params as P  # noqa: E402

import cadquery as cq  # noqa: E402


def _fix_header(path):
    txt = open(path, encoding="utf-8", errors="replace").read()
    txt = re.sub(r"FILE_NAME\('([^']*)','[^']*'", lambda m: f"FILE_NAME('{os.path.basename(path)}','{P.DATE}T00:00:00'", txt, count=1)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)


def _save(assy, path):
    tmp = path + ".tmp.step"
    try:
        assy.export(tmp)
    except AttributeError:
        assy.save(tmp)
    os.replace(tmp, path)
    _fix_header(path)


def jack_model(path):
    """PJ-313D: 11.5 x 6 x 5 body with the Ø5 nose (2.5 long) and the Ø3.6 plug bore, axis 2.5 above the board.

    Footprint frame: nose toward footprint -y = model +y.  Body footprint y -5.17..6.34, nose -7.65..-5.16.
    """
    Jk = P.JACK
    by0, by1 = Jk["body_y"]
    ny0, ny1 = Jk["nose_y"]
    h = Jk["height"]
    bx = Jk["body_x"]
    # model y = -footprint y
    body = (cq.Workplane("XY").box(2 * bx, by1 - by0, h, centered=(True, False, False)).translate((0, -by1, 0)))
    nose_len = ny1 - ny0
    nose = (cq.Workplane("XZ").workplane(offset=0).center(0, Jk["axis_h"]).circle(Jk["nose_d"] / 2).extrude(-nose_len)
            .translate((0, -ny1, 0)))                 # XZ normal is -y; extrude(-len) goes toward +y
    bore_len = 9.0
    bore = (cq.Workplane("XZ").center(0, Jk["axis_h"]).circle(Jk["bore_d"] / 2).extrude(-bore_len)
            .translate((0, -ny0 - bore_len, 0)))
    shell = body.union(nose)
    shell = shell.cut(cq.Workplane("XZ").center(0, Jk["axis_h"]).circle(Jk["bore_d"] / 2).extrude(-bore_len)
                      .translate((0, -ny0 - bore_len, 0)))
    assy = cq.Assembly(name="PJ-313D")
    assy.add(shell, name="housing", color=cq.Color(0.12, 0.12, 0.13))
    for num, y in Jk["pad_y"].items():
        for side in (-1, 1):
            tab = (cq.Workplane("XY").box(Jk["pad_w"] - 0.5, Jk["pad_h"] - 0.2, 0.15, centered=(True, True, False))
                   .translate((side * Jk["pad_x"], -y, 0)))
            assy.add(tab, name=f"tab_{num}_{side}", color=cq.Color(0.8, 0.8, 0.82))
    _save(assy, path)


def header_model(ref, path):
    """Straight 2.54 mm male header: body on the component plane, square pins from -tail to body_h + post.
    Origin = body centre; the footprint holds PRE-MIRRORED pad x offsets (placed flipped), the model follows them."""
    D = P.HDR
    bx0, bx1, bz0, bz1 = P.header_body(ref)
    body = cq.Workplane("XY").box(bx1 - bx0, bz1 - bz0, D["body_h"], centered=(True, True, False))
    assy = cq.Assembly(name=P.HEADERS[ref]["mpn"])
    assy.add(body, name="body", color=cq.Color(0.08, 0.08, 0.08))
    cx, cz = P.header_centre(ref)
    z_lo, z_hi = -D["tail"], D["body_h"] + D["post"]
    for name, (X, Z) in P.HEADERS[ref]["pads"].items():
        dx, dy = -(X - cx), Z - cz                      # footprint offsets (pre-mirrored)
        post = cq.Workplane("XY").center(dx, -dy).box(D["post_sq"], D["post_sq"], z_hi - z_lo,
                                                      centered=(True, True, False)).translate((0, 0, z_lo))
        assy.add(post, name=f"pin_{name}", color=cq.Color(0.85, 0.7, 0.2))
    _save(assy, path)


def models(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    jack_model(os.path.join(out_dir, "JACK_3.5mm_SHOUHAN_PJ-313D.step"))
    header_model("J1", os.path.join(out_dir, "J6_PLUG_1x4_HC-PZ254-11.5L.step"))
    header_model("J2", os.path.join(out_dir, "J6_PLUG_1x1_HC-PZ254-11.5L.step"))
    print("models written to", out_dir)


def eframe(board_step, board_only_step, out_step, out_stl, report):
    """Board STEP (kicad-cli, user origin 0,0: x_s = x_K, y_s = -y_K, z_s up from the F side) -> enclosure frame.

    The headers are on the underside, so z_B (the B.Cu plane the header bodies hang from) is calibrated on the J1 body:
    its corner vertices sit at z_B - 2.5 and z_B.  Then
        X = x_s - 100,   Y = underside_y + (z_s - z_B),   Z = -y_s - 100
    which is a -90 deg rotation about X (det +1) followed by a translation.
    """
    slab = cq.importers.importStep(board_only_step).val()
    zv = [v.Z for v in slab.Vertices()]
    full = cq.importers.importStep(board_step).val()
    bx0, bx1, bz0, bz1 = P.header_body("J1")
    cxs = [P.to_k(bx0, 0)[0], P.to_k(bx1, 0)[0]]
    cys = [-P.to_k(0, bz0)[1], -P.to_k(0, bz1)[1]]
    corner_z = sorted({round(v.Z, 5) for v in full.Vertices()
                       if min(abs(v.X - c) for c in cxs) < 1e-3 and min(abs(v.Y - c) for c in cys) < 1e-3})
    if len(corner_z) < 2 or abs(corner_z[-1] - corner_z[0] - P.HDR["body_h"]) > 1e-3:
        print("J1 body corners not found in the board STEP:", corner_z)
        sys.exit(4)
    z_b = corner_z[-1]
    s = P.STACK
    shp = cq.importers.importStep(board_step)
    comp = shp.val() if hasattr(shp, "val") else shp
    moved = (comp.rotate(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), -90)
             .translate(cq.Vector(-P.K_OX, s["underside_y"] - z_b, -P.K_OY * 0 - P.K_OY)))
    # NOTE: after the -90 deg rotation a point (x_s, y_s, z_s) is (x_s, z_s, -y_s); the translation adds
    # (-100, 116.60 - z_b, -100): Z = -y_s - 100.
    import math
    X5, Z5 = P.HEADERS["J1"]["pads"]["1"]
    xk, yk = P.to_k(X5, Z5)
    xs, ys, zs = xk, -yk, z_b
    e_pt = (xs - P.K_OX, s["underside_y"] + (zs - z_b), -ys - P.K_OY)
    bb = moved.BoundingBox()
    verts = [(v.X, v.Y, v.Z) for v in moved.Vertices()]
    lo = [v for v in verts if v[1] < s["post_tip_y"] + 0.02]
    hi = [v for v in verts if v[1] > s["tail_tip_y"] - 0.02]
    pads = {(ref, nm): xz for ref, h in P.HEADERS.items() for nm, xz in h["pads"].items()}

    def clusters(vs):
        out = []
        for (ref, nm), (px, pz) in pads.items():
            near = [v for v in vs if abs(v[0] - px) < 0.5 and abs(v[2] - pz) < 0.5]
            out.append({"ref": ref, "pad": nm, "n": len(near),
                        "x": round(sum(v[0] for v in near) / len(near), 4) if near else None,
                        "z": round(sum(v[2] for v in near) / len(near), 4) if near else None,
                        "y": round(sum(v[1] for v in near) / len(near), 4) if near else None})
        return out
    # header bodies: vertices of the J1/J2/J3 body boxes
    body_y = []
    for ref in P.HEADERS:
        b = P.header_body(ref)
        for v in verts:
            if b[0] - 1e-3 <= v[0] <= b[1] + 1e-3 and b[2] - 1e-3 <= v[2] <= b[3] + 1e-3 and v[1] < s["underside_y"] + 0.3 \
                    and v[1] > s["body_bottom_y"] - 0.02:
                body_y.append((ref, round(v[1], 4)))
    body_ys = sorted({y for _, y in body_y})
    rep = {"z_B_underside_plane": z_b, "slab_z": [round(min(zv), 4), round(max(zv), 4)],
           "bbox": {"xmin": round(bb.xmin, 4), "xmax": round(bb.xmax, 4), "ymin": round(bb.ymin, 4),
                    "ymax": round(bb.ymax, 4), "zmin": round(bb.zmin, 4), "zmax": round(bb.zmax, 4)},
           "pad1_sample_E": [round(c, 4) for c in e_pt], "post_tips": clusters(lo), "tail_tips": clusters(hi),
           "header_body_vertex_y": body_ys, "rotation": "-90 deg about X (x, y, z) -> (x, z, -y); det +1"}
    errs = []
    vy0, vy1 = min(v[1] for v in verts), max(v[1] for v in verts)
    rep["vertex_y_range"] = [round(vy0, 4), round(vy1, 4)]
    if abs(vy0 - s["post_tip_y"]) > 0.01:
        errs.append(f"lowest vertex Y {vy0:.4f} != post tip {s['post_tip_y']}")
    if abs(vy1 - (s["top_y"] + P.JACK["height"])) > 0.15:
        errs.append(f"highest vertex Y {vy1:.4f} != jack top {s['top_y'] + P.JACK['height']}")
    for grp, ykey, what in ((rep["post_tips"], "post_tip_y", "post tip"), (rep["tail_tips"], "tail_tip_y", "tail tip")):
        for c in grp:
            px, pz = pads[(c["ref"], c["pad"])]
            if not c["n"] or abs(c["x"] - px) > 0.02 or abs(c["z"] - pz) > 0.02 or abs(c["y"] - s[ykey]) > 0.01:
                errs.append(f"{c['ref']} pad {c['pad']} {what} not at X {px} Z {pz} Y {s[ykey]}: {c}")
    # kicad-cli writes the board as a 0.91 dielectric slab and seats B-side models 0.085 off the nominal 1.0 board
    # underside, so a header body top can read up to ~0.09 above Y 116.60 although the part sits flush (the post tips,
    # checked to 0.01 above, prove the seating). Allow 0.10 for that export artefact.
    BODY_TOP_TOL = 0.10
    if not body_ys or max(body_ys) > s["underside_y"] + BODY_TOP_TOL or min(body_ys) < s["body_bottom_y"] - 0.01:
        errs.append(f"header body vertices Y {body_ys} not within {s['body_bottom_y']}..{s['underside_y']}")
    if any(y > s["underside_y"] + BODY_TOP_TOL for _, y in body_y if y < s["underside_y"] + 0.3 and abs(y - s["underside_y"]) > BODY_TOP_TOL
           and y < s["top_y"] - 0.2):
        errs.append("header body vertices poke above the underside")
    if abs(e_pt[0] - X5) > 1e-6 or abs(e_pt[2] - Z5) > 1e-6 or abs(e_pt[1] - s["underside_y"]) > 1e-6:
        errs.append(f"sample transform wrong: {e_pt}")
    rep["errors"] = errs
    with open(report, "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=2)
    if errs:
        print("\n".join(errs))
        sys.exit(3)
    cq.exporters.export(moved, out_step)
    _fix_header(out_step)
    cq.exporters.export(moved, out_stl, tolerance=0.02, angularTolerance=0.2)
    print("E-frame PCBA:", out_step, out_stl, "headers OK", rep["bbox"])


if __name__ == "__main__":
    if sys.argv[1] == "models":
        models(sys.argv[2])
    elif sys.argv[1] == "eframe":
        eframe(*sys.argv[2:7])
    else:
        sys.exit("usage: models <dir> | eframe <board.step> <board_only.step> <out.step> <out.stl> <report.json>")
