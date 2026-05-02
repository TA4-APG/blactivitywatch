"""
Core watcher loop for aw-watcher-screenshot.

On each tick the watcher:
1. Optionally skips capture when the user is AFK.
2. Captures one screenshot per configured monitor via capture.py.
3. Optionally resizes and/or blurs the image.
4. Persists the image to disk via storage.py.
5. Inserts a discrete event in aw-server with path + window metadata.
"""
import logging
import socket
from datetime import datetime, timezone
from time import sleep
from typing import List, Optional

from aw_client import ActivityWatchClient
from aw_core.models import Event

from .capture import capture_monitor
from .config import load_config
from .storage import (
    apply_blur,
    build_filepath,
    get_storage_root,
    resize_image,
    save_image,
)

logger = logging.getLogger(__name__)


def _get_active_window_info() -> dict:
    """Best-effort attempt to get the active window's app name and title.

    Returns a dict with keys ``app`` and ``title``.  Both default to an
    empty string when the information is unavailable.
    """
    try:
        import subprocess
        import platform

        system = platform.system()

        if system == "Linux":
            # Use xdotool when available (X11 only)
            try:
                wid = subprocess.check_output(
                    ["xdotool", "getactivewindow"], text=True
                ).strip()
                title = subprocess.check_output(
                    ["xdotool", "getwindowname", wid], text=True
                ).strip()
                app = subprocess.check_output(
                    ["xdotool", "getwindowclassname", wid], text=True
                ).strip()
                return {"app": app, "title": title}
            except Exception:
                pass

        elif system == "Darwin":
            script = (
                'tell application "System Events" to get name of first process '
                "whose frontmost is true"
            )
            app = subprocess.check_output(
                ["osascript", "-e", script], text=True
            ).strip()
            return {"app": app, "title": ""}

        elif system == "Windows":
            import ctypes

            hwnd = ctypes.windll.user32.GetForegroundWindow()
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
            return {"app": "", "title": buf.value}

    except Exception as exc:
        logger.debug("Could not get active window info: %s", exc)

    return {"app": "", "title": ""}


def _is_afk(client: ActivityWatchClient) -> bool:
    """Return True if aw-watcher-afk reports the user as AFK right now."""
    try:
        hostname = socket.gethostname()
        bucket_id = f"aw-watcher-afk_{hostname}"
        events = client.get_events(bucket_id, limit=1)
        if events:
            status = events[0].data.get("status", "")
            return status == "afk"
    except Exception as exc:
        logger.debug("Could not check AFK status: %s", exc)
    return False


class Settings:
    def __init__(self, config_section, args):
        self.poll_time: float = args.poll_time or config_section["poll_time"]
        self.quality: int = args.quality if args.quality is not None else config_section["quality"]
        self.resolution_scale: float = (
            args.resolution_scale
            if args.resolution_scale is not None
            else config_section["resolution_scale"]
        )
        self.enabled: bool = bool(config_section["enabled"])
        self.skip_afk: bool = bool(config_section["skip_afk"])
        self.blur_apps: List[str] = list(config_section.get("blur_apps", []))
        self.storage_path: str = args.storage_path or config_section.get("storage_path", "")
        self.monitors: List[int] = list(config_section.get("monitors", [1]))


class ScreenshotWatcher:
    def __init__(self, args, testing: bool = False):
        self.testing = testing
        self.settings = Settings(load_config(testing), args)

        self.client = ActivityWatchClient(
            "aw-watcher-screenshot",
            host=args.host,
            port=args.port,
            testing=testing,
        )
        self.bucketname = f"{self.client.client_name}_{self.client.client_hostname}"
        self.storage_root = get_storage_root(self.settings.storage_path)

    def run(self) -> None:
        if not self.settings.enabled:
            logger.warning(
                "aw-watcher-screenshot is disabled (enabled = false in config). "
                "Set 'enabled = true' in the config file to start capturing screenshots."
            )
            return

        logger.info("aw-watcher-screenshot started")

        self.client.wait_for_start()
        self.client.create_bucket(self.bucketname, "screenshot", queued=True)

        with self.client:
            self._capture_loop()

    def _capture_loop(self) -> None:
        while True:
            try:
                self._tick()
                sleep(self.settings.poll_time)
            except KeyboardInterrupt:
                logger.info("aw-watcher-screenshot stopped by keyboard interrupt")
                break

    def _tick(self) -> None:
        if self.settings.skip_afk and _is_afk(self.client):
            logger.debug("User is AFK; skipping screenshot")
            return

        now = datetime.now(timezone.utc)
        window_info = _get_active_window_info()

        for monitor_index in self.settings.monitors:
            self._capture_and_record(now, monitor_index, window_info)

    def _capture_and_record(
        self, timestamp: datetime, monitor_index: int, window_info: dict
    ) -> None:
        try:
            img = capture_monitor(monitor_index)
        except Exception as exc:
            logger.error("Failed to capture monitor %d: %s", monitor_index, exc)
            return

        if self.settings.resolution_scale != 1.0:
            img = resize_image(img, self.settings.resolution_scale)

        app = window_info.get("app", "")
        if app and app in self.settings.blur_apps:
            logger.debug("Blurring screenshot for app: %s", app)
            img = apply_blur(img)

        filepath = build_filepath(
            timestamp, monitor_index, self.settings.quality, self.storage_root
        )

        try:
            save_image(img, filepath, self.settings.quality)
        except Exception as exc:
            logger.error("Failed to save screenshot: %s", exc)
            return

        event = Event(
            timestamp=timestamp,
            duration=0,
            data={
                "path": str(filepath),
                "app": app,
                "title": window_info.get("title", ""),
                "monitor": monitor_index,
            },
        )
        self.client.insert_event(self.bucketname, event)
        logger.info("Screenshot captured: %s", filepath)
