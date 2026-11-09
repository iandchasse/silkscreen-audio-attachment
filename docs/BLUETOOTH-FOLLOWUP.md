# Bluetooth: follow-up, not in rev A

Summary of research/bluetooth.md (2026-11-09). Nothing here was bench-tested.

**Why rev A has none:**
- The e-reader's ESP32-S3 has Bluetooth LE only. It can't send Bluetooth headphone audio (A2DP, Classic Bluetooth),
  and it can't do LE Audio either.
- Any Bluetooth output therefore needs a second radio on the attachment, and the only one that needs no firmware is
  not ready to design in.

**Works today:** plug a battery-powered 3.5 mm Bluetooth transmitter into the jack. It draws nothing from the
e-reader, it's certified, and it pairs with any headphones. Cost is about US$15-30.

**Best integrated candidate: KCX_BT_EMITTER (V1.7)**, an analog-in Bluetooth transmitter module on a Jieli AC1852AP.
- No host, UART or firmware: on power-up it joins the first headphones in pairing mode and remembers them.
- About 24 × 15 × 3 mm, about US$2-4 (AliExpress/Amazon; JLC lists it with no stock).
- About 35-40 mA while on. It has no auto-off, so it would need a slide switch from the battery pin (e.g. SK12D07VG4,
  LCSC C393937, 500 mA; not the 50 mA MSK12C02).
- Unverified: pad pitch (2.0 vs 1.27 mm), current, whether it runs at 3.0 V, certification.

**To do it in a rev B (about an evening of bench work first):**
1. Buy 2-3 modules. Measure the pad pitch, the current at 3.0 / 3.7 / 4.2 V and the range with the cap fitted.
2. If they're good: add the footprint, a fitted slide switch, 1 µF coupling caps from the DAC's line outputs (before
   the headphone driver), and a copper-free antenna corner at the top edge under the cap. PLA/PETG is fine over the
   antenna; avoid conductive filament.
3. **Optional auto-off:** an I2C-controlled switch (the expansion header's SDA/SCL are unused on this board) can power
   the module only while audio plays. That is a small firmware change, not a second firmware project.

**Rejected:**
- I2S-input Bluetooth modules: setup over UART, patchy source support, no stock.
- A second ESP32: a second firmware project and 80-130 mA.
