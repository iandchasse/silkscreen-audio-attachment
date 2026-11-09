# Expansion header (J6) mechanical definition (enclosure frame) - research

Main-board parts named here: J6 is the expansion header; H1 the top-right mounting hole and H5 the right-hand one beside
the battery connector; SW10 the power button; U8 the header's ESD array; D3/D8 the frontlight clamps; CR2/CR3 the 3V3-
and battery-pin clamps; F2 the battery pin's fuse.

Status: COMPLETE (2026-09-25)

Abbreviations: ENC = W\silkscreen-enclosure-claude; PCB = W\de-link_pcb\silkscreen_pcb.kicad_pcb;
J6blk = J6 footprint block extracted from PCB (python); STEP = ENC\hardware\cache\J6.brep (the
footprint's 3D model as placed, analysed with ENC\.venv cadquery).

## Key numbers (enclosure frame, mm)
| Quantity | Value | Source |
|---|---|---|
| Insertion direction of male pins | -Y (J6 face normal +Y) | STEP faces, sec 3 |
| Contact columns X (pins n / n+6) | 44.502 + 2.54k, k=0..5 (model says 44.402+2.54k) | footprints.json pads; sec 2 |
| Row far from board: pins 1-6, Z | -3.81 real (INFERRED) / -3.895 model | S1 B=5.08; STEP |
| Row near board: pins 7-12, Z | -1.27 real (INFERRED) / -1.355 model | same |
| J6 mating face Y | 113.150 model; 112.929 B.Fab; 112.82 STEP-internal | mechanical.json; J6blk |
| J6 body box | X 42.978..58.726, Y 104.42..112.93, Z -5.08..0 (real) | J6blk B.Fab, S1 |
| Contact insertion depth (max) | 6.00 [.236"] | S1 p.115 |
| Min engagement (analog) | 3.68 [.145"] (Samtec SSW; INFERRED for Sullins) | S3 |
| Board top edge Y / faces Z | 111.25 (straight X 42.72..58.32) / rear 0, front 1.60 | outline.json |
| Glass front z / top glass edge Y | 4.98 / 110.615 (active top 107.90) | hw.py:24-30, params.py:24 |
| Stock top wall | inside Y 113.4, outside Y 115.6 (2.2) | params.py:66-69 |
| Stock J6 opening | X 42.582..58.922, Z -5.415..+0.215, through the wall | tub.py:171-175, lid.py:102-104 |
| J6 nets | 5 LED_SW, 6 W-, 11 C-; 1,4 GND; 7 3V3; 12 P+_FUSE; 8 SDA; 10 SCL; 2,3,9 GPIO | PCB pad nets |
| Recommended header | Sullins PRPC006DAAN-RC (2x6, .230"=5.84 mating, 2.54 body) | S2, DigiKey 2775288 |
| Engagement: internal / external-in-opening | 5.84 / 5.60..5.84 | sec 9 |
| Alt. external (body outside wall) | PRPC006DFAN-RC (.318"=8.08): 5.30..5.63 | sec 9 |

## 1. Coordinate frame
- X = KiCad X - 44.24; Y = 148.25 - KiCad Y (+Y = top edge, J6 end); Z = 0 at PCB rear face, +Z
  toward the screen; all parts on the rear (-Z) side. [ENC\README.md:70-74, ENC\src\hw.py:4-5]
- KiCad board thickness 1.6 [PCB `(thickness 1.6)`; ENC\src\hw.py:20]. PCB front face z = +1.60.

## 2. J6 footprint (KiCad)
- `PPPC_12:CONN_PPPC062LJBN-RC_SUL`, layer B.Cu, at KiCad (88.742362, 47.969573), rot 0
  -> CAD origin = pad 1 = (44.502, 100.280). [J6blk; ENC\hardware\footprints.json J6 entry]
- Pads: 12 x thru-hole, circle 1.524, drill 1.016. Local (x, y): pads 1-6 at (0..12.7 step 2.54, 0);
  pads 7-12 at (0..12.7, -2.54). [footprints.json J6 pads]
- Absolute CAD pad centres: pad n (n=1..6) X = 44.502 + 2.54(n-1), Y = 100.280;
  pad n (n=7..12) X = 44.502 + 2.54(n-7), Y = 102.820. Pad X set: 44.502 / 47.042 / 49.582 /
  52.122 / 54.662 / 57.202. Row 7-12 is nearer the top edge.
- B.Fab body outline (local x -1.524..14.224, y -12.649..-4.140) -> CAD X 42.978..58.726,
  Y 104.420..112.929 (8.509 deep, 15.748 wide, centred on pads at X 50.852). [J6blk fp_line B.Fab]
- B.SilkS front CAD Y 113.056; B.CrtYd CAD X 42.724..58.980, Y 99.264..113.183. [J6blk]
- 3D model: `${KIPRJMOD}/KiCad/9.0/3rdparty/PPPC062LJBN_RC/PPPC062LJBN-RC.STEP`,
  offset (6.25, -1.5, 0), scale 1, rotate (-90, 0, 0). [J6blk `(model ...)`]
- **Model misplacement found:** the placed STEP's pin tails are centred at X 44.402 (+2.54k) and
  Y 100.61 / 103.15, i.e. **0.10 mm toward -X and 0.33 mm toward +Y of the real pads** (offset x
  should be 6.35 = pad-row centre). [STEP solids 8-19: x 44.102..44.702, y 100.31.. / 102.85..]
  The enclosure's J6 bounds (and so its top-wall opening) come from this STEP. INFERRED
  consequence: the real body sits ~0.1 mm further +X and its face ~0.2-0.33 mm lower (-Y) than the
  enclosure assumes; see section 3 for the datasheet cross-check.

## 3. J6 in enclosure frame
### 3a. As modelled (STEP / enclosure data)
- Bounds (whole part incl. leads): X 42.882..58.622, Y 100.310..113.150, Z -5.165..3.065
  [ENC\hardware\mechanical.json components.J6; README.md:145].
- Plastic body: 6 cells 2.54 wide + 0.25 end walls, X 42.882..58.622, Y 104.650..113.150,
  Z -5.165..-0.085 (5.08 tall = 2 x 2.54) [STEP solids 0-7; tub.py:172 docstring].
- Mating face plane Y = 113.150, normal +Y (insertion direction of the male pins = -Y).
- Openings on the face: 1.40 x 1.40 lead-in squares, chamfering to 0.60 x 0.60 at Y 112.75,
  modelled socket bottom Y 111.88 (1.27 deep - simplified model, not the real contact depth).
  Opening centres Z = -1.355 (row nearer board) and -3.895 (row farther from board). [STEP faces]
- Leads stand to Z 3.065 (1.465 proud of the PCB front). [mechanical.json; README.md:145]
### 3b. Contact map on the mating face (pin-number mapping from tail geometry)
Row 1-6 tails (Y 100.28, farther from the face) rise to Z -4.095, so they feed the row FARTHER
from the board; row 7-12 tails (Y 102.82) stop at Z -1.555, the row NEARER the board. [STEP]
| Pin | X real (pad) | X as modelled | Z centre | Row |
|---|---|---|---|---|
| 1..6 | 44.502 + 2.54(n-1) | 44.402 + 2.54(n-1) | -3.895 | far from board (outer) |
| 7..12 | 44.502 + 2.54(n-7) | 44.402 + 2.54(n-7) | -1.355 | near board |
Mating face Y: 113.150 (STEP) vs 112.929 (B.Fab); corrected table in 8a.
Nets (PCB pad nets): 1 GND, 2 GPIO46, 3 GPIO45, 4 GND, **5 LED_SW**, **6 W-**, 7 3V3, 8 SDA,
9 GPIO3, 10 SCL, **11 C-**, 12 P+_FUSE (battery). The light needs only 5, 6 (far row) and 11 (near).

## 4. Board outline near the top edge
- Edge.Cuts bbox CAD X -0.0025..59.9975, Y 0..111.2501 [PCB Edge.Cuts; outline.json;
  mechanical.json pcb]. Board top edge Y = 111.250 from X 42.724 to 58.318 (straight line
  (42.724,111.249)-(58.318,111.250)); right corner arc to (59.948,109.430) then X 59.997 edge;
  left end: arc from (41.815,110.293) to (42.724,111.249) then the battery-notch diagonal
  (39.997,83.75)-(41.815,110.293). [outline.json]
- So the board's straight top edge spans only X 42.72..58.32; everything left of X ~41.8 at the top
  is the battery notch (cell occupies X 1.11..38.31, Y 82.0..113.1, Z -3.18..2.0 [params.py:323]).
- J6 face overhangs the top edge by 1.90 (113.15 - 111.25) as modelled [README.md:145].
- Board faces: rear z 0, front z 1.60.

## 5. Display panel (GDEQ0426T82-FT01C) [ENC\src\hw.py:24-30, panel.py:20-45, params.py:24-27]
- Glass/EPD outline 62.37 x 105.33 (+-0.15/+-0.20), X -1.185..61.185, Y 5.285..110.615.
- **Top glass edge Y = 110.615** nominal (110.715 at +tol); pocket top Y 110.865.
- Active area 55.68 x 92.8: X 2.16..57.84, Y 15.10..107.90 (centre 30.0, 61.5).
- Z: touch film front (= glass front surface, lip underside) z 4.98; touch 4.68-4.98; OCA 4.50-4.68;
  light guide (LGP) 4.10-4.50; OCA 3.92-4.10; EPD 3.00-3.92 (TFT glass 3.00-3.64).
- LGP outline X -0.685..60.715, Y 6.865..110.465; touch X -0.735..60.765, Y 10.485..110.185.
- Screen window = active + 0.6 at the lip -> top edge Y 108.50; front face z 6.00; lip 1.02 thick.

## 6. Stock enclosure J6 opening [ENC\src\tub.py:171-175, lid.py:102-104, params.py:28-30,66-69]
- Tub part: X (b0-0.3)..(b1+0.3) = 42.582..58.922, Y TOP_IN-0.5 = 112.90 .. Y1+1 (through the
  2.2 wall, outside face Y 115.6), Z SEAM-0.2 = -3.95 .. -0.085+0.3 = +0.215.
- Lid part: same X/Y, Z b4-0.25 = -5.415 .. SEAM+1 = -2.75.
- Combined through-opening: **X 42.582..58.922 (16.34 wide), Z -5.415..+0.215 (5.63 tall)**, wall
  from Y 113.4 (inside) to 115.6 (outside). Top-wall inside 113.4 = 0.25 beyond modelled face.
- Relative to the REAL body (B.Fab X 42.978..58.726) the opening gives 0.40 (-X) / 0.20 (+X).
- Other top-wall features: top screw M2 at (40.2, 112.8), tub boss D3.4, lid boss D5.0
  [params.py:283-284, lid.py:45-47] -> lid boss spans X 37.7..42.7, i.e. ends 0.12 from the opening.
- Lid floor inside z -5.50, back face z -6.70; parting line z -3.75; front z 6.00 [params.py:14-32].

## 7. Footprints within 12 mm of J6 (all B.Cu; none on F.Cu) [PCB scan; z from mechanical.json]
H1 M2 hole (50.00, 96.60) gap 2.9 | SW10 power switch (57.47, 96.00), body X 53.84..61.19,
Y 89.46..97.53, z -4.49, gap 2.8 | U8 SOT-23-6 (45.86, 95.75) z -1.64 gap 3.2 | D8 SOT-323 (50.29,
92.92) z -1.14 gap 6.4 | CR3 SOD-323 (45.76, 92.35) z -1.20 gap 7.2 | F2 0805 (42.76, 91.25) z -0.54
gap 8.1 | D3 SMA (49.21, 89.45) z -2.31 gap 9.5 | CR2 SOD-323 (44.76, 89.25) z -1.20 gap 9.8.
None is beyond Y 111.25: the plug meets only J6, the top wall, the top-screw boss (X <= 42.7) and
the battery (X <= 38.31, Y <= 113.1).

## 8. Sullins PPPC right-angle datasheet
Source S1 = Sullins catalog pp.114-115, https://www.sullinscorp.com/catalogs/101_PAGE114-115_.100_FEMALE_HDR.pdf
(the footprint's own Datasheet field; identical to DigiKey's Female_Headers.100_DS.pdf).
- Part code: PP = polyester/phosphor bronze (thru-hole), P = gold flash, C = .100" centres, 06 per
  row, 2 = dual row, LJB = dual-row right angle, N = no mounting, RC = RoHS. [S1 p.115]
- LJB (2-row right angle): A (body depth) .335" [8.50]; B (body height) .200" [5.08]; tail .124"
  [3.15]. [S1 p.114 termination table]
- 06-position body length .620" [15.74]; contact pitch .100 [2.54]; row spacing .100 [2.54];
  end contacts .050 [1.27] from the body ends. [S1 p.115 table + drawing]
- **Insertion depth .236" [6.00]** (drawn on the straight dual-readout view; INFERRED to apply to the
  same contact in the LJB version). [S1 p.115]
- 3 A per contact; UL94V-0; PBT/nylon insulator; phosphor bronze contacts. [S1 p.114]
- JLCPCB listing (C3320946): 250 V max, 3 A, -40..+105 C, gold, insulator height 5.08.
  [https://jlcpcb.com/partdetail/3885540-PPPC062LJBNRC/C3320946]
- NOT in the catalog: row heights above the PCB, face-to-hole-row distance, insertion/withdrawal
  force, recommended minimum engagement. Derived instead:
  - Row centre heights: body 5.08 tall sitting on the board -> 1.27 and 3.81 above the rear face
    (INFERRED from B=5.08 and 2.54 row pitch; STEP gives 1.27/3.81 above its z -0.085 base).
  - Face-to-nearest-hole-row: 10.109 (B.Fab: body back 1.600 + depth 8.509) or 10.00 (STEP: back
    1.50 + 8.50). Face-to-far-row 12.649 / 12.54.
- Accepted pin: .025" [0.64] square (standard mate for .100 female headers; the Sullins male
  headers are .025 [0.64] sq. posts, S2 below). The STEP opening lead-in is 1.40 x 1.40 at the face.

### 8a. Real vs modelled J6 face and rows (enclosure frame)
| Item | Modelled (STEP, used by enclosure) | Real (from pads + B.Fab) |
|---|---|---|
| Pin-1 column X | 44.402 | **44.502** |
| Contact columns X | 44.402..56.902 | **44.502, 47.042, 49.582, 52.122, 54.662, 57.202** |
| Body X | 42.882..58.622 | **42.978..58.726** (15.748) |
| Mating face Y | 113.150 | **112.929** (112.82 if STEP's internal 10.00 is right) |
| Body back Y | 104.650 | 104.420 |
| Row near board (pins 7-12) Z | -1.355 | **-1.27** (INFERRED, body on the board, no 0.085 standoff) to -1.355 |
| Row far from board (pins 1-6) Z | -3.895 | **-3.81** (INFERRED) to -3.895 |
| Body Z | -5.165..-0.085 | -5.08..0 (INFERRED) to -5.165..-0.085 |
Design rule: accept the face anywhere in Y 112.8..113.2 and rows +-0.1 in Z; let J6 itself locate
the plug (floating plug / slotted holes), not the case.

## 9. Mating male header recommendation
Sources: S2 = Sullins .025" square-post header catalog pp.74-75,
https://media.digikey.com/pdf/Data%20Sheets/Sullins%20PDFs/Square%20Post%20Header.pdf (post .025
[0.64] sq; termination codes AA = head .230 [5.84] / tail .120 [3.05]; FA = .318 [8.08] / .120;
06-pos length .600 [15.24]; dual-row width .200 [5.08]; insulator .100 [2.54]).
S3 = Samtec SSW spec (same-class 8.5 mm .025 sq socket), https://datasheet.octopart.com/SSW-103-01-G-S-Samtec-datasheet-5312073.pdf:
insertion depth 3.68-6.35, 1.67 N insert / 1.39 N withdraw per contact avg, 125 g normal force.
Parts exist at DigiKey: PRPC006DAAN-RC (2775288), PRPC006DFAN-RC (2775408) - mating lengths from
the S2 code table (DigiKey page 403'd; verify on order).

Geometry: light PCB stands in the XZ plane (normal -Y), straight 2x6 header on its -Y face, pins
along -Y into J6. Header body 15.24 x 5.08 x 2.54; pin field centred X 50.852, Z -2.54 (real).
Let Yf = J6 face, 112.82..113.15 (sec 8a); Dmax = 6.00 (S1); Dmin ~3.68 (S3, INFERRED).

| Variant | Header | Stop | Engagement | Margin to bottom | Light-PCB -Y face Y |
|---|---|---|---|---|---|
| Internal: body on J6 face | PRPC006DAAN-RC (5.84) | J6 face | 5.84 | 0.16 | Yf+2.54 = 115.36..115.69 |
| External, body INSIDE the stock opening | PRPC006DAAN-RC (5.84) | J6 face if Yf>=113.06, else PCB on wall outside (115.6) | 5.60 (Yf 112.82) / 5.71 (112.93) / 5.84 (113.15) | 0.16..0.40 | 115.36..115.69 (<= touches 115.6) |
| External, body OUTSIDE wall (on 115.6) | PRPC006DAAN-RC (5.84) | wall | 3.06..3.39 | - | 115.6+2.54 - **REJECT** (< 3.68) |
| External, body OUTSIDE wall (on 115.6) | PRPC006DFAN-RC (8.08) | wall | 5.30..5.63 (+0.2 if wall prints thin) | 0.37..0.70 | 118.14 |
**Recommendation: PRPC006DAAN-RC (standard .230" mating) with the body seated on J6's face in both
variants.** The stock opening (16.34 x 5.63) admits the 15.24 x 5.08 body with X 0.65/0.45 and
Z 0.335/0.215 clearance (real pin field; 0.25/0.30 on the STEP rows), so the same PCBA works
externally through the stock wall and internally direct, with 5.6-5.84 engagement and no bottoming.
Pin tips end at Yf-5.84 = 107.0..107.3, inside J6's insulator (back at 104.42). Tails: .120 post
stands 1.45 beyond a 1.6 PCB's +Y face - trim flush or cover. Fallback (body kept outside a wall):
PRPC006DFAN-RC plus a 2.45..2.78 standoff (the wall, or a printed rib in the internal bezel).

Safety / positioning:
- A 180 deg flip about Y maps pin 5 LED_SW (up to 24.5 V) onto pin 8 SDA, 6 W- onto 7 3V3, 11 C- onto
  2 GPIO46: the plug/housing must be keyed so it only fits front-up (asymmetric about the pin field).
- The 1.40 lead-in captures ~+-0.38 per pin: locate the pin field to +-0.3 in X/Z on the REAL contact
  X (not the STEP's -0.1). The opening already prevents a whole-pitch (2.54) shift.
- Connect only pins 5, 6, 11; leave 1-4, 7-10, 12 as isolated NC pads (or pull them: 12 pins =
  ~20 N insert / ~17 N withdraw per S3 averages, INFERRED; 3 pins ~5 N / ~4 N). The unplugged plug is
  passive (no source on its pins); J6's contacts sit recessed 0.25-0.6 behind the wall's inside face.
- Insertion load goes into J6's leads; the board is held in Y by the H5 pin at (50.36, 76.05) and
  posts H1 (50.0, 96.6) [mechanical.json holes; lid.py:50-60]. Let J6's face, not the case, stop an
  internal plug (float +-0.2 in Y).

## 10. Clearances for the light PCB and plug
- Plug envelope inside the stock case: X 42.58..58.92, Z -5.415..+0.215 (the opening); tub material
  fills Z > 0.215 above it and the lid floor is z -5.50 [params.py:30].
- Left of the opening: top-screw lid boss D5.0 at (40.2, 112.8) reaches X 42.7; tub boss D3.4 to
  X 41.9 (Z -3.75..4.98); battery X <= 38.31, Y <= 113.1, Z -3.18..2.0 [params.py:283-284,323].
- Right: J6 opening ends 4.49 from the case side (X 63.41); SW10 power side key has its root at
  Y 106.0 on the right wall and flexes below it (pad at Y 93.5) [params.py:207; README.md:132] -
  an external housing must not touch the right wall below Y ~106.
- Case outer: top face Y 115.6, X -3.41..63.41, front z 6.00, back z -6.70, plan corners R5, front
  edge R1.8, back edge R2.0, 0.4 V at the parting line z -3.75 [params.py:28-73; README.md 5.11].
- Glass-grazing targets: glass front z 4.98 (lip underside), front skin 4.98..6.00 over Y 108.5..115.6;
  top glass edge Y 110.615 (touch film top 110.185, LGP 110.465); active-area top Y 107.90; window top
  Y 108.50. From the recommended light-PCB -Y face (Y ~115.4..115.7) to the active top: ~7.5-7.8.
- Nothing else on the board lies beyond Y 111.25; the nearest rear parts (SW10 body to Y 97.53, z -4.49;
  U8 to Y 97.15) are all below J6's body (Y >= 104.42), so the plug never meets them.
