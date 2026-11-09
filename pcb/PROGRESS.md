# Audio PCBA (rev A) - PROGRESS

Contract: ../design/DESIGN-SPEC.md. Netlist: ../research/audio-chain.md sec 1.1/1.2. Nothing committed (per brief).
Generator derived from silkscreen-light-attachment/pcb (params, generate, build_pcb, make_outputs, check_handedness,
export_geometry, make_step_models, report_design, kigeom) plus new tools/router.py (numpy grid router) and
tools/cpl_offsets.py.

## Rebuild (close KiCad first; scripts refuse to write while a *.lck exists)
    "C:\Program Files\KiCad\9.0\bin\python.exe" tools\generate.py [--reroute]   # footprints, symbols, schematic, board
    "C:\Program Files\KiCad\9.0\bin\python.exe" tools\make_outputs.py           # gates, then production/ docs/ build/geometry.json
generate.py reuses build/routes.json when build/pads.json is byte-identical (placement unchanged); --reroute forces the router.

## Frame (proved, gated in tools/check_handedness.py)
F.Cu = top (+Y), x_K = X + 100, y_K = Z + 100. Seen from +Y (eye above, looking down -Y): right = +X, toward viewer = +Y,
so up = (+Y) x (+X) = -Z, down = +Z = K's +y: unmirrored. kicad-cli STEP (x_s, y_s, z_s) = (x_K, -y_K, z) -> E
(X, Y, Z) = (x_s - 100, 116.60 + z_s - z_B, -y_s - 100), a -90 deg rotation about X, det +1. THT headers are footprints on B.Cu
(Flip about their origin; footprint pad x offsets are pre-mirrored). E-frame STEP asserts: lowest vertex Y 108.10 (post tips),
header bodies Y 114.10..116.60 (below 116.60), tails 119.60 (above 117.60) at each pad, jack top 122.60.

## Jack pin mapping (top risk) - evidence
Two independent views of Shou Han PJ-313D (LCSC C668608):
1. Datasheet (atta.szlcsc.com/.../C668608_AB2020...pdf, page 6, saved docs/sources/pj313d_atta.pdf): contact schematic shows
   terminal 1 joined to the plug-sleeve bar, terminals 2 and 3 as spring contacts (3 the deepest); top view numbers contacts
   (1)(2)(3) from the plug-entry nose end (nose = the 2.5 mm Ø5 stub at the start of the body). Parts table: contact piece 1
   (x2, terminals "1-2") vs contact piece 2 (terminal "3"). Bore centre 2.5 above the pad plane (body 5 high, Ø3.6 bore, end view).
2. EasyEDA symbol (docs/sources/ee_C668608.json): pin 1 line joins the plug rectangle's sleeve end, pin 2 a spring at the
   ring position, pin 3 a spring at the far (tip) end. EasyEDA footprint: pad 1 (both tabs) nearest the nose at footprint y
   -3.355, pad 2 -0.145, pad 3 +3.356; nose toward -y; each number appears on both rows (x +-3.60).
=> 1 = sleeve = GND, 2 = ring = HP_R, 3 = tip = HP_L (sleeve contact is at the mouth, tip deepest). Not bench-verified: first
article should be checked with a meter/plug.

## Parts found / stock (JLC parts API 2026-11-09, docs/sources/jlc_*.json)
U1 TPS7A2033PDBVR C2862740 122506; U2 PCM5102APWR C107671 1284; U3 TPA6138A2PWR C183097 3332; D1 BAT54S C8592 221495;
J4 PJ-313D C668608 23114. Headers: Hong Cheng HC-PZ254-11.5L-1x4PZ C27985189 (stock 44988, extended, insulation 2.5, mating
6, end 3), 1x1PZ C27985186 (stock 5114). Pin section 0.64 sq is assumed (not listed).

## Deviations from the spec
- 4 NPTH, not 2: the PJ-313D footprint carries two Ø1.30 positioning pegs (EasyEDA HOLE records) at E (-0.345, 0) and (5.668, 0).
- Rules: clearance 0.15, track 0.25, via 0.6/0.3 (JLC standard); copper keeps 0.5 off every mechanical NPTH (.kicad_dru).
- DigiKey part numbers for the passives are not verified (field says "search DigiKey for <MPN>"); IC numbers are from the research.
- Pours cover the underside over J6 positions 5/6/11 (plastic base floor intervenes); pads/holes keep >= 1.0 off them.
- Router is a custom grid router; see below for the state.

## State at hand-off (2026-11-09) - INCOMPLETE: routing not 100 %
- generate.py runs end to end (footprints, symbols, schematic ERC-clean netlist, placed + routed + poured board, parity 0).
- Router leaves ~8 connections open (see build/router output / DRC unconnected): I2S_WS (J2.9, R1.1, U2.15), AMP_INL (R10.2),
  DAC_OUTL (U2.6) and 3-4 GND stubs (U3.1, U2.3, R6.2...). make_outputs.py therefore stops at the DRC gate, so production/,
  docs/ and build/geometry.json are NOT written. Fix = hand-route those nets in KiCad or loosen the placement (bottom row
  z 4.7, gap column x 23-25 are the congested areas) and run generate.py --reroute again.
- check_handedness.py: frame proof, header pad positions (after the pad-offset fix: B.Cu footprints keep UNmirrored pad offsets
  because SetOrientation after Flip resets the mirror), jack pads/nets, forbidden J6 spots, NPTH, placement, webs, silk are gated.
- Not yet run: E-frame STEP check (header bodies < 116.60 / tails > 117.60), outputs, header model mirror vs pad order.

## Update 2 (2026-11-09, second session) - still not 0 unconnected
Router now: escape stubs on IC signal pads, one GND via per SMD GND pad within 1.0 mm, 16 seeded attempts in parallel (seed 6 first),
stitching vias, stub trimming, pour-pocket connectivity check (counts GND vias stranded in a detached pour pocket as failures).
Track 0.20, clearance 0.15, via 0.6/0.3 (one 0.55/0.25 via inside U2.3 because the pad is boxed in by two signal pins).
History: seed 6 of an earlier router version routed 100 % (DRC 0 violations) but left one detached GND pour pocket right of U2
(E x 32.5..36.4, z -3.6..0.4) = 1 "unconnected" zone pair; the latest run (pocket check on) best = 1 failure (U2.18 DAC_LDOO).
Helper scripts: tools/zone_islands.py (list detached pour components), tools/fix_islands.py, tools/tie_islands.py.
Next step: more seeds (extend `seeds` in router.main) or move C13/C14/C12 so the U2 right-hand GND vias are not enclosed.
Not produced: production/, docs/ renders, build/geometry.json, E-frame STEP check (make_outputs stops at the DRC gate).

## Update 3 (2026-11-09, coordinator finish pass) - COMPLETE, all gates pass
- Board outline z1 6.00 -> 7.00 (1 mm more room toward the front; the lid cavity follows the outline, the base's front
  tongue already supports it). PART_REGION z max 5.5 -> 6.5; bottom row z 4.7 -> 5.6, top row z -4.65 -> -4.95.
- Router seeds 16 -> 40 (stops at the first 0-failure attempt): seed 5 routed 100 % in the first batch, 135 tracks,
  126 vias.
- make_step_models.py: header-body top tolerance 0.01 -> 0.10 (kicad-cli seats B-side models 0.085 off the nominal
  underside of its 0.91 slab; post tips still checked to 0.01).
- make_outputs.py: ERC 0, DRC 0, unconnected 0, parity 0, exclusions 0/0; handedness/placement PASS; field sync 0
  mismatches; E-frame Y range 108.10..122.68. production/, docs/, build/geometry.json written.

## Update 4 (2026-11-09) - R7 10k for presence detect; BOM library types
- R7 (I2S_WS pull-down) 100k -> 10k (C25804, joins the existing 10k BOM line). With IO3's internal ~45k pull-up the
  pin sits at ~0.6 V when the cap is fitted (reads LOW) and HIGH without it. Firmware check in docs/FIRMWARE-NOTES.md.
- generate.py reused build/routes.json (pads unchanged). Diff vs the previous build: only R7's six part fields in the
  .kicad_pcb/.kicad_sch and its value in geometry.json; Gerbers, drill files and jlc_cpl.csv identical (drill map
  PDFs differ only in their dates).
- make_outputs.py: bom.csv "JLC type" now reads from params.JLC_BASIC (it said "JLC Extended" for every part). Basic:
  all 37 R/C. Extended: U1, U2, U3, D1, J4 (+ the hand-soldered headers).
- Gates: ERC 0, DRC 0/0/0, handedness PASS, field sync 0 mismatches, E-frame Y 108.1..122.68.
