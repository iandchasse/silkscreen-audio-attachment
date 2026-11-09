# Silkscreen audio attachment: design spec, rev A

2026-11-09. This file is the build contract and wins over every other file.

**Sources:**
- `research/audio-chain.md`: the electrical design, adopted as written except where this file says otherwise.
- `research/bluetooth.md`: Bluetooth findings.
- `research/basis/*`: J6 and case facts carried over from silkscreen-light-attachment.

**Owner direction (2026-11-09):** "use the unused GPIO and other dev header signals to relay I2S info through to an
audio module with 3.5mm out, perhaps bluetooth if something works". He is away and asked for my own judgement on every
decision. Standing preferences:
- keep accessories BASIC: standard parts, 1-3 printed parts, screws, no glue or optics;
- populate only the header pins actually used;
- low profile, rounded, matching the case.

## 0. Decisions
1. **Audio chain:** PCM5102A (I2S, BCK PLL, no MCLK, no I2C) -> TPA6138A2 ground-centred headphone driver -> 3.5 mm
   TRS jack, per research/audio-chain.md section 1.1.
2. **Power:** a TPS7A2033 3.3 V LDO from P+ (J6 pin 12). Its EN is driven by the passive charge-pump detector on WS, so
   the whole audio side is unpowered unless I2S is running. Calculated idle ~0.1 uA. J6_3V3 and I2C are not used.
3. **Pins:**
   - BCLK on IO46 (J6-2), DOUT on IO45 (J6-3), WS on IO3 (J6-9). All three are ESP32-S3 strapping pins; LOW is the
     correct level for each at reset.
   - Pull-downs: 100k on BCLK and DOUT (R5, R6), **10k on WS (R7)**. No pull-ups anywhere (strap rule).
   - R7 is 10k, not 100k, so it doubles as the presence detect: it outweighs the ESP32's ~45k internal pull-up on IO3
     (about 0.6 V, a clean LOW). Changed 2026-11-09, before any order; layout, gerbers and CPL are unchanged.
4. **Headers: only the used pins get metal.**
   - J1 is a 1x4 on J6 pins 1-4: GND, BCLK, DOUT, GND.
   - J2 is a 1x1 on J6-9 (WS).
   - J3 is a 1x1 on J6-12 (VBAT).
   - Standard 2.54 mm straight male headers with an 11.5 mm pin: 2.5 body, 6.0 post, 3.0 tail. Same family as the light
     attachment: Hong Cheng HC-PZ254-11.5L-1x1PZ is LCSC C27985186; find the 1x4 in the same series. Hand-soldered.
   - Not in the JLC CPL, but listed in bom.csv with LCSC codes and links.
   - The full 2x6 header suggested in the research is rejected.
5. **No Bluetooth hardware on rev A**, and no DNP tap either.
   - The only no-firmware module (KCX_BT_EMITTER) is unverified: no datasheet, pad pitch unknown, uncertified, no
     auto-off, and JLC can't assemble it.
   - A battery-powered 3.5 mm Bluetooth transmitter plugged into the jack works today.
   - Integrated Bluetooth is a documented follow-up; see research/bluetooth.md.
6. **Mechanics:**
   - Reuse the rev C base from silkscreen-light-attachment, already copied into housing/src. The owner printed it and
     likes the fit and snap.
   - Change only the left screw boss, moving it from x 10.00 to **x 12.00** to make room for the jack and the lid's
     screw column.
   - New lid: no hood, a closed rounded cap over the board, and a plug opening at the LEFT end (-X).
   - Same board height, so the same J6 engagement (4.72-5.05 mm).
   - Plug from the side (-X) so the reader can lie flat on its back with headphones plugged in. A rear exit would point
     the plug into the table.

## 1. Frames and fixed interface numbers (enclosure frame E, mm)
**Frame E:**
- X = main-board KiCad X - 44.24; Y = 148.25 - KiCad Y (+Y up, the device's top edge); Z = 0 at the main-PCB rear
  face, +Z toward the reader.
- Case: top face y 115.60; sides x -4.09 / 64.09; front face z 6.00; back face z -6.70.
- J6 face: y 112.82..113.15. J6 contacts: x = 44.502 + 2.54 k. Pins 1-6 at z -3.81 (outer row), pins 7-12 at z -1.27
  (row next to the board).

**PCB:**
- 2 layers, 1.0 mm FR4.
- Outline x **-2.50..62.50**, z **-6.00..6.00**, corners R2.0.
- Underside **y 116.60** (it rests on the base's 1.0 mm floor); top y 117.60.
- **Components on TOP (+Y)**, so all SMD sits on one side.
  - Recommended KiCad mapping: F.Cu = top (+Y), x_K = X + 100, y_K = Z + 100.
  - Derive it, prove it is a proper rotation (not a mirror) and gate it: transform pad centres to E and assert them,
    and check that the E-frame STEP has the header bodies below y 116.60 and the tails above y 117.60.
- **THT headers go in from the underside**, with bodies under the board: on B.Cu if F.Cu is the top.
- **Header pads** are named by the J6 pin they mate with:

| Ref | Pad | E (X, Z) | Net |
|---|---|---|---|
| J1 | 1 | (44.502, -3.810) | GND |
| J1 | 2 | (47.042, -3.810) | I2S_BCLK |
| J1 | 3 | (49.582, -3.810) | I2S_DOUT |
| J1 | 4 | (52.122, -3.810) | GND |
| J2 | 9 | (49.582, -1.270) | I2S_WS |
| J3 | 12 | (57.202, -1.270) | VBAT |

- **No pad and no hole** within 1.0 of J6 positions 5 (54.662, -3.81), 6 (57.202, -3.81), 7 (44.502, -1.27),
  8 (47.042, -1.27), 10 (52.122, -1.27) or 11 (54.662, -1.27). Route VBAT away from 6 and 11.
- **Mounting holes:** NPTH Ø4.80 at **(12.00, -1.00)** and **(38.00, -1.00)**, with no copper within 0.4.
- **Lid screw-column keep-out:** no top-side part within a 3.2 radius of either hole centre.
- **Jack J4:** Shou Han PJ-313D, LCSC C668608. SMD, 14 L x 6 W x 5 H.
  - On the top side, axis along X, plug entry (the nose) toward -X.
  - **Nose tip at x -5.34** (flush with the cap's outer left face), **centred at z 0.00**.
  - Footprint (EasyEDA AUDIO-SMD_PJ-313D-2, origin at the footprint centre):
    - 6 pads, 2.50 x 1.25, at axis positions -3.36 / -0.14 / +3.36 from the origin, in two rows +-3.60 across the
      axis;
    - body silk from -5.17 to +6.34 along the axis, x +-3.0 across;
    - nose from -7.65 to -5.16, +-2.5 across.
  - In E that puts the origin at x = -5.34 + 7.65 = **2.31**, the pads at x -1.05 / 2.17 / 5.67 (+-0.63), z +-3.60
    (+-1.25), and the body at x -2.84..8.65, z -3.0..3.0, y 117.60..122.60.
  - **Tip = left (HP_L), ring = right (HP_R), sleeve = GND.** Take the pad-to-contact mapping from the C668608
    datasheet PDF or the EasyEDA symbol and record the source. The research could not verify it, so this is the top
    risk: derive it from two views.
- **Other SMD parts:**
  - top side only, height <= 1.3, in the region x 9.0..62.0, z -5.5..5.5;
  - outside the screw-column keep-outs, and >= 0.5 from header pads;
  - the header tails (3.0 tail, 2.0 above the top) need 0.5 clearance.
- **Underside:** nothing except the header bodies.
- **Circuit:** exactly research/audio-chain.md section 1.1 (U1 LDO, U2 PCM5102A, U3 TPA6138A2, D1 BAT54S detector,
  R1-R15, C1-C22), renumbered only where the connector refs change (J1-J3 headers, J4 jack).
  - Fields: DigiKey-primary Value/MPN/Manufacturer with a separate LCSC field.
  - Basic parts as listed.
- **Layout:** both layers have a ground pour. Keep DAC_L/DAC_R and HP_L/HP_R short and away from BCLK. Place the
  decoupling caps at their pins. Put the detector next to J2.
- **Silk (top):** name, "rev A", L/R near the jack, and labels by J6 pin. Minimum 0.15 line and 1.0 text.
- **Gates (make_outputs refuses to write production files if any fails):**
  - ERC 0;
  - DRC 0 with schematic parity and no exclusions;
  - handedness/positions as above;
  - no pads near the unused J6 positions;
  - field sync;
  - NPTH webs >= 0.5;
  - silk minimums;
  - JLC BOM/CPL: top-side SMD only, headers excluded and listed in bom.csv.
- **Outputs:**
  - production/: gerbers + zip, bom.csv (DigiKey, LCSC, Assembly), jlc_bom.csv, jlc_cpl.csv;
  - docs/: schematic and layout PDFs, renders, design_summary.md;
  - board STEP, plus an **E-frame PCBA STEP/STL**;
  - **build/geometry.json** in E: outline, holes, part boxes including the jack body and nose, header pins and bodies,
    underside/top Y.

## 2. Housing (CadQuery; enclosure venv python)
- **Base:** the rev C base, unchanged, except the left boss moves to (12.00, -1.00), along with its pilot and anything
  keyed to it. The case-gripping skirt, ridges, X guides, floor, seam rabbet, bosses and blind pilots all keep their
  sizes.
- **Lid:** a new audio lid.
  - No hood. It closes the board on every side, so no board edge shows, except for the plug opening.
  - Front face just in front of the base's front (about z 7.4-8.0), with a rounded top-front edge in the case's style
    (R1.8-2.5). Back and ends rounded the same way as rev C; front-view corners like rev C.
  - Roof underside >= 0.3 above the jack top (122.60) and the header tails (119.60). The roof may be flat; top about
    124.1 (about 8.5 above the case top).
  - Screws: 2 x M2x3 pan from the top, clamping on the PCB top (y 117.60) as in rev C. The head sits in a deep Ø4.4
    counterbore whose floor is set so a 3 mm screw ends 0.1 above the blind pilot's skin.
  - Seam: the rev C rabbet over the base.
  - Plug opening in the left end wall, coaxial with the jack barrel. Take the barrel centre height from the PJ-313D
    drawing/model; it is roughly 2.5 above the board top. Make it about Ø6.5, and let a plug body of Ø9 x 20 mm seat
    fully without touching the case.
- **Checks:**
  - keep: seated, fit (against geometry.json and the E-frame STL), seam, pins (engagement), screws, keepout (SW10:
    nothing at z < 2.0 below y 107 on the right), sweep, print;
  - add: plug (opening coaxial with the jack within 0.2; the plug body envelope clears the case and the lid);
  - drop: the light, view and hood checks.
- **Outputs:** print STL/STEP, plate.3mf, renders (iso on the case, left-end view of the jack opening, front, a section
  through the jack, exploded) and REPORT.md.
- **Slicing:** OrcaSlicer CLI only, no supports. Never open a slicer GUI window.

## 3. Firmware (docs only; the firmware repo is not changed)
research/audio-chain.md section 7: I2S std mode, 44.1/48 kHz, 32-bit slots, no MCLK. Pins:
- BCLK GPIO46;
- DOUT GPIO45;
- WS GPIO3.

Behaviour:
- send >= 250 ms of zeros before audio;
- to stop: fade, send >= 50 ms of zeros, stop I2S, then drive the three pins LOW;
- never call gpio_reset_pin() on them;
- volume in software.

Provide a minimal tone-test example in docs.

## 4. Docs
- README: what it is, status "rev A, designed and CAD-checked, not built", what you need, how it attaches, and safety:
  - plug in with the attachment's cap on;
  - P+ is drawn only while audio plays;
  - while USB charges and audio plays, the charger won't terminate.
- Also: ORDERING (JLC fields, header part numbers and links, screws, print), ASSEMBLY, FIRMWARE-NOTES and
  BLUETOOTH-FOLLOWUP (a summary of research/bluetooth.md).
- Keep it short.
