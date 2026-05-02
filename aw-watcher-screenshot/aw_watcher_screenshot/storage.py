"""
Filesystem helpers for persisting screenshot images.

Layout:
    <storage_root>/
        YYYY-MM-DD/
            HH-MM-SS.jpg   (or .png when quality == 0)
"""
import io
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from PIL import Image, ImageFilter

logger = logging.getLogger(__name__)


def get_default_storage_root() -> Path:
    """Return the default directory for storing screenshots.

    Uses the aw-core data-dir helper so the path respects XDG/platform
    conventions (e.g. ``~/.local/share/activitywatch/screenshots`` on Linux).
    """
    from aw_core.dirs import get_data_dir

    return Path(get_data_dir("screenshots"))


def get_storage_root(override: str = "") -> Path:
    """Return the storage root, using *override* if non-empty."""
    if override:
        return Path(override)
    return get_default_storage_root()


def _image_extension(quality: int) -> str:
    return ".png" if quality == 0 else ".jpg"


def build_filepath(
    timestamp: datetime,
    monitor_index: int,
    quality: int,
    storage_root: Path,
) -> Path:
    """Build the full path for a screenshot without writing anything.

    The filename encodes the monitor index when multiple monitors are
    expected (monitor_index > 1) so that files for the same second do
    not collide::

        2025-05-02/13-30-00.jpg          (single monitor)
        2025-05-02/13-30-00_m2.jpg       (monitor 2)
    """
    date_dir = storage_root / timestamp.strftime("%Y-%m-%d")
    ext = _image_extension(quality)
    time_part = timestamp.strftime("%H-%M-%S")
    if monitor_index > 1:
        filename = f"{time_part}_m{monitor_index}{ext}"
    else:
        filename = f"{time_part}{ext}"
    return date_dir / filename


def apply_blur(img: Image.Image, radius: int = 20) -> Image.Image:
    """Return a blurred copy of *img* using a Gaussian filter."""
    return img.filter(ImageFilter.GaussianBlur(radius=radius))


def resize_image(img: Image.Image, scale: float) -> Image.Image:
    """Return a resized copy of *img* according to *scale* (0 < scale <= 1.0)."""
    if scale == 1.0:
        return img
    new_width = max(1, int(img.width * scale))
    new_height = max(1, int(img.height * scale))
    return img.resize((new_width, new_height), Image.LANCZOS)


def save_image(
    img: Image.Image,
    filepath: Path,
    quality: int = 75,
) -> Path:
    """Persist *img* to *filepath*, creating parent directories as needed.

    Args:
        img:      PIL Image to save.
        filepath: Destination path (extension drives the format).
        quality:  JPEG quality 1-95.  Ignored for PNG (quality == 0).

    Returns:
        The path that was written.
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)

    if quality == 0:
        img.save(filepath, format="PNG", optimize=True)
    else:
        img.save(filepath, format="JPEG", quality=quality, optimize=True)

    logger.debug("Saved screenshot: %s (%d bytes)", filepath, filepath.stat().st_size)
    return filepath
