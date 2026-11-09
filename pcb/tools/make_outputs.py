"""Gates first, then fabrication, assembly, mechanical and documentation outputs.

    "C:\\Program Files\\KiCad\\9.0\\bin\\python.exe" tools\\make_outputs.py

1. Gates (nothing is written to production/ or docs/ unless ALL pass):
     ERC (--severity-all, no exclusions) = 0; DRC with schematic parity (--severity-all) = 0 violations,
     0 unconnected, 0 parity; the handedness/placement gate (tools/check_handedness.py: J1 position, keep-outs,
     NPTH copper clearance, NPTH-to-edge webs >= 0.50, silk minimums); the field-sync gate (every footprint carries
     the schematic symbol's Datasheet / Description / custom fields and DNP flag); the string-voltage sanity.
   Reports always go to build/reports/ so a failure can be read.
2. Everything is staged in build/stage/ and only moved into production/ and docs/ when every step (including
   the enclosure-frame STEP tip assertion) has succeeded:
     production/gerbers/ + production/<name>_rev-<REV>_gerbers.zip (fab layers + drill only)
     production/bom.csv (all parts, Assembly column), jlc_bom.csv + jlc_cpl.csv (the 12 SMT parts only,
     F side, rotations corrected per footprint)
     production/3d/<name>.step (board + models), <name>_pcba_E.step/.stl (enclosure frame)
     docs/<name>_schematic.pdf, docs/<name>_layout.pdf, docs/images/render_{top,bottom}.png,
     docs/design_summary.md, docs/reports/ (ERC/DRC/gate/STEP-tip reports)
     build/geometry.json (enclosure frame)
Environment: KICAD_CLI / KICAD9_DIR, CQ_PYTHON (CadQuery python for the enclosure-frame STEP).
"""
from __future__ import annotations

import csv
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import params as P  # noqa: E402
import generate as G  # noqa: E402

ROOT = os.path.dirname(HERE)
NAME = P.PROJECT
CLI = G.KICAD_CLI
PCB = G.PCB
SCH = G.SCH
BUILD = os.path.join(ROOT, "build")
REP = os.path.join(BUILD, "reports")
STAGE = os.path.join(BUILD, "stage")
S_PROD = os.path.join(STAGE, "production")
S_DOCS = os.path.join(STAGE, "docs")

# JLC placement rotation offsets, derived by tools/cpl_offsets.py from the EasyEDA footprints of the ordered LCSC parts
# (easyeda.com/api/products/<C#>/components?version=6.4.19.5, saved in docs/sources/ee_*.json): rotation that maps the
# EasyEDA pad set onto the KiCad one (JLC rotation = KiCad rotation + offset):
#   SOT-23-5 (C2862740) +180, TSSOP-20 (C107671) +270, TSSOP-14 (C183097) +270, SOT-23 (C8592) +180 (pad-1 corner mismatch
#   0.4 mm only because the EasyEDA SOT-23 land is wider), 0603 R (C25803) / C (C19702) +0 (non-polar), jack (C668608) +0
#   (the KiCad footprint IS the EasyEDA geometry).
# J1-J3 are THT headers on the underside: not in the CPL and not in jlc_bom.csv (hand-soldered); bom.csv lists them.
CPL_OFFSET = {G.STOCK_NAMES["SOT-23-5"]: 180.0, G.STOCK_NAMES["TSSOP-20"]: 270.0, G.STOCK_NAMES["TSSOP-14"]: 270.0,
              G.STOCK_NAMES["SOT-23"]: 180.0, G.FP_R: 0.0, G.FP_C: 0.0, G.FP_JACK: 0.0}
N_SMT = len(P.ICS) + 1 + len(P.PASSIVES)             # 4 ICs/diode + jack + 37 passives
N_JLC = N_SMT


def run(args, ok=(0,)):
    r = subprocess.run([CLI] + args, capture_output=True, text=True)
    if r.returncode not in ok:
        print(r.stdout, r.stderr)
        raise SystemExit(f"kicad-cli {' '.join(args[:3])} failed ({r.returncode})")
    return r.stdout


# ------------------------------------------------------------------ gates
def gates():
    if os.path.isdir(REP):
        shutil.rmtree(REP)
    os.makedirs(REP)
    run(["sch", "erc", "--severity-all", "-o", os.path.join(REP, "erc.rpt"), SCH], ok=(0, 5))
    run(["sch", "erc", "--severity-all", "--format", "json", "-o", os.path.join(REP, "erc.json"), SCH], ok=(0, 5))
    run(["pcb", "drc", "--schematic-parity", "--severity-all", "-o", os.path.join(REP, "drc.rpt"), PCB], ok=(0, 5))
    run(["pcb", "drc", "--schematic-parity", "--severity-all", "--format", "json",
         "-o", os.path.join(REP, "drc.json"), PCB], ok=(0, 5))
    erc = json.load(open(os.path.join(REP, "erc.json"), encoding="utf-8"))
    drc = json.load(open(os.path.join(REP, "drc.json"), encoding="utf-8"))
    pro = json.load(open(G.PRO, encoding="utf-8"))
    res = {
        "erc": sum(len(s.get("violations", [])) for s in erc.get("sheets", [])),
        "drc": len(drc.get("violations", [])),
        "unconnected": len(drc.get("unconnected_items", [])),
        "parity": len(drc.get("schematic_parity", [])),
        "erc_exclusions": len(pro.get("erc", {}).get("erc_exclusions", [])),
        "drc_exclusions": len(pro["board"]["design_settings"].get("drc_exclusions", [])),
        "ignored_drc_checks": sorted(k for k, v in pro["board"]["design_settings"]["rule_severities"].items() if v == "ignore"),
        "ignored_erc_checks": sorted(k for k, v in pro.get("erc", {}).get("rule_severities", {}).items() if v == "ignore"),
    }
    print(f"ERC {res['erc']}  DRC {res['drc']}  unconnected {res['unconnected']}  parity {res['parity']}  "
          f"exclusions {res['erc_exclusions']}/{res['drc_exclusions']}  ignored checks "
          f"{len(res['ignored_drc_checks'])}/{len(res['ignored_erc_checks'])}")
    import check_handedness   # noqa: E402
    res["handedness_gate"] = "PASS" if check_handedness.main() == 0 else "FAIL"
    shutil.copyfile(os.path.join(BUILD, "gate_handedness.json"), os.path.join(REP, "gate_handedness.json"))
    res["field_sync"] = field_sync_gate()
    json.dump(res, open(os.path.join(REP, "gates.json"), "w", encoding="utf-8"), indent=2)
    bad = (res["erc"] + res["drc"] + res["unconnected"] + res["parity"] + res["erc_exclusions"] + res["drc_exclusions"]
           + len(res["ignored_drc_checks"]) + len(res["ignored_erc_checks"]))
    if bad or res["handedness_gate"] != "PASS" or res["field_sync"]["mismatches"]:
        raise SystemExit(f"GATE FAILED ({res}); nothing written to production/ or docs/. See build/reports/.")
    print("gates: PASS")
    return res


def field_sync_gate():
    """Every footprint must carry the schematic symbol's fields (review-electrical F1) and DNP flag."""
    import html
    import pcbnew
    comps = {c["ref"]: c for c in read_netlist()}
    b = pcbnew.LoadBoard(PCB)
    bad, checked = [], 0
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        if ref not in comps:
            continue                                  # board-only NPTH footprints
        c = comps[ref]
        want = {k: html.unescape(v) for k, v in c["fields"].items() if k not in ("Footprint",)}
        want.setdefault("Datasheet", html.unescape(c.get("datasheet", "")))
        want.setdefault("Description", html.unescape(c.get("description", "")))
        have = {f.GetName(): f.GetText() for f in fp.GetFields()}
        for k, v in sorted(want.items()):
            checked += 1
            if have.get(k) != v:
                bad.append(f"{ref}.{k}: PCB {have.get(k)!r} != SCH {v!r}")
        if fp.GetValue() != html.unescape(c["value"]):
            bad.append(f"{ref}.Value: PCB {fp.GetValue()!r} != SCH {c['value']!r}")
        if bool(fp.IsDNP()) != c["dnp"]:
            bad.append(f"{ref}.DNP: PCB {fp.IsDNP()} != SCH {c['dnp']}")
    missing = sorted(set(comps) - {fp.GetReference() for fp in b.GetFootprints()})
    bad += [f"{r}: no footprint" for r in missing]
    print(f"field sync: {len(comps)} parts, {checked} fields compared, {len(bad)} mismatches")
    for x in bad:
        print("  MISMATCH", x)
    return {"parts": len(comps), "fields_compared": checked, "mismatches": bad,
            "dnp": sorted(r for r, c in comps.items() if c["dnp"])}


# ------------------------------------------------------------------ fab
def gerbers():
    gd = os.path.join(S_PROD, "gerbers")
    os.makedirs(gd)
    layers = "F.Cu,B.Cu,F.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts"
    run(["pcb", "export", "gerbers", "--layers", layers, "--subtract-soldermask", "--no-protel-ext", "--precision", "6",
         "-o", gd + os.sep, PCB])
    run(["pcb", "export", "drill", "--format", "excellon", "--excellon-units", "mm", "--excellon-separate-th",
         "--generate-map", "--map-format", "pdf", "-o", gd + os.sep, PCB])
    zpath = os.path.join(S_PROD, f"{NAME}_rev-{P.REVISION}_gerbers.zip")
    names = []
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for fn in sorted(os.listdir(gd)):
            if fn.endswith((".gbr", ".drl")):          # fab layers + drill only (no job file, no drill-map PDF)
                z.write(os.path.join(gd, fn), fn)
                names.append(fn)
    print("gerbers:", len(names), "files in", os.path.basename(zpath))
    return names


def read_netlist():
    net = os.path.join(BUILD, NAME + ".xml")
    run(["sch", "export", "netlist", "--format", "kicadxml", "-o", net, SCH])
    text = open(net, encoding="utf-8").read()
    comps = []
    for m in re.finditer(r'<comp ref="([^"]+)">(.*?)</comp>', text, re.S):
        ref, body = m.group(1), m.group(2)
        val = re.search(r"<value>(.*?)</value>", body).group(1)
        fp = re.search(r"<footprint>(.*?)</footprint>", body)
        fields = dict(re.findall(r'<field name="([^"]+)">(.*?)</field>', body))
        exclude = bool(re.search(r'<property name="exclude_from_bom"', body))
        dnp = bool(re.search(r'<property name="dnp"', body))
        ds = re.search(r"<datasheet>(.*?)</datasheet>", body, re.S)
        de = re.search(r"<description>(.*?)</description>", body, re.S)
        comps.append({"ref": ref, "value": val, "footprint": fp.group(1) if fp else "", "fields": fields,
                      "exclude": exclude, "dnp": dnp, "datasheet": ds.group(1) if ds else "",
                      "description": de.group(1) if de else ""})
    return comps


def refkey(r):
    m = re.match(r"([A-Z]+)(\d+)", r)
    return (m.group(1), int(m.group(2)))


def boms():
    import html
    parts = [c for c in read_netlist() if not c["exclude"]]
    groups = {}
    for c in parts:
        key = (c["value"], c["footprint"], c["fields"].get("LCSC", ""), c["fields"].get("Assembly", "") == G.ASM_HAND)
        groups.setdefault(key, []).append(c)
    order = sorted(groups.items(), key=lambda kv: refkey(min((c["ref"] for c in kv[1]), key=refkey)))
    un = html.unescape
    with open(os.path.join(S_PROD, "bom.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["Qty", "Refs", "Value", "Manufacturer", "MPN", "DigiKey", "LCSC", "JLC type", "Footprint", "Assembly",
                    "Description"])
        for (val, fp, lcsc, dnp), cs in order:
            f0 = cs[0]["fields"]
            refs = ",".join(sorted((c["ref"] for c in cs), key=refkey))
            asm = "THT: JLC hand-solders it, or untick it at JLC and solder it yourself" if dnp else G.ASM_SMT
            jt = P.HDR_JLC_TYPE.split(" (")[0] if dnp else ("JLC Basic" if lcsc in P.JLC_BASIC else "JLC Extended")
            w.writerow([len(cs), refs, un(val), un(f0.get("Manufacturer", "")), un(f0.get("MPN", "")),
                        un(f0.get("DigiKey", "")), lcsc, jt, fp.split(":")[-1], asm, un(f0.get("Description", ""))])
    with open(os.path.join(S_PROD, "jlc_bom.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["Comment", "Designator", "Footprint", "JLCPCB Part #"])
        n_jlc = 0
        for (val, fp, lcsc, dnp), cs in order:
            if dnp:
                continue
            n_jlc += len(cs)
            cct = cs[0]["fields"].get("CCT", "")
            refs = ",".join(sorted((c["ref"] for c in cs), key=refkey))
            w.writerow([un(val) + (f" {cct}" if cct else ""), refs, fp.split(":")[-1], lcsc])
    dnp_refs = sorted(c["ref"] for c in parts if c["fields"].get("Assembly", "") == G.ASM_HAND)
    if dnp_refs != sorted(P.HEADERS) or n_jlc != N_JLC or any(c["dnp"] for c in parts):
        raise SystemExit(f"JLC BOM check failed: THT headers {dnp_refs} (want {sorted(P.HEADERS)}), {n_jlc} JLC parts "
                         f"(want {N_JLC} SMD parts, headers excluded)")
    print("bom:", len(parts), "parts in", len(groups), "lines;", n_jlc, "in jlc_bom.csv (THT headers:", dnp_refs, ")")
    return parts, order


def cpl():
    raw = os.path.join(BUILD, "pos.csv")
    run(["pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "front", "--exclude-dnp", "-o", raw, PCB])
    rows = list(csv.DictReader(open(raw, encoding="utf-8")))
    fpmap = {}
    import pcbnew
    b = pcbnew.LoadBoard(PCB)
    for fp in b.GetFootprints():
        fpmap[fp.GetReference()] = fp.GetFPIDAsString().split(":")[-1]
    out = []
    with open(os.path.join(S_PROD, "jlc_cpl.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for r in sorted(rows, key=lambda r: refkey(r["Ref"])):
            fpn = fpmap[r["Ref"]]
            if fpn not in CPL_OFFSET:
                raise SystemExit(f"no CPL rotation offset for footprint {fpn} ({r['Ref']})")
            rot = (float(r["Rot"]) + CPL_OFFSET[fpn]) % 360
            w.writerow([r["Ref"], f'{float(r["PosX"]):.4f}mm', f'{float(r["PosY"]):.4f}mm', "Top", f"{rot:.1f}"])
            out.append((r["Ref"], fpn, float(r["Rot"]), rot))
    refs = [r["Ref"] for r in rows]
    if len(rows) != N_JLC or any(h in refs for h in P.HEADERS) or any(fpmap[r] not in CPL_OFFSET for r in refs):
        raise SystemExit(f"JLC CPL check failed: {len(rows)} rows (want the {N_SMT} top-side SMD parts, no headers)")
    print("cpl:", len(rows), "top-side SMD placements (headers excluded)")
    return out


# ------------------------------------------------------------------ mechanical
def step_files():
    d3 = os.path.join(S_PROD, "3d")
    os.makedirs(d3)
    full = os.path.join(d3, NAME + ".step")
    run(["pcb", "export", "step", "--force", "--subst-models", "--user-origin", "0x0mm", "-o", full, PCB])
    slab = os.path.join(BUILD, NAME + "_board_only.step")
    run(["pcb", "export", "step", "--force", "--board-only", "--user-origin", "0x0mm", "-o", slab, PCB])
    ef_step = os.path.join(d3, NAME + "_pcba_E.step")
    ef_stl = os.path.join(d3, NAME + "_pcba_E.stl")
    rep = os.path.join(REP, "eframe_step_check.json")
    r = subprocess.run([G.CQ_PYTHON, os.path.join(HERE, "make_step_models.py"), "eframe", full, slab, ef_step, ef_stl, rep],
                       capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode != 0:
        print(r.stderr[-3000:])
        raise SystemExit("enclosure-frame STEP check FAILED (header tips); nothing written. See " + rep)
    return json.load(open(rep, encoding="utf-8"))


# ------------------------------------------------------------------ docs
def docs():
    os.makedirs(os.path.join(S_DOCS, "images"))
    run(["sch", "export", "pdf", "-o", os.path.join(S_DOCS, NAME + "_schematic.pdf"), SCH])
    tmpd = os.path.join(BUILD, "layout_pdf")
    if os.path.isdir(tmpd):
        shutil.rmtree(tmpd)
    run(["pcb", "export", "pdf", "--mode-multipage", "--include-border-title",
         "--layers", "F.Cu,B.Cu,F.Silkscreen,F.Mask,F.Fab,User.3",
         "--cl", "Edge.Cuts", "-o", tmpd + os.sep, PCB])
    pdfs = glob.glob(os.path.join(tmpd, "*.pdf"))
    shutil.move(pdfs[0], os.path.join(S_DOCS, NAME + "_layout.pdf"))
    common = ["--quality", "high", "--background", "opaque", "--width", "2600", "--height", "1100", "--zoom", "1.0"]
    run(["pcb", "render", "--side", "top"] + common + ["-o", os.path.join(S_DOCS, "images", "render_top.png"), PCB])
    run(["pcb", "render", "--side", "bottom"] + common + ["-o", os.path.join(S_DOCS, "images", "render_bottom.png"), PCB])
    print("docs: schematic/layout PDF, renders")


def publish():
    """Move the staged outputs into place (only reached when everything succeeded)."""
    prod = os.path.join(ROOT, "production")
    if os.path.isdir(prod):
        shutil.rmtree(prod)
    shutil.move(S_PROD, prod)
    dd = os.path.join(ROOT, "docs")
    os.makedirs(dd, exist_ok=True)
    for item in os.listdir(S_DOCS):
        dst = os.path.join(dd, item)
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        elif os.path.exists(dst):
            os.remove(dst)
        shutil.move(os.path.join(S_DOCS, item), dst)
    rd = os.path.join(dd, "reports")
    if os.path.isdir(rd):
        shutil.rmtree(rd)
    shutil.copytree(REP, rd)


def main():
    G.refuse_if_open()
    res = gates()
    if os.path.isdir(STAGE):
        shutil.rmtree(STAGE)
    os.makedirs(S_PROD)
    os.makedirs(S_DOCS)
    gerbers()
    boms()
    cpl()
    tips = step_files()
    docs()
    import export_geometry   # noqa: E402
    export_geometry.main(os.path.join(STAGE, "geometry.json"))
    publish()
    shutil.move(os.path.join(STAGE, "geometry.json"), os.path.join(BUILD, "geometry.json"))
    import report_design   # noqa: E402
    report_design.main()
    shutil.rmtree(STAGE, ignore_errors=True)
    print(f"ALL GATES PASS: ERC {res['erc']}, DRC {res['drc']}/{res['unconnected']}/{res['parity']}, "
          f"handedness {res['handedness_gate']}; E-frame Y range {tips['vertex_y_range']}")


if __name__ == "__main__":
    main()
