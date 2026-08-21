# Rust rewrite (Linux + Windows)

Cross-platform Rust port of the Python/Pygame `revy-check` kiosk. The Python tree
stays in place until this reaches parity. Full plan:
`.claude/plans/converte-esse-com-versoes-hidden-riddle.md`.

## Layout

```
Cargo.toml                 # workspace
crates/
  revy-platform/           # OS-abstraction traits + Mock (Linux/Windows impls: Phase 2/3)
  revy-check/              # macroquad GUI, state machine, steps, log
assets/                    # optional bundled font
```

## Build / run

Needs a Rust toolchain (`rustup`, `cargo`) — not currently installed on this
machine. Install from https://rustup.rs then:

```bash
cargo run -p revy-check
```

On Linux you may also need the usual GL/X11 dev headers for macroquad.

## Status

- **Phase 0/1 (done):** window + fullscreen, PROD/DEV mode + `LCtrl+LShift+D+V`
  hotkey + DEV password, the full test flow driven by `MockPlatform`, the
  GUI-only tests (screen color-cycle, on-screen keyboard, touchpad), the menu,
  system-info overlay, and `checklist_log.json` output. Hardware/DB/audio/camera
  steps are placeholders that log the operator's verdict.
- **Phase 2:** Linux platform impls (sysfs/CLI) + real wifi/usb/video/ethernet.
- **Phase 3:** Windows platform impls (WMI/WinAPI).
- **Phase 4:** audio (rodio/cpal) + camera (nokhwa).
- **Phase 5:** MySQL + NTP + device registration; move all creds to config/env.
- **Phase 6:** kiosk packaging/autostart, bundled font, offline log queue.

## Security note carried over from the Python app

The Python source has hardcoded MySQL/SMB credentials (already in git history).
The Rust port must load them from config/env instead — and those credentials
should be rotated. See the plan's Risks section.
```
