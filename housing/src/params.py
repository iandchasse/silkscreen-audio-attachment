"""Rev C housing numbers, enclosure frame E (mm). Contract: design/DESIGN-SPEC-revB.md (rev C = rev B + enclosing hood,
rounder brow, rabbeted lid/base seam; see the "Rev C" block below).

E: X = main-board KiCad X - 44.24, Y = 148.25 - KiCad Y (+Y = the device's top edge),
Z = 0 at the main-PCB rear face, +Z toward the screen/reader.
"""
import math
import os
from pathlib import Path

HOUSING = Path(__file__).resolve().parents[1]
A = HOUSING.parent
OUT = HOUSING / 'out'
# The case the cap is checked against: the 4.26" case's standard (strip-less) tub + lid in the CAD frame, as built by
# silkscreen-enclosures' enclosures/case-426 (src/build.py, SILKSCREEN_VARIANT=standard). A copy is kept in
# housing/reference/case-426-standard/ (PROVENANCE.md there), so the checks run from a fresh clone. The 3.68" case
# has no J6 and is not supported. Override with SILKSCREEN_CASE_OUT (e.g. a fresh build in
# ../silkscreen-enclosures/enclosures/case-426/out/standard, or the old rev K copy at enclosures/silkscreen-enclosure-claude/out).
STOCK_OUT = Path(os.environ.get('SILKSCREEN_CASE_OUT', A.parent / 'silkscreen-enclosures' / 'enclosures' / 'case-426' / 'out' / 'standard'))
PCB_GEOM = A / 'pcb' / 'build' / 'geometry.json'
OPTICS = A / 'tools' / 'optics_sim.py'

# ------------------------------------------------ stock case (rev K, unmodified; mechanical-spec sec 1)
CASE_TOP = 115.60
CX0, CX1 = -4.09, 64.09               # sides
CZF, CZB = 6.00, -6.70                # front / back faces
CORNER_R, CORNER_CY, CORNER_X = 5.0, 110.6, (0.91, 59.09)     # R5 corners in the X-Y view
FRONT_R, FRONT_C = 1.8, (113.8, 4.2)  # front top edge (y, z centre)
BACK_R, BACK_C = 2.0, (113.6, -4.7)   # back top edge
VFRONT_R, VBACK_R = 1.8, 2.0          # vertical corners (X-Z view), centres x -2.29 / -2.09 (mirrored about 30)
J6_OPEN = dict(x0=42.582, x1=58.922, z0=-5.415, z1=0.215)
J6_FACE = (112.82, 113.15)
E_LIM = (3.7, 6.0)
WIN_EDGE = (109.10, 6.00)             # window top edge at the front face (y, z)
ACTIVE = dict(x0=2.16, x1=57.84, y0=15.10, y1=107.90)
PAGES = {'FT01C': 4.98, 'T01C': 4.41, 'PLAIN': 3.926}
RIGHT_KEEP_Y = 107.0                  # SW10 (slot y 89.8..106.0, z <= 0.6; key proud to x 65.59): below this y the
RIGHT_KEEP_Z = 2.0                    # right side is only touched at z >= 2.0 (mechanical-spec sec 1)

# ------------------------------------------------ PCB interface (fixed by the contract; geometry.json overrides)
PCB_Y0, PCB_T = 116.60, 1.00
PCB_Y1 = PCB_Y0 + PCB_T
HOLES = [(12.00, -1.00), (38.00, -1.00)]   # audio: left boss moved 10 -> 12 (jack + lid screw column)
HOLE_D = 4.80
EMIT_Y, EMIT_Z = 115.90, (8.94, 10.06)     # emitter face and z extent (geometry.json: LED emitter box)

# ------------------------------------------------ housing
CL = 0.05                  # clearance to the case on the sides / front / back (the floor sits on the top face)
T = 1.20                   # wall
XO0, XO1 = CX0 - CL - T, CX1 + CL + T      # outer X -5.34 / 65.34 (one wall wider than the case per side)
ZOB = CZB - CL - T                          # outer back -7.95
Y_BOT = 107.0              # skirt bottom (= the SW10 limit on the right; same all round for simplicity)
# X guides: at each front corner the skirt (flat side + the wrap round the vertical corner) runs on down to FIN_Y; its
# rear edge rises at 45 deg from (Y_BOT, FIN_Z) so it prints without support (base printed on its back face, +z up)
# and stays at z >= 2.0 below y 107 (SW10). Rounded in the side view: fillet FIN_RC at the skirt, FIN_RV at the tip.
FIN_Y, FIN_Z, FIN_RC, FIN_RV = 103.5, 2.45, 1.0, 1.5
FLOOR_TOP = PCB_Y0         # 116.60: floor 1.0 on the case top
LID_BOT = FLOOR_TOP + 0.10 # lid rim 0.10 above the base: the clamp goes through the PCB
TAIL_CLR, SKIN = 0.30, 0.60
# LID_TOP = tail tip + clearance + skin (set in parts.py from geometry.json; 119.6 + 0.3 + 0.6 = 120.5)
PCB_GAP = 0.30             # lid wall to the PCB edge (> the 0.2 float on the bosses)
VISOR_Z0 = 11.0 + PCB_GAP  # reflector face starts here, at the PCB underside: z 11.30
BROW_Z = 7.40              # lid parts below the rim stay in front of this (the base's corner wraps end at 7.25)
TOP_R_BACK = 2.0           # cap top-back edge, same radius as the case
XY_R = CORNER_R + CL + T   # 6.25: cap corners in the X-Y view (concentric in x with the case R5)
XZ_R_BACK = VBACK_R + CL + T                # 3.25, concentric with the case's back vertical corner

# ------------------------------------------------ Rev C: hood, rounder brow, rabbeted seam
# Hood: the lid's front wall now runs from the roof down to HOOD_LIP_Y in front of the LED row, with closed ends. Its inner
# face is a flat reflector plane from (y 116.60, z 11.30) flared HOOD_FLARE deg away from the case down to the lip.
HOOD_LIP_Y = 110.50                         # hood lip (bottom edge); never below 110.0 (view of the screen top)
HOOD_FLARE = 20.0                           # deg from vertical, the lower edge further from the case
HOOD_Z_LIP_IN = VISOR_Z0 + (PCB_Y0 - HOOD_LIP_Y) * math.tan(math.radians(HOOD_FLARE))   # inner face z at the lip, 13.52
HOOD_WALL = 1.6                             # wall at the lip
Z_FRONT = round(HOOD_Z_LIP_IN + HOOD_WALL, 2)   # outer front face (vertical): 15.12, 9.1 in front of the case face
# Outer profile, a print-friendly rounded brow (the lid prints roof-down; nothing steeper than 45 deg from vertical except
# the small bed-edge round): vertical front -> R_KNEE -> 45 deg bevel of leg HOOD_CHAMFER -> R_ROOF -> roof.
HOOD_CHAMFER, HOOD_R_KNEE, HOOD_R_ROOF, HOOD_R_LIP = 4.5, 8.0, 2.0, 0.8
XZ_R_FRONT_LID = 3.75                       # plan radius of the hood's front corners (the case's own corners are R1.8-R5)
# Seam: the base's top outer edge is stepped in (rabbet) by RAB for the floor's thickness; the lid wall slides over it with
# RAB_CL clearance all round and RAB_CL_V above the shoulder, outer faces flush.
RAB, RAB_CL, RAB_CL_V = 0.80, 0.10, 0.15
WRAP_R = VFRONT_R + CL + T                  # 3.05: base corner wraps round the case's front vertical corners

# front jaw (base) over the window: flat contact band on the front face, outer face on the grazing ray
JAW_Y0 = 112.60
LED_CLR_Z = 8.50           # base stays behind the LED bodies (z 8.8)
LIGHT_MARGIN = 0.20        # perpendicular margin to the grazing ray

# bosses / screws: 2 x M2 x 3 pan head (ISO 7045 cross / ISO 14583 hexalobular: dk <= 4.0, k <= 1.6), machine screw or
# thread-forming for plastics; either one cuts its own thread in the printed pilot (M2 tap-drill size 1.6)
BOSS_D, PILOT_D, BOSS_TOP = 4.40, 1.60, 118.10
PILOT_SKIN = 0.20          # pilots are BLIND: 0.2 of floor stays under them, so no screw can reach the case top
PILOT_BOT = CASE_TOP + PILOT_SKIN          # 115.80
RECESS_D, RECESS_TOP = 4.80, 118.20
CLR_D, CB_D, HEAD_K = 2.50, 4.60, 1.60     # counterbore floor = lid top - HEAD_K: a k-max head sits flush
SCREW = dict(name='M2 x 3 pan head, ISO 7045 (cross) or ISO 14583 (hexalobular); machine screw or thread-forming for '
                  'plastics', d=2.0, L=3.0, pitch=0.4, head_d=4.0, head_k=1.6, L_tol=0.2)
TIP_MARGIN_MIN = 0.05      # nominal 3 mm screw tip must stop this far above the pilot bottom (head seats first)

# snap bumps: ridges on the back jaw's inner face (0.10 interference with the case back face)
BUMP = dict(r=0.60, y=108.20, proud=CL + 0.10, xs=[(8.0, 16.0), (46.0, 54.0)])

# checks
EPS_VOL = 2e-3
MIN_WALL = 1.20
OVERHANG_DEG = 50.0
BRIDGE_OK_W = 3.0
PLAY_OK = 0.35             # lateral play allowed when the post tips reach the J6 face (receptacle lead-in)
X_PLAY_OK = 0.12           # X play target at that moment (the X guides engage before the pins arrive)


# ================================================================== AUDIO ATTACHMENT (design/DESIGN-SPEC.md sec 1-2)
# Base = rev C base, unchanged except the left boss (HOLES above). It is built with its rev C outline numbers
# (BASE_TOP_REF = the rev C lid top, which fixes the R6.25 X-Y corner arcs) so it stays identical to the printed one.
BASE_TOP_REF = 120.50
# PJ-313D jack (E frame): body x -2.84..8.65, z -3..3, y 117.60..122.60; nose dia 5 x -5.34..-2.84 on the axis
JACK_BODY = dict(x=(-2.84, 8.65), y=(117.60, 122.60), z=(-3.0, 3.0))
JACK_NOSE = dict(x=(-5.34, -2.84), dia=5.0, axis_y=120.10, axis_z=0.0)     # axis 2.5 above the board top (spec; geometry.json overrides)
ROOF_CLR = 0.30            # roof underside above the jack top / header tails
ROOF_T = 1.20              # roof thickness
OPEN_D = 6.5               # plug opening (circle), coaxial with the jack barrel; a straight slot runs from it to the lid's lower edge
Z_FRONT_AUDIO = 8.50       # lid front face: flush with the base's front tongue (checked in build.py)
R_TOP_FRONT = 2.2          # top-front edge (case style R1.8-2.5)
R_END = 0.6                # X-Y top edge round at the two ends (the jack opening top is at y 123.35: no room for more)
COL_R = 3.0                # lid screw column radius (the spec's top-side keep-out is 3.2; 0.2 clear of it and of the jack when the board floats 0.19)
CB_D = 4.40                # deep counterbore for the M2x3 pan head (dk 4.0)
TIP_ABOVE_SKIN = 0.10      # a 3 mm screw ends this far above the blind-pilot skin
PAD_DEPTH = 0.30           # flat pad on the lid's left end face, behind the nose tip, so a plug body never touches the lid
PAD_HALF_Z = 4.90
PLUG = dict(body_d=9.0, body_l=20.0, tip_d=3.5)     # test plug: dia 9 x 20 body seated against the nose tip, dia 3.5 tip in the jack
SMD_H = 1.30
