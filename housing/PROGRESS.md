# Housing progress (audio attachment)

Contract: ../design/DESIGN-SPEC.md sec 0 (6), 1, 2. Python: the silkscreen-enclosure-claude venv. Run `src/build.py` (a few minutes).

## 2026-11-09 milestone 1: code ported
- Started from the rev C light-bar housing (silkscreen-light-attachment/housing/src). Deleted hood_light.py / optics_report.py and the
  light/view/hood checks.
- params.py: HOLES left boss 10.00 -> 12.00; STOCK_OUT -> ../silkscreen-enclosures/enclosures/case-426/out/standard (read-only,
  rebuilt 2026-11-07; the base does not depend on it); audio constants block at the end.
- parts.py: base built with BASE_TOP_REF 120.5 (the rev C lid top) so its outline is identical to the printed rev C base; new
  `build_lid`; PCBA proxy (spec numbers) with the jack.
- build.py: new checks base_identity (diff vs the rev C base.stl is confined to the two boss sites), plug (opening coaxial + plug
  envelope), roof clearance in fit; light/view dropped.

## Decisions
- Lid top = jack top 122.60 + 0.3 + 1.2 roof = 124.10; front z 8.50 = flush with the base's front tongue (the spec said about 7.4-8.0).
- Roof end edges only R0.6 (the dia 6.5 opening top is at y 123.35).
- Opening = dia 6.5 circle + slot to the lid's lower edge (print: no overhang); 0.3 end pad so a dia 9 plug body never touches the lid.
- Screw columns r 3.2 (the spec keep-out), counterbore dia 4.4, floor y 118.90 (3 mm screw ends 0.1 above the pilot skin).

## 2026-11-09 milestone 2: all checks PASS (proxy PCBA)
- build.py exit 0 (about 2.5 min; run it in the FOREGROUND, background runs get starved). out/checks.json, out/REPORT.md, out/print/{base,lid}.stl/.step,
  plate.3mf, out/E/*.stl, out/render/*.png (9 views), out/slice/ (OrcaSlicer CLI: base 20m21s 3.25 g, lid 12m38s 3.84 g, no warnings, pilot skins printed).
- Fixes on the way: jack body starts at x -2.84, past the cavity's -2.8 limit -> local jack pocket in the lid cavity; cavity top-back edge
  filleted R0.6 (the R2 outer round left 1.13 there); screw column r 3.0 (jack float 0.19 needs >= 0.2 gap); thin-wall sampling s 0.35 with
  a 0.05 tolerance (s 0.25 needs > 3 GB).
- Used PROXY geometry: pcb/build/geometry.json did not exist at the end (the PCB agent was still routing). To re-run on the real board:
  `src/build.py` picks it up when it has keys pcb, holes, parts, header, jack (jack.body_box, jack.nose x/dia/axis_y/axis_z); it also globs
  pcb/production/3d/*_pcba_E.stl for the body-by-body check.

## Final run against the real board (2026-11-09, coordinator)
- The board grew to z 7.0 at the front; the lid cavity follows it (front inner face 7.3, wall 1.2 to the z 8.5 face).
- The R2.2 top-front round thinned that wall to 1.06 at the corner: the cavity's top-front edge is now rounded
  concentric with it (R1.0, parts.py build_lid), so the wall and roof stay 1.2 round the corner.
- build.py against pcb/build/geometry.json + the E-frame PCBA STL: all 11 checks PASS (base_identity, seated, fit,
  seam, pins, plug, pcba_stl, screws, keepout, sweep, print). Undeclared minimum wall: base 1.168, lid 1.174.
- slice_check.py (OrcaSlicer CLI): base 20m21s 3.25 g, lid 12m36s 3.39 g, no supports, no warnings; pilot skins print.
