# Firmware notes

These are recommendations for the e-reader firmware. The firmware repo is not changed by this project. The details are
in research/audio-chain.md section 7.

## Start from existing code
research/software.md has the full findings, with source line references. In short:
- **Audio player:** [mr-tbot/crosspoint-reader](https://github.com/mr-tbot/crosspoint-reader) (branch
  `murphy-m3-support`) has a CrossPoint player for MP3, FLAC, AAC, Opus and more, on the same Free-Ink SDK. It uses
  ESP32-audioI2S 3.4.7, which already sends the format below. Port it behind its `CROSSPOINT_AUDIO_PLAYER` flag, with
  these changes:
  - play 16/32/44.1/48 kHz files at their own rate and resample only the others;
  - software volume with a headphone cap (there is no codec volume);
  - stop after ~5 s paused;
  - show the Audio entry only when the presence check finds the cap;
  - park the pins LOW after every stop.
- **Short interface sounds:** the SDK's `AudioManager` has an unused plain-DAC mode (`I2sDac`). It needs 32-bit slots,
  software volume, ≥ 250 ms of preroll and pin parking first.
- **Read-aloud:** PicoTTS (offline, English and four more languages, 16 kHz output).
- **Licence:** ESP32-audioI2S is GPL-3.0, so images built with the player are GPL-3.0. Keep it behind the flag.

## Pins and format
| Signal | ESP32-S3 GPIO | Expansion header pin |
|---|---|---|
| BCLK | 46 | 2 |
| DOUT (data) | 45 | 3 |
| WS (LRCLK) | 3 | 9 |

- **Format:** standard (Philips) I2S, master TX, stereo, **32-bit data in 32-bit slots**, no MCLK.
- **Sample rates:** 44.1 or 48 kHz; 16 kHz is fine for speech. The DAC can't run 8, 11.025, 22.05 or 24 kHz without
  MCLK, so resample those, and only those: a simple resampler dulls the treble of 44.1 kHz music (research/software.md
  section 3.1).
- **`auto_clear = true`,** so an underrun plays zeros.
- **No I2C, no registers.**

## Strap pins: read this first
All three lines are ESP32-S3 strapping pins, sampled at every chip reset:

| GPIO | Strap | If it reads HIGH at reset |
|---|---|---|
| IO45 | Flash supply voltage (VDD_SPI) | Selects 1.8 V: **the reader does not boot**, and looks dead until the cap is removed |
| IO46 | Boot mode, together with IO0 | IO0 LOW with IO46 HIGH is an invalid mode: download mode and flashing fail |
| IO3 | JTAG source | Only read if the STRAP_JTAG_SEL eFuse is burned (not by default) |

- **Board side:** it only pulls the three lines LOW, the correct level for each. That's 100 kΩ on IO45/IO46 and
  10 kΩ on IO3. Nothing on the board can drive a line.
- **Firmware side:**
  - Never enable the internal pull-up on IO45 or IO46.
  - Never call `gpio_reset_pin()` on any of the three: it turns the pull-up on.
  - Park all three LOW when audio stops.
- **Why the pins are mapped this way:** data is on IO45 because it sits LOW through every silence. Word select, the
  line most likely to be left HIGH, is on IO3, the least critical strap.
- **The presence check below uses IO3 only.**

## Presence detection
- IO3 has a 10 kΩ pull-down on the board (`R7`). Turn on the ESP32's internal pull-up (about 45 kΩ) and read the pin:
  - **Cap fitted:** about 0.6 V. That reads LOW: the ESP32-S3's LOW threshold is 0.25 × 3.3 V = 0.83 V.
  - **No cap,** or the light attachment, which has no pin 9: reads HIGH.
- **When to check:** at boot, after each wake from sleep, and before starting audio. Never while I2S is running.
- **Strap safety:**
  - The pull-up is on for 5 ms.
  - A reset in that window clears it before the straps are sampled.
  - IO3 isn't a boot-critical strap anyway.
- **Side effects:**
  - The check costs about 60 µA for 5 ms.
  - The one rising edge nudges the board's on/off detector by a few mV; its regulator stays off.

```c
// After boot, never while I2S is running. IO3 only: IO45/IO46 never get a pull-up.
bool audio_cap_present(void)
{
    gpio_config_t g = { .pin_bit_mask = 1ULL << GPIO_NUM_3, .mode = GPIO_MODE_INPUT,
                        .pull_up_en = GPIO_PULLUP_ENABLE, .pull_down_en = GPIO_PULLDOWN_DISABLE,
                        .intr_type = GPIO_INTR_DISABLE };
    gpio_config(&g);
    vTaskDelay(pdMS_TO_TICKS(5));                   // the board's 10 nF pump capacitor settles in < 1 ms
    bool present = gpio_get_level(GPIO_NUM_3) == 0; // the cap's 10k pull-down wins over the ~45k pull-up
    gpio_set_pull_mode(GPIO_NUM_3, GPIO_FLOATING);
    gpio_set_level(GPIO_NUM_3, 0);                  // park LOW, as after audio stops
    gpio_set_direction(GPIO_NUM_3, GPIO_MODE_OUTPUT);
    return present;
}
```

Fit the cap with the reader off (docs/ASSEMBLY.md). If the cap is fitted while the reader sleeps, the check on wake
catches it.

## Start, stop, sleep
- **Start:** enable I2S, then write **at least 250 ms of zeros** before real audio. The board powers itself up from the
  word-select clock (its rail is up in 3-5 ms), and the amplifier unmutes about 90-130 ms later.
- **Stop:**
  1. Fade the last ~10 ms.
  2. Write **at least 50 ms of zeros**.
  3. Disable and delete the I2S channel.
  4. **Drive all three pins LOW** as plain outputs.
  - **Never call `gpio_reset_pin()` on them:** it turns on the internal pull-up, and `IO45`/`IO46` must never be
    pulled up at a reset (see "Strap pins" above).
  - The board mutes about 1 s later and switches itself off 2-4.5 s later. Idle draw is then about 0.1 µA.
- **Between sounds a few seconds apart:** keep the channel running (zeros). Stop after about 5 s of nothing to play;
  while the clocks run the board draws about 33 mA.
- **Deep sleep:** stop audio first. The board's pull-downs hold the lines LOW.

## Volume
- **No hardware volume:** scale in software, for example `out32 = (int32_t)s16 * vol_q16` with `vol_q16` from a dB
  table in 2 dB steps from -60 to 0 dB.
- **Default:** about **-30 dBFS**.
- **Limits:** about -10 dBFS for headphones and 0 dBFS for line out. The hardware can't tell which is plugged in.
- **Mono sources:** send the same samples to both slots.

## Tone test (ESP-IDF 5.x; also builds in Arduino-ESP32 3.x)
```c
#include <math.h>
#include "driver/i2s_std.h"
#include "driver/gpio.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#define AUD_BCLK GPIO_NUM_46   // J6 pin 2
#define AUD_DOUT GPIO_NUM_45   // J6 pin 3
#define AUD_WS   GPIO_NUM_3    // J6 pin 9
#define FS 48000

static i2s_chan_handle_t tx;

static void write_frames(const int32_t *buf, size_t frames)
{
    size_t done;
    i2s_channel_write(tx, buf, frames * 2 * sizeof(int32_t), &done, portMAX_DELAY);
}

void audio_tone_test(void)
{
    i2s_chan_config_t cc = I2S_CHANNEL_DEFAULT_CONFIG(I2S_NUM_0, I2S_ROLE_MASTER);
    cc.auto_clear = true;
    i2s_new_channel(&cc, &tx, NULL);
    i2s_std_config_t sc = {
        .clk_cfg  = I2S_STD_CLK_DEFAULT_CONFIG(FS),
        .slot_cfg = I2S_STD_PHILIPS_SLOT_DEFAULT_CONFIG(I2S_DATA_BIT_WIDTH_32BIT, I2S_SLOT_MODE_STEREO),
        .gpio_cfg = { .mclk = I2S_GPIO_UNUSED, .bclk = AUD_BCLK, .ws = AUD_WS, .dout = AUD_DOUT, .din = I2S_GPIO_UNUSED },
    };
    i2s_channel_init_std_mode(tx, &sc);
    i2s_channel_enable(tx);

    static int32_t buf[480 * 2];                    // 10 ms of stereo frames
    for (int i = 0; i < 30; i++) {                  // 300 ms of zeros: power-up + amp unmute
        for (int k = 0; k < 960; k++) buf[k] = 0;
        write_frames(buf, 480);
    }
    const float amp = 0.0316f * 2147483647.0f;      // -30 dBFS
    float ph = 0, dph = 2.0f * (float)M_PI * 1000.0f / FS;   // 1 kHz
    for (int i = 0; i < 200; i++) {                 // 2 s of tone; left only for the first second
        for (int k = 0; k < 480; k++) {
            int32_t s = (int32_t)(amp * sinf(ph)); ph += dph; if (ph > 2 * M_PI) ph -= 2 * M_PI;
            buf[2 * k]     = s;                     // left (tip)
            buf[2 * k + 1] = (i < 100) ? 0 : s;     // right (ring) joins after 1 s
        }
        write_frames(buf, 480);
    }
    for (int i = 0; i < 10; i++) {                  // 100 ms of zeros before stopping
        for (int k = 0; k < 960; k++) buf[k] = 0;
        write_frames(buf, 480);
    }
    i2s_channel_disable(tx);
    i2s_del_channel(tx);
    gpio_config_t g = { .pin_bit_mask = (1ULL << AUD_BCLK) | (1ULL << AUD_DOUT) | (1ULL << AUD_WS),
                        .mode = GPIO_MODE_OUTPUT, .pull_up_en = GPIO_PULLUP_DISABLE,
                        .pull_down_en = GPIO_PULLDOWN_DISABLE, .intr_type = GPIO_INTR_DISABLE };
    gpio_config(&g);
    gpio_set_level(AUD_BCLK, 0); gpio_set_level(AUD_DOUT, 0); gpio_set_level(AUD_WS, 0);
}
```

You should hear 1 s of 1 kHz in the left ear, then both ears for 1 s. If the right ear comes first, tip and ring are
swapped: check the jack mapping (docs/ASSEMBLY.md, step 5).
