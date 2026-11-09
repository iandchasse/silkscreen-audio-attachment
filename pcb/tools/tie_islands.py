"""Tie a detached GND pour component to the main GND with one routed track (appended to build/routes.json).

    "C:\\Program Files\\KiCad\\9.0\\bin\\python.exe" tools\\tie_islands.py x0 y0 x1 y1     # region in K mm

Rebuilds the router state from build/pads.json + build/routes.json, then routes from a GND via inside the region to the
nearest GND via outside it (both layers allowed).  Run tools\\generate.py afterwards (it reuses routes.json).
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import router as RT  # noqa: E402

ROOT = os.path.dirname(HERE)
x0, y0, x1, y1 = map(float, sys.argv[1:5])
spec = json.load(open(os.path.join(ROOT, "build", "pads.json")))
res = json.load(open(os.path.join(ROOT, "build", "routes.json")))
r = RT.R(spec).setup()
tw = spec["track"]
for t in res["tracks"]:
    l = 0 if t["layer"] == "F" else 1
    r.nid(t["net"])
    for a, b in zip(t["pts"][:-1], t["pts"][1:]):
        r.stamp(t["net"], ("seg", a[0], a[1], b[0], b[1], tw / 2), [l])
for v in res["vias"]:
    r.nid(v["net"])
    r.stamp(v["net"], ("circle", v["x"], v["y"], v.get("d", spec["via_d"]) / 2), [0, 1])
    i0, i1, j0, j1 = r._sub(v["x"] - 0.9, v["y"] - 0.9, v["x"] + 0.9, v["y"] + 0.9)
    d = np.hypot(r.xs[i0:i1][None, :] - v["x"], r.ys[j0:j1][:, None] - v["y"])
    r.viasp[j0:j1, i0:i1] |= d < 0.85
gnd = spec["gnd"]
inside = [v for v in res["vias"] if v["net"] == gnd and x0 <= v["x"] <= x1 and y0 <= v["y"] <= y1]
outside = [v for v in res["vias"] if v["net"] == gnd and not (x0 <= v["x"] <= x1 and y0 <= v["y"] <= y1)]
print("GND vias inside", len(inside), "outside", len(outside))
for v in outside:
    i, j = r.cell(v["x"], v["y"])
    r.tree[gnd][0, j, i] = r.tree[gnd][1, j, i] = True
best = None
for v in inside:
    i, j = r.cell(v["x"], v["y"])
    src = [(0, j, i), (1, j, i)]
    goal = [r.tree[gnd][0].copy(), r.tree[gnd][1].copy()]
    ys_, xs_ = np.nonzero(goal[0] | goal[1])
    tg = [(r.xs[a], r.ys[b]) for b, a in zip(ys_, xs_)]
    win = r.window_for(src, tg, 8.0)
    path = r.search(gnd, src, goal, tg, win)
    if path and (best is None or len(path) < len(best)):
        best = path
if best is None:
    sys.exit("no tie path found")
r.tracks, r.vias = [], []
r.commit(gnd, best)
res["tracks"] += r.tracks
res["vias"] += r.vias
json.dump(res, open(os.path.join(ROOT, "build", "routes.json"), "w"), indent=1)
print("tie track(s):", r.tracks, "vias", r.vias)
