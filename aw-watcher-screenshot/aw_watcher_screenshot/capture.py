"""
Platform-agnostic screenshot capture using mss.

Returns raw BGRA pixel data wrapped in a PIL Image so callers can
apply resizing, quality compression, or blurring without knowing
which backend was used.
"""
import logging
from typing import List, Optional

from PIL import Image

logger = logging.getLogger(__name__)


def list_monitors() -> List[int]:
    """Return a list of available monitor indices (1-indexed).

    Index 0 is a virtual monitor that combines all displays.
    """
    import mss

    with mss.mss() as sct:
        # mss.monitors[0] is the combined virtual monitor; [1..n] are real monitors.
        return list(range(len(sct.monitors)))


def capture_monitor(monitor_index: int = 1) -> Image.Image:
    """Capture a single monitor and return a PIL Image (RGB).

    Args:
        monitor_index: 1-indexed monitor number, or 0 for all monitors combined.

    Returns:
        A PIL Image in RGB mode.
    """
    import mss

    with mss.mss() as sct:
        monitors = sct.monitors
        if monitor_index >= len(monitors):
            logger.warning(
                "Monitor %d not found (only %d monitors available); "
                "falling back to monitor 1.",
                monitor_index,
                len(monitors) - 1,
            )
            monitor_index = 1

        monitor = monitors[monitor_index]
        screenshot = sct.grab(monitor)
        # mss gives BGRA; PIL wants RGB
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
    return img


def capture_monitors(monitor_indices: Optional[List[int]] = None) -> List[Image.Image]:
    """Capture one or more monitors.

    Args:
        monitor_indices: list of monitor indices to capture.  Defaults to [1].

    Returns:
        A list of PIL Images, one per requested monitor.
    """
    if monitor_indices is None:
        monitor_indices = [1]
    return [capture_monitor(idx) for idx in monitor_indices]
