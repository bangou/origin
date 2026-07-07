import json
from pathlib import Path
import subprocess
import sys

from PIL import Image

from scripts.ingest_review_batch import main
from vision_db.layout import ensure_layout
from vision_db.review_ingest import ingest_review_batch


def test_ingest_review_batch_only_writes_approved_and_corrected_samples(
    tmp_path: Path,
) -> None:
    db_root = tmp_path / "data" / "vision_db"
    batch_dir = tmp_path / "review_batches" / "batch-1"
    crops_dir = batch_dir / "crops"
    crops_dir.mkdir(parents=True)
    ensure_layout(db_root)

    approved_crop = crops_dir / "approved.png"
    corrected_crop = crops_dir / "corrected.png"
    rejected_crop = crops_dir / "rejected.png"
    Image.new("RGB", (50, 73), "white").save(approved_crop)
    Image.new("RGB", (46, 73), "white").save(corrected_crop)
    Image.new("RGB", (50, 73), "white").save(rejected_crop)

    queue_path = batch_dir / "review_queue.jsonl"
    rows = [
        {
            "batch_id": "batch-1",
            "review_item_id": "one",
            "image_id": "img-1",
            "source_profile": "seed",
            "card_slot": "flop_1",
            "candidate_label": "9d",
            "candidate_score": 0.91,
            "match_source": "templates/cards",
            "bbox": [829, 476, 50, 73],
            "crop_path": str(approved_crop),
            "overlay_path": "",
            "review_status": "approved",
        },
        {
            "batch_id": "batch-1",
            "review_item_id": "two",
            "image_id": "img-1",
            "source_profile": "seed",
            "card_slot": "hand_1",
            "candidate_label": "Qc",
            "candidate_score": 0.72,
            "match_source": "templates/cards",
            "bbox": [908, 872, 46, 73],
            "crop_path": str(corrected_crop),
            "overlay_path": "",
            "review_status": "corrected",
            "final_label": "Qc",
        },
        {
            "batch_id": "batch-1",
            "review_item_id": "three",
            "image_id": "img-1",
            "source_profile": "seed",
            "card_slot": "hand_2",
            "candidate_label": "3c",
            "candidate_score": 0.55,
            "match_source": "templates/cards",
            "bbox": [967, 872, 46, 73],
            "crop_path": str(rejected_crop),
            "overlay_path": "",
            "review_status": "rejected",
        },
    ]
    queue_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )

    first = ingest_review_batch(batch_dir, db_root)
    second = ingest_review_batch(batch_dir, db_root)
    sample_rows = [
        json.loads(line)
        for line in (db_root / "metadata" / "samples_cards.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]
    widths = {row["label"]: row["width"] for row in sample_rows}

    assert first["ingested_count"] == 2
    assert first["duplicate_count"] == 0
    assert second["duplicate_count"] == 2
    assert len(sample_rows) == 2
    assert sorted(row["label"] for row in sample_rows) == ["9d", "Qc"]
    assert widths == {"9d": 50, "Qc": 46}


def test_ingest_review_batch_cli_prints_summary(tmp_path: Path, capsys) -> None:
    db_root = tmp_path / "data" / "vision_db"
    batch_dir = tmp_path / "review_batches" / "batch-1"
    crops_dir = batch_dir / "crops"
    crops_dir.mkdir(parents=True)
    ensure_layout(db_root)

    crop_path = crops_dir / "approved.png"
    Image.new("RGB", (50, 73), "white").save(crop_path)
    (batch_dir / "review_queue.jsonl").write_text(
        json.dumps(
            {
                "batch_id": "batch-1",
                "review_item_id": "one",
                "image_id": "img-1",
                "source_profile": "seed",
                "card_slot": "flop_1",
                "candidate_label": "9d",
                "candidate_score": 0.91,
                "match_source": "templates/cards",
                "bbox": [829, 476, 50, 73],
                "crop_path": str(crop_path),
                "overlay_path": "",
                "review_status": "approved",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    exit_code = main(["--batch-dir", str(batch_dir), "--db-root", str(db_root)])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "ingested_count=1" in output
    assert "duplicate_count=0" in output


def test_ingest_review_batch_script_runs_via_python_command() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "ingest_review_batch.py"

    result = subprocess.run(
        [sys.executable, str(script_path), "--help"],
        check=False,
        capture_output=True,
        text=True,
        cwd=str(repo_root),
    )

    assert result.returncode == 0, result.stderr
    assert "Ingest approved review-batch samples." in result.stdout
