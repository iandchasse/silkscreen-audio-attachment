"""Derive the JLC CPL rotation offsets of each footprint from the EasyEDA footprints of the ordered LCSC parts.

    "C:\\Program Files\\KiCad\\9.0\\bin\\python.exe" tools\\cpl_offsets.py

EasyEDA JSON (easyeda.com/api/products/<C#>/components?version=6.4.19.5) is saved in docs/sources/ee_*.json.  Both frames
are y-down screen frames.  For each part: find the rotation (multiple of 90) that maps the EasyEDA pad set (centred on
the pad centroid) onto the KiCad pad set; JLC rotation = KiCad rotation + that offset (JLC rotates ITS footprint).
"""
from __future__ import annotations

import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import params as P  # noqa: E402
import generate as G  # noqa: E402

SRC = os.path.join(G.ROOT, "docs", "sources")
PARTS = {  # footprint name -> LCSC part whose EasyEDA footprint JLC uses
    "SOT-23-5": "C2862740", "TSSOP-20_4.4x6.5mm_P0.65mm": "C107671", "TSSOP-14_4.4x5mm_P0.65mm": "C183097",
    "SOT-23": "C8592", "R_0603_1608Metric": "C25803", "C_0603_1608Metric": "C19702",
    G.FP_JACK: "C668608",
}


def ee_pads(code):
    d = json.load(open(os.path.join(SRC, f"ee_{code}.json"), encoding="utf-8"))["result"]
    shapes = d["packageDetail"]["dataStr"]["shape"]
    out = []
    for s in shapes:
        if s.startswith("PAD~"):
            a = s.split("~")
            out.append((a[8], float(a[2]) * 0.254, float(a[3]) * 0.254))
    return out


def kicad_pads(name):
    t = open(os.path.join(G.PRETTY, name + ".kicad_mod"), encoding="utf-8").read()
    return [(m.group(1), float(m.group(2).split()[0]), float(m.group(2).split()[1]))
            for m in re.finditer(r'\(pad "([^"]*)" (?:smd|thru_hole) \w+\s+\(at ([-\d. ]+)\)', t)]


def best_rot(ee, ki):
    cx = sum(p[1] for p in ee) / len(ee), sum(p[2] for p in ee) / len(ee)
    ck = sum(p[1] for p in ki) / len(ki), sum(p[2] for p in ki) / len(ki)
    res = []
    for rot in (0, 90, 180, 270):
        a = math.radians(rot)
        err = 0.0
        ok = True
        for num, x, y in ee:
            x, y = x - cx[0], y - cx[1]
            rx, ry = x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a)   # CCW on a y-down screen
            cands = [(math.hypot(rx - (kx - ck[0]), ry - (ky - ck[1]))) for n2, kx, ky in ki if n2 == num]
            if not cands:
                ok = False
                break
            err = max(err, min(cands))
        if ok:
            res.append((err, rot))
    return sorted(res)


def main():
    out = {}
    for name, code in PARTS.items():
        ee, ki = ee_pads(code), kicad_pads(name)
        # pads of the same number occur twice on some parts: compare as multisets by nearest match
        r = best_rot(ee, ki)
        out[name] = {"lcsc": code, "candidates": [(round(e, 3), rot) for e, rot in r[:2]]}
        print(f"{name:32s} {code:9s} EE pads {len(ee):2d} KiCad pads {len(ki):2d}: best (err mm, rot of the EE footprint onto KiCad) {out[name]['candidates']}")
    return out


if __name__ == "__main__":
    main()
