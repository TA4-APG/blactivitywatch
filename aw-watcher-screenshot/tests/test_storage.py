"""Unit tests for aw_watcher_screenshot.storage"""
import io
from datetime import datetime, timezone
from pathlib import Path

import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_image(width: int = 100, height: int = 80, color: str = "red") -> Image.Image:
    return Image.new("RGB", (width, height), color=color)


def _utc(year, month, day, hour=0, minute=0, second=0) -> datetime:
    return datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# build_filepath
# ---------------------------------------------------------------------------

class TestBuildFilepath:
    def test_jpg_extension_when_quality_nonzero(self, tmp_path):
        from aw_watcher_screenshot.storage import build_filepath

        ts = _utc(2025, 5, 2, 13, 30, 0)
        p = build_filepath(ts, monitor_index=1, quality=75, storage_root=tmp_path)
        assert p.suffix == ".jpg"

    def test_png_extension_when_quality_zero(self, tmp_path):
        from aw_watcher_screenshot.storage import build_filepath

        ts = _utc(2025, 5, 2, 13, 30, 0)
        p = build_filepath(ts, monitor_index=1, quality=0, storage_root=tmp_path)
        assert p.suffix == ".png"

    def test_date_directory(self, tmp_path):
        from aw_watcher_screenshot.storage import build_filepath

        ts = _utc(2025, 5, 2, 13, 30, 0)
        p = build_filepath(ts, monitor_index=1, quality=75, storage_root=tmp_path)
        assert p.parent.name == "2025-05-02"

    def test_time_in_filename(self, tmp_path):
        from aw_watcher_screenshot.storage import build_filepath

        ts = _utc(2025, 5, 2, 13, 30, 45)
        p = build_filepath(ts, monitor_index=1, quality=75, storage_root=tmp_path)
        assert "13-30-45" in p.name

    def test_monitor_suffix_for_monitor_gt_1(self, tmp_path):
        from aw_watcher_screenshot.storage import build_filepath

        ts = _utc(2025, 5, 2, 13, 30, 0)
        p = build_filepath(ts, monitor_index=2, quality=75, storage_root=tmp_path)
        assert "_m2" in p.name

    def test_no_monitor_suffix_for_monitor_1(self, tmp_path):
        from aw_watcher_screenshot.storage import build_filepath

        ts = _utc(2025, 5, 2, 13, 30, 0)
        p = build_filepath(ts, monitor_index=1, quality=75, storage_root=tmp_path)
        assert "_m" not in p.name


# ---------------------------------------------------------------------------
# save_image
# ---------------------------------------------------------------------------

class TestSaveImage:
    def test_creates_parent_directories(self, tmp_path):
        from aw_watcher_screenshot.storage import save_image

        img = _make_image()
        dest = tmp_path / "2025-05-02" / "13-30-00.jpg"
        assert not dest.parent.exists()
        save_image(img, dest, quality=75)
        assert dest.exists()

    def test_saves_jpeg(self, tmp_path):
        from aw_watcher_screenshot.storage import save_image

        img = _make_image()
        dest = tmp_path / "shot.jpg"
        save_image(img, dest, quality=75)
        loaded = Image.open(dest)
        assert loaded.format == "JPEG"

    def test_saves_png_when_quality_zero(self, tmp_path):
        from aw_watcher_screenshot.storage import save_image

        img = _make_image()
        dest = tmp_path / "shot.png"
        save_image(img, dest, quality=0)
        loaded = Image.open(dest)
        assert loaded.format == "PNG"

    def test_returns_filepath(self, tmp_path):
        from aw_watcher_screenshot.storage import save_image

        img = _make_image()
        dest = tmp_path / "shot.jpg"
        result = save_image(img, dest, quality=75)
        assert result == dest


# ---------------------------------------------------------------------------
# resize_image
# ---------------------------------------------------------------------------

class TestResizeImage:
    def test_half_scale(self):
        from aw_watcher_screenshot.storage import resize_image

        img = _make_image(200, 100)
        resized = resize_image(img, scale=0.5)
        assert resized.size == (100, 50)

    def test_scale_1_returns_original(self):
        from aw_watcher_screenshot.storage import resize_image

        img = _make_image(200, 100)
        result = resize_image(img, scale=1.0)
        assert result is img

    def test_small_scale_does_not_produce_zero_dimension(self):
        from aw_watcher_screenshot.storage import resize_image

        img = _make_image(1, 1)
        resized = resize_image(img, scale=0.1)
        assert resized.width >= 1
        assert resized.height >= 1


# ---------------------------------------------------------------------------
# apply_blur
# ---------------------------------------------------------------------------

class TestApplyBlur:
    def test_returns_image(self):
        from aw_watcher_screenshot.storage import apply_blur

        img = _make_image()
        blurred = apply_blur(img)
        assert isinstance(blurred, Image.Image)

    def test_same_size_as_input(self):
        from aw_watcher_screenshot.storage import apply_blur

        img = _make_image(120, 80)
        blurred = apply_blur(img)
        assert blurred.size == img.size


# ---------------------------------------------------------------------------
# get_storage_root
# ---------------------------------------------------------------------------

class TestGetStorageRoot:
    def test_override_is_used(self, tmp_path):
        from aw_watcher_screenshot.storage import get_storage_root

        result = get_storage_root(override=str(tmp_path))
        assert result == tmp_path

    def test_empty_override_returns_default(self):
        from aw_watcher_screenshot.storage import get_storage_root

        result = get_storage_root(override="")
        assert isinstance(result, Path)
        assert result != Path("")
