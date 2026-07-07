import json
import subprocess
import sys
from http.client import HTTPConnection
from pathlib import Path
from threading import Thread

from PIL import Image

from scripts.review_batch_web import build_review_payload, create_server


def _write_review_row(
    batch_dir: Path,
    file_stub: str,
    review_item_id: str,
    image_id: str,
    card_slot: str,
    candidate_label: str,
) -> dict[str, object]:
    crops_dir = batch_dir / "crops"
    overlays_dir = batch_dir / "overlays"
    crops_dir.mkdir(parents=True, exist_ok=True)
    overlays_dir.mkdir(parents=True, exist_ok=True)

    crop_path = crops_dir / f"{file_stub}.png"
    overlay_path = overlays_dir / f"{image_id}.png"
    Image.new("RGB", (50, 73), "white").save(crop_path)
    Image.new("RGB", (400, 240), "#008b74").save(overlay_path)
    return {
        "batch_id": batch_dir.name,
        "review_item_id": review_item_id,
        "image_id": image_id,
        "source_profile": "seed",
        "card_slot": card_slot,
        "candidate_label": candidate_label,
        "candidate_score": 0.91,
        "match_source": "templates/cards",
        "bbox": [963, 872, 50, 73],
        "crop_path": str(crop_path),
        "overlay_path": str(overlay_path),
        "review_status": "pending",
        "action_hints": {},
    }


def test_build_review_payload_and_http_save_round_trip(tmp_path: Path) -> None:
    batch_root = tmp_path / "review_batches"
    batch_dir = batch_root / "batch-1"
    second_batch_dir = batch_root / "batch-2"
    rows = [
        _write_review_row(batch_dir, "hand_2", "item-1", "img-1", "hand_2", "4h"),
        _write_review_row(batch_dir, "flop_1", "item-2", "img-2", "flop_1", "9c"),
    ]
    second_batch_rows = [
        _write_review_row(second_batch_dir, "turn", "item-3", "img-3", "turn", "As"),
    ]
    (batch_dir / "review_queue.jsonl").write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )
    (second_batch_dir / "review_queue.jsonl").write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in second_batch_rows) + "\n",
        encoding="utf-8",
    )

    payload = build_review_payload(batch_root, "batch-1", "img-1")
    assert payload["summary"]["total"] == 2
    assert payload["rows"][0]["crop_url"] == "/files/batch-1/crops/hand_2.png"
    assert payload["image_ids"] == ["img-1", "img-2"]
    assert payload["selected_image_id"] == "img-1"

    server = create_server(batch_dir, host="127.0.0.1", port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        connection = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        connection.request("GET", "/")
        page_response = connection.getresponse()
        page_body = page_response.read().decode("utf-8")
        assert page_response.status == 200
        assert "spades = \u9ed1\u6843" in page_body
        assert "8s</strong> = 8\u9ed1\u6843" in page_body

        connection.request("GET", "/api/batches")
        batches_response = connection.getresponse()
        batches_payload = json.loads(batches_response.read().decode("utf-8"))
        assert batches_response.status == 200
        assert [item["batch_id"] for item in batches_payload["batches"]] == [
            "batch-1",
            "batch-2",
        ]

        connection.request("GET", "/api/queue")
        response = connection.getresponse()
        body = response.read()
        assert response.status == 200
        queue_payload = json.loads(body.decode("utf-8"))
        assert queue_payload["selected_batch_id"] == "batch-1"
        assert queue_payload["selected_image_id"] == "img-1"
        assert queue_payload["rows"][0]["candidate_label"] == "4h"

        connection.request("GET", "/api/queue?batch_id=batch-1&image_id=img-2")
        second_image_response = connection.getresponse()
        second_image_payload = json.loads(second_image_response.read().decode("utf-8"))
        assert second_image_response.status == 200
        assert [row["image_id"] for row in second_image_payload["rows"]] == ["img-2"]

        rows = queue_payload["rows"]
        rows[0]["review_status"] = "corrected"
        rows[0]["final_label"] = "Ah"
        request_body = json.dumps({"batch_id": "batch-1", "rows": rows}).encode("utf-8")
        connection.request(
            "POST",
            "/api/save",
            body=request_body,
            headers={
                "Content-Type": "application/json",
                "Content-Length": str(len(request_body)),
            },
        )
        save_response = connection.getresponse()
        save_response.read()
        assert save_response.status == 200

        connection.request("GET", "/files/batch-1/crops/hand_2.png")
        file_response = connection.getresponse()
        file_body = file_response.read()
        assert file_response.status == 200
        assert file_body
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()

    saved_row = json.loads(
        (batch_dir / "review_queue.jsonl").read_text(encoding="utf-8").splitlines()[0]
    )
    assert saved_row["review_status"] == "corrected"
    assert saved_row["final_label"] == "Ah"
    assert (batch_dir / "review_queue.backup.jsonl").exists()


def test_review_batch_web_script_runs_via_python_command() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "review_batch_web.py"

    result = subprocess.run(
        [sys.executable, str(script_path), "--help"],
        check=False,
        capture_output=True,
        text=True,
        cwd=str(repo_root),
    )

    assert result.returncode == 0, result.stderr
    assert "Serve a local review page for one review batch." in result.stdout
