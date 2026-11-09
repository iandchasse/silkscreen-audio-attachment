"""List the filled GND pour islands that contain no GND via / plated pad (those cannot tie the two layers together).

    "C:\\Program Files\\KiCad\\9.0\\bin\\python.exe" tools\\zone_islands.py
"""
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import params as P  # noqa: E402

b = pcbnew.LoadBoard(os.path.join(os.path.dirname(HERE), P.PROJECT + ".kicad_pcb"))
mm = pcbnew.ToMM
pts = [(t.GetPosition(), "via") for t in b.GetTracks() if t.GetClass() == "PCB_VIA" and t.GetNetname().endswith("GND")]
for fp in b.GetFootprints():
    for pad in fp.Pads():
        if pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and pad.GetNetname().endswith("GND"):
            pts.append((pad.GetPosition(), "pth"))
for z in b.Zones():
    lay = z.GetFirstLayer()
    ps = z.GetFilledPolysList(lay)
    for i in range(ps.OutlineCount()):
        o = ps.COutline(i)
        bb = o.BBox()
        has = [k for p, k in pts if o.PointInside(p)]
        if not has:
            print(b.GetLayerName(lay), "island", i, "bbox E x %.2f..%.2f z %.2f..%.2f" % (mm(bb.GetLeft()) - 100, mm(bb.GetRight()) - 100, mm(bb.GetTop()) - 100, mm(bb.GetBottom()) - 100), "area %.2f" % (o.Area() / 1e12))

# ---- connected components of (layer, island) joined through GND vias / PTH pads
isl = []
for z in b.Zones():
    lay = z.GetFirstLayer()
    ps = z.GetFilledPolysList(lay)
    for i in range(ps.OutlineCount()):
        isl.append((lay, i, ps.COutline(i)))
par = list(range(len(isl)))
def find(x):
    while par[x] != x:
        par[x] = par[par[x]]
        x = par[x]
    return x
for pos, kind in pts:
    hit = [k for k, (l, i, o) in enumerate(isl) if o.PointInside(pos)]
    for k in hit[1:]:
        par[find(k)] = find(hit[0])
comps = {}
for k in range(len(isl)):
    comps.setdefault(find(k), []).append(k)
big = max(comps.values(), key=len)
for c in comps.values():
    if c is big:
        continue
    for k in c:
        l, i, o = isl[k]
        bb = o.BBox()
        print("DETACHED", b.GetLayerName(l), "E x %.2f..%.2f z %.2f..%.2f" % (mm(bb.GetLeft()) - 100, mm(bb.GetRight()) - 100, mm(bb.GetTop()) - 100, mm(bb.GetBottom()) - 100), "area %.2f" % (o.Area() / 1e12))
print("components", len(comps), "islands", len(isl))
