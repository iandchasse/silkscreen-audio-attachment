"""Single source of numbers for the silkscreen-audio-attachment PCBA (rev A).

Mirrors design/DESIGN-SPEC.md (the contract) and research/audio-chain.md sec 1.1 (the netlist).  Mechanical numbers
are in the ENCLOSURE frame E (mm):
    X = main-board KiCad X - 44.24,   Y = 148.25 - main-board KiCad Y (+Y = device top edge),
    Z = 0 at the main-PCB rear face, +Z toward the screen/reader.
The audio PCB lies in E's X-Z plane with its COMPONENT side (F.Cu) facing +Y (up the device).  Its KiCad frame K:
    x_K = X + 100,   y_K = Z + 100                     (see tools/check_handedness.py for the proof)
Viewed from +Y (looking down -Y) E's X runs right and Z runs down the screen, so the F.Cu view is unmirrored, and the
kicad-cli STEP frame (x_s = x_K, y_s = -y_K, z_s = height above the F.Cu face) maps to E by the proper rotation
(X, Y, Z) = (x_s - 100, Y0 + z_s, -y_s - 100) (det +1).
THT headers go in from the underside: their footprints sit on B.Cu (bodies under the board, tails through to the top).
"""
from __future__ import annotations

PROJECT = "silkscreen-audio-attachment"
REVISION = "A"
DATE = "2026-11-09"
COMPANY = "idc LLC"
TITLE = "Silkscreen audio attachment"

# ------------------------------------------------------------------ frames
K_OX = 100.000          # x_K = X + K_OX
K_OY = 100.000          # y_K = Z + K_OY


def to_k(X, Z):
    """Enclosure (X, Z) -> audio-PCB KiCad (x_K, y_K)."""
    return (X + K_OX, Z + K_OY)


def to_e(xk, yk):
    """Audio-PCB KiCad (x_K, y_K) -> enclosure (X, Z)."""
    return (xk - K_OX, yk - K_OY)


# ------------------------------------------------------------------ stack (E, Y)
HDR = {
    "body_h": 2.50, "post": 6.00, "tail": 3.00, "post_sq": 0.64, "body_w": 2.50, "pitch": 2.54,
    "drill": 1.02, "pad": 1.70,
    "source": "LCSC/JLC product attributes 2026-11-09 (insulation height 2.5 mm, mating pin 6 mm, end pin 3 mm, square "
              "pin, brass, gold, 1x4 = C27985189, 1x1 = C27985186); total 11.5 mm from the MPN; 0.64 mm square pin "
              "assumed (not listed)",
}
STACK = {
    "pcb_t": 1.000,
    "underside_y": 116.60,       # B.Cu face: rests on the housing base's 1.0 floor, on the case top (115.60)
    "top_y": 117.60,             # F.Cu face (components)
}
STACK["body_bottom_y"] = round(STACK["underside_y"] - HDR["body_h"], 4)             # 114.10 (header body bottom)
STACK["post_tip_y"] = round(STACK["body_bottom_y"] - HDR["post"], 4)                # 108.10
STACK["tail_tip_y"] = round(STACK["underside_y"] + HDR["tail"], 4)                  # 119.60 (2.0 above the top)
J6_FACE_Y = (112.82, 113.15)
ENGAGEMENT_LIMITS = (3.7, 6.0)

# ------------------------------------------------------------------ outline (E): rounded rectangle
OUTLINE = {"x0": -2.50, "x1": 62.50, "z0": -6.00, "z1": 7.00, "r": 2.0}   # z1 6.00 -> 7.00 (2026-11-09 routing room)

# ------------------------------------------------------------------ holes (E, all NPTH)
HOLES = [
    # (name, dia, X, Z, purpose)
    ("M1", 4.80, 12.00, -1.00, "lid screw column (rev C base, left boss moved to x 12)"),
    ("M2", 4.80, 38.00, -1.00, "lid screw column"),
]
HOLE_COPPER_CLEAR = 0.40        # no copper within 0.40 of an M1/M2 edge
HOLE_TRACE_CLEAR = 0.50
COLUMN_KEEPOUT = 3.20           # no top-side part within 3.2 of either hole centre (courtyard box)
COLUMN_CRTYD = 0.40
EDGE_WEB_MIN = 0.50

# ------------------------------------------------------------------ J6 (E)
J6 = {
    "pitch": 2.54,
    "pins": {1: (44.502, -3.810), 2: (47.042, -3.810), 3: (49.582, -3.810), 4: (52.122, -3.810),
             5: (54.662, -3.810), 6: (57.202, -3.810),
             7: (44.502, -1.270), 8: (47.042, -1.270), 9: (49.582, -1.270), 10: (52.122, -1.270),
             11: (54.662, -1.270), 12: (57.202, -1.270)},
}
HEADERS = {
    # ref: {pads {J6 pin name: (X, Z)}, nets, part data}
    "J1": {"pads": {"1": (44.502, -3.810), "2": (47.042, -3.810), "3": (49.582, -3.810), "4": (52.122, -3.810)},
           "nets": {"1": "GND", "2": "I2S_BCLK", "3": "I2S_DOUT", "4": "GND"}, "positions": 4,
           "mpn": "HC-PZ254-11.5L-1x4PZ", "manufacturer": "Hong Cheng", "lcsc": "C27985189", "stock": 44988,
           "digikey": "n/a - Hong Cheng is LCSC-only; DigiKey equivalent: Harwin M20-999 series 1x4 cut from a longer strip "
                      "(6.1 mm post, 3 mm tail), part number not verified",
           "datasheet": "https://www.lcsc.com/product-detail/C27985189.html"},
    "J2": {"pads": {"9": (49.582, -1.270)}, "nets": {"9": "I2S_WS"}, "positions": 1,
           "mpn": "HC-PZ254-11.5L-1x1PZ", "manufacturer": "Hong Cheng", "lcsc": "C27985186", "stock": 5114,
           "digikey": "1 pin cut from a Harwin M20-999 series strip (6.1 mm post, 3 mm tail), part number not verified",
           "datasheet": "https://www.lcsc.com/product-detail/C27985186.html"},
    "J3": {"pads": {"12": (57.202, -1.270)}, "nets": {"12": "VBAT"}, "positions": 1,
           "mpn": "HC-PZ254-11.5L-1x1PZ", "manufacturer": "Hong Cheng", "lcsc": "C27985186", "stock": 5114,
           "digikey": "1 pin cut from a Harwin M20-999 series strip (6.1 mm post, 3 mm tail), part number not verified",
           "datasheet": "https://www.lcsc.com/product-detail/C27985186.html"},
}
HDR_JLC_TYPE = "JLC Extended (no Basic 2.54 mm headers are listed; checked 2026-11-09)"
# JLC Basic parts (no loading fee), from the JLC library flags on 2026-11-09. Everything else is Extended
# (U1, U2, U3, D1, J4: one $3.07 loading fee each per order).
JLC_BASIC = {"C19702", "C15849", "C57112", "C14663", "C23630", "C1604", "C1588",
             "C21190", "C22935", "C25803", "C25804", "C23179", "C22859"}
# J6 positions with no pad and no hole within 1.0 (spec sec 1)
FORBIDDEN = {5: "LED_SW up to 25.5 V", 6: "W-", 7: "J6_3V3", 8: "SDA", 10: "SCL", 11: "C-"}
FORBID_R = 1.00
HANDEDNESS_TOL = 0.02


def header_body(ref):
    pads = list(HEADERS[ref]["pads"].values())
    xs = [p[0] for p in pads]
    z = pads[0][1]
    h = HDR["pitch"] / 2
    return (round(min(xs) - h, 4), round(max(xs) + h, 4), round(z - HDR["body_w"] / 2, 4), round(z + HDR["body_w"] / 2, 4))


def header_centre(ref):
    b = header_body(ref)
    return (round((b[0] + b[1]) / 2, 4), round((b[2] + b[3]) / 2, 4))


# ------------------------------------------------------------------ jack J4: Shou Han PJ-313D, EasyEDA AUDIO-SMD_PJ-313D-2
# EasyEDA frame (y down, 0.254 mm per unit, origin = footprint centre).  Nose toward -y; pads 1,2,3 from the nose.
JACK = {
    "mpn": "PJ-313D", "manufacturer": "SHOU HAN", "lcsc": "C668608", "stock": 23114,
    "digikey": "none (LCSC only); DigiKey alternative with a different land: CUI SJ-3524-SMT-TR",
    "datasheet": "https://www.lcsc.com/datasheet/lcsc_datasheet_2006181822_SHOU-HAN-PJ-313D_C668608.pdf",
    "pad_w": 2.50, "pad_h": 1.25, "pad_x": 3.60, "pad_y": {"1": -3.355, "2": -0.145, "3": 3.356},
    # pad "1" = sleeve (GND, nearest the plug entry), "2" = ring (HP_R), "3" = tip (HP_L, deepest)
    "nets": {"1": "GND", "2": "HP_R", "3": "HP_L"},
    "body_y": (-5.17, 6.34), "body_x": 3.0, "nose_y": (-7.65, -5.16), "nose_d": 5.0, "bore_d": 3.6, "height": 5.0,
    "axis_h": 2.5,                      # barrel axis height above the PCB top (drawing: bore centre 2.5 above the pads)
    "pegs": [(0.0, -2.655), (0.0, 3.358)], "peg_d": 1.30,
    "X": 2.31, "Z": 0.00, "rot": 90,    # origin in E; footprint rot 90 => nose toward -X
    "nose_tip_x": -5.34,
}

# ------------------------------------------------------------------ parts (research/audio-chain.md sec 1.1)
RES = {
    "1k": dict(mpn="0603WAF1001T5E", lcsc="C21190", desc="1 kOhm 1 % 0603"),
    "10k": dict(mpn="0603WAF1002T5E", lcsc="C25804", desc="10 kOhm 1 % 0603"),
    "100k": dict(mpn="0603WAF1003T5E", lcsc="C25803", desc="100 kOhm 1 % 0603"),
    "1M": dict(mpn="0603WAF1004T5E", lcsc="C22935", desc="1 MOhm 1 % 0603"),
    "470R": dict(mpn="0603WAF4700T5E", lcsc="C23179", desc="470 Ohm 1 % 0603"),
    "10R": dict(mpn="0603WAF100JT5E", lcsc="C22859", desc="10 Ohm 0603"),
}
for _k, _v in RES.items():
    _v.update(manufacturer="UNI-ROYAL", prefix="R")
CAP = {
    "10uF": dict(mpn="CL10A106KP8NNNC", lcsc="C19702", manufacturer="Samsung Electro-Mechanics", desc="10 uF 10 V X5R 0603"),
    "2.2uF": dict(mpn="CL10A225KO8NNNC", lcsc="C23630", manufacturer="Samsung Electro-Mechanics", desc="2.2 uF 16 V X5R 0603"),
    "1uF": dict(mpn="CL10A105KB8NNNC", lcsc="C15849", manufacturer="Samsung Electro-Mechanics", desc="1 uF 50 V X5R 0603"),
    "100nF": dict(mpn="CC0603KRX7R9BB104", lcsc="C14663", manufacturer="Yageo", desc="100 nF 50 V X7R 0603"),
    "10nF": dict(mpn="0603B103K500NT", lcsc="C57112", manufacturer="Fenghua (FH)", desc="10 nF 50 V X7R 0603"),
    "2.2nF": dict(mpn="0603B222K500NT", lcsc="C1604", manufacturer="Fenghua (FH)", desc="2.2 nF 50 V X7R 0603"),
    "1nF": dict(mpn="CL10B102KB8NNNC", lcsc="C1588", manufacturer="Samsung Electro-Mechanics", desc="1 nF 50 V X7R 0603"),
}
for _k, _v in CAP.items():
    _v.update(prefix="C")

# ref -> (class, {pin: net}).  Net names are the research names (+ explicit names for the helper nodes).
PASSIVES = {
    "R1": ("1k", {"1": "I2S_WS", "2": "PUMP_A"}),
    "R2": ("1M", {"1": "EN_DET", "2": "GND"}),
    "R3": ("100k", {"1": "EN_DET", "2": "MUTE_RC"}),
    "R4": ("10k", {"1": "MUTE_RC", "2": "AMP_MUTE"}),
    "R5": ("100k", {"1": "I2S_BCLK", "2": "GND"}),
    "R6": ("100k", {"1": "I2S_DOUT", "2": "GND"}),
    "R7": ("10k", {"1": "I2S_WS", "2": "GND"}),   # 10k, not 100k: presence detect against the ESP32 pull-up (2026-11-09)
    "R8": ("470R", {"1": "DAC_OUTL", "2": "DAC_L"}),
    "R9": ("470R", {"1": "DAC_OUTR", "2": "DAC_R"}),
    "R10": ("10k", {"1": "DAC_L", "2": "AMP_INL"}),
    "R11": ("10k", {"1": "AMP_INL", "2": "AMP_OUTL"}),
    "R12": ("10k", {"1": "DAC_R", "2": "AMP_INR"}),
    "R13": ("10k", {"1": "AMP_INR", "2": "AMP_OUTR"}),
    "R14": ("10R", {"1": "AMP_OUTL", "2": "HP_L"}),
    "R15": ("10R", {"1": "AMP_OUTR", "2": "HP_R"}),
    "C1": ("10uF", {"1": "VBAT", "2": "GND"}),
    "C2": ("1uF", {"1": "VBAT", "2": "GND"}),
    "C3": ("10nF", {"1": "PUMP_A", "2": "PUMP"}),
    "C4": ("1uF", {"1": "EN_DET", "2": "GND"}),
    "C5": ("1uF", {"1": "MUTE_RC", "2": "GND"}),
    "C6": ("1uF", {"1": "3V3A", "2": "GND"}),
    "C7": ("100nF", {"1": "3V3A", "2": "GND"}),
    "C8": ("10uF", {"1": "3V3A", "2": "GND"}),
    "C9": ("2.2uF", {"1": "DAC_CAPP", "2": "DAC_CAPM"}),
    "C10": ("2.2uF", {"1": "DAC_VNEG", "2": "GND"}),
    "C11": ("100nF", {"1": "3V3A", "2": "GND"}),
    "C12": ("10uF", {"1": "3V3A", "2": "GND"}),
    "C13": ("100nF", {"1": "DAC_LDOO", "2": "GND"}),
    "C14": ("100nF", {"1": "3V3A", "2": "GND"}),
    "C15": ("10uF", {"1": "3V3A", "2": "GND"}),
    "C16": ("2.2nF", {"1": "DAC_L", "2": "GND"}),
    "C17": ("2.2nF", {"1": "DAC_R", "2": "GND"}),
    "C18": ("1uF", {"1": "3V3A", "2": "GND"}),
    "C19": ("1uF", {"1": "AMP_CN", "2": "AMP_CP"}),
    "C20": ("1uF", {"1": "AMP_VSS", "2": "GND"}),
    "C21": ("1nF", {"1": "HP_L", "2": "GND"}),
    "C22": ("1nF", {"1": "HP_R", "2": "GND"}),
}

ICS = {
    "U1": dict(
        fp="SOT-23-5", sym="TPS7A2033", value="TPS7A2033PDBVR", manufacturer="Texas Instruments", mpn="TPS7A2033PDBVR",
        digikey="296-TPS7A2033PDBVRCT-ND", lcsc="C2862740", stock=122506,
        datasheet="https://www.ti.com/lit/ds/symlink/tps7a20.pdf",
        desc="3.3 V 300 mA ultra-low-noise LDO with enable, SOT-23-5",
        left=[("1", "IN"), ("2", "GND"), ("3", "EN")], right=[("5", "OUT"), ("4", "NC")],
        pins={"1": "VBAT", "2": "GND", "3": "EN_DET", "4": None, "5": "3V3A"}),
    "U2": dict(
        fp="TSSOP-20", sym="PCM5102A", value="PCM5102APWR", manufacturer="Texas Instruments", mpn="PCM5102APWR",
        digikey="296-36707-1-ND", lcsc="C107671", stock=1284,
        datasheet="https://www.ti.com/lit/ds/symlink/pcm5102a.pdf",
        desc="112 dB stereo audio DAC, 32-bit 384 kHz I2S, BCK PLL (no MCLK), TSSOP-20",
        left=[("1", "CPVDD"), ("2", "CAPP"), ("3", "CPGND"), ("4", "CAPM"), ("5", "VNEG"), ("6", "OUTL"), ("7", "OUTR"),
              ("8", "AVDD"), ("9", "AGND"), ("10", "DEMP")],
        right=[("20", "DVDD"), ("19", "DGND"), ("18", "LDOO"), ("17", "XSMT"), ("16", "FMT"), ("15", "LRCK"), ("14", "DIN"),
               ("13", "BCK"), ("12", "SCK"), ("11", "FLT")],
        pins={"1": "3V3A", "2": "DAC_CAPP", "3": "GND", "4": "DAC_CAPM", "5": "DAC_VNEG", "6": "DAC_OUTL", "7": "DAC_OUTR",
              "8": "3V3A", "9": "GND", "10": "GND", "11": "GND", "12": "GND", "13": "I2S_BCLK", "14": "I2S_DOUT",
              "15": "I2S_WS", "16": "GND", "17": "3V3A", "18": "DAC_LDOO", "19": "GND", "20": "3V3A"}),
    "U3": dict(
        fp="TSSOP-14", sym="TPA6138A2", value="TPA6138A2PWR", manufacturer="Texas Instruments", mpn="TPA6138A2PWR",
        digikey="296-28248-1-ND", lcsc="C183097", stock=3332,
        datasheet="https://www.ti.com/lit/ds/symlink/tpa6138a2.pdf",
        desc="DirectPath ground-centred stereo headphone amplifier, TSSOP-14",
        left=[("1", "+INR"), ("2", "-INR"), ("3", "OUTR"), ("4", "GND"), ("5", "MUTE"), ("6", "VSS"), ("7", "CN")],
        right=[("14", "+INL"), ("13", "-INL"), ("12", "OUTL"), ("11", "UVP"), ("10", "GND"), ("9", "VDD"), ("8", "CP")],
        pins={"1": "GND", "2": "AMP_INR", "3": "AMP_OUTR", "4": "GND", "5": "AMP_MUTE", "6": "AMP_VSS", "7": "AMP_CN",
              "8": "AMP_CP", "9": "3V3A", "10": "GND", "11": None, "12": "AMP_OUTL", "13": "AMP_INL", "14": "GND"}),
    "D1": dict(
        fp="SOT-23", sym="BAT54S", value="BAT54SLT1G", manufacturer="onsemi", mpn="BAT54SLT1G",
        digikey="BAT54SLT1GOSCT-ND", lcsc="C8592", stock=221495,
        datasheet="https://www.onsemi.com/pdf/datasheet/bat54slt1-d.pdf",
        desc="Dual Schottky diode, series pair, SOT-23. JLC/LCSC part: Jiangsu Changjing BAT54S (C8592)",
        left=[("1", "A1"), ("3", "COM")], right=[("2", "K2")],
        pins={"1": "GND", "2": "EN_DET", "3": "PUMP"}),
}
# NC pins carry a no-connect flag in the schematic
FP_LIB = {"SOT-23-5": ("Package_TO_SOT_SMD", "SOT-23-5"), "SOT-23": ("Package_TO_SOT_SMD", "SOT-23"),
          "TSSOP-20": ("Package_SO", "TSSOP-20_4.4x6.5mm_P0.65mm"), "TSSOP-14": ("Package_SO", "TSSOP-14_4.4x5mm_P0.65mm"),
          "R": ("Resistor_SMD", "R_0603_1608Metric"), "C": ("Capacitor_SMD", "C_0603_1608Metric")}

# ------------------------------------------------------------------ placement (E: X, Z, KiCad rotation)
# top row z -4.65, bottom row z +4.5, left stacks beside the jack lead, gap column between amp and DAC, right band.
PLACE = {
    "U3": (19.5, 0.0, 270), "U2": (30.9, 0.0, 0),
    "R14": (10.9, 3.1, 0), "C21": (10.9, 5.6, 0), "R15": (13.9, 3.1, 0), "C22": (13.9, 5.6, 0),
    "C19": (16.0, 0.0, 90),
    # top row
    "C20": (14.9, -4.95, 0), "R4": (18.0, -4.95, 0), "R13": (21.1, -4.95, 0), "R12": (24.2, -4.95, 0),
    "C7": (27.3, -4.95, 0), "C8": (30.4, -4.95, 0), "C14": (33.5, -4.95, 0),
    # bottom row
    "C18": (18.0, 5.6, 0), "R11": (21.1, 5.6, 0), "R10": (24.2, 5.6, 0), "C11": (27.3, 5.6, 0), "C12": (30.4, 5.6, 0),
    "C13": (33.5, 5.6, 0), "C16": (36.6, 5.6, 0), "C17": (39.7, 5.6, 0),
    "R5": (42.8, 5.6, 0), "R6": (45.9, 5.6, 0), "R7": (49.0, 5.6, 0), "C15": (53.0, 5.6, 0), "C6": (56.1, 5.6, 0),
    # gap column between amp and DAC
    "C9": (25.9, -1.95, 90), "C10": (23.3, -1.95, 90), "R8": (25.9, 1.95, 90), "R9": (23.3, 1.95, 90),
    # right band
    "R1": (44.0, 0.9, 0), "C3": (47.1, 0.9, 0), "C4": (54.0, 0.9, 0), "R2": (57.1, 0.7, 0),
    "R3": (43.0, 2.6, 0), "C5": (46.1, 2.6, 0), "D1": (51.0, 2.2, 0), "C2": (55.2, 2.6, 0),
    "U1": (60.2, 3.3, 0), "C1": (61.2, -1.5, 90),
}

# ------------------------------------------------------------------ rules (JLC standard 2-layer)
RULES = {
    "clearance": 0.15, "track_min": 0.20, "via_pad": 0.60, "via_drill": 0.30, "via_pad_min": 0.55, "via_drill_min": 0.25, "edge_clearance": 0.30,
    "hole_clearance": 0.25, "hole_to_hole": 0.50, "silk_text_h": 1.00, "silk_line_w": 0.15,
    "mask_expansion": 0.05, "min_annular": 0.13,
}
ROUTE = {"track": 0.20, "grid": 0.05, "zone_clearance": 0.20}
BOARD = {"layers": 2, "thickness": 1.0, "mask": "Black (any colour is fine)", "silk": "White",
         "finish": "LF-HASL or ENIG", "copper_oz": 1}

# gate regions (E): other SMD parts (pads + body) in x 9..62, z -5.5..5.5, height <= 1.3
PART_REGION = (9.0, 62.0, -5.5, 6.5)
PART_MAX_H = 1.30
HDR_CLEAR = 0.50

DEVIATIONS = [
    "The PJ-313D footprint carries its two Ø1.3 positioning pegs (EasyEDA HOLE records) as NPTH holes at footprint (0, -2.655) "
    "and (0, +3.358), i.e. E (-0.345, 0) and (5.668, 0): the board has 4 NPTH holes (2 x Ø4.80 screw columns + 2 x Ø1.30 "
    "jack pegs), not 2.",
]
