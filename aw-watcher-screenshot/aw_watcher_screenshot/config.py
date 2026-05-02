import argparse
import sys

from aw_core.config import load_config_toml

default_config = """
[aw-watcher-screenshot]
# Seconds between screenshots
poll_time = 60
# Master on/off switch (false by default for privacy)
enabled = false
# JPEG quality 1-95; set to 0 to save as PNG instead
quality = 75
# Downscale factor applied before saving (1.0 = original size, 0.5 = half)
resolution_scale = 1.0
# Skip capture when the user is AFK (requires aw-watcher-afk to be running)
skip_afk = true
# App names whose screenshots are blurred before saving (comma-separated)
blur_apps = []
# Override the directory where screenshots are stored (empty = default data dir)
storage_path = ""
# Monitor indices to capture (1-indexed; 0 = all monitors combined)
monitors = [1]

[aw-watcher-screenshot-testing]
poll_time = 5
enabled = true
quality = 75
resolution_scale = 1.0
skip_afk = false
blur_apps = []
storage_path = ""
monitors = [1]
""".strip()


def load_config(testing: bool):
    section = "aw-watcher-screenshot" + ("-testing" if testing else "")
    return load_config_toml("aw-watcher-screenshot", default_config)[section]


def parse_args():
    testing = "--testing" in sys.argv
    config = load_config(testing)

    parser = argparse.ArgumentParser(
        description="A watcher that periodically captures screenshots and stores "
        "metadata events in ActivityWatch."
    )
    parser.add_argument("--host", dest="host")
    parser.add_argument("--port", dest="port")
    parser.add_argument(
        "--testing", dest="testing", action="store_true", help="run in testing mode"
    )
    parser.add_argument(
        "--verbose",
        dest="verbose",
        action="store_true",
        help="run with verbose logging",
    )
    parser.add_argument(
        "--poll-time",
        dest="poll_time",
        type=float,
        default=config["poll_time"],
        help="seconds between screenshots (default: %(default)s)",
    )
    parser.add_argument(
        "--quality",
        dest="quality",
        type=int,
        default=config["quality"],
        help="JPEG quality 1-95; 0 saves as PNG (default: %(default)s)",
    )
    parser.add_argument(
        "--resolution-scale",
        dest="resolution_scale",
        type=float,
        default=config["resolution_scale"],
        help="downscale factor before saving (default: %(default)s)",
    )
    parser.add_argument(
        "--storage-path",
        dest="storage_path",
        default=config["storage_path"],
        help="override directory for screenshot files",
    )
    return parser.parse_args()
