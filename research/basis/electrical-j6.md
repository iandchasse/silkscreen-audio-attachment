# The expansion header (J6) as an external-light port: electrical characterisation

Main-board parts named here: J6 is the expansion header and J3 the frontlight connector; U10 is the frontlight driver,
with L2 its inductor, C12 its input and C9 its output capacitor; R37 is the current-set resistor; Q5/Q6 the warm/cool
string switches; R49/R50 the string bleeders; R39/R41/C31 the monitor divider; R75 the colour-select pull-down and U12
its inverter; D3/D8 the frontlight clamps; U8 the header's ESD array; CR2 the 3V3-pin clamp; F2 the battery pin's fuse.

Research notes, 2026-09-25. INFERRED = my calculation or a generic assumption, not a source value.

Source key:
- [HW] `de-link_pcb/docs/HARDWARE.md` (line numbers). [RM] `de-link_pcb/README.md`. [DR] `de-link_pcb/DESIGN_REVIEW.md`.
- [SCH] `de-link_pcb/silkscreen_pcb.kicad_sch` (symbol start line). [PCB] `de-link_pcb/silkscreen_pcb.kicad_pcb`, pad nets read with python.
- [TI] TPS923610/1/2 datasheet SNVSCN8A (Sep 2025, rev Oct 2025), https://www.ti.com/lit/ds/symlink/tps923610.pdf, re-extracted 2026-09-25 (page numbers).
- [LS] `silkscreen-light-strip/docs/research/electrical-limits.md` (same driver, J3 strip).
- [FW] `silkscreen-firmware` at 3323681f (paths below).
- Calcs: python run in the scratchpad (generic LED classes below). Every calc result is INFERRED.

## Key numbers

| Item | Value | Source |
|---|---|---|
| J6 light pins | 5 = LED_SW (anode), 6 = W-, 11 = C-; pin 4 = GND right beside pin 5 | [PCB] |
| String current (one string at a time) | 200 mV / 15 R = 13.33 mA nom; 13.87 mA max (ref + 1 %); 13.96 mA with 60 C drift | [TI p5], [SCH:25926], [DR:405] |
| VIN (LDO_IN) | 3.0-5 V normal; up to 5.5 V on USB-C; 6-7.4 V hot-plug ringing for tens of us (model) | [HW:149,210-220], [TI p4] |
| OVP rising, TPS923610 | 24.25 / 25 / 25.5 V (TJ <= 85 C), 1 V hysteresis; latches after 3 trips | [TI p5-6, p12] |
| OVP rising, TPS923611 (swap part) | 29.6 / 30.5 / 31.4 V | [TI p6], [RM:239-245] |
| VOUT recommended | 5-24.5 V (610), 5-30 V (611); abs max 32 V | [TI p4], [LS:61-62] |
| Switch ILIM / start-up ILIM | 1.6 / 1.8 / 2.1 A; 0.8 A during soft start | [TI p6] |
| C9 | 4.7 uF/50 V 0805 X5R nameplate, ~1-2.5 uF effective at 15-24 V | [SCH:28446], [HW:813-825] |
| D3 SMAJ26A on LED_SW | starts conducting at 28.9 V (VBR min) | [RM:245], [SCH:28969] |
| **Recommended string** | **N = 5 LEDs per colour, + Rs = 120 R (100-150 R), + one BAW56-class dual diode (block + clamp)** | INFERRED, sections 3-5 |
| Worst VOUT, N=5 + 120 R + diode | 18.8-20.3 V (-10 C, max bin), 4.0-5.5 V under OVP min | INFERRED |
| Hot-plug peak, C9 at OVP into N=5 | 150-310 mA with no Rs; 60-77 mA with 120 R (TPS923611: 90-114 mA) | INFERRED |
| C9 decay after OVP latch, no load | tau = 1.12 M x C9 = 2.8-5.3 s; about 4-8 s to fall to 6 V | [LS:233], INFERRED |
| LED_MONIT ratio | 120 k / 1.12 M = 0.1071; open-load reads 2.60-2.73 V | [SCH:36658,41066], [LS:193] |

## 1. J6 pin table

J6 is a Sullins PPPC062LJBN-RC 2x6 0.1" right-angle female header on B.Cu [SCH:31030], [PCB]. Pad nets come from
[PCB] and match [HW:1116-1121]. Row A holds pins 1-6 (y = 0) and row B holds pins 7-12 (y = -2.54 mm, footprint coordinates).
Pin k sits beside pin k+6.

| Pin | Net | Voltage | Notes |
|---|---|---|---|
| 1 | GND | 0 | |
| 2 | UNUSED_GPIO_46 | 0-3.3 V | strap pin, must be LOW at reset, 33 R series [HW:1169-1176] |
| 3 | UNUSED_GPIO_45 | 0-3.3 V | strap pin: HIGH at reset means the board does not boot [HW:1169-1176] |
| 4 | GND | 0 | **directly beside LED_SW** |
| 5 | LED_SW | Off: LDO_IN minus a body-diode drop, about 2.5-5.2 V. On: string V_OUT. Open load: 24.25-25.5 V (611: 29.6-31.4 V) | Boost output and common anode. D3 to GND [PCB] |
| 6 | W- | about 0 V (R50 1 M to GND), or V_FB + Q5 drop when selected | Warm return through Q5 BSS138 to R37. D8 [PCB] |
| 7 | 3V3 | 3.3 V | CR2 |
| 8 / 10 | I2C_SDA / I2C_SCL | 0-3.3 V, pulled up | U8 |
| 9 | UNUSED_GPIO_3 | 0-3.3 V | strap pin, not boot-critical |
| 11 | C- | same as W- | Cool return through Q6 to R37 (R49 1 M). D8 [PCB] |
| 12 | /P+_FUSE | 3.0-4.2 V (raw cell) | PPTC F2 0805L075WR, 0.75 A hold [SCH:40240], [HW:1187-1192] |

- J3 and J6 carry the same three nets in parallel. A panel frontlight or strip on J3 plus a light on J6 share the
  single R37 current by V_f mismatch. That is safe, because the total stays <= 13.96 mA, but brightness is split
  unevenly [HW:755-760].
- Q6 (cool) conducts whenever 3V3 is up and COLOR_SEL is low (R75 pull-down, U12 inverter), so the C- return
  is closed even while the light is off [HW:782-791], [LS:43-45].
- D3 and D8 sit on the tongue and are fitted with the front light whether or not J6 is fitted [HW:1154-1157].

## 2. Frontlight driver facts

Parts [SCH] (line):
- U10 TPS923610DRLR (34647)
- R37 15 R 1 % 0603 (25926)
- C9 4.7u/50V CL21A475KBQNNNE (28446)
- C12 4.7u 0603 CL10A475KO8NNNC (24531)
- L2 10u TDK VLS252012HBX-100M-1 (35068)
- D3 SMAJ26A (28969)
- D8 PESD2IVN-UX, a 24 V bidirectional part per [DR:427] (29485)
- Q5/Q6 BSS138LT1G (28705/38712). The LCSC code C7420339 is a hongjiacheng BSS138, 3 R max at 4.5 V [DR:334].
- U12 74LVC1G04 (34010)
- R49/R50 1 M (38230/25289)
- R39/R41/C31 1 M/120 k/100 n (36658/41066/21966)
- R75 100 k (40496)

Datasheet values, all from [TI], re-checked 2026-09-25 against the PDF text:
- **VIN:** 2.5-5.5 V (p4-5). UVLO rises at 2.3 V typ. LDO_IN comes from the TPS2116 mux, so on USB it is the VBUS
  voltage (5.0-5.5 V), not the 3.0-4.2 V battery range [HW:134-136,149].
- **V_FB:** 195 / 200 / 206 mV at 100 % duty (198-203 mV at 25 C). At 10 % duty it is 14.5-25.5 mV (p5).
- **ADIM:** analog dimming. The PWM chops the reference, and a low-pass filter follows. Recommended carrier is
  10-200 kHz (p13).
  - The first HIGH pulse must be longer than 40 us (tADIM_EN) to enable the part.
  - LOW for longer than 2.5 ms shuts it down (tADIM_SD, p5, p14).
- **Soft start:** the GM amplifier output ramps "very slowly" with the switch limit at ILIM_START 0.8 A, then
  FB ramps to the reference. The datasheet gives no duration (p11).
- **Open LED:** when V_OUT exceeds V_OVP_R the part stops switching. It restarts once V_OUT has fallen by 1 V.
  After 3 trips it latches off. Only shutdown plus re-enable through ADIM, or VIN UVLO, resets it (p12).
- **Load below VIN / shorted string:** there is a DC path VIN -> L2 -> high-side body diode -> VOUT. TI relies on
  "string V_f + body diode > max VIN" to keep the LEDs off in shutdown (p11). Beyond ILIM, FB-short over-current
  protection and thermal shutdown, nothing protects against a shorted LED (p13, p19).
- **C_OUT:** 1 uF effective minimum (p4). C9 meets this only after derating: 4.7 uF nameplate, 1-2.5 uF effective.
- **Unplug overshoot (INFERRED):** the energy in L2 at ILIM max (2.1 A, 22 uJ) adds only 0.2-0.35 V above OVP.
  That gives 25.8 V peak on the 610, under D3's 28.9 V. On the 611 it is 31.7 V, 0.3 V under the 32 V VOUT abs max.
  That tight 611 margin is a board issue, not an accessory one.

## 3. LED string window (N per channel)

Assumptions (INFERRED, generic InGaN white). Per-LED V_f at 14 mA, 25 C (min/typ/max) and dynamic resistance r_d:

| Class | V_f min / typ / max | r_d |
|---|---|---|
| 2835 mid-power | 2.60 / 2.80 / 3.05 V | 4 R |
| 3014 / 3528 | 2.70 / 2.95 / 3.20 V | 8 R |
| 0603 / 0805 | 2.70 / 3.00 / 3.30 V | 12 R |
| Side-view | 2.75 / 3.05 / 3.35 V | 12 R |

Other assumptions:
- Temperature coefficient: -3 mV/K.
- 0.1 % ADIM costs -0.45 V per LED [LS:155-160].
- Q5/Q6 drop 0.14 V (10 R at Vgs 3.3 V).
- The series silicon diode drops 0.95 V cold and 0.45 V at deep dim when hot.

**(a) Lower bound.** N x V_f(14 uA, 65 C, min bin) + diode >= VIN_max 5.5 V + 1 V margin = 6.5 V. The hard limit,
at the 1 uA off-state, is > 5.2 V [LS:136-146]. Results:
- N >= 4 for every class without a diode.
- N = 3 passes only with the series diode, and it fails single-LED-short tolerance.
- The 6-7.4 V USB hot-plug ringing [HW:217-220] is a further reason to stay at N >= 4.

**(b) Upper bound.** N x V_f(max, -10 C) + Rs x 13.96 mA + 0.95 V diode + 0.206 V + 0.14 V must be <= 22.0 V.
That is the design ceiling, 2.25 V under OVP min 24.25 V [LS:125-129]. Allowed N:

| Rs | No diode | With diode |
|---|---|---|
| 0 R | 4-6 | 3-6 (side-view 3-5) |
| 100 R | 4-6 (0603 and side-view 3/4-5) | 3-5 (2835 up to 6) |
| 150 R | 4-5 (2835 up to 6) | 3-5 |

N = 5 with Rs = 120 R and a diode (INFERRED):

| Class | V_OUT typ | V_OUT worst (cold, max bin) | Margin to OVP min | V_OUT at 0.1 % dim, hot |
|---|---|---|---|---|
| 2835 | 16.6 V | 18.75 V | +5.5 V | 10.6 V |
| 3014 | 17.35 V | 19.50 V | +4.75 V | 11.1 V |
| 0603 | about 17.6 V | 20.00 V | +4.25 V | 11.1 V |
| Side-view | about 17.9 V | 20.25 V | +4.0 V | 11.35 V |

**Recommendation: N = 5 per colour (10 LEDs)**, the same as the stock FL01C (5 dies, 15 V typ [LS:108-110]). It:
- clears both bounds for every class;
- survives one shorted LED (4 left, still > 6.5 V at deep dim);
- works unchanged on the TPS923611.

N = 6 is possible only with 2835-class LEDs, or with a tight bin (max <= 3.2 V) and Rs <= 100 R. N = 7 is rejected.

Also:
- Use the **same LED family and V_f bin for warm and cool** (see section 6, 10 kHz mux).
- Rate the LEDs for >= 20 mA continuous and >= 100 mA pulse (IFP).

## 4. Hot-plug and unplug

**Mechanism.** Suppose the light is enabled (brightness > 0 in settings, which is also restored at boot
[FW: lib/hal/HalFrontlight.cpp:7-15]) with nothing on J3 or J6:
- U10 goes to OVP and latches within milliseconds.
- C9 holds 24.25-25.5 V (611: up to 31.4 V) and decays only through R39 + R41 (1.12 M), with tau 2.8-5.3 s.
  It takes about 4-8 s to fall to 6 V (INFERRED).
- Plugging a string in during that window dumps C9 through: the string, Rs, W- or C-, the selected Q5 or Q6, and
  R37 to GND.
- The selected FET is always on, because U12 guarantees one of Q5/Q6 is closed.

**Peak current**, estimated for an N = 5 string at 25 C, min bin, loop resistance
R37 + 2 R + Rs + N x r_d (+ diode), INFERRED:

| Rs | Peak with C9 at 25.5 V (610) | Peak with C9 at 31.4 V (611) | tau (2.5-4.7 uF) |
|---|---|---|---|
| 0 R | 152-312 mA | 226-464 mA | 0.1-0.36 ms |
| 68 R | 82-114 mA | 122-169 mA | |
| 100 R | 67-88 mA | 100-130 mA | 0.35-0.84 ms |
| **120 R** | **60-77 mA** | **90-114 mA** | about 0.4-0.9 ms |
| 150 R | 52-64 mA | 78-96 mA | |

- Energy per LED is 0.16-0.28 mJ, mostly at knee voltage. Energy in Rs is 0.2-0.6 mJ (C9 at 4.7 uF).
- The 2835 class with no Rs exceeds a typical 100-150 mA IFP. Rs = 120 R keeps the TPS923610 case under
  about 80 mA.
- **Rs = 120 R per string** costs:
  - 1.68 V of headroom;
  - about 10 % of LED power (23 mW continuous per resistor).
- Use a 0805 or an anti-surge 0603. Check the part's single-pulse curve against about 1.9 W for 0.5 ms (UNVERIFIED).
- Rs has three more jobs:
  - it bounds the misinsertion case in section 5;
  - it reduces blend errors (section 6);
  - it bounds the current if the J6 string is paralleled with a lower-V_f string on J3.

**Hot-plug with the light off** (ADIM low > 2.5 ms): LED_SW is at most 5.2 V, below the knee of N = 5, so there
is no current. **Hot-plug with a J3 load lit**: C9 sits at the J3 string voltage (about 15 V), so the dump
is limited to the V_f difference and is small.

**Unplug under load:**
- FB falls to 0, the boost ramps to OVP (peak about 25.8 V), trips 3 times and latches.
- A 14 mA break at 25 V or less needs no arc precautions (INFERRED).
- The main risk is an immediate re-plug, which is the hot-plug case above.

## 5. Misinsertion (2x6 male plug, contacts at pins 5 / 6 / 11 only)

Placements enumerated by script: 0 or 180 degree rotation, a column mirror (header soldered on the wrong face),
row offsets of -1/0/+1, and column shifts of -5 to +5. The accessory contacts are a = anode (for pin 5), w = warm
cathode (pin 6) and c = cool cathode (pin 11).

Assumed accessory: per string, the LEDs, then Rs, then a blocking diode toward the w/c contact, plus a clamp diode across the
LEDs. **There is no accessory copper at any other position.**

| Placement | a / w / c land on | Result |
|---|---|---|
| Correct | LED_SW / W- / C- | Normal, regulated |
| Shift -1 | GND / LED_SW / SCL | Warm string is reversed. With the light on, up to 25.5 V reverse is blocked by the diode and the LEDs are clamped. Cool string: GND to SCL is reversed. **Inert** |
| Shift -2, -3, -4 | IO45/GND/IO3, IO46/IO45/SDA, GND/IO46/3V3 | Available forward voltage is <= 3.3 V, below the N = 5 knee (about 11 V). The pull-down straps see only nA (INFERRED). **Inert** |
| Shift +1 | W- / (air) / P+ | Cool string reversed by 4.2 V. **Inert** |
| Rotation 180 | SDA / 3V3 / IO46 | Forward at most 3.3 V. **Inert**. IO46 stays low |
| Rotation 180, shift +1/+2/+4 | IO3/SDA/IO45, SCL/IO3/GND, P+/C-/W- | Forward at most 4.2 V. **Inert** |
| Rotation 180, shift +3 | C- / SCL / LED_SW | Cool string reversed. Blocked and clamped. **Inert** |
| Row offset (one row engaged) | C-/P+/-, SCL/C-/-, and similar | Forward at most 4.2 V or reversed. **Inert** |
| Row swap / mirror, no shift | C- / P+ / LED_SW | Both strings reversed. Blocked. **Inert**. If the light is on, OVP latches |
| **Column mirror + shift +3** | **LED_SW / GND(4) / C-** | Cool string is correct. Warm string runs LED_SW to GND with no current sense (below) |
| **Rotation 180 + row offset + shift +3** | **LED_SW / GND(4) / -** | Warm string runs LED_SW to GND with no current sense (below) |

**The only hazardous geometry: the anode lands on LED_SW and a cathode lands on pin 4 (GND).**
- With warm selected, or in the 2-contact case, FB sees nothing and the boost ramps.
- The boost can deliver at most about 156 mA at 24 V from a 3.0 V battery (ILIM min, eta 0.85; INFERRED).
- Current at OVP min (INFERRED):
  - Rs = 0: 173-497 mA, which needs 4.2-12 W. **The boost never reaches OVP**, so the string is overdriven
    continuously and burns.
  - Rs = 120 R: 59-77 mA (1.4-1.9 W). The boost reaches OVP, trips 3 times and latches in under about 1 ms. That is
    harmless.
- With cool selected in the 3-contact case, V_OUT is pinned by the regulated cool string. The warm string then
  carries about 15 mA unregulated (INFERRED), which is also harmless.
- **Rs >= about 68 R is therefore a safety requirement**, not an option.

Other conclusions:
- **No forward path ever exists from P+, 3V3 or a GPIO** at N >= 3, because 4.2 V is below the string knee.
- The cathode-side blocking diodes also remove the w-to-c cross path. An anode-side diode with anti-parallel
  clamps would conduct 25 V from w to c. So would bare Zener-protected LEDs (reverse Zener string plus forward
  string, about 17 V at N = 5), and in the shift -1 case that current would go into SCL.
- The cathode-side arrangement works with or without LED-internal Zeners. It uses one **BAW56-class common-anode
  dual per string**:
  - common anode at the string cathode;
  - cathode 1 to the W-/C- contact (block);
  - cathode 2 to the anode bus (clamp).
  - VR >= 40 V; 75-100 V preferred for TPS923611 builds.
  - The clamp also limits reverse ESD across the loose accessory's LEDs.

**Pin population:**
- Populate male pins **5, 6 and 11 only**.
- **Put no pad or copper at pin 4 or pin 12.** A dummy pin at pin 4 is harmless only while it floats. A solder
  bridge from it to pin 5 would short LED_SW to GND. That is the worst J6 fault: current from LDO_IN through L2
  and the body diode, limited only by the source or battery protection. D3 does not help (INFERRED).
- Use a 2x2 (columns 5-6, pin 12 pulled) or a 2x3 (columns 4-6, pins 4, 10 and 12 pulled) body with no pads at
  the pulled positions.
- Keying must come from the housing or the bezel. A bare plug can always be shifted or overhung. The two hazardous
  geometries need a column mirror or row overhang plus a 3-column shift, so a housing that fixes position removes
  them.
- Pin length: standard mating length is fine. Contact sequencing buys nothing electrically.
- Keep the mated pins fully inside the female, so no LED_SW metal is exposed on the outside variant. It is SELV
  (<= 31.4 V) but ESD-exposed.
- Note that the stock enclosure's open J6 hole already exposes a pin 4-5 paperclip short.

## 6. Firmware behaviour and required changes

Current firmware:
- **Pin setup.** Board profile `{42, 10000, 8, true, 40}`: ADIM on GPIO42 at 10 kHz, 8-bit; COLOR_SEL on GPIO40 as
  a second LEDC channel [FW: freeink-sdk/libs/hardware/BoardConfig/include/BoardConfig.h:1872-1873].
- **Warm/cool is time-multiplexed.** `apply()` writes ADIM = total brightness (gamma 1.6554) and GPIO40 = warm % of
  255 at **10 kHz**. Warm and cool are never on together, apart from the inverter's transition overlap
  [FW: .../FrontlightManager/src/FrontlightManager.cpp:336-344], [HW:777-800].
- **Defaults** are 60 % brightness and 50 % warmth, so a 50 % mux runs by default [FW: src/CrossPointSettings.h:337-338].
- **No enable pulse and no LED_MONIT read.** A grep of FrontlightManager, lib/hal and src found neither, so the
  light turns on without detecting a load.
- **The firmware contract is not followed.** [HW:1293-1307] asks for four things:
  - a >= 100 us enable pulse;
  - OVP recovery by holding ADIM low for >= 3 ms;
  - LED_MONIT monitoring;
  - colour changes only at duty 0.

  None of these is implemented.

Required or recommended for a J6 light:
1. **Enable pulse.** At 10 kHz the ADIM HIGH time is duty x 100 us. Duty reaches 40 us only above about 58 %
   brightness (INFERRED from the gamma curve), so turning on dimmer than that may never enable U10. Drive GPIO42
   HIGH for >= 100 us, then start the carrier.
2. **Load check using LED_MONIT** (IO2, tau 10.7 ms) about 30-50 ms after enabling:
   - above about 2.40 V (22.4 V): report "no light / open / misinserted" and set duty to 0 (shutdown);
   - N = 5 + 120 R normally reads 1.6-2.17 V; open load reads 2.60-2.73 V;
   - on the TPS923611, open load reads 3.17-3.36 V and may saturate the ADC, which is still "open".

   Do **not** auto-probe periodically. Every probe with nothing attached re-charges C9 to OVP, which recreates the
   hot-plug case. Probe only when the user acts.
3. **Latch recovery.** When the user re-enables after plugging in, force ADIM low for >= 3 ms first. Setting
   duty to 0 already does this if the light is left off for more than 2.5 ms.
4. **Warm/cool mux (INFERRED).**
   - At 10 kHz the C9 re-slew time (100-350 us per volt [HW:813-825]) is longer than the period. The strings share
     one V_OUT, and a V_f mismatch shifts current between them. For a 0.3 V mismatch the error is 4-8 mA with no
     Rs, or about 2 mA with Rs = 100 R.
   - Match the bins. Consider a fixed warm/cool mode until blending is qualified [HW:807-811].
5. **No brightness cap is needed.** R37 fixes the total at <= 13.96 mA. Optionally add a UI hint: "switch the
   light off before attaching".

## 7. Differences from the J3 light-strip analysis ([LS])

- **Same:** driver, current, OVP and N window. N = 5 [LS:172-178].
- **GND beside the anode:** J3 has no GND [LS:40-42]; J6 pin 4 is next to LED_SW. So Rs is mandatory and pin 4
  gets no copper.
- **2-D misinsertion:** J3 only flips [LS:219-223]; J6 shifts and rotates onto logic, P+ and 3V3 pins. These are
  inert at N >= 3 with blocking diodes.
- **Hot-plug is normal use** on J6 (it was only a warning in [LS:303-307]). Rs covers it.
- **Diode on the cathode side** (BAW56 per string), not the anode-side BAV70 [LS:273-291]. This removes the
  w-to-c path.
- **Headroom:** [LS:164-170] had no Rs. With 120 R, N = 6 fails the 22 V ceiling for most classes.

## 8. Open questions / risks

- All LED V_f, r_d, IFP and temperature-coefficient values are generic. Replace them with the chosen part's
  datasheet, including its 1 uA / 14 uA V_f, VR and whether it has an internal Zener.
- The hot-plug and misinsertion currents are linear-model estimates. Bench-check them with a scope: C9 dump into
  the string, and the LED_SW-to-GND case with the 120 R.
- The boost output capability at OVP (about 156 mA) is an estimate. The datasheet gives no max duty or minimum
  off-time [LS:72].
- The BSS138 (C7420339 clone) R_on at 3.3 V is unspecified. 10 R is assumed.
- The ESP32-S3 ADC range at 12 dB is UNVERIFIED (about 3.1 V).
- The TPS923611 unplug overshoot (31.7 V) comes close to VOUT abs max 32 V. This is a board-level item.
- Whether the firmware changes (enable pulse, LED_MONIT) land is outside the hardware design.
