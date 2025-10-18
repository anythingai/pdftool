"""PDF text extraction using Azure Document Intelligence OCR."""
import os
import subprocess
import time
from io import BytesIO
from typing import Callable, List, Optional

import requests
from dotenv import load_dotenv
from PIL import Image
from pypdf import PdfReader
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Load environment variables from .env file
load_dotenv()

# Increase PIL image size limit to handle large PDF renders
Image.MAX_IMAGE_PIXELS = 200_000_000  # 200 megapixels

DEFAULT_DPI = 300


def tool_exists(name: str) -> bool:
    """Check if a command-line tool exists and is executable."""
    try:
        subprocess.run([name, "-v"], capture_output=True, check=True)
        return True
    except (OSError, subprocess.CalledProcessError):
        return False


def render_page_to_png(pdf_path: str, page_number: int, out_png: str, dpi: int = 300) -> bool:
    """Render a PDF page to PNG image using pdftoppm."""
    if not tool_exists("pdftoppm"):
        return False
    try:
        subprocess.run([
            "pdftoppm",
            "-q",
            "-f", str(page_number),
            "-l", str(page_number),
            "-r", str(dpi),
            "-png",
            "-singlefile",
            pdf_path,
            os.path.splitext(out_png)[0],
        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        return os.path.exists(out_png)
    except (OSError, subprocess.CalledProcessError):
        return False


def azure_document_intelligence_ocr(png_path: str) -> str:
    """Extract text using Azure AI Document Intelligence REST API."""
    endpoint = os.environ.get("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    key = os.environ.get("AZURE_DOCUMENT_INTELLIGENCE_KEY")

    if not endpoint or not key:
        raise ValueError(
            "Azure Document Intelligence credentials not found. "
            "Please set AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and "
            "AZURE_DOCUMENT_INTELLIGENCE_KEY environment variables."
        )

    try:
        # Read and resize the image file for Azure compatibility
        with Image.open(png_path) as img:
            # Azure Document Intelligence has size limits, resize if too large
            max_dimension = 2400  # keep payload small and within service limits
            if img.width > max_dimension or img.height > max_dimension:
                # Calculate new dimensions maintaining aspect ratio
                ratio = min(max_dimension / img.width, max_dimension / img.height)
                new_width = int(img.width * ratio)
                new_height = int(img.height * ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)  # type: ignore

            # Convert to JPEG bytes with adaptive compression to keep payload small
            img = img.convert("RGB")
            target_bytes = 1_500_000  # ~1.5 MB target per page
            quality = 85
            downscale_tries = 0
            while True:
                img_buffer = BytesIO()
                img.save(img_buffer, format="JPEG", quality=quality, optimize=True)
                image_bytes = img_buffer.getvalue()
                if len(image_bytes) <= target_bytes:
                    break
                # Reduce quality first, then downscale if still too large
                if quality > 65:
                    quality = max(60, quality - 10)
                elif downscale_tries < 2:
                    # Downscale by 85% and retry from higher quality
                    downscale_tries += 1
                    new_w = int(img.width * 0.85)
                    new_h = int(img.height * 0.85)
                    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)  # type: ignore
                    quality = 80
                else:
                    # Accept current bytes if we've tried enough
                    break

        # Prepare the request URL
        url = (
            f"{endpoint.rstrip('/')}/formrecognizer/"
            f"documentModels/prebuilt-read:analyze?api-version=2023-07-31"
        )

        # Prepare headers for binary upload
        headers = {
            "Ocp-Apim-Subscription-Key": key,
            "Content-Type": "application/octet-stream",
            "Accept": "application/json",
        }

        # Create a session with retry for robust networking
        session = requests.Session()
        retries = Retry(
            total=3,
            connect=3,
            read=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        # Start the analysis
        try:
            response = session.post(url, headers=headers, data=image_bytes, timeout=300)
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Azure Document Intelligence POST failed: {e}") from e

        if response.status_code != 202:
            raise RuntimeError(
                f"Azure Document Intelligence API error: "
                f"{response.status_code} - {response.text}"
            )

        # Get the result URL from the response headers
        result_url = response.headers.get("Operation-Location")
        if not result_url:
            raise RuntimeError(
                "No Operation-Location header found in Azure response"
            )

        # Poll for results
        start_time = time.monotonic()
        # Poll up to ~180 seconds, honoring Retry-After and using ~2s cadence
        while (time.monotonic() - start_time) < 180:
            try:
                result_response = session.get(
                    result_url,
                    headers={"Ocp-Apim-Subscription-Key": key},
                    timeout=60,
                )
            except requests.exceptions.RequestException:
                # Transient network error (e.g., NameResolutionError). Backoff and retry.
                time.sleep(5)
                continue

            if result_response.status_code == 200:
                result = result_response.json()
                status = result.get("status")

                if status == "succeeded":
                    # Extract text from all pages
                    text_parts: List[str] = []
                    pages = result.get("analyzeResult", {}).get("pages", [])

                    for page in pages:
                        lines = page.get("lines", [])
                        for line in lines:
                            content = line.get("content", "")
                            if isinstance(content, str):
                                text_parts.append(content)

                    return "\n".join(text_parts)

                if status == "failed":
                    raise RuntimeError(
                        f"Azure Document Intelligence analysis failed: {result}"
                    )

                # Still running: wait per Retry-After or default ~2s
                retry_after = result_response.headers.get("Retry-After")
                try:
                    wait_s = max(2, int(retry_after)) if retry_after else 2
                except ValueError:
                    wait_s = 2
                time.sleep(wait_s)
                continue

            # Handle throttling or transient errors with a short backoff
            if result_response.status_code in (429, 500, 502, 503, 504):
                retry_after = result_response.headers.get("Retry-After")
                try:
                    wait_s = max(2, int(retry_after)) if retry_after else 5
                except ValueError:
                    wait_s = 5
                time.sleep(wait_s)
                continue

            raise RuntimeError(
                f"Failed to poll Azure results: {result_response.status_code} - {result_response.text}"
            )

        # Timeout
        raise RuntimeError(
            "Azure Document Intelligence analysis timed out after 180 seconds"
        )

    except Exception as e:
        # Re-raise Azure errors with context
        if isinstance(e, (ValueError, RuntimeError)):
            raise
        raise RuntimeError(f"Azure Document Intelligence error: {e}") from e


def extract_pdf_to_markdown(
    pdf_path: str,
    out_md_path: str,
    dpi: Optional[int] = None,
    progress: Optional[Callable[[int, int], None]] = None,
    start_page: Optional[int] = None,
    end_page: Optional[int] = None,
    keep_png: bool = False,
) -> None:
    """Extract text from PDF pages using Azure Document Intelligence OCR."""
    reader = PdfReader(pdf_path)
    num_pages = len(reader.pages)

    # Determine page range (1-based inclusive)
    s = max(1, int(start_page)) if start_page else 1
    e = min(num_pages, int(end_page)) if end_page else num_pages
    if s > e:
        s, e = e, s
    pages = list(range(s, e + 1))
    total_to_process = len(pages)

    effective_dpi = dpi if dpi is not None and dpi > 0 else DEFAULT_DPI

    lines: List[str] = []
    lines.append("# Extracted Markdown")
    lines.append("")
    lines.append(f"Source: {os.path.basename(pdf_path)}")
    lines.append(f"Pages: {num_pages}")
    if s != 1 or e != num_pages:
        lines.append(f"Processed range: {s}-{e}")
    lines.append("OCR Engine: Azure Document Intelligence")
    lines.append("")

    out_dir = os.path.dirname(out_md_path)
    for idx, p in enumerate(pages):
        lines.append(f"## Page {p}")
        png_path = os.path.join(out_dir, f"ocr_page_{p}_{effective_dpi}.png")

        if render_page_to_png(pdf_path, p, png_path, dpi=effective_dpi):
            text = azure_document_intelligence_ocr(png_path)

            if not keep_png:
                try:
                    os.remove(png_path)
                except OSError:
                    pass
        else:
            text = ""

        if text.strip():
            lines.append("")
            lines.append("```text")
            lines.append(text.strip())
            lines.append("```")
        else:
            lines.append("(no text)")
        lines.append("")

        if progress:
            try:
                progress(idx + 1, total_to_process)
            except (OSError, ValueError):
                pass

        # Gentle pacing between page submissions to avoid hitting service TPS limits
        time.sleep(0.3)

    with open(out_md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
