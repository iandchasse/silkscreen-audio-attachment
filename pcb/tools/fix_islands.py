"""Tie detached GND pour components to the main one with extra stitching vias (appended to build/routes.json).

    "C:\\Program Files\\KiCad\\9.0\\bin\\python.exe" tools\\fix_islands.py     # then: tools\\generate.py (reuses routes.json)

A via is placed where a pour island of the detached component overlaps a pour island of the main component on the other
layer, with the point and eight neighbours 0.7 mm around it inside both islands (so it keeps clear of other copper).
"""
import json
import math
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import params as P  # noqa: E402

ROOT = os.path.dirname(HERE)
b = pcbnew.LoadBoard(os.path.join(ROOT, P.PROJECT + ".kicad_pcb"))
mm, fm = pcbnew.ToMM, pcbnew.FromMM
pts = [t.GetPosition() for t in b.GetTracks() if t.GetClass() == "PCB_VIA" and t.GetNetname().endswith("GND")]
for fp in b.GetFootprints():
    for pad in fp.Pads():
        if pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and pad.GetNetname().endswith("GND"):
            pts.append(pad.GetPosition())
isl = []
for z in b.Zones():
    lay = z.GetFirstLayer()
    ps = z.GetFilledPolysList(lay)
    for i in range(ps.OutlineCount()):
        isl.append((lay, ps.COutline(i)))
par = list(range(len(isl)))


def find(x):
    while par[x] != x:
        par[x] = par[par[x]]
        x = par[x]
    return x


for pos in pts:
    hit = [k for k, (l, o) in enumerate(isl) if o.PointInside(pos)]
    for k in hit[1:]:
        par[find(k)] = find(hit[0])
comps = {}
for k in range(len(isl)):
    comps.setdefault(find(k), []).append(k)
big = max(comps.values(), key=len)
rp = os.path.join(ROOT, "build", "routes.json")
res = json.load(open(rp))
added = []
for c in comps.values():
    if c is big:
        continue
    done = False
    for k in c:
        lk, ok = isl[k]
        bb = ok.BBox()
        x0, x1, y0, y1 = mm(bb.GetLeft()), mm(bb.GetRight()), mm(bb.GetTop()), mm(bb.GetBottom())
        y = y0
        while y <= y1 and not done:
            x = x0
            while x <= x1 and not done:
                probe = [(x, y)] + [(x + 0.45 * math.cos(a * math.pi / 4), y + 0.45 * math.sin(a * math.pi / 4)) for a in range(8)]
                ins = lambda o, q: o.PointInside(pcbnew.VECTOR2I(fm(q[0]), fm(q[1])))
                if all(ins(ok, q) for q in probe):
                    for m in big:
                        lm, om = isl[m]
                        if lm != lk and all(ins(om, q) for q in probe):
                            res["vias"].append({"net": "/GND", "x": round(x, 3), "y": round(y, 3)})
                            added.append((round(x, 3), round(y, 3)))
                            done = True
                            break
                x += 0.15
            y += 0.15
        if done:
            break
    print("component", [(mm(isl[k][1].BBox().GetLeft()) - 100) for k in c], "tied" if done else "NOT TIED")
json.dump(res, open(rp, "w"), indent=1)
print("added vias (K):", added)

# ---- remove stitching vias that sit only in detached components (nothing of theirs connects to the main pour)
res = json.load(open(rp))
gtr = [t for t in res["tracks"] if t["net"].endswith("GND")]
removed = []
for c in comps.values():
    if c is big:
        continue
    for v in list(res["vias"]):
        if not v["net"].endswith("GND"):
            continue
        p = pcbnew.VECTOR2I(fm(v["x"]), fm(v["y"]))
        if any(isl[k][1].PointInside(p) for k in c):
            if not any(math.hypot(v["x"] - q[0], v["y"] - q[1]) < 0.3 for t in gtr for q in t["pts"]):
                res["vias"].remove(v)
                removed.append((v["x"], v["y"]))
json.dump(res, open(rp, "w"), indent=1)
print("removed detached stitching vias (K):", removed)
