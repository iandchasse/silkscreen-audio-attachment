# Audio attachment housing - check report

Base = rev C base with the left boss at x 12.00; new audio lid (no hood, closed cap, plug opening in the left end). PCBA source: **geometry.json rev A (2026-11-09, file mtime Mon Nov  9 05:21:35 2026)**. Lid top y 124.1 (8.5 above the case top), roof underside y 122.9, front face z 8.5. Overall: **PASS**.

| Check | Result | Key numbers |
|---|---|---|
| Base identity vs rev C | pass | symmetric difference 30.11 mm3, inside the two boss sites (bbox [7.801, 115.8, -3.2] .. [14.199, 118.1, 1.2]) |
| Seated vs stock case | pass | base (no bumps) 0.001 mm3, lid 0.0, PCBA 0.0/0.0; bumps 0.719 mm3, depth 0.1 |
| PCBA fit | pass | lid-jack gap 0.3, lid-SMD 0.501, lid-tails 2.17, roof over jack/tails/SMD 0.3, PCB edge to the lid below the board top 0.299; float +-0.19 clean |
| Seam (rabbet) | pass | min gap lid-base 0.1; clean when the lid is shifted 0.095 in x/z or lowered 0.095 |
| Plug opening | pass | opening dia 6.56 (design 6.5), centre y 120.095 z -0.002 vs jack axis y 120.1 z 0.0: offset 0.005; plug body dia 9 x 20 to lid gap 0.5, to case 3.0; tip dia 3.5 clean |
| -Y insertion | pass | tips reach the J6 face at h [5.05, 4.72]: X play 0.052 / 0.052 (target <= 0.12), Z 0.052 / 0.047; bumps touch ~h 6.0 |
| Screws | pass | M2 x 3 pan, blind dia 1.6 pilots (skin 0.2); counterbore dia 4.4 floor y 118.9; tip y 115.9 = 0.1 above the pilot bottom; thread 2.2 mm |
| Side keep-out (SW10) | pass | below y 107.0 the base is at z >= 2.17 (needs >= 2.0) |
| J6 engagement | pass | [4.72, 5.05] nominal, [4.39, 5.38] worst (limits [3.7, 6.0]) |
| Printability | pass | base on its back face (back jaw on the bed), lid top-down (roof on the bed) |

Real PCBA STL (pcb\production\3d\silkscreen-audio-attachment_pcba_E.stl, 58 bodies, Mon Nov  9 05:21:14 2026): base_nb 0.0 mm3 / gap 0.085, lid 0.0 mm3 / gap 0.005, case 0.0 mm3 / gap 0.235 -> pass.

## Insertion sweep (h = height above seated; play in mm, None = free > 1.2)

| h | collision mm3 | bumps mm3 | x+ | x- | z+ | z- |
|---|---|---|---|---|---|---|
| 10.0 | 0.0 | 0.0 | None | None | None | 0.619 |
| 9.0 | 0.0 | 0.0 | 0.787 | 0.787 | None | 0.211 |
| 8.5 | 0.0 | 0.0 | 0.516 | 0.516 | None | 0.127 |
| 8.0 | 0.0 | 0.0 | 0.319 | 0.319 | 0.628 | 0.084 |
| 7.5 | 0.0 | 0.0 | 0.188 | 0.188 | 0.267 | 0.061 |
| 7.0 | 0.0 | 0.0 | 0.112 | 0.112 | 0.094 | 0.052 |
| 6.5 | 0.0 | 0.0 | 0.08 | 0.08 | 0.047 | 0.052 |
| 6.0 | 0.0 | 0.099 | 0.066 | 0.066 | 0.047 | 0.052 |
| 5.5 | 0.0 | 0.631 | 0.056 | 0.056 | 0.047 | 0.052 |
| 5.05 | 0.0 | 0.719 | 0.052 | 0.052 | 0.047 | 0.052 |
| 4.72 | 0.0 | 0.719 | 0.052 | 0.052 | 0.047 | 0.047 |
| 4.0 | 0.0 | 0.719 | 0.047 | 0.047 | 0.047 | 0.047 |
| 3.0 | 0.0 | 0.719 | 0.047 | 0.047 | 0.047 | 0.047 |
| 2.0 | 0.0 | 0.719 | 0.047 | 0.047 | 0.047 | 0.047 |
| 1.5 | 0.0 | 0.719 | 0.047 | 0.047 | 0.047 | 0.047 |
| 1.0 | 0.0 | 0.719 | 0.047 | 0.047 | 0.047 | 0.047 |
| 0.5 | 0.0 | 0.719 | 0.047 | 0.047 | 0.047 | 0.047 |
| 0.0 | 0.001 | 0.719 | 0.0 | 0.0 | 0.0 | 0.0 |

## OrcaSlicer CLI (Elegoo CC2 0.4, 0.20 Standard, PETG, 3 walls, 30 %, supports OFF, detect thin walls ON)

- base: 20m 21s, 3.25 g, 82 layers, support 0, warnings 0
- lid: 12m 36s, 3.39 g, 42 layers, support 0, warnings 0
- base G-code, blind-pilot skins: PRINTED

## What it is
- **2 printed parts + 2 screws.** BASE: the rev C base, unchanged (1.0 floor on the case top, window over the J6 opening, 1.2 skirt
  with the X guides and snap ridges, rabbeted top edge, blind dia 1.6 pilots), except that the left boss and pilot moved from x 10
  to **x 12.00** (z -1.00) to clear the jack body (x -2.84..8.65) and give the lid's screw column room.
- LID: a closed rounded cap, no hood. One cavity over the whole board (PCB outline + 0.3), roof underside y 122.9 (jack top
  122.60 + 0.3, header tails 119.60), top y 124.1 (8.5 above the case top), front face z 8.5 (flush with the base's front
  tongue, 2.5 in front of the case face). Rev C seam: the lid's 0.7 skirt rides over the base rabbet. Top-front edge R2.2, back
  top edge R2.0, back plan corners concentric with the case's, front plan corners R3.75. The X-Y end corners follow the base's R6.25
  arcs up to the seam and then rise straight with only R0.6 at the roof ends (the plug opening top is at y 120.10+6.5/2, no room for more).
- **Plug opening** in the left end wall: dia 6.5 circle on the jack barrel axis (y 120.10, z 0.00), plus a straight slot below it to the
  lid's lower edge (the lid prints roof-down, so the opening has no overhang). A 0.3 deep flat pad on the end face (|z| < 4.9) sits
  behind the nose tip (x -5.34) so a dia 9 plug body seated against the nose never touches the lid.
- **Screws.** Two M2 x 3 pan heads from the top, each in a dia 4.4 counterbore (floor y 118.90) in a dia 6.0 lid column (wall
  0.8) whose underside clamps the PCB top (y 117.60). A nominal 3 mm screw ends at y 115.90: 0.10 above the blind-pilot skin,
  0.30 above the case top, thread 2.2 mm. A 4 mm screw bottoms on the pilot skin with its head 2.5 proud of the counterbore floor.
- **Print:** PETG, no supports. Base on its back face; lid top-down (roof on the bed). Turn on Detect thin wall (the 0.2 skins under the pilots).
- **Build:** drop the PCBA on the base, lid on, 2 screws, push the assembly straight down onto the case top.

## Deviations from the spec
1. Roof ends: only R0.6 (the opening top at y 123.35 leaves 0.75 above it; a bigger round would break the opening).
2. Plug opening is a keyhole (circle + slot to the lower edge) for printability, plus a 0.3 end pad; the circle is the spec's dia 6.5.
3. Screw columns are dia 6.0 (r 3.0), not the 3.2 keep-out radius: the jack float (0.19) and a 0.3 gap to parts need it, so the PCB-top clamp is a 0.6 wide ring around the dia 4.8 boss recess.


## Files

- print\base.step
- print\base.stl
- print\lid.step
- print\lid.stl
- print\plate.3mf
- E\base.stl
- E\lid.stl
- E\pcba_header_bodies.stl
- E\pcba_jack.stl
- E\pcba_pcb.stl
- E\pcba_pins.stl
- E\pcba_smd.stl
- render\assembly_iso.png
- render\left_end_jack_opening.png
- render\left_end_iso.png
- render\front.png
- render\exploded_iso.png
- render\section_jack_axis_z0.png
- render\section_jack_x2.3.png
- render\section_boss_x12.png
- render\section_plug_opening_x-4.png
- print/plate.3mf
