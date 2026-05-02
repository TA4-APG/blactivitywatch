"""
Timelapse generator for aw-watcher-screenshot.

Usage
-----
    aw-screenshot-timelapse --start 2025-05-01 --end 2025-05-02 --output timelapse.mp4
    aw-screenshot-timelapse --start 2025-05-01 --end 2025-05-02 --output out.gif --format gif --fps 4

The tool queries aw-server for screenshot events, collects the saved image
files from disk, and assembles them into a video using either:
  - ffmpeg  (preferred; produces mp4 / webm)
  - imageio (fallback; produces GIF)
"""
import argparse
import logging
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


def _parse_dt(s: str) -> datetime:
    """Parse an ISO-8601 date or datetime string and return a UTC-aware datetime."""
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(f"Unrecognised date/time: {s!r}")


def _fetch_screenshot_paths(
    bucket_id: str,
    start: datetime,
    end: datetime,
    host: Optional[str],
    port: Optional[int],
    testing: bool,
) -> List[Path]:
    """Query aw-server for screenshot events and return paths to existing files."""
    from aw_client import ActivityWatchClient

    client = ActivityWatchClient(
        "aw-screenshot-timelapse",
        host=host,
        port=port,
        testing=testing,
    )
    events = client.get_events(bucket_id, start=start, end=end)
    paths = []
    for event in sorted(events, key=lambda e: e.timestamp):
        path_str = event.data.get("path", "")
        if not path_str:
            continue
        p = Path(path_str)
        if p.exists():
            paths.append(p)
        else:
            logger.warning("Screenshot file not found, skipping: %s", p)
    return paths


def _build_with_ffmpeg(
    frame_paths: List[Path],
    output: Path,
    fps: float,
) -> None:
    """Write *frame_paths* into *output* via ffmpeg."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a text file listing all frames for ffmpeg's concat demuxer
        list_file = Path(tmpdir) / "frames.txt"
        duration = 1.0 / fps
        with list_file.open("w") as fh:
            for p in frame_paths:
                fh.write(f"file '{p}'\n")
                fh.write(f"duration {duration:.6f}\n")

        cmd = [
            "ffmpeg",
            "-y",  # overwrite output
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file),
            "-vf", "format=yuv420p",
            str(output),
        ]
        logger.info("Running: %s", " ".join(cmd))
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                f"ffmpeg exited with code {result.returncode}:\n{result.stderr}"
            )


def _build_with_imageio(
    frame_paths: List[Path],
    output: Path,
    fps: float,
) -> None:
    """Write *frame_paths* as an animated GIF using imageio (no ffmpeg needed)."""
    import imageio  # type: ignore
    from PIL import Image

    frames = []
    for p in frame_paths:
        frames.append(Image.open(p).convert("RGB"))

    duration_ms = int(1000 / fps)
    imageio.mimwrite(
        str(output),
        [f for f in frames],
        format="GIF",
        loop=0,
        duration=duration_ms,
    )


def build_timelapse(
    frame_paths: List[Path],
    output: Path,
    fps: float,
    fmt: str,
) -> None:
    if not frame_paths:
        logger.error("No frames found; cannot build timelapse.")
        sys.exit(1)

    logger.info("Building timelapse from %d frames → %s", len(frame_paths), output)

    if fmt == "gif":
        _build_with_imageio(frame_paths, output, fps)
    else:
        try:
            _build_with_ffmpeg(frame_paths, output, fps)
        except FileNotFoundError:
            logger.warning("ffmpeg not found; falling back to imageio (GIF only)")
            fallback = output.with_suffix(".gif")
            _build_with_imageio(frame_paths, fallback, fps)
            logger.info("Saved as %s", fallback)
            return

    logger.info("Timelapse saved: %s", output)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a timelapse video from ActivityWatch screenshot events."
    )
    parser.add_argument(
        "--start",
        required=True,
        type=_parse_dt,
        metavar="DATETIME",
        help="start of the time range (ISO-8601, e.g. 2025-05-01 or 2025-05-01T09:00)",
    )
    parser.add_argument(
        "--end",
        required=True,
        type=_parse_dt,
        metavar="DATETIME",
        help="end of the time range (ISO-8601)",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="output file path (e.g. timelapse.mp4 or out.gif)",
    )
    parser.add_argument(
        "--fps",
        type=float,
        default=4.0,
        help="frames per second in the output video (default: %(default)s)",
    )
    parser.add_argument(
        "--format",
        dest="fmt",
        choices=["mp4", "webm", "gif"],
        default=None,
        help="output format (default: inferred from --output extension)",
    )
    parser.add_argument(
        "--bucket",
        dest="bucket_id",
        default=None,
        help="screenshot bucket ID (default: aw-watcher-screenshot_<hostname>)",
    )
    parser.add_argument("--host", dest="host", default=None)
    parser.add_argument("--port", dest="port", type=int, default=None)
    parser.add_argument(
        "--testing", dest="testing", action="store_true",
        help="connect to the testing server",
    )
    parser.add_argument(
        "--verbose", dest="verbose", action="store_true",
        help="enable verbose logging",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    import socket

    bucket_id = args.bucket_id or f"aw-watcher-screenshot_{socket.gethostname()}"

    fmt = args.fmt or args.output.suffix.lstrip(".")
    if fmt not in ("mp4", "webm", "gif"):
        logger.warning("Unrecognised format %r; defaulting to mp4", fmt)
        fmt = "mp4"

    paths = _fetch_screenshot_paths(
        bucket_id,
        start=args.start,
        end=args.end,
        host=args.host,
        port=args.port,
        testing=args.testing,
    )

    build_timelapse(paths, args.output, args.fps, fmt)


if __name__ == "__main__":
    main()
