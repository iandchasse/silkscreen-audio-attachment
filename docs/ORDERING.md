# Ordering

## The board (JLCPCB, PCB + Economic PCBA, top side)
**Files** in `pcb/production/`; these three are all JLC needs:
- Fab (Gerbers and drill files): `silkscreen-audio-attachment_rev-A_gerbers.zip`
- BOM: `jlc_bom.csv` (18 lines, 42 parts)
- CPL (placement): `jlc_cpl.csv` (42 top-side placements)

`bom.csv` is the full BOM for you, including the headers and DigiKey notes. Don't upload it.

**Steps:**
1. Upload the Gerber zip on jlcpcb.com and set the PCB fields below.
2. Turn on **PCB Assembly**: Economic, **Top side**, and pick the number of boards to assemble.
3. Upload `jlc_bom.csv` and `jlc_cpl.csv`. All 42 parts should match, with nothing flagged as missing.
4. Check the placement preview (list below) before paying.

**PCB:**

| Field | Value |
|---|---|
| Layers | 2 |
| Dimensions | 65.0 × 13.0 mm |
| Thickness | **1.0 mm** |
| Material | FR-4 |
| Copper | 1 oz |
| Surface finish | LF-HASL (ENIG also fine) |
| Mask colour | any (black looks best under the cap) |
| Silk | white |
| Order number | "Remove order number" (or let JLC place it; the board is hidden) |

**PCBA:**
- Economic, **top side only**. The bottom side has only the headers' plastic bodies, which you fit.
- The headers `J1`-`J3` are not in the BOM/CPL; you solder them.

**Parts, all LCSC.**
- **Basic:** the 37 resistors and capacitors.
- **Extended:** the five parts below. Each costs a $3.07 loading fee per order.

| Ref | Part | LCSC | LCSC stock, 2026-11-09 |
|---|---|---|---|
| U1 | TI TPS7A2033PDBVR, 3.3 V LDO | C2862740 | 117,295 |
| U2 | TI PCM5102APWR, I2S DAC | C107671 | **46** |
| U3 | TI TPA6138A2PWR, headphone driver | C183097 | 3,330 |
| D1 | BAT54S dual Schottky (Changjing) | C8592 | 221,000 |
| J4 | Shou Han PJ-313D, 3.5 mm stereo jack | C668608 | 23,105 |
| R, C | 0603 Basic parts | see `jlc_bom.csv` | plenty |

**If U2 runs out:** DigiKey has none until January 2027, but 46 covers a small order.
- Use the **PCM5101APWR** instead: [LCSC C2667024](https://www.lcsc.com/product-detail/C2667024.html), 2,140 in
  stock, about $0.50 more.
- It's the same TI family on the same datasheet, with the same pins, footprint and three-wire I2S mode. Its 106 dB
  dynamic range (against 112 dB) isn't audible on headphones.
- To use it, change `C107671` to `C2667024` in `jlc_bom.csv`. Nothing else changes.

## Cost
JLC prices and fees were checked on 2026-11-09. Shipping and any import duty are extra.

| Boards assembled | Parts | JLC fees | PCBs | Total | Per board |
|---|---|---|---|---|---|
| 2 | about $5 | $25.06 + $0.40 placement | about $2 (5 made) | **about $33** | about $16 |
| 5 | about $12.60 | $25.06 + $1.00 placement | about $2 | **about $41** | about $8 |
| 10 | about $23.50 | $25.06 + $2.00 placement | about $5 | **about $55** | about $5.50 |

- **Fixed fees per order:** $25.06 in all.
  - Setup $8.18.
  - Stencil $1.53.
  - The five Extended parts at $3.07 each, $15.35.
- **Placement:** $0.0016 per solder joint. That's 124 joints, about $0.20 a board.
- **Parts:** about $2.50 a board. The DAC is about $1.11 of that.
- **Headers** (not assembled): LCSC sells them in 20s (1 × 4, about $0.46) and 50s (1 × 1, about $0.59). Any
  11.5 mm breakaway strip works.
- **Printed parts:** about 7 g of PETG. Screws: 2 × M2 × 3.

**Placement preview checks:**
- `J4`, the jack: its round nose sits at the board's left edge (`L`/`R` silk beside it) and overhangs the edge.
- `U2` and `U3`: the pin-1 dot matches the silk dot.
- `D1` and `U1`: orientation matches the silk.

## Headers (you solder them)
| Ref | J6 pins | Part | LCSC |
|---|---|---|---|
| J1 | 1-4 | Hong Cheng HC-PZ254-11.5L-1x4PZ, 1 × 4 | [C27985189](https://www.lcsc.com/product-detail/C27985189.html) (44,988) |
| J2 | 9 | Hong Cheng HC-PZ254-11.5L-1x1PZ, 1 × 1 | [C27985186](https://www.lcsc.com/product-detail/C27985186.html) (5,114) |
| J3 | 12 | same as J2 | same |

- Any standard 2.54 mm straight breakaway male header works if it has **11.5 mm pins: 6.0 mm mating side, 2.5 mm
  body, 3.0 mm tail**. Snap a 1 × 4 and two 1 × 1 pieces off a strip.
- Don't use long, stacking or round (machined) pins: long ones bottom out in `J6`, and round ones make loose contact.
- The pins should be about 0.6-0.65 mm square.

## Printed parts
- **Files:** `housing/out/print/base.stl`, `lid.stl` (already in print orientation), the matching `.step` files, and
  `plate.3mf`.
- **Material:** PETG, or PLA for a trial fit. No supports.
- **Orientation:** the base prints on its back face, the lid roof-down.
- **Slicer:** turn on "Detect thin wall" (OrcaSlicer) or use Arachne walls. That prints the 0.2 mm stop under each
  screw hole. Without it the holes are just open, which is fine with 3 mm screws.
- **Reference slice** (OrcaSlicer, 0.4 nozzle, 0.20 mm, 3 walls, 30 % infill): base 20 min 21 s / 3.25 g, lid
  12 min 36 s / 3.39 g, no warnings.
- **The base is the light attachment's rev C base,** with the left screw boss moved 2 mm to the right (x 10 → 12).
  It fits the same way, but print this project's `base.stl`: a light-attachment base won't take this board's left
  screw.

## Screws
2 × **M2 × 3** pan head (ISO 7045 or ISO 14583), machine screw or plastic thread-forming. Nothing longer.
