"""Optional: slice the two printed parts (rev C) with the installed OrcaSlicer (Elegoo Centauri Carbon 2,
0.4 nozzle, 0.20 mm Standard, Elegoo PETG, 3 walls, 30 % infill, supports OFF) and report time,
filament and any support / floating-region warnings. Adapted from the stock case's slice_check.py.
Nothing is sent to a printer. Writes out/slice/slice-report.json (build.py folds it into REPORT.md).

    <enclosure venv python> slice_check.py
"""
import json
import math
import re
import subprocess
from pathlib import Path

import params as P

ORCA = Path(r'C:\Program Files\OrcaSlicer\orca-slicer.exe')
PROFILES = Path(r'C:\Program Files\OrcaSlicer\resources\profiles')
OUT = P.OUT / 'slice'
PRESETS = {'machine': 'Elegoo Centauri Carbon 2 0.4 nozzle',
           'process': '0.20mm Standard @Elegoo CC2 0.4 nozzle',
           'filament': 'Elegoo PETG @ECC2'}
# detect_thin_wall: the blind pilots' 0.2 skins are thinner than one line; the CC2 profile's classic wall generator drops
# them (the pilots would open onto the case top) unless thin walls are detected (Arachne prints them too).
OVERRIDES = {'process': {'wall_loops': '3', 'sparse_infill_density': '30%', 'enable_support': '0', 'detect_thin_wall': '1'}}


def index():
    idx = {}
    for kind in ('machine', 'process', 'filament'):
        for f in sorted(PROFILES.rglob(f'{kind}/**/*.json')):
            try:
                d = json.loads(f.read_text(encoding='utf-8'))
            except Exception:
                continue
            if 'name' in d:
                idx.setdefault((kind, d['name']), f)
    return idx


def flatten(kind, name, idx):
    d = json.loads(idx[(kind, name)].read_text(encoding='utf-8'))
    parent = d.get('inherits')
    base = flatten(kind, parent, idx) if parent and (kind, parent) in idx else {}
    base.update({k: v for k, v in d.items() if k != 'inherits'})
    return base


def presets():
    idx = index()
    paths = {}
    for kind, name in PRESETS.items():
        d = flatten(kind, name, idx)
        d['name'] = name
        d.pop('instantiation', None)
        d.update(OVERRIDES.get(kind, {}))
        if kind == 'machine' and 'G92 E0' not in (d.get('layer_gcode') or ''):
            d['layer_gcode'] = ((d.get('layer_gcode') or '') + '\nG92 E0').strip()
        p = OUT / f'{kind}.json'
        p.write_text(json.dumps(d, indent=1))
        paths[kind] = p
    return paths


def slice_part(stl, pre):
    dest = OUT / stl.stem
    dest.mkdir(parents=True, exist_ok=True)
    for old in dest.glob('*.gcode'):
        old.unlink()
    cmd = [str(ORCA), '--orient', '0', '--arrange', '1', '--slice', '0', '--load-settings',
           f"{pre['machine']};{pre['process']}", '--load-filaments', str(pre['filament']), '--outputdir', str(dest), str(stl)]
    r = subprocess.run(cmd, capture_output=True, timeout=900, cwd=str(dest),     # Orca drops a 00000.log in its cwd
                       creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    log = (r.stdout or b'').decode(errors='ignore') + (r.stderr or b'').decode(errors='ignore')
    g = next(dest.glob('*.gcode'), None)
    info = {'exit': r.returncode, 'gcode': g.name if g else None,
            'warnings': sorted({ln.strip()[:200] for ln in log.splitlines()
                                if re.search(r'support|floating|overhang|cantilever|warning', ln, re.I)})[:20]}
    if g:
        head = g.read_text(errors='ignore')
        for key, pat in {'time': r'estimated printing time \(normal mode\) = (.+)',
                         'grams': r'total filament used \[g\] = ([\d.]+)',
                         'layers': r'total layers count = (\d+)', 'filament_type': r'; filament_type = (\S+)',
                         'support_used': r'; enable_support = (\d)'}.items():
            m = re.search(pat, head)
            info[key] = m.group(1).strip() if m else None
    return info


def gcode_points(g, step=0.02):
    """Extrusion moves of a G-code file as dense points (layer z, x, y)."""
    import numpy as np
    out, x, y, z = [], 0.0, 0.0, 0.0
    for ln in open(g, errors='ignore'):
        if ln.startswith(';Z:'):
            z = float(ln[3:])
        elif ln.startswith(('G1 ', 'G2 ', 'G3 ')):
            d = dict((m.group(1), float(m.group(2))) for m in re.finditer(r'([XYE])(-?[\d.]+)', ln.split(';')[0]))
            nx, ny = d.get('X', x), d.get('Y', y)
            if d.get('E', 0) > 0:
                n = max(2, int(math.hypot(nx - x, ny - y) / step))
                t = np.linspace(0, 1, n)
                out.append(np.c_[np.full(n, z), x + (nx - x) * t, y + (ny - y) * t])
            x, y = nx, ny
        elif ln.startswith('G0 '):
            d = dict((m.group(1), float(m.group(2))) for m in re.finditer(r'([XY])(-?[\d.]+)', ln))
            x, y = d.get('X', x), d.get('Y', y)
    return np.vstack(out)


def pilot_skins(g, stl):
    """Is the 0.2 skin under each blind pilot actually printed? The base prints on its back face (X' = x,
    Y' = y - Y_BOT, Z' = z - ZOB); Orca's arrange moves and may turn it by k x 90 deg: the turn is the one that puts
    the boss tops where the model has them."""
    import numpy as np
    import trimesh
    G = gcode_points(g)
    b = trimesh.load(stl).bounds
    up = G[G[:, 0] > 0.5]
    zs = np.unique(G[:, 0])
    lay = G[G[:, 0] == zs[np.argmin(np.abs(zs - (P.HOLES[0][1] - P.ZOB + 0.1)))]]     # the layer through the pilot axes
    best = None
    for k in range(4):
        cx, cy = b[[0, 1, 0, 1], 0], b[[0, 0, 1, 1], 1]
        for _ in range(k):
            cx, cy = -cy, cx
        ox, oy = up[:, 1].min() - cx.min() - 0.21, up[:, 2].min() - cy.min() - 0.21

        def inv(px, py, k=k, ox=ox, oy=oy):
            xm, ym = px - ox, py - oy
            for _ in range(k):
                xm, ym = ym, -xm
            return xm, ym + P.Y_BOT
        ex, ey = inv(lay[:, 1], lay[:, 2])
        top = ey > P.BOSS_TOP - 0.6
        boss = top & np.any([np.abs(ex - hx) < P.BOSS_D / 2 + 0.1 for hx, _ in P.HOLES], axis=0)
        score = boss.sum() - 5 * (top & ~boss).sum()
        if best is None or score > best[0]:
            best = (score, k, inv)
    _, k, inv = best
    res = {'turn_deg': 90 * k, 'skin_y': [P.CASE_TOP, P.PILOT_BOT]}
    ok = True
    for hx, hz in P.HOLES:
        rows = []
        for zl in sorted(set(G[:, 0])):
            ze = zl - 0.1 + P.ZOB                 # mid-layer E-frame z
            if abs(ze - hz) > P.PILOT_D / 2 - 0.2:
                continue
            L = G[np.isclose(G[:, 0], zl)]
            ex, ey = inv(L[:, 1], L[:, 2])
            m = (np.abs(ex - hx) < 0.25) & (ey > P.CASE_TOP - 0.2) & (ey < P.PILOT_BOT + 0.15)
            rows.append(bool(m.any()))
        res[f'x {hx}'] = f'{sum(rows)}/{len(rows)} layers through the pilot have extrusion in the skin'
        ok &= bool(rows) and all(rows)
    res['printed'] = bool(ok)
    return res


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    pre = presets()
    report = {'presets': PRESETS, 'overrides': OVERRIDES}
    for name in ('base', 'lid'):
        info = slice_part(P.OUT / 'print' / f'{name}.stl', pre)
        if name == 'base' and info.get('gcode'):
            info['pilot_skins'] = pilot_skins(OUT / 'base' / info['gcode'], P.OUT / 'print' / 'base.stl')
        report[name] = info
        print(name, info, flush=True)
    (OUT / 'slice-report.json').write_text(json.dumps(report, indent=1))
