"""2-D cross-section drawings (matplotlib + manifold3d slices): a capped, flat-coloured section through the E-frame meshes.

    section_png(out, [(trimesh_or_path, '#rrggbb', 'label'), ...], x=28.1, box=(z0, z1, y0, y1))

The section plane is x = const; the drawing has +Z (toward the reader) to the LEFT and +Y up, like side_right.png.
"""
from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import trimesh
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MPath

import util as U


def _slice_polys(mesh, x):
    import manifold3d as m3
    v = np.asarray(mesh.vertices, np.float32)[:, [1, 2, 0]]          # (y, z, x): the cut plane x becomes the slicing height
    m = m3.Manifold(m3.Mesh(vert_properties=v, tri_verts=np.asarray(mesh.faces, np.uint32)))
    cs = m.slice(float(x))
    return [np.asarray(p, float) for p in cs.to_polygons()]            # columns (y, z)


def section_png(out, items, x, box, size=(11.0, 8.0), title=None, marks=None):
    z0, z1, y0, y1 = box
    fig, ax = plt.subplots(figsize=size, dpi=130)
    for obj, color, label in items:
        mesh = obj if isinstance(obj, trimesh.Trimesh) else U.load_stl(obj)
        polys = _slice_polys(mesh, x)
        if not polys:
            continue
        verts, codes = [], []
        for p in polys:
            q = p[:, ::-1]                                              # (z, y)
            verts += list(q) + [q[0]]
            codes += [MPath.MOVETO] + [MPath.LINETO] * (len(q) - 1) + [MPath.CLOSEPOLY]
        ax.add_patch(PathPatch(MPath(verts, codes), facecolor=color, edgecolor='#222', lw=0.5))
        if label:
            ax.plot([], [], 's', color=color, label=label)
    for kind, args, kw in (marks or []):
        if kind == 'line':
            ax.plot(*args, **kw)
        elif kind == 'text':
            ax.text(*args, **kw)
    ax.set_xlim(z1, z0)                                                 # +Z to the left
    ax.set_ylim(y0, y1)
    ax.set_aspect('equal')
    ax.grid(True, lw=0.3, color='#bbb')
    ax.set_xlabel('z (mm, +z toward the reader, to the left)')
    ax.set_ylabel('y (mm, up)')
    ax.set_title(title or f'Section x = {x}')
    ax.legend(loc='lower right', fontsize=8)
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    return out
