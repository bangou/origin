import argparse
import json
import mimetypes
import shutil
import sys
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Sequence
from urllib.parse import urlparse

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

HTML_PAGE = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Review Batch</title>
  <style>
    :root {
      --bg: #0e1513;
      --panel: #16211d;
      --panel-2: #1c2a25;
      --line: #2e463d;
      --text: #ecf4f0;
      --muted: #98b2a8;
      --accent: #57c08b;
      --warn: #f0b25d;
      --bad: #f07070;
      --good: #68d391;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
      background: linear-gradient(180deg, #0e1513, #13201b 50%, #0f1714);
      color: var(--text);
    }
    .app {
      display: grid;
      grid-template-columns: 300px 1fr;
      min-height: 100vh;
    }
    .sidebar {
      border-right: 1px solid var(--line);
      background: rgba(14, 21, 19, 0.88);
      padding: 18px;
      overflow: auto;
    }
    .main {
      padding: 18px;
      display: grid;
      grid-template-rows: auto auto 1fr auto;
      gap: 14px;
    }
    h1, h2, h3, p { margin: 0; }
    .muted { color: var(--muted); }
    .panel {
      background: rgba(22, 33, 29, 0.92);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 14px;
    }
    .stats {
      display: grid;
      grid-template-columns: repeat(6, minmax(0, 1fr));
      gap: 10px;
    }
    .stat {
      background: var(--panel-2);
      border-radius: 12px;
      padding: 10px;
    }
    .item-list {
      display: grid;
      gap: 8px;
      margin-top: 14px;
    }
    .item-button {
      width: 100%;
      text-align: left;
      border: 1px solid var(--line);
      background: var(--panel-2);
      color: var(--text);
      border-radius: 12px;
      padding: 10px 12px;
      cursor: pointer;
    }
    .item-button.active { border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent) inset; }
    .status-chip {
      display: inline-block;
      min-width: 78px;
      text-align: center;
      padding: 4px 8px;
      border-radius: 999px;
      font-size: 12px;
      border: 1px solid var(--line);
      background: #26352f;
    }
    .status-pending { color: var(--good); }
    .status-needs_review { color: var(--warn); }
    .status-approved { color: var(--good); }
    .status-corrected { color: #74c0fc; }
    .status-rejected { color: var(--bad); }
    .viewer {
      display: grid;
      grid-template-columns: minmax(240px, 340px) 1fr;
      gap: 14px;
    }
    .img-wrap {
      background: #0a0f0d;
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 12px;
      min-height: 260px;
      display: grid;
      place-items: center;
    }
    .img-wrap img {
      max-width: 100%;
      max-height: 420px;
      object-fit: contain;
      image-rendering: auto;
    }
    .meta-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }
    .meta {
      background: var(--panel-2);
      border-radius: 12px;
      padding: 10px;
    }
    .toolbar {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }
    button, input {
      font: inherit;
    }
    button.action {
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 10px 14px;
      cursor: pointer;
      color: var(--text);
      background: var(--panel-2);
    }
    button.primary { background: #1e3b30; border-color: #2c5d49; }
    button.warn { background: #3d3321; border-color: #7f6434; }
    button.danger { background: #3b2323; border-color: #7b4141; }
    input[type="text"] {
      width: 100%;
      background: #0f1714;
      border: 1px solid var(--line);
      color: var(--text);
      border-radius: 10px;
      padding: 10px 12px;
    }
    .footer {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      align-items: center;
      flex-wrap: wrap;
    }
    pre {
      white-space: pre-wrap;
      word-break: break-word;
      margin: 0;
      color: var(--muted);
    }
    @media (max-width: 1080px) {
      .app { grid-template-columns: 1fr; }
      .viewer { grid-template-columns: 1fr; }
      .stats { grid-template-columns: repeat(3, minmax(0, 1fr)); }
    }
  </style>
</head>
<body>
  <div class="app">
    <aside class="sidebar">
      <div class="panel">
        <h1>Review Batch</h1>
        <p id="batchPath" class="muted" style="margin-top:8px;"></p>
        <div class="stats" style="margin-top:14px;">
          <div class="stat"><div class="muted">总数</div><div id="statTotal"></div></div>
          <div class="stat"><div class="muted">待审</div><div id="statPending"></div></div>
          <div class="stat"><div class="muted">需复核</div><div id="statNeedsReview"></div></div>
          <div class="stat"><div class="muted">通过</div><div id="statApproved"></div></div>
          <div class="stat"><div class="muted">修正</div><div id="statCorrected"></div></div>
          <div class="stat"><div class="muted">拒绝</div><div id="statRejected"></div></div>
        </div>
      </div>
      <div class="item-list" id="itemList"></div>
    </aside>
    <main class="main">
      <div class="panel">
        <div class="footer">
          <div>
            <h2 id="title"></h2>
            <p id="subtitle" class="muted" style="margin-top:6px;"></p>
          </div>
          <span id="statusChip" class="status-chip"></span>
        </div>
      </div>
      <div class="viewer">
        <div class="panel">
          <h3>裁剪图</h3>
          <div class="img-wrap" style="margin-top:12px;"><img id="cropImage" alt="crop"></div>
        </div>
        <div class="panel">
          <h3>Overlay</h3>
          <div class="img-wrap" style="margin-top:12px;"><img id="overlayImage" alt="overlay"></div>
        </div>
      </div>
      <div class="panel">
        <div class="meta-grid">
          <div class="meta"><div class="muted">候选标签</div><div id="candidateLabel"></div></div>
          <div class="meta"><div class="muted">候选分数</div><div id="candidateScore"></div></div>
          <div class="meta"><div class="muted">bbox</div><div id="bboxText"></div></div>
          <div class="meta"><div class="muted">action hints</div><pre id="actionHints"></pre></div>
        </div>
        <div style="margin-top:14px;">
          <div class="muted" style="margin-bottom:6px;">最终标签</div>
          <input id="finalLabelInput" type="text" placeholder="例如 Ah / 8s / As">
        </div>
        <div class="toolbar" style="margin-top:14px;">
          <button class="action primary" id="approveButton">通过</button>
          <button class="action warn" id="correctButton">修正</button>
          <button class="action danger" id="rejectButton">拒绝</button>
          <button class="action" id="saveButton">仅保存文本</button>
        </div>
      </div>
      <div class="panel footer">
        <div id="message" class="muted">键盘：← → 切换，A 通过，C 修正，R 拒绝</div>
        <div class="toolbar">
          <button class="action" id="prevButton">上一张</button>
          <button class="action" id="nextButton">下一张</button>
        </div>
      </div>
    </main>
  </div>
  <script>
    const state = { rows: [], index: 0, batchPath: "", summary: {} };

    function statusLabel(status) {
      return {
        pending: "pending",
        needs_review: "needs_review",
        approved: "approved",
        corrected: "corrected",
        rejected: "rejected",
      }[status] || status;
    }

    function setMessage(text) {
      document.getElementById("message").textContent = text;
    }

    function clampIndex(index) {
      if (!state.rows.length) return 0;
      return Math.max(0, Math.min(index, state.rows.length - 1));
    }

    function summarizeRows(rows) {
      const summary = {
        total: rows.length,
        pending: 0,
        needs_review: 0,
        approved: 0,
        corrected: 0,
        rejected: 0,
      };
      for (const row of rows) {
        if (summary[row.review_status] !== undefined) {
          summary[row.review_status] += 1;
        }
      }
      return summary;
    }

    function renderList() {
      const list = document.getElementById("itemList");
      list.innerHTML = "";
      state.rows.forEach((row, index) => {
        const button = document.createElement("button");
        button.className = "item-button" + (index === state.index ? " active" : "");
        button.innerHTML = `
          <div style="display:flex;justify-content:space-between;gap:8px;align-items:center;">
            <strong>${index + 1}. ${row.card_slot}</strong>
            <span class="status-chip status-${row.review_status}">${statusLabel(row.review_status)}</span>
          </div>
          <div class="muted" style="margin-top:6px;">${row.candidate_label} (${row.candidate_score})</div>
        `;
        button.addEventListener("click", () => {
          state.index = index;
          render();
        });
        list.appendChild(button);
      });
    }

    function renderStats() {
      const summary = summarizeRows(state.rows);
      document.getElementById("statTotal").textContent = summary.total;
      document.getElementById("statPending").textContent = summary.pending;
      document.getElementById("statNeedsReview").textContent = summary.needs_review;
      document.getElementById("statApproved").textContent = summary.approved;
      document.getElementById("statCorrected").textContent = summary.corrected;
      document.getElementById("statRejected").textContent = summary.rejected;
    }

    function render() {
      renderStats();
      renderList();
      document.getElementById("batchPath").textContent = state.batchPath;
      if (!state.rows.length) {
        document.getElementById("title").textContent = "没有条目";
        return;
      }
      const row = state.rows[state.index];
      document.getElementById("title").textContent = `${state.index + 1}/${state.rows.length} ${row.card_slot}`;
      document.getElementById("subtitle").textContent = `${row.image_id} · ${row.review_item_id}`;
      const chip = document.getElementById("statusChip");
      chip.textContent = statusLabel(row.review_status);
      chip.className = `status-chip status-${row.review_status}`;
      document.getElementById("cropImage").src = row.crop_url;
      document.getElementById("overlayImage").src = row.overlay_url;
      document.getElementById("candidateLabel").textContent = row.candidate_label;
      document.getElementById("candidateScore").textContent = row.candidate_score;
      document.getElementById("bboxText").textContent = JSON.stringify(row.bbox);
      document.getElementById("actionHints").textContent = JSON.stringify(row.action_hints || {}, null, 2);
      document.getElementById("finalLabelInput").value = row.final_label || "";
    }

    async function saveRows(message) {
      const response = await fetch("/api/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rows: state.rows }),
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await response.json();
      render();
      setMessage(message);
    }

    async function applyStatus(status) {
      if (!state.rows.length) return;
      const row = state.rows[state.index];
      const finalLabelInput = document.getElementById("finalLabelInput");
      row.final_label = finalLabelInput.value.trim();
      if (status === "corrected" && !row.final_label) {
        setMessage("修正时必须填写最终标签");
        finalLabelInput.focus();
        return;
      }
      if (status === "approved" && !row.final_label) {
        delete row.final_label;
      }
      if (status === "rejected") {
        delete row.final_label;
      }
      row.review_status = status;
      await saveRows(`已保存 ${row.card_slot} -> ${status}`);
    }

    async function saveFinalLabelOnly() {
      if (!state.rows.length) return;
      const row = state.rows[state.index];
      const value = document.getElementById("finalLabelInput").value.trim();
      if (value) {
        row.final_label = value;
      } else {
        delete row.final_label;
      }
      await saveRows(`已保存 ${row.card_slot} 的文本修改`);
    }

    async function loadQueue() {
      const response = await fetch("/api/queue");
      const payload = await response.json();
      state.rows = payload.rows;
      state.batchPath = payload.batch_dir;
      state.index = clampIndex(state.index);
      render();
    }

    document.getElementById("approveButton").addEventListener("click", () => applyStatus("approved"));
    document.getElementById("correctButton").addEventListener("click", () => applyStatus("corrected"));
    document.getElementById("rejectButton").addEventListener("click", () => applyStatus("rejected"));
    document.getElementById("saveButton").addEventListener("click", () => saveFinalLabelOnly());
    document.getElementById("prevButton").addEventListener("click", () => {
      state.index = clampIndex(state.index - 1);
      render();
    });
    document.getElementById("nextButton").addEventListener("click", () => {
      state.index = clampIndex(state.index + 1);
      render();
    });
    document.addEventListener("keydown", (event) => {
      if (event.target && event.target.tagName === "INPUT") {
        if (event.key === "Enter") {
          saveFinalLabelOnly();
          event.preventDefault();
        }
        return;
      }
      if (event.key === "ArrowLeft") {
        state.index = clampIndex(state.index - 1);
        render();
      } else if (event.key === "ArrowRight") {
        state.index = clampIndex(state.index + 1);
        render();
      } else if (event.key.toLowerCase() === "a") {
        applyStatus("approved");
      } else if (event.key.toLowerCase() === "c") {
        applyStatus("corrected");
      } else if (event.key.toLowerCase() === "r") {
        applyStatus("rejected");
      }
    });

    loadQueue().catch((error) => setMessage(String(error)));
  </script>
</body>
</html>
"""


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def load_review_queue(batch_dir: Path) -> list[dict[str, Any]]:
    return _load_jsonl(batch_dir / "review_queue.jsonl")


def save_review_queue(batch_dir: Path, rows: list[dict[str, Any]]) -> None:
    queue_path = batch_dir / "review_queue.jsonl"
    backup_path = batch_dir / "review_queue.backup.jsonl"
    if queue_path.exists() and not backup_path.exists():
        shutil.copy2(queue_path, backup_path)
    queue_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def _summary(rows: list[dict[str, Any]]) -> dict[str, int]:
    summary = {
        "total": len(rows),
        "pending": 0,
        "needs_review": 0,
        "approved": 0,
        "corrected": 0,
        "rejected": 0,
    }
    for row in rows:
        status = row.get("review_status", "")
        if status in summary:
            summary[status] += 1
    return summary


def build_review_payload(batch_dir: Path) -> dict[str, Any]:
    rows = []
    for row in load_review_queue(batch_dir):
        normalized = dict(row)
        crop_path = Path(row["crop_path"])
        overlay_path = Path(row["overlay_path"])
        normalized["crop_url"] = "/files/" + crop_path.relative_to(batch_dir).as_posix()
        normalized["overlay_url"] = "/files/" + overlay_path.relative_to(batch_dir).as_posix()
        rows.append(normalized)
    return {
        "batch_dir": str(batch_dir),
        "rows": rows,
        "summary": _summary(rows),
    }


def _safe_file_path(batch_dir: Path, request_path: str) -> Path | None:
    candidate = (batch_dir / request_path.removeprefix("/files/")).resolve()
    try:
        candidate.relative_to(batch_dir.resolve())
    except ValueError:
        return None
    return candidate if candidate.is_file() else None


def create_server(batch_dir: Path, host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    resolved_batch_dir = batch_dir.resolve()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:
            return

        def _send_bytes(
            self,
            status: int,
            body: bytes,
            content_type: str,
        ) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
            self._send_bytes(
                status,
                json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8",
            )

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/":
                self._send_bytes(200, HTML_PAGE.encode("utf-8"), "text/html; charset=utf-8")
                return
            if parsed.path == "/api/queue":
                self._send_json(build_review_payload(resolved_batch_dir))
                return
            if parsed.path.startswith("/files/"):
                target = _safe_file_path(resolved_batch_dir, parsed.path)
                if target is None:
                    self._send_json({"error": "file not found"}, status=404)
                    return
                self._send_bytes(
                    200,
                    target.read_bytes(),
                    mimetypes.guess_type(target.name)[0] or "application/octet-stream",
                )
                return
            self._send_json({"error": "not found"}, status=404)

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path != "/api/save":
                self._send_json({"error": "not found"}, status=404)
                return
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            rows = payload.get("rows", [])
            save_review_queue(resolved_batch_dir, rows)
            self._send_json({"ok": True, "summary": _summary(rows)})

    return ThreadingHTTPServer((host, port), Handler)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Serve a local review page for one review batch."
    )
    parser.add_argument("--batch-dir", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--open", action="store_true", dest="open_browser")
    args = parser.parse_args(argv)

    server = create_server(args.batch_dir, host=args.host, port=args.port)
    url = f"http://{args.host}:{server.server_port}/"
    print(f"Review page: {url}")
    print(f"Batch dir: {args.batch_dir}")
    if args.open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
