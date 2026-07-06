import argparse
import sys
from pathlib import Path
from typing import Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from vision_db.pipeline import build_vision_db


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the phase 2 vision database.")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--db-root", type=Path, required=True)
    args = parser.parse_args(argv)

    summary = build_vision_db(args.source, args.db_root)
    print(
        " ".join(
            [
                f'total_images={summary["total_images"]}',
                f'template_seed_count={summary["template_seed_count"]}',
                f'full_screenshot_count={summary["full_screenshot_count"]}',
                f'compressed_count={summary["compressed_count"]}',
                f'failure_count={summary["failure_count"]}',
            ]
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
