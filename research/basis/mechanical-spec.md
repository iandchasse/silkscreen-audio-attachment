# External clip-on light attachment - header + clip-on mechanical spec

Main-board parts named here: J6 is the expansion header (the 2x6 socket on the top edge); SW10 the power button and SW7
the left-up page key (both side keys); H5 the right-hand mounting hole beside the battery connector. C0-C2 are the rev A
cover columns, not parts.

Status: COMPLETE for the mechanical concept (2026-09-25). Reconciled with `design/optics-final.md` (done 2026-09-25: 3014 LEDs
+ 4.0 PMMA rod in a PCB-registered carrier), see sec 3f.
Frame: enclosure frame (X = KiCad X - 44.24; Y = 148.25 - KiCad Y, +Y = top edge; Z = 0 main-PCB rear, +Z toward the screen).
Stock case = silkscreen-enclosure-claude rev K, **unmodified**. Evidence: research/mechanical-j6.md, research/enclosure.md,
design/optics-sweep.md, design/parts.md, and the new section measurements below.

## 0. Summary
- **Header**: Samtec **TSW-102-14-G-D-004**: 2x2, .320 [8.13] gold post, .110 [2.79] tail, .100 body, position 4 omitted
  (J6 pin 12). LCSC C20382277; DigiKey TSW-102-14-G-D = product 1102472. Metal only at J6 pins 5, 6 and 11.
- **Stack**:
  - The header body can NOT rest on the case: it fits inside the J6 opening.
  - A 3-pad printed clip lands on the tub top face (y 115.60), and the cover's roof pushes the **header tail tips**.
  - Pin tip **y 107.94**, engagement **4.68..5.21 nominal**, worst case **4.03..5.64** (limits 3.68 / 6.00).
  - **PCB underside y 118.61** (1.6 board), gap to the case top 3.0.
- **Optics consequence**: optics-final assumed the PCB underside at 118.14. The real value is 118.61, so the LED face, rod and
  channel ride 0.47 higher: LED face 117.91, rod axis 114.16. The carrier lip bottom stays at y 110.0 absolute.
- **Grip**: the Z datum is the front lip on the bezel band (y 110.0..113.8), preloaded by 2 back spring fingers (0.30). The X datum
  is a right ear (y 107..110.6), preloaded by a left leaf (0.40). Two L-section front corner fingers beside the window guide X/Z from
  7.6 / 10.8 mm before seating, while the pins meet J6 at 4.7..5.2. Retention is about 8 N (J6 4.2 + friction), insertion about 10 N.
- **PCB**: floats +-0.30 in X/Z on 3 cover columns (Ø3.4 in Ø4.0 holes), centred by 4 light leaves, with 0.21 Y play.
- **Parts**: 2 printed parts (clip, cover) in PETG, both support-free, plus 3 x M2x6 screws.

## 1. Stock case exterior near the top edge (measured)

Method: `mesh_plane` sections of `E\out\tub.stl` + `E\out\lid.stl` (built 2026-09-25 from E\src, both watertight) with the
enclosure venv (trimesh 5.1, shapely 2.1; no rtree). Script: scratchpad `slice_top.py` / `slice2.py` (Y-Z sections at
x = 0, 5, 20, 30, 40.2, 50, 55, 60; X-Z at y = 113.5..115.59; X-Y at z = 5.95..-6.65; side skins x = -4.05/64.05).
Mesh bounds: tub x -4.09..64.09, y -8.4..115.6, z -5.15..6.0; lid x -5.59..65.59 (side-key pads), z -6.7..2.485.
Numbers below agree with `params.py` to 0.003 (tessellation).

### 1a. Top-face profile (Y-Z section; identical at x = 5, 20, 30, 40.2 and at x = 50/55 outside the opening)
| z | -6.7 | -6.6 | -6.4 | -6.2 | -6.0 | -5.5 | -5.0 | -4.7..-4.15 | -3.75 (V bottom) | -3.35..4.2 | 4.6 | 5.0 | 5.5 | 5.8 | 5.9 | 6.0 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| y top | 113.6 | 114.22 | 114.65 | 114.92 | 115.12 | 115.43 | 115.58 | **115.600** | **115.20** | **115.600** | 115.55 | 115.41 | 115.04 | 114.62 | 114.39 | 113.80 |
- **Top face y 115.600**, flat over **x 0.91..59.09** (R5 plan corners centred (0.91, 110.6) / (59.09, 110.6); at
  x = 0 and 60 the top is already 115.515) and **z -4.70..+4.20** less the seam V.
- **Back edge**: R2.0, centre (y 113.6, z -4.7): back face z -6.700 flat for y <= 113.6.
- **Front edge**: R1.8, centre (y 113.8, z 4.2): front face z 6.000 flat for y <= 113.8.
- **Seam V on the top face: z -4.15..-3.35 at the surface, bottom (y 115.20, z -3.75), 45 deg flanks (90 deg included),
  0.40 deep, 0.80 wide.** Tub above z -3.75, lid below. It runs x 0.91 (and round the corners) .. 42.582 and 58.922 ..
  59.09: **the J6 opening interrupts it** (x 42.582..58.922). At y 115.59 the X-Z section shows the gap at z -4.14..-3.36.
- **Seam V on the sides**: same V, z -4.15..-3.35, bottom at x -3.69 / 63.69 (0.40 deep), all the way down both sides.

### 1b. Front, back, sides, plan corners
- **Front face** z 6.000: flat band **y 109.1..113.8** over the window (x 1.01..58.99), then R1.8. Window bevel 45 deg from
  the lip (y 108.5, z 5.4) to the face edge **y 109.10 at z 6.0** (109.05 at z 5.95). Outside the window (x < 0.96,
  x > 59.04) the front face is flat from far below up to 113.8. Front face spans x -2.29..62.29 (R1.8 to the sides).
- **Back face** z -6.700: flat for y <= 113.6, x -2.71..62.71 (R2.0 to the sides). Nothing on it within 20 mm of the top
  except the **top-screw counterbore**: D4.2 at (40.2, 112.8) (x 38.1..42.3, y 110.7..114.9), floor z -4.90 (1.8 deep),
  D2.4 clearance above it (pilot ends z 5.45). Its top edge y 114.9 cuts into the back round wherever the round is below
  114.9 (z < -6.25): a **scallop in the back-top edge, x 38.1..42.3, up to 0.86 deep at z -6.7**. Screw head (M2 pan
  ~D3.8 x 1.3) sits ~0.5 below the back face.
- **Side faces** x **-4.090 / 64.090**, flat for z -3.30..4.30 (tub) and -4.80..-4.20 (lid), V between, R1.8 to the front
  (x -2.29 / 62.29 at z 6.0), R2.0 to the back (x -2.71 / 62.71 at z -6.6). **Flat in Y only up to y 110.6**; above it the
  R5 plan corner: side x at z 0 = -4.073 (y 111.0), -3.889 (112.0), -3.475 (113.0), -2.755 (114.0), -1.464 (115.0),
  -0.083 (115.5) (mirror at +X about x 30).
- **Keys/openings within 20 mm of the top (y >= 95.6)**:
  - Right side: **SW10 side key** (separate part in a wall slot) x 61.435..65.59, **y 89.8..106.0**, z -6.7..0.6; its pad
    stands 1.5 proud (x to 65.59) at y 90.0..97.0, z -4.49..-0.09; the flexure root = slot top **y 106.0**. The right side
    is plain above y 106.0.
  - Left side: SW7 slot y 70.3..**91.0** (24.6 below the top); plain above y 91.0.
  - Front: only the window. Back: only the counterbore (logo centred y 53.6, grip grooves y -5.6..-1.6: far away).
  - Top: only the J6 opening and the V.
- **J6 opening** (top face): **x 42.582..58.922 (16.34), z -5.415..+0.215 (5.63)**, square, sharp edges (no mouth chamfer),
  straight through the 2.2 wall. Its back edge z -5.415 lies on the back round (y 115.47 there). The lintel above it is
  solid tub z 0.215..6.0, so in front of the opening there is a flat top land **x 42.58..58.92, z 0.3..4.2 at y 115.6**.
  Inside: J6 face y 112.82..113.15 (2.45..2.78 below the top face); the lid cavity reaches y 114.4 at x 42.4..60.8,
  z -5.5..-3.75 (lid rim 1.2) - not reachable from outside except through the opening.
- **Brief/research correction**: case X extent is **-4.09..64.09** (params X0/X1); `research/mechanical-j6.md` sec 10
  quotes the stale -3.41/63.41 comment.

### 1c. Keep-out / grip table (stock case, external surfaces)
| Surface | Usable region | Use by the housing | Keep-out / notes |
|---|---|---|---|
| Top face y 115.6 (tub) | x 1.4..42.1, z -3.1..4.0 | **Y datum** pads P1 (x 2..8), P2 (x 24..30) | stay >= 0.25 off the V edges and the R1.8 start (z 4.2); do not land on the lid strip z < -3.75 |
| Top lintel land y 115.6 | x 43.0..58.5, z 0.5..4.1 | Y datum pad P3 (x 43.0..58.3, z 0.6..4.1), right beside the pins | opening edge z 0.215 |
| J6 opening | x 42.582..58.922, z -5.415..0.215, depth to J6 face 2.45..2.78 | boss (guard/filler, 0.3 clearance) + the 3 pins | boss bottom y 114.20 (>= 1.05 above the J6 face) |
| Seam V (top face) | z -4.15..-3.35, x 1..42.5 | **not used** (0.40 relief) | interrupted by the J6 opening; tub/lid boundary |
| Front face z 6.0 | y 110.0..113.8 over x -0.6..60.6 (lip); x -2.29..-1.10 / 61.10..62.29 down to y 103 (beside the window, outside the optics keep-out x -1.0..61.0) | **front lip = Z datum**; corner fingers = early Z/X guides | lip bottom >= 0.6 above the optics keep-out (sec 3f); nothing over the window (x 0.96..59.04) below y 110.0 |
| Back face z -6.7 (lid) | y <= 113.6, x -2.7..62.7 | **back spring fingers** x 3..13 and 47..57 (0.30 preload) | avoid the counterbore x 37.6..42.8 |
| Side faces x -4.09 / 64.09 | flat for y <= 110.6 (R5 corner above), tub z -3.3..4.3 | **right ear = X datum** (y 107.0..110.6, z -3.0..4.0); left spring leaf (bump y 104.5); corner-finger side parts z 2.0..4.3 down to y 103 | right side: no contact at z < 2.0 below y 107 (SW10 slot y 89.8..106.0, z <= 0.6); left side plain above y 91.0 |
| R5 plan corners | y 110.6..115.6 | ears may hug the corner with a 5.3 inner radius | - |

## 2. Header choice and engagement stack

### 2a. Choice
**Recommended: Samtec TSW-102-14-G-D-004** (2x2, lead style -14, gold, factory-omitted position 4).
| Item | Value | Source |
|---|---|---|
| Lead style -14 | A (OAL) .530 [13.46], B (tail) .110 [2.79], C (post) .320 [8.13]; body .100 [2.54] | Samtec TSW catalogue lead-style table (suddendocs tsw_th.pdf); samtec.com/products/tsw-102-14-g-d (post .320, OAL .530) |
| Post | .025 [0.64] sq phosphor bronze; -G = 10 u" gold on the contact area, 3 u" gold on the tail | TSW print (tsw-xxx-xx-xxx-x-xx-xxx-mkt.pdf) |
| Tolerances | .XXX = +-.005 [0.13] (OAL, post, body); tow & sway 2 deg max, all pins, post and tail (= up to 0.28 at an 8.13 post tip) | TSW print title block + note 7 |
| Omitted position | "-XXX = polarizing specification, position to be omitted"; -004 exists as a catalogue part | TSW print; LCSC datasheet for TSW-102-14-G-D-004 |
| DigiKey | TSW-102-14-G-D = DigiKey product 1102472 (the -004 suffix is not confirmed at DigiKey: order the -004 from Samtec direct, or TSW-102-14-G-D and push position 4 out before soldering) | digikey.com search result |
| LCSC / JLC | **C20382277** (TSW-102-14-G-D-004); C3332404 (TSW-102-14-G-D) | lcsc.com |
| Samtec position map (1/2 across the rows of the first column) | pos 1 = J6 pin 5 LED_SW (x 54.662, z -3.810); pos 2 = J6 pin 11 C- (54.662, -1.270); pos 3 = J6 pin 6 W- (57.202, -3.810); **pos 4 omitted = J6 pin 12 P+_FUSE (57.202, -1.270)** | parts.md sec 4 (Samtec numbering); J6 real contacts research/mechanical-j6.md 8a |
- Footprint: **3 PTH only** (Ø1.02 drill, Ø1.7 pad) at the three live positions, **no hole at position 4**. The 3-pin L then
  fits the 3-hole L in exactly one rotation, and nothing metal can ever sit at J6 pin 12 (or pin 4).
- Rejected / alternatives:
  - **Samtec -08 is NOT a .318 post**: TSW -08 = tail .200 / post .230 (OAL .530). The .320 post styles are -14 (tail .110),
    -25 (tail .210) and -29 (tail .910). -14 is the shortest tail and the one used here.
  - **Sullins PRPC002DFAN-RC** (FA = post .318 [8.08] / tail .120 [3.05], body .100, OAL .538 [13.67]; DigiKey
    S2211EC-02-ND INFERRED from PRPC023DFAN-RC = S2211EC-23-ND; 2x3 PRPC003DFAN-RC = DigiKey 2775411). Pin 12 must be pushed
    out by hand; Sullins tolerances not confirmed (+-.010 INFERRED). If used, raise the roof pad by 0.21 (to y 121.61).
  - Generic 2.54 "long pin" headers (2.5 body, 11-15 mm OAL): no DigiKey MPN, loose tolerances - not recommended.

### 2b. Why the header body cannot be the stop (correction to the brief)
The 2x2 body (x 53.392..58.472, z -5.080..0.000 on the real J6 columns) - and even a 2x6 body (15.24 x 5.08) - lies wholly
inside the J6 opening's plan area (x 42.582..58.922, z -5.415..0.215). A body "resting on the case top" would drop into the
opening and bottom on J6's face: engagement 8.13 > 6.00. The stop must be the **housing on the case top face**, and the
pins must be pushed by a housing surface whose height is fixed relative to that datum.

### 2c. Stop and push path (decided)
- **Y datum**: three clip pads on the **tub** top face y 115.60 (sec 3a). Nothing else touches the case top.
- **Push path**: the cover's roof underside (y 121.40) bears on the **header tail tips** over the pin field; the roof is held
  at that height by two cover columns (C1, C2) that stand on clip blocks right beside the header (sec 3e/5). The pin tip is
  then roof - OAL: **no PCB thickness, body or post tolerance in the chain**.
- The PCB+header hangs between the clip's top faces (y 118.40, pull-off ledges) and the roof pad with **0.21 Y play**; off the
  case it rests on the clip; while plugging, J6's resistance lifts it 0.21 onto the roof pad.
- **Do not trim the tails**; solder on the tail tips <= 0.10.

### 2d. Engagement stack (Y, mm; seated)
| Link | Nominal | Tol |
|---|---|---|
| Case top face (tub, at the pads) | 115.60 | +-0.10 (tub print, face vs the board's H5 location) |
| Clip: datum pad -> clip top face (column seat) | +2.80 -> 118.40 | +-0.10 (print Z, 14 layers of 0.20) |
| Cover: column seat -> roof underside (tail pad) | +3.00 -> 121.40 | +-0.10 |
| Header OAL (tail top -> post tip) | -13.46 -> **tip 107.94** | +-0.13 |
| Solder on tail tips | 0 | 0..+0.10 (less engagement) |
| Roof deflection at the pad under insertion (2.0 roof, columns 14 apart) | 0 | 0..+0.12 (less engagement) |
| Resulting: header body bottom 116.07 (0.47 above the top face), **PCB underside 118.61 seated / 118.40 resting on the clip**, PCB top 120.21 (1.6 board), tail tops 121.40 | | |

| J6 face Yf | Engagement E = Yf - 107.94 |
|---|---|
| 113.15 (enclosure model) | 5.21 |
| 112.93 (B.Fab) | 4.99 |
| 112.82 (STEP-internal) | 4.88 |
| 112.62 (112.82 with the main board pushed 0.20 down in its locating fit, INFERRED) | 4.68 |
- Worst case: E_max = 5.21 + 0.43 = **5.64 < 6.00** (0.36 margin); E_min = 4.68 - 0.43 - 0.10 - 0.12 = **4.03 > 3.68** (0.35
  margin). RSS of the four print/part tolerances = +-0.22 -> E typically 4.7..5.4.
- **What stops over-insertion**: the three clip pads on the tub top face, with the roof pad held by the C1/C2 columns straddling
  the header. A hard press on the roof goes roof -> columns -> clip blocks -> pads -> case. The pins cannot travel past 107.94
  -0.43 (worst) = J6 depth 5.64.
- Pin tips when the attachment is off: y 107.73 (hanging 0.21 lower).
- If Sullins PRPC002DFAN-RC is used: OAL 13.67 -> roof pad 121.61 for the same tip.

## 3. Housing datum / grip scheme

Two printed parts and the PCBA between them:
- **CLIP** (lower): datum pads, rails that seat the PCB, the front lip, 2 front corner fingers, 2 back spring fingers, the right
  ear, the left spring leaf, the J6 boss, and the column seat blocks. Every feature hangs from the clip's top face (y 118.40).
- **COVER** (upper): roof and tail pad, 3 columns with M2 screws into the clip, PCB float stops, centering leaves, the front skirt, and the
  end and back walls.
- **Assembly**:
  1. Drop the PCBA onto the clip, header down through the header pocket.
  2. Put the cover on.
  3. Fit 3 x M2x6 pan screws through the columns into Ø1.7 pilots in the clip.

### 3a. Datums on the case (all on the tub except the back springs)
| DOF | Case surface | Housing feature | Nominal fit |
|---|---|---|---|
| Y | tub top face y 115.60 | **P1** x 2.0..8.0, z -2.9..3.9. **P2** x 24.0..30.0, z -2.9..3.9. **P3** x 43.0..58.3, z 0.6..4.1 (the lintel land in front of the opening). | contact. Every other clip underside stays >= 0.40 off the case: y >= 116.0 over the flat top, >= 0.4 normal to the rounds. The V and the lid's top strip (z < -3.1) are relieved. |
| Z | front face z 6.000, bezel band y 109.1..113.8. This is the tub's first layer, so it is flat and accurate. | **front lip** inner face z 6.00, x -0.6..60.6, lower edge y 110.0 (0.9 above the window edge; 3.8 contact band) | contact, preloaded by the back fingers |
| Z (spring) | back face z -6.700 (lid) | 2 **back fingers** at x 3.0..13.0 and 47.0..57.0, clear of the counterbore (x 38.1..42.3) | inner face z -6.85 (0.15 clearance). Bump crest z -6.40 at y 106.0 = **0.30 interference**. |
| X | right side face x 64.090 (tub, z > -3.75), flat for y <= 110.6 | **right ear** inner face x 64.09, z -3.0..4.0, y 107.0..116.0 | contact, preloaded by the left leaf |
| X (spring) | left side face x -4.090 (tub) | **left leaf** z -2.5..3.5, inner face x -4.24 (0.15 clearance) | bump crest x -3.69 at y 104.5 = **0.40 interference** |
| Guides | front face beside the window; both side faces | 2 **front corner fingers**, L section. The front part covers x -2.29..-1.10 / 61.10..62.29 at z 6.10, outside the optics keep-out's x -1.0..61.0, and wraps round the R1.8 vertical edge (inner R1.9). The side part sits at x -4.19 / 64.19 over z 2.0..4.3. Tips at y 103.0. | 0.10 clearance on both faces |
- **No bead in the seam V.** This is a deliberate change from the brief:
  - the V spans the tub and the lid, whose faces can mismatch by about +-0.1;
  - the J6 opening interrupts it;
  - a bead would fight the front-lip Z datum.

  The housing bridges the V with 0.40 of relief.
- **Keep-outs honoured**:
  - The right ear ends at y 107.0. The SW10 slot and its flexure root are at y <= 106.0, z <= 0.6.
  - The right corner finger's side part stays at z >= 2.0, 1.4 clear of the slot's z 0.6 edge. Nothing touches the right side at
    z < 2.0 below y 107.
  - The left side is plain above y 91.0.
  - The back fingers avoid the counterbore.
  - The front lip stays above the window (y >= 110.0; window edge 109.1) and above the optics keep-out (3f).
- **Corner fingers below y 109.1 (a deliberate exception to "front jaw above 109.1").** The fingers sit beside the window and
  outside the optics keep-out's x range: x <= -1.10 / >= 61.10, against window face edges at 0.96 / 59.04 and an active area of
  2.16..57.84. They go below 109.1 because the 3.8 mm lip band engages only 3.8 mm before seating. That is after the pins have
  already met J6 (see 3c).

### 3b. Feature dimensions
| Feature | Section / size | Lead-in | Notes |
|---|---|---|---|
| Front lip | t 1.6 (z 6.00..7.60), x -0.6..60.6, from the front rail (y 116.0) down to a **flat bottom at y 110.0** | 0.3x45 on the inner bottom edge | >= 0.6 above the optics keep-out, 3f |
| Front corner fingers | t 1.6. Front part 1.19 wide, then the wrap, then the side part over z 2.0..4.3. y 103.0..116.0. | 1.0x45 outward on the tip | rigid guides, anti-rock, table feet |
| Back fingers | b 10.0, t 1.2. Root y 116.0 (R1.0 fillet into the back rail), tip y 103.0. Bump: a 45-deg ridge 0.45 high on the inner face at y 106.0, crest R0.2. | 1.0x45 outward on the tip | springs, 3d |
| Right ear | t 1.6 (x 64.09..65.69), z -3.0..4.0, y 107.0..116.0 | 0.8x45 at the inner bottom edge | rigid X datum (k about 90 N/mm) |
| Left leaf | b 6.0, t 1.2, root y 116.0, tip y 103.0. Bump 0.55 high at y 104.5. | 1.0x45 outward on the tip | spring, 3d |
| J6 boss | x 43.0..52.6, z -5.10..-0.10, bottom **y 114.20**, solid up to the clip top (118.40) | 0.3x45 all round the bottom | Clearances: 0.42 (-X) and 0.315 (+-Z) to the opening; 0.29..0.49 to the header body; >= 1.05 above J6's face (113.15). |
| Back rail | z -8.05..-4.20; the fingers hang from z -8.05..-6.85. Underside y 116.0. **Notched to z <= -5.70 over x 52.6..59.3** for the header body. | - | seats the PCB's back strip |
| Front rail | z 4.20..7.60, underside y 116.0 (above the R1.8 round) | - | carries the lip and fingers; seats the PCB |
| Right end block (C2 seat) | x 59.3..65.69, z -6.55..4.6, underside y >= 116.0 (clear of the R5 corner) | - | Ø1.7 pilot at (61.0, -2.54) |

### 3c. Engagement order (h = height of the housing above its seated position)
| h (mm) | Event |
|---|---|
| 12.6 | Finger tips (y 103.0 when seated) reach the top-face level. The 1.0x45 lead-ins capture about 1.1 of misalignment on the edge rounds. |
| 10.8 / 10.6 | The front fingers reach the flat front face (below 113.8) and the back finger inner faces reach the flat back face (below 113.6): **Z guided to +-0.13**. |
| 9.6 -> 7.6 | The back-finger bumps ride over the back round onto the flat back face, so the Z preload builds. The front fingers carry it until the lip engages. |
| **7.6** | The corner fingers' side parts reach the flat side faces (below 110.6): **X guided to +-0.10**. |
| 7.65 | The pin tips pass the top-face plane into the opening, >= 1.49 from its walls. No contact. |
| 6.1 | The left-leaf bump reaches the flat left side, so the X preload builds. |
| **5.21..4.68** | **The pin tips reach J6's face.** By now the housing has been aligned for >= 2.4 of travel in X and >= 5.4 in Z. |
| 3.6 | The right ear reaches the flat right side and takes over from the finger guide as the X datum. |
| 3.8 | The front lip reaches the bezel band and becomes the Z datum. |
| 1.4 | The boss enters the opening with 0.3 clearance. It is a guard and filler, not a locator. |
| 0 | P1/P2/P3 land on the tub top face. The roof pad, held by the C1/C2 columns, has pushed the tails so the tips sit at y 107.94. |

Capture budget, pin tip vs J6 contact:

| Axis | J6 vs case (INFERRED) | Housing vs case | Pin sway (2 deg max) | PCB rest: centred / not centred | Worst | RSS |
|---|---|---|---|---|---|---|
| X | +-0.25 | +-0.10 | +-0.28 | +-0.05 / +-0.30 | 0.68 / 0.93 | 0.39 / 0.49 |
| Z | +-0.10 | +-0.10 | +-0.28 | +-0.05 / +-0.30 | 0.53 / 0.78 | 0.32 / 0.43 |

J6's lead-in (1.40 sq at the face, per the STEP) captures (1.40-0.64)/2 = 0.38. The TSW tip bevel adds about 0.1, for about 0.5 in
total. That margin is why the centering leaves in 3e are recommended. Typical sway is far below 2 deg; bent pins are caught with the
go-gauge (sec 5).

### 3d. Springs, retention, forces (PETG E 2.0 GPa; PLA 3.5 in brackets)
- **Back fingers** (x2). Geometry: L 10.0 (root y 116.0 to bump y 106.0), b 10, t 1.2. Stiffness k = 8.6 N/mm [15.1].
  Deflection is 0.30 nominal and 0.05..0.55 over the case thickness (12.7 +-0.15) and the clip (+-0.10). That gives
  **N = 2.6 N each (0.4..4.8)** [4.5 (0.8..8.3)]. Strain at 0.55 is 0.99 % (across layers).
- **Left leaf**. L 11.5, b 6, t 1.2, k = 3.4 N/mm [6.0]. Deflection 0.40 (0.15..0.65), so N = 1.4 N (0.5..2.2). Strain at 0.65 is 0.88 %.
- **Retention (pull-off force)**, about **8 N in total (about 5..12 N)**:
  - J6: 3 contacts x 1.39 N = 4.2 N (Samtec SSW analogue).
  - Front/back friction: mu 0.3 x (back 5.2 + front reaction 5.2) = 3.1 N.
  - Side friction: 0.3 x 2.8 = 0.8 N.
- **Insertion force**, about **10 N**: J6 5 N (3 x 1.67) + friction 4 N + the bump ramps.
- **No positive snap.** The case has no Y undercut near the top:
  - the R5 corners only narrow the case upward;
  - the counterbore's top edge is scalloped away (y 114.9 vs the round at z < -6.25);
  - the screw head leaves only 0.2-0.5 of depth in the counterbore.
- **Optional screw lock** if friction proves too light. A back tab at x 36..44 carries a Ø4.0 x 1.7 boss that sits in the
  counterbore. Replace the stock M2x10 with an **M2x12** through the tab: head on the tab at z -7.9, tip at z 4.1, below the pilot end (5.45).
- **Load paths**:
  - **Push down** (seating, or pressing the roof): roof -> columns C0/C1/C2 and walls -> clip -> P1/P2/P3 -> case. The pins carry
    only J6's insertion force.
  - **Visor pushed down** (forward rock about the front pad edge, y 115.6 / z 4.1): the lip and front fingers bear on the front
    face below the pivot. Lever arms: lip 3.6, fingers up to 12.6, front edge about 15. The load goes into the case.
  - **Visor pulled up** (backward rock): the back fingers press on the back face. The pins mostly withdraw axially, and the float
    absorbs the small Z component.
  - **Side loads**: ear, leaf and finger side parts -> case sides.
  - **Drop while mounted**: the housing's inertia goes to the case. Only the PCBA's own inertia (about 5 g) reaches J6 through the
    pins, and the +-0.30 float stops cap it.
- **Pin protection off the case.** The finger tips (y 103.0) and the leaf tip stand **4.7 beyond the pin tips (107.73)**. Off the
  case, the part rests on 4 fingers spanning x -2.3..62.3, z -8.05..7.6. The pins' Euler load (fixed-free, 8.13 post) is about 56 N.
- **180-deg rotated attempt.** The rotated pins (x 2.80/5.34, z 0.57/3.11) meet the solid top face at h 7.65, with the fingers
  already guiding. **It cannot make electrical contact.** The boss cannot key: it enters only in the last 1.4, long after the pins
  arrive. What keys the connection is the off-centre opening.

### 3e. PCB float and Y retention
- **Float stops.** 3 cover columns (Ø3.40, M2 clearance bore Ø2.2) pass through **PCB holes Ø4.00 NPTH**, giving a radial float of
  **0.30**. The stops are drilled holes (+-0.05), not the routed outline (+-0.2).
  - C0 (5.00, 0.50) on P1.
  - C1 (47.00, 2.35) on P3.
  - C2 (61.00, -2.54) on the right end block.

  The cover walls stay 0.60 off the PCB edges and never touch.
- **Centering (recommended).** 4 cover leaves (0.8 x 3 x 8 mm) hang from the roof onto the PCB edges:
  - left: x -3.50, z 0..3;
  - right: x 63.50, z 10..13;
  - back: z -6.20, x 20..23;
  - front: on the rod carrier's +Z wall outer face (z 19.1), x 28..31, from the cover skirt.

  Preload 0.15, <= 1 N at full float. That is negligible against J6's lead-in: moving the PCB 0.3 bends the pins about 0.02.
- **Y.** Off the case, the PCB rests on the clip's top faces at y 118.40: rails, the P1/P2/P3/boss blocks and the right end block.
  While plugging, J6 lifts it 0.21 onto the roof pad. Y play 0.21. There is no clamp, so no friction opposes the float.

### 3f. Optics interface (from design/optics-final.md, status done 2026-09-25)
The optics pick is LUXEON 3014 warm/cool LEDs on the PCB underside behind a 4.0 PMMA rod. The rod sits in a matte-black
**rod carrier registered to the PCB**. Optics-final assumed PCB underside 118.14 (header body on the case top), which is
wrong (sec 2b). With this stack the whole light engine sits **0.47 higher**:

| Item | optics-final (PCB 118.14) | This stack (PCB 118.61 seated) |
|---|---|---|
| LED emitting face (0.70 package) | 117.44 | **117.91** (117.70 when off the case) |
| Rod axis (top 1.75 below the emitter face, z 15.90) | 113.69 | **114.16**; bottom 112.16 |
| Carrier -Z wall (inner face z 13.80) down to the rod equator | 113.69 | **114.16** |
| Carrier +Z wall = optics "front lip" (inner face z 18.1, outer >= 19.1) | lower edge 110.0 (allowed 108.0..110.85) | lower edge **y 110.0 absolute**, so the wall hangs 8.61 below the PCB |

Because the rod and both channel walls ride on the PCB, the rod-to-emitter geometry, and with it the beam, is unchanged. Only
the source height rises 0.47. Optics should re-run the pick at emitter y 117.91 (open item); higher sources shrink the top
shadow band.

**Carrier mounting (my interface)**:
- The carrier is **fixed to the PCB** and floats with it (+-0.30 X/Z, 0.21 Y). It must never be clamped to the housing, which
  would kill the float.
- It has 2 locating pins Ø1.50 into **PCB NPTH Ø1.60** at (-2.40, 16.00) and (62.40, 16.00), heat-staked on the PCB top. The
  stake heads must be <= 0.6 tall, leaving >= 0.59 below the roof.
- Rod end sockets: inner faces at x -1.0 / 61.0, rod x -3.0..63.0. The carrier's end walls reach x -4.2 / 64.2, overhanging the
  PCB ends by 0.7.
- The housing keeps >= 0.40 from the carrier everywhere, including float.

**Housing keep-out**:
- Optics rule: y_ko(z) = 107.99 + 0.341 (z - 4.00) for z 3.93..13.80, valid for x -1.0..61.0.
- The +0.47 source rise lifts the envelope by at most about 0.47 (z - 4)/(13.8 - 4). Allow y_ko + 0.2 at z 6..7.6, i.e. about 108.9 / 109.4.
- The **front lip bottom at y 110.0** (z 6.0..7.6) is **>= 0.6 clear**.
- The corner fingers sit at x <= -1.10 / >= 61.10, outside the keep-out's x range.
- The clip has nothing in z 7.6..13.8 below y 116.0; the optics "brow floor" allows y >= 111.5 (about 111.8 after the shift).

**Cover front skirt**:
- Optional cosmetic outer skin: z 19.5..21.0 (0.4 clear of the carrier +Z wall nominal, 0.1 at full float), bottom **y 110.0**, which is inside
  the optics' allowed 108.0..110.85.
- Matte black inside.
- It hides the float gap and the carrier. The carrier's own +Z wall is the optical lip.

## 4. Printability
- **Material: PETG, black, matte.**
  - The springs flex with the stress across layers: 0.99 % back fingers, 0.88 % left leaf. PETG takes this with margin (about 2 %
    across layers). It also resists creep under constant preload and heat.
  - PLA is for fit-check prints only. It reaches the same strains at 1.75x the force and creeps under the permanent 0.3-0.4 preload.
    The case README's PLA limit is 1.5 % in-plane.
  - A white or light interior would add unmodelled diffuse fill (optics).
- **CLIP**:
  - Printed **top face (y 118.40) on the bed**, so every feature is a prism growing toward -Y. **No supports.**
  - The first layer is the PCB seat, so the PCB sits flat.
  - Datum pads P1/P2/P3 are top surfaces at print Z 2.80 (14 x 0.20 layers). The boss top is at 4.20, finger tips at 15.4.
  - All X/Z locating faces are vertical walls in the print plane (+-0.1): lip z 6.00, ear x 64.09, fingers, boss.
  - Bumps are 45-deg ridges. The lip bottom (y 110.0) faces up in print. Pilots are Ø1.7 holes along print Z.
- **COVER**:
  - Printed **roof top (y 123.40) on the bed**. The roof is 2.0 thick. The tail pad is the roof's inner face, a top surface at print
    Z 2.0 (ironing optional).
  - Columns, walls, the front skirt and centering leaves grow upward. Screw counterbores (Ø4.2 x 1.0) open at the bed.
  - No supports. The skirt's outer face may lean <= 45 deg.
- **Minimum walls**: 1.2 (3 x 0.4 perimeters) for springs; 1.5-1.6 for the lip, corner fingers, ear and skirt; 0.6 for column walls
  around the M2 bore.
- **Layers**: 0.20 layers, 3 perimeters, 30 % infill. Pads and column seats solid (they are thin anyway). A 0.2x45 elephant-foot
  chamfer on the bed-face edges of both parts.
- **Fit coupon first**: print just the clip's datum + lip + ear + fingers strip (y 103..118.4) in PLA. Check it on the real case:
  lip contact, 0.30 back interference, ear contact, clearance to SW10.

## 5. Interface table (PCB <-> housing), enclosure frame
| Item | Value |
|---|---|
| PCB thickness | **1.6 mm** (JLC standard). It is not in the engagement chain (the push is on the tails), so 1.6's stiffness wins for the 12 mm front overhang, the LED row and header support. 1.0 would only lower the stack by 0.6 while leaving the tails 1.79 proud. |
| PCB outline (X-Z) | x **-3.50..63.50**, z **-6.20..17.70** (optics: front edge 17.6..17.8), corners R1.0; no notches. The cover walls stay 0.60 off. |
| PCB underside y | **118.61 seated** (roof pad on the tails) / 118.40 off the case (resting on the clip). Top face 120.21 seated. |
| PCB top side | **no parts**. Only the header tails, 1.19 proud with **no trimming**. The roof underside is at 121.40 over the whole PCB. |
| Header | Samtec **TSW-102-14-G-D-004** (LCSC C20382277; DigiKey TSW-102-14-G-D product 1102472, pull pos 4 if -004 is unavailable). Inserted from the underside, body against the PCB underside, posts -Y. 3 PTH Ø1.02 / pad Ø1.7 at **(54.662, -3.810) LED_SW = J6-5, (57.202, -3.810) W- = J6-6, (54.662, -1.270) C- = J6-11**. **No hole** at (57.202, -1.270), J6-12. Body x 53.392..58.472, z -5.080..0.000. |
| Float / screw holes | 3 x **Ø4.00 NPTH** at C0 (5.00, 0.50), C1 (47.00, 2.35), C2 (61.00, -2.54). No copper within 0.40 of their edges. |
| Centering-leaf contact points (edge copper keep-out 0.5) | left edge z 0..3; right edge z 10..13; back edge x 20..23; front: on the carrier's +Z wall (z 19.1), x 28..31 |
| Underside keep-out, no parts (clip contact + 0.4 incl. float) | Back rail strip z <= -3.80, and z <= -5.30 over x 52.6..59.3. Front rail strip z 3.80..8.00. P1 x 1.6..8.4, z -3.3..4.3. P2 x 23.6..30.4, same z. Boss/P3 block x 42.6..58.7, z 0.2..4.5 and x 42.6..53.0, z -5.5..0.3. Header x 52.9..59.0, z -5.6..0.5 (header only). Right end block x >= 58.9 over z -6.2..4.9. |
| Underside part height, over the case (zone A: x 8.4..23.6, 30.4..42.6 and -3.1..1.6, z -3.8..3.8) | **<= 2.0** (bottom >= 116.40, 0.8 above the top face) |
| Underside part height, in front of the face (z 8.0..LED row) | <= 2.0 for z <= 14.0. Nearer the LEDs, parts must stay above the optics plane + 0.3: at z 15, **<= 1.2**; within 1 mm behind the LED row, no taller than the LEDs. |
| LED row | LUXEON 3014 (0.70) at **z 16.00**, x 1.1/4.9 ... 55.1/58.9 (L5-w13.5-s1.9, optics-final). Emitting face y 117.91 seated. |
| Rod carrier zone z 13.4..17.7, x -4.2..64.2 | LEDs and the carrier only; carrier datum holes 2 x **Ø1.60 NPTH** at (-2.40, 16.00), (62.40, 16.00) |
| Inside the J6 opening | nothing from the PCB. Only the header posts (x 54.662/57.202) and the clip boss (x 43.0..52.6) enter it. |
| Housing envelope | x **-6.1..66.1** (the cover's front-region end walls clear the carrier), y **103.0..123.40**, z **-8.05..21.0** (skirt outer). It stands 7.8 above the case top face, 15.0 in front of the front face and 1.35 behind the back face. |
| Fasteners | 3 x M2x6 pan (thread-forming into PETG): cover -> clip, heads counterbored 1.0 into the roof, tips at y 116.4 (0.8 above the case top) |
| Go-gauge (QA) | a printed plate 1.0 thick with 3 x Ø0.95 holes at the pin pattern, slid to the pin tips, checks tip position within about +-0.15 before first mating |

## 6. Corrections to the brief / earlier research
1. **"Header body bottom rests at the case top face" is impossible.** A 2x2 (or even a 2x6) body fits inside the J6 opening
   (16.34 x 5.63), so it would drop in and bottom 8.13 pins in a 6.00-deep socket.
   - The stop must be the housing on the tub top face.
   - The same flaw is in research/mechanical-j6.md sec 9, rows "External, body OUTSIDE wall (on 115.6)".
   - The PCB underside is therefore 118.61 (set by the housing), not 118.14.
2. **Samtec -08 is not a .318 post.** TSW -08 is tail .200 / post .230. The .320 post with the shortest tail is **-14** (tail .110,
   OAL .530).
3. **Case X extent is -4.09..64.09** (params X0/X1). research/mechanical-j6.md sec 10 quotes the stale -3.41/63.41 comment.
4. **The J6 key boss cannot key or locate in time.**
   - It can go only about 1.4 into the opening (J6's face is 2.45..2.78 down), while the pins lead by 6.2.
   - X/Z must come from features on the case's outer faces.
   - 180-deg safety comes from the off-centre opening: rotated pins land on solid top face at x 2.8/5.3.
5. **The seam V is not a useful detent.** It sits on the tub/lid boundary, is interrupted by the J6 opening, and would
   over-constrain Z against the front datum. The retention it would give is along Z, not Y.
6. **"Front jaw must stay above y 109.1" needs an exception.** A lip limited to y >= 110.0 engages only in the last 3.8 mm, after the
   pins reach J6. Corner fingers beside the window (x <= -0.6 / >= 60.6) must go down to y 103 to guide X/Z first.
7. **The PCB float stops should be drilled holes on printed columns**, not the routed outline (+-0.2). The float should be +-0.30
   with light centering: the capture budget X is 0.39 RSS centred vs 0.49 uncentred, against about 0.5 capture.
8. **The top-screw counterbore offers no snap.** Its top edge breaks into the back round, and the pan head leaves only 0.2..0.5 of
   depth. It is only usable for an optional M2x12 screw-lock tab.

9. **design/optics-final.md used PCB underside 118.14**, from the same impossible "header body on the case top" stop. The real
   value is 118.61, so the emitter is at 117.91 and the rod axis at 114.16.
   - The rod-to-LED geometry is preserved because the carrier is PCB-registered.
   - The carrier's +Z wall must be 8.61 tall to keep its lower edge at y 110.0.
   - The carrier must be fixed to the PCB and float with it: "clamped between the PCB and the housing" would defeat the float.
10. **The front jaw can sit lower than the brief assumed.** The final keep-out (y_ko = 107.99 + 0.341 (z - 4)) lets the lip go
    down to y 110.0 with >= 0.6 clearance. That gives a 3.8 mm datum band instead of 3.2.

## 7. Open items
- Optics: re-run the rod pick (tools/rod_lens.py --pick) with the emitter face at y 117.91 (0.47 higher). Confirm band/uniformity
  and the keep-out shift (<= +0.47 at z 13.8).
- Confirm DigiKey stocks the -004 suffix. If not, order TSW-102-14-G-D and push position 4 out.
- Confirm Samtec pos-4 placement on the footprint (3-hole L).
- Real Sullins PPPC062LJBN-RC entry size (the STEP shows 1.40 sq), and the main board's Y/X play in the case (INFERRED 0.20 / 0.25).
  These drive the capture and engagement margins.
- Rod carrier detail design: pins/heat-stake, and matte black. It is PCB-mounted, so it belongs to the PCBA, not the housing.
- Bench: fit coupon for lip/ear/fingers on a real case, pull-off force (target 5..12 N), and whether the centering leaves are needed.
- PETG spring preloads assume the case at nominal 12.7 thick; re-measure a printed case.
