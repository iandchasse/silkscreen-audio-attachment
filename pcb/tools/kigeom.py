"""Small geometry and S-expression helpers shared by the generator scripts.

Coordinates are KiCad millimetres (x right, y down).  Nothing here imports
pcbnew, so it runs under any Python 3.
"""
from __future__ import annotations

import math
import uuid as _uuid

# Deterministic UUIDs: the same generator input always yields the same files,
# so git diffs show real changes only.
_NS = _uuid.UUID("5a1c5c7e-11e7-4f1e-9b1a-00000000a77c")


def uid(*parts) -> str:
    return str(_uuid.uuid5(_NS, "/".join(str(p) for p in parts)))


def q(s: str) -> str:
    """Quote a string for an S-expression."""
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def f(v: float) -> str:
    """Format a number the way KiCad does (no trailing zeros, no -0)."""
    v = round(float(v), 6)
    if v == 0:
        v = 0.0
    s = f"{v:.6f}".rstrip("0").rstrip(".")
    return s if s not in ("", "-0") else "0"


# ---------------------------------------------------------------- vectors
def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def mul(a, k):
    return (a[0] * k, a[1] * k)


def norm(a):
    l = math.hypot(a[0], a[1])
    return (a[0] / l, a[1] / l)


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


# ---------------------------------------------------------------- fillets
def _corner(p_prev, p, p_next, r):
    """Tangent points, arc midpoint and centre for a fillet of radius r at p."""
    u = norm(sub(p, p_prev))
    v = norm(sub(p_next, p))
    c = cross(u, v)
    d = max(-1.0, min(1.0, dot(u, v)))
    phi = math.acos(d)                 # turning angle, 0 = straight
    if r <= 0 or phi < 1e-9:
        return None
    t = r * math.tan(phi / 2.0)
    t1 = sub(p, mul(u, t))
    t2 = add(p, mul(v, t))
    n = (-u[1], u[0]) if c > 0 else (u[1], -u[0])
    centre = add(t1, mul(n, r))
    m = add(centre, mul(norm(sub(p, centre)), r))
    return {"t1": t1, "t2": t2, "mid": m, "centre": centre, "t": t}


def rounded_path(points, radii, closed):
    """Turn a polyline into ('line', a, b) / ('arc', start, mid, end) primitives.

    radii[i] is the fillet radius at vertex i (ignored at open-path ends).
    Raises ValueError if two neighbouring fillets would overlap on an edge.
    """
    n = len(points)
    corners = [None] * n
    rng = range(n) if closed else range(1, n - 1)
    for i in rng:
        corners[i] = _corner(points[i - 1], points[i], points[(i + 1) % n], radii[i])
    # check edge budgets
    edges = range(n) if closed else range(n - 1)
    for i in edges:
        j = (i + 1) % n
        need = (corners[i]["t"] if corners[i] else 0) + (corners[j]["t"] if corners[j] else 0)
        if need > dist(points[i], points[j]) + 1e-6:
            raise ValueError(f"fillets at vertices {i},{j} overlap: need {need:.3f} mm, edge {dist(points[i], points[j]):.3f} mm")
    prims = []
    start = lambda i: corners[i]["t2"] if corners[i] else points[i]
    end = lambda i: corners[i]["t1"] if corners[i] else points[i]
    for i in edges:
        j = (i + 1) % n
        a, b = start(i), end(j)
        if dist(a, b) > 1e-6:
            prims.append(("line", a, b))
        if corners[j] and (closed or j < n - 1):
            c = corners[j]
            prims.append(("arc", c["t1"], c["mid"], c["t2"]))
    return prims


def arc_points(start, mid, end, seg=24):
    """Polyline approximation of a 3-point arc (for previews and polygons)."""
    ax, ay = start
    bx, by = mid
    cx, cy = end
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
    r = math.hypot(ax - ux, ay - uy)
    a0 = math.atan2(ay - uy, ax - ux)
    a1 = math.atan2(by - uy, bx - ux)
    a2 = math.atan2(cy - uy, cx - ux)
    # choose the sweep direction that passes through the midpoint
    def sweep(a_from, a_to):
        s = (a_to - a_from) % (2 * math.pi)
        return s
    s_total = sweep(a0, a2)
    s_mid = sweep(a0, a1)
    if s_mid > s_total:          # go the other way
        s_total = s_total - 2 * math.pi
    return [(ux + r * math.cos(a0 + s_total * k / seg), uy + r * math.sin(a0 + s_total * k / seg)) for k in range(seg + 1)]


def prims_to_polygon(prims, seg=16):
    pts = []
    for p in prims:
        if p[0] == "line":
            pts += [p[1], p[2]]
        else:
            pts += arc_points(p[1], p[2], p[3], seg)
    out = []
    for p in pts:
        if not out or dist(out[-1], p) > 1e-4:
            out.append(p)
    if dist(out[0], out[-1]) < 1e-4:
        out.pop()
    return out


def path_length(prims):
    tot = 0.0
    for p in prims:
        if p[0] == "line":
            tot += dist(p[1], p[2])
        else:
            pts = arc_points(p[1], p[2], p[3], 64)
            tot += sum(dist(pts[k], pts[k + 1]) for k in range(len(pts) - 1))
    return tot


def rotate(p, deg, about=(0.0, 0.0)):
    a = math.radians(deg)
    x, y = p[0] - about[0], p[1] - about[1]
    # KiCad rotation is counter-clockwise on screen with y down == clockwise in maths coords
    return (about[0] + x * math.cos(a) + y * math.sin(a), about[1] - x * math.sin(a) + y * math.cos(a))
