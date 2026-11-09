"""Generate the silkscreen-audio-attachment KiCad 9 project (rev A) from tools/params.py.

Run with KiCad's bundled Python (it needs pcbnew), with KiCad closed:

    "C:\\Program Files\\KiCad\\9.0\\bin\\python.exe" tools\\generate.py

Environment: KICAD9_DIR (KiCad install, default C:\\Program Files\\KiCad\\9.0), CQ_PYTHON (a python with
CadQuery for the STEP models; default: the enclosure project's .venv).

Writes, in order:
  lib/<name>.pretty       footprints (PJ-313D jack from the EasyEDA data, J6 plug headers, NPTH 4.80, stock SOT-23/-5,
                          TSSOP-14/-20, 0603 R/C copied in)
  lib/<name>.3dshapes     STEP models (jack + headers built with CadQuery, stock packages copied)
  lib/<name>.kicad_sym    symbols (R/C from KiCad stock; ICs, diode, jack, headers written here)
  <name>.kicad_sch        schematic (every pin on a labelled net)
  <name>.kicad_pro, fp-lib-table, sym-lib-table, <name>.kicad_dru
  <name>.kicad_pcb        placed, routed and poured board (built from the schematic's own netlist)
Every write is atomic (temp file + replace); refuses to run while KiCad holds a lock file.
"""
from __future__ import annotations

import glob
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import params as P  # noqa: E402
from kigeom import uid, q, f  # noqa: E402

ROOT = os.path.dirname(HERE)
NAME = P.PROJECT
LIBNAME = NAME
LIBDIR = os.path.join(ROOT, "lib")
PRETTY = os.path.join(LIBDIR, NAME + ".pretty")
SHAPES = os.path.join(LIBDIR, NAME + ".3dshapes")
SYMLIB = os.path.join(LIBDIR, NAME + ".kicad_sym")
SCH = os.path.join(ROOT, NAME + ".kicad_sch")
PCB = os.path.join(ROOT, NAME + ".kicad_pcb")
PRO = os.path.join(ROOT, NAME + ".kicad_pro")
KICAD = os.environ.get("KICAD9_DIR", r"C:\Program Files\KiCad\9.0")
KICAD_CLI = os.environ.get("KICAD_CLI", os.path.join(KICAD, "bin", "kicad-cli.exe"))
if not os.path.exists(KICAD_CLI):
    KICAD_CLI = shutil.which("kicad-cli") or KICAD_CLI
STOCK_SYM = os.path.join(KICAD, "share", "kicad", "symbols")
STOCK_FP = os.path.join(KICAD, "share", "kicad", "footprints")
STOCK_3D = os.path.join(KICAD, "share", "kicad", "3dmodels")
CQ_PYTHON = os.environ.get("CQ_PYTHON", os.path.normpath(os.path.join(
    ROOT, "..", "..", "silkscreen-enclosure-claude", ".venv", "Scripts", "python.exe")))
TEMPLATE_PRO = os.path.join(HERE, "template.kicad_pro")
MODEL = "${KIPRJMOD}/lib/" + NAME + ".3dshapes/"


def refuse_if_open(root=ROOT):
    locks = glob.glob(os.path.join(root, "~*.lck")) + glob.glob(os.path.join(root, "*.lck"))
    if locks:
        sys.exit(f"KiCad has this project open ({', '.join(os.path.basename(x) for x in locks)}). "
                 "Close it first, or your next save would overwrite the generated files.")


def write_text(path, text):
    """Atomic write with LF line ends."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    os.replace(tmp, path)


# =====================================================================================
# footprints
# =====================================================================================
STOCK_NAMES = {k: v[1] for k, v in P.FP_LIB.items()}          # key -> stock footprint name
FP_R, FP_C = STOCK_NAMES["R"], STOCK_NAMES["C"]
FP_JACK = "JACK_3.5mm_SHOUHAN_PJ-313D"
FP_HDR = {"J1": "J6_PLUG_1x4_P1-P4", "J2": "J6_PLUG_1x1_P9", "J3": "J6_PLUG_1x1_P12"}
FP_NPTH = {4.80: "NPTH_4.80mm"}
STEP_JACK = "JACK_3.5mm_SHOUHAN_PJ-313D.step"
STEP_HDR = {"J1": "J6_PLUG_1x4_HC-PZ254-11.5L.step", "J2": "J6_PLUG_1x1_HC-PZ254-11.5L.step",
            "J3": "J6_PLUG_1x1_HC-PZ254-11.5L.step"}
STOCK_STEP = {"SOT-23-5": ("Package_TO_SOT_SMD", "SOT-23-5"), "SOT-23": ("Package_TO_SOT_SMD", "SOT-23"),
              "TSSOP-20": ("Package_SO", "TSSOP-20_4.4x6.5mm_P0.65mm"), "TSSOP-14": ("Package_SO", "TSSOP-14_4.4x5mm_P0.65mm"),
              "R": ("Resistor_SMD", "R_0603_1608Metric"), "C": ("Capacitor_SMD", "C_0603_1608Metric")}
J = P.JACK


def fp_header(name, descr, tags, attr, ref_layer="F.SilkS", ref_hide=True):
    hide = " (hide yes)" if ref_hide else ""
    return [f'(footprint {q(name)}', '\t(version 20241229)', f'\t(generator {q(NAME)})',
            '\t(generator_version "9.0")', '\t(layer "F.Cu")', f'\t(descr {q(descr)})', f'\t(tags {q(tags)})',
            f'\t(property "Reference" "REF**" (at 0 -2 0) (layer {q(ref_layer)}){hide} (uuid {q(uid(name, "ref"))}) '
            '(effects (font (size 1 1) (thickness 0.15))))',
            f'\t(property "Value" {q(name)} (at 0 2 0) (layer "F.Fab") (hide yes) (uuid {q(uid(name, "val"))}) '
            '(effects (font (size 0.5 0.5) (thickness 0.08))))',
            f'\t(property "Datasheet" "" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid {q(uid(name, "ds"))}) '
            '(effects (font (size 1 1) (thickness 0.15))))',
            f'\t(property "Description" {q(descr)} (at 0 0 0) (layer "F.Fab") (hide yes) (uuid {q(uid(name, "de"))}) '
            '(effects (font (size 1 1) (thickness 0.15))))',
            f'\t(attr {attr})']


def g_line(a, b, layer, w, name, i):
    return (f'\t(fp_line (start {f(a[0])} {f(a[1])}) (end {f(b[0])} {f(b[1])}) '
            f'(stroke (width {f(w)}) (type solid)) (layer {q(layer)}) (uuid {q(uid(name, layer, i))}))')


def g_rect(a, b, layer, w, name, i, fill=False):
    return (f'\t(fp_rect (start {f(a[0])} {f(a[1])}) (end {f(b[0])} {f(b[1])}) '
            f'(stroke (width {f(w)}) (type solid)) (fill {"yes" if fill else "no"}) (layer {q(layer)}) '
            f'(uuid {q(uid(name, layer, "r", i))}))')


def g_circle(c, r, layer, w, name, i):
    return (f'\t(fp_circle (center {f(c[0])} {f(c[1])}) (end {f(c[0] + r)} {f(c[1])}) '
            f'(stroke (width {f(w)}) (type solid)) (fill no) (layer {q(layer)}) (uuid {q(uid(name, layer, "c", i))}))')


def g_text(txt, at, layer, h, name, i, w=None):
    w = w if w is not None else max(0.08, h * 0.15)
    return (f'\t(fp_text user {q(txt)} (at {f(at[0])} {f(at[1])} 0) (layer {q(layer)}) '
            f'(uuid {q(uid(name, "t", i))}) (effects (font (size {f(h)} {f(h)}) (thickness {f(w)}))))')


def model(fname):
    return f'\t(model {q(MODEL + fname)} (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))'


def write_jack_fp():
    """Shou Han PJ-313D, EasyEDA AUDIO-SMD_PJ-313D-2 (C668608), same frame as EasyEDA (nose toward -y, y down).

    6 pads 2.50 x 1.25 at x +-3.60, y -3.355 / -0.145 / +3.356 (pad numbers 1, 2, 3 on BOTH rows: the left and the
    right tab of one contact), two NPTH pegs dia 1.30 at (0, -2.655) and (0, +3.358).  Placed at rotation 90 the nose
    points to -X.  1 = sleeve (GND), 2 = ring (HP_R), 3 = tip (HP_L): see PROGRESS.md for the evidence.
    """
    n = FP_JACK
    out = fp_header(n, "Shou Han PJ-313D 3.5 mm stereo jack, SMD, 14 x 6 x 5 mm (LCSC C668608, EasyEDA AUDIO-SMD_PJ-313D-2); "
                    "pad 1 = sleeve, 2 = ring, 3 = tip (both tabs of a contact share the number); nose toward -y",
                    "audio jack 3.5mm SMD", "smd")
    for num, y in J["pad_y"].items():
        for side in (-1, 1):
            out.append(f'\t(pad {q(num)} smd rect (at {f(side * J["pad_x"])} {f(y)}) (size {f(J["pad_w"])} {f(J["pad_h"])}) '
                       f'(layers "F.Cu" "F.Paste" "F.Mask") (uuid {q(uid(n, "pad", num, side))}))')
    for k, (px, py) in enumerate(J["pegs"]):
        out.append(f'\t(pad "" np_thru_hole circle (at {f(px)} {f(py)}) (size {f(J["peg_d"])} {f(J["peg_d"])}) '
                   f'(drill {f(J["peg_d"])}) (layers "*.Cu" "*.Mask") (uuid {q(uid(n, "peg", k))}))')
    by0, by1 = J["body_y"]
    ny0, ny1 = J["nose_y"]
    bx, nx_ = J["body_x"], J["nose_d"] / 2
    # fab: body + nose outline
    out.append(g_rect((-bx, by0), (bx, by1), "F.Fab", 0.1, n, 0))
    out.append(g_rect((-nx_, ny0), (nx_, by0), "F.Fab", 0.1, n, 1))
    out.append(g_text("${REFERENCE}", (0, 1.0), "F.Fab", 0.8, n, 2))
    # silk only where it stays on the board (nose side hangs 2.84 past the board edge) and clear of the pads
    w = P.RULES["silk_line_w"]
    out.append(g_line((-bx, by1), (bx, by1), "F.SilkS", w, n, 3))
    out.append(g_line((-bx, by1), (-bx, 4.85), "F.SilkS", w, n, 4))
    out.append(g_line((bx, by1), (bx, 4.85), "F.SilkS", w, n, 5))
    out.append(g_rect((-bx - 0.1, ny0 - 0.1), (bx + 0.1, by1 + 0.1), "F.CrtYd", 0.05, n, 6))
    out.append(model(STEP_JACK))
    out.append(')')
    return n, "\n".join(out) + "\n"


def hdr_pad_offsets(ref):
    """Footprint offsets of a header's pads from its origin (body centre).  The footprint is placed on B.Cu (flipped
    left-right about its origin), so the authored x offset is the NEGATIVE of the wanted E offset."""
    cx, cz = P.header_centre(ref)
    return {nm: (round(X - cx, 4), round(Z - cz, 4)) for nm, (X, Z) in P.HEADERS[ref]["pads"].items()}


def write_hdr_fp(ref):
    n = FP_HDR[ref]
    H = P.HEADERS[ref]
    bx0, bx1, bz0, bz1 = P.header_body(ref)
    hx, hz = (bx1 - bx0) / 2, (bz1 - bz0) / 2
    pins = ", ".join(f"{nm} {H['nets'][nm]}" for nm in H["pads"])
    out = fp_header(n, f"1x{H['positions']} 2.54 mm straight male header ({H['mpn']}) plugging into main-board J6, mounted "
                    f"from the underside: place it on B.Cu (the pad x offsets here are pre-mirrored); pads named by the "
                    f"mating J6 pin: {pins}", "pin header 2.54 J6 plug", "through_hole")
    for nm, (dx, dy) in hdr_pad_offsets(ref).items():
        shape = "rect" if nm == "1" else "circle"
        out.append(f'\t(pad {q(nm)} thru_hole {shape} (at {f(dx)} {f(dy)}) (size {f(P.HDR["pad"])} {f(P.HDR["pad"])}) '
                   f'(drill {f(P.HDR["drill"])}) (layers "*.Cu" "*.Mask") (remove_unused_layers no) '
                   f'(uuid {q(uid(n, "pad", nm))}))')
    out.append(g_rect((-hx, -hz), (hx, hz), "F.Fab", 0.1, n, 0))
    out.append(g_text("${REFERENCE}", (0, hz - 0.35), "F.Fab", 0.4, n, 1))
    out.append(g_rect((-hx, -hz), (hx, hz), "F.CrtYd", 0.05, n, 2))
    out.append(model(STEP_HDR[ref]))
    out.append(')')
    return n, "\n".join(out) + "\n"


def write_npth_fp(d):
    n = FP_NPTH[d]
    margin = P.COLUMN_CRTYD
    out = fp_header(n, f"Non-plated hole {d:.2f} mm (courtyard = hole + {margin:.2f})", "NPTH hole mechanical",
                    "board_only exclude_from_pos_files exclude_from_bom")
    out.append(f'\t(pad "" np_thru_hole circle (at 0 0) (size {f(d)} {f(d)}) (drill {f(d)}) (layers "*.Cu" "*.Mask") '
               f'(uuid {q(uid(n, "pad"))}))')
    out.append(g_circle((0, 0), d / 2, "F.Fab", 0.05, n, 0))
    out.append(g_circle((0, 0), d / 2 + margin, "F.CrtYd", 0.05, n, 1))
    out.append(')')
    return n, "\n".join(out) + "\n"


def copy_stock_fp(lib, name, model_file, descr_note):
    src = open(os.path.join(STOCK_FP, lib + ".pretty", name + ".kicad_mod"), encoding="utf-8").read()
    src = re.sub(r'\(model "[^"]*"', f'(model {q(MODEL + model_file)}', src, count=1)
    w = P.RULES["silk_line_w"]

    def widen(m):
        blk = m.group(0)
        if '(layer "F.SilkS")' not in blk and '(layer "B.SilkS")' not in blk:
            return blk
        return re.sub(r'\(width ([0-9.]+)\)', lambda n: f'(width {f(max(float(n.group(1)), w))})', blk)
    src = re.sub(r'\(fp_(?:line|poly|arc|circle|rect)\b.*?\(layer "[^"]+"\)', widen, src, flags=re.S)
    src = re.sub(r'\(descr "([^"]*)"\)', lambda m: f'(descr {q(m.group(1) + " " + descr_note)})', src, count=1)
    src = re.sub(r'(\(property "Reference" "REF\*\*"\s*\(at [^)]*\)\s*\(layer "F.SilkS"\))',
                 r'\1\n\t\t(hide yes)', src, count=1)
    return name, src


def write_footprints():
    os.makedirs(PRETTY, exist_ok=True)
    os.makedirs(SHAPES, exist_ok=True)
    items = [write_jack_fp(), write_npth_fp(4.80)] + [write_hdr_fp(r) for r in ("J1", "J2", "J3")]
    for key, (lib, name) in P.FP_LIB.items():
        items.append(copy_stock_fp(lib, name, name + ".step", "(KiCad stock, copied into the project)"))
    keep = set()
    for name, text in items:
        write_text(os.path.join(PRETTY, name + ".kicad_mod"), text)
        keep.add(name + ".kicad_mod")
    for fn in os.listdir(PRETTY):
        if fn not in keep:
            os.remove(os.path.join(PRETTY, fn))
    models = {STEP_JACK, "models.stamp"} | set(STEP_HDR.values())
    for key, (lib, name) in STOCK_STEP.items():
        src = os.path.join(STOCK_3D, lib + ".3dshapes", name + ".step")
        if not os.path.exists(src):
            sys.exit("stock 3D model missing: " + src)
        shutil.copyfile(src, os.path.join(SHAPES, name + ".step"))
        models.add(name + ".step")
    for fn in os.listdir(SHAPES):
        if fn not in models:
            os.remove(os.path.join(SHAPES, fn))
    import hashlib
    src = open(os.path.join(HERE, "make_step_models.py"), encoding="utf-8").read()
    stamp = hashlib.sha256((src + repr(P.JACK) + repr(P.HDR) + repr(P.HEADERS) + P.DATE).encode()).hexdigest()
    stamp_file = os.path.join(SHAPES, "models.stamp")
    have = all(os.path.exists(os.path.join(SHAPES, fn)) for fn in [STEP_JACK] + list(STEP_HDR.values()))
    if have and os.path.exists(stamp_file) and open(stamp_file).read().strip() == stamp:
        return
    if not os.path.exists(CQ_PYTHON):
        sys.exit("CadQuery python not found (set CQ_PYTHON): " + CQ_PYTHON)
    r = subprocess.run([CQ_PYTHON, os.path.join(HERE, "make_step_models.py"), "models", SHAPES],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("STEP model build failed:\n" + r.stdout + r.stderr)
    write_text(stamp_file, stamp + "\n")


# =====================================================================================
# symbols
# =====================================================================================
def extract_symbol(lib_file, name):
    text = open(os.path.join(STOCK_SYM, lib_file), encoding="utf-8").read()
    m = re.search(r'^\t\(symbol "' + re.escape(name) + r'"\n', text, re.M)
    if not m:
        raise KeyError(name)
    i = m.start()
    depth = 0
    for j in range(i, len(text)):
        c = text[j]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return text[i:j + 1]
    raise ValueError("unbalanced")


def set_prop(block, prop, value):
    new, n = re.subn(r'(\(property "' + re.escape(prop) + r'" )"[^"]*"', lambda m: m.group(1) + q(value), block, count=1)
    if n != 1:
        raise KeyError(prop)
    return new


def _prop(k, v, at=(0, 0), hide=True, justify=None):
    j = f"\n\t\t\t\t(justify {justify})" if justify else ""
    h = "\n\t\t\t\t(hide yes)" if hide else ""
    return (f'\t\t(property {q(k)} {q(v)}\n\t\t\t(at {f(at[0])} {f(at[1])} 0)\n\t\t\t(effects\n\t\t\t\t(font\n'
            f'\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t){j}{h}\n\t\t\t)\n\t\t)')


def _pin(num, name, at, ang, length):
    return (f'\t\t\t(pin passive line\n\t\t\t\t(at {f(at[0])} {f(at[1])} {ang})\n\t\t\t\t(length {f(length)})\n'
            f'\t\t\t\t(name {q(name)}\n\t\t\t\t\t(effects\n\t\t\t\t\t\t(font\n\t\t\t\t\t\t\t(size 1.27 1.27)\n'
            f'\t\t\t\t\t\t)\n\t\t\t\t\t)\n\t\t\t\t)\n\t\t\t\t(number {q(num)}\n\t\t\t\t\t(effects\n\t\t\t\t\t\t(font\n'
            f'\t\t\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t\t\t)\n\t\t\t\t\t)\n\t\t\t\t)\n\t\t\t)')


BOX_W = 6.35          # half width of an IC symbol body
PIN_X = 8.89          # pin end x (body edge 6.35 + length 2.54)


def box_symbol(name, prefix, left, right, props):
    """Rectangle symbol; pin i of a side at y = -2.54 i (left pins at x -8.89, right pins at +8.89), all passive."""
    rows = max(len(left), len(right))
    y1 = -2.54 * (rows - 1) - 1.27
    rect = (f'\t\t\t(rectangle\n\t\t\t\t(start {f(-BOX_W)} 1.27)\n\t\t\t\t(end {f(BOX_W)} {f(y1)})\n\t\t\t\t(stroke\n'
            '\t\t\t\t\t(width 0.254)\n\t\t\t\t\t(type default)\n\t\t\t\t)\n\t\t\t\t(fill\n\t\t\t\t\t(type background)\n'
            '\t\t\t\t)\n\t\t\t)')
    pins = [_pin(num, nm, (-PIN_X, -2.54 * i), 0, 2.54) for i, (num, nm) in enumerate(left)]
    pins += [_pin(num, nm, (PIN_X, -2.54 * i), 180, 2.54) for i, (num, nm) in enumerate(right)]
    pr = [_prop("Reference", prefix, (-BOX_W, 2.54), False), _prop("Value", name, (-BOX_W, y1 - 1.27), False)]
    pr += [_prop(k, v) for k, v in props.items()]
    return (f'\t(symbol {q(name)}\n\t\t(pin_names\n\t\t\t(offset 0.508)\n\t\t)\n\t\t(exclude_from_sim no)\n'
            f'\t\t(in_bom yes)\n\t\t(on_board yes)\n' + "\n".join(pr) + f'\n\t\t(symbol "{name}_0_1"\n' + rect +
            f'\n\t\t)\n\t\t(symbol "{name}_1_1"\n' + "\n".join(pins) + '\n\t\t)\n\t\t(embedded_fonts no)\n\t)')


def symbol_sides(ref):
    """(symbol name, prefix, left pins, right pins, fp name) of an IC / diode / jack / header."""
    if ref in P.ICS:
        c = P.ICS[ref]
        return c["sym"], "U" if ref.startswith("U") else "D", c["left"], c["right"], STOCK_NAMES[c["fp"]]
    if ref == "J4":
        return "PJ-313D", "J", [("1", "SLEEVE_GND"), ("2", "RING_R"), ("3", "TIP_L")], [], FP_JACK
    H = P.HEADERS[ref]
    return ("J6_PLUG_1x%d_P%s" % (H["positions"], "-".join(H["pads"])), "J",
            [(nm, f"J6-{nm} {H['nets'][nm]}") for nm in H["pads"]], [], FP_HDR[ref])


def build_symbols():
    syms = {}
    r = extract_symbol("Device.kicad_sym", "R")
    syms["R"] = set_prop(r, "Footprint", f"{LIBNAME}:{FP_R}")
    c = extract_symbol("Device.kicad_sym", "C")
    syms["C"] = set_prop(c, "Footprint", f"{LIBNAME}:{FP_C}")
    for ref in list(P.ICS) + ["J4", "J1", "J2", "J3"]:
        name, prefix, left, right, fpn = symbol_sides(ref)
        if name in syms:
            continue
        pf = {"Footprint": f"{LIBNAME}:{fpn}", "Datasheet": "", "Description": name}
        syms[name] = box_symbol(name, prefix, left, right, pf)
    return syms


def write_symbol_lib(syms):
    write_text(SYMLIB, f'(kicad_symbol_lib\n\t(version 20241209)\n\t(generator {q(NAME)})\n\t(generator_version "9.0")\n'
               + "".join(s + "\n" for s in syms.values()) + ")\n")


# =====================================================================================
# schematic
# =====================================================================================
ROOT_UUID = uid("root-sheet")
ASM_SMT = "JLC SMT (top side)"
ASM_HAND = "hand-solder (builder)"


class Sch:
    def __init__(self, syms):
        self.syms = syms
        self.items = []
        self.symbols = []
        self.n = 0

    def _u(self, *k):
        self.n += 1
        return uid("sch", self.n, *k)

    def wire(self, a, b):
        self.items.append(f'\t(wire (pts (xy {f(a[0])} {f(a[1])}) (xy {f(b[0])} {f(b[1])})) '
                          f'(stroke (width 0) (type default)) (uuid {q(self._u("w"))}))')

    def label(self, name, at, angle=0):
        just = "right bottom" if angle == 180 else "left bottom"
        self.items.append(f'\t(label {q(name)} (at {f(at[0])} {f(at[1])} {angle}) (fields_autoplaced yes) '
                          f'(effects (font (size 1.27 1.27)) (justify {just})) (uuid {q(self._u("l"))}))')

    def noconn(self, at):
        self.items.append(f'\t(no_connect (at {f(at[0])} {f(at[1])}) (uuid {q(self._u("nc"))}))')

    def text(self, s, at, size=1.27):
        self.items.append(f'\t(text {q(s)} (exclude_from_sim no) (at {f(at[0])} {f(at[1])} 0) '
                          f'(effects (font (size {f(size)} {f(size)})) (justify left top)) (uuid {q(self._u("t"))}))')

    def symbol(self, lib, ref, at, rot=0, fields=None, pins=(), ref_at=None, val_at=None, hide_value=False, fangle=0):
        u = uid("sym", ref)
        fields = dict(fields or {})
        props = [("Reference", ref, ref_at or (at[0], at[1] - 3.81), False),
                 ("Value", fields.pop("Value"), val_at or (at[0], at[1] + 3.81), hide_value)]
        for k, v in fields.items():
            props.append((k, v, at, True))
        lines = [f'\t(symbol (lib_id {q(LIBNAME + ":" + lib)}) (at {f(at[0])} {f(at[1])} {rot}) (unit 1)',
                 f'\t\t(exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid {q(u)})']
        for k, v, pos, hidden in props:
            ang = fangle if k in ("Reference", "Value") else 0
            lines.append(f'\t\t(property {q(k)} {q(v)} (at {f(pos[0])} {f(pos[1])} {ang}) '
                         f'(effects (font (size 1.27 1.27))' + (' (hide yes)' if hidden else '') + '))')
        for p in pins:
            lines.append(f'\t\t(pin {q(p)} (uuid {q(uid("pin", ref, p))}))')
        lines.append(f'\t\t(instances (project {q(NAME)} (path {q("/" + ROOT_UUID)} (reference {q(ref)}) (unit 1))))')
        lines.append('\t)')
        self.symbols.append("\n".join(lines))
        return u

    def write(self, path):
        head = ['(kicad_sch', '\t(version 20250114)', '\t(generator "eeschema")', '\t(generator_version "9.0")',
                f'\t(uuid {q(ROOT_UUID)})', '\t(paper "A3")',
                '\t(title_block', f'\t\t(title {q(P.TITLE)})', f'\t\t(date {q(P.DATE)})',
                f'\t\t(rev {q(P.REVISION)})', f'\t\t(company {q(P.COMPANY)})',
                '\t\t(comment 1 "PCM5102A I2S DAC + TPA6138A2 headphone driver + 3.5 mm jack; plugs into main-board J6")',
                '\t\t(comment 2 "Licensed under CERN-OHL-S-2.0")', '\t\t(comment 3 "(c) 2026 idc LLC")',
                '\t\t(comment 4 "Generated by pcb/tools/generate.py - do not edit")', '\t)', '\t(lib_symbols']
        for name, s in self.syms.items():
            s = s.replace(f'(symbol "{name}"', f'(symbol "{LIBNAME}:{name}"', 1)
            head.append("\t" + s.replace("\n", "\n\t"))
        head.append('\t)')
        body = head + self.items + self.symbols + ['\t(sheet_instances (path "/" (page "1")))',
                                                   '\t(embedded_fonts no)', ')']
        write_text(path, "\n".join(body) + "\n")


def part_fields(ref):
    """Schematic / BOM fields of a part (DigiKey-primary Value = MPN, separate LCSC field)."""
    if ref in P.PASSIVES:
        cls, _ = P.PASSIVES[ref]
        d = (P.RES if ref.startswith("R") else P.CAP)[cls]
        kind = "R" if ref.startswith("R") else "C"
        return {"Value": d["mpn"], "Footprint": f"{LIBNAME}:{FP_R if kind == 'R' else FP_C}",
                "Datasheet": f"https://www.lcsc.com/product-detail/{d['lcsc']}.html",
                "Description": d["desc"], "Manufacturer": d["manufacturer"], "MPN": d["mpn"],
                "DigiKey": f"search DigiKey for {d['mpn']} (part number not verified)", "LCSC": d["lcsc"],
                "Assembly": ASM_SMT}
    if ref in P.ICS:
        c = P.ICS[ref]
        return {"Value": c["value"], "Footprint": f"{LIBNAME}:{STOCK_NAMES[c['fp']]}", "Datasheet": c["datasheet"],
                "Description": c["desc"], "Manufacturer": c["manufacturer"], "MPN": c["mpn"], "DigiKey": c["digikey"],
                "LCSC": c["lcsc"], "Assembly": ASM_SMT}
    if ref == "J4":
        return {"Value": J["mpn"], "Footprint": f"{LIBNAME}:{FP_JACK}", "Datasheet": J["datasheet"],
                "Description": "3.5 mm stereo headphone jack, SMD, 14 x 6 x 5 mm; pad 1 sleeve (GND), 2 ring (HP_R), "
                               "3 tip (HP_L); both tabs of a contact share the pad number",
                "Manufacturer": J["manufacturer"], "MPN": J["mpn"], "DigiKey": J["digikey"], "LCSC": J["lcsc"],
                "Assembly": ASM_SMT}
    h = P.HEADERS[ref]
    d = P.HDR
    return {"Value": h["mpn"], "Footprint": f"{LIBNAME}:{FP_HDR[ref]}", "Datasheet": h["datasheet"],
            "Description": (f"1x{h['positions']} 2.54 mm straight male pin header, body {d['body_h']:.1f}, mating post "
                            f"{d['post']:.1f}, tail {d['tail']:.1f}, {d['post_sq']:.2f} sq; mounted from the underside, "
                            "soldered by the builder on the top side; pins = J6 " + "/".join(h["pads"])),
            "Manufacturer": h["manufacturer"], "MPN": h["mpn"], "DigiKey": h["digikey"], "LCSC": h["lcsc"],
            "Assembly": ASM_HAND}


def all_refs():
    return list(P.ICS) + ["J4", "J1", "J2", "J3"] + sorted(P.PASSIVES, key=lambda r: (r[0], int(r[1:])))


def pin_net(ref, pin):
    if ref in P.ICS:
        return P.ICS[ref]["pins"][pin]
    if ref in P.PASSIVES:
        return P.PASSIVES[ref][1][pin]
    if ref == "J4":
        return J["nets"][pin]
    return P.HEADERS[ref]["nets"][pin]


def build_schematic(syms):
    s = Sch(syms)

    def box(ref, at, ref_at=None):
        name, prefix, left, right, fpn = symbol_sides(ref)
        x, y = at
        rows = max(len(left), len(right))
        s.symbol(name, ref, at, 0, part_fields(ref), pins=[p for p, _ in left + right],
                 ref_at=(x - BOX_W, y - 3.81), val_at=(x - BOX_W, y + 2.54 * rows + 1.27))
        for i, (num, nm) in enumerate(left):
            gx, gy = x - PIN_X, y + 2.54 * i
            net = pin_net(ref, num)
            if net is None:
                s.noconn((gx, gy))
            else:
                s.wire((gx - 2.54, gy), (gx, gy))
                s.label(net, (gx - 2.54, gy), 180)
        for i, (num, nm) in enumerate(right):
            gx, gy = x + PIN_X, y + 2.54 * i
            net = pin_net(ref, num)
            if net is None:
                s.noconn((gx, gy))
            else:
                s.wire((gx, gy), (gx + 2.54, gy))
                s.label(net, (gx + 2.54, gy), 0)

    # ---------------- connectors, ICs, diode
    box("J1", (50.8, 40.64))
    box("J2", (50.8, 66.04))
    box("J3", (50.8, 78.74))
    box("J4", (50.8, 101.6))
    box("U1", (127.0, 40.64))
    box("D1", (127.0, 76.2))
    box("U3", (200.66, 53.34))
    box("U2", (299.72, 66.04))
    # ---------------- passives on a grid below the ICs
    refs = sorted(P.PASSIVES, key=lambda r: (r[0], int(r[1:])))
    x0, y0, dx, dy, cols = 40.64, 160.02, 50.8, 17.78, 7
    for k, ref in enumerate(refs):
        x, y = x0 + (k % cols) * dx, y0 + (k // cols) * dy
        kind = "R" if ref.startswith("R") else "C"
        s.symbol(kind, ref, (x, y), 90, part_fields(ref), pins=["1", "2"], ref_at=(x, y - 3.81), val_at=(x, y + 2.54),
                 fangle=0)
        for pin, sign in (("1", -1), ("2", 1)):
            gx = x + sign * 3.81
            net = P.PASSIVES[ref][1][pin]
            s.wire((gx, y), (gx + sign * 2.54, y))
            s.label(net, (gx + sign * 2.54, y), 180 if sign < 0 else 0)
    notes = [
        "HOW IT WORKS (rev A)",
        "I2S (BCLK J6-2 / IO46, DOUT J6-3 / IO45, WS J6-9 / IO3) -> PCM5102A (BCK PLL, no MCLK) -> TPA6138A2 (gain -1, ground-centred)",
        "-> 3.5 mm jack (tip = left = HP_L, ring = right = HP_R, sleeve = GND). 100k pull-downs on the three lines, no pull-ups.",
        "Power: P+ (raw cell, J6-12) -> TPS7A2033 3.3 V LDO, switched by EN_DET = charge pump on WS (R1 C3 D1 C4 R2): idle ~0.1 uA.",
        "The amplifier is held in mute by R3/C5 for ~100 ms after the LDO turns on. J6_3V3 and I2C are not used.",
        "Headers (pads named by the J6 pin they mate): J1 1x4 = pins 1-4 (GND, BCLK, DOUT, GND); J2 = pin 9 (WS); J3 = pin 12 (VBAT).",
        "No pad and no hole at J6 5, 6, 7, 8, 10, 11. Jack pads: 1 sleeve, 2 ring, 3 tip (each on both tabs).",
    ]
    s.text("\n".join(notes), (20.32, 220.0), 1.27)
    s.write(SCH)
    return s


# =====================================================================================
# project files
# =====================================================================================
def write_project_files():
    write_text(os.path.join(ROOT, "fp-lib-table"),
               f'(fp_lib_table\n\t(version 7)\n\t(lib (name {q(LIBNAME)})(type "KiCad")'
               f'(uri "${{KIPRJMOD}}/lib/{NAME}.pretty")(options "")(descr "Audio attachment footprints (generated)"))\n)\n')
    write_text(os.path.join(ROOT, "sym-lib-table"),
               f'(sym_lib_table\n\t(version 7)\n\t(lib (name {q(LIBNAME)})(type "KiCad")'
               f'(uri "${{KIPRJMOD}}/lib/{NAME}.kicad_sym")(options "")(descr "Audio attachment symbols (generated)"))\n)\n')
    pro = json.load(open(TEMPLATE_PRO, encoding="utf-8"))
    ds = pro["board"]["design_settings"]
    ds["drc_exclusions"] = []
    R = P.RULES
    ds["rules"].update({
        "min_clearance": R["clearance"], "min_copper_edge_clearance": R["edge_clearance"],
        "min_track_width": R["track_min"], "min_via_diameter": R["via_pad_min"],
        "min_through_hole_diameter": R["via_drill_min"], "min_via_annular_width": R["min_annular"],
        "min_hole_clearance": R["hole_clearance"], "min_hole_to_hole": R["hole_to_hole"],
        "min_text_height": R["silk_text_h"], "min_text_thickness": R["silk_line_w"], "min_silk_clearance": 0.0,
        "solder_mask_to_copper_clearance": 0.0,
    })
    ds["track_widths"] = [0.0, P.ROUTE["track"]]
    ds["via_dimensions"] = [{"diameter": 0.0, "drill": 0.0}, {"diameter": R["via_pad"], "drill": R["via_drill"]}]
    ds["defaults"]["board_outline_line_width"] = 0.05
    ds["defaults"]["silk_line_width"] = R["silk_line_w"]
    ds["defaults"]["silk_text_size_h"] = 1.0
    ds["defaults"]["silk_text_size_v"] = 1.0
    ds["defaults"]["silk_text_thickness"] = R["silk_line_w"]
    sev = ds.setdefault("rule_severities", {})
    for k, v in list(sev.items()):          # nothing ignored
        if v == "ignore":
            sev[k] = "warning"
    sev.update({"courtyards_overlap": "error", "copper_edge_clearance": "error", "solder_mask_bridge": "error",
                "missing_courtyard": "error", "hole_clearance": "error", "hole_to_hole": "error",
                "silk_over_copper": "warning", "npth_inside_courtyard": "error", "pth_inside_courtyard": "error"})
    erc = pro.setdefault("erc", {})
    erc["erc_exclusions"] = []
    for k, v in list(erc.get("rule_severities", {}).items()):
        if v == "ignore":
            erc["rule_severities"][k] = "warning"
    ns = pro["net_settings"]
    base = ns["classes"][0]
    base.update({"clearance": R["clearance"], "track_width": P.ROUTE["track"], "via_diameter": R["via_pad"],
                 "via_drill": R["via_drill"]})
    ns["classes"] = [base]
    ns["netclass_assignments"] = None
    ns["netclass_patterns"] = []
    pro["meta"]["filename"] = NAME + ".kicad_pro"
    pro["sheets"] = [[ROOT_UUID, "Root"]]
    pro["text_variables"] = {}
    pro["boards"] = []
    pro["libraries"] = {"pinned_footprint_libs": [], "pinned_symbol_libs": []}
    pro["pcbnew"] = {"last_paths": {"gencad": "", "idf": "", "netlist": "", "plot": "production/gerbers/",
                                    "pos_files": "production/", "specctra_dsn": "", "step": "production/3d/",
                                    "svg": "", "vrml": ""}, "page_layout_descr_file": ""}
    write_text(PRO, json.dumps(pro, indent=2) + "\n")
    dru = """(version 1)

# Copper (tracks, pads, vias, pours) keeps 0.5 mm off every mechanical NPTH: the two 4.80 lid screw columns and the
# two 1.30 jack pegs.
(rule "npth_mech_0p5"
    (constraint hole_clearance (min 0.5mm))
    (condition "B.Pad_Type == 'NPTH, mechanical'"))
"""
    write_text(os.path.join(ROOT, NAME + ".kicad_dru"), dru)


# =====================================================================================
# netlist from the schematic (so the PCB matches it exactly)
# =====================================================================================
def schematic_netlist():
    out = os.path.join(ROOT, "build", NAME + ".net")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    r = subprocess.run([KICAD_CLI, "sch", "export", "netlist", "--format", "kicadsexpr", "-o", out, SCH],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("netlist export failed:\n" + r.stdout + r.stderr)
    text = open(out, encoding="utf-8").read()
    padnet = {}
    for blk in re.split(r'\n\s*\(net ', text)[1:]:
        nm = re.search(r'\(name "((?:[^"\\]|\\.)*)"\)', blk).group(1)
        for ref, pad in re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', blk):
            padnet[(ref, pad)] = nm
    comps = {}
    comp_text = text.split("(libparts", 1)[0]
    for blk in re.split(r'\n\s*\(comp ', comp_text)[1:]:
        ref = re.search(r'\(ref "([^"]+)"\)', blk).group(1)
        val = re.search(r'\(value "((?:[^"\\]|\\.)*)"\)', blk).group(1)
        fpn = re.search(r'\(footprint "([^"]+)"\)', blk)
        fields = dict(re.findall(r'\(field \(name "([^"]+)"\) "((?:[^"\\]|\\.)*)"\)', blk))
        dnp = bool(re.search(r'\(property \(name "dnp"\)', blk))
        comps[ref] = {"value": val, "footprint": fpn.group(1) if fpn else "", "fields": fields, "dnp": dnp}
    want = sorted(all_refs())
    if sorted(comps) != want or any(c["dnp"] for c in comps.values()):
        sys.exit(f"netlist parts {sorted(comps)} (want {want}, none DNP)")
    return padnet, comps


def main():
    refuse_if_open()
    write_footprints()
    syms = build_symbols()
    write_symbol_lib(syms)
    build_schematic(syms)
    write_project_files()
    padnet, comps = schematic_netlist()
    import build_pcb   # noqa: E402  (needs pcbnew)
    build_pcb.build(padnet, comps)
    write_project_files()          # again: nothing pcbnew saved may override the rules/severities
    prl = os.path.join(ROOT, NAME + ".kicad_prl")
    if os.path.exists(prl):
        os.remove(prl)
    print("generated", PCB)


if __name__ == "__main__":
    main()
