"""
launcher/app.py — Desktop Web UI for eda-report.

Starts a local FastAPI server bound to 127.0.0.1 on a random available port
and opens the browser automatically.  No internet connection required.

Interfaces
----------
POST /generate      Starts a render; streams log output via WebSocket /ws/{job_id}
GET  /download/{f}  Serves output files from output_dir (no path traversal)
GET  /              Serves the launcher UI (index.html)

Usage
-----
  python launcher/app.py          # developer launch
  EDA Report.exe / .app           # packaged launch (PyInstaller)

Architecture note
-----------------
Use WebSocket (not StreamingResponse) for render log output — StreamingResponse
does not support the back-and-forth needed for cancel/status signals.
"""

from __future__ import annotations

import asyncio
import pathlib
import socket
import subprocess
import sys
import uuid
import webbrowser
from typing import Any

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="EDA Report Launcher", docs_url=None, redoc_url=None)

# Locate templates and static dirs relative to this file
_HERE = pathlib.Path(__file__).parent
templates = Jinja2Templates(directory=str(_HERE / "templates"))
app.mount("/static", StaticFiles(directory=str(_HERE / "static")), name="static")

# Active render jobs: job_id → {"process": Popen, "output_dir": Path, "report": Path}
_jobs: dict[str, dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index(request: Any):
    """Serve the launcher UI."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/generate")
async def generate(body: dict):
    """Start a render job.  Returns ``{"job_id": "..."}`` immediately.

    Expected body
    -------------
    {
        "data_file":   "/abs/path/to/delivery.xpt",
        "x_axis_var":  "procdt",          // optional
        "title":       "CABG 2025 Q1",    // optional
        "output_dir":  "/abs/path/out",   // optional
        "cat_max":     10,
        "suppress_above": 20,
        "no_manifest": false,
        "manifest_format": "both"
    }

    TODO: implement
    - Validate data_file exists.
    - Build the eda-report CLI command list.
    - Launch with subprocess.Popen, stdout=PIPE, stderr=STDOUT.
    - Store the process in _jobs[job_id].
    - Return job_id.
    """
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "pending", "output_dir": None, "report": None}
    # TODO: launch subprocess
    raise NotImplementedError


@app.websocket("/ws/{job_id}")
async def ws_log(websocket: WebSocket, job_id: str):
    """Stream render log output to the browser line-by-line via WebSocket.

    Sends lines as plain text.  Sends ``__DONE__`` or ``__ERROR__`` as the
    final message so the UI knows when to show the Open/Download buttons.

    TODO: implement
    - Accept the WebSocket.
    - Read _jobs[job_id]["process"].stdout line-by-line (non-blocking).
    - Send each line via websocket.send_text().
    - On process exit: send __DONE__ (rc=0) or __ERROR__ (rc!=0).
    """
    await websocket.accept()
    try:
        # TODO: implement streaming
        await websocket.send_text("__NOT_IMPLEMENTED__")
    except WebSocketDisconnect:
        pass


@app.get("/download/{filename}")
async def download(filename: str, output_dir: str):
    """Serve a file from output_dir.  Prevents path traversal.

    Parameters
    ----------
    filename:
        Bare filename (no directory component).
    output_dir:
        Absolute path to the output directory (passed as query param).

    TODO: implement
    - Resolve output_dir / filename.
    - Reject if the resolved path escapes output_dir (path traversal guard).
    - Return FileResponse with media_type='application/octet-stream'.
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _find_free_port() -> int:
    """Return an available localhost port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def run():
    """Start the server and open the browser."""
    port = _find_free_port()
    url = f"http://127.0.0.1:{port}"

    # Open browser slightly after server starts
    async def _open_browser():
        await asyncio.sleep(1.0)
        webbrowser.open(url)

    @app.on_event("startup")
    async def startup():
        asyncio.create_task(_open_browser())

    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    run()
