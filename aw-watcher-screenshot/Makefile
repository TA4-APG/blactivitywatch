.PHONY: build test typecheck clean

build:
	poetry install

test:
	poetry run aw-watcher-screenshot --help
	poetry run aw-screenshot-timelapse --help
	poetry run pytest tests/ -v

typecheck:
	poetry run mypy aw_watcher_screenshot --ignore-missing-imports

clean:
	rm -rf build dist
	rm -rf aw_watcher_screenshot/__pycache__
	rm -rf tests/__pycache__
