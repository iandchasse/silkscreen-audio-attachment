# Silkscreen audio attachment: audio chain research

Status: research complete 2026-11-09 (electrical research lead). Not committed to git.
Scope: the electrical chain from `J6` (IO3/IO45/IO46 + P+) to a 3.5 mm stereo jack. Mechanical form
(header style, keying, jack position) belongs to the mechanical design and is only noted here.

Datasheet page numbers are PDF page numbers of the TI files listed in section 8.

---

## 1. Recommendation

**PCM5102A (3-wire I2S DAC, no MCLK, no I2C) -> TPA6138A2 (ground-centred stereo headphone/line
driver) on a 3.3 V rail from a TPS7A2033 LDO fed by P+, whose EN is driven by a passive
"clock-present" charge pump on the WS line.** No I2C, no firmware init, no enable GPIO, no MCLK.
Every part is a stock LCSC/JLC SMD part; all passives are JLC basic.

How it behaves:

- **Idle (I2S stopped):** WS does not toggle, the pump output `EN_DET` is 0 V, the LDO is off and
  the whole audio side is unpowered. P+ draw = LDO shutdown current, **0.07 uA typ / 0.2 uA max**
  (TPS7A20 p6), plus capacitor leakage. Nothing on J6_3V3, nothing on I2C.
- **Playing:** WS toggling charges `EN_DET` to about 2.8 V within a few ms, the LDO turns on (EN
  threshold 0.9 V max, TPS7A20 p7), the PCM5102A starts its BCK-derived PLL by itself (p25), and the
  amplifier is held in mute by a slower RC until about 90-130 ms after the clocks start, so the DAC's
  start-up transient never reaches the jack. Draw from P+: **~33 mA in silence, ~50 mA at normal
  headphone level, ~110 mA at maximum into 32 ohm.**
- **Stop:** firmware fades out, sends >= 50 ms of zeros, stops I2S and parks the three pins LOW.
  The amplifier mutes 0.7-1.5 s later, and the LDO turns off 2-4.5 s after the last WS edge,
  always after the amplifier has muted.

### 1.1 Netlist in words

Net names in `CAPS`. All resistors 0603 1 %, all capacitors 0603 X5R/X7R. "basic" = JLC basic part
(no extended-part fee). Stock = LCSC/JLC stock on 2026-11-09.

**Connector to the main board, J1** - 2x6 2.54 mm male header mating with `J6` (pin numbers are
`J6`'s; see HARDWARE.md section 11 for which socket row is which and the Rev 1.0 label reversal).

| J1 pin | J6 signal | Accessory net | Notes |
|---|---|---|---|
| 1, 4 | GND | `GND` | both pins to the ground plane |
| 2 | IO46 | `I2S_BCLK` | |
| 3 | IO45 | `I2S_DOUT` | |
| 9 | IO3 | `I2S_WS` | carries the clock-present detector |
| 12 | P+ (raw cell, 0.75 A PPTC) | `VBAT` | |
| 5, 6, 7, 8, 10, 11 | LED_SW, W-, J6_3V3, SDA, SCL, C- | not connected | pad only, no copper; keep clearance around pin 5 (up to 25.5 V) and route `VBAT` away from pins 6 and 11 |

Candidate part: XFCN PZ254V-12-12P, straight 2x6 2.54 mm male, THT, LCSC C492423 (31,761, extended).
The mechanical design picks the final form and must key it, because a header plugged in rotated puts
P+ on the accessory ground (risk 6.5).

**Line pull-downs (strap-safe; no pull-ups anywhere on this board)**

- R5 100k `I2S_BCLK` -> `GND`; R6 100k `I2S_DOUT` -> `GND`; R7 100k `I2S_WS` -> `GND`.
  **Changed after this research (2026-11-09): R7 is 10k (C25804),** so it also serves as a presence detect against
  the ESP32's ~45k internal pull-up on IO3. See design/DESIGN-SPEC.md and docs/FIRMWARE-NOTES.md.
  Yageo/Uniroyal 0603WAF1003T5E, LCSC C25803 (16.07 M, basic).
- No series resistors at the accessory: the main board already has 33 ohm (`R65`/`R68`/`R69`) and the
  PCM5102A inputs are failsafe (section 3.4).

**Clock-present detector (charge pump on WS) -> LDO enable**

- R1 1k (C21190, basic): `I2S_WS` -> `PUMP_A`.
- C3 10 nF 50 V X7R (C57112, basic): `PUMP_A` -> `PUMP`.
- D1 BAT54S (series dual Schottky, SOT-23; Changjing BAT54S, LCSC C8592, 221,495, extended; DigiKey
  alternative onsemi BAT54SLT1G): pin 1 (anode, lower diode) -> `GND`; pin 3 (common) -> `PUMP`;
  pin 2 (cathode, upper diode) -> `EN_DET`.
- C4 1 uF 50 V X5R (C15849, basic): `EN_DET` -> `GND`.
- R2 1M (C22935, basic): `EN_DET` -> `GND` (bleed; sets the turn-off delay).
- `EN_DET` -> U1 pin 3 (EN) directly.

**Amplifier mute delay**

- R3 100k (C25803, basic): `EN_DET` -> `MUTE_RC`.
- C5 1 uF (C15849, basic): `MUTE_RC` -> `GND`.
- R4 10k (C25804, basic): `MUTE_RC` -> `AMP_MUTE` (U3 pin 5). Limits current into the Mute pin when
  the rail collapses while C5 is still charged.

**U1 - LDO, TPS7A2033PDBVR** (TI, 3.3 V, 300 mA, 7 uVrms, SOT-23-5; LCSC C2862740, 122,457, extended;
DigiKey 296-TPS7A2033PDBVRCT-ND)

- Pin 1 IN -> `VBAT`; pin 2 GND -> `GND`; pin 3 EN -> `EN_DET`; pin 4 NC -> leave open;
  pin 5 OUT -> `3V3A`.
- C1 10 uF 10 V X5R (C19702, basic) `VBAT` -> `GND` at J1. C2 1 uF (C15849) `VBAT` -> `GND` at U1 pin 1.
- C6 1 uF (C15849) `3V3A` -> `GND` at U1 pin 5. Total capacitance on `3V3A` is about 33 uF nominal,
  inside the 1-200 uF the TPS7A20 allows (p5).

**U2 - DAC, PCM5102APWR** (TI, TSSOP-20; LCSC C107671, 1,289, extended; DigiKey 296-36707-1-ND)

| U2 pin | Name | Connection |
|---|---|---|
| 1 | CPVDD | `3V3A`; C7 100 nF (C14663, basic) + C8 10 uF (C19702) to `GND` |
| 2 | CAPP | C9 2.2 uF 16 V (C23630, basic) between pin 2 and pin 4 |
| 3 | CPGND | `GND` |
| 4 | CAPM | other side of C9 |
| 5 | VNEG | C10 2.2 uF (C23630) to `GND` |
| 6 | OUTL | `DAC_OUTL` -> R8 470R (C23179, basic) -> `DAC_L`; C16 2.2 nF (C1604, basic) `DAC_L` -> `GND` |
| 7 | OUTR | `DAC_OUTR` -> R9 470R -> `DAC_R`; C17 2.2 nF `DAC_R` -> `GND` |
| 8 | AVDD | `3V3A`; C11 100 nF + C12 10 uF to `GND` |
| 9 | AGND | `GND` |
| 10 | DEMP | `GND` (de-emphasis off) |
| 11 | FLT | `GND` (normal-latency FIR) |
| 12 | SCK | `GND` (required for BCK-PLL mode, p25) |
| 13 | BCK | `I2S_BCLK` |
| 14 | DIN | `I2S_DOUT` |
| 15 | LRCK | `I2S_WS` |
| 16 | FMT | `GND` (I2S format, p15) |
| 17 | XSMT | `3V3A` directly (allowed, p16) |
| 18 | LDOO | C13 100 nF to `GND` (p28) |
| 19 | DGND | `GND` |
| 20 | DVDD | `3V3A` (3.3 V I/O, internal 1.8 V LDO on); C14 100 nF + C15 10 uF to `GND` |

Values follow TI's typical application (Figure 33, p26; output filter 470 ohm + 2.2 nF, p8 note 3).

**U3 - headphone driver, TPA6138A2PWR** (TI, TSSOP-14; LCSC C183097, 3,332, extended; DigiKey
296-28248-1-ND). Each channel is a plain inverting stage with gain -1 V/V (Rin = Rfb = 10k, Table 1 p11).

| U3 pin | Name | Connection |
|---|---|---|
| 1 | +INR | `GND` |
| 2 | -INR | R12 10k (C25804, basic) from `DAC_R`; R13 10k from pin 2 to pin 3 (feedback) |
| 3 | OUTR | `AMP_OUTR` -> R15 10R (C22859, basic) -> `HP_R`; C22 1 nF (C1588, basic) `HP_R` -> `GND` |
| 4 | GND | `GND` |
| 5 | Mute | `AMP_MUTE` (active low) |
| 6 | VSS | C20 1 uF (C15849) to `GND` |
| 7 | CN | C19 1 uF flying cap, pin 7 to pin 8 |
| 8 | CP | other side of C19 |
| 9 | VDD | `3V3A`; C18 1 uF to `GND` at the pin |
| 10 | GND | `GND` |
| 11 | UVP | leave unconnected (internal pull-up; "unconnected if UVP function is unused", p3) |
| 12 | OUTL | `AMP_OUTL` -> R14 10R -> `HP_L`; C21 1 nF `HP_L` -> `GND` |
| 13 | -INL | R10 10k from `DAC_L`; R11 10k from pin 13 to pin 12 |
| 14 | +INL | `GND` |

The 10 ohm + 1 nF on each output is the "simple resistor-capacitor ESD protection" TI quotes for
+/-8 kV IEC (p1) and matches the characterisation conditions (ROUT = 10 ohm, COUT = 1 nF, p6). The input
is DC-coupled: both the DAC output and the amplifier are ground-referenced, so no coupling capacitors
(and no capacitor-charging pops).

**J2 - 3.5 mm stereo jack**: Shou Han PJ-313D, SMD, 14 x 6 x 5 mm, LCSC C668608 (23,114, extended).
Tip -> `HP_L`, ring -> `HP_R`, sleeve -> `GND` (connect the sleeve pad to the ground plane next to
U3's GND pins). Any switch/detect contacts: not connected (no GPIO for detect). I could not open the
PJ-313D datasheet (LCSC returned an HTML page), so take the pad numbering from the LCSC/EasyEDA
footprint and datasheet for C668608 when placing it. DigiKey-listed alternative: CUI SJ-3524-SMT-TR,
LCSC C20182907 (614, extended).

**Placement count**: 3 ICs, 1 diode pair, 15 resistors, 22 capacitors, 2 connectors = 43 placements.
Extended parts: U1, U2, U3, D1, J2 (plus J1). Everything else is basic.

### 1.2 Bill of materials

| Ref | Qty | Value / part | MPN | LCSC | Stock | JLC | DigiKey |
|---|---|---|---|---|---|---|---|
| U1 | 1 | LDO 3.3 V 300 mA | TPS7A2033PDBVR | C2862740 | 122,457 | ext | 296-TPS7A2033PDBVRCT-ND |
| U2 | 1 | Audio DAC, BCK PLL | PCM5102APWR | C107671 | 1,289 | ext | 296-36707-1-ND |
| U3 | 1 | DirectPath HP driver | TPA6138A2PWR | C183097 | 3,332 | ext | 296-28248-1-ND |
| D1 | 1 | Dual Schottky series | BAT54S (Changjing) | C8592 | 221,495 | ext | onsemi BAT54SLT1G (alt.) |
| J2 | 1 | 3.5 mm stereo jack SMD | PJ-313D (Shou Han) | C668608 | 23,114 | ext | none; alt. CUI SJ-3524-SMT-TR |
| J1 | 1 | 2x6 2.54 mm male | PZ254V-12-12P (XFCN) | C492423 | 31,761 | ext (THT) | per mechanical design |
| R5-R7, R3 | 4 | 100k | 0603WAF1003T5E | C25803 | 16.07 M | basic | |
| R4, R10-R13 | 5 | 10k | 0603WAF1002T5E | C25804 | 47.28 M | basic | |
| R1 | 1 | 1k | 0603WAF1001T5E | C21190 | 26.64 M | basic | |
| R2 | 1 | 1M | 0603WAF1004T5E | C22935 | 4.40 M | basic | |
| R8, R9 | 2 | 470R | 0603WAF4700T5E | C23179 | 4.12 M | basic | |
| R14, R15 | 2 | 10R | 0603WAF100JT5E | C22859 | 5.64 M | basic | |
| C1, C8, C12, C15 | 4 | 10 uF 10 V X5R | CL10A106KP8NNNC | C19702 | 10.22 M | basic | |
| C9, C10 | 2 | 2.2 uF 16 V X5R | CL10A225KO8NNNC | C23630 | 2.29 M | basic | |
| C2, C4, C5, C6, C18-C20 | 7 | 1 uF 50 V X5R | CL10A105KB8NNNC | C15849 | 12.80 M | basic | |
| C7, C11, C13, C14 | 4 | 100 nF 50 V X7R | CC0603KRX7R9BB104 | C14663 | 33.67 M | basic | |
| C3 | 1 | 10 nF 50 V X7R | 0603B103K500NT | C57112 | 5.81 M | basic | |
| C16, C17 | 2 | 2.2 nF 50 V X7R | 0603B222K500NT | C1604 | 601 k | basic | |
| C21, C22 | 2 | 1 nF 50 V X7R | CL10B102KB8NNNC | C1588 | 5.31 M | basic | |

---

## 2. Comparison of DAC / headphone chains

| Option | No MCLK, 3 pins? | Drives 16-32 ohm? | Idle with clocks stopped | Pops | Parts (approx.) | LCSC stock / class | Firmware |
|---|---|---|---|---|---|---|---|
| **PCM5102A + TPA6138A2 (recommended)** | yes, BCK PLL (p25) | yes, 40 mW into 32 ohm at 1 % THD, 50 mA limit (TPA6138A2 p5) | both parts unpowered by the switched LDO: 0.07 uA | DAC start transient masked by delayed amp unmute; stop handled by the DAC's own soft/auto mute | 43 | 1,289 + 3,332, ext | none (I2S only) |
| PCM5102A alone | yes | **no**: load impedance 1 kOhm min (p9); full scale 2.1 Vrms would need 66 mA into 32 ohm | power-down mode still 0.5 mA DVDD + 0.2 mA AVDD/CPVDD typ, 0.8 + 0.4 mA max (p9-10) | auto-mute / clock-halt pops reported (TI E2E) | ~13 | 1,289, ext | none |
| PCM5102A + TPA6132A2 | yes | yes, 25 mW into 16 ohm; 2.1 mA Iq, EN pin, 1 uA shutdown, runs 2.3-5.5 V (TPA6132A2 p1, p4-5) | best playing current of all | good (active pop suppression, 5 ms start) | ~35 | **TPA6132A2RTER: 18 pcs**, WQFN-16 | none |
| PCM5102A + MAX97220A | yes | yes | needs SHDN control | good | ~38 | **65 pcs**; HT97220 clone 0 pcs | none |
| UDA1334ATS | yes | line level only | n/a | n/a | ~15 | **0 pcs** (both listings) | none |
| TLV320DAC3100 | yes (BCLK as PLL source) | headphone output is AC-coupled (p7-8): 2 large DC-blocking caps, pops on start/stop | low with registers off, but needs a reset each power-up | cap-charging pops | ~30 + 1.8 V LDO + reset RC | 1,831, ext, QFN-32 | full I2C register init at address 0x18 (p18); RESET must be low while DVDD ramps (p20); DVDD 1.65-1.95 V |
| ES8311 | yes (SCLK as MCLK) | mono codec; needs an external amplifier for stereo | low | depends | ~25 | 112,008, ext | I2C init (0x18/0x19) |
| MAX98357A | yes | class-D BTL speaker output, cannot share a TRS sleeve | auto shutdown | good | ~6 | ok | none |

I2C note (only relevant to the rejected codecs): the main board's bus carries the RTC at 0x51 (U14,
RV-8263-C7) or 0x68 (DS3231 option) plus the touch controller; 0x18 does not collide with the RTCs.
The recommendation uses no I2C at all.

Why TPA6138A2 over TPA6132A2: the TPA6132A2 is the nicer amplifier (2.1 mA vs 14 mA Iq, EN pin,
runs straight from P+), but LCSC holds 18 pieces. The TPA6138A2 has 3,332 at $0.41, an easy TSSOP-14
package, and the extra 12 mA only flows while audio is playing because the whole rail is switched.
The TPA6138A2 needs a 3.0-3.6 V supply (abs max 4 V, p4), so it cannot sit on P+; it shares the
switched 3.3 V rail.

---

## 3. Power architecture and idle analysis

### 3.1 Options considered

| Architecture | Idle draw | Verdict |
|---|---|---|
| Always-on LDO, rely on the parts' auto-standby | PCM5102A power-down 0.7 mA typ / 1.2 mA max (p9-10); TPA6138A2 has no shutdown, 14 mA even with Mute low (p5) | fails the tens-of-uA target by 30x to 1000x |
| Logic from J6_3V3 (20 mA budget) | PCM5102A DVDD alone is 8-9 mA playing, 0.5 mA in power-down, permanently on the main 3V3 | fails idle and budget |
| **LDO from P+, EN from a passive clock-present detector on WS** | TPS7A20 ISHDN 0.07 uA typ, 0.2 uA max (p6) | **chosen** |

### 3.2 The detector

The pump is AC-coupled, so only a toggling WS can turn the rail on. A WS line stuck HIGH (firmware
slip) or LOW leaves the rail off.

- Each WS edge moves charge through R1/C3 into C4 via D1's upper diode; D1's lower diode resets C3 on
  the falling edge. Effective pump source resistance is about 4.5 kOhm at 44.1-48 kHz and about
  6.8 kOhm at 16 kHz (R1*C3 = 10 us against an 11-31 us half period).
- Open-circuit level = WS swing minus two Schottky drops, about 3.3 - 2 x 0.25 = 2.8 V. Against the 1 MOhm
  bleed plus EN leakage (<= 250 nA, p7), `EN_DET` settles at **about 2.75-2.8 V** at any supported
  sample rate. At a low cell (P+ = 3.3 V, so WS swing ~3.2 V) it is about 2.7 V.
- LDO thresholds (TPS7A20 p7): enables at `EN_DET` > 0.9 V max (rising), disables below 0.3 V min
  (falling). A 500 kOhm "smart" pull-down holds EN low when it floats. EN abs max is VIN + 0.3 V, and
  2.8 V is below the 3.0 V minimum P+.
- Amp mute (TPA6138A2 p4): unmuted above 60 % VDD (1.98 V at 3.3 V), muted below 40 % VDD (1.32 V).
  Mute input current is 1 uA max (p5), which is why R4 is only 10k and R3 100k.

**Start-up timeline (44.1 kHz):**

| t after first WS edge | Event |
|---|---|
| ~2-3 ms | `EN_DET` passes 0.9 V, LDO starts |
| +0.75 ms typ / 1.15 ms max | `3V3A` at 95 % (tSTR, p7) |
| +16 LRCK periods (0.36 ms) | PCM5102A switches to the BCK PLL and runs its power-up sequence (p25, p33) |
| ~90 ms (typ threshold) to ~130 ms (60 % VDD worst case) | `MUTE_RC` passes VIH and the amp unmutes |

Firmware must send >= 250 ms of zeros before real audio (section 7).

**Stop timeline:** `EN_DET` decays with about 2 s time constant (R2 x (C4 + C5)).

| t after last WS edge | Event |
|---|---|
| 0 | PCM5102A sees the clock halt and enters standby: DAC and line driver off (p33). If 50 ms of zeros came first, its zero-data auto-mute has already engaged |
| 0.7-1.5 s | amp mutes (`MUTE_RC` falls through 1.98-1.32 V) |
| 2.3-4.5 s | LDO turns off (`EN_DET` falls through 0.9-0.3 V); its 150 ohm active discharge pulls the rail down in about 5 ms (p7) |

The order (amp muted before rail loss) holds across all threshold tolerances. The worst case is a
mute at `EN_DET` around 1.26 V against an LDO off at <= 0.9 V, which leaves >= 0.67 s of margin.

### 3.3 Current numbers

**Idle (I2S stopped, rail off), from P+:**

| Item | Current |
|---|---|
| TPS7A20 shutdown (VIN 6 V, 25 C) | 0.07 uA typ, 0.2 uA max (p6) |
| C1/C2 leakage at 4.2 V | < 0.1 uA |
| Detector, pull-downs (lines LOW) | 0 |
| **Total** | **~0.1 uA typ, < 0.5 uA worst** |

J6_3V3: 0. ESP32 pins: 0 while parked LOW. A line the firmware leaves HIGH costs 33 uA (100k; 330 uA on IO3 now that R7 is 10k), and
still does not turn the rail on.

**Playing, from P+** (the LDO passes the current through, plus 6.5 uA ground current):

| Case | PCM5102A (p9-10) | TPA6138A2 (p5) | Headphone load | Total |
|---|---|---|---|---|
| Digital silence, clocks running | 8 + 11 = 19 mA | 14 mA (5-25) | 0 | **~33 mA** (worst-case spec ~54 mA) |
| Normal listening, 1 mW/ch into 32 ohm (0.18 Vrms) | ~22-25 mA | 14 mA | ~11 mA | **~50 mA** |
| Maximum into 32 ohm (current limited) | ~31 mA | 14 mA | ~64 mA | **~110 mA** (~140 mA worst spec) |
| Line out into 10 kOhm amplifier | ~25-31 mA | 14 mA | ~0.5 mA | **~40-45 mA** |

The TPS7A20 is rated 300 mA. Worst dissipation is (4.2 - 3.3) V x 0.11 A = 0.1 W in SOT-23-5.
The pin-12 PPTC (0.75 A) is not stressed.

**Charging interaction:** while audio plays on USB, the 33-50 mA load is above the ~5 mA average
limit, so the charger cannot terminate until playback stops. Within 2-4.5 s of the stop the board
draws ~0.1 uA and termination proceeds normally. Playback on USB is still net charging, at about
65-80 mA into the cell instead of 115 mA.

**Hangover energy:** each stop leaves ~33 mA flowing for 2-4.5 s, about 0.04 mAh, which is negligible.

### 3.4 Back-powering

- A generic CMOS DAC with clamp diodes to an unpowered VDD would take (3.3 - 0.6) V / 33 ohm, about
  80 mA, per driven line through the main board's series resistors, and would partly power its own rail.
- The PCM5102A's digital inputs are **failsafe LVCMOS Schmitt inputs** (features list p1; pin-table
  note 1 p5). Their absolute maximum is -0.3 to 3.9 V with DVDD at 3.3 V (p6), with no reference to a
  live DVDD. Driving 3.3 V into the unpowered DAC during the ~3 ms rail-up window, or with a stuck line,
  injects nothing. This is why the accessory needs no series resistors and can let the clocks start
  before its rail.
- The TPA6138A2 touches no ESP32 line. The pump draws from WS only, through 1 kOhm.
- Nothing on the accessory can drive a J6 line or feed the main 3V3: there are no outputs on the
  lines and J6_3V3 is not connected.

---

## 4. Pin mapping

| Signal | J6 pin | GPIO | Why |
|---|---|---|---|
| WS (LRCK) | 9 | IO3 | Carries the extra detector circuitry and is the line most likely to be left HIGH when I2S stops. HARDWARE.md: "Use IO3 for anything that idles high"; its strap (JTAG source) only matters if the STRAP_JTAG_SEL eFuse is burned |
| DOUT | 3 | IO45 | IO45 is the most dangerous strap (HIGH at reset = 1.8 V VDD_SPI, no boot). DOUT sits LOW through every silence, and the firmware ends each stream with zeros, so it is the line least likely to be high at any instant |
| BCLK | 2 | IO46 | The remaining pin; IO46 is a normal bidirectional GPIO on the S3 |

Strap safety in any case:

- At any chip reset the ESP32 releases all three pins (input, IO45/IO46 internal pull-down). The
  accessory has only pull-downs and inputs, and no device on it can drive a line, so every strap
  reads LOW.
- D1 blocks any path from the charged `EN_DET` back into WS.
- The ESP32-S3 ROM does not toggle IO3/IO45/IO46 during boot. If some boot code ever did, the rail
  would blip on for a few seconds, which is harmless.
- Pull-downs are allowed and used; there are no pull-ups and no series resistors at the accessory.

---

## 5. Output network and levels

- **Coupling**: ground-centred end to end. The PCM5102A has a charge-pump line driver, bipolar zero
  error +/-2 mV max (p9); the TPA6138A2 is DirectPath with offset <= 1 mV (p5). DC offset at the jack
  is <= ~3 mV, so the design needs no DC-blocking caps anywhere and has no capacitor-charging pops.
- **Protection**: 10 ohm series + 1 nF to ground per channel at the jack (TI's RC for +/-8 kV IEC, p1).
  The amplifier is short-circuit protected (50 mA limit, p5), which covers tip/ring shorts while a plug
  is inserted. No extra TVS.
- **Pop suppression**: start-up transient masked by the delayed unmute. The TPA6138A2's own mute and
  unmute are designed pop-free (p1, p11). At the stop, the DAC is already auto-muted by the zero
  pre-roll before the clocks halt.
- **Jack**: plain stereo TRS. Headphone detect is not used: there is no GPIO left, and a switched jack
  would add nothing without one.

**Maximum output** (gain -0.955 V/V, from 10k / (10k + 470R); PCM5102A full scale 2.1 Vrms, p9;
TPA6138A2 VOH 3.1 V at 3.3 V, 50 mA limit, p5):

| Load | Max level | Limited by | Reached at |
|---|---|---|---|
| 10 kOhm line input | ~2.0 Vrms | DAC full scale (2.83 Vpk < 3.1 V swing) | 0 dBFS (cap at -1 dBFS on a low cell) |
| 32 ohm headphones | ~1.1 Vrms, ~40 mW | amplifier current limit (~35 mA rms) | about -3 dBFS |
| 16 ohm headphones | ~0.57 Vrms, ~20 mW | current limit | about -7 dBFS |

40 mW into a 100 dB/mW headphone is about 116 dB SPL, so the firmware must default low (section 7).
The 10 ohm resistors cost 2.3 dB (32 ohm) / 4.2 dB (16 ohm) of level at a given volume setting, but
they do not reduce the maximum, because the current limit binds first.

---

## 6. Risks

1. **Stop click at clock halt.** The PCM5102A hard-mutes on clock halt even with XSMT high (internal
   clock-error detection, TI E2E 970965), and it zero-data auto-mutes after about 21 ms of zeros
   (E2E 765759). TI says this transition is "generally not audible" except in systems with high
   external gain; our external gain is -1 V/V. Mitigation is firmware: fade, then >= 50 ms of zeros,
   then stop. The DAC then halts from an already-muted state, the same transition every PCM5102A
   product makes at every pause. No hardware fallback without a GPIO. Check on the bench with
   sensitive IEMs.
2. **The detector is a custom passive circuit, verified by calculation only.** Bench check on the
   first article: `EN_DET` 2.6-2.8 V while playing at 16 / 44.1 / 48 kHz; < 50 mV within 5 s of
   stopping; `3V3A` 0 V idle; P+ current < 1 uA idle (meter in series with pin 12).
3. **PCM5102A stock is 1,289 at LCSC.** Fine for a small run; recheck before ordering. Five extended
   parts each carry JLC's extended-part fee.
4. **TPA6138A2 quiescent current is 14 mA typ, 25 mA max** (p5). Playing current is higher than a
   TPA6132A2 build would be. Accepted, because idle is unaffected and the TPA6132A2 is not stocked.
5. **Misplug.** The board is unpowered when idle, but a 2x6 header plugged rotated puts P+ on the
   accessory ground and IO3 on the accessory P+ input, and trips the main board's F2. The mechanical
   design must key the plug. Same J6 label caveat as HARDWARE.md: Rev 1.0 boards print the rows reversed.
6. **Jack pad numbering not verified** (PJ-313D datasheet unreachable). The signals are defined by
   function; take the numbering from the C668608 footprint.
7. **Charger does not terminate during playback on USB** (section 3.3). Expected, and resolves itself
   when playback stops.
8. **Unsupported sample rates.** In 3-wire mode the PCM5102A PLL handles only 16 kHz (64 fs only), 32,
   44.1, 48, 96, 192 and 384 kHz (Table 11, p25). 8, 11.025, 22.05 and 24 kHz content must be
   resampled; the DAC stays silent if fed those.
9. **Hum with a mains-powered line-in amplifier while the reader charges from another mains supply**
   (ground loop through the sleeve). That is inherent to any unbalanced output; it is a user note,
   not a design fault.
10. **Resume latency.** After a pause longer than ~0.7 s the amp re-mutes, and a resume costs a
    90-130 ms unmute delay. The firmware's pre-roll covers it.

---

## 7. Firmware notes (ESP32-S3, ESP-IDF 5.x API; also callable from Arduino-ESP32 3.x)

Settings:

- Standard (Philips) I2S, master TX, stereo.
- **32-bit data in 32-bit slots** (BCLK = 64 fs: 2.8224 MHz at 44.1 kHz, 3.072 MHz at 48 kHz, 1.024 MHz
  at 16 kHz), so software volume loses no resolution.
- MCLK not output. FMT low = I2S (p15); the DAC takes up to 32-bit data.
- Run everything at **44.1 or 48 kHz** (16 kHz also fine for speech). No 8/22.05/24 kHz.
- `auto_clear = true` so a DMA underrun clocks out zeros instead of stale data.
- No I2C, no registers, no init sequence.

```c
#include "driver/i2s_std.h"
#include "driver/gpio.h"

#define AUD_BCLK GPIO_NUM_46   // J6 pin 2
#define AUD_DOUT GPIO_NUM_45   // J6 pin 3
#define AUD_WS   GPIO_NUM_3    // J6 pin 9

static i2s_chan_handle_t s_tx;

void audio_start(uint32_t fs /* 44100 or 48000 (16000 ok) */)
{
    i2s_chan_config_t cc = I2S_CHANNEL_DEFAULT_CONFIG(I2S_NUM_0, I2S_ROLE_MASTER);
    cc.auto_clear = true;
    ESP_ERROR_CHECK(i2s_new_channel(&cc, &s_tx, NULL));
    i2s_std_config_t sc = {
        .clk_cfg  = I2S_STD_CLK_DEFAULT_CONFIG(fs),
        .slot_cfg = I2S_STD_PHILIPS_SLOT_DEFAULT_CONFIG(I2S_DATA_BIT_WIDTH_32BIT, I2S_SLOT_MODE_STEREO),
        .gpio_cfg = {
            .mclk = I2S_GPIO_UNUSED, .bclk = AUD_BCLK, .ws = AUD_WS,
            .dout = AUD_DOUT, .din = I2S_GPIO_UNUSED,
            .invert_flags = { .mclk_inv = false, .bclk_inv = false, .ws_inv = false },
        },
    };
    ESP_ERROR_CHECK(i2s_channel_init_std_mode(s_tx, &sc));
    ESP_ERROR_CHECK(i2s_channel_enable(s_tx));
    // Pre-roll: write >= 250 ms of zero frames before any audio. This powers the board up
    // (rail ~3-5 ms) and waits out the amplifier's delayed unmute (~90-130 ms).
}

void audio_stop(void)
{
    // 1. Fade the last ~10 ms to zero, then write >= 50 ms of zero frames and wait for them to play.
    i2s_channel_disable(s_tx);
    i2s_del_channel(s_tx);
    // 2. Park all three lines LOW. Never call gpio_reset_pin() on them: it enables the internal
    //    pull-up, which must never be on IO45/IO46 at a reset.
    gpio_config_t g = {
        .pin_bit_mask = (1ULL << AUD_BCLK) | (1ULL << AUD_DOUT) | (1ULL << AUD_WS),
        .mode = GPIO_MODE_OUTPUT, .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE, .intr_type = GPIO_INTR_DISABLE,
    };
    gpio_config(&g);
    gpio_set_level(AUD_BCLK, 0); gpio_set_level(AUD_DOUT, 0); gpio_set_level(AUD_WS, 0);
    // The hardware mutes itself in ~1 s and powers off ~2-4.5 s later.
}
```

Arduino-ESP32 3.x equivalent:

- Start: `I2SClass i2s; i2s.setPins(46, 3, 45); i2s.begin(I2S_MODE_STD, 44100, I2S_DATA_BIT_WIDTH_32BIT, I2S_SLOT_MODE_STEREO);`
- Stop: `i2s.end();` then immediately `pinMode(x, OUTPUT); digitalWrite(x, LOW);` for 46, 3 and 45.

**Software volume.** The PCM5102A has no volume control, so scale in software:
`out32 = (int32_t)s16 * vol_q16` with `vol_q16` in 0..65535 from a dB table (e.g. 2 dB steps, -60 to 0 dB).
Mono sources go to both slots.

**Volume defaults.** Start at about -30 dBFS (~65 mVrms). Offer a "headphones" limit at -10 dBFS and a
"line out" limit at 0 dBFS (-1 dBFS on a low cell). There is no hardware way to tell headphones from a
line input.

**When to stop clocks.** Keep the channel enabled (zeros via `auto_clear`) between sounds that are
seconds apart, and call `audio_stop()` after ~5 s of nothing to play. Stopping is the only way into the
0.1 uA state; while clocks run the board draws ~33 mA.

**Deep sleep.** Nothing extra is needed. Non-RTC pads (IO45/IO46) release in deep sleep and the
accessory's pull-downs hold all three lines LOW. Stop audio before sleeping so the rail is off.

**Charging.** No audio-side action is needed. The 0.1 uA idle draw is far below the charger's
termination threshold.

---

## 8. Sources

Datasheets (PDF page numbers used above):

- TI PCM5102A, SLAS859C: https://www.ti.com/lit/ds/symlink/pcm5102a.pdf. p1 failsafe inputs, p5 pins,
  p6 abs max, p7 VIH 0.7 DVDD, p8-10 output, load and supply currents, p15 formats, p16 XSMT,
  p25 3-wire PLL and Table 11, p26 typical application, p28 LDOO and power-down sequence,
  p33 power-save modes.
- TI TPA6138A2, SLOS704B: https://www.ti.com/lit/ds/symlink/tpa6138a2.pdf. p1 features and IEC RC,
  p3 pins and UVP, p4 abs max and Mute thresholds, p5 Iq, VOH, ILIMIT, PO, p6 test conditions,
  p11 gain Table 1.
- TI TPA6132A2, SLOS597B: https://www.ti.com/lit/ds/symlink/tpa6132a2.pdf. p1, p4-5.
- TI TPS7A20, SBVS338H: https://www.ti.com/lit/ds/symlink/tps7a20.pdf. p3-4 pins and smart EN
  pull-down, p5 COUT 1-200 uF, p6 ISHDN, p7 VEN thresholds, tSTR, discharge.
- TI TLV320DAC3100: https://www.ti.com/lit/ds/symlink/tlv320dac3100.pdf. p7-8 AC-coupled headphone
  output, p18 I2C address, p20 reset.

Pop behaviour of the PCM5102A (TI E2E):

- https://e2e.ti.com/support/audio-group/audio/f/audio-forum/765759/pcm5102-pop-noise-when-pause-and-play-music-in-android-music-player
- https://e2e.ti.com/support/audio-group/audio/f/audio-forum/970965/pcm5102a-question-regarding-clock-halt
- https://e2e.ti.com/support/audio-group/audio/f/audio-forum/359885/pcm5102a-click-pop-between-track-changes

Distributor pages:

- LCSC/JLC stock and class: JLC `selectSmtComponentList` API, queried 2026-11-09.
- DigiKey PCM5102APWR: https://www.digikey.ca/en/products/detail/texas-instruments/PCM5102APWR/3727211
- DigiKey TPA6138A2PWR: https://www.digikey.ca/en/products/detail/texas-instruments/TPA6138A2PWR/2552042
- DigiKey TPS7A2033PDBVR: https://www.digikey.co.uk/en/products/detail/texas-instruments/TPS7A2033PDBVR/13566915
- LCSC jack: https://www.lcsc.com/product-detail/C668608.html

Main-board facts: de-link_pcb/docs/HARDWARE.md section 11 (J6 pinout, ESD, strap rule, P+ and 3V3
rules) and section 10 (RTC addresses).
