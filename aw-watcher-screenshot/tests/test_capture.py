"""Unit tests for aw_watcher_screenshot.capture (with mss mocked out)."""
import sys
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _make_mock_screenshot(width: int = 1920, height: int = 1080) -> MagicMock:
    """Return a mock object that resembles an mss screenshot."""
    mock = MagicMock()
    mock.size = (width, height)
    # mss provides raw BGRA bytes; create a simple all-black buffer
    mock.bgra = bytes(width * height * 4)
    return mock


def _make_mock_sct(num_monitors: int = 2) -> MagicMock:
    """Return a mock mss.mss() context manager with *num_monitors* entries."""
    sct = MagicMock()
    # monitors[0] is the combined virtual monitor; [1..n] are physical monitors
    sct.monitors = [MagicMock()] * (num_monitors + 1)
    sct.grab.return_value = _make_mock_screenshot()
    # Support 'with mss.mss() as sct:' usage
    sct.__enter__ = MagicMock(return_value=sct)
    sct.__exit__ = MagicMock(return_value=False)
    return sct


# ---------------------------------------------------------------------------
# capture_monitor
# ---------------------------------------------------------------------------

class TestCaptureMonitor:
    def test_returns_rgb_image(self):
        from aw_watcher_screenshot.capture import capture_monitor

        mock_sct = _make_mock_sct(num_monitors=1)
        with patch("mss.mss", return_value=mock_sct):
            img = capture_monitor(monitor_index=1)

        assert isinstance(img, Image.Image)
        assert img.mode == "RGB"

    def test_fallback_to_monitor_1_when_index_too_large(self, caplog):
        from aw_watcher_screenshot.capture import capture_monitor

        mock_sct = _make_mock_sct(num_monitors=1)
        with patch("mss.mss", return_value=mock_sct):
            with caplog.at_level("WARNING"):
                img = capture_monitor(monitor_index=99)

        assert isinstance(img, Image.Image)
        assert "not found" in caplog.text.lower() or "falling back" in caplog.text.lower()

    def test_correct_monitor_grabbed(self):
        from aw_watcher_screenshot.capture import capture_monitor

        mock_sct = _make_mock_sct(num_monitors=2)
        with patch("mss.mss", return_value=mock_sct):
            capture_monitor(monitor_index=2)

        # mss.grab should have been called with monitors[2]
        mock_sct.grab.assert_called_once_with(mock_sct.monitors[2])


# ---------------------------------------------------------------------------
# capture_monitors
# ---------------------------------------------------------------------------

class TestCaptureMonitors:
    def test_returns_list_of_images(self):
        from aw_watcher_screenshot.capture import capture_monitors

        mock_sct = _make_mock_sct(num_monitors=2)
        with patch("mss.mss", return_value=mock_sct):
            images = capture_monitors(monitor_indices=[1, 2])

        assert len(images) == 2
        assert all(isinstance(img, Image.Image) for img in images)

    def test_defaults_to_monitor_1(self):
        from aw_watcher_screenshot.capture import capture_monitors

        mock_sct = _make_mock_sct(num_monitors=1)
        with patch("mss.mss", return_value=mock_sct):
            images = capture_monitors()

        assert len(images) == 1

    def test_empty_list_returns_empty(self):
        from aw_watcher_screenshot.capture import capture_monitors

        mock_sct = _make_mock_sct(num_monitors=1)
        with patch("mss.mss", return_value=mock_sct):
            images = capture_monitors(monitor_indices=[])

        assert images == []


# ---------------------------------------------------------------------------
# list_monitors
# ---------------------------------------------------------------------------

class TestListMonitors:
    def test_returns_list_of_ints(self):
        from aw_watcher_screenshot.capture import list_monitors

        mock_sct = _make_mock_sct(num_monitors=2)
        with patch("mss.mss", return_value=mock_sct):
            indices = list_monitors()

        # monitors list has num_monitors + 1 entries (index 0 = combined)
        assert indices == [0, 1, 2]
