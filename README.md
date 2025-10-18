# PDF → Markdown Web App

A small web app that lets you upload PDFs and get a clean Markdown file back. It uses robust text extraction and automatically OCRs pages with embedded/subset fonts (the “weird tokens” problem), so you get readable text even when the PDF’s text layer is broken.

## Features

- Upload a PDF and receive a `.md` download link
- OCR-only extraction (English) with adaptive DPI for better accuracy
- Simple frontend (HTML/JS)
- Cleanup utility for temp artifacts and old files

## Project structure

``` text
server/
  main.py                 # FastAPI app, routes for upload/download, serves frontend
frontend/
  index.html              # Upload UI
uploads/                  # Uploaded PDFs
outputs/                  # Generated Markdown and any OCR artifacts
pdftool/
  __init__.py             # Package metadata
  cli.py                  # Installable CLI entry point
  processing/
    extract.py            # OCR-only extraction pipeline
scripts/
  setup/
    setup_app.ps1         # Full one-click setup on Windows (tools + venv + deps)
    setup_app.sh          # Full one-click setup on macOS/Linux (tools + venv + deps)
    setup_all.py          # Unified cross-platform setup (tools + venv + deps)
  start/
    start_app.py          # Cross-platform start (uses venv python if present)
    start_app.ps1         # Windows start script
    start_app.sh          # macOS/Linux start script
  tools/
    install_tools.ps1     # One-click install on Windows (Poppler, Tesseract, eng data)
    install_tools.sh      # One-click install on macOS/Linux (Poppler, Tesseract, eng data)
  maintenance/
    cleanup.py            # Remove temp artifacts and old files
.venv/                    # Python virtual environment (local)
pyproject.toml            # Project metadata and dependencies
README.md                 # This file
bootstrap.py              # Root-level script: runs setup then start
```

## Quick Start (single command)

```bash
python bootstrap.py
```

This will install external tools (Poppler/Tesseract), create the virtual environment, install Python dependencies using the project metadata, and start the server at `http://127.0.0.1:8000`. If `.venv` already exists, setup is skipped where possible and dependencies are ensured.

## Setup

- Unified:

```bash
python scripts/setup/setup_all.py
```

- Windows:

```powershell
scripts\setup\setup_app.ps1
```

- macOS/Linux:

```bash
chmod +x scripts/setup/setup_app.sh
scripts/setup/setup_app.sh
```

These scripts will:

- Install Poppler/Tesseract and ensure `eng.traineddata`
- Create the venv
- Install the project in editable mode via `pip install -e .` (pyproject.toml)

## Start

- Cross‑platform:

```bash
python scripts/start/start_app.py
```

- Windows:

```powershell
scripts\start\start_app.ps1
```

- macOS/Linux:

```bash
chmod +x scripts/start/start_app.sh
scripts/start/start_app.sh
```

Open the app at `http://127.0.0.1:8000` and upload a PDF. When processing finishes, you’ll see a link to download the generated `.md`.

## CLI usage

Install the project in your venv (editable mode):

- Windows:

```powershell
.venv\Scripts\pip install -e .
```

- macOS/Linux:

```bash
source .venv/bin/activate
pip install -e .
```

Then run:

```bash
pdftool convert <path-to.pdf> [-o outputs/out.md] [--dpi 400]
```

Alternative without installing the console script:

```bash
python -m pdftool.cli convert <path-to.pdf> [-o outputs/out.md] [--dpi 400]
```

## Extraction pipeline (OCR‑only)

1. For each page, render to PNG using `pdftoppm` (DPI adaptive: 300 → 400 → 600).
2. OCR with Tesseract (English language `-l eng`, `--psm 6`).
3. Pick the best OCR result via a simple token-count heuristic; early-stop when text looks good.
4. Auto-cleanup temporary OCR files (`.txt`, `.png`).
5. Write a unified Markdown file with per-page sections.

Notes:

- OCR language is English only by default. To add languages, install the trained data files and set `TESSDATA_PREFIX`.
- Higher DPI improves accuracy for small text but costs time; the adaptive mode balances speed and quality.

## Cleanup

Use the utility to remove temp artifacts and old files:

```bash
.venv\Scripts\python scripts/maintenance/cleanup.py --dry-run --retention-days 14
.venv\Scripts\python scripts/maintenance/cleanup.py --retention-days 14
```

It deletes known temp files (e.g., OCR PNGs `ocr_page_*.png`) and any `uploads/` or `outputs/` files older than the retention window.

## Troubleshooting

- If OCR results are sparse on certain pages, the adaptive DPI will retry at higher resolution.
- Tesseract language not found: ensure `TESSDATA_PREFIX` points to the tessdata directory and that `eng.traineddata` exists.
- Missing Poppler/Tesseract: run the one‑click scripts above.

## Extending

- Add progress and job IDs for long-running conversions
- Support OCR language selection in the UI
- Add Dockerfile/image bundling Poppler/Tesseract
- Improve Markdown structuring (detect headings/TOC, split by sections)

## License

MIT (or your preferred license). Add a `LICENSE` file if needed.
