# Bluetooth audio output for the audio attachment

Status: research done 2026-11-09 (agent, owner away). Not committed. Nothing bench-tested.

## Question

Can the J6 audio daughterboard (I2S from the ESP32-S3 -> DAC -> 3.5 mm jack) also send
audio to Bluetooth headphones, simply, with no spare GPIO/UART for control, near-zero idle
draw from P+ (3.0-4.2 V, live in deep sleep), and under ~5 mA average while USB charges?

## Constraints recap

- ESP32-S3: BLE 5 only. No BR/EDR (Classic), so no A2DP. No LE Audio (LC3/ISO channels) either.
- J6 gives BCLK, WS, DATA (I2S), P+, GND, I2C (shared with touch + RTC). No free GPIO, no UART.
- Idle draw from P+ must be tens of uA. Charging-time average < ~5 mA.
- Owner wants basic, standard parts, no fiddly steps.

## 1. Options

### (a) Analog-input BT transmitter modules (KCX_BT_EMITTER and similar)

KCX_BT_EMITTER (Shenzhen Kechuangxin, Jieli-class BT audio SoC; firmware V1.1 / V1.2 / V1.7 seen in the wild).
Takes line-level stereo L/R and sends A2DP to a sink (headphones, speaker).

Pairing without a host (from the vendor AT manual, firmware V1.7, via the Mark-MDO47 repo):
- The auto-connect filter tables (10 MAC slots + 10 name slots) are EMPTY by default, and "When all
  record spaces are empty, no MAC address is matched and filtered, and it will be connected when it is
  searched". So out of the box it powers up, searches, and connects to whatever A2DP sink it finds in
  pairing mode. No UART, no host, no configuration.
- It also records `Last_Add` (last connected MAC) for reconnection.
- A PAIR button (pin) "Disconnect[s] the current connection and search[es] for pairing again"; AT+PAIR does the same.
- Optional: a one-time UART session (AT+ADDLINKADD=<mac>) locks it to specific headphones so it never
  grabs a neighbour's speaker. Not needed for a single-user device; the UART is 5 V-ish TTL per Mark-MDO47.
- AT+POWER_OFF exists (wake = button or power cycle). There is no documented auto-off timer, so a hard
  power switch is the only way to guarantee zero idle draw.

Electrical (retail listings, not a datasheet; no official electrical spec found):
- Supply 3.3-5 V (some listings 3.5-5 V); operating current ~35 mA (uelectronics), <=40 mA (Cirkit Designer).
- Line-level input, NOT speaker level. Mark-MDO47: keep audio ground separate from digital ground
  (route the module's audio GND to the DAC's analog ground), and mute any parallel wired speaker
  because BT adds latency.
- Mark-MDO47: "It is not the very latest Bluetooth spec so it doesn't work with every single Bluetooth
  speaker, but it works with many". SBC codec only (no aptX/AAC claimed).

Sourcing: AliExpress/Amazon/Tokopedia/hobby stores (~US$2-4). JLC lists one variant as
C9900041854 `KCX_BT_EMITTER,KCX_BT_L24_H15_P2.0_11` (24 x 15 mm, 11 pins, 2.0 mm pitch) as a
"global sourcing / new arrival" part with stock 0 (checked 2026-11-09), so it is not a normal LCSC
stock part. No FCC/CE module certification found.

### (b) I2S-input BT source modules

- Feasycom FSC-BT1035 / BT1036 / BT1026 / BT1046 / BT1058 / BT1006A (Qualcomm/CSR-based, 13 x 26.9 mm
  LCC-52 etc.): JLC lists them all as stock 0 global-sourcing parts (2026-11-09). Feasycom says only some
  modules support A2DP Source; the FSC-BT95X/90x manuals list "Scan and Connect Nearby Device <a2dp source only>"
  and "Auto Link" as AT commands, i.e. source mode and auto-link are set up over UART. An EDAboard user
  trying BT955/BT1036 with I2S got silence. Every path here needs UART configuration (at least once), a
  vendor firmware with source profile, and a 13 x 27 mm module. Not basic.
(Module photo in the Mark-MDO47 repo: Jieli **AC1852AP** SoC, 24 MHz crystal, printed meander antenna at one short
end, 11 castellated pads at the other. Pin table from the same repo: 1 +5V, 2 PGND, 3 LED (status), 4 RX, 5 TX,
6 IN_L, 7 IN_R, 8 AGND, 9 DP, 10 DM (USB-audio input), 11 CON ("External button, low level trigger is valid").
Size ~24-25 x 15 x 3 mm (JLC footprint name L24_H15; Cirkit Designer 25 x 15 x 3 mm). Pad pitch is NOT
consistent across sources: JLC's footprint says 2.0 mm, the photo of the 15 mm edge looks nearer 1.27 mm.
Measure a module in hand before drawing a footprint. A Spanish V1.7 listing: red LED = transmit mode,
blinking when not connected. Retail listings claim BT 4.1 / 4.2 / 5.1 / 5.3 for "the same" module.)

- Microchip BM83: A2DP sink module (speaker/headset side). JLC stock 0. Not a source.
- Qualcomm QCC30xx/QCC51xx: source mode needs a custom ADK firmware build (licensed SDK). No.
- Realtek RTL8763 modules: sink-focused, SDK firmware. No.

### (c) Second MCU with Classic BT (ESP32-WROOM / PICO as A2DP source)

Works in principle: original ESP32 has BR/EDR, ESP-IDF has an A2DP source API, and pschatzmann's
ESP32-A2DP `BluetoothA2DPSource` takes PCM from a callback (44.1 kHz/16-bit/stereo). No ready
"I2S in -> A2DP out" example was found; the library README also warns its old I2S integration is gone
with Arduino core 3 / IDF 5.
- Parts: ESP32-WROOM-32E-N4 LCSC C701341 (US$3.76, 56k stock, 18 x 25.5 mm, listing quotes 112 mA RX /
  239 mA TX peaks) or ESP32-PICO-V3-02 C908392 (US$5.69, 2.7k stock, SiP, needs its own antenna design).
- Burden: a second firmware project (I2S slave capture, resample to 44.1 kHz, A2DP source, scan/pair
  logic, NVS bonding), a way to flash it (UART/USB pads), a 3.3 V regulator + load switch, and a pairing
  UI with no buttons or screen (or an I2C-slave protocol so the e-reader drives it - even more firmware).
- Power: roughly 80-130 mA average while streaming (estimate from the RX/TX figures), 2-3x the KCX module.
Verdict: rejected for rev A per the brief (second firmware project when a no-firmware module exists).

### (d) Other routes (LE Audio etc.)

- LE Audio from the S3 itself: not possible. LE Audio needs BT 5.2 isochronous channels (CIS/BIS);
  the S3 controller is BLE 5.0, and Espressif's ESP-BLE-AUDIO / ESP-BLE-ISO docs exist only for newer
  targets (ESP32-S31, ESP32-H4 pages), with no ESP32-S3 entry. Also, most headphones in use are still
  Classic A2DP only, so LE Audio would not reach them anyway.
- A2DP from the S3: impossible (no BR/EDR radio). No firmware trick changes this.
- Zero-hardware route: plug a consumer battery-powered 3.5 mm Bluetooth transmitter (1Mii, daskmenbo,
  UGREEN and many others, ~US$15-30, FCC/CE certified, own battery, own button) into the attachment's
  jack. Draws nothing from P+, already certified, works today with rev A as designed. Downside: a
  dongle hanging off the reader, one more thing to charge, ~40 ms (low-latency codec) to ~200 ms (SBC)
  latency, which does not matter for audiobooks/TTS.

## 2. Integration of the best integrated option (KCX_BT_EMITTER)

Power
- Feed the module's +5V pin straight from P+ (3.0-4.2 V) through a series SPDT slide switch ("BT off/on").
  No regulator: listings rate the pin 3.3-5 V and Jieli BT SoCs normally run from a Li-ion cell directly,
  but there is NO datasheet - bench-check that it pairs and streams cleanly at 3.3 V and 3.0 V (low
  battery); if it browns out, the fallback is a small 5 V boost behind the same switch.
- Switch: Shou Han SK12D07VG4 (LCSC C393937, 500 mA, right-angle THT, 84k stock) can carry the load
  directly. Do NOT use MSK12C02 (C431540) in the power path: rated 50 mA, too close to the module's
  35-40 mA plus RF peaks. (Or let the switch drive a load-switch EN so it carries no current.)
- Idle: switch off = 0 uA. There is no auto-off in the module (only AT+POWER_OFF over UART), so a
  module left switched on searches/streams at ~35-40 mA. That breaks the "tens of uA idle" and
  "<5 mA while charging" budgets, so the switch is mandatory, and it must be OFF by default.
- Optional auto-off (rev B, if wanted): if the DAC/codec chosen for the board has an I2C-controlled
  GPIO, or via a 1-uA-class I2C GPIO expander (address must not clash with touch + RTC), firmware can
  enable a load switch for the module only while "Bluetooth" output is selected, read the LED pin for
  "connected", and pulse CON to re-pair. Small change inside the existing e-reader firmware, not a
  second firmware project. Not needed for a first version.

Audio path
- Tap the DAC's LINE output (before any headphone amp / volume stage if there is one) into IN_L/IN_R
  through 1 uF series caps (module input coupling is unknown; extra caps are harmless). Line level
  (~0.5-1 Vrms full scale) is what it expects; do not feed speaker-level. The module's own volume
  defaults to max (31/31).
- AGND (pin 8) to the DAC's analog ground / jack sleeve ground; PGND (pin 2) to the power ground at the
  P+ entry (Mark-MDO47 warns against tying audio ground to digital ground).
- Jack and BT both play if headphones are also plugged in; BT lags the wire, so use one at a time.

Mechanical / antenna
- ~25 x 15 x 3 mm. Put the antenna end at the very top edge of the daughterboard under the printed
  cap, with NO copper on any layer under or beside the antenna (keep-out of the antenna area plus
  ~3-5 mm), ideally overhanging the board edge, away from the battery and the main board's ground pour.
- PLA/PETG/ASA caps are fine at 2.4 GHz; no metallic, carbon-fibre or conductive filament, no metal paint.
- Slide switch needs a slot in the cap; label it "BT".

Pairing UX
1. Put the headphones in pairing mode.
2. Slide "BT" on. The module searches and connects to the first A2DP sink it finds (default filter is
   empty). LED blinks while searching, steady when connected.
3. Next time: slide on with the headphones on; it reconnects to the last device.
4. New headphones: turn the old ones off and put the new ones in pairing mode (or press a button on
   CON, which drops the link and re-pairs).
Caveat: with an empty filter it could grab a stranger's speaker that happens to be in pairing mode.
Locking to one MAC needs a one-time UART session (AT+ADDLINKADD) with a TTL adapter - optional.
Codec SBC only; latency typically ~150-250 ms for SBC (fine for audiobooks/TTS). Range nominal 10 m.

## 3. Recommendation

Leave Bluetooth OUT of the populated rev A build. Make it a documented follow-up, with a free DNP tap
on rev A so the follow-up needs no respin of the audio path.

Rev A (costs nothing in the default build):
- DNP 1x5 2.54 mm pad row "BT": SW_P+ (P+ through a DNP SK12D07VG4 slide switch footprint), PGND,
  LINE_L, LINE_R (each after a DNP 1 uF cap from the DAC line out), AGND.
- Leave a ~27 x 17 mm copper-free corner at the top edge under the cap if board space allows, so a
  module can sit there with its antenna clear.

Why not populate it now:
1. No datasheet: current (35-40 mA from retail listings only), minimum supply voltage (we need 3.0 V)
   and the pad pitch (2.0 vs ~1.27 mm across sources/versions) are all unverified. A footprint drawn
   from listings may not fit the modules that arrive.
2. Not assemblable: JLC/LCSC has no stock (C9900041854 is a stock-0 global-sourcing entry), so it is
   an AliExpress part hand-soldered on castellated pads - the fiddly step the owner wants to avoid.
3. Power: it needs a user-operated switch (or I2C/firmware gating) to meet the idle and charging
   budgets; a forgotten "on" switch drains ~35-40 mA.
4. Uncertified radio module (no FCC/CE ID found) - fine for a personal build, a problem for boards
   given to others.
5. A certified plug-in 3.5 mm transmitter already gives Bluetooth headphones with zero board work.

Follow-up plan (when the owner is back, ~1 evening):
- Buy 2-3 KCX_BT_EMITTER V1.7 (AliExpress, ~US$2-4). Measure: pad pitch and outline; current while
  searching / connected / streaming at 3.0, 3.7 and 4.2 V; whether it works at 3.0 V; hiss with the
  DAC; pairing with the owner's headphones; range with the cap fitted.
- If good: rev B gets the measured footprint, the slide switch populated, the antenna corner, and
  optionally the I2C-gated auto-off.
- Meanwhile, for Bluetooth headphones on rev A: plug a battery-powered 3.5 mm Bluetooth transmitter
  into the jack.

Rejected: Feasycom/Qualcomm/Realtek I2S modules (UART setup, source-mode support patchy, stock 0),
BM83 (sink only), a second ESP32 (second firmware project, ~80-130 mA), LE Audio (S3 can't).

## Sources

- Mark-MDO47, BluetoothAudioTransmitter_KCX_BT_EMITTER (README, V1.7 AT command notes, pin-function and
  board photos): https://github.com/Mark-MDO47/BluetoothAudioTransmitter_KCX_BT_EMITTER
- Vendor AT manual (Shenzhen Kechuangxin, 2022-11), in that repo: specs/BT GY19733-CN.zh-CN.en.pdf
- Electro-Tech-Online thread (V1.x notes, 10 stored MACs): https://www.electro-tech-online.com/threads/kcx_bt_emitter-low-cost-bluetooth-bt-audio-module.158156/
- uelectronics KCX V1.7 listing (3.5-5 V, 35 mA, LED behaviour; via search snippet, page blocks fetch):
  https://uelectronics.com/producto/kcx-bt-emitter-v1-7-modulo-de-audio-estereo-bluetooth/
- Cirkit Designer KCX page (3.3-5 V, <=40 mA, 25 x 15 x 3 mm; page has errors, low confidence):
  https://docs.cirkitdesigner.com/component/6b5d29f7-39f2-4a93-b921-d9ac79168382/kcxbtemitter
- Sigmanortec KCX listing (35 mA, BT 5.1): https://sigmanortec.ro/en/audio-transmitter-module-bluetooth-51-ble
- JLC parts API (checked 2026-11-09): KCX C9900041854 stock 0; Feasycom FSC-BT10xx stock 0; BM83 stock 0;
  ESP32-WROOM-32E-N4 C701341; ESP32-PICO-V3-02 C908392; SK12D07VG4 C393937; MSK12C02 C431540.
- Feasycom forum, A2DP source support varies by module: https://forum.feasycom.com/d/75-a2dp-source
- Feasycom FSC-BT95X manual (source-only auto-link AT commands): https://manuals.online/feasycom/control-unit/fsc-bt95x-series/user-manual/1kop2
- EDAboard, BT955/BT1036 I2S trouble: https://edaboard.com/threads/feasycom-bt955-bt1036-as-i2s-dac.413637
- pschatzmann ESP32-A2DP: https://github.com/pschatzmann/ESP32-A2DP
- ESP-IDF A2DP API (original ESP32): https://docs.espressif.com/projects/esp-idf/en/v5.4.4/esp32/api-reference/bluetooth/esp_a2dp.html
- ESP-IDF LE Audio docs (ESP32-S31 / ESP32-H4 targets only): https://docs.espressif.com/projects/esp-idf/en/latest/esp32s31/api-guides/ble/ble-audio.html
- Consumer 3.5 mm transmitters (example): https://shopsavvy.com/reviews-tldr/1mii-bluetooth-5.3-audio-adapter.md
