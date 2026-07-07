import argparse
import sys
from pathlib import Path
from typing import Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from vision_db.review_ingest import ingest_review_batch


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest approved review-batch samples.")
    parser.add_argument("--batch-dir", type=Path, required=True)
    parser.add_argument("--db-root", type=Path, required=True)
    args = parser.parse_args(argv)

    summary = ingest_review_batch(args.batch_dir, args.db_root)
    print(
        " ".join(
            [
                f'ingested_count={summary["ingested_count"]}',
                f'duplicate_count={summary["duplicate_count"]}',
                f'skipped_count={summary["skipped_count"]}',
            ]
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
