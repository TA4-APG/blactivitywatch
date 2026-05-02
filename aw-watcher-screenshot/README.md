# aw-watcher-screenshot

An [ActivityWatch](https://activitywatch.net/) watcher that periodically captures screenshots, stores them on disk, and records metadata events in aw-server.  It also ships a companion CLI tool (`aw-screenshot-timelapse`) for generating timelapse videos from the captured frames.

> **Privacy notice:** Screenshot capture is **disabled by default**.  You must explicitly set `enabled = true` in the configuration file before any screenshot is taken.  All images are stored locally on your machine and are never uploaded anywhere.

---

## Features

- Cross-platform screen capture (Windows, macOS, Linux X11) via [mss](https://python-mss.readthedocs.io/)
- Configurable capture interval, JPEG quality, and resolution downscaling
- Optional per-app blurring (irreversible, applied before saving)
- Skips capture automatically when the user is AFK (requires `aw-watcher-afk`)
- Multi-monitor support
- Timelapse generator: produces MP4/WebM (via ffmpeg) or animated GIF (via imageio, no ffmpeg required)

---

## Installation

```bash
pip install aw-watcher-screenshot
# with GIF timelapse support (no ffmpeg needed):
pip install "aw-watcher-screenshot[timelapse]"
```

Or, from source inside the ActivityWatch bundle:

```bash
cd aw-watcher-screenshot
poetry install
```

---

## Configuration

The config file is created automatically at first run.  Its location follows the [aw-core](https://github.com/ActivityWatch/aw-core) convention:

| Platform | Path |
|----------|------|
| Linux    | `~/.config/activitywatch/aw-watcher-screenshot/aw-watcher-screenshot.toml` |
| macOS    | `~/Library/Preferences/activitywatch/aw-watcher-screenshot/aw-watcher-screenshot.toml` |
| Windows  | `%APPDATA%\activitywatch\aw-watcher-screenshot\aw-watcher-screenshot.toml` |

### Available options

```toml
[aw-watcher-screenshot]
# Master on/off switch (off by default for privacy)
enabled = false

# Seconds between captures
poll_time = 60

# JPEG quality 1–95; set to 0 to save as lossless PNG instead
quality = 75

# Downscale factor (1.0 = original resolution, 0.5 = half)
resolution_scale = 1.0

# Skip capture when aw-watcher-afk reports the user as AFK
skip_afk = true

# App names whose screenshots are blurred before saving
blur_apps = []

# Override storage directory (empty = default data dir)
storage_path = ""

# Monitor indices to capture (1-indexed; 0 = all combined)
monitors = [1]
```

---

## Usage

### Watcher

```bash
aw-watcher-screenshot [--host HOST] [--port PORT] [--testing] [--verbose]
                      [--poll-time SECONDS] [--quality 0-95]
                      [--resolution-scale 0.1-1.0]
                      [--storage-path /path/to/screenshots]
```

### Timelapse generator

```bash
# MP4 via ffmpeg
aw-screenshot-timelapse --start 2025-05-01 --end 2025-05-02 --output timelapse.mp4

# Animated GIF via imageio (no ffmpeg required)
aw-screenshot-timelapse --start 2025-05-01T09:00 --end 2025-05-01T17:00 \
    --output workday.gif --format gif --fps 4

# Full option list
aw-screenshot-timelapse --help
```

---

## Screenshot storage layout

```
~/.local/share/activitywatch/screenshots/
    2025-05-02/
        13-30-00.jpg
        13-31-00.jpg
        13-31-00_m2.jpg   ← monitor 2
    2025-05-03/
        ...
```

---

## Privacy

- **Opt-in only** – `enabled = false` by default; the watcher exits immediately if this is not changed.
- **Local storage only** – images never leave your machine.
- **Blur list** – add app names to `blur_apps` to have those windows blurred before the image is saved.  The blur is irreversible.
- **AFK skip** – set `skip_afk = true` (default) to avoid capturing screenshots when you are not at your computer.

---

## License

MPL-2.0 – see [LICENSE.txt](../LICENSE.txt).
