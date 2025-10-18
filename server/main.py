"""FastAPI server entrypoint for the PDF → Markdown web app."""
import os
import uuid
from typing import Dict, Any
from datetime import datetime, timezone
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from pdftool.processing.extract import extract_pdf_to_markdown

app = FastAPI()

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
OUTPUT_DIR = os.path.join(os.getcwd(), "outputs")
FRONTEND_DIR = os.path.join(os.getcwd(), "frontend")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# In-memory job store for simple progress tracking
JOBS: Dict[str, Dict[str, Any]] = {}

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
def index():
    """Serve the frontend index page."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>PDF to Markdown</h1><p>Upload UI not found.</p>"


@app.post("/upload")
def upload_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Handle PDF upload, enqueue OCR-only extraction, and return a job id for progress."""
    fname = (file.filename or "").strip()
    if not fname.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    safe_name = fname.replace(" ", "_")
    upload_path = os.path.join(UPLOAD_DIR, f"{timestamp}_{safe_name}")
    with open(upload_path, "wb") as f:
        f.write(file.file.read())

    out_md_name = os.path.splitext(os.path.basename(upload_path))[0] + ".md"
    out_md_path = os.path.join(OUTPUT_DIR, out_md_name)

    # Determine total pages up-front for progress display
    try:
        reader = PdfReader(upload_path)
        total_pages = len(reader.pages)
    except (PdfReadError, OSError, ValueError) as e:
        raise HTTPException(status_code=500, detail=f"Failed to read PDF: {e}") from e

    job_id = uuid.uuid4().hex
    JOBS[job_id] = {
        "status": "processing",
        "total": total_pages,
        "done": 0,
        "filename": out_md_name,
        "markdown": None,
        "error": None,
    }

    def run_extraction(job: str, src: str, dst: str):
        """Background task: run extraction and update progress."""
        def cb(page: int, total: int):
            j = JOBS.get(job)
            if j is not None:
                j["done"] = page
                j["total"] = total
        try:
            extract_pdf_to_markdown(src, dst, progress=cb)
            j = JOBS.get(job)
            if j is not None:
                j["status"] = "done"
                j["markdown"] = f"/download/{out_md_name}"
        except Exception as e:
            j = JOBS.get(job)
            if j is not None:
                j["status"] = "error"
                j["error"] = str(e)

    # Always run in background for HTTP requests
    background_tasks.add_task(run_extraction, job_id, upload_path, out_md_path)

    return {"job_id": job_id, "total": total_pages, "filename": out_md_name}


@app.get("/status/{job_id}")
def status(job_id: str):
    """Return current job status and progress."""
    job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    done = int(job.get("done") or 0)
    total = int(job.get("total") or 0)
    percent = int(done * 100 / total) if total > 0 else 0
    return {
        "status": job.get("status"),
        "done": done,
        "total": total,
        "percent": percent,
        "filename": job.get("filename"),
        "markdown": job.get("markdown"),
        "error": job.get("error"),
    }


@app.get("/download/{name}")
def download_md(name: str):
    """Return the generated Markdown file by name."""
    path = os.path.join(OUTPUT_DIR, name)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, media_type="text/markdown")
