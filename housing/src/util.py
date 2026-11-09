"""Geometry and mesh helpers (CadQuery / OCP / trimesh / scipy). No rtree needed."""
import math
from functools import reduce

import cadquery as cq
import numpy as np
import trimesh
from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCP.gp import gp_Vec
from scipy.spatial import cKDTree

V = cq.Vector


# ------------------------------------------------------------------ solids
def poly_face(pts3):
    return cq.Face.makeFromWires(cq.Wire.makePolygon([V(*p) for p in pts3], close=True))


def prism(pts3, vec):
    return cq.Shape.cast(BRepPrimAPI_MakePrism(poly_face(pts3).wrapped, gp_Vec(*vec)).Shape())


def prism_x(pts_yz, x0, x1):
    return prism([(x0, y, z) for y, z in pts_yz], (x1 - x0, 0, 0))


def prism_y(pts_xz, y0, y1):
    return prism([(x, y0, z) for x, z in pts_xz], (0, y1 - y0, 0))


def prism_z(pts_xy, z0, z1):
    return prism([(x, y, z0) for x, y in pts_xy], (0, 0, z1 - z0))


def box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl_y(x, z, r, y0, y1):
    return cq.Solid.makeCylinder(r, y1 - y0, V(x, y0, z), V(0, 1, 0))


def cyl_x(y, z, r, x0, x1):
    return cq.Solid.makeCylinder(r, x1 - x0, V(x0, y, z), V(1, 0, 0))


def arc(cx, cy, r, a0, a1, n=24):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def fuse(*shapes):
    shapes = [s for s in shapes if s is not None]
    return shapes[0].fuse(*shapes[1:]).clean() if len(shapes) > 1 else shapes[0]


def cut(a, *tools):
    return a.cut(*tools).clean() if tools else a


def translate(s, v):
    return s.translate(V(*v))


def mirror_x(s, x0=30.0):
    return s.mirror('YZ', V(x0, 0, 0))


def one_solid(s):
    """Fused result as a single Solid when possible (compounds of one solid)."""
    sol = s.Solids()
    return sol[0] if len(sol) == 1 else s


# ------------------------------------------------------------------ meshes
def to_mesh(shape, tol=0.01, ang=0.1):
    vs, fs = shape.tessellate(tol, ang)
    m = trimesh.Trimesh(np.array([v.toTuple() for v in vs], dtype=float), np.array(fs, dtype=np.int64), process=True)
    m.merge_vertices()
    trimesh.repair.fix_normals(m)
    return m


def load_stl(path):
    m = trimesh.load(str(path), force='mesh')
    m.merge_vertices()
    return m


def sample_triangles(tris, s):
    """Deterministic grid samples on triangles (n,3,3): returns points, triangle index, normals."""
    tris = np.asarray(tris, float)
    out_p, out_i = [], []
    e = np.stack([tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 1], tris[:, 0] - tris[:, 2]], 1)
    el = np.linalg.norm(e, axis=2)
    nrm = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    nl = np.linalg.norm(nrm, axis=1)
    nl[nl == 0] = 1
    nrm = nrm / nl[:, None]
    for i in range(len(tris)):
        k = int(np.argmax(el[i]))
        p0, p1, p2 = tris[i, k], tris[i, (k + 1) % 3], tris[i, (k + 2) % 3]
        L = el[i, k]
        if L < 1e-9:
            continue
        u = (p1 - p0) / L
        w = p2 - p0
        cu = w @ u
        wv = w - cu * u
        h = np.linalg.norm(wv)
        pts = [tris[i]]
        # edges
        for a, b in ((p0, p1), (p1, p2), (p2, p0)):
            n = max(1, int(math.ceil(np.linalg.norm(b - a) / s)))
            t = np.arange(n + 1)[:, None] / n
            pts.append(a + (b - a) * t)
        if h > s * 0.5:
            v = wv / h
            nu, nv = int(math.ceil(L / s)), int(math.ceil(h / s))
            gu, gv = np.meshgrid((np.arange(nu) + 0.5) * L / nu, (np.arange(nv) + 0.5) * h / nv)
            gu, gv = gu.ravel(), gv.ravel()
            t = gv / h
            ok = (gu >= cu * t) & (gu <= L - (L - cu) * t)
            if ok.any():
                pts.append(p0 + gu[ok, None] * u + gv[ok, None] * v)
        P = np.vstack(pts)
        out_p.append(P)
        out_i.append(np.full(len(P), i))
    P = np.vstack(out_p)
    I = np.concatenate(out_i)
    return P, I, nrm[I]


class SurfaceField:
    """Distance-to-surface queries against a mesh: KD over grid samples, exact refinement on triangles."""

    def __init__(self, meshes, s=0.08, crop=None):
        tris = []
        for m in meshes:
            t = m.triangles
            if crop is not None:
                t = t[crop(t)]
            tris.append(t)
        self.tris = np.vstack(tris)
        self.P, self.I, _ = sample_triangles(self.tris, s)
        self.tree = cKDTree(self.P)
        self.s = s

    def approx(self, pts):
        d, _ = self.tree.query(pts, workers=-1)
        return d

    def exact_min(self, pts, margin=None, cap=6000):
        """Exact min distance from pts (m,3) to the surface; returns (dist, point, closest)."""
        if len(pts) == 0:
            return math.inf, None, None
        margin = margin or 1.5 * self.s
        d = self.approx(pts)
        order = np.argsort(d)[:cap]
        sel = order[d[order] <= d[order[0]] + margin]
        best = (math.inf, None, None)
        lists = self.tree.query_ball_point(pts[sel], d[sel] + margin, workers=-1)
        pi, ti = [], []
        for j, lst in zip(sel, lists):
            tt = np.unique(self.I[lst])
            pi.append(np.full(len(tt), j))
            ti.append(tt)
        pi, ti = np.concatenate(pi), np.concatenate(ti)
        for a in range(0, len(pi), 200000):
            q = trimesh.triangles.closest_point(self.tris[ti[a:a + 200000]], pts[pi[a:a + 200000]])
            dd = np.linalg.norm(q - pts[pi[a:a + 200000]], axis=1)
            k = int(np.argmin(dd))
            if dd[k] < best[0]:
                best = (float(dd[k]), pts[pi[a + k]].tolist(), q[k].tolist())
        return best


def manifold_of(mesh):
    import manifold3d as m3
    return m3.Manifold(m3.Mesh(vert_properties=np.asarray(mesh.vertices, np.float32),
                               tri_verts=np.asarray(mesh.faces, np.uint32)))


def mvolume(m):
    return float(m.volume()) if hasattr(m, 'volume') else float(m.get_volume())


def mbbox(m):
    b = m.bounding_box() if hasattr(m, 'bounding_box') else None
    mesh = m.to_mesh()
    vp = np.asarray(mesh.vert_properties)[:, :3]
    if len(vp) == 0:
        return None
    return vp.min(0).tolist(), vp.max(0).tolist()


def minter(a, b):
    return a ^ b


def mtranslate(m, v):
    return m.translate(list(map(float, v)))
