# Assembly

You need:
- the assembled board;
- headers `J1` (1 × 4) and `J2`, `J3` (1 × 1);
- a spare 2.54 mm female header strip, used as a jig;
- the printed base and lid;
- 2 × M2 × 3 pan-head screws;
- a soldering iron, a multimeter and a small screwdriver.

## 1. Check the board
- Look it over: no solder bridges on `U2`/`U3` (TSSOP), and the jack `J4` seated flat.
- **Meter checks, unpowered:**
  - `J3` pad (pin 12, battery) to either GND pad of `J1` (pins 1/4): no short. Expect high resistance.
  - **Strap lines** (pull-downs to GND):
    - `J1` pins 2 and 3 (`IO46`, `IO45`): about 100 kΩ each, from `R5` and `R6`.
    - The `J2` pad (pin 9, `IO3`): about 10 kΩ, from `R7`, which is also the presence detect.
    - None of them may read low resistance to `J3` (battery): a bridge there holds a boot strap HIGH, and the reader
      won't start.
  - Jack: the sleeve contact to GND reads about 0 Ω. Tip and ring must not be shorted to GND or to each other. Each
    goes through a 10 Ω resistor into the unpowered amplifier, so expect more than 10 Ω, not a short.

## 2. Solder the headers
1. Push `J1` into the four holes labelled 1-4, `J2` into 9 and `J3` into 12, **from the bottom side (no parts on it)**.
   Short tails first, so the plastic bodies sit flat against the bottom.
2. Press the long mating pins into the female header strip; it holds them square while you solder. Set it down with
   the board on top.
3. Solder the six pins on the top side. **Don't trim the tails;** the lid has a pocket for them.
4. Check: measure from the bottom of the board to the pin tips. It should be about 8.5 mm (2.5 mm body + 6.0 mm pin).

## 3. Put the cap together
1. Drop the board into the base, parts up, jack at the base's left end. The two screw holes go over the bosses.
2. Put the lid on. The jack's round nose sits in the lid's left opening.
3. Fit the two M2 × 3 screws from the top, snug only. They clamp the board between the lid and the base floor.
4. Hold the cap so the jack opening is at the left and the flat front faces you. Check that the pins come out of the
   bottom of the cap on the right-hand side.

## 4. Fit it on the reader
1. Turn the reader off, or at least stop any audio.
2. Hold the reader display towards you. Push the cap straight down onto the top edge until it snaps. The pins go
   through the opening in the case's top wall into the expansion header.
3. To remove it, pull straight up by the two ends.

## 5. First power-up (first article)
1. **Boot check, before anything else.**
   - All three audio lines are ESP32-S3 boot strap pins:
     - `IO45` HIGH at reset selects 1.8 V flash power, and the reader won't boot.
     - `IO46` HIGH with `IO0` LOW is an invalid boot mode, so flashing fails.
     - `IO3` is only read if a JTAG eFuse is burned; it isn't by default.
   - The cap only pulls them LOW, which is the correct level for all three, and nothing on it can drive them. Still,
     check this on the first board.
   - With the cap fitted, start the reader from off about 5 times on battery and 5 times on USB, and press reset
     (`SW11`) a few times. Flash it once over USB. It must start every time.
   - Repeat a reset while a tone is playing (step 2). The lines must still read LOW at reset.
   - If it ever fails to start: unplug the cap, and recheck the strap-line readings in section 1.
2. **Before headphones:** with the firmware playing a tone at low volume (see FIRMWARE-NOTES), put a meter on the jack
   with a plug breakout, or on the jack pads.
   - The tip (left) and ring (right) carry an AC signal.
   - The sleeve is ground.
   - The jack's pad mapping comes from the datasheet and the LCSC footprint, but nothing has been built yet: confirm it.
3. **While playing:** the board's 3.3 V rail (U1 output, or C6) reads 3.2-3.3 V. About 3-5 s after the audio stops,
   it drops to 0 V.
4. **Idle current** from the battery pin should be under 1 µA: measure in series with `J3` if you have a way to.
5. **Listen for clicks** at start and stop with sensitive earbuds. A click at stop is the known risk; the firmware's
   fade plus 50 ms of zeros is the fix.
