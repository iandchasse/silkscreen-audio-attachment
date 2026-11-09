"""Export the as-built PCBA geometry in the ENCLOSURE frame to build/geometry.json (for the housing checks).

    "C:\\Program Files\\KiCad\\9.0\\bin\\python.exe" tools\\export_geometry.py [out.json]

Units mm.  E frame: X across the device, Y up the device (+Y = top edge; the PCB underside rests on the base floor at
Y 116.60, the F.Cu face and every SMD part are at Y >= 117.60), Z toward the screen.  Boxes are [min, max] per axis.
Read-only on the board.
"""
from __future__ import annotations

import json
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import params as P  # noqa: E402
from kigeom import prims_to_polygon  # noqa: E402

ROOT = os.path.dirname(HERE)
mm = pcbnew.ToMM
S = P.STACK
R3 = lambda v: round(v, 4)
HEIGHT = {"SOT-23-5": 1.25, "SOT-23": 1.15, "TSSOP-20_4.4x6.5mm_P0.65mm": 1.20, "TSSOP-14_4.4x5mm_P0.65mm": 1.20, "R_0603_1608Metric": 0.55,
          "C_0603_1608Metric": 0.95}


def outline_e():
    import build_pcb   # noqa: E402
    poly = prims_to_polygon(build_pcb.outline_prims(), 12)
    return [[R3(c) for c in P.to_e(x, y)] for x, y in poly]


def main(out=None):
    out = out or os.path.join(ROOT, "build", "geometry.json")
    b = pcbnew.LoadBoard(os.path.join(ROOT, P.PROJECT + ".kicad_pcb"))
    bb = b.GetBoardEdgesBoundingBox()
    X0, Z0 = P.to_e(mm(bb.GetLeft()), mm(bb.GetTop()))
    X1, Z1 = P.to_e(mm(bb.GetRight()), mm(bb.GetBottom()))
    outline = outline_e()
    xs = [p[0] for p in outline]
    zs = [p[1] for p in outline]
    assert abs(min(xs) - X0) < 0.03 and abs(max(xs) - X1) < 0.03 and abs(min(zs) - Z0) < 0.03 and abs(max(zs) - Z1) < 0.03, \
        "outline polygon disagrees with the board's Edge.Cuts"
    ty = S["top_y"]
    g = {
        "generator": "pcb/tools/export_geometry.py", "project": P.PROJECT, "rev": P.REVISION, "date": P.DATE,
        "frame": "enclosure E (mm): X = main-board KiCad X - 44.24; Y = 148.25 - main-board KiCad Y; Z = 0 at the main-PCB "
                 "rear face, +Z toward the screen. Audio-PCB KiCad: x_K = X + 100, y_K = Z + 100. F.Cu (all SMD parts, "
                 "the jack) faces +Y; the THT header bodies hang below the underside (Y 116.60).",
        "pcb": {"thickness": S["pcb_t"], "underside_y": S["underside_y"], "top_y": ty,
                "bbox_xz": [[R3(min(xs)), R3(max(xs))], [R3(min(zs)), R3(max(zs))]], "outline_xz": outline},
        "holes": [], "parts": [], "jack": {}, "header": {}, "j6_pins": {}, "forbidden_j6": {},
    }
    pins, bodies = [], []
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        pos = fp.GetPosition()
        X, Z = P.to_e(mm(pos.x), mm(pos.y))
        if ref.startswith("H"):
            for pad in fp.Pads():
                g["holes"].append({"ref": ref, "name": fp.GetValue().split()[0], "purpose": fp.GetValue(),
                                   "dia": R3(mm(pad.GetDrillSize().x)), "x": R3(X), "z": R3(Z), "plated": False})
            continue
        if ref in P.HEADERS:
            D, H = P.HDR, P.HEADERS[ref]
            bx0, bx1, bz0, bz1 = P.header_body(ref)
            for pad in fp.Pads():
                pX, pZ = P.to_e(mm(pad.GetPosition().x), mm(pad.GetPosition().y))
                pins.append({"pad": pad.GetNumber(), "ref": ref, "net": pad.GetNetname().lstrip("/"), "x": R3(pX),
                             "z": R3(pZ), "square": D["post_sq"], "y_post_tip": S["post_tip_y"],
                             "y_tail_tip": S["tail_tip_y"], "segment_y": [S["post_tip_y"], S["tail_tip_y"]]})
            bodies.append({"ref": ref, "mpn": H["mpn"], "lcsc": H["lcsc"], "positions": H["positions"],
                           "body_box": {"x": [bx0, bx1], "z": [bz0, bz1], "y": [R3(S["underside_y"] - D["body_h"]), S["underside_y"]]}})
            continue
        if ref == "J4":
            J = P.JACK
            by0, by1 = J["body_y"]
            ny0, ny1 = J["nose_y"]
            jx, jz = J["X"], J["Z"]
            body = {"x": [R3(jx + by0), R3(jx + by1)], "z": [R3(jz - J["body_x"]), R3(jz + J["body_x"])],
                    "y": [ty, R3(ty + J["height"])]}
            nose = {"x": [R3(jx + ny0), R3(jx + ny1)], "z": [R3(jz - J["nose_d"] / 2), R3(jz + J["nose_d"] / 2)],
                    "y": [ty, R3(ty + J["height"])]}
            g["jack"] = {"ref": "J4", "mpn": J["mpn"], "lcsc": J["lcsc"], "body_box": body, "nose_box": nose,
                         "nose": {"x": [R3(jx + ny0), R3(jx + ny1)], "dia": J["nose_d"], "axis_y": R3(ty + J["axis_h"]), "axis_z": R3(jz)},
                         "nose_tip_x": R3(jx + ny0), "axis": {"y": R3(ty + J["axis_h"]), "z": R3(jz), "direction": [-1, 0, 0],
                                                              "x_range": [R3(jx + ny0), R3(jx + by1)]},
                         "outer_dia": J["nose_d"], "bore_dia": J["bore_d"], "plug_entry_x": R3(jx + ny0),
                         "pads": [{"pad": p.GetNumber(), "net": p.GetNetname().lstrip("/"),
                                   "x": R3(P.to_e(mm(p.GetPosition().x), mm(p.GetPosition().y))[0]),
                                   "z": R3(P.to_e(mm(p.GetPosition().x), mm(p.GetPosition().y))[1])}
                                  for p in fp.Pads() if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD],
                         "pegs": [{"x": R3(jx + py), "z": R3(jz), "dia": J["peg_d"]} for _, py in J["pegs"]]}
            g["holes"].extend({"ref": "J4", "name": "peg", "purpose": "jack peg", "dia": J["peg_d"], "x": R3(jx + py),
                               "z": R3(jz), "plated": False} for _, py in J["pegs"])
            continue
        pb = [pad.GetBoundingBox() for pad in fp.Pads()]
        x0 = min(P.to_e(mm(q.GetLeft()), 0)[0] for q in pb)
        x1 = max(P.to_e(mm(q.GetRight()), 0)[0] for q in pb)
        z0 = min(P.to_e(0, mm(q.GetTop()))[1] for q in pb)
        z1 = max(P.to_e(0, mm(q.GetBottom()))[1] for q in pb)
        kind = fp.GetFPIDAsString().split(":")[-1]
        g["parts"].append({"ref": ref, "kind": kind, "value": fp.GetValue(), "x": R3(X), "z": R3(Z),
                           "body_box": {"x": [R3(x0), R3(x1)], "z": [R3(z0), R3(z1)], "y": [ty, R3(ty + HEIGHT[kind])]},
                           "note": "pad bounding box (conservative), height from the package"})
    bodies.sort(key=lambda d: d["ref"])
    D = P.HDR
    eng = [round(f - S["post_tip_y"], 3) for f in P.J6_FACE_Y]
    g["header"] = {
        "refs": [d["ref"] for d in bodies], "bodies": bodies, "drill": D["drill"], "pad": D["pad"],
        "part_data": {"body_h": D["body_h"], "post": D["post"], "tail": D["tail"], "post_sq": D["post_sq"], "source": D["source"]},
        "pins": sorted(pins, key=lambda p: int(p["pad"])), "j6_face_y": list(P.J6_FACE_Y), "engagement": eng,
        "engagement_limits": list(P.ENGAGEMENT_LIMITS),
        "body_y": [R3(S["underside_y"] - D["body_h"]), S["underside_y"]], "tail_tip_y": S["tail_tip_y"],
        "post_tip_y": S["post_tip_y"]}
    if len(pins) != 6:
        raise SystemExit(f"geometry: header pins {pins}")
    g["parts"].sort(key=lambda d: (d["ref"][0], int(d["ref"][1:])))
    g["holes"].sort(key=lambda d: (d["ref"], d["x"]))
    g["j6_pins"] = {str(k): {"x": v[0], "z": v[1]} for k, v in P.J6["pins"].items()}
    g["forbidden_j6"] = {str(k): {"x": P.J6["pins"][k][0], "z": P.J6["pins"][k][1], "radius": P.FORBID_R, "why": w}
                         for k, w in P.FORBIDDEN.items()}
    g["checks"] = {"lowest_y": S["post_tip_y"], "highest_y": R3(ty + P.JACK["height"])}
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(g, fh, indent=1)
    print("geometry:", out)
    return out


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
