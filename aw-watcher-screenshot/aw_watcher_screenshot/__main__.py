from aw_core.log import setup_logging

from .config import parse_args
from .screenshot import ScreenshotWatcher


def main() -> None:
    args = parse_args()

    setup_logging(
        "aw-watcher-screenshot",
        testing=args.testing,
        verbose=args.verbose,
        log_stderr=True,
        log_file=True,
    )

    watcher = ScreenshotWatcher(args, testing=args.testing)
    watcher.run()


if __name__ == "__main__":
    main()
