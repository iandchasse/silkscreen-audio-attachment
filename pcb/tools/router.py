"""Two-layer grid router for the audio attachment (numpy only; runs under KiCad's python or any python with numpy).

    python router.py in.json out.json

in.json (K frame, mm): {"grid", "clearance", "track", "via_d", "via_drill", "edge_clear", "bbox": [x0,y0,x1,y1],
  "outline": {x0,y0,x1,y1,r}, "holes": [{x,y,r}], "via_block": [{x,y,r}], "pads": [{ref,num,net,x,y,shape,w,h,layers}],
  "order": [net, ...], "gnd": "GND", "skip_gnd_refs": [...]}
Every pad is stamped as copper of its net; routing is an A* with a turn penalty over (layer, cell, heading), vias
between the two layers, string-pulled to straight segments.  GND pads of SMD parts get a short stub to a legal via
(the board has GND pours on both layers); other nets are routed as trees.  Writes {"tracks", "vias", "failed"}.
"""
from __future__ import annotations

import heapq
import json
import math
import sys

import numpy as np

SQ2 = math.sqrt(2.0)
DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]


class R:
    def __init__(self, spec):
        s = spec
        self.s = s
        self.G = s["grid"]
        self.cl = s["clearance"]
        self.tw = s["track"]
        self.vd = s["via_d"]
        self.margin = 0.03
        x0, y0, x1, y1 = s["bbox"]
        self.x0, self.y0 = x0, y0
        self.nx = int(round((x1 - x0) / self.G)) + 1
        self.ny = int(round((y1 - y0) / self.G)) + 1
        self.xs = x0 + np.arange(self.nx) * self.G
        self.ys = y0 + np.arange(self.ny) * self.G
        shp = (2, self.ny, self.nx)
        self.own_t = np.full(shp, -1, np.int16)
        self.mul_t = np.zeros(shp, bool)
        self.own_v = np.full(shp, -1, np.int16)
        self.mul_v = np.zeros(shp, bool)
        self.stat_t = np.zeros(shp, bool)
        self.stat_v = np.zeros(shp, bool)
        self.viasp = np.zeros((self.ny, self.nx), bool)      # via spacing (hole to hole)
        self.nopad = np.zeros((self.ny, self.nx), bool)      # no via in / next to an SMD pad
        self.rt = self.cl + self.tw / 2 + self.margin
        self.rv = self.cl + self.vd / 2 + self.margin
        self.netid = {}
        self.tree = {}                                       # net -> bool (2, ny, nx) target mask
        self.tracks, self.vias, self.failed = [], [], []
        self.esc = []
        self.pad_vias = []
        self.stubs = {}

    # ---------------------------------------------------------------- stamping
    def nid(self, net):
        if net not in self.netid:
            self.netid[net] = len(self.netid)
            self.tree[net] = np.zeros((2, self.ny, self.nx), bool)
        return self.netid[net]

    def _sub(self, bx0, by0, bx1, by1):
        i0 = max(int(math.floor((bx0 - self.x0) / self.G)), 0)
        i1 = min(int(math.ceil((bx1 - self.x0) / self.G)) + 1, self.nx)
        j0 = max(int(math.floor((by0 - self.y0) / self.G)), 0)
        j1 = min(int(math.ceil((by1 - self.y0) / self.G)) + 1, self.ny)
        return i0, i1, j0, j1

    def dist(self, shape, i0, i1, j0, j1):
        X = self.xs[i0:i1][None, :]
        Y = self.ys[j0:j1][:, None]
        k = shape[0]
        if k == "rect":
            _, cx, cy, hx, hy = shape
            return np.hypot(np.maximum(np.abs(X - cx) - hx, 0), np.maximum(np.abs(Y - cy) - hy, 0))
        if k == "circle":
            _, cx, cy, r = shape
            return np.maximum(np.hypot(X - cx, Y - cy) - r, 0)
        _, ax, ay, bx, by, hw = shape                         # segment with half width
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        if L2 == 0:
            return np.maximum(np.hypot(X - ax, Y - ay) - hw, 0)
        t = np.clip(((X - ax) * dx + (Y - ay) * dy) / L2, 0, 1)
        return np.maximum(np.hypot(X - (ax + t * dx), Y - (ay + t * dy)) - hw, 0)

    def bbox(self, shape):
        k = shape[0]
        if k == "rect":
            return shape[1] - shape[3], shape[2] - shape[4], shape[1] + shape[3], shape[2] + shape[4]
        if k == "circle":
            return shape[1] - shape[3], shape[2] - shape[3], shape[1] + shape[3], shape[2] + shape[3]
        return min(shape[1], shape[3]) - shape[5], min(shape[2], shape[4]) - shape[5], \
            max(shape[1], shape[3]) + shape[5], max(shape[2], shape[4]) + shape[5]

    def stamp(self, net, shape, layers):
        n = self.nid(net)
        bx0, by0, bx1, by1 = self.bbox(shape)
        for own, mul, rad in ((self.own_t, self.mul_t, self.rt), (self.own_v, self.mul_v, self.rv)):
            i0, i1, j0, j1 = self._sub(bx0 - rad, by0 - rad, bx1 + rad, by1 + rad)
            if i1 <= i0 or j1 <= j0:
                continue
            m = self.dist(shape, i0, i1, j0, j1) < rad
            for l in layers:
                o = own[l, j0:j1, i0:i1]
                mu = mul[l, j0:j1, i0:i1]
                free = m & (o == -1)
                o[free] = n
                mu |= m & (o != -1) & (o != n)

    def stamp_static(self, shape, rad_t, rad_v, layers=(0, 1)):
        bx0, by0, bx1, by1 = self.bbox(shape)
        rad = max(rad_t, rad_v)
        i0, i1, j0, j1 = self._sub(bx0 - rad, by0 - rad, bx1 + rad, by1 + rad)
        d = self.dist(shape, i0, i1, j0, j1)
        for l in layers:
            self.stat_t[l, j0:j1, i0:i1] |= d < rad_t
            self.stat_v[l, j0:j1, i0:i1] |= d < rad_v

    def blocked(self, net, l, via=False):
        n = self.netid[net]
        own, mul, st = (self.own_v, self.mul_v, self.stat_v) if via else (self.own_t, self.mul_t, self.stat_t)
        o = own[l]
        return ((o != -1) & ((o != n) | mul[l])) | st[l]

    # ---------------------------------------------------------------- setup
    def setup(self):
        s = self.s
        o = s["outline"]
        cx, cy = (o["x0"] + o["x1"]) / 2, (o["y0"] + o["y1"]) / 2
        hx, hy, r = (o["x1"] - o["x0"]) / 2, (o["y1"] - o["y0"]) / 2, o["r"]
        X = self.xs[None, :]
        Y = self.ys[:, None]
        qx = np.abs(X - cx) - (hx - r)
        qy = np.abs(Y - cy) - (hy - r)
        sdf = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r
        edge_t = s["edge_clear"] + self.tw / 2 + self.margin
        edge_v = s["edge_clear"] + self.vd / 2 + self.margin
        for l in (0, 1):
            self.stat_t[l] |= sdf > -edge_t
            self.stat_v[l] |= sdf > -edge_v
        for h in s["holes"]:
            keep = h.get("keep", 0.5)
            self.stamp_static(("circle", h["x"], h["y"], h["r"]), keep + self.tw / 2 + self.margin,
                              max(keep, 0.4) + self.vd / 2 + self.margin)
        for h in s["via_block"]:
            self.stamp_static(("circle", h["x"], h["y"], h["r"]), 0.0, h.get("rv", 0.5) + 0.3)
        for p in s["pads"]:
            self.nid(p["net"] or "~none")
        for p in s["pads"]:
            net = p["net"] or "~none"
            if p["shape"] == "circle":
                shp = ("circle", p["x"], p["y"], p["w"] / 2)
            else:
                shp = ("rect", p["x"], p["y"], p["w"] / 2, p["h"] / 2)
            self.stamp(net, shp, [0] if p["layers"] == ["F"] else [0, 1])
            if p["layers"] == ["F"]:
                self.stamp_nopad(shp)
            p["_shape"] = shp
            if p["layers"] != ["F"]:
                self.stamp_static(("circle", p["x"], p["y"], 0.0), 0.0, 1.2)
        # a via must keep clear of every hole: PTH header pads act as holes through a plated pad (already copper)
        return self

    def stamp_nopad(self, shp):
        bx0, by0, bx1, by1 = self.bbox(shp)
        rad = 0.30
        i0, i1, j0, j1 = self._sub(bx0 - rad, by0 - rad, bx1 + rad, by1 + rad)
        self.nopad[j0:j1, i0:i1] |= self.dist(shp, i0, i1, j0, j1) < rad

    def via_legal(self, net):
        return ~(self.blocked(net, 0, True) | self.blocked(net, 1, True) | self.viasp | self.nopad)

    # ---------------------------------------------------------------- geometry helpers
    def cell(self, x, y):
        return int(round((x - self.x0) / self.G)), int(round((y - self.y0) / self.G))

    def pad_cells(self, p, net):
        """(layer, j, i) cells inside pad p that are free for net."""
        shp = p["_shape"]
        bx0, by0, bx1, by1 = self.bbox(shp)
        i0, i1, j0, j1 = self._sub(bx0, by0, bx1, by1)
        d = self.dist(shp, i0, i1, j0, j1)
        out = []
        for l in ([0] if p["layers"] == ["F"] else [0, 1]):
            bl = self.blocked(net, l)[j0:j1, i0:i1]
            jj, ii = np.nonzero((d <= 1e-9) & ~bl)
            out += [(l, j0 + a, i0 + b) for a, b in zip(jj, ii)]
        return out

    def los(self, net, l, a, b, blk):
        (ax, ay), (bx, by) = a, b
        n = int(max(abs(bx - ax), abs(by - ay)) / (self.G * 0.5)) + 1
        for k in range(n + 1):
            t = k / n
            i, j = self.cell(ax + (bx - ax) * t, ay + (by - ay) * t)
            if blk[j, i]:
                return False
        return True

    def stamp_track(self, net, l, a, b):
        self.stamp(net, ("seg", a[0], a[1], b[0], b[1], self.tw / 2), [l])
        t = self.tree[net][l]
        n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1])) / (self.G * 0.5)) + 1
        for k in range(n + 1):
            f = k / n
            i, j = self.cell(a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
            t[j, i] = True

    def add_via(self, net, x, y):
        self.vias.append({"net": net, "x": round(x, 4), "y": round(y, 4)})
        self.stamp(net, ("circle", x, y, self.vd / 2), [0, 1])
        i0, i1, j0, j1 = self._sub(x - 0.9, y - 0.9, x + 0.9, y + 0.9)
        d = np.hypot(self.xs[i0:i1][None, :] - x, self.ys[j0:j1][:, None] - y)
        self.viasp[j0:j1, i0:i1] |= d < 0.85
        i, j = self.cell(x, y)
        self.tree[net][0, j, i] = True
        self.tree[net][1, j, i] = True

    # ---------------------------------------------------------------- search
    def search(self, net, sources, goal, targets_xy, window):
        """A* from `sources` [(l,j,i)] to a cell where goal[l][j,i]; returns [(l,j,i)] or None."""
        G = self.G
        blk = [self.blocked(net, 0), self.blocked(net, 1)]
        vl = self.via_legal(net)
        wi0, wi1, wj0, wj1 = window
        if targets_xy:
            pts = targets_xy if len(targets_xy) <= 300 else targets_xy[:: max(1, len(targets_xy) // 300)]
            h = None
            for (tx, ty) in pts:
                dx = np.abs(self.xs[wi0:wi1][None, :] - tx)
                dy = np.abs(self.ys[wj0:wj1][:, None] - ty)
                o = (dx + dy) + (SQ2 - 2) * np.minimum(dx, dy)
                h = o if h is None else np.minimum(h, o)
        else:
            h = np.zeros((wj1 - wj0, wi1 - wi0))
        TURN, VIA, BL = 0.35, 6.0, 1.08
        best = {}
        prev = {}
        pq = []
        cnt = 0
        for (l, j, i) in sources:
            if not (wi0 <= i < wi1 and wj0 <= j < wj1):
                continue
            k = (l, j, i, 8)
            best[k] = 0.0
            prev[k] = None
            heapq.heappush(pq, (float(h[j - wj0, i - wi0]), cnt, 0.0, k))
            cnt += 1
        while pq:
            f, _, g, k = heapq.heappop(pq)
            if g > best.get(k, 1e18) + 1e-9:
                continue
            l, j, i, d = k
            if goal[l][j, i]:
                path = []
                kk = k
                while kk is not None:
                    path.append(kk[:3])
                    kk = prev[kk]
                return path[::-1]
            for nd, (di, dj) in enumerate(DIRS):
                ni, nj = i + di, j + dj
                if not (wi0 <= ni < wi1 and wj0 <= nj < wj1) or blk[l][nj, ni]:
                    continue
                if di and dj and (blk[l][j, ni] or blk[l][nj, i]):
                    continue
                step = (SQ2 if (di and dj) else 1.0) * G * (BL if l else 1.0)
                if d != 8 and d != nd:
                    step += TURN * (1 if abs(d - nd) % 8 in (1, 7) else 2)
                ng = g + step
                nk = (l, nj, ni, nd)
                if ng < best.get(nk, 1e18) - 1e-9:
                    best[nk] = ng
                    prev[nk] = k
                    heapq.heappush(pq, (ng + float(h[nj - wj0, ni - wi0]), cnt, ng, nk))
                    cnt += 1
            if vl[j, i] and not blk[1 - l][j, i]:
                nk = (1 - l, j, i, 8)
                ng = g + VIA
                if ng < best.get(nk, 1e18) - 1e-9:
                    best[nk] = ng
                    prev[nk] = k
                    heapq.heappush(pq, (ng + float(h[j - wj0, i - wi0]), cnt, ng, nk))
                    cnt += 1
        return None

    def commit(self, net, path, via_end=False):
        """Turn a cell path into straight segments (string pulling per layer run) + vias; stamp them."""
        runs, cur = [], [path[0]]
        for c in path[1:]:
            if c[0] != cur[-1][0]:
                runs.append(cur)
                cur = [c]
            else:
                cur.append(c)
        runs.append(cur)
        for r_idx, run in enumerate(runs):
            l = run[0][0]
            pts = [(self.xs[c[2]], self.ys[c[1]]) for c in run]
            blk = self.blocked(net, l)
            out = [pts[0]]
            a = 0
            while a < len(pts) - 1:
                b = len(pts) - 1
                while b > a + 1 and not self.los(net, l, pts[a], pts[b], blk):
                    b -= 1
                out.append(pts[b])
                a = b
            if len(out) >= 2 and out[0] != out[-1]:
                self.tracks.append({"net": net, "layer": "F" if l == 0 else "B", "pts": [[round(float(x), 4), round(float(y), 4)] for x, y in out]})
                for u, v in zip(out[:-1], out[1:]):
                    self.stamp_track(net, l, u, v)
            elif len(out) == 1 or out[0] == out[-1]:
                i, j = self.cell(*out[0])
                self.tree[net][l, j, i] = True
            if r_idx < len(runs) - 1 or via_end:
                x, y = pts[-1]
                self.add_via(net, float(x), float(y))
        return

    # ---------------------------------------------------------------- nets
    def window_for(self, cells, targets_xy, pad=7.0):
        xs = [self.xs[c[2]] for c in cells] + [t[0] for t in targets_xy]
        ys = [self.ys[c[1]] for c in cells] + [t[1] for t in targets_xy]
        i0, j0 = self.cell(min(xs) - pad, min(ys) - pad)
        i1, j1 = self.cell(max(xs) + pad, max(ys) + pad)
        return max(i0, 0), min(i1 + 1, self.nx), max(j0, 0), min(j1 + 1, self.ny)

    def route_gnd(self, pads, gnd, radius=1.0):
        """Every SMD GND pad gets its own via within `radius` of the pad centre (into the B.Cu pour)."""
        for p in pads:
            src = self.pad_cells(p, gnd)
            if not src:
                self.failed.append(f"{p['ref']}.{p['num']} {gnd}: no free cell inside the pad")
                continue
            win = self.window_for(src, [], radius + 1.0)
            wi0, wi1, wj0, wj1 = win
            X = self.xs[None, :]
            Y = self.ys[:, None]
            near = np.hypot(X - p["x"], Y - p["y"]) <= radius
            path = None
            for strict in (True, False):
                keep = self.nopad
                if not strict:
                    self.nopad = np.zeros_like(self.nopad)
                vl = self.via_legal(gnd) & near
                self.nopad = keep
                goal = [vl & ~self.blocked(gnd, 0), np.zeros_like(vl)]
                if goal[0].any():
                    path = self.search(gnd, src, goal, [], win)
                if path is not None:
                    break
            if path is None:
                self.failed.append(f"{p['ref']}.{p['num']} {gnd}: no via spot within {radius} mm")
                continue
            n0 = len(self.vias)
            self.commit(gnd, path, via_end=True)
            self.pad_vias += [(v['x'], v['y'], f"{p['ref']}.{p['num']}") for v in self.vias[n0:]]
            self.mark(p, gnd)

    def escapes(self, pads, gnd, length=0.9):
        """Reserve a short straight escape stub outward from every IC signal pad (so neighbours cannot box it in)."""
        by_ref = {}
        for p in pads:
            by_ref.setdefault(p["ref"], []).append(p)
        for ref, ps in by_ref.items():
            if not ref.startswith("U") or ref == "U1" and False:
                continue
            cx = sum(p["x"] for p in ps) / len(ps)
            cy = sum(p["y"] for p in ps) / len(ps)
            for p in ps:
                if not p["net"] or p["net"] == gnd:
                    continue
                horiz = p["w"] > p["h"]
                if horiz:
                    d = (1 if p["x"] > cx else -1, 0)
                    half = p["w"] / 2
                else:
                    d = (0, 1 if p["y"] > cy else -1)
                    half = p["h"] / 2
                a = (p["x"], p["y"])
                b = (p["x"] + d[0] * (half + length), p["y"] + d[1] * (half + length))
                net = p["net"]
                blk = self.blocked(net, 0)
                if self.los(net, 0, a, b, blk):
                    self.tracks.append({"net": net, "layer": "F", "pts": [[round(a[0], 4), round(a[1], 4)], [round(b[0], 4), round(b[1], 4)]]})
                    self.stamp(net, ("seg", a[0], a[1], b[0], b[1], self.tw / 2), [0])
                    self.esc.append((net, p))
                    self.stubs[(p["ref"], p["num"])] = (a, b)

    def stub_cells(self, p):
        st = self.stubs.get((p["ref"], p["num"]))
        if not st:
            return []
        (ax, ay), (bx, by) = st
        n = int(max(abs(bx - ax), abs(by - ay)) / (self.G * 0.5)) + 1
        out = set()
        for k in range(n + 1):
            i, j = self.cell(ax + (bx - ax) * k / n, ay + (by - ay) * k / n)
            out.add((0, j, i))
        return list(out)

    def pour_connectivity(self, gnd):
        """Flood the GND-free area of both layers from the J1 GND pad; report pad vias that are not in it."""
        free = [~self.blocked(gnd, 0), ~self.blocked(gnd, 1)]
        vm = np.zeros((self.ny, self.nx), bool)
        for v in self.vias:
            if v["net"] == gnd:
                i, j = self.cell(v["x"], v["y"])
                vm[j, i] = True
        seed = [p for p in self.s["pads"] if p["net"] == gnd and p["layers"] != ["F"]][0]
        i, j = self.cell(seed["x"], seed["y"])
        m = [np.zeros((self.ny, self.nx), bool), np.zeros((self.ny, self.nx), bool)]
        m[0][j, i] = m[1][j, i] = True
        for l in (0, 1):
            free[l] = free[l] | m[l]
        while True:
            old = m[0].sum() + m[1].sum()
            for l in (0, 1):
                d = m[l].copy()
                d[1:] |= m[l][:-1]; d[:-1] |= m[l][1:]; d[:, 1:] |= m[l][:, :-1]; d[:, :-1] |= m[l][:, 1:]
                m[l] = d & free[l]
            link = (m[0] | m[1]) & vm
            m[0] |= link & free[0]
            m[1] |= link & free[1]
            if m[0].sum() + m[1].sum() == old:
                break
        bad = []
        for (x, y, nm) in self.pad_vias:
            i, j = self.cell(x, y)
            if not (m[0][max(j - 1, 0):j + 2, max(i - 1, 0):i + 2].any() or m[1][max(j - 1, 0):j + 2, max(i - 1, 0):i + 2].any()):
                bad.append(nm)
        return bad

    def cleanup_stubs(self):
        """Trim each escape stub back to the farthest point where something of the same net connects to it (drop it if none)."""
        def seg_pt(u, v, pt):
            dx, dy = v[0] - u[0], v[1] - u[1]
            L2 = dx * dx + dy * dy or 1e-9
            f = max(0, min(1, ((pt[0] - u[0]) * dx + (pt[1] - u[1]) * dy) / L2))
            return f, math.hypot(pt[0] - (u[0] + f * dx), pt[1] - (u[1] + f * dy))
        stub_keys = {(tuple(map(lambda c: round(c, 4), a)), tuple(map(lambda c: round(c, 4), b))) for (a, b) in self.stubs.values()}
        out = []
        for k, t in enumerate(self.tracks):
            key = (tuple(t["pts"][0]), tuple(t["pts"][1])) if len(t["pts"]) == 2 else None
            if key not in stub_keys:
                out.append(t)
                continue
            u, v = t["pts"]
            best = 0.0
            for k2, t2 in enumerate(self.tracks):
                if k2 == k or t2["net"] != t["net"]:
                    continue
                for pt in (t2["pts"][0], t2["pts"][-1]):
                    f, d = seg_pt(u, v, pt)
                    if d <= 0.13:
                        best = max(best, f)
            for vv in self.vias:
                if vv["net"] == t["net"]:
                    f, d = seg_pt(u, v, (vv["x"], vv["y"]))
                    if d <= 0.3:
                        best = max(best, f)
            for pp in self.s["pads"]:
                if pp["net"] != t["net"] or (abs(pp["x"] - u[0]) < 1e-3 and abs(pp["y"] - u[1]) < 1e-3):
                    continue
                for q10 in range(1, 11):
                    f = q10 / 10
                    pt = (u[0] + (v[0] - u[0]) * f, u[1] + (v[1] - u[1]) * f)
                    if self.dist_pt(pp, pt) <= 0.0:
                        best = max(best, f)
                        break
            if best > 0.02:
                nv = [round(u[0] + (v[0] - u[0]) * best, 4), round(u[1] + (v[1] - u[1]) * best, 4)]
                out.append({"net": t["net"], "layer": "F", "pts": [u, nv]})
        self.tracks = out

    def dist_pt(self, p, pt):
        hx, hy = p["w"] / 2, p["h"] / 2
        if p["shape"] == "circle":
            return max(math.hypot(pt[0] - p["x"], pt[1] - p["y"]) - hx, 0)
        return math.hypot(max(abs(pt[0] - p["x"]) - hx, 0), max(abs(pt[1] - p["y"]) - hy, 0))

    def stitch(self, gnd, pitch=3.0):
        """GND stitching vias on a coarse grid wherever a via fits (ties every pour fragment to both layers)."""
        vl = self.via_legal(gnd)
        x = self.x0 + 1.0
        while x < self.x0 + (self.nx - 1) * self.G:
            y = self.y0 + 1.0
            while y < self.y0 + (self.ny - 1) * self.G:
                bestc = None
                for dx in (0, -0.4, 0.4, -0.8, 0.8):
                    for dy in (0, -0.4, 0.4, -0.8, 0.8):
                        i, j = self.cell(x + dx, y + dy)
                        if vl[j, i] and not self.viasp[j, i]:
                            bestc = (self.xs[i], self.ys[j])
                            break
                    if bestc:
                        break
                if bestc:
                    self.add_via(gnd, float(bestc[0]), float(bestc[1]))
                    vl = self.via_legal(gnd)
                y += pitch
            x += pitch

    def mark(self, p, net):
        for (l, j, i) in self.pad_cells(p, net) + self.stub_cells(p):
            self.tree[net][l, j, i] = True

    def route_net(self, net, pads):
        if len(pads) < 2:
            return
        self.nid(net)
        todo = list(pads)
        ok_first = [p for p in todo if self.pad_cells(p, net)]
        if not ok_first:
            self.failed.append(f"{net}: no pad has a free cell")
            return
        first = ok_first[0]
        todo.remove(first)
        self.mark(first, net)
        done = [first]
        while todo:
            todo.sort(key=lambda p: min(math.hypot(p["x"] - q["x"], p["y"] - q["y"]) for q in done))
            p = todo.pop(0)
            src = self.pad_cells(p, net)
            blk0 = self.blocked(net, 0)
            src = src + [c for c in self.stub_cells(p) if not blk0[c[1], c[2]]]
            if not src:
                self.failed.append(f"{p['ref']}.{p['num']} {net}: no free cell inside the pad")
                continue
            goal = [self.tree[net][0] & ~self.blocked(net, 0), self.tree[net][1] & ~self.blocked(net, 1)]
            if not (goal[0].any() or goal[1].any()):
                self.failed.append(f"{net}: empty tree")
                continue
            ys_, xs_ = np.nonzero(goal[0] | goal[1])
            tg = [(self.xs[i], self.ys[j]) for j, i in zip(ys_, xs_)]
            win = self.window_for(src, tg, 6.0)
            path = self.search(net, src, goal, tg, win)
            if path is None:
                self.failed.append(f"{p['ref']}.{p['num']} {net}: no path")
                continue
            self.commit(net, path)
            self.mark(p, net)
            done.append(p)


def attempt(args):
    import random
    inp, seed = args
    spec = json.load(open(inp, encoding="utf-8"))
    r = R(spec).setup()
    pads = spec["pads"]
    gnd = spec["gnd"]
    skip = set(spec.get("skip_gnd_refs", []))
    gnd_pads = [p for p in pads if p["net"] == gnd and p["layers"] == ["F"] and p["ref"] not in skip
                and f'{p["ref"]}.{p["num"]}' not in spec.get("pour_gnd", [])]
    by = {}
    for p in pads:
        if p["net"] and p["net"] != gnd:
            by.setdefault(p["net"], []).append(p)
    order = [n for n in spec["order"] if n in by] + sorted(set(by) - set(spec["order"]))
    ws = [n for n in order if n.endswith("I2S_WS")]
    if seed:
        rng = random.Random(seed)
        order = [n for _, n in sorted((i + rng.uniform(-7, 7), n) for i, n in enumerate(order))]
    order = ws + [n for n in order if n not in ws]
    r.escapes(pads, gnd)
    r.route_gnd(gnd_pads, gnd)
    for net in order:
        r.route_net(net, by[net])
    pour = [p for p in pads if f'{p["ref"]}.{p["num"]}' in spec.get("pour_gnd", [])]
    nfail = len(r.failed)
    for p in pour:                         # inward via under the IC body (pad sandwiched by two signal pins)
        ps = [q for q in pads if q["ref"] == p["ref"]]
        cx = sum(q["x"] for q in ps) / len(ps)
        d = 1 if cx > p["x"] else -1
        vl = r.via_legal(gnd)
        for off in (0.65, 0.8, 1.0, 1.3):
            vx = p["x"] + d * (p["w"] / 2 + off)
            i, j = r.cell(vx, p["y"])
            if vl[j, i] and r.los(gnd, 0, (p["x"], p["y"]), (float(r.xs[i]), float(r.ys[j])), r.blocked(gnd, 0)):
                a_ = (p["x"], p["y"])
                b_ = (float(r.xs[i]), float(r.ys[j]))
                r.tracks.append({"net": gnd, "layer": "F", "pts": [[round(a_[0], 4), round(a_[1], 4)], [round(b_[0], 4), round(b_[1], 4)]]})
                r.stamp_track(gnd, 0, a_, b_)
                r.add_via(gnd, b_[0], b_[1])
                break
        else:                              # small (0.5/0.25) via inside the pad: the pad is boxed in by two signal pins
            vx = p["x"] + d * 0.3
            r.vias.append({"net": gnd, "x": round(vx, 4), "y": round(p["y"], 4), "d": 0.55, "drill": 0.25})
    del r.failed[nfail:]
    r.cleanup_stubs()
    for nm in r.pour_connectivity(gnd):
        r.failed.append(f"{nm} GND via sits in a detached pour pocket")
    r.stitch(gnd)
    return len(r.failed), seed, r.tracks, r.vias, r.failed


def main(inp, outp):
    import multiprocessing as mp
    best = None
    seeds = [6, 0, 1, 2, 3, 4, 5, 7] + list(range(8, 40))
    with mp.Pool(min(8, mp.cpu_count())) as pool:
        for k in range(0, len(seeds), 8):
            res = pool.map(attempt, [(inp, sd) for sd in seeds[k:k + 8]])
            for nf, sd, tr, vi, fl in res:
                print("attempt seed", sd, "failed", nf, flush=True)
                if best is None or nf < best[0]:
                    best = (nf, sd, tr, vi, fl)
            if best[0] == 0:
                break
    nf, sd, tr, vi, fl = best
    json.dump({"tracks": tr, "vias": vi, "failed": fl, "seed": sd}, open(outp, "w"), indent=1)
    print("best seed", sd, "tracks", len(tr), "vias", len(vi), "failed", nf)
    for f in fl:
        print("  FAIL", f)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
