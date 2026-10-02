# Broken Skyscraper - Unity Edition

Unity **6000.6.0f1**, Windows x64, English UI. This is a native C# Unity project; Python is used only to generate independent rule reference traces during development.

## Immersion update 0.3

- Pressure builds from veil proximity, low health and remaining time. The HUD meter and layered ambience reflect danger without changing combat rules.
- Jump tuck, landing compression, velocity-based lean, hit recoil, brighter hit suits and a subtle idle motion improve action readability.
- Attacks draw short arcs; dodges leave silhouettes; fast falls produce speed lines; jumps, steps and landings emit dust. Impacts scatter sparks.
- Wind motes and tower beacons react to danger. Effects use a reusable 160-particle pool.
- Eleven original synthesized cues cover steps, jumps, landings, windup, swings, dodges, impacts, warnings, countdown, start and results. Twelve effect voices use priority-based allocation; ambience has two separate layers.
- Settings include **Reduced motion** and **Effect intensity**, plus separate effects/ambience volume and camera shake. Reduced motion disables shake, trails and wind drift, reduces body lean and particle bursts, and removes beacon pulsing.
- Pause freezes world motion, particles and audio. Replays retain the 0.2 simulation format because presentation does not modify the match.

Action labels describe animation state; `EVADE` means a dodge was activated, not that an incoming attack was successfully avoided. `HARD LANDING` is feedback only and causes no fall damage.

## Launch

Run `BrokenSkyscraper.exe` from the Windows build folder. Keep `BrokenSkyscraper_Data`, `UnityPlayer.dll`, and the other packaged files beside the executable.

For editing, add the `unity` folder to Unity Hub and open it with Unity 6000.6.0f1. Open `Assets/Scenes/Main.unity` and press Play. The scene contains the runtime game entry point; visual scenery and characters are assembled from native Unity geometry at runtime.

## Game modes

- **Descent:** an experimental fixed, symmetric tower; start at Y=30, descend to Y=2 while avoiding the veil. Two-minute match. Higher position wins on timeout; health breaks a height tie.
- **Combat Lab:** the five-platform baseline with the veil disabled. Use settings to mirror starts, give P2 initial motion, or select a training target.
- **Final 15 Seconds:** starts at 105 seconds of the original timeline, with 900 ticks left. Select 100/100, 100/60, 60/60 or 40/100 initial health in settings before starting.

The full tower is a playable experiment, not a validated balance result. Body pass-through and last-second jumping remain open playtest questions.

## Controls

| Action | P1 | P2 | Controller (Xbox layout) |
|---|---|---|---|
| Move | A / D | Left / Right | Left stick |
| Jump | W | Up | A |
| Drop through | S + W | Down + Up | Stick down + A |
| Push | F | K | X |
| Dodge | G | L | B |
| Pause | Esc | Esc | Start |

Keyboard bindings can be changed in Settings. Buttons use the legacy Unity joystick mapping with two independent slots. Physical device compatibility still requires verification.

- **Tab:** show/hide controls.
- **R:** restart current mode.
- **F1:** debug coordinates, velocity, support and action state.
- **F7 / F8:** save / replay the latest local input recording.
- **N:** single simulation tick while paused with debug enabled.

Window focus loss or controller removal pauses play. Resume explicitly after reconnecting. Sound effects, ambient volume, screen shake and fullscreen/windowed display are configurable.

## Included details

- Separate C# simulation and Unity presentation, fixed 60 ticks, independent render loop.
- Swept one-way platform collisions, residual movement after landing, coyote time, jump buffering and drop-through.
- Exact attack windup/active/recovery, fixed attack direction, simultaneous trades, 14-tick knockback and timed dodge immunity.
- Integer health, descending veil, strict same-tick elimination priorities, countdown, pause and rematch.
- Segmented suit characters with animated walking/push/dodge states; impact sparks and optional screen shake.
- Layered skyline, lit windows, tower bracing, platform trim and rivets.
- Procedurally synthesized impact/jump/warning/result cues and ambient tone; no external art/audio downloads.
- Shared camera, timed split-screen at large height differences, height leader indicator, player markers and exposure warnings.
- Match statistics and explicit result reason.
- Local replays with input frames, state hashes, periodic snapshots and first-divergence reporting.

## Build

From the repository root:

```powershell
python -m tools.generate_unity_fixtures
powershell -ExecutionPolicy Bypass -File build-unity.ps1
```

Pass `-UnityEditor 'path\to\Editor\Unity.exe'` if Unity is installed elsewhere. An activated Unity Editor with Windows build support is required. The build method runs C# rule checks and Python-reference comparisons before producing `dist/UnityWindows/BrokenSkyscraper.exe`.

Player logs and replays are stored under Unity's `Application.persistentDataPath`, normally `%USERPROFILE%/AppData/LocalLow/BrokenSkyscraper/Broken Skyscraper`. Replays retain up to 20 files with an approximate 40 MB combined limit. Keyboard/audio preferences use Unity PlayerPrefs.

## Validation limits

Automated rule checks do not establish competitive balance or input-device compatibility. Human pressure/counterattack playtests, physical two-controller checks, endgame strategy comparisons and hardware performance testing remain necessary. No online multiplayer, accounts, shop or destructive platforms are included.
