# Software for the audio attachment: what exists, what fits, what it will sound like

Researched 2026-11-09. Nothing in the firmware repos was changed. The hardware side is in `audio-chain.md`; the
settings and code to write are in `../docs/FIRMWARE-NOTES.md`.

**Versions checked:**
- Silkscreen firmware: CrossPoint `aeb340de` (silkscreen branch), Free-Ink SDK `6c0783f` (2026-11-08). Both use the
  pioarduino `55.03.x` platform (Arduino-ESP32 3.x on ESP-IDF 5.5).
- [mr-tbot/crosspoint-reader](https://github.com/mr-tbot/crosspoint-reader), branch `murphy-m3-support`, release
  `murphy-m3-v1.1` (2026-07-30).
- [ESP32-audioI2S](https://github.com/schreibfaul1/ESP32-audioI2S) tag `3.4.7`, the version that fork pins.
- ESP-IDF 5.5.5 (the local `framework-espidf` package), for the I2S driver's pin handling.

## 1. Summary
- **An audio player already exists for CrossPoint:** mr-tbot's Murphy M3 port, built on the same Free-Ink SDK. It is
  the recommended starting point. It needs four changes for this board (section 3) plus pin parking (section 5).
- **Nothing goes upstream.** CrossPoint rejected the player as out of scope, and CrossInk's `SCOPE.md` excludes audio.
  It would live on the `silkscreen` branches behind a build flag.
- **The SDK's own `AudioManager`** has an unused plain-DAC mode (`I2sDac`). It is fine for short WAV interface sounds
  after five fixes (section 4).
- **No library touches the strap pins** (no pull-ups, no `gpio_reset_pin()`), but none parks them LOW either. The
  firmware has to do that (section 5).
- **No e-ink reader does text-to-speech** in anything found. PicoTTS is the best offline engine for adding it
  (section 6).
- **Expected sound:** like wired earbuds on a phone's headphone jack: about 20 kHz bandwidth, roughly CD-level noise.
  The Metalio eInk4's 16 kHz path is Bluetooth-call quality by comparison (section 8).

## 2. Existing firmware
| Project | Hardware | Audio | Use to us |
|---|---|---|---|
| **mr-tbot/crosspoint-reader** (`murphy-m3-support`), MIT | Murphy M3 (HamGeek M3): ESP32-S3R8, 8 MB PSRAM, ES8388 codec | Full player: MP3, WAV, FLAC, AAC, M4A, Opus, Vorbis | **Port it** (section 3) |
| Free-Ink SDK `AudioManager` (in both our forks) | Murphy M3 (ES8388), M5 PaperColor (ES8311), Metalio eInk4 (module) | 16-bit PCM WAV only | `I2sDac` mode for short sounds (section 4) |
| Upstream CrossPoint / CrossInk | Xteink X4/X3 and others | None | Out of scope upstream |
| Open Book Touch (Oddly Specific Objects), MIT firmware | ESP32-S3, 4.26" touch e-paper | None found | — |
| Diptyx | Dual-screen ESP32-S3 | None found | — |
| BacaIn (khad1r), CC BY-NC-SA 4.0 | ESP32-S3 e-ink reader | None found | — |

Upstream status:
- [CrossPoint PR 2794](https://github.com/crosspoint-reader/crosspoint-reader/pull/2794) (the Murphy M3 port with the
  player) was closed on 2026-07-30. A maintainer wrote that the audio player is "definitely outside scope".
- CrossInk's `SCOPE.md` line 43 says no audio players or audiobooks.
- [CrossPoint issue 290](https://github.com/crosspoint-reader/crosspoint-reader/issues/290) asked for an X4 music player.
  It closed because the X4's ESP32-C3 has no Bluetooth audio.

Outside the e-reader world, whole firmwares such as ESPuino (audiobook player), Squeezelite-ESP32 and ESPHome support
PCM5102A boards. They are firmwares for other devices, so only their library choices matter here. Most use
ESP32-audioI2S.

## 3. The mr-tbot audio player
**What it has:**
- `src/activities/audio/AudioPlayerActivity.cpp` (393 lines): track name, position in the folder playlist,
  elapsed/total time, tap-to-seek bar, prev/pause/next, volume.
- Folder playlists auto-advance. Volume persists in Settings and the web API. No auto-sleep mid-track.
- An **Audio** entry on the home screen opens a file browser that starts at `/Audio`, `/Audiobooks` or `/Music` if one
  exists.
- Decoding runs on its own pinned FreeRTOS task. One mutex covers every decoder call, because the library isn't
  thread-safe.

**Build gating** (`platformio.ini`):
```ini
build_flags = -DCROSSPOINT_AUDIO_PLAYER=1
lib_deps =
  AudioManager=symlink://freeink-sdk/libs/hardware/AudioManager
  ESP32-audioI2S=https://github.com/schreibfaul1/ESP32-audioI2S.git#3.4.7
```

**Hardware coupling:**
- Pins come from the SDK board config:
  `audio->setPinout(pins.bclk, pins.lrclk, pins.dout, pins.mclk)` with `pins = BoardConfig::ACTIVE.audio`.
- Volume is the **codec's** analog volume through `AudioManager::setVolume()`. Digital volume is pinned at full scale
  with `audio->setVolume(21)`.

**Changes for this board:**
1. **Sample rate.**
   - The player never sets an output rate, so 3.4.7 plays at the file's own rate (`SR_ORIGIN`, the default in
     `Audio.h:498`). The Murphy's codec has a master clock and takes any rate; our DAC doesn't.
   - The PCM5102A plays 16, 32, 44.1 and 48 kHz (`audio-chain.md` risk 8). It is **silent** at 8, 11.025, 22.05 and
     24 kHz, which are common audiobook rates.
   - Fix: play 16/32/44.1/48 kHz at the source rate. Call `setOutputSampleRate(Audio::SR_48000)` only for the other
     rates, decided per file from the rate the decoder reports. Don't force 48 kHz for everything: the library's
     resampler dulls the treble (section 3.1).
2. **Volume.**
   - With no codec, `AudioManager::setVolume()` does nothing, so the player would send full scale: about 2 Vrms
     straight into headphones.
   - Fix: map the volume setting onto the library's own volume (`setVolume()`, 0-21 by default, or more steps via
     `setVolumeSteps()`), with a headphone cap and a quiet default. See FIRMWARE-NOTES "Volume".
3. **Long pauses.**
   - `pauseResume()` keeps the I2S channel enabled, and with `auto_clear` it sends zeros, so the clocks keep running.
     Resume is instant, but the board stays powered at about 33 mA.
   - Fix: after about 5 s paused, save `getAudioCurrentTime()` and call `stopSong()`, which disables the channel. Then
     park the pins (section 5). Resume with `connecttoFS(fs, path, savedSeconds)` (its `fileStartTime` argument,
     `Audio.h:153`). The first ~0.1 s after resume is lost while the amp unmutes.
4. **Presence.**
   - The Audio entry exists whenever the build flag is on.
   - Fix: show it only when `audio_cap_present()` (FIRMWARE-NOTES) finds the cap. Run the check before
     `setPinout()`, or after a stop and park, never while the decoder holds IO3.

**Board config entry** for the SDK (`BoardConfig.h`). The field order is output, bclk, lrclk, dout, mclk, enable,
enableActiveHigh, ampEnable, codecSda, codecScl, codecAddr, buzzer:
```cpp
// Silkscreen audio attachment on J6: PCM5102A, no MCLK, no codec control, no enables.
constexpr AudioConfig SILKSCREEN_J6_AUDIO = {AudioOutput::I2sDac, 46, 3, 45, PIN_UNASSIGNED, PIN_UNASSIGNED, true,
                                             PIN_UNASSIGNED, PIN_UNASSIGNED, PIN_UNASSIGNED, 0, PIN_UNASSIGNED};
```
`FREEINK_CAP_AUDIO` (`BoardConfig.h:394`) currently covers only Murphy, M5 and Metalio; add the Silkscreen devices.

### 3.1 ESP32-audioI2S 3.4.7 against our hardware (from the source)
| Point | Finding | Where |
|---|---|---|
| Slot format | Philips I2S, **32-bit data in 32-bit stereo slots**, the format FIRMWARE-NOTES asks for (BCLK = 64 fs) | `Audio.cpp:5845`, `:6289` |
| MCLK | Unused unless `setPinout()` is given one | `Audio.cpp:5849`, `:5866-5874` |
| Underrun | `auto_clear = true`: sends zeros, not stale DMA data | `Audio.cpp:5835` |
| Output rate | `SR_ORIGIN` by default; `SR_44100` / `SR_48000` turn on the resampler. The README's "always 48 kHz" is not true for 3.4.7 | `Audio.h:147`, `:498`; `Audio.cpp:6410-6418` |
| Stop | `stopSong()` → `I2Sstop()` disables the channel: clocks stop, so the board powers itself down | `Audio.cpp:404-411`, `:3228` |
| Pause | Channel stays enabled, zeros flow, board stays on | `Audio.cpp:3254-3268` |
| PSRAM | "PSRAM is mandatory". The N16R8 module has 8 MB | `Audio.cpp:13` |
| Strap pins | No `gpio_reset_pin()`, no pull-up calls anywhere in the source | grep of `Audio.cpp` |
| Licence | **GPL-3.0** (section 7) | GitHub licence API |

**Resampler quality.**
- `resampleI2Soutput()` (`Audio.cpp:3310`) is linear interpolation followed by one 2nd-order Butterworth low-pass
  (`makeButterworthLPF_Q31()`, `:3270`).
- The filter is designed at 0.45 × the source rate but runs at the output rate, so its corner sits at about 21.6 kHz.
- Calculated response for a **44.1 kHz** file resampled to 48 kHz:

| Frequency | Loss |
|---|---|
| 5 kHz | -0.4 dB |
| 10 kHz | -1.7 dB |
| 15 kHz | -4.3 dB |
| 18 kHz | -6.8 dB |

- **Aliasing:** a strong 10 kHz tone also produces a 13.9 kHz image about 23 dB down; at 5 kHz it is 36 dB down.
- For music this sounds like the treble turned down a notch, with a little grit on cymbals. That's why section 3
  plays 44.1/48 kHz files untouched.
- For a **22.05 kHz** speech file the loss is -1.5 dB at 5 kHz and -4 dB at 8 kHz: slightly softer "s" sounds, on
  files that are band-limited anyway. Acceptable.

## 4. Free-Ink SDK `AudioManager`, `I2sDac` mode
`libs/hardware/AudioManager/src/AudioManager.cpp` in the SDK (written upstream by Free-Ink; present in
`fk-upstream/main`).
- **What it does:**
  - Plays 16-bit PCM WAV, mono or stereo, from caller-supplied read/seek callbacks (SD, LittleFS or a memory buffer).
  - Runs on its own task, with an optional loop for alarms.
- **Status on our board:** `I2sDac` is in `AudioOutput` (`BoardConfig.h:617`) and in `present()`, and `codecInit()`
  returns true for `codecAddr == 0`. **No board uses it yet.**

**Gaps for this board:**

| Gap | Where | Effect | Fix |
|---|---|---|---|
| 16-bit slots (BCLK = 32 fs) | `AudioManager.cpp:285` | 16 kHz WAVs are silent: the PCM5102A needs 64 fs at 16 kHz. 32/44.1/48 kHz play. The rate check at `:238-239` still admits 8-48 kHz | 32-bit slots for `I2sDac`, or reject the rates the DAC can't play |
| No volume without a codec | `setVolume()` returns at `:145` when `codecAddr == 0` | Full scale into headphones | Software gain in the play loop, as the Metalio path already does |
| About 21 ms of preroll | `:496-503`: two writes of 2,048 bytes = 1,024 frames | The board needs ~250 ms of clocks before sound is heard (rail 3-5 ms, amp unmute 90-130 ms). Short sounds such as a page-turn click are lost | ≥ 250 ms of zeros for `I2sDac`, or keep the channel running between closely spaced sounds |
| No pin parking | `teardownI2s()`, `:307-322`: disable + delete only | Pins are left as stopped I2S outputs | Park LOW after teardown (section 5) |
| Presence fixed at build time | `present()`, `:65-70` | Can't tell whether the cap is fitted | Use `audio_cap_present()` at runtime |

## 5. Strap pins (IO3, IO45, IO46)
All three audio lines are ESP32-S3 strapping pins (FIRMWARE-NOTES "Strap pins"). Findings:
- **ESP32-audioI2S 3.4.7 and the SDK's `AudioManager`** never call `gpio_reset_pin()` and never enable a pull-up.
- **ESP-IDF 5.5.5's `i2s_del_channel()` doesn't change pin settings.**
  - It calls `i2s_output_gpio_revoke()` (`esp_driver_i2s/i2s_common.c:919-930`).
  - That calls `esp_gpio_revoke()` (`esp_hw_support/esp_gpio_reserve.c:20-23`), which only clears a reservation
    bitmask.
  - So the pins stay routed to the stopped I2S peripheral, and their pulls are unchanged.
- **Nothing parks them LOW.** After every stop, and before deep sleep, the firmware drives all three LOW as plain
  outputs (FIRMWARE-NOTES "Start, stop, sleep").
  - If word select (IO3) is left HIGH, it wastes about 330 µA through the cap's 10 kΩ pull-down (`R7`).
  - LOW is also the correct strap level if anything later resets the pins.
- **Presence check:** IO3 only. Run it while no I2S driver holds the pin. IO45/IO46 never get a pull-up.
- **Port checklist:**
  1. Grep the port for `gpio_reset_pin`, `pinMode(..., INPUT_PULLUP)`, `GPIO_PULLUP_ENABLE` and `gpio_pullup_en` on
     pins 3, 45 and 46.
  2. Run the boot check in `../docs/ASSEMBLY.md` on the first board.

## 6. Text-to-speech
No e-ink reader firmware found reads books aloud. The engines that run on an ESP32-S3:

| Engine | Offline | Languages | Output | Cost on the S3 | Licence | Sounds like |
|---|---|---|---|---|---|---|
| **PicoTTS**: [DiUS/esp-picotts](https://github.com/DiUS/esp-picotts), registry `jmattsson/picotts` 1.1.3 | yes | US and UK English, German, French, Italian, Spanish | 16-bit, 16 kHz, via a sample callback | ~175 KB code; 750-1,400 KB flash per language; ~1.1 MB RAM while running (fits in PSRAM) | Upstream engine Apache-2.0 (Android's SVOX Pico); the port's repo has no licence file GitHub can detect: **check before shipping** | Android's built-in voice around 2009-2012: clear, clearly synthetic |
| **eSpeak NG**: [pschatzmann/arduino-espeak-ng](https://pschatzmann.github.io/arduino-espeak-ng) | yes | 100+ | 16-bit, 22.05 kHz | Reads `espeak-ng-data` from a filesystem; needs arduino-audio-tools | GPL-3.0 | The NVDA screen reader's default voice: robotic |
| ESP32-audioI2S `connecttospeech()` | **no** | many | stream | Wi-Fi | GPL-3.0 | Google Translate's voice. Sends the page text to Google |
| ESP-SR TTS (Espressif) | yes | Chinese only | — | — | — | — |

PicoTTS notes:
- **Voice data:** embed it in the app, which grows the image, or put it in two partitions (`picotts_ta`,
  `picotts_sg`). The current CrossPoint table (two 6.4 MB app slots, 3.4 MB SPIFFS) would need resizing for the
  partition route.
- **Output:** 16 kHz plays as-is on our DAC with 32-bit slots, or can be upsampled ×3 to 48 kHz.
- **Real time:** one developer reports real-time speech on an otherwise idle S3, but the TTS task can trip the task
  watchdog unless it yields or the watchdog is adjusted.

## 7. Licences
- **CrossPoint and CrossInk** are MIT.
- **ESP32-audioI2S** (and the eSpeak NG port) are **GPL-3.0**.
  - A firmware image that links either one is GPL-3.0 as a whole. That's fine for the public `silkscreen` forks, since
    their source is already published.
  - Keep the player behind `CROSSPOINT_AUDIO_PLAYER` so the default images stay MIT.
- **PicoTTS's** upstream licence is Apache-2.0, which is compatible with MIT. Confirm the port's terms first.

## 8. What it will sound like
**The three numbers:**
- **Sample rate (kHz):** snapshots per second. It sets the highest pitch, at half the rate.
  - 16 kHz stops at about 7-8 kHz: speech is understandable, but "s", "t" and "f" go soft and music loses its
    cymbals and air.
  - 48 kHz reaches about 20 kHz, the top of human hearing. Most adults stop hearing around 15-17 kHz.
- **Bit depth:** how fine each snapshot is, which sets the hiss floor.
  - A CD is 16-bit: about 96 dB between the loudest sound and the hiss.
  - The PCM5102A is rated at 112 dB SNR and -93 dB THD+N. The TPA6138A2 headphone driver is rated at more than 90 dB
    SNR and below 0.01 % THD+N at 10 mW into 32 Ω. The whole chain is roughly CD level.
- **Bitrate (kbps):** how hard a compressed file is squeezed. It belongs to the file, not the hardware.
  - Audiobooks are typically 32-64 kbps.
  - Streaming music is 96-320 kbps; a CD is 1,411 kbps uncompressed.

**Compared with real sources:**

| Source | Highest pitch | What it's like |
|---|---|---|
| Landline or old mobile call (8 kHz) | ~3.4 kHz | A classic phone call |
| AM radio | ~5 kHz | Talk radio |
| **Metalio eInk4 (16 kHz)** | ~7 kHz | A Bluetooth headset in call mode, e.g. AirPods when a Teams or Zoom call starts. Its module supplies a fixed 16 kHz clock, and the SDK's Metalio path rejects every other rate (`freeink-sdk/docs/metalio-audio.md`) |
| FM radio | 15 kHz | Music on car FM |
| **This attachment (48 kHz)** | ~20 kHz | A CD, or streaming music through a phone's wired headphone output |

**Expected experience, if it works as designed:**
- **Audiobooks** sound as they do on a phone. At 64 kbps the file is the only limit: like a well-made podcast.
- **Music** at 256-320 kbps or FLAC is phone-wired-output quality, which almost nobody can tell from a CD blind. At
  128 kbps it's fine for casual listening.
- **Bass:** the output is DC-coupled and ground-centred, as phones do it, so earbuds keep their bass.
- **Loudness:**
  - About 40 mW into 32 Ω: phone-level, and loud on earbuds.
  - 250-300 Ω studio headphones play quieter, as they do from a phone.
  - Line out is about 2 Vrms, the standard CD-player level, so a car aux input or a stereo matches its other sources.

**What could make it worse (first-article checks):**
1. **Electrical noise from the reader.** The front light's high-voltage boost converter, e-ink refreshes, SD card
   bursts and Wi-Fi bursts could show up as a faint whine or ticking. It's most likely with sensitive in-ear monitors at
   low volume in a quiet room, and least likely with over-ear headphones or line out. Listen for it on the first board,
   with the front light on and during page turns.
2. **Dropouts** if an e-ink refresh or SD contention starves the decoder. This is buffering and task priority, not
   fidelity.
3. **Resampling:** section 3.1. Avoided for 16/32/44.1/48 kHz files by playing them at their own rate.
4. **Edges:** the first ~0.1 s after silence (covered by the 250 ms preroll), and a possible click at stop (see
   `../docs/ASSEMBLY.md`).

## 9. Port plan (not started)
1. **SDK:** add `SILKSCREEN_J6_AUDIO` to the Silkscreen board entries and add those devices to `FREEINK_CAP_AUDIO`.
2. **CrossPoint `silkscreen` branch:** bring over `AudioPlayerActivity` and its settings, home-screen and web-API
   pieces from `murphy-m3-support`, behind `CROSSPOINT_AUDIO_PLAYER`.
3. **Silkscreen changes:** the four in section 3, the pin parking in section 5, and the presence check gating the Audio
   entry.
4. **Optional:** make `AudioManager`'s `I2sDac` mode usable for interface sounds (section 4).
5. **Later, separately:** PicoTTS read-aloud.
6. **First board:** the boot check, tone test, jack mapping and a listening pass for noise (section 8).

## Sources (checked 2026-11-09)
- **mr-tbot/crosspoint-reader:** [repo](https://github.com/mr-tbot/crosspoint-reader),
  [`AudioPlayerActivity.cpp`](https://github.com/mr-tbot/crosspoint-reader/blob/murphy-m3-support/src/activities/audio/AudioPlayerActivity.cpp).
- **CrossPoint:** [PR 2794](https://github.com/crosspoint-reader/crosspoint-reader/pull/2794),
  [issue 290](https://github.com/crosspoint-reader/crosspoint-reader/issues/290).
- **ESP32-audioI2S:** [repo](https://github.com/schreibfaul1/ESP32-audioI2S) (source at tag 3.4.7),
  [wiki](https://github.com/schreibfaul1/ESP32-audioI2S/wiki).
- **PicoTTS:** [DiUS/esp-picotts](https://github.com/DiUS/esp-picotts),
  [ESP registry `jmattsson/picotts`](https://components.espressif.com/components/jmattsson/picotts).
- **eSpeak NG:** [arduino-espeak-ng](https://pschatzmann.github.io/arduino-espeak-ng).
- **ESP-SR:** [TTS docs](https://docs.espressif.com/projects/esp-sr/en/latest/esp32s3/speech_synthesis/readme.html).
- **TI parts:** [PCM5102A](https://www.ti.com/product/PCM5102A), [TPA6138A2](https://www.ti.com/product/TPA6138A2).
- **Other readers:** [Open Book Touch](https://www.crowdsupply.com/oddly-specific-objects/open-book-touch),
  [Diptyx (CNX Software)](https://www.cnx-software.com/2025/12/12/diptyx-e-reader-an-open-source-esp32-powered-dual-screen-e-book-reader/),
  [BacaIn](https://github.com/khad1r/Bacain).
- **Local:** silkscreen-firmware (CrossPoint, CrossInk and the Free-Ink SDK at the versions above), and
  `framework-espidf` 5.5.5 in the PlatformIO packages.
