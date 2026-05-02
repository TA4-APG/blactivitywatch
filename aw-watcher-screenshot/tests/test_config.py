"""Unit tests for aw_watcher_screenshot.config"""
import sys
from unittest.mock import patch

import pytest


class TestLoadConfig:
    def test_default_poll_time(self):
        from aw_watcher_screenshot.config import load_config

        cfg = load_config(testing=False)
        assert cfg["poll_time"] == 60

    def test_default_enabled_is_false(self):
        from aw_watcher_screenshot.config import load_config

        cfg = load_config(testing=False)
        assert cfg["enabled"] is False or cfg["enabled"] == "false" or not cfg["enabled"]

    def test_testing_mode_enabled(self):
        from aw_watcher_screenshot.config import load_config

        cfg = load_config(testing=True)
        # In testing mode enabled should be true
        assert cfg["enabled"] is True or cfg["enabled"] == "true" or cfg["enabled"]

    def test_testing_mode_poll_time(self):
        from aw_watcher_screenshot.config import load_config

        cfg = load_config(testing=True)
        assert cfg["poll_time"] == 5

    def test_default_quality(self):
        from aw_watcher_screenshot.config import load_config

        cfg = load_config(testing=False)
        assert int(cfg["quality"]) == 75

    def test_default_skip_afk(self):
        from aw_watcher_screenshot.config import load_config

        cfg = load_config(testing=False)
        assert cfg["skip_afk"] is True or cfg["skip_afk"] == "true" or cfg["skip_afk"]

    def test_default_resolution_scale(self):
        from aw_watcher_screenshot.config import load_config

        cfg = load_config(testing=False)
        assert float(cfg["resolution_scale"]) == 1.0


class TestParseArgs:
    def test_help_does_not_crash(self):
        """Verify --help exits cleanly (not a crash)."""
        from aw_watcher_screenshot.config import parse_args

        with patch("sys.argv", ["aw-watcher-screenshot", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                parse_args()
        assert exc_info.value.code == 0

    def test_defaults_applied(self):
        from aw_watcher_screenshot.config import parse_args

        with patch("sys.argv", ["aw-watcher-screenshot"]):
            args = parse_args()

        assert args.poll_time == 60
        assert args.quality == 75
        assert args.resolution_scale == 1.0

    def test_custom_poll_time(self):
        from aw_watcher_screenshot.config import parse_args

        with patch("sys.argv", ["aw-watcher-screenshot", "--poll-time", "30"]):
            args = parse_args()

        assert args.poll_time == 30.0
