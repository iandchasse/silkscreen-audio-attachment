# Enclosure research (silkscreen-enclosure-claude rev K) for the top light attachment

Main-board parts named here: J6 is the expansion header; SW10 the power button and SW7 the left-up page key; H3/H4 the
two bottom mounting holes; J2-J5 the display, frontlight, touch and battery connectors.

`E` = `silkscreen-light-attachment/enclosures/silkscreen-enclosure-claude` (our copy; `diff -rq` of src vs the
original is clean). `LS` = `silkscreen-light-strip/enclosures/silkscreen-enclosure-claude`. (py) = printed by
importing `E/src/hw.py`/`params.py` with the venv python. (sect) = measured on the freshly built `E/out/tub.stl`,
`lid.stl` by sectioning at x = 20 (plain top), 40.2 (top screw), 50 (J6). INFERRED = my derivation.

## Key numbers
| Quantity | Value | Source |
|---|---|---|
| Frame | X = KiCad X - 44.24; Y = 148.25 - KiCad Y (+Y = top edge, J6 end); Z = 0 PCB rear, +Z toward screen | params.py:1-2, README:69-77 |
| Envelope | X -4.09..64.09 (68.18), Y -8.4..115.6 (124.0), Z -6.7..6.0 (12.7) | (py) params.py:58-72,28,32; README:43. (Comments "-3.41/63.41" at params.py:59-60 are stale) |
| Top wall | inside TOP_IN 113.4, outside Y1 115.6, TOP_WALL 2.2 | params.py:67-69 |
| Front skin | SKIN 1.02: LIP (lip underside = glass/touch front) 4.98 -> Z_FRONT 6.0 | params.py:24-28 |
| Parting line | SEAM -3.75; 0.4 V chamfer on each half | params.py:29,76 |
| Rounds | plan CORNER_R 5.0; FRONT_EDGE_R 1.8; BACK_EDGE_R 2.0 | params.py:73-75 |
| Flat top face (y 115.6) | x 0.91..59.09 (58.18), z -4.7..4.2 (8.9), V groove z -4.15..-3.35 | INFERRED from rounds; (sect) y 115.35 at z -3.6/-3.9 |
| Screen pocket | X -1.41..61.41, Y 5.035..110.865; steps in (X only) above z 4.05 | (py) params.py:35-39,77; tub.py:35-41 |
| Panel FT01C | X -1.185..61.185, Y 5.285..110.615 (glass top), T 1.98 +-0.2; LGP z 4.1..4.5 top edge y 110.465; touch z 4.68..4.98 top y 110.185 | (py) hw.py:24-28, panel.z_levels(), panel.LGP/TOUCH |
| Active area | x 2.16..57.84, y 15.1..107.9 | (py) hw.py:29-30 |
| Window | at lip: x 1.56..58.44, y 14.5..108.5; 0.6x45deg bevel -> at face y 109.1 | tub.py:18-26, params.py:81-82; (sect) |
| Top bezel on the front face | flat z 6.0 from y 109.1 to 113.8, then R1.8 round to y 115.6 at z 4.2. README: "top bezel 6.9 mm" | (sect); README:55 |
| Lip over glass (top) | skin covers glass y 108.5..110.615 (2.1 mm); lip overlaps touch film 1.7 (top) .. 4.0 (bottom) | README:364-370 |
| Top ledge (tub) | solid y 110.865..113.4, z 2.0..6.0 behind the glass's top edge | (sect) x=20 & 50; tub.py:29-49 |
| J6 body | X 42.882..58.622, Y 100.31..113.15 (socket face), Z -5.165..-0.085 plastic (leads to +3.065) | (py) hw.bounds('J6'); README:145 |
| J6 pins | pin 1 at (44.502, 100.280), 2x6 at 2.54, columns x 44.50..57.20, B.Cu, PPPC062LJBN-RC | (py) hw.footprints()['J6'] |
| J6 socket openings | 12 at x 44.40/46.94/49.48/52.02/54.56/57.10 (model sits 0.10 -X of the footprint pads), rows z -1.36 and -3.90; 1.1-1.14 sq entry at y 113.0, 0.6 sq at y 112.0 | measured on hw.solids()['J6'] (board STEP cache), sections at y 113.0/112.0 |
| J6 face to outer top face | 2.45 (113.15 -> 115.6) | params.py:67-69 |
| J6 opening in the top face | x 42.582..58.922 (16.34), z -5.415..0.215 (5.63); lintel above it z 0.215..6.0 | tub.py:171-175, lid.py:102-104; (sect) x=50 |
| Top screw | M2x10 pan at (40.2, 112.8), from the back. Tub boss D3.4 z -3.75..4.99, pilot D1.7 to z 5.45; lid boss D5.0, clear D2.4, counterbore D4.2 x 1.8 (y 110.7..114.9 on the back face) | params.py:283-285, tub.py:113-115, lid.py:45-48, README:44 |
| Top tongue/groove | tub tongue x 1.3..37.0, y 113.4..114.33, z -3.75..-5.15; lid rim y 114.4..115.6 | params.py:296-301, joint.py:48; (sect) x=20 |
| Battery | x 1.11..38.31, y 82.0..113.1, z -3.18..2.0 | params.py:323 |
| Side keys near top | right SW10 pad y 90..97 (proud 1.5), flexure root y 106.0; left SW7 root y 91.0 | (py) body.side_tabs(); params.py:207 |
| Build + checks | build.py 345 s rc 0 (7 designed contacts, all paths clear); mechanics.py 153 s rc 0 (max strain 1.37 %) | this run, see last section |

## Parts and coordinate frame
- **tub** (`tub.py`, printed FACE DOWN on the front face): everything above SEAM: the front skin/bezel, the
  window, the screen pocket, the solid top ledge, the top wall down to the seam, the upper J6 opening, the top-screw
  boss, and the top tongue below the seam. **The tub forms both the front bezel and the top wall.**
- **lid** (`lid.py`, back face down): everything below SEAM incl. the five side keys, the lid's top rim (RIM 1.2),
  the lower J6 opening, the top screw's clearance + counterbore, battery springs (y 91, 104).
- **midplate** (1 mm, z 2.0..3.0, top edge POCKET_Y1 - EDGE_CLR); **key_SW9/8/3/2** bottom rockers; refs
  (display, battery) and `pcba-dummy` are not case parts. 3 x M2x10 screws (H3, H4, top).
- Both halves are `outer_body()` (body.py:8-13) split at SEAM and finally clipped by `.intersect(body)`
  (tub.py:240, lid.py:116): **nothing may stand outside the envelope unless outer_body changes.**

## Code references (E/src)
- Envelope, rounds: body.py:8-13 (`rbox` X0..X1,Y0..Y1,Z_BACK..Z_FRONT, fillet FRONT/BACK_EDGE_R); seam V
  body.py:25-39, applied tub.py:233-234, lid.py:111-112. Split: tub.py:221, lid.py:33-34.
- Top wall: params.py:67-69; joint wall table joint.py:44-49 (`'top': face=TOP_IN, t=TOP_WALL`); tongue runs
  params.py:296-301; latches only on the sides (params.py:310).
- J6 opening: `tub.header_opening()` tub.py:171-175 (cut at tub.py:232); lid cut lid.py:102-104. Both run to
  `P.Y1 + 1`, so they follow a taller wall automatically.
- Top screw/boss: params.py:283-285; tub.py:113-115 (in `screw_bosses()`, tub.py:103-116); lid.py:45-48.
- Battery near the top: params.py:323-326; midplate.py:87-184 (`battery_bay`); lid.py:79-91; later-move crop box
  y 79..112 in build.py:157.
- Screen window: tub.py:18-26 (`window()`); params.py:81-82. Pocket and ledge: tub.py:29-49 (`cavity()`).
- Front skin: params.py:26-28 (SKIN, Z_FRONT); key caps reference Z_FRONT (keys.py:58-59).
- Top-edge rounds: body.py:11-12 only (no separate chamfers at the top; window bevel tub.py:23-25).
- Build/checks: build.py:17-24 (PARTS), 30-55 (build_all/export), 58-85 (interference), 88-118 (insertion), 130-185
  (later_moves), 188-220 (mesh_interference), 223-242 (main). Envelope dims for the showcase: showcase.py:232.
  Back logo is centred at (Y0+Y1)/2 (params.py:102-103), so it moves if Y1 grows.

## Light-strip integration diff (recipe)
`diff -ru --strip-trailing-cr` of the original src vs `LS/src` (the README is unchanged; `LS/00000.log` is only an
OrcaSlicer CLI log of `out/print/tub.stl`):
1. **params.py (+86 lines, appended section "light-strip variant")**: `STRIP_GEOMETRY` (JSON exported from the
   KiCad strip project into `hardware/reference/light-strip/strip-geometry.json`), `PLAIN` (plain GDEY0426T82
   stack), `PLAIN_FRONT` 3.926, `STRIP_STACK`, `STRIP_FLEX_TOP` 4.311, `STRIP_LED_TOP` 5.111, `WIN_X0/X1/Y0/Y1`
   (1.56/58.44/14.5/108.5), `STRIP_CEIL` (x POCKET_X0..WIN_X0, y 12.5..109.6, **z 5.30 = raised skin underside,
   0.70 skin left**), `STRIP_HOLD` (hold-down pads), `PANEL_STOPS`, `STRIP_GAP_X0` 7.7, `STRIP_TAIL`,
   `STRIP_DRAPE`, `STRIP_J3_MID`, `STRIP_DIODE`.
2. **tub.py**: `strip_cuts()` (raised ceiling box + step-wall removal) appended to the cut list before the seam
   chamfer; `strip_adds()` (stops, hold-downs) unioned AFTER all cuts; ribbon gap widened. Lid, midplate, keys
   untouched.
3. **refs.py**: new hardware solids from the JSON: `strip_geometry`, `plain_body/display/fpc`, `strip_front`,
   `StripPath`, `strip_tail`. **panel.py**: Ribbon ctor gets `ze/z_glass` overrides.
4. **build.py**: checks swap in the new refs (`others` in interference, extra insertion paths for the strip
   pieces/LEDs/U-fold, new `EXPECTED` pairs incl. `EXPECTED_STRIP`), plus `strip_check()` -> `out/light-strip.json`
   (BREP `distance` + overlap volume on cropped regions; `mesh_gap()` with scipy cKDTree for meshes).
5. **strip_sections.py** (new): matplotlib cross-sections -> `out/light-strip-sections/`.
6. Logs: `LS/out/build-strip.log` ends in `ModuleNotFoundError: rtree` (trimesh proximity) - hence cKDTree;
   `LS/out/slice-strip.log`: tub slices, exit 0, 56 layers, 11.30 g, est. 28m31s print.
**Mirror for the top**: append a `# ---- top light variant` params block; export the light PCBA outline/LED/header
positions from KiCad to `hardware/reference/light-attachment/*.json`; add `refs.light_pcba()` solids; add
`tub.light_cuts()/light_adds()` (+ `lid` cuts where the pocket crosses the seam); register the PCBA in
interference `others`, EXPECTED (header pins x J6), an insertion/plug-in sweep along -Y, and a `light_check()`.

## Proposal (a) integrated top brow (INFERRED)
Space today: J6 face 113.15, wall inside 113.4, outside 115.6; the solid ledge y 110.865..113.4 z 2.0..6.0 sits
between the glass's top edge and the wall; over J6 only the lintel z 0.215..6.0 remains.
- **PCB outline in XZ** (normal +Y): a wide LED bar over x ~1..59 at z ~0.5..6+, plus a tab over J6 only
  (x 42.6..58.9) running back to z ~ -5.3 to carry the 2x6 pins (rows z -1.36/-3.90 need copper to ~-5.2).
  Keeping the wide part above z ~0.2 leaves the top tongue/groove (z < -3.75, x 1.3..37) and the top screw
  (x 38.5..41.9 boss, pilot to z 5.45, y <= 113.65) intact.
- **Raise the wall**: `TOP_WALL` 2.2 -> 2.2 + H (keep `TOP_IN` 113.4). `Y1` flows into outer_body, both J6 cuts,
  the lid tray and the back logo. H = (PCB underside above 113.15 set by the male header spacer) + PCB t + >= 1.2
  roof. E.g. underside 115.8 (same as the external variant, so one PCBA), t 1.0, roof 1.2 -> Y1 ~ 118.0 (+2.4).
- **Brow pocket**: new `tub.light_cuts()` box x(bar) x y(113.15..Y1-roof) x z(0.2..ceiling), plus the J6 tab
  slot (the existing opening, extended to Y1-roof) and a lid cut for the tab below SEAM.
- **LED channel to the glass**: LEDs on the underside emit -Y, grazing the glass. They must sit at z >= 4.98 and
  the channel must pass through the ledge (y 110.865..113.4). Under a 6.0 face only 5.30 is proven (0.70 skin,
  STRIP_CEIL): a 0.32 slot, too thin for an LED. Options: (1) raise `SKIN`/`Z_FRONT` globally ~0.6-0.8 (tub stays
  flat for face-down printing, keys follow Z_FRONT; window gets deeper); (2) a brow proud of Z_FRONT only at the
  top - **breaks the flat face-down first layer of the tub** (tub.py:1-3), so it would need a separate printed
  "brow cap" part that carries the PCBA and takes the top screw; (3) edge-light the FT01C's LGP instead (z
  4.1..4.5, top edge 110.465, 0.4 from the pocket wall 110.865) by cutting the ledge back at z 3.64..4.98.
- New checks: PCBA solid vs tub/lid/battery/display, pins x J6 EXPECTED, a -Y plug-in sweep (like `later_moves`).

## Proposal (b) external clip-on (no change to the stock case; INFERRED)
Registration and grip features on the stock case:
- **Top face** y 115.6: flat x 0.91..59.09, z -4.7..4.2. The seam V (0.4 deep, z -4.15..-3.35) is a ready-made
  detent line for a small bead on the housing.
- **J6 opening** x 42.58..58.92, z -5.415..0.215, J6 face 2.45 inside. A 2x6 male spacer (~15.24 x 5.08) can nose
  into it for X/Z location (~0.5/0.27 per side). Pins must reach 2.45 + the socket's engagement depth.
- **Front face band** z 6.0, y 109.1..113.8 (then R1.8): the front jaw/LED hood may overlap it but must stay at
  y >= 109.1 (window bevel edge). An LED at (y 110, z 6.5) lights glass down to y ~107.93 past the window's corner
  (108.5, 5.4); the active top is 107.9. Rays graze at <1 deg over most of the page.
- **Back face** z -6.7, flat from y 113.6 down (R2.0). The top screw's counterbore (D4.2, 1.8 deep at (40.2,
  112.8)) can take a D<=4.0 spigot on a back jaw: swap in M2x12 through a 1.2 tab (tip z 4.1 < pilot end 5.45).
- **Case thickness** 12.7 for a C-clamp (jaws round R1.8 front / R2.0 back). **Top corners** R5 (y 110.6..115.6).
  Side ears may grip x = -4.09 / 64.09 only at y >= ~107 (right SW10 flexure to 106.0; left SW7 root 91.0).
- The same PCBA (pins -Y, LEDs at its front edge over the face) fits both variants if (a) puts the PCB at the
  same height above J6.

## Build / check commands and timings
- Python: `W/silkscreen-enclosure-claude/.venv/Scripts/python.exe` (3.11, cadquery 2.8.0, trimesh 5.1.0;
  README:986-987). **rtree is not installed**: trimesh ray/proximity calls fail, so use cKDTree or section math.
- Run from the copy root (hw.ROOT = src/.. -> reads `E/hardware`, writes `E/out`; board.step, cache/*.brep,
  footprints.json, logo/ are all in the copy, so only the venv comes from the original):
  `cd E && "<W>/silkscreen-enclosure-claude/.venv/Scripts/python.exe" src/build.py` (`--no-check` skips interference).
- This run (2026-09-25): **rc 0, 345 s wall**. tub 15.2 s, lid 31.8 s, midplate 9.5 s, keys 0.6 s each;
  insertion + later moves 154 s; interference 95 s. Wrote tub/lid/midplate/key_* .stl+.step, key_*-printed,
  lid_body, skey_* (5), ref_display, ref_battery, insertion.json, interference.json.
- Results: insertion paths all clear; PCBA-in and lid-on clear; **7 interferences, all designed** (lid x battery
  12.0 mm3 spring preload, midplate x PCB 6.25, midplate x display_thick 1154.6 take-up, 3 ribbons + battery plug
  seated in J2-J5). Identical to the previous `out/interference.json`/`insertion.json`.
- Pipeline after build: `mechanics.py` -> out/mechanics.json; `plates.py` -> out/print/ (no `out/print/tub.stl`
  in the copy yet); `slice_check.py [part]` needs `C:\Program Files\OrcaSlicer\orca-slicer.exe` (installed).
- `src/mechanics.py` (same python, same cwd): **rc 0, 153 s wall** -> out/mechanics.json. Key sweeps touch only
  plungers and the designed stops (side keys meet the tub sliver only at 115 % = 0.805 nub travel); max strain
  1.37 % (board snap root) < the ~1.5 % PLA limit (README:245). Slicing not run (Orca installed; needs
  plates.py first because out/print/tub.stl is missing).
