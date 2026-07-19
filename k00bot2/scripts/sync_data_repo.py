# thinkx-system/k00bot2/scripts/sync_data_repo.py
#
# Mirror live k00bot2 data into the adjacent persistence repository.

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


IGNORED_NAMES = {"log_daily.txt", "log_monthly.txt", "x_archive"}


def ignored_paths(_directory: str, names: list[str]) -> set[str]:
    return set(names) & IGNORED_NAMES


def mirror_data(source: Path, target: Path) -> None:
    source = source.resolve()
    target = target.resolve()

    if not source.is_dir():
        raise RuntimeError(f"source data directory does not exist: {source}")
    if target.name != "data":
        raise RuntimeError(f"target must be a data directory: {target}")
    if not (target.parent / ".git").exists():
        raise RuntimeError(f"target parent is not a Git clone: {target.parent}")
    if source == target:
        raise RuntimeError("source and target data directories are identical")

    staging = target.parent / ".data-sync-new"
    previous = target.parent / ".data-sync-previous"
    for temporary_path in (staging, previous):
        if temporary_path.exists():
            shutil.rmtree(temporary_path)

    shutil.copytree(source, staging, ignore=ignored_paths)
    try:
        if target.exists():
            target.rename(previous)
        staging.rename(target)
    except Exception:
        if previous.exists() and not target.exists():
            previous.rename(target)
        raise
    else:
        if previous.exists():
            shutil.rmtree(previous)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    args = parser.parse_args()
    mirror_data(args.source, args.target)


if __name__ == "__main__":
    main()
