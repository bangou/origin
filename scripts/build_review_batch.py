import argparse
import sys
from pathlib import Path
from typing import Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from vision_db.review_batches import build_review_batch


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a phase 3 review batch.")
    parser.add_argument("--db-root", type=Path, required=True)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--batch-root", type=Path, required=True)
    parser.add_argument("--template-threshold", type=float, default=0.65)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args(argv)

    summary = build_review_batch(
        db_root=args.db_root,
        profile_path=args.profile,
        batch_root=args.batch_root,
        template_threshold=args.template_threshold,
        limit=args.limit,
    )
    print(
        " ".join(
            [
                f'batch_id={summary["batch_id"]}',
                f'review_item_count={summary["review_item_count"]}',
                f'needs_review_count={summary["needs_review_count"]}',
            ]
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
