import json
import subprocess
import sys
from http.client import HTTPConnection
from pathlib import Path
from threading import Thread

from PIL import Image

from scripts.review_batch_web import build_review_payload, create_server


def test_build_review_payload_and_http_save_round_trip(tmp_path: Path) -> None:
    batch_dir = tmp_path / "review_batches" / "batch-1"
    crops_dir = batch_dir / "crops"
    overlays_dir = batch_dir / "overlays"
    crops_dir.mkdir(parents=True)
    overlays_dir.mkdir(parents=True)

    crop_path = crops_dir / "hand_2.png"
    overlay_path = overlays_dir / "table.png"
    Image.new("RGB", (50, 73), "white").save(crop_path)
    Image.new("RGB", (400, 240), "#008b74").save(overlay_path)
    (batch_dir / "review_queue.jsonl").write_text(
        json.dumps(
            {
                "batch_id": "batch-1",
                "review_item_id": "item-1",
                "image_id": "img-1",
                "source_profile": "seed",
                "card_slot": "hand_2",
                "candidate_label": "4h",
                "candidate_score": 0.91,
                "match_source": "templates/cards",
                "bbox": [963, 872, 50, 73],
                "crop_path": str(crop_path),
                "overlay_path": str(overlay_path),
                "review_status": "pending",
                "action_hints": {},
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    payload = build_review_payload(batch_dir)
    assert payload["summary"]["total"] == 1
    assert payload["rows"][0]["crop_url"] == "/files/crops/hand_2.png"

    server = create_server(batch_dir, host="127.0.0.1", port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        connection = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        connection.request("GET", "/api/queue")
        response = connection.getresponse()
        body = response.read()
        assert response.status == 200
        queue_payload = json.loads(body.decode("utf-8"))
        assert queue_payload["rows"][0]["candidate_label"] == "4h"

        rows = queue_payload["rows"]
        rows[0]["review_status"] = "corrected"
        rows[0]["final_label"] = "Ah"
        request_body = json.dumps({"rows": rows}).encode("utf-8")
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

        connection.request("GET", "/files/crops/hand_2.png")
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
